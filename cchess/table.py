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


import time

from pubsub import pub

from common import *
from engine import *

#-----------------------------------------------------#

class ChessTable(object):
    def __init__(self, parent, board) :
        self.parent =  parent
        self.board = board
        #self.players = [None,None]
        self.history = []

        pub.subscribe(self.on_side_move_request, "side_move_request")
        pub.subscribe(self.on_game_reshow, "game_reshow")
        
    '''    
    def set_players(self, players):
        self.players = players
        
        self.players[RED].side = RED
        self.players[BLACK].side = BLACK
    '''
    
    def new_game(self, fen_str = None) :
    
        self.board.init_board(fen_str)
        
        self.history = []
        self.last_non_killed_fen = self.board.get_fen()         
        self.last_non_killed_moves = []
        
        move_log = MoveLogItem(fen_after_move =  self.board.get_fen(), last_non_killed_fen = self.last_non_killed_fen,  last_non_killed_moves = self.last_non_killed_moves)
        move_log.step_no = 0
        move_log.move_str_zh = u"==开始=="
        self.history.append(move_log)
        
        pub.sendMessage("game_inited", move_log = move_log)
        
    def start_game(self):
        
        self.reshow_mode = False
        
        pub.sendMessage("game_started", move_side = self.board.move_side)
        
        #self.players[RED].start_game()
        #self.players[BLACK].start_game()
        
        #self.players[self.board.move_side].ready_to_move()
        
    def stop_game(self, dead_side = None):
        
        pub.sendMessage("game_stoped", dead_side = dead_side)
        
    def undo_move(self):
        
        if len(self.history) <= 1:
            return
        
        self.history.pop()
        
        move_log = self.history[-1]
        
        self.board.init_board(move_log.fen_after_move)
        
        self.last_non_killed_fen = move_log.last_non_killed_fen         
        self.last_non_killed_moves = move_log.last_non_killed_moves[:]
        
        pub.sendMessage('game_step_moved_undo', steps = 1, move_log = move_log, next_move_side = self.board.move_side)
    
    def on_game_reshow(self, move_log) :
        self.board.init_board(move_log.fen_after_move)
        if move_log.step_no != (len(self.history) -1) :
            self.reshow_mode = True
        else :
            self.reshow_mode = False
            
    def on_side_move_request(self, from_pos,  to_pos) :
        
        if self.reshow_mode :
            return
            
        if not self.board.can_make_move(from_pos, to_pos) :
            #print "chesstable move check error", from_pos, to_pos
            return
        
        fen_str = self.board.get_fen() 
        move_str_zh = self.board.std_move_to_chinese_move(from_pos, to_pos) 
        move_log = self.board.make_log_step_move(from_pos, to_pos) 
        
        self.board.turn_side()
         
        move_log.fen_after_move =  self.board.get_fen()
        move_log.move_str_zh = move_str_zh
        
        if  move_log.killed_man :
            self.last_non_killed_fen = self.board.get_fen()         
            self.last_non_killed_moves = []
        else :
            self.last_non_killed_moves.append(move_log.move_str)
            
        move_log.last_non_killed_fen = self.last_non_killed_fen
        move_log.last_non_killed_moves = self.last_non_killed_moves[:]
        move_log.step_no = len(self.history)
        #print  "move_log", self.last_non_killed_fen,self.last_non_killed_moves
        self.history.append(move_log)
        
        #self.parent.notify_move_from_table(move_log)
        pub.sendMessage('game_step_moved', move_log = move_log)
        #push.sendMessge("ready_to_move", self.board.move_side)
       
        #self.players[self.board.move_side].ready_to_move()
        