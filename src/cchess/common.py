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

import json
import re
from collections import OrderedDict

# pylint: disable=missing-function-docstring,import-outside-toplevel
# -----------------------------------------------------#
# 从 constants 导入并重新导出，方便其他模块使用
from .constants import (
    ANY_COLOR,
    BLACK,
    EMPTY_BOARD,
    EMPTY_FEN,
    FULL_INIT_BOARD,
    FULL_INIT_FEN,
    RED,
)

# 明确导出列表，避免 Ruff F401 警告
__all__ = [
    "ANY_COLOR",
    "BLACK",
    "EMPTY_BOARD",
    "EMPTY_FEN",
    "FULL_INIT_BOARD",
    "FULL_INIT_FEN",
    "RED",
    "append_move_to_game",
    "next_color",
    "fench_to_txt_name",
    "fench_to_text",
    "text_to_fench",
    "swap_fench",
    "fench_to_species",
    "pos2iccs",
    "iccs2pos",
    "iccs_mirror",
    "iccs_flip",
    "iccs_swap",
    "iccs_list_mirror",
    "half2full",
    "full2half",
    "fen_move_color",
    "get_fen_type",
    "get_fen_type_detail",
    "get_fen_pieces",
    "parse_dhtmlxq",
]


def next_color(color: int) -> int:
    """切换到下一个走子方，对应 ChessPlayer.next() 的逻辑。"""
    return (3 - color) % 3


# -----------------------------------------------------#
_h_dict = {
    "a": "i",
    "b": "h",
    "c": "g",
    "d": "f",
    "e": "e",
    "f": "d",
    "g": "c",
    "h": "b",
    "i": "a",
}

_v_dict = {
    "0": "9",
    "1": "8",
    "2": "7",
    "3": "6",
    "4": "5",
    "5": "4",
    "6": "3",
    "7": "2",
    "8": "1",
    "9": "0",
}


# -----------------------------------------------------#
def pos2iccs(pos_from, pos_to):
    return f"{chr(ord('a') + pos_from[0])}{pos_from[1]}{chr(ord('a') + pos_to[0])}{pos_to[1]}"


def iccs2pos(iccs):
    return (
        (ord(iccs[0]) - ord("a"), int(iccs[1])),
        (ord(iccs[2]) - ord("a"), int(iccs[3])),
    )


def iccs_mirror(iccs):
    return f"{_h_dict[iccs[0]]}{iccs[1]}{_h_dict[iccs[2]]}{iccs[3]}"


def iccs_flip(iccs):
    return f"{iccs[0]}{_v_dict[iccs[1]]}{iccs[2]}{_v_dict[iccs[3]]}"


def iccs_swap(iccs):
    return f"{_h_dict[iccs[0]]}{_v_dict[iccs[1]]}{_h_dict[iccs[2]]}{_v_dict[iccs[3]]}"


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
    return fench.lower() if color == BLACK else fench.upper()


def swap_fench(fench: str) -> str:
    """交换棋子的大小写（红黑互换）。

    大写表示红方、小写表示黑方。该函数将棋子字母大小写取反。

    参数:
        fench: 棋子 FEN 字符，如 'K', 'a', 'r' 等

    返回:
        str: 交换后的棋子字符
    """
    return fench.upper() if fench.islower() else fench.lower()


# 缓存 fench 到 (species, color) 的映射，避免重复计算
_SPECIES_CACHE = {}


def fench_to_species(fen_ch):
    if fen_ch not in _SPECIES_CACHE:
        _SPECIES_CACHE[fen_ch] = (fen_ch.lower(), BLACK if fen_ch.islower() else RED)
    return _SPECIES_CACHE[fen_ch]


# -----------------------------------------------------#
def fen_move_color(fen):
    color = fen.rstrip().split(" ")[1].lower()
    return RED if color == "w" else BLACK




# -----------------------------------------------------#
# 全角半角数字转换映射表
_DIGIT_MAP_FULL_TO_HALF = str.maketrans("１２３４５６７８９", "123456789")
_DIGIT_MAP_HALF_TO_FULL = str.maketrans("123456789", "１２３４５６７８９")


def full2half(text):
    """将全角数字转换为半角数字。"""
    return text.translate(_DIGIT_MAP_FULL_TO_HALF)


def half2full(text):
    """将半角数字转换为全角数字。"""
    return text.translate(_DIGIT_MAP_HALF_TO_FULL)


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
    from pathlib import Path

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
    from pathlib import Path

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
