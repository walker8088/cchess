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

#from .exception import CChessException
#from .board import ChessBoard

#-----------------------------------------------------#

def read_from_cbl(file_name):

    with open(file_name, "rb") as f:
        contents = f.read()

    magic, _i1, lib_name = struct.unpack("<16s48s512s",  contents[:576])
    print(magic.decode("GB18030"))
    print(lib_name[:19].decode("utf-8"))
    
    if magic != b"XQ":  
        return None

#read_from_cbl('D:\\01_MyRepos\\cchess\\tests\\data\\1956年全国象棋锦标赛93局.CBL')
