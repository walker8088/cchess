# -*- coding: utf-8 -*-
"""
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
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .common import (
    BLACK,
    RED,
    fench_to_species,
    fench_to_text,
    text_to_fench,
    pos2iccs,
    half2full,
    full2half,
)

if TYPE_CHECKING:
    from .board import MoveInfo

# pylint: disable=too-many-instance-attributes,too-many-public-methods
# pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
# pylint: disable=too-many-locals,fixme

# -----------------------------------------------------#
# 列索引数组：RED 使用中文数字（从右到左），BLACK 使用全角数字（从左到右）
_h_level_index = (
    (),
    ("九", "八", "七", "六", "五", "四", "三", "二", "一"),
    ("１", "２", "３", "４", "５", "６", "７", "８", "９"),
)

_v_change_index = (
    (),
    ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九"),
    ("误", "１", "２", "３", "４", "５", "６", "７", "８", "９"),
)

# 中文数字到半角数字映射
_ZH_TO_HALF = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

# 半角数字到中文数字映射
_HALF_TO_ZH = (None, "一", "二", "三", "四", "五", "六", "七", "八", "九")


def _detect_move_side_from_notation(move_str):
    """根据着法字符串中的数字类型检测走子方。

    - 含中文数字（一二三...）→ RED
    - 含阿拉伯数字（123...或 123...）→ BLACK

    参数:
        move_str: 走法字符串（已去除空格）

    返回:
        int: RED(1) 或 BLACK(2)，无法判断返回 None
    """
    # 检查是否包含中文数字
    has_chinese = any(ch in _ZH_TO_HALF for ch in move_str)

    # 检查是否包含阿拉伯数字（先转半角再检查）
    move_str_half = full2half(move_str)
    has_arabic = any(ch.isdigit() for ch in move_str_half)

    if has_chinese and not has_arabic:
        return RED
    elif has_arabic and not has_chinese:
        return BLACK
    else:
        # 混合或都无法判断
        return None


def _convert_digit_format(digit_char, move_side):
    """将数字字符转换为指定走子方的索引数组格式。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方（RED=1 用中文数字，BLACK=2 用全角数字）

    返回:
        str: 转换后的数字字符，无法转换返回 None
    """
    # 已经是目标格式
    try:
        _h_level_index[move_side].index(digit_char)
        return digit_char
    except ValueError:
        pass

    # 半角数字
    if digit_char.isdigit():
        half_digit = int(digit_char)
        if half_digit == 0 or half_digit > 9:
            return None
        if move_side == 1:  # RED: 半角转中文
            return _HALF_TO_ZH[half_digit]
        else:  # BLACK: 半角转全角
            return chr(0xFF10 + half_digit)

    # 中文数字（仅用于红方）
    if digit_char in _ZH_TO_HALF:
        if move_side == 1:  # RED: 保持中文
            return _HALF_TO_ZH[_ZH_TO_HALF[digit_char]]
        # BLACK 不接受中文数字，返回 None
        return None

    return None


def _get_index(digit_char, move_side, use_v_index=False):
    """获取数字字符在索引数组中的位置。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方（RED=1 用中文数字，BLACK=2 用全角数字）
        use_v_index: True 使用_v_change_index，False 使用_h_level_index

    返回:
        int: 索引位置 (0-9)，找不到返回 None
    """
    index_array = _v_change_index if use_v_index else _h_level_index

    try:
        return index_array[move_side].index(digit_char)
    except ValueError:
        pass

    # 尝试转换格式后查找
    converted = _convert_digit_format(digit_char, move_side)
    if converted:
        try:
            return index_array[move_side].index(converted)
        except ValueError:
            pass

    return None


def _get_digit_index(digit_char, move_side):
    """获取数字字符在列索引数组中的位置。

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方（RED=1 用中文数字，BLACK=2 用全角数字）

    返回:
        int: 列索引 (0-8)，找不到返回 None
    """
    return _get_index(digit_char, move_side, use_v_index=False)


def _get_v_index(step_digit, move_side):
    """获取步数数字在 v_index 数组中的位置。

    参数:
        step_digit: 数字字符（中文、半角或全角）
        move_side: 走子方

    返回:
        int: 步数差值，找不到返回 None
    """
    return _get_index(step_digit, move_side, use_v_index=True)


def _get_target_x(digit_char, move_side):
    """Get target column index.

    参数:
        digit_char: 数字字符（中文、半角或全角）
        move_side: 走子方

    返回:
        int: 目标列索引 (0-8)，无法解析返回 None
    """
    digit_index = _get_digit_index(digit_char, move_side)
    if digit_index is None:
        return None
    return digit_index


def _advisor_move(move_side, p_from, move_str):
    """解析士/仕的走法。

    参数:
        move_side: 走子方
        p_from: 起点坐标
        move_str: 走法字符串（如'进 6'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)
    """
    direction = move_str[0]
    target_digit = move_str[1:].strip()

    new_x = _get_target_x(target_digit, move_side)
    if new_x is None:
        return None

    if abs(new_x - p_from[0]) != 1:
        return None

    diff_y = -1 if direction == "进" else 1
    if move_side == BLACK:
        diff_y = -diff_y

    return (new_x, p_from[1] - diff_y)


def _bishop_move(move_side, p_from, move_str):
    """解析象/相的走法。

    参数:
        move_side: 走子方
        p_from: 起点坐标
        move_str: 走法字符串（如'进 5'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)
    """
    direction = move_str[0]
    target_digit = move_str[1:].strip()

    new_x = _get_target_x(target_digit, move_side)
    if new_x is None:
        return None

    if abs(new_x - p_from[0]) != 2:
        return None

    diff_y = -2 if direction == "进" else 2
    if move_side == BLACK:
        diff_y = -diff_y

    return (new_x, p_from[1] - diff_y)


def _knight_move(move_side, p_from, move_str):
    """解析马的走法。

    参数:
        move_side: 走子方
        p_from: 起点坐标
        move_str: 走法字符串（如'进 5'、'退 3'）

    返回:
        tuple: 目标坐标 (x, y)
    """
    direction = move_str[0]
    target_digit = move_str[1:].strip()

    new_x = _get_target_x(target_digit, move_side)
    if new_x is None:
        return None

    diff_x = abs(p_from[0] - new_x)

    if diff_x not in (1, 2):
        return None

    diff_y_magnitude = 2 if diff_x == 1 else 1

    # Calculate y-coordinate
    # For RED: 进 = y increases (diff_y > 0), 退 = y decreases (diff_y < 0)
    # For BLACK: 进 = y decreases (diff_y < 0), 退 = y increases (diff_y > 0)
    if direction == "进":
        diff_y = diff_y_magnitude if move_side == RED else -diff_y_magnitude
    else:  # 退
        diff_y = -diff_y_magnitude if move_side == RED else diff_y_magnitude

    return (new_x, p_from[1] + diff_y)


def _king_rook_cannon_pawn_move(move_side, p_from, move_str):
    """解析王、车、炮、兵的走法。

    参数:
        move_side: 走子方
        p_from: 起点坐标
        move_str: 走法字符串（如'进一'、'平五'）

    返回:
        tuple: 目标坐标 (x, y)
    """
    # 平移
    if move_str[0] == "平":
        new_x = _get_digit_index(move_str[1], move_side)
        if new_x is None:
            return None
        return (new_x, p_from[1])

    # 前进/后退 - 使用 _get_digit_index 获取步数
    step_digit = move_str[1:].strip()

    # 使用 _v_change_index 获取步数差值
    try:
        diff = _v_change_index[move_side].index(step_digit)
    except ValueError:
        # 尝试转换格式
        diff = _get_v_index(step_digit, move_side)
        if diff is None:
            return None

    if move_str[0] == "退":
        diff = -diff

    # 黑方前进方向与红方相反
    if move_side == BLACK:
        diff = -diff

    return (p_from[0], p_from[1] + diff)


# -----------------------------------------------------#
class Move:
    """表示一步棋及其在走子树中的关系（含变招、注释等）。"""

    def __init__(self, move_info: MoveInfo, is_checking=False, is_checkmate=False):
        """初始化一个走子对象。

        基于 MoveInfo 创建走子记录，包含移动前后棋盘状态。
        """

        self.move_info = move_info
        self.p_from = move_info.from_pos
        self.p_to = move_info.to_pos
        self.is_checking = is_checking
        self.is_checkmate = is_checkmate
        self.step_index = 0
        self.score = None
        self.annote = ""
        self.parent = None
        self.next_move = None
        self.variation_next = None
        self.variations_all = [self]
        self.move_list_for_engine = []
        self.fen_for_engine = None

        # 延迟计算的棋盘快照（仅 board，board_done 已移除）
        self._board_cache = None

        # 设置被吃棋子
        self.captured = move_info.captured_fench

    @property
    def board(self):
        """移动前的棋盘状态（延迟生成的快照）"""
        if self._board_cache is None:
            from .board import ChessBoard

            # 创建新棋盘实例，复制移动前状态
            b = ChessBoard()
            b._board = [row[:] for row in self.move_info.board_before]
            b.move_side = self.move_info.prev_move_side
            b._attack_matrix_dirty = self.move_info.prev_attack_matrix_dirty
            # 攻击矩阵缓存保持默认（脏标志为 True 时会被重新计算）
            self._board_cache = b
        return self._board_cache

    @property
    def move_side(self):
        """返回执行此走子的玩家（当前棋盘的 `move_side`）。"""
        return self.board.move_side

    def __str__(self):
        """返回此走子的 ICCS 格式字符串表示。"""
        return self.to_iccs()

    def _clear_caches(self):
        """Clear cached board snapshots to force regeneration."""
        self._board_cache = None
        self._board_done_cache = None

    def mirror(self):
        """水平镜像当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行左右镜像，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        from .board import ChessBoard

        temp_board = ChessBoard()
        temp_board._board = self.move_info.board_before
        mirrored_board = temp_board.mirror()
        self.move_info.board_before = mirrored_board._board

        self.p_from = (8 - self.p_from[0], self.p_from[1])
        self.p_to = (8 - self.p_to[0], self.p_to[1])

        self._clear_caches()

        for move in self.get_variations():
            move.mirror()

        if self.next_move:
            self.next_move.mirror()

    def flip(self):
        """垂直翻转当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行上下翻转，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        from .board import ChessBoard

        temp_board = ChessBoard()
        temp_board._board = self.move_info.board_before
        flipped_board = temp_board.flip()
        self.move_info.board_before = flipped_board._board

        self.p_from = (self.p_from[0], 9 - self.p_from[1])
        self.p_to = (self.p_to[0], 9 - self.p_to[1])

        self._clear_caches()

        for move in self.get_variations():
            move.flip()

        if self.next_move:
            self.next_move.flip()

    def swap(self):
        """交换红黑视角（棋子交换阵营）并更新所有子节点（就地）。

        对当前走子、`board_done` 及所有分支和 `next_move` 做视角
        交换，使之从另一方视角表示。
        """
        from .board import ChessBoard

        temp_board = ChessBoard()
        temp_board._board = self.move_info.board_before
        swapped_board = temp_board.swap()
        self.move_info.board_before = swapped_board._board

        def swap_fench(fench):
            """swap_fench 函数。"""
            if fench is None:
                return None
            return fench.upper() if fench.islower() else fench.lower()

        self.move_info.moving_fench = swap_fench(self.move_info.moving_fench)
        self.move_info.captured_fench = swap_fench(self.move_info.captured_fench)

        self.move_info.prev_move_side = self.move_info.prev_move_side.next()

        self._clear_caches()

        for move in self.get_variations():
            move.swap()

        if self.next_move:
            self.next_move.swap()

    def is_valid_move(self):
        """判断该走子在原始棋盘上是否合法。

        通过底层棋盘的 `is_valid_move` 方法验证由 `p_from` 到 `p_to`
        的移动是否合法，返回布尔值。
        """
        return self.board.is_valid_move(self.p_from, self.p_to)

    def is_king_killed(self):
        """如果此走子吃掉了将/帅，返回 True。

        检查记录的 `captured` 字符是否表示国王（不区分大小写）。
        """
        if self.captured and self.captured.lower() == "k":
            return True
        return False

    def len_variations(self):
        """返回当前走子的分支（变招）数量。"""
        return len(self.variations_all)

    def get_variations(self, include_me=False):
        """返回当前走子的所有分支（变招），可选择是否包含自身。"""
        if include_me:
            return self.variations_all

        sibs = self.variations_all[:]
        sibs.remove(self)

        return sibs

    def last_variation(self):
        """返回最后一个分支（变招）走子。"""
        return self.variations_all[-1]

    def get_variation_index(self):
        """返回当前走子在分支列表中的索引及分支总数。"""
        sibling_count = len(self.variations_all)
        for index, m in enumerate(self.variations_all):
            if m == self:
                return (index, sibling_count)
        return None

    def add_variation(self, chess_move):
        """将 `chess_move` 添加为当前走子的一个新分支（变招）。"""
        chess_move.parent = self.parent
        chess_move.step_index = self.step_index
        last = self.last_variation()

        assert last.variation_next is None

        last.variation_next = chess_move

        self.variations_all.append(chess_move)
        for node in self.get_variations():
            node.variations_all = self.variations_all

        return chess_move

    def remove_variation(self, chess_move):
        """从当前走子的分支列表中移除指定的 `chess_move`。"""
        if chess_move not in self.variations_all:
            return

        # 先移出兄弟表
        self.variations_all.remove(chess_move)

        # 从链上摘下
        # 找到链表头节点（第一个兄弟节点）
        head = self.variations_all[0]

        # 如果要删除的是头节点
        if chess_move == head:
            # 将原头节点从链表中断开
            chess_move.variation_next = None
            # 注意：variations_all 已经更新，head 已经变为新的头节点
        else:
            # 遍历链表找到前驱节点
            prev = head
            while prev.variation_next and prev.variation_next != chess_move:
                prev = prev.variation_next
            if prev.variation_next == chess_move:
                # 跳过要删除的节点
                prev.variation_next = chess_move.variation_next
                chess_move.variation_next = None

        # 更新兄弟表到所有的兄弟
        for node in self.get_variations():
            node.variations_all = self.variations_all

    def append_next_move(self, chess_move):
        """将 `chess_move` 作为当前走子的后继加入走子树。

        设置 `chess_move.parent` 与 `step_index`。若当前无 `next_move`
        则作为线性后继；否则将其作为现有 `next_move` 的一个分支。
        """
        chess_move.parent = self
        chess_move.step_index = self.step_index + 1
        if not self.next_move:
            self.next_move = chess_move
        else:
            self.next_move.variations_all.append(chess_move)

    def dump_moves(
        self, move_list, curr_move_line, is_tree_mode, curr_variation_index=0
    ):
        """将从当前节点开始的走子线路序列化并追加到 `move_list`。

        `curr_move_line` 表示当前遍历路径，本方法会在递归过程中
        扩展路径并将每条线（含分支索引）追加到 `move_list`。
        """

        backup_move_line = curr_move_line["moves"][:]
        curr_move_line["moves"].append(self)

        curr_line_index = curr_move_line["index"]

        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line, is_tree_mode, 0)

        # curr_variation_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        # 所以就不能在分支中再找兄弟了，否则会重复输出分支
        # assert curr_variation_index == self.get_variation_index()
        if curr_variation_index > 0:
            return

        # 只有主分支（index == 0）才会遍历兄弟分支

        for index, variation_move in enumerate(self.get_variations()):
            variation_index = index + 1
            new_line_index = len(move_list)
            line_name = f"{curr_line_index}.{self.step_index}.{variation_index}_{new_line_index}"
            new_line = {
                "index": new_line_index,
                "name": line_name,
                #'variations':variations,
                "variation_index": variation_index,
                "from_line": (curr_line_index, self.step_index, variation_index),
                "moves": [],
            }

            if not is_tree_mode:
                new_line["moves"].extend(backup_move_line)

            move_list.append(new_line)
            variation_move.dump_moves(
                move_list, new_line, is_tree_mode, variation_index
            )

    def init_move_line(self):
        """初始化并返回一个空的走子线路字典。"""
        return {"index": 0, "name": "0", "variations": [], "moves": []}

    def to_text(self, detailed=False):
        """返回此走子的中文可读文本表示。

        若 `detailed` 为 True，则在返回字符串后附加括号内的详细信息，
        例如吃子、将军或将死等注记。
        """

        fench = self.board.get_fench(self.p_from)
        _, man_side = fench_to_species(fench)

        diff = self.p_to[1] - self.p_from[1]

        # 黑方是红方的反向操作
        if man_side == BLACK:
            diff = -diff

        if diff == 0:
            diff_str = "平"
        elif diff > 0:
            diff_str = "进"
        else:
            diff_str = "退"

        # 王车炮兵规则
        if fench.lower() in ("k", "r", "c", "p"):
            if diff == 0:
                dest_str = _h_level_index[man_side][self.p_to[0]]
            elif diff > 0:
                dest_str = _v_change_index[man_side][diff]
            else:
                dest_str = _v_change_index[man_side][-diff]
        else:  # 士相马的规则
            dest_str = _h_level_index[man_side][self.p_to[0]]

        name_str = self.__get_text_name(self.p_from)

        text = name_str + diff_str + dest_str
        if not detailed:
            return text

        details = []
        if self.captured:
            details.append(
                f"吃{fench_to_text(self.captured)}",
            )
        if self.is_checkmate:
            details.append(
                "将死",
            )
        elif self.is_checking:
            details.append(
                "将军",
            )

        if len(details) == 0:
            return text
        return f"{text}({','.join(details)})"

    def __get_text_name(self, pos):
        """根据位置计算并返回带有位置限定词的棋子名称。

        当棋盘上有多个相同类型的子时（例如同一列有多辆车），返回
        用于区分的限定词如 '前'、'中'、'后' 或文件编号。
        """

        fench = self.board.get_fench(pos)
        _, man_side = fench_to_species(fench)
        piece_name = fench_to_text(fench)

        # 王，士，相命名规则
        if fench.lower() in ("k", "a", "b"):
            return piece_name + _h_level_index[man_side][pos[0]]

        # 车,马,炮,兵命名规则
        # 红黑顺序相反，俩数组减少计算工作量
        pos_name2 = ((), ("后", "前"), ("前", "后"))
        pos_name3 = ((), ("后", "中", "前"), ("前", "中", "后"))
        pos_name4 = ((), ("后", "三", "二", "前"), ("前", "２", "３", "后"))
        pos_name5 = ((), ("后", "四", "三", "二", "前"), ("前", "２", "３", "４", "后"))

        count = 0
        pos_index = -1
        for y in range(10):
            if self.board._board[y][pos[0]] == fench:  # pylint: disable=protected-access
                if pos[1] == y:
                    pos_index = count
                count += 1

        if count == 1:
            return piece_name + _h_level_index[man_side][pos[0]]
        if count == 2:
            return pos_name2[man_side][pos_index] + piece_name
        if count == 3:
            # TODO 查找另一个多子行
            return pos_name3[man_side][pos_index] + piece_name
        if count == 4:
            return pos_name4[man_side][pos_index] + piece_name
        if count == 5:
            return pos_name5[man_side][pos_index] + piece_name

        return piece_name + _h_level_index[man_side][pos[0]]

    def to_text_detail(self, show_variation, show_annote):
        """返回走子的文本表示，可选择是否显示变招和注释。"""
        if show_variation:
            txt = self.to_text_variation()
        else:
            txt = self.to_text()

        annote = self.annote if show_annote else ""

        return (txt, annote)

    def to_text_variation(self):
        """返回带有变招标记的走子文本表示（多分支以方括号包裹）。"""
        assert len(self.variations_all) > 0

        # 父节点只有一个孩子，那就是自己
        if len(self.variations_all) == 1:
            return self.to_text()

        txts = []
        for _index, m in enumerate(self.variations_all):
            if m == self:
                txts.append(f"{m.to_text()}")
            else:
                txts.append("*")  # m.to_text())

        return f"[{','.join(txts)}]"

    def prepare_for_engine(self, move_side, history):
        """为引擎查询准备 FEN 与 moves 列表。

        如果当前走子为吃子，则引擎的 FEN 应为走子后的局面；否则
        根据历史拼接 moves 列表以便向引擎发送完整走子序列。
        """
        if self.captured:
            # 吃子移动：临时生成走子后的 FEN，不缓存棋盘对象
            from .board import ChessBoard

            temp_board = ChessBoard()
            temp_board._board = [row[:] for row in self.move_info.board_before]
            temp_board.move_side = self.move_info.prev_move_side

            # 应用移动
            moving_fench = temp_board._board[self.p_from[1]][self.p_from[0]]
            temp_board._board[self.p_to[1]][self.p_to[0]] = moving_fench
            temp_board._board[self.p_from[1]][self.p_from[0]] = None
            temp_board.move_side = move_side

            self.fen_for_engine = temp_board.to_fen()
            self.move_list_for_engine = []
        else:
            # 未吃子移动
            if not history:
                # 历史为空
                self.fen_for_engine = self.board.to_fen()
                self.move_list_for_engine = [self.to_iccs()]
            else:
                # 历史不为空，向后追加
                last_move = history[-1]
                self.fen_for_engine = last_move.fen_for_engine
                self.move_list_for_engine = last_move.move_list_for_engine[:]
                self.move_list_for_engine.append(self.to_iccs())

    def to_engine_fen(self):
        """返回用于引擎的输入字符串：基础 FEN（可选加 moves）。

        若 `move_list_for_engine` 为空，直接返回 `fen_for_engine`；
        否则返回形如 '<fen> moves <m1> <m2> ...' 的字符串。
        """
        if len(self.move_list_for_engine) == 0:
            return self.fen_for_engine

        move_str = " ".join(self.move_list_for_engine)
        return " ".join([self.fen_for_engine, "moves", move_str])

    def to_iccs(self):
        """返回此走子的 ICCS（引擎）走法字符串。

        将内部 (x,y) 坐标元组转换为引擎使用的 ICCS 表示法。
        """
        return pos2iccs(self.p_from, self.p_to)

    @staticmethod
    def text_move_to_std_move(piece_fench, move_side, p_from, move_str):
        """将中文走法片段转换为目标坐标。

        参数:
            piece_fench: 棋子类型字符
            move_side: 走子方
            p_from: 起点坐标
            move_str: 走法字符串（如'进一'、'平五'等）

        返回:
            tuple: 目标坐标 (x, y)，无法解析返回 None
        """
        # 移动规则检查
        if not move_str:
            return None
        if piece_fench in ["a", "b", "n"] and move_str[0] == "平":
            return None
        if move_str[0] not in ["进", "退", "平"]:
            return None

        # 王，车，炮，兵的移动规则
        if piece_fench in ["k", "r", "c", "p"]:
            return _king_rook_cannon_pawn_move(move_side, p_from, move_str)

        # 仕/士的移动规则
        if piece_fench == "a":
            return _advisor_move(move_side, p_from, move_str)

        # 象/相的移动规则
        if piece_fench == "b":
            return _bishop_move(move_side, p_from, move_str)

        # 马的移动规则
        if piece_fench == "n":
            return _knight_move(move_side, p_from, move_str)

        return None

    @staticmethod
    def from_text(board, move_str):
        """解析中文走法字符串，返回标准化的走子 ((p_from, p_to))。

        根据数字类型检测走子方：中文数字=RED，阿拉伯数字=BLACK。
        直接在原始棋盘上查找棋子，不使用规范局面转换。
        """
        move_str = move_str.replace(" ", "")

        move_indices = ["前", "中", "后", "一", "二", "三", "四", "五"]

        multi_pieces = False
        multi_lines = False

        if move_str[0] in move_indices:
            multi_pieces = True
            man_index = move_indices.index(move_str[0])
            if man_index > 2:
                multi_lines = True
            piece_name = move_str[1]
        else:
            piece_name = move_str[0]

        work_side = _detect_move_side_from_notation(move_str)
        if work_side is None:
            work_side = board.move_side.color
        if work_side == 0:
            work_side = RED

        fench = text_to_fench(piece_name, work_side)
        if not fench:
            return None

        piece_fench = fench.lower()

        if multi_lines:
            digit_char = move_str[0]
            target_x = _get_digit_index(digit_char, work_side)

            positions = []
            if target_x is not None:
                positions = board.get_fenchs_x(fench, target_x)

            if not positions:
                positions = board.get_fenchs(fench)

            if piece_fench == "p" and len(positions) > 1:
                if work_side == RED:
                    positions.sort(key=lambda p: p[1], reverse=True)
                else:
                    positions.sort(key=lambda p: p[1])

            if len(positions) == 0:
                return None

            for pos in positions:
                move = Move.text_move_to_std_move(
                    piece_fench, work_side, pos, move_str[2:]
                )
                if move:
                    return [(pos, move)]

            return None

        if not multi_pieces:
            digit_char = move_str[1]
            x = _get_digit_index(digit_char, work_side)
            if x is None:
                return None
            positions = board.get_fenchs_x(fench, x)

            if len(positions) == 0:
                return None

            if (len(positions) > 1) and (piece_fench not in ["a", "b"]):
                return None

            moves = []
            for pos in positions:
                move = Move.text_move_to_std_move(
                    piece_fench, work_side, pos, move_str[2:]
                )
                if move:
                    moves.append((pos, move))

            return moves

        if move_str[0] in ["前", "中", "后"]:
            positions = board.get_fenchs(fench)

            move_idx = {"前": -1, "中": 1, "后": 0}
            if work_side == BLACK:
                positions.sort(key=lambda p: p[1])
            pos = positions[move_idx[move_str[0]]]

            move = Move.text_move_to_std_move(piece_fench, work_side, pos, move_str[2:])
            if move:
                return [(pos, move)]
            return None
        return None
