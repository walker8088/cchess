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

from collections import OrderedDict

#-----------------------------------------------------#
NO_COLOR, RED, BLACK = (0, 1, 2)

def opposite_color(color):
    return 3 - color


#-----------------------------------------------------#
EMPTY_BOARD = '9/9/9/9/9/9/9/9/9/9'
FULL_INIT_BOARD = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'

EMPTY_FEN = f'{EMPTY_BOARD} w'
FULL_INIT_FEN = f'{FULL_INIT_BOARD} w'

#-----------------------------------------------------#
_h_dict = {
    'a': 'i',
    'b': 'h',
    'c': 'g',
    'd': 'f',
    'e': 'e',
    'f': 'd',
    'g': 'c',
    'h': 'b',
    'i': 'a'
}

_v_dict = {
    '0': '9',
    '1': '8',
    '2': '7',
    '3': '6',
    '4': '5',
    '5': '4',
    '6': '3',
    '7': '2',
    '8': '1',
    '9': '0'
}

#-----------------------------------------------------#
def pos2iccs(p_from, p_to):
    return chr(ord('a') + p_from[0]) + str(
        p_from[1]) + chr(ord('a') + p_to[0]) + str(p_to[1])


def iccs2pos(iccs):
    return ((ord(iccs[0]) - ord('a'), int(iccs[1])), (ord(iccs[2]) - ord('a'),
                                                      int(iccs[3])))

def iccs_mirror(iccs):
    return f'{_h_dict[iccs[0]]}{iccs[1]}{_h_dict[iccs[2]]}{iccs[3]}'


def iccs_flip(iccs):
    return f'{iccs[0]}{_v_dict[iccs[1]]}{iccs[2]}{_v_dict[iccs[3]]}'


def iccs_swap(iccs):
    return f'{_h_dict[iccs[0]]}{_v_dict[iccs[1]]}{_h_dict[iccs[2]]}{_v_dict[iccs[3]]}'
    
def iccs_list_mirror(iccs_list):
    return [iccs_mirror(x) for x in iccs_list]

#-----------------------------------------------------#
_fench_name_dict = {
    'K': "帅",
    'k': "将",
    'A': "仕",
    'a': "士",
    'B': "相",
    'b': "象",
    'N': "马",
    'n': "马",
    'R': "车",
    'r': "车",
    'C': "炮",
    'c': "炮",
    'P': "兵",
    'p': "卒"
}

_name_fench_dict = {
    "帅": 'K',
    "将": 'k',
    "仕": 'A',
    "士": 'a',
    "相": 'B',
    "象": 'b',
    "马": 'n',
    "车": 'r',
    "炮": 'c',
    "兵": 'P',
    "卒": 'p'
}

_fench_txt_name_dict = {
    'K': "帅",
    'A': "仕",
    'B': "相",
    'R': "车",
    'N': "马",
    'C': "炮",
    'P': "兵",
    'k': "将",
    'a': "士",
    'b': "象",
    'r': "砗",
    'n': "碼",
    'c': "砲",
    'p': "卒"
}

def fench_to_txt_name(fench):    
    if fench not in _fench_txt_name_dict:
        return None
        
    return _fench_txt_name_dict[fench]


def fench_to_text(fench):
    return _fench_name_dict[fench]

def text_to_fench(text, color):
    if text not in _name_fench_dict:
        return None
    fench = _name_fench_dict[text]
    return fench.lower() if color == BLACK else fench.upper()

def fench_to_species(fen_ch):
    return fen_ch.lower(), BLACK if fen_ch.islower() else RED

#-----------------------------------------------------#
def get_move_color(fen):
    color = fen.rstrip().split(' ' )[1].lower()
    return RED if color == 'w' else BLACK

def fen_mirror(fen):
    from .board import ChessBoard
    
    b = ChessBoard(fen)
    return b.mirror().to_fen()

#-----------------------------------------------------#
def full2half(text):
    # 全角到半角的映射
    fullwidth_map = {
        '１': '1', '２': '2', '３': '3', '４': '4', '５': '5',
        '６': '6', '７': '7', '８': '8', '９': '9'
    }
    
    # 使用 translate 方法进行批量替换
    translation_table = str.maketrans(fullwidth_map)
    return text.translate(translation_table)

def half2full(text):
    # 半角到全角的映射
    halfwidth_map = {
        '1': '１', '2': '２', '3': '３', '4': '４', '5': '５',
        '6': '６', '7': '７', '8': '８', '9': '９'
    }
    
    # 使用 translate 方法进行批量替换
    translation_table = str.maketrans(halfwidth_map)
    return text.translate(translation_table)
#-----------------------------------------------------#
p_count_dict = {
    "R1":'车',
    "R2":'双车',
    "N1":'马',
    "N2":'双马',
    "C1":'炮',
    "C2":'双炮',
    "P1":'兵',
    "P2":'双兵',
    "P3":'三兵',
    "P4":'多兵',
    "P5":'多兵',
    'A1':'仕',
    'A2':'双仕',    
    'B1':'相',
    'B2':'双相',    
}

p_dict = {
    "R":'车',
    "N":'马',
    "C":'炮',
    "P":'兵',
    'A':'士',
    'B':'象',    
}

def get_fen_pieces(fen):
    pieces = OrderedDict()
    fen_base = fen.split(' ')[0]
    for ch in fen_base:
        if not ch.isalpha():
            continue
        if ch not in pieces:
            pieces[ch] = 0
        pieces[ch] += 1
    return pieces

def get_fen_type(fen):

    pieces = get_fen_pieces(fen)
    for ch in ['K', 'A', 'B']:
        if ch in pieces:
            pieces.pop(ch)
    
    title = ''
    p_count = 0
    for fench in ['R', 'N', "C", 'P']:
        if fench not in pieces:
            continue
 
        title += p_dict[f'{fench}']
        p_count += 1
        
    return title

def get_fen_type_detail(fen):
    pieces = get_fen_pieces(fen)
    
    title_red = ''
    p_count = 0
    for fench in ['R', 'N', "C", 'P', "A", "B"]:
        if fench not in pieces:
            continue
        title_red += p_count_dict[f'{fench}{pieces[fench]}']
        p_count += 1
    
    title_red = title_red.replace('双仕双相', '仕相全')
    if title_red in ['车', '马', '炮', '兵', '仕', '相']:
        title_red = '单' + title_red
    
    if title_red == '':
        title_red = '帅'
        
    p_count = 0
    title_black = ''
    for fench in ['r', 'n', "c", 'p', 'a', 'b']:
        if fench not in pieces:
            continue
        ch_upper = fench.upper()    
        title_black += p_count_dict[f'{ch_upper}{pieces[fench]}']
        p_count += 1
    
    title_black = title_black.replace('兵', '卒')
    title_black = title_black.replace('仕', '士')
    title_black = title_black.replace('相', '象')
    title_black = title_black.replace('双士双象', '士象全')
    
    if title_black in ['车', '马', '炮', '卒', '士', '象']:
        title_black = '单' + title_black
    
    if title_black == '':
        title_black = '将'
    
    return (title_red, title_black)
