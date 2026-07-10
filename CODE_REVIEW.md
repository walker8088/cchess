# CChess 代码审查清单

## 提交前检查

### 代码质量
- [ ] Ruff 检查通过 (`uvx ruff check ./src`)
- [ ] Pylint 评分 >= 8.0
- [ ] 无未使用的导入
- [ ] 无未使用的变量
- [ ] 函数复杂度合理（< 50 行）

### 类型安全
- [ ] 新增函数有类型提示
- [ ] 核心模块类型覆盖率 > 80%
- [ ] mypy 检查通过（可选）

### 测试
- [ ] 快速测试通过 (`python -m pytest tests/ -m "not slow" -x`)
- [ ] 引擎集成测试通过（`python -m pytest tests/test_engine_async.py -m "slow" -v`）
- [ ] 新增功能有对应测试
- [ ] 性能测试通过 (`python tests/check_regression.py`)
- [ ] 测试覆盖率 > 80%

### 文档
- [ ] 公共函数有 docstring
- [ ] 复杂逻辑有注释说明
- [ ] API 文档更新（如适用）
- [ ] ReleaseNote.txt 更新
- [ ] README 代码示例与最新 API 一致

### 性能
- [ ] 无性能回归（< 10% 阈值）
- [ ] 内存使用合理
- [ ] 无不必要的对象创建

## 代码风格

### 命名规范
- 函数名：snake_case
- 类名：PascalCase
- 常量：UPPER_CASE
- 私有方法：_leading_underscore

### 导入规范
- 标准库导入在前
- 第三方库导入在中
- 本地导入在后
- 按字母顺序排序

### 文档字符串规范
```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述。
    
    详细描述（如需要）。
    
    参数:
        param1: 参数描述
        param2: 参数描述
    
    返回:
        返回值描述
    
    异常:
        异常描述（如适用）
    
    示例:
        >>> function_name("test", 1)
        True
    """
```

## 提交规范

### 提交消息格式
```
<type>: <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复 bug
- `perf`: 性能优化
- `refactor`: 重构（不改变行为）
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例
```
feat: add normalized board position support

- Add ChessBoard.normalized() method
- Add ChessBoard.denormalize_pos() method
- Modify board.create_moves() to use normalized board
- Remove Move.from_text() test-only method (use board.copy().move_text() instead)

This reduces color branching in piece logic and makes
the code more maintainable.
```

## 审查流程

1. **作者自查** - 使用本清单检查代码
2. **自动检查** - CI/CD 运行测试和代码检查
3. **同行审查** - 至少一人审查
4. **合并** - 审查通过后合并到 master

## 常见问题

### Q: 如何添加类型提示？
A: 使用 Python 类型注解：
```python
def function_name(param1: str, param2: int) -> bool:
    ...
```

### Q: 如何运行性能测试？
A: 运行基准测试脚本：
```bash
python tests/benchmark.py          # 运行基准测试
python tests/check_regression.py   # 检查性能回归
```

### Q: 如何运行异步引擎测试？
A: 异步引擎测试需要启动 eleeye 等真实引擎，默认标记为 `slow`：
```bash
# 只跑快速测试（不启动引擎，CI 默认）
python -m pytest tests/ -m "not slow" -x -q

# 跑全部 slow 测试（需要本地引擎）
python -m pytest tests/test_engine_async.py -m "slow" -v

# 跑某个测试类
python -m pytest tests/test_engine_async.py::TestAsyncEngineBoundaryConditions -v
```

### Q: 如何验证 README 代码示例？
A: README 示例代码在发布前人工核对。修改 README 时运行对应示例代码确认输出与预期一致。

### Q: 如何更新文档？
A: 更新对应的 .md 文件，并确保 docstring 与代码同步。

---
**最后更新**: 2026-05
**维护者**: CChess 开发团队

## 参考资料

- [AGENTS.md](AGENTS.md) - 项目规则与开发流程
- [ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md) - 详细架构分析
- [ReleaseNote.txt](ReleaseNote.txt) - 版本变更记录
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - 通用开发经验指南
- [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) - 升级指南
