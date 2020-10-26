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

import os, sys, time
from enum import *

import subprocess

from threading import Thread
from queue import Queue, Empty

from .board import *
from .move import *

#-----------------------------------------------------#
#Engine status
class EngineStatus(IntEnum):
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
class UcciEngine(Thread):
    def __init__(self, name=''):
        super().__init__()

        self.engine_name = name

        self.daemon = True
        self.running = False

        self.engine_status = None
        self.ids = []
        self.options = []

        self.last_fen = None
        self.move_queue = Queue()

    def run(self):

        self.running = True

        while self.running:
            output = self.pout.readline().strip().decode('utf-8')
            self.engine_out_queque.put(output)

    def handle_msg_once(self):
        try:
            output = self.engine_out_queque.get_nowait()
        except Empty:
            return False

        if output in ['bye', '']:  #stop pipe
            self.pipe.terminate()
            return False

        #print( "<<<", output)

        outputs_list = output.split()
        resp_id = outputs_list[0]

        if self.enging_status == EngineStatus.BOOTING:
            if resp_id == "id":
                self.ids.append(output)
            elif resp_id == "option":
                self.options.append(output)
            if resp_id == "ucciok":
                self.enging_status = EngineStatus.READY

        elif self.enging_status == EngineStatus.READY:

            if resp_id == 'nobestmove':
                self.move_queue.put(("dead", {'fen': self.last_fen}))

            elif resp_id == 'bestmove':
                #print(output)
                if outputs_list[1] == 'null':
                    self.move_queue.put(("dead", {'fen': self.last_fen}))
                #elif outputs_list[-1] == 'draw':
                #    self.move_queue.put(("draw", {'fen': self.last_fen}))
                #elif outputs_list[-1] == 'resign':
                #    self.move_queue.put(("resign", {'fen': self.last_fen}))
                else:
                    move_str = output[9:13]
                    pos_move = Move.from_iccs(move_str)

                    move_info = {}
                    move_info["fen"] = self.last_fen
                    move_info["move"] = pos_move

                    self.move_queue.put(("best_move", move_info))

            elif resp_id == 'info':
                #info depth 6 score 4 pv b0c2 b9c7 c3c4 h9i7 c2d4 h7e7
                if outputs_list[1] == "depth":
                    move_info = {}
                    info_list = output[5:].split()

                    if len(info_list) < 5:
                        return

                    move_info["fen"] = self.last_fen
                    move_info[info_list[0]] = int(info_list[1])  #depth 6
                    move_info[info_list[2]] = int(info_list[3])  #score 4

                    move_steps = []
                    for step_str in info_list[5:]:
                        move = Move.from_iccs(step_str)
                        move_steps.append(move)
                    move_info["move"] = move_steps

                    self.move_queue.put(("info_move", move_info))

        return True

    def load(self, engine_path):

        self.engine_name = engine_path

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.pipe = subprocess.Popen(
                self.engine_name, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                startupinfo=startupinfo)  #, close_fds=ON_POSIX)
        except OSError:
            return False

        time.sleep(0.5)

        (self.pin, self.pout) = (self.pipe.stdin, self.pipe.stdout)

        self.engine_out_queque = Queue()

        self.enging_status = EngineStatus.BOOTING
        self._send_cmd("ucci")

        self.start()

        while self.enging_status == EngineStatus.BOOTING:
            self.handle_msg_once()

        return True

    def quit(self):

        self._send_cmd("quit")
        time.sleep(0.2)

    def go_from(self, fen, search_depth=8):

        #pass all output msg first
        #self._send_cmd('stop')
        while True:
            try:
                output = self.engine_out_queque.get_nowait()
            except Empty:
                break

        self._send_cmd('position fen ' + fen)

        self.last_fen = fen

        self._send_cmd('go depth  %d' % (search_depth))
        time.sleep(0.2)

    def stop_thinking(self):
        self._send_cmd('stop')
        while True:
            try:
                output = self.engine_out_queque.get_nowait()
            except Empty:
                continue
            outputs_list = output.split()
            resp_id = outputs_list[0]
            if resp_id in ['bestmove', 'nobestmove']:
                return

    def _send_cmd(self, cmd_str):

        #print(">>>", cmd_str)

        try:
            cmd_bytes = (cmd_str + "\n").encode('utf-8')
            self.pin.write(cmd_bytes)
            self.pin.flush()
        except IOError as e:
            print("error in send cmd", e)

    '''
    def preset_best_move(self, iccs_move_str):

        pos_move = Move.from_iccs(iccs_move_str)

        move_info = {}
        move_info["fen"] = self.last_fen
        move_info["move"] = pos_move

        self.move_queue.put(("best_move", move_info))
    '''

#-----------------------------------------------------#
