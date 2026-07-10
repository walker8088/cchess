# cchess

cchess是一个Python版中国象棋库，主要功能如下:

## 初始化
```python
from cchess import ChessBoard, FULL_INIT_FEN

# 注意：ChessBoard() 默认创建空棋盘，不是初始局面！
# 如需初始局面，需使用 FULL_INIT_FEN 或调用 from_fen()

# 方式 1：使用 FULL_INIT_FEN 常量
board = ChessBoard(FULL_INIT_FEN)

# 方式 2：使用 from_fen 加载自定义局面
board = ChessBoard()
board.from_fen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1')
```

## 棋盘显示
```python
board_strs = board.print_view()
print()
for s in board_strs:
    print(s)
```

## 走子(内部格式), 中文显示
```python
move = board.copy().move((0, 0), (0, 1))
print(move.to_text())  # 车九进一
```

## 走子(ICCS纵线格式), 中文显示
```python
move = board.copy().move_iccs('a0a1')
print(move.to_text())  # 车九进一
```

## 走子(中文格式), 中文显示
```python
move = board.copy().move_text('车九进一')
print(move.to_text())  # 车九进一
```

## 产生某个棋子的合法走子
```python
for mv in board.create_piece_moves((0, 0)):
    move = board.copy().move(*mv)
    print(move.to_text())
```

## 产生所有合法走子
```python
for mv in board.create_moves():
    move = board.copy().move(*mv)
    print(move.to_text())
```

## 将军检测
```python
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1')
print(board.is_checking())  # True (红车将军)
```

## 将死对方检测
```python
print(board.is_checkmate())  # True
```

## 走子被将军检测
```python
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1')

# 方式 1：走子前检查（推荐）——使用 gives_check 检查走子后是否将军对方
print(board.gives_check((3, 9), (4, 9)))  # True

# 方式 2：走子后检查走子后是否被将军 —— 需要使用 copy() 避免修改原棋盘
mv = board.copy().move_iccs('d9e9')
print(board.gives_check(mv.pos_from, mv.pos_to))  # True
```

> **注意**：`leaves_king_in_check()` 用于判断执行走子后己方是否被将军（不含在本例中），且走子会修改棋盘状态。如需检查该走子是否将军对方，应使用 `gives_check()`。

## 被对方将死检测
```python
print(board.has_no_legal_moves())  # True
```

## 读取 xqf 文件, 显示棋谱
```python
from cchess import Book

book = Book.read_from("WildHouse.xqf")
book.print_init_board()
book.print_text_moves()
```

## 读取 cbr 文件, 显示棋谱
```python
book = Book.read_from("WildHouse.cbr")
book.print_init_board()
book.print_text_moves()
```

## 读取 cbl 文件, 显示所有棋谱
```python
lib = Book.read_from_lib("WildHouse.cbl")
for book in lib['games']:
    book.print_init_board()
    book.print_text_moves()
```

## 加载引擎进行对弈
支持 UCCI引擎（eyeele "象眼"引擎）和UCI引擎（pikafish "皮卡鱼"引擎）

## 异步引擎调用
基于 `asyncio` 的非阻塞引擎接口，适合Web服务、批量分析等场景。

### 基本用法（异步上下文管理器）
```python
import asyncio
from cchess import ChessBoard, FULL_INIT_FEN
from cchess.engine_async import AsyncEngine

async def main():
    # 自动检测协议类型（默认）
    async with AsyncEngine("Engine/eleeye/ELEEYE.EXE") as engine:
        board = ChessBoard(FULL_INIT_FEN)

        # 异步走一步棋（带超时保护，默认 60 秒）
        result = await engine.play(board, depth=10, timeout=30)
        print(f"最佳走法: {result['move']}")
        print(f"评分: {result.get('score')}")
        print(f"PV 线: {result.get('pv', [])}")

asyncio.run(main())
```

### 带时间限制的走子
```python
async def timed_play():
    async with AsyncEngine("Engine/eleeye/ELEEYE.EXE") as engine:
        board = ChessBoard(FULL_INIT_FEN)
        # 限制思考时间 2 秒
        result = await engine.play(board, time_limit=2.0)
        print(result["move"])

asyncio.run(timed_play())
```

### 局面分析
```python
async def analyse():
    async with AsyncEngine("Engine/pikafish_230408/pikafish.exe") as engine:
        board = ChessBoard(FULL_INIT_FEN)
        # 分析局面，返回评分、PV 线等信息
        results = await engine.analyse(
            board,
            depth=15,
            multipv=3,        # 返回 3 条最佳线路
            timeout=30
        )
        for i, info in enumerate(results, 1):
            print(f"线路 {i}: 评分={info.get('score')}, PV={info.get('pv')}")

asyncio.run(analyse())
```

### 显式指定协议
```python
# 明确指定 UCCI 协议
engine = AsyncEngine("Engine/eleeye/ELEEYE.EXE", protocol="ucci")

# 明确指定 UCI 协议
engine = AsyncEngine("Engine/pikafish_230408/pikafish.exe", protocol="uci")

async def explicit():
    async with AsyncEngine("Engine/eleeye/ELEEYE.EXE", protocol="ucci") as engine:
        # 手动初始化
        await engine.initialize()
        # 配置引擎参数
        await engine.configure({"Hash": "128", "Threads": "4"})
        # ... 使用引擎
asyncio.run(explicit())
```

### 便捷函数
```python
from cchess.engine_async import play_move, analyse_position

async def quick_play():
    async with AsyncEngine("Engine/eleeye/ELEEYE.EXE") as engine:
        board = ChessBoard(FULL_INIT_FEN)
        # 一步走棋，返回 ICCS 格式字符串（如 'a0a1'）
        move_str = await play_move(engine, board, depth=10)
        print(move_str)

        # 分析局面，返回第一条结果
        result = await analyse_position(engine, board, depth=15)
        print(result)

asyncio.run(quick_play())
```

### 并发调用多个引擎
```python
async def multi_engine():
    # 同时启动多个引擎实例（UCCI + UCI）
    async def run(name, path, protocol):
        async with AsyncEngine(path, protocol=protocol) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=8)
            return name, result["move"]

    # 并发执行
    results = await asyncio.gather(
        run("象眼", "Engine/eleeye/ELEEYE.EXE", "ucci"),
        run("皮卡鱼", "Engine/pikafish_230408/pikafish.exe", "uci"),
    )
    for name, move in results:
        print(f"{name}: {move}")

asyncio.run(multi_engine())
```

### 错误处理
```python
async def safe_play():
    engine = AsyncEngine("Engine/eleeye/ELEEYE.EXE")
    try:
        await engine.initialize()
        board = ChessBoard(FULL_INIT_FEN)
        result = await engine.play(board, depth=10, timeout=10)
        print(result["move"])
    except RuntimeError as e:
        print(f"引擎未初始化: {e}")
    except asyncio.TimeoutError:
        print("走棋超时")
    finally:
        # 确保引擎进程被关闭
        await engine.quit()

asyncio.run(safe_play())
```
