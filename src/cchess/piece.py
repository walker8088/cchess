"""Copyright (C) 2024  walker li <walker8088@gmail.com>

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

from __future__ import annotations

from .common import (
    SIDE_BLACK,
    SIDE_RED,
    _get_target_x,
    _get_v_index,
    get_fench_color,
    next_color,
)

# -----------------------------------------------------#
# 士象固定位置（红方/黑方字典）
_ADVISOR_POS = {
    SIDE_RED: frozenset(((3, 0), (5, 0), (4, 1), (3, 2), (5, 2))),
    SIDE_BLACK: frozenset(((3, 9), (5, 9), (4, 8), (3, 7), (5, 7))),
}

_BISHOP_POS = {
    SIDE_RED: frozenset(((2, 0), (6, 0), (0, 2), (4, 2), (2, 4), (6, 4))),
    SIDE_BLACK: frozenset(((2, 9), (6, 9), (0, 7), (4, 7), (2, 5), (6, 5))),
}

# 九宫格 y 范围（红方/黑方）
_PALACE_Y_RANGE = {
    SIDE_RED: (0, 2),
    SIDE_BLACK: (7, 9),
}

# 九宫格 x 范围
_PALACE_X_RANGE = (3, 5)

# 象的活动范围 y 边界（红方/黑方）
_BISHOP_Y_RANGE = {
    SIDE_RED: (0, 4),
    SIDE_BLACK: (5, 9),
}

# 兵卒相关常量（红方/黑方）
_PAWN_DY = {SIDE_RED: 1, SIDE_BLACK: -1}  # 前进步长（y 方向）
_PAWN_RIVER_Y = {SIDE_RED: 5, SIDE_BLACK: 4}  # 过河界限
_PAWN_Y_RANGE = {SIDE_RED: (3, 9), SIDE_BLACK: (0, 6)}  # 合法活动 y 范围


# 滑走棋子方向常量（车、炮）
_SLIDING_DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))

# 马棋子走法偏移量（目标偏移, 蹩腿偏移）
_KNIGHT_MOVES = (
    ((1, 2), (0, 1)),  # 右跳上：纵向2格，蹩腿在上方
    ((1, -2), (0, -1)),  # 右跳下：纵向2格，蹩腿在下方
    ((-1, 2), (0, 1)),  # 左跳上：纵向2格，蹩腿在上方
    ((-1, -2), (0, -1)),  # 左跳下：纵向2格，蹩腿在下方
    ((2, 1), (1, 0)),  # 上跳右：横向2格，蹩腿在右方
    ((2, -1), (1, 0)),  # 下跳右：横向2格，蹩腿在右方
    ((-2, 1), (-1, 0)),  # 上跳左：横向2格，蹩腿在左方
    ((-2, -1), (-1, 0)),  # 下跳左：横向2格，蹩腿在左方
)


# -----------------------------------------------------#
def abs_diff(x, y):
    """返回两点坐标在各维度上的绝对差值元组。"""
    return (abs(x[0] - y[0]), abs(x[1] - y[1]))


def _linear_piece_move(pos_from, move_str):
    """解析王、车、炮、兵的走法（直线移动）。

    参数:
        pos_from: 起点坐标
        move_str: 走法字符串（如'进一'、'平五'）

    返回:
        tuple: 目标坐标 (x, y)，无法解析返回 None
    """
    # 平移
    if move_str[0] == "平":
        new_x = _get_target_x(move_str[1])
        if new_x is None:
            return None
        return (new_x, pos_from[1])

    # 前进/后退
    step_digit = move_str[1:].strip()
    diff = _get_v_index(step_digit)
    if diff is None:
        return None
    if move_str[0] == "退":
        diff = -diff

    return (pos_from[0], pos_from[1] + diff)


# -----------------------------------------------------#
class Piece:
    """棋子基类，封装棋子在棋盘上的位置、类型与颜色等通用属性。"""

    __slots__ = ["board", "fench", "color", "x", "y"]

    # pylint: disable=attribute-defined-outside-init

    def __init__(self, board, fench, pos):
        """初始化棋子，记录所属棋盘、FEN 字符、颜色及坐标。"""
        self.board = board
        self.fench = fench
        self.color = get_fench_color(fench)
        self.x, self.y = pos

    def is_valid_pos(self, pos):
        """判断给定坐标是否在棋盘范围内。"""
        return (0 <= pos[0] < 9) and (0 <= pos[1] <= 9)

    def is_valid_move(self, _pos_to):
        """判断移动到目标位置是否合法（基类默认返回 True）。"""
        return True

    def get_color_fench(self):
        """返回带颜色前缀的棋子标识字符串（如 'rk'、'bK'）。"""
        if self.fench.islower():
            return f"b{self.fench}"
        return f"r{self.fench.lower()}"

    def is_enemy_piece(self, target_fench):
        """判断目标棋子是否为敌方。

        FEN 字符约定：大写表示红方棋子，小写表示黑方棋子。

        参数:
            target_fench: 目标棋子的 FEN 字符，None 表示空位

        返回:
            bool: True 如果是敌方棋子，False 如果是友方棋子或空位
        """
        if target_fench is None:
            return False
        # FEN 大写=红方，小写=黑方；目标棋子颜色与己方不同即为敌方
        return target_fench.isupper() != (self.color == SIDE_RED)

    def _create_moves_from_offsets(self, offsets):
        """从偏移量列表生成候选走子。

        参数:
            offsets: 相对当前位置的偏移量列表，如 [(1, 1), (-1, -1)]

        返回:
            过滤后的合法走子迭代器
        """
        curr_pos = (self.x, self.y)
        # 内联边界检查：0 <= x <= 8, 0 <= y <= 9
        moves = []
        for dx, dy in offsets:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx <= 8 and 0 <= ny <= 9:
                moves.append((curr_pos, (nx, ny)))
        return filter(self.board.is_valid_move_t, moves)

    def _create_sliding_moves(self, directions):
        """生成滑走棋子（车/炮不吃子时）的走法，沿方向扫描直到遇到棋子或边界。

        参数:
            directions: 方向列表，如 [(0,1), (0,-1), (1,0), (-1,0)]

        返回:
            合法走子列表
        """
        moves = []
        curr_x, curr_y = self.x, self.y
        board = self.board._board

        for dx, dy in directions:
            x, y = curr_x + dx, curr_y + dy

            # 内联边界检查：0 <= x < 9, 0 <= y <= 9
            while 0 <= x <= 8 and 0 <= y <= 9:
                target = board[y][x]

                if target is None:
                    moves.append(((curr_x, curr_y), (x, y)))
                else:
                    if self.is_enemy_piece(target):
                        moves.append(((curr_x, curr_y), (x, y)))
                    break

                x += dx
                y += dy

        return moves

    def _is_on_straight_line(self, pos_to):
        """判断目标位置是否与当前位置在同一直线上。

        参数:
            pos_to: 目标坐标 (x, y)

        返回:
            bool: True 如果在同一直线上，否则 False
        """
        return self.x == pos_to[0] or self.y == pos_to[1]

    def _count_line_pieces(self, pos_to):
        """计算当前位置到目标位置直线上的棋子数量（不含端点）。

        前提：调用者需确保 pos_to 在同一直线上。

        参数:
            pos_to: 目标坐标 (x, y)

        返回:
            int: 中间棋子数量
        """
        if self.x != pos_to[0]:
            return self.board.count_x_line_in(self.y, self.x, pos_to[0])
        return self.board.count_y_line_in(self.x, self.y, pos_to[1])

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

    __slots__ = ()

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内。"""
        if not super().is_valid_pos(pos):
            return False
        # 九宫格范围：x 见 _PALACE_X_RANGE，y 见 _PALACE_Y_RANGE
        min_x, max_x = _PALACE_X_RANGE
        min_y, max_y = _PALACE_Y_RANGE[self.color]
        return min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y

    def is_valid_move(self, pos_to):
        """判断将/帅移动到目标位置是否合法（含白脸将规则）。"""
        k2 = self.board.get_king(next_color(self.color))
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

        k2 = self.board.get_king(next_color(self.color))
        if k2 is not None:
            positions.append((k2.x, k2.y))

        curr_pos = (self.x, self.y)
        return (
            (curr_pos, to_pos)
            for to_pos in positions
            if self.board.is_valid_move_t((curr_pos, to_pos))
        )

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算将/帅目标坐标。

        参数:
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进一'、'平五'）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        # 将/帅走法同车、炮、兵：使用通用解析逻辑
        if move_str[0] == "平":
            new_x = _get_target_x(move_str[1])
            if new_x is None:
                return None
            return (new_x, pos_from[1])

        step_digit = move_str[1:].strip()
        diff = _get_v_index(step_digit)
        if diff is None:
            return None
        if move_str[0] == "退":
            diff = -diff
        return (pos_from[0], pos_from[1] + diff)


# -----------------------------------------------------#
# 士
class Advisor(Piece):
    """士/仕棋子，只能在九宫格内斜走。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内的士位上。"""
        if not super().is_valid_pos(pos):
            return False
        return pos in _ADVISOR_POS[self.color]

    def is_valid_move(self, pos_to):
        """判断士/仕斜走一步到目标位置是否合法。"""
        if not self.is_valid_pos(pos_to):
            return False

        if abs_diff((self.x, self.y), pos_to) == (1, 1):
            return True

        return False

    def create_moves(self):
        """生成士/仕所有可能的合法走子。"""
        return self._create_moves_from_offsets([(1, 1), (1, -1), (-1, 1), (-1, -1)])

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算士/仕目标坐标。

        参数:
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进 6'、'退 3'）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        direction = move_str[0]
        target_digit = move_str[1:].strip()

        new_x = _get_target_x(target_digit)
        if new_x is None:
            return None

        if abs(new_x - pos_from[0]) != 1:
            return None

        # 规范局面下（红方视角）：进 = y增加，退 = y减少
        diff_y = 1 if direction == "进" else -1

        return (new_x, pos_from[1] + diff_y)


# -----------------------------------------------------#
# 象
class Bishop(Piece):
    """象/相棋子，走田字，不能过河。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        """判断位置是否在己方半场内的象位上。"""
        if not super().is_valid_pos(pos):
            return False

        return pos in _BISHOP_POS[self.color]

    def is_valid_move(self, pos_to):
        """判断象/相走田字到目标位置是否合法（含塞象眼和过河检查）。"""
        if abs_diff((self.x, self.y), (pos_to)) != (2, 2):
            return False

        # 塞象眼：田字中心位置
        eye_x = (self.x + pos_to[0]) // 2
        eye_y = (self.y + pos_to[1]) // 2
        if self.board.get_fench((eye_x, eye_y)) is not None:
            return False

        # 象不能过河：y 范围见 _BISHOP_Y_RANGE
        min_y, max_y = _BISHOP_Y_RANGE[self.color]
        return min_y <= pos_to[1] <= max_y

    def create_moves(self):
        """生成象/相所有可能的合法走子。"""
        return self._create_moves_from_offsets([(2, 2), (2, -2), (-2, 2), (-2, -2)])

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算象/相目标坐标。

        参数:
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进 5'、'退 3'）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        direction = move_str[0]
        target_digit = move_str[1:].strip()

        new_x = _get_target_x(target_digit)
        if new_x is None:
            return None

        if abs(new_x - pos_from[0]) != 2:
            return None

        # 规范局面下（红方视角）：进 = y增加，退 = y减少
        diff_y = 2 if direction == "进" else -2

        return (new_x, pos_from[1] + diff_y)


# -----------------------------------------------------#
# 马
class Knight(Piece):
    """马棋子，走日字，有蹩马腿限制。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断马走日字到目标位置是否合法（含蹩马腿检查）。"""
        for (dx, dy), (bx, by) in _KNIGHT_MOVES:
            if self.x + dx == pos_to[0] and self.y + dy == pos_to[1]:
                # 目标位置匹配，检查蹩马腿
                return self.board.get_fench((self.x + bx, self.y + by)) is None
        return False

    def create_moves(self):
        """生成马所有可能的合法走子。

        使用预计算的偏移量，减少运行时计算。
        """

        curr_pos = (self.x, self.y)
        board = self.board._board  # 直接访问棋盘数组
        moves = []

        for (dx, dy), (bx, by) in _KNIGHT_MOVES:
            nx, ny = self.x + dx, self.y + dy

            # 快速边界检查
            if not (0 <= nx <= 8 and 0 <= ny <= 9):
                continue

            # 检查蹩马腿
            if board[self.y + by][self.x + bx] is not None:
                continue

            # 检查目标位置
            target_fench = board[ny][nx]
            if target_fench is not None:
                # 快速同色判断：FEN 大写=红方，小写=黑方
                if target_fench.isupper() == (self.color == SIDE_RED):
                    continue  # 同色棋子，跳过

            moves.append((curr_pos, (nx, ny)))

        return moves

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算马目标坐标。

        参数:
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进 5'、'退 3'）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        direction = move_str[0]
        target_digit = move_str[1:].strip()

        new_x = _get_target_x(target_digit)
        if new_x is None:
            return None

        diff_x = abs(pos_from[0] - new_x)

        if diff_x not in (1, 2):
            return None

        diff_y_magnitude = 2 if diff_x == 1 else 1

        # 规范局面下（红方视角）：进 = y增加，退 = y减少
        diff_y = diff_y_magnitude if direction == "进" else -diff_y_magnitude

        return (new_x, pos_from[1] + diff_y)


# -----------------------------------------------------#
# 车
class Rook(Piece):
    """车棋子，沿直线行走，不能越子。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断车直线移动到目标位置是否合法（不能越子）。"""
        if not self._is_on_straight_line(pos_to):
            return False
        return self._count_line_pieces(pos_to) == 0

    def create_moves(self):
        """生成车所有可能的合法走子。"""
        return self._create_sliding_moves(_SLIDING_DIRECTIONS)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算车目标坐标。

        参数:
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进一'、'平五'）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        return _linear_piece_move(pos_from, move_str)


# -----------------------------------------------------#
# 炮
class Cannon(Piece):
    """炮棋子，直行不越子，吃子需隔一子（炮架）。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断炮移动到目标位置是否合法（直行不越子，吃子需隔一子）。"""
        if not self._is_on_straight_line(pos_to):
            return False

        count = self._count_line_pieces(pos_to)
        target = self.board.get_fench(pos_to)
        # 不吃子：中间无障碍
        if count == 0 and target is None:
            return True
        # 吃子：中间恰好隔一个棋子
        if count == 1 and target is not None:
            return True

        return False

    def create_moves(self):
        """生成炮所有可能的合法走子。

        炮的走法规则：
        1. 不吃子时：沿直线行走，不能越子（同车）
        2. 吃子时：必须隔一个棋子（炮架）才能吃
        """
        moves = []
        curr_x, curr_y = self.x, self.y

        for dx, dy in _SLIDING_DIRECTIONS:
            x, y = curr_x + dx, curr_y + dy
            screen_found = False  # 是否找到炮架

            while self.is_valid_pos((x, y)):
                target = self.board._board[y][x]

                if not screen_found:
                    # 寻找炮架阶段
                    if target is None:
                        # 空位，可以移动
                        moves.append(((curr_x, curr_y), (x, y)))
                    else:
                        # 遇到第一个棋子，作为炮架
                        screen_found = True
                else:
                    # 炮架后阶段
                    if target is not None:
                        if self.is_enemy_piece(target):
                            moves.append(((curr_x, curr_y), (x, y)))
                        # 无论是否吃子，都停止扫描
                        break

                x += dx
                y += dy

        return moves

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算炮目标坐标。"""
        return _linear_piece_move(pos_from, move_str)


# -----------------------------------------------------#
# 兵/卒
class Pawn(Piece):
    """兵/卒棋子，未过河前只能前进，过河后可左右移动。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        """判断位置是否在兵的合法活动范围内（不能后退）。"""
        if not super().is_valid_pos(pos):
            return False
        # 兵不能后退：y 范围见 _PAWN_Y_RANGE
        min_y, max_y = _PAWN_Y_RANGE[self.color]
        return min_y <= pos[1] <= max_y

    def is_valid_move(self, pos_to):
        """判断兵/卒移动到目标位置是否合法（含过河前后规则）。"""
        step = (pos_to[0] - self.x, pos_to[1] - self.y)
        crossed_river = self.is_crossed_river()

        # 前进方向：见 _PAWN_DY
        forward_step = (0, _PAWN_DY[self.color])
        if not crossed_river and step == forward_step:
            return True

        # 过河后可前进或左右移动
        if crossed_river:
            side_steps = ((-1, 0), (1, 0))
            if step == forward_step or step in side_steps:
                return True

        return False

    def is_crossed_river(self):
        """判断兵/卒是否已经过河。"""
        limit = _PAWN_RIVER_Y[self.color]
        return self.y >= limit if self.color == SIDE_RED else self.y <= limit

    def create_moves(self):
        """生成兵/卒所有可能的合法走子。"""
        curr_pos = (self.x, self.y)
        moves = []
        # 前进方向：见 _PAWN_DY
        dy = _PAWN_DY[self.color]
        forward = (self.x, self.y + dy)
        # 快速边界检查（y 范围 0-9）
        if 0 <= forward[1] <= 9:
            moves.append((curr_pos, forward))

        # 过河后可左右移动
        if self.is_crossed_river():
            # 左右移动，x 范围 0-8
            lx, rx = self.x - 1, self.x + 1
            if lx >= 0:
                moves.append((curr_pos, (lx, self.y)))
            if rx <= 8:
                moves.append((curr_pos, (rx, self.y)))

        return filter(self.board.is_valid_move_t, moves)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        """从中文走法片段计算兵/卒目标坐标。"""
        return _linear_piece_move(pos_from, move_str)
