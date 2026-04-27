"""修复循环导入问题的脚本 - 将 fen_mirror/fen_flip/fen_swap 从 common.py 移到 board.py"""

import re
from pathlib import Path

# ==========================================
# 修改 1: board.py - 在文件末尾添加三个函数
# ==========================================
board_path = Path(__file__).parent / "src" / "cchess" / "board.py"
content = board_path.read_text(encoding="utf-8")

board_addition = '''

# -----------------------------------------------------#
# 模块级 FEN 变换函数（避免从 common.py 导入 board 导致循环导入）
def fen_mirror(fen: str) -> str:
    """返回 FEN 字符串的水平镜像版本（左右翻转）。"""
    return ChessBoard.fen_mirror(fen)


def fen_flip(fen: str) -> str:
    """返回 FEN 字符串的垂直翻转版本（上下翻转）。"""
    return ChessBoard.fen_flip(fen)


def fen_swap(fen: str) -> str:
    """返回 FEN 字符串的交换版本（红黑互换）。"""
    return ChessBoard.fen_swap(fen)
'''

board_path.write_text(content + board_addition, encoding="utf-8")
print("1. board.py - 添加完成")

# ==========================================
# 修改 2: common.py - 删除三个函数及 __all__ 中的引用
# ==========================================
common_path = Path(__file__).parent / "src" / "cchess" / "common.py"
content = common_path.read_text(encoding="utf-8")

# 删除三个函数（匹配实际的函数定义）
content = re.sub(
    r"\ndef fen_mirror\(fen\):\n    from \.board import ChessBoard\n\n    return ChessBoard\.fen_mirror\(fen\)\n\n\ndef fen_flip\(fen\):\n    from \.board import ChessBoard\n\n    return ChessBoard\.fen_flip\(fen\)\n\n\ndef fen_swap\(fen\):\n    from \.board import ChessBoard\n\n    return ChessBoard\.fen_swap\(fen\)\n",
    "\n",
    content,
)

# 从 __all__ 中删除 fen_flip, fen_mirror, fen_swap
content = re.sub(r'    "fen_flip",\n', "", content)
content = re.sub(r'    "fen_mirror",\n', "", content)
content = re.sub(r'    "fen_swap",\n', "", content)

common_path.write_text(content, encoding="utf-8")
print("2. common.py - 删除完成")

# ==========================================
# 修改 3: __init__.py - 更新导入
# ==========================================
init_path = Path(__file__).parent / "src" / "cchess" / "__init__.py"
content = init_path.read_text(encoding="utf-8")

# 修改 board import - 添加 fen_flip, fen_mirror, fen_swap
content = content.replace(
    "from .board import ChessBoard",
    "from .board import ChessBoard, fen_flip, fen_mirror, fen_swap",
)

# 从 common import 中删除 fen_flip, fen_mirror
content = re.sub(r"    fen_flip,\n", "", content)
content = re.sub(r"    fen_mirror,\n", "", content)

init_path.write_text(content, encoding="utf-8")
print("3. __init__.py - 导入更新完成")

# ==========================================
# 修改 4: engine.py - 更新导入
# ==========================================
engine_path = Path(__file__).parent / "src" / "cchess" / "engine.py"
content = engine_path.read_text(encoding="utf-8")

# 在 common import 之前添加 board import（fen_mirror）
content = content.replace(
    "from .common import (\n    RED,\n    fen_mirror,",
    "from .board import fen_mirror\nfrom .common import (\n    RED,",
)

engine_path.write_text(content, encoding="utf-8")
print("4. engine.py - 导入更新完成")

# ==========================================
# 修改 5: test_coverage.py - 更新导入
# ==========================================
test_path = Path(__file__).parent / "tests" / "test_coverage.py"
content = test_path.read_text(encoding="utf-8")

content = content.replace(
    "from cchess.common import fen_mirror", "from cchess.board import fen_mirror"
)

test_path.write_text(content, encoding="utf-8")
print("5. test_coverage.py - 导入更新完成")

print("\n所有修改完成！")
