"""Copyright (C) 2024  walker li <walker8088@gmail.com>

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
"""

from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from .common import (
    fench_to_species,
    fench_to_txt_name,
    iccs2pos,
    load_json,
    next_color,
    swap_fench,
)
from .constants import ANY_COLOR, BLACK, RED
from .exception import CChessError
from .move import Move
from .piece import Piece
from .zhash_data import Z_HASH_TABLE, Z_MAP_PIECES, Z_RED_KEY, z_c90

# pylint: disable=protected-access,attribute-defined-outside-init,too-many-public-methods

# -----------------------------------------------------#
_text_board = [
    #'  1   2   3   4   5   6   7   8   9 ',
    "9 ┌───┬───┬───┬───┬───┬───┬───┬───┐ ",
    "  │   │   │   │ ＼│／ │   │   │   │ ",
    "8 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │   │　 │   │ ／│＼ │   │   │   │ ",
    "7 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │   │　 │　 │　 │   │   │   │   │ ",
    "6 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │　 │　 │   │   │   │   │   │   │ ",
    "5 ├───┴───┴───┴───┴───┴───┴───┴───┤ ",
    "  │　                             │ ",
    "4 ├───┬───┬───┬───┬───┬───┬───┬───┤ ",
    "  │　 │　 │   │   │   │　 │　 │　 │ ",
    "3 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │   │　 │　 │　 │   │   │   │   │ ",
    "2 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │   │   │   │ ＼│／ │　 │　 │　 │ ",
    "1 ├───┼───┼───┼───┼───┼───┼───┼───┤ ",
    "  │   │　 │   │ ／│＼ │　 │   │   │ ",
    "0 └───┴───┴───┴───┴───┴───┴───┴───┘ ",
    "   ",
    "  a   b   c   d   e   f   g   h   i ",
    "  0   1   2   3   4   5   6   7   8 ",
    #'  九  八  七  六  五  四  三  二  一',
    #'',
]

BOARD_WIDTH = 9
BOARD_HEIGHT = 10

_g_fen_num_set = set(("1", "2", "3", "4", "5", "6", "7", "8", "9"))
_g_fen_ch_set = set(("k", "a", "b", "n", "r", "c", "p"))


# -----------------------------------------------------#
def _pos_to_text_board_pos(pos):
    """将棋盘坐标 (x,y) 转换为文本画板中字符位置。

    参数:
        pos (tuple): 棋盘坐标 (x, y)，x 范围 0-8，y 范围 0-9。

    返回:
        tuple: 文本画板中的 (col, row) 索引，可用于字符串替换绘制棋子。
    """
    return (4 * pos[0] + 2, (9 - pos[1]) * 2)


# -----------------------------------------------------#
PLAYER = ("", "RED", "BLACK")


# -----------------------------------------------------#
@dataclass
class MoveInfo:
    """记录棋盘移动的增量状态信息，用于撤销操作"""

    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    moving_fench: str  # 移动的棋子字符
    captured_fench: Optional[str]  # 被吃棋子，None 表示无吃子
    prev_attack_matrix_dirty: bool  # 移动前攻击矩阵脏标志
    next_attack_matrix_dirty: bool  # 移动后攻击矩阵脏标志
    prev_move_side: int  # 移动前走子方 (RED/BLACK/ANY_COLOR)
    next_move_side: int  # 移动后走子方 (RED/BLACK/ANY_COLOR)
    board_before: List[List[Optional[str]]]  # 移动前棋盘数组的深拷贝
    board_after: List[List[Optional[str]]]  # 移动后棋盘数组的深拷贝


# -----------------------------------------------------#
class ChessBoard:
    """棋盘核心类：存储棋子分布并提供走子/检测规则的工具方法。

    该类提供加载/导出 FEN、生成走子、检查将军/将死等功能。
    """

    def __init__(self, fen: str = "") -> None:
        """使用可选的 FEN 字符串初始化棋盘。

        参数:
            fen: 初始局面 FEN（缺省为空表示默认空棋盘或初始局面）。
        """
        self.clear()
        self.from_fen(fen)

    def clear(self) -> None:
        """清空棋盘并将走子方设为任意颜色（`ANY_COLOR`）。"""
        self._board: List[List[Optional[str]]] = [
            [None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self._move_side = ANY_COLOR
        # 攻击矩阵缓存
        self._red_attacks: List[List[bool]] = [
            [False for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self._black_attacks: List[List[bool]] = [
            [False for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
        ]
        self._attack_matrix_dirty = True

    def copy(self) -> "ChessBoard":
        """返回棋盘的快照（独立副本）。"""
        b = self.__class__()
        b._board = [row[:] for row in self._board]
        b.set_move_side(self.move_side())
        b._red_attacks = [row[:] for row in self._red_attacks]
        b._black_attacks = [row[:] for row in self._black_attacks]
        b._attack_matrix_dirty = self._attack_matrix_dirty
        return b

    def from_board(self, b: "ChessBoard") -> None:
        """从另一个ChessBoard Copy属性"""
        self._board = b._board
        self._move_side = b.move_side()
        # 复制攻击矩阵缓存（如果存在）
        if hasattr(b, "_red_attacks"):
            self._red_attacks = b._red_attacks
            self._black_attacks = b._black_attacks
            self._attack_matrix_dirty = b._attack_matrix_dirty
        else:
            # 旧版本棋盘没有这些属性，标记为脏
            self._red_attacks = [
                [False for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
            ]
            self._black_attacks = [
                [False for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)
            ]
            self._attack_matrix_dirty = True

    def mirror(self) -> "ChessBoard":
        """返回新棋盘: 沿竖直中线镜像（左右翻转）。"""
        b = self.copy()
        b._board = [[self._board[y][8 - x] for x in range(9)] for y in range(10)]
        b._attack_matrix_dirty = True
        return b

    def flip(self) -> "ChessBoard":
        """返回新棋盘: 绕横轴翻转（上下翻转）+ 沿竖直中线镜像（左右翻转）。"""
        b = self.copy()
        b._board = [[self._board[9 - y][8 - x] for x in range(9)] for y in range(10)]
        b._attack_matrix_dirty = True
        return b

    def swap(self) -> "ChessBoard":
        """返回新棋盘: 交换棋子大小写（红黑互换）。

        大写表示红方、小写表示黑方。该方法将所有棋子字母大小写取反，
        同时切换走子方（调用 `next()`）。
        """

        b = self.copy()
        b._board = [
            [swap_fench(self._board[y][x]) for x in range(9)] for y in range(10)
        ]

        b.set_move_side(next_color(b.move_side()))
        b._attack_matrix_dirty = True

        return b

    @staticmethod
    def fen_mirror(fen: str) -> str:
        """返回给定 FEN 字符串的镜像局面 FEN。"""
        b = ChessBoard(fen)
        return b.mirror().to_fen()

    @staticmethod
    def fen_flip(fen: str) -> str:
        """返回给定 FEN 字符串的翻转局面 FEN。"""
        b = ChessBoard(fen)
        return b.flip().to_fen()

    @staticmethod
    def fen_swap(fen: str) -> str:
        """返回给定 FEN 字符串的交换局面 FEN。"""
        b = ChessBoard(fen)
        return b.swap().to_fen()

    def is_mirror(self):
        """判断当前棋盘是否关于竖中线对称（镜像局面）。"""
        b = self.mirror()
        return self.to_fen() == b.to_fen()

    def normalized(self):
        """返回规范局面：当前走子方始终视为红方。

        如果当前是黑方走子，返回 swap().flip() 后的棋盘。
        如果当前是红方走子，返回棋盘的副本。

        返回:
            ChessBoard: 规范局面棋盘
        """
        if self.move_side() == BLACK:
            return self.swap().flip()
        return self.copy()

    def is_normalized(self):
        """判断当前是否为规范局面（红方走子）。"""
        return self.move_side() == RED

    def denormalize_pos(self, pos):
        """将规范局面坐标转换回原局面。

        规范局面中：原点在左下角，x 向右，y 向上
        黑方视角：需要 flip 回去，坐标变换为 (8-x, 9-y)
        红方视角：直接返回原坐标（因为规范化棋盘已经是红方走子）

        参数:
            pos: 规范局面中的坐标 (x, y)

        返回:
            tuple: 原局面中的坐标
        """
        # 如果当前棋盘已经是规范局面（红方走子），则原棋盘也是红方走子
        if self.is_normalized():
            return pos
        # 否则原棋盘是黑方走子，需要应用 flip 变换
        return (8 - pos[0], 9 - pos[1])

    # move_player 已被废弃，请使用 move_side() 和 set_move_side() 方法

    def move_side(self):
        """获取当前走子方（整数颜色值）"""
        return self._move_side

    def set_move_side(self, value):
        """设置走子方，支持整数"""
        self._move_side = value

    def _validate_pos(self, pos):
        """验证坐标是否在棋盘范围内。"""
        if not (0 <= pos[0] <= 8 and 0 <= pos[1] <= 9):
            raise ValueError(f"Position {pos} out of board bounds (0-8, 0-9)")

    def put_fench(self, fench, pos):
        """在指定位置放置棋子（不做合法性检查）。

        参数:
            fench (str): 棋子字符，例如 'K' 或 'p'
            pos (tuple): 目标坐标 (x, y)
        """
        self._validate_pos(pos)
        self._board[pos[1]][pos[0]] = fench
        self._attack_matrix_dirty = True

    def pop_fench(self, pos):
        """移除并返回指定位置的棋子（若为空则返回 None）。"""
        self._validate_pos(pos)
        fench = self._board[pos[1]][pos[0]]
        self._board[pos[1]][pos[0]] = None
        self._attack_matrix_dirty = True
        return fench

    def get_fench(self, pos):
        """返回指定位置的棋子字符。"""
        self._validate_pos(pos)
        return self._board[pos[1]][pos[0]]

    def occupied(self, pos):
        """检查指定位置是否有棋子。

        参数:
            pos: 坐标 (x, y)

        返回:
            RED: 如果该位置有红方棋子
            BLACK: 如果该位置有黑方棋子
            None: 如果该位置为空

        示例:
            if board.occupied((4, 4)) == RED:
                print("红方棋子")
            elif board.occupied((4, 4)) == BLACK:
                print("黑方棋子")
            else:
                print("空位")
        """
        self._validate_pos(pos)
        fench = self._board[pos[1]][pos[0]]
        if fench is None:
            return None
        return RED if fench.isupper() else BLACK

    def get_fenchs(self, fench):
        """返回棋盘上所有与给定 fench 相同的坐标列表。"""
        positions = []
        for x in range(9):
            for y in range(10):
                if self._board[y][x] == fench:
                    positions.append((x, y))
        return positions

    def get_fenchs_x(self, fench, x):
        """返回指定列 x 上匹配 fench 的所有坐标。"""
        positions = []
        for y in range(10):
            if self._board[y][x] == fench:
                positions.append((x, y))
        return positions

    def get_piece(self, pos):
        """返回指定位置的 `Piece` 实例（若有棋子），否则返回 None。"""
        fench = self.get_fench(pos)
        return Piece.create(self, fench, pos) if fench else None

    def get_pieces(self, color=None):
        """生成器：遍历棋盘并产出 `Piece` 对象。

        参数:
            color (int|None): 若指定，仅返回该颜色的棋子。
        """
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

    def get_king(self, color):
        """查找并返回指定颜色的王 `Piece`，找不到返回 None。

        参数:
            color (int): 指定要查找的颜色。
        """
        limit_y = ((), (0, 1, 2), (7, 8, 9))
        for x in (3, 4, 5):
            for y in limit_y[color]:
                fench = self._board[y][x]
                if not fench:
                    continue
                if fench.lower() == "k":
                    return Piece.create(self, fench, (x, y))
        return None

    def is_valid_move_t(self, move_t):
        """便捷方法：接受 (from, to) 的元组并验证其是否合法。"""
        return self.is_valid_move(move_t[0], move_t[1])

    def is_valid_iccs_move(self, iccs: str) -> bool:
        """接受 ICCS 格式字符串并判定是否为合法走子。"""
        move_from, move_to = iccs2pos(iccs)
        return self.is_valid_move(move_from, move_to)

    def is_valid_move(self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]) -> bool:
        """只进行最基本的走子规则检查，不对每个子的规则进行检查，以加快文件加载之类的速度。"""

        if not 0 <= pos_to[0] <= 8:
            return False
        if not 0 <= pos_to[1] <= 9:
            return False

        fench_from = self._board[pos_from[1]][pos_from[0]]
        if not fench_from:
            return False

        _, from_color = fench_to_species(fench_from)

        if self.move_side() not in (ANY_COLOR, from_color):
            return False

        fench_to = self._board[pos_to[1]][pos_to[0]]
        if fench_to:
            _, to_color = fench_to_species(fench_to)
            if from_color == to_color:
                return False

        # 直接使用当前棋盘的 piece 检查
        # 注：不使用规范化，因为规范化会改变棋子颜色（swap），导致判断复杂
        piece = self.get_piece(pos_from)
        return piece.is_valid_move(pos_to) if piece else False

    def _move_piece(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]
    ) -> Optional[str]:
        """在内部执行棋子移动（不做合法性检查），并返回被移动的 fench。"""
        fench = self._board[pos_from[1]][pos_from[0]]
        self._board[pos_to[1]][pos_to[0]] = fench
        self._board[pos_from[1]][pos_from[0]] = None
        self._attack_matrix_dirty = True

        return fench

    def make_move(self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]) -> MoveInfo:
        """执行移动并返回状态记录，不进行合法性检查。

        注意：此函数不切换走子方，走子方由外部程序控制。
        """
        # 记录移动前状态
        prev_attack_matrix_dirty = self._attack_matrix_dirty
        prev_move_side = self.move_side()
        moving_fench = self._board[pos_from[1]][pos_from[0]]
        captured_fench = self._board[pos_to[1]][pos_to[0]]
        board_before = [row[:] for row in self._board]  # 深拷贝棋盘数组

        # 执行移动
        self._move_piece(pos_from, pos_to)

        # 记录移动后状态（不切换走子方）
        next_attack_matrix_dirty = self._attack_matrix_dirty
        next_move_side = self.move_side()
        board_after = [row[:] for row in self._board]  # 深拷贝棋盘数组

        # 返回状态记录
        return MoveInfo(
            from_pos=pos_from,
            to_pos=pos_to,
            moving_fench=moving_fench,
            captured_fench=captured_fench,
            prev_attack_matrix_dirty=prev_attack_matrix_dirty,
            next_attack_matrix_dirty=next_attack_matrix_dirty,
            prev_move_side=prev_move_side,
            next_move_side=next_move_side,
            board_before=board_before,
            board_after=board_after,
        )

    def unmake_move(self, move_info: MoveInfo) -> None:
        """根据 MoveInfo 撤销移动，恢复棋盘状态"""
        # 恢复被吃棋子（如果有）
        if move_info.captured_fench is not None:
            self._board[move_info.to_pos[1]][move_info.to_pos[0]] = (
                move_info.captured_fench
            )
        else:
            self._board[move_info.to_pos[1]][move_info.to_pos[0]] = None

        # 将移动棋子移回原位置
        self._board[move_info.from_pos[1]][move_info.from_pos[0]] = (
            move_info.moving_fench
        )

        # 恢复攻击矩阵脏标志
        self._attack_matrix_dirty = move_info.prev_attack_matrix_dirty

        # 恢复走子方
        self._move_side = move_info.prev_move_side

    def move(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int], check: bool = True
    ) -> Optional[Move]:
        """尝试执行走子：若合法则修改棋盘并返回 `Move` 对象，否则返回 None。
        返回的 `Move` 包含移动前的棋盘（用于回退或记录）。"""
        if not self.is_valid_move(pos_from, pos_to):
            return None

        # 执行移动并记录状态
        move_info = self.make_move(pos_from, pos_to)

        # 切换走子方（除非吃掉将帅）
        if move_info.captured_fench not in ("k", "K"):
            self._move_side = next_color(self.move_side())

        move = Move(move_info)
        if check:
            # 检查刚走完棋的一方是否对对方将军
            # 需要临时切换回上一步的走子方
            original_move_side = self.move_side()
            self._move_side = move_info.prev_move_side
            is_checking = self.is_checking()
            move.is_checking = is_checking
            move.is_checkmate = is_checking and self.is_checkmate()
            # 恢复走子方
            self._move_side = original_move_side

        return move

    def move_iccs(self, move_str: str, check: bool = True) -> Optional[Move]:
        """根据 ICCS 格式的字符串执行走子，返回 `Move` 或 None。"""
        move_from, move_to = iccs2pos(move_str)
        return self.move(move_from, move_to, check)

    def move_text(self, move_str: str, check: bool = True) -> Optional[Move]:
        """根据中文棋谱文本解析并执行走子，返回 `Move` 或 None。

        根据走法文本中的数字类型自动检测走子方：
        - 中文数字（一二三...）→ 红方格式
        - 阿拉伯/全角数字（123...或１２３...）→ 黑方格式

        对黑方格式走法，先规范化局面为红方视角，解析后再反规范化坐标。
        """
        from .move import _detect_move_side_from_text, _normalize_move_str

        move_str = move_str.replace(" ", "")

        # 从文本检测走子方格式
        text_side = _detect_move_side_from_text(move_str)
        if text_side is None:
            # 无法从文本判断，使用棋盘当前走子方
            text_side = self.move_side()

        # 规范化局面（统一为红方视角解析）
        normalized_board = self.normalized()

        # 根据文本格式规范化走法字符串
        if text_side == BLACK:
            normalized_move_str = _normalize_move_str(move_str, BLACK, RED)
        else:
            normalized_move_str = move_str

        # 在规范局面上解析（此时 normalized_board.move_side() == RED，
        # 所以 _MoveTextParser.needs_denormalization == False，
        # 返回的坐标是规范局面坐标）
        ret = Move.from_text(normalized_board, normalized_move_str)
        if not ret:
            return None

        # 将规范局面坐标反规范化回原局面坐标
        for norm_from, norm_to in ret:
            orig_from = self.denormalize_pos(norm_from)
            orig_to = self.denormalize_pos(norm_to)
            move = self.move(orig_from, orig_to, check)
            if move is not None:
                return move

        return None

    def move_any(
        self,
        pos_from: Tuple[int, int],
        pos_to: Tuple[int, int],
        check: bool = False,
        switch_turn: bool = False,
    ) -> Optional[Move]:
        """执行任意走子，不检查颜色限制（用于摆棋/分析）。

        参数:
            pos_from: 起点坐标
            pos_to: 终点坐标
            check: 是否检查将军/将死（默认 False，提高摆棋速度）
            switch_turn: 是否切换走子方（默认 False，摆棋时通常不切换）

        返回:
            Move 对象，如果走子非法（如起点无棋子）则返回 None

        注意:
            - 可以移动任意方的棋子
            - 可以吃己方棋子
            - 不检查 move_side 颜色
        """
        # 最基本的检查：起点必须有棋子，目标位置在棋盘内
        if not (0 <= pos_to[0] <= 8 and 0 <= pos_to[1] <= 9):
            return None

        fench_from = self._board[pos_from[1]][pos_from[0]]
        if not fench_from:
            return None

        # 检查棋子走法是否合法（不检查颜色）
        piece = self.get_piece(pos_from)
        if not piece or not piece.is_valid_move(pos_to):
            return None

        # 执行移动并记录状态
        move_info = self.make_move(pos_from, pos_to)
        move = Move(move_info)

        # 如果不切换走子方，恢复原来的走子方
        if not switch_turn:
            self._move_side = move_info.prev_move_side

        if check:
            is_checking = self.is_checking()
            move.is_checking = is_checking
            move.is_checkmate = is_checking and self.is_checkmate()

        return move

    def next_turn(self):
        """切换到下一个走子方并返回新的颜色值（工具方法）。"""
        self._move_side = next_color(self.move_side())
        return self.move_side()

    def set_piece(self, fench, pos):
        """在指定位置放置棋子（摆棋专用，不检查合法性）。

        参数:
            fench: 棋子字符（如 'K', 'r', 'c' 等），None 表示移除棋子
            pos: 坐标 (x, y)

        返回:
            self（支持链式调用）

        注意:
            - 不检查走子方
            - 不切换走子方
            - 可以放置任意棋子到任意位置
        """
        self._board[pos[1]][pos[0]] = fench
        self._attack_matrix_dirty = True
        return self

    def remove_piece(self, pos: Tuple[int, int]) -> Optional[str]:
        """移除指定位置的棋子（摆棋专用）。

        参数:
            pos: 坐标 (x, y)

        返回:
            被移除的棋子字符（如果有）
        """
        return self.set_piece(None, pos)

    def setup_board(self, fen: Optional[str] = None) -> "ChessBoard":
        """快速设置棋盘（摆棋专用）。

        参数:
            fen: FEN 字符串，如果为 None 则清空棋盘

        返回:
            self（支持链式调用）

        示例:
            board.setup_board().set_piece('R', (4, 4)).set_piece('k', (4, 9))
        """
        if fen:
            self.from_fen(fen)
        else:
            self.clear()
        return self

    def create_moves(self) -> Iterator[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """生成当前走子方的所有候选走法（每个为 (from, to) 元组）。

        使用规范局面：将黑方走子转换为红方视角处理，简化逻辑。
        """
        is_flipped = not self.is_normalized()
        normalized_board = self.normalized()

        for piece in normalized_board.get_pieces(RED):
            for from_pos, to_pos in piece.create_moves():
                if is_flipped:
                    from_pos = self.denormalize_pos(from_pos)
                    to_pos = self.denormalize_pos(to_pos)
                yield (from_pos, to_pos)

    def create_piece_moves(
        self, pos: Tuple[int, int]
    ) -> Iterator[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """生成指定位置棋子的所有候选走法。

        使用规范局面：将黑方走子转换为红方视角处理，简化逻辑。
        """
        piece = self.get_piece(pos)
        if not piece:
            return

        _, piece_color = fench_to_species(piece.fench)
        if piece_color != self.move_side():
            return

        is_flipped = not self.is_normalized()
        normalized_board = self.normalized()

        # 在规范局面中找到对应位置的棋子
        norm_pos = self.denormalize_pos(pos) if is_flipped else pos
        norm_piece = normalized_board.get_piece(norm_pos)

        if norm_piece:
            for from_pos, to_pos in norm_piece.create_moves():
                if is_flipped:
                    from_pos = self.denormalize_pos(from_pos)
                    to_pos = self.denormalize_pos(to_pos)
                yield (from_pos, to_pos)

    def _check_move_for_general(
        self,
        pos_from: Tuple[int, int],
        pos_to: Tuple[int, int],
        check_after_move: bool = True,
    ) -> bool:
        """执行走子后检查将军状态的通用辅助方法。

        参数:
            pos_from: 起始位置
            pos_to: 目标位置
            check_after_move: True 检查移动后己方是否被将军，
                             False 检查移动后是否将军对方

        返回:
            bool: 是否处于将军状态
        """
        move_info = self.make_move(pos_from, pos_to)

        if check_after_move:
            # 检查移动后己方是否被将军
            # make_move 不切换走子方，需要手动切换
            self._move_side = next_color(self.move_side())
            checking = self.is_checking()
            self._move_side = move_info.prev_move_side
        else:
            # 检查移动后是否将军对方
            original_player = self.move_side()
            self._move_side = move_info.prev_move_side
            checking = self.is_checking()
            self._move_side = original_player

        self.unmake_move(move_info)
        return checking

    def is_checked_move(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]
    ) -> bool:
        """判断执行给定走子后己方是否处于被将军状态。
        若走子非法，抛出 `CChessError('Invalid Move')`。"""
        if not self.is_valid_move(pos_from, pos_to):
            raise CChessError("Invalid Move")
        return self._check_move_for_general(pos_from, pos_to, check_after_move=True)

    def is_checking_move(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]
    ) -> bool:
        """判断执行该走子后是否对对方形成将军（不切换走子方）。"""
        return self._check_move_for_general(pos_from, pos_to, check_after_move=False)

    def _compute_piece_attacks(self, piece: Piece) -> List[Tuple[int, int]]:
        """返回棋子可以攻击到的坐标列表（包括吃子位置）。"""
        attacks = []
        for from_pos, to_pos in piece.create_moves():
            attacks.append(to_pos)
        return attacks

    def _get_attack_matrix(self, color: int) -> List[List[bool]]:
        """根据颜色获取对应的攻击矩阵。

        参数:
            color: 颜色值 (RED 或 BLACK)

        返回:
            List[List[bool]]: 对应的攻击矩阵
        """
        return self._red_attacks if color == RED else self._black_attacks

    def _recompute_attack_matrix(self) -> None:
        """重新计算红黑双方的攻击矩阵，并将脏标志设置为 False。"""
        # 清空攻击矩阵
        for y in range(10):
            for x in range(9):
                self._red_attacks[y][x] = False
                self._black_attacks[y][x] = False
        # 遍历所有棋子，填充攻击矩阵
        for piece in self.get_pieces():
            attacks = self._compute_piece_attacks(piece)
            color = piece.color
            matrix = self._get_attack_matrix(color)
            for x, y in attacks:
                matrix[y][x] = True
        self._attack_matrix_dirty = False

    def is_checking(self) -> bool:
        """判断当前走子方是否对对方构成将军（对方王被攻击）。"""
        if self._attack_matrix_dirty:
            self._recompute_attack_matrix()
        king = self.get_king(next_color(self.move_side()))
        if not king:
            return False
        matrix = self._get_attack_matrix(self.move_side())
        return matrix[king.y][king.x]

    def is_checkmate(self) -> bool:
        """判断当前局面在对方回合是否为将死（无路可走）。"""
        original_player = self.move_side()
        self._move_side = next_color(self.move_side())
        try:
            return self.has_no_legal_moves()
        finally:
            self._move_side = original_player

    def has_no_legal_moves(self) -> bool:
        """判断当前走子方是否没有任何合法且不留被将军的走法（困毙）。"""
        king = self.get_king(self.move_side())
        if not king:
            return True
        for piece in self.get_pieces(self.move_side()):
            for move_it in piece.create_moves():
                if self.is_valid_move_t(move_it):
                    if not self.is_checked_move(move_it[0], move_it[1]):
                        return False
        return True

    def count_x_line_in(self, y: int, x_from: int, x_to: int) -> int:
        """统计同一行 y 上 x_from 与 x_to 之间（不含端点）被占用的格子数。"""
        return sum(1 for f in self.x_line_in(y, x_from, x_to) if f)

    def count_y_line_in(self, x: int, y_from: int, y_to: int) -> int:
        """统计同一列 x 上 y_from 与 y_to 之间（不含端点）被占用的格子数。"""
        return sum(1 for f in self.y_line_in(x, y_from, y_to) if f)

    def x_line_in(self, y: int, x_from: int, x_to: int) -> List[Optional[str]]:
        """返回水平方向上两个 x 之间（不含端点）的格子内容列表。"""
        step = 1 if x_to > x_from else -1
        return [self._board[y][x] for x in range(x_from + step, x_to, step)]

    def y_line_in(self, x: int, y_from: int, y_to: int) -> List[Optional[str]]:
        """返回垂直方向上两个 y 之间（不含端点）的格子内容列表。"""
        step = 1 if y_to > y_from else -1
        return [self._board[y][x] for y in range(y_from + step, y_to, step)]

    def from_fen(self, fen: str) -> bool:
        """从简化的 FEN 字符串加载棋盘布局并设置走子方。

        返回 True 表示加载成功，False 表示遇到无法识别字符。
        """

        fen = fen.strip()
        if fen == "":
            self.clear()
            return True

        fen0, fen1 = fen.split(" ")[:2]  # 只取前两个元素

        b = ChessBoard()
        x = 0
        y = 9
        for i, ch in enumerate(fen0):
            if (x > 9) or (y < 0):
                raise CChessError(f"fen:{fen} 行列超出界限:{i}, 列:{x}, 行:{y}")
            if ch == "/":
                x = 0
                y -= 1
            elif ch in _g_fen_num_set:
                x += int(ch)
            elif ch.lower() in _g_fen_ch_set:
                b.put_fench(ch, (x, y))
                x += 1
            else:
                raise CChessError(f"fen:{fen} 不合法的fen字符串:{i},[{ch}]")

        self._move_side = ANY_COLOR

        if fen1 == "b":
            b.set_move_side(BLACK)
        elif fen1 in ["w", "r"]:
            b.set_move_side(RED)
        else:
            raise CChessError(f"fen:{fen} 走子合理的值只包括[w,r,b] 当前值为:{fen1}")

        # 事务性转换
        self.from_board(b)

        return True

    def to_fen(self):
        """将棋盘序列化为简化 FEN 字符串（不含额外信息）。"""
        fen = ""
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
                fen += "/"

        if self.move_side() == BLACK:
            fen += " b"
        else:
            fen += " w"

        return fen

    def to_full_fen(self) -> str:
        """返回包含占位信息的完整 FEN（方便外部工具兼容）。"""
        return self.to_fen() + " - - 0 1"

    def zhash(self, fen: Optional[str] = None) -> int:
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
                if letter in Z_MAP_PIECES:
                    chess = Z_MAP_PIECES[letter]
                    key ^= Z_HASH_TABLE[chess * 256 + square]

        if self.move_side() == RED:
            key ^= Z_RED_KEY

        return (key & ((1 << 63) - 1)) - (key & (1 << 63))

    def detect_move_pieces(
        self, new_board: "ChessBoard"
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
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

    def create_move_from_board(
        self, new_board: "ChessBoard"
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
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
                    new_text = (
                        board_str[pos[1]][: pos[0]]
                        + fench_to_txt_name(ch)
                        + board_str[pos[1]][pos[0] + 2 :]
                    )
                    board_str[pos[1]] = new_text
                x -= 1
            y += 1

        return board_str

    def print_board(self):
        """在标准输出打印棋盘的文本表示，便于调试。"""
        print("")
        for s in self.text_view():
            print(s)

    def __str__(self):
        """__str__ 方法。"""
        return self.to_fen()

    def __repr__(self):
        """__repr__ 方法。"""
        return self.to_fen()

    def __eq__(self, other):
        """__eq__ 方法。"""
        if isinstance(other, str):
            return self.to_fen() == other
        if isinstance(other, ChessBoard):
            return self.to_fen() == other.to_fen()
        return False


# -----------------------------------------------------#
class ChessBoardOneHot(ChessBoard):
    """基于 `ChessBoard` 的独热编码棋盘表示。"""

    def __init__(self, fen="", chess_dict=None):
        """"""
        super().__init__(fen)
        self.__chess_dict = chess_dict

    def load_one_hot_dict(self, file):
        """从 JSON 文件加载棋子到独热向量的映射。"""
        self.__chess_dict = load_json(file) or {}
        self.__chess_dict[None] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def get_one_hot_board(self) -> list:
        """依据`self.__chess_dict`对棋子进行独热编码
        :return: 一个列表，将棋子进行独热编码后的棋盘
        """
        one_hot_board = []
        for x in self._board.copy():
            temp = []
            for y in x:
                temp.append(
                    self.__chess_dict.get(y, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                )
            one_hot_board.append(temp)
        return one_hot_board

    def chess_dict(self):
        """获取棋子-独热编码的映射
        :return: 字典，棋子-独热编码的映射
        """
        return self.__chess_dict.copy()
