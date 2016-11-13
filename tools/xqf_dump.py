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

import os
import base64
import struct, copy

from cchess import *
                
#-----------------------------------------------------#
if __name__ == '__main__':
    
    loader = XQFLoader()
    file_name = sys.argv[1]
    book = loader.load(file_name)
    book.dump_info()
    print book.init_fen
    print book.annotation    
    print 'verified', book.verify_moves()
    moves = book.dump_chinese_moves()
    for move_it in moves:
        print move_it
    