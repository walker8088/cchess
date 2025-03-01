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
import time
import enum
import json
import logging
import subprocess
from pathlib import Path
from threading import Thread
from queue import Queue, Empty
 
from .common import get_move_color, fen_mirror, iccs_mirror, iccs_list_mirror, RED, FULL_INIT_FEN

from .game import Game
from .board import ChessBoard
from .exception import EngineErrorException
  
#-----------------------------------------------------#
logger = logging.getLogger(__name__)

#-----------------------------------------------------#
def is_int(s):
    if s.isdigit():
        return True
    if s[0] == '-':
        if s[1:].isdigit():
            return True
    return False
    
def parse_engine_info_to_dict(s):  
    result = {}  
    current_key = None
    info = s.split()
    for index, part in enumerate(info): 
        if part in ['info', 'cp', 'lowerbound', 'upperbound']: #略过这些关键字,不影响分析结果
            continue
        elif part == 'pv': ##遇到pv就是到尾了，剩下的都是招法
            result['moves'] = info[index+1:]
            break
            
        if current_key is None:  
            current_key = part
            #替换key
            if current_key == 'bestmove':
                current_key = 'move'
        else:    
            if part == 'mate': # score mate 这样的字符串，后滑一个关键字 
                current_key = part
                continue  
            else:
                if is_int(part):
                    result[current_key] = int(part)  
                else:
                    result[current_key] = part  
                current_key = None  

    return result  

#------------------------------------------------------------------------------
#Engine status
class EngineStatus(enum.IntEnum):
    ERROR = 0,
    BOOTING = 1,
    READY = 2,
    WAITING = 3,
    INFO_MOVE = 4,
    MOVE = 5,
    DEAD = 6,
    UNKNOWN = 7,
    BOARD_RESET = 8


#ON_POSIX = 'posix' in sys.builtin_module_names

#------------------------------------------------------------------------------
class Engine(Thread):
    def __init__(self, exec_path=''):
        super().__init__()

        self.engine_exec_path = exec_path

        self.daemon = True
        self.running = False

        self.engine_status = None
        self.ids = {}
        self.options = []

        self.last_fen = None
        self.move_queue = Queue()

    def init_cmd(self):
        return ""
    
    def load(self, engine_path):

        self.engine_exec_path = engine_path

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(self.engine_exec_path,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            startupinfo=startupinfo,
                                            cwd=Path(
                                                self.engine_exec_path).parent,
                                             text=True)
        except Exception as e:
            logger.error(f"load engine {engine_path} ERROR: {e}")
            self.engine_status = EngineStatus.ERROR
            return False

        time.sleep(0.5)
        
        self.pin = self.process.stdin
        self.pout = self.process.stdout
        self.perr = self.process.stderr
        self.engine_out_queque = Queue()
        self.engine_status = EngineStatus.BOOTING

        self._send_cmd(self.init_cmd())
        
        self.start()
        
        return True

    def go_from(self, fen, params={}):
        
        self._send_cmd(f'position fen {fen}')
        param_list = [f"{key} {value}" for key, value in params.items()]
        go_cmd = "go " + ' '.join(param_list)
        
        ok = self._send_cmd(go_cmd)
        if not ok:
            return False
            
        self.last_fen = fen
        self.last_go = go_cmd
        self.score_dict = {}
        
        return True

    def get_action(self):
        self._handle_msg_once()
        if self.move_queue.empty():
            return None           
        return self.move_queue.get()
                
    def set_option(self, name, value):
        cmd = f'setoption name {name} value {value}'
        self._send_cmd(cmd)
    
    def _send_cmd(self, cmd_str):

        logger.debug(f"--> {cmd_str}")
        
        if self.process.returncode is not None:
            self.engine_status = EngineStatus.ERROR
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
        
        try:
            cmd_bytes = f'{cmd_str}\r\n'
            self.pin.write(cmd_bytes)
            self.pin.flush()
        except Exception as e:
            logger.error(f"Send cmd [{cmd_str}] ERROR: {e}")
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
            
        if self.process.returncode is not None:
            self.engine_status = EngineStatus.ERROR
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
         
        return True


    def wait_for_ready(self, timeout = 10):
        
        start_time = time.time()
        
        while True:
            self._handle_msg_once()
            if self.engine_status == EngineStatus.READY:
                return True
                
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.2)
        
        return False
        
    def quit(self):
        self._send_cmd("quit")
        time.sleep(0.2)

    def stop_thinking(self):
        self._send_cmd('stop')
        time.sleep(0.1)
        self.get_action()
        time.sleep(0.1)
        self.get_action()
        
    def run(self):

        self.running = True

        while self.running:
            self.run_once()
    
    #run_once 在线程中运行        
    def run_once(self):
        #readline 会阻塞
        output = self.pout.readline().strip()
        if len(output) > 0:
            self.engine_out_queque.put(output)
    
    #handle_msg_once 在前台运行        
    def _handle_msg_once(self):
        
        try:
            output = self.engine_out_queque.get_nowait()
        except Empty:
            return False

        logger.debug(f"<-- {output}")

        if output in ['bye', '']:  #stop pipe
            self.process.terminate()
            return True

        out_list = output.split()
        resp_id = out_list[0]

        move_info = {}

        if self.engine_status == EngineStatus.BOOTING:
            if resp_id == "id":
                self.ids[out_list[1]] = ' '.join(out_list[2:])
            elif resp_id == "option":
                self.options.append(output)
            if resp_id == self.ok_resp():
                self.engine_status = EngineStatus.READY
                move_info["action"] = 'ready'

        elif self.engine_status == EngineStatus.READY:
            move_info["fen_engine"] = self.last_fen
            move_info['raw_msg'] = output
            move_info["action"] = 'info'

            if resp_id == 'nobestmove':
                move_info["action"] = 'dead'
            elif resp_id == 'bestmove':
                if out_list[1] in ['null', 'resign', '(none)']:
                    move_info["action"] = 'dead'
                elif out_list[1] == 'draw':
                    move_info["action"] = 'draw'
                else:
                    move_info["action"] = 'bestmove'
                    resp_dict = parse_engine_info_to_dict(output)
                    move_info.update(resp_dict)
                    move_key = move_info['move']
                    if move_key in self.score_dict:
                        for key in ['score', 'mate', 'moves', 'seldepth', 'time']:
                            if key in self.score_dict[move_key]:
                                move_info[key] = self.score_dict[move_key][key]
                        
            elif resp_id == 'info' and out_list[1] == "depth":
                #info depth 6 score 4 pv b0c2 b9c7  c3c4 h9i7 c2d4 h7e7
                #info depth 1 seldepth 1 multipv 1 score cp -58 nodes 28 nps 14000 hashfull 0 tbhits 0 time 2 pv f5c5
                move_info['action'] = 'info_move'
                resp_dict = parse_engine_info_to_dict(output)               
                move_info.update(resp_dict)
                if 'moves' in move_info:
                    move_key = move_info['moves'][0]
                    self.score_dict[move_key] = move_info
                elif 'currmove' in move_info:
                    #暂时不处理
                    pass
                else:
                    logger.info(move_info)
                    
        if len(move_info) > 0:
            self.move_queue.put(move_info)
        
        return True
        
#------------------------------------------------------------------------------
class UcciEngine(Engine):
    def init_cmd(self):
        return "ucci"

    def ok_resp(self):
        return "ucciok"


class UciEngine(Engine):
    def init_cmd(self):
        return "uci"

    def ok_resp(self):
        return "uciok"

#------------------------------------------------------------------------------
def action_mirror(action):
    for key in action:
        if key in ['move', 'ponder']:
            action[key] = iccs_mirror(action[key])
        if key in ['moves']:
            action[key] = iccs_list_mirror(action[key])


#------------------------------------------------------------------------------
class FenCache():
    def __init__(self):
        self.fen_dict = {}
        self.cache_file = ''
        self.need_save = False
        
    def get(self, fen):
        if fen in self.fen_dict:
            return (self.fen_dict[fen], '')
        
        f_mirror = fen_mirror(fen)
        if f_mirror in self.fen_dict:
            return (self.fen_dict[f_mirror], 'mirror')
        
        return (None, None)
    
    def get_best_action(self, fen):
        move_color = get_move_color(fen)
        
        info, state = self.get(fen)
        if info is None:
            return None
            
        actions = [v for v in sorted(info.values(), key=lambda item: item['score'])]
        
        if move_color == RED:
            act = actions[0]
        else:
            act = actions[-1]
        
        if state == 'mirror':
            #print('mirror')
            return action_mirror(act)        
        
        return act
        
    def save_action(self, fen, action):
        
        iccs = action['move']
        if fen in self.fen_dict:
            self.fen_dict[fen][iccs] = action
            return True
            
        f_mirror = fen_mirror(fen)
        i_mirror = iccs_mirror(iccs)
        if f_mirror in self.fen_dict:    
            self.fen_dict[f_mirror][i_mirror] = action
            return True
       
        self.fen_dict[fen]= {}
        self.fen_dict[fen][iccs] = action
        self.need_save = True
        
        return True
                        
    def load(self, cache_file):
        
        if not Path(cache_file).is_file():
            self.fen_dict = {}
        else:   
            with open(cache_file, 'r') as f:
                self.fen_dict = json.load(f)
        
        self.cache_file = cache_file
        self.need_save = False
        
    def save(self): 
        with open(self.cache_file, 'w') as f:
            json.dump(self.fen_dict, f)
        self.need_save = False
        
#------------------------------------------------------------------------------
class EngineManager():
    def __init__(self, fen_cache = FenCache()):
        self.engine = None
        self.cache = fen_cache
        
    def load_uci(self, engine_exec, options, go_params):
        self.engine = UciEngine()
        return self._load(engine_exec, options, go_params)
        
    def load_ucci(self, engine_exec, options, go_params):
        self.engine = UcciEngine()
        return self._load(engine_exec, options, go_params)
        
    def _load(self, engine_exec, options, go_params):
        
        ok = self.engine.load(engine_exec)
        if not ok:
            return False
        
        ok = self.engine.wait_for_ready()
        if not ok:
            return False
        
        #self.engine_options = options
        for name, value in options.items():
            self.engine.set_option(name, value)
            
        self.go_params = go_params
        
        return True
        
    def get_best_cache(self, fen):
        return self.cache.get_best_action(fen)
        
    def get_fen_score(self, fen):
        action = self.get_best_cache(fen)
        return action or self.run_engine(fen)
        
    def run_engine(self, fen):
  
        board = ChessBoard(fen)   
        self.engine.go_from(fen, self.go_params)
        
        #print('go:', fen, self.go_params)
        while True:
            action = self.engine.get_action()
            
            if action is None:
                time.sleep(0.2)
                continue
                
            action_id = action['action']
            if action_id == 'info_move':
                #print(action['raw_msg'])
                pass
            elif action_id in ['dead', 'draw']:
                print(action['raw_msg'])
                action['score'] = 30000
                action['mate'] = 0
                return action
                
            elif action_id == 'bestmove':
                iccs = action["move"]
                move = board.move_iccs(iccs)
                if move is None:
                    continue
                   
                board.next_turn()
                #fen_next = board.to_fen()
                #action['move_text'] = move.to_text()
                
                #本步的得分是下一步的负值
                for key in ['score', 'mate']:
                    if key in action:
                        action[key] = -action[key]
                        
                #再处理出现mate时，score没分的情况
                if ('score' not in action) and ('mate' in action):
                    mate_v = action['mate']
                    mate_flag = 1 if mate_v > 0 else -1
                    action['score'] = (30000-abs(mate_v)) * mate_flag
     
                self.cache.save_action(fen, action)    
                
                return action
   
    def quit(self):
        self.engine.quit()
        time.sleep(0.5)

#------------------------------------------------------------------------------
