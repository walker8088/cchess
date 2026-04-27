# -*- coding: utf-8 -*-
"""
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
"""

from cchess import ANY_COLOR, BLACK, FULL_INIT_FEN, RED, ChessBoard


class TestBoardExtended:
    def test_set_move_color(self):
        board = ChessBoard(FULL_INIT_FEN)
        board.set_move_side(RED)
        assert board.move_side() == RED

        board.set_move_side(BLACK)
        assert board.move_side() == BLACK

        board.set_move_side(ANY_COLOR)
        assert board.move_side() == ANY_COLOR

    def test_put_fench_pop_fench(self):
        board = ChessBoard()
        # 放置棋子
        board.put_fench("R", (0, 0))
        assert board.get_fench((0, 0)) == "R"

        # 移除棋子
        fench = board.pop_fench((0, 0))
        assert fench == "R"
        assert board.get_fench((0, 0)) is None

    def test_put_fench_chain_calls(self):
        """测试 put_fench 的链式调用功能"""
        board = ChessBoard()

        # 链式调用放置多个棋子
        board.put_fench("K", (4, 0)).put_fench("k", (4, 9)).put_fench(
            "R", (0, 0)
        ).put_fench("r", (0, 9))

        # 验证棋子放置正确
        assert board.get_fench((4, 0)) == "K"
        assert board.get_fench((4, 9)) == "k"
        assert board.get_fench((0, 0)) == "R"
        assert board.get_fench((0, 9)) == "r"

        # 链式调用移除棋子
        board.put_fench(None, (0, 0)).put_fench(None, (0, 9))

        # 验证棋子已移除
        assert board.get_fench((0, 0)) is None
        assert board.get_fench((0, 9)) is None

        # 验证其他棋子仍然存在
        assert board.get_fench((4, 0)) == "K"
        assert board.get_fench((4, 9)) == "k"

    def test_clear_and_from_fen_chain_calls(self):
        """测试 clear 和 from_fen 方法的链式调用"""
        board = ChessBoard()

        # 使用 clear 替代 setup_board(None) 的链式调用示例
        board.clear().put_fench("R", (4, 4)).put_fench("k", (4, 9))

        # 验证棋子放置正确
        assert board.get_fench((4, 4)) == "R"
        assert board.get_fench((4, 9)) == "k"

        # 使用 from_fen 加载特定局面并进行链式调用
        board.from_fen("4k4/9/9/9/9/9/9/9/9/4K4 w").put_fench("R", (0, 0)).put_fench(
            "r", (0, 9)
        )

        # 验证所有棋子放置正确
        assert board.get_fench((4, 0)) == "K"  # 红帅
        assert board.get_fench((4, 9)) == "k"  # 黑将
        assert board.get_fench((0, 0)) == "R"  # 红车
        assert board.get_fench((0, 9)) == "r"  # 黑车

    def test_pop_fench_removal(self):
        """测试 pop_fench 移除棋子功能"""
        board = ChessBoard()

        # 放置棋子
        board.put_fench("R", (0, 0))
        board.put_fench("k", (4, 9))

        # 验证棋子存在
        assert board.get_fench((0, 0)) == "R"
        assert board.get_fench((4, 9)) == "k"

        # 移除棋子并验证返回值
        removed_fench = board.pop_fench((0, 0))
        assert removed_fench == "R"
        assert board.get_fench((0, 0)) is None

        # 移除另一个棋子
        removed_fench = board.pop_fench((4, 9))
        assert removed_fench == "k"
        assert board.get_fench((4, 9)) is None

        # 移除不存在的棋子
        removed_fench = board.pop_fench((1, 1))
        assert removed_fench is None
        assert board.get_fench((1, 1)) is None

    def test_clear_chain_calls(self):
        """测试 clear 方法的链式调用"""
        board = ChessBoard()

        # 先放置一些棋子
        board.put_fench("R", (0, 0))
        board.put_fench("k", (4, 9))
        assert board.get_fench((0, 0)) == "R"
        assert board.get_fench((4, 9)) == "k"

        # 清空棋盘并立即放置新棋子（链式调用）
        board.clear().put_fench("K", (4, 0)).put_fench("r", (0, 9))

        # 验证旧棋子已清除
        assert board.get_fench((0, 0)) is None
        assert board.get_fench((4, 9)) is None

        # 验证新棋子已放置
        assert board.get_fench((4, 0)) == "K"
        assert board.get_fench((0, 9)) == "r"

    def test_from_fen_chain_calls(self):
        """测试 from_fen 方法的链式调用"""
        board = ChessBoard()

        # 从 FEN 加载并立即进行链式调用
        board.from_fen("4k4/9/9/9/9/9/9/9/9/4K4 w").put_fench("R", (0, 0)).put_fench(
            "r", (0, 9)
        )

        # 验证 FEN 中的棋子
        assert board.get_fench((4, 0)) == "K"  # 红帅
        assert board.get_fench((4, 9)) == "k"  # 黑将

        # 验证链式调用添加的棋子
        assert board.get_fench((0, 0)) == "R"  # 红车
        assert board.get_fench((0, 9)) == "r"  # 黑车

    def test_occupied_color(self):
        """测试 occupied 方法获取棋子颜色"""
        board = ChessBoard(FULL_INIT_FEN)
        # 红方棋子
        color = board.occupied((0, 0))
        assert color == RED

        # 黑方棋子
        color = board.occupied((0, 9))
        assert color == BLACK

        # 空位置
        board.clear()
        color = board.occupied((4, 4))
        assert color is None  # 空位置返回None

    def test_get_fench_positions_x(self):
        board = ChessBoard(FULL_INIT_FEN)
        # 获取第0列的所有车
        rooks = board.get_fench_positions_x("R", 0)
        assert len(rooks) == 1
        assert rooks[0] == (0, 0)

        # 获取不存在的棋子
        empty = board.get_fench_positions_x("X", 4)
        assert len(empty) == 0

    def test_get_fench_positions(self):
        """测试 get_fench_positions 方法"""
        board = ChessBoard(FULL_INIT_FEN)

        # 获取所有红车
        red_rooks = board.get_fench_positions("R")
        assert len(red_rooks) == 2
        assert (0, 0) in red_rooks
        assert (8, 0) in red_rooks

        # 获取所有黑车
        black_rooks = board.get_fench_positions("r")
        assert len(black_rooks) == 2
        assert (0, 9) in black_rooks
        assert (8, 9) in black_rooks

        # 获取所有红兵
        red_pawns = board.get_fench_positions("P")
        assert len(red_pawns) == 5
        for i in range(5):
            assert (i * 2, 3) in red_pawns

        # 获取所有黑兵
        black_pawns = board.get_fench_positions("p")
        assert len(black_pawns) == 5
        for i in range(5):
            assert (i * 2, 6) in black_pawns

        # 获取不存在的棋子
        empty = board.get_fench_positions("X")
        assert len(empty) == 0

        # 清空棋盘后测试
        board.clear()
        empty_after_clear = board.get_fench_positions("R")
        assert len(empty_after_clear) == 0

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

        # 从两个棋盘创建move - 返回元组 (pos_from, pos_to) 或 None
        result = board1.create_move_from_board(board2)
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == (0, 0)
        assert result[1] == (0, 1)

    def test_to_full_fen(self):
        board = ChessBoard(FULL_INIT_FEN)
        full_fen = board.to_full_fen()
        assert " " in full_fen
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
        board = ChessBoard("4k4/9/9/9/4R4/9/9/9/9/5K3 w")
        # 车移动到将的同一列可以将军
        is_checking = board.is_checking_move((4, 4), (4, 8))
        assert is_checking is True

        # 非将军走子
        board2 = ChessBoard(FULL_INIT_FEN)
        is_checking = board2.is_checking_move((0, 0), (0, 1))
        assert is_checking is False

    def test_is_mirror(self):
        """测试 is_mirror 方法判断棋盘水平对称性"""
        # 测试初始局面 - 应该是对称的
        board = ChessBoard(FULL_INIT_FEN)
        assert board.is_mirror() is True, "初始局面应该水平对称"

        # 创建对称局面
        symmetric_board = ChessBoard()
        symmetric_board.put_fench("K", (4, 0)).put_fench("k", (4, 9))
        symmetric_board.put_fench("R", (0, 0)).put_fench("R", (8, 0))
        symmetric_board.put_fench("r", (0, 9)).put_fench("r", (8, 9))
        symmetric_board.put_fench("N", (1, 0)).put_fench("N", (7, 0))
        symmetric_board.put_fench("n", (1, 9)).put_fench("n", (7, 9))
        assert symmetric_board.is_mirror() is True, "完全对称局面应该返回True"

        # 创建不对称局面
        asymmetric_board = ChessBoard()
        asymmetric_board.put_fench("K", (4, 0)).put_fench("k", (4, 9))
        asymmetric_board.put_fench("R", (0, 0)).put_fench(
            "R", (7, 0)
        )  # 不对称：右车在(7,0)而不是(8,0)
        asymmetric_board.put_fench("r", (0, 9)).put_fench("r", (8, 9))
        assert asymmetric_board.is_mirror() is False, "不对称局面应该返回False"

        # 测试棋子类型不对称
        type_asymmetric_board = ChessBoard()
        type_asymmetric_board.put_fench("K", (4, 0)).put_fench("k", (4, 9))
        type_asymmetric_board.put_fench("R", (0, 0)).put_fench(
            "N", (8, 0)
        )  # 不对称：左边是车，右边是马
        assert type_asymmetric_board.is_mirror() is False, "棋子类型不对称应该返回False"

        # 测试空棋盘 - 应该对称
        empty_board = ChessBoard()
        empty_board.clear()
        assert empty_board.is_mirror() is True, "空棋盘应该对称"

        # 测试单个棋子在中间列 - 应该对称
        center_board = ChessBoard()
        center_board.put_fench("K", (4, 0))  # 中间列
        assert center_board.is_mirror() is True, "中间列单个棋子应该对称"
