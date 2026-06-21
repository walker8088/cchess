"""验证 README.md 中的代码示例是否正确"""

import os
import sys
from pathlib import Path


def test_init():
    """测试初始化 - 默认行为 vs 初始局面"""
    print("=" * 60)
    print("1. 测试初始化")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard()
        # 注意：默认 ChessBoard() 是空棋盘！不是初始局面
        if board.to_fen().startswith("9/9/9/9/9/9/9/9/9/9"):
            print(f"⚠ 默认 ChessBoard() 是空棋盘（FEN: {board.to_fen()[:20]}...）")
            print(f"   初始局面需要使用 ChessBoard(FULL_INIT_FEN) 或 from_fen()")

        # 使用 FULL_INIT_FEN 测试初始局面
        board2 = ChessBoard(FULL_INIT_FEN)
        if "rnbakabnr" in board2.to_fen():
            print(f"✓ FULL_INIT_FEN 初始化正确")
        else:
            print(f"✗ FULL_INIT_FEN 初始化失败: {board2.to_fen()}")

        # 测试 from_fen
        board3 = ChessBoard()
        board3.from_fen(
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        )
        if "rnbakabnr" in board3.to_fen():
            print(f"✓ from_fen 初始化正确")
            return True
        else:
            print(f"✗ from_fen 初始化失败")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False


def test_print_view():
    """测试棋盘显示"""
    print("=" * 60)
    print("2. 测试棋盘显示")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard(FULL_INIT_FEN)

        # print_view() - 实际存在
        board_strs = board.print_view()
        if isinstance(board_strs, (list, tuple)) and len(board_strs) > 0:
            print(f"✓ print_view() 存在并返回 {len(board_strs)} 行")
            return True
        else:
            print(f"✗ print_view() 返回类型错误: {type(board_strs)}")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_move_internal():
    """测试内部格式走子"""
    print("=" * 60)
    print("3. 测试内部格式走子")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        # 注意：必须使用 FULL_INIT_FEN，否则默认是空棋盘
        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move((0, 0), (0, 1))
        text = move.to_text()
        print(f"✓ move((0,0), (0,1)): {text}")
        if text == "车九进一":
            print(f"✓ 中文文本匹配 README 期望值")
            return True
        else:
            print(f"⚠ 实际为 '{text}', 期望 '车九进一'")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_move_iccs():
    """测试 ICCS 格式走子"""
    print("=" * 60)
    print("4. 测试 ICCS 格式走子")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move_iccs("a0a1")
        text = move.to_text()
        print(f"✓ move_iccs('a0a1'): {text}")
        if text == "车九进一":
            print(f"✓ 中文文本匹配 README 期望值")
            return True
        else:
            print(f"⚠ 实际为 '{text}', 期望 '车九进一'")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_move_text():
    """测试中文格式走子"""
    print("=" * 60)
    print("5. 测试中文格式走子")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard(FULL_INIT_FEN)
        move = board.copy().move_text("车九进一")
        text = move.to_text()
        print(f"✓ move_text('车九进一'): {text}")
        if text == "车九进一":
            print(f"✓ 中文文本匹配 README 期望值")
            return True
        else:
            print(f"⚠ 实际为 '{text}', 期望 '车九进一'")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_create_piece_moves():
    """测试产生某个棋子的合法走子"""
    print("=" * 60)
    print("6. 测试产生某个棋子的合法走子")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_piece_moves((0, 0)))
        print(f"✓ 车在 (0,0) 的合法走子数量: {len(moves)}")
        if len(moves) > 0:
            for mv in moves[:3]:
                move = board.copy().move(*mv)
                print(f"  - {move.to_text()}")
            return True
        else:
            print(f"⚠ 没有合法走子")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_create_moves():
    """测试产生所有合法走子"""
    print("=" * 60)
    print("7. 测试产生所有合法走子")
    print("=" * 60)
    try:
        from cchess import FULL_INIT_FEN, ChessBoard

        board = ChessBoard(FULL_INIT_FEN)
        moves = list(board.create_moves())
        print(f"✓ 初始局面合法走子数量: {len(moves)}")
        if len(moves) > 30:  # 初始局面应该有 44 个走子
            return True
        else:
            print(f"⚠ 走子数量过少")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_is_checking():
    """测试将军检测"""
    print("=" * 60)
    print("8. 测试将军检测")
    print("=" * 60)
    try:
        from cchess import ChessBoard

        board = ChessBoard()
        board.from_fen("3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1")
        result = board.is_checking()
        print(f"✓ is_checking() = {result}")
        if result is True:
            print(f"✓ 匹配 README 期望值 True")
            return True
        else:
            print(f"⚠ 实际为 {result}, 期望 True")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_is_checkmate():
    """测试将死对方检测"""
    print("=" * 60)
    print("9. 测试将死对方检测")
    print("=" * 60)
    try:
        from cchess import ChessBoard

        board = ChessBoard()
        board.from_fen("3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1")
        result = board.is_checkmate()
        print(f"✓ is_checkmate() = {result}")
        if result is True:
            print(f"✓ 匹配 README 期望值 True")
            return True
        else:
            print(f"⚠ 实际为 {result}, 期望 True")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_is_checked_move():
    """测试走子被将军检测"""
    print("=" * 60)
    print("10. 测试走子被将军检测")
    print("=" * 60)
    try:
        from cchess import ChessBoard

        board = ChessBoard()
        board.from_fen("3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1")

        # 方式 1：走子前检查（推荐）
        result1 = board.is_checking_move((3, 9), (4, 9))
        print(f"✓ is_checking_move((3,9), (4,9)) = {result1}")

        # 方式 2：走子后检查（使用 copy）
        mv = board.copy().move_iccs("d9e9")
        result2 = board.is_checking_move(mv.pos_from, mv.pos_to)
        print(f"✓ copy().move_iccs + is_checking_move = {result2}")

        if result1 is True and result2 is True:
            return True
        else:
            print(f"⚠ 结果不匹配 README 期望值 True")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_has_no_legal_moves():
    """测试被对方将死检测"""
    print("=" * 60)
    print("11. 测试被对方将死检测")
    print("=" * 60)
    try:
        from cchess import ChessBoard

        board = ChessBoard()
        board.from_fen("3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1")
        result = board.has_no_legal_moves()
        print(f"✓ has_no_legal_moves() = {result}")
        if result is True:
            print(f"✓ 匹配 README 期望值 True")
            return True
        else:
            print(f"⚠ 实际为 {result}, 期望 True")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_read_xqf():
    """测试读取 xqf 文件"""
    print("=" * 60)
    print("12. 测试读取 xqf 文件")
    print("=" * 60)
    try:
        from cchess import Book

        # 查找测试数据目录
        data_dir = Path(__file__).parent / "tests" / "data"
        xqf_files = list(data_dir.glob("*.xqf")) + list(data_dir.glob("*.XQF"))
        if not xqf_files:
            print(f"⚠ 未找到 .xqf 测试文件，跳过")
            return True

        book = Book.read_from(str(xqf_files[0]))
        print(f"✓ 读取 XQF 文件: {xqf_files[0].name}")

        # print_init_board
        if hasattr(book, "print_init_board"):
            book.print_init_board()
            print(f"✓ print_init_board() 调用成功")
        else:
            print(f"⚠ Book 没有 print_init_board 方法")
            return False

        # print_text_moves
        if hasattr(book, "print_text_moves"):
            book.print_text_moves()
            print(f"✓ print_text_moves() 调用成功")
        else:
            print(f"⚠ Book 没有 print_text_moves 方法")
            return False

        return True
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_read_cbr():
    """测试读取 cbr 文件"""
    print("=" * 60)
    print("13. 测试读取 cbr 文件")
    print("=" * 60)
    try:
        from cchess import Book

        # 查找测试数据目录
        data_dir = Path(__file__).parent / "tests" / "data"
        cbr_files = list(data_dir.glob("*.cbr")) + list(data_dir.glob("*.CBR"))
        if not cbr_files:
            print(f"⚠ 未找到 .cbr 测试文件，跳过")
            return True

        book = Book.read_from(str(cbr_files[0]))
        print(f"✓ 读取 CBR 文件: {cbr_files[0].name}")

        if hasattr(book, "print_init_board"):
            book.print_init_board()
            print(f"✓ print_init_board() 调用成功")
        else:
            print(f"⚠ Book 没有 print_init_board 方法")
            return False
        if hasattr(book, "print_text_moves"):
            book.print_text_moves()
            print(f"✓ print_text_moves() 调用成功")
        else:
            print(f"⚠ Book 没有 print_text_moves 方法")
            return False

        return True
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_read_cbl():
    """测试读取 cbl 文件"""
    print("=" * 60)
    print("14. 测试读取 cbl 文件")
    print("=" * 60)
    try:
        from cchess import Book

        # 查找测试数据目录
        data_dir = Path(__file__).parent / "tests" / "data"
        cbl_files = list(data_dir.glob("*.cbl")) + list(data_dir.glob("*.CBL"))
        if not cbl_files:
            print(f"⚠ 未找到 .cbl 测试文件，跳过")
            return True

        lib = Book.read_from_lib(str(cbl_files[0]))
        print(f"✓ 读取 CBL 文件: {cbl_files[0].name}")
        print(f"✓ lib 类型: {type(lib)}")

        if isinstance(lib, dict) and "games" in lib:
            print(f"✓ lib 是字典，包含 'games' 键")
            for book in lib["games"][:2]:
                if hasattr(book, "print_init_board"):
                    book.print_init_board()
                if hasattr(book, "print_text_moves"):
                    book.print_text_moves()
            return True
        else:
            print(f"⚠ lib 格式不符合 README 期望")
            return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_engine_load():
    """测试加载引擎对弈（仅检查 API 是否存在，不实际启动引擎）"""
    print("=" * 60)
    print("15. 测试引擎 API 存在性")
    print("=" * 60)
    try:
        from cchess import EngineManager, UcciEngine, UciEngine

        print(f"✓ UcciEngine 存在")
        print(f"✓ UciEngine 存在")
        print(f"✓ EngineManager 存在")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False


def main():
    """运行所有验证"""
    print("\n" + "=" * 60)
    print("README.md 代码示例验证")
    print("=" * 60 + "\n")

    results = []

    tests = [
        ("初始化", test_init),
        ("棋盘显示", test_print_view),
        ("内部格式走子", test_move_internal),
        ("ICCS 格式走子", test_move_iccs),
        ("中文格式走子", test_move_text),
        ("产生棋子走子", test_create_piece_moves),
        ("产生所有走子", test_create_moves),
        ("将军检测", test_is_checking),
        ("将死对方检测", test_is_checkmate),
        ("走子被将军检测", test_is_checked_move),
        ("被对方将死检测", test_has_no_legal_moves),
        ("读取 XQF", test_read_xqf),
        ("读取 CBR", test_read_cbr),
        ("读取 CBL", test_read_cbl),
        ("引擎 API", test_engine_load),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} - 未捕获异常: {e}")
            results.append((name, False))
        print()

    print("=" * 60)
    print("汇总")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print(f"\n通过率: {passed}/{total} ({100 * passed / total:.1f}%)")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
