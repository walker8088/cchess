# CChess AI Agent 指南

## 项目概述

中国象棋（CChess）Python 实现，支持棋谱读写、走法生成、引擎接口等功能。

## 架构文档
详细代码架构分析请参考：[ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md)

## 开发环境

### 依赖安装
```bash
pip install -r requirements.txt
```

### 代码检查
```bash
# Ruff 代码检查
uvx ruff check ./src

# Pylint 检查
python -m pylint src/cchess/*.py --disable=all --enable=duplicate-code,too-many-branches,too-many-locals,too-many-statements
```

### 测试
```bash
# 运行快速测试（CI 默认，排除需要启动引擎的慢速测试）
python -m pytest tests/ --ignore=tests/test_engine.py --ignore=tests/test_engine_extended.py -m "not slow" -x -q

# 运行引擎集成测试（启动 eleeye 等引擎，本地/夜间跑）
python -m pytest tests/test_engine_async.py -m "slow" -v

# 单独运行某类测试
python -m pytest tests/test_board_move.py -xvs
python -m pytest tests/test_coverage.py -x -q
```

> `slow` 标记定义在 `pyproject.toml` 的 `[tool.pytest.ini_options].markers` 中。
> 凡是需调用 `ELEEYE.EXE` / `pikafish.exe` 的测试都应加 `@pytest.mark.slow`。

## 代码优化指南

### 已完成的优化

1. **规范局面重构** - 使用 `normalized()` 方法减少红黑颜色分支
2. **Piece 类优化** - 添加 `__slots__` 减少内存占用 40%
3. **车/炮走法优化** - 直接访问棋盘数组，减少方法调用
4. **代码清理** - 修复所有 ruff 检查错误
5. **性能专项优化** - 关键操作 3.5-5.1 倍性能提升

### 命名约定

- `positions` - 坐标列表（避免使用 `poss`）
- `next_node` - 链表下一个节点（避免 shadow 内置 `next`）
- `engine_out_queue` - 引擎输出队列（拼写正确）
- `SIDE_ANY` - 任意颜色（原 `NO_COLOR`，语义更清晰）

### 性能优化点

1. **缓存 `fench_to_species()`** - 模块级 `_SPECIES_CACHE` 字典
2. **直接数组访问** - 替代方法调用，减少开销
3. **简化颜色判断** - 使用 `isupper()`/`islower()` 替代函数调用
4. **列表推导式** - 替代传统循环，提高性能
5. **滑走棋子方向常量** - `_SLIDING_DIRECTIONS` 避免重复创建
6. **减少元组创建** - 使用局部变量代替中间元组
7. **规范局面应用** - 在 `create_moves()` 中统一处理红黑方

## 架构说明

### 核心模块

- `board.py` - 棋盘类，含走法生成、FEN 解析
- `piece.py` - 棋子类层次结构（King, Advisor, Bishop, Knight, Rook, Cannon, Pawn）
- `move.py` - 走法类，含中文走法解析
- `common.py` - 工具函数和常量
- `engine_async.py` - 异步引擎支持

### 设计模式

1. **规范局面（Normalized Board）** - 将黑方走子转换为红方视角处理
2. **延迟计算** - `Move` 对象的棋盘快照按需生成
3. **工厂模式** - `Piece.create()` 根据棋子类型创建实例
4. **缓存模式** - 模块级缓存减少重复计算

## 测试策略

### 测试覆盖

- 单元测试：`test_board_move.py`, `test_piece.py`
- 覆盖率测试：`test_coverage.py` (300+ 测试)
- 集成测试：`test_io_pgn_txt.py`, `test_read_xqf.py`
- 异步引擎测试：`test_engine_async.py` (14 个测试类，56 个测试)
- 性能测试：基准测试套件

### 异步引擎测试（`tests/test_engine_async.py`）

- `TestAsyncEngineInit` - 构造参数
- `TestAsyncEngineLifecycle` - 启动 / 退出 / 上下文管理
- `TestAsyncEnginePlay` / `TestAsyncEngineAnalyse` - 走子 / 分析
- `TestAsyncEngineGoCommand` / `TestAsyncEngineParseInfo` - 纯逻辑单测
- `TestAsyncEngineBoundaryConditions` - 空棋盘 / 将死 / 深度 0 / 超时
- `TestAsyncEngineErrorRecovery` - 多次 quit / 重连 / 失败初始化
- `TestAsyncEngineConcurrency` - 并发 play / analyse
- `TestAsyncEngineInfoParsing` - info 全字段解析
- `TestAsyncEngineSetOption` - setoption 选项
- `TestAsyncEngineProtocolDetection` - auto / ucci / uci 探测

> 全部 `slow` 测试需启动 eleeye 引擎，约 100 秒；快速测试 18 个 < 0.1s。

### 文档验证

- `verify_readme.py` (项目根) - 15 个测试覆盖 README 代码示例

### 已知问题

- `test_engine.py` - 需要外部引擎文件，CI 环境跳过

## Git 工作流

### 提交规范

```
feat: 新功能
fix: bug 修复
perf: 性能优化
refactor: 重构（不改变行为）
docs: 文档更新
chore: 构建/工具相关
```

### 推送前检查清单

```bash
# 1. 运行 ruff 检查
uvx ruff check ./src

# 2. 运行测试
python -m pytest tests/ --ignore=tests/test_engine.py -x -q

# 3. 确认无临时文件
git status
```

## 性能基准

### 优化后性能指标

```
get_all_pieces() x10000:   0.001s (0.0001ms/次)      # 173倍提升
create_moves() x1000:      0.000s (0.0000ms/次)      # 13150倍提升
Rook at center x1000:      0.00489s (0.0049ms/次)    # 5.12倍提升
Cannon at center x1000:    0.00536s (0.0054ms/次)    # 4.32倍提升
Knight at center x1000:    0.00592s (0.0059ms/次)    # 3.94倍提升
Pawn at center x1000:      0.00528s (0.0053ms/次)    # 3.47倍提升
```

### 性能测试方法

```python
import time
from cchess import ChessBoard, FULL_INIT_FEN

board = ChessBoard(FULL_INIT_FEN)
start = time.perf_counter()
for _ in range(10000):
    list(board.get_all_pieces())
elapsed = time.perf_counter() - start
print(f'get_all_pieces x10000: {elapsed:.3f}s')
```

## 版本号命名规则

本项目使用 **大版本号.年.顺序** 三段式语义化版本号。

### 格式

```
MAJOR.YEAR.SEQUENCE
```

| 段 | 含义 | 说明 |
|---|------|------|
| **MAJOR** | 大版本号 | 与上一大版本有 **不兼容 API 变化** 时从 1 递増 |
| **YEAR** | 发布年份 | 两位数表示（如 `26` = 2026） |
| **SEQUENCE** | 当年顺序 | 该大版本年份内的第 N 个发布，从 `1` 开始 |

### 示例

- `2.26.1` = **第 2 大版本，2026 年第 1 个发布**
  （与 1.x 不兼容，2026 年首发）
- `2.26.2` = 第 2 大版本，2026 年第 2 个发布
- `1.26.2` = 第 1 大版本，2026 年第 2 个发布
- `1.24.6` = 第 1 大版本，2024 年第 6 个发布
- `1.24.4` = 第 1 大版本，2024 年第 4 个发布

### 升号原则

| 场景 | 递增哪一段 | 说明 |
|------|----------|------|
| 删除/重命名类、方法、常量等破坏性 API | **MAJOR** | 同步递增到下一大版本号（1 → 2） |
| 跨自然年发布 | **YEAR** | 示例：1.24.6 → 1.26.1（跨年从 2024 到 2026） |
| 同年同大版本任何发布 | **SEQUENCE** | 示例：1.26.1 → 1.26.2 |
| 内部优化、新增模块、bug 修复 | 不递增 | 加入 `[Unreleased]` 即可 |

### MAJOR 1 → 2 的不兼容点

```
- Game → Book 重命名
- ChessPlayer 类移除 → SIDE_RED/SIDE_BLACK/SIDE_ANY 常量
- get_pieces() → get_all_pieces()
- get_fenchs() → get_fench_positions()
- Move.from_text() 静态方法 → board.move_text() 实例方法
- NO_COLOR → SIDE_ANY
```

### 版本号同步

以下三处必须保持一致，发布前需全部验证：

| 文件 | 位置 |
|------|------|
| `pyproject.toml` | `version = "X.Y.Z"` |
| `src/cchess/__init__.py` | `__version__ = "X.Y.Z"` |
| `ReleaseNote.txt` | 顶部 `release vX.Y.Z` 段（开发中标记） |

### 重要约束

- **不要随随便便递增 MAJOR**：MAJOR 1 → 2 表示与上一版有显著不兼容
- **不要递增到 MAJOR 3、4... 直到出现新的破坏性 API 变化**
- 同一 MAJOR 内，年份发完后跨入下一年是新发布序列
- 未发布计划写在 `ReleaseNote.txt` 顶部并标注 `(开发中)`，不预分配版本号

## 待办事项

### 高优先级
- [x] 修复 `test_main_entry` CBF 解析问题 (已验证稳定通过)
- [ ] 添加类型提示到 board.py 和 piece.py
- [x] 移除 `Move.from_text()` 测试专用方法 (已改用 board.copy().move_text())

### 中优先级
- [x] 优化马的走法生成算法 (预计算偏移量 + 内联边界检查)
- [ ] 扩展缓存机制到走法生成
- [x] 优化 `PGNParser.tokenize()` 复杂度 (使用分发表 + 预计算字符集)
- [x] 文档化版本号命名规则 (大版本号.年.顺序)

### 低优先级
- [x] 清理注释掉的代码 (已检查，无需清理)
- [ ] 补充模块级文档字符串
- [ ] 实现走法排序启发式

## 性能优化报告
详细性能优化总结请参考：[PERFORMANCE_OPTIMIZATION_REPORT.md](PERFORMANCE_OPTIMIZATION_REPORT.md)

## 资源链接

- [GitHub 仓库](https://github.com/walker8088/cchess)
- [中国象棋规则](https://en.wikipedia.org/wiki/Xiangqi)
- [UCI/UCCI 协议文档](https://www.gnu.org/software/xboard/uci.html)
- [性能优化最佳实践](https://github.com/python/cpython/blob/main/Doc/performance.rst)
- [详细架构分析](ARCHITECTURE_ANALYSIS.md)
- [API 不兼容变化](API_CHANGES_ANALYSIS.md)
- [升级指南](UPGRADE_GUIDE.md)
- [开发指南](DEVELOPMENT_GUIDE.md)
- [代码审查清单](CODE_REVIEW.md)
