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
import copy

from functools import *

from .exception import *
from .piece import *
from .move import *

#-----------------------------------------------------#
FULL_INIT_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'

#-----------------------------------------------------#
_text_board = [
    #' 1   2   3   4   5   6   7   8   9',
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
    #'九  八  七  六  五  四  三  二  一'
]

#-----------------------------------------------------#


def _pos_to_text_board_pos(pos):
    return (4 * pos[0] + 2, (9 - pos[1]) * 2)


#-----------------------------------------------------#
class BaseChessBoard(object):
    def __init__(self, fen=''):
        self.from_fen(fen)

    def clear(self):
        self._board = [[None for x in range(9)] for y in range(10)]
        self.move_side = ChessSide(ChessSide.NO_SIDE)

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self):
        board = [[self._board[y][8 - x] for x in range(9)] for y in range(10)]
        self._board = board

    def swap(self):
        def swap_fench(fench):
            if fench == None: return None
            return fench.upper() if fench.islower() else fench.lower()

        self._board = [[swap_fench(self._board[y][x]) for x in range(9)]
                       for y in range(10)]
        self.move_side.next()

    def put_fench(self, fench, pos):
        self._board[pos[1]][pos[0]] = fench

    def get_fench(self, pos):
        return self._board[pos[1]][pos[0]]

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
    
    def get_pieces(self, side = None):
        for x in range(9):
            for y in range(10):
                fench = self._board[y][x]
                if not fench:
                    continue
                if side == None:
                    yield Piece.create(self, fench, (x, y))
                else:
                    _, p_side = fench_to_species(fench)
                    if side == p_side:
                        yield Piece.create(self, fench, (x, y))
    
    def get_fenchs_x(self, x, fench):
        poss = []
        for y in range(10):
            if self._board[y][x] == fench:
                poss.append((x, y))
        return poss
           
    def get_king(self, side):
        limit_y = ((), (0, 1, 2), (7, 8, 9))
        for x in (3, 4, 5):
            for y in limit_y[side]:
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

        _, from_side = fench_to_species(fench_from)

        #move_side 不是None值才会进行走子颜色检查，这样处理某些特殊的存储格式时会处理比较迅速
        if (self.move_side != ChessSide.NO_SIDE) and (from_side !=
                                                      self.move_side):
            return False

        fench_to = self._board[pos_to[1]][pos_to[0]]
        if not fench_to:
            return True

        _, to_side = fench_to_species(fench_to)

        return (from_side != to_side)

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

    def move_chinese(self, move_str):
        move_from, move_to = Move.from_chinese(self, move_str)
        return self.move(move_from, move_to)

    def next_turn(self):
        return self.move_side.next()
        
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

        self.move_side = ChessSide(ChessSide.NO_SIDE)
        if (len(fens) >= 2) and (fens[1] == 'b'):
            self.move_side = ChessSide(ChessSide.BLACK)
        else:
            self.move_side = ChessSide(ChessSide.RED)

        return True

    def to_fen_base(self):
        fen = ''
        count = 0
        for y in range(9, -1, -1):
            for x in range(9):
                fench = self._board[y][x]
                if fench:
                    if count is not 0:
                        fen += str(count)
                        count = 0
                    fen += fench
                else:
                    count += 1

            if count > 0:
                fen += str(count)
                count = 0

            if y > 0: fen += '/'

        fen += ' b' if self.move_side == ChessSide.BLACK else ' w'

        return fen

    def to_fen(self):
        return self.to_fen_base() + ' - - 0 1'

    def dump_board(self):

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

#-----------------------------------------------------#

class ChessBoard(BaseChessBoard):
    def __init__(self, fen=''):
        super().__init__(fen)

    def is_valid_move(self, pos_from, pos_to):
        if not super().is_valid_move(pos_from, pos_to):
            return False

        piece = self.get_piece(pos_from)
        return piece.is_valid_move(pos_to)

    def create_moves(self):
        for piece in self.get_pieces(self.move_side):
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
        board.move_side.next()
        return (board.check_count() > 0)

    def is_checking_move(self, pos_from, pos_to):
        board = self.copy()
        board._move_piece(pos_from, pos_to)
        return (board.check_count() > 0)
    
    def is_checking(self):
        board = self.copy()
        return (board.check_count() > 0)

    def check_count(self):
        king = self.get_king(self.move_side.opposite())
        killers = self.get_pieces(self.move_side)
        return reduce(
            lambda count, piece: count + 1
            if piece.is_valid_move((king.x, king.y)) else count, killers, 0)

    def is_dead(self):
        for piece in self.get_pieces(self.move_side):
            for move_it in piece.create_moves():
                if self.is_valid_move_t(move_it):
                    if not self.is_checked_move(move_it[0], move_it[1]):
                        return False
        return True
    
    def is_win(self):
        board = self.copy()
        board.move_side.next()
        return board.is_dead()
    
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