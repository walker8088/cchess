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
import os
from pathlib import Path

from cchess import Game

#result_dict = {'红胜': RED_WIN, '黑胜': BLACK_WIN, '和棋': PEACE}
result_dict = {'红胜': '1-0', '黑胜': '0-1', '和棋': '1/2-1/2'}

class TestReaderCbf():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))

    def teardown_method(self):
        pass

    def test_read_cbf(self):
        m_text = ['炮二平五', '炮８平５', '马二进三', '马８进７', '车一进一', '车９平８', '车一平六', '车８进６', '车六进七', '马２进１', '车九进一', '车８平７', '车九平四', '士４进５', '马八进九', '炮２进２', '车六退三', '卒１进１', '车四进七', '炮５平４', '兵五进一', '象３进５', '车四退六', '炮２平３', '炮五平七', '车１平２', '炮七进三', '卒３进１', '兵五进一', '卒５进１', '车六平五', '车２进３', '炮八平五', '马１进３', '车五平七', '马７进５', '车七平九', '马３进４', '车九平五', '马４进６', '车五退二', '马５进７', '车五平六', '马７进５', '车六平五', '马６退７', '车四进三', '车７进１', '车五进一', '车２进１', '车四平八', '马７进５', '仕六进五', '车７进２', '车八退一', '车７退４', '兵九进一', '卒７进１', '车八平七', '炮４进１', '炮五平八', '炮４平８', '帅五平六', '炮８进６', '帅六进一', '炮８退４', '炮八进二', '马５进３', '车七退一', '炮８平２', '马九进八', '车７平２', '兵九进一', '卒７进１', '车七进三']
        
        game = Game.read_from(Path("data", "test2.cbf"))
        moves = game.dump_text_moves()
        assert len(moves) == 1
        move = moves[0]
        assert len(move) == 75
        for index, m in enumerate(move):
            assert m == m_text[index]
            
        assert game.verify_moves() is True
    