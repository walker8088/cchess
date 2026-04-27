# -*- coding: utf-8 -*-
"""
CChess 性能基准测试套件

提供可重复的性能测试，自动检测性能回归。
"""

import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from cchess import BLACK, FULL_INIT_FEN, RED, ChessBoard
from cchess.common import fench_to_species
from cchess.piece import Piece


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    name: str
    iterations: int
    total_time: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    ops_per_sec: float


class Benchmark:
    """性能基准测试类"""

    def __init__(self, name: str, iterations: int = 1000):
        """初始化基准测试。

        参数:
            name: 测试名称
            iterations: 迭代次数
        """
        self.name = name
        self.iterations = iterations
        self.results: List[BenchmarkResult] = []

    def run(self, func, *args, **kwargs) -> BenchmarkResult:
        """运行基准测试。

        参数:
            func: 要测试的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        返回:
            BenchmarkResult 对象
        """
        times = []

        # 预热
        for _ in range(10):
            func(*args, **kwargs)

        # 正式测试
        for _ in range(self.iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 转换为毫秒

        avg_time = statistics.mean(times)
        result = BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            total_time=sum(times) / 1000,
            avg_time_ms=avg_time,
            min_time_ms=min(times),
            max_time_ms=max(times),
            std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
            ops_per_sec=1000 / avg_time if avg_time > 0 else 0,
        )

        self.results.append(result)
        return result

    def print_report(self):
        """打印基准测试报告"""
        print(f"\n{'=' * 60}")
        print(f"性能基准测试报告: {self.name}")
        print(f"{'=' * 60}")
        print(f"迭代次数: {self.iterations}")
        print(f"{'=' * 60}")

        for result in self.results:
            print(f"\n测试: {result.name}")
            print(f"  平均耗时: {result.avg_time_ms:.3f} ms")
            print(f"  最小耗时: {result.min_time_ms:.3f} ms")
            print(f"  最大耗时: {result.max_time_ms:.3f} ms")
            print(f"  标准差:   {result.std_dev_ms:.3f} ms")
            print(f"  吞吐量:   {result.ops_per_sec:.1f} ops/sec")


# -----------------------------------------------------#
# 预定义基准测试用例
# -----------------------------------------------------#


def benchmark_get_pieces():
    """测试 get_all_pieces() 性能"""
    board = ChessBoard(FULL_INIT_FEN)
    bench = Benchmark("get_all_pieces", iterations=1000)
    return bench.run(lambda: list(board.get_all_pieces()))


def benchmark_create_moves():
    """测试 create_moves() 性能"""
    board = ChessBoard(FULL_INIT_FEN)
    bench = Benchmark("create_moves", iterations=100)
    return bench.run(lambda: list(board.create_moves()))


def benchmark_is_valid_move():
    """测试 is_valid_move() 性能"""
    board = ChessBoard(FULL_INIT_FEN)
    bench = Benchmark("is_valid_move", iterations=1000)
    return bench.run(lambda: board.is_valid_move((4, 0), (4, 1)))


def benchmark_fench_to_species():
    """测试 fench_to_species() 性能"""
    bench = Benchmark("fench_to_species", iterations=10000)
    return bench.run(lambda: fench_to_species("K"))


def benchmark_rook_moves():
    """测试车走法生成性能"""
    board = ChessBoard("9/9/9/9/9/9/9/9/9/4K4 w")
    board.put_fench("R", (4, 4))
    bench = Benchmark("Rook moves", iterations=1000)
    return bench.run(lambda: list(board.create_piece_moves((4, 4))))


def benchmark_cannon_moves():
    """测试炮走法生成性能"""
    board = ChessBoard("9/9/9/9/9/9/9/9/9/4K4 w")
    board.put_fench("C", (4, 4))
    bench = Benchmark("Cannon moves", iterations=1000)
    return bench.run(lambda: list(board.create_piece_moves((4, 4))))


def benchmark_knight_moves():
    """测试马走法生成性能"""
    board = ChessBoard("9/9/9/9/9/9/9/9/9/4K4 w")
    board.put_fench("N", (4, 4))
    bench = Benchmark("Knight moves", iterations=1000)
    return bench.run(lambda: list(board.create_piece_moves((4, 4))))


def benchmark_pawn_moves():
    """测试兵走法生成性能"""
    board = ChessBoard("9/9/9/9/9/9/9/9/9/4K4 w")
    board.put_fench("P", (4, 4))
    bench = Benchmark("Pawn moves", iterations=1000)
    return bench.run(lambda: list(board.create_piece_moves((4, 4))))


def benchmark_move_text():
    """测试 move_text() 性能"""
    board = ChessBoard(FULL_INIT_FEN)
    bench = Benchmark("move_text", iterations=100)
    return bench.run(lambda: board.move_text("炮二平五"))


def benchmark_normalized():
    """测试 normalized() 性能"""
    board = ChessBoard(FULL_INIT_FEN)
    board.next_turn()  # 切换到黑方
    bench = Benchmark("normalized", iterations=1000)
    return bench.run(lambda: board.normalized())


def run_all_benchmarks():
    """运行所有基准测试"""
    print("\n" + "=" * 60)
    print("CChess 性能基准测试套件")
    print("=" * 60)

    benchmarks = [
        ("get_pieces", benchmark_get_pieces),
        ("create_moves", benchmark_create_moves),
        ("is_valid_move", benchmark_is_valid_move),
        ("fench_to_species", benchmark_fench_to_species),
        ("Rook moves", benchmark_rook_moves),
        ("Cannon moves", benchmark_cannon_moves),
        ("Knight moves", benchmark_knight_moves),
        ("Pawn moves", benchmark_pawn_moves),
        ("move_text", benchmark_move_text),
        ("normalized", benchmark_normalized),
    ]

    results = []
    for name, func in benchmarks:
        print(f"\n运行测试: {name}...")
        try:
            result = func()
            results.append(result)
            print(f"  完成: {result.avg_time_ms:.3f} ms/次")
        except Exception as e:
            print(f"  失败: {e}")

    # 打印汇总报告
    print(f"\n{'=' * 60}")
    print("汇总报告")
    print(f"{'=' * 60}")
    print(f"{'测试名称':<20} {'平均耗时(ms)':<15} {'吞吐量(ops/s)':<15}")
    print("-" * 60)
    for result in results:
        print(
            f"{result.name:<20} {result.avg_time_ms:<15.3f} {result.ops_per_sec:<15.1f}"
        )

    return results


if __name__ == "__main__":
    run_all_benchmarks()
