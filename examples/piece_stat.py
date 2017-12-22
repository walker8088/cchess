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

import numpy as np
import os, sys

sys.path.append('..')
from cchess import *

counters = {
   'P':np.ones((10, 9), dtype = np.int),
   'C':np.ones((10, 9), dtype = np.int),
   'R':np.ones((10, 9), dtype = np.int),
   'N':np.ones((10, 9), dtype = np.int),
   'A':np.ones((10, 9), dtype = np.int),
   'B':np.ones((10, 9), dtype = np.int),
   'K':np.ones((10, 9), dtype = np.int),
}

def count_board(board, counter):
    for y in range(10):
        for x in range(9):
            piece = board[y][x]
            if piece == None : continue
            new_y = 9-y if piece.isupper() else y
            counter[piece.upper()][new_y][x] += 1

def balance_add(map):
    for y in range(10):
        v = map[y][::-1]
        map[y] += v
        
def norm(map):
    #logmap = np.log(map)
    xmax, xmin = map.max(), map.min()
    return (map - xmin)/(xmax - xmin)*50
    
def show(map):
    for y in range(10):
        print("%3d %3d %3d %3d %3d %3d %3d %3d %3d " % tuple(map[y]))
            
def main(root_path):
    #num = 0
    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_name = os.path.join(root, file)
            name, ext = os.path.splitext(file)
            names = name.split()
            name = "_".join(names)
            if ext.lower() not in [".xqf"] :
                print("PASSED ", file_name)
                continue
            print( "processing",  file_name)
            game = read_from_xqf(file_name)
            for move in game.iter_moves():
                count_board(move.board_done._board, counters)
            break
            
    for piece in counters:
        map = counters[piece]
        min = map.min() 
        avg = np.average(map)
        if piece == 'P':
             map[6] = np.ones(9)
        
        elif piece == 'C':
             map[7][1] = min
             map[7][7] = min
             map[7][4] = map[7][4]*1.2
        
        elif piece == 'R':
             map[9][0] = min
             map[9][8] = min
             map[9][1] = avg
             map[9][7] = avg
        
        elif piece == 'N':
             map[9][4] = avg
             map[7][0] = avg
             map[7][2] = avg*1.2
             map[7][6] = avg*1.2
             map[7][8] = avg
             
             map[9][1] = map.min()
             map[9][7] = map.min()
             map[9][4] = map.min()
             
        
        elif piece == 'A':
             map[9][3] = map[8][4] * 1.2
             map[9][5] = map[9][3]
             
        elif piece == 'B':
             map[9][2] = map[7][4] * 1.2
             map[9][6] = map[9][2]
             
        elif piece == 'K':
             map[9][4] = map[9][3] * 1.2
             
        balance_add(map)
        map = norm(map)
        print(piece)
        show(map)
        np.savetxt('%s.txt'%piece, map)

        
#-----------------------------------------------------#
if __name__ == '__main__':
    main('../game_book/对局谱/')
    