import os
import sys
import argparse

from .read_xqf import read_from_xqf
from .read_cbf import read_from_cbf

def main():
    parser = argparse.ArgumentParser(prog='python -m cchess')
    parser.add_argument('-r', '--readfile', help = 'read xqf,cbf file')
    args = parser.parse_args()
    
    file_name = args.readfile
    ext = os.path.splitext(file_name)[1].lower()
    try:
        if ext == '.xqf':
            game = read_from_xqf(file_name)
        elif ext == '.cbf':
            game = read_from_cbf(file_name)
        else:
            print(f'Unknown file type {ext}')
            sys.exit(-1)
        if game is None:
            print(f'Read file error: {ext}')
            sys.exit(-1)
    except FileNotFoundError as e:
        print(e)
        sys.exit(-1)
        
    print('\n=====================================')
    game.print_init_board()
    print('=====================================\n')
    game.print_text_moves(steps_per_line = 5)


if __name__ == "__main__":
    main()