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

import re
from typing import Any, Dict, List, NamedTuple, Optional

import chardet

from .board import ChessBoard
from .common import FULL_INIT_FEN


# -----------------------------------------------------#
# 内部数据结构
class PGNMove:
    """PGN 棋步"""

    def __init__(self, notation: str):
        self.notation = notation
        self.annote: Optional[str] = None
        self.variations: List["MoveNode"] = []

    def __str__(self) -> str:
        return self.notation


class MoveNode:
    """PGN 棋步节点"""

    def __init__(self, move: PGNMove):
        self.move = move
        self.next_node: Optional["MoveNode"] = None

    def add_variation(self, variation: "MoveNode") -> None:
        """添加变招"""
        self.move.variations.append(variation)

    def __str__(self) -> str:
        return str(self.move)


class PGNGame(NamedTuple):
    """PGN对局（不可变数据容器）"""

    headers: Dict[str, str]
    moves: Optional[MoveNode]
    result: Optional[str]


# -----------------------------------------------------#
class PGNParser:
    """PGN解析器"""

    def __init__(self):
        """__init__ 方法。"""
        self.tokens = []
        self.current_token_index = 0

    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        """将PGN文本分词"""
        return PGNTokenizer(text).tokenize()

    def parse_headers(self, lines: List[str]) -> Dict[str, str]:
        """解析头信息"""
        headers = {}
        header_pattern = re.compile(r'^\s*\[\s*(\w+)\s+"([^"]*)"\s*\]\s*$')

        for line in lines:
            match = header_pattern.match(line)
            if match:
                key, value = match.groups()
                headers[key] = value

        return headers

    # pylint: disable=too-many-locals,too-many-branches
    def parse_moves(self, tokens):
        """解析棋步序列"""
        if not tokens:
            return None, None

        root = MoveNode(PGNMove("root"))
        current_line = [root]
        stack = [current_line]
        current_node = root
        result = None

        i = 0
        while i < len(tokens):
            token = tokens[i]
            token_type = token["type"]

            if token_type == "move_number":
                # 跳过棋步编号
                pass

            elif token_type == "move":
                current_node, current_line = self._handle_move_token(
                    token, current_node, current_line
                )

            elif token_type == "annote":
                if current_node != root:
                    current_node.move.annote = token["value"]

            elif token_type == "variation_start":
                current_node, current_line = self._handle_variation_start(
                    stack, current_line
                )

            elif token_type == "variation_end":
                current_node, current_line = self._handle_variation_end(
                    stack, current_line
                )

            elif token_type == "result":
                result = token["value"]
                break

            i += 1

        return root.next_node, result

    def _handle_move_token(self, token, current_node, current_line):
        """处理 move token"""
        new_node = MoveNode(PGNMove(token["value"]))
        current_node.next_node = new_node
        current_node = new_node
        current_line.append(new_node)
        return current_node, current_line

    def _handle_variation_start(self, stack, current_line):
        """处理变招开始"""
        stack.append(current_line.copy())
        variation_root = MoveNode(PGNMove("variation_root"))
        current_line = [variation_root]
        return variation_root, current_line

    def _handle_variation_end(self, stack, current_line):
        """处理变招结束"""
        variation_nodes = current_line[1:]  # 跳过根节点
        if variation_nodes:
            prev_main_line = stack[-1]
            parent_node = prev_main_line[-1]

            # 创建变招链表
            variation_head = variation_nodes[0]
            current_var = variation_head
            for node in variation_nodes[1:]:
                current_var.next_node = node
                current_var = node

            parent_node.move.variations.append(variation_head)

        current_line = stack.pop()
        current_node = current_line[-1]
        return current_node, current_line

    # pylint: enable=too-many-locals,too-many-branches

    def parse(self, pgn_text) -> PGNGame:
        """解析完整的PGN文本"""

        # 分割头和棋步部分
        lines = pgn_text.split("\n")
        header_lines = []
        move_lines = []

        in_headers = True
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if in_headers and stripped.startswith("["):
                header_lines.append(stripped)
            else:
                in_headers = False
                move_lines.append(stripped)

        # 解析头信息
        headers = self.parse_headers(header_lines)

        # 解析棋步
        moves_text = " ".join(move_lines)
        tokens = self.tokenize(moves_text)
        moves, result = self.parse_moves(tokens)

        return PGNGame(headers=headers, moves=moves, result=result)


class PGNTokenizer:
    """PGN分词器，使用状态机模式降低复杂度"""

    def __init__(self, text: str):
        self.text = text
        self.tokens: List[Dict[str, Any]] = []
        self.index = 0
        self.length = len(text)

    def tokenize(self) -> List[Dict[str, Any]]:
        """执行分词操作"""
        while self.index < self.length:
            char = self.text[self.index]

            if char.isspace():
                self._skip_whitespace()
            elif char == "{":
                self._process_annotation()
            elif char == "(":
                self._process_variation_start()
            elif char == ")":
                self._process_variation_end()
            elif char.isdigit():
                self._process_move_number()
            elif char in ["1", "0", "½", "*"] and self._is_result_start():
                # 结果标记检查必须在 move 检查之前
                self._process_result()
            elif char.isalpha() or char in "+#=" or not char.isascii():
                # 处理 ASCII 字符和非 ASCII 字符（如中文）
                self._process_move()
            else:
                self.index += 1

        return self.tokens

    def _skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.index < self.length and self.text[self.index].isspace():
            self.index += 1

    def _process_annotation(self) -> None:
        """处理注释"""
        annote_end = self.text.find("}", self.index + 1)
        if annote_end == -1:
            raise ValueError("未匹配的注释结束符 '}'")

        annote = self.text[self.index + 1 : annote_end]
        self.tokens.append({"type": "annote", "value": annote})
        self.index = annote_end + 1

    def _process_variation_start(self) -> None:
        """处理变招开始"""
        self.tokens.append({"type": "variation_start", "value": "("})
        self.index += 1

    def _process_variation_end(self) -> None:
        """处理变招结束"""
        self.tokens.append({"type": "variation_end", "value": ")"})
        self.index += 1

    def _process_move_number(self) -> None:
        """处理棋步编号"""
        start = self.index
        while self.index < self.length and (
            self.text[self.index].isdigit() or self.text[self.index] == "."
        ):
            self.index += 1

        move_number = self.text[start : self.index]
        if "." in move_number:
            self.tokens.append({"type": "move_number", "value": move_number})

    def _process_move(self) -> None:
        """处理棋步"""
        start = self.index
        while self.index < self.length:
            char = self.text[self.index]
            # 处理 ASCII 字符和非 ASCII 字符（如中文）
            if char.isalnum() or char in "+#=." or not char.isascii():
                self.index += 1
            else:
                break

        move = self.text[start : self.index]
        self.tokens.append({"type": "move", "value": move})

    def _process_result(self) -> None:
        """处理结果"""
        start = self.index
        while self.index < self.length and self.text[self.index] not in " \t\n)":
            self.index += 1

        result = self.text[start : self.index]
        self.tokens.append({"type": "result", "value": result})

    def _is_result_start(self) -> bool:
        """检查是否是结果开始"""
        # 检查接下来的3个字符中是否包含-或/或*
        lookahead = min(3, self.length - self.index)
        return any(
            c in self.text[self.index : self.index + lookahead] for c in ["-", "/", "*"]
        )


# -----------------------------------------------------#
class PGNWriter:
    """PGN写入器"""

    def __init__(self, game):
        """__init__ 方法。"""
        self.indent_level = 0
        self.game = game

    def write_headers(self):
        """写入头信息"""
        lines = []
        standard_headers = ["Event", "Date", "Round", "Red", "Black", "Result"]

        lines.append('[Game "Chinese Chess"]')
        # 先写入标准头信息
        for header in standard_headers:
            if header in self.game.info:
                value = self.game.info[header]
                lines.append(f'[{header} "{value}"]')

        # 写入其他头信息
        for header, value in self.game.info.items():
            if header not in standard_headers and header not in ["branchs"]:
                lines.append(f'[{header} "{value}"]')

        # 写入初始局面
        lines.append(f'[Fen "{self.game.init_board.to_fen()}"]')
        # 写入棋局注释
        if self.game.annote:
            lines.append(f"{{{self.game.annote}}}")

        return "\n".join(lines)

    def write_moves(self, move, curr_sibling_index=0):
        """递归写入棋步"""
        if move is None:
            return ""

        lines = []
        current = move

        while current is not None:
            current_move_number = current.step_index

            # 添加棋步编号（红方）
            if current_move_number % 2 == 0:
                lines.append(f"\n{current_move_number // 2 + 1}.")

            # 添加棋步
            lines.append(current.to_text())

            # 添加注释
            if current.annote:
                lines.append(f"{{{current.annote}}}")

            # 只有主变才处理变招，避免循环递归
            if curr_sibling_index == 0:
                for index, variation in enumerate(current.get_variations()):
                    lines.append("\n(")
                    variation_text = self.write_moves(variation, index + 1)
                    lines.append(variation_text.strip())
                    lines.append(")\n")

            current = current.next_move

        return " ".join(lines)

    def write_lines(self):
        """写入完整的PGN"""
        lines = []

        # 写入头信息
        headers = self.write_headers()
        lines.append(headers)

        # 写入棋步
        moves_text = self.write_moves(self.game.first_move)
        lines.append(moves_text)

        # 添加结果
        if "result" in self.game.info:
            lines.append(f"  {self.game.info['result']}")
            lines.append("  =========")

        return "\n".join(lines)

    def save(self, file_name):
        """将生成的 PGN 文本保存到文件。"""
        with open(file_name, "w", encoding="utf-8") as f:
            lines = self.write_lines()
            f.write(lines)


# -----------------------------------------------------#
def _read_pgn_file(file_name):
    """读取 PGN 文件并检测编码

    Args:
        file_name: 文件路径

    Returns:
        str: 文件文本内容
    """
    with open(file_name, "rb") as f:
        raw = f.read()

    # 优先尝试 utf-8，失败后尝试 GBK（PGN 文件常见编码），
    # 最后才依赖 chardet 的检测结果
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("gbk")
        except UnicodeDecodeError:
            detected = chardet.detect(raw)
            encoding = detected.get("encoding", "gbk")
            if encoding and encoding.lower().startswith("utf"):
                encoding = "gbk"
            return raw.decode(encoding, errors="replace")


def _parse_pgn_headers(pgn_game, game):
    """解析 PGN 头信息并设置游戏信息

    Args:
        pgn_game: 解析后的 PGN 游戏对象
        game: Game 对象

    Returns:
        ChessBoard: 初始棋盘（可能被 FEN 头信息覆盖）
    """
    board = game.init_board

    for key, value in pgn_game.headers.items():
        key_lower = key.lower()
        if key_lower == "fen":
            # 处理FEN头信息，设置初始棋盘
            board = ChessBoard(value)
            game.init_board = board
        else:
            game.info[key_lower] = value

    return board


def _try_parse_and_apply_move(board, move_str, game, parent_move):
    """尝试解析并应用一步走法

    Args:
        board: 棋盘对象
        move_str: 走法字符串
        game: Game 对象
        parent_move: 父走法

    Returns:
        tuple: (move, success)
    """
    # 使用 board.move_text() 直接解析并执行走法
    move = board.move_text(move_str)
    if move is None:
        return None, False

    # move已经是Move对象，不需要再创建

    # 添加走法到游戏
    if parent_move is None:
        # 第一个走法
        game.append_next_move(move)
        parent_move = game.first_move
    else:
        # 后续走法
        if game.last_move:
            game.last_move.append_next_move(move)
            game.last_move = move
            parent_move = game.last_move
        else:
            # 如果 last_move 不存在，重新设置
            game.append_next_move(move)
            parent_move = game.first_move

    return move, True


def _process_pgn_moves(node, board, game, parent_move=None):
    """递归处理 PGN 棋步节点

    Args:
        node: 当前节点
        board: 棋盘状态
        game: Game 对象
        parent_move: 父走法
    """
    while node:
        move_str = node.move.notation

        # 跳过结果标记和非法走法字符串
        if move_str in ["1-0", "0-1", "1/2-1/2", "*"]:
            game.info["result"] = move_str
            node = node.next_node
            continue

        try:
            move, success = _try_parse_and_apply_move(
                board, move_str, game, parent_move
            )
            if not success:
                node = node.next_node
                continue

            # 更新 parent_move 用于下一次循环
            parent_move = game.last_move

            # 处理变招
            for variation in node.move.variations:
                # 保存当前棋盘状态（应用走法前的状态）
                saved_board = board.copy()

                # 递归处理变招
                _process_pgn_moves(variation, saved_board, game, parent_move)

        except Exception:
            # 走法解析或应用出错，继续处理下一个走法
            node = node.next_node
            continue

        node = node.next_node


def read_from_pgn(file_name, game_class):
    """从 PGN 文件读取并解析为 `Game` 对象。

    Args:
        file_name: 文件路径
        game_class: Game类，用于创建游戏实例
    """
    board = ChessBoard(FULL_INIT_FEN)

    game = game_class(board)

    # 读取文件
    text = _read_pgn_file(file_name)

    parser = PGNParser()
    try:
        pgn_game = parser.parse(text)

        # 解析头信息
        current_board = _parse_pgn_headers(pgn_game, game)

        # 直接使用当前棋盘，不进行规范化
        # board.move_text() 内部已经使用规范局面处理
        _process_pgn_moves(pgn_game.moves, current_board, game)

    except Exception as e:
        print(f"解析PGN文件时出错: {e}")

    return game
