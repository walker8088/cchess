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

from .exception import CChessException
from .common import fench_to_species, FULL_INIT_FEN
from .board import ChessBoard

#-----------------------------------------------------#
def read_from_txt(moves_txt, pos_txt=None):
    #避免循环导入
    from .game import Game
    
    def decode_txt_pos(pos):
        return (int(pos[0]), 9 - int(pos[1]))

    #车马相士帅士相马车炮炮兵兵兵兵兵
    #车马象士将士象马车炮炮卒卒卒卒卒
    chessman_kinds = 'RNBAKABNRCCPPPPP'

    if not pos_txt:
        board = ChessBoard(FULL_INIT_FEN)
    else:
        if len(pos_txt) != 64:
            raise CChessException("bad pos_txt")

        board = ChessBoard()
        for side in range(2):
            for man_index in range(16):
                pos_index = (side * 16 + man_index) * 2
                man_pos = pos_txt[pos_index:pos_index + 2]
                if man_pos == '99':
                    continue
                pos = decode_txt_pos(man_pos)
                fen_ch = chr(ord(chessman_kinds[man_index]) + side * 32)
                board.put_fench(fen_ch, pos)

    last_move = None
    if not moves_txt:
        return Game(board)
    step_no = 0
    while step_no * 4 < len(moves_txt):
        #steps = moves_txt[step_no * 4:step_no * 4 + 4]

        move_from = decode_txt_pos(moves_txt[step_no * 4:step_no * 4 + 2])
        move_to = decode_txt_pos(moves_txt[step_no * 4 + 2:step_no * 4 + 4])

        if board.is_valid_move(move_from, move_to):

            if not last_move:
                _, man_side = fench_to_species(board.get_fench(move_from))
                board.move_side = man_side
                game = Game(board)
                last_move = game

            new_move = board.move(move_from, move_to)
            last_move.append_next_move(new_move)
            last_move = new_move
            board.next_turn()
        else:
            raise CChessException(f"bad move at {step_no} {move_from} {move_to}")
        step_no += 1
    if step_no == 0:
        game = Game(board)

    return game
