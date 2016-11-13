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
import base64
import struct, copy

from board import *
from book import *

from utils import *

#-----------------------------------------------------#
def _decode_pos(man_pos) :
        return (int(man_pos / 10), man_pos % 10) 

def _decode_pos2(man_pos) :
        return (int(man_pos[0] / 10), man_pos[0] % 10), (int(man_pos[1] / 10), man_pos[1] % 10) 

#-----------------------------------------------------# 
class XQFKey(object) :
	def __init__(self):
		pass

#-----------------------------------------------------#
class XQFBuffDecoder(object) :
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
                
        def read_str(self, size, coding = "GB18030"):
                buff =  self.__read(size)       
                
                try:
                        ret = buff.decode(coding)
                except:
                        ret = None
                
                return ret
                
        def read_bytes(self, size):
                return bytearray(self.__read(size))
        
        def read_int(self):
                bytes =  self.read_bytes(4)               
                return  bytes[0] + (bytes[1] << 8) + (bytes[2] << 16) + (bytes[3] << 24) 

#-----------------------------------------------------#
class XQFLoader(object):
	def __init__(self):	
                self.result_dict = { 0:"*", 1:"1-0", 2:"0-1", 3:"1/2-1/2", 4:"1/2-1/2" } 
                
	def __init_decrypt_key(self, buff_str):
		
                keys = XQFKey()
		
		key_buff =bytearray(buff_str)
		
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
                keys.KeyXY = ((((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * bKey) & 0xFF
                
                #棋谱加密因子(起点)
                #pascal code
                #bKey       := XQFHead.KeyXYf;
                #KeyXYf     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXY;
                bKey = HEAD_KeyXYf
                keys.KeyXYf  = ((((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * keys.KeyXY) & 0xFF
                
                #棋谱加密因子(终点)
                #pascal code 
                #bKey       := XQFHead.KeyXYt;
                #KeyXYt     := (((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * KeyXYf;
                bKey  = HEAD_KeyXYt
                keys.KeyXYt  = ((((((bKey*bKey)*3+9)*3+8)*2+1)*3+8) * keys.KeyXYf) & 0xFF
                
                #注解大小加密因子
                #pascal code 
                #wKey       := (XQFHead.KeysSum) * 256 + XQFHead.KeyXY;
                #KeyRMKSize := (wKey mod 32000) + 767;
                wKey = HEAD_KeysSum * 256 + HEAD_KeyXY
                keys.KeyRMKSize = ((wKey % 32000) + 767)  & 0xFFFF
                
                B1 = (HEAD_KeysSum & HEAD_KeyMask) | HEAD_KeyOrA
                B2 = (HEAD_KeyXY  & HEAD_KeyMask) | HEAD_KeyOrB
                B3 = (HEAD_KeyXYf  & HEAD_KeyMask) | HEAD_KeyOrC
                B4 = (HEAD_KeyXYt  & HEAD_KeyMask) | HEAD_KeyOrD
            
                keys.FKeyBytes = (B1, B2, B3, B4)
                keys.F32Keys = bytearray("[(C) Copyright Mr. Dong Shiwei.]")
                for i in range(len(keys.F32Keys)):
                        keys.F32Keys[i] &= keys.FKeyBytes[ i % 4]         
                
		return keys
		
	def __init_chess_board(self,  man_str, version, keys = None):
		
		tmpMan =bytearray([0 for x in range(32)])
		man_buff =bytearray(man_str)
		
		if keys == None:
			for i in range(32) :
				tmpMan[i] = man_buff[i]
			return tmpMan
			
		for i in range(32) :
			if version >= 12:
                                tmpMan[(keys.KeyXY + i + 1) & 0x1F] =  man_buff[i]
                        else :
                                  tmpMan[i] =  man_buff[i]
                                  
		for i in range(32) :
			tmpMan[i] = (tmpMan[i] - keys.KeyXY) & 0xFF
			if (tmpMan[i] > 89) :
				tmpMan[i] = 0xFF
     
		return tmpMan
	
	def __decode_buff(self, keys, buff) : 
		
                nPos = 0x400
                de_buff =bytearray(buff)
                
                for i in range(len(buff)) :
                        KeyByte = keys.F32Keys[(nPos + i) % 32]
			de_buff[i] = (de_buff[i] - KeyByte) & 0xFF
		
                return str(de_buff)
	
                                
        def __read_init_info(self, buff_decoder, version, keys):
                
                step_info = buff_decoder.read_bytes(4)
                        
                annote_len = 0        
		if version <= 0x0A:
                        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
                        annote_len = buff_decoder.read_int()
                else: 
                        #高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
                        step_info[2] &= 0xE0
                        if (step_info[2] & 0x20) : #有注释
                                annote_len = buff_decoder.read_int() - keys.KeyRMKSize
                                
                return buff_decoder.read_str(annote_len) if (annote_len > 0) else None
        	
	def __read_steps(self, buff_decoder, version, keys, parent, checker):
                
                step_info = buff_decoder.read_bytes(4)
                
                if len(step_info) == 0:
                        return

                annote_len = 0
                has_next_step = False
                has_var_step = False
                checker_bak = copy.deepcopy(checker)
                
                if version <= 0x0A:
                        #低版本在走子数据后紧跟着注释长度，长度为0则没有注释
                        if (step_info[2] & 0xF0) :
                               has_next_step = True
                        if (step_info[2] & 0x0F) :
                               has_var_step = True #有变着
                        annote_len = buff_decoder.read_int()
                        
                        step_info[0] = (step_info[0] - 0x18) & 0xFF;
                        step_info[1] = (step_info[1] - 0x20) & 0xFF;
                        
                else : 
                        #高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
                        step_info[2] &= 0xE0
                        if (step_info[2] & 0x80) :  #有后续
                                has_next_step = True
                        if (step_info[2] & 0x40) :  #有变招
                                has_var_step = True
                        if (step_info[2] & 0x20) : #有注释
                                annote_len = buff_decoder.read_int() - keys.KeyRMKSize
                                 
                        step_info[0] = (step_info[0] - 0x18 - keys.KeyXYf) & 0xFF
                        step_info[1] = (step_info[1] - 0x20 - keys.KeyXYt) & 0xFF
                       
                move_from, move_to = _decode_pos2(step_info)
                annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None
                if checker and checker.move(move_from, move_to):
                        curr_move = ChessMove((move_from, move_to), annotation = annote)
                        #print curr_move.move_str(), has_next_step, has_var_step
                        parent.append_next_move(curr_move)
                        good_move = curr_move
                else:
                        #print "bad move at", move_from, move_to
                        #checker.dump()        
                        good_move = parent
                        
                if has_next_step :
                        self.__read_steps(buff_decoder, version, keys, good_move, checker)    
                        
                if has_var_step :
                        #print move_to_str(parent.next_move.move), 'has var'
                        self.__read_steps(buff_decoder, version, keys, parent, checker_bak)

	def load(self, full_file_name, read_annotation = True):
                
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
		
		if magic != "XQ":
			return None
		
                book_info = {}
                
                book_info["book_source"] = "XQF"
                book_info["book_version"] = version
                book_info["book_type"] =  ucType + 1
                
                if ucRes <= 4: #It's really some file has value 4
                        book_info["Result"] = self.result_dict[ucRes]
                else:
                        print "Bad Result  ", ucRes, full_file_name 
                        book_info["Result"] = '*'
                        
                if ucRedPlayerNameLen > 0:
                        try:
                                book_info["Red"] = szRedPlayerName[:ucRedPlayerNameLen].decode("GB18030")
                        except : pass
                        
                if ucBlackPlayerNameLen > 0:
                        try:
                                book_info["Black"] = szBlackPlayerName[:ucBlackPlayerNameLen].decode("GB18030")
                        except : pass
                        
                if ucTitleLen > 0:
                        try:
                                book_info["Game"] = szTitle[:ucTitleLen].decode("GB18030")
                        except: pass
                        
                if ucMatchNameLen > 0:
                        try:
                                book_info["Event"] = szMatchName[:ucMatchNameLen].decode("GB18030")
                        except: pass
                        
                path, file_name=os.path.split(full_file_name)
                '''
                if book_info["Result"] == '*' :
                        if (u"先胜" in file_name) and (u"先和" not in file_name) and (u"先负" not in file_name) :
                                book_info["Result"] = '1-0'
                        elif (u"先负" in file_name) and (u"先和" not in file_name) and (u"先胜" not in file_name) :
                                book_info["Result"] = '0-1'
                        elif (u"先和" in file_name) and (u"先负" not in file_name) and (u"先胜" not in file_name) :
                                book_info["Result"] = '1/2-1/2'
                '''
                if (version <= 0x0A):
                        keys = None
                        chess_mans = self.__init_chess_board(ucBoard, version)
                        step_base_buff =XQFBuffDecoder(contents[0x400:]) 
                else:
                        keys = self.__init_decrypt_key(crypt_keys)
                        chess_mans = self.__init_chess_board(ucBoard, version, keys)	
                        step_base_buff = XQFBuffDecoder(self.__decode_buff(keys, contents[0x400:])) 
		
                chess_board = Chessboard()
                checker = MoveChecker()
                
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
                                fen_ch = chr(ord(chessman_kinds[man_index]) +side * 32)
                                chess_board.create_chessman_from_fench(fen_ch, pos)
                                
                #checker.dump()
                chess_board.move_side = ChessSide.RED
                init_fen = chess_board.to_fen()
                checker.from_fen(init_fen)
                book_annotation = self.__read_init_info(step_base_buff, version, keys)
                
                book = ChessBook(init_fen, book_annotation)
                book.info = book_info
                
                self.__read_steps(step_base_buff, version, keys, book, checker)
                
                #Guess Move side 
                first_move = book.next_move
                if first_move :
                    man = chess_board.chessman_of_pos(first_move.move[0])
                    if man.side != ChessSide.RED:  
                        chess_board.move_side = ChessSide.BLACK
                        book.init_fen = chess_board.to_fen()
                                                  
                return book
                
#-----------------------------------------------------#
if __name__ == '__main__':
    
    loader = XQFLoader()
    '''
    book = loader.load(u"test\\XQF_FiveGoatsTest.xqf")
    book.dump_info()
    print 'verified', book.verify_moves()
    #moves = book.dump_moves()
    #print len(moves)
    '''
    book = loader.load(u"test\\XQF_EmptyTest.xqf")
    book.dump_info()
    '''
    book = loader.load(u"test\\XQF_BadMoveTest1.xqf")
    book.dump_info()
    print book.init_fen
    print 'verified', book.verify_moves()
    
    book = loader.load(u"test\\XQF_BadMoveTest2.xqf")
    book.dump_info()
    print book.init_fen
    print book.annotation    
    print 'verified', book.verify_moves()
    '''
    
    book = loader.load(u"test\\XQF_BadMoveTest3.xqf")
    #book = loader.load(u"test\\XQF_BadMoveTest4.xqf")
    #book = loader.load(u"test\\XQF_WildHouse.xqf")
    book.dump_info()
    moves = book.dump_chinese_moves()
    #print len(moves)
    print 'verified', book.verify_moves()
    with open(u"bad_moves.txt", "wb") as f: 
        for move_it in moves:
                f.write(move_it.encode('utf-8')+'\n')
    #print 'verified', book.verify_moves()
    