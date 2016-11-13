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

from common import *
from engine import *

#-----------------------------------------------------#

class ChessPlayer(object):
    def __init__(self, master) :
        self.master = master
        self.board = master.board
        self.side = None

    def ready_to_move(self) :
        pass

    def get_next_move(self) :
        pass
                
'''
#-----------------------------------------------------#

class EngineChessPlayer(ChessPlayer) :
    def __init__(self, master, engine_name) :
        super(EngineChessPlayer, self).__init__(master)
        self.engine = UcciEngine(engine_name)
        self.engine.load()

    def ready_to_move(self) :
        fen_str = self.board.get_fen()
        self.engine.go_from(fen_str)
    
    def get_next_move(self) :   
        return self.engine.get_next_move()
    
    def start_game(self) :
        self.engine.start_game()
            
    def stop_game(self) :
        self.engine.stop_game()
'''    
#-----------------------------------------------------#

class UiChessPlayer(ChessPlayer) :
    def __init__(self, master) :
        super(UiChessPlayer, self).__init__(master)
        self.move_queue = Queue()
        self.engine = None
    
    def bind_engine(self,  engine):
        self.engine = engine
            
    def start_game(self) :
        self.board.set_hook_move(self.side, self.on_move_chessman)
    
    def stop_game(self) :
        self.board.set_hook_move(self.side, None)
            
    def ready_to_move(self) :
        pass
        
    def on_move_chessman(self, p_from, p_to) :
        if self.board.can_make_move(p_from, p_to) :
            self.move_queue.put((MOVE, (p_from, p_to)))
                    
    def get_next_move(self) :   
    
        # UI Player 绑定到Engine的时候，需要从engine取执行指令        
        if self.engine:
            move = self.engine.get_next_move()
            if move:
                return move    
        #
        try:
            move = self.move_queue.get_nowait()
        except Empty:
            return None
        
        return move
        