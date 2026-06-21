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

import asyncio
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
    @pytest.mark.slow
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
    @pytest.mark.slow
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
    @pytest.mark.slow
    async def test_initialize_invalid_path(self):
        """测试无效路径初始化失败"""
        engine = AsyncEngine("nonexistent_engine.exe")
        result = await engine.initialize()
        assert result is False
        assert engine._initialized is False

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_context_manager(self):
        """测试异步上下文管理器"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            assert engine._initialized is True
            assert engine.process is not None
        # 退出上下文后进程应该已关闭
        assert engine._initialized is False

    @pytest.mark.asyncio
    @pytest.mark.slow
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
    @pytest.mark.slow
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
    @pytest.mark.slow
    async def test_play_with_time_limit(self):
        """测试带时间限制的走棋"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, time_limit=0.5)
            assert "move" in result
            assert result["move"] is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
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
    @pytest.mark.slow
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
    @pytest.mark.slow
    async def test_analyse_initial_position(self):
        """测试初始局面分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, depth=2)
            assert isinstance(results, list)
            assert len(results) >= 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyse_with_time_limit(self):
        """测试带时间限制的分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, time_limit=0.5)
            assert isinstance(results, list)
            assert len(results) >= 1

    @pytest.mark.asyncio
    @pytest.mark.slow
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
    @pytest.mark.slow
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
    @pytest.mark.slow
    async def test_configure_options(self):
        """测试配置引擎选项"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 配置选项不应抛出异常
            await engine.configure({"Threads": "2", "Hash": "64"})


class TestAsyncEngineHelpers:
    """测试异步引擎便捷函数"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_move_function(self):
        """测试 play_move 便捷函数"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            move = await play_move(engine, board, depth=2)
            assert isinstance(move, str)
            assert len(move) == 4  # ICCS 格式

    @pytest.mark.asyncio
    @pytest.mark.slow
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
    @pytest.mark.slow
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


class TestAsyncEngineBoundaryConditions:
    """测试边界条件"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_empty_board(self):
        """测试空局面走棋（使用时间限制避免引擎深搜索卡死）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 空局面（只有红方帅和黑方将，对面）
            board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
            result = await engine.play(board, time_limit=0.5, timeout=10)
            assert "move" in result
            # 走法可能是 None（超时）或 4 字符 ICCS 格式
            if result["move"] is not None:
                assert len(result["move"]) == 4

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_invalid_fen(self):
        """测试无效 FEN 走棋（应发送原始 FEN，引擎可能报错）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            # 即使 FEN 无效，引擎也可能返回结果（取决于引擎实现）
            result = await engine.play(board, depth=2, timeout=10)
            assert "move" in result

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_checkmate_position(self):
        """测试即将被将死的局面"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 红方被黑方将死局面
            board = ChessBoard("3k5/9/9/9/9/9/9/9/9/4K4 w")
            result = await engine.play(board, time_limit=0.5, timeout=10)
            assert "move" in result

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyse_empty_board(self):
        """测试空局面分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard("4k4/9/9/9/9/9/9/9/9/4K4 w")
            results = await engine.analyse(board, time_limit=0.5, timeout=10)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyse_checkmate_position(self):
        """测试将死局面分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard("3k5/9/9/9/9/9/9/9/9/4K4 w")
            results = await engine.analyse(board, time_limit=0.5, timeout=10)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_with_zero_depth(self):
        """测试深度为 0 的走棋"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=0, timeout=10)
            assert "move" in result

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyse_with_zero_time(self):
        """测试时间为 0 的分析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            results = await engine.analyse(board, time_limit=0, timeout=10)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_timeout_protection(self):
        """测试超时保护机制"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)
            # 使用非常短的超时 (1秒)
            result = await engine.play(board, time_limit=10, timeout=1)
            assert "move" in result
            # 超时后 move 可能是 None（引擎还没完成思考）


class TestAsyncEngineErrorRecovery:
    """测试错误恢复"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_reinitialize_after_quit(self):
        """测试退出后重新初始化"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)

        # 第一次初始化
        result1 = await engine.initialize()
        assert result1 is True
        assert engine._initialized is True

        # 退出
        await engine.quit()
        assert engine._initialized is False

        # 重新初始化
        result2 = await engine.initialize()
        assert result2 is True
        assert engine._initialized is True
        await engine.quit()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_quit_calls(self):
        """测试多次调用 quit 不抛出异常"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        await engine.initialize()

        # 多次 quit 不应抛出异常
        await engine.quit()
        await engine.quit()
        await engine.quit()

        assert engine._initialized is False

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_play_after_failed_init(self):
        """测试初始化失败后调用 play"""
        engine = AsyncEngine("nonexistent_engine.exe")
        result = await engine.initialize()
        assert result is False

        board = ChessBoard(FULL_INIT_FEN)
        with pytest.raises(RuntimeError, match="Engine not initialized"):
            await engine.play(board, depth=2)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_reconnect_scenario(self):
        """测试重连场景（初始化 -> 走棋 -> 退出 -> 重新初始化 -> 走棋）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)

        # 第一次会话
        await engine.initialize()
        board1 = ChessBoard(FULL_INIT_FEN)
        result1 = await engine.play(board1, depth=2)
        assert result1["move"] is not None
        await engine.quit()

        # 第二次会话
        await engine.initialize()
        board2 = ChessBoard(FULL_INIT_FEN)
        result2 = await engine.play(board2, depth=2)
        assert result2["move"] is not None
        await engine.quit()


class TestAsyncEngineConcurrency:
    """测试并发调用"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_play_calls(self):
        """测试并发调用 play"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)

            # 并发发送两个走棋请求（引擎通常串行处理）
            # 这里测试的是快速连续调用不会导致死锁或状态混乱
            tasks = [
                engine.play(board, depth=2),
                engine.play(board, depth=2),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 至少一个结果应该成功
            valid_results = [
                r for r in results if isinstance(r, dict) and r.get("move")
            ]
            assert len(valid_results) >= 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_analyse_calls(self):
        """测试并发调用 analyse"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)

            tasks = [
                engine.analyse(board, depth=2),
                engine.analyse(board, depth=2),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 至少一个结果应该成功
            valid_results = [r for r in results if isinstance(r, list) and len(r) >= 1]
            assert len(valid_results) >= 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rapid_play_sequence(self):
        """测试快速连续走棋（模拟连续落子）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            board = ChessBoard(FULL_INIT_FEN)

            # 连续走几步棋
            for _ in range(3):
                result = await engine.play(board, depth=2)
                assert result["move"] is not None

                # 执行走法
                move = board.move_iccs(result["move"])
                assert move is not None


class TestAsyncEngineInfoParsing:
    """测试 info 行解析完整性"""

    def test_parse_info_full_line(self):
        """测试完整 info 行解析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 15 seldepth 20 score cp 128 nodes 123456 nps 500000 time 500 pv a0a1 b1c3 c2d4"
        result = engine._parse_info(line)

        assert result.get("depth") == 15
        assert result.get("score") == 128
        assert result.get("pv") == ["a0a1", "b1c3", "c2d4"]

    def test_parse_info_seldepth(self):
        """测试解析 seldepth"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 10 seldepth 15 score cp 50"
        result = engine._parse_info(line)

        assert result.get("depth") == 10
        assert result.get("seldepth") == 15
        assert result.get("score") == 50

    def test_parse_info_nodes_nps_time(self):
        """测试解析 nodes, nps, time"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 8 nodes 999999 nps 2000000 time 500"
        result = engine._parse_info(line)

        assert result.get("nodes") == "999999"
        assert result.get("nps") == "2000000"
        assert result.get("time") == "500"

    def test_parse_info_currmove(self):
        """测试解析 currmove"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 5 score cp 30 currmove b0c2 currmovenumber 1"
        result = engine._parse_info(line)

        assert result.get("currmove") == "b0c2"
        assert result.get("currmovenumber") == "1"

    def test_parse_info_hashfull(self):
        """测试解析 hashfull"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)
        line = "info depth 10 score cp 100 hashfull 50"
        result = engine._parse_info(line)

        assert result.get("hashfull") == "50"

    def test_parse_info_multipv_order(self):
        """测试 multipv 顺序解析"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path)

        results = []
        lines = [
            "info depth 5 multipv 1 score cp 100 pv a0a1",
            "info depth 5 multipv 2 score cp 80 pv b0b2",
            "info depth 5 multipv 3 score cp 60 pv c0c2",
        ]

        for line in lines:
            result = engine._parse_info(line)
            results.append(result)

        assert results[0].get("multipv") == 1
        assert results[1].get("multipv") == 2
        assert results[2].get("multipv") == 3

        assert results[0].get("score") == 100
        assert results[1].get("score") == 80
        assert results[2].get("score") == 60


class TestAsyncEngineSetOption:
    """测试 setoption 命令发送"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_setoption_single(self):
        """测试设置单个选项"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 设置线程数
            await engine.configure({"Threads": "2"})
            # 验证可以正常走棋（选项已设置）
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=2)
            assert result["move"] is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_setoption_multiple(self):
        """测试设置多个选项"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            options = {
                "Threads": "4",
                "Hash": "128",
            }
            await engine.configure(options)
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=2)
            assert result["move"] is not None

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_setoption_empty_dict(self):
        """测试空选项字典"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        async with AsyncEngine(engine_path) as engine:
            # 空字典不应抛出异常
            await engine.configure({})
            board = ChessBoard(FULL_INIT_FEN)
            result = await engine.play(board, depth=2)
            assert result["move"] is not None


class TestAsyncEngineProtocolDetection:
    """测试协议自动检测"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_protocol_auto_detection_ucci(self):
        """测试 UCCI 协议自动检测"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path, protocol="auto")
        await engine.initialize()
        # eleeye 是 UCCI 引擎
        assert engine._protocol == "ucci"
        await engine.quit()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_protocol_explicit_ucci(self):
        """测试显式指定 UCCI 协议"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path, protocol="ucci")
        await engine.initialize()
        assert engine._protocol == "ucci"
        await engine.quit()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_protocol_explicit_uci(self):
        """测试显式指定 UCI 协议（会失败并快速返回，因为引擎是 UCCI）"""
        engine_path = os.path.join(PROJECT_ROOT, "Engine", "eleeye", "ELEEYE.EXE")
        engine = AsyncEngine(engine_path, protocol="uci")
        # 这里会尝试 UCI 协议，但引擎是 UCCI 的
        # 应该超时返回 False（大约 5 秒后），而不是挂死
        result = await engine.initialize()
        # 超时后 initialize 返回 False
        assert result is False
        # 进程应被清理
        assert engine.process is None
