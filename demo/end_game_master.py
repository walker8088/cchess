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
import logging

from pathlib import Path
from collections import OrderedDict

import pygame
from pygame.locals import *

import cchess
from cchess import Game, ChessBoard, UcciEngine, UciEngine

#-----------------------------------------------------#
BORDER, SPACE = 15, 56
pads = (5,5)
BOARD_SIZE = (WIDTH, HEIGHT) = (530, 586)
SCREEN_SIZE = (WIDTH, HEIGHT)

win_dict = {cchess.BLACK: "红胜", cchess.RED: "黑胜"}

go_params = {'depth': 15} 

ROOT_PATH = Path(__file__).parent
RES_PATH = Path(ROOT_PATH, 'UI')
    
#-----------------------------------------------------#
p_count_dict = {
    "R1":'车',
    "R2":'双车',
    "N1":'马',
    "N2":'双马',
    "C1":'炮',
    "C2":'双炮',
    "P1":'兵',
    "P2":'双兵',
    "P3":'三兵',
    "P4":'多兵',
    "P5":'多兵',
    'A1':'士',
    'A2':'双士',    
    'B1':'象',
    'B2':'双象',    
}

p_dict = {
    "R":'车',
    "N":'马',
    "C":'炮',
    "P":'兵',
    'A':'士',
    'B':'象',    
}

def get_pieces(fen):
    pieces = OrderedDict()
    fen_base = fen.split(' ')[0]
    for ch in fen_base:
        if not ch.isalpha():
            continue
        if ch not in pieces:
            pieces[ch] = 0
        pieces[ch] += 1
    return pieces

def get_title(fen):
    pieces = get_pieces(fen)
    for ch in ['K', 'A', 'B']:
        if ch in pieces:
            pieces.pop(ch)
    
    title = ''
    p_count = 0
    for fench in ['R', 'N', "C", 'P']:
        if fench not in pieces:
            continue
 
        title += p_dict[f'{fench}']
        p_count += 1
        
    return title

def get_title_full(fen):
    pieces = get_pieces(fen)
    
    title = ''
    p_count = 0
    for fench in ['R', 'N', "C", 'P', "A", "B"]:
        if fench not in pieces:
            continue
        #if fench == 'P' and p_count > 0:
        #    continue
        title += p_count_dict[f'{fench}{pieces[fench]}']
        p_count += 1
    
    p_count = 0
    title2 = ''
    for fench in ['r', 'n', "c", 'p', 'a', 'b']:
        if fench not in pieces:
            continue
        ch_upper = fench.upper()    
        #if fench == 'P' and p_count > 0:
        #    continue
        title2 += p_count_dict[f'{ch_upper}{pieces[fench]}']
        p_count += 1
    
    title2 = title2.replace('兵', '卒')
    if title2 == '':
        title2 = '将'
    
    return title + '胜' + title2

#-----------------------------------------------------#
def load_image(file_name):
    return pygame.image.load(os.path.join(RES_PATH, file_name)).convert()

def load_image_alpha(file_name):
    return pygame.image.load(os.path.join(RES_PATH, file_name)).convert_alpha()

def load_sound(file_name):
    return pygame.mixer.Sound(os.path.join(RES_PATH, file_name))

#-----------------------------------------------------#
def screen_to_pos(pos):
    return ((pos[0] - BORDER) // SPACE, 9 - (pos[1] - BORDER) // SPACE)

def pos_to_screen(pos):
    return (BORDER + pos[0] * SPACE, BORDER + (9 - pos[1]) * SPACE)

#-----------------------------------------------------#
class GameTable():
    def __init__(self):
        
        self.screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
        
        self.selected = None
        self.last_moved = None
        self.last_checked = False
        
        self.surface = load_image('board.png')
        self.select_surface = load_image_alpha('select.png')
        self.done_surface = load_image_alpha('done.png')
        self.over_surface = load_image_alpha('over.png')
        self.pieces_image = {}
        
        for name in ['r', 'n', 'c', 'k', 'a', 'b', 'p']:
            self.pieces_image[name] = load_image_alpha(name + '.png')

        self.clock = pygame.time.Clock()
        self.board = ChessBoard()

        self.engine = [None, None, None]
    
        
    def new_game(self, title, fen):

        pygame.display.set_caption(title)
        self.board.from_fen(fen)
        #self.best_moves = best_moves.split(",")
        self.best_index = 0

        self.selected = None
        self.last_moved = None
        self.move_history = []
        self.dead_side = None
        self.kill_count = 0
        
        engine = self.engine[self.board.get_move_color()]
        if engine:
            engine.go_from(fen, go_params)
            #print(f"go from: {fen}")
        #pygame.display.set_caption(title.encode('utf-8'))
        
    def attach_engine(self, engine, side):
        self.engine[side] = engine
        
    def draw(self):

        self.screen.fill((0, 0, 0))
        self.screen.blit(self.surface, (0, 0))

        for x in range(9):
            for y in range(10):
                key = (x, y)
                piece = self.board.get_piece(key)
                if not piece:
                    continue

                image = self.pieces_image[piece.fench.lower()]
                board_pos = pos_to_screen(key)

                if piece.color == cchess.RED:
                    offset = (0, 0, 52, 52)
                else:
                    offset = (53, 0, 52, 52)

                self.screen.blit(image, board_pos, offset)

                if self.selected and key == self.selected:
                    self.screen.blit(self.select_surface, board_pos, offset)
                elif self.last_moved and key == self.last_moved:
                    self.screen.blit(self.done_surface, board_pos, offset)

                # elif key == self.done:
                #    self.screen.blit(self.over_surface, board_pos(), offset)

    def make_move_steps(self, p_from, p_to):

        steps = []
        step_count = 7

        for i in range(step_count):
            x = p_from.x + (p_to.x - p_from.x) / step_count * (i + 1)
            y = p_from.y + (p_to.y - p_from.y) / step_count * (i + 1)
            steps.append(Pos(x, y))

        return steps

    def show_move(self, p_from, p_to):

        board_p_from = pos_to_screen(p_from)
        board_p_to = pos_to_screen(p_to)
        steps = self.make_move_steps(board_p_from, board_p_to)

        for step in steps:
            self.screen.blit(self.surface, (0, 0))

            for x in range(9):
                for y in range(10):
                    key = Pos(x, y)
                    piece = self.board.get_piece(key)
                    if piece is None:
                        continue

                    board_pos = pos_to_screen(piece)
                    image = self.pieces_image[piece.fench.lower()]
                    offset = (int(piece.side) * 53, 0, 52, 52)
                    if key == p_from:
                        self.screen.blit(image, step(), offset)
                    else:
                        self.screen.blit(image, board_pos(), offset)

            pygame.display.flip()
            pygame.event.pump()
            msElapsed = self.clock.tick(30)

    def run_once(self):
        dead = False
        has_move = False
        engine = self.engine[self.board.get_move_color()]
        if engine:
            engine.handle_msg_once()
            if not engine.move_queue.empty():
                output = engine.move_queue.get()
                action = output['action']
                if action == 'bestmove':
                    iccs = output["move"]
                    move = self.board.move_iccs(iccs)
                    #print(output["move"], move.to_text())    
                    self.board.next_turn()
                    move.prepare_for_engine(self.board.move_player, self.move_history)
                    self.move_history.append(move)
                    move_list_text = ','.join([m.to_text() for m in self.move_history])
                    print(move_list_text)
                    has_move = True
                    
                elif action in ['dead', 'draw', 'resign']:
                    print(action, self.board.get_move_color())
                    dead = True
                    
        self.clock.tick(30)

        for event in pygame.event.get():
            if event.type == QUIT:
                return (True, None, False)

        self.draw()
        pygame.display.flip()

        return (False, has_move, dead)


#-----------------------------------------------------#
class GameKeeper():
    def __init__(self, file):

        self.file = file
        self.games = []
        self.games_done = []
        self.file_src = f'{self.file}.txt'
        self.flile_eplib = self.file + '.eplib'

    def load(self):

        with open(self.file_src, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                continue
            its = line.split(',')
            self.games.append((its[0], its[1].strip()))

        self.games_done = bytearray(b'0' * len(self.games))

        if os.path.isfile(self.file + '.eplib'):
            with open(self.flile_eplib, 'rb') as f:
                done_array = bytearray(open(self.flile_eplib, 'rb').read())
            for i, it in enumerate(done_array):
                if i >= len(self.games):
                    break
                if it == ord('1'):
                    self.games_done[i] = it

        self.save_done()

    def done(self, index):
        self.games_done[index] = ord('1')
        self.save_done()

    def save_done(self):
        pass
        #open(self.flile_eplib, 'wb').write(bytes(self.games_done))
        
    def next(self, index):
        #if index > 2:
        #    return -1
        for i in range(index, len(self.games)):
            if self.games_done[i] == ord('0'):
                return i
        return -1


#-----------------------------------------------------#
if __name__ == '__main__':
    
    
    engine = UcciEngine() 
    if not engine.load(Path(ROOT_PATH, "..\\Engine\\eleeye\\eleeye.exe")):
        print("Can not load engine.")
        sys.exit(-1)
        
    '''
    engine = UciEngine()
    if not engine.load(".\\Engine\\pikafish_230408\pikafish"):
        print("Can not load engine.")
        sys.exit(-1)
    '''
    
    for i in range(30):
        engine.handle_msg_once()
        time.sleep(0.3)
    
    print(engine.engine_status)
    
    table = GameTable()

    table.attach_engine(engine, cchess.BLACK)
    table.attach_engine(engine, cchess.RED)
    
    type_name = '马兵类杀法'
    #type_name = '兵类杀法'
    #type_name = sys.argv[1]
    
    keeper = GameKeeper(type_name)
    keeper.load()
    
    fen_moves = []
    
    index = 0
    quit = False
    bad_files = []
    
    while not quit:
        index = keeper.next(index)
        if index < 0:
            if len(bad_files) > 0:
                print(f"全部完成！有{len(bad_files)}个残局未通过。")
                for bad_f in bad_files:
                    print(bad_f)
            else:
                print("全部完成！")
            break

        game_it = keeper.games[index]
        print(u"挑战", game_it)
        fen = game_it[1]
        table.new_game(game_it[0], game_it[1])
        title = get_title_full(fen)
        print(title)
        
        done = False
        while not done:
            quit, has_move, dead = table.run_once()
            
            if quit:
                done = True
            
            if dead:
                print('挑战失败！', game_it)
                bad_files.append(game_it[0])
                keeper.done(index)
                done = True
                time.sleep(0.5)
      
            elif has_move:
                move_side = table.board.get_move_color()
                if table.board.no_moves():
                    if move_side == cchess.RED:
                        print('挑战失败！', game_it)
                        bad_files.append(game_it[0])
                    else:
                        print('挑战成功！')
                        iccs_list = [x.to_iccs() for x in table.move_history]
                        fen_moves.append([len(table.move_history), game_it[0], fen, ' '.join(iccs_list)])
                    keeper.done(index)
                    done = True
                    time.sleep(0.5)
                else:
                    if len(table.move_history) > 80:
                        print('挑战失败！', game_it)
                        bad_files.append(game_it[0])
                        keeper.done(index)
                        done = True
                    else:        
                        engine = table.engine[table.board.get_move_color()]
                        move = table.move_history[-1]
                        fen_engine = move.to_engine_fen()
                        engine.go_from(fen_engine, go_params)
                        #print(f"go from: {fen_engine}")                        
        if quit:
            break

    engine.quit()
    time.sleep(0.2)
    
    fen_moves.sort(key = lambda x: x[0])
    
    with open(f'{type_name}.csv', 'w') as f:
        f.write(f'title, old_name, hint, fen, moves\n')
        for move_len, old_name, fen, moves in fen_moves:
            steps = (move_len +1)// 2
            f.write(f'{steps}步杀, {old_name}, {get_title_full(fen)}, {fen}, {moves}\n')
            