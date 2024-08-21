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
import logging
import subprocess
from pathlib import Path
from threading import Thread
from queue import Queue, Empty

#-----------------------------------------------------#
logger = logging.getLogger(__name__)

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
            
    def run_once(self):
        output = self.pout.readline().strip()
        if len(output) > 0:
            self.engine_out_queque.put(output)
            
    def handle_msg_once(self):
        try:
            output = self.engine_out_queque.get_nowait()
        except Empty:
            return

        logger.debug(f"<-- {output}")

        if output in ['bye', '']:  #stop pipe
            self.process.terminate()
            return

        out_list = output.split()
        resp_id = out_list[0]

        move_info = {}

        if self.enging_status == EngineStatus.BOOTING:
            if resp_id == "id":
                self.ids[out_list[1]] = ' '.join(out_list[2:])
            elif resp_id == "option":
                self.options.append(output)
            if resp_id == self.ok_resp():
                self.enging_status = EngineStatus.READY
                move_info["action"] = 'ready'

        elif self.enging_status == EngineStatus.READY:
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
                    move_info['move'] = out_list[1]

            elif resp_id == 'info' and out_list[1] == "depth":
                #info depth 6 score 4 pv b0c2 b9c7  c3c4 h9i7 c2d4 h7e7
                #info depth 1 seldepth 1 multipv 1 score cp -58 nodes 28 nps 14000 hashfull 0 tbhits 0 time 2 pv f5c5
                move_info['action'] = 'info_move'
                info_list = out_list[1:]

                if len(info_list) < 5:
                    return False

                depth_index = info_list.index('depth')
                if depth_index >= 0:
                    move_info['depth'] = info_list[depth_index + 1]

                score_index = info_list.index('score')
                if score_index >= 0:
                    score_type = info_list[score_index + 1]
                    if score_type == 'cp':
                        move_info['score'] = int(info_list[score_index + 2])
                    elif score_type == 'mate':
                        mate_steps = int(info_list[score_index + 2])
                        move_info['mate'] = mate_steps
                        #move_info['score'] = 9999 if mate_steps > 0 else -9999
                    elif score_type == 'lowerbound':
                        move_info['score'] = int(info_list[score_index + 2])
                    elif score_type == 'upperbound':
                        move_info['score'] = int(info_list[score_index + 2])

                move_info["move"] = []
                if 'pv' in info_list:
                    pv_index = info_list.index('pv')
                    move_info["move"] = info_list[pv_index + 1:]

        if len(move_info) > 0:
            self.move_queue.put(move_info)

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
            return False

        time.sleep(0.5)
        
        self.pin = self.process.stdin
        self.pout = self.process.stdout
        self.perr = self.process.stderr
        self.engine_out_queque = Queue()
        self.enging_status = EngineStatus.BOOTING

        #self._send_cmd('test')
        
        if not self._send_cmd(self.init_cmd()):
            self.enging_status = EngineStatus.ERROR
            return False

        self.start()

        #while self.enging_status == EngineStatus.BOOTING:
        #    self.handle_msg_once()

        return True

    def quit(self):

        self._send_cmd("quit")
        time.sleep(0.2)

    def stop_thinking(self):
        self._send_cmd('stop')

    def go_from(self, fen, params={}):
        #pass all output msg first
        self._send_cmd('stop')
        time.sleep(0.1)
        
        while True:
            try:
                _ = self.engine_out_queque.get_nowait()
            except Empty:
                break

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
