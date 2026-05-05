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

# 颜色常量
SIDE_ANY, SIDE_RED, SIDE_BLACK = (0, 1, 2)

# 向后兼容别名
ANY_COLOR = SIDE_ANY
RED = SIDE_RED
BLACK = SIDE_BLACK

# 棋盘常量
EMPTY_BOARD = "9/9/9/9/9/9/9/9/9/9"
FULL_INIT_BOARD = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"

EMPTY_FEN = f"{EMPTY_BOARD} w"
FULL_INIT_FEN = f"{FULL_INIT_BOARD} w"

FEN_NUM_SET = frozenset(("1", "2", "3", "4", "5", "6", "7", "8", "9"))
FEN_CHAR_SET = frozenset(("k", "a", "b", "n", "r", "c", "p"))

# 比赛结果映射
GAME_RESULT_MAP = {0: "*", 1: "1-0", 2: "0-1", 3: "1/2-1/2", 4: "1/2-1/2"}
