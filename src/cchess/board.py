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

import copy
import json
from functools import reduce

from .exception import CChessException
from .common import fench_to_species, fench_to_txt_name, NO_COLOR, RED, BLACK, iccs2pos
from .piece import Piece
from .move import Move
from .zhash_data import z_c90, z_pieces, z_redKey, z_hashTable

#-----------------------------------------------------#
_text_board = [
    #'  1   2   3   4   5   6   7   8   9 ',
    '9 ┌───┬───┬───┬───┬───┬───┬───┬───┐ ',
    '  │   │   │   │ ＼│／ │   │   │   │ ',
    '8 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │   │ ／│＼ │   │   │   │ ',
    '7 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │　 │　 │   │   │   │   │ ',
    '6 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │　 │　 │   │   │   │   │   │   │ ',
    '5 ├───┴───┴───┴───┴───┴───┴───┴───┤ ',
    '  │　                             │ ',
    '4 ├───┬───┬───┬───┬───┬───┬───┬───┤ ',
    '  │　 │　 │   │   │   │　 │　 │　 │ ',
    '3 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │　 │　 │   │   │   │   │ ',
    '2 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │   │   │ ＼│／ │　 │　 │　 │ ',
    '1 ├───┼───┼───┼───┼───┼───┼───┼───┤ ',
    '  │   │　 │   │ ／│＼ │　 │   │   │ ',
    '0 └───┴───┴───┴───┴───┴───┴───┴───┘ ',
    '   ',
    '  a   b   c   d   e   f   g   h   i ',
    '  0   1   2   3   4   5   6   7   8 ',
    #'  九  八  七  六  五  四  三  二  一',
    #'',
]


#-----------------------------------------------------#
def _pos_to_text_board_pos(pos):
    """
    将棋盘坐标 (x,y) 转换为文本画板中字符位置。

    参数:
        pos (tuple): 棋盘坐标 (x, y)，x 范围 0-8，y 范围 0-9。

    返回:
        tuple: 文本画板中的 (col, row) 索引，可用于字符串替换绘制棋子。
    """
    return (4 * pos[0] + 2, (9 - pos[1]) * 2)


#-----------------------------------------------------#
PLAYER = ('', 'RED', 'BLACK')

class ChessPlayer():
    """表示当前走子的玩家（颜色）。

    该类封装了简单的颜色切换逻辑，用于记录当前走子方。
    """

    def __init__(self, color):
        self.color = color

    def next(self):
        """切换到下一个玩家并返回新的 `ChessPlayer` 实例。

        如果当前颜色为 `NO_COLOR`（未指定），则保持不变。
        返回一个新的 `ChessPlayer`，避免就地修改引用带来的副作用。
        """
        if self.color != NO_COLOR:
            self.color = 3 - self.color
        return ChessPlayer(self.color)

    def opposite(self):
        """返回与当前颜色相反的颜色值（整数）。

        如果未指定颜色（`NO_COLOR`）则返回 `NO_COLOR`。
        """
        if self.color == NO_COLOR:
            return NO_COLOR
        return 3 - self.color

    def __str__(self):
        return PLAYER[self.color]

    def __eq__(self, other):
        """比较操作。

        支持与另一个 `ChessPlayer` 或整数颜色值比较。
        """
        if isinstance(other, ChessPlayer):
            return self.color == other.color
        elif isinstance(other, int):
            return self.color == other
        return False


#-----------------------------------------------------#
class ChessBoard(object):
    """棋盘核心类：存储棋子分布并提供走子/检测规则的工具方法。

    该类提供加载/导出 FEN、生成走子、检查将军/将死等功能。
    """

    def __init__(self, fen=''):
        """使用可选的 FEN 字符串初始化棋盘。

        参数:
            fen (str): 初始局面 FEN（缺省为空表示默认空棋盘或初始局面）。
        """
        self.from_fen(fen)

    def clear(self):
        """清空棋盘并将走子方设为未指定（`NO_COLOR`）。"""
        self._board = [[None for x in range(9)] for y in range(10)]
        self.move_player = ChessPlayer(NO_COLOR)

    def copy(self):
        """返回棋盘的深拷贝（用于模拟走子或回溯）。"""
        return copy.deepcopy(self)

    def mirror(self):
        """返回沿竖直中线镜像的棋盘拷贝（左右翻转）。"""
        b = self.copy()
        b._board = [[self._board[y][8 - x] for x in range(9)]
                    for y in range(10)]
        return b
            
    def flip(self):
        """返回绕横轴翻转（上下翻转）的棋盘拷贝。"""
        b = self.copy()
        b._board = [[self._board[9 - y][x] for x in range(9)]
                    for y in range(10)]
        return b

    def swap(self):
        """交换棋子大小写（红黑互换），并返回新的棋盘拷贝。

        大写表示红方、小写表示黑方。该方法将所有棋子字母大小写取反，
        同时切换走子方（调用 `next()`）。
        """
        def swap_fench(fench):
            if fench is None: 
                return None
            return fench.upper() if fench.islower() else fench.lower()
            
        b = self.copy()
        b._board = [[swap_fench(self._board[y][x]) for x in range(9)]
                for y in range(10)]

        b.move_player.next()

        return b
    
    def is_mirror(self):
        """判断当前棋盘是否关于竖中线对称（镜像局面）。"""
        b = self.mirror()
        return  self.to_fen() == b.to_fen()

    def set_move_color(self, color):
        """设置当前走子方为指定颜色（整数或 `ChessPlayer` 内部值）。"""
        self.move_player = ChessPlayer(color)

    def get_move_color(self):
        """返回当前走子方的颜色整数值。"""
        return self.move_player.color

    def put_fench(self, fench, pos):
        """在指定位置放置棋子（不做合法性检查）。

        参数:
            fench (str): 棋子字符，例如 'K' 或 'p'
            pos (tuple): 目标坐标 (x, y)
        """
        self._board[pos[1]][pos[0]] = fench

    def pop_fench(self, pos):
        """移除并返回指定位置的棋子（若为空则返回 None）。"""
        fench = self._board[pos[1]][pos[0]]
        self._board[pos[1]][pos[0]] = None

        return fench
        
    def get_fench(self, pos):
        """返回指定位置的棋子字符，越界返回 None。"""
        if pos[0] < 0 or pos[0] > 8 :
            return None

        if pos[1] < 0 or pos[1] > 9:
            return None

        return self._board[pos[1]][pos[0]]

    def get_fench_color(self, pos):
        """返回指定位置棋子的颜色（`RED` 或 `BLACK`），若无棋子返回 None。"""
        fench = self.get_fench(pos)

        if not fench:
            return None

        return RED if fench.isupper() else BLACK

    def get_fenchs(self, fench):
        """返回棋盘上所有与给定 fench 相同的坐标列表。"""
        poss = []
        for x in range(9):
            for y in range(10):
                if self._board[y][x] == fench:
                    poss.append((x, y))
        return poss

    def get_piece(self, pos):
        """返回指定位置的 `Piece` 实例（若有棋子），否则返回 None。"""
        fench = self.get_fench(pos)
        return Piece.create(self, fench, pos) if fench else None

    def get_pieces(self, color=None):
        """生成器：遍历棋盘并产出 `Piece` 对象。

        参数:
            color (int|ChessPlayer|None): 若指定，仅返回该颜色的棋子。
        """
        if isinstance(color, ChessPlayer):
            color = color.color

        for x in range(9):
            for y in range(10):
                fench = self._board[y][x]
                if not fench:
                    continue
                if color is None:
                    yield Piece.create(self, fench, (x, y))
                else:
                    _, p_color = fench_to_species(fench)
                    if color == p_color:
                        yield Piece.create(self, fench, (x, y))

    def get_fenchs_x(self, x, fench):
        """返回指定列 x 上匹配 fench 的所有坐标。"""
        poss = []
        for y in range(10):
            if self._board[y][x] == fench:
                poss.append((x, y))
        return poss

    def get_king(self, color):
        """查找并返回指定颜色的王 `Piece`，找不到返回 None。

        参数:
            color (int|ChessPlayer): 指定要查找的颜色。
        """
        if isinstance(color, ChessPlayer):
            color = color.color

        limit_y = ((), (0, 1, 2), (7, 8, 9))
        for x in (3, 4, 5):
            for y in limit_y[color]:
                fench = self._board[y][x]
                if not fench:
                    continue
                if fench.lower() == 'k':
                    return Piece.create(self, fench, (x, y))
        return None

    def is_valid_move_t(self, move_t):
        """便捷方法：接受 (from, to) 的元组并验证其是否合法。"""
        return self.is_valid_move(move_t[0], move_t[1])

    def is_valid_iccs_move(self, iccs):
        """接受 ICCS 格式字符串并判定是否为合法走子。"""
        move_from, move_to = iccs2pos(iccs)
        return self.is_valid_move(move_from, move_to)

    def is_valid_move(self, pos_from, pos_to):
        '''
        只进行最基本的走子规则检查，不对每个子的规则进行检查，以加快文件加载之类的速度
        '''

        if not (0 <= pos_to[0] <= 8): 
            return False
        if not (0 <= pos_to[1] <= 9): 
            return False

        fench_from = self._board[pos_from[1]][pos_from[0]]
        if not fench_from:
            return False

        _, from_color = fench_to_species(fench_from)

        if (self.move_player != NO_COLOR) and (self.move_player != from_color):
            return False

        fench_to = self._board[pos_to[1]][pos_to[0]]
        if fench_to:
            _, to_color = fench_to_species(fench_to)
            if from_color == to_color:
                return False

        piece = self.get_piece(pos_from)

        return piece.is_valid_move(pos_to)

    def _move_piece(self, pos_from, pos_to):
        """在内部执行棋子移动（不做合法性检查），并返回被移动的 fench。"""
        fench = self._board[pos_from[1]][pos_from[0]]
        self._board[pos_to[1]][pos_to[0]] = fench
        self._board[pos_from[1]][pos_from[0]] = None

        return fench

    def move(self, pos_from, pos_to, check = True):
        """尝试执行走子：若合法则修改棋盘并返回 `Move` 对象，否则返回 None。

        返回的 `Move` 包含移动前的棋盘（用于回退或记录）。"""
        if not self.is_valid_move(pos_from, pos_to):
            return None

        # 保存board移动之前的状态
        board = self.copy()
        self._move_piece(pos_from, pos_to)
        move = Move(board, pos_from, pos_to)
        if check:
            if self.is_checking():
                move.is_checking = True
                if self.is_checkmate():
                    move.is_checkmate = True

        return move

    def move_iccs(self, move_str, check = True):
        """根据 ICCS 格式的字符串执行走子，返回 `Move` 或 None。"""
        move_from, move_to = iccs2pos(move_str)
        return self.move(move_from, move_to, check)

    def move_text(self, move_str, check = True):
        """根据中文棋谱文本解析并执行走子，返回 `Move` 或 None。"""
        ret = Move.from_text(self, move_str)
        if not ret:
            return None
        move_from, move_to = ret
        return self.move(move_from, move_to, check)

    def next_turn(self):
        """切换到下一个走子方并返回新的 `ChessPlayer` 实例（工具方法）。"""
        return self.move_player.next()

    def create_moves(self):
        """生成当前走子方的所有候选走法（每个为 (from, to) 元组）。"""
        for piece in self.get_pieces(self.move_player):
            for move in piece.create_moves():
                yield move

    def create_piece_moves(self, pos):
        """生成指定位置棋子的所有候选走法。"""
        piece = self.get_piece(pos)
        if piece:
            for move in piece.create_moves():
                yield move

    def is_checked_move(self, pos_from, pos_to):
        """判断执行给定走子后己方是否处于被将军状态。

        若走子非法，抛出 `CChessException('Invalid Move')`。"""
        if not self.is_valid_move(pos_from, pos_to):
            raise CChessException('Invalid Move')
        board = self.copy()
        board._move_piece(pos_from, pos_to)
        board.move_player.next()
        return board.is_checking()

    def is_checking_move(self, pos_from, pos_to):
        """判断执行该走子后是否对对方形成将军（不切换走子方）。"""
        board = self.copy()
        board._move_piece(pos_from, pos_to)
        return board.is_checking()

    def is_checking(self):
        """判断当前走子方是否对对方构成将军（对方王被攻击）。"""
        king = self.get_king(self.move_player.opposite())
        if not king:
            return False

        for piece in self.get_pieces(self.move_player):
            if piece.is_valid_move((king.x, king.y)):
                return True

        return False

    def is_checkmate(self):
        """判断当前局面在对方回合是否为将死（无路可走）。"""
        board = self.copy()
        board.move_player.next()
        return board.no_moves()

    def no_moves(self):
        """判断当前走子方是否没有任何合法且不留被将军的走法。"""
        king = self.get_king(self.move_player)
        if not king:
            return True
        for piece in self.get_pieces(self.move_player):
            for move_it in piece.create_moves():
                if self.is_valid_move_t(move_it):
                    if not self.is_checked_move(move_it[0], move_it[1]):
                        return False
        return True

    def count_x_line_in(self, y, x_from, x_to):
        """统计同一行 y 上 x_from 与 x_to 之间（不含端点）被占用的格子数。"""
        return reduce(lambda count, fench: count + 1 if fench else count,
                      self.x_line_in(y, x_from, x_to), 0)

    def count_y_line_in(self, x, y_from, y_to):
        """统计同一列 x 上 y_from 与 y_to 之间（不含端点）被占用的格子数。"""
        return reduce(lambda count, fench: count + 1 if fench else count,
                      self.y_line_in(x, y_from, y_to), 0)

    def x_line_in(self, y, x_from, x_to):
        """返回水平方向上两个 x 之间（不含端点）的格子内容列表。"""
        step = 1 if x_to > x_from else -1
        return [self._board[y][x] for x in range(x_from + step, x_to, step)]

    def y_line_in(self, x, y_from, y_to):
        """返回垂直方向上两个 y 之间（不含端点）的格子内容列表。"""
        step = 1 if y_to > y_from else -1
        return [self._board[y][x] for y in range(y_from + step, y_to, step)]

    def from_fen(self, fen):
        """从简化的 FEN 字符串加载棋盘布局并设置走子方。

        返回 True 表示加载成功，False 表示遇到无法识别字符。
        """

        num_set = set(('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        ch_set = set(('k', 'a', 'b', 'n', 'r', 'c', 'p'))

        self.clear()

        if fen == '':
            return True

        fen = fen.strip()

        x = 0
        y = 9

        for i in range(0, len(fen)):
            ch = fen[i]

            if ch == ' ': 
                break
            elif ch == '/':
                y -= 1
                x = 0
                if y < 0: 
                    break
            elif ch in num_set:
                x += int(ch)
                if x > 8: 
                    x = 8
            elif ch.lower() in ch_set:
                if x <= 8:
                    self.put_fench(ch, (x, y))
                    x += 1
            else:
                return False

        fens = fen.split()

        self.move_player = ChessPlayer(NO_COLOR)

        if (len(fens) >= 2) and (fens[1] == 'b'):
            self.move_player = ChessPlayer(BLACK)
        else:
            self.move_player = ChessPlayer(RED)

        return True

    def to_fen(self):
        """将棋盘序列化为简化 FEN 字符串（不含额外信息）。"""
        fen = ''
        count = 0
        for y in range(9, -1, -1):
            for x in range(9):
                fench = self._board[y][x]
                if fench:
                    if count != 0:
                        fen += str(count)
                        count = 0
                    fen += fench
                else:
                    count += 1

            if count > 0:
                fen += str(count)
                count = 0

            if y > 0: 
                fen += '/'

        if self.move_player == BLACK:
            fen += ' b'
        else: 
            fen += ' w'

        return fen

    def to_full_fen(self):
        """返回包含占位信息的完整 FEN（方便外部工具兼容）。"""
        return self.to_fen() + ' - - 0 1'
        
    def zhash(self, fen = None):
        """计算当前棋盘的 Zobrist 哈希值。

        可选地传入 `fen` 先加载局面再计算哈希，返回一个带符号的整数哈希值。
        """
        if fen:
            self.from_fen(fen)

        key = 0
        for y in range(10):
            for x in range(9):
                square = z_c90[x + (9 - y) * 9]
                letter = self.get_fench((x, y))
                if letter in z_pieces:
                    chess = z_pieces[letter]
                    key ^= z_hashTable[chess * 256 + square]

        if (self.get_move_color() == RED):
            key ^= z_redKey

        return (key & ((1 << 63) - 1)) - (key & (1 << 63))
        
    def detect_move_pieces(self, new_board):
        """比较当前棋盘与 `new_board` 并返回变化位置元组 (from_positions, to_positions)。"""
        p_from = []
        p_to = []
        for x in range(9):
            for y in range(10):
                p_old = self.get_fench((x, y))
                p_new = new_board.get_fench((x, y))
                # same
                if p_old == p_new:
                    continue
                # move from
                if p_new is None:
                    p_from.append((x, y))
                # move_to
                else:
                    p_to.append((x, y))
        return (p_from, p_to)

    def create_move_from_board(self, new_board):
        """尝试从两个棋盘状态推断唯一的一步走法，返回 (from, to) 或 None。"""
        p_froms, p_tos = self.detect_move_pieces(new_board)
        if (len(p_froms) == 1) and (len(p_tos) == 1):
            p_from = p_froms[0]
            p_to = p_tos[0]
            if self.is_valid_move(p_from, p_to):
                return (p_from, p_to)
        return None
    
    def text_view(self):

        """将棋盘渲染为文本画板（返回字符串列表）。"""

        board_str = _text_board[:]

        y = 0
        for line in self._board:
            x = 8
            for ch in line[::-1]:
                if ch:
                    pos = _pos_to_text_board_pos((x, y))
                    new_text = board_str[pos[1]][:pos[0]] + fench_to_txt_name(
                        ch) + board_str[pos[1]][pos[0] + 2:]
                    board_str[pos[1]] = new_text
                x -= 1
            y += 1

        return board_str
        
    def print_board(self):
        """在标准输出打印棋盘的文本表示，便于调试。"""
        print('')
        for s in self.text_view():
            print(s)

    def __str__(self):
        return self.to_fen()

    def __repr__(self):
        return self.to_fen()

    def __eq__(self, other):
        if isinstance(other, str):
            return (self.to_fen() == other)
        elif isinstance(other, ChessBoard):
            return (self.to_fen() == other.to_fen())
        else:
            return False

#-----------------------------------------------------#
class ChessBoardOneHot(ChessBoard):
    def __init__(self, fen='', chess_dict=None):
        super().__init__(fen)
        self.__chess_dict = chess_dict

    def load_one_hot_dict(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            self.__chess_dict = json.load(f)
        self.__chess_dict[None] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def get_one_hot_board(self) -> list:
        """
        依据`self.__chess_dict`对棋子进行独热编码
        :return: 一个列表，将棋子进行独热编码后的棋盘
        """
        one_hot_board = []
        for x in self._board.copy():
            temp = []
            for y in x:
                temp.append(
                    self.__chess_dict.get(
                        y, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
            one_hot_board.append(temp)
        return one_hot_board

    @property
    def chess_dict(self):
        """
        获取棋子-独热编码的映射
        :return: 字典，棋子-独热编码的映射
        """
        return self.__chess_dict.copy()

