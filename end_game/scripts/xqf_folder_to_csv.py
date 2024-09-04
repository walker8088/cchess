# -*- coding: utf-8 -*-
import os
import sys
import csv
import shutil
import pathlib

import cchess
from cchess import Game 

fen_dict = {}
same_files = []

def load_board(root_path):
    games = []
    for root, dirs, files in os.walk(root_path, topdown=True):
        for name in files:
            file_name = pathlib.Path(root, name)
            game_info = {}
            ext = file_name.suffix.lower()
            if ext != '.xqf':
                continue
            #print(file_name)
            game = Game.read_from(file_name)
            fen = game.init_board.to_fen()
            moves = game.dump_iccs_moves()
            sub_type = cchess.get_fen_type_detail(fen)
            
            game_info['name'] = file_name.name
            game_info['fen'] = fen
            game_info['sub_type'] = sub_type
            
            moves = game.dump_iccs_moves()
            move_lens = [len(x) for x in moves]
            
            if len(move_lens) > 0:
                game_info['max_len'] = max(move_lens)
            else:
                game_info['max_len'] = 0
                
            print(len(moves), file_name)
            game_info['moves'] = moves
            
            if fen not in fen_dict:
                fen_dict['fen'] = game
                games.append(game_info)
            else:
                same_files.append('棋局重复', fen_dict[fen][name], '==', game['name'])
            
    return games

#---------------------------------------------------------
collection = pathlib.Path(sys.argv[1])
games = load_board(collection)

if len(same_files) == 0:
    print('没有重复棋局')
else:
    print(f'有{len(same_files)}局重复棋局：')
    for f1, f2 in same_files:
        print(f2, '==', f1)

games.sort(key = lambda x: x['max_len'])

with open(f"{collection.name}.csv", 'w') as f:
    writer = csv.writer(f)
    # write a row to the csv file
    writer.writerow(['name', 'type_red', 'type_black', 'fen', 'branchs', 'steps', 'moves'])
    for g in games:
        moves_all = []
        for moves in g['moves']:
            line = ' '.join(moves)
            moves_all.append(line)
        moves_line = '|'.join(moves_all)
        
        row = [g['name'], *g['sub_type'], g['fen'], len(g['moves']), g['max_len'], moves_line]
        writer.writerow(row)

