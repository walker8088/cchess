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
from array import *

import pygame
from pygame.locals import *

sys.path.append('..')
from cchess import *

#-----------------------------------------------------#
BORDER, SPACE = 15, 56
BOARD_SIZE = (WIDTH, HEIGHT) = (530, 586)
RES_PATH = 'res'

win_dict = { ChessSide.BLACK : u"红胜", ChessSide.RED : u"黑胜" }

#-----------------------------------------------------#
def load_image(file_name):
    return  pygame.image.load(os.path.join(RES_PATH,file_name)).convert()

def load_image_alpha(file_name):
    return  pygame.image.load(os.path.join(RES_PATH,file_name)).convert_alpha()
    
def load_sound(file_name):
    return pygame.mixer.Sound(os.path.join(RES_PATH,file_name))
    
def screen_to_pos(pos):
     return Pos((pos.x - BORDER) / SPACE, 9 - (pos.y - BORDER) / SPACE)

def pos_to_screen(pos):
     return Pos(BORDER + pos.x * SPACE, BORDER + (9 - pos.y) * SPACE)
      
#-----------------------------------------------------#	
class GameTable():
    
    def __init__(self):
        
        self.screen = pygame.display.set_mode(BOARD_SIZE, 0, 32)
	pygame.display.set_caption(u'中国象棋'.encode('utf-8'))
        
	self.selected = None
        self.last_moved = None
        #self.done = None
        
        self.surface = load_image('board.png')
        self.select_surface = load_image_alpha('select.png') 
        self.done_surface = load_image_alpha('done.png')
        self.over_surface = load_image_alpha('over.png')
        self.pieces_image = {}
        
        for name in ['r','n','c','k','a','b','p']:
            self.pieces_image[name] = load_image_alpha(name + '.png')
            
        #self.check_sound = load_sound('check.wav')
        #self.move_sound = load_sound('move.wav')
        #self.capture_sound = load_sound('capture.wav')
	
	self.clock = pygame.time.Clock()
	
        self.board = ChessBoard()
        self.engine = [None,None]
        
    def new_game(self, title, fen):
    
        pygame.display.set_caption(title.encode('utf-8'))
        self.board.from_fen(fen)
        
        self.selected = None
        self.last_moved = None
        
        engine = self.engine[self.board.move_side]
        if engine:
                engine.go_from(self.board.to_fen())
        
        
    def attach_engine(self, engine, side):
        self.engine[side] = engine
                
    def try_move(self, move_from, move_to):
        if self.board.is_valid_move(move_from, move_to):
                self.show_move(move_from, move_to)
                move = self.board.move(move_from, move_to)
                print move.to_chinese()
                self.last_moved = Pos(move_to.x, move_to.y)
                self.selected = None
                self.board.next_turn()
                engine = self.engine[self.board.move_side]
                if engine:
                        engine.go_from(self.board.to_fen())
                return True
        else:
                return False
                
    def draw(self):
        
        self.screen.fill((0,0,0))
        self.screen.blit(self.surface, (0, 0))
        
        for x in range(9):
            for y in range(10):
                    key = Pos(x,y)
                    piece = self.board.get_piece(key)
                    
                    if not piece:
                        continue
                    
                    image = self.pieces_image[piece.fench.lower()]
                        
                    #board_x = BORDER + x * SPACE
                    #board_y = BORDER + (9-y) * SPACE
                    
                    board_pos = pos_to_screen(key)
                    
                    if piece.side == ChessSide.RED:
                        offset = (0, 0, 52, 52)
                    else:
                        offset = (53, 0, 52, 52)
                        
                    self.screen.blit(image, board_pos(), offset)
                    
                    if self.selected and key == self.selected:
                        self.screen.blit(self.select_surface, board_pos(), offset)
                    
                    elif self.last_moved and key == self.last_moved:
                        self.screen.blit(self.done_surface, board_pos(), offset)
                        
                    #elif key == self.done:
                    #    self.screen.blit(self.over_surface, board_pos(), offset)
                          
    
    def make_move_steps(self, p_from, p_to):
	
        steps = []
        step_count = 7
	for i in range(step_count):
		
		x = p_from.x + (p_to.x - p_from.x) / step_count * (i+1)
		y = p_from.y + (p_to.y - p_from.y) / step_count * (i+1)
		
		steps.append(Pos(x,y))
	
	return steps 

    def show_move(self, p_from, p_to) :
	
	board_p_from = pos_to_screen(p_from)
	board_p_to   = pos_to_screen(p_to)
	
	steps = self.make_move_steps(board_p_from, board_p_to)
	for step in steps :
                self.screen.blit(self.surface, (0, 0))
		for x in range(9):
                    for y in range(10):
                        key = Pos(x,y)
                        piece = self.board.get_piece(key)
                        if piece == None:
                             continue
		    
                        board_pos = pos_to_screen(piece)
                        image = self.pieces_image[piece.fench.lower()]
                         
		        if piece.side == ChessSide.RED:
			    offset = (0, 0, 52, 52)
		        else:
			    offset = (53, 0, 52, 52)
		        
                        if key == p_from:
                                self.screen.blit(image, step(), offset)
                        else:        
                                self.screen.blit(image, board_pos(), offset)
		
		pygame.display.flip()
		pygame.event.pump()
		msElapsed = self.clock.tick(30)
	
    def run_once(self):
        
        engine = self.engine[self.board.move_side]
        if engine :
            engine.handle_msg_once()
            if not engine.move_queue.empty():
                output = engine.move_queue.get()
                #print output
                if output[0] == 'best_move':
                    p_from, p_to = output[1]["move"]
                    if not self.try_move(p_from, p_to):
                        print "engine output error"
                elif output[0] == 'dead':
                    #print self.board.move_side
                    print win_dict[self.board.move_side]   
                    return (False, self.board.move_side)
                    
        self.clock.tick(30)
	for event in pygame.event.get():

                if event.type == QUIT:
                    return (True, None)
                   
                if event.type == MOUSEBUTTONDOWN:
                    
                    sx, sy = pygame.mouse.get_pos()
                    
                    if sx < BORDER or sx > (WIDTH - BORDER):
                        break
                    if sy < BORDER or sy > (HEIGHT - BORDER):
                        break
                        
                    key = screen_to_pos(Pos(sx, sy))
                    
                    #move check
                    has_moved = False
                    if self.selected:
                        move_from = self.selected
                        move_to = key
                        has_moved = self.try_move(move_from, move_to)
                    #pickup check
                    if not has_moved:
                        piece = self.board.get_piece(key)
                        if piece and piece.side == self.board.move_side:
                            self.selected = key
                            self.last_moved = None
                                
	self.draw()   
	
	pygame.display.flip()
	
	return (False, None)

#-----------------------------------------------------#        
class GameKeeper():
    def __init__(self, file):
        self.file = file
        self.games = []
        self.games_done = []
        self.file_epd = self.file + '.epd'
        self.file_epg = self.file + '.epg'
        
    def load(self):
        lines = open(self.file_epd, 'rb').readlines()
        for line in lines:
                its = line.split('|')
                self.games.append((its[0].decode('utf-8'), its[1]))
        
        if not os.path.isfile(self.file + '.epg'):
                open(self.file_epg, 'wb').write('0'*len(self.games))
	
        self.games_done = array('c', open(self.file_epg, 'rb').readlines()[0])
        
    def done(self, index):
        self.games_done[index] = '1'
        open(self.file_epg, 'wb').write(self.games_done.tostring())
    
    def next(self, index):
        for i in range(index, len(self.games_done)):
             if self.games_done[i] == '0':
                return i
        return -1 
        
#-----------------------------------------------------#
if __name__ == '__main__': 
   
        engine = UcciEngine()
        engine.load("..\\cchess\\test\\eleeye\\eleeye.exe")
        
        table = GameTable()
        #table.attach_engine(engine, ChessSide.RED)
        table.attach_engine(engine, ChessSide.BLACK)
        
        #keeper = GameKeeper('level0')
        keeper = GameKeeper(u'梦入神机')
        keeper.load()
        
        index = 0
        quit = False
        while not quit:
            index = keeper.next(index)
            if index < 0:
                print u"恭喜！全部完成！"
                break
            game_it = keeper.games[index]    
            print u"挑战", game_it[0]
	    table.new_game(*game_it)
            done = False
            while not done:
                quit, dead_side = table.run_once()
                if quit :
                        done = True
                if dead_side == ChessSide.BLACK:
                        keeper.done(index)
                        print u'挑战成功！再接再励！'
                        done = True
                elif dead_side == ChessSide.RED:
                        done = True
                        print u'挑战失败！重新再来！'
            if quit :
                break
                    
        engine.quit()
        time.sleep(0.2)
        