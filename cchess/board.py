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
import sys
import copy
import json

from functools import *

from .exception import *
from .piece import *
from .move import *


#-----------------------------------------------------#
FULL_INIT_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w'
EMPTY_BOARD = '9/9/9/9/9/9/9/9/9/9'
EMPTY_FEN = f'{EMPTY_BOARD} w'

#-----------------------------------------------------#
_text_board = [
    #'  1   2   3   4   5   6   7   8   9 ',
    '9 ┌───┬───┬───┬───┬───┬───┬───┬───┐ ',
    '  │   │   │   │ ＼│ ／│   │   │   │ ',
    '8 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │   │ ／│ ＼│   │   │   │ ',
    '7 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │　 │　 │   │   │   │   │ ',
    '6 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │　 │　 │   │   │   │   │   │   │ ',
    '5 ├───┴───┴───┴───┴───┴───┴───┴───┤ ',
    '  │　                             │ ',
    '4 ├───┬───┬───┬───┬───┬───┬───┬───┤ ',
    '  │　 │　 │   │   │   │　 │　 │　 │ ',
    '3 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │　 │　 │   │   │   │   │ ',
    '2 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │   │   │ ＼│ ／│　 │　 │　 │ ',
    '1 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │   │ ／│ ＼│　 │   │   │ ',
    '0 └───┴───┴───┴───┴───┴───┴───┴───┘ ',
    '   ',
    '  a   b   c   d   e   f   g   h   i ',
    '  0   1   2   3   4   5   6   7   8 ',
    #'  九  八  七  六  五  四  三  二  一',
    #'',
]

PLAYER = ('', 'RED', 'BLACK')
PLAYER_CN = ('', '红方', '黑方')

#-----------------------------------------------------#
def _pos_to_text_board_pos(pos):
    return (4 * pos[0] + 2, (9 - pos[1]) * 2)


#-----------------------------------------------------#
class ChessPlayer():
    
    def __init__(self, color):
        self.color = color
        
    def next(self):
        if self.color != NO_COLOR: 
            self.color = 3 - self.color
        return ChessPlayer(self.color)

    def opposite(self):
        if self.color == NO_COLOR: 
            return NO_COLOR
        return 3 - self.color
    
    def __str__(self):
        return PLAYER[self.color]
        
    def __eq__(self, other):
        if isinstance(other, ChessPlayer):
            return self.color == other.color
        elif isinstance(other, int):
            return self.color == other    
        return False
        
#-----------------------------------------------------#
class BaseChessBoard(object):
    def __init__(self, fen=''):
        self.from_fen(fen)

    def clear(self):
        self._board = [[None for x in range(9)] for y in range(10)]
        self.move_player = ChessPlayer(NO_COLOR)

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self):
        board = [[self._board[y][8 - x] for x in range(9)] for y in range(10)]
        self._board = board
    
    def flip(self):
        board = [[self._board[9 - y][x] for x in range(9)] for y in range(10)]
        self._board = board

    def swap(self):
    
        def swap_fench(fench):
            if fench == None: return None
            return fench.upper() if fench.islower() else fench.lower()

        self._board = [[swap_fench(self._board[y][x]) for x in range(9)]
                       for y in range(10)]
                       
        self.move_player.next()
    
    def set_move_color(self, color):
        self.move_player = ChessPlayer(color)
        
    def get_move_color(self):
        return self.move_player.color
        
    def put_fench(self, fench, pos):
        self._board[pos[1]][pos[0]] = fench
    
    def remove_fench(self, pos):
        self._board[pos[1]][pos[0]] = None

    def get_fench(self, pos):
        return self._board[pos[1]][pos[0]]
    
    def get_fench_color(self, pos):
        fench = self.get_fench(pos)
        
        if not fench:
            return None
        
        return RED if fench.isupper() else BLACK
        
    def get_fenchs(self, fench):
        poss = []
        for x in range(9):
            for y in range(10):
                if self._board[y][x] == fench:
                    poss.append((x, y))
        return poss
    
    def get_piece(self, pos):
        fench = self.get_fench(pos)
        return Piece.create(self, fench, pos) if fench else None
    
    def get_pieces(self, color = None):
        
        if isinstance(color, ChessPlayer):
            color = color.color
        
        for x in range(9):
            for y in range(10):
                fench = self._board[y][x]
                if not fench:
                    continue
                if color == None:
                    yield Piece.create(self, fench, (x, y))
                else:
                    _, p_color = fench_to_species(fench)
                    if color == p_color:
                        yield Piece.create(self, fench, (x, y))
    
    def get_fenchs_x(self, x, fench):
        poss = []
        for y in range(10):
            if self._board[y][x] == fench:
                poss.append((x, y))
        return poss
           
    def get_king(self, color):
        
        if isinstance(color, ChessPlayer):
            color = color.color
            
        limit_y = ((), (0, 1, 2), (7, 8, 9))
        for x in (3, 4, 5):
            for y in limit_y[color]:
                fench = self._board[y][x]
                if not fench:
                    continue
                if fench.lower() == 'k':
                    return Piece.create(self, fench, (x, y))
        return None

    def is_valid_move_t(self, move_t):
        return self.is_valid_move(move_t[0], move_t[1])

    def is_valid_move(self, pos_from, pos_to):
        '''
        只进行最基本的走子规则检查，不对每个子的规则进行检查，以加快文件加载之类的速度
        '''

        if not (0 <= pos_to[0] <= 8): return False
        if not (0 <= pos_to[1] <= 9): return False

        fench_from = self._board[pos_from[1]][pos_from[0]]
        if not fench_from:
            return False

        _, from_color = fench_to_species(fench_from)

        #move_player 不是None值才会进行走子颜色检查，这样处理某些特殊的存储格式时会处理比较迅速
        if (self.move_player != NO_COLOR) and (self.move_player != from_color):
            return False

        fench_to = self._board[pos_to[1]][pos_to[0]]
        if not fench_to:
            return True

        _, to_color = fench_to_species(fench_to)

        return (from_color != to_color)

    def _move_piece(self, pos_from, pos_to):

        fench = self._board[pos_from[1]][pos_from[0]]
        self._board[pos_to[1]][pos_to[0]] = fench
        self._board[pos_from[1]][pos_from[0]] = None

        return fench

    def move(self, pos_from, pos_to):

        if not self.is_valid_move(pos_from, pos_to):
            return None

        board = self.copy()
        fench = self.get_fench(pos_to)
        self._move_piece(pos_from, pos_to)

        return Move(board, pos_from, pos_to)

    def move_iccs(self, move_str):
        move_from, move_to = Move.from_iccs(move_str)
        return self.move(move_from, move_to)

    def move_text(self, move_str):
        move_from, move_to = Move.from_text(self, move_str)
        return self.move(move_from, move_to)

    def next_turn(self):
        return self.move_player.next()
        
    def from_fen(self, fen):

        num_set = set(('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        ch_set = set(('k', 'a', 'b', 'n', 'r', 'c', 'p'))

        self.clear()

        if fen == '':
            return True

        fen = fen.strip()

        x = 0
        y = 9

        for i in range(0, len(fen)):
            ch = fen[i]

            if ch == ' ': break
            elif ch == '/':
                y -= 1
                x = 0
                if y < 0: break
            elif ch in num_set:
                x += int(ch)
                if x > 8: x = 8
            elif ch.lower() in ch_set:
                if x <= 8:
                    self.put_fench(ch, (x, y))
                    x += 1
            else:
                return False

        fens = fen.split()

        self.move_player = ChessPlayer(NO_COLOR)
        
        if (len(fens) >= 2) and (fens[1] == 'b'):
            self.move_player = ChessPlayer(BLACK)
        else:
            self.move_player = ChessPlayer(RED)

        return True

    def to_fen(self):
        fen = ''
        count = 0
        for y in range(9, -1, -1):
            for x in range(9):
                fench = self._board[y][x]
                if fench:
                    if count != 0:
                        fen += str(count)
                        count = 0
                    fen += fench
                else:
                    count += 1

            if count > 0:
                fen += str(count)
                count = 0

            if y > 0: fen += '/'

        fen += ' b' if self.move_player == BLACK else ' w'

        return fen

    def to_full_fen(self):
        return self.to_fen() + ' - - 0 1'
    
    def detect_move_pieces(self, new_board):
        p_from = []
        p_to = []
        for x in range(9):
            for y in range(10):
                p_old = self.get_fench((x, y))
                p_new = new_board.get_fench((x, y))    
                #same
                if p_old == p_new: 
                    continue
                #move from
                if p_new is None:
                   p_from.append((x, y)) 
                #move_to
                else:
                   p_to.append((x, y))
        return (p_from, p_to)
    
    def create_move_from_board(self, new_board):
        p_froms, p_tos = self.detect_move_pieces(new_board)
        if (len(p_froms) == 1) and (len(p_tos) == 1):
            p_from = p_froms[0]   
            p_to = p_tos[0]   
            if self.is_valid_move(p_from, p_to):
                return (p_from, p_to)   
        return None
            
    def text_view(self):

        board_str = _text_board[:]

        y = 0
        for line in self._board:
            x = 8
            for ch in line[::-1]:
                if ch:
                    pos = _pos_to_text_board_pos((x, y))
                    new_text = board_str[pos[1]][:pos[0]] + fench_to_txt_name(ch) + board_str[pos[1]][pos[0] + 2:]
                    board_str[pos[1]] = new_text
                x -= 1
            y += 1

        return board_str

    def print_board(self):
        print('')
        for s in self.text_view():
            print(s)

#-----------------------------------------------------#

class ChessBoard(BaseChessBoard):
    def __init__(self, fen = '', chess_dict = None):
        super().__init__(fen)
        self.__chess_dict = chess_dict
        
    def load_one_hot_dict(self, file):
           self.__chess_dict = json.load(open(file))
           self.__chess_dict[None] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def move(self, pos_from, pos_to):
        move = super().move(pos_from, pos_to)  
        if move:
            if  self.is_checking():
                move.is_checking = True
                if  self.is_checkmate():
                    move.is_checkmate = True        
        return  move
        
    def is_valid_move(self, pos_from, pos_to):
        if not super().is_valid_move(pos_from, pos_to):
            return False  

        piece = self.get_piece(pos_from)
        return piece.is_valid_move(pos_to)

    def create_moves(self):
        for piece in self.get_pieces(self.move_player):
            for move in piece.create_moves():
                yield move

    def create_piece_moves(self, pos):
        piece = self.get_piece(pos)
        if piece:
            for move in piece.create_moves():
                yield move

    def is_checked_move(self, pos_from, pos_to):
        if not self.is_valid_move(pos_from, pos_to):
            raise CChessException('Invalid Move')
        board = self.copy()
        board._move_piece(pos_from, pos_to)
        board.move_player.next()
        return board.is_checking()

    def is_checking_move(self, pos_from, pos_to):
        board = self.copy()
        board._move_piece(pos_from, pos_to)
        return board.is_checking()
    
    def is_checking(self):
        king = self.get_king(self.move_player.opposite())
        if not king:
            return False
        
        for piece in self.get_pieces(self.move_player):
            if piece.is_valid_move((king.x, king.y)):
                return True
        
        return False     
    
    def is_checkmate(self):
        board = self.copy()
        board.move_player.next()
        return board.no_moves()
    
    def no_moves(self):
        king = self.get_king(self.move_player)
        if not king:
            return True
        for piece in self.get_pieces(self.move_player):
            for move_it in piece.create_moves():
                if self.is_valid_move_t(move_it):
                    if not self.is_checked_move(move_it[0], move_it[1]):
                        return False
        return True
    
    
    def count_x_line_in(self, y, x_from, x_to):
        return reduce(lambda count, fench: count + 1 if fench else count,
                      self.x_line_in(y, x_from, x_to), 0)

    def count_y_line_in(self, x, y_from, y_to):
        return reduce(lambda count, fench: count + 1 if fench else count,
                      self.y_line_in(x, y_from, y_to), 0)

    def x_line_in(self, y, x_from, x_to):
        step = 1 if x_to > x_from else -1
        return [self._board[y][x] for x in range(x_from + step, x_to, step)]

    def y_line_in(self, x, y_from, y_to):
        step = 1 if y_to > y_from else -1
        return [self._board[y][x] for y in range(y_from + step, y_to, step)]

    def get_one_hot_board(self) -> list:
        """
        依据`self.__chess_dict`对棋子进行独热编码
        :return: 一个列表，将棋子进行独热编码后的棋盘
        """
        one_hot_board = []
        for x in self._board.copy():
            temp = []
            for y in x:
                temp.append(self.__chess_dict.get(y, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
            one_hot_board.append(temp)
        return one_hot_board

    @property
    def chess_dict(self):
        """
        获取棋子-独热编码的映射
        :return: 字典，棋子-独热编码的映射
        """
        return self.__chess_dict.copy()

