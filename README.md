# cchess

cchess是一个Python版的中国象棋库，主要功能如下:

##棋盘显示
```
board_strs = board.text_view()
print()
for s in board_strs:
    print(s)
#or    
board.print_board()
```

##走子(内部格式), 中文显示
```
move = board.copy().move((0,0),(0,1))
print(move.to_text())
```

##走子(ICCS纵线格式),中文显示
```
move = board.copy().move_iccs('a0a1')
print(move.to_text())
```

##走子(中文格式,尚待完善),中文显示
```
move = board.copy().move_text('车九进一')
print(move.to_text())
```

##产生某个棋子的合法走子
```
moves = board.create_piece_moves((0,0))
for mv in moves:
    move = board.copy().move(*mv)
    print(move.to_text())
```

##产生所有合法走子
```
moves = board.create_moves()
for mv in moves:
    move = board.copy().move(*mv)
    print(move.to_text())
```

##将军检测
```
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1') 
print(board.is_checking()) #True
```

##将死对方检测
```
print(board.is_checkmate())      #True 
```

##走子被将军检测
```
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1')
mv = move.from_iccs('d9e9') 
print(board.is_checked_move(*mv)) #True
```

##被对方将死检测
```
print(board.no_moves())    #True
```

##读取xqf文件, 显示棋谱
```
game = Game.read_from("WildHouse.xqf")
game.init_board.print_board()
board_strs = game.init_board.text_view()
print()
for s in board_strs:
    print(s)
    
game.print_text_moves()
```
##读取cbr文件, 显示棋谱
```
game = Game.read_from("WildHouse.cbr")
game.init_board.print_board()
board_strs = game.init_board.text_view()
print()
for s in board_strs:
    print(s)
    
game.print_text_moves()
```

##读取cbl文件, 显示所有棋谱
```
lib = Game.read_from_lib("WildHouse.cbl")
for game in lib['games']:
    game.init_board.print_board()
    board_strs = game.init_board.text_view()
    print()
    for s in board_strs:
        print(s)
        
    game.print_text_moves()
```

##加载引擎进行对弈
支持 UCCI引擎（eyeele “象眼”引擎）和UCI引擎（pikafish “皮卡鱼”引擎）
参见demo/end_game_master.py
