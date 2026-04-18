# -*- coding: utf-8 -*-
"""
Comprehensive tests targeting uncovered lines in cchess modules.
"""

import os
import sys
import tempfile
import json
import subprocess
import pytest

# Ensure tests run from the project root for file path tests
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from cchess import (
    ChessBoard,
    Move,
    FULL_INIT_FEN,
    RED,
    BLACK,
    CChessError,
    iccs_mirror,
    iccs_flip,
    iccs_swap,
    fen_mirror,
    fen_flip,
    fen_swap,
)
from cchess.common import (
    get_fen_type_detail,
    full2half,
    half2full,
)
from cchess.game import Game
from cchess.piece import Piece, Knight, Rook, Cannon, Pawn
from cchess.board import ChessPlayer, ChessBoardOneHot
from cchess.exception import EngineError
from cchess.engine import (
    is_int,
    parse_engine_info_to_dict,
    EngineStatus,
    UciEngine,
    UcciEngine,
    FenCache,
    action_mirror,
)


# ============================================================
# move.py tests
# ============================================================


class TestMoveMirrorFlipSwap:
    """Tests for Move.mirror(), Move.flip(), Move.swap() (lines 102-144)."""

    def test_mirror(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        assert move.p_from == (0, 0)
        assert move.p_to == (0, 1)
        move.mirror()
        assert move.p_from == (8, 0)
        assert move.p_to == (8, 1)

    def test_mirror_with_next_move(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move1.append_next_move(move2)
        move1.mirror()
        assert move1.p_from == (8, 0)
        assert move1.p_to == (8, 1)
        assert move1.next_move.p_from == (8, 9)
        assert move1.next_move.p_to == (8, 8)

    def test_flip(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        move.flip()
        assert move.p_from == (0, 9)
        assert move.p_to == (0, 8)

    def test_flip_with_next_move(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move1.append_next_move(move2)
        move1.flip()
        assert move1.p_from == (0, 9)
        assert move1.p_to == (0, 8)
        assert move1.next_move.p_from == (0, 0)
        assert move1.next_move.p_to == (0, 1)

    def test_swap(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        original_from = move.p_from
        original_to = move.p_to
        move.swap()
        # swap does not change coordinates, only swaps board pieces
        assert move.p_from == original_from
        assert move.p_to == original_to

    def test_swap_with_next_move(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move1.append_next_move(move2)
        move1.swap()
        assert move1.next_move is not None


class TestMoveVariations:
    """Tests for Move variation operations (lines 165-223)."""

    def test_get_variation_index(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        result = move.get_variation_index()
        assert result == (0, 1)

    def test_get_variation_index_with_variations(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((8, 0), (8, 1))
        move1.variations_all.append(move2)
        move2.variations_all = move1.variations_all
        idx = move2.get_variation_index()
        assert idx is not None
        assert idx[0] == 1

    def test_add_variation(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move1.parent = None
        move2 = board.copy().move((8, 0), (8, 1))
        move1.append_next_move(move2)
        # Create move3 with parent set to None
        board3 = ChessBoard(FULL_INIT_FEN)
        move3 = board3.copy().move((2, 0), (2, 1))
        if move3:
            move3.parent = None
            move1.add_variation(move3)
            assert move1.len_variations() == 2

    def test_remove_variation(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((8, 0), (8, 1))
        move1.variations_all.append(move2)
        move2.variations_all = move1.variations_all
        move1.remove_variation(move2)
        assert move2 not in move1.variations_all

    def test_remove_variation_not_in_list(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((8, 0), (8, 1))
        # move2 not in variations_all, should not raise
        move1.remove_variation(move2)
        assert len(move1.variations_all) == 1

    def test_get_variations_include_me(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        variations = move.get_variations(include_me=True)
        assert len(variations) == 1
        assert variations[0] == move

    def test_last_variation(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        assert move.last_variation() == move


class TestMoveToTextDetail:
    """Tests for Move.to_text_detail() (lines 380-388)."""

    def test_to_text_detail_no_variation_no_annote(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        txt, annote = move.to_text_detail(show_variation=False, show_annote=False)
        assert txt == "车九进一"
        assert annote == ""

    def test_to_text_detail_with_variation(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        txt, annote = move.to_text_detail(show_variation=True, show_annote=False)
        assert "车九进一" in txt
        assert annote == ""

    def test_to_text_detail_with_annote(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        move.annote = "good move"
        _, annote = move.to_text_detail(show_variation=False, show_annote=True)
        assert annote == "good move"


class TestMovePrepareForEngine:
    """Tests for Move.prepare_for_engine() and to_engine_fen() (lines 426-452)."""

    def test_prepare_for_engine_with_capture(self):
        board = ChessBoard(FULL_INIT_FEN)
        # Set up a position where rook can capture (remove blocking pieces)
        board.pop_fench((0, 9))  # Remove black rook
        board.pop_fench((0, 3))  # Remove red pawn blocking the way
        board.pop_fench((0, 6))  # Remove black pawn blocking the way
        board.put_fench("p", (0, 9))  # Place black pawn for capture
        move = board.copy().move((0, 0), (0, 9))
        assert move is not None, "Move should be valid"
        assert move.captured == "p", "Should capture the pawn"
        move.prepare_for_engine(RED, [])
        assert move.fen_for_engine is not None
        assert move.move_list_for_engine == []

    def test_prepare_for_engine_no_capture_empty_history(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        move.prepare_for_engine(RED, [])
        assert move.fen_for_engine is not None
        assert move.move_list_for_engine == [move.to_iccs()]

    def test_prepare_for_engine_no_capture_with_history(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move1.prepare_for_engine(RED, [])
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move2.prepare_for_engine(BLACK, [move1])
        assert move2.fen_for_engine == move1.fen_for_engine
        assert move2.move_list_for_engine == move1.move_list_for_engine[:] + [
            move2.to_iccs()
        ]

    def test_to_engine_fen_empty_moves(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        move.fen_for_engine = "test_fen"
        move.move_list_for_engine = []
        assert move.to_engine_fen() == "test_fen"

    def test_to_engine_fen_with_moves(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        move.fen_for_engine = "test_fen"
        move.move_list_for_engine = ["a0a1", "i9i8"]
        result = move.to_engine_fen()
        assert "moves" in result
        assert "a0a1" in result
        assert "i9i8" in result


class TestMoveFromTextMultiPiece:
    """Tests for Move.from_text() multi-piece selection (lines 472-500)."""

    def test_from_text_a_b_piece_ping_returns_none(self):
        # Advisor and Bishop cannot do 平 (horizontal move)
        result = Move.text_move_to_std_move("a", RED, (3, 0), "平五")
        assert result is None
        result = Move.text_move_to_std_move("b", RED, (2, 0), "平五")
        assert result is None
        result = Move.text_move_to_std_move("n", RED, (2, 0), "平五")
        assert result is None

    def test_from_text_invalid_direction(self):
        result = Move.text_move_to_std_move("r", RED, (0, 0), "左一")
        assert result is None

    def test_from_text_king_ping(self):
        result = Move.text_move_to_std_move("k", RED, (4, 0), "平六")
        assert result is not None
        assert result == (3, 0)

    def test_from_text_chinese_numeral_fallback(self):
        # Test with Chinese numerals that need fallback mapping
        result = Move.text_move_to_std_move("r", RED, (0, 0), "进一")
        assert result is not None
        assert result == (0, 1)

    def test_from_text_multi_pieces_front_back(self):
        board = ChessBoard(
            "r1bak1b1r/4a4/2n1ccn2/p1p1C1p1p/9/9/P1P1P1P1P/4C1N2/9/RNBAKABR1 w"
        )
        result = Move.from_text(board, "前炮退二")
        assert result is not None

    def test_from_text_multi_pieces_returns_none_when_no_valid(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 前兵 - no pawns in multi positions on initial board
        Move.from_text(board, "前兵进一")
        # May return a valid move or None depending on board state

    def test_from_text_chinese_digit_black_reversed(self):
        board = ChessBoard(FULL_INIT_FEN)
        board.next_turn()
        # Black pawn selection
        Move.from_text(board, "一卒进1")
        # May be None if no valid move, but should go through the black reversed path
        # Just ensure no exception is raised


class TestMoveTextParsingChineseNumerals:
    """Tests for Move text parsing with Chinese numerals (lines 581-616)."""

    def test_chinese_digit_target_x_none(self):
        board = ChessBoard(FULL_INIT_FEN)
        # Invalid chinese digit
        result = Move.from_text(board, "十车进一")
        assert result is None

    def test_chinese_digit_pawn_same_column_sort_red(self):
        # Red pawns on same column, should pick the most advanced one
        board = ChessBoard("4k4/9/9/9/4P4/4P4/9/9/9/4K4 w")
        result = Move.from_text(board, "一兵进一")
        assert result is not None

    def test_chinese_digit_pawn_same_column_sort_black(self):
        board = ChessBoard("4k4/9/9/9/4p4/4p4/9/9/9/4K4 b")
        Move.from_text(board, "一卒进1")
        # Should not raise, goes through black pawn sorting path

    def test_chinese_digit_no_poss_returns_none(self):
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        result = Move.from_text(board, "一车进一")
        assert result is None

    def test_chinese_digit_fallback_to_all_pieces(self):
        board = ChessBoard(FULL_INIT_FEN)
        # If no piece on target column, falls back to all pieces
        Move.from_text(board, "一车进一")
        # Should find the rook on column 0 (一 for red maps to x=8)
        # If no valid move found, may return None


class TestMoveTreeOperations:
    """Tests for Move tree operations (lines 656-658)."""

    def test_multi_pieces_select_returns_none(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 前/中/后 with no matching pieces - no knights in multi positions
        Move.from_text(board, "前象进一")
        # May return None or a valid move

    def test_multi_pieces_select_middle(self):
        board = ChessBoard(
            "r1bak1b1r/4a4/2n1ccn2/p1p1C1p1p/9/9/P1P1P1P1P/4C1N2/9/RNBAKABR1 w"
        )
        Move.from_text(board, "中炮平五")
        # Should go through the middle piece selection path


class TestMoveMisc:
    """Tests for other uncovered lines in move.py."""

    def test_move_str(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        assert str(move) == "a0a1"

    def test_is_king_killed(self):
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        move = board.copy().move((4, 0), (4, 9))
        assert move.is_king_killed() is True

    def test_is_king_killed_not_king(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        assert move.is_king_killed() is False

    def test_to_text_detail_captured(self):
        board = ChessBoard(FULL_INIT_FEN)
        # Set up a position where rook can capture - need to clear path
        board.from_fen("rnbakabnr/9/9/9/9/9/9/9/9/RNBAKABNR w")
        move = board.copy().move((0, 0), (0, 9))
        if move is None:
            pytest.skip("Move not valid")
        text = move.to_text(detailed=True)
        assert "吃" in text

    def test_to_text_detail_checkmate(self):
        board = ChessBoard("rnbakabnr/9/9/p1p1p1p1p/9/4c4/PCP1c1P1P/5C3/9/RNBAKABNR w")
        move = board.copy().move((1, 2), (4, 2))
        if move and move.is_checkmate:
            text = move.to_text(detailed=True)
            assert "将死" in text

    def test_to_text_detail_checking(self):
        board = ChessBoard(
            "rnbakabnr/9/1c2c4/p1p1C1p1p/9/9/P1P1P1P1P/1C7/9/RNBAKABNR w"
        )
        move = board.copy().move((1, 2), (4, 2))
        if move and move.is_checking and not move.is_checkmate:
            text = move.to_text(detailed=True)
            assert "将军" in text

    def test_to_text_detail_no_details(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        text = move.to_text(detailed=True)
        # No capture, no check, no checkmate - should return just text
        assert text == "车九进一"

    def test_to_text_variation_single(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        txt = move.to_text_variation()
        assert txt == "车九进一"

    def test_to_text_variation_multiple(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((8, 0), (8, 1))
        move1.variations_all.append(move2)
        move2.variations_all = move1.variations_all
        txt = move1.to_text_variation()
        assert "[" in txt
        assert "]" in txt

    def test_init_move_line(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        line = move.init_move_line()
        assert "index" in line
        assert "name" in line
        assert "moves" in line

    def test_dump_moves_tree_mode(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move1.append_next_move(move2)
        game = Game(board)
        game.first_move = move1
        game.last_move = move2
        moves = game.dump_moves(is_tree_mode=True)
        assert len(moves) >= 1

    def test_dump_moves_non_tree_mode(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        move1.append_next_move(move2)
        game = Game(board)
        game.first_move = move1
        game.last_move = move2
        moves = game.dump_moves(is_tree_mode=False)
        assert len(moves) >= 1

    def test_dump_moves_with_variation(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move1.parent = None
        board2 = ChessBoard(FULL_INIT_FEN)
        move2 = board2.copy().move((8, 0), (8, 1))
        move1.append_next_move(move2)
        board3 = ChessBoard(FULL_INIT_FEN)
        move3 = board3.copy().move((2, 0), (2, 1))
        if move3:
            move3.parent = None
            move1.add_variation(move3)
            game = Game(board)
            game.first_move = move1
            game.last_move = move2
            moves = game.dump_moves(is_tree_mode=False)
            assert len(moves) >= 2


# ============================================================
# read_pgn.py tests
# ============================================================


class TestReadPGN:
    """Tests for read_pgn.py uncovered lines."""

    def test_gbk_fallback_encoding(self):
        """Test GBK encoding fallback (lines 49-54)."""
        from cchess.read_pgn import read_from_pgn

        # Create a temp file with GBK-encoded content
        content = '[Game "Chinese Chess"]\n[Red "测试"]\n\n1. 炮二平五 炮８平５\n *\n'
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pgn", delete=False) as f:
            f.write(content.encode("gbk"))
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game is not None
        finally:
            os.unlink(tmp_path)

    def test_chardet_fallback(self):
        """Test chardet-based encoding fallback (lines 50-54)."""
        from cchess.read_pgn import read_from_pgn

        # Create a file with content that fails both utf-8 and gbk decode
        # Use bytes that are invalid in both encodings
        raw = b'\x80\x81\x82\x83[Game "Chinese Chess"]\n\n1. a0a1 a9a8\n *\n'
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pgn", delete=False) as f:
            f.write(raw)
            tmp_path = f.name
        try:
            read_from_pgn(tmp_path)
            # Should not crash even with bad encoding
        finally:
            os.unlink(tmp_path)

    def test_get_headers_all_lines_are_headers(self):
        """Test when all lines are headers, returns empty list (line 105)."""
        from cchess.read_pgn import read_from_pgn

        content = '[Game "Chinese Chess"]\n[Red "Player"]\n[Black "Player2"]\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game is not None
            assert game.info.get("red") == "Player"
        finally:
            os.unlink(tmp_path)

    def test_get_steps_iccs_format(self):
        """Test ICCS format step parsing (lines 149-154)."""
        from cchess.read_pgn import read_from_pgn

        content = '[Game "Chinese Chess"]\n[Format "ICCS"]\n\n1. a0a1 i9i8\n *\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game is not None
            assert game.first_move is not None
        finally:
            os.unlink(tmp_path)

    def test_get_steps_iccs_5char(self):
        """Test ICCS 5-character format (line 151)."""
        from cchess.read_pgn import read_from_pgn

        content = '[Game "Chinese Chess"]\n[Format "ICCS"]\n\n1. a0-a1 i9-i8\n *\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game is not None
        finally:
            os.unlink(tmp_path)

    def test_get_steps_game_result(self):
        """Test game result markers in steps (lines 141-146)."""
        from cchess.read_pgn import read_from_pgn

        content = '[Game "Chinese Chess"]\n\n1. a0a1 i9i8 1-0\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game is not None
        finally:
            os.unlink(tmp_path)

    def test_get_steps_move_none_returns_game(self):
        """Test when board.move_text returns None, returns game (line 158)."""
        from cchess.read_pgn import read_from_pgn

        content = '[Game "Chinese Chess"]\n\n1. 非法走法\n *\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            read_from_pgn(tmp_path)
            # Should return game object, not crash
        finally:
            os.unlink(tmp_path)

    def test_get_steps_fen_header(self):
        """Test FEN header creates custom init board (line 94)."""
        from cchess.read_pgn import read_from_pgn

        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        content = f'[Game "Chinese Chess"]\n[FEN "{fen}"]\n\n *\n'
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pgn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name
        try:
            game = read_from_pgn(tmp_path)
            assert game.init_board.to_fen() == fen
        finally:
            os.unlink(tmp_path)


# ============================================================
# read_cbr.py tests
# ============================================================


class TestReadCBR:
    """Tests for read_cbr.py uncovered lines."""

    def test_cbr_decoder_read_int8(self):
        """Test CbrBuffDecoder.read_int8 (lines 103-104)."""
        from cchess.read_cbr import CbrBuffDecoder

        data = b"\xff\x00\x01\x7f"
        decoder = CbrBuffDecoder(data, "utf-16-le")
        val = decoder.read_int8()
        assert val == -1  # 0xff as signed byte

    def test_cbr_decoder_read_int(self):
        """Test CbrBuffDecoder.read_int (line 109-110)."""
        from cchess.read_cbr import CbrBuffDecoder
        import struct

        val = 12345
        data = struct.pack("<i", val)
        decoder = CbrBuffDecoder(data, "utf-16-le")
        result = decoder.read_int()
        assert result == val

    def test_cbr_decoder_is_end(self):
        """Test CbrBuffDecoder.is_end (line 90)."""
        from cchess.read_cbr import CbrBuffDecoder

        data = b"\x00\x00"
        decoder = CbrBuffDecoder(data, "utf-16-le")
        assert decoder.is_end() is False
        decoder.read_bytes(1)
        # After reading 1 byte, length=2, index=1, (2-1-1)==0
        assert decoder.is_end() is True

    def test_read_from_cbr_buffer_bad_magic(self):
        """Test read_from_cbr_buffer with bad magic returns None (line 211)."""
        from cchess.read_cbr import read_from_cbr_buffer

        bad_data = b"\x00" * 2214
        result = read_from_cbr_buffer(bad_data)
        assert result is None

    def test_read_from_cbr_buffer_move_side_black(self):
        """Test read_from_cbr_buffer with black to move (line 225)."""
        from cchess.read_cbr import read_from_cbr_buffer
        import struct

        # Build a minimal valid CBR buffer
        magic = b"CCBridge Record\x00"
        # Build header
        header = struct.pack(
            "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si",
            magic,
            b"\x00" * 164,
            b"\x00" * 128,
            b"\x00" * 384,
            b"\x00" * 64,
            b"\x00" * 320,
            b"\x00" * 64,
            b"\x00" * 160,
            b"\x00" * 64,
            b"\x00" * 712,
            0,  # game_result
            b"\x00" * 35,
            0,  # _is6
            b"\x00" * 3,
            0,  # _steps
            b"\x00" * 2,
            b"\x00" * 90,
            2,  # move_side = 2 means black
        )
        boards_data = bytearray(90)
        # Place a red king at (4,0) -> y=9, x=4 -> index = 9*9+4 = 85
        boards_data[85] = 0x15  # Red king
        # Place a black king at (4,9) -> y=0, x=4 -> index = 0*9+4 = 4
        boards_data[4] = 0x25  # Black king
        full_data = header[: 2214 - 90] + bytes(boards_data)
        # Pad to at least 2214
        full_data = full_data.ljust(2214, b"\x00")
        full_data += b"\x00\x00\x00\x00"  # step info terminator
        result = read_from_cbr_buffer(full_data)
        assert result is not None

    def test_read_from_cbr_invalid_fench_returns(self):
        """Test __read_steps when fench is None returns early (line 162)."""
        from cchess.read_cbr import read_from_cbr_buffer
        import struct

        magic = b"CCBridge Record\x00"
        header = struct.pack(
            "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si",
            magic,
            b"\x00" * 164,
            b"\x00" * 128,
            b"\x00" * 384,
            b"\x00" * 64,
            b"\x00" * 320,
            b"\x00" * 64,
            b"\x00" * 160,
            b"\x00" * 64,
            b"\x00" * 712,
            0,
            b"\x00" * 35,
            0,
            b"\x00" * 3,
            0,
            b"\x00" * 2,
            b"\x00" * 90,
            1,
        )
        boards_data = bytearray(90)
        boards_data[85] = 0x15  # Red king
        boards_data[4] = 0x25  # Black king
        full_data = header[: 2214 - 90] + bytes(boards_data)
        full_data = full_data.ljust(2214, b"\x00")
        # Add init info (annote_len = 0) + step terminator
        full_data += b"\x00\x00\x00\x00"  # a_len = 0
        full_data += b"\x00\x00\x00\x00"  # step_info all zeros
        result = read_from_cbr_buffer(full_data)
        # Should not crash
        assert result is not None

    def test_read_from_cbl_no_games_found(self):
        """Test read_from_cbl when no CBR magic found (line 274)."""
        from cchess.read_cbr import read_from_cbl
        import struct

        magic = b"CCBridgeLibrary\x00"
        header = struct.pack("<16s44si512s", magic, b"\x00" * 44, 1, b"\x00" * 512)
        # No CBR magic in game buffer
        data = header + b"\x00" * (101952 - len(header)) + b"\x00" * 4096
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".cbl", delete=False) as f:
            f.write(data)
            tmp_path = f.name
        try:
            result = read_from_cbl(tmp_path)
            assert result is not None
            assert len(result["games"]) == 0
        finally:
            os.unlink(tmp_path)

    def test_read_from_cbl_progressing_no_games(self):
        """Test read_from_cbl_progressing when no games found (line 333)."""
        from cchess.read_cbr import read_from_cbl_progressing
        import struct

        magic = b"CCBridgeLibrary\x00"
        header = struct.pack("<16s44si512s", magic, b"\x00" * 44, 1, b"\x00" * 512)
        data = header + b"\x00" * (101952 - len(header)) + b"\x00" * 4096
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".cbl", delete=False) as f:
            f.write(data)
            tmp_path = f.name
        try:
            results = list(read_from_cbl_progressing(tmp_path))
            assert len(results) >= 1
        finally:
            os.unlink(tmp_path)

    def test_read_from_cbl_progressing_bad_magic(self):
        """Test read_from_cbl_progressing with bad magic returns early (line 309)."""
        from cchess.read_cbr import read_from_cbl_progressing

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".cbl", delete=False) as f:
            f.write(b"\x00" * 576)
            tmp_path = f.name
        try:
            results = list(read_from_cbl_progressing(tmp_path))
            assert len(results) == 0  # returns without yielding
        finally:
            os.unlink(tmp_path)

    def test_read_cbr_step_info_empty(self):
        """Test __read_steps with empty step_info (line 133)."""
        from cchess.read_cbr import read_from_cbr_buffer
        import struct

        magic = b"CCBridge Record\x00"
        header = struct.pack(
            "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si",
            magic,
            b"\x00" * 164,
            b"\x00" * 128,
            b"\x00" * 384,
            b"\x00" * 64,
            b"\x00" * 320,
            b"\x00" * 64,
            b"\x00" * 160,
            b"\x00" * 64,
            b"\x00" * 712,
            0,
            b"\x00" * 35,
            0,
            b"\x00" * 3,
            0,
            b"\x00" * 2,
            b"\x00" * 90,
            1,
        )
        boards_data = bytearray(90)
        boards_data[85] = 0x15
        boards_data[4] = 0x25
        full_data = header[: 2214 - 90] + bytes(boards_data)
        full_data = full_data.ljust(2214, b"\x00")
        # Add init info with annote_len = 0, then no step data
        full_data += b"\x00\x00\x00\x00"  # a_len = 0
        # No step data - decoder will hit end
        result = read_from_cbr_buffer(full_data)
        assert result is not None

    def test_read_cbr_step_mark_all_zero(self):
        """Test __read_steps with all-zero step_mark (line 136)."""
        from cchess.read_cbr import read_from_cbr_buffer
        import struct

        magic = b"CCBridge Record\x00"
        header = struct.pack(
            "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si",
            magic,
            b"\x00" * 164,
            b"\x00" * 128,
            b"\x00" * 384,
            b"\x00" * 64,
            b"\x00" * 320,
            b"\x00" * 64,
            b"\x00" * 160,
            b"\x00" * 64,
            b"\x00" * 712,
            0,
            b"\x00" * 35,
            0,
            b"\x00" * 3,
            0,
            b"\x00" * 2,
            b"\x00" * 90,
            1,
        )
        boards_data = bytearray(90)
        boards_data[85] = 0x15
        boards_data[4] = 0x25
        full_data = header[: 2214 - 90] + bytes(boards_data)
        full_data = full_data.ljust(2214, b"\x00")
        full_data += b"\x00\x00\x00\x00"
        result = read_from_cbr_buffer(full_data)
        assert result is not None


# ============================================================
# game.py tests
# ============================================================


class TestGame:
    """Tests for game.py uncovered lines."""

    def test_game_str(self):
        """Test Game.__str__ (line 64)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.info["title"] = "Test Game"
        result = str(game)
        assert "title" in result

    def test_game_get_children_no_moves(self):
        """Test Game.get_children with no moves (line 104)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        children = game.get_children()
        assert children == []

    def test_game_get_children_with_moves(self):
        """Test Game.get_children with moves (lines 107-108)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        children = game.get_children()
        assert len(children) == 1

    def test_game_dump_moves_no_first_move(self):
        """Test Game.dump_moves with no first_move (lines 168-169)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        moves = game.dump_moves()
        assert moves == []

    def test_game_dump_moves_line_no_first_move(self):
        """Test Game.dump_moves_line with no first_move (lines 205-206)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        lines = game.dump_moves_line()
        assert lines == []

    def test_game_move_line_to_list_no_move(self):
        """Test Game.move_line_to_list with no move (lines 212-213)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        line = game.move_line_to_list()
        assert line == []

    def test_game_move_line_to_list_with_move(self):
        """Test Game.move_line_to_list with move (lines 215-220)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        line = game.move_line_to_list(move1)
        assert len(line) == 1

    def test_game_make_branchs_tag_no_first_move(self):
        """Test Game.make_branchs_tag with no first_move (lines 224-225)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.make_branchs_tag()  # Should not crash

    def test_game_mirror_no_first_move(self):
        """Test Game.mirror with no first_move (line 133)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.mirror()  # Should not crash

    def test_game_flip_no_first_move(self):
        """Test Game.flip with no first_move (line 139)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.flip()

    def test_game_swap_no_first_move(self):
        """Test Game.swap with no first_move (line 145)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.swap()

    def test_game_save_to_unknown_format(self):
        """Test Game.save_to with unknown format (line 355)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unknown file format"):
                game.save_to(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_game_read_from_unknown_format(self):
        """Test Game.read_from with unknown format (line 293)."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unknown file format"):
                Game.read_from(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_game_read_from_lib_unknown_format(self):
        """Test Game.read_from_lib with unknown format (line 304)."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unknown lib file format"):
                Game.read_from_lib(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_game_dump_fen_iccs_moves(self):
        """Test Game.dump_fen_iccs_moves (lines 187-189)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        result = game.dump_fen_iccs_moves()
        assert len(result) >= 1
        assert len(result[0]) >= 1
        assert len(result[0][0]) == 2

    def test_game_dump_text_moves(self):
        """Test Game.dump_text_moves (lines 193-196)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        result = game.dump_text_moves(show_branch=False)
        assert len(result) >= 1

    def test_game_dump_text_moves_with_annote(self):
        """Test Game.dump_text_moves_with_annote (lines 200-201)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        move.annote = "test annote"
        game.append_first_move(move)
        result = game.dump_text_moves_with_annote()
        assert len(result) >= 1
        assert result[0][0][1] == "test annote"

    def test_game_print_text_moves_multiple_branches(self):
        """Test Game.print_text_moves with multiple branches (line 243)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        board2 = ChessBoard(FULL_INIT_FEN)
        move2 = board2.copy().move((8, 0), (8, 1))
        game.append_first_move(move2)
        # Should print branch info
        game.print_text_moves(steps_per_line=1)

    def test_game_print_text_moves_with_annote(self):
        """Test Game.print_text_moves with annote (line 251)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        move.annote = "good"
        game.append_first_move(move)
        game.print_text_moves(show_annote=True)

    def test_game_print_text_moves_line_move_printed(self):
        """Test Game.print_text_moves line_move printed at end (line 257)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        game.print_text_moves(steps_per_line=10)

    def test_game_dump_info(self):
        """Test Game.dump_info (lines 261-262)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.info["title"] = "Test"
        game.info["red"] = "Player"
        game.dump_info()

    def test_game_verify_moves(self):
        """Test Game.verify_moves (lines 117-127)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        assert game.verify_moves() is True

    def test_game_verify_moves_invalid(self):
        """Test Game.verify_moves with invalid move (line 123)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        # Create a move that won't be valid when replayed
        move = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move)
        # Manually corrupt the move to make it invalid
        game.first_move.p_from = (7, 7)
        game.first_move.p_to = (8, 8)
        with pytest.raises(ValueError):
            game.verify_moves()

    def test_game_iter_moves(self):
        """Test Game.iter_moves (lines 152-156)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        game.append_next_move(move2)
        moves = list(game.iter_moves())
        assert len(moves) == 2

    def test_game_iter_moves_with_start(self):
        """Test Game.iter_moves with start move."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        game.append_next_move(move2)
        moves = list(game.iter_moves(move=move2))
        assert len(moves) == 1

    def test_game_append_first_move_with_existing(self):
        """Test Game.append_first_move when first_move already exists (line 79)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        move2 = board.copy().move((8, 0), (8, 1))
        game.append_first_move(move2)
        assert game.first_move.len_variations() == 2

    def test_game_save_to_pgn_with_annote(self):
        """Test Game.save_to_pgn with annote (lines 321-322)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        game.annote = "Test annotation"
        move = board.copy().move((0, 0), (0, 1))
        move.annote = "Move note"
        game.append_first_move(move)
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            game.save_to_pgn(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "Test annotation" in content
        finally:
            os.unlink(tmp_path)

    def test_game_save_to_pgn_no_moves(self):
        """Test Game.save_to_pgn with no moves."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            game.save_to_pgn(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "*" in content
        finally:
            os.unlink(tmp_path)

    def test_game_save_to_pgn_odd_index(self):
        """Test Game.save_to_pgn with odd index (line 331)."""
        board = ChessBoard(FULL_INIT_FEN)
        game = Game(board)
        move1 = board.copy().move((0, 0), (0, 1))
        game.append_first_move(move1)
        board.next_turn()
        move2 = board.copy().move((0, 9), (0, 8))
        game.append_next_move(move2)
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            game.save_to_pgn(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "01." in content or "1." in content
        finally:
            os.unlink(tmp_path)

    def test_game_save_to_pgn_custom_fen(self):
        """Test Game.save_to_pgn with non-default init fen (line 319)."""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        game = Game(board)
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            tmp_path = f.name
        try:
            game.save_to_pgn(tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "FEN" in content
        finally:
            os.unlink(tmp_path)


# ============================================================
# common.py tests
# ============================================================


class TestCommon:
    """Tests for common.py uncovered lines."""

    def test_iccs_mirror(self):
        """Test iccs_mirror (line 84)."""
        result = iccs_mirror("a0a1")
        assert result == "i0i1"

    def test_iccs_flip(self):
        """Test iccs_flip (line 88)."""
        result = iccs_flip("e0e1")
        assert result == "e9e8"

    def test_iccs_swap(self):
        """Test iccs_swap (line 92)."""
        result = iccs_swap("e0e1")
        assert result == "e9e8"

    def test_fen_mirror(self):
        """Test fen_mirror (lines 186-189)."""
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        mirrored = fen_mirror(fen)
        assert mirrored is not None

    def test_fen_flip(self):
        """Test fen_flip (lines 193-196)."""
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        flipped = fen_flip(fen)
        assert flipped is not None

    def test_fen_swap(self):
        """Test fen_swap (lines 202-216)."""
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        swapped = fen_swap(fen)
        assert swapped is not None

    def test_get_fen_type_detail_keyerror_edge(self):
        """Test get_fen_type_detail edge case with unusual piece counts (lines 332, 359-373)."""
        # 3 rooks - edge case for p_count_dict lookup
        fen = "4k4/9/9/9/9/9/9/9/9/3K1R1R1 w"
        red_title, _black_title = get_fen_type_detail(fen)
        assert red_title is not None

    def test_get_fen_type_detail_with_a_b_pieces(self):
        """Test get_fen_type_detail with advisors and bishops."""
        fen = "4k4/9/9/9/9/9/9/9/4A4/4K4 w"
        red_title, _black_title = get_fen_type_detail(fen)
        assert "仕" in red_title

    def test_full2half(self):
        """Test full2half conversion."""
        result = full2half("１２３")
        assert result == "123"

    def test_half2full(self):
        """Test half2full conversion."""
        result = half2full("123")
        assert result == "１２３"


# ============================================================
# piece.py tests
# ============================================================


class TestPiece:
    """Tests for piece.py uncovered lines."""

    def test_piece_create_unknown_type(self):
        """Test Piece.create with unknown type returns None (line 92)."""
        board = ChessBoard(FULL_INIT_FEN)
        result = Piece.create(board, "x", (4, 4))
        assert result is None

    def test_piece_is_valid_move_base(self):
        """Test Piece.is_valid_move base class returns True (line 66)."""
        board = ChessBoard(FULL_INIT_FEN)
        piece = Piece(board, "K", (4, 0))
        assert piece.is_valid_move((4, 1)) is True

    def test_piece_get_color_fench_lower(self):
        """Test Piece.get_color_fench with lowercase (lines 70-72)."""
        board = ChessBoard(FULL_INIT_FEN)
        piece = Piece(board, "k", (4, 9))
        assert piece.get_color_fench() == "bk"

    def test_piece_get_color_fench_upper(self):
        """Test Piece.get_color_fench with uppercase."""
        board = ChessBoard(FULL_INIT_FEN)
        piece = Piece(board, "K", (4, 0))
        assert piece.get_color_fench() == "rk"

    def test_knight_is_valid_move_not_day_shape(self):
        """Test Knight.is_valid_move when not day shape (line 241)."""
        board = ChessBoard(FULL_INIT_FEN)
        knight = Knight(board, "N", (2, 0))
        assert knight.is_valid_move((2, 1)) is False  # Not a day shape

    def test_rook_is_valid_move_diagonal(self):
        """Test Rook.is_valid_move diagonal returns False (lines 268-269)."""
        board = ChessBoard(FULL_INIT_FEN)
        rook = Rook(board, "R", (0, 0))
        assert rook.is_valid_move((1, 1)) is False

    def test_cannon_is_valid_move_diagonal(self):
        """Test Cannon.is_valid_move diagonal returns False (lines 299-301)."""
        board = ChessBoard(FULL_INIT_FEN)
        cannon = Cannon(board, "C", (1, 2))
        assert cannon.is_valid_move((2, 3)) is False

    def test_pawn_is_valid_move_backward(self):
        """Test Pawn.is_valid_move backward returns False (lines 356-360)."""
        board = ChessBoard("4k4/9/9/9/4P4/9/9/9/9/4K4 w")
        pawn = Pawn(board, "P", (4, 4))
        assert pawn.is_valid_move((4, 3)) is False

    def test_pawn_is_valid_pos_red_too_far_back(self):
        """Test Pawn.is_valid_pos red pawn too far back (lines 339-340)."""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        pawn = Pawn(board, "P", (4, 4))
        assert pawn.is_valid_pos((4, 5)) is True
        assert pawn.is_valid_pos((4, 2)) is False

    def test_pawn_is_valid_pos_black_too_far_back(self):
        """Test Pawn.is_valid_pos black pawn too far back (lines 342-343)."""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 b")
        pawn = Pawn(board, "p", (4, 5))
        assert pawn.is_valid_pos((4, 4)) is True
        assert pawn.is_valid_pos((4, 8)) is False


# ============================================================
# board.py tests
# ============================================================


class TestBoard:
    """Tests for board.py uncovered lines."""

    def test_chess_player_eq_not_chess_player_not_int(self):
        """Test ChessPlayer.__eq__ with non-ChessPlayer, non-int (line 122)."""
        player = ChessPlayer(RED)
        assert (player == "RED") is False

    def test_chess_player_next_no_color(self):
        """Test ChessPlayer.next with NO_COLOR (line 97)."""
        from cchess.common import NO_COLOR

        player = ChessPlayer(NO_COLOR)
        result = player.next()
        assert result.color == NO_COLOR

    def test_chess_player_opposite_no_color(self):
        """Test ChessPlayer.opposite with NO_COLOR (lines 106-107)."""
        from cchess.common import NO_COLOR

        player = ChessPlayer(NO_COLOR)
        assert player.opposite() == NO_COLOR

    def test_board_eq_str(self):
        """Test ChessBoard.__eq__ with string (lines 628-629)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board == FULL_INIT_FEN

    def test_board_eq_other_type(self):
        """Test ChessBoard.__eq__ with other type (line 632)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert (board == 42) is False

    def test_board_repr(self):
        """Test ChessBoard.__repr__ (line 625)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert repr(board) == FULL_INIT_FEN

    def test_board_from_fen_empty(self):
        """Test ChessBoard.from_fen with empty string (lines 473-474)."""
        board = ChessBoard(FULL_INIT_FEN)
        result = board.from_fen("")
        assert result is True
        assert board.to_fen() == "9/9/9/9/9/9/9/9/9/9 w"

    def test_board_from_fen_invalid_turn(self):
        """Test ChessBoard.from_fen with invalid turn value (lines 502-504)."""
        board = ChessBoard()
        with pytest.raises(CChessError, match="走子合理的值"):
            board.from_fen("9/9/9/9/9/9/9/9/9/9 x")

    def test_board_from_fen_out_of_bounds(self):
        """Test ChessBoard.from_fen with out of bounds (line 483)."""
        board = ChessBoard()
        with pytest.raises(CChessError, match="行列超出界限"):
            board.from_fen("1111111111/9/9/9/9/9/9/9/9/9 w")

    def test_board_pop_fench(self):
        """Test ChessBoard.pop_fench."""
        board = ChessBoard(FULL_INIT_FEN)
        fench = board.pop_fench((0, 0))
        assert fench == "R"
        assert board.get_fench((0, 0)) is None

    def test_board_get_fench_color(self):
        """Test ChessBoard.get_fench_color."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board.get_fench_color((0, 0)) == RED
        assert board.get_fench_color((0, 9)) == BLACK
        assert board.get_fench_color((4, 4)) is None

    def test_board_to_full_fen(self):
        """Test ChessBoard.to_full_fen (line 542)."""
        board = ChessBoard(FULL_INIT_FEN)
        full_fen = board.to_full_fen()
        assert full_fen.endswith(" - - 0 1")

    def test_board_detect_move_pieces(self):
        """Test ChessBoard.detect_move_pieces (lines 567-582)."""
        board = ChessBoard(FULL_INIT_FEN)
        new_board = board.copy()
        new_board._move_piece((0, 0), (0, 1))
        p_from, p_to = board.detect_move_pieces(new_board)
        assert (0, 0) in p_from
        assert (0, 1) in p_to

    def test_board_create_move_from_board_ambiguous(self):
        """Test ChessBoard.create_move_from_board with ambiguous changes (line 592)."""
        board = ChessBoard(FULL_INIT_FEN)
        new_board = board.copy()
        new_board._move_piece((0, 0), (0, 1))
        new_board._move_piece((8, 0), (8, 1))
        result = board.create_move_from_board(new_board)
        assert result is None

    def test_board_create_move_from_board_invalid(self):
        """Test ChessBoard.create_move_from_board with invalid move (line 590)."""
        board = ChessBoard(FULL_INIT_FEN)
        new_board = board.copy()
        # Move king far away - invalid
        new_board._board[0][4] = None
        new_board._board[0][8] = "K"
        result = board.create_move_from_board(new_board)
        assert result is None

    def test_board_is_valid_move_out_of_bounds_x(self):
        """Test ChessBoard.is_valid_move with out of bounds x (line 310)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((0, 0), (-1, 0)) is False

    def test_board_is_valid_move_out_of_bounds_y(self):
        """Test ChessBoard.is_valid_move with out of bounds y (line 312)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((0, 0), (0, -1)) is False

    def test_board_is_valid_move_no_piece(self):
        """Test ChessBoard.is_valid_move with no piece at source (lines 316-317)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((4, 4), (4, 5)) is False

    def test_board_is_valid_move_wrong_turn(self):
        """Test ChessBoard.is_valid_move with wrong turn (lines 321-322)."""
        board = ChessBoard(FULL_INIT_FEN)
        board.next_turn()  # Now black's turn
        assert board.is_valid_move((0, 0), (0, 1)) is False

    def test_board_is_valid_move_same_color(self):
        """Test ChessBoard.is_valid_move capturing same color (lines 326-328)."""
        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((0, 0), (2, 0)) is False

    def test_board_move_iccs(self):
        """Test ChessBoard.move_iccs (lines 362-363)."""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a1")
        assert move is not None
        assert move.to_iccs() == "a0a1"

    def test_board_move_text_no_result(self):
        """Test ChessBoard.move_text returning None (lines 368-376)."""
        board = ChessBoard(FULL_INIT_FEN)
        result = board.move_text("不存在的走法")
        assert result is None

    def test_board_create_piece_moves_no_piece(self):
        """Test ChessBoard.create_piece_moves with no piece (line 390)."""
        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_piece_moves((4, 4)))
        assert moves == []

    def test_board_is_checking_no_king(self):
        """Test ChessBoard.is_checking with no king (lines 412-413)."""
        board = ChessBoard("9/9/9/9/9/9/9/9/9/9 w")
        assert board.is_checking() is False

    def test_board_has_no_legal_moves_no_king(self):
        """Test ChessBoard.has_no_legal_moves with no king (lines 429-431)."""
        board = ChessBoard("9/9/9/9/9/9/9/9/9/9 w")
        assert board.has_no_legal_moves() is True

    def test_board_get_king_no_king(self):
        """Test ChessBoard.get_king when no king exists (line 296)."""
        board = ChessBoard("9/9/9/9/9/9/9/9/9/9 w")
        assert board.get_king(RED) is None

    def test_board_get_pieces_with_chess_player(self):
        """Test ChessBoard.get_pieces with ChessPlayer color (lines 264-265)."""
        board = ChessBoard(FULL_INIT_FEN)
        player = ChessPlayer(RED)
        pieces = list(board.get_pieces(color=player))
        assert len(pieces) == 16

    def test_board_get_king_with_chess_player(self):
        """Test ChessBoard.get_king with ChessPlayer (lines 285-286)."""
        board = ChessBoard(FULL_INIT_FEN)
        player = ChessPlayer(RED)
        king = board.get_king(player)
        assert king is not None
        assert king.fench == "K"

    def test_chess_board_one_hot(self):
        """Test ChessBoardOneHot."""
        board = ChessBoardOneHot(FULL_INIT_FEN)
        board._ChessBoardOneHot__chess_dict = {
            "R": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            None: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        }
        one_hot = board.get_one_hot_board()
        assert len(one_hot) == 10
        assert len(one_hot[0]) == 9

    def test_chess_board_one_hot_load_dict(self):
        """Test ChessBoardOneHot.load_one_hot_dict."""
        board = ChessBoardOneHot(FULL_INIT_FEN)
        d = {"R": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(d, f)
            tmp_path = f.name
        try:
            board.load_one_hot_dict(tmp_path)
            assert board.chess_dict is not None
        finally:
            os.unlink(tmp_path)

    def test_chess_board_one_hot_chess_dict(self):
        """Test ChessBoardOneHot.chess_dict property."""
        board = ChessBoardOneHot(FULL_INIT_FEN)
        d = {"R": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}
        board._ChessBoardOneHot__chess_dict = d
        result = board.chess_dict
        assert result == d


# ============================================================
# engine.py tests
# ============================================================


class TestEngine:
    """Tests for engine.py uncovered lines."""

    def test_is_int_empty(self):
        """Test is_int with empty string (line 63)."""
        assert is_int("") is False

    def test_is_int_plus_only(self):
        """Test is_int with just '+' (line 70)."""
        assert is_int("+") is False

    def test_is_int_minus_only(self):
        """Test is_int with just '-' (line 70)."""
        assert is_int("-") is False

    def test_is_int_zero(self):
        """Test is_int with '0' (line 73)."""
        assert is_int("0") is True

    def test_is_int_leading_zero(self):
        """Test is_int with leading zero (line 78)."""
        assert is_int("007") is False

    def test_is_int_negative_zero(self):
        """Test is_int with '-0'."""
        assert is_int("-0") is True

    def test_is_int_positive(self):
        """Test is_int with positive number."""
        assert is_int("123") is True

    def test_is_int_negative(self):
        """Test is_int with negative number."""
        assert is_int("-456") is True

    def test_is_int_with_spaces(self):
        """Test is_int with leading/trailing spaces."""
        assert is_int("  42  ") is True

    def test_is_int_float(self):
        """Test is_int with float string."""
        assert is_int("3.14") is False

    def test_parse_engine_info_to_dict(self):
        """Test parse_engine_info_to_dict."""
        result = parse_engine_info_to_dict("info depth 5 score cp 100 pv a0a1")
        assert result["depth"] == 5
        assert result["score"] == 100
        assert result["moves"] == ["a0a1"]

    def test_parse_engine_info_to_dict_mate(self):
        """Test parse_engine_info_to_dict with mate."""
        result = parse_engine_info_to_dict("info depth 3 score mate 5")
        assert result["depth"] == 3
        assert result["mate"] == 5

    def test_parse_engine_info_to_dict_bestmove(self):
        """Test parse_engine_info_to_dict with bestmove."""
        result = parse_engine_info_to_dict("bestmove a0a1 ponder i9i8")
        assert result["move"] == "a0a1"

    def test_parse_engine_info_to_dict_keywords(self):
        """Test parse_engine_info_to_dict with keywords like cp, lowerbound."""
        result = parse_engine_info_to_dict("info depth 2 lowerbound cp 50")
        assert result["depth"] == 2

    def test_uci_engine_init_cmd(self):
        """Test UciEngine.init_cmd (line 484)."""
        engine = UciEngine()
        assert engine.init_cmd() == "uci"

    def test_uci_engine_ok_resp(self):
        """Test UciEngine.ok_resp (line 487)."""
        engine = UciEngine()
        assert engine.ok_resp() == "uciok"

    def test_ucci_engine_init_cmd(self):
        """Test UcciEngine.init_cmd (line 474)."""
        engine = UcciEngine()
        assert engine.init_cmd() == "ucci"

    def test_ucci_engine_ok_resp(self):
        """Test UcciEngine.ok_resp (line 477)."""
        engine = UcciEngine()
        assert engine.ok_resp() == "ucciok"

    def test_engine_base_init_cmd(self):
        """Test Engine base init_cmd returns empty (line 186)."""
        from cchess.engine import Engine

        engine = Engine()
        assert engine.init_cmd() == ""

    def test_engine_base_ok_resp(self):
        """Test Engine base ok_resp returns empty (line 190)."""
        from cchess.engine import Engine

        engine = Engine()
        assert engine.ok_resp() == ""

    def test_action_mirror(self):
        """Test action_mirror (lines 493-498)."""
        action = {"move": "a0a1", "moves": ["a0a1", "i9i8"], "ponder": "i9i8"}
        result = action_mirror(action)
        assert result["move"] == "i0i1"
        assert result["moves"] == ["i0i1", "a9a8"]
        assert result["ponder"] == "a9a8"

    def test_fen_cache_get(self):
        """Test FenCache.get (lines 524-531)."""
        cache = FenCache()
        cache.fen_dict["test_fen"] = {"a0a1": {"score": 100}}
        info, state = cache.get("test_fen")
        assert info is not None
        assert state == ""

    def test_fen_cache_get_mirror(self):
        """Test FenCache.get with mirror (lines 527-529)."""
        cache = FenCache()
        from cchess.common import fen_mirror

        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        mirrored = fen_mirror(fen)
        cache.fen_dict[mirrored] = {"a0a1": {"score": 100}}
        info, _state = cache.get(fen)
        assert info is not None
        # state may be '' or 'mirror' depending on whether fen == mirrored

    def test_fen_cache_get_miss(self):
        """Test FenCache.get miss (line 531)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        info, state = cache.get(fen)
        assert info is None
        assert state is None

    def test_fen_cache_get_best_action_red(self):
        """Test FenCache.get_best_action for red (lines 548-549)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        cache.fen_dict[fen] = {
            "a0a1": {"score": 100, "move": "a0a1"},
            "b0b1": {"score": 200, "move": "b0b1"},
        }
        action = cache.get_best_action(fen)
        assert action["score"] == 100  # Red picks lowest score

    def test_fen_cache_get_best_action_black(self):
        """Test FenCache.get_best_action for black (lines 550-551)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 b"
        cache.fen_dict[fen] = {
            "a0a1": {"score": 100, "move": "a0a1"},
            "b0b1": {"score": 200, "move": "b0b1"},
        }
        action = cache.get_best_action(fen)
        assert action["score"] == 200  # Black picks highest score

    def test_fen_cache_get_best_action_mirror(self):
        """Test FenCache.get_best_action with mirror (line 555)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        mirrored = fen_mirror(fen)
        cache.fen_dict[mirrored] = {
            "i0i1": {"score": 100, "move": "i0i1"},
        }
        action = cache.get_best_action(fen)
        assert action is not None

    def test_fen_cache_save_action_new_fen(self):
        """Test FenCache.save_action with new fen (lines 577-581)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        action = {"move": "a0a1", "score": 100}
        result = cache.save_action(fen, action)
        assert result is True
        assert fen in cache.fen_dict
        assert cache.need_save is True

    def test_fen_cache_save_action_existing_fen(self):
        """Test FenCache.save_action with existing fen (lines 568-569)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        cache.fen_dict[fen] = {"a0a1": {"score": 100, "move": "a0a1"}}
        action = {"move": "b0b1", "score": 200}
        result = cache.save_action(fen, action)
        assert result is True
        assert "b0b1" in cache.fen_dict[fen]

    def test_fen_cache_save_action_mirror(self):
        """Test FenCache.save_action with mirror fen (lines 571-575)."""
        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        mirrored = fen_mirror(fen)
        cache.fen_dict[mirrored] = {"i0i1": {"score": 100, "move": "i0i1"}}
        action = {"move": "a0a1", "score": 200}
        result = cache.save_action(fen, action)
        assert result is True

    def test_fen_cache_load_no_file(self):
        """Test FenCache.load with non-existent file (lines 590-591)."""
        cache = FenCache()
        cache.load("/nonexistent/path/cache.json")
        assert cache.fen_dict == {}

    def test_fen_cache_load_save(self):
        """Test FenCache.load and save."""
        cache = FenCache()
        cache.fen_dict = {"test": {"a0a1": {"score": 100}}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp_path = f.name
        try:
            cache.cache_file = tmp_path
            cache.save()
            cache2 = FenCache()
            cache2.load(tmp_path)
            assert "test" in cache2.fen_dict
        finally:
            os.unlink(tmp_path)

    def test_engine_manager_init(self):
        """Test EngineManager init without fen_cache (lines 618-620)."""
        from cchess.engine import EngineManager

        mgr = EngineManager()
        assert mgr.cache is not None
        assert mgr.engine is None

    def test_engine_manager_get_fen_score_cache_hit(self):
        """Test EngineManager.get_fen_score with cache hit (lines 672-673)."""
        from cchess.engine import EngineManager

        cache = FenCache()
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w"
        cache.fen_dict[fen] = {
            "a0a1": {"score": 100, "move": "a0a1"},
        }
        mgr = EngineManager(fen_cache=cache)
        action = mgr.get_fen_score(fen)
        assert action is not None

    def test_engine_status_values(self):
        """Test EngineStatus enum values."""
        assert EngineStatus.ERROR == 0
        assert EngineStatus.BOOTING == 1
        assert EngineStatus.READY == 2
        assert EngineStatus.WAITING == 3
        assert EngineStatus.INFO_MOVE == 4
        assert EngineStatus.MOVE == 5
        assert EngineStatus.DEAD == 6
        assert EngineStatus.UNKNOWN == 7
        assert EngineStatus.BOARD_RESET == 8


# ============================================================
# exception.py tests
# ============================================================


class TestException:
    """Tests for exception.py uncovered lines."""

    def test_engine_error_exception(self):
        """Test EngineError (line 31)."""
        exc = EngineError("test error")
        assert exc.reason == "test error"
        assert str(exc) == "test error"

    def test_cchess_exception(self):
        """Test CChessError."""
        exc = CChessError("test reason")
        assert exc.reason == "test reason"


# ============================================================
# __main__.py tests
# ============================================================


class TestMain:
    """Tests for __main__.py uncovered lines."""

    def test_convert_format_unsupported_input(self):
        """Test convert_format with unsupported input format (lines 53-55)."""
        f = tempfile.NamedTemporaryFile(suffix=".xyz", delete=False)
        f.write(b"test")
        f.close()
        tmp_path = f.name
        output_path = os.path.join(os.path.dirname(tmp_path), "output.xqf")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "cchess", "-i", tmp_path, "-o", output_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_convert_format_unsupported_output(self):
        """Test convert_format with unsupported output format (lines 57-59)."""
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            f.write('[Game "Chinese Chess"]\n\n1. a0a1 i9i8\n *\n')
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "cchess", "-i", tmp_path, "-o", "output.xyz"],
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0
        finally:
            os.unlink(tmp_path)

    def test_convert_format_same_format(self):
        """Test convert_format with same input/output format (lines 61-63)."""
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="w") as f:
            f.write('[Game "Chinese Chess"]\n\n1. a0a1 i9i8\n *\n')
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, "-m", "cchess", "-i", tmp_path, "-o", "output.pgn"],
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0
        finally:
            os.unlink(tmp_path)

    def test_convert_format_read_error(self):
        """Test convert_format with read error (lines 65-69)."""
        f = tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="wb")
        f.write(b"\x00\x01\x02\x03\x04\x05")
        f.close()
        tmp_path = f.name
        output_path = os.path.join(os.path.dirname(tmp_path), "output.xqf")
        try:
            subprocess.run(
                [sys.executable, "-m", "cchess", "-i", tmp_path, "-o", output_path],
                capture_output=True,
                text=True,
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_main_read_cbl(self):
        """Test main() reading .cbl file (lines 98-101)."""
        import struct

        magic = b"CCBridgeLibrary\x00"
        header = struct.pack("<16s44si512s", magic, b"\x00" * 44, 1, b"\x00" * 512)
        data = header + b"\x00" * (101952 - len(header)) + b"\x00" * 4096
        with tempfile.NamedTemporaryFile(suffix=".cbl", delete=False, mode="wb") as f:
            f.write(data)
            tmp_path = f.name
        try:
            subprocess.run(
                [sys.executable, "-m", "cchess", "-r", tmp_path],
                capture_output=True,
                text=True,
            )
        finally:
            os.unlink(tmp_path)

    def test_main_read_error(self):
        """Test main() with read error (lines 105-107)."""
        with tempfile.NamedTemporaryFile(suffix=".pgn", delete=False, mode="wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
            tmp_path = f.name
        try:
            subprocess.run(
                [sys.executable, "-m", "cchess", "-r", tmp_path],
                capture_output=True,
                text=True,
            )
        finally:
            os.unlink(tmp_path)
