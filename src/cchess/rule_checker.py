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

from typing import List, Tuple

from .constants import RED
from .piece import Piece


class RuleChecker:
    """规则检查类，负责将军、将死等规则判断。

    此类从 ChessBoard 类中提取规则检查相关的功能，实现关注点分离。
    """

    def is_checked_move(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]
    ) -> bool:
        """判断执行给定走子后己方是否处于被将军状态。
        若走子非法，抛出 `CChessError('Invalid Move')`。"""
        if not self.is_valid_move(pos_from, pos_to):
            from .exception import CChessError

            raise CChessError("Invalid Move")
        move_info = self.make_move(pos_from, pos_to)
        # make_move 不切换走子方，需要手动切换以检查移动后是否被将军
        self._move_side = self.move_side().next()
        checking = self.is_checking()
        # 恢复走子方
        self._move_side = move_info.prev_move_side
        self.unmake_move(move_info)
        return checking

    def is_checking_move(
        self, pos_from: Tuple[int, int], pos_to: Tuple[int, int]
    ) -> bool:
        """判断执行该走子后是否对对方形成将军（不切换走子方）。"""
        move_info = self.make_move(pos_from, pos_to)
        # 临时恢复走子方到移动前，以检查移动是否将军
        original_player = self.move_side()
        self._move_side = move_info.prev_move_side
        checking = self.is_checking()
        # 恢复回切换后的走子方，以便 unmake_move 正确工作
        self._move_side = original_player
        self.unmake_move(move_info)
        return checking

    def _compute_piece_attacks(self, piece: Piece) -> List[Tuple[int, int]]:
        """返回棋子可以攻击到的坐标列表（包括吃子位置）。"""
        attacks = []
        for from_pos, to_pos in piece.create_moves():
            attacks.append(to_pos)
        return attacks

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
            if color == RED:
                matrix = self._red_attacks
            else:
                matrix = self._black_attacks
            for x, y in attacks:
                matrix[y][x] = True
        self._attack_matrix_dirty = False

    def is_checking(self) -> bool:
        """判断当前走子方是否对对方构成将军（对方王被攻击）。"""
        if self._attack_matrix_dirty:
            self._recompute_attack_matrix()
        king = self.get_king(self.move_side().opposite())
        if not king:
            return False
        if self.move_side().color == RED:
            matrix = self._red_attacks
        else:
            matrix = self._black_attacks
        return matrix[king.y][king.x]

    def is_checkmate(self) -> bool:
        """判断当前局面在对方回合是否为将死（无路可走）。"""
        original_player = self.move_side()
        self._move_side = self.move_side().next()
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

    def x_line_in(self, y: int, x_from: int, x_to: int) -> List[str]:
        """返回水平方向上两个 x 之间（不含端点）的格子内容列表。"""
        step = 1 if x_to > x_from else -1
        return [self._board[y][x] for x in range(x_from + step, x_to, step)]

    def y_line_in(self, x: int, y_from: int, y_to: int) -> List[str]:
        """返回垂直方向上两个 y 之间（不含端点）的格子内容列表。"""
        step = 1 if y_to > y_from else -1
        return [self._board[y][x] for y in range(y_from + step, y_to, step)]
