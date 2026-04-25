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

import struct

from .board import ChessBoard
from .common import BLACK, RED, fench_to_species
from .exception import CChessError

# pylint: disable=too-many-locals,too-many-branches
# -----------------------------------------------------#
CODING_PAGE_CBR = "utf-16-le"
result_dict = {0: "*", 1: "1-0", 2: "0-1", 3: "1/2-1/2", 4: "1/2-1/2"}
piece_dict = {
    # 红方
    0x11: "R",  # 车
    0x12: "N",  # 马
    0x13: "B",  # 相
    0x14: "A",  # 仕
    0x15: "K",  # 帅
    0x16: "C",  # 炮
    0x17: "P",  # 兵
    # 黑方
    0x21: "r",  # 车
    0x22: "n",  # 马
    0x23: "b",  # 相
    0x24: "a",  # 仕
    0x25: "k",  # 帅
    0x26: "c",  # 炮
    0x27: "p",  # 卒
}


# CBL 文件格式常量
_CBL_HEADER_SIZE = 576  # CBL 文件头大小
_CBL_RECORD_SIZE = 4096  # CBL 记录大小
_CBL_MAGIC = b"CCBridgeLibrary\x00"  # CBL 文件魔术字

# CBL 数据偏移量表（根据棋谱数量）
_CBL_INDEX_OFFSETS = (
    (128, 101952),  # <= 128 局
    (256, 137280),  # <= 256 局
    (384, 151080),  # <= 384 局
    (512, 207936),  # <= 512 局
)
_DEFAULT_CBL_OFFSET = 349248  # 默认偏移量


def _get_cbl_data_offset(book_count):
    """根据棋谱数量获取数据区起始偏移量

    Args:
        book_count: 棋谱数量

    Returns:
        int: 数据区起始偏移量
    """
    for max_count, offset in _CBL_INDEX_OFFSETS:
        if book_count <= max_count:
            return offset
    return _DEFAULT_CBL_OFFSET


def _parse_cbl_header(contents):
    """解析 CBL 文件头

    Args:
        contents: 文件内容字节

    Returns:
        tuple: (lib_name, book_count, valid)
    """
    magic, _i1, book_count, lib_name = struct.unpack(
        "<16s44si512s", contents[:_CBL_HEADER_SIZE]
    )

    if magic != _CBL_MAGIC:
        # 检查是否是文本文件（包含中文字符）
        try:
            text_sample = contents[:100].decode("latin1", errors="ignore")
            if any("\u4e00" <= c <= "\u9fff" for c in text_sample):
                raise CChessError(
                    f"文件看起来是文本文件而非 CBL 棋谱库文件，magic: {repr(magic[:8])}..."
                )
        except Exception:
            pass
        raise CChessError(
            f"不支持的 CBL 文件格式，期望 magic: 'CCBridgeLibrary\\x00'，实际: {repr(magic)}"
        )

    return cut_bytes_to_str(lib_name), book_count, True


def _find_and_validate_cbl_records(contents, buff_start):
    """查找并验证 CBL 记录缓冲区

    Args:
        contents: 文件内容
        buff_start: 数据区起始位置

    Returns:
        tuple: (game_buffer, game_buffer_len, game_buffer_index)
    """
    game_buffer = contents[buff_start:]
    game_buffer_len = len(game_buffer)
    game_buffer_index = game_buffer.find(b"CCBridge Record")

    if game_buffer_index < 0:
        return game_buffer, game_buffer_len, game_buffer_index

    if ((game_buffer_len - game_buffer_index) % _CBL_RECORD_SIZE) != 0:
        raise CChessError(
            f"文件格式错误：缓冲区不是{_CBL_RECORD_SIZE}的整数倍： {len(contents)}, {game_buffer_index + buff_start}"
        )

    return game_buffer, game_buffer_len, game_buffer_index


def _parse_cbl_games(contents, buff_start, game_buffer_index, game_buffer_len):
    """解析 CBL 文件中的游戏列表

    Args:
        contents: 文件内容
        buff_start: 数据区起始位置
        game_buffer_index: 游戏缓冲区索引
        game_buffer_len: 游戏缓冲区长度

    Yields:
        tuple: (game, game_index) 或 None
    """
    game_buffer = contents[buff_start:]
    game_index = 0
    count = 0

    while game_buffer_index < game_buffer_len:
        book_buffer = game_buffer[game_buffer_index:]
        try:
            game = read_from_cbr_buffer(book_buffer)
            if game is not None:
                game.info["index"] = game_index
                yield game, game_index
                game_index += 1
        except Exception as e:
            raise CChessError(
                f"{count}, {game_buffer_index} {len(contents)}, {len(book_buffer)}, {e}"
            ) from e

        count += 1
        game_buffer_index += _CBL_RECORD_SIZE


# -----------------------------------------------------#


# -----------------------------------------------------#
def _decode_pos(p):
    """_decode_pos 函数。"""
    return (p % 9, 9 - p // 9)


def cut_bytes_to_str(buff):
    """将字节缓冲区截断到首个空字节并解码为字符串。"""
    end_index = buff.find(b"\x00\x00")
    # TODO 探查一下error原因
    if end_index >= 0:
        annote = buff[:end_index].decode(CODING_PAGE_CBR, errors="ignore")
    else:
        annote = buff.decode(CODING_PAGE_CBR, errors="ignore")
    return annote


# -----------------------------------------------------#
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
class CbrBuffDecoder:
    """对 CBR 文件缓冲区提供顺序读取辅助。"""

    def __init__(self, buffer, coding):
        """__init__ 方法。"""
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)
        self.coding = coding

    def __read(self, size):
        """__read 方法。"""
        start = self.index
        stop = min(self.index + size, self.length)

        self.index = stop
        return self.buffer[start:stop]

    def is_end(self):
        """判断是否已读取缓冲区末尾。"""
        return (self.length - self.index - 1) == 0

    def read_str(self, size):
        """读取指定字节并解码为字符串（去除末尾空字节）。"""
        buff = self.__read(size)
        return cut_bytes_to_str(buff)

    def read_bytes(self, size):
        """读取指定字节并返回 bytearray。"""
        return bytearray(self.__read(size))

    def read_int8(self):
        """读取 1 字节并返回有符号整数。"""
        data = self.read_bytes(1)
        return struct.unpack("<b", data)[0]

    def read_int(self):
        """读取 4 字节并按小端序返回有符号整数。"""
        data = self.read_bytes(4)
        # return bytes[0] + (bytes[1] << 8) + (bytes[2] << 16) + (bytes[3] << 24)
        return struct.unpack("<i", data)[0]


# -----------------------------------------------------#
def __read_init_info(buff_decoder):
    """读取并返回走子前的初始化注释信息。"""
    # 注释长度, 为0则没有注释
    a_len = buff_decoder.read_int()
    if a_len == 0:
        return ""
    annote_len = buff_decoder.read_int()
    return buff_decoder.read_str(annote_len)


# -----------------------------------------------------#
def __read_steps(buff_decoder, game, parent_move, board):
    """递归读取走子数据块并将走子构造为 `Game` 中的 `Move` 链。"""
    if buff_decoder.is_end():
        return

    step_info = buff_decoder.read_bytes(4)

    if len(step_info) == 0:
        return

    if step_info == b"\x00\x00\x00\x00":
        return

    step_mark, _step_none, step_from, step_to = step_info

    # 棋谱分支结束
    if step_mark & 0x01:
        has_next_move = False
    else:
        has_next_move = True

    # 有变招
    has_var_step = bool(step_mark & 0x02)

    # 有注释
    if step_mark & 0x04:
        annote_len = buff_decoder.read_int()
    else:
        annote_len = 0

    board_bak = board.copy()
    move_from = _decode_pos(step_from)
    move_to = _decode_pos(step_to)
    annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None

    fench = board.get_fench(move_from)
    if not fench:
        return
    _, piece_color = fench_to_species(fench)
    board.set_move_side(piece_color)

    if board.is_valid_move(move_from, move_to):
        curr_move = board.move(move_from, move_to)
        curr_move.annote = annote
        good_move = _append_move_to_game(game, curr_move, parent_move)
    else:
        return

    if has_next_move:
        __read_steps(buff_decoder, game, good_move, board)

    if has_var_step:
        __read_steps(buff_decoder, game, parent_move, board_bak)


# -----------------------------------------------------#
def read_from_cbr_buffer(contents, game=None):
    """从 CBR 文件的字节内容解析并返回 `Game` 对象。

    Args:
        contents: 文件内容字节
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）
    """
    (
        magic,
        _is1,
        title,
        _is2,
        event,
        _is3,
        red,
        _is_red,
        black,
        _is_black,
        game_result,
        _is4,
        _steps,
        _is5,
        move_side,
        _is6,
        boards,
        _is7,
    ) = struct.unpack(
        "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si", contents[:2214]
    )

    if magic != b"CCBridge Record\x00":
        return None

    game_info = {}
    game_info["source"] = "CBR"
    game_info["title"] = cut_bytes_to_str(title)
    game_info["event"] = cut_bytes_to_str(event)
    game_info["red"] = cut_bytes_to_str(red)
    game_info["black"] = cut_bytes_to_str(black)
    game_info["result"] = result_dict[game_result]
    board = ChessBoard()
    if move_side == 1:
        board.set_move_side(RED)
    else:
        board.set_move_side(BLACK)

    for x in range(9):
        for y in range(10):
            v = boards[y * 9 + x]
            if v in piece_dict:
                board.put_fench(piece_dict[v], (x, 9 - y))

    buff_decoder = CbrBuffDecoder(contents[2214:], CODING_PAGE_CBR)
    game_annote = __read_init_info(buff_decoder)
    # 如果提供了game实例，使用它；否则创建新的
    if game is None:
        from .game import Game  # pylint: disable=import-outside-toplevel

        game = Game(board, game_annote)
    else:
        # 使用提供的game实例
        game.init_board = board
        game.annote = game_annote
        game.first_move = None
        game.last_move = None
    game.info = game_info

    if not buff_decoder.is_end():
        __read_steps(buff_decoder, game, None, board)

    return game


# -----------------------------------------------------#
def read_from_cbr(file_name, game=None):
    """从 `.cbr` 文件读取并解析为 `Game` 对象。

    Args:
        file_name: 文件路径
        game: 已存在的Game实例，如果为None则创建新实例（向后兼容）
    """
    with open(file_name, "rb") as f:
        contents = f.read()

    return read_from_cbr_buffer(contents, game)


# -----------------------------------------------------#
def read_from_cbl(file_name, verify=True, game=None):  # pylint: disable=unused-argument
    """从 `.cbl` 棋谱库文件读取并返回包含多个 `Game` 的字典。

    Args:
        file_name: 文件路径
        verify: 验证标志
        game: 模板Game实例，用于创建新游戏（向后兼容）
    """
    with open(file_name, "rb") as f:
        contents = f.read()

    lib_name, _book_count, _valid = _parse_cbl_header(contents)

    lib_info = {}
    lib_info["name"] = lib_name
    lib_info["games"] = []

    buff_start = _get_cbl_data_offset(_book_count)
    game_buffer, game_buffer_len, game_buffer_index = _find_and_validate_cbl_records(
        contents, buff_start
    )

    if game_buffer_index < 0:
        return lib_info

    for game, game_index in _parse_cbl_games(
        contents, buff_start, game_buffer_index, game_buffer_len
    ):
        game.info["index"] = game_index
        lib_info["games"].append(game)

    return lib_info


def read_from_cbl_progressing(file_name):
    """从 `.cbl` 棋谱库文件逐步读取并 yield 中间结果（用于进度显示）。"""
    with open(file_name, "rb") as f:
        contents = f.read()

    try:
        lib_name, book_count, _valid = _parse_cbl_header(contents)
    except CChessError:
        # 如果不是支持的 CBL 格式，直接返回（不 yield 任何结果）
        return

    lib_info = {}
    lib_info["name"] = lib_name
    lib_info["games"] = []

    buff_start = _get_cbl_data_offset(book_count)
    game_buffer, game_buffer_len, game_buffer_index = _find_and_validate_cbl_records(
        contents, buff_start
    )

    if game_buffer_index < 0:
        yield lib_info
        return

    game_index = 0
    count = 0
    while game_buffer_index < game_buffer_len:
        book_buffer = game_buffer[game_buffer_index:]
        try:
            game = read_from_cbr_buffer(book_buffer)
            if game is not None:
                game.info["index"] = game_index
                lib_info["games"].append(game)
                game_index += 1
        except Exception as e:
            raise CChessError(
                f"{game_buffer_index}/{count}, {len(contents)}, {len(book_buffer)}, {e}"
            ) from e
        count += 1
        game_buffer_index += _CBL_RECORD_SIZE

        yield lib_info
