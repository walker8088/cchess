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

#-----------------------------------------------------#
def load_games(root_path):
    good_moves = Set()
    
    loader = XQFLoader()
    
    for root, paths, files in os.walk(root_path):
        for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext != '.xqf':
                        continue
                file_name = os.path.join(root, file)
                print file_name.encode('GB18030')
                game = loader.load(file_name)
                if not game:
                        print 'None game at file', file_name
                if not game.verify_moves():
                        print 'Bad move at file', file_name
                        
                game.init_board.print_board()
                game.print_chinese_moves(3)
                
                moves = game.dump_chinese_moves()
                for it in moves:
                        line = ' '.join(it)
                        print line
                        good_moves.add(line)
                        
                
    return good_moves

#-----------------------------------------------------#    
def find_bad_games(root_path, good_moves):
    
    loader = XQFLoader()
    
    for root, paths, files in os.walk(root_path):
        for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext != '.xqf':
                        continue
                file_name = os.path.join(root, file)
                game = loader.load(file_name)
                if not game:
                        print 'None game at file', file_name
                if not game.verify_moves():
                        print 'Bad move at file', file_name
                        
                board_txt = game.dump_init_board()
                
                #print
                #for line in board_txt:
                #        print line
                #print   
                
                moves = game.dump_chinese_moves()
                if len(moves) > 1:
                        #print "Multi move at file", file_name 
                        #continue
                        pass
                        
                for it in moves:
                        line = ' '.join(it)
                        #print line
                        if line not in good_moves:
                               line2 = ' '.join(it[:-4])
                               find = False
                               for it2  in good_moves:
                                        if line2 in it2:
                                             #print "matched"
                                             find = True
                               if not find:              
                                    print 'Diff game at file', file_name 
                                
#-----------------------------------------------------#
def main():
        good_moves = load_games(u'..\\games\\残局谱\\适情雅趣550局')
        find_bad_games(u'..\\games\\残局谱\\适情雅趣360局', good_moves)
        #good_moves = load_games(u'..\\games\\testgames\\1')
        #find_bad_games(u'..\\games\\testgames\\2', good_moves)
        
#-----------------------------------------------------#
if __name__ == '__main__':
    main()
    
    