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


from .board import ChessBoard, FULL_INIT_FEN
from .game import Game
from .exception import CChessException

#读取PGN文件的简易版本

#-----------------------------------------------------#
def read_from_pgn(file_name):
    
    board = ChessBoard(FULL_INIT_FEN)
    
    with open(file_name) as file:
        flines = file.readlines()

    lines = []
    for line in flines:
        it = line.strip()

        if len(it) == 0:
            continue

        lines.append(it)

    lines = __get_headers(lines)
    
    game = Game(board)
    
    #lines, docs = __get_comments(lines)
    #infos["Doc"] = docs
    __get_steps(lines, game)
    
    return game
    
def __get_headers(lines):

    index = 0
    for it in lines:
        line = it.strip()
        if line[0] != "[":
            return lines[index:]

        if line[-1] != "]":
            raise CChessException(f"Format Error on line {index + 1}")

        items = line[1:-1].split("\"")

        if len(items) < 3:
            raise CChessException(f"Format Error on line {index + 1}")

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


def __get_steps(lines, game):
    
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
            
            #print(game.first_move.to_text(), game.last_move.to_text())
            #print(move.next_move)
            '''
            count = 0
            m = game.first_move
            while m is not None:
                print(count, m.to_text())
                m = m.next_move
                count += 1
                if count > 10:
                    break
            '''
            #steps.append(it)
            
    return game
    