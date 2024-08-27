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
import struct

from .common import RED, fench_to_species
from .board import ChessPlayer, ChessBoard 
from .game import Game

#-----------------------------------------------------#
#result_dict = {0: UNKNOWN, 1: RED_WIN, 2: BLACK_WIN, 3: PEACE, 4: PEACE}
result_dict = {0: '*', 1: '1-0', 2: '0-1', 3: '1/2-1/2', 4: '1/2-1/2'}

def _decode_pos(man_pos):
    return (int(man_pos // 10), man_pos % 10)

def _decode_pos2(man_pos):
    return ((int(man_pos[0] // 10), man_pos[0] % 10), (int(man_pos[1] // 10),
                                                       man_pos[1] % 10))

#-----------------------------------------------------#
class XQFKey(object):
    def __init__(self):
        pass

#-----------------------------------------------------#
class XQFBuffDecoder(object):
    def __init__(self, buffer):
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)

    def __read(self, size):

        start = self.index
        stop = self.index + size

        if stop > self.length:
            stop = self.length

        self.index = stop
        return self.buffer[start:stop]

    def read_str(self, size, coding="GB18030"):
        buff = self.__read(size)

        try:
            ret = buff.decode(coding)
        except Exception:
            ret = None

        return ret

    def read_bytes(self, size):
        return bytearray(self.__read(size))

    def read_int(self):
        bytes = self.read_bytes(4)
        return bytes[0] + (bytes[1] << 8) + (bytes[2] << 16) + (bytes[3] << 24)


#-------------------------------------------------
def __init_decrypt_key(buff_str):

    keys = XQFKey()

    #key_buff = bytearray(buff_str)

    # Pascal code here from XQFRW.pas
    # KeyMask   : dTByte;                         // 加密掩码
    # ProductId : dTDWord;                        // 产品号(厂商的产品号)
    # KeyOrA    : dTByte;
    # KeyOrB    : dTByte;
    # KeyOrC    : dTByte;
    # KeyOrD    : dTByte;
    # KeysSum   : dTByte;                         // 加密的钥匙和
    # KeyXY     : dTByte;                         // 棋子布局位置钥匙
    # KeyXYf    : dTByte;                         // 棋谱起点钥匙
    # KeyXYt    : dTByte;                         // 棋谱终点钥匙

    HEAD_KeyMask, HEAD_ProductId, \
    HEAD_KeyOrA, HEAD_KeyOrB, HEAD_KeyOrC, HEAD_KeyOrD, \
    HEAD_KeysSum, HEAD_KeyXY, HEAD_KeyXYf, HEAD_KeyXYt = struct.unpack("<BIBBBBBBBB", buff_str)
    """ 
        #以下是密码计算公式
        bKey       := XQFHead.KeyXY;
        KeyXY      := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * bKey;
        bKey       := XQFHead.KeyXYf;
        KeyXYf     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXY;
        bKey       := XQFHead.KeyXYt;
        KeyXYt     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXYf;
        wKey       := (XQFHead.KeysSum) * 256 + XQFHead.KeyXY;
        KeyRMKSize := (wKey mod 32000) + 767;
        """

    #pascal code
    #bKey       := XQFHead.KeyXY;
    #KeyXY      := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * bKey;
    bKey = HEAD_KeyXY
    #棋子32个位置加密因子
    keys.KeyXY = (((((
        (bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * bKey) & 0xFF

    #棋谱加密因子(起点)
    #pascal code
    #bKey       := XQFHead.KeyXYf;
    #KeyXYf     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXY;
    bKey = HEAD_KeyXYf
    keys.KeyXYf = (((((
        (bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * keys.KeyXY) & 0xFF

    #棋谱加密因子(终点)
    #pascal code
    #bKey       := XQFHead.KeyXYt;
    #KeyXYt     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXYf;
    bKey = HEAD_KeyXYt
    keys.KeyXYt = (((((
        (bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * keys.KeyXYf) & 0xFF

    #注解大小加密因子
    #pascal code
    #wKey       := (XQFHead.KeysSum) * 256 + XQFHead.KeyXY;
    #KeyRMKSize := (wKey mod 32000) + 767;
    wKey = HEAD_KeysSum * 256 + HEAD_KeyXY
    keys.KeyRMKSize = ((wKey % 32000) + 767) & 0xFFFF

    B1 = (HEAD_KeysSum & HEAD_KeyMask) | HEAD_KeyOrA
    B2 = (HEAD_KeyXY & HEAD_KeyMask) | HEAD_KeyOrB
    B3 = (HEAD_KeyXYf & HEAD_KeyMask) | HEAD_KeyOrC
    B4 = (HEAD_KeyXYt & HEAD_KeyMask) | HEAD_KeyOrD

    keys.FKeyBytes = (B1, B2, B3, B4)
    keys.F32Keys = bytearray(b"[(C) Copyright Mr. Dong Shiwei.]")
    for i in range(len(keys.F32Keys)):
        keys.F32Keys[i] &= keys.FKeyBytes[i % 4]

    return keys


#-----------------------------------------------------#
def __init_chess_board(man_str, version, keys=None):

    tmpMan = bytearray([0 for x in range(32)])
    man_buff = bytearray(man_str)

    if keys is None:
        for i in range(32):
            tmpMan[i] = man_buff[i]
        return tmpMan

    for i in range(32):
        if version >= 12:
            tmpMan[(keys.KeyXY + i + 1) & 0x1F] = man_buff[i]
        else:
            tmpMan[i] = man_buff[i]

    for i in range(32):
        tmpMan[i] = (tmpMan[i] - keys.KeyXY) & 0xFF
        if (tmpMan[i] > 89):
            tmpMan[i] = 0xFF

    return tmpMan


#-----------------------------------------------------#
def __decode_buff(keys, buff):

    nPos = 0x400
    de_buff = bytearray(buff)

    for i in range(len(buff)):
        KeyByte = keys.F32Keys[(nPos + i) % 32]
        de_buff[i] = (de_buff[i] - KeyByte) & 0xFF

    return bytes(de_buff)


#-----------------------------------------------------#
def __read_init_info(buff_decoder, version, keys):

    step_info = buff_decoder.read_bytes(4)

    annote_len = 0
    if version <= 0x0A:
        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        annote_len = buff_decoder.read_int()
    else:
        #高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
        step_info[2] &= 0xE0
        if (step_info[2] & 0x20):  #有注释
            annote_len = buff_decoder.read_int() - keys.KeyRMKSize

    return buff_decoder.read_str(annote_len) if (annote_len > 0) else None


#-----------------------------------------------------#
def __read_steps(buff_decoder, version, keys, game, parent_move, board):

    step_info = buff_decoder.read_bytes(4)

    if len(step_info) == 0:
        return

    annote_len = 0
    has_next_step = False
    has_var_step = False
    board_bak = board.copy()

    if version <= 0x0A:
        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        if (step_info[2] & 0xF0):
            has_next_step = True
        if (step_info[2] & 0x0F):
            has_var_step = True  #有变着
        annote_len = buff_decoder.read_int()

        step_info[0] = (step_info[0] - 0x18) & 0xFF
        step_info[1] = (step_info[1] - 0x20) & 0xFF

    else:
        #高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
        step_info[2] &= 0xE0
        if (step_info[2] & 0x80):  #有后续
            has_next_step = True
        if (step_info[2] & 0x40):  #有变招
            has_var_step = True
        if (step_info[2] & 0x20):  #有注释
            annote_len = buff_decoder.read_int() - keys.KeyRMKSize

        step_info[0] = (step_info[0] - 0x18 - keys.KeyXYf) & 0xFF
        step_info[1] = (step_info[1] - 0x20 - keys.KeyXYt) & 0xFF

    move_from, move_to = _decode_pos2(step_info)
    annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None

    fench = board.get_fench(move_from)

    if not fench:
        #raise CChessException("bad move at %s %s" % (str(move_from), str(move_to)))
        good_move = parent_move
    else:
        _, man_side = fench_to_species(fench)
        board.move_player = ChessPlayer(man_side)

        if board.is_valid_move(move_from, move_to):
            #认为当前走子一方就是合理一方，避免过多走子方检查
            curr_move = board.move(move_from, move_to)
            curr_move.annote = annote
            #print curr_move.move_str(), has_next_step, has_var_step
            if parent_move:
                parent_move.append_next_move(curr_move)
            else:
                game.append_first_move(curr_move)
            good_move = curr_move
        else:
            #print "bad move at", move_from, move_to
            #board.print_board()
            good_move = parent_move

    if has_next_step:
        __read_steps(buff_decoder, version, keys, game, good_move, board)

    if has_var_step:
        #print Move.to_iccs(parent.next_move.move), 'has var'
        __read_steps(buff_decoder, version, keys, game, parent_move, board_bak)


#-----------------------------------------------------#
def read_from_xqf(full_file_name, read_annotation=True):
    #避免循环导入
    from .game import Game
    
    with open(full_file_name, "rb") as f:
        contents = f.read()

    magic, version,  crypt_keys, ucBoard,\
    ucUn2, ucRes,\
    ucUn3, ucType,\
    ucUn4, ucTitleLen,szTitle,\
    ucUn5, ucMatchNameLen,szMatchName,\
    ucDateLen, szDate,\
    ucAddrLen, szAddr,\
    ucRedPlayerNameLen, szRedPlayerName,\
    ucBlackPlayerNameLen,szBlackPlayerName,\
    ucTimeRuleLen,szTimeRule,\
    ucRedTimeLen,szRedTime,\
    ucBlackTime,szBlackTime, \
    ucUn6,\
    ucCommenerNameLen,szCommenerName,ucAuthorNameLen,szAuthorName,\
    ucUn7 = struct.unpack("<2sB13s32s3sB12sB15sB63s64sB63sB15sB15sB15sB15sB63sB15sB15s32sB15sB15s528s",  contents[:0x400])

    if magic != b"XQ":
        return None

    game_info = {}

    game_info["source"] = "XQF"
    game_info["version"] = version
    game_info["type"] = ucType + 1

    if ucRes <= 4:  #It's really some file has value 4
        game_info["result"] = result_dict[ucRes]
    else:
        print("Bad Result  ", ucRes, full_file_name)
        game_info["result"] = '*'

    if ucRedPlayerNameLen > 0:
        try:
            game_info["red"] = szRedPlayerName[:ucRedPlayerNameLen].decode(
                "GB18030")
        except Exception:
            pass

    if ucBlackPlayerNameLen > 0:
        try:
            game_info[
                "black"] = szBlackPlayerName[:ucBlackPlayerNameLen].decode(
                    "GB18030")
        except Exception:
            pass

    if ucTitleLen > 0:
        try:
            game_info["name"] = szTitle[:ucTitleLen].decode("GB18030")
        except Exception:
            pass

    if ucMatchNameLen > 0:
        try:
            game_info["event"] = szMatchName[:ucMatchNameLen].decode("GB18030")
        except Exception:
            pass

    path, file_name = os.path.split(full_file_name)

    if (version <= 0x0A):
        keys = None
        chess_mans = __init_chess_board(ucBoard, version)
        step_base_buff = XQFBuffDecoder(contents[0x400:])
    else:
        keys = __init_decrypt_key(crypt_keys)
        chess_mans = __init_chess_board(ucBoard, version, keys)
        step_base_buff = XQFBuffDecoder(__decode_buff(keys, contents[0x400:]))

    board = ChessBoard()

    chessman_kinds = \
            (
                    'R',  'N',  'B',  'A', 'K', 'A',  'B',  'N', 'R' , \
                    'C', 'C', \
                    'P','P','P','P','P'
            )

    for side in range(2):
        for man_index in range(16):
            man_pos = chess_mans[side * 16 + man_index]
            if man_pos == 0xFF:
                continue
            pos = _decode_pos(man_pos)
            fen_ch = chr(ord(chessman_kinds[man_index]) + side * 32)
            board.put_fench(fen_ch, pos)

    game_annotation = __read_init_info(step_base_buff, version, keys)

    game = Game(board, game_annotation)
    game.info = game_info

    __read_steps(step_base_buff, version, keys, game, None, board)

    if game.first_move is not None:
        game.init_board.move_player = game.first_move.board.move_player
    else:
        game.init_board.move_player = ChessPlayer(RED)

    game.info['move_player'] = str(game.init_board.move_player)

    return game
