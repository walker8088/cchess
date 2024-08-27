import os
import sys
import argparse

from .game import Game

def main():
    parser = argparse.ArgumentParser(prog='python -m cchess')
    parser.add_argument('-r', '--readfile', help = 'read xqf,cbf file')
    args = parser.parse_args()
    
    file_name = args.readfile
    if not file_name:
        return
        
    try:
        game = Game.read_from(file_name)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)
        
    print('\n=====================================')
    game.print_init_board()
    print('=====================================')
    if game.annote:
        print(game.annote)
    print('-------------------------------------')
    
    game.print_text_moves(steps_per_line = 5, show_annote = True)


if __name__ == "__main__":
    main()