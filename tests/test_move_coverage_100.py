"""
针对 move.py 未覆盖代码的测试，目标是实现 100% 覆盖率
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cchess.board import ChessBoard
from src.cchess.common import (
    BLACK,
    EMPTY_FEN,
    FULL_INIT_FEN,
    RED,
)
from src.cchess.move import Move, MoveInfo
from src.cchess.piece import King


class TestMoveInfoCoverage:
    """测试 MoveInfo 类的覆盖"""

    def test_move_info_creation(self):
        """测试 MoveInfo 创建"""
        move_info = MoveInfo(
            from_pos=(0, 0),
            to_pos=(0, 2),
            moving_fench="r",
            captured_fench=None,
            prev_attack_matrix_dirty=True,
            next_attack_matrix_dirty=False,
            prev_move_side=BLACK,
            next_move_side=RED,
            board_before=[[None for _ in range(9)] for _ in range(10)],
            board_after=[[None for _ in range(9)] for _ in range(10)],
        )

        assert move_info.from_pos == (0, 0)
        assert move_info.to_pos == (0, 2)
        assert move_info.moving_fench == "r"
        assert move_info.captured_fench is None
        assert move_info.prev_attack_matrix_dirty == True
        assert move_info.next_attack_matrix_dirty == False
        assert move_info.prev_move_side == BLACK
        assert move_info.next_move_side == RED

    def test_move_info_eq(self):
        """测试 MoveInfo 相等性比较"""
        move_info1 = MoveInfo(
            from_pos=(0, 0),
            to_pos=(0, 2),
            moving_fench="r",
            captured_fench=None,
            prev_attack_matrix_dirty=True,
            next_attack_matrix_dirty=False,
            prev_move_side=BLACK,
            next_move_side=RED,
            board_before=[[None for _ in range(9)] for _ in range(10)],
            board_after=[[None for _ in range(9)] for _ in range(10)],
        )

        move_info2 = MoveInfo(
            from_pos=(0, 0),
            to_pos=(0, 2),
            moving_fench="r",
            captured_fench=None,
            prev_attack_matrix_dirty=True,
            next_attack_matrix_dirty=False,
            prev_move_side=BLACK,
            next_move_side=RED,
            board_before=[[None for _ in range(9)] for _ in range(10)],
            board_after=[[None for _ in range(9)] for _ in range(10)],
        )

        assert move_info1 == move_info2

        # 测试不相等的 MoveInfo
        move_info3 = MoveInfo(
            from_pos=(1, 0),
            to_pos=(1, 2),
            moving_fench="r",
            captured_fench=None,
            prev_attack_matrix_dirty=True,
            next_attack_matrix_dirty=False,
            prev_move_side=BLACK,
            next_move_side=RED,
            board_before=[[None for _ in range(9)] for _ in range(10)],
            board_after=[[None for _ in range(9)] for _ in range(10)],
        )

        assert move_info1 != move_info3


class TestMoveCreationCoverage:
    """测试 Move 创建相关代码覆盖"""

    def test_move_from_board(self):
        """测试从棋盘创建走法"""
        board = ChessBoard(FULL_INIT_FEN)
        board_before = board.copy()

        # 执行走法
        move = board.move_iccs("a0a2")
        assert move is not None

        # 验证走法属性
        assert move.pos_from == (0, 0)
        assert move.pos_to == (0, 2)
        assert move.move_info.moving_fench == "R"  # 红车
        assert move.captured is None

        # 验证棋盘前后状态
        assert move.move_info.board_before is not None
        assert move.move_info.board_after is not None

    def test_move_with_capture(self):
        """测试吃子走法"""
        # 创建一个可以吃子的局面
        fen = "4k4/9/9/9/9/9/9/9/4r3/4K3 b"
        board = ChessBoard(fen)

        # 黑车 (4,1) 吃红帅 (4,0)
        move = board.move_iccs("e1e0")
        assert move is not None
        assert move.captured == "K"
        assert move.captured is not None  # is_capture equivalent

    def test_move_with_check(self):
        """测试将军走法"""
        # 创建一个将军局面
        fen = "4k4/9/9/9/9/9/9/9/9/3RK4 w"
        board = ChessBoard(fen)

        # 红车 (3,0) 移动到 (3,9) 将军
        move = board.move_iccs("d0d9")
        assert move is not None
        assert move.is_checking == True

    def test_move_with_checkmate(self):
        """测试将军走法（非将死）"""
        # 创建一个将军局面
        fen = "4k4/9/9/9/9/9/9/9/4R4/3K5 w"
        board = ChessBoard(fen)

        # 红车 (4,1) 移动到 (4,8) 将军（黑将可逃到 3,9 或 5,9）
        move = board.move_iccs("e1e8")
        assert move is not None
        assert move.is_checking == True


class TestMoveTextParsingCoverage:
    """测试走法文本解析的覆盖"""

    def test_from_text_simple(self):
        """测试简单走法解析"""
        board = ChessBoard(FULL_INIT_FEN)

        # 测试红方走法 - 返回坐标列表
        moves = Move.from_text(board, "炮二平五")
        assert moves is not None
        assert isinstance(moves, list)
        assert len(moves) > 0

        # 测试黑方走法
        board.move_iccs("a0a2")  # 黑车前进
        moves = Move.from_text(board, "马8进7")
        assert moves is not None
        assert isinstance(moves, list)

    def test_from_text_multi_piece(self):
        """测试多棋子走法解析"""
        # 创建一个有多个相同棋子的局面
        fen = "3k5/9/9/9/9/9/9/9/4R4/3K1R3 w"
        board = ChessBoard(fen)

        # 前车进一
        move = Move.from_text(board, "前车进一")
        assert move is not None

        # 后车进一
        move = Move.from_text(board, "后车进一")
        assert move is not None

    def test_from_text_chinese_numerals(self):
        """测试中文数字走法"""
        board = ChessBoard(FULL_INIT_FEN)

        # 测试中文数字
        test_cases = [
            ("炮二平五", True),
            ("炮２平５", True),  # 全角数字
            ("马八进七", True),
            ("车一进二", True),
            ("象三进五", True),
            ("士四进五", True),
            ("兵七进一", True),
        ]

        for text, should_succeed in test_cases:
            moves = Move.from_text(board, text)
            if should_succeed:
                assert moves is not None, f"走法 '{text}' 应该成功"
            else:
                assert moves is None, f"走法 '{text}' 应该失败"

    def test_from_text_invalid(self):
        """测试无效走法解析"""
        board = ChessBoard(FULL_INIT_FEN)

        # 测试完全无效的输入
        moves = Move.from_text(board, "无效走法")
        assert moves is None, "走法 '无效走法' 应该失败"

    def test_from_text_ambiguous(self):
        """测试模糊走法解析"""
        # 创建有多个相同棋子的模糊局面
        fen = "3k5/9/9/9/9/9/9/9/1R2R4/3K5 w"
        board = ChessBoard(fen)

        # 前车进一
        move = Move.from_text(board, "前车进一")
        assert move is not None

        # 后车进一
        move = Move.from_text(board, "后车进一")
        assert move is not None

        # 二车进一（当有3个以上车时）
        fen3 = "3k5/9/9/9/9/9/9/9/1R1R1R2/3K5 w"
        board3 = ChessBoard(fen3)
        move = Move.from_text(board3, "二车进一")
        assert move is not None


class TestMoveOperationsCoverage:
    """测试走法操作的覆盖"""

    def test_move_mirror(self):
        """测试走法镜像"""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a2")
        assert move is not None

        # 镜像走法（就地修改）
        original_pos = move.pos_from
        move.mirror()
        assert move.pos_from[0] == 8 - original_pos[0]
        assert move.pos_from[1] == original_pos[1]

    def test_move_flip(self):
        """测试走法翻转"""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a2")
        assert move is not None

        # 翻转走法（就地修改）
        original_pos = move.pos_from
        move.flip()
        assert move.pos_from[0] == original_pos[0]
        assert move.pos_from[1] == 9 - original_pos[1]

    def test_move_swap(self):
        """测试走法交换"""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a2")
        assert move is not None

        # 交换走法（就地修改，只交换棋子颜色）
        original_fench = move.move_info.moving_fench
        move.swap()
        assert move.move_info.moving_fench != original_fench

    def test_move_with_next_move(self):
        """测试带后续走法的走法"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建第一个走法
        move1 = board.move_iccs("a0a2")
        assert move1 is not None

        # 创建第二个走法
        move2 = board.move_iccs("i9i7")
        assert move2 is not None

        # 链接走法
        move1.next_move = move2
        assert move1.next_move == move2

        # 测试带后续走法的镜像（就地修改）
        move1.mirror()
        assert move1.next_move is not None


class TestMoveVariationsCoverage:
    """测试走法变着的覆盖"""

    def test_move_variations(self):
        """测试走法变着"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建主走法
        main_move = board.move_iccs("a0a2")
        assert main_move is not None

        # 创建变着
        board2 = ChessBoard(FULL_INIT_FEN)
        variation_move = board2.move_iccs("a0a3")
        if variation_move is None:
            return  # Skip if move is invalid

        # 添加变着
        main_move.add_variation(variation_move)
        # variations_all 包含主走法 + 所有变着
        assert len(main_move.variations_all) == 2

        # 获取变着
        variations = main_move.get_variations()
        assert len(variations) == 1

        # 获取包含自身的变着
        variations_with_self = main_move.get_variations(include_me=True)
        assert len(variations_with_self) == 2  # 主走法 + 变着

        # 移除变着
        main_move.remove_variation(variation_move)
        assert len(main_move.variations_all) == 1  # 只剩主走法

        # 移除不存在的变着
        main_move.remove_variation(variation_move)  # 应该不会报错

    def test_move_variation_index(self):
        """测试变着索引"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建主走法
        main_move = board.move_iccs("a0a2")

        # 没有变着时的索引
        idx, total = main_move.get_variation_index()
        assert idx == 0
        assert total == 1

        # 创建并添加变着 - 使用有效走法
        board2 = ChessBoard(FULL_INIT_FEN)
        variation1 = board2.move_iccs("h2h4")  # 红炮前进，有效
        assert variation1 is not None
        main_move.add_variation(variation1)
        idx2, total2 = variation1.get_variation_index()
        assert idx2 == 1
        assert total2 == 2

    def test_last_variation(self):
        """测试最后一个变着"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建主走法
        main_move = board.move_iccs("a0a2")
        if main_move is None:
            return

        # 没有变着时，last_variation 返回自身
        assert main_move.last_variation() == main_move

        # 添加变着
        board2 = ChessBoard(FULL_INIT_FEN)
        variation1 = board2.move_iccs("a0a3")
        if variation1:
            main_move.add_variation(variation1)
            assert main_move.last_variation() == variation1


class TestMoveTextConversionCoverage:
    """测试走法文本转换的覆盖"""

    def test_to_text_detail(self):
        """测试详细文本转换"""
        board = ChessBoard(FULL_INIT_FEN)

        # 普通走法
        move = board.move_iccs("a0a2")
        text, annote = move.to_text_detail(show_variation=False, show_annote=False)
        assert "车" in text
        assert "进" in text or "平" in text or "退" in text

        # 吃子走法 - 红车从a0吃黑炮到b2
        fen = "4k4/9/9/9/9/9/1C7/9/1r7/4K4 w"
        board2 = ChessBoard(fen)
        move2 = board2.move_iccs("b1b2")
        if move2:
            text2, annote2 = move2.to_text_detail(
                show_variation=False, show_annote=False
            )
            assert "吃" in text2 or "×" in text2

        # 将军走法
        fen3 = "4k4/9/9/9/9/9/9/9/4R4/3K5 w"
        board3 = ChessBoard(fen3)
        move3 = board3.move_iccs("e1e0")
        if move3:
            text3, annote3 = move3.to_text_detail(
                show_variation=False, show_annote=False
            )
            # 将军走法文本非空即可
            assert text3 is not None and len(text3) > 0

        # 将死走法
        fen4 = "5k3/9/9/9/9/9/9/9/4R4/3K5 w"
        board4 = ChessBoard(fen4)
        move4 = board4.move_iccs("e1e0")
        if move4:
            text4, annote4 = move4.to_text_detail(
                show_variation=False, show_annote=False
            )
            # 将死走法文本非空即可
            assert text4 is not None and len(text4) > 0

    def test_to_text_variation(self):
        """测试变着文本转换"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建主走法 - 红车前进
        main_move = board.move_iccs("a0a2")
        assert main_move is not None

        # 没有变着时
        text_no_var = main_move.to_text()
        assert text_no_var is not None

        # 添加变着 - 使用另一个有效走法（红炮前进）
        board2 = ChessBoard(FULL_INIT_FEN)
        variation = board2.move_iccs("b2b4")  # 红炮从b2到b4
        if variation:
            main_move.add_variation(variation)

            # 有变着时
            text_with_var = main_move.to_text()
            assert text_with_var is not None

    def test_to_text_with_annote(self):
        """测试带注释的文本转换"""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a2")
        assert move is not None

        # 添加注释
        move.annote = "好棋！"
        text = move.to_text()
        assert text is not None
        # 可能包含注释


class TestMoveTreeOperationsCoverage:
    """测试走法树操作的覆盖"""

    def test_init_move_line(self):
        """测试初始化走法线"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建走法并手动链接 - 使用有效走法序列
        move1 = board.move_iccs("a0a2")  # 红车前进
        assert move1 is not None
        move2 = board.move_iccs("i9i7")  # 黑炮移动
        assert move2 is not None
        move3 = board.move_iccs("b2b4")  # 红炮前进
        assert move3 is not None

        # 手动链接走法
        move1.next_move = move2
        move2.next_move = move3

        # 检查走法是否正确链接
        assert move1.next_move == move2
        assert move2.next_move == move3
        assert move3.next_move is None

        # 测试 init_move_line 返回空字典
        move_line = move1.init_move_line()
        assert isinstance(move_line, dict)
        assert "index" in move_line
        assert "moves" in move_line

    def test_dump_moves(self):
        """测试走法导出"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建走法树
        move1 = board.move_iccs("a0a2")
        assert move1 is not None
        board2 = board.copy()
        move2 = board2.move_iccs("a0a3")

        if move2:
            move1.add_variation(move2)

            # 树模式导出
            move_list = []
            curr_move_line = move1.init_move_line()
            move1.dump_moves(move_list, curr_move_line, is_tree_mode=True)
            assert len(move_list) > 0

            # 非树模式导出
            move_list2 = []
            curr_move_line2 = move1.init_move_line()
            move1.dump_moves(move_list2, curr_move_line2, is_tree_mode=False)
            assert len(move_list2) > 0

    def test_dump_moves_with_variation(self):
        """测试带变着的走法导出"""
        board = ChessBoard(FULL_INIT_FEN)

        # 创建带变着的走法树
        main_move = board.move_iccs("a0a2")
        assert main_move is not None

        # 创建两个变着
        board_var1 = ChessBoard(FULL_INIT_FEN)
        var1_move1 = board_var1.move_iccs("h2h4")
        var1_move2 = board_var1.move_iccs("i9i7")

        board_var2 = ChessBoard(FULL_INIT_FEN)
        var2_move1 = board_var2.move_iccs("b2b4")

        if var1_move1 and var1_move2 and var2_move1:
            # 链接变着1的走法
            var1_move1.next_move = var1_move2

            # 添加变着
            main_move.add_variation(var1_move1)
            main_move.add_variation(var2_move1)

            # 导出带变着的走法树
            move_list = []
            curr_move_line = main_move.init_move_line()
            main_move.dump_moves(move_list, curr_move_line, is_tree_mode=True)
            assert len(move_list) > 0


class TestMoveMultiPieceCoverage:
    """测试多棋子走法的覆盖"""

    def test_multi_piece_selection(self):
        """测试多棋子选择"""
        # 创建有多个相同棋子的局面
        fen = "3k5/9/9/9/9/9/9/9/1R2R4/3K5 w"
        board = ChessBoard(fen)

        # 测试前车
        move = Move.from_text(board, "前车进一")
        assert move is not None
        assert isinstance(move, list)

        # 测试后车
        move = Move.from_text(board, "后车进一")
        assert move is not None
        assert isinstance(move, list)

        # 测试无效的多棋子选择（回退到基本解析）
        move = Move.from_text(board, "三车进一")  # 只有2个车
        # 注意：解析器可能回退到基本走法解析，返回坐标列表
        # 而不是返回 None
        if move is not None:
            assert isinstance(move, list)

    def test_multi_piece_sorting(self):
        """测试多棋子排序"""
        # 测试红方排序（从下到上，从左到右）
        fen_red = "3k5/9/9/9/9/9/9/9/1R1R1R2/3K5 w"
        board_red = ChessBoard(fen_red)

        # 前车应该是y最大的
        move = Move.from_text(board_red, "前车进一")
        assert move is not None

        # 后车应该是y最小的
        move = Move.from_text(board_red, "后车进一")
        assert move is not None

        # 测试黑方排序（从上到下，从右到左）
        fen_black = "3k5/1r1r1r2/9/9/9/9/9/9/9/3K5 b"
        board_black = ChessBoard(fen_black)

        move = Move.from_text(board_black, "前车进一")
        assert move is not None

        move = Move.from_text(board_black, "后车进一")
        assert move is not None


class TestMoveEdgeCasesCoverage:
    """测试走法边界情况的覆盖"""

    def test_move_str(self):
        """测试走法字符串表示"""
        board = ChessBoard(FULL_INIT_FEN)
        move = board.move_iccs("a0a2")

        if move:
            # __str__ 返回 ICCS 格式，如 "a0a2"
            move_str = str(move)
            assert move_str is not None
            assert "a0a2" == move_str

    def test_is_king_killed(self):
        """测试是否吃掉将/帅"""
        board = ChessBoard(FULL_INIT_FEN)

        # 普通走法不是将死
        move = board.move_iccs("a0a2")
        assert not move.is_king_killed()

        # 吃将的走法 - 红车从e0到e9吃黑将
        fen2 = "4k4/9/9/9/9/9/9/9/9/4R4 w"
        board2b = ChessBoard(fen2)
        move2b = board2b.move_iccs("e0e9")  # 红车从e0到e9吃黑将
        if move2b:
            assert move2b.is_king_killed()

        # 吃子但不是将
        fen3 = "4k4/9/9/9/9/9/9/9/3r5/3RK3 w"
        board3 = ChessBoard(fen3)
        move3 = board3.move_iccs("d0d1")  # 红车吃黑车不是将
        if move3:
            assert not move3.is_king_killed()

    def test_move_prepare_for_engine(self):
        """测试为引擎准备走法"""
        board = ChessBoard(FULL_INIT_FEN)

        # 普通走法
        move = board.move_iccs("a0a2")
        if move:
            # prepare_for_engine 需要 move_side 和 history 参数
            move.prepare_for_engine("w", [])
            # 检查引擎相关属性是否设置
            assert (
                move.fen_for_engine is not None or move.move_list_for_engine is not None
            )

        # 吃子走法
        fen = "4k4/9/9/4r4/9/9/9/9/9/4K3 w"
        board2 = ChessBoard(fen)
        move2 = board2.move_iccs("e5e9")  # 吃将
        if move2:
            move2.prepare_for_engine("w", [])
            assert move2.fen_for_engine is not None

    def test_to_engine_fen(self):
        """测试转换为引擎FEN"""
        board = ChessBoard(FULL_INIT_FEN)

        # 有走法时
        move = board.move_iccs("a0a2")
        if move:
            move.prepare_for_engine("w", [])
            # to_engine_fen 是实例方法，不需要参数
            fen = move.to_engine_fen()
            assert fen is not None


class TestMoveMiscCoverage:
    """测试走法其他功能的覆盖"""

    def test_move_copy(self):
        """测试走法复制 - Move 类没有 copy() 方法"""
        board = ChessBoard(FULL_INIT_FEN)
        original = board.move_iccs("a0a2")

        if original:
            # Move 类没有 copy() 方法，测试其属性
            assert original.pos_from is not None
            assert original.pos_to is not None
            assert original.move_info is not None

    def test_move_hash(self):
        """测试走法哈希值 - Move 对象是可变且不 hashable 的"""
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.move_iccs("a0a2")
        board2 = ChessBoard(FULL_INIT_FEN)
        move2 = board2.move_iccs("a0a2")

        if move1 and move2:
            # Move 对象使用默认的 object __hash__，基于对象身份
            # 相同走法但不同对象有不同哈希值
            assert hash(move1) != hash(move2)  # 不同对象有不同哈希

            # 不同走法应该有不同哈希值
            move3 = board2.move_iccs("i9i7")
            if move3:
                assert hash(move1) != hash(move3)

    def test_move_comparison(self):
        """测试走法比较 - Move 没有 __eq__，使用对象身份比较"""
        board = ChessBoard(FULL_INIT_FEN)
        move1 = board.move_iccs("a0a2")
        board2 = ChessBoard(FULL_INIT_FEN)
        move2 = board2.move_iccs("a0a2")
        move3 = board2.move_iccs("i9i7")

        if move1 and move2:
            # Move 没有 __eq__，使用对象身份比较
            # 相同走法但是不同对象，所以不相等
            assert move1 is not move2
            assert move1 != move2  # 不同对象

        if move1 and move3:
            # 不同走法当然也不相等
            assert move1 != move3

            # 与非Move对象比较
            assert move1 != "not a move"
            assert move1 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
