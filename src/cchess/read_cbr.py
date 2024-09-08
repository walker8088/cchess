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
import struct

from .exception import CChessException
from .common import RED, BLACK, fench_to_species
from .board import ChessPlayer, ChessBoard 
from .game import Game

CODING_PAGE = 'utf-16-le'

#-----------------------------------------------------#
piece_dict = {
    #红方
    0x11:'r', #车
    0x12:'n', #马
    0x13:'b', #相
    0x14:'a', #仕
    0x15:'k', #帅
    0x16:'c', #炮
    0x17:'p', #兵
    #黑方
    0x21:'R', #车
    0x22:'N', #马
    0x23:'B', #相
    0x24:'A', #仕
    0x25:'K', #帅
    0x26:'C', #炮
    0x27:'P', #卒
}

def _decode_pos(p):
    return (p%9, 9-p//9)    

def cut_bytes_to_str(buff):
    buff_len = len(buff)
    for index in range(0, buff_len, 2):
        if buff[index : index+2] == b'\x00\x00':
            return buff[:index].decode(CODING_PAGE)    
    
#-----------------------------------------------------#
class CbrBuffDecoder(object):
    def __init__(self, buffer, coding):
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)
        self.coding = coding
        
    def __read(self, size):

        start = self.index
        stop = self.index + size

        if stop > self.length:
            stop = self.length

        self.index = stop
        return self.buffer[start:stop]

    def read_str(self, size):
        buff = self.__read(size)
        return cut_bytes_to_str(buff)
        
    def read_bytes(self, size):
        return bytearray(self.__read(size))

    def read_int8(self):
        bytes = self.read_bytes(1)
        return struct.unpack('<b', bytes)[0]
        
    def read_int(self):
        bytes = self.read_bytes(4)
        #return bytes[0] + (bytes[1] << 8) + (bytes[2] << 16) + (bytes[3] << 24)
        return struct.unpack('<i', bytes)[0]
        
#-----------------------------------------------------#
def __read_init_info(buff_decoder):

    #注释长度长度, 为0则没有注释
    a_len = buff_decoder.read_int()
    if a_len == 0:
        return ''
    else:
        annote_len = buff_decoder.read_int()
        return buff_decoder.read_str(annote_len)

#-----------------------------------------------------#
def __read_steps(buff_decoder, game, parent_move, board):
    
    step_info = buff_decoder.read_bytes(4)
    #print(step_info.hex())
    step_mark, step_none, step_from, step_to = step_info
    
    #棋谱分支结束
    if step_mark & 0x01:
        has_next_move = False
    else:
        has_next_move = True
    
    #有变招    
    if step_mark & 0x02: 
        has_var_step = True
    else:
        has_var_step = False
    
    #有注释    
    if step_mark & 0x04: 
        annote_len = buff_decoder.read_int()
    else:
        annote_len = 0
    
    board_bak = board.copy()
    move_from = _decode_pos(step_from)
    move_to   = _decode_pos(step_to)
    annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None
    
    fench = board.get_fench(move_from)
    if not fench:
        raise CChessException(f"bad move: {board.to_fen()} {move_from}, {move_to}")
        good_move = parent_move
    else:
        _, man_side = fench_to_species(fench)
        board.move_player = ChessPlayer(man_side)
        #print(fench, man_side)
        
        if board.is_valid_move(move_from, move_to):
            #认为当前走子一方就是合理一方，避免过多走子方检查
            curr_move = board.move(move_from, move_to)
            curr_move.annote = annote
            #print(step_info.hex(), curr_move.to_text(), has_var_step, annote_len)
            #board.print_board()
            
            if parent_move:
                parent_move.append_next_move(curr_move)
            else:
                game.append_first_move(curr_move)
            good_move = curr_move
        else:
            raise CChessException(f"bad move: {board.to_fen()} {move_from}, {move_to}")
            good_move = parent_move
    
    if has_next_move:
        __read_steps(buff_decoder, game, good_move, board)

    if has_var_step:
        #print(parent_move.to_text(), 'read var moves')
        __read_steps(buff_decoder, game, parent_move, board_bak)
    
    
#-----------------------------------------------------#
def read_from_cbr_buffer(contents):

    bmagic, _i1, btitle, _i2, move_side, _i3, boards, _i4 = struct.unpack("<16s164s128s1804sB7s90s4s", contents[:2214])
    
    if bmagic != b"CCBridge Record\x00":  
        return None

    game_info = {}
    game_info["source"] = "CBR"
    game_info['title'] =  cut_bytes_to_str(btitle)
    
    board = ChessBoard()
    if move_side == 1:    
        board.move_player = ChessPlayer(RED)
    else:
        board.move_player = ChessPlayer(BLACK)
   
    for x in range(9):
        for y in range(10):
            v = boards[y*9+x]
            if v in piece_dict:
                board.put_fench(piece_dict[v], (x, y))
    
    #board.print_board()
    
    buff_decoder = CbrBuffDecoder(contents[2214:], CODING_PAGE)
    game_annotation = __read_init_info(buff_decoder)
    
    game = Game(board, game_annotation)
    game.info = game_info
    
    __read_steps(buff_decoder, game, None, board)
    
    return game


#-----------------------------------------------------#
def read_from_cbr(file_name):

    with open(file_name, "rb") as f:
        contents = f.read()
    
    return read_from_cbr_buffer(contents)
    