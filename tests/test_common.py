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

from cchess import RED, BLACK, FULL_INIT_FEN
from cchess.common import fench_to_txt_name, text_to_fench, get_fen_pieces, get_fen_type, get_fen_type_detail

class TestCommon():
    def test_fench_to_txt_name(self):
        assert fench_to_txt_name('K') == '帅'
        assert fench_to_txt_name('k') == '将'
        assert fench_to_txt_name('R') == '车'
        assert fench_to_txt_name('r') == '砗'
        assert fench_to_txt_name('N') == '马'
        assert fench_to_txt_name('n') == '碼'
        assert fench_to_txt_name('C') == '炮'
        assert fench_to_txt_name('c') == '砲'
        assert fench_to_txt_name('P') == '兵'
        assert fench_to_txt_name('p') == '卒'
        assert fench_to_txt_name('A') == '仕'
        assert fench_to_txt_name('a') == '士'
        assert fench_to_txt_name('B') == '相'
        assert fench_to_txt_name('b') == '象'
        assert fench_to_txt_name('X') is None  # 不存在的棋子
    
    def test_text_to_fench(self):
        assert text_to_fench('帅', RED) == 'K'
        assert text_to_fench('将', BLACK) == 'k'
        assert text_to_fench('车', RED) == 'R'
        assert text_to_fench('车', BLACK) == 'r'
        assert text_to_fench('马', RED) == 'N'
        assert text_to_fench('马', BLACK) == 'n'
        assert text_to_fench('炮', RED) == 'C'
        assert text_to_fench('炮', BLACK) == 'c'
        assert text_to_fench('兵', RED) == 'P'
        assert text_to_fench('卒', BLACK) == 'p'
        assert text_to_fench('仕', RED) == 'A'
        assert text_to_fench('士', BLACK) == 'a'
        assert text_to_fench('相', RED) == 'B'
        assert text_to_fench('象', BLACK) == 'b'
        assert text_to_fench('不存在', RED) is None
    
    def test_get_fen_pieces(self):
        pieces = get_fen_pieces(FULL_INIT_FEN)
        assert pieces['R'] == 2  # 红车
        assert pieces['N'] == 2  # 红马
        assert pieces['C'] == 2  # 红炮
        assert pieces['P'] == 5  # 红兵
        assert pieces['K'] == 1  # 红帅
        assert pieces['A'] == 2  # 红仕
        assert pieces['B'] == 2  # 红相
        assert pieces['r'] == 2  # 黑车
        assert pieces['n'] == 2  # 黑马
        assert pieces['c'] == 2  # 黑炮
        assert pieces['p'] == 5  # 黑卒
        assert pieces['k'] == 1  # 黑将
        assert pieces['a'] == 2  # 黑士
        assert pieces['b'] == 2  # 黑象
        
        # 空棋盘
        empty_fen = '9/9/9/9/9/9/9/9/9/9 w'
        pieces = get_fen_pieces(empty_fen)
        assert len(pieces) == 0
    
    def test_get_fen_type(self):
        # 初始局面
        title = get_fen_type(FULL_INIT_FEN)
        assert title == '车马炮兵'
        
        # 残局
        endgame_fen = '4k4/9/9/9/9/9/9/9/9/4K4 w'
        title = get_fen_type(endgame_fen)
        assert title == ''
        
        # 只有车
        rook_fen = '4k4/9/9/9/9/9/9/9/9/3K1R3 w'
        title = get_fen_type(rook_fen)
        assert title == '车'
        
        # 车马
        rook_knight_fen = '4k4/9/9/9/9/9/9/9/4N4/3K1R3 w'
        title = get_fen_type(rook_knight_fen)
        assert title == '车马'
    
    def test_get_fen_type_detail(self):
        # 初始局面
        red_title, black_title = get_fen_type_detail(FULL_INIT_FEN)
        assert '车' in red_title
        assert '马' in red_title
        assert '炮' in red_title
        assert '兵' in red_title
        assert '车' in black_title
        assert '马' in black_title
        assert '炮' in black_title
        assert '卒' in black_title
        
        # 只有帅将
        king_fen = '4k4/9/9/9/9/9/9/9/9/4K4 w'
        red_title, black_title = get_fen_type_detail(king_fen)
        assert red_title == '帅'
        assert black_title == '将'
        
        # 单子
        single_fen = '4k4/9/9/9/9/9/9/9/9/3K1R3 w'
        red_title, black_title = get_fen_type_detail(single_fen)
        assert red_title == '单车'
        assert black_title == '将'
        
        # 双车
        double_rook_fen = '4k4/9/9/9/9/9/9/9/9/3K1R1R3 w'
        red_title, black_title = get_fen_type_detail(double_rook_fen)
        assert '双车' in red_title or '车' in red_title
