from cchess import *

board = ChessBoard(FULL_INIT_FEN)
board.print_board()

board = ChessBoard('3k5/9/9/9/9/4R4/9/9/9/5K3 w - - 0 1')

#mv = Move.from_iccs('e4e9')
#print(mv)
board.move_iccs('e4e9')
#print(board.check_count())

board.print_board()
#print(board.dump_board())

#board.copy().is_checked_move(*mv))
