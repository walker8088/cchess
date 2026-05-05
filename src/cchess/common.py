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

import json
import re
from collections import OrderedDict
from pathlib import Path

from .constants import (  # noqa: F401 (re-exported for other modules)
    ANY_COLOR,
    BLACK,
    EMPTY_BOARD,
    EMPTY_FEN,
    FULL_INIT_BOARD,
    FULL_INIT_FEN,
    RED,
    SIDE_BLACK,
    SIDE_RED,
)

# -----------------------------------------------------#
# 中文数字映射常量（用于走法文本解析）
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

# 列索引数组：规范局面下使用红方索引（中文数字，从右到左）
_H_LEVEL_INDEX = ("九", "八", "七", "六", "五", "四", "三", "二", "一")
_V_CHANGE_INDEX = ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九")

# 半角数字到中文数字映射（索引即数字值）
_HALF_TO_ZH = (None, "一", "二", "三", "四", "五", "六", "七", "八", "九")

# 中文数字到半角数字映射（反向自动生成）
_ZH_TO_HALF = {zh: i for i, zh in enumerate(_HALF_TO_ZH) if zh}

# -----------------------------------------------------#
# 走法记谱常量（被 move.py 共用）

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
REVERSE_PIECE_MAP: dict[str, str] = {}
for _fen, (_simp, _trad) in PIECE_MAP.items():
    REVERSE_PIECE_MAP[_simp] = _fen
    if _trad != _simp:
        REVERSE_PIECE_MAP[_trad] = _fen


# 列数字映射（红方视角，从右到左）
COLUMN_MAP = {
    0: ("九", "９"),
    1: ("八", "８"),
    2: ("七", "７"),
    3: ("六", "６"),
    4: ("五", "５"),
    5: ("四", "４"),
    6: ("三", "３"),
    7: ("二", "２"),
    8: ("一", "１"),
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

# 限定词数字映射（红方中文数字，黑方全角数字）
_QUALIFIER_DIGIT_MAP = {
    SIDE_RED: ("一", "二", "三", "四", "五", "六", "七", "八", "九"),
    SIDE_BLACK: ("１", "２", "３", "４", "５", "６", "７", "８", "９"),
}

# 反向查找：列号字符 -> 列索引
_COLUMN_CHAR_TO_IDX: dict[str, int] = {}
for _idx, (_c, _f) in COLUMN_MAP.items():
    _COLUMN_CHAR_TO_IDX[_c] = _idx
    _COLUMN_CHAR_TO_IDX[_f] = _idx

# 反向查找：中文数字/全角数字 -> 整数
_CHINESE_NUM_TO_INT: dict[str, int] = {
    **_ZH_TO_HALF,
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

# 方向字符 -> 符号映射
_DIRECTION_CHAR_TO_SYMBOL: dict[str, str] = {
    "进": "+",
    "進": "+",
    "退": "-",
    "平": "=",
}

# -----------------------------------------------------#
# 走法文本解析辅助函数（被 move.py 和 piece.py 共用）


def _convert_digit_format(digit_char, move_side):
    """将数字字符转换为指定走子方的索引数组格式。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方（SIDE_RED=1 用中文数字，SIDE_BLACK=2 用全角数字）

    返回:
        str: 转换后的数字字符，无法转换返回 None
    """
    # 已经是目标格式
    try:
        _H_LEVEL_INDEX[move_side].index(digit_char)
        return digit_char
    except ValueError:
        pass

    # 半角数字
    if digit_char.isdigit():
        half_digit = int(digit_char)
        if half_digit == 0 or half_digit > 9:
            return None
        if move_side == 1:  # SIDE_RED: 半角转中文
            return _HALF_TO_ZH[half_digit]
        return chr(0xFF10 + half_digit)

    # 中文数字（仅用于红方）
    if digit_char in _ZH_TO_HALF:
        if move_side == 1:  # SIDE_RED: 保持中文
            return _HALF_TO_ZH[_ZH_TO_HALF[digit_char]]
        # SIDE_BLACK 不接受中文数字，返回 None
        return None

    return None


def _get_index(digit_char, use_v_index=False):
    """获取数字字符在索引数组中的位置。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        use_v_index: True 使用_V_CHANGE_INDEX，False 使用_H_LEVEL_INDEX

    返回:
        int: 索引位置 (0-9)，找不到返回 None

    注意：所有走法都在规范局面（红方视角）下解析，因此只使用红方索引
    """
    index_array = _V_CHANGE_INDEX if use_v_index else _H_LEVEL_INDEX

    try:
        return index_array.index(digit_char)
    except ValueError:
        pass

    # 尝试转换格式后查找
    converted = _convert_digit_format(digit_char, SIDE_RED)  # 规范局面下使用红方格式
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


def _normalize_digit_char(digit_char, original_side, normalized_side=SIDE_RED):
    """将数字字符转换为规范局面下的格式。

    当原始局面是黑方走子时，走法字符串中的数字是全角格式（如"２"）。
    在规范局面上，我们需要将其转换为红方格式（中文数字"二"）。

    参数:
        digit_char: 原始数字字符
        original_side: 原始走子方 (SIDE_RED/SIDE_BLACK)
        normalized_side: 规范局面走子方 (默认为RED)

    返回:
        str: 转换后的数字字符
    """
    if original_side == normalized_side:
        return digit_char

    # 如果原始是黑方，规范局面是红方，需要将全角数字转换为中文数字
    if original_side == SIDE_BLACK and normalized_side == SIDE_RED:
        return _FULLWIDTH_TO_CHINESE.get(digit_char, digit_char)

    # 如果原始是红方，规范局面是黑方（理论上不会发生，因为规范局面总是红方）
    if original_side == SIDE_RED and normalized_side == SIDE_BLACK:
        return _CHINESE_TO_FULLWIDTH.get(digit_char, digit_char)

    return digit_char


def _normalize_move_str(move_str, original_side):
    """将走法字符串中的数字字符转换为规范局面（红方视角）下的格式。

    作用：将黑方格式的走法字符串转换为红方视角格式，用于统一解析。
    - 黑方使用全角/阿拉伯数字（如"炮２平５"、"车1平5"）
    - 红方使用中文数字（如"炮二平五"）
    - 规范局面（红方视角）下统一使用中文数字

    例如：
    - "炮２平５"（黑方格式）→ "炮二平五"（红方格式）
    - "车1平5"（黑方格式）→ "车一平五"（红方格式）
    - "炮二平五"（红方格式）→ 直接返回（无需转换）

    参数:
        move_str: 原始走法字符串
        original_side: 原始走子方 (SIDE_RED/SIDE_BLACK)

    返回:
        str: 转换后的走法字符串（规范局面红方视角格式）
    """
    # 规范局面总是红方视角
    if original_side == SIDE_RED:
        return move_str

    # 如果原始是黑方，规范局面是红方，需要转换所有数字字符
    result = []
    for char in move_str:
        if char in _FULLWIDTH_TO_CHINESE:
            result.append(_FULLWIDTH_TO_CHINESE[char])
        else:
            result.append(char)
    return "".join(result)


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


def next_color(color: int) -> int:
    """切换到下一个走子方，对应 ChessPlayer.next() 的逻辑。"""
    return (3 - color) % 3


# -----------------------------------------------------#


def _h_mirror(c: str) -> str:
    """水平镜像列字母（a↔i, b↔h, ...）"""
    return chr(ord("a") + ord("i") - ord(c))


def _v_mirror(c: str) -> str:
    """垂直翻转行数字（0↔9, 1↔8, ...）"""
    return str(9 - int(c))


# -----------------------------------------------------#
def pos2iccs(pos_from, pos_to):
    return f"{chr(ord('a') + pos_from[0])}{pos_from[1]}{chr(ord('a') + pos_to[0])}{pos_to[1]}"


def iccs2pos(iccs):
    return (
        (ord(iccs[0]) - ord("a"), int(iccs[1])),
        (ord(iccs[2]) - ord("a"), int(iccs[3])),
    )


def iccs_mirror(iccs):
    return f"{_h_mirror(iccs[0])}{iccs[1]}{_h_mirror(iccs[2])}{iccs[3]}"


def iccs_flip(iccs):
    return f"{iccs[0]}{_v_mirror(iccs[1])}{iccs[2]}{_v_mirror(iccs[3])}"


def iccs_swap(iccs):
    return f"{_h_mirror(iccs[0])}{_v_mirror(iccs[1])}{_h_mirror(iccs[2])}{_v_mirror(iccs[3])}"


def iccs_list_mirror(iccs_list):
    return [iccs_mirror(x) for x in iccs_list]


# -----------------------------------------------------#
_fench_name_dict = {
    "K": "帅",
    "k": "将",
    "A": "仕",
    "a": "士",
    "B": "相",
    "b": "象",
    "N": "马",
    "n": "马",
    "R": "车",
    "r": "车",
    "C": "炮",
    "c": "炮",
    "P": "兵",
    "p": "卒",
}

_name_fench_dict = {
    "帅": "K",
    "将": "k",
    "仕": "A",
    "士": "a",
    "相": "B",
    "象": "b",
    "马": "n",
    "车": "r",
    "炮": "c",
    "兵": "P",
    "卒": "p",
}

_fench_txt_name_dict = {
    "K": "帅",
    "A": "仕",
    "B": "相",
    "R": "车",
    "N": "马",
    "C": "炮",
    "P": "兵",
    "k": "将",
    "a": "士",
    "b": "象",
    "r": "砗",
    "n": "碼",
    "c": "砲",
    "p": "卒",
}


# -----------------------------------------------------#
def fench_to_txt_name(fench):
    if fench not in _fench_txt_name_dict:
        return None

    return _fench_txt_name_dict[fench]


def fench_to_text(fench):
    return _fench_name_dict[fench]


def text_to_fench(text, color):
    if text not in _name_fench_dict:
        return None
    fench = _name_fench_dict[text]
    return fench.lower() if color == SIDE_BLACK else fench.upper()


def swap_fench(fench: str) -> str:
    """交换棋子的大小写（红黑互换）。

    大写表示红方、小写表示黑方。该函数将棋子字母大小写取反。

    参数:
        fench: 棋子 FEN 字符，如 'K', 'a', 'r' 等

    返回:
        str: 交换后的棋子字符
    """
    return fench.upper() if fench.islower() else fench.lower()


def fench_to_species(fen_ch):
    """从 FEN 字符返回 (species, color) 元组。

    参数:
        fen_ch: FEN 字符（如 'K', 'k', 'R', 'r' 等）

    返回:
        tuple: (species, color)，其中 species 是小写棋子类型，color 是 SIDE_RED 或 SIDE_BLACK
    """
    return (fen_ch.lower(), SIDE_BLACK if fen_ch.islower() else SIDE_RED)


def get_fench_color(fen_ch):
    """从 FEN 字符返回棋子颜色。

    参数:
        fen_ch: FEN 字符（如 'K', 'k', 'R', 'r' 等）

    返回:
        int: SIDE_RED 或 SIDE_BLACK
    """
    return SIDE_BLACK if fen_ch.islower() else SIDE_RED


# -----------------------------------------------------#
def fen_move_color(fen):
    color = fen.rstrip().split(" ")[1].lower()
    return SIDE_RED if color == "w" else SIDE_BLACK


# -----------------------------------------------------#
# 全角半角数字转换映射表
_DIGIT_MAP_FULL_TO_HALF = str.maketrans("１２３４５６７８９", "123456789")
# _DIGIT_MAP_HALF_TO_FULL = str.maketrans("123456789", "１２３４５６７８９")


def full2half(text):
    """将全角数字转换为半角数字。"""
    return text.translate(_DIGIT_MAP_FULL_TO_HALF)


# def half2full(text):
#    """将半角数字转换为全角数字。"""
#    return text.translate(_DIGIT_MAP_HALF_TO_FULL)


# -----------------------------------------------------#
p_count_dict = {
    "R1": "车",
    "R2": "双车",
    "N1": "马",
    "N2": "双马",
    "C1": "炮",
    "C2": "双炮",
    "P1": "兵",
    "P2": "双兵",
    "P3": "三兵",
    "P4": "多兵",
    "P5": "多兵",
    "A1": "仕",
    "A2": "双仕",
    "B1": "相",
    "B2": "双相",
}

p_dict = {
    "R": "车",
    "N": "马",
    "C": "炮",
    "P": "兵",
    "A": "士",
    "B": "象",
}


# -----------------------------------------------------#
def get_fen_pieces(fen):
    pieces = OrderedDict()
    fen_base = fen.split(" ")[0]
    for ch in fen_base:
        if not ch.isalpha():
            continue
        if ch not in pieces:
            pieces[ch] = 0
        pieces[ch] += 1
    return pieces


def get_fen_type(fen):
    pieces = get_fen_pieces(fen)
    for ch in ["K", "A", "B"]:
        if ch in pieces:
            pieces.pop(ch)

    title = ""
    p_count = 0
    for fench in ["R", "N", "C", "P"]:
        if fench not in pieces:
            continue

        title += p_dict[f"{fench}"]
        p_count += 1

    return title


# -----------------------------------------------------#
def get_fen_type_detail(fen):
    pieces = get_fen_pieces(fen)

    title_red = ""
    p_count = 0
    for fench in ["R", "N", "C", "P", "A", "B"]:
        if fench not in pieces:
            continue
        title_red += p_count_dict[f"{fench}{pieces[fench]}"]
        p_count += 1

    title_red = title_red.replace("双仕双相", "仕相全")
    if title_red in ["车", "马", "炮", "兵", "仕", "相"]:
        title_red = "单" + title_red

    if title_red == "":
        title_red = "帅"

    p_count = 0
    title_black = ""
    for fench in ["r", "n", "c", "p", "a", "b"]:
        if fench not in pieces:
            continue
        ch_upper = fench.upper()
        title_black += p_count_dict[f"{ch_upper}{pieces[fench]}"]
        p_count += 1

    title_black = title_black.replace("兵", "卒")
    title_black = title_black.replace("仕", "士")
    title_black = title_black.replace("相", "象")
    title_black = title_black.replace("双士双象", "士象全")

    if title_black in ["车", "马", "炮", "卒", "士", "象"]:
        title_black = "单" + title_black

    if title_black == "":
        title_black = "将"

    return (title_red, title_black)


def append_move_to_game(game, curr_move, parent_move):
    """将走子添加到游戏树中。

    Args:
        game: Game 对象
        curr_move: 当前走子
        parent_move: 父节点走子

    Returns:
        当前走子（如果成功添加），否则返回 parent_move
    """
    if parent_move:
        parent_move.append_next_move(curr_move)
    else:
        game.append_first_move(curr_move)
    return curr_move


# -----------------------------------------------------#
def parse_dhtmlxq(html_str):
    """解析 DhtmlXQHTML 格式的象棋谱字符串，返回一个字典。

    示例输入:
        [DhtmlXQHTML]
        [DhtmlXQ_init]500,350[/DhtmlXQ_init]
        ...
        [/DhtmlXQHTML]

    返回:
        {
            "init": "500,350",
            "binit": "8979695949392919097717866646260600102030405060708012720323436383",
            "title": "中炮对左三步虎",
            ...
        }
    """
    result = {}

    # 使用正则表达式匹配所有 [DhtmlXQ_xxx]content[/DhtmlXQ_xxx]
    pattern = r"\[DhtmlXQ_([^]]+)\](.*?)\[/DhtmlXQ_\1\]"
    matches = re.findall(pattern, html_str, re.DOTALL)

    for key, value in matches:
        # 去除内容中的换行和多余空白
        cleaned_value = value.strip()
        # 恢复原始字段名（去掉 DhtmlXQ_ 前缀）
        field_name = key.lower()
        result[field_name] = cleaned_value

    # 特殊处理：如果有 [DhtmlXQHTML] 开头和结尾，可以忽略
    return result


# -----------------------------------------------------#
def load_json(filepath: str):
    """从文件加载 JSON 数据。

    参数:
        filepath: JSON 文件路径

    返回:
        解析后的 JSON 数据，如果文件不存在返回 None
    """

    if not Path(filepath).is_file():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, filepath: str) -> bool:
    """将数据保存为 JSON 文件。

    参数:
        data: 要保存的数据
        filepath: 输出文件路径

    返回:
        bool: 保存是否成功
    """

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return True


# -----------------------------------------------------#
def is_int(s: str) -> bool:
    """判断字符串是否表示一个有效的整数。

    支持：
    - 正整数（如 "123"）
    - 负整数（如 "-456"）
    - 零（如 "0"、"-0"、"+0"）
    - 可选的正负号（"+" 或 "-"）
    - 首尾空格（如 " 123 "）

    不支持：
    - 小数（如 "123.45"）
    - 前导零（如 "00123"，除了 "0" 本身）
    - 其他非数字字符

    参数：
        s (str): 要判断的字符串

    返回：
        bool: True 表示是有效整数字符串，False 表示不是
    """
    s = s.strip()  # 去除首尾空格
    if not s:
        return False

    # 处理可选的正负号
    if s[0] in ("+", "-"):
        s = s[1:]

    if not s:
        return False  # 如 "+" 或 "-"

    # 单独处理 "0"
    if s == "0":
        return True

    # 不允许前导零
    if s[0] == "0":
        return False

    # 其余部分必须全为数字
    return s.isdigit()
