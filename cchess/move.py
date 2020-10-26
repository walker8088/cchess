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

from .piece import *


#-----------------------------------------------------#
class Move(object):
    def __init__(self, board, p_from, p_to, checked = None):

        self.board = board.copy()
        self.p_from = p_from
        self.p_to = p_to
        self.checked = checked
        self.captured = self.board.get_fench(p_to)
        self.board_done = board.copy()
        self.board_done._move_piece(p_from, p_to)
        self.board_done.next_turn()
        self.next_move = None
        self.sibling_move = None
        self.ucci_moves = []

    def mirror(self):
        self.board.mirror()
        self.p_from[0] = 8 - self.p_from[0]
        self.p_to[0] = 8 - self.p_to[0]
        self.board_done.mirror()

        if self.next_move:
            self.next_move.mirror()
        if self.sibling_move:
            self.sibling_move.mirror()

    def is_valid_move(self):
        return self.board.is_valid_move(self.p_from, self.p_to)

    def is_king_killed(self):
        if self.captured and self.captured.lower() == 'k':
            return True
        return False

    @property
    def move_side(self):
        return self.board.move_side

    def append_next_move(self, chess_move):
        chess_move.parent = self
        if not self.next_move:
            self.next_move = chess_move
        else:
            #找最右一个
            move = self.next_move
            while move.sibling_move:
                move = move.sibling_move
            move.sibling_move = chess_move

    def dump_moves(self, move_list, curr_move_line):

        if self.sibling_move:
            backup_move_line = curr_move_line[:]

        curr_move_line.append(self)
        #print curr_move_line
        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line)
        #else:
        #    print curr_move_line
        if self.sibling_move:
            #print self.move, 'has right', self.right.move
            move_list.append(backup_move_line)
            self.sibling_move.dump_moves(move_list, backup_move_line)

    def __str__(self):
        return self.to_iccs()
        
    def to_chinese(self):

        fench = self.board.get_fench(self.p_from)
        _, man_side = fench_to_species(fench)

        diff = self.p_to[1] - self.p_from[1]

        #黑方是红方的反向操作
        if man_side == ChessSide.BLACK:
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
                dest_str = h_level_index[man_side][self.p_to[0]]
            elif diff > 0:
                dest_str = v_change_index[man_side][diff]
            else:
                dest_str = v_change_index[man_side][-diff]
        else:  #士相马的规则
            dest_str = h_level_index[man_side][self.p_to[0]]

        name_str = self.__get_chinese_name(self.p_from)

        return name_str + diff_str + dest_str

    def __get_chinese_name(self, pos):

        fench = self.board.get_fench(pos)
        _, man_side = fench_to_species(fench)
        man_name = fench_to_chinese(fench)

        #王，士，相命名规则
        if fench.lower() in ('k', 'a', 'b'):
            return man_name + h_level_index[man_side][pos[0]]

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
            return man_name + h_level_index[man_side][pos[0]]
        elif count == 2:
            return pos_name2[man_side][pos_index] + man_name
        elif count == 3:
            #TODO 查找另一个多子行
            return pos_name3[man_side][pos_index] + man_name
        elif count == 4:
            return pos_name4[man_side][pos_index] + man_name
        elif count == 5:
            return pos_name5[man_side][pos_index] + man_name

        return man_name + h_level_index[man_side][pos[0]]

    def for_ucci(self, move_side, history):
        if self.captured:
            #吃子移动
            self.board_done.move_side = move_side
            self.ucci_fen = self.board_done.to_fen()
            self.ucci_moves = []
        else:
            #未吃子移动
            if not history:
                #历史为空
                self.ucci_fen = self.board.to_fen()
                self.ucci_moves = [self.to_iccs()]
            else:
                #历史不为空,往后追加
                last_move = history[-1]
                self.ucci_fen = last_move.ucci_fen
                self.ucci_moves = last_move.ucci_moves[:]
                self.ucci_moves.append(self.to_iccs())

    def to_ucci_fen(self):
        if len(self.ucci_moves) == 0:
            return self.ucci_fen

        move_str = ' '.join(self.ucci_moves)
        return ' '.join([self.ucci_fen, 'moves', move_str])

    def to_iccs(self):
        return chr(ord('a') + self.p_from[0]) + str(
            self.p_from[1]) + chr(ord('a') + self.p_to[0]) + str(self.p_to[1])

    @staticmethod
    def from_iccs(move_str):
        return ((ord(move_str[0]) - ord('a'), int(move_str[1])),
                (ord(move_str[2]) - ord('a'), int(move_str[3])))

    @staticmethod
    def chinese_move_to_std_move(man_kind, move_side, p_from, move_str):

        #移动规则检查
        if man_kind in ['a', 'b', 'n'] and move_str[0] == "平":
            return None
        if move_str[0] not in ['进', '退', '平']:
            return None

        #王,车,炮,兵的移动规则
        if man_kind in ['k', 'r', 'c', 'p']:
            #平移
            if move_str[0] == "平":
                new_x = h_level_index[move_side].index(move_str[1])
                return (new_x, p_from[1])
            else:
                #王，车，炮，兵的前进和后退
                diff = v_change_index[move_side].index(move_str[1])

                if move_str[0] == "退":
                    diff = -diff

                if move_side == ChessSide.BLACK:
                    diff = -diff

                return (p_from[0], p_from[1] + diff)

        #仕的移动规则
        elif man_kind == 'a':
            new_x = h_level_index[move_side].index(move_str[1])
            diff_y = -1 if move_str[0] == "进" else 1
            if self.side == ChessSide.BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #象的移动规则
        elif man_kind == 'b':
            new_x = h_level_index[move_side].index(move_str[1])
            diff_y = -2 if move_str[0] == "进" else 2
            if self.side == ChessSide.BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #马的移动规则
        elif man_kind == 'n':
            new_x = h_level_index[self.side].index(move_str[1])
            diff_x = abs(p_from[0] - new_x)

            if move_str[0] == "进":
                diff_y = [3, 2, 1][diff_x]
            else:
                diff_y = [-3, -2, -1][diff_x]

            if move_side == ChessSide.RED:
                diff_y = -diff_y

            return (new_x, p_from[1] - diff_y)

    @staticmethod
    def from_chinese(board, move_str):

        move_indexs = ["前", "中", "后", "一", "二", "三", "四", "五"]

        multi_mans = False
        multi_lines = False

        if move_str[0] in move_indexs:
            multi_mans = True
            man_index = move_indexs.index(mov_str[0])
            if man_index > 2:
                multi_lines = True
            man_name = move_str[1]

        else:
            man_name = move_str[0]

        fench = chinese_to_fench(man_name, board.move_side)
        if not fench:
            return None

        man_kind, move_side = fench_to_species(fench)

        if not multi_mans:
            #单子移动
            x = h_level_index[move_side].index(move_str[1])
            poss = board.get_fenchs_x(x, fench)

            #无子可走
            if len(poss) == 0:
                return None

            #同一行选出来多个,这种情况下, 只有士象是可以多个子尝试移动而不用标明前后的
            if (len(poss) > 1) and (man_kind not in ['a', 'b']):
                return None

            for pos in poss:
                move = Move.chinese_move_to_std_move(man_kind, move_side, pos,
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
                move = Move.chinese_move_to_std_move(man_kind, move_side, pos,
                                                     move_str[2:])
                if move:
                    return (pos, move)
                else:
                    return None
            #多兵选一移动
            else:
                pass
