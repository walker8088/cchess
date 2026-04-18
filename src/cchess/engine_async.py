"""异步引擎接口 - 基于 asyncio 的异步调用支持
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional

from .board import ChessBoard

logger = logging.getLogger(__name__)


class AsyncEngine:
    """异步引擎封装，基于 asyncio 实现非阻塞调用。

    使用示例:
        async with AsyncEngine("path/to/engine") as engine:
            result = await engine.play(board, depth=10)
            print(result)
    """

    def __init__(self, exec_path: str = ""):
        self.engine_exec_path = exec_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self._initialized = False
        self._options: Dict[str, Any] = {}
        self._id: Dict[str, str] = {}

    async def __aenter__(self) -> AsyncEngine:
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.quit()

    async def initialize(self) -> bool:
        """启动引擎进程并初始化。

        返回:
            bool: 成功返回 True
        """
        if self._initialized:
            return True

        try:
            startupinfo = None
            if subprocess.mswindows:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = await asyncio.create_subprocess_exec(
                self.engine_exec_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=startupinfo,
            )

            # 发送初始化命令
            await self._send_line("uci")

            # 等待 uciok
            while True:
                line = await self._read_line()
                if line == "uciok":
                    break
                elif line.startswith("option"):
                    await self._parse_option(line)
                elif line.startswith("id"):
                    await self._parse_id(line)

            self._initialized = True
            logger.info("Engine initialized: %s", self._id.get("name", "Unknown"))
            return True

        except Exception as e:
            logger.error("Failed to initialize engine: %s", e)
            return False

    async def _send_line(self, line: str) -> None:
        """发送一行命令到引擎"""
        if self.process and self.process.stdin:
            self.process.stdin.write((line + "\n").encode())
            await self.process.stdin.drain()
            logger.debug(">> %s", line)

    async def _read_line(self) -> str:
        """从引擎读取一行"""
        if self.process and self.process.stdout:
            line_bytes = await self.process.stdout.readline()
            line = line_bytes.decode().strip()
            logger.debug("<< %s", line)
            return line
        return ""

    async def _parse_option(self, line: str) -> None:
        """解析 option 行"""
        parts = line.split()
        if len(parts) < 4:
            return

        name_idx = parts.index("name") + 1 if "name" in parts else -1
        if name_idx > 0 and name_idx < len(parts):
            name = parts[name_idx]
            self._options[name] = {
                "type": parts[parts.index("type") + 1] if "type" in parts else None,
                "default": parts[parts.index("default") + 1]
                if "default" in parts
                else None,
            }

    async def _parse_id(self, line: str) -> None:
        """解析 id 行"""
        parts = line.split(maxsplit=2)
        if len(parts) >= 3:
            key = parts[1]
            value = parts[2]
            self._id[key] = value

    async def configure(self, options: Dict[str, Any]) -> None:
        """配置引擎选项。

        参数:
            options: 选项字典
        """
        for name, value in options.items():
            await self._send_line(f"setoption name {name} value {value}")

    async def play(
        self,
        board: ChessBoard,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None,
        ponder: bool = False,
    ) -> Dict[str, Any]:
        """执行一步棋。

        参数:
            board: 当前局面
            depth: 搜索深度
            time_limit: 时间限制（秒）
            ponder: 是否 ponder

        返回:
            dict: 包含 'move', 'score', 'pv' 等信息
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        # 发送局面
        await self._send_line(f"position fen {board.to_fen()}")

        # 构建 go 命令
        go_cmd = "go"
        if depth is not None:
            go_cmd += f" depth {depth}"
        if time_limit is not None:
            go_cmd += f" movetime {int(time_limit * 1000)}"
        if ponder:
            go_cmd += " ponder"

        await self._send_line(go_cmd)

        # 等待结果
        result = {"move": None, "score": None, "pv": []}
        while True:
            line = await self._read_line()
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    result["move"] = parts[1]
                if len(parts) >= 4 and parts[2] == "ponder":
                    result["ponder"] = parts[3]
                break
            elif line.startswith("info") and "score" in line:
                info = self._parse_info(line)
                if "score" in info:
                    result["score"] = info["score"]
                if "pv" in info:
                    result["pv"] = info["pv"]

        return result

    async def analyse(
        self,
        board: ChessBoard,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None,
        multipv: int = 1,
    ) -> List[Dict[str, Any]]:
        """分析局面。

        参数:
            board: 当前局面
            depth: 搜索深度
            time_limit: 分析时间（秒）
            multipv: 分析多条线路的数量

        返回:
            list: 分析结果列表
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        # 设置 multipv
        if multipv > 1:
            await self.configure({"MultiPV": str(multipv)})

        # 发送局面
        await self._send_line(f"position fen {board.to_fen()}")

        # 发送分析命令
        go_cmd = "go"
        if depth is not None:
            go_cmd += f" depth {depth}"
        if time_limit is not None:
            go_cmd += f" movetime {int(time_limit * 1000)}"

        await self._send_line(go_cmd)

        # 收集分析结果
        results: List[Dict[str, Any]] = []
        current_info: Dict[int, Dict[str, Any]] = {}

        while True:
            line = await self._read_line()
            if line.startswith("bestmove"):
                break
            elif line.startswith("info"):
                info = self._parse_info(line)
                multipv_num = info.get("multipv", 1)
                current_info[multipv_num] = info

        # 整理结果
        for i in range(1, multipv + 1):
            if i in current_info:
                results.append(current_info[i])

        return results

    def _parse_info(self, line: str) -> Dict[str, Any]:
        """解析 info 行"""
        result = {}
        parts = line.split()

        i = 1  # 跳过 "info"
        while i < len(parts):
            if parts[i] == "depth":
                result["depth"] = int(parts[i + 1])
                i += 2
            elif parts[i] == "score":
                if i + 1 < len(parts) and parts[i + 1] == "cp":
                    result["score"] = int(parts[i + 2]) if i + 2 < len(parts) else None
                    i += 3
                elif i + 1 < len(parts) and parts[i + 1] == "mate":
                    result["mate"] = int(parts[i + 2]) if i + 2 < len(parts) else None
                    i += 3
                else:
                    i += 1
            elif parts[i] == "pv":
                result["pv"] = parts[i + 1 :]
                break
            elif parts[i] == "multipv":
                result["multipv"] = int(parts[i + 1])
                i += 2
            else:
                i += 1

        return result

    async def quit(self) -> None:
        """关闭引擎进程"""
        if self.process:
            await self._send_line("quit")
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

            self.process = None
            self._initialized = False
            logger.info("Engine terminated")


# 便捷函数
async def play_move(
    engine: AsyncEngine,
    board: ChessBoard,
    depth: int = 10,
    time_limit: Optional[float] = None,
) -> str:
    """使用引擎走一步棋。

    参数:
        engine: 引擎实例
        board: 当前局面
        depth: 搜索深度
        time_limit: 时间限制

    返回:
        str: 最佳走法 (ICCS 格式)
    """
    result = await engine.play(board, depth=depth, time_limit=time_limit)
    return result.get("move", "")


async def analyse_position(
    engine: AsyncEngine, board: ChessBoard, depth: int = 20, time_limit: float = 5.0
) -> Dict[str, Any]:
    """分析当前局面。

    参数:
        engine: 引擎实例
        board: 当前局面
        depth: 搜索深度
        time_limit: 分析时间

    返回:
        dict: 分析结果
    """
    results = await engine.analyse(board, depth=depth, time_limit=time_limit)
    return results[0] if results else {}
