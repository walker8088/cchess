
import sys

sys.path.insert(0, '..\\src\\')

import cchess

lib = cchess.read_from_cbl('D:\\01_MyRepos\\cchess\\tests\\data\\1956年全国象棋锦标赛93局.CBL')

#print(lib['name'])
#for game in lib['games']:
    #print('\n=====================================')
    #print(game.info['title'])
    #game.print_init_board()
    #print('=====================================')
    #if game.annote:
    #    print(game.annote)
    #    print('-------------------------------------')
    #game.print_text_moves(steps_per_line = 1, show_annote = True)

'''
game = cchess.read_from_cbr('test2.cbr')
print('\n=====================================')
game.print_init_board()
print('=====================================')
if game.annote:
    print(game.annote)
print('-------------------------------------')

game.print_text_moves(steps_per_line = 1, show_annote = True)
print('李3'.encode('utf-16-le').hex())
'''