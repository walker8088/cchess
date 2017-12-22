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

import os, sys

sys.path.append('..')
from cchess import *

games = set()
repeated = []
bad_results = []
emptys = []
not_full_fen = []

def main(root_path):
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
            if game.next_move == None:
                emptys.append(file_name)
                continue
            if game.init_board.to_short_fen() != 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w':
                not_full_fen.append(file_name)
                print('开局不全')
                continue
            if game.next_move.p_from.x < 5:
                game.mirror()
            #print(game.info)    
            if game.info["Result"] == '*':
                if ('先胜' in file) and ('先负' not in file) and ('先和' not in file):
                    game.info["Result"] == '1-0'
                elif ('先胜' not in file) and ('先负' in file) and ('先和' not in file):
                    game.info["Result"] == '0-1'
                elif ('先胜' not in file) and ('先负' not in file) and ('先和' in file):
                    game.info["Result"] == '1/2-1/2'
                elif ('-胜-' in file) and ('-负-' not in file) and ('-和-' not in file):
                    game.info["Result"] == '1-0'
                elif ('-胜-' not in file) and ('-负-' in file) and ('-和-' not in file):
                    game.info["Result"] == '0-1'
                elif ('-胜-' not in file) and ('-负-' not in file) and ('-和-' in file):
                    game.info["Result"] == '1/2-1/2'
                else:
                    print('Unknown Result')
                    bad_results.append(file_name)
                                       
            #ok = game.verify_moves()
            #if not ok:
            #    print('非法移动')
            #    return
            moves = game.dump_iccs_moves()
            for move_it in moves[:1]:
                move_str  = ''.join(move_it)
                if move_str in games:
                    #if file_name == games[move_str]:
                    #    print('系统错误{}'.format(file_name))
                    #    return
                    print('重复数据')
                    repeated.append(file_name)
                    continue
                games.add(move_str)    
                #games[move_str] = file_name
                
    print('结果未知文件%d局' % (len(bad_results)))    
    for it in bad_results:
        print(it)
    
    print('让子文件%d局' % (len(not_full_fen)))    
    for it in not_full_fen:
        print(it)
       
    print('空文件%d局' % (len(emptys)))    
    for it in emptys:
        print(it)
        try:
           os.remove(it)
        except:
           pass
    
    print('重复数据%d局' % (len(repeated)))    
    for it in repeated:
        print(it)
        try:
            os.remove(it)
        except:
            pass
           
#-----------------------------------------------------#
if __name__ == '__main__':
    main('../game_book/对局谱/')
    