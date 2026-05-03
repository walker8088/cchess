#!/usr/bin/env python3
"""
API 兼容性测试脚本
测试从 v1.26.1 到当前 HEAD 的 API 不兼容变化
"""

import sys

from cchess import ANY_COLOR, BLACK, FULL_INIT_FEN, RED, ChessBoard, Move


def test_method_renames():
    """测试重命名的方法"""
    print("测试方法重命名...")
    board = ChessBoard(FULL_INIT_FEN)

    # 1. get_fenchs() -> get_fench_positions()
    try:
        # 旧方法应该不存在
        board.get_fenchs("K")
        print("❌ get_fenchs() 仍然存在（应该被重命名）")
        return False
    except AttributeError:
        print("✅ get_fenchs() 已重命名为 get_fench_positions()")

    # 新方法应该存在
    positions = board.get_fench_positions("K")
    print(f"✅ get_fench_positions('K') 返回 {len(positions)} 个位置")

    # 2. get_pieces() -> get_all_pieces()
    try:
        board.get_pieces(RED)
        print("❌ get_pieces() 仍然存在（应该被重命名）")
        return False
    except AttributeError:
        print("✅ get_pieces() 已重命名为 get_all_pieces()")

    pieces = list(board.get_all_pieces(RED))
    print(f"✅ get_all_pieces(RED) 返回 {len(pieces)} 个棋子")

    return True


def test_move_from_text_removal():
    """测试 Move.from_text() 移除"""
    print("\n测试 Move.from_text() 移除...")

    try:
        # 旧方法应该不存在
        Move.from_text("炮二平五", ChessBoard(FULL_INIT_FEN))
        print("❌ Move.from_text() 仍然存在（应该被移除）")
        return False
    except AttributeError:
        print("✅ Move.from_text() 已移除")

    # 新方法 board.move_text() 应该存在
    board = ChessBoard(FULL_INIT_FEN)
    move = board.move_text("炮二平五")
    if move:
        print(f"✅ board.move_text('炮二平五') 返回 Move 对象: {move}")
        return True
    else:
        print("❌ board.move_text() 返回 None")
        return False


def test_chess_player_removal():
    """测试 ChessPlayer 类移除"""
    print("\n测试 ChessPlayer 类移除...")

    try:
        from cchess import ChessPlayer

        print("❌ ChessPlayer 类仍然存在（应该被移除）")
        return False
    except ImportError:
        print("✅ ChessPlayer 类已移除")

    # 现在应该使用整数常量
    print(f"✅ 颜色常量: RED={RED}, BLACK={BLACK}, ANY_COLOR={ANY_COLOR}")

    # 测试颜色使用
    board = ChessBoard(FULL_INIT_FEN)
    board.set_move_side(RED)  # 应该接受整数
    print(f"✅ board.move_side = {board.move_side}")

    return True


def test_method_removals():
    """测试移除的方法"""
    print("\n测试移除的方法...")
    board = ChessBoard(FULL_INIT_FEN)

    # 1. unmake_move()
    try:
        board.unmake_move()
        print("❌ unmake_move() 仍然存在（应该被移除）")
        return False
    except AttributeError:
        print("✅ unmake_move() 已移除")

    # 2. move_any()
    try:
        board.move_any((0, 0), (1, 1))
        print("❌ move_any() 仍然存在（应该被移除）")
        return False
    except AttributeError:
        print("✅ move_any() 已移除")

    return True


def test_move_side_naming():
    """测试 move_side 命名统一"""
    print("\n测试 move_side 命名统一...")
    board = ChessBoard(FULL_INIT_FEN)

    # move_side 属性应该存在
    try:
        side = board.move_side
        print(f"✅ board.move_side = {side}")

        # 应该可以设置
        board.set_move_side(BLACK)
        print(f"✅ board.set_move_side(BLACK) 成功, move_side = {board.move_side}")

        return True
    except AttributeError as e:
        print(f"❌ move_side 相关API错误: {e}")
        return False


def test_no_color_to_any_color():
    """测试 NO_COLOR -> ANY_COLOR 重命名"""
    print("\n测试 NO_COLOR -> ANY_COLOR 重命名...")

    try:
        from cchess import NO_COLOR

        print("❌ NO_COLOR 常量仍然存在（应该被重命名）")
        return False
    except ImportError:
        print("✅ NO_COLOR 已重命名为 ANY_COLOR")

    print(f"✅ ANY_COLOR = {ANY_COLOR}")
    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("CChess API 兼容性测试")
    print("测试从 v1.26.1 到当前 HEAD 的 API 不兼容变化")
    print("=" * 60)

    tests = [
        ("方法重命名", test_method_renames),
        ("Move.from_text() 移除", test_move_from_text_removal),
        ("ChessPlayer 类移除", test_chess_player_removal),
        ("方法移除", test_method_removals),
        ("move_side 命名统一", test_move_side_naming),
        ("NO_COLOR -> ANY_COLOR", test_no_color_to_any_color),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"测试: {name}")
        print("=" * 40)
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ 测试失败，异常: {e}")
            results.append((name, False))

    print(f"\n{'=' * 60}")
    print("测试结果摘要:")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:30} {status}")
        if not success:
            all_passed = False

    print(f"\n{'=' * 60}")
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
