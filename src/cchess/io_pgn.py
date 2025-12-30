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

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

#from .exception import CChessException
#from .common import FULL_INIT_FEN
#from .board import ChessBoard

#-----------------------------------------------------#

class Color(Enum):
    RED = "red"
    BLACK = "black"

@dataclass
class Move:
    """表示一个棋步"""
    san: str  
    comment: Optional[str] = None
    variations: List['MoveNode'] = None
    
    def __post_init__(self):
        if self.variations is None:
            self.variations = []

@dataclass
class MoveNode:
    """表示棋步树节点"""
    move: Move
    next: Optional['MoveNode'] = None
    
    def add_variation(self, variation: 'MoveNode'):
        """添加变招"""
        self.move.variations.append(variation)

class PGNGame:
    """表示一局棋"""
    
    def __init__(self):
        self.headers: Dict[str, str] = {}
        self.moves: Optional[MoveNode] = None
        self.result: Optional[str] = None
    
    def set_header(self, key: str, value: str):
        """设置头信息"""
        self.headers[key] = value
    
    def add_move(self, san: str, comment: Optional[str] = None) -> MoveNode:
        """添加主变招的棋步"""
        move = Move(san, comment)
        new_node = MoveNode(move)
        
        if self.moves is None:
            self.moves = new_node
        else:
            current = self.moves
            while current.next:
                current = current.next
            current.next = new_node
        
        return new_node

#-----------------------------------------------------#
class PGNParser:
    """PGN解析器"""
    
    def __init__(self):
        self.tokens = []
        self.current_token_index = 0
    
    def tokenize(self, text: str) -> List[Dict[str, Any]]:
        """将PGN文本分词"""
        tokens = []
        i = 0
        length = len(text)
        
        while i < length:
            char = text[i]
            
            # 跳过空白字符
            if char.isspace():
                i += 1
                continue
            
            # 注释
            if char == '{':
                comment_end = text.find('}', i + 1)
                if comment_end == -1:
                    raise ValueError("未匹配的注释结束符 '}'")
                comment = text[i+1:comment_end]
                tokens.append({'type': 'comment', 'value': comment})
                i = comment_end + 1
                continue
            
            # 变招开始
            if char == '(':
                tokens.append({'type': 'variation_start', 'value': '('})
                i += 1
                continue
            
            # 变招结束
            if char == ')':
                tokens.append({'type': 'variation_end', 'value': ')'})
                i += 1
                continue
            
            # 棋步编号
            if char.isdigit():
                j = i
                while j < length and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                move_number = text[i:j]
                if '.' in move_number:
                    tokens.append({'type': 'move_number', 'value': move_number})
                i = j
                continue
            
            # 棋步（字母、数字、+、#、=等）
            if char.isalpha() or char in '+#=':
                j = i
                while j < length and (text[j].isalnum() or text[j] in '+#=.'):
                    j += 1
                move = text[i:j]
                tokens.append({'type': 'move', 'value': move})
                i = j
                continue
            
            # 结果
            if char in ['1', '0', '½'] and any(c in text[i:i+3] for c in ['-', '/']):
                j = i
                while j < length and text[j] not in ' \t\n)':
                    j += 1
                result = text[i:j]
                tokens.append({'type': 'result', 'value': result})
                i = j
                continue
            
            i += 1
        
        return tokens
    
    def parse_headers(self, lines: List[str]) -> Dict[str, str]:
        """解析头信息"""
        headers = {}
        header_pattern = re.compile(r'^\s*\[\s*(\w+)\s+"([^"]*)"\s*\]\s*$')
        
        for line in lines:
            match = header_pattern.match(line)
            if match:
                key, value = match.groups()
                headers[key] = value
        
        return headers
    
    def parse_moves(self, tokens: List[Dict[str, Any]]) -> tuple[Optional[MoveNode], Optional[str]]:
        """解析棋步序列"""
        if not tokens:
            return None, None
        
        root = MoveNode(Move("root"))
        current_line = [root]
        stack = [current_line]
        current_node = root
        result = None
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token['type'] == 'move_number':
                # 跳过棋步编号
                pass
            
            elif token['type'] == 'move':
                new_node = MoveNode(Move(token['value']))
                
                if current_node == root:
                    current_node.next = new_node
                    current_node = new_node
                else:
                    current_node.next = new_node
                    current_node = new_node
                
                current_line.append(new_node)
            
            elif token['type'] == 'comment':
                if current_node != root:
                    current_node.move.comment = token['value']
            
            elif token['type'] == 'variation_start':
                # 保存当前主线
                stack.append(current_line.copy())
                # 开始新变招
                variation_root = MoveNode(Move("variation_root"))
                current_line = [variation_root]
                current_node = variation_root
            
            elif token['type'] == 'variation_end':
                # 结束当前变招，回到主线
                variation_nodes = current_line[1:]  # 跳过根节点
                if variation_nodes:
                    # 找到变招应该附加的节点
                    prev_main_line = stack[-1]
                    parent_node = prev_main_line[-1]
                    
                    # 创建变招链表
                    variation_head = variation_nodes[0]
                    current_var = variation_head
                    for node in variation_nodes[1:]:
                        current_var.next = node
                        current_var = node
                    
                    parent_node.move.variations.append(variation_head)
                
                current_line = stack.pop()
                current_node = current_line[-1]
            
            elif token['type'] == 'result':
                result = token['value']
                break
            
            i += 1
        
        return root.next, result
    
    def parse(self, pgn_text: str) -> PGNGame:
        """解析完整的PGN文本"""
        game = PGNGame()
        
        # 分割头和棋步部分
        lines = pgn_text.split('\n')
        header_lines = []
        move_lines = []
        
        in_headers = True
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if in_headers and stripped.startswith('['):
                header_lines.append(stripped)
            else:
                in_headers = False
                move_lines.append(stripped)
        
        # 解析头信息
        game.headers = self.parse_headers(header_lines)
        
        # 解析棋步
        moves_text = ' '.join(move_lines)
        tokens = self.tokenize(moves_text)
        moves, result = self.parse_moves(tokens)
        
        game.moves = moves
        game.result = result
        
        return game

    def read_file(self, file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            txts = f.read()
            self.parser(txts)
            
#-----------------------------------------------------#
class PGNWriter:
    """PGN写入器"""
    
    def __init__(self, game):
        self.indent_level = 0
        self.game = game

    def write_headers(self) -> str:
        """写入头信息"""
        lines = []
        standard_headers = ['Event', 'Date', 'Round', 'Red', 'Black', 'Result']
        
        lines.append('[Game "Chinese Chess"]')
        # 先写入标准头信息
        for header in standard_headers:
            if header in self.game.info:
                value = self.game.info[header]
                lines.append(f'[{header} "{value}"]')
        
        # 写入其他头信息
        #for header, value in game.headers.items():
        #    if header not in standard_headers:
        #        lines.append(f'[{header} "{value}"]')
        
        #写入初始局面
        lines.append(f'[Fen "{self.game.init_board.to_fen()}"]')
        
        return '\n'.join(lines)
    
    def write_moves(self, move, curr_sibling_index = 0) -> str:
        """递归写入棋步"""
        if move is None:
            return ""
        
        lines = []
        current = move
        
        while current is not None:
            current_move_number = current.step_index
            
            # 添加棋步编号（红方）
            if current_move_number % 2 == 0:
                lines.append(f"\n{current_move_number//2+1}.")
            
            # 添加棋步
            lines.append(current.to_text())
            
            # 添加注释
            if current.comment:
                lines.append(f"{{{current.comment}}}")
            
            #只有主变才处理变招，避免循环递归
            if curr_sibling_index == 0:
                for index, variation in enumerate(current.get_siblings(include_me = False)):
                    lines.append("\n(")
                    variation_text = self.write_moves(variation, index+1)
                    lines.append(variation_text.strip())
                    lines.append(")\n")
                
            current = current.next_move
            
        return ' '.join(lines)
    
    def write_lines(self) -> str:
        
        if not self.game.first_move:
            return ''

        """写入完整的PGN"""
        lines = []
        
        # 写入头信息
        headers = self.write_headers()
        lines.append(headers)
        
        # 写入棋步
        moves_text = self.write_moves(self.game.first_move)
        lines.append(moves_text)
        
        # 添加结果
        if 'result' in self.game.info:
            lines.append(self.game.info['result'])
        
        return '\n'.join(lines)

    def write_file(self, file_name):
        with open(file_name, 'w') as f:
            lines = self.write_lines()
            f.write(lines)

#-----------------------------------------------------#
