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

from cchess import ChessBoard, ChessPlayer, FULL_INIT_FEN, RED, BLACK, NO_COLOR

class TestBoardExtended():
    def test_set_move_color(self):
        board = ChessBoard(FULL_INIT_FEN)
        board.set_move_color(RED)
        assert board.move_player == RED
        
        board.set_move_color(BLACK)
        assert board.move_player == BLACK
        
        board.set_move_color(NO_COLOR)
        assert board.move_player == NO_COLOR
    
    def test_put_fench_pop_fench(self):
        board = ChessBoard()
        # 放置棋子
        board.put_fench('R', (0, 0))
        assert board.get_fench((0, 0)) == 'R'
        
        # 移除棋子
        fench = board.pop_fench((0, 0))
        assert fench == 'R'
        assert board.get_fench((0, 0)) is None
    
    def test_get_fench_color(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 红方棋子
        color = board.get_fench_color((0, 0))
        assert color == RED
        
        # 黑方棋子
        color = board.get_fench_color((0, 9))
        assert color == BLACK
        
        # 空位置
        board.clear()
        color = board.get_fench_color((4, 4))
        assert color is None  # 空位置返回None
    
    def test_get_fenchs_x(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 获取第0列的所有车
        rooks = board.get_fenchs_x(0, 'R')
        assert len(rooks) == 1
        assert rooks[0] == (0, 0)
        
        # 获取不存在的棋子
        empty = board.get_fenchs_x(4, 'X')
        assert len(empty) == 0
    
    def test_detect_move_pieces(self):
        board1 = ChessBoard(FULL_INIT_FEN)
        board2 = board1.copy()
        move_result = board2.move((0, 0), (0, 1))
        if move_result:
            board2.next_turn()
        
        # 检测移动的棋子 - 返回两个列表 (p_froms, p_tos)
        p_froms, p_tos = board1.detect_move_pieces(board2)
        assert isinstance(p_froms, list)
        assert isinstance(p_tos, list)
        assert len(p_froms) >= 1
        assert len(p_tos) >= 1
        assert (0, 0) in p_froms
        assert (0, 1) in p_tos
    
    def test_create_move_from_board(self):
        board1 = ChessBoard(FULL_INIT_FEN)
        board2 = board1.copy()
        move_result = board2.move((0, 0), (0, 1))
        if move_result:
            board2.next_turn()
        
        # 从两个棋盘创建move - 返回元组 (p_from, p_to) 或 None
        result = board1.create_move_from_board(board2)
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == (0, 0)
        assert result[1] == (0, 1)
    
    def test_to_full_fen(self):
        board = ChessBoard(FULL_INIT_FEN)
        full_fen = board.to_full_fen()
        assert ' ' in full_fen
        parts = full_fen.split()
        assert len(parts) >= 2  # 至少包含棋盘和走子方
    
    def test_x_line_in_y_line_in(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 测试x_line_in - 返回FEN字符列表
        line = list(board.x_line_in(0, 0, 8))
        assert isinstance(line, list)
        assert len(line) == 7  # 从1到7，不包括0和8
        
        # 测试y_line_in - 返回FEN字符列表
        line = list(board.y_line_in(4, 0, 9))
        assert isinstance(line, list)
        assert len(line) == 8  # 从1到8，不包括0和9
    
    def test_is_checking_move(self):
        # 创建一个简单的将军局面：车和将之间没有阻挡
        # 车在(4,4)，将在(4,9)，车移动到(4,8)可以将军
        board = ChessBoard('4k4/9/9/9/4R4/9/9/9/9/5K3 w')
        # 车移动到将的同一列可以将军
        is_checking = board.is_checking_move((4, 4), (4, 8))
        assert is_checking == True
        
        # 非将军走子
        board2 = ChessBoard(FULL_INIT_FEN)
        is_checking = board2.is_checking_move((0, 0), (0, 1))
        assert is_checking == False

