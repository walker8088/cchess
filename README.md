# cchess

cchess是一个Python版中国象棋库，主要功能如下:

##初始化
```python
from cchess import ChessBoard

# 使用默认初始局面
board = ChessBoard()
board.from_fen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1')
```

##棋盘显示
```python
board_strs = board.print_view()
print()
for s in board_strs:
    print(s)
# or
board.print_board()
```

##走子(内部格式), 中文显示
```python
move = board.copy().move((0, 0), (0, 1))
print(move.to_text())  # 车九进一
```

##走子(ICCS纵线格式),中文显示
```python
move = board.copy().move_iccs('a0a1')
print(move.to_text())  # 车九进一
```

##走子(中文格式),中文显示
```python
move = board.copy().move_text('车九进一')
print(move.to_text())  # 车九进一
```

##产生某个棋子的合法走子
```python
for mv in board.create_piece_moves((0, 0)):
    move = board.copy().move(*mv)
    print(move.to_text())
```

##产生所有合法走子
```python
for mv in board.create_moves():
    move = board.copy().move(*mv)
    print(move.to_text())
```

##将军检测
```python
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1')
print(board.is_checking())  # True (红车将军)
```

##将死对方检测
```python
print(board.is_checkmate())  # True
```

##走子被将军检测
```python
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1')
mv = board.move_iccs('d9e9')  # 注意：是 board.move_iccs 不是 move.from_iccs
print(board.is_checked_move(mv.pos_from, mv.pos_to))  # True
```

##被对方将死检测
```python
print(board.has_no_legal_moves())  # True
```

##读取xqf文件, 显示棋谱
```python
from cchess import Book

book = Book.read_from("WildHouse.xqf")
book.print_init_board()
book.print_text_moves()
```

##读取cbr文件, 显示棋谱
```python
book = Book.read_from("WildHouse.cbr")
book.print_init_board()
book.print_text_moves()
```

##读取cbl文件, 显示所有棋谱
```python
lib = Book.read_from_lib("WildHouse.cbl")
for book in lib['games']:
    book.print_init_board()
    book.print_text_moves()
```

##加载引擎进行对弈
支持 UCCI引擎（eyeele "象眼"引擎）和UCI引擎（pikafish "皮卡鱼"引擎）
