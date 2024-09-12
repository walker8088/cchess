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
import re  
import time
import enum
import logging
import subprocess
from pathlib import Path
from threading import Thread
from queue import Queue, Empty
  

#-----------------------------------------------------#
logger = logging.getLogger(__name__)

  
#-----------------------------------------------------#
def parse_engine_info_to_dict(s):  
    result = {}  
    current_key = None  
    for part in s.split():  
        if current_key is None and part != 'score': #, 'lowerbound', 'higherbound']:  
            current_key = part  
    
        elif current_key is not None and part == 'score':  
            current_key
            continue  
        
        elif current_key is not None:  
            result[current_key] = part  
            current_key = None  
      
    # 注意：这个简单的实现没有处理'cp'后面没有值的情况，或者字符串格式不正确的情况  
    # 在实际应用中，你可能需要添加更多的错误检查和处理逻辑  
  
    # 由于'cp'后面通常跟着值，但在这个例子中我们将其视为值的一部分，  
    # 所以我们不需要对'cp'进行特殊处理（除了上面的跳过逻辑）  
    # 但是，如果'cp'后面没有值，或者格式经常变化，你可能需要更复杂的逻辑  
  
    # 示例中'cp'已经隐含地作为'score'值的一部分处理了，所以不需要额外操作  
    # 但如果'cp'应该作为一个独立的键或标记存在，你需要调整逻辑来适应  
  
    # 返回结果  
    return result  
  
# 示例字符串  
#s = "depth 1 seldepth 1 multipv 1 score cp -58 nodes 28 nps 14000 hashfull 0 tbhits 0 time 2 pv f5c5"  
# 调用函数并打印结果  
# 注意：这个实现不会将'cp'作为独立的键，而是将其视为'score'值的一部分  
#result = parse_special_string_to_dict(s)  
# 由于'cp'被视为'score'值的一部分，这里我们不会直接看到'cp'，但'-58'将是'score'的值  
#print(result)  # 输出可能不包括'cp'作为独立键，但'score'的值将是'-58'

#-----------------------------------------------------#
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
#-----------------------------------------------------#
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
    def handle_msg_once(self):
        
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
                #print("GOT", resp_id)
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
                    move_info['move'] = resp_dict.pop('bestmove')
                    move_info.update(resp_dict)
                    
            elif resp_id == 'info' and out_list[1] == "depth":
                #info depth 6 score 4 pv b0c2 b9c7  c3c4 h9i7 c2d4 h7e7
                #info depth 1 seldepth 1 multipv 1 score cp -58 nodes 28 nps 14000 hashfull 0 tbhits 0 time 2 pv f5c5
               
                move_info['action'] = 'info_move'
                move_info["move"] = []
                
                pv_index = output.find(' pv ')
                if pv_index > 0:
                    move_info["move"] = output[pv_index+4:].split(' ')
                
                resp_dict = parse_engine_info_to_dict(output[5:pv_index+1])
                if 'cp' in resp_dict:
                    move_info['score'] = resp_dict.pop('cp')
                move_info.update(resp_dict)
                
        if len(move_info) > 0:
            self.move_queue.put(move_info)
        
        return True
        
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
            logger.warning(f"load engine {engine_path} ERROR: {e}")
            self.engine_status = EngineStatus.ERROR
            return False

        time.sleep(0.5)
        
        self.pin = self.process.stdin
        self.pout = self.process.stdout
        self.perr = self.process.stderr
        self.engine_out_queque = Queue()
        self.engine_status = EngineStatus.BOOTING

        #self._send_cmd('test')
        
        if not self._send_cmd(self.init_cmd()):
            self.engine_status = EngineStatus.ERROR
            return False

        self.start()

        #while self.engine_status == EngineStatus.BOOTING:
        #    self.handle_msg_once()

        return True

    def quit(self):
        self._send_cmd("quit")
        time.sleep(0.2)

    def stop_thinking(self):
        self._send_cmd('stop')
        
        time.sleep(0.1)
        self.handle_msg_once()
        time.sleep(0.1)
        self.handle_msg_once()
        time.sleep(0.1)
        self.handle_msg_once()
        
    def go_from(self, fen, params={}):
        
        self._send_cmd(f'position fen {fen}')
        param_list = [f"{key} {value}" for key, value in params.items()]
        go_cmd = "go " + ' '.join(param_list)
        
        ok = self._send_cmd(go_cmd)
        if not ok:
            return False
            
        self.last_fen = fen
        self.last_go = go_cmd
        
        return True
        
    def set_option(self, name, value):
        cmd = f'setoption name {name} value {value}'
        self._send_cmd(cmd)

    def _send_cmd(self, cmd_str):

        logger.debug(f"--> {cmd_str}")

        try:
            cmd_bytes = f'{cmd_str}\r\n'
            self.pin.write(cmd_bytes)
            self.pin.flush()
        except Exception as e:
            logger.warning(f"Send cmd [{cmd_str}] ERROR: {e}")
            return False

        return True


#-----------------------------------------------------#
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
