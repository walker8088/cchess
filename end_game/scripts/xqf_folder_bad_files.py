# -*- coding: utf-8 -*-
import os
import sys
import shutil
import pathlib
from collections import OrderedDict

import cchess
from cchess import Game

p_dict = {
    "R":'车',
    "N":'马',
    "C":'炮',
    "P":'兵',
}

bad_files = []

def load_board(root_path):
    games = []
    files = os.listdir(root_path)
    for file in files:
        game_info = {}
        ext = os.path.splitext(file)[1].lower()
        if ext != '.xqf':
            continue
        file_name = os.path.join(root_path, file)
        game = Game.read_from(file_name)
        fen = game.init_board.to_fen()
        moves = game.dump_iccs_moves()
        game_info['name'] = file[:-4]
        game_info['fen'] = fen
        game_info['moves'] = game.dump_iccs_moves()
        print(fen)
        if cchess.FULL_INIT_BOARD in fen:
            bad_files.append(file_name)
        else:
            games.append(game_info)

    return games

def get_red_pieces(fen):
    pieces = OrderedDict()
    fen_base = fen.split(' ')[0]
    for ch in fen_base:
        if ch.isupper():
            if ch not in pieces:
                pieces[ch] = 0
            pieces[ch] += 1    
            
    return pieces

def get_title(fen):
    pieces = get_red_pieces(fen)
    for ch in ['K', 'A', 'B']:
        if ch in pieces:
            pieces.pop(ch)
    
    title = ''
    p_count = 0
    for fench in ['R', 'N', "C", 'P']:
        if fench not in pieces:
            continue
        #if fench == 'P' and p_count > 0:
        #    continue
        #title += p_dict[f'{fench}{pieces[fench]}']
        title += p_dict[f'{fench}']
        p_count += 1
        
    return title


collection_dir = sys.argv[1]
games = load_board(collection_dir)
print(len(bad_files))

'''
game_types = {}
for game in games:
    title = get_title(game['fen'])
    game['title'] = title
    if title == '':
        continue
    if title not in game_types:
        game_types[title] = []
    game_types[title].append(game)

for title, games in game_types.items():
    with open(f"{title}类杀法.txt", 'w') as f:
        print(title, len(games))
        for g in games:
            f.write(f"{g['name']},{g['fen']}\n")

'''