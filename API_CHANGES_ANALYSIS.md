# CChess v1.26.1 到当前 HEAD API 不兼容变化分析报告

## 概述

根据 ReleaseNote.txt 和代码分析，从 v1.26.1 到当前版本进行了重大的 API 重构和性能优化。本文档详细分析所有不兼容的 API 变化及其影响。

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

## 性能优化相关变化

### 5. 内部优化（不影响 API）

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
# 旧常量
NO_COLOR -> SIDE_ANY
```

## 影响范围分析

### 直接影响

1. **测试代码**：需要更新所有使用旧 API 的测试用例
2. **示例代码**：文档中的示例需要更新
3. **依赖项目**：依赖 cchess 库的项目需要适配

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
```

## 测试验证

运行 `test_api_compatibility.py` 可以验证所有 API 变化：

```bash
python test_api_compatibility.py
```

## 已知问题

1. **版本号不匹配**：`__init__.py` 中版本号仍为 1.26.1，但代码已包含 1.27.0 的变更
2. **文档更新**：需要更新所有相关文档
3. **类型提示**：部分新 API 可能需要更完整的类型提示

## 总结

从 v1.26.1 到当前版本的 API 变化主要包括：

1. **方法重命名**：2 个方法
2. **方法移除**：3 个方法 + 1 个类
3. **常量重命名**：1 个常量
4. **命名统一**：1 个属性

这些变化主要是为了：
- 提高 API 一致性
- 简化设计（移除 ChessPlayer 类）
- 为性能优化铺平道路
- 统一命名约定

迁移工作相对简单，主要涉及方法名和常量名的更新。最大的变化是 `ChessPlayer` 类的移除，需要将颜色处理改为使用整数常量。