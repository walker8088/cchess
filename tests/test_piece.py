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

from cchess import *

#-----------------------------------------------------#
class TestPiece():
    def test_base(self):
        side = ChessPlayer(NO_COLOR)
        assert side.next() == NO_COLOR
        assert side.opposite() == NO_COLOR
        
        side = ChessPlayer(RED)
        assert side.opposite() == BLACK
        assert side.next() == BLACK
        assert side.next() == RED
        