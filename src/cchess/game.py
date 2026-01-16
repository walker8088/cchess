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
import pathlib
import datetime as dt
from collections import defaultdict

from .common import FULL_INIT_FEN
from .board import ChessBoard
from .exception import CChessException

# 比赛结果
UNKNOWN, RED_WIN, BLACK_WIN, PEACE = range(4)
result_str = (u"未知", u"红胜", u"黑胜", u"平局")

#存储类型
BOOK_UNKNOWN, BOOK_ALL, BOOK_BEGIN, BOOK_MIDDLE, BOOK_END = range(5)
book_type_str = (u"未知", u"全局", u"开局", u"中局", u"残局")


#-----------------------------------------------------#
class Game(object):
    def __init__(self, board = None, annote = None):
        """创建一个 `Game` 实例。

        参数:
            board (ChessBoard|None): 初始棋盘；若为 None 则使用默认初始棋盘。
            annote (str|None): 比赛注释或元信息。

        初始化走子链的头尾指针以及信息字典 `info`。
        """

        if board is not None:
            self.init_board = board.copy()
        else:
            self.init_board = ChessBoard()
        self.annote = annote
        #初始节点
        self.first_move = None
        #最后节点，追加新的move时，从这个节点后追加
        self.last_move = None

        self.info = defaultdict(str)
        #默认一个分支
        self.info['branchs'] = 1

    def __str__(self):
        """返回游戏信息的字符串表示（通常用于调试）。"""
        return str(self.info)
    
    #当第一步走法就有变招的时候，需多次调用这个函数
    def append_first_move(self, chess_move):
        """将 `chess_move` 添加为游戏的第一个走子节点或作为分支加入。

        若当前没有 `first_move`，则设为首步并更新 `last_move`；否则
        将其作为 `first_move` 的一个分支追加。返回传入的 `chess_move`。
        """
        chess_move.parent = self
        if not self.first_move:
            self.first_move = chess_move
            self.init_board = chess_move.board.copy()
            self.last_move = self.first_move
        else:
            self.first_move.add_variation(chess_move)
        
        return chess_move

    #给当前的最后招法节点增加后续节点，如果已经有后续节点了，则增加后续节点的兄弟节点    
    def append_next_move(self, chess_move):
        """将 `chess_move` 作为当前游戏的下一个走子追加。

        若游戏尚无首步，则将其设为首步并更新 `last_move`；否则委托给
        `last_move.append_next_move` 并更新 `last_move`。返回 self，
        便于链式调用。
        """
        if not self.first_move:
            chess_move.parent = self
            self.first_move = chess_move
            self.init_board = chess_move.board.copy()
            self.last_move = self.first_move
        else:    
            self.last_move.append_next_move(chess_move)
            self.last_move = chess_move
        
        return chess_move
    
    '''
    def add_variation_move(self, chess_move):
        if not self.last_move:
        
        else:    
            self.last_move.add_variation_move(chess_move)
            self.last_move = chess_move
        
        return chess_move
    '''

    def get_children(self):
        if not self.first_move:
            return []
        
        variations = list(self.first_move.get_variations(include_me = True))
        return variations

    def verify_moves(self):
        """验证已记录的走子序列在初始棋盘上是否都合法。

        遍历通过 `dump_iccs_moves` 获取的每条走子线路，逐步执行每个
        ICCS 走法并检查是否返回有效 `Move` 对象；若发现无效走法会
        抛出异常，全部通过则返回 True。
        """
        move_list = self.dump_iccs_moves()
        for index, move_line in enumerate(move_list):
            board = self.init_board.copy()
            for step_no, iccs in enumerate(move_line):
                m = board.move_iccs(iccs)
                if m is None:
                    raise Exception(f"{index}_{step_no}_{iccs} {','.join(move_line)}")
                board.next_turn()
                    
        return True

    def mirror(self):
        """对游戏进行水平镜像：镜像初始棋盘并镜像所有走子。"""
        self.init_board = self.init_board.mirror()
        if self.first_move:
            self.first_move.mirror()

    def flip(self):
        """对游戏进行垂直翻转：翻转初始棋盘并翻转所有走子。"""
        self.init_board = self.init_board.flip()
        if self.first_move:
            self.first_move.flip()

    def swap(self):
        """交换棋子颜色视角：交换初始棋盘并对所有走子执行 swap 操作。"""
        self.init_board = self.init_board.swap()
        if self.first_move:
            self.first_move.swap()

    def iter_moves(self, move=None):
        """按线性顺序迭代走子，从 `move`（或 `first_move`）开始。

        只会沿 `next_move` 链迭代，不会进入分支列表。
        """
        if move is None:
            move = self.first_move
        while move:
            yield move
            move = move.next_move

    def dump_init_board(self):
        """返回初始棋盘的文本视图（用于打印）。"""
        return self.init_board.text_view()

    def dump_moves(self, is_tree_mode = False):
        """序列化游戏中记录的所有走子线路。

        返回一个列表，每个元素表示一条走子线路（包含分支索引和顺序），
        由 `Move.dump_moves` 完成具体递归构造。
        """
        if not self.first_move:
            return []

        move_list = []

        if self.first_move:
            curr_line = self.first_move.init_move_line()
            move_list.append(curr_line)            
            self.first_move.dump_moves(move_list, curr_line, is_tree_mode)
            
        return move_list

    def dump_iccs_moves(self):
        """以 ICCS 字符串形式返回所有走子线路（去掉路径前缀）。"""
        return [[ move.to_iccs() for move in move_line['moves'] ]
            for move_line in self.dump_moves()]
    
    def dump_fen_iccs_moves(self):
        """返回每一步的 (FEN, ICCS) 对，便于调试或分析。"""
        return [[ [move.board.to_fen(), str(move)] for move in move_line['moves'] ]
            for move_line in self.dump_moves()]
                
    def dump_text_moves(self, show_branch = False):
        """以中文可读文本形式返回所有走子线路。"""
        return [[ move.to_text_detail(show_branch, show_annote = False)[0] for move in move_line['moves']]
            for move_line in self.dump_moves()]
      
    def dump_text_moves_with_annote(self):
        """返回 (走法文本, 注释) 元组的列表，用于显示含注释的走子。"""
        return [[(move.to_text(), move.annote) for move in move_line['moves']]
            for move_line in self.dump_moves()]
    
    def dump_moves_line(self):
        """返回沿当前选定分支的一条走子线路（线性，不含分支信息）。"""
        if not self.first_move:
            return []
        return [[str(move) for move in move_line['moves']]
                for move_line in self.dump_moves()]
        
    def move_line_to_list(self, move = None):
        if not move:
            move = self.first_move
        
        move_line = []
        while move:
            move_line.append(move)
            move = move.next_move
        
        return move_line    
        
    def make_branchs_tag(self):
        if not self.first_move:
            return
        self.first_move.make_branchs_tag(0, 0)            
            
    def print_init_board(self):
        """将初始棋盘的文本视图打印到标准输出。"""
        for line in self.init_board.text_view():
            print(line)

    def print_text_moves(self, steps_per_line = 2, show_annote = False):
        """以格式化方式打印走子文本，支持每行若干步并显示注释。

        参数:
            steps_per_line (int): 每行显示的步数（每步包含红黑双方，共计 2 个走子）
            show_annote (bool): 是否显示每步的注释
        """
        moves = self.dump_text_moves_with_annote()
        for index, line in enumerate(moves):
            if len(moves) > 1:
                print(f'第 {index+1} 分支')
            line_move = '' 
            for i, (text, annote) in enumerate(line):
                if (i % 2) == 0:
                    line_move += f' {(i // 2 + 1):02d}.{text}'
                else:
                    line_move += f' {text}'
                if show_annote and annote:
                    line_move += f'[{annote}]'
                i += 1
                if (i % (steps_per_line * 2)) == 0:
                    print(line_move)
                    line_move = ''
            if line_move:
                print(line_move)
                
    def dump_info(self):
        """打印存储在 `info` 字典中的游戏元信息键值对。"""
        for key in self.info:
            print(key, self.info[key])
    
    @staticmethod
    def from_ubb_dhtml(txt):
        """从 UBB 格式的 DHTML 文本中读取并返回 Game 对象（静态方法）。"""
        from .read_txt import read_from_ubb_dhtml
        
        return read_from_ubb_dhtml(txt)

    @staticmethod
    def read_from(file_name):
        """从文件中读取棋谱并返回 Game 对象，自动根据文件后缀选择解析器。

        支持的后缀包括 .xqf, .pgn, .cbf, .cbr；函数内部延迟导入对应解析
        模块以避免循环依赖。
        """
        #在函数开始时才导入以避免循环导入
        from .io_xqf import read_from_xqf
        from .read_pgn import read_from_pgn
        from .read_cbf import read_from_cbf
        from .read_cbr import read_from_cbr
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.xqf':
            return read_from_xqf(file_name)
        elif ext == '.pgn':
            return read_from_pgn(file_name)
        elif ext == '.cbf':
            return read_from_cbf(file_name)
        elif ext == '.cbr':
            return read_from_cbr(file_name)
        else:
            raise Exception(f"Unknown file format:{file_name}")
    
    @staticmethod
    def read_from_lib(file_name):
        """从库文件读取（如 .cbl）并返回 Game 对象（静态方法）。"""
        #在函数开始时才导入以避免循环导入
        from .read_cbr import read_from_cbl
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.cbl':
            return read_from_cbl(file_name)
        else:
            raise Exception(f"Unknown lib file format:{file_name}")
    
    def save_to_pgn(self, file_name):
        
        #w = PGNWriter(self)
        #w.write_file(file_name)
        
        init_fen = self.init_board.to_fen()
        with open(file_name, 'w') as f:
            f.write('[Game "Chinese Chess"]\n')
            f.write(f'[Date "{dt.date.today()}"]\n')
            f.write('[Red ""]\n')
            f.write('[Black ""]\n')
            if init_fen != FULL_INIT_FEN:
                f.write(f'[FEN "{self.init_board.to_full_fen()}"]\n')

            if self.annote:
                f.write(f'{{ {self.annote} }}\n')
                
            moves = self.dump_moves()
            if len(moves) > 0:
                move_line = moves[0]['moves']
                for index, m in enumerate(move_line):
                    if (index % 2) == 0:
                        pre_str = f" {index//2+1}."
                    else:
                        pre_str = "    "
                    if m.annote:
                        f.write(f'{pre_str} {m.to_text()} {{ {m.annote} }}\n')
                    else:    
                        f.write(f'{pre_str} {m.to_text()}\n')

            f.write('   *\n')
            f.write('  =========\n')

    def save_to(self, file_name):
        """根据文件扩展名写入对应格式的棋谱文件。
        参数:
            file_name (str): 输出文件路径
        """

        from .io_xqf import XQFWriter
        from .io_pgn import PGNWriter
        
        ext = pathlib.Path(file_name).suffix.lower()
        if ext == '.xqf':
            writer = XQFWriter(self)    
        elif ext == '.pgn':
            writer = PGNWriter(self)    
         
        return writer.save(file_name)
        