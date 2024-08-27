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
import re

from .exception import CChessException
from .common import FULL_INIT_FEN
from .board import ChessBoard


#读取PGN文件的简易版本

#-----------------------------------------------------#
def read_from_pgn(file_name):
    #避免循环导入
    from .game import Game
    
    board = ChessBoard(FULL_INIT_FEN)
    game = Game(board)
    
    with open(file_name) as file:
        flines = file.readlines()

    lines = []
    for line in flines:
        it = line.strip()

        if len(it) == 0:
            continue

        lines.append(it)

    lines = __get_headers(game, lines)
    #lines, docs = __get_comments(lines)
    #infos["Doc"] = docs
    __get_steps(game, lines)
    
    return game
    
def __get_headers(game, lines):

    index = 0
    for it in lines:
        line = it.strip()
        #匹配 [] 并取出包含的内容
        pattern1 = r'\[([^\[\]]*)\]'
        #匹配并捕获xxx和YYYY（不包括引号），且它们之间至少有一个空格  
        pattern2 = r'(\w+)\s+"\s*([^"]+)"' 
        matches = re.findall(pattern1, line) 
        if len(matches) == 0: 
            return lines[index:]
        for text in matches:
            #print(text)
            match = re.search(pattern2, text)    
            if match:  
                # match.groups()会返回一个包含所有捕获组的元组  
                # 我们可以通过索引来访问它们  
                name = match.group(1).lower()  
                value = match.group(2)  
                if name.lower() == 'fen':
                    game.init_board = ChessBoard(value)
                else:
                    game.info[name] = value
                
        #if len(items) < 3:
        #    raise CChessException(f"Format Error on line {index + 1}")

        #self.infos[str(items[0]).strip()] = items[1].strip()

        index += 1


def __get_comments(lines):

    if lines[0][0] != "{":
        return (lines, None)

    docs = lines[0][1:]

    #处理一注释行的情况
    if docs[-1] == "}":
        return (lines[1:], docs[:-1].strip())

    #处理多行注释的情况
    index = 1

    for line in lines[1:]:
        if line[-1] == "}":
            docs = docs + "\n" + line[:-1]
            return (lines[index + 1:], docs.strip())

        docs = docs + "\n" + line
        index += 1

    #代码能运行到这里，就是出了异常了
    raise CChessException("Comments not closed")


def __get_steps(game, lines):
    
    steps = []
    
    board = game.init_board.copy()
      
    for line in lines:
        if line in ["*", "1-0", "0-1", "1/2-1/2"]:
            return steps

        for step, it in enumerate(line.split(" ")):
            if it in ["*", "1-0", "0-1", "1/2-1/2"]:
                break
            if it.endswith('.'):
                continue
            
            move = board.move_text(it)
            if move is None:
               return game
            board.next_turn()
            game.append_next_move(move)
                       
    return game
    