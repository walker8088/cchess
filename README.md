# cchess
cchess是一个Python版的中国象棋库，目标是为

这是一个快速的例子：

1.棋盘表示，走子和中文走子显示

from cchess import *

board = ChessBoard()

board.from_fen(FULL_INIT_FEN)

board.print_board()

move = board.move((0,0),(0,1)))

print(move.to_chinese())


2.读取xqf格式棋谱文件,并显示棋谱内容

from cchess import *

game = read_from_xqf("1.xqf")

game.print_init_board()

game.print_chinese_moves()

3.读取txt格式的棋谱文件，并显示棋谱内容


4.加载引擎进行对弈
  参见examples/end_game.py
  
cchess库使用pytest进行单元测试，使用pytest-cov进行覆盖检查，目标实现100%覆盖。
测试执行：pytest -v --pep8 --flakes --cov=cchess .\tests\
代码检测：pytest -v --pep8 --flakes .\src\
或者直接执行：pytest  