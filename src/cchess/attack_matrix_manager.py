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


class AttackMatrixManager:
    """攻击矩阵管理类，负责管理红黑双方的攻击矩阵。

    攻击矩阵用于快速判断棋子是否被攻击，优化将军判断性能。
    """

    def __init__(self) -> None:
        """初始化攻击矩阵管理器。"""
        # 攻击矩阵缓存
        self._red_attacks: List[List[bool]] = [
            [False for _ in range(9)] for _ in range(10)
        ]
        self._black_attacks: List[List[bool]] = [
            [False for _ in range(9)] for _ in range(10)
        ]
        self._attack_matrix_dirty = True

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

    def mark_attack_matrix_dirty(self) -> None:
        """标记攻击矩阵为脏，需要重新计算。"""
        self._attack_matrix_dirty = True

    def get_red_attacks(self) -> List[List[bool]]:
        """获取红方攻击矩阵。"""
        if self._attack_matrix_dirty:
            self._recompute_attack_matrix()
        return self._red_attacks

    def get_black_attacks(self) -> List[List[bool]]:
        """获取黑方攻击矩阵。"""
        if self._attack_matrix_dirty:
            self._recompute_attack_matrix()
        return self._black_attacks

    def is_position_attacked_by(self, pos: Tuple[int, int], color: int) -> bool:
        """判断指定位置是否被指定颜色的棋子攻击。

        参数:
            pos: 要检查的位置 (x, y)
            color: 攻击方颜色 (RED 或 BLACK)

        返回:
            如果该位置被指定颜色的棋子攻击则返回 True，否则返回 False
        """
        if self._attack_matrix_dirty:
            self._recompute_attack_matrix()

        if color == RED:
            return self._red_attacks[pos[1]][pos[0]]
        else:
            return self._black_attacks[pos[1]][pos[0]]

    def is_king_attacked(self, king: Piece, attacker_color: int) -> bool:
        """判断指定颜色的王是否被攻击。

        参数:
            king: 要检查的王棋子
            attacker_color: 攻击方颜色 (RED 或 BLACK)

        返回:
            如果王被攻击则返回 True，否则返回 False
        """
        if not king:
            return False
        return self.is_position_attacked_by((king.x, king.y), attacker_color)

    def copy_attack_matrix(self) -> Tuple[List[List[bool]], List[List[bool]], bool]:
        """复制攻击矩阵状态。

        返回:
            元组 (red_attacks_copy, black_attacks_copy, attack_matrix_dirty)
        """
        red_copy = [row[:] for row in self._red_attacks]
        black_copy = [row[:] for row in self._black_attacks]
        return red_copy, black_copy, self._attack_matrix_dirty

    def restore_attack_matrix(
        self,
        red_attacks: List[List[bool]],
        black_attacks: List[List[bool]],
        attack_matrix_dirty: bool,
    ) -> None:
        """恢复攻击矩阵状态。

        参数:
            red_attacks: 红方攻击矩阵副本
            black_attacks: 黑方攻击矩阵副本
            attack_matrix_dirty: 攻击矩阵脏标志
        """
        self._red_attacks = [row[:] for row in red_attacks]
        self._black_attacks = [row[:] for row in black_attacks]
        self._attack_matrix_dirty = attack_matrix_dirty

    def clear(self) -> None:
        """清空攻击矩阵。"""
        self._red_attacks = [[False for _ in range(9)] for _ in range(10)]
        self._black_attacks = [[False for _ in range(9)] for _ in range(10)]
        self._attack_matrix_dirty = True
