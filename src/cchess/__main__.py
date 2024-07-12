import os
import sys
import argparse

from .board import *

from .read_xqf import read_from_xqf

def main():
    parser = argparse.ArgumentParser(prog='python -m cchess')
    parser.add_argument('-r', '--readxqf', help = 'read xqf file')
    args = parser.parse_args()
    
    game = read_from_xqf(args.readxqf)
    game.init_board.move_player = ChessPlayer(RED)
    print('\n=====================================')
    game.print_init_board()
    print('=====================================\n')
    
    game.print_text_moves(steps_per_line = 4)


if __name__ == "__main__":
    main()