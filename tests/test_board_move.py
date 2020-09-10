# -*- coding: utf-8 -*-
'''
Copyright (C) 2014  walker li <walker8088@gmail.com>

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
'''

from cchess import *

#-----------------------------------------------------#
class TestBoard():
    def test_base(self):
        board = ChessBoard(FULL_INIT_FEN)
        fen = board.to_fen()
        assert FULL_INIT_FEN == fen

        board.from_fen(fen)
        assert board.to_fen() == fen

        board.swap()
        board.swap()
        assert board.to_fen() == fen

        board.mirror()
        board.mirror()
        assert board.to_fen() == fen

        k = board.get_king(ChessSide.RED)
        assert (k.x, k.y) == (4, 0)

        k = board.get_king(ChessSide.BLACK)
        assert (k.x, k.y) == (4, 9)
        assert len(list(board.create_moves())) == 44

        assert board.check_count() == 0
        
        #assert board.is_checkmate() is False
        
        assert board.get_fench((0, 9)) == 'r'

        fen2 = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1'
        board.from_fen(fen2)
        assert board.to_fen() == fen2

        board.swap()
        board.swap()
        assert board.to_fen() == fen2

        board.mirror()
        board.mirror()
        assert board.to_fen() == fen2

        k = board.get_king(ChessSide.RED)
        assert (k.x, k.y) == (4, 0)

        k = board.get_king(ChessSide.BLACK)
        assert (k.x, k.y) == (4, 9)

        assert board.check_count() == 0
        assert board.is_dead() is False
        assert board.is_win() is False

        #不存在的棋子的移动
        assert board.move((1, 0), (2, 0)) is None
        #错误fen字符串
        assert board.from_fen(
            'rnbaka~d~nr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1'
        ) is False

    def test_line1(self):
        board = ChessBoard(FULL_INIT_FEN)
        assert board.count_x_line_in(0, 0, 8) == 7
        assert board.count_y_line_in(4, 0, 9) == 2
        assert board.count_y_line_in(4, 1, 8) == 2

    def test_kk_move(self):
        #face to face
        fen_king_face_to_face = '4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1'
        
        board = ChessBoard(fen_king_face_to_face)
        
        assert board.to_fen() == fen_king_face_to_face
        assert board.is_valid_move((4, 0), (4, 9)) is True
        assert board.is_valid_move((4, 0), (4, 8)) is False
        assert board.is_valid_move((4, 1), (4, 9)) is False
        
        move = board.copy().move_chinese('帅五进九')
        assert str(move) == 'e0e9'
        #assert board.copy().move_chinese('帅五进八') is None
        
        new_board = board.copy()
        move = new_board.move((4, 0), (4, 9))
        #assert new_board.get_king(ChessSide.BLACK) is None
        assert new_board.to_fen() == '4K4/9/9/9/9/9/9/9/9/9 w - - 0 1'
        
        assert move.is_king_killed() is True

        assert board.is_valid_move((4, 0), (4, 1)) is True
        assert board.is_valid_move((4, 0), (5, 0)) is True
        assert board.is_valid_move((4, 0), (3, 0)) is True
        
        moves = list(board.create_piece_moves((4, 0)))
        assert len(moves) == 4
        
        moves = list(board.create_piece_moves((4, 9)))
        assert len(moves) == 0
        
        board.next_turn()
        assert board.is_valid_move((4, 9), (4, 8)) is True
        assert board.is_valid_move((4, 9), (5, 9)) is True
        assert board.is_valid_move((4, 9), (3, 9)) is True
        
        moves = list(board.create_piece_moves((4, 9)))
        assert len(moves) == 4
        
        #not face to face
        board = ChessBoard('3k5/9/9/9/9/9/9/9/9/4K4 w - - 0 1')
        assert board.is_valid_move((4, 0), (4, 9)) is False
        assert board.is_valid_move((4, 0), (4, 1)) is True
        assert board.is_valid_move((4, 0), (5, 0)) is True
        assert board.is_valid_move((4, 0), (3, 0)) is True
        
        moves = list(board.create_piece_moves((4, 0)))
        assert len(moves) == 3
        
        moves = list(board.create_piece_moves((3, 9)))
        assert len(moves) == 0
        
        board.next_turn()
        assert board.is_valid_move((3, 9), (3, 8)) is True
        assert board.is_valid_move((3, 9), (4, 9)) is True
        
        moves = list(board.create_piece_moves((3, 9)))
        assert len(moves) == 2

        board = ChessBoard('4k4/9/9/9/9/4R4/9/9/9/5K3 w - - 0 1')
        assert board.copy().move_iccs('e4e9').is_king_killed() is True

        board = ChessBoard('3k5/9/9/9/9/4R4/9/9/9/5K3 w - - 0 1')
        assert board.copy().move_iccs('e4e9').is_king_killed() is False
        assert board.copy().is_checking_move(*move.from_iccs('e4e9')) == True
        
    def test_AA_move(self):

        #middle AA
        board = ChessBoard('4k4/4a4/9/9/9/9/9/9/4A4/4K4 w - - 0 1')
        assert board.is_valid_move((4, 1), (3, 0)) is True
        assert board.is_valid_move((4, 1), (5, 0)) is True
        assert board.is_valid_move((4, 1), (3, 2)) is True
        assert board.is_valid_move((4, 1), (5, 2)) is True
        moves = list(board.create_piece_moves((4, 1)))
        assert len(moves) == 4
        moves = list(board.create_piece_moves((4, 8)))
        assert len(moves) == 0

        board.next_turn()
        assert board.is_valid_move((4, 8), (3, 9)) is True
        assert board.is_valid_move((4, 8), (5, 9)) is True
        assert board.is_valid_move((4, 8), (3, 7)) is True
        assert board.is_valid_move((4, 8), (5, 7)) is True
        moves = list(board.create_piece_moves((4, 8)))
        assert len(moves) == 4

        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((3, 0), (4, 1)) is True
        assert board.is_valid_move((5, 0), (4, 1)) is True
        moves = list(board.create_piece_moves((3, 0)))
        assert len(moves) == 1
        moves = list(board.create_piece_moves((5, 0)))
        assert len(moves) == 1

    def test_BB_move(self):
        #middle BB
        board = ChessBoard('4k4/4a4/4b4/9/9/9/9/4B4/4A4/4K4 w - - 0 1')
        assert board.is_valid_move((4, 2), (2, 0)) is True
        assert board.is_valid_move((4, 2), (6, 0)) is True
        assert board.is_valid_move((4, 2), (2, 4)) is True
        assert board.is_valid_move((4, 2), (6, 4)) is True
        moves = list(board.create_piece_moves((4, 2)))
        assert len(moves) == 4
        moves = list(board.create_piece_moves((4, 7)))
        assert len(moves) == 0

        #block BB
        board = ChessBoard('4k4/3ca4/4b4/3c5/9/9/9/4B4/3CAC3/4K4 w - - 0 1')
        assert board.is_valid_move((4, 2), (2, 0)) is False
        assert board.is_valid_move((4, 2), (6, 0)) is False
        assert board.is_valid_move((4, 2), (2, 4)) is True
        assert board.is_valid_move((4, 2), (6, 4)) is True
        moves = list(board.create_piece_moves((4, 2)))
        assert len(moves) == 2
        board.next_turn()
        assert board.is_valid_move((4, 7), (2, 9)) is False
        assert board.is_valid_move((4, 7), (6, 9)) is True
        assert board.is_valid_move((4, 7), (2, 5)) is False
        assert board.is_valid_move((4, 7), (6, 5)) is True
        moves = list(board.create_piece_moves((4, 7)))
        assert len(moves) == 2

        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_valid_move((2, 0), (4, 2)) is True
        assert board.is_valid_move((6, 0), (4, 2)) is True
        moves = list(board.create_piece_moves((2, 0)))
        assert len(moves) == 2
        moves = list(board.create_piece_moves((6, 0)))
        assert len(moves) == 2

    def test_PP_move(self):
        #Pawn move
        board = ChessBoard('4k4/9/9/4p4/4P4/9/9/9/9/4K4 w - - 0 1')
        assert board.is_valid_move((4, 5), (4, 6)) is True
        assert board.is_valid_move((4, 5), (5, 5)) is True
        assert board.is_valid_move((4, 5), (3, 5)) is True
        assert board.is_valid_move((4, 5), (4, 4)) is False
        moves = list(board.create_piece_moves((4, 5)))
        assert len(moves) == 3
        moves = list(board.create_piece_moves((4, 6)))
        assert len(moves) == 0
        board.next_turn()
        assert board.is_valid_move((4, 6), (4, 5)) is True
        assert board.is_valid_move((4, 6), (4, 7)) is False
        assert board.is_valid_move((4, 6), (5, 6)) is False
        moves = list(board.create_piece_moves((4, 6)))
        assert len(moves) == 1

    def test_RR_move(self):
        #Rook move
        board = ChessBoard('4k4/9/9/9/5r3/9/9/9/9/3K1R3 w - - 0 1')
        assert board.is_valid_move((5, 0), (5, 4)) is True
        assert board.is_valid_move((5, 0), (5, 5)) is True
        assert board.is_valid_move((5, 0), (5, 6)) is False
        assert board.is_valid_move((5, 0), (8, 0)) is True
        assert board.is_valid_move((5, 0), (4, 0)) is True
        assert board.is_valid_move((5, 0), (3, 0)) is False
        assert board.is_valid_move((5, 0), (0, 0)) is False
        moves = list(board.create_piece_moves((5, 0)))
        assert len(moves) == 9
        moves = list(board.create_piece_moves((5, 5)))
        assert len(moves) == 0
        board.next_turn()
        assert board.is_valid_move((5, 5), (8, 5)) is True
        assert board.is_valid_move((5, 5), (0, 5)) is True
        moves = list(board.create_piece_moves((5, 5)))
        assert len(moves) == 17

        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_piece_moves((0, 0)))
        assert len(moves) == 2
        moves = list(board.create_piece_moves((8, 0)))
        assert len(moves) == 2
        board.next_turn()
        moves = list(board.create_piece_moves((0, 9)))
        assert len(moves) == 2
        moves = list(board.create_piece_moves((8, 9)))
        assert len(moves) == 2

    def test_CC_move(self):
        #Cannon move
        board = ChessBoard('4k4/9/2c6/8p/9/8P/9/8C/9/3K5 w - - 0 1')
        assert board.is_valid_move((8, 2), (8, 3)) is True
        assert board.is_valid_move((8, 2), (8, 4)) is False
        assert board.is_valid_move((8, 2), (8, 5)) is False
        assert board.is_valid_move((8, 2), (8, 6)) is True
        assert board.is_valid_move((8, 2), (0, 2)) is True
        assert board.is_valid_move((8, 2), (8, 0)) is True
        moves = list(board.create_piece_moves((8, 2)))
        assert len(moves) == 12
        moves = list(board.create_piece_moves((2, 7)))
        assert len(moves) == 0
        board.next_turn()
        assert board.is_valid_move((2, 7), (2, 0)) is True
        assert board.is_valid_move((2, 7), (2, 9)) is True
        assert board.is_valid_move((2, 7), (0, 7)) is True
        assert board.is_valid_move((2, 7), (8, 7)) is True
        moves = list(board.create_piece_moves((2, 7)))
        assert len(moves) == 17

        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_piece_moves((1, 2)))
        assert len(moves) == 12
        moves = list(board.create_piece_moves((7, 2)))
        assert len(moves) == 12
        board.next_turn()
        moves = list(board.create_piece_moves((1, 7)))
        assert len(moves) == 12
        moves = list(board.create_piece_moves((7, 7)))
        assert len(moves) == 12

    def test__NN_move(self):
        #Knight move
        board = ChessBoard('5k3/9/c8/nc7/p8/4N4/8n/4N4/4C4/4K4 w - - 0 1')
        assert board.is_valid_move((4, 4), (5, 6)) is True
        assert board.is_valid_move((4, 4), (5, 2)) is True
        assert board.is_valid_move((4, 4), (3, 6)) is True
        assert board.is_valid_move((4, 4), (3, 2)) is True
        assert board.is_valid_move((4, 4), (6, 5)) is True
        assert board.is_valid_move((4, 4), (6, 3)) is True
        assert board.is_valid_move((4, 4), (2, 3)) is True
        assert board.is_valid_move((4, 4), (2, 5)) is True

        moves = list(board.create_piece_moves((4, 4)))
        assert len(moves) == 8

        assert board.is_valid_move((4, 2), (2, 1)) is True
        assert board.is_valid_move((4, 2), (6, 1)) is True
        assert board.is_valid_move((4, 2), (3, 0)) is False
        assert board.is_valid_move((4, 2), (5, 0)) is False

        moves = list(board.create_piece_moves((4, 2)))
        assert len(moves) == 6

        moves = list(board.create_piece_moves((8, 3)))
        assert len(moves) == 0

        board.next_turn()
        assert board.is_valid_move((8, 3), (7, 5)) is True
        assert board.is_valid_move((8, 3), (7, 1)) is True
        assert board.is_valid_move((8, 3), (6, 4)) is True
        assert board.is_valid_move((8, 3), (6, 2)) is True

        moves = list(board.create_piece_moves((8, 3)))
        assert len(moves) == 4

        moves = list(board.create_piece_moves((0, 6)))
        assert len(moves) == 0

        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_piece_moves((2, 0)))
        assert len(moves) == 2

        moves = list(board.create_piece_moves((7, 0)))
        assert len(moves) == 2

        board.next_turn()

        moves = list(board.create_piece_moves((2, 9)))
        assert len(moves) == 2

        moves = list(board.create_piece_moves((7, 9)))
        assert len(moves) == 2

    def test_iccs_move(self):
        board = ChessBoard(FULL_INIT_FEN)

        move = board.copy().move_iccs('a0a1')
        assert move.move_side == ChessSide.RED
        assert move.to_iccs() == 'a0a1'
        assert str(move) == 'a0a1'
        assert move.is_valid_move() is True
        
        assert move.from_iccs('a0a1') == ((0, 0), (0, 1))
        assert move.to_chinese() == '车九进一'
        #assert move.from_chinese(board, '车九进一') == ((0,0), (0,1))
    
    def test_board_text(self):
        board = ChessBoard(FULL_INIT_FEN)
        board_txt = board.dump_board()
        good_txt = [
            '9 砗──碼──象──士──将──士──象──碼──砗',
            '  │   │   │   │ ＼│ ／│   │   │   │ ',
            '8 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
            '  │   │　 │   │ ／│ ＼│   │   │   │ ',
            '7 ├───砲──┼───┼───┼───┼───┼───砲──┤ ',
            '  │   │　 │　 │　 │   │   │   │   │ ',
            '6 卒──┼───卒──┼───卒──┼───卒──┼───卒',
            '  │　 │　 │   │   │   │   │   │   │ ',
            '5 ├───┴───┴───┴───┴───┴───┴───┴───┤ ',
            '  │　                             │ ',
            '4 ├───┬───┬───┬───┬───┬───┬───┬───┤ ',
            '  │　 │　 │   │   │   │　 │　 │　 │ ',
            '3 兵──┼───兵──┼───兵──┼───兵──┼───兵',
            '  │   │　 │　 │　 │   │   │   │   │ ',
            '2 ├───炮──┼───┼───┼───┼───┼───炮──┤ ',
            '  │   │   │   │ ＼│ ／│　 │　 │　 │ ',
            '1 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
            '  │   │　 │   │ ／│ ＼│　 │   │   │ ',
            '0 车──马──相──仕──帅──仕──相──马──车',
            '   ',
            '  a   b   c   d   e   f   g   h   i ',
            '  0   1   2   3   4   5   6   7   8 ',
            ]
        for i in range(len(board_txt)):
            assert board_txt[i] == good_txt[i]
        
    def test_chinese(self):
        board = ChessBoard(FULL_INIT_FEN)
        assert board.copy().move((7, 2), (4, 2)).to_chinese() == '炮二平五'
        assert board.copy().move((1, 2), (1, 1)).to_chinese() == '炮八退一'
        assert board.copy().move((7, 2), (7, 6)).to_chinese() == '炮二进四'
        assert board.copy().move((6, 3), (6, 4)).to_chinese() == '兵三进一'
        assert board.copy().move((8, 0), (8, 1)).to_chinese() == '车一进一'
        assert board.copy().move((4, 0), (4, 1)).to_chinese() == '帅五进一'
        assert board.copy().move((2, 0), (4, 2)).to_chinese() == '相七进五'
        assert board.copy().move((5, 0), (4, 1)).to_chinese() == '仕四进五'
        assert board.copy().move((7, 0), (6, 2)).to_chinese() == '马二进三'
        board.next_turn()
        assert board.copy().move((7, 7), (4, 7)).to_chinese() == '炮８平５'
        assert board.copy().move((7, 7), (7, 3)).to_chinese() == '炮８进４'
        assert board.copy().move((0, 9), (0, 8)).to_chinese() == '车１进１'
        assert board.copy().move((4, 9), (4, 8)).to_chinese() == '将５进１'
