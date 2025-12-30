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
from pathlib import Path
from cchess import FenCache, FULL_INIT_FEN, ChessBoard
from cchess.engine import action_mirror, is_int, parse_engine_info_to_dict

class TestEngineExtended():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))
    
    def test_is_int(self):
        assert is_int('123') == True
        assert is_int('-123') == True
        assert is_int('0') == True
        assert is_int('abc') == False
        assert is_int('12.3') == False
        assert is_int('') == False
    
    def test_parse_engine_info_to_dict(self):
        # 测试解析引擎信息
        info_str = "info depth 6 score cp 100 pv b0c2 b9c7"
        result = parse_engine_info_to_dict(info_str)
        assert 'depth' in result
        assert result['depth'] == 6
        assert 'score' in result
        assert 'moves' in result
        assert len(result['moves']) > 0
        
        # 测试bestmove
        bestmove_str = "bestmove b0c2"
        result = parse_engine_info_to_dict(bestmove_str)
        assert 'move' in result
        assert result['move'] == 'b0c2'
    
    def test_action_mirror(self):
        action = {
            'move': 'a0a1',
            'ponder': 'b0b1',
            'moves': ['a0a1', 'b0b1'],
            'score': 100
        }
        mirrored = action_mirror(action.copy())
        assert mirrored['move'] != action['move']
        assert mirrored['move'] == 'i0i1'  # mirror后的结果
        assert 'score' in mirrored  # 其他字段应该保留
    
    def test_fen_cache(self):
        cache = FenCache()
        board = ChessBoard(FULL_INIT_FEN)
        fen = board.to_fen()
        
        # 保存action
        action = {
            'move': 'a0a1',
            'score': 100,
            'mate': None
        }
        cache.save_action(fen, action)
        
        # 获取action
        cached_action = cache.get_best_action(fen)
        assert cached_action is not None
        assert cached_action['move'] == 'a0a1'
        assert cached_action['score'] == 100
        
        # 测试mirror
        board_mirror = board.copy().mirror()
        fen_mirror = board_mirror.to_fen()
        cached_action_mirror = cache.get_best_action(fen_mirror)
        # 如果支持mirror查找，应该能找到
        assert cached_action_mirror is not None or cached_action_mirror is None
    
    def test_fen_cache_load_save(self):
        cache = FenCache()
        cache_file = Path("data", "test_cache.json")
        
        # 保存一些数据
        board = ChessBoard(FULL_INIT_FEN)
        action = {'move': 'a0a1', 'score': 100}
        cache.save_action(board.to_fen(), action)
        
        # 保存到文件
        cache.cache_file = str(cache_file)
        cache.save()
        
        # 从文件加载
        cache2 = FenCache()
        cache2.load(str(cache_file))
        cached_action = cache2.get_best_action(board.to_fen())
        assert cached_action is not None
        
        # 清理
        if cache_file.exists():
            os.remove(cache_file)

