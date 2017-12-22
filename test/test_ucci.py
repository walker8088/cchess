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

if __name__ == '__main__':


    win_dict = {ChessSide.RED: u"红胜", ChessSide.BLACK: u"黑胜"}

    game = read_from_xqf('ucci_test1.xqf')
    game.init_board.move_side = ChessSide.RED
    game.print_init_board()
    #game.print_chinese_moves()

    board = game.init_board.copy()

    engine = UcciEngine()
    engine.load("eleeye\\eleeye.exe")
    
    for id in engine.ids:
        print( id)
    for op in engine.options:
        print( op)
    
    dead = False
    while not dead:
        engine.go_from(board.to_fen(), 10)
        while True:
            engine.handle_msg_once()
            if engine.move_queue.empty():
                time.sleep(0.2)
                continue
            output = engine.move_queue.get()
            if output[0] == 'best_move':
                p_from, p_to = output[1]["move"]
                print( board.move(p_from, p_to).to_chinese(),)
                #board.print_board()
                last_side = board.move_side
                board.next_turn()
                break
            elif output[0] == 'dead':
                print( win_dict[last_side])
                dead = True
                break
            elif output[0] == 'draw':
                print( u'引擎议和')
                dead = True
                break
            elif output[0] == 'resign':
                print( u'引擎认输', win_dict[last_side])
                dead = True
                break

    engine.quit()
    time.sleep(0.5)
