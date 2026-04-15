# cchess 项目重新扫描报告

**扫描日期：** 2026-04-15  
**项目版本：** 1.26.1

---

## 📊 项目概况

### 代码统计
| 文件 | 行数 | 备注 |
|------|------|------|
| board.py | 737 | 棋盘核心逻辑 |
| engine.py | 737 | 引擎通信 |
| zhash_data.py | 3,735 | Zobrist 哈希数据 |
| io_xqf.py | 710 | XQF 格式读写 |
| move.py | 669 | 走子逻辑 |
| piece.py | 391 | 棋子规则 |
| common.py | 360 | 通用工具函数 |
| game.py | 355 | 棋局管理 |
| read_cbr.py | 359 | CBR 格式读取 |
| io_pgn.py | 388 | PGN 格式处理 |
| 其他 | ~600 | 辅助模块 |
| **总计** | **~9,000** | |

### 已完成优化 ✅
1. **pyproject.toml 修复** - package-data 包名已更正为 `cchess`
2. **CHANGELOG.md 添加** - 已创建标准格式变更日志
3. **__version__ 添加** - `__init__.py` 中已添加版本号
4. **constants.py 分离** - 常量已提取到独立文件
5. **全角标点修复** - 已清理所有中文标点符号

---

## 🐛 发现的 Bug

### 严重：King.create_moves() 空指针问题

**位置：** `src/cchess/piece.py:143`

**问题描述：**
```python
def create_moves(self):
    poss = [...]
    k2 = self.board.get_king(opposite_color(self.color))
    if k2 is not None:
        poss.append((k2.x, k2.y))  # ✅ 正确

    curr_pos = (self.x, self.y)
    moves = [(curr_pos, to_pos) for to_pos in poss]
    return filter(self.board.is_valid_move_t, moves)
```

但在 `board.py:452` 调用时：
```python
for from_pos, to_pos in piece.create_moves():
    # 当 k2 为 None 时，poss 包含未检查的坐标
```

**测试失败：**
```
tests/test_board_move.py::TestBoard::test_kk_move - AttributeError: 'NoneType' object has no attribute 'x'
```

**修复建议：**
```python
# piece.py:135-148
def create_moves(self):
    """生成将/帅所有可能的合法走子。"""
    poss = [
        (self.x + 1, self.y),
        (self.x - 1, self.y),
        (self.x, self.y + 1),
        (self.x, self.y - 1),
    ]

    # 只有当对方将/帅存在时，才添加"对脸笑"走法
    k2 = self.board.get_king(opposite_color(self.color))
    if k2 is not None:
        # 检查是否在同一纵线上且中间无棋子
        if k2.x == self.x:
            poss.append((k2.x, k2.y))

    curr_pos = (self.x, self.y)
    # 过滤掉 None 值（理论上不应该有，但防御性编程）
    valid_poss = [p for p in poss if p is not None]
    moves = [(curr_pos, to_pos) for to_pos in valid_poss]
    return filter(self.board.is_valid_move_t, moves)
```

---

## 🔧 建议优化项

### 高优先级 🔴

#### 1. 修复 King.create_moves() Bug
- **影响：** 测试失败，可能导致对局中异常
- **工作量：** 30 分钟
- **文件：** `src/cchess/piece.py`

#### 2. 添加缺失的 `is_king_killed()` 方法
- **问题：** 测试调用 `board.is_king_killed()` 但未定义
- **建议实现：**
```python
# board.py
def is_king_killed(self):
    """检查将/帅是否被吃掉（用于测试）"""
    return self.get_king(RED) is None or self.get_king(BLACK) is None
```

#### 3. 完善类型注解
- **现状：** 部分函数缺少类型提示
- **建议：** 对公共 API 添加完整类型注解
- **工具：** 使用 `mypy --strict src/cchess/` 检查

#### 4. 添加测试覆盖率配置
- **建议创建：** `.coveragerc` 或 `pyproject.toml` 配置
```toml
[tool.coverage.run]
source = ["src/cchess"]
branch = true
omit = ["tests/*", "*/zhash_data.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
]
```

### 中优先级 🟡

#### 5. board.py 模块化拆分
**现状：** 737 行，包含过多职责

**建议拆分为：**
```
src/cchess/
├── board/
│   ├── __init__.py      # 导出 ChessBoard
│   ├── core.py          # 基础棋盘操作 (from_fen, to_fen, copy)
│   ├── move.py          # 走子逻辑 (move, move_iccs, create_moves)
│   ├── attack.py        # 攻击检测 (is_checking, is_checkmate)
│   └── display.py       # 显示逻辑 (text_view, print_board)
```

#### 6. engine.py 命令常量提取
**现状：** UCI/UCCI 命令硬编码在方法中

**建议：**
```python
# src/cchess/engine_constants.py
class UCICommands:
    POSITION = "position"
    GO = "go"
    STOP = "stop"
    QUIT = "quit"
    # ...

class UCCICommands:
    POSITION = "position"
    GO = "go"
    # ...
```

#### 7. 添加日志配置
**现状：** `engine.py` 使用 `logger` 但未配置

**建议：**
```python
# src/cchess/logging_config.py
import logging

def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger
```

#### 8. 改进异常处理
**现状：** `exception.py` 只有 2 个简单异常类

**建议：**
```python
class CChessException(Exception):
    """基类异常"""
    pass

class InvalidMoveError(CChessException):
    """非法走子"""
    pass

class InvalidFENError(CChessException):
    """非法 FEN 串"""
    pass

class EngineTimeoutError(CChessException):
    """引擎超时"""
    pass

class FileFormatError(CChessException):
    """文件格式错误"""
    pass
```

### 低优先级 🟢

#### 9. 添加性能基准测试
```python
# tests/benchmarks/test_performance.py
import pytest

def test_create_all_moves(benchmark):
    board = ChessBoard(FULL_INIT_FEN)
    result = benchmark(lambda: list(board.create_moves()))
    assert len(result) == 44
```

#### 10. 添加 pre-commit 钩子
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

#### 11. README.md 改进
**建议添加：**
- 安装说明 (`pip install cchess`)
- 更多使用示例
- API 文档链接
- 贡献指南

#### 12. 添加 CI/CD 配置
**建议创建：** `.github/workflows/tests.yml`
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .[test]
      - run: pytest tests/
```

---

## 📈 代码质量指标

### Pylint 配置分析
当前 `.pylintrc` 禁用了大量警告：
- `R0401` (cyclic-import) - 需要包重构
- `R0801` (duplicate-code) - 需要提取公共逻辑
- `C0302` (too-many-lines) - 需要拆分大文件
- `R09xx` 系列 - 类/方法过于复杂

**建议：** 逐步修复这些问题，而不是禁用

### 测试覆盖率
**当前状态：** 14 个测试，1 个失败  
**建议目标：** 
- 核心模块（board, piece, move）：>90%
- 文件读写（io_*）：>80%
- 引擎通信（engine）：>70%

---

## 🎯 实施路线图

### 第一阶段（1-2 天）
1. ✅ 修复 King.create_moves() Bug
2. ✅ 添加 is_king_killed() 方法
3. ✅ 确保所有测试通过

### 第二阶段（1 周）
1. 添加完整类型注解
2. 配置测试覆盖率
3. 添加 pre-commit 钩子

### 第三阶段（2-4 周）
1. board.py 模块化拆分
2. 异常层次结构完善
3. 日志系统配置

### 第四阶段（持续）
1. CI/CD 集成
2. 性能基准测试
3. 文档完善

---

## 📝 总结

项目整体结构良好，核心功能完整。主要问题：
1. **1 个严重 Bug** 需要立即修复
2. **代码组织** 可以进一步模块化
3. **工程化** 方面（类型注解、测试覆盖率、CI/CD）有提升空间

建议优先修复 Bug，然后逐步改进代码质量和工程化水平。
