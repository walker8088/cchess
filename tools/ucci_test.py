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

import sys, time

sys.path.append('..')
from cchess import *

win_dict = { ChessSide.RED : u"红胜", ChessSide.BLACK : u"黑胜" }

def do_game(fen, engine):
    
    board = Chessboard(fen)
    board.print_board()
    
    dead = False
    while not dead:    
        engine.go_from(board.to_fen())
        while True:
            engine.handle_msg_once()
            if engine.move_queue.empty():
                time.sleep(0.2)
                continue
            output = engine.move_queue.get()
            if output[0] == 'best_move':
                p_from, p_to = output[1]["move"]
                if not board.is_valid_move(p_from, p_to):
                        print "move error", p_from, p_to
                        dead = True
                        break
                print board.move(p_from, p_to).to_chinese(),
                #board.print_board()
                last_side = board.move_side
                board.next_turn()
                break
            elif output[0] == 'dead_move':
                print win_dict[last_side]
                dead = True
                break           
    return last_side
    
def do_end_games(epd_file, start_pos) :
	engine = UcciEngine()
        engine.load("..\\cchess\\test\\eleeye\\eleeye.exe")
    
	lines = open(epd_file).readlines()
	i = 0
	for line in lines[start_pos:] :
		print "challenge ", start_pos + i
                
		do_game(line, engine)
		i += 1	
        engine.quit()
        time.sleep(0.5)        
	
def main():
    do_end_games("endgames.epd", 0)
	
#-----------------------------------------------------#
if __name__ == '__main__':
    main()
   