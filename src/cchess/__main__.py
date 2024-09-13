
import sys
import argparse
import pathlib

from .game import Game

def print_game(game):
    
    print('\n=====================================')
    print(game.info)
    game.print_init_board()
    print('-------------------------------------')
    if game.annote:
        print(game.annote)
        print('-------------------------------------')
    
    game.print_text_moves(steps_per_line = 5, show_annote = True)

def main():
    parser = argparse.ArgumentParser(prog='python -m cchess')
    parser.add_argument('-r', '--readfile', help = 'read pgn,xqf,cbf and cbl file')
    args = parser.parse_args()
    
    file_name = args.readfile
    if not file_name:
        return
    
    ext = pathlib.Path(file_name).suffix.lower()
    if ext == '.cbl':
        lib = Game.read_lib_from(file_name)
        print(lib.info['name'])
        for game in lib['games']:
            print_game(game)
    else:            
        try:
            game = Game.read_from(file_name)
        except Exception as e:
            print(e)
            sys.exit(-1)
        print_game(game)    


if __name__ == "__main__":
    main()