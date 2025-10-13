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

from cchess import Game

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
        game = Game.read_from(Path("data", "game_test.xqf"))
        moves = game.dump_iccs_moves()
        assert len(moves) == 1
        assert game.verify_moves() is True
    
    def test_branchs_5(self):
        game = Game.read_from(Path("data", "test_5_variations.xqf"))
        assert game.verify_moves() is True
        assert game.info['branchs'] == 5
        
        moves = game.dump_iccs_moves()
        assert len(moves) == 5
        
        move_text = ('炮二平五,炮８平５,马二进三,马８进７,兵三进一,车９平８',
                     '炮二平五,炮８平５,马二进三,马８进７,车一平二,车９进１,车二进六,车９平４',
                     '炮二平五,炮８平５,马二进三,马８进７,车一平二,卒７进１,兵七进一,车９进１',
                     '炮二平五,炮８平５,马二进三,马８进７,车一进一,车９平８,车一平六,马２进３,马八进七,卒３进１',
                     '炮二平六,马８进７,马二进三,车９平８,车一平二',    
                    )
        moves = game.dump_moves(is_tree_mode = False)
        assert len(moves) == 5
        for index, m_line in enumerate(moves):
            print(m_line['name'])
            txt = ','.join([x.to_text() for x in m_line['moves']])
            print(txt)
            assert txt == move_text[index]

        moves = game.dump_moves(is_tree_mode = True)
        assert len(moves) == 5
        
        for index, m_line in enumerate(moves):
            print(m_line['name'])
            txt = ','.join([x.to_text() for x in m_line['moves']])
            print(txt)
            #assert txt == move_text[index]
        
    def test_big_file(self):
        game = Game.read_from(Path("data", "WildHouse.xqf"))
        assert game.info['branchs'] == 139
        
        moves = game.dump_iccs_moves()
        #assert game.verify_moves() is True
        #for m_line in moves:
        #    print(m_line)
        #moves = game.dump_moves(is_tree_mode = False)
        #for m_line in moves:
        #    print(m_line['name'])
        #    print(','.join([x.to_text() for x in m_line['moves']]))

        moves = game.dump_moves(is_tree_mode = True)
        #for m_line in moves:
        #    print(m_line['name'])
        #    print(','.join([x.to_text() for x in m_line['moves']]))
            
    def test_k1(self):
        fen, moves, result = load_move_txt(Path("data", "test1_move.txt"))
        game = Game.read_from(Path("data", "test1.xqf"))
        assert game.init_board.to_fen() == fen
        assert game.info['result'] == result
        assert game.info['branchs'] == 1
        
        #game.print_init_board()
        m = game.dump_text_moves()[0]
        assert len(m) == len(moves)
        for i in range(len(m)):
            assert m[i] == moves[i]


