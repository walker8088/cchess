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

# pylint: disable=invalid-name
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
# pylint: disable=too-many-arguments,too-few-public-methods

# import os
import struct
from typing import Tuple

from .board import ChessBoard, ChessPlayer
from .common import RED, fench_to_species

# -----------------------------------------------------#
# result_dict = {0: UNKNOWN, 1: RED_WIN, 2: BLACK_WIN, 3: PEACE, 4: PEACE}
result_dict = {0: "*", 1: "1-0", 2: "0-1", 3: "1/2-1/2", 4: "1/2-1/2"}


def _decode_pos(man_pos):
    """将单个压缩的棋子位置整数解码为 (x, y) 坐标。

    XQF 中棋子位置一般以十进制编码，函数将其拆为列和行。
    """
    return (int(man_pos // 10), man_pos % 10)


def _decode_pos2(man_pos):
    """将包含两个压缩位置的元组解码为 ((from_x,from_y),(to_x,to_y))。"""
    return (
        (int(man_pos[0] // 10), man_pos[0] % 10),
        (int(man_pos[1] // 10), man_pos[1] % 10),
    )


# -----------------------------------------------------#
class XQFKey:
    """承载 XQF 文件中用于解密走子和注释的密钥字段的简单容器。"""

    def __init__(self):
        """初始化密钥容器。"""
        self.KeyXY = None
        self.KeyXYf = None
        self.KeyXYt = None
        self.KeyRMKSize = None
        self.FKeyBytes = None
        self.F32Keys = None


# -----------------------------------------------------#
class XQFBuffDecoder:
    """对 XQF 中走子数据区的字节流提供顺序读取辅助。

    提供按字节读取、按长度解码字符串以及读取 4 字节整数的便利方法，
    以便在解析走子（steps）时按顺序消费缓冲区。
    """

    def __init__(self, buffer):
        """__init__ 方法。"""
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)

    def __read(self, size):
        """内部方法：从当前索引读 `size` 字节并推进索引。"""
        start = self.index
        stop = min(self.index + size, self.length)

        self.index = stop
        return self.buffer[start:stop]

    def read_str(self, size, coding="GB18030"):
        """读取指定字节并按给定编码尝试解码为字符串，失败返回 None。"""

        buff = self.__read(size)

        try:
            ret = buff.decode(coding)
        except (UnicodeDecodeError, ValueError):
            ret = None

        return ret

    def read_bytes(self, size):
        """读取指定字节并返回 bytearray。"""
        return bytearray(self.__read(size))

    def read_int(self):
        """读取 4 字节并按小端序返回一个整数。"""
        data = self.read_bytes(4)
        return data[0] + (data[1] << 8) + (data[2] << 16) + (data[3] << 24)


# -------------------------------------------------
def __init_decrypt_key(buff_str):
    """根据 XQF 头部的密钥字段计算并返回用于解密数据的 `XQFKey` 对象。"""

    keys = XQFKey()

    # Pascal code here from XQFRW.pas
    # KeyMask   : dTByte;                         // 加密掩码
    # ProductId : dTDWord;                        // 产品号(厂商的产品号)
    # KeyOrA    : dTByte;
    # KeyOrB    : dTByte;
    # KeyOrC    : dTByte;
    # KeyOrD    : dTByte;
    # KeysSum   : dTByte;                         // 加密的钥匙和
    # KeyXY     : dTByte;                         // 棋子布局位置钥匙
    # KeyXYf    : dTByte;                         // 棋谱起点钥匙
    # KeyXYt    : dTByte;                         // 棋谱终点钥匙

    (
        HEAD_KeyMask,
        _HEAD_ProductId,
        HEAD_KeyOrA,
        HEAD_KeyOrB,
        HEAD_KeyOrC,
        HEAD_KeyOrD,
        HEAD_KeysSum,
        HEAD_KeyXY,
        HEAD_KeyXYf,
        HEAD_KeyXYt,
    ) = struct.unpack("<BIBBBBBBBB", buff_str)
    # 以下是密码计算公式

    # 棋子32个位置加密因子
    bKey = HEAD_KeyXY
    keys.KeyXY = ((((((bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * bKey) & 0xFF

    # 棋谱加密因子(起点)
    bKey = HEAD_KeyXYf
    keys.KeyXYf = (
        (((((bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * keys.KeyXY
    ) & 0xFF

    # 棋谱加密因子(终点)
    bKey = HEAD_KeyXYt
    keys.KeyXYt = (
        (((((bKey * bKey) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * keys.KeyXYf
    ) & 0xFF

    # 注解大小加密因子
    wKey = HEAD_KeysSum * 256 + HEAD_KeyXY
    keys.KeyRMKSize = ((wKey % 32000) + 767) & 0xFFFF

    B1 = (HEAD_KeysSum & HEAD_KeyMask) | HEAD_KeyOrA
    B2 = (HEAD_KeyXY & HEAD_KeyMask) | HEAD_KeyOrB
    B3 = (HEAD_KeyXYf & HEAD_KeyMask) | HEAD_KeyOrC
    B4 = (HEAD_KeyXYt & HEAD_KeyMask) | HEAD_KeyOrD

    keys.FKeyBytes = (B1, B2, B3, B4)
    keys.F32Keys = bytearray(b"[(C) Copyright Mr. Dong Shiwei.]")
    for i, _ in enumerate(keys.F32Keys):
        keys.F32Keys[i] &= keys.FKeyBytes[i % 4]

    return keys


# -----------------------------------------------------#
def __init_chess_board(man_str, version, keys=None):
    """根据文件中存放的棋子布局字节串构造内部的 32 长度数组。

    如果 `keys` 提供了解密因子则按版本和密钥做位置解密与字节变换，
    否则直接拷贝原始布局。
    返回一个长度为 32 的 bytearray，值为 0xFF 表示该位置无子。
    """
    tmpMan = bytearray([0 for x in range(32)])
    man_buff = bytearray(man_str)

    if keys is None:
        for i in range(32):
            tmpMan[i] = man_buff[i]
        return tmpMan

    for i in range(32):
        if version >= 12:
            tmpMan[(keys.KeyXY + i + 1) & 0x1F] = man_buff[i]
        else:
            tmpMan[i] = man_buff[i]

    for i in range(32):
        tmpMan[i] = (tmpMan[i] - keys.KeyXY) & 0xFF
        if tmpMan[i] > 89:
            tmpMan[i] = 0xFF

    return tmpMan


# -----------------------------------------------------#
def __decode_buff(keys, buff):
    """使用 `keys` 中的 F32Keys 对缓冲区做逐字节的解密变换并返回解密后的 bytes。"""
    nPos = 0x400
    de_buff = bytearray(buff)

    for i in range(len(buff)):
        KeyByte = keys.F32Keys[(nPos + i) % 32]
        de_buff[i] = (de_buff[i] - KeyByte) & 0xFF

    return bytes(de_buff)


# -----------------------------------------------------#
def __read_init_info(buff_decoder, version, keys):
    """读取并返回记录区的注释信息（若存在）。

    对应 XQF 中走子前的初始化注释，低版本和高版本通过不同方式
    存放注释长度，因此对此进行兼容解析。返回注释字符串或 None。
    """
    step_info = buff_decoder.read_bytes(4)

    annote_len = 0
    if version <= 0x0A:
        # 低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        annote_len = buff_decoder.read_int()
    else:
        # 高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
        step_info[2] &= 0xE0
        if step_info[2] & 0x20:  # 有注释
            annote_len = buff_decoder.read_int() - keys.KeyRMKSize

    return buff_decoder.read_str(annote_len) if (annote_len > 0) else None


def _append_move_to_game(game, curr_move, parent_move):
    """将走子添加到游戏树中。

    参数:
        game: Game 对象
        curr_move: 当前走子
        parent_move: 父节点走子

    返回:
        当前走子（如果成功添加），否则返回 parent_move
    """
    if parent_move:
        parent_move.append_next_move(curr_move)
    else:
        game.append_first_move(curr_move)
    return curr_move


# -----------------------------------------------------#
def __read_steps(buff_decoder, version, keys, game, parent_move, board):
    """递归读取走子数据块并将走子构造为 `Game` 中的 `Move` 链。

    解析单个走子记录，根据版本与 keys 解码起点/终点、注释和分支标志，
    对合法走子调用 `board.move` 并插入到游戏树；若检测到变招或后续走
    子，则递归读取相应子区块(深度优先遍历)。
    """
    step_info = buff_decoder.read_bytes(4)

    if len(step_info) == 0:
        return

    annote_len = 0
    has_next_step = False
    has_var_step = False
    board_bak = board.copy()

    if version <= 0x0A:
        # 低版本在走子数据后紧跟着注释长度，长度为0则没有注释
        if step_info[2] & 0xF0:
            has_next_step = True
        if step_info[2] & 0x0F:
            has_var_step = True  # 有变着
        annote_len = buff_decoder.read_int()
        # 走子起点，落点
        step_info[0] = (step_info[0] - 0x18) & 0xFF
        step_info[1] = (step_info[1] - 0x20) & 0xFF

    else:
        # 高版本通过flag来标记有没有注释，有则紧跟着注释长度和注释字段
        step_info[2] &= 0xE0
        if step_info[2] & 0x80:  # 有后续
            has_next_step = True
        if step_info[2] & 0x40:  # 有变招
            has_var_step = True
        if step_info[2] & 0x20:  # 有注释
            annote_len = buff_decoder.read_int() - keys.KeyRMKSize

        # 走子起点，落点
        step_info[0] = (step_info[0] - 0x18 - keys.KeyXYf) & 0xFF
        step_info[1] = (step_info[1] - 0x20 - keys.KeyXYt) & 0xFF

    move_from, move_to = _decode_pos2(step_info)
    annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None

    good_move = parent_move
    fench = board.get_fench(move_from)
    if fench:
        _, man_side = fench_to_species(fench)
        board.move_player = ChessPlayer(man_side)
        if board.is_valid_move(move_from, move_to):
            curr_move = board.move(move_from, move_to)
            curr_move.annote = annote
            good_move = _append_move_to_game(game, curr_move, parent_move)

    if has_next_step:
        __read_steps(buff_decoder, version, keys, game, good_move, board)

    if has_var_step:
        # print("new_line", parent_move.step_index, parent_move.to_text())
        __read_steps(buff_decoder, version, keys, game, parent_move, board_bak)
        game.info["branchs"] += 1


# -----------------------------------------------------#
def read_from_xqf(full_file_name, read_annotation=True, game=None):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
    """从 `.xqf` 文件读取并解析为 `Game` 对象。

    该函数负责读取文件头、根据版本决定是否需要解密、构造初始棋盘，
    读取游戏注释并递归解析走子数据块，最终返回填充完毕的 `Game`。

    参数:
        full_file_name (str): XQF 文件路径
        read_annotation (bool): 是否读取注释
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）

    返回:
        Game | None: 成功返回 `Game`，若文件格式不匹配返回 None
    """

    with open(full_file_name, "rb") as f:
        contents = f.read()

    (
        magic,
        version,
        crypt_keys,
        ucBoard,
        _ucUn2,
        ucRes,
        _ucUn3,
        ucType,
        _ucUn4,
        ucTitleLen,
        szTitle,
        _ucUn5,
        ucMatchNameLen,
        szMatchName,
        _ucDateLen,
        _szDate,
        _ucAddrLen,
        _szAddr,
        ucRedPlayerNameLen,
        szRedPlayerName,
        ucBlackPlayerNameLen,
        szBlackPlayerName,
        _ucTimeRuleLen,
        _szTimeRule,
        _ucRedTimeLen,
        _szRedTime,
        _ucBlackTime,
        _szBlackTime,
        _ucUn6,
        _ucCommenerNameLen,
        _szCommenerName,
        _ucAuthorNameLen,
        _szAuthorName,
        _ucUn7,
    ) = struct.unpack(
        "<2sB13s32s3sB12sB15sB63s64sB63sB15sB15sB15sB15sB63sB15sB15s32sB15sB15s528s",
        contents[:0x400],
    )

    if magic != b"XQ":
        return None

    game_info = {}

    game_info["source"] = "XQF"
    game_info["version"] = version
    game_info["type"] = ucType + 1

    if ucRes <= 4:  # It's really some file has value 4
        game_info["result"] = result_dict[ucRes]
    else:
        print("Bad Result  ", ucRes, full_file_name)
        game_info["result"] = "*"

    if ucRedPlayerNameLen > 0:
        try:
            game_info["red_player"] = szRedPlayerName[:ucRedPlayerNameLen].decode(
                "GB18030"
            )
        except (UnicodeDecodeError, ValueError):
            pass

    if ucBlackPlayerNameLen > 0:
        try:
            game_info["black_player"] = szBlackPlayerName[:ucBlackPlayerNameLen].decode(
                "GB18030"
            )
        except (UnicodeDecodeError, ValueError):
            pass

    if ucTitleLen > 0:
        try:
            game_info["title"] = szTitle[:ucTitleLen].decode("GB18030")
        except (UnicodeDecodeError, ValueError):
            pass

    if ucMatchNameLen > 0:
        try:
            game_info["event"] = szMatchName[:ucMatchNameLen].decode("GB18030")
        except (UnicodeDecodeError, ValueError):
            pass

    if version <= 0x0A:
        keys = None
        chess_mans = __init_chess_board(ucBoard, version)
        step_base_buff = XQFBuffDecoder(contents[0x400:])
    else:
        keys = __init_decrypt_key(crypt_keys)
        chess_mans = __init_chess_board(ucBoard, version, keys)
        step_base_buff = XQFBuffDecoder(__decode_buff(keys, contents[0x400:]))

    board = ChessBoard()

    chessman_kinds = (
        "R",
        "N",
        "B",
        "A",
        "K",
        "A",
        "B",
        "N",
        "R",
        "C",
        "C",
        "P",
        "P",
        "P",
        "P",
        "P",
    )

    for side in range(2):
        for man_index in range(16):
            man_pos = chess_mans[side * 16 + man_index]
            if man_pos == 0xFF:
                continue
            pos = _decode_pos(man_pos)
            fen_ch = chr(ord(chessman_kinds[man_index]) + side * 32)
            board.put_fench(fen_ch, pos)

    game_annotation = __read_init_info(step_base_buff, version, keys)

    # 如果提供了game实例，使用它；否则创建新的（向后兼容）
    if game is None:
        from .game import Game  # pylint: disable=import-outside-toplevel

        game = Game(board, game_annotation)
    else:
        # 使用提供的game实例
        game.init_board = board
        game.annote = game_annotation
        game.first_move = None
        game.last_move = None

    game.info.update(game_info)

    __read_steps(step_base_buff, version, keys, game, None, board)

    if game.first_move:
        game.init_board.move_player = game.first_move.board.move_player
    else:
        game.init_board.move_player = ChessPlayer(RED)

    game.info["move_player"] = str(game.init_board.move_player)

    return game


# -----------------------------------------------------#
def _encode_pos(pos):
    """_encode_pos 函数。"""
    return pos[0] * 10 + pos[1]


# -----------------------------------------------------#
class XQMove:
    """表示一步棋及其变招。"""

    def __init__(
        self,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        annote: str = "",
        has_variation=False,
    ):
        """__init__ 方法。"""
        self.start_pos = start_pos  # (x, y) 元组
        self.end_pos = end_pos  # (x, y) 元组
        self.annote = annote
        self.has_variation = has_variation


# -----------------------------------------------------#
class XQFWriter:
    """从 `Game` 对象写入 XQF 格式文件的写入器。"""

    def __init__(self, game):
        """__init__ 方法。"""
        self.game = game
        self.header = bytearray(b"\x00" * 1024)  # 头部固定1024字节

        # 设置文件标记和版本
        self._set_bytes(0, b"XQ")  # 文件标记
        self.header[2] = 0x0A  # 版本号 1.0

        # 设置默认初始局面
        self.set_initial_position()

        # 设置默认结果和类型
        self.set_result(0x00)  # 默认未知结果
        self.set_game_type(0x00)  # 默认全局文件

        # 设置棋局信息
        self.set_title(game.info["title"])
        self.set_event(game.info["event"])
        self.set_date(game.info["date"])
        self.set_location(game.info["location"])
        self.set_red_player(game.info["red_player"])
        self.set_black_player(game.info["black_player"])
        self.set_commentator(game.info["commentator"])
        self.set_author("cchess")

    def _set_bytes(self, offset: int, data: bytes):
        """在指定偏移量设置字节数据"""
        for i, byte in enumerate(data):
            self.header[offset + i] = byte

    def _set_string(self, offset: int, text: str, max_length: int):
        """设置字符串字段"""
        if not text:
            self.header[offset] = 0
            return

        # 转换为GBK编码（XQF使用GBK编码）
        try:
            encoded = text.encode("gbk")
        except (UnicodeEncodeError, LookupError):
            encoded = text.encode("gbk", errors="ignore")

        length = min(len(encoded), max_length - 1)
        self.header[offset] = length
        self._set_bytes(offset + 1, encoded[:length])

    def set_initial_position(self):
        """设置初始局面"""
        # 默认初始局面（红方和黑方从右到左排列）
        # default_position = [
        #    0x50, 0x46, 0x3C, 0x32, 0x28, 0x1E, 0x14, 0x0A,  # 红方车马相士帅士相马
        #    0x00, 0x48, 0x0C, 0x53, 0x3F, 0x2B, 0x17, 0x03,  # 红方车炮炮兵兵兵兵兵
        #    0x09, 0x13, 0x1D, 0x27, 0x31, 0x3B, 0x45, 0x4F,  # 黑方车马象士将士象马
        #    0x59, 0x11, 0x4D, 0x06, 0x1A, 0x2E, 0x42, 0x56   # 黑方车炮炮卒卒卒卒卒
        # ]

        position = bytearray(32)

        board = self.game.init_board
        pieces_dict = {}
        for key in ["R", "N", "B", "A", "K", "C", "P"]:
            pieces_dict[key] = board.get_fenchs(key)
            key_lower = key.lower()
            pieces_dict[key_lower] = board.get_fenchs(key_lower)

        fenchs = "RNBAKABNRCCPPPPP"
        for x in range(2):
            for i, fench in enumerate(fenchs):
                key = fench.lower() if x > 0 else fench
                pos_list = pieces_dict[key]
                pos_index = x * 16 + i
                if len(pos_list) == 0:
                    position[pos_index] = 0xFF
                else:
                    pos = pos_list.pop(0)
                    position[pos_index] = _encode_pos(pos)

        self._set_bytes(0x0010, bytes(position))

    def set_result(self, result: int):
        """设置棋局结果
        0x00-未知, 0x01-红胜, 0x02-黑胜, 0x03-和棋
        """
        self.header[0x0033] = result

    def set_game_type(self, game_type: int):
        """设置棋局类型
        0x00-全局文件, 0x01-布局文件, 0x02-中局文件, 0x03-残局文件
        """
        self.header[0x0040] = game_type

    def set_title(self, title: str):
        """设置标题"""
        self._set_string(0x0050, title, 63)

    def set_event(self, event: str):
        """设置比赛名称"""
        self._set_string(0x00D0, event, 63)

    def set_date(self, date: str):
        """设置比赛日期"""
        self._set_string(0x0110, date, 15)

    def set_location(self, location: str):
        """设置比赛地点"""
        self._set_string(0x0120, location, 15)

    def set_red_player(self, player: str):
        """设置红方棋手"""
        self._set_string(0x0130, player, 15)

    def set_black_player(self, player: str):
        """设置黑方棋手"""
        self._set_string(0x0140, player, 15)

    def set_time_rule(self, rule: str):
        """设置用时规则"""
        self._set_string(0x0150, rule, 63)

    def set_red_time(self, time_str: str):
        """设置红方用时"""
        self._set_string(0x0190, time_str, 15)

    def set_black_time(self, time_str: str):
        """设置黑方用时"""
        self._set_string(0x01A0, time_str, 15)

    def set_commentator(self, commentator: str):
        """设置棋谱讲评人"""
        self._set_string(0x01D0, commentator, 15)

    def set_author(self, author: str):
        """设置文件作者"""
        self._set_string(0x01E0, author, 15)

    def _encode_move(self, move: XQMove, is_last) -> Tuple[bytes, bytes]:
        """编码一步棋为XQF格式"""
        start_pos_value = _encode_pos(move.start_pos)
        end_pos_value = _encode_pos(move.end_pos)

        # 构建移动记录
        move_record = bytearray(8)
        move_record[0] = start_pos_value + 24  # 起始位置+24
        move_record[1] = end_pos_value + 32  # 目标位置+32

        # 如果是序列中的最后一步或者是棋局的最后一步，则标记为最后一步
        move_record[2] = 0x00

        if move.has_variation:
            move_record[2] |= 0x0F
        if not is_last:
            move_record[2] |= 0xF0

        move_record[3] = 0x00  # 保留字节
        # 处理注解
        annote_data = b""
        if move.annote:
            try:
                annote_data = move.annote.encode("gbk")
            except (UnicodeEncodeError, LookupError):
                annote_data = move.annote.encode("gbk", errors="ignore")

        # 设置注解长度（32位整数，小端序）
        annote_length = len(annote_data)
        move_record[4:8] = struct.pack("<I", annote_length)

        return bytes(move_record + annote_data)

    def save(self, file_name):
        """将游戏数据序列化并保存到指定 XQF 文件。"""
        with open(file_name, "wb") as f:
            move_lines = []
            lines = self.game.dump_moves(is_tree_mode=True)
            for line in lines:
                w_line = []
                for _index, move in enumerate(line["moves"]):
                    has_variation = move.variation_next is not None
                    w_line.append(
                        XQMove(move.p_from, move.p_to, move.annote, has_variation)
                    )
                move_lines.append(w_line)

            f.write(self.header)

            if len(move_lines) == 0:
                # 只有初始局面，没有着法记录
                f.write(b"\x18\x20\x00\xff\x00\x00\x00\x00")
                return

            # 有棋谱记录
            f.write(b"\x18\x20\xf0\xff\x00\x00\x00\x00")
            for line in move_lines:
                for i, move in enumerate(line):
                    is_last = i == len(line) - 1
                    move_record = self._encode_move(move, is_last)
                    # 写入招法记录
                    f.write(move_record)
