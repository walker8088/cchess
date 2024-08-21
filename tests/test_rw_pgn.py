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

from cchess import read_from_pgn

class TestPGN():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))

    def teardown_method(self):
        pass

    def test_base(self):
        game = read_from_pgn(Path("data", "test.pgn"))
        moves = game.dump_text_moves()
        assert len(moves[0]) == 25
        move_line = ','.join(moves[0])
        assert move_line == '炮二平五,马２进３,马二进三,马８进９,车一进一,象３进５,兵五进一,炮８平６,兵五进一,卒５进１,马三进五,士４进５,车一平六,车１平４,车九进一,炮２进７,车六进八,将５平４,车九平六,将４平５,马五进七,炮６进３,马七进六,炮６平５,炮五进三'
        
        assert len(moves) == 1
        assert game.verify_moves() is True
    
    
    def test_base2(self):
        move_t ='相七进五,炮２平５,兵七进一,马２进３,马八进七,车１平２,车九平八,炮８平６,炮八进四,马８进７,马二进三,车９平８,车一平二,车８进４,炮二平一,车８进５,马三退二,卒７进１,仕四进五,卒５进１,马二进三,炮５进１,炮八进二,士４进５,兵三进一,卒７进１,相五进三,炮５平７,马三进四,炮７进６,马四进六,象３进５,马六进七,炮６平３,炮八退一,士５进４,炮一平五,士６进５,马七进六,将５平６,炮五进三,炮３进３,相三退五,炮３退１,炮五平四,马７进６,马六进四,炮７退８,兵五进一,车２进１,马四进三,将６平５,兵五进一,士５进６,马三退一,炮７平３,仕五进四,后炮退１,兵五平六,前炮进２,车八进三,前炮平１,兵六进一,炮１进３,仕六进五,炮３平２,兵六进一,炮２进２,车八进三,炮１退４,车八平九,炮１平２,车九退二,前炮退１,车九进五,车２退１,车九退四,前炮进１,马一进三,后炮进２,兵六进一,前炮平５,帅五平六,炮５退２,兵一进一,炮５平７,帅六平五,卒３进１,仕五退六,炮７平５,相五退七,卒３进１,马三进一,将５平６,车九进一,炮５平２,马一退三,将６进１,车九进一,后炮退１,车九退一,后炮进１'
        
        game = read_from_pgn(Path("data", "test2.pgn"))
        moves_all = game.dump_text_moves()
        move_line = move_t.split(',')
        assert len(moves_all) == 1
        moves = moves_all[0]
        assert len(moves) == 102
        assert len(moves) == len(move_line)
        for i in range(len(moves)):
            assert moves[i] == move_line[i]
        assert game.verify_moves() is True
        
        game.save_to(Path("data", "test2_out.pgn"))
        
        game2 = read_from_pgn(Path("data", "test2_out.pgn"))
        moves_all = game2.dump_text_moves()
        move_line = move_t.split(',')
        assert len(moves_all) == 1
        moves = moves_all[0]
        assert len(moves) == len(move_line)
        for i in range(len(moves)):
            assert moves[i] == move_line[i]
        assert game2.verify_moves() is True
       