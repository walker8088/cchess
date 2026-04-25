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
ANY_COLOR, RED, BLACK = (0, 1, 2)

# 棋盘常量
EMPTY_BOARD = "9/9/9/9/9/9/9/9/9/9"
FULL_INIT_BOARD = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"

EMPTY_FEN = f"{EMPTY_BOARD} w"
FULL_INIT_FEN = f"{FULL_INIT_BOARD} w"

# 棋盘尺寸
BOARD_WIDTH = 9  # 棋盘宽度（列数）
BOARD_HEIGHT = 10  # 棋盘高度（行数）

# 九宫格范围
PALACE_MIN_X = 3  # 九宫格最小列
PALACE_MAX_X = 5  # 九宫格最大列
RED_PALACE_MAX_Y = 2  # 红方九宫格最大行
BLACK_PALACE_MIN_Y = 7  # 黑方九宫格最小行

# 河岸线
RED_RIVER_LINE = 4  # 红方河岸（红方一侧）
BLACK_RIVER_LINE = 5  # 黑方河岸（黑方一侧）

# 边界范围
MIN_X = 0  # 最小列索引
MAX_X = 8  # 最大列索引
MIN_Y = 0  # 最小行索引
MAX_Y = 9  # 最大行索引
