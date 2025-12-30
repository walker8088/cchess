
import os
from pathlib import Path

import cchess
from cchess import Game

ubb_str = '''
    [DhtmlXQHTML]
    [DhtmlXQ_init]500,350[/DhtmlXQ_init]
    [DhtmlXQ_binit]8979695949392919097717866646260600102030405060708012720323436383[/DhtmlXQ_binit]
    [DhtmlXQ_title]中炮对左三步虎[/DhtmlXQ_title]
    [DhtmlXQ_movelist]77477062796780701927728266652324170710220919001089881216885870761918766658576364187816120708625408688252575466672748676647676646656460826777527277473041542420422423725248674656681810306463303418165657161757566362525478755444594822306261121117165657675534352343575575553555434455656151656948596964474241524445[/DhtmlXQ_movelist]
    [DhtmlXQ_firstnum]0[/DhtmlXQ_firstnum]
    [DhtmlXQ_length]77[/DhtmlXQ_length]
    [DhtmlXQ_type]全局[/DhtmlXQ_type]
    [DhtmlXQ_gametype]慢棋[/DhtmlXQ_gametype]
    [DhtmlXQ_other]第1局[/DhtmlXQ_other]
    [DhtmlXQ_open]中炮对左三步虎[/DhtmlXQ_open]
    [DhtmlXQ_class]其他大师或以上级别大赛[/DhtmlXQ_class]
    [DhtmlXQ_event]2025年第五届上海杯象棋大师公开赛[/DhtmlXQ_event]
    [DhtmlXQ_group]男子组[/DhtmlXQ_group]
    [DhtmlXQ_place]上海[/DhtmlXQ_place]
    [DhtmlXQ_timerule]50分＋20秒[/DhtmlXQ_timerule]
    [DhtmlXQ_round]决赛[/DhtmlXQ_round]
    [DhtmlXQ_table]第01台[/DhtmlXQ_table]
    [DhtmlXQ_date]2025-09-27[/DhtmlXQ_date]
    [DhtmlXQ_result]红胜[/DhtmlXQ_result]
    [DhtmlXQ_red]成都 孟辰[/DhtmlXQ_red]
    [DhtmlXQ_redteam]成都[/DhtmlXQ_redteam]
    [DhtmlXQ_redname]孟辰[/DhtmlXQ_redname]
    [DhtmlXQ_black]江苏 刘柏宏[/DhtmlXQ_black]
    [DhtmlXQ_blackteam]江苏[/DhtmlXQ_blackteam]
    [DhtmlXQ_blackname]刘柏宏[/DhtmlXQ_blackname]
    [DhtmlXQ_refer]网上收集[/DhtmlXQ_refer]
    [DhtmlXQ_generator]南山象棋谱[/DhtmlXQ_generator]
    [/DhtmlXQHTML]
'''

class TestReaderCbr():
    def setup_method(self):
        #os.chdir(os.path.dirname(__file__))
        pass

    def teardown_method(self):
        pass
    
    def test_read_ubb(self):
        game = Game()
        game.from_ubb_dhtml(ubb_str)
        
        for k,v in game.info.items():
            print(f"{k}:{v}")

        moves = game.dump_moves()
        for index, m_line in enumerate(moves):
            txt = ','.join([x.to_text() for x in m_line['moves']])
            print("招法：", txt)
