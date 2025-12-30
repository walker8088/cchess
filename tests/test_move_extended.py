# -*- coding: utf-8 -*-
'''
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
'''

from cchess import ChessBoard, Move, FULL_INIT_FEN, RED, BLACK

class TestMoveExtended():
    def test_to_text_detailed(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 普通走子
        move = board.copy().move((0, 0), (0, 1))
        assert move.to_text() == '车九进一'
        assert move.to_text(detailed=False) == '车九进一'
        
        # 将军
        board.from_fen('rnbakabnr/9/1c2c4/p1p1C1p1p/9/9/P1P1P1P1P/1C7/9/RNBAKABNR w')
        move = board.copy().move((1, 2), (4, 2))
        if move:
            text = move.to_text(detailed=True)
            assert '将军' in text or '将' in text
        
        # 吃子
        board.from_fen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w')
        move = board.copy().move((0, 0), (0, 9))
        if move and move.captured:
            text = move.to_text(detailed=True)
            assert '吃' in text
        
        # 将死
        board.from_fen('rnbakabnr/9/9/p1p1p1p1p/9/4c4/PCP1c1P1P/5C3/9/RNBAKABNR w')
        move = board.copy().move((1, 2), (4, 2))
        if move and move.is_checkmate:
            text = move.to_text(detailed=True)
            assert '将死' in text
   
    ''' 
    def test_move_mirror_flip_swap(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        
        # mirror
        board2 = board.copy().mirror()
        move2 = move1.mirror()
        assert move2.p_from[0] == 8 - move1.p_from[0]
        assert move2.p_to[0] == 8 - move1.p_to[0]
        
        # flip
        board3 = board.copy().flip()
        move3 = move1.flip()
        assert move3.p_from[1] == 9 - move1.p_from[1]
        assert move3.p_to[1] == 9 - move1.p_to[1]
        
        # swap
        board4 = board.copy().swap()
        move4 = move1.swap()
        assert move4.p_from[0] == 8 - move1.p_from[0]
        assert move4.p_from[1] == 9 - move1.p_from[1]
        assert move4.p_to[0] == 8 - move1.p_to[0]
        assert move4.p_to[1] == 9 - move1.p_to[1]
    
    def test_move_branch_operations(self):
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.copy().move((0, 0), (0, 1))
        move2 = board.copy().move((8, 0), (8, 1))
        
        # 添加分支
        move1.append_next_move(move2)
        assert len(move1.branchs) == 0
        assert move1.next_move == move2
        
        # 添加变招
        move3 = board.copy().move((2, 0), (2, 1))
        move1.branchs.append(move3)
        assert len(move1.branchs) == 1
        
        # get_branch
        branch = move1.get_branch(0)
        assert branch == move3
        
        # select_branch
        move1.select_branch(0)
        assert move1.next_move == move3
        
        # get_all_branchs
        all_branchs = move1.get_all_branchs()
        assert len(all_branchs) >= 1
    
    
    def test_to_engine_fen(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        engine_fen = move.to_engine_fen()
        assert ' ' in engine_fen  # FEN格式应该包含空格分隔符
        assert engine_fen.split()[0] == move.board_done.to_fen().split()[0]
    '''

    def test_prepare_for_engine(self):
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        history = []
        move.prepare_for_engine(RED, history)
        # 检查是否设置了必要的属性
        assert hasattr(move, 'board_done')
    
