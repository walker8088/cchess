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

def decode_txt_pos(pos) :
        return (int(pos[0]), 9 - int(pos[1])) 
            
#-----------------------------------------------------#
        
class TXTLoader(object):
	def __init__(self):	
		pass
                #self.r_table = {"0":"a", "1":"b", "2":"c", "3":"d", "4":"e", "5":"f", "6":"g","7":"h","8":"i"}
	            
	def load_from_str(self, txt):

                book = {}
                book["source"] = "TXT"
                
                chess_board = Chessboard()
                chess_board.init_board()
                chess_board.move_side = RED
                
                book['fen_str'] = chess_board.get_fen()
                
                moves_str = ''
                step_no = 0
                while step_no*4 < len(txt) : 
                        steps = txt[step_no*4:step_no*4+4]
                        
                        '''
                        new_step = ''
                        if steps[0] in self.r_table.keys():
                                new_step += self.r_table[steps[0]]
                        new_step += steps[1]
                        if steps[2] in self.r_table.keys():
                                new_step += self.r_table[steps[2]]
                        new_step += steps[3]
                        '''
                        
                        move_from = decode_txt_pos(txt[step_no*4:step_no*4+2])
                        move_to = decode_txt_pos(txt[step_no*4+2:step_no*4+4])
                        
                        if chess_board.can_make_move(move_from, move_to, color_limit = True) :
                                chess_board.make_step_move(move_from, move_to, color_limit = True)
                                chess_board.turn_side()
                                step_str = move_to_str(move_from, move_to)
                        else :
                                print "bad move at", step_no, move_from, move_to
                                return  "BAD_MOVE"
                        
                        moves_str = moves_str + " " + step_str
                        step_no += 1
                        
                book["moves"] = moves_str 
                        
                return book
                        
#-----------------------------------------------------#
if __name__ == '__main__':
        txt = '77477242796770628979808166658131192710222625120209193136797136267121624117132324191724256755251547431516212226225534222434532454171600105361545113635161636061601610'
	loader = TXTLoader()
	book = loader.load_from_str(txt)
	#dump_info(book)
        moves = book["moves"]       
        print moves
        