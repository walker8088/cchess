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

from board import *

#-----------------------------------------------------#

h_level_index = \
(
        (u"九",u"八",u"七",u"六",u"五",u"四",u"三",u"二",u"一"), 
        (u"１",u"２",u"３",u"４",u"５",u"６",u"７",u"８",u"９") 
)

v_change_index = \
(
        (u"错", ""u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"), 
        (u"误", ""u"１", u"２", u"３", u"４", u"５", u"６", u"７", u"８", u"９")
)

#-----------------------------------------------------#

    
#-----------------------------------------------------#
class Move(object):

    def __init__(self, board, p_from, p_to):
        
        self.board = board.copy()
        self.p_from = p_from
        self.p_to = p_to
        
        self.next_move = None
        self.right_move = None
        
    def append_next_move(self, chess_move):
        chess_move.parent = self
        if not self.next_move:
                self.next_move = chess_move
        else:
                #找最右一个        
                move = self.next_move
                while move.right_move:
                        move = move.right_move
                move.right_move = chess_move 
     
    def dump_moves(self, move_list, curr_move_line):
        
        if self.right_move:
            backup_move_line = curr_move_line[:]
                
        curr_move_line.append(self)
        #print curr_move_line
        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line)
        #else:
        #    print curr_move_line    
        if self.right_move:
            #print self.move, 'has right', self.right.move
            move_list.append(backup_move_line)    
            self.right_move.dump_moves(move_list, backup_move_line)
            
    def __str__(self):
        
        move_str = ''
        move_str += chr(ord('a') + self.p_from.x)
        move_str += str(self.p_from.y)
        move_str += chr(ord('a') + self.p_to.x)
        move_str += str(self.p_to.y)

        return move_str
        
    def from_str(self, move_str):
    
        self.p_from = Pos(ord(move_str[0]) - ord('a'), int(move_str[1]))
        self.p_to   = Pos(ord(move_str[2]) - ord('a'), int(move_str[3]))
        
        return (self.p_from, self.p_to)
        
    def to_chinese(self):
        
        fench = self.board.get_man(self.p_from)
        man_species, man_side = fench_to_species(fench)
        
        diff = self.p_to.y - self.p_from.y
        
        #黑方是红方的反向操作    
        if man_side == ChessSide.BLACK:
                diff = -diff
                
        if diff == 0:        
                diff_str = u"平"                            
        elif diff > 0:
                diff_str = u"进"       
        else:
                diff_str = u"退" 
        
        #王车炮兵规则
        if man_species in [ PieceT.KING,  PieceT.ROOK,  PieceT.CANNON,  PieceT.PAWN]:
                if diff == 0 : 
                        dest_str = h_level_index[man_side][self.p_to.x]
                elif diff > 0 : 
                        dest_str = v_change_index[man_side][diff]
                else :
                        dest_str = v_change_index[man_side][-diff]  
        else : #士相马的规则
                dest_str = h_level_index[man_side][self.p_to.x]
        
        name_str = self.__get_chinese_name(self.p_from)
                
        return name_str + diff_str + dest_str 
        
    def __get_chinese_name(self, p_from):
        
        fench = self.board.get_man(p_from)
        man_species, man_side = fench_to_species(fench)
        man_name = fench_to_name(fench) 
        
        #王，士，相命名规则
        if man_species in [ PieceT.KING,  PieceT.ADVISOR,  PieceT.BISHOP]:
                return man_name + h_level_index[man_side][p_from.x]
        
        pos_name2 = ((u'后', u'前'), (u'前', u'后')) 
        pos_name3 = ((u'后', u'中', u'前'), (u'前', u'中', u'后')) 
        pos_name4 = ((u'后', u'三', u'二', u'前'), (u'前', u'２', u'３', u'后')) 
        pos_name5 = ((u'后', u'四', u'三', u'二', u'前'), (u'前', u'２', u'３', u'４', u'后')) 
                         
        #车马炮命名规则        
        if man_species in [ PieceT.ROOK,  PieceT.CANNON,  PieceT.KNIGHT,  PieceT.PAWN]:
                #红黑顺序相反，俩数组减少计算工作量
                count = 0
                pos_index = -1
                for y in range(10):
                        if self.board._board[y][p_from.x] == fench:
                                if p_from.y == y:
                                        pos_index = count
                                count += 1
                if count == 1:
                        return man_name + h_level_index[man_side][p_from.x]
                elif count == 2:
                        return pos_name2[man_side][pos_index] + man_name
                elif count == 3:
                        return pos_name3[man_side][pos_index] + man_name
                elif count == 4:
                        return pos_name4[man_side][pos_index] + man_name
                elif count == 5:
                        return pos_name5[man_side][pos_index] + man_name
        
        return man_name + h_level_index[man_side][p_from.x]
        
    def from_chinese(self, chinese_str):
    
        move_indexs = [u"前", u"中", u"后", u"一", u"二", u"三", u"四", u"五"]
        
        multi_man = False
        multi_lines = False
        
        if move_str[0] in move_indexs:
            
            man_index = move_indexs.index(mov_str[0])
            
            if man_index > 1:
                multi_lines = True
                
            multi_man = True
            man_name = move_str[1]
            
        else :
            
            man_name = move_str[0]
        
        if man_name not in chessman_show_names[self.move_side]:
            print "error",  move_str     
        
        man_kind = chessman_show_names[self.move_side].index(man_name)
        if not multi_man:
            #单子移动指示
            man_x = h_level_index[self.move_side].index(man_name)
            mans = __get_mans_at_vline(man_kind, self.move_side) 
            
            #无子可走
            if len(mans) == 0:
                return None
            
            #同一行选出来多个
            if (len(mans) > 1) and (man_kind not in[ADVISOR, BISHOP]):
                #只有士象是可以多个子尝试移动而不用标明前后的
                return None
            
            for man in mans:
                move = man.chinese_move_to_std_move(move_str[2:]) 
                if move :
                    return move
            
            return None
            
        else:
            #多子选一移动指示
            mans = __get_mans_of_kind(man_kind, self.move_side) 
                

#-----------------------------------------------------#
if __name__ == '__main__':    
    board = BaseChessboard(FULL_INIT_FEN)
    m = Move(board, Pos(0,0), Pos(0,1) )
    print m.to_chinese() == u'车九进一'    