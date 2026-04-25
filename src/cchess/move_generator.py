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

from typing import Optional, Tuple

from .board_state import MoveInfo
from .common import fench_to_species, iccs2pos
from .constants import ANY_COLOR
from .exception import CChessError
from .move import Move


class MoveGenerator:
    """走法生成和执行类，负责棋子的移动、撤销和走法验证。

    此类从 ChessBoard 类中提取走法相关的功能，实现关注点分离。
    """

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
            self._move_side = self.move_side().next()

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
        """根据中文棋谱文本解析并执行走子，返回 `Move` 或 None。"""
        ret = Move.from_text(self, move_str)
        if not ret:
            return None

        for move_from, move_to in ret:
            move = self.move(move_from, move_to, check)
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
        """切换到下一个走子方并返回新的 `ChessPlayer` 实例（工具方法）。"""
        self._move_side = self.move_side().next()
        return self.move_side()
