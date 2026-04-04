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

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

import cchess.__main__ as rt_main


class TestReaderXQF:
    def setup_method(self):
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    def teardown_method(self):
        pass

    def test_main_entry(self):
        testargs = ["prog", "-r", ".\\data\\test.cbf"]
        with patch.object(sys, "argv", testargs):
            rt_main.main()

    def test_pgn_to_xqf(self):
        out_file = Path("data", "test_convert_out.xqf")
        if out_file.exists():
            os.remove(out_file)
        testargs = ["prog", "-i", "data\\test.pgn", "-o", str(out_file)]
        with patch.object(sys, "argv", testargs):
            rt_main.main()
        assert out_file.exists()
        game = rt_main.Game.read_from(str(out_file))
        moves = game.dump_text_moves()
        assert len(moves[0]) == 25
        os.remove(out_file)

    def test_xqf_to_pgn(self):
        out_file = Path("data", "test_convert_out.pgn")
        if out_file.exists():
            os.remove(out_file)
        testargs = ["prog", "-i", "data\\test.xqf", "-o", str(out_file)]
        with patch.object(sys, "argv", testargs):
            rt_main.main()
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        assert "兵七进一" in content or "兵" in content
        os.remove(out_file)

    def test_cbf_to_xqf(self):
        out_file = Path("data", "test_cbf_convert_out.xqf")
        if out_file.exists():
            os.remove(out_file)
        testargs = ["prog", "-i", "data\\test.cbf", "-o", str(out_file)]
        with patch.object(sys, "argv", testargs):
            rt_main.main()
        assert out_file.exists()
        game = rt_main.Game.read_from(str(out_file))
        moves = game.dump_text_moves()
        assert len(moves) >= 1
        os.remove(out_file)

    def test_same_format_error(self):
        testargs = ["prog", "-i", "data\\test.pgn", "-o", "data\\test_out.pgn"]
        with patch.object(sys, "argv", testargs):
            with pytest.raises(SystemExit) as ctx:
                rt_main.main()
            assert ctx.value.code == -1

    def test_unsupported_input_format(self):
        out_file = Path("data", "test_out.xqf")
        testargs = ["prog", "-i", "data\\test.cbl", "-o", str(out_file)]
        with patch.object(sys, "argv", testargs):
            with pytest.raises(SystemExit) as ctx:
                rt_main.main()
            assert ctx.value.code == -1
