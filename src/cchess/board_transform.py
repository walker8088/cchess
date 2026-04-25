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

from typing import Optional, Tuple, TypeVar

from .constants import ANY_COLOR, BLACK, RED

# 类型变量
T = TypeVar("T", bound="ChessBoard")


class BoardTransform:
    """棋盘变换功能类，提供镜像、翻转、交换等棋盘变换操作。

    此类包含原 ChessBoard 类中的棋盘变换方法，提取为独立类以便复用。
    """

    # 棋盘大小常量
    BOARD_WIDTH = 9  # 棋盘宽度（列数）
    BOARD_HEIGHT = 10  # 棋盘高度（行数）

    def mirror(self: T) -> T:
        """返回新棋盘: 沿竖直中线镜像（左右翻转）。

        坐标变换: (x, y) -> (8-x, y)
        """
        b = self.copy()
        b._board = [[self._board[y][8 - x] for x in range(9)] for y in range(10)]
        b._attack_matrix_dirty = True
        return b

    def flip(self: T) -> T:
        """返回新棋盘: 绕横轴翻转（上下翻转）+ 沿竖直中线镜像（左右翻转）。

        坐标变换: (x, y) -> (8-x, 9-y)
        """
        b = self.copy()
        b._board = [[self._board[9 - y][8 - x] for x in range(9)] for y in range(10)]
        b._attack_matrix_dirty = True
        return b

    def swap(self: T) -> T:
        """返回新棋盘: 交换棋子大小写（红黑互换）。

        大写表示红方、小写表示黑方。该方法将所有棋子字母大小写取反，
        同时切换走子方（调用 `next()`）。
        """

        def swap_fench(fench: Optional[str]) -> Optional[str]:
            """交换棋子大小写。"""
            if fench is None:
                return None
            return fench.upper() if fench.islower() else fench.lower()

        b = self.copy()
        b._board = [
            [swap_fench(self._board[y][x]) for x in range(9)] for y in range(10)
        ]

        b.set_move_side(b.move_side().next())
        b._attack_matrix_dirty = True

        return b

    @staticmethod
    def fen_mirror(fen: str) -> str:
        """返回给定 FEN 字符串的镜像局面 FEN。"""
        from .board import ChessBoard

        b = ChessBoard(fen)
        return b.mirror().to_fen()

    @staticmethod
    def fen_flip(fen: str) -> str:
        """返回给定 FEN 字符串的翻转局面 FEN。"""
        from .board import ChessBoard

        b = ChessBoard(fen)
        return b.flip().to_fen()

    @staticmethod
    def fen_swap(fen: str) -> str:
        """返回给定 FEN 字符串的交换局面 FEN。"""
        from .board import ChessBoard

        b = ChessBoard(fen)
        return b.swap().to_fen()

    def is_mirror(self) -> bool:
        """判断当前棋盘是否关于竖中线对称（镜像局面）。"""
        b = self.mirror()
        return self.to_fen() == b.to_fen()

    def normalized(self: T) -> T:
        """返回规范局面：当前走子方始终视为红方。

        如果当前是黑方走子，返回 swap().flip() 后的棋盘。
        如果当前是红方走子，返回棋盘的副本。

        返回:
            ChessBoard: 规范局面棋盘
        """
        if self.move_side().color == BLACK:
            return self.swap().flip()
        return self.copy()

    def is_normalized(self) -> bool:
        """判断当前是否为规范局面（红方走子）。"""
        return self.move_side().color == RED

    def denormalize_pos(self, pos: Tuple[int, int]) -> Tuple[int, int]:
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
