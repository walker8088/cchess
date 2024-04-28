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

#-----------------------------------------------------#
#todo 英文全角半角统一识别
h_level_index = ((), ("九", "八", "七", "六", "五", "四", "三", "二", "一"),
                 ("１", "２", "３", "４", "５", "６", "７", "８", "９"))

v_change_index = ((), ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九"),
                  ("误", "１", "２", "３", "４", "５", "６", "７", "８", "９"))

#-----------------------------------------------------#
#士象固定位置枚举
advisor_pos = ((), ((3, 0), (5, 0), (4, 1), (3, 2), (5, 2)),
               ((3, 9), (5, 9), (4, 8), (3, 7), (5, 7)))

bishop_pos = ((), ((2, 0), (6, 0), (0, 2), (4, 2), (9, 2), (2, 4), (6, 4)),
              ((2, 9), (6, 9), (0, 7), (4, 7), (9, 7), (2, 5), (6, 5)))

#-----------------------------------------------------#
fench_name_dict = {
    'K': "帅",
    'k': "将",
    'A': "仕",
    'a': "士",
    'B': "相",
    'b': "象",
    'N': "马",
    'n': "马",
    'R': "车",
    'r': "车",
    'C': "炮",
    'c': "炮",
    'P': "兵",
    'p': "卒"
}

#-----------------------------------------------------#
name_fench_dict = {
    "帅": 'K',
    "将": 'k',
    "仕": 'A',
    "士": 'a',
    "相": 'B',
    "象": 'b',
    "马": 'n',
    "车": 'r',
    "炮": 'c',
    "兵": 'P',
    "卒": 'p'
}

_fench_txt_name_dict = {
    'K': "帅",
    'A': "仕",
    'B': "相",
    'R': "车",
    'N': "马",
    'C': "炮",
    'P': "兵",
    'k': "将",
    'a': "士",
    'b': "象",
    'r': "砗",
    'n': "碼",
    'c': "砲",
    'p': "卒"
}


def fench_to_txt_name(fench):
    return _fench_txt_name_dict[fench]


#-----------------------------------------------------#
def fench_to_text(fench):
    return fench_name_dict[fench]


def text_to_fench(text, color):
    fench = name_fench_dict[text]
    return fench.lower() if color == BLACK else fench.upper()


def fench_to_species(fen_ch):
    return fen_ch.lower(), BLACK if fen_ch.islower() else RED


def species_to_fench(species, color):
    return species_fench_dict[species][color]


#-----------------------------------------------------#
#KING, ADVISOR, BISHOP, KNIGHT, ROOK, CANNON, PAWN
'''
chessman_show_name_dict = {
    PieceT.KING: ("帅", "将"),
    PieceT.ADVISOR: ("仕", "士"),
    PieceT.BISHOP: ("相", "象"),
    PieceT.KNIGHT: ("马", "碼"),
    PieceT.ROOK: ("车", "砗"),
    PieceT.CANNON: ("炮", "砲"),
    PieceT.PAWN: ("兵", "卒")
}

def get_show_name(species, color):
    return chessman_show_name_dict[species][color]
'''
'''
piece_create_dict = {
    'k': King,
    'a': Advisor,
    'b': Bishop,
    'r': Rook,
    'c': Cannon,
    'n': Knight,
    'p': Pawn,
    }
'''


#-----------------------------------------------------#
def abs_diff(x, y):
    return (abs(x[0] - y[0]), abs(x[1] - y[1]))


def middle_p(x, y):
    return ((x[0] + y[0]) // 2, (x[1] + y[1]) // 2)


#-----------------------------------------------------#

NO_COLOR, RED, BLACK = (0, 1, 2)


def opposite_color(color):
    return 3 - color


#-----------------------------------------------------#
class Piece(object):
    def __init__(self, board, fench, pos):

        self.board = board
        self.fench = fench
        self.species, self.color = fench_to_species(fench)
        self.x, self.y = pos

    def is_valid_pos(self, pos):
        return True if ((0 <= pos[0] < 9) and (0 <= pos[1] <= 9)) else False

    def is_valid_move(self, pos_to):
        return True

    @staticmethod
    def create(board, fench, pos):
        p_type = fench.lower()
        if p_type == 'k':
            return King(board, fench, pos)
        if p_type == 'a':
            return Advisor(board, fench, pos)
        if p_type == 'b':
            return Bishop(board, fench, pos)
        if p_type == 'r':
            return Rook(board, fench, pos)
        if p_type == 'c':
            return Cannon(board, fench, pos)
        if p_type == 'n':
            return Knight(board, fench, pos)
        if p_type == 'p':
            return Pawn(board, fench, pos)


#-----------------------------------------------------#
#王
class King(Piece):
    def is_valid_pos(self, pos):
        #因为存在王杀王的情况,王可以放到对方的九宫中,所以不再根据红黑判断王的九宫在哪一边
        if not super().is_valid_pos(pos):
            return False

        if pos[0] < 3 or pos[0] > 5:
            return False

        if (pos[1] > 2) and (pos[1] < 7):
            return False

        return True

    def is_valid_move(self, pos_to):

        #face to face
        k2 = self.board.get_king(opposite_color(self.color))
        if (self.x == k2.x) and (pos_to[1]
                                 == k2.y) and (self.board.count_y_line_in(
                                     self.x, self.y, k2.y) == 0):
            #白脸将,王杀王
            return True

        if not self.is_valid_pos(pos_to):
            return False

        diff = abs_diff(pos_to, (self.x, self.y))

        return True if ((diff[0] + diff[1]) == 1) else False

    def create_moves(self):
        poss = [
            (self.x + 1, self.y),
            (self.x - 1, self.y),
            (self.x, self.y + 1),
            (self.x, self.y - 1),
        ]

        k2 = self.board.get_king(opposite_color(self.color))
        poss.append((k2.x, k2.y))

        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#士
class Advisor(Piece):
    def is_valid_pos(self, pos):
        if not super().is_valid_pos(pos):
            return False
        return True if pos in advisor_pos[self.color] else False

    def is_valid_move(self, pos_to):

        if not self.is_valid_pos(pos_to):
            return False

        if abs_diff((self.x, self.y), pos_to) == (1, 1):
            return True

        return False

    def create_moves(self):
        poss = [(self.x + 1, self.y + 1), (self.x + 1, self.y - 1),
                (self.x - 1, self.y + 1), (self.x - 1, self.y - 1)]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#象
class Bishop(Piece):
    def is_valid_pos(self, pos):
        if not super().is_valid_pos(pos):
            return False

        return True if pos in bishop_pos[self.color] else False

    def is_valid_move(self, pos_to):
        if abs_diff((self.x, self.y), (pos_to)) != (2, 2):
            return False

        #塞象眼检查
        if self.board.get_fench(middle_p((self.x, self.y), pos_to)) != None:
            return False

        #象过河检查
        if (self.color == RED) and (pos_to[1] > 4):
            return False
        if (self.color == BLACK) and (pos_to[1] < 5):
            return False

        return True

    def create_moves(self):
        poss = [(self.x + 2, self.y + 2), (self.x + 2, self.y - 2),
                (self.x - 2, self.y + 2), (self.x - 2, self.y - 2)]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#马
class Knight(Piece):
    def is_valid_move(self, pos_to):
        if (abs(self.x - pos_to[0]) == 2) and (abs(self.y - pos_to[1]) == 1):
            m_x = (self.x + pos_to[0]) // 2
            m_y = self.y

            #别马腿检查
            if self.board.get_fench((m_x, m_y)) != None:
                return False
            else:
                return True

        if (abs(self.x - pos_to[0]) == 1) and (abs(self.y - pos_to[1]) == 2):
            m_x = self.x
            m_y = (self.y + pos_to[1]) // 2
            #别马腿检查
            if self.board.get_fench((m_x, m_y)) != None:
                return False
            else:
                return True
        return False

    def create_moves(self):
        poss = [
            (self.x + 1, self.y + 2),
            (self.x + 1, self.y - 2),
            (self.x - 1, self.y + 2),
            (self.x - 1, self.y - 2),
            (self.x + 2, self.y + 1),
            (self.x + 2, self.y - 1),
            (self.x - 2, self.y + 1),
            (self.x - 2, self.y - 1),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#车
class Rook(Piece):
    def is_valid_move(self, pos_to):
        if self.x != pos_to[0]:
            #斜向移动是非法的
            if self.y != pos_to[1]:
                return False

            #水平移动
            if self.board.count_x_line_in(self.y, self.x, pos_to[0]) == 0:
                return True

        else:
            #垂直移动
            if self.board.count_y_line_in(self.x, self.y, pos_to[1]) == 0:
                return True

        return False

    def create_moves(self):
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#炮
class Cannon(Piece):
    def is_valid_move(self, pos_to):

        if self.x != pos_to[0]:
            #斜向移动是非法的
            if self.y != pos_to[1]:
                return False

            #水平移动
            count = self.board.count_x_line_in(self.y, self.x, pos_to[0])
            if (count == 0) and (self.board.get_fench(pos_to) == None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) != None):
                return True
        else:
            #垂直移动
            count = self.board.count_y_line_in(self.x, self.y, pos_to[1])
            if (count == 0) and (self.board.get_fench(pos_to) == None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) != None):
                return True

        return False

    def create_moves(self):
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)


#-----------------------------------------------------#
#兵/卒
class Pawn(Piece):
    def is_valid_pos(self, pos):

        if not super().is_valid_pos(pos):
            return False

        if (self.color == RED) and pos[1] < 3:
            return False

        if (self.color == BLACK) and pos[1] > 6:
            return False

        return True

    def is_valid_move(self, pos_to):

        not_crossed_river_step = ((), (0, 1), (0, -1))
        crossed_river_step = ((), ((-1, 0), (1, 0), (0, 1)), ((-1, 0), (1, 0),
                                                              (0, -1)))

        step = (pos_to[0] - self.x, pos_to[1] - self.y)

        crossed_river = self.is_crossed_river()

        if (not crossed_river) and (step
                                    == not_crossed_river_step[self.color]):
            return True

        if crossed_river and (step in crossed_river_step[self.color]):
            return True

        return False

    def is_crossed_river(self):
        if (self.color == RED) and (self.y > 4):
            return True

        if (self.color == BLACK) and (self.y < 5):
            return True

        return False

    def create_moves(self):
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)
