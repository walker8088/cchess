# -*- coding: utf-8 -*-
'''
Copyright (C) 2024  walker li <walker8088@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

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