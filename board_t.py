
import cchess

board = cchess.ChessBoard()  
board.from_fen('3k5/9/9/9/9/6B2/9/3A5/9/3A1KB2 w')

board.print_board()
    
b = board.copy()
b.move_text('仕六进五').to_iccs() == 'd0e1'
b.print_board()

b = board.copy()
b.move_text('相三退一').to_iccs() == 'g4i2'
b.print_board()

b = board.copy()
b.move_text('相三进一').to_iccs() == 'g0i2'
b.print_board()
