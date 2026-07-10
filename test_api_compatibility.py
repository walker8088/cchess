#!/usr/bin/env python3
"""
API 兼容性测试脚本

测试从 v1.26.2 到 v2.26.1 的不兼容 API 变更。
这些是 MAJOR 2 的破坏性变更，外部用户升级时需要确认：
- 旧 API 已被删除
- 新 API 行为符合预期
"""

import sys

from cchess import (
    FULL_INIT_FEN,
    SIDE_ANY,
    SIDE_BLACK,
    SIDE_RED,
    ChessBoard,
    Move,
)


def test_method_renames():
    """测试重命名的方法：get_fenchs → get_fench_positions。"""
    print("测试方法重命名...")
    board = ChessBoard(FULL_INIT_FEN)

    # 1. get_fenchs() 应该被删除
    try:
        board.get_fenchs("K")
    except AttributeError:
        print("✅ get_fenchs() 已删除")
    else:
        print("❌ get_fenchs() 仍然存在（应该被删除）")
        return False

    # get_fench_positions() 应该存在
    positions = board.get_fench_positions("K")
    print(f"✅ get_fench_positions('K') 返回 {len(positions)} 个位置")

    # 2. get_all_fench_positions() 是当前推荐的 API
    fench_positions = list(board.get_all_fench_positions(SIDE_RED))
    print(f"✅ get_all_fench_positions(SIDE_RED) 返回 {len(fench_positions)} 个红方棋子")

    return True


def test_move_from_text_removal():
    """测试 Move.from_text() → board.move_text()。"""
    print("\n测试 Move.from_text() 移除...")

    try:
        Move.from_text("炮二平五", ChessBoard(FULL_INIT_FEN))  # type: ignore[attr-defined]
    except AttributeError:
        print("✅ Move.from_text() 已移除")
    else:
        print("❌ Move.from_text() 仍然存在（应该被移除）")
        return False

    # 新方法 board.move_text() 应该存在
    board = ChessBoard(FULL_INIT_FEN)
    move = board.move_text("炮二平五")
    if move:
        print(f"✅ board.move_text('炮二平五') 返回 Move 对象: {move}")
        return True

    print("❌ board.move_text() 返回 None")
    return False


def test_chess_player_removal():
    """测试 ChessPlayer 类移除，统一改用 SIDE_RED/SIDE_BLACK/SIDE_ANY 常量。"""
    print("\n测试 ChessPlayer 类移除...")

    try:
        from cchess import ChessPlayer  # noqa: F401  # pylint: disable=import-outside-toplevel
    except ImportError:
        print("✅ ChessPlayer 类已移除")
    else:
        print("❌ ChessPlayer 类仍然存在（应该被移除）")
        return False

    print(f"✅ 颜色常量: SIDE_RED={SIDE_RED}, SIDE_BLACK={SIDE_BLACK}, SIDE_ANY={SIDE_ANY}")

    board = ChessBoard(FULL_INIT_FEN)
    board.set_move_side(SIDE_BLACK)
    if board.move_side() != SIDE_BLACK:
        print(f"❌ set_move_side(SIDE_BLACK) 后 move_side={board.move_side()}")
        return False
    print(f"✅ board.set_move_side(SIDE_BLACK) 成功, move_side = {board.move_side()}")

    return True


def test_legacy_constants_removed():
    """测试旧颜色常量被移除：NO_COLOR/RED/BLACK/ANY_COLOR。"""
    print("\n测试旧颜色常量被移除...")

    failures = []
    for name in ("NO_COLOR", "RED", "BLACK", "ANY_COLOR"):
        try:
            from cchess import name as _unused  # noqa: F401  # pylint: disable=import-outside-toplevel,redefined-builtin
        except ImportError:
            print(f"✅ cchess.{name} 已移除")
        else:  # pragma: no cover - reached only on regression
            del _unused
            print(f"❌ cchess.{name} 仍然存在（应该被移除）")
            failures.append(name)

    return not failures


def test_legacy_methods_removed():
    """测试被移除的方法：unmake_move / move_any 等。"""
    print("\n测试被移除的方法...")

    failures = []
    for method_name in ("unmake_move", "make_move", "move_any"):
        try:
            getattr(ChessBoard(FULL_INIT_FEN), method_name)
        except AttributeError:
            print(f"✅ ChessBoard.{method_name}() 已移除")
        else:  # pragma: no cover - reached only on regression
            print(f"❌ ChessBoard.{method_name}() 仍然存在（应该被移除）")
            failures.append(method_name)

    return not failures


def test_move_side_naming():
    """测试 move_side 命名（替代旧的 move_player）。"""
    print("\n测试 move_side 命名...")

    board = ChessBoard(FULL_INIT_FEN)

    side = board.move_side()
    print(f"✅ board.move_side() = {side}")

    board.set_move_side(SIDE_BLACK)
    if board.move_side() != SIDE_BLACK:
        print(f"❌ set_move_side(SIDE_BLACK) 后 move_side={board.move_side()}")
        return False
    print(f"✅ board.set_move_side(SIDE_BLACK) 成功")
    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("CChess v1.26.2 → v2.26.1 API 不兼容变化测试")
    print("=" * 60)

    tests = [
        ("get_fenchs 重命名", test_method_renames),
        ("Move.from_text() 移除", test_move_from_text_removal),
        ("ChessPlayer 类移除", test_chess_player_removal),
        ("旧颜色常量移除", test_legacy_constants_removed),
        ("方法移除检查", test_legacy_methods_removed),
        ("move_side 命名", test_move_side_naming),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"测试: {name}")
        print("=" * 40)
        try:
            success = test_func()
        except (AttributeError, ImportError, KeyError, TypeError, ValueError) as exc:
            print(f"❌ 测试失败，异常: {exc}")
            success = False
        results.append((name, success))

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
        print("✅ 所有 API 兼容性测试通过!")
        return 0
    print("❌ 部分 API 兼容性测试失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
