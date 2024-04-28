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
from cchess import *

#result_dict = {'红胜': RED_WIN, '黑胜': BLACK_WIN, '和棋': PEACE}
result_dict = {'红胜': '1-0', '黑胜': '0-1', '和棋': '1/2-1/2'}


def load_move_txt(txt_file):
    with open(txt_file, "rb") as f:
        lines = f.readlines()
    fen = lines[0].strip().decode('utf-8')
    moves = [it.strip().decode('utf-8') for it in lines[1:-1]]
    result = result_dict[lines[-1].strip().decode('utf-8')]
    return (fen, moves, result)


class TestReaderXQF():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))

    def teardown_method(self):
        pass

    def test_base(self):
        game = read_from_xqf(Path("data", "WildHouse.xqf"))
        moves = game.dump_moves()
        #assert moves == ''

    def test_k1(self):
        fen, moves, result = load_move_txt(Path("data", "test1_move.txt"))
        game = read_from_xqf(Path("data", "test1.xqf"))
        assert game.init_board.to_fen() == fen
        assert game.info['result'] == result

        #game.print_init_board()
        m = game.dump_text_moves()[0]
        assert len(m) == len(moves)
        for i in range(len(m)):
            assert m[i] == moves[i]
