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

from xml.etree import ElementTree as et

from .board import ChessBoard
from .exception import CChessError

# -----------------------------------------------------#


def read_from_cbf(file_name, game=None):  # pylint: disable=too-many-locals
    """从 CBF 文件读取棋局并转换为 `Game` 对象。

    Args:
        file_name: 文件路径
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）
    """
    # 如果提供了game实例，使用它；否则创建新的（向后兼容）
    if game is None:
        from .game import Game  # pylint: disable=import-outside-toplevel

    def decode_move(move_str):
        """decode_move 函数。"""
        p_from = (int(move_str[0]), 9 - int(move_str[1]))
        p_to = (int(move_str[3]), 9 - int(move_str[4]))

        return (p_from, p_to)

    tree = et.parse(file_name)
    root = tree.getroot()

    init_fen = None
    head = root.find("Head")
    for node in list(head):  # .getchildren():
        if node.tag == "FEN":
            init_fen = node.text
        # print node.tag

    if init_fen is None:
        raise CChessError("Missing FEN in CBF file")

    board = ChessBoard(init_fen)

    move_list = list(root.find("MoveList"))  # .getchildren()

    # 如果提供了game实例，使用它；否则创建新的
    if game is None:
        game = Game(board)
    else:
        # 使用提供的game实例
        game.init_board = board
        game.first_move = None
        game.last_move = None
    last_move = None
    step_no = 1
    for node in move_list[1:]:
        move_from, move_to = decode_move(node.attrib["value"])
        if board.is_valid_move(move_from, move_to):
            new_move = board.move(move_from, move_to)
            if last_move is not None:
                last_move.append_next_move(new_move)
            else:
                game.append_next_move(new_move)
            last_move = new_move
        else:
            raise CChessError(f"bad move at {step_no} {move_from}, {move_to}")
        step_no += 1
    return game
