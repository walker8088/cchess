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

import struct
from .read_cbr import read_from_cbr_buffer, CODING_PAGE 


#-----------------------------------------------------#
def read_from_cbl(file_name):

    with open(file_name, "rb") as f:
        contents = f.read()

    bmagic, _i1, book_count, blib = struct.unpack("<16s44si512s",  contents[:576])
    
    if bmagic != b'CCBridgeLibrary\x00':  
        return None
    
    lib_info = {}    
    lib_name = blib.decode(CODING_PAGE)
    
    lib_info['name'] = lib_name
    lib_info['games'] = []
    
    index = 101952
    count = 0
    while index < len(contents):
        book_buffer = contents[index:]
        game = read_from_cbr_buffer(book_buffer)
        lib_info['games'].append(game)
        count += 1
        index += 4096
        print(count+1, game.info['title'])
        
    return lib_info
    
#read_from_cbl('D:\\01_MyRepos\\cchess\\tests\\data\\1956年全国象棋锦标赛93局.CBL')