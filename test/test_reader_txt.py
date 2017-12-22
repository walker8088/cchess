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

import sys

sys.path.append('..')

from cchess import *

#-----------------------------------------------------#
if __name__ == '__main__':

    pos_s = '9999999949399920109981999999993129629999409999997109993847999999'
    move_s = '31414050414050402032'  #'77477242796770628979808166658131192710222625120209193136797136267121624117132324191724256755251547431516212226225534222434532454171600105361545113635161636061601610'

    game = read_from_txt(moves_txt=move_s, pos_txt=pos_s)
    board_txt = game.dump_init_board()
    #print(game.init_board.to_fen())
    print()
    for line in board_txt:
        print(line)
    print()

    moves = game.dump_chinese_moves()
    for it in moves[0]:
        print(it)
