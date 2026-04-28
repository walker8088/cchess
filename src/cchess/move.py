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

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .common import (
    BLACK,
    RED,
    fench_to_species,
    fench_to_text,
    full2half,
    next_color,
    pos2iccs,
    swap_fench,
    text_to_fench,
)

# pylint: disable=too-many-branches,too-many-statements,too-many-locals


# -----------------------------------------------------#
@dataclass
class MoveInfo:
    """记录棋盘移动的增量状态信息，用于撤销操作"""

    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    moving_fench: str  # 移动的棋子字符
    captured_fench: Optional[str]  # 被吃棋子，None 表示无吃子
    prev_move_side: int  # 移动前走子方 (RED/BLACK/ANY_COLOR)
    next_move_side: int  # 移动后走子方 (RED/BLACK/ANY_COLOR)
    board_before: List[List[Optional[str]]]  # 移动前棋盘数组的深拷贝
    board_after: List[List[Optional[str]]]  # 移动后棋盘数组的深拷贝
    prev_attack_matrix_dirty: bool  # 移动前攻击矩阵脏标志
    next_attack_matrix_dirty: bool  # 移动后攻击矩阵脏标志


# -----------------------------------------------------#
# 数字映射字典常量
_FULLWIDTH_TO_CHINESE = {
    "０": "零",
    "１": "一",
    "２": "二",
    "３": "三",
    "４": "四",
    "５": "五",
    "６": "六",
    "７": "七",
    "８": "八",
    "９": "九",
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}
_CHINESE_TO_FULLWIDTH = {
    "零": "０",
    "一": "１",
    "二": "２",
    "三": "３",
    "四": "４",
    "五": "５",
    "六": "６",
    "七": "７",
    "八": "８",
    "九": "九",
    "前": "前",
    "中": "中",
    "后": "后",
}

# -----------------------------------------------------#
# 列索引数组：规范局面下使用红方索引（中文数字，从右到左）
# 黑方走法会先转换为规范局面（红方视角）再解析
_h_level_index = ("九", "八", "七", "六", "五", "四", "三", "二", "一")

_v_change_index = ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九")

# 中文数字到半角数字映射
_ZH_TO_HALF = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

# 半角数字到中文数字映射
_HALF_TO_ZH = (None, "一", "二", "三", "四", "五", "六", "七", "八", "九")


# -----------------------------------------------------#
class MoveNotation:
    """走法中间表示，支持多种输出格式"""

    # 棋子类型映射（简体，繁体）
    PIECE_MAP = {
        "K": ("帅", "將"),
        "k": ("将", "將"),
        "A": ("仕", "士"),
        "a": ("士", "士"),
        "B": ("相", "象"),
        "b": ("象", "象"),
        "N": ("马", "馬"),
        "n": ("马", "馬"),
        "R": ("车", "車"),
        "r": ("车", "車"),
        "C": ("炮", "砲"),
        "c": ("炮", "砲"),
        "P": ("兵", "兵"),
        "p": ("卒", "卒"),
    }

    # 反向棋子类型映射（从中文到FEN字符）
    REVERSE_PIECE_MAP = {}
    for fen_char, (simp, trad) in PIECE_MAP.items():
        REVERSE_PIECE_MAP[simp] = fen_char
        if trad != simp:  # 繁体不同时添加
            REVERSE_PIECE_MAP[trad] = fen_char

    # 中文限定词映射
    CHINESE_QUALIFIER_MAP = {
        "前": "f",
        "中": "m",
        "后": "b",
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
    }

    # 列数字映射（红方视角，从右到左）
    # 红方视角：最右边是第一路（一），最左边是第九路（九）
    COLUMN_MAP = {
        0: ("九", "９"),  # 最左边
        1: ("八", "８"),
        2: ("七", "７"),
        3: ("六", "６"),
        4: ("五", "５"),
        5: ("四", "４"),
        6: ("三", "３"),
        7: ("二", "２"),
        8: ("一", "１"),  # 最右边
    }

    # 全角数字映射（黑方使用）
    FULLWIDTH_NUM_MAP = {
        0: "９",
        1: "８",
        2: "７",
        3: "６",
        4: "５",
        5: "４",
        6: "３",
        7: "２",
        8: "１",
    }

    # 方向映射
    DIRECTION_MAP = {
        "+": ("进", "進"),
        "-": ("退", "退"),
        "=": ("平", "平"),
    }

    # 限定词映射
    QUALIFIER_MAP = {
        "f": ("前", "前"),
        "m": ("中", "中"),
        "b": ("后", "後"),
        "1": ("一", "一"),
        "2": ("二", "二"),
        "3": ("三", "三"),
        "4": ("四", "四"),
        "5": ("五", "五"),
        "6": ("六", "六"),
        "7": ("七", "七"),
        "8": ("八", "八"),
        "9": ("九", "九"),
    }

    # 反向查找：列号字符 -> 列索引 (O(1) 查找)
    _COLUMN_CHAR_TO_IDX: dict[str, int] = {}
    for idx, (chinese, fullwidth) in COLUMN_MAP.items():
        _COLUMN_CHAR_TO_IDX[chinese] = idx
        _COLUMN_CHAR_TO_IDX[fullwidth] = idx

    # 反向查找：中文数字 -> 整数 (O(1) 查找)
    _CHINESE_NUM_TO_INT: dict[str, int] = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "１": 1,
        "２": 2,
        "３": 3,
        "４": 4,
        "５": 5,
        "６": 6,
        "７": 7,
        "８": 8,
        "９": 9,
    }

    # 方向字符 -> 符号映射 (O(1) 查找)
    _DIRECTION_CHAR_TO_SYMBOL: dict[str, str] = {
        "进": "+",
        "進": "+",
        "退": "-",
        "平": "=",
    }

    def __init__(
        self,
        piece_type,
        column,
        direction,
        distance,
        qualifier="",
        is_capture=False,
        is_check=False,
        is_checkmate=False,
        piece_color=None,
    ):
        self.piece_type = piece_type  # K/A/B/N/R/C/P
        self.column = column  # 0-8（红方视角）
        self.direction = direction  # +/ -/=
        self.distance = distance  # 1-9
        self.qualifier = qualifier  # f/m/b/1/2/3/4
        self.is_capture = is_capture
        self.is_check = is_check
        self.is_checkmate = is_checkmate
        self.piece_color = piece_color  # RED/BLACK

    @classmethod
    def from_move(cls, move):
        """从Move对象创建中间表示"""
        # 获取棋子信息
        board = move.board_before()
        fench = board.get_fench(move.pos_from)
        species, color = fench_to_species(fench)

        # 确定棋子类型（大写红方，小写黑方）
        piece_type = species.upper() if color == RED else species.lower()

        # 计算列（红方视角）
        column = move.pos_from[0]
        if color == BLACK:
            # 黑方需要转换为红方视角
            column = 8 - column

        # 计算方向和目标信息
        diff = move.pos_to[1] - move.pos_from[1]
        if color == BLACK:
            diff = -diff

        if diff == 0:
            direction = "="
            # 平移动：目标列（红方视角）
            target_column = move.pos_to[0]
            if color == BLACK:
                target_column = 8 - target_column
            # 对于平移动，距离表示目标列
            distance = target_column
        else:
            direction = "+" if diff > 0 else "-"

            # 对于士、相、马，前进/后退显示的是目标列
            # 对于王、车、炮、兵，前进/后退显示的是步数
            if species in ("a", "b", "n"):  # 士、相、马
                # 目标列（红方视角）
                target_column = move.pos_to[0]
                if color == BLACK:
                    target_column = 8 - target_column
                distance = target_column
            else:  # 王、车、炮、兵
                distance = abs(diff)

        # 确定限定词
        qualifier = ""

        # 将/帅、士/仕、象/相没有限定词，无论有多少个
        if species in ("k", "a", "b"):
            qualifier = ""
        else:
            # 检查同列是否有多个相同棋子（车、马、炮、兵）
            count = 0
            positions = []
            for y in range(10):
                if board._board[y][move.pos_from[0]] == fench:
                    positions.append((move.pos_from[0], y))
                    count += 1

            if count > 1:
                # 排序位置（红方从下到上，黑方从上到下）
                # 当y坐标相同时，按x坐标排序（红方从左到右，黑方从右到左）
                if color == RED:
                    # 红方：从下到上，当y相同时从左到右
                    positions.sort(key=lambda p: (p[1], p[0]), reverse=True)
                else:
                    # 黑方：从上到下，当y相同时从右到左
                    positions.sort(key=lambda p: (p[1], -p[0]))

                # 找到当前位置的索引
                idx = positions.index(move.pos_from)

                if count == 2:
                    qualifier = "f" if idx == 0 else "b"  # 前/后
                elif count == 3:
                    if idx == 0:
                        qualifier = "f"  # 前
                    elif idx == 1:
                        qualifier = "m"  # 中
                    else:
                        qualifier = "b"  # 后
                elif count == 4:
                    # 排序后：前(idx=0), 二(idx=1), 三(idx=2), 后(idx=3)
                    if idx == 0:
                        qualifier = "f"  # 前
                    elif idx == 1:
                        qualifier = "2"  # 二
                    elif idx == 2:
                        qualifier = "3"  # 三
                    else:  # idx == 3
                        qualifier = "b"  # 后
                elif count == 5:
                    if idx == 0:
                        qualifier = "f"  # 前
                    elif idx == count - 1:
                        qualifier = "b"  # 后
                    else:
                        # 使用数字限定词：二、三、四
                        qualifier = str(idx + 1)  # 1+1=2, 2+1=3, 3+1=4
                elif count > 5:
                    if idx == 0:
                        qualifier = "f"  # 前
                    elif idx == count - 1:
                        qualifier = "b"  # 后
                    else:
                        qualifier = str(idx + 1)  # 数字限定词

        return cls(
            piece_type,
            column,
            direction,
            distance,
            qualifier,
            is_capture=bool(move.captured),
            is_check=move.is_checking,
            is_checkmate=move.is_checkmate,
            piece_color=color,
        )

    @classmethod
    def from_text(cls, text, board):
        """从中文走法文本解析中间表示

        参数:
            text: 中文走法字符串，如"炮二平五"、"前车进一"
            board: ChessBoard对象，用于获取棋盘状态

        返回:
            MoveNotation对象，解析失败返回None
        """
        if not text or not board:
            return None

        text = text.replace(" ", "")
        if not text:
            return None

        # 1. 解析限定词
        qualifier = ""
        offset = 0
        first_char = text[0]
        if first_char in cls.CHINESE_QUALIFIER_MAP:
            qualifier = cls.CHINESE_QUALIFIER_MAP[first_char]
            offset = 1

        # 2. 解析棋子类型
        if len(text) <= offset:
            return None

        piece_char = text[offset]
        piece_type = cls.REVERSE_PIECE_MAP.get(piece_char)
        if piece_type is None:
            return None
        offset += 1

        # 3. 解析列、方向和距离
        if len(text) < offset + 2:
            return None

        # 判断是否有列信息（有限定词时无列，否则需要检查是否是方向字符）
        column = None
        if text[offset] not in cls._DIRECTION_CHAR_TO_SYMBOL:
            # 存在列信息
            column = cls._COLUMN_CHAR_TO_IDX.get(text[offset])
            if column is None:
                return None
            offset += 1
            if len(text) < offset + 2:
                return None

        # 解析方向
        direction = cls._DIRECTION_CHAR_TO_SYMBOL.get(text[offset])
        if direction is None:
            return None

        # 解析距离（O(1) 查找）
        distance_char = text[offset + 1 :]
        distance = cls._parse_distance_char(distance_char, direction, piece_type)
        if distance is None:
            return None

        # 4. 确定棋子颜色
        piece_color = RED if piece_type.isupper() else BLACK

        return cls(
            piece_type=piece_type,
            column=column,
            direction=direction,
            distance=distance,
            qualifier=qualifier,
            piece_color=piece_color,
        )

    @classmethod
    def _parse_distance_char(
        cls, distance_char: str, direction: str, piece_type: str
    ) -> int | None:
        """解析距离字符，根据方向和棋子类型返回对应的数字。

        参数:
            distance_char: 距离字符（中文数字或全角数字）
            direction: 方向符号 ("+", "-", "=")
            piece_type: 棋子类型字符 (K/A/B/N/R/C/P)

        返回:
            距离数字，解析失败返回 None
        """
        # 平移或士/象/马：距离表示目标列
        if direction == "=" or piece_type.lower() in ("a", "b", "n"):
            return cls._COLUMN_CHAR_TO_IDX.get(distance_char)
        # 王/车/炮/兵：距离表示步数
        return cls._CHINESE_NUM_TO_INT.get(distance_char)

    def to_compact(self):
        """转换为紧凑格式"""
        result = ""
        if self.qualifier:
            result += self.qualifier
        result += self.piece_type
        result += str(self.column + 1)  # 转换为1-9
        result += self.direction
        result += str(self.distance)

        # 添加特殊标记
        if self.is_capture:
            result += "x"
        if self.is_check:
            result += "+"
        if self.is_checkmate:
            result += "#"

        return result

    def to_chinese(self, traditional=False, use_fullwidth_for_black=True):
        """转换为中文（简体/繁体）

        参数:
            traditional: 是否使用繁体中文
            use_fullwidth_for_black: 黑方是否使用全角数字
        """
        piece_name = self.PIECE_MAP[self.piece_type][1 if traditional else 0]

        # 根据棋子颜色选择数字格式
        if self.piece_color == BLACK and use_fullwidth_for_black:
            # 黑方使用全角数字
            direction_name = self.DIRECTION_MAP[self.direction][1 if traditional else 0]

            # 处理限定词（黑方限定词使用全角数字）
            qualifier_name = ""
            if self.qualifier:
                if self.qualifier in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    # 数字限定词转换为全角
                    if self.qualifier in ("1", "2", "3", "4"):
                        # 对于"前四三二后"的情况
                        fullwidth_map = {
                            "1": "１",
                            "2": "２",
                            "3": "３",
                            "4": "４",
                        }
                        qualifier_name = fullwidth_map.get(
                            self.qualifier, self.qualifier
                        )
                    else:
                        qualifier_name = str(self.qualifier)
                else:
                    qualifier_name = self.QUALIFIER_MAP.get(self.qualifier, ("", ""))[
                        1 if traditional else 0
                    ]

            # 构建结果
            if self.direction == "=":
                # 平移动：目标列使用全角数字
                target_column = (
                    self.FULLWIDTH_NUM_MAP.get(self.distance, str(self.distance))
                    if 0 <= self.distance <= 8
                    else str(self.distance)
                )
                # 有限定词时不显示列标识
                if qualifier_name:
                    return (
                        f"{qualifier_name}{piece_name}{direction_name}{target_column}"
                    )
                column_name = self.FULLWIDTH_NUM_MAP[self.column]
                return f"{piece_name}{column_name}{direction_name}{target_column}"
            # 进退移动
            if self.piece_type.lower() in ("a", "b", "n"):  # 士、相、马
                # 目标列使用全角数字
                target_column = (
                    self.FULLWIDTH_NUM_MAP.get(self.distance, str(self.distance))
                    if 0 <= self.distance <= 8
                    else str(self.distance)
                )
                # 有限定词时不显示列标识
                if qualifier_name:
                    return (
                        f"{qualifier_name}{piece_name}{direction_name}{target_column}"
                    )
                column_name = self.FULLWIDTH_NUM_MAP[self.column]
                return f"{piece_name}{column_name}{direction_name}{target_column}"
            # 王、车、炮、兵
            # 步数使用全角数字
            if 1 <= self.distance <= 9:
                # 将步数转换为全角数字
                distance_name = str(self.distance)
                fullwidth_digits = {
                    "1": "１",
                    "2": "２",
                    "3": "３",
                    "4": "４",
                    "5": "５",
                    "6": "６",
                    "7": "７",
                    "8": "８",
                    "9": "９",
                }
                distance_name = "".join(
                    fullwidth_digits.get(c, c) for c in distance_name
                )
            else:
                distance_name = str(self.distance)
            # 有限定词时不显示列标识
            if qualifier_name:
                return f"{qualifier_name}{piece_name}{direction_name}{distance_name}"
            column_name = self.FULLWIDTH_NUM_MAP[self.column]
            return f"{piece_name}{column_name}{direction_name}{distance_name}"
        # 红方或黑方不使用全角数字时，使用中文数字
        direction_name = self.DIRECTION_MAP[self.direction][1 if traditional else 0]

        # 处理限定词
        qualifier_name = ""
        if self.qualifier:
            if self.qualifier in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                # 数字限定词转换为中文数字
                num_map = {
                    "1": "一",
                    "2": "二",
                    "3": "三",
                    "4": "四",
                    "5": "五",
                    "6": "六",
                    "7": "七",
                    "8": "八",
                    "9": "九",
                }
                qualifier_name = num_map.get(self.qualifier, self.qualifier)
            else:
                qualifier_name = self.QUALIFIER_MAP.get(self.qualifier, ("", ""))[
                    1 if traditional else 0
                ]

        # 构建结果
        if self.direction == "=":
            # 平移动：目标列使用列映射
            target_column = (
                self.COLUMN_MAP[self.distance][0]
                if 0 <= self.distance <= 8
                else str(self.distance)
            )
            # 有限定词时不显示列标识
            if qualifier_name:
                return f"{qualifier_name}{piece_name}{direction_name}{target_column}"
            column_name = self.COLUMN_MAP[self.column][0]
            return f"{piece_name}{column_name}{direction_name}{target_column}"
        # 进退移动
        if self.piece_type.lower() in ("a", "b", "n"):  # 士、相、马
            # 目标列使用列映射
            target_column = (
                self.COLUMN_MAP[self.distance][0]
                if 0 <= self.distance <= 8
                else str(self.distance)
            )
            # 有限定词时不显示列标识
            if qualifier_name:
                return f"{qualifier_name}{piece_name}{direction_name}{target_column}"
            column_name = self.COLUMN_MAP[self.column][0]
            return f"{piece_name}{column_name}{direction_name}{target_column}"
        # 王、车、炮、兵
        # 步数使用中文数字（一-九）
        if 1 <= self.distance <= 9:
            distance_name = (
                _HALF_TO_ZH[self.distance]
                if self.distance < len(_HALF_TO_ZH)
                else str(self.distance)
            )
        else:
            distance_name = str(self.distance)
        # 有限定词时不显示列标识
        if qualifier_name:
            return f"{qualifier_name}{piece_name}{direction_name}{distance_name}"
        column_name = self.COLUMN_MAP[self.column][0]
        return f"{piece_name}{column_name}{direction_name}{distance_name}"

    def __str__(self):
        return self.to_compact()


# -----------------------------------------------------#
def _detect_move_side_from_text(move_str):
    """根据着法字符串中的数字类型检测走子方。

    - 含中文数字（一二三...）→ RED
    - 含阿拉伯数字（123...或 123...）→ BLACK

    参数:
        move_str: 走法字符串（已去除空格）

    返回:
        int: RED(1) 或 BLACK(2)，无法判断返回 None
    """
    # 检查是否包含中文数字
    has_chinese = any(ch in _ZH_TO_HALF for ch in move_str)

    # 检查是否包含阿拉伯数字（先转半角再检查）
    move_str_half = full2half(move_str)
    has_arabic = any(ch.isdigit() for ch in move_str_half)

    if has_chinese and not has_arabic:
        return RED
    if has_arabic and not has_chinese:
        return BLACK
    # 混合或都无法判断
    return None


def _convert_digit_format(digit_char, move_side):
    """将数字字符转换为指定走子方的索引数组格式。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方（RED=1 用中文数字，BLACK=2 用全角数字）

    返回:
        str: 转换后的数字字符，无法转换返回 None
    """
    # 已经是目标格式
    try:
        _h_level_index[move_side].index(digit_char)
        return digit_char
    except ValueError:
        pass

    # 半角数字
    if digit_char.isdigit():
        half_digit = int(digit_char)
        if half_digit == 0 or half_digit > 9:
            return None
        if move_side == 1:  # RED: 半角转中文
            return _HALF_TO_ZH[half_digit]
        return chr(0xFF10 + half_digit)

    # 中文数字（仅用于红方）
    if digit_char in _ZH_TO_HALF:
        if move_side == 1:  # RED: 保持中文
            return _HALF_TO_ZH[_ZH_TO_HALF[digit_char]]
        # BLACK 不接受中文数字，返回 None
        return None

    return None


def _get_index(digit_char, use_v_index=False):
    """获取数字字符在索引数组中的位置。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        use_v_index: True 使用_v_change_index，False 使用_h_level_index

    返回:
        int: 索引位置 (0-9)，找不到返回 None

    注意：所有走法都在规范局面（红方视角）下解析，因此只使用红方索引
    """
    index_array = _v_change_index if use_v_index else _h_level_index

    try:
        return index_array.index(digit_char)
    except ValueError:
        pass

    # 尝试转换格式后查找
    converted = _convert_digit_format(digit_char, RED)  # 规范局面下使用红方格式
    if converted:
        try:
            return index_array.index(converted)
        except ValueError:
            pass

    return None


def _get_digit_index(digit_char):
    """获取数字字符在列索引数组中的位置。

    参数:
        digit_char: 数字字符（中文、半角或全角）

    返回:
        int: 列索引 (0-8)，找不到返回 None

    注意：所有走法都在规范局面（红方视角）下解析
    """
    return _get_index(digit_char, use_v_index=False)


def _get_v_index(step_digit):
    """获取步数数字在垂直方向索引数组中的位置。

    参数:
        step_digit: 步数数字字符

    返回:
        int: v_index 位置 (0-9)，找不到返回 None

    注意：所有走法都在规范局面（红方视角）下解析
    """
    return _get_index(step_digit, use_v_index=True)


def _normalize_digit_char(digit_char, original_side, normalized_side=RED):
    """将数字字符转换为规范局面下的格式。

    当原始局面是黑方走子时，走法字符串中的数字是全角格式（如"２"）。
    在规范局面上，我们需要将其转换为红方格式（中文数字"二"）。

    参数:
        digit_char: 原始数字字符
        original_side: 原始走子方 (RED/BLACK)
        normalized_side: 规范局面走子方 (默认为RED)

    返回:
        str: 转换后的数字字符
    """
    if original_side == normalized_side:
        return digit_char

    # 如果原始是黑方，规范局面是红方，需要将全角数字转换为中文数字
    if original_side == BLACK and normalized_side == RED:
        return _FULLWIDTH_TO_CHINESE.get(digit_char, digit_char)

    # 如果原始是红方，规范局面是黑方（理论上不会发生，因为规范局面总是红方）
    if original_side == RED and normalized_side == BLACK:
        return _CHINESE_TO_FULLWIDTH.get(digit_char, digit_char)

    return digit_char


def _normalize_move_str(move_str, original_side, normalized_side=RED):
    """将走法字符串中的数字字符转换为规范局面下的格式。

    例如："炮２平５"（黑方格式）转换为"炮二平五"（红方格式）

    参数:
        move_str: 原始走法字符串
        original_side: 原始走子方 (RED/BLACK)
        normalized_side: 规范局面走子方 (默认为RED)

    返回:
        str: 转换后的走法字符串
    """
    if original_side == normalized_side:
        return move_str

    # 如果原始是黑方，规范局面是红方，需要转换所有数字字符
    if original_side == BLACK and normalized_side == RED:
        result = []
        for char in move_str:
            if char in _FULLWIDTH_TO_CHINESE:
                result.append(_FULLWIDTH_TO_CHINESE[char])
            else:
                result.append(char)
        return "".join(result)

    # 如果原始是红方，规范局面是黑方（理论上不会发生，因为规范局面总是红方）
    if original_side == RED and normalized_side == BLACK:
        result = []
        for char in move_str:
            if char in _CHINESE_TO_FULLWIDTH:
                result.append(_CHINESE_TO_FULLWIDTH[char])
            else:
                result.append(char)
        return "".join(result)

    return move_str


def _get_target_x(digit_char):
    """获取目标列索引。

    参数:
        digit_char: 数字字符

    返回:
        int: 目标列索引 (0-8)，无法解析返回 None

    注意：所有走法都在规范局面（红方视角）下解析
    """
    digit_index = _get_digit_index(digit_char)
    if digit_index is None:
        return None
    return digit_index


def _advisor_move(pos_from, move_str):
    """解析士/仕的走法。

    参数:
        pos_from: 起点坐标（在规范局面中）
        move_str: 走法字符串（如'进 6'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)（在规范局面中）

    注意：所有走法都在规范局面（红方视角）下解析
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


def _bishop_move(pos_from, move_str):
    """解析象/相的走法。

    参数:
        pos_from: 起点坐标（在规范局面中）
        move_str: 走法字符串（如'进 5'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)（在规范局面中）

    注意：所有走法都在规范局面（红方视角）下解析
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


def _knight_move(pos_from, move_str):
    """解析马的走法。

    参数:
        pos_from: 起点坐标（在规范局面中）
        move_str: 走法字符串（如'进 5'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)（在规范局面中）

    注意：所有走法都在规范局面（红方视角）下解析
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


def _king_rook_cannon_pawn_move(pos_from, move_str):
    """解析王、车、炮、兵的走法。

    参数:
        pos_from: 起点坐标
        move_str: 走法字符串（如'进一'、'平五'）

    返回:
        tuple: 目标坐标 (x, y)

    注意：所有走法都在规范局面（红方视角）下解析
    """
    # 平移
    if move_str[0] == "平":
        new_x = _get_digit_index(move_str[1])
        if new_x is None:
            return None
        return (new_x, pos_from[1])

    # 前进/后退 - 使用 _get_digit_index 获取步数
    step_digit = move_str[1:].strip()

    # 使用 _v_change_index 获取步数差值
    try:
        diff = _v_change_index.index(step_digit)
    except ValueError:
        # 尝试转换格式
        diff = _get_v_index(step_digit)
        if diff is None:
            return None

    if move_str[0] == "退":
        diff = -diff

    return (pos_from[0], pos_from[1] + diff)


# -----------------------------------------------------#
class Move:
    """表示一步棋及其在走子树中的关系（含变招、注释等）。"""

    def __init__(
        self,
        move_info: "MoveInfo",
        board_before,
        board_after,
        is_checking=False,
        is_checkmate=False,
    ):
        """初始化一个走子对象。

        基于 MoveInfo 创建走子记录，包含移动前后棋盘状态。
        """

        self.move_info = move_info
        self.pos_from = move_info.from_pos
        self.pos_to = move_info.to_pos
        self.is_checking = is_checking
        self.is_checkmate = is_checkmate
        self.move_side = move_info.prev_move_side
        self.step_index = 0
        self.score = None
        self.annote = ""
        self.parent = None
        self.next_move = None
        self.variation_next = None
        self.variations_all = [self]
        self.move_list_for_engine = []
        self.fen_for_engine = None

        # 直接使用传入的棋盘实例
        self._board_cache = board_before  # 移动前的棋盘
        self._board_done_cache = board_after  # 移动后的棋盘

        # 设置被吃棋子
        self.captured = move_info.captured_fench

    def board_before(self):
        """移动前的棋盘状态"""
        return self._board_cache

    def board_after(self):
        """移动后的棋盘状态"""
        return self._board_done_cache

    # move_side 是数据属性，在构造函数中已赋值

    def __str__(self):
        """返回此走子的 ICCS 格式字符串表示。"""
        return self.to_iccs()

    def _clear_caches(self):
        """Clear cached board snapshots to force regeneration."""
        self._board_cache = None
        self._board_done_cache = None

    def mirror(self):
        """水平镜像当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行左右镜像，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        # 直接使用 board_before() 获取实例，避免延迟导入
        mirrored_board = self.board_before().mirror()
        self.move_info.board_before = mirrored_board._board

        self.pos_from = (8 - self.pos_from[0], self.pos_from[1])
        self.pos_to = (8 - self.pos_to[0], self.pos_to[1])

        self._clear_caches()

        for move in self.get_variations():
            move.mirror()

        if self.next_move:
            self.next_move.mirror()

    def flip(self):
        """垂直翻转当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行上下翻转，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        # 直接使用 board_before() 获取实例，避免延迟导入
        flipped_board = self.board_before().flip()
        self.move_info.board_before = flipped_board._board

        self.pos_from = (self.pos_from[0], 9 - self.pos_from[1])
        self.pos_to = (self.pos_to[0], 9 - self.pos_to[1])

        self._clear_caches()

        for move in self.get_variations():
            move.flip()

        if self.next_move:
            self.next_move.flip()

    def swap(self):
        """交换红黑视角（棋子交换阵营）并更新所有子节点（就地）。

        对当前走子、`board_done` 及所有分支和 `next_move` 做视角
        交换，使之从另一方视角表示。
        """
        # 直接使用 board_before() 获取实例，避免延迟导入
        swapped_board = self.board_before().swap()
        self.move_info.board_before = swapped_board._board

        self.move_info.moving_fench = swap_fench(self.move_info.moving_fench)
        if self.move_info.captured_fench is not None:
            self.move_info.captured_fench = swap_fench(self.move_info.captured_fench)

        self.move_info.prev_move_side = next_color(self.move_info.prev_move_side)

        self._clear_caches()

        for move in self.get_variations():
            move.swap()

        if self.next_move:
            self.next_move.swap()

    def is_king_killed(self):
        """如果此走子吃掉了将/帅，返回 True。

        检查记录的 `captured` 字符是否表示国王（不区分大小写）。
        """
        if self.captured and self.captured.lower() == "k":
            return True
        return False

    def len_variations(self):
        """返回当前走子的分支（变招）数量。"""
        return len(self.variations_all)

    def get_variations(self, include_me=False):
        """返回当前走子的所有分支（变招），可选择是否包含自身。"""
        if include_me:
            return self.variations_all

        sibs = self.variations_all[:]
        sibs.remove(self)

        return sibs

    def last_variation(self):
        """返回最后一个分支（变招）走子。"""
        return self.variations_all[-1]

    def get_variation_index(self):
        """返回当前走子在分支列表中的索引及分支总数。"""
        sibling_count = len(self.variations_all)
        for index, m in enumerate(self.variations_all):
            if m == self:
                return (index, sibling_count)
        return None

    def add_variation(self, chess_move):
        """将 `chess_move` 添加为当前走子的一个新分支（变招）。"""
        chess_move.parent = self.parent
        chess_move.step_index = self.step_index
        last = self.last_variation()

        assert last.variation_next is None

        last.variation_next = chess_move

        self.variations_all.append(chess_move)
        for node in self.get_variations():
            node.variations_all = self.variations_all

        return chess_move

    def remove_variation(self, chess_move):
        """从当前走子的分支列表中移除指定的 `chess_move`。"""
        if chess_move not in self.variations_all:
            return

        # 先移出兄弟表
        self.variations_all.remove(chess_move)

        # 从链上摘下
        # 找到链表头节点（第一个兄弟节点）
        head = self.variations_all[0]

        # 如果要删除的是头节点
        if chess_move == head:
            # 将原头节点从链表中断开
            chess_move.variation_next = None
            # 注意：variations_all 已经更新，head 已经变为新的头节点
        else:
            # 遍历链表找到前驱节点
            prev = head
            while prev.variation_next and prev.variation_next != chess_move:
                prev = prev.variation_next
            if prev.variation_next == chess_move:
                # 跳过要删除的节点
                prev.variation_next = chess_move.variation_next
                chess_move.variation_next = None

        # 更新兄弟表到所有的兄弟
        for node in self.get_variations():
            node.variations_all = self.variations_all

    def append_next_move(self, chess_move):
        """将 `chess_move` 作为当前走子的后继加入走子树。

        设置 `chess_move.parent` 与 `step_index`。若当前无 `next_move`
        则作为线性后继；否则将其作为现有 `next_move` 的一个分支。
        """
        chess_move.parent = self
        chess_move.step_index = self.step_index + 1
        if not self.next_move:
            self.next_move = chess_move
        else:
            self.next_move.variations_all.append(chess_move)

    def dump_moves(
        self, move_list, curr_move_line, is_tree_mode, curr_variation_index=0
    ):
        """将从当前节点开始的走子线路序列化并追加到 `move_list`。

        `curr_move_line` 表示当前遍历路径，本方法会在递归过程中
        扩展路径并将每条线（含分支索引）追加到 `move_list`。
        """

        backup_move_line = curr_move_line["moves"][:]
        curr_move_line["moves"].append(self)

        curr_line_index = curr_move_line["index"]

        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line, is_tree_mode, 0)

        # curr_variation_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        # 所以就不能在分支中再找兄弟了，否则会重复输出分支
        # assert curr_variation_index == self.get_variation_index()
        if curr_variation_index > 0:
            return

        # 只有主分支（index == 0）才会遍历兄弟分支

        for index, variation_move in enumerate(self.get_variations()):
            variation_index = index + 1
            new_line_index = len(move_list)
            line_name = f"{curr_line_index}.{self.step_index}.{variation_index}_{new_line_index}"
            new_line = {
                "index": new_line_index,
                "name": line_name,
                #'variations':variations,
                "variation_index": variation_index,
                "from_line": (curr_line_index, self.step_index, variation_index),
                "moves": [],
            }

            if not is_tree_mode:
                new_line["moves"].extend(backup_move_line)

            move_list.append(new_line)
            variation_move.dump_moves(
                move_list, new_line, is_tree_mode, variation_index
            )

    def init_move_line(self):
        """初始化并返回一个空的走子线路字典。"""
        return {"index": 0, "name": "0", "variations": [], "moves": []}

    def to_text(
        self,
        detailed=False,
        fmt="chinese",
        traditional=False,
        use_fullwidth_for_black=True,
    ):
        """返回此走子的文本表示。

        参数:
            detailed: 是否显示详细信息（吃子、将军等）
            fmt: 输出格式，可选值："chinese"（默认）、"compact"
            traditional: 当fmt为"chinese"时，是否使用繁体中文
            use_fullwidth_for_black: 当fmt为"chinese"时，黑方是否使用全角数字

        返回:
            指定格式的走法字符串
        """
        notation = MoveNotation.from_move(self)

        if fmt == "compact":
            text = notation.to_compact()
        else:  # "chinese" or default
            text = notation.to_chinese(traditional, use_fullwidth_for_black)

        if detailed:
            details = []
            if self.captured:
                # 吃子表示
                details.append("吃" + fench_to_text(self.captured))
            if self.is_checkmate:
                details.append("将死")
            elif self.is_checking:
                details.append("将军")

            if details:
                text = f"{text}({','.join(details)})"

        return text

    def _get_direction_str(self, diff):
        """获取走法方向字符串（平/进/退）"""
        if diff == 0:
            return "平"
        return "进" if diff > 0 else "退"

    def _get_dest_str(self, fench, piece_color, diff):
        """获取目标位置字符串（兼容旧版）"""
        # 根据走子方确定使用哪个索引
        # 红方使用中文数字，黑方使用全角数字
        if piece_color == RED:
            h_index = _h_level_index
            v_index = _v_change_index
        else:
            # 黑方使用全角数字，需要将坐标转换为黑方视角
            # 黑方视角：x坐标从右到左，y坐标从上到下
            # 所以需要将x坐标转换为黑方索引
            h_index = ("１", "２", "３", "４", "５", "６", "７", "８", "９")
            v_index = ("误", "１", "２", "３", "４", "５", "６", "７", "８", "９")

        if fench.lower() in ("k", "r", "c", "p"):
            # 王车炮兵规则
            if diff == 0:
                return h_index[self.pos_to[0]]
            if diff > 0:
                return v_index[diff]
            return v_index[-diff]
        # 士相马的规则
        return h_index[self.pos_to[0]]

    def _get_detailed_info(self):
        """获取详细信息列表（吃子、将军、将死）"""
        details = []
        if self.captured:
            details.append(f"吃{fench_to_text(self.captured)}")
        if self.is_checkmate:
            details.append("将死")
        elif self.is_checking:
            details.append("将军")
        return details

    def to_text_detail(
        self,
        show_variation,
        show_annote,
        fmt="chinese",
        traditional=False,
        use_fullwidth_for_black=True,
    ):
        """返回走子的文本表示，可选择是否显示变招和注释。"""
        if show_variation:
            txt = self.to_text_variation(
                fmt=fmt,
                traditional=traditional,
                use_fullwidth_for_black=use_fullwidth_for_black,
            )
        else:
            txt = self.to_text(
                fmt=fmt,
                traditional=traditional,
                use_fullwidth_for_black=use_fullwidth_for_black,
            )

        annote = self.annote if show_annote else ""

        return (txt, annote)

    def to_text_variation(
        self, fmt="chinese", traditional=False, use_fullwidth_for_black=True
    ):
        """返回带有变招标记的走子文本表示（多分支以方括号包裹）。"""
        assert len(self.variations_all) > 0

        # 父节点只有一个孩子，那就是自己
        if len(self.variations_all) == 1:
            return self.to_text(
                fmt=fmt,
                traditional=traditional,
                use_fullwidth_for_black=use_fullwidth_for_black,
            )

        txts = []
        for _index, m in enumerate(self.variations_all):
            if m == self:
                txts.append(
                    f"{m.to_text(fmt=fmt, traditional=traditional, use_fullwidth_for_black=use_fullwidth_for_black)}"
                )
            else:
                txts.append("*")  # m.to_text())

        return f"[{','.join(txts)}]"

    def prepare_for_engine(self, move_side, history):
        """为引擎查询准备 FEN 与 moves 列表。

        如果当前走子为吃子，则引擎的 FEN 应为走子后的局面；否则
        根据历史拼接 moves 列表以便向引擎发送完整走子序列。
        """
        if self.captured:
            # 吃子移动：使用 board_before() 的副本生成走子后的 FEN
            temp_board = self.board_before().copy()

            # 应用移动
            moving_fench = temp_board._board[self.pos_from[1]][self.pos_from[0]]
            temp_board._board[self.pos_to[1]][self.pos_to[0]] = moving_fench
            temp_board._board[self.pos_from[1]][self.pos_from[0]] = None
            temp_board.set_move_side(move_side)

            self.fen_for_engine = temp_board.to_fen()
            self.move_list_for_engine = []
        else:
            # 未吃子移动
            if not history:
                # 历史为空
                self.fen_for_engine = self.board_before().to_fen()
                self.move_list_for_engine = [self.to_iccs()]
            else:
                # 历史不为空，向后追加
                last_move = history[-1]
                self.fen_for_engine = last_move.fen_for_engine
                self.move_list_for_engine = last_move.move_list_for_engine[:]
                self.move_list_for_engine.append(self.to_iccs())

    def to_engine_fen(self):
        """返回用于引擎的输入字符串：基础 FEN（可选加 moves）。

        若 `move_list_for_engine` 为空，直接返回 `fen_for_engine`；
        否则返回形如 '<fen> moves <m1> <m2> ...' 的字符串。
        """
        if len(self.move_list_for_engine) == 0:
            return self.fen_for_engine

        move_str = " ".join(self.move_list_for_engine)
        return " ".join([self.fen_for_engine, "moves", move_str])

    def to_iccs(self):
        """返回此走子的 ICCS（引擎）走法字符串。

        将内部 (x,y) 坐标元组转换为引擎使用的 ICCS 表示法。
        """
        return pos2iccs(self.pos_from, self.pos_to)

    @staticmethod
    def text_move_to_std_move(piece_fench, pos_from, move_str):
        """将中文走法片段转换为目标坐标。

        参数:
            piece_fench: 棋子类型字符
            pos_from: 起点坐标（在规范局面中）
            move_str: 走法字符串（如'进一'、'平五'等）

        返回:
            tuple: 目标坐标 (x, y)（在规范局面中），无法解析返回 None

        注意：所有走法都在规范局面（红方视角）下解析
        """
        # 移动规则检查
        if not move_str:
            return None
        if piece_fench in ["a", "b", "n"] and move_str[0] == "平":
            return None
        if move_str[0] not in ["进", "退", "平"]:
            return None

        # 王，车，炮，兵的移动规则
        if piece_fench in ["k", "r", "c", "p"]:
            return _king_rook_cannon_pawn_move(pos_from, move_str)

        # 仕/士的移动规则
        if piece_fench == "a":
            return _advisor_move(pos_from, move_str)

        # 象/相的移动规则
        if piece_fench == "b":
            return _bishop_move(pos_from, move_str)

        # 马的移动规则
        if piece_fench == "n":
            return _knight_move(pos_from, move_str)

        return None

    @staticmethod
    def from_text(board, move_str):
        """解析中文走法字符串，返回标准化的走子 ((pos_from, pos_to))。

        使用规范局面（红方视角）处理所有走法，统一红黑方逻辑。

        注意：此函数主要用于测试，生产代码请使用 board.move_text()。
        """
        move_str = move_str.replace(" ", "")
        return _MoveTextParser(board, move_str).parse()


class _MoveTextParser:
    """中文走法文本解析器，使用规范局面（红方视角）处理所有走法"""

    def __init__(self, board, move_str):
        self.original_board = board
        # 转换为规范局面（红方视角）处理
        self.normalized_board = board.normalized()
        self.move_str = move_str
        self.work_side = None
        self.fench = None
        self.piece_fench = None
        self.piece_name = None
        # 中间表示
        self.notation = None
        # 记录是否需要坐标转换
        self.needs_denormalization = board.move_side() == BLACK

    def parse(self):
        """执行解析，返回原局面中的走法坐标"""
        # 首先尝试使用 MoveNotation 中间表示解析
        self.notation = MoveNotation.from_text(self.move_str, self.original_board)
        if self.notation:
            # 使用中间表示解析
            result = self._parse_from_notation()
            if result:
                return result

        # 回退到原始解析方法
        if not self._parse_basic_info():
            return None

        # 在规范局面中解析走法
        normalized_moves = self._parse_in_normalized_board()
        if not normalized_moves:
            return None

        # 将规范局面中的坐标转换回原局面
        return self._denormalize_moves(normalized_moves)

    def _parse_in_normalized_board(self):
        """在规范局面中解析走法"""
        # 根据首字符选择解析策略
        first_char = self.move_str[0]
        if first_char in ["一", "二", "三", "四", "五"]:
            return self._parse_multi_lines()
        if first_char in ["前", "中", "后"]:
            return self._parse_multi_pieces()
        return self._parse_simple()

    def _parse_basic_info(self):
        """解析基本信息：棋子名称、FEN字符"""
        # 如果有中间表示，从中获取信息
        if self.notation:
            # 从中间表示获取棋子信息
            piece_type = self.notation.piece_type.upper()  # 规范局面使用大写

            # 棋子类型到 FEN 字符的映射
            piece_type_to_fench = {
                "K": "K",
                "A": "A",
                "B": "B",
                "N": "N",
                "R": "R",
                "C": "C",
                "P": "P",
            }

            if piece_type in piece_type_to_fench:
                self.fench = piece_type_to_fench[piece_type]
                self.piece_fench = self.fench.lower()
                self.work_side = RED
                return True

        # 回退到原始解析方法
        # 确定棋子名称
        if self.move_str[0] in ["前", "中", "后", "一", "二", "三", "四", "五"]:
            self.piece_name = self.move_str[1]
        else:
            self.piece_name = self.move_str[0]

        # 在规范局面中，所有走子方都视为红方
        self.work_side = RED

        # 转换为FEN字符（在规范局面中，所有棋子都是红方视角）
        self.fench = text_to_fench(self.piece_name, RED)
        if not self.fench:
            return False

        self.piece_fench = self.fench.lower()
        return True

    def _parse_simple(self):
        """解析简单走法（如"炮二平五"）"""
        digit_char = self.move_str[1]
        x = _get_digit_index(digit_char)
        if x is None:
            return None

        positions = self.normalized_board.get_fench_positions_x(self.fench, x)
        if len(positions) == 0:
            return None

        # 除了士/象，同一列不能有多个相同棋子
        if (len(positions) > 1) and (self.piece_fench not in ["a", "b"]):
            return None

        moves = []
        for pos in positions:
            move = Move.text_move_to_std_move(self.piece_fench, pos, self.move_str[2:])
            if move:
                moves.append((pos, move))

        return moves

    def _parse_multi_pieces(self):
        """解析多棋子情况（如"前炮平五"、"中兵平五"、"后炮平五"）"""
        positions = self.normalized_board.get_fench_positions(self.fench)
        if not positions:
            return None

        # 规范局面下（红方视角）：前=y 大（靠近对方），后=y 小（靠近己方）
        positions.sort(key=lambda p: p[1], reverse=True)  # y 降序：前->后

        move_idx = {"前": 0, "中": 1, "后": -1}  # 前=第一个，后=最后一个
        pos = positions[move_idx[self.move_str[0]]]

        move = Move.text_move_to_std_move(self.piece_fench, pos, self.move_str[2:])
        if move:
            return [(pos, move)]
        return None

    def _parse_multi_lines(self):
        """解析多线情况（如"一炮平五"、"二炮平五"等）"""
        digit_char = self.move_str[0]
        target_x = _get_digit_index(digit_char)

        positions = []
        if target_x is not None:
            positions = self.normalized_board.get_fench_positions_x(
                self.fench, target_x
            )

        if not positions:
            positions = self.normalized_board.get_fench_positions(self.fench)

        if self.piece_fench == "p" and len(positions) > 1:
            # 规范局面下（红方视角）：兵从后往前排序
            positions.sort(key=lambda p: p[1], reverse=True)

        if len(positions) == 0:
            return None

        for pos in positions:
            move = Move.text_move_to_std_move(self.piece_fench, pos, self.move_str[2:])
            if move:
                return [(pos, move)]

        return None

    def _denormalize_moves(self, normalized_moves):
        """将规范局面中的走法坐标转换回原局面"""
        if not self.needs_denormalization:
            return normalized_moves

        denormalized_moves = []
        for pos_from, pos_to in normalized_moves:
            # 使用原棋盘的 denormalize_pos 方法转换坐标
            denormalized_from = self.original_board.denormalize_pos(pos_from)
            denormalized_to = self.original_board.denormalize_pos(pos_to)
            denormalized_moves.append((denormalized_from, denormalized_to))

        return denormalized_moves

    def _parse_from_notation(self):
        """从 MoveNotation 中间表示解析走法坐标"""
        if not self.notation:
            return None

        # 从中间表示获取棋子信息
        piece_type = self.notation.piece_type
        column = self.notation.column
        direction = self.notation.direction
        distance = self.notation.distance
        qualifier = self.notation.qualifier

        # 将棋子类型转换为 FEN 字符（规范局面下使用红方）
        piece_type_upper = piece_type.upper()

        # 验证棋子类型有效性
        valid_piece_types = {"K", "A", "B", "N", "R", "C", "P"}
        if piece_type_upper not in valid_piece_types:
            return None

        self.fench = piece_type_upper
        self.piece_fench = self.fench.lower()

        # 在规范局面中，所有走子方都视为红方
        self.work_side = RED

        # 根据限定词和列获取候选棋子位置
        positions = []

        if qualifier:
            # 有限定词：获取所有该类型的棋子
            all_positions = self.normalized_board.get_fench_positions(self.fench)
            if not all_positions:
                return None

            # 根据棋子类型和限定词排序
            if self.piece_fench in ["r", "c", "n", "p"]:
                # 车、炮、马、兵：按 y 坐标降序排序（红方视角：前->后）
                all_positions.sort(key=lambda p: p[1], reverse=True)

                # 根据限定词选择棋子
                if qualifier == "f":  # 前
                    if len(all_positions) > 0:
                        positions = [all_positions[0]]
                elif qualifier == "m":  # 中
                    if len(all_positions) > 1:
                        positions = [all_positions[1]]
                elif qualifier == "b":  # 后
                    if len(all_positions) > 0:
                        positions = [all_positions[-1]]
                elif qualifier.isdigit():  # 数字限定词
                    idx = int(qualifier) - 1
                    if 0 <= idx < len(all_positions):
                        positions = [all_positions[idx]]
        else:
            # 无限定词：按列查找
            positions = self.normalized_board.get_fench_positions_x(self.fench, column)

        if not positions:
            return None

        # 对于非士/象的棋子，如果同列有多个且没有限定词，则无法确定
        if len(positions) > 1 and not qualifier and self.piece_fench not in ["a", "b"]:
            return None

        # 构建中文走法字符串，使用 Move.text_move_to_std_move 计算目标坐标
        # 方向字符映射
        direction_char_map = {"+": "进", "-": "退", "=": "平"}
        direction_char = direction_char_map.get(direction, "")

        # 步数距离字符映射（中文数字）
        step_distance_map = {
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
        }

        # 根据棋子类型和方向确定距离字符的含义
        if direction == "=":
            # 平移动：距离表示目标列索引（0-8）
            # 使用 COLUMN_MAP 将列索引转换为中文数字
            if 0 <= distance <= 8:
                distance_char = self.notation.COLUMN_MAP[distance][0]
            else:
                distance_char = ""
        elif self.piece_fench in ["a", "b", "n"]:
            # 士、象、马：距离表示目标列索引（0-8）
            if 0 <= distance <= 8:
                distance_char = self.notation.COLUMN_MAP[distance][0]
            else:
                distance_char = ""
        else:
            # 王、车、炮、兵：距离表示步数（1-9）
            distance_char = step_distance_map.get(distance, "")

        # 构建走法字符串
        move_str = direction_char + distance_char

        # 为每个候选位置计算目标坐标
        moves = []
        for pos in positions:
            # 使用 Move.text_move_to_std_move 计算目标坐标
            pos_to = Move.text_move_to_std_move(self.piece_fench, pos, move_str)
            if pos_to:
                moves.append((pos, pos_to))

        if not moves:
            return None

        # 将规范局面中的坐标转换回原局面
        return self._denormalize_moves(moves)
