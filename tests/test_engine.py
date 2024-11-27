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
import sys
import time
from pathlib import Path
import logging

import cchess
from cchess import EngineStatus, UcciEngine, UciEngine, EngineManager, EngineErrorException, FenCache, Game, ChessBoard, ChessPlayer, iccs2pos, pos2iccs

result_dict = {'红胜': '1-0', '黑胜': '0-1', '和棋': '1/2-1/2'}
S_RED_WIN = '1-0'
S_BLACK_WIN = '0-1'


def load_move_txt(txt_file):
    with open(txt_file, "rb") as f:
        lines = f.readlines()
    fen = lines[0].strip().decode('utf-8')
    moves = [it.strip().decode('utf-8') for it in lines[1:-1]]
    result = result_dict[lines[-1].strip().decode('utf-8')]
    return (fen, moves, result)

def load_iccs_txt(txt_file):
    with open(txt_file, "r") as f:
        line = f.readline()
    fen, iccs_str, result = line.strip().split(',')
    iccs_list = iccs_str.strip().split(' ')
    result = result.strip()
    return (fen, iccs_list, result)


class TestEngineException():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        
    def teardown_method(self):
        pass

    def test_engine_error(self):
        self.engine = UciEngine()
        ret = self.engine.load("..\\Engine\\pikafish_230408\\pikafishh.exe")
        assert ret == False
        assert self.engine.engine_status == EngineStatus.ERROR

    def test_engine_exception(self):
        self.engine = UciEngine()
        ret = self.engine.load("..\\Engine\\pikafish_230408\\pikafish-vnni512.exe")
        print(ret)
        print(self.engine.engine_status)
        #assert self.engine.engine_status == EngineStatus.ERROR


class TestUcci():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        
    def teardown_method(self):
        pass

    def test_ucci(self):
        
        self.engine = UcciEngine()
        assert self.engine.load("eleeye") is False 

        assert self.engine.load("..\\Engine\\eleeye\\eleeye.exe") is True
        assert self.engine.wait_for_ready() is True
        assert self.engine.engine_status == EngineStatus.READY
        
        fen, moves, result = load_move_txt(Path("data", "ucci_test1_move.txt"))
        game = Game.read_from(Path('data', 'ucci_test1.xqf'))
        game.init_board.move_player = ChessPlayer(cchess.RED)

        assert game.init_board.to_fen() == fen
        assert game.info['result'] == result
        board = game.init_board.copy()

        dead = False
        while not dead:
            self.engine.go_from(board.to_fen(), {'depth': 2})
            while True:
                output = self.engine.get_action()
                if output is None:
                    time.sleep(0.2)
                    continue
                action = output['action']
                if action == 'bestmove':
                    print(output)
                    iccs = output["move"]
                    move_txt = board.move_iccs(iccs).to_text()
                    print(move_txt)
                    assert move_txt == moves.pop(0)
                    last_player = board.move_player
                    board.next_turn()
                    break
                elif action == 'dead':
                    #print(output)
                    if board.move_player == cchess.RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result == S_RED_WIN
                    dead = True
                    break
                elif action == 'draw':
                    dead = True
                    break
                
            self.engine.stop_thinking()
                
        self.engine.quit()

        time.sleep(0.5)

class TestUci():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        self.engine = UciEngine()
        
        ret = self.engine.load("..\\Engine\\pikafish_230408\\pikafish.exe")
        assert ret is True
        assert self.engine.wait_for_ready() is True
        assert self.engine.engine_status == EngineStatus.READY
        
    def teardown_method(self):
        pass

    def test_uci_endgame(self):
        
        fen, moves, result = load_iccs_txt(Path("data", "uci_test_move.txt"))
        #print(moves)
        board = ChessBoard(fen)

        dead = False
        while not dead:
            self.engine.go_from(board.to_fen(), {'depth': 15})
            while True:
                output = self.engine.get_action()
                if output is None:
                    time.sleep(0.2)
                    continue
                #print(output)
                action = output['action']
                if action == 'bestmove':
                    print(output)
                    iccs = output["move"]
                    move = board.move_iccs(iccs)
                    print(move.to_text()) 
                    assert move.to_iccs() == moves.pop(0)
                    last_player = board.move_player
                    board.next_turn()
                    break
                elif action == 'info_move':
                    #print(output)
                    pass
                    
                elif action == 'dead':
                    #print(output)
                   
                    if board.move_player == cchess.RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result  == S_RED_WIN
                    dead = True
                    break
                elif action == 'draw':
                    dead = True
                    break
                
            self.engine.stop_thinking()

    def test_uci_game(self):
        
        board = ChessBoard(cchess.FULL_INIT_FEN)

        #self.engine.go_from(board.to_fen(), {'depth': 15})
        steps = 1
        while steps < 10:
            self.engine.go_from(board.to_fen(), {'depth': 15})
            while True:
                output = self.engine.get_action()
                if output is None:
                    time.sleep(0.2)
                    continue
                action = output['action']
                if action == 'bestmove':
                    steps += 1
                    print(output)
                    iccs = output["move"]
                    move = board.move_iccs(iccs)
                    print(move.to_text()) 
                    board.next_turn()
                    break
                elif action == 'info_move':
                    #print(output)
                    pass
                    
            self.engine.stop_thinking()
        
        self.engine.quit()

        time.sleep(0.5)

    
class TestEngineManager():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        self.mgr = EngineManager()
        
    def teardown_method(self):
        self.mgr.quit()

    def test_game_score(self):
        options ={'LU_Output': 'false', 'Threads ':'8', 'Hash ':'2000'}
        
        go_params = {'depth': 15}
        self.mgr.load_uci("..\\Engine\\pikafish_230408\\pikafish.exe", options, go_params)
        self.mgr.get_game_file_score(Path('data', '030-黄松轩先胜冯敬如.XQF'))