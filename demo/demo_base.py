from cchess import *

board = ChessBoard()
board.from_fen(FULL_INIT_FEN)

#1.棋盘显示
board_strs = board.text_view()
print()
for s in board_strs:
    print(s)
#或者
board.print_board()

#2.走子(内部格式), 中文显示
move = board.copy().move((0,0),(0,1))
print(move.to_chinese())

#3.走子(ICCS纵线格式),中文显示
move = board.copy().move_iccs('a0a1')
print(move.to_chinese())

#4.走子(中文格式,尚待完善),中文显示
move = board.copy().move_chinese('车九进一')
print(move.to_chinese())

#5.产生某个棋子的合法走子
moves = board.create_piece_moves((0,0))
print('******************')
for mv in moves:
    move = board.copy().move(*mv)
    print(move.to_chinese())

#6.产生所有合法走子
moves = board.create_moves()
print('******************')
for mv in moves:
    move = board.copy().move(*mv)
    print(move.to_chinese())
 
#6.将军检测
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 w - - 0 1') 
print(board.is_checking()) #True
#将死对方检测
print(board.is_win())      #True 

#7.走子被将军检测
board.from_fen('3k5/9/9/9/9/3R5/9/9/9/4K4 b - - 0 1')

mv = move.from_iccs('d9e9') 
print(board.is_checked_move(*mv)) #True

#被对方将死检测
print(board.is_lost())    #True

#8.读取xqf文件, 显示棋谱
game = read_from_xqf("WildHouse.xqf")

game.init_board.print_board()

board_strs = game.init_board.text_view()
print('******************')
print()
for s in board_strs:
    print(s)
    
game.print_chinese_moves()

'''            
moves = game.dump_moves()
for move_line in moves:
    for mv in move_line:
        print(mv.to_chinese())
'''        