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

from .board import ChessBoard
from .common import FULL_INIT_FEN, fench_to_species
from .exception import CChessError


# -----------------------------------------------------#
def decode_txt_pos(pos):
    """将两位文本坐标转换为棋盘坐标。"""
    return (int(pos[0]), 9 - int(pos[1]))


# -----------------------------------------------------#
def read_from_txt(moves_txt, pos_txt=None, game=None):  # pylint: disable=too-many-locals
    """从文本棋谱字符串读取并返回 `Game` 对象。

    Args:
        moves_txt: 走法文本
        pos_txt: 位置文本
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）
    """
    # 如果提供了game实例，使用它；否则创建新的（向后兼容）
    if game is None:
        from .game import Game  # pylint: disable=import-outside-toplevel

    # 车马相士帅士相马车炮炮兵兵兵兵兵
    # 车马象士将士象马车炮炮卒卒卒卒卒
    chessman_kinds = "RNBAKABNRCCPPPPP"

    if not pos_txt:
        board = ChessBoard(FULL_INIT_FEN)
    else:
        if len(pos_txt) != 64:
            raise CChessError("bad pos_txt")

        board = ChessBoard()
        for side in range(2):
            for man_index in range(16):
                pos_index = (side * 16 + man_index) * 2
                man_pos = pos_txt[pos_index : pos_index + 2]
                if man_pos == "99":
                    continue
                pos = decode_txt_pos(man_pos)
                fen_ch = chr(ord(chessman_kinds[man_index]) + side * 32)
                board.put_fench(fen_ch, pos)

    last_move = None
    if not moves_txt:
        # 如果提供了game实例，使用它；否则创建新的
        if game is None:
            return Game(board)
        else:
            # 使用提供的game实例
            game.init_board = board
            game.first_move = None
            game.last_move = None
            return game

    step_no = 0
    while step_no * 4 < len(moves_txt):
        # steps = moves_txt[step_no * 4:step_no * 4 + 4]

        move_from = decode_txt_pos(moves_txt[step_no * 4 : step_no * 4 + 2])
        move_to = decode_txt_pos(moves_txt[step_no * 4 + 2 : step_no * 4 + 4])

        if board.is_valid_move(move_from, move_to):
            if not last_move:
                _, man_side = fench_to_species(board.get_fench(move_from))
                board.set_move_side(man_side)
                # 如果提供了game实例，使用它；否则创建新的
                if game is None:
                    game = Game(board)
                else:
                    # 使用提供的game实例
                    game.init_board = board
                    game.first_move = None
                    game.last_move = None
                last_move = game

            new_move = board.move(move_from, move_to)
            last_move.append_next_move(new_move)
            last_move = new_move
        else:
            raise CChessError(f"bad move at {step_no} {move_from} {move_to}")
        step_no += 1
    if step_no == 0:
        # 如果提供了game实例，使用它；否则创建新的
        if game is None:
            game = Game(board)
        else:
            # 使用提供的game实例
            game.init_board = board
            game.first_move = None
            game.last_move = None

    return game


# -----------------------------------------------------#
def ubb_to_dict(ubb_text):
    """解析 UBB 的 DhtmlXQHTML 片段并返回键值字典。"""
    # 先提取整个 [DhtmlXQHTML] ... [/DhtmlXQHTML] 块的内容（去掉外层标签）
    block_match = re.search(
        r"\[DhtmlXQHTML\](.*?)\[/DhtmlXQHTML\]", ubb_text, re.DOTALL
    )
    if not block_match:
        return "{}"

    content = block_match.group(1)

    # 正则匹配所有 [DhtmlXQ_xxx]value[/DhtmlXQ_xxx]
    pattern = r"\[DhtmlXQ_([^]]+)\](.*?)\[/DhtmlXQ_\1\]"
    matches = re.findall(pattern, content, re.DOTALL)

    result = {}
    for key, value in matches:
        cleaned_value = value.strip()
        result[key] = cleaned_value

    return result


# -----------------------------------------------------#
def txt_to_board(pos_txt):
    """将局面文本编码转换为 `ChessBoard`。"""

    # 车马相士帅士相马车炮炮兵兵兵兵兵
    # 车马象士将士象马车炮炮卒卒卒卒卒
    chessman_kinds = "RNBAKABNRCCPPPPP"

    if not pos_txt:
        board = ChessBoard(FULL_INIT_FEN)
    else:
        if len(pos_txt) != 64:
            raise CChessError("bad pos_txt")

        board = ChessBoard()
        for side in range(2):
            for man_index in range(16):
                pos_index = (side * 16 + man_index) * 2
                man_pos = pos_txt[pos_index : pos_index + 2]
                if man_pos == "99":
                    continue
                pos = decode_txt_pos(man_pos)
                fen_ch = chr(ord(chessman_kinds[man_index]) + side * 32)
                board.put_fench(fen_ch, pos)

    return board


# -----------------------------------------------------#
def txt_to_moves(board, moves_txt):
    """将走子文本解析为 `Move` 列表。"""
    moves = []
    step_no = 0
    while step_no * 4 < len(moves_txt):
        move_from = decode_txt_pos(moves_txt[step_no * 4 : step_no * 4 + 2])
        move_to = decode_txt_pos(moves_txt[step_no * 4 + 2 : step_no * 4 + 4])

        if board.is_valid_move(move_from, move_to):
            if len(moves) == 0:
                _, man_side = fench_to_species(board.get_fench(move_from))
                board.set_move_side(man_side)

            new_move = board.move(move_from, move_to)
            moves.append(new_move)
        else:
            raise CChessError(f"bad move at {step_no} {move_from} {move_to}")
        step_no += 1

    return moves


# -----------------------------------------------------#
def read_from_ubb_dhtml(ubb_text, game=None):
    """从 UBB DHTML 文本读取并返回 `Game` 对象。

    Args:
        ubb_text: UBB文本
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）
    """
    # 如果提供了game实例，使用它；否则创建新的（向后兼容）
    if game is None:
        from .game import Game  # pylint: disable=import-outside-toplevel

    info = ubb_to_dict(ubb_text)
    board = txt_to_board(info["binit"])
    moves = txt_to_moves(board, info["movelist"])

    # 如果提供了game实例，使用它；否则创建新的
    if game is None:
        game = Game(board)
    else:
        # 使用提供的game实例
        game.init_board = board
        game.first_move = None
        game.last_move = None

    game.info = info
    for move in moves:
        game.append_next_move(move)

    return game
