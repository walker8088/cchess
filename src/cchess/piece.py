# -*- coding: utf-8 -*-
"""
Copyright (C) 2024  walker li <walker8088@gmail.com>

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
"""

from .common import fench_to_species, opposite_color, RED, BLACK

# pylint: disable=too-many-return-statements

# -----------------------------------------------------#
# 士象固定位置枚举
_advisor_pos = (
    (),
    ((3, 0), (5, 0), (4, 1), (3, 2), (5, 2)),
    ((3, 9), (5, 9), (4, 8), (3, 7), (5, 7)),
)

_bishop_pos = (
    (),
    ((2, 0), (6, 0), (0, 2), (4, 2), (9, 2), (2, 4), (6, 4)),
    ((2, 9), (6, 9), (0, 7), (4, 7), (9, 7), (2, 5), (6, 5)),
)


# -----------------------------------------------------#
def abs_diff(x, y):
    """返回两点坐标在各维度上的绝对差值元组。"""
    return (abs(x[0] - y[0]), abs(x[1] - y[1]))


def middle_p(x, y):
    """返回两点坐标的中点位置（整数除法）。"""
    return ((x[0] + y[0]) // 2, (x[1] + y[1]) // 2)


# -----------------------------------------------------#
class Piece:
    """棋子基类，封装棋子在棋盘上的位置、类型与颜色等通用属性。"""

    def __init__(self, board, fench, pos):
        """初始化棋子，记录所属棋盘、FEN字符、种类与颜色及坐标。"""
        self.board = board
        self.fench = fench
        self.species, self.color = fench_to_species(fench)
        self.x, self.y = pos

    def is_valid_pos(self, pos):
        """判断给定坐标是否在棋盘范围内。"""
        return (0 <= pos[0] < 9) and (0 <= pos[1] <= 9)

    def is_valid_move(self, pos_to):  # pylint: disable=unused-argument
        """判断移动到目标位置是否合法（基类默认返回 True）。"""
        return True

    def get_color_fench(self):
        """返回带颜色前缀的棋子标识字符串（如 'rk'、'bK'）。"""
        if self.fench.islower():
            return f"b{self.fench}"
        return f"r{self.fench.lower()}"

    @staticmethod
    def create(board, fench, pos):
        """根据棋子类型字符创建并返回对应的棋子实例。"""
        p_type = fench.lower()
        if p_type == "k":
            return King(board, fench, pos)
        if p_type == "a":
            return Advisor(board, fench, pos)
        if p_type == "b":
            return Bishop(board, fench, pos)
        if p_type == "r":
            return Rook(board, fench, pos)
        if p_type == "c":
            return Cannon(board, fench, pos)
        if p_type == "n":
            return Knight(board, fench, pos)
        if p_type == "p":
            return Pawn(board, fench, pos)
        return None


# -----------------------------------------------------#
# 王
class King(Piece):
    """将/帅棋子，只能在九宫格内移动。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内。"""
        if not super().is_valid_pos(pos):
            return False

        if pos[0] < 3 or pos[0] > 5:
            return False

        if (self.color == RED) and (pos[1] > 2):
            return False

        if (self.color == BLACK) and (pos[1] < 7):
            return False

        return True

    def is_valid_move(self, pos_to):
        """判断将/帅移动到目标位置是否合法（含白脸将规则）。"""
        k2 = self.board.get_king(opposite_color(self.color))
        if k2 is not None:
            if (
                (self.x == k2.x)
                and (pos_to[1] == k2.y)
                and (self.board.count_y_line_in(self.x, self.y, k2.y) == 0)
            ):
                return True

        if not self.is_valid_pos(pos_to):
            return False

        diff = abs_diff(pos_to, (self.x, self.y))

        return (diff[0] + diff[1]) == 1

    def create_moves(self):
        """生成将/帅所有可能的合法走子。"""
        positions = [
            (self.x + 1, self.y),
            (self.x - 1, self.y),
            (self.x, self.y + 1),
            (self.x, self.y - 1),
        ]

        k2 = self.board.get_king(opposite_color(self.color))
        if k2 is not None:
            positions.append((k2.x, k2.y))

        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in positions]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 士
class Advisor(Piece):
    """士/仕棋子，只能在九宫格内斜走。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内的士位上。"""
        if not super().is_valid_pos(pos):
            return False
        return pos in _advisor_pos[self.color]

    def is_valid_move(self, pos_to):
        """判断士/仕斜走一步到目标位置是否合法。"""
        if not self.is_valid_pos(pos_to):
            return False

        if abs_diff((self.x, self.y), pos_to) == (1, 1):
            return True

        return False

    def create_moves(self):
        """生成士/仕所有可能的合法走子。"""
        positions = [
            (self.x + 1, self.y + 1),
            (self.x + 1, self.y - 1),
            (self.x - 1, self.y + 1),
            (self.x - 1, self.y - 1),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in positions]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 象
class Bishop(Piece):
    """象/相棋子，走田字，不能过河。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方半场内的象位上。"""
        if not super().is_valid_pos(pos):
            return False

        return pos in _bishop_pos[self.color]

    def is_valid_move(self, pos_to):
        """判断象/相走田字到目标位置是否合法（含塞象眼和过河检查）。"""
        if abs_diff((self.x, self.y), (pos_to)) != (2, 2):
            return False

        if self.board.get_fench(middle_p((self.x, self.y), pos_to)) is not None:
            return False

        if (self.color == RED) and (pos_to[1] > 4):
            return False
        if (self.color == BLACK) and (pos_to[1] < 5):
            return False

        return True

    def create_moves(self):
        """生成象/相所有可能的合法走子。"""
        positions = [
            (self.x + 2, self.y + 2),
            (self.x + 2, self.y - 2),
            (self.x - 2, self.y + 2),
            (self.x - 2, self.y - 2),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in positions]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 马
class Knight(Piece):
    """马棋子，走日字，有蹩马腿限制。"""

    def is_valid_move(self, pos_to):
        """判断马走日字到目标位置是否合法（含蹩马腿检查）。"""
        if (abs(self.x - pos_to[0]) == 2) and (abs(self.y - pos_to[1]) == 1):
            m_x = (self.x + pos_to[0]) // 2
            m_y = self.y

            return self.board.get_fench((m_x, m_y)) is None

        if (abs(self.x - pos_to[0]) == 1) and (abs(self.y - pos_to[1]) == 2):
            m_x = self.x
            m_y = (self.y + pos_to[1]) // 2
            return self.board.get_fench((m_x, m_y)) is None
        return False

    def create_moves(self):
        """生成马所有可能的合法走子。"""
        positions = [
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
        moves = [(curr_pos, to_pos) for to_pos in positions]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 车
class Rook(Piece):
    """车棋子，沿直线行走，不能越子。"""

    def is_valid_move(self, pos_to):
        """判断车直线移动到目标位置是否合法（不能越子）。"""
        if self.x != pos_to[0]:
            if self.y != pos_to[1]:
                return False

            if self.board.count_x_line_in(self.y, self.x, pos_to[0]) == 0:
                return True

        else:
            if self.board.count_y_line_in(self.x, self.y, pos_to[1]) == 0:
                return True

        return False

    def create_moves(self):
        """生成车所有可能的合法走子。"""
        curr_pos = (self.x, self.y)
        moves = []
        # 同一行的所有位置（横向移动）
        for x in range(9):
            if x != self.x:
                moves.append((curr_pos, (x, self.y)))
        # 同一列的所有位置（纵向移动）
        for y in range(10):
            if y != self.y:
                moves.append((curr_pos, (self.x, y)))
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 炮
class Cannon(Piece):
    """炮棋子，直行不越子，吃子需隔一子（炮架）。"""

    def is_valid_move(self, pos_to):
        """判断炮移动到目标位置是否合法（直行不越子，吃子需隔一子）。"""
        if self.x != pos_to[0]:
            if self.y != pos_to[1]:
                return False

            count = self.board.count_x_line_in(self.y, self.x, pos_to[0])
            if (count == 0) and (self.board.get_fench(pos_to) is None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) is not None):
                return True
        else:
            count = self.board.count_y_line_in(self.x, self.y, pos_to[1])
            if (count == 0) and (self.board.get_fench(pos_to) is None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) is not None):
                return True

        return False

    def create_moves(self):
        """生成炮所有可能的合法走子。"""
        curr_pos = (self.x, self.y)
        moves = []
        # 同一行的所有位置（横向移动）
        for x in range(9):
            if x != self.x:
                moves.append((curr_pos, (x, self.y)))
        # 同一列的所有位置（纵向移动）
        for y in range(10):
            if y != self.y:
                moves.append((curr_pos, (self.x, y)))
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 兵/卒
class Pawn(Piece):
    """兵/卒棋子，未过河前只能前进，过河后可左右移动。"""

    def is_valid_pos(self, pos):
        """判断位置是否在兵的合法活动范围内（不能后退）。"""
        if not super().is_valid_pos(pos):
            return False

        if (self.color == RED) and pos[1] < 3:
            return False

        if (self.color == BLACK) and pos[1] > 6:
            return False

        return True

    def is_valid_move(self, pos_to):
        """判断兵/卒移动到目标位置是否合法（含过河前后规则）。"""
        not_crossed_river_step = ((), (0, 1), (0, -1))
        crossed_river_step = ((), ((-1, 0), (1, 0), (0, 1)), ((-1, 0), (1, 0), (0, -1)))

        step = (pos_to[0] - self.x, pos_to[1] - self.y)

        crossed_river = self.is_crossed_river()

        if (not crossed_river) and (step == not_crossed_river_step[self.color]):
            return True

        if crossed_river and (step in crossed_river_step[self.color]):
            return True

        return False

    def is_crossed_river(self):
        """判断兵/卒是否已经过河。"""
        if (self.color == RED) and (self.y > 4):
            return True

        if (self.color == BLACK) and (self.y < 5):
            return True

        return False

    def create_moves(self):
        """生成兵/卒所有可能的合法走子。"""
        curr_pos = (self.x, self.y)
        moves = []
        # 前进方向
        if self.color == RED:
            forward = (self.x, self.y + 1)
        else:  # BLACK
            forward = (self.x, self.y - 1)
        # 检查前进位置是否在棋盘范围内
        if 0 <= forward[0] < 9 and 0 <= forward[1] <= 9:
            moves.append((curr_pos, forward))

        # 如果已经过河，可以左右移动
        if self.is_crossed_river():
            left = (self.x - 1, self.y)
            right = (self.x + 1, self.y)
            if 0 <= left[0] < 9:
                moves.append((curr_pos, left))
            if 0 <= right[0] < 9:
                moves.append((curr_pos, right))

        return filter(self.board.is_valid_move_t, moves)
