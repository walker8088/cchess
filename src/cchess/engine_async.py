"""异步引擎接口 - 基于 asyncio 的异步调用支持"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional

from .board import ChessBoard

logger = logging.getLogger(__name__)


class AsyncEngine:
    """异步引擎封装，基于 asyncio 实现非阻塞调用。

    支持 UCI 和 UCCI 两种协议，自动检测引擎类型。

    使用示例:
        async with AsyncEngine("path/to/engine") as engine:
            result = await engine.play(board, depth=10)
            print(result)
    """

    def __init__(self, exec_path: str = "", protocol: str = "auto"):
        self.engine_exec_path = exec_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self._initialized = False
        self._options: Dict[str, Any] = {}
        self._id: Dict[str, str] = {}
        self._protocol = protocol  # "auto", "uci", or "ucci"

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
        # 协议分支处理天然多嵌套多分支
        # pylint: disable=too-many-branches,too-many-nested-blocks
        if self._initialized:
            return True

        try:
            startupinfo = None
            if subprocess._mswindows:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = await asyncio.create_subprocess_exec(
                self.engine_exec_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=startupinfo,
            )

            # 自动检测协议类型或发送指定协议初始化命令
            if self._protocol == "auto":
                # 先尝试 UCCI
                await self._send_line("ucci")
                try:
                    line = await asyncio.wait_for(self._read_line(), timeout=3.0)
                    if line == "ucciok":
                        self._protocol = "ucci"
                    elif line.startswith("option"):
                        # 继续读取直到找到 ucciok 或 uciok
                        while True:
                            line = await asyncio.wait_for(
                                self._read_line(), timeout=3.0
                            )
                            if line == "ucciok":
                                self._protocol = "ucci"
                                break
                            if line == "uciok":
                                self._protocol = "uci"
                                break
                            if line.startswith("id"):
                                await self._parse_id(line)
                    elif line == "uciok":
                        self._protocol = "uci"
                    else:
                        # 默认当作 UCCI 处理
                        self._protocol = "ucci"
                        while True:
                            line = await asyncio.wait_for(
                                self._read_line(), timeout=3.0
                            )
                            if line == "ucciok":
                                break
                            if line.startswith("id"):
                                await self._parse_id(line)
                except asyncio.TimeoutError:
                    # UCCI 超时，尝试 UCI
                    await self._send_line("uci")
                    while True:
                        line = await asyncio.wait_for(self._read_line(), timeout=3.0)
                        if line == "uciok":
                            self._protocol = "uci"
                            break
                        if line.startswith("option"):
                            await self._parse_option(line)
                        elif line.startswith("id"):
                            await self._parse_id(line)
            elif self._protocol == "uci":
                await self._send_line("uci")
                try:
                    while True:
                        line = await asyncio.wait_for(self._read_line(), timeout=5.0)
                        if not line:
                            # EOF - 引擎关闭了 stdout 或不识别协议
                            logger.error(
                                "UCI initialization failed: engine closed connection"
                            )
                            if self.process:
                                self.process.kill()
                                await self.process.wait()
                            self.process = None
                            return False
                        if line == "uciok":
                            break
                        if line.startswith("option"):
                            await self._parse_option(line)
                        elif line.startswith("id"):
                            await self._parse_id(line)
                except asyncio.TimeoutError:
                    logger.error(
                        "UCI initialization timeout (engine may not support UCI)"
                    )
                    if self.process:
                        self.process.kill()
                        await self.process.wait()
                    self.process = None
                    return False
            else:  # ucci
                await self._send_line("ucci")
                try:
                    while True:
                        line = await asyncio.wait_for(self._read_line(), timeout=5.0)
                        if not line:
                            # EOF - 引擎关闭了 stdout 或不识别协议
                            logger.error(
                                "UCCI initialization failed: engine closed connection"
                            )
                            if self.process:
                                self.process.kill()
                                await self.process.wait()
                            self.process = None
                            return False
                        if line == "ucciok":
                            break
                        if line.startswith("option"):
                            await self._parse_option(line)
                        elif line.startswith("id"):
                            await self._parse_id(line)
                except asyncio.TimeoutError:
                    logger.error(
                        "UCCI initialization timeout (engine may not support UCCI)"
                    )
                    if self.process:
                        self.process.kill()
                        await self.process.wait()
                    self.process = None
                    return False

            self._initialized = True
            logger.info("Engine initialized: %s", self._id.get("name", "Unknown"))
            return True

        except (RuntimeError, OSError) as e:
            logger.error("Failed to initialize engine: %s", e)
            if self.process:
                try:
                    self.process.kill()
                    await self.process.wait()
                except OSError:  # pylint: disable=broad-exception-caught
                    pass
                self.process = None
            return False

    async def _send_line(self, line: str) -> None:
        """发送一行命令到引擎"""
        if self.process and self.process.stdin:
            self.process.stdin.write((line + "\n").encode())
            await self.process.stdin.drain()
            logger.debug(">> %s", line)

    async def _read_line(self) -> str:
        """从引擎读取一行

        返回空字符串表示 EOF（引擎关闭了 stdout）
        """
        if self.process and self.process.stdout:
            try:
                line_bytes = await self.process.stdout.readline()
                if not line_bytes:  # EOF
                    return ""
                line = line_bytes.decode().strip()
                logger.debug("<< %s", line)
                return line
            except (OSError, UnicodeDecodeError) as e:
                logger.debug("read_line error: %s", e)
                return ""
        return ""

    async def _parse_option(self, line: str) -> None:
        """解析 option 行"""
        parts = line.split()
        if len(parts) < 4:
            return

        name_idx = parts.index("name") + 1 if "name" in parts else -1
        if 0 < name_idx < len(parts):
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
        timeout: Optional[float] = 60.0,
    ) -> Dict[str, Any]:
        """执行一步棋。

        参数:
            board: 当前局面
            depth: 搜索深度
            time_limit: 时间限制（秒）
            ponder: 是否 ponder
            timeout: 整体超时（秒），默认 60 秒

        返回:
            dict: 包含 'move', 'score', 'pv' 等信息
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized")

        # 发送局面
        await self._send_line(f"position fen {board.to_fen()}")

        # 构建并发送 go 命令
        go_cmd = self._build_go_command(depth, time_limit, ponder)
        await self._send_line(go_cmd)

        # 等待结果（带超时保护）
        try:
            if timeout is not None:
                return await asyncio.wait_for(self._wait_for_result(), timeout=timeout)
            return await self._wait_for_result()
        except asyncio.TimeoutError:
            logger.warning("play() timed out after %s seconds", timeout)
            # 超时后尝试停止引擎思考
            await self._stop_thinking()
            return {"move": None, "score": None, "pv": []}

    async def _stop_thinking(self) -> None:
        """停止引擎思考（发送 stop/quit 命令）"""
        try:
            if self._protocol == "ucci":
                await self._send_line("quit")
            else:
                await self._send_line("stop")
        except (OSError, ConnectionError) as e:
            logger.debug("Failed to stop thinking: %s", e)

    def _build_go_command(
        self,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None,
        ponder: bool = False,
    ) -> str:
        """构建 go 命令字符串"""
        go_cmd = "go"
        if depth is not None:
            go_cmd += f" depth {depth}"
        if time_limit is not None:
            go_cmd += f" movetime {int(time_limit * 1000)}"
        if ponder:
            go_cmd += " ponder"
        return go_cmd

    async def _wait_for_result(self) -> Dict[str, Any]:
        """等待引擎返回结果"""
        result = {"move": None, "score": None, "pv": []}
        empty_line_count = 0
        while True:
            line = await self._read_line()
            if not line:
                # EOF 或连续空行
                empty_line_count += 1
                if empty_line_count > 5:
                    logger.warning("Engine returned too many empty lines")
                    break
                continue
            empty_line_count = 0
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    result["move"] = parts[1]
                if len(parts) >= 4 and parts[2] == "ponder":
                    result["ponder"] = parts[3]
                break
            if line.startswith("info") and "score" in line:
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
        timeout: Optional[float] = 60.0,
    ) -> List[Dict[str, Any]]:
        """分析局面。

        参数:
            board: 当前局面
            depth: 搜索深度
            time_limit: 分析时间（秒）
            multipv: 分析多条线路的数量
            timeout: 整体超时（秒），默认 60 秒

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

        # 收集分析结果（带超时保护）
        try:
            return await self._collect_analysis_results(multipv, timeout)
        except asyncio.TimeoutError:
            logger.warning("analyse() timed out after %s seconds", timeout)
            await self._stop_thinking()
            return []

    async def _collect_analysis_results(
        self, multipv: int, timeout: Optional[float]
    ) -> List[Dict[str, Any]]:
        """收集分析结果

        参数:
            multipv: 期望的多线路数量
            timeout: 超时秒数

        返回:
            list: 分析结果列表
        """
        results: List[Dict[str, Any]] = []
        current_info: Dict[int, Dict[str, Any]] = {}

        async def _collect():
            empty_line_count = 0
            while True:
                line = await self._read_line()
                if not line:
                    # EOF 或连续空行
                    empty_line_count += 1
                    if empty_line_count > 5:
                        logger.warning("Engine returned too many empty lines")
                        break
                    continue
                empty_line_count = 0
                if line.startswith("bestmove"):
                    break
                if line.startswith("info"):
                    info = self._parse_info(line)
                    multipv_num = info.get("multipv", 1)
                    current_info[multipv_num] = info

            # 整理结果
            for i in range(1, multipv + 1):
                if i in current_info:
                    results.append(current_info[i])

        if timeout is not None:
            await asyncio.wait_for(_collect(), timeout=timeout)
        else:
            await _collect()

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
            elif parts[i] == "seldepth":
                result["seldepth"] = int(parts[i + 1]) if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "nodes":
                result["nodes"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "nps":
                result["nps"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "time":
                result["time"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "currmove":
                result["currmove"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "currmovenumber":
                result["currmovenumber"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            elif parts[i] == "hashfull":
                result["hashfull"] = parts[i + 1] if i + 1 < len(parts) else None
                i += 2
            else:
                i += 1

        return result

    async def quit(self) -> None:
        """关闭引擎进程（总是确保进程被关闭）

        资源清理路径故意使用 Exception 捕获以确保进程终止。
        """
        # pylint: disable=broad-exception-caught
        if self.process:
            try:
                # 先尝试正常退出
                try:
                    self.process.stdin.close()
                except Exception:
                    pass
                await self._send_line("quit")
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    # 优雅退出超时，强制 kill
                    try:
                        self.process.kill()
                        await self.process.wait()
                    except Exception as e:
                        logger.debug("Failed to kill process: %s", e)
            except Exception as e:
                # 出错时也确保进程被终止
                logger.warning("Error during quit: %s, force killing", e)
                try:
                    self.process.kill()
                    await self.process.wait()
                except Exception:
                    pass

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
