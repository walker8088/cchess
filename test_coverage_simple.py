"""
简单的覆盖率测试脚本，用于测试 board.py 和 move.py 的覆盖率
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import coverage
import pytest


def test_board_coverage():
    """测试 board.py 的覆盖率"""
    print("运行 board.py 覆盖率测试...")

    # 使用 coverage 模块测量覆盖率
    cov = coverage.Coverage(source=["src/cchess"], include=["src/cchess/board.py"])
    cov.start()

    # 运行现有的测试
    pytest.main(
        [
            "tests/test_coverage.py",
            "tests/test_board_move.py",
            "tests/test_board_extended.py",
            "tests/test_board_make_unmake.py",
            "-x",
            "-q",
            "--tb=short",
        ]
    )

    cov.stop()
    cov.save()

    # 获取覆盖率报告
    print("\nboard.py 覆盖率报告:")
    cov.report(show_missing=True, ignore_errors=True)

    # 获取详细信息
    data = cov.get_data()
    measured_files = data.measured_files()

    for file in measured_files:
        if "board.py" in file:
            print(f"\n{file}:")
            analysis = cov.analysis(file)
            lines, excluded, missing = analysis
            print(f"  总行数: {len(lines)}")
            print(f"  执行行数: {len(lines) - len(missing)}")
            print(f"  未执行行数: {len(missing)}")
            if missing:
                print(f"  未执行行号: {sorted(missing)[:20]}")  # 只显示前20个
                if len(missing) > 20:
                    print(f"  ... 还有 {len(missing) - 20} 行未显示")

    return cov


def test_move_coverage():
    """测试 move.py 的覆盖率"""
    print("\n运行 move.py 覆盖率测试...")

    # 使用 coverage 模块测量覆盖率
    cov = coverage.Coverage(source=["src/cchess"], include=["src/cchess/move.py"])
    cov.start()

    # 运行现有的测试
    pytest.main(
        ["tests/test_coverage.py", "tests/test_board_move.py", "-x", "-q", "--tb=short"]
    )

    cov.stop()
    cov.save()

    # 获取覆盖率报告
    print("\nmove.py 覆盖率报告:")
    cov.report(show_missing=True, ignore_errors=True)

    # 获取详细信息
    data = cov.get_data()
    measured_files = data.measured_files()

    for file in measured_files:
        if "move.py" in file:
            print(f"\n{file}:")
            analysis = cov.analysis(file)
            lines, excluded, missing = analysis
            print(f"  总行数: {len(lines)}")
            print(f"  执行行数: {len(lines) - len(missing)}")
            print(f"  未执行行数: {len(missing)}")
            if missing:
                print(f"  未执行行号: {sorted(missing)[:20]}")  # 只显示前20个
                if len(missing) > 20:
                    print(f"  ... 还有 {len(missing) - 20} 行未显示")

    return cov


def create_targeted_tests():
    """创建针对未覆盖代码的测试"""
    print("\n创建针对未覆盖代码的测试...")

    test_code = '''
import pytest
from src.cchess.board import ChessBoard
from src.cchess.common import FULL_INIT_FEN, RED, BLACK
from src.cchess.move import Move

def test_board_symmetry():
    """测试棋盘对称性"""
    board = ChessBoard(FULL_INIT_FEN)
    # 初始棋盘应该对称
    assert board.is_symmetric()

    # 移动后应该不对称
    board.move_iccs("a0a2")
    assert not board.is_symmetric()

def test_board_attack_matrix():
    """测试攻击矩阵"""
    board = ChessBoard(FULL_INIT_FEN)

    # 初始为脏状态
    assert board._attack_matrix_dirty == True

    # 获取攻击后应该变干净
    attacks = board.get_attacks(RED)
    assert board._attack_matrix_dirty == False

    # 攻击矩阵应该有正确形状
    assert isinstance(attacks, list)
    assert len(attacks) == 10
    assert len(attacks[0]) == 9

def test_move_from_board_comprehensive():
    """全面测试 _create_move_from_board"""
    board = ChessBoard(FULL_INIT_FEN)

    # 测试有效走法
    board._move_side = BLACK
    move = board._create_move_from_board((0, 0), (0, 2))
    assert move is not None

    # 测试无效走法（空位置）
    move = board._create_move_from_board((4, 4), (4, 5))
    assert move is None

    # 测试越界
    move = board._create_move_from_board((-1, -1), (0, 0))
    assert move is None

def test_move_text_parsing():
    """测试走法文本解析"""
    board = ChessBoard(FULL_INIT_FEN)

    # 测试有效走法
    move = board.copy().move_text("炮二平五")
    assert move is not None

    # 测试无效走法
    move = board.copy().move_text("无效走法")
    assert move is None

    # 测试多棋子走法
    fen = "3k5/9/9/9/9/9/9/9/4R4/3K1R3 w"
    board2 = ChessBoard(fen)
    move = board2.copy().move_text("前车进一")
    assert move is not None

def test_move_variations():
    """测试走法变着"""
    board = ChessBoard(FULL_INIT_FEN)
    main_move = board.move_iccs("a0a2")

    board2 = ChessBoard(FULL_INIT_FEN)
    var_move = board2.move_iccs("a0a3")

    # 添加变着
    main_move.add_variation(var_move)
    assert len(main_move.variations) == 1

    # 获取变着
    variations = main_move.get_variations()
    assert len(variations) == 1
    assert variations[0] == var_move

def test_move_operations():
    """测试走法操作"""
    board = ChessBoard(FULL_INIT_FEN)
    move = board.move_iccs("a0a2")

    # 测试镜像
    mirrored = move.mirror()
    assert mirrored is not None
    assert mirrored.from_pos[0] == 8 - move.from_pos[0]

    # 测试翻转
    flipped = move.flip()
    assert flipped is not None
    assert flipped.from_pos[1] == 9 - move.from_pos[1]

    # 测试交换
    swapped = move.swap()
    assert swapped is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

    # 保存测试文件
    test_file = os.path.join(
        os.path.dirname(__file__), "tests", "test_targeted_coverage.py"
    )
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"已创建测试文件: {test_file}")
    return test_file


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("中国象棋项目覆盖率测试")
    print("=" * 60)

    # 运行现有测试的覆盖率
    board_cov = test_board_coverage()
    move_cov = test_move_coverage()

    # 创建并运行针对性测试
    test_file = create_targeted_tests()

    print("\n运行针对性测试...")
    result = pytest.main([test_file, "-v", "--tb=short"])

    if result == 0:
        print("\n✅ 针对性测试全部通过")
    else:
        print("\n❌ 针对性测试失败")

    print("\n" + "=" * 60)
    print("覆盖率测试完成")
    print("=" * 60)

    return board_cov, move_cov


if __name__ == "__main__":
    run_all_tests()
