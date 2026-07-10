# CChess v1.26.1 到 v2.26.1 不兼容变化

> **版本说明**：本项目使用 `大版本号.年.顺序` 三段式语义化版本号
> （如 `2.26.1` = 大版本 2 / 2026 年 / 当年第 1 发）。
> 不兼容 API 变化会触发 MAJOR 递増（1 → 2），其他变化只递增 SEQUENCE。
> 详见 [AGENTS.md §版本号命名规则](AGENTS.md#版本号命名规则)。

## 概述

根据 ReleaseNote.txt 和代码分析，从 v1.26.1 到 v2.26.1（开发中）进行了重大的 API 重构和性能优化。本文档详细分析所有不兼容的 API 变化及其影响。

## 主要 API 变化

### 1. 方法重命名

#### 1.1 `get_fenchs()` -> `get_fench_positions()`
- **旧 API**: `board.get_fenchs(fench)`
- **新 API**: `board.get_fench_positions(fench)`
- **影响**: 所有使用 `get_fenchs()` 的代码需要更新
- **示例**:
  ```python
  # 旧代码
  positions = board.get_fenchs('K')
  
  # 新代码
  positions = board.get_fench_positions('K')
  ```

#### 1.2 `get_pieces()` -> `get_all_pieces()`
- **旧 API**: `board.get_pieces(color)`
- **新 API**: `board.get_all_pieces(color)`
- **影响**: 所有使用 `get_pieces()` 的代码需要更新
- **示例**:
  ```python
  # 旧代码
  red_pieces = board.get_pieces(SIDE_RED)
  
  # 新代码
  red_pieces = board.get_all_pieces(SIDE_RED)
  ```

### 2. 方法移除

#### 2.1 `Move.from_text()` 移除
- **旧 API**: `Move.from_text(move_str, board)`
- **替代方案**: `board.move_text(move_str)`
- **影响**: 直接调用 `Move.from_text()` 的代码需要重构
- **示例**:
  ```python
  # 旧代码
  move = Move.from_text("炮二平五", board)
  
  # 新代码
  move = board.move_text("炮二平五")
  ```

#### 2.2 `unmake_move()` 移除
- **旧 API**: `board.unmake_move()`
- **影响**: 撤销走子功能被移除，需要其他方式实现
- **说明**: 这个功能被简化，可能通过保存棋盘快照替代

#### 2.3 `move_any()` 移除
- **旧 API**: `board.move_any(pos_from, pos_to)`
- **替代方案**: 使用 `board.move()` 或 `board.move_iccs()`
- **影响**: 这个便捷方法被移除

#### 2.4 `ChessPlayer` 类移除
- **旧 API**: 使用 `ChessPlayer` 类表示颜色
- **新方案**: 使用整数常量 `SIDE_RED=1`, `SIDE_BLACK=2`, `SIDE_ANY=0`
- **影响**: 所有使用 `ChessPlayer` 的代码需要更新
- **示例**:
  ```python
  # 旧代码（假设）
  player = ChessPlayer.RED
  board.set_move_side(player)
  
  # 新代码
  from cchess import SIDE_RED
  board.set_move_side(SIDE_RED)
  ```

### 3. 常量重命名

#### 3.1 `NO_COLOR` -> `SIDE_ANY`
- **旧常量**: `NO_COLOR`
- **新常量**: `SIDE_ANY`
- **影响**: 所有使用 `NO_COLOR` 的代码需要更新
- **示例**:
  ```python
  # 旧代码
  from cchess import NO_COLOR
  
  # 新代码
  from cchess import SIDE_ANY
  ```

#### 3.2 `RED` / `BLACK` -> `SIDE_RED` / `SIDE_BLACK`
- **旧常量**: `RED`, `BLACK`
- **新常量**: `SIDE_RED`, `SIDE_BLACK`
- **影响**: 所有直接使用 `RED` / `BLACK` 常量的代码需要更新
- **示例**:
  ```python
  # 旧代码
  from cchess import RED, BLACK
  if board.move_side == RED:
      ...
  
  # 新代码
  from cchess import SIDE_RED, SIDE_BLACK
  if board.move_side == SIDE_RED:
      ...
  ```

### 4. 属性命名统一

#### 4.1 `move_player` -> `move_side`
- **旧命名**: `move_player`（可能存在于某些地方）
- **新命名**: `move_side`
- **影响**: 更统一的命名约定
- **当前 API**:
  ```python
  # 获取当前走子方
  side = board.move_side
  
  # 设置走子方
  board.set_move_side(SIDE_RED)
  ```

### 5. 将军检测方法重命名

#### 5.1 `is_checking_move()` -> `gives_check()`
- **旧 API**: `board.is_checking_move(pos_from, pos_to)`
- **新 API**: `board.gives_check(pos_from, pos_to)`
- **动机**: 原命名 `is_checking_move` 与无参 `is_checking()` 极易混淆（一个动名词后缀与现在时后缀），且语义"是否将军"不够直观
- **影响**: 所有使用 `is_checking_move()` 的代码需更新
- **语义对比**:
  - `gives_check(from, to)` — "走子后**走子方**对**对方**形成将军"
  - `leaves_king_in_check(from, to)` — "走子后**走子方**己方王被对方将军"
  - `is_checking()` (无参) — "**当前局面**走子方是否将军对方"（名称不变）

- **示例**:
  ```python
  # 旧代码
  if board.is_checking_move(pos_from, pos_to):
      ...

  # 新代码
  if board.gives_check(pos_from, pos_to):
      ...
  ```

#### 5.2 `is_checked_move()` -> `leaves_king_in_check()`
- **旧 API**: `board.is_checked_move(pos_from, pos_to)`
- **新 API**: `board.leaves_king_in_check(pos_from, pos_to)`
- **动机**: 原命名 `is_checked_move` 读起来像"该走子是否被将军过"，歧义严重
- **影响**: 所有使用 `is_checked_move()` 的代码需更新；非法走子会抛 `CChessError`（行为不变）
- **示例**:
  ```python
  # 旧代码
  if board.is_checked_move(pos_from, pos_to):
      ...  # 走子后己方被将军

  # 新代码
  if board.leaves_king_in_check(pos_from, pos_to):
      ...  # 走子后己方王被攻击（送将走子）
  ```

### 6. CBL 库字典键名重命名

#### 6.1 `lib['games']` -> `lib['books']`
- **旧 API**: `Book.read_from_lib(file)` 返回字典，键 `'games'` 包含棋谱列表
- **新 API**: 键 `'books'` 包含棋谱列表（与 `Book` 类名一致）
- **动机**: 延续 `Game → Book` 重命名，统一术语
- **影响**: 所有读取 CBL 库字典键的代码需更新；`'name'` 键保持不变
- **示例**:
  ```python
  lib = Book.read_from_lib("WildHouse.cbl")

  # 旧代码
  for book in lib['games']:  # KeyError: 'games'
      ...

  # 新代码
  for book in lib['books']:
      ...
  ```

## 性能优化相关变化

### 7. 内部优化（不影响 API）

以下优化不直接影响公共 API，但可能影响性能特征：

1. **马走法生成优化**：性能提升约35%
2. **车/炮走法优化**：直接访问棋盘数组减少方法调用
3. **内存优化**：`Piece` 类添加 `__slots__`，内存占用减少40%
4. **规范局面应用**：统一红黑方走法处理，减少颜色分支

## 迁移指南

### 步骤 1: 更新导入语句

```python
# 旧导入
from cchess import ChessPlayer, NO_COLOR

# 新导入
from cchess import SIDE_RED, SIDE_BLACK, SIDE_ANY
```

### 步骤 2: 更新方法调用

```python
# 重命名的方法
board.get_fenchs(fench) -> board.get_fench_positions(fench)
board.get_pieces(color) -> board.get_all_pieces(color)

# 移除的方法
Move.from_text(text, board) -> board.move_text(text)
board.unmake_move() -> 需要重新设计
board.move_any(from_pos, to_pos) -> board.move(from_pos, to_pos)
```

### 步骤 3: 更新颜色处理

```python
# 旧方式（假设）
player = ChessPlayer.RED
if board.move_player == player:
    # ...

# 新方式
from cchess import SIDE_RED
if board.move_side == SIDE_RED:
    # ...
```

### 步骤 4: 更新常量引用

```python
# 旧常量 → 新常量
NO_COLOR -> SIDE_ANY
RED -> SIDE_RED
BLACK -> SIDE_BLACK
```

### 步骤 5: 更新将军检测方法

```python
# 旧 API → 新 API
board.is_checking_move(from, to) -> board.gives_check(from, to)
board.is_checked_move(from, to)  -> board.leaves_king_in_check(from, to)
```

### 步骤 6: 更新 CBL 库字典键名

```python
# 旧代码
for book in lib['games']:
    ...

# 新代码
for book in lib['books']:
    ...
```

## 影响范围分析

### 直接影响

1. **测试代码**：需要更新所有使用旧 API 的测试用例
2. **示例代码**：文档中的示例需要更新
3. **依赖项目**：依赖 cchess 库的项目需要适配
4. **将军检测逻辑**：任何走子合法性判断、搜索引擎代码
5. **CBL 库处理**：批量棋谱导入/导出工具

### 间接影响

1. **性能特征**：优化后的代码性能更好，但可能改变某些边界情况的行为
2. **内存使用**：`Piece` 类内存占用减少，可能影响序列化

## 兼容性层建议

对于需要向后兼容的项目，可以考虑添加兼容性层：

```python
# compatibility.py
from cchess import ChessBoard, Move

class CompatibleChessBoard(ChessBoard):
    """向后兼容的 ChessBoard 类"""
    
    def get_fenchs(self, fench):
        """兼容旧 API"""
        return self.get_fench_positions(fench)
    
    def get_pieces(self, color=None):
        """兼容旧 API"""
        return self.get_all_pieces(color)
    
    def move_any(self, pos_from, pos_to):
        """兼容旧 API"""
        return self.move(pos_from, pos_to)

# 为 Move 类添加兼容性方法
def move_from_text(move_str, board):
    """兼容旧 API"""
    return board.move_text(move_str)

# 临时添加到 Move 类
Move.from_text = staticmethod(move_from_text)

# 将军检测方法的兼容层
class BackwardCompatCheckMixin:
    """ChessBoard 子类：保留旧 is_checking_move / is_checked_move 名字"""
    def is_checking_move(self, pos_from, pos_to):
        import warnings
        warnings.warn("is_checking_move() 已弃用，请使用 gives_check()", DeprecationWarning, stacklevel=2)
        return self.gives_check(pos_from, pos_to)

    def is_checked_move(self, pos_from, pos_to):
        import warnings
        warnings.warn("is_checked_move() 已弃用，请使用 leaves_king_in_check()", DeprecationWarning, stacklevel=2)
        return self.leaves_king_in_check(pos_from, pos_to)
```

## 测试验证

运行 `test_api_compatibility.py` 可以验证所有 API 变化：

```bash
python test_api_compatibility.py
```

## 附录：AsyncEngine 新增功能

AsyncEngine（`engine_async.py`）是本版本新增的异步引擎接口，
不是不兼容变化，但是项目架构的重要补充。

### 公共 API

```python
from cchess.engine_async import AsyncEngine, play_move, analyse_position
```

| 名称 | 类型 | 说明 |
|------|------|------|
| `AsyncEngine` | 类 | 异步引擎封装，支持 ucci/uci/auto 三种协议 |
| `play_move` | 函数 | 便捷函数：一步走棋返回 ICCS 字符串 |
| `analyse_position` | 函数 | 便捷函数：分析局面返回第一条结果 |

### 主要方法

- `async initialize() -> bool` - 启动引擎并握手协议 (5s 超时)
- `async quit()` - 关闭引擎 (2s 优雅等待后 force kill)
- `async play(board, depth, time_limit, timeout=60) -> dict` - 走子
- `async analyse(board, depth, time_limit, multipv, timeout=60) -> list` - 分析
- `async configure(options: dict) -> None` - setoption 设置
- `async __aenter__/__aexit__` - 异步上下文管理器

### 错误处理

引擎不响应时, `play()` / `analyse()` 会：
1. 在 `timeout` 秒后触发 `asyncio.TimeoutError` (内部处理)
2. 调用 `_stop_thinking()` 发送 `quit` (UCCI) 或 `stop` (UCI)
3. 返回空结果 `{"move": None, ...}` 或 `[]`

调用方需自行 try/except:
```python
try:
    result = await engine.play(board, depth=10, timeout=30)
except RuntimeError:
    # 引擎未初始化
    ...
```

## 已知问题

无。

## 总结

从 v1.26.1 到 v2.26.1 的 API 变化主要包括：

1. **方法重命名**：4 个方法
   - `get_fenchs()` → `get_fench_positions()`
   - `get_pieces()` → `get_all_pieces()`
   - `is_checking_move()` → `gives_check()`
   - `is_checked_move()` → `leaves_king_in_check()`
2. **方法移除**：3 个方法 + 1 个类（`Move.from_text`、`unmake_move`、`move_any`、`ChessPlayer`）
3. **常量重命名**：3 个常量（`NO_COLOR` → `SIDE_ANY`、`RED` → `SIDE_RED`、`BLACK` → `SIDE_BLACK`）
4. **字典键重命名**：1 个（`lib['games']` → `lib['books']`）
5. **属性命名统一**：1 个属性（`move_player` → `move_side`）

这些变化主要是为了：
- 提高 API 一致性（棋谱术语统一为 Book）
- 简化设计（移除 ChessPlayer 类）
- 消除命名歧义（将军检测方法重命名）
- 为性能优化铺平道路
- 统一命名约定

迁移工作相对直接，主要涉及方法名、常量名和字典键名的更新。最大的变化是 `ChessPlayer` 类的移除，需要将颜色处理改为使用整数常量。