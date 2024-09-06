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

from cchess import UcciEngine, UciEngine, Game, ChessPlayer, RED, BLACK, iccs2pos, pos2iccs

result_dict = {'红胜': '1-0', '黑胜': '0-1', '和棋': '1/2-1/2'}
S_RED_WIN = '1-0'
S_BLACK_WIN = '0-1'

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s", level = logging.DEBUG)

def load_move_txt(txt_file):
    with open(txt_file, "rb") as f:
        lines = f.readlines()
    fen = lines[0].strip().decode('utf-8')
    moves = [it.strip().decode('utf-8') for it in lines[1:-1]]
    result = result_dict[lines[-1].strip().decode('utf-8')]
    return (fen, moves, result)


class TestUCCI_BAD():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))

    def teardown_method(self):
        pass

    def test_ucci(self):
        self.engine = UcciEngine()
        assert self.engine.load("eleeye") is False 

        fen, moves, result = load_move_txt(Path("data", "ucci_test1_move.txt"))
        game = Game.read_from(Path('data', 'ucci_test1.xqf'))
        game.init_board.move_player = ChessPlayer(RED)


class TestUcci():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        self.engine = UcciEngine()
        
    def teardown_method(self):
        pass

    def test_ucci(self):
        ret = self.engine.load("bin\\eleeye")
        assert ret == True
        
        for i in range(10):
            self.engine.handle_msg_once()
            time.sleep(0.3)
    
        print(self.engine.engine_status)
    
        fen, moves, result = load_move_txt(Path("data", "ucci_test1_move.txt"))
        game = Game.read_from(Path('data', 'ucci_test1.xqf'))
        game.init_board.move_player = ChessPlayer(RED)

        assert game.init_board.to_fen() == fen
        assert game.info['result'] == result
        board = game.init_board.copy()

        dead = False
        while not dead:
            self.engine.stop_thinking()
            self.engine.go_from(board.to_fen(), {'depth': 8})
            while True:
                self.engine.handle_msg_once()
                if self.engine.move_queue.empty():
                    time.sleep(0.2)
                    continue
                output = self.engine.move_queue.get()
                print(output)
                action = output['action']
                if action == 'bestmove':
                    p_from, p_to = iccs2pos(output["move"])
                    move_str = board.move(p_from, p_to).to_text()
                    assert move_str == moves.pop(0)
                    last_player = board.move_player
                    board.next_turn()
                    break
                elif action == 'dead':
                    if board.move_player == RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result == S_RED_WIN
                    dead = True
                    break
                elif action == 'draw':
                    dead = True
                    break
                elif action == 'resign':
                    if board.move_player == RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result == S_RED_WIN
                    dead = True
                    break

        self.engine.quit()

        time.sleep(0.5)

'''
class TestUci():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
        self.engine = UciEngine()
        
    def teardown_method(self):
        pass

    def test_uci(self):
        ret = self.engine.load("bin\\pikafish")
        assert ret is True
    
        for i in range(10):
            self.engine.handle_msg_once()
            time.sleep(0.3)
    
        fen, moves, result = load_move_txt(Path("data", "ucci_test1_move.txt"))
        game = Game.read_from(Path('data', 'ucci_test1.xqf'))
        game.init_board.move_player = ChessPlayer(RED)

        assert game.init_board.to_fen() == fen
        assert game.info['result'] == result
        board = game.init_board.copy()

        dead = False
        while not dead:
            self.engine.stop_thinking()
            self.engine.go_from(board.to_fen(), {'depth': 10})
            while True:
                self.engine.handle_msg_once()
                if self.engine.move_queue.empty():
                    time.sleep(0.2)
                    continue
                output = self.engine.move_queue.get()
                print(output)
                action = output['action']
                if action == 'bestmove':
                    p_from, p_to = iccs2pos(output["move"])
                    move_str = board.move(p_from, p_to).to_text()
                    #print(move_str) #assert move_str == moves.pop(0)
                    last_player = board.move_player
                    board.next_turn()
                    break
                elif action == 'dead':
                    if board.move_player == RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result == S_RED_WIN
                    dead = True
                    break
                elif action == 'draw':
                    dead = True
                    break
                elif action == 'resign':
                    if board.move_player == RED:
                        assert result == S_BLACK_WIN
                    else:
                        assert result == S_RED_WIN
                    dead = True
                    break

        self.engine.quit()

        time.sleep(0.5)
'''