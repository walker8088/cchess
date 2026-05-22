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

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .common import (
    _CHINESE_NUM_TO_INT,
    _COLUMN_CHAR_TO_IDX,
    _DIRECTION_CHAR_TO_SYMBOL,
    _QUALIFIER_DIGIT_MAP,
    COLUMN_MAP,
    DIRECTION_MAP,
    FULLWIDTH_NUM_MAP,
    PIECE_MAP,
    PRE_NUM_MAP,
    QUALIFIER_MAP,
    REVERSE_PIECE_MAP,
    SIDE_BLACK,
    SIDE_RED,
    fench_to_species,
    fench_to_text,
    next_side,
    pos2iccs,
    swap_fench,
)

# pylint: disable=too-many-branches,too-many-statements,too-many-locals


# -----------------------------------------------------#
@dataclass
class MoveInfo:
    """记录棋盘移动的增量状态信息，用于撤销操作"""

    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    moving_fench: str  # 移动的棋子字符
    captured_fench: Optional[str]  # 被吃棋子，None 表示无吃子
    prev_move_side: int  # 移动前走子方 (SIDE_RED/SIDE_BLACK/SIDE_ANY)
    next_move_side: int  # 移动后走子方 (SIDE_RED/SIDE_BLACK/SIDE_ANY)
    board_before: List[List[Optional[str]]]  # 移动前棋盘数组的深拷贝
    board_after: List[List[Optional[str]]]  # 移动后棋盘数组的深拷贝
    prev_attack_matrix_dirty: bool  # 移动前攻击矩阵脏标志
    next_attack_matrix_dirty: bool  # 移动后攻击矩阵脏标志


# pylint: disable=too-many-branches,too-many-statements,too-many-locals


# -----------------------------------------------------#
class MoveNotation:
    """走法中间表示，支持多种输出格式

    作用：将中文走法文本转换为统一的中间表示，便于解析和处理。

    中间表示包含：
    - piece_type: 棋子类型（K/A/B/N/R/C/P，大写红方，小写黑方）
    - column: 列索引（0-8，走子方视角）
    - direction: 方向（+进/-退/=平）
    - distance: 距离/目标列
    - qualifier: 限定词（前/中/后/数字）
    - piece_color: 棋子颜色（SIDE_RED/SIDE_BLACK）

    支持红方和黑方格式的走法文本解析，统一转换为中间表示后，
    可以方便地输出为不同格式（中文等）。
    """

    def __init__(
        self,
        piece_type,
        column,
        direction,
        distance,
        qualifier="",
        is_capture=False,
        is_check=False,
        is_checkmate=False,
        piece_color=None,
    ):
        self.piece_type = piece_type  # K/A/B/N/R/C/P
        self.column = column  # 0-8（红方视角）
        self.direction = direction  # +/ -/=
        self.distance = distance  # 1-9
        self.qualifier = qualifier  # f/m/b/1/2/3/4
        self.is_capture = is_capture
        self.is_check = is_check
        self.is_checkmate = is_checkmate
        self.piece_color = piece_color  # SIDE_RED/SIDE_BLACK

    @staticmethod
    def from_move(move):
        """从Move对象创建中间表示"""
        # 获取棋子信息
        board = move.board_before
        fench = board.get_fench(move.pos_from)
        species, color = fench_to_species(fench)

        # 确定棋子类型（大写红方，小写黑方）
        piece_type = species.upper() if color == SIDE_RED else species.lower()

        # 计算列（红方视角）
        column = move.pos_from[0]
        if color == SIDE_BLACK:
            # 黑方需要转换为红方视角
            column = 8 - column

        # 计算方向和目标信息
        diff = move.pos_to[1] - move.pos_from[1]
        if color == SIDE_BLACK:
            diff = -diff

        if diff == 0:
            direction = "="
            # 平移动：目标列（红方视角）
            target_column = move.pos_to[0]
            if color == SIDE_BLACK:
                target_column = 8 - target_column
            # 对于平移动，距离表示目标列
            distance = target_column
        else:
            direction = "+" if diff > 0 else "-"

            # 对于士、相、马，前进/后退显示的是目标列
            # 对于王、车、炮、兵，前进/后退显示的是步数
            if species in ("a", "b", "n"):  # 士、相、马
                # 目标列（红方视角）
                target_column = move.pos_to[0]
                if color == SIDE_BLACK:
                    target_column = 8 - target_column
                distance = target_column
            else:  # 王、车、炮、兵
                distance = abs(diff)

        # 确定限定词
        qualifier = MoveNotation._compute_qualifier(board, fench, move.pos_from, color)

        return MoveNotation(
            piece_type,
            column,
            direction,
            distance,
            qualifier,
            is_capture=bool(move.captured),
            is_check=move.is_checking,
            is_checkmate=move.is_checkmate,
            piece_color=color,
        )

    @staticmethod
    def _compute_qualifier(board, fench, pos, color):
        """根据同列相同棋子数量计算限定词（前/中/后/字母）。

        将/帅、士/仕、象/相没有限定词。
        车、马、炮、兵根据同列数量分配限定词。
        """
        if fench.lower() in ("k", "a", "b"):
            return ""

        # 收集同列相同棋子位置
        positions = []
        for y in range(10):
            if board._board[y][pos[0]] == fench:
                positions.append((pos[0], y))

        count = len(positions)
        if count <= 1:
            return ""

        # 排序位置（红方从下到上，黑方从上到下）
        if color == SIDE_RED:
            positions.sort(key=lambda p: (p[1], p[0]), reverse=True)
        else:
            positions.sort(key=lambda p: (p[1], -p[0]))

        # 找到当前位置的索引
        idx = positions.index(pos)

        # 根据数量分配限定词
        if count == 2:
            return "+" if idx == 0 else "."  # 前/后
        elif count == 3:
            return {0: "+", 1: "-", 2: "."}[idx]  # 前/中/后
        elif count == 4:
            # 前(idx=0), 二(idx=1), 三(idx=2), 后(idx=3)
            return {0: "+", 1: "b", 2: "c", 3: "."}[idx]
        else:
            # count >= 5: 前(idx=0), 后(idx=count-1), 中间用字母
            if idx == 0:
                return "+"
            if idx == count - 1:
                return "."
            return chr(ord("a") + idx)  # 字母限定词

    @staticmethod
    def from_text(text):
        """从中文走法文本解析中间表示

        参数:
            text: 中文走法字符串，如"炮二平五"、"前车进一"

        返回:
            MoveNotation对象，解析失败返回None
        """
        if not text:
            return None

        text = text.replace(" ", "")
        if not text:
            return None
        if len(text) != 4:
            raise ValueError(f"走法字符串长度应为4: {text!r}")

        # 1. 解析限定词
        qualifier = ""
        offset = 0
        first_char = text[0]
        if first_char in PRE_NUM_MAP:
            qualifier = PRE_NUM_MAP[first_char]
            offset = 1

        # 2. 解析棋子类型
        piece_char = text[offset]
        piece_type = REVERSE_PIECE_MAP.get(piece_char)
        if piece_type is None:
            raise ValueError(f"无法识别棋子: {piece_char!r}")
        offset += 1

        # 3. 解析列、方向和距离
        # 判断是否有列信息（有限定词时无列，否则需要检查是否是方向字符）
        column = None
        if text[offset] not in _DIRECTION_CHAR_TO_SYMBOL:
            # 存在列信息
            column = _COLUMN_CHAR_TO_IDX.get(text[offset])
            if column is None:
                return None
            offset += 1
            if len(text) < offset + 2:
                return None

        # 解析方向
        direction = _DIRECTION_CHAR_TO_SYMBOL.get(text[offset])
        if direction is None:
            return None

        # 解析距离（O(1) 查找）
        distance_char = text[offset + 1 :]
        distance = MoveNotation._parse_distance_char(
            distance_char, direction, piece_type
        )
        if distance is None:
            return None

        # 4. 确定棋子颜色
        piece_color = SIDE_RED if piece_type.isupper() else SIDE_BLACK

        return MoveNotation(
            piece_type=piece_type,
            column=column,
            direction=direction,
            distance=distance,
            qualifier=qualifier,
            piece_color=piece_color,
        )

    @staticmethod
    def _parse_distance_char(
        distance_char: str, direction: str, piece_type: str
    ) -> int | None:
        """解析距离字符，根据方向和棋子类型返回对应的数字。

        参数:
            distance_char: 距离字符（中文数字或全角数字）
            direction: 方向符号 ("+", "-", "=")
            piece_type: 棋子类型字符 (K/A/B/N/R/C/P)

        返回:
            距离数字，解析失败返回 None
        """
        # 平移或士/象/马：距离表示目标列
        if direction == "=" or piece_type.lower() in ("a", "b", "n"):
            return _COLUMN_CHAR_TO_IDX.get(distance_char)
        # 王/车/炮/兵：距离表示步数
        return _CHINESE_NUM_TO_INT.get(distance_char)

    def to_compact(self):
        """转换为 WXF 纵线格式

        WXF 格式规范：
        - 符号写在棋子的后面
        - 进=+ 退=- 平=.
        - 前=+ 中=- 后=.
        - 多兵同线：一二三四五→abcde
        - 有限定词时不显示列号
        - 无限定词时显示列号（1-9，从右到左）

        示例：
        - 炮二平五 → C2.5
        - 前炮退二 → C+-2
        - 前车平五 → R+.5
        - 一兵平五 → Pa.5
        """
        result = ""
        # 棋子名称（大写=红方，小写=黑方）
        result += self.piece_type

        if self.qualifier:
            # 有限定词：符号写在棋子后面，不显示列号
            result += self.qualifier
        else:
            # 无限定词：显示列号（WXF 从右到左 1-9）
            wxf_column = 9 - self.column
            result += str(wxf_column)

        # 方向符号：进=+ 退=- 平=.
        if self.direction == "=":
            result += "."
        else:
            result += self.direction

        # 距离/目标列
        if self.direction == "=" or self.piece_type.lower() in ("a", "b", "n"):
            # 平移或士/相/马：距离是目标列，需要转换为 WXF（从右到左）
            wxf_target = 9 - self.distance
            result += str(wxf_target)
        else:
            # 王/车/炮/兵进退：距离是步数，直接使用
            result += str(self.distance)

        # 添加特殊标记
        if self.is_capture:
            result += "x"
        if self.is_check:
            result += "+"
        if self.is_checkmate:
            result += "#"

        return result

    def to_chinese(self, traditional=False):
        """转换为中文（简体/繁体）

        参数:
            traditional: 是否使用繁体中文

        返回:
            str: 中文走法字符串
        """
        piece_name = PIECE_MAP[self.piece_type][1 if traditional else 0]
        color = self.piece_color
        direction_name = DIRECTION_MAP[self.direction][1 if traditional else 0]
        qualifier_name = self._get_qualifier_name(color, traditional)
        is_black = color == SIDE_BLACK

        if self.direction == "=" or self.piece_type.lower() in ("a", "b", "n"):
            # 平移动，或士/相/马的进退移动：显示目标列
            target = self._get_target_column(color)
        else:
            # 王/车/炮/兵的进退移动：显示步数
            target = self._get_distance_name(color)

        return self._build_move_str(
            piece_name, direction_name, target, qualifier_name, is_black
        )

    def _get_qualifier_name(self, color, traditional):
        """获取限定词名称（从 WXF/旧格式 转中文）"""
        if not self.qualifier:
            return ""

        idx = 1 if traditional else 0
        # 从统一 QUALIFIER_MAP 查找（支持 WXF + 旧格式）
        name = QUALIFIER_MAP.get(self.qualifier)
        if name:
            return name[idx]

        # 兼容旧数字格式（6-9）
        if self.qualifier in ("6", "7", "8", "9"):
            return _QUALIFIER_DIGIT_MAP[color][int(self.qualifier) - 1]

        return ""

    def _get_target_column(self, color):
        """获取目标列，红方用中文数字，黑方用全角数字"""
        if color == SIDE_RED:
            return COLUMN_MAP[self.distance][0]
        return FULLWIDTH_NUM_MAP.get(self.distance, str(self.distance))

    def _get_distance_name(self, color):
        """获取距离名称"""
        return _QUALIFIER_DIGIT_MAP[color][self.distance - 1]

    def _build_move_str(
        self, piece_name, direction_name, target_name, qualifier_name, is_black
    ):
        """构建走法字符串"""
        if qualifier_name:
            return f"{qualifier_name}{piece_name}{direction_name}{target_name}"

        # 获取列标识
        if is_black:
            column_name = FULLWIDTH_NUM_MAP[self.column]
        else:
            column_name = COLUMN_MAP[self.column][0]

        return f"{piece_name}{column_name}{direction_name}{target_name}"

    def __str__(self):
        return self.to_compact()


# -----------------------------------------------------#
class Move:
    """表示一步棋及其在走子树中的关系（含变招、注释等）。"""

    def __init__(
        self,
        move_info: "MoveInfo",
        board_before,
        board_after,
        is_checking=False,
        is_checkmate=False,
    ):
        """初始化一个走子对象。

        基于 MoveInfo 创建走子记录，包含移动前后棋盘状态。
        """

        self.move_info = move_info
        self.pos_from = move_info.from_pos
        self.pos_to = move_info.to_pos
        self.is_checking = is_checking
        self.is_checkmate = is_checkmate
        self.move_side = move_info.prev_move_side
        self.step_index = 0
        self.score = None
        self.annote = ""
        self.parent = None
        self.next_move = None
        self.variation_next = None
        self.variations_all = [self]
        self.move_list_for_engine = []
        self.fen_for_engine = None

        # 直接使用传入的棋盘实例
        self._board_cache = board_before  # 移动前的棋盘
        self._board_done_cache = board_after  # 移动后的棋盘

        # 设置被吃棋子
        self.captured = move_info.captured_fench

    @property
    def board_before(self):
        """移动前的棋盘状态"""
        return self._board_cache

    @property
    def board_after(self):
        """移动后的棋盘状态"""
        return self._board_done_cache

    # move_side 是数据属性，在构造函数中已赋值

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
        # 直接使用 board_before 获取实例，避免延迟导入
        mirrored_board = self.board_before.mirror()
        self.move_info.board_before = mirrored_board._board

        self.pos_from = (8 - self.pos_from[0], self.pos_from[1])
        self.pos_to = (8 - self.pos_to[0], self.pos_to[1])

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
        # 直接使用 board_before 获取实例，避免延迟导入
        flipped_board = self.board_before.flip()
        self.move_info.board_before = flipped_board._board

        self.pos_from = (self.pos_from[0], 9 - self.pos_from[1])
        self.pos_to = (self.pos_to[0], 9 - self.pos_to[1])

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
        # 直接使用 board_before 获取实例，避免延迟导入
        swapped_board = self.board_before.swap()
        self.move_info.board_before = swapped_board._board

        self.move_info.moving_fench = swap_fench(self.move_info.moving_fench)
        if self.move_info.captured_fench is not None:
            self.move_info.captured_fench = swap_fench(self.move_info.captured_fench)

        self.move_info.prev_move_side = next_side(self.move_info.prev_move_side)

        self._clear_caches()

        for move in self.get_variations():
            move.swap()

        if self.next_move:
            self.next_move.swap()

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

    def make_branchs_tag(self, branch_id, depth):
        """为走子树递归生成分支编号标记。

        当前为桩实现，预留接口供未来扩展。
        """
        pass

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

    def to_text(
        self,
        detailed=False,
        fmt="chinese",
        traditional=False,
    ):
        """返回此走子的文本表示。

        参数:
            detailed: 是否显示详细信息（吃子、将军等）
            fmt: 输出格式，可选值："chinese"（默认）、"compact"
            traditional: 当fmt为"chinese"时，是否使用繁体中文

        返回:
            指定格式的走法字符串
        """
        notation = MoveNotation.from_move(self)

        if fmt == "compact":
            text = notation.to_compact()
        else:  # "chinese" or default
            text = notation.to_chinese(traditional)

        if detailed:
            details = []
            if self.captured:
                # 吃子表示
                details.append("吃" + fench_to_text(self.captured))
            if self.is_checkmate:
                details.append("将死")
            elif self.is_checking:
                details.append("将军")

            if details:
                text = f"{text}({','.join(details)})"

        return text

    def to_text_detail(
        self,
        show_variation,
        show_annote,
        fmt="chinese",
        traditional=False,
    ):
        """返回走子的文本表示，可选择是否显示变招和注释。"""
        if show_variation:
            txt = self.to_text_variation(
                fmt=fmt,
                traditional=traditional,
            )
        else:
            txt = self.to_text(
                fmt=fmt,
                traditional=traditional,
            )

        annote = self.annote if show_annote else ""

        return (txt, annote)

    def to_text_variation(self, fmt="chinese", traditional=False):
        """返回带有变招标记的走子文本表示（多分支以方括号包裹）。"""
        assert len(self.variations_all) > 0

        # 父节点只有一个孩子，那就是自己
        if len(self.variations_all) == 1:
            return self.to_text(
                fmt=fmt,
                traditional=traditional,
            )

        txts = []
        for _index, m in enumerate(self.variations_all):
            if m == self:
                txts.append(f"{m.to_text(fmt=fmt, traditional=traditional)}")
            else:
                txts.append("*")

        return f"[{','.join(txts)}]"

    def prepare_for_engine(self, move_side, history):
        """为引擎查询准备 FEN 与 moves 列表。

        如果当前走子为吃子，则引擎的 FEN 应为走子后的局面；否则
        根据历史拼接 moves 列表以便向引擎发送完整走子序列。
        """
        if self.captured:
            # 吃子移动：使用 board_before 的副本生成走子后的 FEN
            temp_board = self.board_before.copy()

            # 应用移动
            moving_fench = temp_board._board[self.pos_from[1]][self.pos_from[0]]
            temp_board._board[self.pos_to[1]][self.pos_to[0]] = moving_fench
            temp_board._board[self.pos_from[1]][self.pos_from[0]] = "."
            temp_board.set_move_side(move_side)

            self.fen_for_engine = temp_board.to_fen()
            self.move_list_for_engine = []
        else:
            # 未吃子移动
            if not history:
                # 历史为空
                self.fen_for_engine = self.board_before.to_fen()
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
        return pos2iccs(self.pos_from, self.pos_to)
