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
import json
import shutil
from sets import Set

sys.path.append('..')
from cchess import *

dup_files = []


def read_hist_moves():
    moves = Set()
    with open('game_moves_good.txt') as f:
        lines = f.readlines()
    for item in lines:
        moves.add(item.strip())
    return moves


def main(root_path):
    good_moves = Set()
    bad_files = []
    skip_count = 0

    for root, paths, files in os.walk(root_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext != '.xqf':
                continue
            file_name = os.path.join(root, file)
            print file_name.encode('GB18030')
            game = read_from_xqf(file_name)
            if not game:
                print 'None game at file', file_name
            if not game.verify_moves():
                print 'Bad move at file', file_name
                bad_files.append(file_name)

            game.print_init_board()
            game.print_chinese_moves()

            continue

            for moves in book['Moves']:
                if moves in good_moves:
                    #print "already moves",file_name
                    dup_files.append(file_name)
                    skip_count += 1
                    continue

                steps = len(moves.split(' '))
                #print steps
                if (steps < 30) and (book['Result'] == '1/2-1/2'):
                    print "bad peace moves", steps, file_name.encode('GB18030')
                    dup_files.append(file_name)
                    #print moves
                    #shutil.move(file_name, 'bad_' + file)
                    continue
                good_moves.add(moves)
                #print 'ok'
    '''                    
    with open("book_moves.txt", "wb") as f: 
         for file_name in bad_files:
                file = os.path.basename(file_name)
                shutil.copyfile(file_name, 'bad_' + file)
                                
                #f.write(item.encode("GB18030") + "\n")
    #    for item in book_moves:
    #            f.write(item + "\n")
    
    for file_name in dup_files:
        print 'deleting', file_name
        try:
             os.remove(file_name.encode('GBK'))
        except Exception as e:
             print(e)
    '''
    #print 'total ', len(good_moves), 'skiped:',skip_count

#-----------------------------------------------------#


if __name__ == '__main__':
    main(u'..\\games\\对局谱\\')
    #main(u'D:\\09_ChessBook\\1_布局\\')
    #main(u'..\\games\\endgames')
    #main('badmoves')
    #main(u'..\\games\\testgames')
