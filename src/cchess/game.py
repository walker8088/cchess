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
import pathlib
import datetime as dt
from collections import defaultdict

from .common import FULL_INIT_FEN
from .board import ChessBoard

# 比赛结果
UNKNOWN, RED_WIN, BLACK_WIN, PEACE = range(4)
result_str = (u"未知", u"红胜", u"黑胜", u"平局")

#存储类型
BOOK_UNKNOWN, BOOK_ALL, BOOK_BEGIN, BOOK_MIDDLE, BOOK_END = range(5)
book_type_str = (u"未知", u"全局", u"开局", u"中局", u"残局")


#-----------------------------------------------------#
class Game(object):
    def __init__(self, board = None, comment = None):
        if board is not None:
            self.init_board = board.copy()
        else:
            self.init_board = ChessBoard()
        self.comment = comment
        #初始节点
        self.first_move = None
        #最后节点，追加新的move时，从这个节点后追加
        self.last_move = None

        self.info = defaultdict(str)
        #默认一个分支
        self.info['branchs'] = 1

    def __str__(self):
        return str(self.info)
    
    #当第一步走法就有变招的时候，需多次调用这个函数
    def append_first_move(self, chess_move):
        chess_move.parent = self
        
        if not self.first_move:
            self.first_move = chess_move
            self.init_board = chess_move.board.copy()
            self.last_move = self.first_move
        else:
            self.first_move.add_sibling(chess_move)
        
        return chess_move

    #给当前的最后招法节点增加后续节点，如果已经有后续节点了，则增加后续节点的兄弟节点    
    def append_next_move(self, chess_move):
        if not self.first_move:
            chess_move.parent = self
            self.first_move = chess_move
            self.init_board = chess_move.board.copy()
            self.last_move = self.first_move
        else:    
            self.last_move.append_next_move(chess_move)
            self.last_move = chess_move
        
        return chess_move
    
    '''
    def add_sibling_move(self, chess_move):
        if not self.last_move:
        
        else:    
            self.last_move.add_sibling_move(chess_move)
            self.last_move = chess_move
        
        return chess_move
    '''

    def get_children(self):
        if not self.first_move:
            return []
        
        siblings = list(self.first_move.get_siblings(include_me = True))
        print(siblings)
        return siblings

    def verify_moves(self):
        move_list = self.dump_iccs_moves()
        for index, move_line in enumerate(move_list):
            board = self.init_board.copy()
            for step_no, iccs in enumerate(move_line):
                m = board.move_iccs(iccs)
                if m is None:
                    raise Exception(f"{index}_{step_no}_{iccs} {','.join(move_line)}")
                board.next_turn()
                    
        return True

    def mirror(self):
        self.init_board.mirror()
        if self.first_move:
            self.first_move.mirror()

    def flip(self):
        self.init_board.flip()
        if self.first_move:
            self.first_move.flip()

    def swap(self):
        self.init_board.swap()
        if self.first_move:
            self.first_move.swap()

    def iter_moves(self, move=None):
        if move is None:
            move = self.first_move
        while move:
            yield move
            move = move.next_move

    def dump_init_board(self):
        return self.init_board.dump_board()

    def dump_moves(self, is_tree_mode = False):

        move_list = []

        if self.first_move:
            curr_line = self.first_move.init_move_line()
            move_list.append(curr_line)            
            self.first_move.dump_moves(move_list, curr_line, is_tree_mode)
            
        return move_list

    def dump_iccs_moves(self):
        return [[str(move) for move in move_line['moves']]
                for move_line in self.dump_moves()]
    
    def dump_fen_iccs_moves(self):
        return [[ [move.board.to_fen(), str(move)] for move in move_line['moves'] ]
                for move_line in self.dump_moves()]

    def dump_text_moves(self, show_branch = False):
        return [[move.to_text_detail(show_branch, show_comment = False)[0] for move in move_line['moves']]
                for move_line in self.dump_moves()]
    
    def dump_text_note_moves(self, show_branch = False, show_comment = False):
        return [[move.to_text_detail(show_branch, show_comment) for move in move_line['moves']]
                for move_line in self.dump_moves()]
    
    def move_line_to_list(self, move = None):
        if not move:
            move = self.first_move
        
        move_line = []
        while move:
            move_line.append(move)
            move = move.next_move
        
        return move_line    
        
    def make_branchs_tag(self):
        if not self.first_move:
            return
        self.first_move.make_branchs_tag(0, 0)            
            
    def print_init_board(self):
        for line in self.init_board.text_view():
            print(line)

    def print_text_moves(self, steps_per_line = 2, show_comment = False):

        moves = self.dump_text_note_moves(True, show_comment)
        for index, line in enumerate(moves):
            if len(moves) > 1:
                print(f'第 {index+1} 分支')
            line_move = '' 
            for i, (text, comment) in enumerate(line):
                if (i % 2) == 0:
                    line_move += f' {(i // 2 + 1):02d}.{text}'
                else:
                    line_move += f' {text}'
                if show_comment and comment:
                    line_move += f'[{comment}]'
                i += 1
                if (i % (steps_per_line * 2)) == 0:
                    print(line_move)
                    line_move = ''
            if line_move:
                print(line_move)
                
    def dump_info(self):
        for key in self.info:
            print(key, self.info[key])
    
    @staticmethod
    def read_from(file_name):
        #在函数开始时才导入以避免循环导入
        from .io_xqf import read_from_xqf
        from .read_pgn import read_from_pgn
        from .read_cbf import read_from_cbf
        from .read_cbr import read_from_cbr
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.xqf':
            return read_from_xqf(file_name)
        elif ext == '.pgn':
            return read_from_pgn(file_name)
        elif ext == '.cbf':
            return read_from_cbf(file_name)
        elif ext == '.cbr':
            return read_from_cbr(file_name)
        else:
            raise Exception(f"Unknown file format:{file_name}")
    
    @staticmethod
    def read_from_lib(file_name):
        #在函数开始时才导入以避免循环导入
        from .read_cbr import read_from_cbl
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.cbl':
            return read_from_cbl(file_name)
        else:
            raise Exception(f"Unknown lib file format:{file_name}")
    
    def save_to_pgn(self, file_name):
        from .io_pgn import PGNWriter
        
        w = PGNWriter(self)
        w.write_file(file_name)
        
    
    def save_to(self, file_name):
       
        from .io_xqf import XQFWriter
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.xqf':
            writer = XQFWriter(self)    
            return writer.save(file_name)
        elif ext == '.pgn':
            return self.save_to_pgn(file_name)
            