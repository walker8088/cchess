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

from .attack_matrix_manager import AttackMatrixManager
from .board import ChessBoard, ChessPlayer
from .board_state import BoardState, MoveInfo
from .board_transform import BoardTransform
from .common import (
    ANY_COLOR,
    BLACK,
    EMPTY_BOARD,
    EMPTY_FEN,
    FULL_INIT_BOARD,
    FULL_INIT_FEN,
    RED,
    fen_flip,
    fen_mirror,
    fen_swap,
    fench_to_species,
    fench_to_text,
    get_fen_type,
    get_fen_type_detail,
    get_move_color,
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
from .game import Game
from .io_pgn import read_from_pgn
from .io_xqf import read_from_xqf
from .move import Move
from .move_generator import MoveGenerator
from .piece import (
    Advisor,
    Bishop,
    Cannon,
    King,
    Knight,
    Pawn,
    Piece,
    Rook,
)
from .read_cbf import read_from_cbf
from .read_cbr import read_from_cbl, read_from_cbr
from .rule_checker import RuleChecker

__all__ = [
    # exception
    "CChessError",
    "EngineError",
    # common
    "ANY_COLOR",
    "RED",
    "BLACK",
    "fench_to_species",
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
    "get_move_color",
    "get_fen_type",
    "get_fen_type_detail",
    "FULL_INIT_BOARD",
    "FULL_INIT_FEN",
    "EMPTY_BOARD",
    "EMPTY_FEN",
    # piece
    "Piece",
    "King",
    "Advisor",
    "Bishop",
    "Knight",
    "Rook",
    "Cannon",
    "Pawn",
    # board state and components
    "ChessBoard",
    "ChessPlayer",
    "BoardState",
    "MoveInfo",
    "BoardTransform",
    "MoveGenerator",
    "RuleChecker",
    "AttackMatrixManager",
    # move
    "Move",
    # game
    "Game",
    # engine
    "EngineStatus",
    "UcciEngine",
    "UciEngine",
    "EngineManager",
    "FenCache",
    "AsyncEngine",
    "play_move",
    "analyse_position",
    # io
    "read_from_xqf",
    "read_from_pgn",
    "read_from_cbf",
    "read_from_cbr",
    "read_from_cbl",
    # version
    "__version__",
]

__version__ = "1.26.1"
