# 软件开发全局经验指南

> 本文档收集了在软件开发过程中遇到的通用问题和解决方案，适用于所有项目。

---

## 目录

1. [编码与字符处理](#1-编码与字符处理)
2. [调试方法论](#2-调试方法论)
3. [架构设计原则](#3-架构设计原则)
4. [测试策略](#4-测试策略)
5. [代码审查清单](#5-代码审查清单)
6. [Git 最佳实践](#6-git-最佳实践)
7. [性能优化](#7-性能优化)
8. [错误处理](#8-错误处理)

---

## 1. 编码与字符处理

### 1.1 文件编码问题

**症状**：
- 文件读取后内容乱码
- 字符串比较失败但看起来一样
- 同一文件在不同系统上行为不一致

**诊断命令**：

```bash
# 检查文件实际编码
file -i filename.txt

# 查看文件前 100 字节的十六进制
head -c 100 filename.txt | od -An -tx1

# 检测文件编码（需要 chardet）
python -c "import chardet; print(chardet.detect(open('file','rb').read()))"
```

**Python 最佳实践**：

```python
# ✅ 总是显式指定编码
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# ✅ 处理不确定编码的文件
def read_file_auto_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # 尝试常见编码
    for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    
    # 最后尝试 chardet
    import chardet
    detected = chardet.detect(raw)
    return raw.decode(detected['encoding'], errors='replace')

# ✅ 字符串调试：打印 Unicode 码点
def debug_string(s, label='String'):
    print(f'{label}: {repr(s)}')
    print(f'  Code points: {[f"U+{ord(c):04X}" for c in s]}')
    return s
```

### 1.2 常见字符陷阱

| 字符 | 中文/全角 | 英文/半角 | 区别 |
|------|----------|----------|------|
| 逗号 | `，` U+FF0C | `,` U+002C | 编码不同 |
| 空格 | ` ` U+3000 | ` ` U+0020 | 宽度不同 |
| 引号 | `"` U+201C | `"` U+0022 | 方向不同 |
| 数字 | `123` U+FF11-19 | `123` U+0031-39 | 编码不同 |
| 括号 | `（）` U+FF08-09 | `()` U+0028-29 | 宽度不同 |

**检测代码**：

```python
def check_string_composition(s):
    """检查字符串中混用的字符类型"""
    result = {'chinese_punct': [], 'ascii': [], 'fullwidth_digit': []}
    
    for i, c in enumerate(s):
        code = ord(c)
        if 0xFF01 <= code <= 0xFF5E:  # 全角字符
            result['fullwidth'].append((i, c, f'U+{code:04X}'))
        elif 0x3000 <= code <= 0x303F:  # 中文标点
            result['chinese_punct'].append((i, c, f'U+{code:04X}'))
        elif 0x0020 <= code <= 0x007E:  # ASCII
            result['ascii'].append((i, c, f'U+{code:04X}'))
    
    return result
```

---

## 2. 调试方法论

### 2.1 二分法定位

**适用场景**：问题出现在一系列操作的某个环节

```python
# 场景：处理 100 个数据，第 N 个开始出错
for i, item in enumerate(data):
    if i == 50:  # 中间点
        breakpoint()  # 检查状态
    process(item)

# 根据结果缩小范围：
# - 如果 50 之前出错 → 问题在 0-50
# - 如果 50 之后出错 → 问题在 50-100
```

### 2.2 最小复现原则

**步骤**：

1. **剥离无关代码**：删除所有不相关的逻辑
2. **简化输入**：用最小的输入复现问题
3. **隔离环境**：在新环境中测试

**示例**：

```python
# ❌ 复杂场景难以定位
def process_game():
    load_pgn()
    validate_moves()
    analyze_position()
    save_result()
    # 哪里出错了？

# ✅ 最小复现
def test_move_parsing():
    move = parse_move("炮二平五")
    assert move is not None  # 直接定位问题
```

### 2.3 打印调试的艺术

**差的调试**：
```python
print('debug:', x)  # 不知道 x 是什么
print('here')       # 不知道这里是什么
```

**好的调试**：
```python
print(f'[parse_move] Input: {move_str!r}')
print(f'[parse_move] Piece positions: {piece_positions}')
print(f'[parse_move] Returning: {result}')

# 或者使用 logging
import logging
logging.debug('Parsing move: %s', move_str)
logging.debug('Piece positions: %r', piece_positions)
```

**结构化输出**：
```python
import json
state = {
    'board': board.to_fen(),
    'move_player': board.move_player.color,
    'is_checking': board.is_checking(),
}
print(json.dumps(state, indent=2, ensure_ascii=False))
```

---

## 3. 架构设计原则

### 3.1 单一职责原则 (SRP)

**定义**：一个函数/类应该只有一个改变的理由

**反面教材**：
```python
def move_and_check_and_switch(self, from_pos, to_pos):
    """做太多事的函数"""
    # 1. 移动棋子
    self._move_piece(from_pos, to_pos)
    
    # 2. 切换走子方
    self._move_side = self._move_side.next()
    
    # 3. 检查将军
    if self.is_checking():
        print('将军!')
    
    # 4. 记录日志
    self.log_move(from_pos, to_pos)
    
    # 5. 通知 UI 更新
    self.ui.update()
```

**正确设计**：
```python
# 底层：只移动棋子
def _make_move(self, from_pos, to_pos):
    self._move_piece(from_pos, to_pos)
    return MoveInfo(...)

# 中层：移动 + 切换
def move(self, from_pos, to_pos):
    move_info = self._make_move(from_pos, to_pos)
    self._move_side = self._move_side.next()
    return Move(move_info)

# 高层：完整流程
def play_move(self, from_pos, to_pos):
    move = self.move(from_pos, to_pos)
    if move.is_checking:
        self.notify_check()
    self.log_move(move)
    self.ui.update()
    return move
```

### 3.2 状态管理原则

**核心规则**：
1. **状态变更必须显式**：不要隐式修改状态
2. **状态变更必须可预测**：同样的输入产生同样的状态变化
3. **状态变更必须可回滚**：支持 undo/redo

**反面教材**：
```python
# ❌ 隐式状态变更
def process(self, data):
    # 偷偷修改了状态，调用者不知道
    self._internal_state = compute(data)
    return result
```

**正确设计**：
```python
# ✅ 显式状态变更
def process(self, data):
    result = compute(data)
    # 状态变更在函数名中体现
    self.update_state(result)
    return result

# ✅ 返回新状态
def with_updated_state(self, data):
    new_state = compute(data)
    return self._replace(state=new_state)
```

### 3.3 依赖倒置原则

**定义**：高层模块不应该依赖低层模块，两者都应该依赖抽象

**示例**：
```python
# ❌ 直接依赖具体实现
class Game:
    def __init__(self):
        self.engine = EleeyeEngine()  # 硬编码依赖

# ✅ 依赖抽象
class Game:
    def __init__(self, engine: ChessEngine):
        self.engine = engine  # 依赖抽象接口

# 使用时注入具体实现
engine = EleeyeEngine()  # 或 PikafishEngine()
game = Game(engine)
```

---

## 4. 测试策略

### 4.1 测试金字塔

```
        /\
       /  \      E2E 测试 (10%)
      /----\    慢，不稳定
     /      \
    /--------\  集成测试 (20%)
   /          \  中等速度
  /------------\
 /              \ 单元测试 (70%)
/________________\ 快，稳定
```

### 4.2 单元测试最佳实践

**好的单元测试**：

```python
def test_move_captures_piece():
    # Arrange - 准备
    board = ChessBoard("rnbakabnr/9/9/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w")
    
    # Act - 执行
    move = board.move((0, 0), (0, 9))
    
    # Assert - 断言
    assert move is not None
    assert move.captured == 'r'
    assert board.get_fench((0, 9)) == 'R'
```

**避免的陷阱**：

```python
# ❌ 测试内部实现细节
def test_make_move_switches_turn():
    board.make_move(from, to)
    assert board.move_player == BLACK  # 测试了不该测试的

# ✅ 测试外部行为
def test_move_switches_turn():
    board.move(from, to)
    assert board.move_player == BLACK  # 测试公共 API
```

### 4.3 测试数据管理

```python
# ✅ 使用 Fixture
@pytest.fixture
def initial_board():
    return ChessBoard(FULL_INIT_FEN)

def test_opening_move(initial_board):
    move = initial_board.move((1, 2), (1, 4))
    assert move is not None

# ✅ 参数化测试
@pytest.mark.parametrize('fen,expected', [
    ("4k4/9/9/9/9/9/9/9/9/4K4 w", False),
    ("4k4/9/9/9/9/9/9/9/9/4K1C1 w", True),
])
def test_is_checking(fen, expected):
    board = ChessBoard(fen)
    assert board.is_checking() == expected
```

---

## 5. 代码审查清单

### 5.1 代码质量

- [ ] 函数是否超过 50 行？（考虑拆分）
- [ ] 嵌套是否超过 4 层？（考虑提前返回）
- [ ] 变量名是否有意义？（避免 `a`, `b`, `tmp`）
- [ ] 是否有魔法数字？（提取为常量）
- [ ] 是否有重复代码？（DRY 原则）

### 5.2 错误处理

- [ ] 是否处理了所有异常情况？
- [ ] 错误信息是否清晰有用？
- [ ] 是否记录了足够的调试信息？
- [ ] 是否有资源泄漏风险？（文件、连接等）

### 5.3 性能考虑

- [ ] 是否有不必要的循环嵌套？
- [ ] 是否有重复计算？（考虑缓存）
- [ ] 是否加载了不必要的数据？
- [ ] 是否有内存泄漏风险？

### 5.4 安全性

- [ ] 是否验证了用户输入？
- [ ] 是否有 SQL 注入风险？
- [ ] 是否有路径遍历风险？
- [ ] 是否泄露了敏感信息？

---

## 6. Git 最佳实践

### 6.1 提交信息规范

**格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（不改变行为）
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**：
```
fix(board): correct move side switching in board.move()

- board.make_move() no longer switches move side (low-level function)
- board.move() now switches move side after make_move()
- is_checked_move() manually switches to check for checks
- Fixed test expectations in test_board_make_unmake.py

Fixes: #123
All 303 tests pass.
```

### 6.2 分支策略

```
main (生产)
  │
  ├── develop (开发)
  │     │
  │     ├── feature/login
  │     ├── feature/search
  │     └── fix/issue-123
  │
  └── release/v1.0 (发布准备)
```

### 6.3 常用命令

```bash
# 查看未提交的变化
git status
git diff

# 查看提交历史
git log --oneline -10
git log --graph --oneline --all

# 修改最后一次提交
git commit --amend -m "新提交信息"

# 合并多个提交
git rebase -i HEAD~3

# 查找引入问题的提交
git bisect start
git bisect bad    # 当前有问题
git bisect good v1.0  # 某个好的版本
# Git 会自动二分查找
```

---

## 7. 性能优化

### 7.1 性能分析

```python
# 使用 cProfile
import cProfile
cProfile.run('my_function()', 'output.prof')

# 使用 snakeviz 查看结果
# pip install snakeviz
# snakeviz output.prof

# 简单的时间测量
import time
start = time.time()
my_function()
end = time.time()
print(f'Took {end - start:.3f} seconds')
```

### 7.2 常见优化技巧

**缓存**：
```python
# ✅ 使用 functools.lru_cache
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_computation(x, y):
    return compute(x, y)

# ✅ 手动缓存
class CachedResult:
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        if key not in self._cache:
            self._cache[key] = self.compute(key)
        return self._cache[key]
```

**批量操作**：
```python
# ❌ 逐个处理
for item in items:
    process(item)

# ✅ 批量处理
batch_process(items)  # 内部可能使用向量化
```

**延迟计算**：
```python
class LazyProperty:
    def __init__(self, func):
        self.func = func
    
    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value

class Data:
    @LazyProperty
    def expensive_data(self):
        return load_large_file()  # 只在第一次访问时加载
```

---

## 8. 错误处理

### 8.1 异常处理原则

**不要**：
```python
# ❌ 捕获所有异常
try:
    process()
except Exception:
    pass  # 静默失败

# ❌ 模糊的错误信息
except Exception as e:
    print(f'Error: {e}')
```

**要**：
```python
# ✅ 捕获特定异常
try:
    process()
except FileNotFoundError as e:
    logger.error(f'File not found: {e.filename}')
    raise CChessError(f'File not found: {e.filename}')

# ✅ 提供有用的上下文
except InvalidMoveError as e:
    logger.error(f'Invalid move {move} at position {board.to_fen()}')
    raise CChessError(f'Invalid move {move}: {e}') from e
```

### 8.2 自定义异常

```python
class CChessError(Exception):
    """基础异常类"""
    pass

class InvalidMoveError(CChessError):
    """非法移动"""
    def __init__(self, move, reason):
        super().__init__(f'Invalid move {move}: {reason}')
        self.move = move
        self.reason = reason

class InvalidFenError(CChessError):
    """非法 FEN 字符串"""
    def __init__(self, fen, position=None):
        super().__init__(f'Invalid FEN: {fen}')
        self.fen = fen
        self.position = position
```

### 8.3 防御性编程

```python
# ✅ 验证输入
def move(self, pos_from, pos_to):
    if not self._is_valid_coordinate(pos_from):
        raise ValueError(f'Invalid coordinate: {pos_from}')
    if not self._is_valid_coordinate(pos_to):
        raise ValueError(f'Invalid coordinate: {pos_to}')
    
    # 继续处理...

# ✅ 使用断言
def process(self, data):
    assert data is not None, 'data cannot be None'
    assert len(data) > 0, 'data cannot be empty'
    
    # 继续处理...

# ✅ 返回可选值
def get_piece(self, pos):
    if not self._is_valid_coordinate(pos):
        return None
    return self._board[pos[1]][pos[0]]
```

---

## 附录：调试工具箱

### 命令行调试

```bash
# 查看文件内容
head -n 20 file.txt      # 前 20 行
tail -n 20 file.txt      # 后 20 行
sed -n '50,60p' file.txt # 第 50-60 行

# 搜索内容
grep "pattern" file.txt         # 搜索
grep -n "pattern" file.txt      # 带行号
grep -r "pattern" ./src/        # 递归搜索
grep -l "pattern" *.py          # 只显示文件名

# 统计
wc -l file.txt       # 行数
sort | uniq -c       # 计数
sort | uniq -d       # 查找重复
```

### Python 调试工具

```python
# breakpoint() - Python 3.7+
def debug_function():
    breakpoint()  # 等同于 import pdb; pdb.set_trace()

# pprint - 漂亮打印
from pprint import pprint
pprint(complex_data_structure)

# traceback - 打印堆栈
import traceback
try:
    risky_operation()
except Exception:
    traceback.print_exc()

# logging - 日志
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug('Debug info')
logging.info('General info')
logging.warning('Warning')
logging.error('Error')
logging.critical('Critical error')
```

---

## 持续更新

本文档会随着新问题的发现而持续更新。每次遇到新的通用性问题，都应该：

1. 记录问题现象
2. 分析根本原因
3. 总结解决方案
4. 更新到本文档相应章节

**最后更新**: 2024-01-XX
**维护者**: 开发团队
