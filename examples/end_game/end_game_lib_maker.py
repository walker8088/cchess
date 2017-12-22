# -*- coding: utf-8 -*-
'''
Copyright (C) 2014  walker li <walker8088@gmail.com>

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

import sys, os
import shutil

sys.path.append('..')
from cchess import *


def load_board(root_path):
    games = []
    files = os.listdir(root_path)
    for file in files:
        game_info = {}
        ext = os.path.splitext(file)[1].lower()
        if ext != '.xqf':
            continue
        file_name = os.path.join(root_path, file)
        game = read_from_xqf(file_name)
        game.init_board.move_side = ChessSide.RED
        fen = game.init_board.to_short_fen()
        #fen = ' '.join(init_fen.split()[0:2])
        print file[:-4], game.info["Result"], fen
        game_info['name'] = file[:-4]
        game_info['result'] = game.info["Result"]
        game_info['fen'] = fen
        game_info['moves'] = game.dump_std_moves()
        #f.write("%s|%s\n" % (file[:-4].encode('utf-8'), fen))
        #game.print_init_board()
        #game.print_chinese_moves()
        max_len = 0
        for move in game.dump_std_moves():
            if len(move) > max_len:
                max_len = len(move)
        game_info['len'] = max_len
        games.append(game_info)

    games.sort(key=lambda x: x['len'])
    return games


#collection_name = u'适情雅趣360.eglib'
#collection_dir = u'..\\games\\残局谱\\适情雅趣360局'
collection_name = u'适情雅趣550.eglib'
collection_dir = u'..\\games\\残局谱\\适情雅趣550局\\先胜局'
#collection_name = u'弈海烟波.eglib'
#collection_dir = u'..\\games\\残局谱\\\弈海烟波'
#collection_name = u'非连杀小局.eglib'
#collection_dir = u'..\\games\\残局谱\\\非连杀小局'
#collection_name = u'烂柯神机.eglib'
#collection_dir = u'..\\games\\残局谱\\\烂柯神机'
#collection_name = u'少子百局谱.eglib'
#collection_dir = u'..\\games\\残局谱\\\少子百局谱'
#collection_name = u'泥马渡康王.eglib'
#collection_dir = u'..\\games\\残局谱\\\泥马渡康王'

with open(collection_name, 'wb') as f:
    for game in load_board(collection_dir):
        #if u"红胜" not in game['name']:
        #        continue
        if "1-0" not in game['result']:
            continue

        moves = game['moves']
        moves.sort(key=lambda x: len(x))
        for move in moves:
            f.write("%s|%s|%s\n" % (game['name'].encode('utf-8'), game['fen'],
                                    ','.join(move)))
