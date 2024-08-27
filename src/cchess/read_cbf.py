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


from xml.etree import ElementTree as et

from .exception import CChessException
from .board import ChessBoard

#-----------------------------------------------------#


def read_from_cbf(file_name):
    #避免循环导入
    from .game import Game
    
    def decode_move(move_str):
        p_from = (int(move_str[0]), 9 - int(move_str[1]))
        p_to = (int(move_str[3]), 9 - int(move_str[4]))

        return (p_from, p_to)

    tree = et.parse(file_name)
    root = tree.getroot()

    head = root.find("Head")
    for node in list(head): #.getchildren():
        if node.tag == "FEN":
            init_fen = node.text
        #print node.tag

    #books = {}
    board = ChessBoard(init_fen)

    move_list = list(root.find("MoveList")) #.getchildren()

    game = Game(board)
    last_move = None
    step_no = 1
    for node in move_list[1:]:
        move_from, move_to = decode_move(node.attrib["value"])
        if board.is_valid_move(move_from, move_to):
            new_move = board.move(move_from, move_to)
            if last_move is not None:
                last_move.append_next_move(new_move)
            else:
                game.append_first_move(new_move)
            last_move = new_move
            board.next_turn()
        else:
            raise CChessException(f"bad move at {step_no} {move_from}, {move_to}")
        step_no += 1
    return game
