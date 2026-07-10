"""性能基准测试脚本。

运行方法：
    python bench.py
"""

import sys
import time

sys.path.insert(0, "src")
from cchess.board import ChessBoard
from cchess.common import FULL_INIT_FEN

board = ChessBoard(FULL_INIT_FEN)

# Test 1: get_all_fench_positions
start = time.perf_counter()
for _ in range(10000):
    list(board.get_all_fench_positions())
elapsed = time.perf_counter() - start
print(f"get_all_fench_positions x10000: {elapsed:.3f}s")

# Test 2: create_moves
start = time.perf_counter()
for _ in range(1000):
    list(board.create_moves())
elapsed = time.perf_counter() - start
print(f"create_moves x1000: {elapsed:.3f}s")

# Test 3: move_text (the refactored function)
start = time.perf_counter()
for _ in range(1000):
    b = ChessBoard(FULL_INIT_FEN)
    b.move_text("炮二平五")
elapsed = time.perf_counter() - start
print(f"move_text x1000: {elapsed:.3f}s")
