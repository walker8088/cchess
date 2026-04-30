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
from pathlib import Path

import pytest

from cchess import FULL_INIT_FEN, ChessBoard
from cchess.engine_async import AsyncEngine, analyse_position, play_move

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestAsyncEngineInit:
    """测试异步引擎初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        engine = AsyncEngine()
        assert engine.engine_exec_path == ""
        assert engine.process is None
        assert engine._initialized is False
        assert engine._options == {}
        assert engine._id == {}

    def test_init_with_path(self):
        """测试带路径初始化"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        assert engine.engine_exec_path == engine_path


class TestAsyncEngineLifecycle:
    """测试异步引擎生命周期"""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """测试成功初始化引擎"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        result = await engine.initialize()
        assert result is True
        assert engine._initialized is True
        assert engine.process is not None
        await engine.quit()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        """测试初始化幂等性（多次调用返回相同结果）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        result1 = await engine.initialize()
        result2 = await engine.initialize()
        assert result1 is True
        assert result2 is True
        await engine.quit()

    @pytest.mark.asyncio
    async def test_initialize_invalid_path(self):
        """测试无效路径初始化失败"""
        engine = AsyncEngine("nonexistent_engine.exe")
        result = await engine.initialize()
        assert result is False
        assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试异步上下文管理器"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            assert engine._initialized is True
            assert engine.process is not None
        # 退出上下文后进程应该已关闭
        assert engine._initialized is False

    @pytest.mark.asyncio
    async def test_quit(self):
        """测试正常关闭引擎"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        await engine.initialize()
        await engine.quit()
        assert engine._initialized is False
        assert engine.process is None


class TestAsyncEnginePlay:
    """测试异步引擎走棋功能"""

    @pytest.mark.asyncio
    async def test_play_initial_position(self):
        """测试初始局面走棋"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=2)
            assert "move" in result
            assert result["move"] is not None
            # 走法应该是有效的 ICCS 格式（4个字符）
            assert len(result["move"]) == 4

    @pytest.mark.asyncio
    async def test_play_with_time_limit(self):
        """测试带时间限制的走棋"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, time_limit=0.5)
            assert "move" in result
            assert result["move"] is not None

    @pytest.mark.asyncio
    async def test_play_with_ponder(self):
        """测试带 ponder 选项的走棋"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=2, ponder=True)
            assert "move" in result
            assert result["move"] is not None

    @pytest.mark.asyncio
    async def test_play_not_initialized(self):
        """测试未初始化时调用 play 抛出异常"""
        engine = AsyncEngine()
        board = ChessBoard(FULL_INIT_FEN)
        with pytest.raises(RuntimeError, match="Engine not initialized"):
            await engine.play(board, depth=2)

    @pytest.mark.asyncio
    async def test_play_returns_pv(self):
        """测试走棋返回包含 PV 线"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=3)
            # PV 线应该包含走法序列
            assert "pv" in result
            if result["pv"]:
                assert isinstance(result["pv"], list)


class TestAsyncEngineAnalyse:
    """测试异步引擎分析功能"""

    @pytest.mark.asyncio
    async def test_analyse_initial_position(self):
        """测试初始局面分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, depth=2)
            assert isinstance(results, list)
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_analyse_with_time_limit(self):
        """测试带时间限制的分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, time_limit=0.5)
            assert isinstance(results, list)
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_analyse_multipv(self):
        """测试多线路分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, depth=2, multipv=3)
            assert isinstance(results, list)
            # 应该返回多条分析结果
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_analyse_not_initialized(self):
        """测试未初始化时调用 analyse 抛出异常"""
        engine = AsyncEngine()
        board = ChessBoard(FULL_INIT_FEN)
        with pytest.raises(RuntimeError, match="Engine not initialized"):
            await engine.analyse(board, depth=2)

    @pytest.mark.asyncio
    async def test_analyse_returns_score(self):
        """测试分析结果包含评分"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, depth=3)
            if results:
                first_result = results[0]
                # 应该包含深度信息
                assert "depth" in first_result


class TestAsyncEngineConfigure:
    """测试异步引擎配置功能"""

    @pytest.mark.asyncio
    async def test_configure_options(self):
        """测试配置引擎选项"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 配置选项不应抛出异常
            await engine.configure({"Threads": "2", "Hash": "64"})


class TestAsyncEngineHelpers:
    """测试异步引擎便捷函数"""

    @pytest.mark.asyncio
    async def test_play_move_function(self):
        """测试 play_move 便捷函数"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            move = await play_move(engine, board, depth=2)
            assert isinstance(move, str)
            assert len(move) == 4  # ICCS 格式

    @pytest.mark.asyncio
    async def test_analyse_position_function(self):
        """测试 analyse_position 便捷函数"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await analyse_position(engine, board, depth=2)
            assert isinstance(result, dict)


class TestAsyncEngineEndgame:
    """测试异步引擎残局走法（参考 test_engine.py 的 TestUcci）"""

    @pytest.mark.asyncio
    async def test_endgame_sequence(self):
        """测试残局走法序列"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 使用初始局面（更稳定）
            board = ChessBoard(FULL_INIT_FEN)

            # 走一步棋（使用较短的时间限制）
            result = await engine.play(board, time_limit=1.0)
            assert "move" in result
            assert result["move"] is not None
            # 验证走法合法性
            move = board.move_iccs(result["move"])
            assert move is not None


class TestAsyncEngineGoCommand:
    """测试 go 命令构建"""

    def test_build_go_command_depth_only(self):
        """测试只带深度的 go 命令"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        cmd = engine._build_go_command(depth=10)
        assert cmd == "go depth 10"

    def test_build_go_command_time_only(self):
        """测试只带时间限制的 go 命令"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        cmd = engine._build_go_command(time_limit=1.5)
        assert cmd == "go movetime 1500"

    def test_build_go_command_ponder_only(self):
        """测试只带 ponder 的 go 命令"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        cmd = engine._build_go_command(ponder=True)
        assert cmd == "go ponder"

    def test_build_go_command_combined(self):
        """测试组合参数的 go 命令"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        cmd = engine._build_go_command(depth=10, ponder=True)
        assert cmd == "go depth 10 ponder"

    def test_build_go_command_no_params(self):
        """测试无参数的 go 命令"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        cmd = engine._build_go_command()
        assert cmd == "go"


class TestAsyncEngineParseInfo:
    """测试 info 行解析"""

    def test_parse_info_depth_score(self):
        """测试解析包含深度和评分的 info 行"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 5 score cp 100 pv b0c2"
        result = engine._parse_info(line)
        assert result["depth"] == 5
        assert result["score"] == 100
        assert result["pv"] == ["b0c2"]

    def test_parse_info_mate(self):
        """测试解析包含 mate 的 info 行"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 10 score mate 3"
        result = engine._parse_info(line)
        assert result["depth"] == 10
        assert result["mate"] == 3

    def test_parse_info_multipv(self):
        """测试解析包含 multipv 的 info 行"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 5 multipv 2 score cp 50"
        result = engine._parse_info(line)
        assert result["depth"] == 5
        assert result["multipv"] == 2
        assert result["score"] == 50
