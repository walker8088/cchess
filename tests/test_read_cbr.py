
import sys

sys.path.insert(0, '..\\src\\')

import cchess

game = cchess.read_from_cbr('test.cbr')
print('\n=====================================')
game.print_init_board()
print('=====================================')
if game.annote:
    print(game.annote)
print('-------------------------------------')

game.print_text_moves(steps_per_line = 5, show_annote = False)
