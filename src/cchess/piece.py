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
    get_fench_color,
    is_enemy_fench,
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


def _abs_diff(x, y):
    """返回两点坐标在各维度上的绝对差值元组。"""
    return (abs(x[0] - y[0]), abs(x[1] - y[1]))


def _linear_piece_move(pos_from, direction, distance):
    """解析王、车、炮、兵的走法（直线移动）。

    参数:
        pos_from: 起点坐标
        direction: WXF 方向符号 ("+", "-", "=")
        distance: 距离/目标列（整数）

    返回:
        tuple: 目标坐标 (x, y)，无法解析返回 None
    """
    if direction == "=":
        return (distance, pos_from[1])
    dy = distance if direction == "+" else -distance
    return (pos_from[0], pos_from[1] + dy)


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


def _advisor_text_move_to_pos(pos_from, direction, distance):
    if abs(distance - pos_from[0]) != 1:
        return None
    diff_y = 1 if direction == "+" else -1
    return (distance, pos_from[1] + diff_y)


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
    if board.get_fench((eye_x, eye_y)) != ".":
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


def _bishop_text_move_to_pos(pos_from, direction, distance):
    if abs(distance - pos_from[0]) != 2:
        return None
    diff_y = 2 if direction == "+" else -2
    return (distance, pos_from[1] + diff_y)


# --- 马 ---
def _knight_valid_move(board, fench, pos_from, pos_to):
    for (dx, dy), (bx, by) in _KNIGHT_MOVES:
        if pos_from[0] + dx == pos_to[0] and pos_from[1] + dy == pos_to[1]:
            return board.get_fench((pos_from[0] + bx, pos_from[1] + by)) == "."
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
        if board_arr[y + by][x + bx] != ".":
            continue
        target_fench = board_arr[ny][nx]
        if target_fench != "." and target_fench.isupper() == (color == SIDE_RED):
            continue
        moves.append((curr_pos, (nx, ny)))
    return moves


def _knight_text_move_to_pos(pos_from, direction, distance):
    diff_x = abs(pos_from[0] - distance)
    if diff_x not in (1, 2):
        return None
    diff_y_magnitude = 2 if diff_x == 1 else 1
    diff_y = diff_y_magnitude if direction == "+" else -diff_y_magnitude
    return (distance, pos_from[1] + diff_y)


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
    return (count == 0 and target == ".") or (count == 1 and target != ".")


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
                if target == ".":
                    moves.append((curr_pos, (nx, ny)))
                else:
                    if is_enemy_fench(fench, target):
                        moves.append((curr_pos, (nx, ny)))
                    break
            else:
                if not screen_found:
                    if target == ".":
                        moves.append((curr_pos, (nx, ny)))
                    else:
                        screen_found = True
                else:
                    if target != ".":
                        if is_enemy_fench(fench, target):
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


# 公共 API 函数（直接查询 _PIECE_RULES，消除派生表）
def is_valid_pos(fench, pos):
    rules = _PIECE_RULES.get(fench.lower())
    return (
        rules["valid_pos"](fench, pos)
        if rules and "valid_pos" in rules
        else _is_on_board(pos)
    )


def is_valid_move(board, fench, pos_from, pos_to):
    rules = _PIECE_RULES.get(fench.lower())
    return rules["valid_move"](board, fench, pos_from, pos_to) if rules else False


def create_moves(board, fench, pos):
    rules = _PIECE_RULES.get(fench.lower())
    return rules["create_moves"](board, fench, pos) if rules else []


def text_move_to_pos(piece_fench, pos_from, direction, distance):
    rules = _PIECE_RULES.get(piece_fench)
    return rules["text_move"](pos_from, direction, distance) if rules else None


# =====================================================
# 向后兼容层（委托给公共 API）
# =====================================================
