# -*- coding: utf-8 -*-
"""
Copyright (C) 2024  walker li <walker8088@gmail.com>

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

import os
from pathlib import Path

from cchess import FULL_INIT_FEN, Book, ChessBoard
from cchess.io_xqf import read_from_xqf

# result_dict = {'红胜': RED_WIN, '黑胜': BLACK_WIN, '和棋': PEACE}
result_dict = {"红胜": "1-0", "黑胜": "0-1", "和棋": "1/2-1/2"}


def load_move_txt(txt_file):
    with open(txt_file, "rb") as f:
        lines = f.readlines()
    fen = lines[0].strip().decode("utf-8")
    moves = [it.strip().decode("utf-8") for it in lines[1:-1]]
    result = result_dict[lines[-1].strip().decode("utf-8")]
    return (fen, moves, result)


class TestReaderXQF:
    def setup_method(self):
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    def teardown_method(self):
        pass

    """
    def test_base(self):
        book = read_from_xqf(Path("data", "WildHouse.xqf"))
        moves = book.dump_moves()
        #assert moves == ''
    """

    def test_base(self):
        read_from_xqf(Path("tests", "data", "game_test.xqf"), Book)
        # assert moves == ''

    def test_k1(self):
        fen, moves, result = load_move_txt(Path("tests", "data", "test1_move.txt"))
        book = read_from_xqf(Path("tests", "data", "test1.xqf"), Book)
        assert book.init_board.to_fen() == fen
        assert book.info["result"] == result

        # book.print_init_board()
        m = book.dump_text_moves()[0]
        assert len(m) == len(moves)
        for i in range(len(m)):
            assert m[i] == moves[i]


class TestBookExtended:
    def setup_method(self):
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    def test_book_mirror_flip_swap(self):
        book = Book()
        test_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABN1 w"
        book.init_board.from_fen(test_fen)
        original_fen = book.init_board.to_fen()

        # mirror
        book.mirror()
        mirrored_fen = book.init_board.to_fen()
        assert mirrored_fen != original_fen
        book.mirror()  # 再次mirror应该恢复
        assert book.init_board.to_fen() == original_fen

        # flip
        book.flip()
        flipped_fen = book.init_board.to_fen()
        assert flipped_fen != original_fen
        book.flip()  # 再次flip应该恢复
        assert book.init_board.to_fen() == original_fen

        # swap
        book.swap()
        swapped_fen = book.init_board.to_fen()
        assert swapped_fen != original_fen
        book.swap()  # 再次swap应该恢复
        assert book.init_board.to_fen() == original_fen

    def test_iter_moves(self):
        book = Book()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((1, 2), (1, 1))
        move1.append_next_move(move2)

        book.append_first_move(move1)

        moves = list(book.iter_moves())
        assert len(moves) >= 1
        assert moves[0] == move1

        # 测试从指定move开始迭代
        moves_from_move2 = list(book.iter_moves(move2))
        assert len(moves_from_move2) >= 0

    def test_dump_init_board(self):
        book = Book()
        book.init_board.from_fen(FULL_INIT_FEN)
        board_dump = book.dump_init_board()
        assert isinstance(board_dump, list)
        assert len(board_dump) == 22  # 棋盘有10行，打印出来22行数据

    def test_append_first_move(self):
        book = Book()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move_text("车九进一")

        result = book.append_first_move(move1)
        assert result == move1
        assert book.first_move == move1
        assert book.last_move == move1

        # 添加第二个move作为分支
        move2 = board.copy().move_text("炮八退一")
        book.append_first_move(move2)
        assert len(book.first_move.variations_all) == 2

    def test_append_next_move(self):
        book = Book()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.move_text("车九进一")
        book.append_first_move(move1)
        # Note: move_text already switches turns, so no need to call next_turn()
        move2 = board.move_text("炮2平5")
        book.append_next_move(move2)

        assert book.first_move == move1
        assert book.last_move == move2
        assert book.first_move.next_move == move2
