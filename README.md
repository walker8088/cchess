# cchess
cchesss是一个Python版的中国象棋库

这是一个快速的例子：

1.移动和文字显示

from cchess import *

board = ChessBoard()
board.from_fen(FULL_INIT_FEN)
board.print_board()
move = board.move(Pos(0,0),(Pos(0,1)))
print move.to_chinese()


2.读取xqf格式棋谱文件,并显示棋谱内容

from cchess import *

game = read_from_xqf("1.xqf")
game.print_init_board()
game.print_chinese_moves()


3.读取dhtml网页文件,并显示棋谱内容

import request

from cchess import *

url='http://game.onegreen.net/chess/HTML/13490.html'

req = requests.get(url)
html = req.content
game = read_from_dhtml(html)
game.print_init_board()
game.print_chinese_moves()

4.加载引擎进行对弈
  参见examples/end_game.py
  