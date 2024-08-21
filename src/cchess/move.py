# -*- coding: utf-8 -*-
'''
Copyright (C) 2014  walker li <walker8088@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from copy import deepcopy

from .common import RED, BLACK, fench_to_species, fench_to_text, text_to_fench, pos2iccs

#-----------------------------------------------------#
#TODO 英文全角半角统一识别
_h_level_index = ((), ("九", "八", "七", "六", "五", "四", "三", "二", "一"),
                 ("１", "２", "３", "４", "５", "６", "７", "８", "９"))

_v_change_index = ((), ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九"),
                  ("误", "１", "２", "３", "４", "５", "６", "７", "８", "９"))

#-----------------------------------------------------#
class Move(object):
    def __init__(self, board, p_from, p_to, is_checking=False):

        self.board = board.copy()
        self.p_from = p_from
        self.p_to = p_to
        self.is_checking = is_checking
        self.step_index = 0
        self.score = None

        if self.is_checking:
            self.is_checkmate = self.board.is_checkmate()
        else:
            self.is_checkmate = False

        self.captured = self.board.get_fench(p_to)
        self.board_done = board.copy()
        self.board_done._move_piece(p_from, p_to)
        self.board_done.next_turn()  ##TODO fix
        self.next_move = None

        self.branchs = []

        self.branch_index = 0

        self.move_list_for_engine = []
        self.fen_for_engine = None

    def mirror(self):
        self.board.mirror()
        self.p_from = (8 - self.p_from[0], self.p_from[1])
        self.p_to = (8 - self.p_to[0], self.p_to[1])
        self.board_done.mirror()

        for move in self.branchs:
            move.mirror()

        if self.next_move:
            self.next_move.mirror()

    def flip(self):
        self.board.flip()
        self.p_from = (self.p_from[0], 9 - self.p_from[1])
        self.p_to = (self.p_to[0], 9 - self.p_to[1])
        self.board_done.flip()

        for move in self.branchs:
            move.flip()

        if self.next_move:
            self.next_move.flip()

    def swap(self):
        self.board.swap()
        self.board_done.swap()

        for move in self.branchs:
            move.swap()

        if self.next_move:
            self.next_move.swap()

    def is_valid_move(self):
        return self.board.is_valid_move(self.p_from, self.p_to)

    def is_king_killed(self):
        if self.captured and self.captured.lower() == 'k':
            return True
        return False

    @property
    def move_player(self):
        return self.board.move_player

    def append_next_move(self, chess_move):
        chess_move.parent = self
        chess_move.step_index = self.step_index + 1
        if not self.next_move:
            self.next_move = chess_move
        else:
            self.next_move.branchs.append(chess_move)

    def branchs(self):
        return len(self.branchs)

    def get_branch(self, index):
        return self.branchs[index]

    def select_branch(self, index):
        self.branch_index = index

    def get_all_branchs(self):
        return [self].extent(self.branchs)

    def dump_moves(self, move_list, curr_move_line):

        backup_move_line = curr_move_line[:]
        index_save = backup_move_line[0][:]

        curr_move_line.append(self)

        if not self.next_move:
            return

        if len(self.branchs) > 0:
            curr_move_line[0].append(0)

        self.next_move.dump_moves(move_list, curr_move_line)

        if len(self.branchs) > 0:
            for index, move in enumerate(self.branchs):
                new_line = backup_move_line[:]
                indexs = index_save[:]
                indexs.append(index + 1)
                new_line[0] = indexs
                move_list.append(new_line)
                move.dump_moves(move_list, new_line)

    def dump_moves_line(self, move_list):

        if self.branch_index == 0:
            sel_move = self

        elif self.branch_index <= len(self.branchs):
            sel_move = self.branchs[self.branch_index - 1]
        else:
            sel_move = None

        if not sel_move:
            return
        move_list.append(sel_move)

        if not sel_move.next_move:
            return

        sel_move.next_move.dump_moves_line(move_list)

    #对move分支进行标记
    def tag_move_branch(self, move_list, curr_move_line):

        backup_move_line = deepcopy(curr_move_line)

        curr_move_line.append(self)
        #print curr_move_line
        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line)
        if len(self.branchs) > 0:
            #print self.move, 'has right', self.right.move
            move_list.append(backup_move_line)
            for move in self.branchs:
                move.dump_moves(move_list, backup_move_line)

    def __str__(self):
        return self.to_iccs()

    def to_text(self, detailed=False):

        fench = self.board.get_fench(self.p_from)
        _, man_side = fench_to_species(fench)

        diff = self.p_to[1] - self.p_from[1]

        #黑方是红方的反向操作
        if man_side == BLACK:
            diff = -diff

        if diff == 0:
            diff_str = "平"
        elif diff > 0:
            diff_str = "进"
        else:
            diff_str = "退"

        #王车炮兵规则
        if fench.lower() in ('k', 'r', 'c', 'p'):
            if diff == 0:
                dest_str = _h_level_index[man_side][self.p_to[0]]
            elif diff > 0:
                dest_str = _v_change_index[man_side][diff]
            else:
                dest_str = _v_change_index[man_side][-diff]
        else:  #士相马的规则
            dest_str = _h_level_index[man_side][self.p_to[0]]

        name_str = self.__get_text_name(self.p_from)

        text = name_str + diff_str + dest_str
        if not detailed:
            return text

        details = []
        if self.captured:
            details.append(f'吃{fench_to_text(self.captured)}', )
        if self.is_checkmate:
            details.append('将死', )
        elif self.is_checking:
            details.append('将军', )

        if len(details) == 0:
            return text
        else:
            return f'{text}({",".join(details)})'

    def __get_text_name(self, pos):

        fench = self.board.get_fench(pos)
        _, man_side = fench_to_species(fench)
        man_name = fench_to_text(fench)

        #王，士，相命名规则
        if fench.lower() in ('k', 'a', 'b'):
            return man_name + _h_level_index[man_side][pos[0]]

        #车,马,炮,兵命名规则
        #红黑顺序相反，俩数组减少计算工作量
        pos_name2 = ((), ('后', '前'), ('前', '后'))
        pos_name3 = ((), ('后', '中', '前'), ('前', '中', '后'))
        pos_name4 = ((), ('后', '三', '二', '前'), ('前', '２', '３', '后'))
        pos_name5 = ((), ('后', '四', '三', '二', '前'), ('前', '２', '３', '４', '后'))

        count = 0
        pos_index = -1
        for y in range(10):
            if self.board._board[y][pos[0]] == fench:
                if pos[1] == y:
                    pos_index = count
                count += 1

        if count == 1:
            return man_name + _h_level_index[man_side][pos[0]]
        elif count == 2:
            return pos_name2[man_side][pos_index] + man_name
        elif count == 3:
            #TODO 查找另一个多子行
            return pos_name3[man_side][pos_index] + man_name
        elif count == 4:
            return pos_name4[man_side][pos_index] + man_name
        elif count == 5:
            return pos_name5[man_side][pos_index] + man_name

        return man_name + _h_level_index[man_side][pos[0]]

    def prepare_for_engine(self, move_player, history):
        if self.captured:
            #吃子移动
            self.board_done.move_player = move_player
            self.fen_for_engine = self.board_done.to_fen()
            self.move_list_for_engine = []
        else:
            #未吃子移动
            if not history:
                #历史为空
                self.fen_for_engine = self.board.to_fen()
                self.move_list_for_engine = [self.to_iccs()]
            else:
                #历史不为空,往后追加
                last_move = history[-1]
                self.fen_for_engine = last_move.fen_for_engine
                self.move_list_for_engine = last_move.move_list_for_engine[:]
                self.move_list_for_engine.append(self.to_iccs())

    def to_engine_fen(self):
        if len(self.move_list_for_engine) == 0:
            return self.fen_for_engine

        move_str = ' '.join(self.move_list_for_engine)
        return ' '.join([self.fen_for_engine, 'moves', move_str])

    def to_iccs(self):
        return pos2iccs(self.p_from, self.p_to)

    @staticmethod
    def text_move_to_std_move(man_kind, move_player, p_from, move_str):

        #移动规则检查
        if man_kind in ['a', 'b', 'n'] and move_str[0] == "平":
            return None
        if move_str[0] not in ['进', '退', '平']:
            return None

        #王,车,炮,兵的移动规则
        if man_kind in ['k', 'r', 'c', 'p']:
            #平移
            if move_str[0] == "平":
                new_x = _h_level_index[move_player].index(move_str[1])
                return (new_x, p_from[1])
            else:
                #王，车，炮，兵的前进和后退
                diff = _v_change_index[move_player].index(move_str[1])

                if move_str[0] == "退":
                    diff = -diff

                if move_player == BLACK:
                    diff = -diff

                return (p_from[0], p_from[1] + diff)

        #仕的移动规则
        elif man_kind == 'a':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_y = -1 if move_str[0] == "进" else 1
            if move_player == BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #象的移动规则
        elif man_kind == 'b':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_y = -2 if move_str[0] == "进" else 2
            if move_player == BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #马的移动规则
        elif man_kind == 'n':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_x = abs(p_from[0] - new_x)

            if move_str[0] == "进":
                diff_y = [3, 2, 1][diff_x]
            else:
                diff_y = [-3, -2, -1][diff_x]

            if move_player == RED:
                diff_y = -diff_y

            return (new_x, p_from[1] - diff_y)

    @staticmethod
    def from_text(board, move_str):

        move_indexs = ["前", "中", "后", "一", "二", "三", "四", "五"]

        multi_mans = False
        multi_lines = False

        if move_str[0] in move_indexs:
            multi_mans = True
            man_index = move_indexs.index(move_str[0])
            if man_index > 2:
                multi_lines = True
            man_name = move_str[1]

        else:
            man_name = move_str[0]
        
        if multi_lines:
            #TODO 处理兵的多行位置定位问题
            pass

        fench = text_to_fench(man_name, board.move_player)
        if not fench:
            return None

        man_kind, move_player = fench_to_species(fench)

        if not multi_mans:
            #单子移动
            x = _h_level_index[move_player].index(move_str[1])
            poss = board.get_fenchs_x(x, fench)

            #无子可走
            if len(poss) == 0:
                return None

            #同一行选出来多个,这种情况下, 只有士象是可以多个子尝试移动而不用标明前后的
            if (len(poss) > 1) and (man_kind not in ['a', 'b']):
                return None

            for pos in poss:
                move = Move.text_move_to_std_move(man_kind, move_player, pos,
                                                  move_str[2:])
                if move:
                    return (pos, move)

            return None

        else:
            #多选一移动
            if move_str[0] in ['前', '后']:
                poss = board.get_fenchs(fench)
                move_indexs = {"前": 0, "后": -1}
                pos = poss[move_indexs[move_str[0]]]
                move = Move.text_move_to_std_move(man_kind, move_player, pos,
                                                  move_str[2:])
                if move:
                    return (pos, move)
                else:
                    return None
            #多兵选一移动
            else:
                pass

