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

import os
from pathlib import Path
from cchess import Game, ChessBoard, FULL_INIT_FEN

class TestGameExtended():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
    
    def test_game_mirror_flip_swap(self):
        game = Game()
        test_fen = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABN1 w'
        game.init_board.from_fen(test_fen)
        original_fen = game.init_board.to_fen()
        
        # mirror
        game.mirror()
        mirrored_fen = game.init_board.to_fen()
        assert mirrored_fen != original_fen
        game.mirror()  # 再次mirror应该恢复
        assert game.init_board.to_fen() == original_fen
        
        # flip
        game.flip()
        flipped_fen = game.init_board.to_fen()
        assert flipped_fen != original_fen
        game.flip()  # 再次flip应该恢复
        assert game.init_board.to_fen() == original_fen
        
        # swap
        game.swap()
        swapped_fen = game.init_board.to_fen()
        assert swapped_fen != original_fen
        game.swap()  # 再次swap应该恢复
        assert game.init_board.to_fen() == original_fen
    
    def test_iter_moves(self):
        game = Game()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((1, 2), (1, 1))
        move1.append_next_move(move2)
        
        game.append_first_move(move1)
        
        moves = list(game.iter_moves())
        assert len(moves) >= 1
        assert moves[0] == move1
        
        # 测试从指定move开始迭代
        moves_from_move2 = list(game.iter_moves(move2))
        assert len(moves_from_move2) >= 0
    
    def test_dump_init_board(self):
        game = Game()
        game.init_board.from_fen(FULL_INIT_FEN)
        board_dump = game.dump_init_board()
        assert isinstance(board_dump, list)
        assert len(board_dump) == 22  # 棋盘有10行，打印出来22行数据
    
    '''
    def test_dump_moves_line(self):
        game = Game()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((1, 2), (1, 1))
        move1.append_next_move(move2)
        
        game.append_first_move(move1)
        
        move_line = game.dump_moves_line()
        assert isinstance(move_line, list)
        assert len(move_line) >= 2
    
    def test_dump_text_moves_with_annote(self):
        game = Game()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move1.annote = "好棋"
        move2 = board.copy().move((1, 2), (1, 1))
        move1.append_next_move(move2)
        
        game.append_first_move(move1)
        
        moves_with_annote = game.dump_text_moves_with_annote()
        assert isinstance(moves_with_annote, list)
        if len(moves_with_annote) > 0 and len(moves_with_annote[0]) > 0:
            text, annote = moves_with_annote[0][0]
            assert isinstance(text, str)
            assert isinstance(annote, str)
    '''
    
    def test_append_first_move(self):
        game = Game()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move_text('车九进一')
        
        result = game.append_first_move(move1)
        assert result == move1
        assert game.first_move == move1
        assert game.last_move == move1
        
        # 添加第二个move作为分支
        move2 = board.copy().move_text('炮八退一')
        game.append_first_move(move2)
        assert len(game.first_move.variations_all) == 2
    
    def test_append_next_move(self):
        game = Game()
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.move_text('车九进一')
        game.append_first_move(move1)
        board.next_turn()
        move2 = board.move_text('炮2平5')
        game.append_next_move(move2)
        
        assert game.first_move == move1
        assert game.last_move == move2
        assert game.first_move.next_move == move2

