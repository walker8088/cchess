
import sys
import argparse
import pathlib

from .game import Game

def print_game(game):
    
    print('\n=====================================')
    for key, v in game.info.items():
        if v: 
            print(f"{key} : {v}")

    game.print_init_board()
    print('-------------------------------------')
    if game.comment:
        print(game.comment)
        print('-------------------------------------')
    
    game.print_text_moves(steps_per_line = 5, show_comment = True)

def main():
    parser = argparse.ArgumentParser(prog='python -m cchess')
    parser.add_argument('-r', '--readfile', help = 'read pgn,xqf,cbf and cbl file')
    parser.add_argument('-c', '--change format', help = 'read [pgn,cbf] file and save to xqf file')
    args = parser.parse_args()
    
    file_name = args.readfile
    if file_name:
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