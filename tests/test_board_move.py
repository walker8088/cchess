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

from cchess import CChessException, ChessBoard,ChessPlayer, iccs2pos, pos2iccs, iccs_mirror, iccs_flip, iccs_swap, get_move_color, FULL_INIT_FEN, RED, BLACK

#-----------------------------------------------------#
class TestBoard():
    def test_base(self):
        board = ChessBoard('')
        assert '9/9/9/9/9/9/9/9/9/9 w' == board.to_fen()
        
        assert board.get_king(RED) is None
        assert board.get_king(BLACK) is None 
        assert board.is_checking() is False
        assert board.no_moves() is True 
        assert board.is_mirror()  is True 

        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_checking() is False
        assert board.no_moves() is False 
        assert board.is_checkmate() is False 
        assert board.is_mirror() is True 

        fen = board.to_fen()
        assert FULL_INIT_FEN == fen

        board.from_fen(fen)
        assert board.to_fen() == fen

        board = board.flip()
        board = board.flip()
        assert board.to_fen() == fen

        baord = board.mirror()
        board = board.mirror()
        assert board.to_fen() == fen

        board = board.swap()
        board =  board.swap()
        assert board.to_fen() == fen

        k = board.get_king(RED)
        assert (k.x, k.y) == (4, 0)

        k = board.get_king(BLACK)
        assert (k.x, k.y) == (4, 9)
        assert len(list(board.create_moves())) == 44

        assert board.is_checking() is False
        try:
            board.is_checked_move(
                (4, 0),
                (5, 0),
            )
        except CChessException as e:
            assert True
        else:
            assert False
        #assert board.is_checkmate() is False

        assert board.get_fench((0, 9)) == 'r'

        fen2 = 'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR w'
        board.from_fen(fen2)
        assert board.to_fen() == fen2

        b = board.mirror()
        assert board.to_fen() != b.to_fen()
        b2 = b.mirror()
        assert str(board) == str(b2)

        board.flip()
        board.flip()
        assert board.to_fen() == fen2

        board.swap()
        board.swap()
        assert board.to_fen() == fen2

        k = board.get_king(RED)
        assert (k.x, k.y) == (4, 0)

        k = board.get_king(BLACK)
        assert (k.x, k.y) == (4, 9)

        assert board.is_checking() is False
        assert board.no_moves() is False
        assert board.is_checkmate() is False

        #不存在的棋子的移动
        assert board.move((1, 0), (2, 0)) is None
        #错误fen字符串
        assert board.from_fen(
            'rnbaka~dnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b'
        ) is False

        board.from_fen(
            'rnbakabnr/9/1c2c4/p1p1C1p1p/9/9/P1P1P1P1P/1C7/9/RNBAKABNR w')
        assert board.is_checking() is True 
        assert board.is_checkmate() is False 

        board.from_fen(
            'rnbakabnr/9/1c2c4/p1p1C1p1p/9/9/P1P1P1P1P/1C7/9/RNBAKABNR b')
        assert board.is_checking() is False

        board.from_fen(
            'rnbakabnr/9/9/p1p1p1p1p/9/4c4/PCP1c1P1P/5C3/9/RNBAKABNR b')
        assert board.is_checking() is True 
        assert board.is_checkmate() is True 

        board.from_fen(
            'rnbakabnr/9/9/p1p1p1p1p/9/4c4/PCP1c1P1P/5C3/9/RNBAKABNR w')
        assert board.is_checking() is False
        #assert  is True board.is_checked()
        assert board.no_moves() is True 

        board.from_fen(
            'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR w')
        assert (board.mirror().to_fen(
        ) == 'rnbakabnr/9/1c5c1/p3p1p1p/2p6/9/P1P1P1P1P/1C2B2C1/9/RNBAKA1NR w')

        assert (board.is_valid_iccs_move('b0d1') is True)
        assert (board.copy().is_valid_iccs_move('b0d1') is True)
        assert (board.is_valid_move((1, 0), (3, 1)) is True)
        move_it = board.move((1, 0), (3, 1))
        assert move_it.to_text() == '马八进六'
        
        board.from_fen('1nbaka1nr/r8/1c2b2c1/p1p1p1p1p/9/9/P1P1P1P1P/2N3CC1/9/R1BAKABNR w')
        assert board.mirror().move_iccs('c2e2') is not None
        board.from_fen('1rbakabnr/9/1cn6/p3p1p1p/2p6/6P2/P1P1P2cP/2N1C2C1/9/1RBAKABNR w')
        assert board.mirror().move_iccs('b0c2').to_text() == '马八进七'

        fen = 'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR w'
        assert get_move_color(fen) == RED
        fen = 'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR w - - 0 1'
        assert get_move_color(fen) == RED
        
        fen = 'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR b'
        assert get_move_color(fen) == BLACK
        fen = 'rnbakabnr/9/1c5c1/p1p1p3p/6p2/9/P1P1P1P1P/1C2B2C1/9/RN1AKABNR b - - 0 1'
        assert get_move_color(fen) == BLACK
        
    def test_line1(self):
        board = ChessBoard(FULL_INIT_FEN)
        assert board.count_x_line_in(0, 0, 8) == 7
        assert board.count_y_line_in(4, 0, 9) == 2
        assert board.count_y_line_in(4, 1, 8) == 2

    def test_kk_move(self):
        #face to face
        fen_king_face_to_face = '4k4/9/9/9/9/9/9/9/9/4K4 w'

        board = ChessBoard(fen_king_face_to_face)

        assert board.to_fen() == fen_king_face_to_face
        assert board.is_valid_move((4, 0), (4, 9)) is True
        assert board.is_valid_move((4, 0), (4, 8)) is False
        assert board.is_valid_move((4, 1), (4, 9)) is False

        move = board.copy().move_text('帅五进九')
        assert str(move) == 'e0e9'
        #assert board.copy().move_text('帅五进八') is None

        new_board = board.copy()
        move = new_board.move((4, 0), (4, 9))
        #assert new_board.get_king(ChessSide.BLACK) is None
        assert new_board.to_fen() == '4K4/9/9/9/9/9/9/9/9/9 w'

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
        board = ChessBoard('3k5/9/9/9/9/9/9/9/9/4K4 w')
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

        board = ChessBoard('4k4/9/9/9/9/4R4/9/9/9/5K3 w')
        assert board.copy().move_iccs('e4e9').is_king_killed() is True

        board = ChessBoard('3k5/9/9/9/9/4R4/9/9/9/5K3 w')
        assert board.copy().move_iccs('e4e9').is_king_killed() is False
        assert board.copy().is_checking_move(*iccs2pos('e4e9')) is True
        assert board.is_mirror() is False 

    def test_AA_move(self):

        #middle AA
        board = ChessBoard('4k4/4a4/9/9/9/9/9/9/4A4/4K4 w')
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
        board = ChessBoard('4k4/4a4/4b4/9/9/9/9/4B4/4A4/4K4 w')
        assert board.is_valid_move((4, 2), (2, 0)) is True
        assert board.is_valid_move((4, 2), (6, 0)) is True
        assert board.is_valid_move((4, 2), (2, 4)) is True
        assert board.is_valid_move((4, 2), (6, 4)) is True
        moves = list(board.create_piece_moves((4, 2)))
        assert len(moves) == 4
        moves = list(board.create_piece_moves((4, 7)))
        assert len(moves) == 0

        #block BB
        board = ChessBoard('4k4/3ca4/4b4/3c5/9/9/9/4B4/3CAC3/4K4 w')
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
        board = ChessBoard('4k4/9/9/4p4/4P4/9/9/9/9/4K4 w')
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
        board = ChessBoard('4k4/9/9/9/5r3/9/9/9/9/3K1R3 w')
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
        board = ChessBoard('4k4/9/2c6/8p/9/8P/9/8C/9/3K5 w')
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
        board = ChessBoard('5k3/9/c8/nc7/p8/4N4/8n/4N4/4C4/4K4 w')
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
        assert move.move_player == RED
        assert move.to_iccs() == 'a0a1'
        assert str(move) == 'a0a1'
        assert move.is_valid_move() is True

        assert iccs2pos('a0a1') == ((0, 0), (0, 1))
        assert pos2iccs((0, 0), (0, 1)) == 'a0a1'
        assert iccs_mirror('a0a1') == 'i0i1'
        assert iccs_flip('a0a1') == 'a9a8'
        assert iccs_swap('a0a1') == 'i9i8'

        assert move.to_text() == '车九进一'
        #assert move.from_text(board, '车九进一') == ((0,0), (0,1))
    
    def test_qianhou_move(self):
        board = ChessBoard('r1bak1b1r/4a4/2n1ccn2/p1p1C1p1p/9/9/P1P1P1P1P/4C1N2/9/RNBAKABR1 w')
        move = board.copy().move_text('前炮退二')
        assert move.move_player == RED
        
    def test_board_text(self):
        board = ChessBoard(FULL_INIT_FEN)
        board_txt = board.text_view()
        good_txt = [
            '9 砗──碼──象──士──将──士──象──碼──砗',
            '  │   │   │   │ ＼│／ │   │   │   │ ',
            '8 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
            '  │   │　 │   │ ／│＼ │   │   │   │ ',
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
            '  │   │   │   │ ＼│／ │　 │　 │　 │ ',
            '1 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
            '  │   │　 │   │ ／│＼ │　 │   │   │ ',
            '0 车──马──相──仕──帅──仕──相──马──车',
            '   ',
            '  a   b   c   d   e   f   g   h   i ',
            '  0   1   2   3   4   5   6   7   8 ',
        ]
        for i in range(len(board_txt)):
            assert board_txt[i] == good_txt[i]

    def test_text(self):
        board = ChessBoard(FULL_INIT_FEN)
        assert board.copy().move_text('炮二平五').to_text() == '炮二平五'
        
        assert board.copy().move((7, 2), (4, 2)).to_text() == '炮二平五'
        assert board.copy().move((1, 2), (1, 1)).to_text() == '炮八退一'
        assert board.copy().move((7, 2), (7, 6)).to_text() == '炮二进四'
        assert board.copy().move((6, 3), (6, 4)).to_text() == '兵三进一'
        assert board.copy().move((8, 0), (8, 1)).to_text() == '车一进一'
        assert board.copy().move((4, 0), (4, 1)).to_text() == '帅五进一'
        assert board.copy().move((2, 0), (4, 2)).to_text() == '相七进五'
        assert board.copy().move((5, 0), (4, 1)).to_text() == '仕四进五'
        assert board.copy().move((7, 0), (6, 2)).to_text() == '马二进三'
        board.next_turn()
        assert board.copy().move_text('炮８平５').to_text() == '炮８平５'
        assert board.copy().move_text('炮8平5').to_text()   == '炮８平５'
        assert board.copy().move((7, 7), (4, 7)).to_text() == '炮８平５'
        assert board.copy().move((7, 7), (7, 3)).to_text() == '炮８进４'
        assert board.copy().move((0, 9), (0, 8)).to_text() == '车１进１'
        assert board.copy().move((4, 9), (4, 8)).to_text() == '将５进１'

    def test_hash(self):
        board = ChessBoard(FULL_INIT_FEN)
        assert board.zhash() == 7101337512282506414
        assert board.zhash(FULL_INIT_FEN) == 7101337512282506414
        b = board.mirror()
        assert b.zhash() == 7101337512282506414
        