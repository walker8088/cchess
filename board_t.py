
import cchess

board = cchess.ChessBoard()  
'''
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
'''
board.from_fen('3k5/9/9/9/9/6B2/9/3A5/9/3A1KB2 w')
print(board.copy().move_text('仕六进五').to_iccs() == 'd0e1')
print(board.copy().move_text('仕六退五').to_iccs() == 'd2e1')
assert board.copy().move_text('相三退一').to_iccs() == 'g4i2'
assert board.copy().move_text('相三进一').to_iccs() == 'g0i2'

board = cchess.ChessBoard(
            'r1bak1b1r/4a4/2n1ccn2/p1p1C1p1p/9/9/P1P1P1P1P/4C1N2/9/RNBAKABR1 w'
        )
move = board.copy().move_text('前炮退二')
assert move.move_player == cchess.RED
