# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.27.0] - 2026-4-17

### Added
- 性能基准测试套件 (`tests/benchmark.py`)
- 性能回归检测脚本 (`tests/check_regression.py`)
- 代码审查清单 (`CODE_REVIEW.md`)
- 异步引擎测试 (`tests/test_engine_async.py`)
- `board.py` 核心方法类型提示
- `_append_move_to_game()` 辅助函数（消除代码重复）
- 马走法生成优化（内联检查，减少函数调用）

### Changed
- 优化 `Knight.create_moves()` 方法，性能提升约 35%
- 简化 `io_xqf.py` 和 `read_cbr.py` 中的重复代码
- 清理遗留注释代码和未使用导入
- 统一数字格式处理（RED 用中文，BLACK 用全角）

### Fixed
- 移除 `board.py` 中未使用的 `Union` 导入
- 修复 `io_xqf.py` 中的注释代码格式

### Performance
- get_pieces(): 0.024 ms/次 (42,259 ops/sec)
- create_moves(): 0.100 ms/次 (9,952 ops/sec)
- is_valid_move(): 0.003 ms/次 (389,469 ops/sec)
- Rook moves: 0.034 ms/次 (29,398 ops/sec)
- Cannon moves: 0.022 ms/次 (44,997 ops/sec)
- Knight moves: 0.023 ms/次 (44,132 ops/sec)
- Pawn moves: 0.023 ms/次 (42,708 ops/sec)

## [1.26.1] - 2026-4-15

### Fixed
- PGN 文件编码问题：优先尝试 UTF-8，再尝试 GBK，最后使用 chardet 兜底
- PGN 读取测试失败问题（chardet 误判编码导致 PGN 解析为空）
- io_xqf.py 语法错误（全角标点导致 Python 解析失败）
- read_cbr.py 变量名遮蔽内置函数问题
- PGN 编码检测策略，解决 Windows 本地编码 PGN 文件读取失败
- pyproject.toml pytest 配置警告（tb_style -> addopts）

### Changed
- 添加 chardet 为项目依赖
- 修复大量 pylint 问题，评分从 9.01 提升至 10.00/10
- 添加/完善类和函数 docstring
- 修复异常处理：使用具体异常类型替代宽泛 Exception

### Added
- 新增命令行格式转换功能：-i 输入文件 -o 输出文件，支持 pgn<->xqf、cbf->xqf
- 5 个命令行转换测试用例（pgn->xqf, xqf->pgn, cbf->xqf, 格式错误, 不支持格式）

## [1.24.6] 

### Added
- 读写带 xqf 格式棋谱，支持变招和注释
- 读取东萍 UBB dhtml 格式棋谱（不支持变招和注释）
- 读写 pgn 格式棋谱，支持变招和注释

## [1.24.4] 

### Added
- 目前可以读入 XQF, CBR, CBL, PGN (iccs 格式和文本格式) 的棋谱

## [Unreleased] - TBD

### Performance
- 引入 `make_move`/`unmake_move` 机制：新增 `MoveInfo` dataclass 记录移动增量信息，替代深拷贝，大幅减少内存分配和复制开销。
- 实现攻击矩阵缓存：添加 `_red_attacks`、`_black_attacks` 缓存和 `_attack_matrix_dirty` 脏标志，`is_checking()` 等方法优先使用缓存，仅在脏时重新计算，显著提升查询性能。
- 优化车、炮、兵的 `create_moves()` 方法：减少无效计算，将全棋盘遍历（90个位置）改为基于规则生成候选位置（车/炮最多17个，兵最多3个），提升性能。

### Fixed
- 修复 `read_txt.py` 中属性名 `move_side` 错误，改为 `move_player`。
- 修复 `exception.py` 中 `CChessError` 未调用 `super().__init__()`。
- 修复 `move.py` 中引用不存在的 `sibling_next` 属性，导致无限循环。
- 修复 `is_checking_move` 和 `is_checked_move` 中的将军检测逻辑。
- 修复吃将时走子方切换问题：`make_move` 中检查 `captured_fench` 为 `'k'`/`'K'` 时不切换走子方。
- 修复 Python 3.8 兼容性问题：将 `tuple[int, int]` 改为 `Tuple[int, int]`，并导入 `Tuple, List`。
- 修复 `test_gbk_fallback_encoding` 测试失败：调整 PGN 文件读取的编码处理策略，解决中文字符乱码问题。
- 修复 `io_pgn.py` 中 `Move` dataclass 命名冲突，重命名为 `PGNMove`。
- 修复 `ChessPlayer.next()` 行为不一致问题：改为返回新实例，不修改原对象。

### Changed
- 重构常量管理：创建 `constants.py` 集中管理颜色、棋盘等常量，消除循环导入风险。
- 重构 `fen_mirror`、`fen_flip`、`fen_swap` 函数：转为 `Board` 类的静态方法，调整模块导入关系。
- 统一模块文档字符串引号格式：将单引号三引号改为双引号，修复孤立引号注释块。
- 修复 `__init__.py` 中 `__all__` 列表：填充所有公共 API 名称，确保 `from cchess import *` 正常工作。
- 将 `CChessException` 重构为 `CChessError`，同步更新所有导入和测试代码。
- 运行 Ruff check 并修复问题：合并未使用的导入，添加 `noqa` 注释。

### Added
- 新增 `MoveInfo` dataclass：用于记录移动的增量信息，支持 `make_move`/`unmake_move` 机制。
- 新增攻击矩阵缓存属性：`_red_attacks`、`_black_attacks`、`_attack_matrix_dirty`。
- 新增 `_compute_piece_attacks()` 和 `_recompute_attack_matrix()` 方法：实现攻击矩阵的懒更新。
- 新增测试文件 `test_board_make_unmake.py`：包含 9 个测试用例，验证 `make_move`/`unmake_move` 机制的正确性。

### Planned
- 异步引擎支持
- 类型注解补全
- 性能回归测试
- 模块化重构（board.py 拆分）
