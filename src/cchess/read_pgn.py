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

import re

import chardet

from .board import ChessBoard
from .common import FULL_INIT_FEN
from .exception import CChessError

# 读取PGN文件的简易版本


# -----------------------------------------------------#
def read_from_pgn(file_name):
    """从 PGN 文件读取并解析为 `Game` 对象。"""
    # 避免循环导入
    from .game import Game  # pylint: disable=import-outside-toplevel

    board = ChessBoard(FULL_INIT_FEN)
    game = Game(board)

    with open(file_name, "rb") as f:
        raw = f.read()

    # 优先尝试 utf-8，失败后尝试 GBK（PGN 文件常见编码），
    # 最后才依赖 chardet 的检测结果
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            detected = chardet.detect(raw)
            encoding = detected.get("encoding", "gbk")
            if encoding and encoding.lower().startswith("utf"):
                encoding = "gbk"
            text = raw.decode(encoding, errors="replace")
    flines = text.splitlines()

    lines = []
    for line in flines:
        it = line.strip()

        if len(it) == 0:
            continue

        lines.append(it)

    lines = __get_headers(game, lines)
    # lines, docs = __get_comments(lines)
    # infos["Doc"] = docs
    __get_steps(game, lines)

    return game


def __get_headers(game, lines):
    """__get_headers 函数。"""
    index = 0
    for it in lines:
        line = it.strip()
        # 匹配 [] 并取出包含的内容
        pattern1 = r"\[([^\[\]]*)\]"
        # 匹配并捕获xxx和YYYY（不包括引号），且它们之间至少有一个空格
        pattern2 = r'(\w+)\s+"\s*([^"]+)"'
        matches = re.findall(pattern1, line)
        if len(matches) == 0:
            return lines[index:]
        for text in matches:
            # print(text)
            match = re.search(pattern2, text)
            if match:
                # match.groups()会返回一个包含所有捕获组的元组
                # 我们可以通过索引来访问它们
                name = match.group(1).lower()
                value = match.group(2)
                if name.lower() == "fen":
                    game.init_board = ChessBoard(value)
                else:
                    game.info[name] = value

        # if len(items) < 3:
        #    raise CChessError(f"Format Error on line {index + 1}")

        # self.infos[str(items[0]).strip()] = items[1].strip()

        index += 1

    return []


def __get_comments(lines):
    """__get_comments 函数。"""
    if lines[0][0] != "{":
        return (lines, None)

    docs = lines[0][1:]

    # 处理一注释行的情况
    if docs[-1] == "}":
        return (lines[1:], docs[:-1].strip())

    # 处理多行注释的情况
    index = 1

    for line in lines[1:]:
        if line[-1] == "}":
            docs = docs + "\n" + line[:-1]
            return (lines[index + 1 :], docs.strip())

        docs = docs + "\n" + line
        index += 1

    # 代码能运行到这里，就是出了异常了
    raise CChessError("Comments not closed")


def _parse_move_text(move_text, piece_chars, multi_piece_markers):
    """解析移动文本，返回待解析的移动列表。"""
    if not move_text:
        return []
    
    # 移除注释
    if "{" in move_text:
        move_text = re.sub(r"\{[^}]*\}", "", move_text).strip()
    
    if not move_text:
        return []
    
    # 找到第二个棋子字符的位置来分割红黑走法
    piece_positions = []
    for j, char in enumerate(move_text):
        if char in piece_chars:
            piece_positions.append(j)
        elif char in multi_piece_markers:
            # "前/中/后"标记，继续查找真正的棋子
            continue
    
    if len(piece_positions) >= 2:
        # 一行两个移动（红方 + 黑方）
        split_pos = piece_positions[1]
        # 检查第二个棋子字符前是否有"前/中/后"标记
        # 如果有，从标记位置开始分割
        for j in range(split_pos - 1, -1, -1):
            if move_text[j] in multi_piece_markers:
                split_pos = j
            elif move_text[j] == ' ':
                continue
            else:
                break
        red_move = move_text[:split_pos].strip()
        black_move = move_text[split_pos:].strip()
        moves = []
        if red_move:
            moves.append(red_move)
        if black_move:
            moves.append(black_move)
        return moves
    else:
        # 只有一个移动
        return [move_text] if move_text else []


def __get_steps(game, lines):
    """__get_steps 函数。"""
    board = game.init_board.copy()

    use_iccs = "format" in game.info and game.info["format"].lower() == "iccs"

    piece_chars = set(
        "\u9a6c\u8f66\u70ae\u5175\u58eb\u76f8\u5c06\u8c61\u5352\u5e05\u4ed5"
    )  # 马车炮兵士相将士象卒帅仕
    multi_piece_markers = set("\u524d\u4e2d\u540e")  # 前中后
    
    pending_black = False  # 跟踪是否需要处理黑方续行

    for line in lines:
        stripped = line.strip()
        if stripped in ["*", "1-0", "0-1", "1/2-1/2", "========="]:
            return game

        if not stripped:
            continue

        # 清理行尾的结束标记
        for marker in ["*", "1-0", "0-1", "1/2-1/2", "========="]:
            stripped = stripped.replace(marker, "").strip()

        # 按步数编号分割
        parts = re.split(r"(\d+)\.", stripped)
        
        # 处理没有移动编号的续行（黑方单独一行）
        if len(parts) == 1:
            if pending_black:
                moves_to_parse = _parse_move_text(stripped, piece_chars, multi_piece_markers)
                pending_black = False
            else:
                continue
        else:
            # 有移动编号的行
            move_text = parts[2].strip() if len(parts) > 2 else ""
            moves_to_parse = _parse_move_text(move_text, piece_chars, multi_piece_markers)
            # 如果只有一个棋子字符，说明是红方单独一行
            piece_count = sum(1 for c in move_text if c in piece_chars)
            pending_black = piece_count == 1

        # 解析移动
        for it in moves_to_parse:
            if not it:
                continue
            if use_iccs:
                new_it = it.replace("-", "")
                move = board.move_iccs(new_it.lower())
            else:
                move = board.move_text(it)
            if move:
                game.append_next_move(move)

    return game
