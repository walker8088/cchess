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

#-----------------------------------------------------#
NO_COLOR, RED, BLACK = (0, 1, 2)

def opposite_color(color):
    return 3 - color


#-----------------------------------------------------#
FULL_INIT_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w'
EMPTY_BOARD = '9/9/9/9/9/9/9/9/9/9'
EMPTY_FEN = f'{EMPTY_BOARD} w'

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

#-----------------------------------------------------#
