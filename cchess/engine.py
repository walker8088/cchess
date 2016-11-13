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

import sys,time
from enum import *

from subprocess import PIPE, Popen
from threading import Thread
from Queue import Queue, Empty

from common import *
from utils import *

#-----------------------------------------------------#

#Engine status   
class EngineStatus(Enum):
        BOOTING = 0,
        READY = 1, 
        WAITING = 2, 
        INFO_MOVE = 3, 
        MOVE = 4, 
        DEAD = 5, 
        UNKNOWN = 6, 
        BOARD_RESET = 7
    
ON_POSIX = 'posix' in sys.builtin_module_names

#-----------------------------------------------------#

class UcciEngine(Thread):
    def __init__(self, name = ''):
        super(UcciEngine, self).__init__()
        
        self.engine_name = name
        
        self.daemon  = True
        self.running = False
        
        self.engine_status = None
        self.ids = []
        self.options = []
        
        self.last_fen = None
        self.move_queue = Queue()
    
    '''    
    def on_game_inited(self, move_log) :
        self.init_fen = move_log.fen_after_move
        self.last_fen = move_log.fen_after_move
        self.send_cmd("setoption newgame")
        
    def on_game_started(self, move_side) :
        self.move_side = move_side
        self.go_from(self.init_fen)
       
    def on_game_step_moved(self, move_log) :
        self.move_side = move_log.next_move_side()
        self.last_fen_str = move_log.fen_after_move
        self.go_from(move_log.fen_for_engine())
    
    def on_game_step_moved_undo(self, steps, move_log, next_move_side) :
        self.move_side = next_move_side
        self.last_fen_str = move_log.fen_after_move
        self.go_from(move_log.fen_for_engine())
    '''
    
    def run(self) :
        
        self.running = True
        
        while self.running :
            output = self.pout.readline().strip()
            self.engine_out_queque.put(output)
            
    def handle_msg_once(self) :
        try:  
            output = self.engine_out_queque.get_nowait()
        except Empty:
            return 
    
        if output in ['bye','']: #stop pipe
            self.pipe.terminate()
            return False
            
        self.__handle_engine_out_line(output)
        
        return True
    
    def load(self, engine_path):
    
        self.engine_name = engine_path
        
        try:
            self.pipe = Popen(self.engine_name, stdin=PIPE, stdout=PIPE)#, close_fds=ON_POSIX)
        except OSError:
            return False
            
        time.sleep(0.5)
        
        (self.pin, self.pout) = (self.pipe.stdin,self.pipe.stdout)
        
        self.engine_out_queque = Queue()
        
        self.enging_status = EngineStatus.BOOTING
        self.send_cmd("ucci")
        
        self.start()
        
        while self.enging_status ==  EngineStatus.BOOTING :
            self.handle_msg_once()
            
        return True
        
    def quit(self):
        
        self.send_cmd("quit")
        time.sleep(0.2)
            
    def go_from(self, fen, search_depth = 8):
        
        #pass all out msg first
        while True:
            try:  
                output = self.engine_out_queque.get_nowait()
            except Empty:
                break 
        
        self.send_cmd('position fen ' + fen)
        
        self.last_fen = fen
        
        #if ban_move :
        #        self.send_cmd('banmoves ' + ban_move)
        
        self.send_cmd('go depth  %d' % (search_depth))
        time.sleep(0.2)
         
    def send_cmd(self, cmd_str) :
        
        #print ">>>", cmd_str
        
        try :
            self.pin.write(cmd_str + "\n")
            self.pin.flush()
        except IOError as e :
            print "error in send cmd", e
                
    def __handle_engine_out_line(self, output) :
                
        #print "<<<", output
        
        outputs_list = output.split()
        resp_id = outputs_list[0]
        
        if self.enging_status == EngineStatus.BOOTING:
            if resp_id == "id" :
                    self.ids.append(output)
            elif resp_id == "option" :
                    self.options.append(output)
            if resp_id == "ucciok" :
                    self.enging_status = EngineStatus.READY
    
        elif self.enging_status == EngineStatus.READY:
            
            if resp_id == 'nobestmove':         
                self.move_queue.put(("dead_move", self.move_side))
                
            elif resp_id == 'bestmove':
                if outputs_list[1].lower() == 'null':
                    self.move_queue.put(("dead_move", self.move_side))
                
                else :  
                    move_str = output[9:13]
                    pos_move = str_to_move(move_str)
                    
                    move_info = {}    
                    move_info["fen"] = self.last_fen
                    move_info["move"] = pos_move    
                    
                    self.move_queue.put(("best_move",move_info))
                    
            elif resp_id == 'info':
                #info depth 6 score 4 pv b0c2 b9c7 c3c4 h9i7 c2d4 h7e7
                if outputs_list[1] == "depth":
                    move_info = {}    
                    info_list = output[5:].split()
                    
                    if len(info_list) < 5:
                        return
                        
                    move_info["fen"] = self.last_fen
                    move_info[info_list[0]] =  int(info_list[1]) #depth 6
                    move_info[info_list[2]] =  int(info_list[3]) #score 4
                    
                    move_steps = []
                    for step_str in info_list[5:] :
                        move= str_to_move(step_str)
                        move_steps.append(move)    
                    move_info["move"] = move_steps    
                    
                    self.move_queue.put(("info_move", move_info))
                    
#-----------------------------------------------------#

if __name__ == '__main__':
    engine = UcciEngine()
    engine.load("test\\eleeye\\eleeye.exe")
    for id in engine.ids:
        print id
    for op in engine.options:
        print op
    engine.go_from(FULL_INIT_FEN, 8)
    while True:
            engine.handle_msg_once()
            output = engine.move_queue.get()
            print output
            if output[0] == 'best_move':
                break
    engine.quit()
        
