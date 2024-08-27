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

from .common import FULL_INIT_FEN

# 比赛结果
UNKNOWN, RED_WIN, BLACK_WIN, PEACE = range(4)
result_str = (u"未知", u"红胜", u"黑胜", u"平局")

#存储类型
BOOK_UNKNOWN, BOOK_ALL, BOOK_BEGIN, BOOK_MIDDLE, BOOK_END = range(5)
book_type_str = (u"未知", u"全局", u"开局", u"中局", u"残局")


#-----------------------------------------------------#
class Game(object):
    def __init__(self, board = None, annotation = None):
        if board is not None:
            self.init_board = board.copy()
        else:
            self.init_board = ChessBoard()
        self.annotation = annotation
        self.first_move = None
        self.last_move = None

        self.info = {}

    def __str__(self):
        return str(self.info)

    def append_first_move(self, chess_move):
        if not self.first_move:
            self.first_move = chess_move
            self.last_move = self.first_move
        else:
            self.first_move.branchs.append(chess_move)
        return chess_move
    
    def append_next_move(self, chess_move):
    
        if not self.first_move:
            self.first_move = chess_move
            self.last_move = self.first_move
            return
            
        self.last_move.append_next_move(chess_move)
        self.last_move = chess_move
        
        return self
        
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

    def dump_moves(self):

        if not self.first_move:
            return []

        move_list = []
        curr_move = [
            [],
        ]
        move_list.append(curr_move)

        self.first_move.dump_moves(move_list, curr_move)

        return move_list
    
    def dump_iccs_moves(self):
        return [[str(move) for move in move_line[1:]]
                for move_line in self.dump_moves()]
    
    def dump_fen_iccs_moves(self):
        return [[ [move.board.to_fen(), str(move)] for move in move_line[1:] ]
                for move_line in self.dump_moves()]

    def dump_text_moves(self):
        return [[move.to_text() for move in move_line[1:]]
                for move_line in self.dump_moves()]
    
    def dump_moves_line(self):

        if not self.first_move:
            return []

        move_line = []
        self.first_move.dump_moves_line(move_line)

        return move_line

    def print_init_board(self):
        for line in self.init_board.text_view():
            print(line)

    def print_text_moves(self, steps_per_line = 2):

        moves = self.dump_text_moves()
        for index, line in enumerate(moves):
            if len(moves) > 1:
                print(f'第 {index+1} 分支')
            line_move = '' 
            for i, it in enumerate(line):
                if (i % 2) == 0:
                    line_move += f' {(i // 2 + 1):02d}.{it}'
                else:
                    line_move += f' {it}'
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
        #避免循环导入
        from .read_xqf import read_from_xqf
        from .read_pgn import read_from_pgn
        from .read_cbf import read_from_cbf

        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.xqf':
            return read_from_xqf(file_name)
        if ext == '.pgn':
            return read_from_pgn(file_name)
        if ext == '.cbf':
            return read_from_cbf(file_name)
            
    def save_to(self, file_name):
        init_fen = self.init_board.to_fen()
        with open(file_name, 'w') as f:
            f.write('[Game "Chinese Chess"]\n')
            f.write(f'[Date "{dt.date.today()}"]\n')
            f.write('[Red ""]\n')
            f.write('[Black ""]\n')
            if init_fen != FULL_INIT_FEN:
                f.write(f'[FEN "{self.init_board.to_full_fen()}"]\n')
            moves = self.dump_text_moves()
            if len(moves) > 0:
                move_line = moves[0]
                for index, m in enumerate(move_line):
                    if (index % 2) == 0:
                        pre_str = f" {index//2+1}."
                    else:
                        pre_str = "    "
                    f.write(f'{pre_str} {m}\n')
            f.write('   *\n')
            f.write('  =========\n')
            