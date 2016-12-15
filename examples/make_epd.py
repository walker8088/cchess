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

def load_board(root_path, f):
        files = os.listdir(root_path)
        for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext != '.xqf':
                        continue
                file_name = os.path.join(root_path, file)
                #print file_name
                game = read_from_xqf(file_name)
               
                game.init_board.move_side = ChessSide.RED
                fen = game.init_board.to_fen()
                print file[:-4],fen
                f.write("%s|%s\n" % (file[:-4].encode('utf-8'), fen))
                #game.print_init_board()
                #game.print_chinese_moves()
    
with open(u'适情雅趣550.epd', 'wb') as f:
        load_board(u'..\\games\\残局谱\\适情雅趣550局\\先胜局', f)
            