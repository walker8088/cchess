# CChess v1.26.1 到 v2.26.1 升级指南

## 升级概述

从 v1.26.1 升级到 v2.26.1（开发中）涉及多个不兼容的 API 变化。本文档提供详细的升级步骤和建议。

## 升级步骤

### 1. 检查当前代码的 API 使用

首先，使用以下命令检查你的代码中是否使用了已弃用或已移除的 API：

```bash
# 搜索已移除的方法
grep -r "get_fenchs\|get_pieces\|Move.from_text\|unmake_move\|move_any" your_project/

# 搜索已移除的类
grep -r "ChessPlayer" your_project/

# 搜索已重命名的常量
grep -r "NO_COLOR" your_project/

# 搜索已重命名的将军检测方法
grep -r "is_checking_move\|is_checked_move" your_project/

# 搜索 CBL 库字典键名（已重命名为 books）
grep -rn "books" your_project/  # 配合 read_from_lib 调用排查
```

### 2. 更新依赖版本

在 `requirements.txt` 或 `pyproject.toml` 中更新 cchess 版本：

```txt
# requirements.txt
cchess>=1.27.0

# 或使用 git 引用
git+https://github.com/walker8088/cchess.git@main
```

### 3. 逐项更新 API 调用

#### 3.1 方法重命名

**更新前：**
```python
from cchess import ChessBoard

board = ChessBoard()
positions = board.get_fenchs('K')
pieces = board.get_pieces(SIDE_RED)
```

**更新后：**
```python
from cchess import ChessBoard, SIDE_RED

board = ChessBoard()
positions = board.get_fench_positions('K')
pieces = board.get_all_fench_positions(SIDE_RED)
```

#### 3.2 Move.from_text() 移除

**更新前：**
```python
from cchess import ChessBoard, Move

board = ChessBoard()
move = Move.from_text("炮二平五", board)
```

**更新后：**
```python
from cchess import ChessBoard

board = ChessBoard()
move = board.move_text("炮二平五")
```

#### 3.3 ChessPlayer 类移除

**更新前（假设的旧 API）：**
```python
from cchess import ChessPlayer

player = ChessPlayer.RED
if board.move_player == player:
    # ...
```

**更新后：**
```python
from cchess import SIDE_RED

if board.move_side == SIDE_RED:
    # ...
```

#### 3.4 常量更新

**更新前：**
```python
from cchess import NO_COLOR

color = NO_COLOR
```

**更新后：**
```python
from cchess import SIDE_ANY

color = SIDE_ANY
```

#### 3.5 将军检测方法重命名

为消除 `is_checking_move` / `is_checked_move` 的歧义，重命名如下：

**更新前：**
```python
# 检查走子后是否将军对方
if board.is_checking_move(pos_from, pos_to):
    ...

# 检查走子后己方是否被将军（非法走子会抛 CChessError）
if board.is_checked_move(pos_from, pos_to):
    ...
```

**更新后：**
```python
# 检查走子后是否将军对方
if board.gives_check(pos_from, pos_to):
    ...

# 检查走子后己方是否被将军（非法走子会抛 CChessError）
if board.leaves_king_in_check(pos_from, pos_to):
    ...
```

注意：无参的 `board.is_checking()`（判断当前局面是否构成将军）名称不变。

#### 3.6 CBL 库字典键名重命名

`Book.read_from_lib()` 返回的字典中，包含棋谱列表的键从 `'games'` 改为 `'books'`，与棋谱类名保持一致。

**更新前：**
```python
lib = Book.read_from_lib("WildHouse.cbl")
for book in lib['games']:
    book.print_init_board()
```

**更新后：**
```python
lib = Book.read_from_lib("WildHouse.cbl")
for book in lib['books']:
    book.print_init_board()
```

字典的 `'name'` 键保持不变。

### 4. 处理移除的方法

#### 4.1 unmake_move() 替代方案

如果使用了 `unmake_move()`，需要改为保存棋盘快照：

**更新前：**
```python
board.move((0, 0), (1, 1))
board.unmake_move()
```

**更新后：**
```python
# 保存快照
snapshot = board.copy()

# 执行走子
board.move((0, 0), (1, 1))

# 恢复快照
board = snapshot
```

#### 4.2 move_any() 替代方案

**更新前：**
```python
board.move_any((0, 0), (1, 1))
```

**更新后：**
```python
board.move((0, 0), (1, 1))
```

### 5. 更新测试代码

如果你的项目包含测试代码，需要相应更新：

```python
# 更新前
def test_old_api():
    board = ChessBoard()
    positions = board.get_fenchs('K')
    assert len(positions) == 1

# 更新后
def test_new_api():
    board = ChessBoard()
    positions = board.get_fench_positions('K')
    assert len(positions) == 1
```

## 自动化升级脚本

对于大型项目，可以创建自动化升级脚本：

```python
#!/usr/bin/env python3
"""
cchess API 自动升级脚本
"""

import re
import os

def upgrade_file(filepath):
    """升级单个文件中的 API 调用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换规则
    replacements = [
        (r'\.get_fenchs\(', '.get_fench_positions('),
        (r'\.get_pieces\(', '.get_all_fench_positions('),
        (r'Move\.from_text\(', '# Move.from_text() 已移除，请使用 board.move_text()'),
        (r'NO_COLOR', 'SIDE_ANY'),
        (r'ChessPlayer\.SIDE_RED', 'SIDE_RED'),
        (r'ChessPlayer\.SIDE_BLACK', 'SIDE_BLACK'),
        (r'\.is_checking_move\(', '.gives_check('),
        (r'\.is_checked_move\(', '.leaves_king_in_check('),
        (r"\[(['\"])games\1\]", r'[\1books\1]'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已更新: {filepath}")

def main():
    """主函数"""
    project_dir = input("请输入项目目录路径: ").strip()
    
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                upgrade_file(filepath)
    
    print("升级完成！")

if __name__ == '__main__':
    main()
```

## 兼容性层（临时方案）

如果无法立即升级所有代码，可以创建兼容性层：

```python
# compatibility.py
from cchess import ChessBoard, Move, SIDE_RED, SIDE_BLACK, SIDE_ANY

class BackwardCompatibleBoard(ChessBoard):
    """向后兼容的棋盘类"""
    
    def get_fenchs(self, fench):
        """兼容旧 API: get_fenchs -> get_fench_positions"""
        import warnings
        warnings.warn(
            "get_fenchs() is deprecated, use get_fench_positions() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_fench_positions(fench)
    
    def get_pieces(self, color=None):
        """兼容旧 API: get_pieces -> get_all_fench_positions"""
        import warnings
        warnings.warn(
            "get_pieces() is deprecated, use get_all_fench_positions() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_all_fench_positions(color)
    
    def move_any(self, pos_from, pos_to):
        """兼容旧 API: move_any -> move"""
        import warnings
        warnings.warn(
            "move_any() is deprecated, use move() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.move(pos_from, pos_to)

# 为 Move 类添加兼容方法
def move_from_text(move_str, board):
    """兼容旧 API: Move.from_text -> board.move_text"""
    import warnings
    warnings.warn(
        "Move.from_text() is deprecated, use board.move_text() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return board.move_text(move_str)

# 临时添加到 Move 类
Move.from_text = staticmethod(move_from_text)

# 导出兼容性常量
NO_COLOR = SIDE_ANY

# 创建兼容的 ChessPlayer 类（如果确实需要）
class ChessPlayer:
    SIDE_RED = SIDE_RED
    SIDE_BLACK = SIDE_BLACK
    NO_COLOR = SIDE_ANY
    
    @staticmethod
    def next(color):
        from cchess.common import next_side
        return next_side(color)
```

## 验证升级结果

升级后，运行以下验证：

### 1. 运行 API 兼容性测试

```bash
python test_api_compatibility.py
```

### 2. 运行项目测试

```bash
# 运行你的项目测试
pytest your_project/tests/

# 或运行 cchess 自带的测试
python -m pytest tests/ --ignore=tests/test_engine.py -x -q
```

### 3. 性能验证

验证性能改进：

```python
import time
from cchess import ChessBoard, FULL_INIT_FEN

board = ChessBoard(FULL_INIT_FEN)

# 测试性能
start = time.perf_counter()
for _ in range(10000):
    list(board.get_all_fench_positions())
elapsed = time.perf_counter() - start
print(f'get_all_fench_positions x10000: {elapsed:.3f}s')

start = time.perf_counter()
for _ in range(1000):
    list(board.create_moves())
elapsed = time.perf_counter() - start
print(f'create_moves x1000: {elapsed:.3f}s')
```

## 常见问题解决

### Q1: 升级后出现 ImportError: cannot import name 'ChessPlayer'

**解决方案：**
- 将 `from cchess import ChessPlayer` 改为 `from cchess import SIDE_RED, SIDE_BLACK, SIDE_ANY`
- 使用整数常量代替 ChessPlayer 实例

### Q2: Move.from_text() 调用失败

**解决方案：**
- 将 `Move.from_text(text, board)` 改为 `board.move_text(text)`
- 确保 `board` 是有效的 ChessBoard 实例

### Q3: get_fenchs() 或 get_pieces() 调用失败

**解决方案：**
- 将 `board.get_fenchs(fench)` 改为 `board.get_fench_positions(fench)`
- 将 `board.get_pieces(color)` 改为 `board.get_all_fench_positions(color)`

### Q4: 需要撤销走子功能

**解决方案：**
- 使用 `board.copy()` 保存快照
- 实现自定义的撤销栈：
  ```python
  class BoardWithUndo:
      def __init__(self, board):
          self.board = board
          self.history = []
      
      def move(self, pos_from, pos_to):
          # 保存快照
          self.history.append(self.board.copy())
          # 执行走子
          return self.board.move(pos_from, pos_to)
      
      def undo(self):
          if self.history:
              self.board = self.history.pop()
              return True
          return False
  ```

## 性能改进说明

升级后的版本包含多项性能优化：

1. **3.5-5.1倍性能提升**：关键操作（走法生成、棋子遍历等）
2. **内存占用减少40%**：Piece 类使用 `__slots__`
3. **马走法优化**：性能提升约35%
4. **规范局面处理**：减少红黑方分支代码

## 新增功能：AsyncEngine 异步引擎

本版本新增了异步引擎接口 `AsyncEngine`（`engine_async.py`），
适用于 Web 服务、批量分析等需要非阻塞调用的场景。

### 启用方式

```python
from cchess.engine_async import AsyncEngine, play_move, analyse_position
import asyncio

async def main():
    async with AsyncEngine("Engine/eleeye/ELEEYE.EXE") as engine:
        board = ChessBoard(FULL_INIT_FEN)
        result = await engine.play(board, depth=10, timeout=30)
        print(result["move"])

asyncio.run(main())
```

### 主要特性

- 支持 UCCI / UCI / auto 三种协议
- `play()` / `analyse()` 带 `timeout` 参数（默认 60s）防止挂起
- 上下文管理器（`async with`）保证进程自动清理
- `play_move()` / `analyse_position()` 便捷函数

### 依赖项

`pytest-asyncio >= 0.23`（仅测试时需要）
- `pyproject.toml` 中已配 `asyncio_mode = "auto"`
- 需启动真实引擎的测试统一标记为 `@pytest.mark.slow`

## 联系支持

如果在升级过程中遇到问题：

1. 查看 [API_CHANGES_ANALYSIS.md](API_CHANGES_ANALYSIS.md) 了解详细变化
2. 检查测试用例：`tests/test_coverage.py`
3. 提交 Issue：项目 GitHub 仓库

## 总结

升级到新版本的主要工作包括：
1. 更新方法名（4个重命名：`get_fenchs`/`get_pieces`/`is_checking_move`/`is_checked_move`）
2. 更新 CBL 库字典键名（`'games'` → `'books'`）
3. 更新 API 调用方式（Move.from_text -> board.move_text）
4. 更新颜色处理（ChessPlayer -> 整数常量）
5. 更新常量名（NO_COLOR -> SIDE_ANY）
6. **可选**：采用新的 `AsyncEngine` 异步接口（需用 `async/await`）

虽然涉及不兼容变化，但迁移工作相对直接，且能获得显著的性能改进。

## 验证清单

升级后逐项验证以下内容：

- [ ] `from cchess import SIDE_RED, SIDE_BLACK, SIDE_ANY` 导入成功
- [ ] `board.get_fench_positions()` / `board.get_all_fench_positions()` 调用成功
- [ ] `board.move_text("炮二平五")` 返回 `Move` 对象
- [ ] `board.move_side()` 可正常读取/设置
- [ ] `board.gives_check()` / `board.leaves_king_in_check()` 调用成功
- [ ] `lib = Book.read_from_lib(...)` 后 `len(lib['books'])` 正常
- [ ] `uvx ruff check ./src` 无错误
- [ ] `python -m pytest tests/ -m "not slow" -x -q` 全部快速测试通过
- [ ] （可选）`python -m pytest tests/test_engine_async.py -m "slow" -v` 引擎集成测试通过

## 相关文档

- [API_CHANGES_ANALYSIS.md](API_CHANGES_ANALYSIS.md) - 详细的 API 变化分析
- [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md) - 架构分析
- [ReleaseNote.txt](ReleaseNote.txt) - 版本变更记录
- [AGENTS.md](AGENTS.md) - 项目开发规则
- [CODE_REVIEW.md](CODE_REVIEW.md) - 代码审查清单
