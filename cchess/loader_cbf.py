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

from xml.etree import ElementTree as et

from board import *

#-----------------------------------------------------#
                
class CBFLoader(object):
    def __init__(self):
        pass
        
    def load(self, file_name):
        
        def decode_move(move_str):
            p_from = (int(move_str[0]), int(move_str[1])) 
            p_to = (int(move_str[3]), int(move_str[4])) 
            
            return (p_from, p_to)
            
        tree = et.parse(file_name)
        root = tree.getroot()
        
        head = root.find("Head")
        for node in head.getchildren() :
            if node.tag == "FEN":
                init_fen = node.text
            #print node.tag
        
        books = {}
        board = Chessboard()
        board.init_board(init_fen)
        
        move_list = root.find("MoveList").getchildren()
        
        head_node = move_list[0]
        
        if head_node.text :
            step_head_node = LabelNode( head_node.text, init_fen)
        else :
            step_head_node = LabelNode(u"=开始＝", init_fen)
                
        step_node = step_head_node        
        for node in move_list[1:] :
            
            p_from, p_to = decode_move(node.attrib["value"])
            
            if not board.can_make_move(p_from, p_to, color_limit = False):
                raise Exception("Move Error")
            
            fen_before_move = board.get_fen() 
            chinese_move_str = board.std_move_to_chinese_move(p_from, p_to) 
            board.make_step_move(p_from, p_to) 
            fen_after_move = board.get_fen()
            
            new_node = StepNode(chinese_move_str,  fen_before_move, fen_after_move, (p_from, p_to), node.text )
            step_node.add_child(new_node)
            step_node = new_node
            
            board.turn_side()
            
            #print p_from, p_to, chinese_move_str
        
        books["steps"] = step_head_node    
        return books
                
#-----------------------------------------------------#

if __name__ == '__main__':
    pass
    
