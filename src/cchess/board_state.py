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

from .common import fench_to_species
from .constants import ANY_COLOR, BLACK, RED
from .piece import Piece


class ChessPlayer:
    """表示当前走子的玩家（颜色）。

    该类封装了简单的颜色切换逻辑，用于记录当前走子方。
    """

    def __init__(self, color: int) -> None:
        """初始化 ChessPlayer。

        参数:
            color: 颜色值 (RED=1, BLACK=2, ANY_COLOR=0)
        """
        self.color = color

    def next(self) -> "ChessPlayer":
        """切换到下一个玩家并返回新的 `ChessPlayer` 实例。

        如果当前颜色为 `ANY_COLOR`（任意颜色），则保持 `ANY_COLOR`。
        返回一个新的 `ChessPlayer`，避免就地修改引用带来的副作用。
        """
        if self.color == ANY_COLOR:
            return ChessPlayer(RED)
        return ChessPlayer(3 - self.color)

    def opposite(self) -> int:
        """返回与当前颜色相反的颜色值（整数）。

        如果颜色为 `ANY_COLOR`（任意颜色）则返回 `ANY_COLOR`。
        """
        if self.color == ANY_COLOR:
            return ANY_COLOR
        return 3 - self.color

    def __str__(self) -> str:
        """__str__ 方法。"""
        player_names = ("", "RED", "BLACK")
        return player_names[self.color]

    def __eq__(self, other: object) -> bool:
        """比较操作。

        支持与另一个 `ChessPlayer` 或整数颜色值比较。
        """
        if isinstance(other, ChessPlayer):
            return self.color == other.color
        if isinstance(other, int):
            return self.color == other
        return False


@dataclass
class MoveInfo:
    """记录棋盘移动的增量状态信息，用于撤销操作"""

    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    moving_fench: str  # 移动的棋子字符
    captured_fench: Optional[str]  # 被吃棋子，None 表示无吃子
    prev_attack_matrix_dirty: bool  # 移动前攻击矩阵脏标志
    next_attack_matrix_dirty: bool  # 移动后攻击矩阵脏标志
    prev_move_side: ChessPlayer  # 移动前走子方
    next_move_side: ChessPlayer  # 移动后走子方
    board_before: List[List[Optional[str]]]  # 移动前棋盘数组的深拷贝
    board_after: List[List[Optional[str]]]  # 移动后棋盘数组的深拷贝


class BoardState:
    """棋盘状态管理类：负责存储和操作棋盘基础状态。

    该类封装了棋盘数据存储、棋子操作、状态管理等基础功能，
    提供独立于规则逻辑的棋盘状态管理。
    """

    def __init__(self, fen: str = "") -> None:
        """初始化棋盘状态。

        参数:
            fen: 初始局面 FEN 字符串（可选）
        """
        self._board: List[List[Optional[str]]] = [
            [None for _ in range(9)] for _ in range(10)
        ]
        self._move_side = ChessPlayer(ANY_COLOR)

        if fen:
            self._parse_fen(fen)

    def clear(self) -> None:
        """清空棋盘并将走子方设为任意颜色（`ANY_COLOR`）。"""
        self._board = [[None for _ in range(9)] for _ in range(10)]
        self._move_side = ChessPlayer(ANY_COLOR)

    def copy(self) -> "BoardState":
        """返回棋盘状态的快照（独立副本）。"""
        return self.snapshot()

    def snapshot(self) -> "BoardState":
        """返回完全独立的棋盘状态副本。"""
        b = self.__class__()
        b._board = [row[:] for row in self._board]
        b.set_move_side(self.move_side())
        return b

    def from_board(self, other: "BoardState") -> None:
        """从另一个 BoardState 复制属性。"""
        self._board = [row[:] for row in other._board]
        self._move_side = other.move_side()

    def move_side(self) -> ChessPlayer:
        """获取当前走子方（ChessPlayer 对象）。"""
        return self._move_side

    def set_move_side(self, value) -> None:
        """设置走子方，支持整数或 ChessPlayer。"""
        if isinstance(value, int):
            self._move_side = ChessPlayer(value)
        else:
            self._move_side = value

    def _validate_pos(self, pos: Tuple[int, int]) -> None:
        """验证坐标是否在棋盘范围内。"""
        if not (0 <= pos[0] <= 8 and 0 <= pos[1] <= 9):
            raise ValueError(f"Position {pos} out of board bounds (0-8, 0-9)")

    def put_fench(self, fench: str, pos: Tuple[int, int]) -> None:
        """在指定位置放置棋子（不做合法性检查）。

        参数:
            fench: 棋子字符，例如 'K' 或 'p'
            pos: 目标坐标 (x, y)
        """
        self._validate_pos(pos)
        self._board[pos[1]][pos[0]] = fench

    def pop_fench(self, pos: Tuple[int, int]) -> Optional[str]:
        """移除并返回指定位置的棋子（若为空则返回 None）。"""
        self._validate_pos(pos)
        fench = self._board[pos[1]][pos[0]]
        self._board[pos[1]][pos[0]] = None
        return fench

    def get_fench(self, pos: Tuple[int, int]) -> Optional[str]:
        """返回指定位置的棋子字符。"""
        self._validate_pos(pos)
        return self._board[pos[1]][pos[0]]

    def occupied(self, pos: Tuple[int, int]) -> Optional[int]:
        """检查指定位置是否有棋子。

        参数:
            pos: 坐标 (x, y)

        返回:
            RED: 如果该位置有红方棋子
            BLACK: 如果该位置有黑方棋子
            None: 如果该位置为空
        """
        self._validate_pos(pos)
        fench = self._board[pos[1]][pos[0]]
        if fench is None:
            return None
        return RED if fench.isupper() else BLACK

    def get_fench_color(self, pos: Tuple[int, int]) -> Optional[int]:
        """返回指定位置棋子的颜色（`RED` 或 `BLACK`），若无棋子返回 None。"""
        fench = self.get_fench(pos)
        if not fench:
            return None
        return RED if fench.isupper() else BLACK

    def get_fenchs(self, fench: str) -> List[Tuple[int, int]]:
        """返回棋盘上所有与给定 fench 相同的坐标列表。"""
        positions = []
        for x in range(9):
            for y in range(10):
                if self._board[y][x] == fench:
                    positions.append((x, y))
        return positions

    def get_fenchs_x(self, fench: str, x: int) -> List[Tuple[int, int]]:
        """返回指定列 x 上匹配 fench 的所有坐标。"""
        positions = []
        for y in range(10):
            if self._board[y][x] == fench:
                positions.append((x, y))
        return positions

    def get_piece(self, pos: Tuple[int, int]) -> Optional[Piece]:
        """返回指定位置的 `Piece` 实例（若有棋子），否则返回 None。"""
        fench = self.get_fench(pos)
        return Piece.create(self, fench, pos) if fench else None

    def get_pieces(self, color: Optional[int] = None) -> Iterator[Piece]:
        """生成器：遍历棋盘并产出 `Piece` 对象。

        参数:
            color: 若指定，仅返回该颜色的棋子。
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

    def get_king(self, color) -> Optional[Piece]:
        """查找并返回指定颜色的王 `Piece`，找不到返回 None。

        参数:
            color: 指定要查找的颜色（整数或 ChessPlayer）。
        """
        if isinstance(color, ChessPlayer):
            color = color.color

        # 九宫格范围
        limit_y = ((), (0, 1, 2), (7, 8, 9))
        for x in (3, 4, 5):
            for y in limit_y[color]:
                fench = self._board[y][x]
                if not fench:
                    continue
                if fench.lower() == "k":
                    return Piece.create(self, fench, (x, y))
        return None

    def _parse_fen(self, fen: str) -> None:
        """解析 FEN 字符串并设置棋盘状态。

        这是一个简化版本，仅用于初始化。完整的 FEN 解析在 ChessBoard 类中。
        """
        parts = fen.split()
        if not parts:
            return

        board_part = parts[0]
        rows = board_part.split("/")

        for y, row in enumerate(rows):
            x = 0
            for char in row:
                if char.isdigit():
                    x += int(char)
                else:
                    if 0 <= y < 10 and 0 <= x < 9:
                        self._board[y][x] = char
                    x += 1

        # 设置走子方
        if len(parts) > 1:
            side_char = parts[1].lower()
            if side_char == "b":
                self._move_side = ChessPlayer(BLACK)
            else:
                self._move_side = ChessPlayer(RED)

    def __str__(self) -> str:
        """返回棋盘的文本表示。"""
        lines = []
        for y in range(10):
            line = []
            for x in range(9):
                fench = self._board[y][x]
                line.append(fench if fench else ".")
            lines.append("".join(line))
        return "\n".join(lines)

    def __repr__(self) -> str:
        """返回对象的官方字符串表示。"""
        return f"BoardState(fen='{self.to_fen()}')"

    def to_fen(self) -> str:
        """将棋盘状态转换为 FEN 字符串（简化版）。"""
        # 构建棋盘部分
        rows = []
        for y in range(10):
            row = []
            empty_count = 0
            for x in range(9):
                fench = self._board[y][x]
                if fench:
                    if empty_count > 0:
                        row.append(str(empty_count))
                        empty_count = 0
                    row.append(fench)
                else:
                    empty_count += 1
            if empty_count > 0:
                row.append(str(empty_count))
            rows.append("".join(row))

        board_fen = "/".join(rows)

        # 构建走子方部分
        side_char = "b" if self._move_side.color == BLACK else "w"

        return f"{board_fen} {side_char}"
