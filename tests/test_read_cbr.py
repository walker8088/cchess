
import os
from pathlib import Path

import cchess
from cchess import Game

#lib = cchess.read_from_cbl('D:\\01_MyRepos\\cchess\\tests\\data\\1956年全国象棋锦标赛93局.CBL')

class TestReaderCbr():
    def setup_method(self):
        os.chdir(os.path.dirname(__file__))

    def teardown_method(self):
        pass
    
    def test_read_cbr(self):
        game = Game.read_from(Path("data", "test2.cbr"))
        moves = ','.join(game.dump_text_moves()[0])
        assert moves == '炮二平五,炮８平５'
    
    def test_read_cbl1(self):
        lib = Game.read_from_lib(Path("data", "1989年龙化杯象棋名师邀请赛35局.CBL"))
        assert lib['name'] == '1989年龙化杯象棋名师邀请赛35局'
        assert len(lib['games']) == 38
    
    def test_read_cbl2(self):
        lib = Game.read_from_lib(Path("data", "1956年全国象棋锦标赛93局.CBL"))
        assert lib['name'] == '1956年全国象棋锦标赛93局'
        assert len(lib['games']) == 93
    