# -*- coding: utf-8 -*-

from enum import *

FULL_INIT_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'
    
class ChessSide(IntEnum):     
    RED = 0
    BLACK = 1
    
    @staticmethod
    def turn_side(side):
        return {ChessSide.RED:ChessSide.BLACK, ChessSide.BLACK:ChessSide.RED}[side]
     
class ChessmanT(IntEnum):
    KING = 1
    ADVISOR = 2
    BISHOP = 3
    KNIGHT = 4
    ROOK = 5 
    CANNON = 6
    PAWN = 7


