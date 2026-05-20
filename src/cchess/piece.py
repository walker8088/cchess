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

中国象棋棋子模块

提供棋子走法生成、合法性检查、中文走法解析等功能。

设计架构：
- 使用函数式 API 替代类层次结构
- 通过分发表（dispatch dict）根据棋子类型路由
- 性能优化：减少对象创建开销，直接操作棋盘数组

主要函数：
- is_valid_pos(): 检查棋子位置合法性
- is_valid_move(): 检查走法合法性
- create_moves(): 生成所有合法走法
- text_move_to_pos(): 解析中文走法
"""

from __future__ import annotations

from .common import (
    SIDE_BLACK,
    SIDE_RED,
    _get_target_x,
    _get_v_index,
    get_fench_color,
    next_side,
)

# -----------------------------------------------------#
# 按棋子类型分组的常量（优化 7：提高内聚）
# -----------------------------------------------------#
_PIECE_CONSTANTS = {
    "k": {
        "palace_x": (3, 5),
        "palace_y": {SIDE_RED: (0, 2), SIDE_BLACK: (7, 9)},
    },
    "a": {
        "positions": {
            SIDE_RED: frozenset(((3, 0), (5, 0), (4, 1), (3, 2), (5, 2))),
            SIDE_BLACK: frozenset(((3, 9), (5, 9), (4, 8), (3, 7), (5, 7))),
        },
    },
    "b": {
        "positions": {
            SIDE_RED: frozenset(((2, 0), (6, 0), (0, 2), (4, 2), (2, 4), (6, 4))),
            SIDE_BLACK: frozenset(((2, 9), (6, 9), (0, 7), (4, 7), (2, 5), (6, 5))),
        },
        "y_range": {SIDE_RED: (0, 4), SIDE_BLACK: (5, 9)},
    },
    "p": {
        "dy": {SIDE_RED: 1, SIDE_BLACK: -1},
        "river_y": {SIDE_RED: 5, SIDE_BLACK: 4},
        "y_range": {SIDE_RED: (3, 9), SIDE_BLACK: (0, 6)},
    },
}

# 通用常量
_SLIDING_DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))
_KNIGHT_MOVES = (
    ((1, 2), (0, 1)),
    ((1, -2), (0, -1)),
    ((-1, 2), (0, 1)),
    ((-1, -2), (0, -1)),
    ((2, 1), (1, 0)),
    ((2, -1), (1, 0)),
    ((-2, 1), (-1, 0)),
    ((-2, -1), (-1, 0)),
)


# -----------------------------------------------------#
# 内部辅助函数（纯函数，无外部依赖）
# -----------------------------------------------------#
def _is_on_board(pos):
    """检查坐标是否在棋盘范围内。"""
    return 0 <= pos[0] <= 8 and 0 <= pos[1] <= 9


def _is_enemy_fench(fench_from, fench_to):
    """判断目标棋子是否为敌方。"""
    if fench_to is None:
        return False
    color_from = get_fench_color(fench_from)
    return fench_to.isupper() != (color_from == SIDE_RED)


def _abs_diff(x, y):
    """返回两点坐标在各维度上的绝对差值元组。"""
    return (abs(x[0] - y[0]), abs(x[1] - y[1]))


def _linear_piece_move(pos_from, move_str):
    """解析王、车、炮、兵的走法（直线移动）。"""
    if move_str[0] == "平":
        new_x = _get_target_x(move_str[1])
        return (new_x, pos_from[1]) if new_x is not None else None

    step_digit = move_str[1:].strip()
    diff = _get_v_index(step_digit)
    if diff is None:
        return None
    if move_str[0] == "退":
        diff = -diff
    return (pos_from[0], pos_from[1] + diff)


# =====================================================
# 向后兼容层（Piece 类层次结构）
# 注意：这些类仅用于向后兼容，建议使用函数式 API
# =====================================================


class Piece:
    """棋子基类（向后兼容，建议使用函数式 API）。"""

    __slots__ = ["board", "fench", "color", "x", "y"]

    def __init__(self, board, fench, pos):
        """初始化棋子。"""
        self.board = board
        self.fench = fench
        self.color = get_fench_color(fench)
        self.x, self.y = pos

    def is_valid_pos(self, pos):
        """判断给定坐标是否在棋盘范围内。"""
        return _is_on_board(pos)

    def is_valid_move(self, pos_to):
        """判断移动到目标位置是否合法。"""
        return is_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    def get_color_fench(self):
        """返回带颜色前缀的棋子标识字符串。"""
        if self.fench.islower():
            return f"b{self.fench}"
        return f"r{self.fench.lower()}"

    def is_enemy_piece(self, target_fench):
        """判断目标棋子是否为敌方。"""
        return _is_enemy_fench(self.fench, target_fench)

    def _create_moves_from_offsets(self, offsets):
        """从偏移量列表生成候选走子。"""
        curr_pos = (self.x, self.y)
        moves = []
        for dx, dy in offsets:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx <= 8 and 0 <= ny <= 9:
                moves.append((curr_pos, (nx, ny)))
        return filter(self.board.is_valid_move_t, moves)

    def _create_sliding_moves(self, directions):
        """生成滑走棋子的走法。"""
        return _create_sliding_moves(
            self.board, self.fench, (self.x, self.y), directions
        )

    def _is_on_straight_line(self, pos_to):
        """判断目标位置是否与当前位置在同一直线上。"""
        return (self.x == pos_to[0]) or (self.y == pos_to[1])

    def _count_line_pieces(self, pos_to):
        """计算当前位置到目标位置直线上的棋子数量。"""
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

    def create_moves(self):
        """生成所有合法走法（向后兼容方法）。"""
        return create_moves(self.board, self.fench, (self.x, self.y))


# -----------------------------------------------------#
# 向后兼容的棋子子类
# -----------------------------------------------------#


class King(Piece):
    """将/帅棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        return _king_valid_pos(self.fench, pos)

    def is_valid_move(self, pos_to):
        return _king_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _linear_piece_move(pos_from, move_str)


class Advisor(Piece):
    """士/仕棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        return _advisor_valid_pos(self.fench, pos)

    def is_valid_move(self, pos_to):
        return _advisor_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _advisor_text_move_to_pos(pos_from, move_str)


class Bishop(Piece):
    """象/相棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        return _bishop_valid_pos(self.fench, pos)

    def is_valid_move(self, pos_to):
        return _bishop_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _bishop_text_move_to_pos(pos_from, move_str)


class Knight(Piece):
    """马棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        return _knight_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _knight_text_move_to_pos(pos_from, move_str)


class Rook(Piece):
    """车棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        return _rook_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _linear_piece_move(pos_from, move_str)


class Cannon(Piece):
    """炮棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_move(self, pos_to):
        return _cannon_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _linear_piece_move(pos_from, move_str)


class Pawn(Piece):
    """兵/卒棋子（向后兼容）。"""

    __slots__ = ()

    def is_valid_pos(self, pos):
        return _pawn_valid_pos(self.fench, pos)

    def is_valid_move(self, pos_to):
        return _pawn_valid_move(self.board, self.fench, (self.x, self.y), pos_to)

    def is_crossed_river(self):
        return _crossed_river(self.fench, (self.x, self.y))

    @staticmethod
    def text_move_to_pos(pos_from, move_str):
        return _linear_piece_move(pos_from, move_str)


# =====================================================
# 各棋子的核心实现函数（按类型分组）
# =====================================================


# --- 王 ---
def _king_valid_pos(fench, pos):
    if not _is_on_board(pos):
        return False
    color = get_fench_color(fench)
    cfg = _PIECE_CONSTANTS["k"]
    min_x, max_x = cfg["palace_x"]
    min_y, max_y = cfg["palace_y"][color]
    return min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y


def _king_valid_move(board, fench, pos_from, pos_to):
    color = get_fench_color(fench)
    k2_pos = board.get_king_pos(next_side(color))
    if k2_pos is not None:
        if pos_from[0] == k2_pos[0] and pos_to[1] == k2_pos[1]:
            if board.count_y_line_in(pos_from[0], pos_from[1], k2_pos[1]) == 0:
                return True
    if not _king_valid_pos(fench, pos_to):
        return False
    diff = _abs_diff(pos_from, pos_to)
    return (diff[0] + diff[1]) == 1


def _king_create_moves(board, fench, pos):
    x, y = pos
    color = get_fench_color(fench)
    positions = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    k2_pos = board.get_king_pos(next_side(color))
    if k2_pos is not None:
        positions.append(k2_pos)
    curr_pos = (x, y)
    return (
        (curr_pos, to_pos)
        for to_pos in positions
        if board.is_valid_move_t((curr_pos, to_pos))
    )


# --- 士 ---
def _advisor_valid_pos(fench, pos):
    if not _is_on_board(pos):
        return False
    return pos in _PIECE_CONSTANTS["a"]["positions"][get_fench_color(fench)]


def _advisor_valid_move(board, fench, pos_from, pos_to):
    if not _advisor_valid_pos(fench, pos_to):
        return False
    return _abs_diff(pos_from, pos_to) == (1, 1)


def _advisor_create_moves(board, fench, pos):
    x, y = pos
    curr_pos = (x, y)
    moves = []
    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx <= 8 and 0 <= ny <= 9:
            moves.append((curr_pos, (nx, ny)))
    return filter(board.is_valid_move_t, moves)


def _advisor_text_move_to_pos(pos_from, move_str):
    direction = move_str[0]
    target_digit = move_str[1:].strip()
    new_x = _get_target_x(target_digit)
    if new_x is None or abs(new_x - pos_from[0]) != 1:
        return None
    diff_y = 1 if direction == "进" else -1
    return (new_x, pos_from[1] + diff_y)


# --- 象 ---
def _bishop_valid_pos(fench, pos):
    if not _is_on_board(pos):
        return False
    return pos in _PIECE_CONSTANTS["b"]["positions"][get_fench_color(fench)]


def _bishop_valid_move(board, fench, pos_from, pos_to):
    if _abs_diff(pos_from, pos_to) != (2, 2):
        return False
    eye_x = (pos_from[0] + pos_to[0]) // 2
    eye_y = (pos_from[1] + pos_to[1]) // 2
    if board.get_fench((eye_x, eye_y)) is not None:
        return False
    color = get_fench_color(fench)
    min_y, max_y = _PIECE_CONSTANTS["b"]["y_range"][color]
    return min_y <= pos_to[1] <= max_y


def _bishop_create_moves(board, fench, pos):
    x, y = pos
    curr_pos = (x, y)
    moves = []
    for dx, dy in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx <= 8 and 0 <= ny <= 9:
            moves.append((curr_pos, (nx, ny)))
    return filter(board.is_valid_move_t, moves)


def _bishop_text_move_to_pos(pos_from, move_str):
    direction = move_str[0]
    target_digit = move_str[1:].strip()
    new_x = _get_target_x(target_digit)
    if new_x is None or abs(new_x - pos_from[0]) != 2:
        return None
    diff_y = 2 if direction == "进" else -2
    return (new_x, pos_from[1] + diff_y)


# --- 马 ---
def _knight_valid_move(board, fench, pos_from, pos_to):
    for (dx, dy), (bx, by) in _KNIGHT_MOVES:
        if pos_from[0] + dx == pos_to[0] and pos_from[1] + dy == pos_to[1]:
            return board.get_fench((pos_from[0] + bx, pos_from[1] + by)) is None
    return False


def _knight_create_moves(board, fench, pos):
    x, y = pos
    color = get_fench_color(fench)
    board_arr = board._board
    curr_pos = (x, y)
    moves = []
    for (dx, dy), (bx, by) in _KNIGHT_MOVES:
        nx, ny = x + dx, y + dy
        if not (0 <= nx <= 8 and 0 <= ny <= 9):
            continue
        if board_arr[y + by][x + bx] is not None:
            continue
        target_fench = board_arr[ny][nx]
        if target_fench is not None and target_fench.isupper() == (color == SIDE_RED):
            continue
        moves.append((curr_pos, (nx, ny)))
    return moves


def _knight_text_move_to_pos(pos_from, move_str):
    direction = move_str[0]
    target_digit = move_str[1:].strip()
    new_x = _get_target_x(target_digit)
    if new_x is None:
        return None
    diff_x = abs(pos_from[0] - new_x)
    if diff_x not in (1, 2):
        return None
    diff_y_magnitude = 2 if diff_x == 1 else 1
    diff_y = diff_y_magnitude if direction == "进" else -diff_y_magnitude
    return (new_x, pos_from[1] + diff_y)


# --- 车 ---
def _rook_valid_move(board, fench, pos_from, pos_to):
    if pos_from[0] != pos_to[0] and pos_from[1] != pos_to[1]:
        return False
    if pos_from[0] != pos_to[0]:
        return board.count_x_line_in(pos_from[1], pos_from[0], pos_to[0]) == 0
    return board.count_y_line_in(pos_from[0], pos_from[1], pos_to[1]) == 0


# --- 炮 ---
def _cannon_valid_move(board, fench, pos_from, pos_to):
    if pos_from[0] != pos_to[0] and pos_from[1] != pos_to[1]:
        return False
    if pos_from[0] != pos_to[0]:
        count = board.count_x_line_in(pos_from[1], pos_from[0], pos_to[0])
    else:
        count = board.count_y_line_in(pos_from[0], pos_from[1], pos_to[1])
    target = board.get_fench(pos_to)
    return (count == 0 and target is None) or (count == 1 and target is not None)


# --- 兵 ---
def _pawn_valid_pos(fench, pos):
    if not _is_on_board(pos):
        return False
    color = get_fench_color(fench)
    min_y, max_y = _PIECE_CONSTANTS["p"]["y_range"][color]
    return min_y <= pos[1] <= max_y


def _crossed_river(fench, pos):
    color = get_fench_color(fench)
    limit = _PIECE_CONSTANTS["p"]["river_y"][color]
    return pos[1] >= limit if color == SIDE_RED else pos[1] <= limit


def _pawn_valid_move(board, fench, pos_from, pos_to):
    step = (pos_to[0] - pos_from[0], pos_to[1] - pos_from[1])
    crossed = _crossed_river(fench, pos_from)
    color = get_fench_color(fench)
    forward_step = (0, _PIECE_CONSTANTS["p"]["dy"][color])
    if not crossed and step == forward_step:
        return True
    if crossed and (step == forward_step or step in ((-1, 0), (1, 0))):
        return True
    return False


# =====================================================
# 滑走棋子通用逻辑（优化 6：提取通用逻辑）
# =====================================================
def _create_sliding_moves(board, fench, pos, directions, is_cannon=False):
    x, y = pos
    board_arr = board._board
    curr_pos = (x, y)
    moves = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        screen_found = False
        while 0 <= nx <= 8 and 0 <= ny <= 9:
            target = board_arr[ny][nx]
            if not is_cannon:
                if target is None:
                    moves.append((curr_pos, (nx, ny)))
                else:
                    if _is_enemy_fench(fench, target):
                        moves.append((curr_pos, (nx, ny)))
                    break
            else:
                if not screen_found:
                    if target is None:
                        moves.append((curr_pos, (nx, ny)))
                    else:
                        screen_found = True
                else:
                    if target is not None:
                        if _is_enemy_fench(fench, target):
                            moves.append((curr_pos, (nx, ny)))
                        break
            nx += dx
            ny += dy
    return moves


def _rook_create_moves(board, fench, pos):
    return _create_sliding_moves(
        board, fench, pos, _SLIDING_DIRECTIONS, is_cannon=False
    )


def _cannon_create_moves(board, fench, pos):
    return _create_sliding_moves(board, fench, pos, _SLIDING_DIRECTIONS, is_cannon=True)


def _pawn_create_moves(board, fench, pos):
    x, y = pos
    color = get_fench_color(fench)
    curr_pos = (x, y)
    moves = []
    dy = _PIECE_CONSTANTS["p"]["dy"][color]
    forward = (x, y + dy)
    if 0 <= forward[1] <= 9:
        moves.append((curr_pos, forward))
    if _crossed_river(fench, pos):
        lx, rx = x - 1, x + 1
        if lx >= 0:
            moves.append((curr_pos, (lx, y)))
        if rx <= 8:
            moves.append((curr_pos, (rx, y)))
    return filter(board.is_valid_move_t, moves)


# =====================================================
# 统一分发表（优化 2：集中管理）
# =====================================================
_PIECE_RULES = {
    "k": {
        "valid_pos": _king_valid_pos,
        "valid_move": _king_valid_move,
        "create_moves": _king_create_moves,
        "text_move": _linear_piece_move,
    },
    "a": {
        "valid_pos": _advisor_valid_pos,
        "valid_move": _advisor_valid_move,
        "create_moves": _advisor_create_moves,
        "text_move": _advisor_text_move_to_pos,
    },
    "b": {
        "valid_pos": _bishop_valid_pos,
        "valid_move": _bishop_valid_move,
        "create_moves": _bishop_create_moves,
        "text_move": _bishop_text_move_to_pos,
    },
    "n": {
        "valid_move": _knight_valid_move,
        "create_moves": _knight_create_moves,
        "text_move": _knight_text_move_to_pos,
    },
    "r": {
        "valid_move": _rook_valid_move,
        "create_moves": _rook_create_moves,
        "text_move": _linear_piece_move,
    },
    "c": {
        "valid_move": _cannon_valid_move,
        "create_moves": _cannon_create_moves,
        "text_move": _linear_piece_move,
    },
    "p": {
        "valid_pos": _pawn_valid_pos,
        "valid_move": _pawn_valid_move,
        "create_moves": _pawn_create_moves,
        "text_move": _linear_piece_move,
    },
}

# 派生分发表（保持现有 API 兼容）
_VALID_POS_TABLE = {
    k: v["valid_pos"] for k, v in _PIECE_RULES.items() if "valid_pos" in v
}
_VALID_MOVE_TABLE = {k: v["valid_move"] for k, v in _PIECE_RULES.items()}
_CREATE_MOVES_TABLE = {k: v["create_moves"] for k, v in _PIECE_RULES.items()}
_TEXT_MOVE_TABLE = {k: v["text_move"] for k, v in _PIECE_RULES.items()}


# =====================================================
# 公共 API 函数
# =====================================================
def is_valid_pos(fench, pos):
    handler = _VALID_POS_TABLE.get(fench.lower())
    return handler(fench, pos) if handler else _is_on_board(pos)


def is_valid_move(board, fench, pos_from, pos_to):
    handler = _VALID_MOVE_TABLE.get(fench.lower())
    return handler(board, fench, pos_from, pos_to) if handler else False


def create_moves(board, fench, pos):
    handler = _CREATE_MOVES_TABLE.get(fench.lower())
    return handler(board, fench, pos) if handler else []


def text_move_to_pos(piece_fench, pos_from, move_str):
    handler = _TEXT_MOVE_TABLE.get(piece_fench)
    return handler(pos_from, move_str) if handler else None


# =====================================================
# 向后兼容层（委托给公共 API）
# =====================================================
