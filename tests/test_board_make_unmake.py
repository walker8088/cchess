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

import pytest

from cchess.board import ChessBoard, ChessPlayer, MoveInfo
from cchess.common import BLACK, RED


class TestMakeUnmake:
    """测试 make_move 和 unmake_move 功能"""

    def test_make_move_basic(self):
        """测试基本移动"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        # 红帅前进一格
        move_info = board.make_move((4, 0), (4, 1))
        assert isinstance(move_info, MoveInfo)
        assert move_info.from_pos == (4, 0)
        assert move_info.to_pos == (4, 1)
        assert move_info.moving_fench == "K"
        assert move_info.captured_fench is None
        # 检查棋盘状态
        assert board.get_fench((4, 0)) is None
        assert board.get_fench((4, 1)) == "K"
        # make_move 是底层函数，不切换走子方
        assert board.move_side().color == RED

    def test_unmake_move_basic(self):
        """测试撤销移动"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        # 记录初始棋盘
        initial_board = [row[:] for row in board._board]
        # 执行移动
        move_info = board.make_move((4, 0), (4, 1))
        # 撤销
        board.unmake_move(move_info)
        # 检查恢复
        assert board._board == initial_board
        assert board.move_side().color == RED
        assert board._attack_matrix_dirty == True  # 脏标志应为 True，因为移动后设置

    def test_make_capture(self):
        """测试吃子移动"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/4r4/4K4 w")
        # 红帅吃黑车
        move_info = board.make_move((4, 0), (4, 1))
        assert move_info.captured_fench == "r"
        # 检查棋盘状态
        assert board.get_fench((4, 0)) is None
        assert board.get_fench((4, 1)) == "K"

    def test_unmake_capture(self):
        """测试撤销吃子"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/4r4/4K4 w")
        initial_board = [row[:] for row in board._board]
        move_info = board.make_move((4, 0), (4, 1))
        board.unmake_move(move_info)
        # 棋盘应完全恢复
        assert board._board == initial_board
        assert board.get_fench((4, 1)) == "r"

    def test_attack_matrix_dirty_flag(self):
        """测试攻击矩阵脏标志处理"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        # 初始脏标志应为 True
        assert board._attack_matrix_dirty == True
        # 计算攻击矩阵后，脏标志变为 False
        board.is_checking()  # 这会触发重新计算
        assert board._attack_matrix_dirty == False
        # 执行移动
        move_info = board.make_move((4, 0), (4, 1))
        # 移动后脏标志应为 True
        assert board._attack_matrix_dirty == True
        # 撤销移动
        board.unmake_move(move_info)
        # 脏标志应恢复为 False
        assert board._attack_matrix_dirty == False

    def test_move_side_restoration(self):
        """测试走子方恢复"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        initial_player = board.move_side()
        move = board.move((4, 0), (4, 1))
        if move:
            assert board.move_side().color != initial_player.color
            board.unmake_move(move.move_info)
            assert board.move_side().color == initial_player.color

    def test_multiple_moves_unmake(self):
        """测试连续移动和撤销"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        # 记录初始状态
        initial_board = [row[:] for row in board._board]
        # 第一次移动
        move1 = board.make_move((4, 0), (4, 1))
        # 第二次移动（黑方）
        move2 = board.make_move((4, 9), (4, 8))
        # 检查状态
        assert board.get_fench((4, 0)) is None
        assert board.get_fench((4, 1)) == "K"
        assert board.get_fench((4, 9)) is None
        assert board.get_fench((4, 8)) == "k"
        # 撤销第二次移动
        board.unmake_move(move2)
        assert board.get_fench((4, 9)) == "k"
        assert board.get_fench((4, 8)) is None
        # 撤销第一次移动
        board.unmake_move(move1)
        assert board._board == initial_board

    def test_move_info_fields(self):
        """检查 MoveInfo 字段完整性"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        move_info = board.make_move((4, 0), (4, 1))
        # 确保所有字段都存在
        assert hasattr(move_info, "from_pos")
        assert hasattr(move_info, "to_pos")
        assert hasattr(move_info, "moving_fench")
        assert hasattr(move_info, "captured_fench")
        assert hasattr(move_info, "prev_attack_matrix_dirty")
        assert hasattr(move_info, "prev_move_side")
        assert hasattr(move_info, "board_before")

    def test_make_move_invalid(self):
        """测试 make_move 不检查合法性"""
        board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
        # 非法移动（从空位移动），make_move 不会检查，直接执行
        move_info = board.make_move((0, 0), (0, 1))
        # 移动后，棋盘状态会变化（空位移动棋子？实际上 _move_piece 会处理）
        # 这里我们只是确保不会抛出异常
        assert isinstance(move_info, MoveInfo)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
