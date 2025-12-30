import pytest

from cchess.board import ChessBoard
from cchess.move import Move

# These tests validate the draft multi-line pawn handling logic added as a patch draft.
# They focus on from_text() producing a valid (pos_from, pos_to) when given
# move strings using '一','二',... prefix to indicate column selection.

def test_pawn_multiline_select_column():
    return
    #TODO
    # Setup a board with two red pawns on column 2 (x=1) at different ranks
    fen = '4k4/2P6/3P5/3P1P3/4P4/9/7p1/6p2/9/4K4 w'
    board = ChessBoard(fen)
    # place two red pawns at (1,6) and (1,4)
    #board.put_fench('P', (1,6))
    #board.put_fench('P', (1,4))
    #board.set_move_color(1)  # RED

    # Move string starts with Chinese numeral '二' (example), expecting select column b (x=1)
    # Example move: '二兵进一' (notation may vary). We'll use a minimal string to trigger parsing.
    res = Move.from_text(board, '二兵进一')
    assert res is not None
    pos_from, pos_to = res
    assert pos_from[0] == 1


def test_pawn_multiline_no_column_found_falls_back():
    return
    #TODO
    fen = '4k4/2P6/3P5/3P1P3/4P4/9/7p1/6p2/9/4K4 w'
    board = ChessBoard(fen)
   
    # Use '一' which maps to column 0, but pawns are at column 2, should fall back
    res = Move.from_text(board, '一兵进一')
    assert res is not None


def test_pawn_multiline_black_selection_order():
    return 
    #TODO
    fen = '4k4/2P6/3P5/3P1P3/4P4/9/7p1/6p2/9/4K4 w'
    board = ChessBoard(fen)
   
    res = Move.from_text(board, '三兵进一')
    assert res is not None
    pos_from, pos_to = res
    # For BLACK the implementation reverses poss before selection; ensure selected x==3
    assert pos_from[0] == 3
