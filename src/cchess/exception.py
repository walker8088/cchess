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


class CChessError(Exception):
    """中国象棋库通用异常。"""

    def __init__(self, reason):
        """__init__ 方法。"""
        super().__init__(reason)
        self.reason = reason


class EngineErrorException(Exception):
    """引擎通信或执行过程中发生的异常。"""

    def __init__(self, reason):
        """__init__ 方法。"""
        super().__init__(reason)
        self.reason = reason
