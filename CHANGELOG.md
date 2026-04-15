# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.26.1] - 2024-xx-xx

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

## [1.24.6] - 2024-xx-xx

### Added
- 读写带 xqf 格式棋谱，支持变招和注释
- 读取东萍 UBB dhtml 格式棋谱（不支持变招和注释）
- 读写 pgn 格式棋谱，支持变招和注释

## [1.24.4] - 2024-xx-xx

### Added
- 目前可以读入 XQF, CBR, CBL, PGN (iccs 格式和文本格式) 的棋谱

## [Unreleased] - TBD

### Performance
- 优化车、炮、兵的 `create_moves()` 方法：减少无效计算，将全棋盘遍历（90个位置）改为基于规则生成候选位置（车/炮最多17个，兵最多3个），提升性能。

### Planned
- 异步引擎支持
- 类型注解补全
- 性能回归测试
- 模块化重构（board.py 拆分）
