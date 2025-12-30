# -*- coding: utf-8 -*-
'''
Copyright (C) 2024  walker li <walker8088@gmail.com>

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

#import os
import struct
from typing import Tuple

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

    comment_len = 0
    if version <= 0x0A:
        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        comment_len = buff_decoder.read_int()
    else:
        #高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
        step_info[2] &= 0xE0
        if (step_info[2] & 0x20):  #有注释
            comment_len = buff_decoder.read_int() - keys.KeyRMKSize

    return buff_decoder.read_str(comment_len) if (comment_len > 0) else None


#-----------------------------------------------------#
def __read_steps(buff_decoder, version, keys, game, parent_move, board):

    step_info = buff_decoder.read_bytes(4)

    if len(step_info) == 0:
        return

    comment_len = 0
    has_next_step = False
    has_var_step = False
    board_bak = board.copy()

    if version <= 0x0A:
        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        if (step_info[2] & 0xF0):
            has_next_step = True
        if (step_info[2] & 0x0F):
            has_var_step = True  #有变着
        comment_len = buff_decoder.read_int()
        #走子起点，落点
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
            comment_len = buff_decoder.read_int() - keys.KeyRMKSize

        #走子起点，落点
        step_info[0] = (step_info[0] - 0x18 - keys.KeyXYf) & 0xFF
        step_info[1] = (step_info[1] - 0x20 - keys.KeyXYt) & 0xFF

    move_from, move_to = _decode_pos2(step_info)
    comment = buff_decoder.read_str(comment_len) if comment_len > 0 else None

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
            curr_move.comment = comment
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
        #print("new_line", parent_move.step_index, parent_move.to_text())
        __read_steps(buff_decoder, version, keys, game, parent_move, board_bak)
        game.info['branchs'] += 1

#-----------------------------------------------------#
def read_from_xqf(file_name, read_annotation=True):
    
    with open(file_name, "rb") as f:
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
        print("Bad Result  ", ucRes, file_name)
        game_info["result"] = '*'

    if ucRedPlayerNameLen > 0:
        try:
            game_info["red_player"] = szRedPlayerName[:ucRedPlayerNameLen].decode("GB18030")
        except Exception:
            pass

    if ucBlackPlayerNameLen > 0:
        try:
            game_info["black_player"] = szBlackPlayerName[:ucBlackPlayerNameLen].decode("GB18030")
        except Exception:
            pass

    if ucTitleLen > 0:
        try:
            game_info["title"] = szTitle[:ucTitleLen].decode("GB18030")
        except Exception:
            pass

    if ucMatchNameLen > 0:
        try:
            game_info["event"] = szMatchName[:ucMatchNameLen].decode("GB18030")
        except Exception:
            pass

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
    game.info.update(game_info)

    __read_steps(step_base_buff, version, keys, game, None, board)

    if game.first_move:
        game.init_board.move_player = game.first_move.board.move_player
    else:
        game.init_board.move_player = ChessPlayer(RED)

    game.info['move_player'] = str(game.init_board.move_player)

    return game

#-----------------------------------------------------#
def _encode_pos(pos):
    return pos[0]*10 + pos[1]

#-----------------------------------------------------#
class XQMove:
    """表示一步棋及其变招"""
    def __init__(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 comment: str = "", has_variation = False):
        self.start_pos = start_pos  # (x, y) 元组
        self.end_pos = end_pos      # (x, y) 元组
        self.comment = comment
        self.has_variation = has_variation
    
#-----------------------------------------------------#
class XQFWriter:
    def __init__(self, game):
        self.game = game
        self.header = bytearray(1024)  # 头部固定1024字节
        
        # 初始化头部为0
        for i in range(len(self.header)):
            self.header[i] = 0
            
        # 设置文件标记和版本
        self._set_bytes(0x0000, b'XQ')  # 文件标记
        self.header[0x0002] = 0x0A      # 版本号 1.0
        
        # 设置默认初始局面
        self.set_initial_position()
        
        # 设置默认结果和类型
        self.set_result(0x00)  # 默认未知结果
        self.set_game_type(0x00)  # 默认全局文件
        
        # 设置棋局信息
        self.set_title(game.info['title'])
        self.set_event(game.info['event'])
        self.set_date(game.info['date'])
        self.set_location(game.info['location'])
        self.set_red_player(game.info['red_player'])
        self.set_black_player(game.info['black_player'])
        self.set_commentator(game.info['commentator'])
        self.set_author("cchess")
        
    def _set_bytes(self, offset: int, data: bytes):
        """在指定偏移量设置字节数据"""
        for i, byte in enumerate(data):
            self.header[offset + i] = byte
    
    def _set_string(self, offset: int, text: str, max_length: int):
        """设置字符串字段"""
        if not text:
            self.header[offset] = 0
            return
            
        # 转换为GBK编码（XQF使用GBK编码）
        try:
            encoded = text.encode('gbk')
        except Exception:
            encoded = text.encode('gbk', errors='ignore')
            
        length = min(len(encoded), max_length - 1)
        self.header[offset] = length
        self._set_bytes(offset + 1, encoded[:length])
    
    def set_initial_position(self):
        """设置初始局面"""
        # 默认初始局面（红方和黑方从右到左排列）
        #default_position = [
        #    0x50, 0x46, 0x3C, 0x32, 0x28, 0x1E, 0x14, 0x0A,  # 红方车马相士帅士相马
        #    0x00, 0x48, 0x0C, 0x53, 0x3F, 0x2B, 0x17, 0x03,  # 红方车炮炮兵兵兵兵兵
        #    0x09, 0x13, 0x1D, 0x27, 0x31, 0x3B, 0x45, 0x4F,  # 黑方车马象士将士象马
        #    0x59, 0x11, 0x4D, 0x06, 0x1A, 0x2E, 0x42, 0x56   # 黑方车炮炮卒卒卒卒卒
        #]

        position = bytearray(32)
    
        board = self.game.init_board
        pieces_dict = {}
        for key in ['R', 'N', 'B', 'A', 'K', 'C', 'P']:
            pieces_dict[key] = board.get_fenchs(key)
            key_lower = key.lower()
            pieces_dict[key_lower] = board.get_fenchs(key_lower)
            
        fenchs = ('RNBAKABNRCCPPPPP')
        for x in range(2):
            for i, fench in enumerate(fenchs):
                key = fench.lower() if x > 0 else fench
                pos_list = pieces_dict[key]
                pos_index = x * 16 + i
                if len(pos_list) == 0:
                    position[pos_index] = 0xff 
                else:
                    pos = pos_list.pop(0)
                    position[pos_index] = _encode_pos(pos)
        
        self._set_bytes(0x0010, bytes(position))
    
    def set_result(self, result: int):
        """设置棋局结果
        0x00-未知, 0x01-红胜, 0x02-黑胜, 0x03-和棋
        """
        self.header[0x0033] = result
    
    def set_game_type(self, game_type: int):
        """设置棋局类型
        0x00-全局文件, 0x01-布局文件, 0x02-中局文件, 0x03-残局文件
        """
        self.header[0x0040] = game_type
    
    def set_title(self, title: str):
        """设置标题"""
        self._set_string(0x0050, title, 63)
    
    def set_event(self, event: str):
        """设置比赛名称"""
        self._set_string(0x00D0, event, 63)
    
    def set_date(self, date: str):
        """设置比赛日期"""
        self._set_string(0x0110, date, 15)
    
    def set_location(self, location: str):
        """设置比赛地点"""
        self._set_string(0x0120, location, 15)
    
    def set_red_player(self, player: str):
        """设置红方棋手"""
        self._set_string(0x0130, player, 15)
    
    def set_black_player(self, player: str):
        """设置黑方棋手"""
        self._set_string(0x0140, player, 15)
    
    def set_time_rule(self, rule: str):
        """设置用时规则"""
        self._set_string(0x0150, rule, 63)
    
    def set_red_time(self, time_str: str):
        """设置红方用时"""
        self._set_string(0x0190, time_str, 15)
    
    def set_black_time(self, time_str: str):
        """设置黑方用时"""
        self._set_string(0x01A0, time_str, 15)
    
    def set_commentator(self, commentator: str):
        """设置棋谱讲评人"""
        self._set_string(0x01D0, commentator, 15)
    
    def set_author(self, author: str):
        """设置文件作者"""
        self._set_string(0x01E0, author, 15)
    
    def _encode_move(self, move: XQMove, is_last) -> Tuple[bytes, bytes]:
        """编码一步棋为XQF格式"""
        start_pos_value = _encode_pos(move.start_pos)
        end_pos_value = _encode_pos(move.end_pos)
        
        # 构建移动记录
        move_record = bytearray(8)
        move_record[0] = start_pos_value + 24  # 起始位置+24
        move_record[1] = end_pos_value + 32    # 目标位置+32
        
        # 如果是序列中的最后一步或者是棋局的最后一步，则标记为最后一步
        move_record[2] = 0x00

        if move.has_variation:
            move_record[2] |= 0x0F
        if not is_last:
            move_record[2] |= 0xF0
        
        move_record[3] = 0x00  # 保留字节
        # 处理注解
        comment_data = b""
        if move.comment:
            try:
                comment_data = move.comment.encode('gbk')
            except Exception:
                comment_data = move.comment.encode('gbk', errors='ignore')
        
        # 设置注解长度（32位整数，小端序）
        comment_length = len(comment_data)
        move_record[4:8] = struct.pack('<I', comment_length)
        
        return bytes(move_record+comment_data)
    

    def save(self, file_name):

        with open(file_name, 'wb') as f:
            move_lines = []
            lines = self.game.dump_moves(is_tree_mode = True)
            for line in lines:
                w_line = []
                for index, move in enumerate(line['moves']): 
                    has_variation = move.sibling_next is not None
                    w_line.append(XQMove(move.p_from, move.p_to, move.comment, has_variation))      
                move_lines.append(w_line)

            f.write(self.header)
            
            if len(move_lines) == 0:
                # 只有初始局面，没有着法记录
                f.write(b'\x18\x20\x00\xFF\x00\x00\x00\x00')
                return

            # 有棋谱记录
            f.write(b'\x18\x20\xF0\xFF\x00\x00\x00\x00')            
            for line in move_lines:
                for i, move in enumerate(line):
                    is_last = (i == len(line)-1) 
                    move_record = self._encode_move(move, is_last)    
                    # 写入招法记录
                    f.write(move_record)
