# -*- coding: utf-8 -*-
"""测试异步引擎功能"""

import pytest
from cchess import ChessBoard, AsyncEngine
from cchess.engine_async import play_move, analyse_position


class TestAsyncEngine:
    """测试 AsyncEngine 类"""

    def test_async_engine_init(self):
        """测试异步引擎初始化"""
        engine = AsyncEngine("test_engine.exe")
        assert engine.engine_exec_path == "test_engine.exe"
        assert engine.process is None
        assert engine._initialized is False

    def test_async_engine_methods_exist(self):
        """测试异步引擎方法存在"""
        engine = AsyncEngine("test_engine.exe")
        assert hasattr(engine, 'initialize')
        assert hasattr(engine, 'configure')
        assert hasattr(engine, 'play')
        assert hasattr(engine, 'analyse')
        assert hasattr(engine, 'quit')

    def test_async_engine_context_manager(self):
        """测试异步上下文管理器"""
        engine = AsyncEngine("test_engine.exe")
        assert hasattr(engine, '__aenter__')
        assert hasattr(engine, '__aexit__')


class TestAsyncEngineHelpers:
    """测试异步引擎辅助函数"""

    def test_play_move_function_exists(self):
        """测试 play_move 函数存在"""
        assert callable(play_move)

    def test_analyse_position_function_exists(self):
        """测试 analyse_position 函数存在"""
        assert callable(analyse_position)


class TestAsyncEngineIntegration:
    """测试异步引擎集成"""

    def test_async_engine_with_board(self):
        """测试异步引擎与棋盘交互"""
        board = ChessBoard()
        
        # 创建引擎实例（不实际启动）
        engine = AsyncEngine("test_engine.exe")
        
        # 测试 play 方法签名
        assert hasattr(engine, 'play')
        
        # 测试 analyse 方法签名
        assert hasattr(engine, 'analyse')
