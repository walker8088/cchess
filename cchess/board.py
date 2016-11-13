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

import sys
from sets import Set

from common import *
from chessman import *
from utils import *

#-----------------------------------------------------#
class Chessboard(object):
    def __init__(self, fen = None):        
        self.clear()
        self.from_fen(fen)
            
    def clear(self):
        self._board = {}
        self.move_side = None
        self.round = 1
        self.non_kill_moves = 0
            
    def chessman_of_pos(self, pos):
        try:
            return self._board[pos]
        except:
            return None
        
    def turn_side(self) :
        if self.move_side == None :
            return None
            
        self.move_side = ChessSide.turn_side(self.move_side)
        
        self.round += 1
        
        return self.move_side
    
    def create_chessman(self, species, side, pos):     
        self._board[pos] = Chessman(self, species, side, pos)
    
    def create_chessman_from_fench(self, fench, pos):     
        species, side = fench_to_species(fench)
        self._board[pos] = Chessman(self, species, side, pos)
        
    def remove_chessman(self, pos):     
        try:
            self._board.pop(pos)
        except:
            pass
            
    def to_fen(self):
        fen = ''
        count = 0
        for y in range(9, -1, -1):
            for x in range(9):
                if (x, y) in self._board.keys():
                    if count is not 0:
                        fen += str(count)
                        count = 0
                    chessman = self._board[(x, y)]
                    ch = species_to_fench(chessman.species, chessman.side)
                    
                    if ch is not '':
                        fen += ch
                else:
                    count += 1
                    
            if count > 0:
                fen += str(count)
                count = 0
                
            if y > 0:
                fen += '/'
                
        if self.move_side is ChessSide.BLACK:
            fen += ' b'
        else:
            fen += ' w'
            
        fen += ' - - 0 %d' %(self.round)

        return fen

    def from_fen(self, fen):
        
        num_set = Set(('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        ch_set = Set(('k','a','b','n','r','c','p'))
        
        self.clear()
        
        if not fen or fen == '':
                return
        
        fen = fen.strip()
        
        x = 0
        y = 9

        for i in range(0, len(fen)):
            ch = fen[i]
            
            if ch == ' ':
                break
            elif ch == '/':
                y -= 1
                x = 0
                if y < 0:
                    break
            elif ch in num_set:
                x += int(ch)
                if x > 8:
                    x = 8
            elif ch.lower() in ch_set:
                if x <= 8:
                    self.create_chessman_from_fench(ch, (x, y))                
                    x += 1
            else:
                print "pase error"
                
        fens = fen.split() 
        
        if (len(fens) >= 2) and (fens[1] == 'b') :
                 self.move_side = ChessSide.BLACK
        else:
                self.move_side = ChessSide.RED            
        
        if len(fens) >= 6  :
                self.round = int(fens[5])
        else:
                self.round = 1      
        
    def can_make_move(self, p_from, p_to, color_limit = True) :
        
        if (p_from[0] == p_to[0]) and (p_from[1] == p_to[1]):
            print "no move"
            return False
            
        if p_from not in self._board.keys():
            print "not in"
            return False 
        
        chessman = self._board[p_from]
        
        if (chessman.side != self.move_side)  and color_limit :
            print chessman.side, "not move side ", self.move_side
            return False
            
        if not chessman.can_move_to(p_to[0],  p_to[1]):
            print "can not move"
            return False
          
        return True
        
    def make_step_move(self, p_from, p_to, color_limit = True):
    
        if not self.can_make_move(p_from, p_to, color_limit):
            return False
        
        killed_man = self._do_move(p_from, p_to)
        self.non_kill_moves = 0 if killed_man else (self.non_kill_moves + 1) 
        
        return True
                
    def make_log_step_move(self, p_from, p_to, color_limit = True):
    
        if not self.can_make_move(p_from, p_to, color_limit):
            return None
        
        fen_before_move = self.to_fen()    
        killed_man = self._do_move(p_from, p_to)
        #fen_after_move = self.to_fen()
        self.non_kill_moves = 0 if killed_man else (self.non_kill_moves + 1) 
        
        move_log = MoveLogItem(p_from, p_to, killed_man,  fen_before_move,  None,  self.non_kill_moves)
        
        return move_log
    
    def chinese_move_to_std_move(self, move_str):
        
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
                
    def std_move_to_chinese_move(self, p_from, p_to):
        
        man = self._board[p_from]
        
        return man.std_move_to_chinese_move(p_to)
    
    
    def _do_move(self, p_from, p_to):

        killed_man = None
        if p_to in self._board.keys():
            killed_man = self._board[p_to]
            
        chessman = self._board.pop(p_from)
        
        chessman.x, chessman.y = p_to
        self._board[p_to] = chessman
        
        return killed_man
        
    def __undo_move(self, p_from, p_to, killed_man = None):
        chessman = self._board[p_to]
        
        chessman.x, chessman.y = p_from
        self._board[p_from] = chessman

        if killed_man is not None:
            self._board[p_to] = killed_man
        else:
            del self._board[p_to]
    
    def between_v_line(self, x, y1, y2):
        
        min_y = min(y1, y2)
        max_y = max(y1, y2)
        
        #if (max_y - min_y) <= 1:
        #    return 0
        
        count = 0
        for m_y in range(min_y+1, max_y):
            if (x, m_y) in self._board.keys():
                count += 1
                
        return count    
    
    def between_h_line(self, y, x1, x2):
        
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        
        count = 0
        for m_x in range(min_x+1, max_x):
            if (m_x, y) in self._board.keys():
                count  += 1
        
        return count
    
    def all_chessman_at_h_line(self, y):
        #TODO
        pass
        
    def all_chessman_at_v_line(self, x):
        #TODO
        pass
    
    def __get_mans_of_kind(self, species, side):
        
        mans = []
        for key in self._board.keys():    
            man = self._board[key]
            if man.species == species and man.side == side:
                mans.append(man)
        
        return mans 
    
    def __get_mans_at_vline(self, species, side, x):
        
        mans = __get_mans_of_kind(species, side)
        
        new_mans = []
        for man in mans:    
            if man.x == x:
                new_mans.append(man)
        
        return new_mans 
  
#-----------------------------------------------------#
  
def  moves_to_chinese_moves(fen, moves_str) :
        board = Chessboard(fen)
        
        moves = moves_str.split()
        chinese_moves = []
        
        for item in moves :
                if item[0] not in ["a", "b", "c", "d", "e", "f", "g", "h", "i"] :
                        chinese_moves.append(item)
                        continue
                move_from, move_to = str_to_move(item)
                if board.can_make_move(move_from, move_to,  color_limit = False) :
                        chinese_move_str = board.std_move_to_chinese_move(move_from, move_to)
                        chinese_moves.append(chinese_move_str)
                        board.make_step_move(move_from, move_to,  color_limit = False)
                        #board.turn_side()
                else :                
                        print  move_from, move_to
                        break
                        chinese_moves.append(item)
                        continue
                        
        return " ".join(chinese_moves)       
         