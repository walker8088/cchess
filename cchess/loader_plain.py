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

import os
import struct, copy

from common import *
from board import *
  
#-----------------------------------------------------#
class PlainLoader(object):
	def __init__(self):	
			pass
	
	def load_from(self,  book):
                
                def man_at(man_str, index) :
                        return man_str[index*2 : index*2+2]
                
                def move_at(move_str,  index) :
                        return move_str[index*4 : index*4+4]
                        
                board = Chessboard()
                chess_mans = book['binit']
                chessman_kinds = \
                        (
                                'R',  'N',  'B',  'A', 'K', 'A',  'B',  'N', 'R' , \
                                'C', 'C', \
                                'P','P','P','P','P'  
                        )
                
                #print chess_mans
                for side in range(2):
                        for man_index in range(16):
                                man_pos = man_at(chess_mans, side * 16 + man_index)
                                if man_pos == '99':
                                        continue
                                pos =  ( int(man_pos[0]), 9 - int(man_pos[1]) )  
                                fen_ch = chr(ord(chessman_kinds[man_index]) +side * 32)
                                #print fen_ch, pos
                                board.create_chessman(get_kind(fen_ch), side, pos)
                                
                board.move_side = RED
                book['fen'] = ' '. join(board.get_fen().split()[:2])
                
                moves_str = book['bmoves']
                moves_log = []
                cmoves_log = []
                if (moves_str != None) and (len(moves_str) >= 4) :
                
                        if len(moves_str)%4 != 0 :
                                raise "steps errror"
                        
                        steps = len(moves_str)/4
                        
                        for i in range(steps) :
                                move = move_at(moves_str, i)
                                p_from = ( int(move[0]), 9- int(move[1]) )
                                p_to = ( int(move[2]), 9 - int(move[3]) )
                                if board.can_make_move(p_from, p_to) :
                                        moves_log.append(move_to_str(p_from, p_to))
                                        cmoves_log.append(board.std_move_to_chinese_move(p_from, p_to))
                                        board.make_step_move(p_from, p_to)
                                        board.turn_side()
                                else :
                                        raise "move errror"
                
                book["moves"] = ["".join(moves_log)] if len(moves_log) > 0 else []
                book["moves_zh"] = " ".join(cmoves_log)
                
                return book
                
#-----------------------------------------------------#
if __name__ == '__main__':
    loader = PlainLoader()
    