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

result_dict = {'红胜': RED_WIN, '黑胜': BLACK_WIN, '和棋': PEACE}


def load_move_txt(txt_file):
    with open(txt_file, "rb") as f:
        lines = f.readlines()
    fen = lines[0].strip().decode('utf-8')
    moves = [it.strip().decode('utf-8') for it in lines[1:-1]]
    result = result_dict[lines[-1].strip().decode('utf-8')]
    return (fen, moves, result)


class TestReaderXQF():
    def setup(self):
        os.chdir(os.path.dirname(__file__))

    def teardown(self):
        pass

    def test_base(self):
        game = read_from_xqf(Path("data", "WildHouse.xqf"))
        moves = game.dump_moves()
        #assert moves == ''

    def test_k1(self):
        fen, moves, result = load_move_txt(Path("data", "test1_move.txt"))
        game = read_from_xqf(Path("data", "test1.xqf"))
        game.init_board.move_side = ChessSide.RED
        assert game.init_board.to_fen() == fen
        assert game.info['Result'] == result

        #game.print_init_board()
        m = game.dump_chinese_moves()[0]
        assert len(m) == len(moves)
        for i in range(len(m)):
            assert m[i] == moves[i]


#-----------------------------------------------------#
if __name__ == '__main___':
    '''
    game = read_from_xqf(u"test\\FiveGoatsTest.xqf")
    game.dump_info()
    print 'verified', game.verify_moves()
    #moves = game.dump_moves()
    #print len(moves)
    '''
    game = read_from_xqf(u"test\\EmptyTest.xqf")
    game.dump_info()
    '''
    game = read_from_xqf(u"test\\BadMoveTest1.xqf")
    game.dump_info()
    print game.init_fen
    print 'verified', game.verify_moves()
    
    game = read_from_xqf(u"test\\BadMoveTest2.xqf")
    game.dump_info()
    print game.init_fen
    print game.annotation    
    print 'verified', game.verify_moves()
    '''

    #game = read_from_xqf(u"test\\BadMoveTest3.xqf")
    #game = read_from_xqf(u"test\\BadMoveTest4.xqf")
    game = read_from_xqf(u"test\\WildHouse.xqf")
    game.dump_info()
    #moves = game.dump_moves()
    #moves = game.dump_std_moves()
    #print moves
    game.print_init_board()
    game.print_chinese_moves(3)
    #print len(moves)
    #print 'verified', game.verify_moves()
    #print 'verified', game.verify_moves()

#-----------------------------------------------------#
if __name__ == '__main__':
    from reader_xqf import *
    game = read_from_xqf('test\\ucci_test1.xqf')
    game.init_board.move_side = ChessSide.RED
    game.print_init_board()
    game.print_chinese_moves()
