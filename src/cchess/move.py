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

from .common import RED, BLACK, fench_to_species, fench_to_text, text_to_fench, pos2iccs, half2full

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
        self.annote = ''
        self.parent = None

        if self.is_checking:
            self.is_checkmate = self.board.is_checkmate()
        else:
            self.is_checkmate = False

        self.captured = self.board.get_fench(p_to)
        self.board_done = board.copy()
        self.board_done._move_piece(p_from, p_to)
        self.board_done.next_turn()  #TODO 默认红走一步，黑走一步，对于让先的处理后续考虑
        self.next_move = None

        self.sibling_next = None
        self.siblings_all_list = [self]

        self.move_list_for_engine = []
        self.fen_for_engine = None

    @property
    def move_player(self):
        return self.board.move_player

    def __str__(self):
        return self.to_iccs()

    def mirror(self):
        self.board.mirror()
        self.p_from = (8 - self.p_from[0], self.p_from[1])
        self.p_to = (8 - self.p_to[0], self.p_to[1])
        self.board_done.mirror()

        for move in self.get_siblings():
            move.mirror()

        if self.next_move:
            self.next_move.mirror()

    def flip(self):
        self.board.flip()
        self.p_from = (self.p_from[0], 9 - self.p_from[1])
        self.p_to = (self.p_to[0], 9 - self.p_to[1])
        self.board_done.flip()

        for move in self.get_siblings():
            move.flip()

        if self.next_move:
            self.next_move.flip()

    def swap(self):
        self.board.swap()
        self.board_done.swap()

        for move in self.get_siblings():
            move.swap()

        if self.next_move:
            self.next_move.swap()

    def is_valid_move(self):
        return self.board.is_valid_move(self.p_from, self.p_to)

    def is_king_killed(self):
        if self.captured and self.captured.lower() == 'k':
            return True
        return False

    def len_siblings(self):
        return len(self.siblings_all_list)
    
    def get_siblings(self, include_me = False):
        if include_me:
            return self.siblings_all_list
        
        sibs = self.siblings_all_list[:]
        sibs.remove(self)

        return sibs 

    def last_sibling(self):
        return self.siblings_all_list[-1]        
    
    def get_silbing_index(self):
        slibling_count = len(self.siblings_all_list)
        for index, m in enumerate(self.siblings_all_list):
            if m == self:
                return (index, slibling_count)

    def add_sibling(self, chess_move):
        chess_move.parent = self.parent
        chess_move.step_index = self.step_index
        last = self.last_sibling()
        
        assert last.sibling_next is None

        last.sibling_next = chess_move
        
        self.siblings_all_list.append(chess_move)
        for node in self.get_siblings():
            node.siblings_all_list = self.siblings_all_list
                    
    def remove_sibling(self, chess_move):
        if chess_move not in self.siblings_all_list:
            return
        
        #先移出兄弟表
        self.siblings_all_list.remove(chess_move)
        
        #从链上摘下
        node = self
        while node.sibling_next :
            if node.sibling_next == chess_move:
                next_node = node.sibling_next.slibling_next
                node.sibling_next = next_node
                chess_move.sibling_next = None

        #更新兄弟表到所有的兄弟        
        for node in self.get_siblings():
            node.siblings_all_list = self.siblings_all_list
                
    def append_next_move(self, chess_move):
        chess_move.parent = self
        chess_move.step_index = self.step_index + 1
        if not self.next_move:
            self.next_move = chess_move
        else:
            self.next_move.add_sibling(chess_move)
    
    def get_children(self):
        if not self.next_move:
            return []
        
        return self.next_move.get_siblings(include_me = True)
        
    def make_branchs_tag(self, branch_index, curr_sibling_index):
        
        self.branch_index = branch_index
        self.sibling_index = curr_sibling_index

        if self.next_move:
            self.next_move.make_branchs_tag(branch_index, 0)
        
        #curr_sibling_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        #所以就不能在分支中再找兄弟了，否则会重复输出分支
        if curr_sibling_index > 0:
            return

        for index, sibling_move in enumerate(self.get_siblings()):
            branch_index += 1
            sibling_index = index + 1
            sibling_move.make_branchs_tag(branch_index, sibling_index)

    def dump_moves(self, move_list, curr_move_line, is_tree_mode, curr_sibling_index = 0):

        backup_move_line = curr_move_line['moves'][:] 
        curr_move_line['moves'].append(self)
        
        curr_line_index = curr_move_line['index']

        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line, is_tree_mode, 0)
        
        #curr_sibling_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        #所以就不能在分支中再找兄弟了，否则会重复输出分支
        #assert curr_sibling_index == self.get_silbing_index()
        if curr_sibling_index > 0:
            return
        
        #只有主分支（index == 0）才会遍历兄弟分支

        for index, sibling_move in enumerate(self.get_siblings()):
            sibling_index = index + 1
            new_line_index = len(move_list)
            line_name = f'{curr_line_index}.{self.step_index}.{sibling_index}_{new_line_index}'    
            new_line = {
                    'index': new_line_index, 
                    'name':line_name,  
                     #'siblings':siblings, 
                    'sibling_index':sibling_index, 
                    'from_line': (curr_line_index, self.step_index, sibling_index), 
                    'moves':[]
                    }
    
            if not is_tree_mode:
                new_line['moves'].extend(backup_move_line)

            move_list.append(new_line)
            sibling_move.dump_moves(move_list, new_line, is_tree_mode, sibling_index)

    def init_move_line(self):
        return {'index': 0, 'name':'0', 'siblings':[], 'moves':[] }
            
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

    def to_text_with_branchs(self):
        
        assert len(self.siblings_all_list) > 0
        
        #父节点只有一个孩子，那就是自己
        if len(self.siblings_all_list) == 1:
            return self.to_text()
        
        txts = []
        for index, m in enumerate(self.siblings_all_list):
            if m == self:
               txts.append(f'{m.to_text()}') 
            else:
               txts.append('*') #m.to_text())
        
        return f"[{','.join(txts)}]"
                       
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

        move_str = half2full(move_str)

        #TODO测试黑方
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
            if move_str[0] in ['前','中','后']:
                poss = board.get_fenchs(fench)
                if move_player == BLACK:
                    poss.reverse()
                
                move_indexs = {"前": -1, "中": 1, "后": 0}
                pos = poss[move_indexs[move_str[0]]]
   
                #print(man_kind, move_player, pos, move_str[2:])
                move = Move.text_move_to_std_move(man_kind, move_player, pos,
                                                  move_str[2:])
                if move:
                    return (pos, move)
                else:
                    return None
            #多兵选一移动
            else:
                pass

