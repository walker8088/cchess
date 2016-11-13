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
from utils import *

#-----------------------------------------------------#
class ChessMove(object):
    def __init__(self, move, fen = None, annotation = None):
        self.parent = None
        self.fen = fen
        self.annotation = annotation
        self.move = move
        self.next_move = None
        self.right = None

    def append_next_move(self, chess_move):
        chess_move.parent = self
        if not self.next_move:
                self.next_move = chess_move
        else:
                #找最右一个        
                move = self.next_move
                while move.right:
                        move = move.right
                move.right = chess_move

    def dump_moves(self, move_list, curr_move_line):
        
        if self.right:
            backup_move_line = curr_move_line[:]
                
        curr_move_line.append(self.move)
        #print curr_move_line
        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line)
        #else:
        #    print curr_move_line    
        if self.right:
            #print self.move, 'has right', self.right.move
            move_list.append(backup_move_line)    
            self.right.dump_moves(move_list, backup_move_line)
            
    def move_str(self):
        return move_to_str(self.move)
                
#-----------------------------------------------------#
class ChessBook(object):
    def __init__(self, init_fen = None, annotation = None):
        self.init_fen = init_fen
        self.annotation = annotation
        self.next_move = None
        self.infos = {}
        
    def append_next_move(self, chess_move):
        chess_move.parent = self
        if not self.next_move:
                self.next_move = chess_move
        else:
                #找最右一个        
                move = self.next_move
                while move.right:
                        move = move.right
                move.right = chess_move 
    
    def verify_moves(self):
        board = Chessboard()
        move_list = self.dump_moves() 
        for move_line in move_list:        
             board.from_fen(self.init_fen) 
             j = 0
             for move in move_line:   
                if board.make_step_move(move[0], move[1]):
                    board.turn_side()
                else:
                    print moves_to_chinese(self.init_fen, move_line[:j])
                    #print j, move, move_line
                    return False
                j += 1
        return True

    def dump_moves(self):
        
        if not self.next_move:
                return []

        move_list = []
        curr_move = []
        move_list.append(curr_move)

        self.next_move.dump_moves(move_list, curr_move)
        
        return move_list
    
    def count_moves(self):

        std_moves = []
        move_list = self.dump_moves()
        for move_line in move_list:
                std_moves.append(moves_to_std_moves_str(move_line))
        return std_moves

    def dump_std_moves(self):

        std_moves = []
        move_list = self.dump_moves()
        for move_line in move_list:
                std_moves.append(moves_to_std_moves_str(move_line))
        return std_moves

    def dump_chinese_moves(self):
        chinese_moves = []
        move_list = self.dump_std_moves()
        for move_line in move_list:
                chinese_moves.append(moves_to_chinese_moves(self.init_fen, move_line))
        return chinese_moves

    def dump_info(self):   
        for key in self.info:
                print key, self.info[key]
        
#-----------------------------------------------------#
if __name__ == '__main__':    
    pass
