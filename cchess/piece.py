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

import sys

from sets import *
from enum import *
    
#-----------------------------------------------------#

h_level_index = \
(
        (u"九",u"八",u"七",u"六",u"五",u"四",u"三",u"二",u"一"), 
        (u"１",u"２",u"３",u"４",u"５",u"６",u"７",u"８",u"９") 
)

v_change_index = \
(
        (u"错", ""u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"), 
        (u"误", ""u"１", u"２", u"３", u"４", u"５", u"６", u"７", u"８", u"９")
)

#-----------------------------------------------------#

advisor_pos = (
    ((3, 0), (5, 0), (4, 1), (3, 2), (5, 2)),
    ((3, 9), (5, 9), (4, 8), (3, 7), (5, 7)), 
    )

bishop_pos = (
    ((2, 0), (6, 0), (0, 2), (4, 2), (9, 2), (2, 4), (6, 4)),
    ((2, 9), (6, 9), (0, 7), (4, 7), (9, 7), (2, 5), (6, 5)), 
    )

#-----------------------------------------------------#
class ChessSide(IntEnum):     
    RED = 0
    BLACK = 1
    
    @staticmethod
    def turn_side(side):
        return {ChessSide.RED:ChessSide.BLACK, ChessSide.BLACK:ChessSide.RED}[side]
     
#-----------------------------------------------------#
class PieceT(IntEnum):
    KING = 1
    ADVISOR = 2
    BISHOP = 3
    KNIGHT = 4
    ROOK = 5 
    CANNON = 6
    PAWN = 7
        
#-----------------------------------------------------#
fench_species_dict = {
    'k': PieceT.KING,
    'a': PieceT.ADVISOR,
    'b': PieceT.BISHOP,
    'n': PieceT.KNIGHT,
    'r': PieceT.ROOK,
    'c': PieceT.CANNON,
    'p': PieceT.PAWN
}

fench_name_dict = {
   'K': u"帅",
   'k': u"将",
   'A': u"仕",
   'a': u"士",
   'B': u"相", 
   'b': u"象",
   'N': u"马",
   'n': u"马",
   'R': u"车",
   'r': u"车",
   'C': u"炮", 
   'c': u"炮",
   'P': u"兵", 
   'p': u"卒"     
}

fench_txt_name_dict = {
   'K': u"帅",
   'k': u"将",
   'A': u"仕",
   'a': u"士",
   'B': u"相", 
   'b': u"象",
   'N': u"马",
   'n': u"碼",
   'R': u"车",
   'r': u"砗",
   'C': u"炮", 
   'c': u"砲",
   'P': u"兵", 
   'p': u"卒"     
}
    
species_fench_dict = {
    PieceT.KING:    ('K', 'k'),
    PieceT.ADVISOR: ('A', 'a'),
    PieceT.BISHOP:  ('B', 'b'),
    PieceT.KNIGHT:  ('N', 'n'),
    PieceT.ROOK:    ('R', 'r'),
    PieceT.CANNON:  ('C', 'c'),
    PieceT.PAWN:    ('P', 'p')     
}

#-----------------------------------------------------#

def fench_to_name(fench) :
    return fench_name_dict[fench]

def fench_to_txt_name(fench) :
    return fench_txt_name_dict[fench]
    
def fench_to_species(fen_ch):
    return fench_species_dict[fen_ch.lower()], ChessSide.BLACK if fen_ch.islower() else ChessSide.RED
    
def species_to_fench(species, side):
    return species_fench_dict[species][side]
    
#KING, ADVISOR, BISHOP, KNIGHT, ROOK, CANNON, PAWN

chessman_show_name_dict = {
    PieceT.KING:    (u"帅", u"将"),
    PieceT.ADVISOR: (u"仕", u"士"),
    PieceT.BISHOP:  (u"相", u"象"),
    PieceT.KNIGHT:  (u"马", u"碼"),
    PieceT.ROOK:    (u"车", u"砗"),
    PieceT.CANNON:  (u"炮", u"砲"),
    PieceT.PAWN:    (u"兵", u"卒")     
}

def get_show_name(species, side) :
        return chessman_show_name_dict[species][side]
        
    
#-----------------------------------------------------#

class Piece(object):
    
    def __init__(self, board, species, side, pos):
        
        self.board = board
        
        self.species = species
        self.side = side
        
        self.x, self.y = pos
        
        self.__can_place_checks = {
             PieceT.KING   : self.__can_place_king, 
             PieceT.ADVISOR: self.__can_place_advisor, 
             PieceT.BISHOP : self.__can_place_bishop, 
             PieceT.PAWN   : self.__can_place_pawn
        }
        
        self.__can_move_checks = {
             PieceT.KING   :  self.__can_move_king, 
             PieceT.ADVISOR:  self.__can_move_advisor, 
             PieceT.BISHOP :  self.__can_move_bishop, 
             PieceT.KNIGHT :  self.__can_move_knight, 
             PieceT.ROOK   :  self.__can_move_rook, 
             PieceT.CANNON :  self.__can_move_cannon,
             PieceT.PAWN   :  self.__can_move_pawn
        }
        
        self.__chinese_move_to_std_move_checks = {
             PieceT.ADVISOR : self.__chinese_move_to_std_move_advisor, 
             PieceT.BISHOP : self.__chinese_move_to_std_move_bishop, 
             PieceT.KNIGHT : self.__chinese_move_to_std_move_knight, 
        }
    
    def can_place_to(self, x, y):
        if not self.__can_place_check_default(x, y):
            return False
            
        if self.species in self.__can_place_checks:
            return self.__can_place_checks[self.species](x, y)
        
        return True
        
    def can_move_to(self, x, y):
        if not self.__can_move_check_default(x, y):
            print "not self.__can_move_check_default",  x,  y
            return False
        
        return self.__can_move_checks[self.species](x, y) 
        
    
    def chinese_move_to_std_move(self, move_str):
        
        if self.species in self.__chinese_move_to_std_move_checks :
            new_pos = self.__chinese_move_to_std_move_checks[self.species](move_str)
        else :    
            new_pos = self.__chinese_move_to_std_move_default(move_str)
        
        if not new_pos :
            return None
            
        if not self.can_move_to(new_pos[0] , new_pos[1]):
            return None 
            
        return ((self.x,  self.y), new_pos)
    
    def __can_place_check_default(self, x, y):
        
        if x < 0 or x > 8 or y < 0 or y > 9:
            return False
        
        if self.board.chessman_of_pos((x, y)) != None :
            return False
            
        return True
    
    #王
    def __can_place_king(self, x, y):
        
        if x < 3 or x > 5:
            return False
            
        if (self.side == ChessSide.RED) and y > 2:
            return False
            
        if (self.side == ChessSide.BLACK) and y < 7:
            return False
            
        return True
    
    #士
    def __can_place_advisor(self, x, y):
        
        if (x, y) in advisor_pos[self.side] :
            return True    
        
        return False
    
    #象    
    def __can_place_bishop(self, x, y):
        
        if (x, y) in bishop_pos[self.side] :
            return True
            
        return False
        
    #兵    
    def __can_place_pawn(self, x, y):
        
        if (self.side == ChessSide.RED) and y < 3:
            return False
            
        if (self.side == ChessSide.BLACK) and y > 6:
            return False
            
        return True
    
    def __can_move_check_default(self, x, y):
        
        if x < 0 or x > 8 or y < 0 or y > 9:
            return False
        
        old_man = self.board.chessman_of_pos((x, y))
        
        if old_man and (old_man.side == self.side) :
            return False
            
        return True
    
        
    def __can_move_king(self, x, y):
        
        if not self.__can_place_king(x, y) :
            return False
        
        if (abs(self.x - x) + abs(self.y - y)) != 1:
            return False
        
        #照将检查    
        
        #被将军检查TODO
        
        return True
        
    def __can_move_advisor(self, x, y):
        
        if not self.__can_place_advisor(x, y) :
            return False
        
        if (abs(self.x - x) == 1) and (abs(self.y - y) == 1):
            return True
        else :
            return False
        
    def __can_move_bishop(self, x, y):
        
        if (abs(self.x - x) != 2) or (abs(self.y - y) != 2):
            return False
        
        m_x = (self.x + x) / 2
        m_y = (self.y + y) / 2
        
        #塞象眼检查
        if self.board.chessman_of_pos((m_x, m_y)) != None :
            return False
        
        return True
    
    def __can_move_knight(self, x, y):
        
        if (abs(self.x - x) == 2) and (abs(self.y - y) == 1):
            
            m_x = (self.x + x) / 2
            m_y = self.y
            
            #别马腿检查
            if self.board.chessman_of_pos((m_x, m_y)) == None :
                return True

        if (abs(self.x - x) == 1) and (abs(self.y - y) == 2):
            
            m_x = self.x
            m_y = (self.y + y) / 2
            
            #别马腿检查
            if self.board.chessman_of_pos((m_x, m_y)) == None :
                return True

        return False
        
    def __can_move_rook(self, x, y):
        
        if self.x != x:
            
            #斜向移动是非法的
            if self.y != y:   
                return False
            
            if self.board.between_h_line(self.y, self.x, x) != 0:
                return False
                
        else :
            if self.board.between_v_line(self.x, self.y, y) != 0:
                return False
                
        return True
        
    def __can_move_cannon(self, x, y):
        
        if self.x != x:
            #斜向移动是非法的
            if self.y != y:   
                return False
            
            #水平移动    
            count = self.board.between_h_line(self.y, self.x, x)
            
        else :
            #垂直移动
            count = self.board.between_v_line(self.x, self.y, y)
        
        if count == 0 :
            #炮移动
            if self.board.chessman_of_pos((x, y)) == None :
                return True
        
        if count == 1 :
            #炮吃子
            if self.board.chessman_of_pos((x, y)) != None :
                return True
        
        return False
        
    def __pawn_over_river(self) :      
        if (self.side == ChessSide.RED) and (self.y > 4) :
            return True
            
        if (self.side == ChessSide.BLACK) and (self.y < 5) :
            return True
            
        return False
    
    def __can_move_pawn(self, x, y):
        
        not_over_river_step = ((0, 1), (0, -1))
        over_river_step = (((-1, 0), (1, 0), (0, 1)),((-1, 0), (1, 0), (0, -1)))
                           
        step = (x - self.x, y - self.y)
        
        over_river = self.__pawn_over_river()
        
        if (not over_river) and (step == not_over_river_step[self.side]):
                return True
        
        if over_river and (step in over_river_step[self.side]):
                return True
                
        return False
        
    def __chinese_move_to_std_move_advisor(self, move_str):
        if move_str[0] == u"平":
            return None
        
        new_x = h_level_index[self.side].index(move_str[1])
                
        if move_str[0] == u"进" :
            diff_y = -1
        elif move_str[0] == u"退" :
            diff_y = 1    
        else :
            return None
        
        if self.side == ChessSide.BLACK:
            diff_y = - diff_y
        
        new_y = self.y - diff_y
        
        return (new_x,  new_y)
        
    def __chinese_move_to_std_move_bishop(self, move_str):
        if move_str[0] == u"平":
            return None
        
        new_x = h_level_index[self.side].index(move_str[1])
                
        if move_str[0] == u"进" :
            diff_y = -2
        elif move_str[0] == u"退" :
            diff_y = 2    
        else :
            return None
        
        if self.side == ChessSide.BLACK:
            diff_y = - diff_y
        
        new_y = self.y - diff_y
        
        return (new_x,  new_y)
        
    def __chinese_move_to_std_move_knight(self, move_str):
        if move_str[0] == u"平":
            return None
        
        new_x = h_level_index[self.side].index(move_str[1])
        
        diff_x = abs(self.x - new_x)
        
        if move_str[0] == u"进" :
            diff_y = [3, 2, 1][diff_x]
            
        elif move_str[0] == u"退" :
            diff_y = [-3, -2, -1][diff_x]
            
        else :
            return None
        
        if self.side == ChessSide.RED:
            diff_y = -diff_y
        
        new_y = self.y - diff_y
        
        return (new_x,  new_y)
        
    def __chinese_move_to_std_move_default(self, move_str):
        
        if move_str[0] == u"平":
            new_x = h_level_index[self.side].index(move_str[1])
            
            return (new_x,  self.y)
            
        else :
            #王，车，炮，兵的前进和后退
            diff = v_change_index[self.side].index(move_str[1])
            
            if move_str[0] == u"退":
                diff = -diff
            elif move_str[0] != u"进":
                return None
                
            if self.side == ChessSide.BLACK:
                diff = -diff
            
            new_y = self.y + diff
            
            return (self.x,  new_y)
    
