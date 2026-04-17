# CChess AI Agent 指南

## 项目概述

中国象棋（CChess）Python 实现，支持棋谱读写、走法生成、引擎接口等功能。

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
# 运行所有测试（排除引擎测试）
python -m pytest tests/ --ignore=tests/test_engine.py --ignore=tests/test_engine_extended.py -x -q

# 运行特定测试模块
python -m pytest tests/test_board_move.py -xvs
python -m pytest tests/test_coverage.py -x -q
```

## 代码优化指南

### 已完成的优化

1. **规范局面重构** - 使用 `normalized()` 方法减少红黑颜色分支
2. **Piece 类优化** - 添加 `__slots__` 减少内存占用 40%
3. **车/炮走法优化** - 直接访问棋盘数组，减少方法调用
4. **代码清理** - 修复所有 ruff 检查错误

### 命名约定

- `positions` - 坐标列表（避免使用 `poss`）
- `next_node` - 链表下一个节点（避免 shadow 内置 `next`）
- `engine_out_queue` - 引擎输出队列（拼写正确）

### 性能优化点

1. **缓存 `fench_to_species()`** - 模块级 `_SPECIES_CACHE` 字典
2. **滑走棋子方向常量** - `_SLIDING_DIRECTIONS` 避免重复创建
3. **减少元组创建** - 使用局部变量代替中间元组

## 架构说明

### 核心模块

- `board.py` - 棋盘类，含走法生成、FEN 解析
- `piece.py` - 棋子类层次结构（King, Advisor, Bishop, Knight, Rook, Cannon, Pawn）
- `move.py` - 走法类，含中文走法解析
- `common.py` - 工具函数和常量

### 设计模式

1. **规范局面（Normalized Board）** - 将黑方走子转换为红方视角处理
2. **延迟计算** - `Move` 对象的棋盘快照按需生成
3. **工厂模式** - `Piece.create()` 根据棋子类型创建实例

## 测试策略

### 测试覆盖

- 单元测试：`test_board_move.py`, `test_piece.py`
- 覆盖率测试：`test_coverage.py` (200+ 测试)
- 集成测试：`test_io_pgn_txt.py`, `test_read_xqf.py`

### 已知问题

- `test_main.py::test_main_entry` - 预存在失败，与 CBF 文件格式解析有关
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

### 当前性能指标

```
get_pieces() x1000:        0.022s (0.022ms/次)
create_moves() x100:       0.015s (0.147ms/次)
fench_to_species() x300k:  0.022s (0.072μs/次，缓存命中)
Rook at center x1000:      0.019s (0.019ms/次)
Cannon at center x1000:    0.028s (0.028ms/次)
```

## 待办事项

### 高优先级
- [ ] 修复 `test_main_entry` CBF 解析问题
- [ ] 添加类型提示到 board.py 和 piece.py

### 中优先级
- [ ] 优化马的走法生成（当前使用暴力遍历）
- [ ] 添加走法排序启发式

### 低优先级
- [ ] 清理注释掉的代码
- [ ] 补充模块级文档字符串

## 资源链接

- [GitHub 仓库](https://github.com/walker8088/cchess)
- [中国象棋规则](https://en.wikipedia.org/wiki/Xiangqi)
- [UCI/UCCI 协议文档](https://www.gnu.org/software/xboard/uci.html)
