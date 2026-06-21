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

from .board import ChessBoard, fen_flip, fen_mirror, fen_swap
from .book import (
    BLACK_WIN,
    BOOK_ALL,
    BOOK_BEGIN,
    BOOK_END,
    BOOK_MIDDLE,
    BOOK_UNKNOWN,
    PEACE,
    RED_WIN,
    UNKNOWN,
    Book,
    book_result_str,
    book_type_str,
)
from .common import (
    EMPTY_BOARD,
    EMPTY_FEN,
    FULL_INIT_BOARD,
    FULL_INIT_FEN,
    SIDE_ANY,
    SIDE_BLACK,
    SIDE_RED,
    fen_move_color,
    fench_to_species,
    fench_to_text,
    get_fen_type,
    get_fen_type_detail,
    get_fench_color,
    iccs2pos,
    iccs_flip,
    iccs_list_mirror,
    iccs_mirror,
    iccs_swap,
    pos2iccs,
)
from .engine import (
    EngineManager,
    EngineStatus,
    FenCache,
    UcciEngine,
    UciEngine,
)
from .engine_async import AsyncEngine, analyse_position, play_move
from .exception import CChessError, EngineError
from .move import Move

__all__ = [
    # exception
    "CChessError",
    "EngineError",
    # common
    "SIDE_ANY",
    "SIDE_RED",
    "SIDE_BLACK",
    "fench_to_species",
    "get_fench_color",
    "fench_to_text",
    "iccs2pos",
    "pos2iccs",
    "iccs_mirror",
    "iccs_list_mirror",
    "iccs_flip",
    "iccs_swap",
    "fen_mirror",
    "fen_flip",
    "fen_swap",
    "fen_move_color",
    "get_fen_type",
    "get_fen_type_detail",
    "FULL_INIT_BOARD",
    "FULL_INIT_FEN",
    "EMPTY_BOARD",
    "EMPTY_FEN",
    # board
    "ChessBoard",
    # move
    "Move",
    # book
    "Book",
    # book constants
    "UNKNOWN",
    "RED_WIN",
    "BLACK_WIN",
    "PEACE",
    "BOOK_UNKNOWN",
    "BOOK_ALL",
    "BOOK_BEGIN",
    "BOOK_MIDDLE",
    "BOOK_END",
    "book_result_str",
    "book_type_str",
    # engine
    "EngineStatus",
    "UcciEngine",
    "UciEngine",
    "EngineManager",
    "FenCache",
    "AsyncEngine",
    "play_move",
    "analyse_position",
    # version
    "__version__",
]

__version__ = "2.26.1"
