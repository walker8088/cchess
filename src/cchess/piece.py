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

from .common import BLACK, RED, fench_to_species, next_color

# pylint: disable=too-many-return-statements


# -----------------------------------------------------#
# 士象固定位置枚举
_advisor_pos = (
    frozenset(),
    frozenset(((3, 0), (5, 0), (4, 1), (3, 2), (5, 2))),
    frozenset(((3, 9), (5, 9), (4, 8), (3, 7), (5, 7))),
)

_bishop_pos = (
    frozenset(),
    frozenset(((2, 0), (6, 0), (0, 2), (4, 2), (2, 4), (6, 4))),
    frozenset(((2, 9), (6, 9), (0, 7), (4, 7), (2, 5), (6, 5))),
)

# 滑走棋子方向常量（车、炮）
_SLIDING_DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))

# 马棋子走法偏移量常量（8个方向）
_KNIGHT_OFFSETS = (
    (1, 2),
    (1, -2),
    (-1, 2),
    (-1, -2),
    (2, 1),
    (2, -1),
    (-2, 1),
    (-2, -1),
)

# 马棋子蹩马腿偏移量（与 _KNIGHT_OFFSETS 一一对应）
# |dx|==2 时蹩腿在横向 (±1, 0)，|dy|==2 时蹩腿在纵向 (0, ±1)
_KNIGHT_BLOCKS = (
    (0, 1),  # (1, 2): 纵向2格，蹩腿在上方
    (0, -1),  # (1, -2): 纵向2格，蹩腿在下方
    (0, 1),  # (-1, 2): 纵向2格，蹩腿在上方
    (0, -1),  # (-1, -2): 纵向2格，蹩腿在下方
    (1, 0),  # (2, 1): 横向2格，蹩腿在右方
    (1, 0),  # (2, -1): 横向2格，蹩腿在右方
    (-1, 0),  # (-2, 1): 横向2格，蹩腿在左方
    (-1, 0),  # (-2, -1): 横向2格，蹩腿在左方
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

    __slots__ = ["board", "fench", "species", "color", "x", "y"]

    def __init__(self, board, fench, pos):
        """初始化棋子，记录所属棋盘、FEN 字符、种类与颜色及坐标。"""
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

    def is_enemy_piece(self, target_fench):
        """判断目标棋子是否为敌方。

        参数:
            target_fench: 目标棋子的 FEN 字符，None 表示空位

        返回:
            bool: True 如果是敌方棋子，False 如果是友方棋子或空位
        """
        if target_fench is None:
            return False
        return (target_fench.isupper() and self.color == BLACK) or (
            target_fench.islower() and self.color == RED
        )

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

        if pos[0] < 3 or pos[0] > 5:
            return False

        if (self.color == RED) and (pos[1] > 2):
            return False

        if (self.color == BLACK) and (pos[1] < 7):
            return False

        return True

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


# -----------------------------------------------------#
# 士
class Advisor(Piece):
    """士/仕棋子，只能在九宫格内斜走。"""

    __slots__ = ()

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
        return self._create_moves_from_offsets([(1, 1), (1, -1), (-1, 1), (-1, -1)])


# -----------------------------------------------------#
# 象
class Bishop(Piece):
    """象/相棋子，走田字，不能过河。"""

    __slots__ = ()

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
        return self._create_moves_from_offsets([(2, 2), (2, -2), (-2, 2), (-2, -2)])


# -----------------------------------------------------#
# 马
class Knight(Piece):
    """马棋子，走日字，有蹩马腿限制。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断马走日字到目标位置是否合法（含蹩马腿检查）。"""
        dx = pos_to[0] - self.x
        dy = pos_to[1] - self.y

        if abs(dx) == 2 and abs(dy) == 1:
            block_x = self.x + (1 if dx > 0 else -1)
            block_y = self.y
            return self.board.get_fench((block_x, block_y)) is None

        if abs(dx) == 1 and abs(dy) == 2:
            block_x = self.x
            block_y = self.y + (1 if dy > 0 else -1)
            return self.board.get_fench((block_x, block_y)) is None

        return False

    def create_moves(self):
        """生成马所有可能的合法走子。

        使用预计算的偏移量，减少运行时计算。
        """

        curr_pos = (self.x, self.y)
        board = self.board._board  # 直接访问棋盘数组
        moves = []

        for i, (dx, dy) in enumerate(_KNIGHT_OFFSETS):
            nx, ny = self.x + dx, self.y + dy

            # 快速边界检查
            if not (0 <= nx <= 8 and 0 <= ny <= 9):
                continue

            # 检查蹩马腿
            bx, by = self.x + _KNIGHT_BLOCKS[i][0], self.y + _KNIGHT_BLOCKS[i][1]
            if board[by][bx] is not None:
                continue

            # 检查目标位置
            target_fench = board[ny][nx]
            if target_fench is not None:
                # 快速颜色判断：大写=红方，小写=黑方
                is_red = target_fench.isupper()
                if (is_red and self.color == RED) or (
                    not is_red and self.color == BLACK
                ):
                    continue

            moves.append((curr_pos, (nx, ny)))

        return moves


# -----------------------------------------------------#
# 车
class Rook(Piece):
    """车棋子，沿直线行走，不能越子。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断车直线移动到目标位置是否合法（不能越子）。"""
        # 必须在同一直线上
        if self.x != pos_to[0] and self.y != pos_to[1]:
            return False

        # 根据方向选择计数方法
        if self.x != pos_to[0]:
            return self.board.count_x_line_in(self.y, self.x, pos_to[0]) == 0
        return self.board.count_y_line_in(self.x, self.y, pos_to[1]) == 0

    def create_moves(self):
        """生成车所有可能的合法走子。"""
        return self._create_sliding_moves(_SLIDING_DIRECTIONS)


# -----------------------------------------------------#
# 炮
class Cannon(Piece):
    """炮棋子，直行不越子，吃子需隔一子（炮架）。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        """判断炮移动到目标位置是否合法（直行不越子，吃子需隔一子）。"""
        # 必须在同一直线上
        if self.x != pos_to[0] and self.y != pos_to[1]:
            return False

        # 根据方向选择计数方法
        if self.x != pos_to[0]:
            count = self.board.count_x_line_in(self.y, self.x, pos_to[0])
        else:
            count = self.board.count_y_line_in(self.x, self.y, pos_to[1])

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


# -----------------------------------------------------#
# 兵/卒
class Pawn(Piece):
    """兵/卒棋子，未过河前只能前进，过河后可左右移动。"""

    __slots__ = ()

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
        # 前进方向：红方+1，黑方-1
        dy = 1 if self.color == RED else -1
        forward = (self.x, self.y + dy)
        # 快速边界检查（y 范围 0-9）
        if 0 <= forward[1] <= 9:
            moves.append((curr_pos, forward))

        # 过河后可左右移动：红方 y>=5，黑方 y<=4
        crossed = (self.y >= 5) if self.color == RED else (self.y <= 4)
        if crossed:
            # 左右移动，x 范围 0-8
            lx, rx = self.x - 1, self.x + 1
            if lx >= 0:
                moves.append((curr_pos, (lx, self.y)))
            if rx <= 8:
                moves.append((curr_pos, (rx, self.y)))

        return filter(self.board.is_valid_move_t, moves)
