# -*- coding: utf-8 -*-
'''
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
'''
import os 
import time
import enum
import json
import logging
import subprocess
from pathlib import Path
from threading import Thread
from queue import Queue, Empty
 
from .common import get_move_color, fen_mirror, iccs_mirror, iccs_list_mirror, RED

from .board import ChessBoard
from .exception import EngineErrorException
  
#-----------------------------------------------------#
logger = logging.getLogger(__name__)

#-----------------------------------------------------#

def is_int(s: str) -> bool:
    """
    判断字符串是否表示一个有效的整数。
    
    支持：
    - 正整数（如 "123"）
    - 负整数（如 "-456"）
    - 零（如 "0"、"-0"、"+0"）
    - 可选的正负号（"+" 或 "-"）
    - 首尾空格（如 " 123 "）
    
    不支持：
    - 小数（如 "123.45"）
    - 前导零（如 "00123"，除了 "0" 本身）
    - 其他非数字字符
    
    参数：
        s (str): 要判断的字符串
    
    返回：
        bool: True 表示是有效整数字符串，False 表示不是
    """
    s = s.strip()  # 去除首尾空格
    if not s:
        return False
    
    # 处理可选的正负号
    if s[0] in ('+', '-'):
        s = s[1:]
    
    if not s:
        return False  # 如 "+" 或 "-"
    
    # 单独处理 "0"
    if s == '0':
        return True
    
    # 不允许前导零
    if s[0] == '0':
        return False
    
    # 其余部分必须全为数字
    return s.isdigit()

def parse_engine_info_to_dict(s):  
    """把引擎输出的 info 字符串解析为字典。

    解析 UCI/UCCI 引擎输出的单行信息，将键值对提取为字典，
    遇到 'pv' 时会把剩余部分作为候选走法列表放到 'moves' 键下。

    参数:
        s (str): 引擎输出的一行字符串

    返回:
        dict: 解析出的键值对字典，数字字段会转换为 int
    """
    result = {}  
    current_key = None
    info = s.split()
    for index, part in enumerate(info): 
        if part in ['info', 'cp', 'lowerbound', 'upperbound']: #略过这些关键字,不影响分析结果
            continue
        elif part == 'pv': ##遇到pv就是到尾了，剩下的都是招法
            result['moves'] = info[index+1:]
            break
            
        if current_key is None:  
            current_key = part
            #替换key
            if current_key == 'bestmove':
                current_key = 'move'
        else:    
            if part == 'mate': # score mate 这样的字符串，后滑一个关键字 
                current_key = part
                continue  
            else:
                if is_int(part):
                    result[current_key] = int(part)  
                else:
                    result[current_key] = part  
                current_key = None  

    return result  

#------------------------------------------------------------------------------
#Engine status
class EngineStatus(enum.IntEnum):
    ERROR = 0,
    BOOTING = 1,
    READY = 2,
    WAITING = 3,
    INFO_MOVE = 4,
    MOVE = 5,
    DEAD = 6,
    UNKNOWN = 7,
    BOARD_RESET = 8


#ON_POSIX = 'posix' in sys.builtin_module_names

#------------------------------------------------------------------------------
class Engine(Thread):
    def __init__(self, exec_path=''):
        """Engine 进程包装对象。

        该类继承自 `Thread`，用于启动和管理外部棋力引擎进程，
        并通过队列暴露解析后的引擎信息。

        参数:
            exec_path (str): 引擎可执行文件路径（可选）
        """

        super().__init__()
 
        self.engine_exec_path = exec_path

        self.daemon = True
        self.running = False

        self.engine_status = None
        self.ids = {}
        self.options = []

        self.last_fen = None
        self.move_queue = Queue()

    def init_cmd(self):
        """返回启动时发送给引擎的初始化命令。

        子类（如 UciEngine、UcciEngine）应重写此方法返回
        对应协议的初始化命令（例如 'uci' 或 'ucci'）。
        """
        return ""
    
    def load(self, engine_path):
        """启动引擎进程并进行必要的初始化。

        参数:
            engine_path (str): 引擎可执行文件路径

        返回:
            bool: 成功则返回 True，失败返回 False
        """

        self.engine_exec_path = engine_path

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(
                self.engine_exec_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                cwd=Path(self.engine_exec_path).parent,
                text=True,
            )
        except Exception as e:
            logger.error(f"load engine {engine_path} ERROR: {e}")
            self.engine_status = EngineStatus.ERROR
            return False

        time.sleep(0.5)
        
        self.pin = self.process.stdin
        self.pout = self.process.stdout
        self.perr = self.process.stderr
        self.engine_out_queque = Queue()
        self.engine_status = EngineStatus.BOOTING

        self._send_cmd(self.init_cmd())
        
        self.start()
        
        return True

    def go_from(self, fen, params=None):
        """向引擎发送 position + go 命令以开始搜索。

        参数:
            fen (str): 要搜索的棋局 FEN
            params (dict): 传递给引擎的 go 参数（如 depth, movetime 等）

        返回:
            bool: 命令发送成功返回 True，否则返回 False
        """

        if params is None:
            params = {}

        self._send_cmd(f'position fen {fen}')
        param_list = [f"{key} {value}" for key, value in params.items()]
        go_cmd = "go " + ' '.join(param_list)

        ok = self._send_cmd(go_cmd)
        if not ok:
            return False

        self.last_fen = fen
        self.last_go = go_cmd
        self.score_dict = {}

        return True

    def get_action(self):
        """尝试获取已解析的引擎动作（非阻塞）。

        会先处理一次内部消息队列，然后从 `move_queue` 弹出一条
        已解析的动作信息并返回；若队列为空返回 None。
        """
        self._handle_msg_once()
        if self.move_queue.empty():
            return None           
        return self.move_queue.get()
                
    def set_option(self, name, value):
        """向引擎发送设置选项的命令（UCI/UCCI setoption）。

        参数:
            name (str): 选项名
            value: 选项值
        """
        cmd = f'setoption name {name} value {value}'
        self._send_cmd(cmd)
    
    def _send_cmd(self, cmd_str):
        """向引擎进程的 stdin 发送一条命令并刷新。

        在发送前会检查进程是否已经退出，如异常会抛出 `EngineErrorException`。

        参数:
            cmd_str (str): 要发送的命令（单行，不含换行）

        返回:
            bool: 成功返回 True，否则抛出异常
        """
        logger.debug(f"--> {cmd_str}")
        
        if self.process.returncode is not None:
            self.engine_status = EngineStatus.ERROR
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
        
        try:
            cmd_bytes = f'{cmd_str}\r\n'
            self.pin.write(cmd_bytes)
            self.pin.flush()
        except Exception as e:
            logger.error(f"Send cmd [{cmd_str}] ERROR: {e}")
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
            
        if self.process.returncode is not None:
            self.engine_status = EngineStatus.ERROR
            raise EngineErrorException(f"程序异常退出，退出码：{self.process.returncode}")
         
        return True


    def wait_for_ready(self, timeout = 10):
        """等待引擎进入 READY 状态，最多等待 `timeout` 秒。
        在等待期间会间歇性地处理来自引擎的输出消息。

        参数:
            timeout (float): 超时时间（秒）

        返回:
            bool: 引擎准备好返回 True，超时返回 False
        """
        start_time = time.time()
        
        while True:
            self._handle_msg_once()
            if self.engine_status == EngineStatus.READY:
                return True
                
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.2)
        
        return False
        
    def quit(self):
        """发送 'quit' 命令终止引擎并短暂停顿以便进程退出。"""
        self._send_cmd("quit")
        time.sleep(0.2)

    def stop_thinking(self):
        """请求引擎停止正在进行的搜索并读取可能的返回信息。
        发送 'stop' 后尝试多次拉取动作以确保引擎的响应被消费。
        """
        self._send_cmd('stop')
        time.sleep(0.1)
        self.get_action()
        time.sleep(0.1)
        self.get_action()
        
    def run(self):
        """线程主循环。不断调用 `run_once` 读取引擎输出直到停止。"""
        
        self.running = True

        while self.running:
            self.run_once()
    
    #run_once 在线程中运行        
    def run_once(self):
        #readline 会阻塞
        output = self.pout.readline().strip()
        if len(output) > 0:
            self.engine_out_queque.put(output)
    
    #handle_msg_once 在前台运行        
    def _handle_msg_once(self):
        """处理引擎输出队列中的一条消息（非阻塞）。

        从内部输出队列中取出一行引擎输出，解析后根据当前状态构造
        动作字典并放入 `move_queue`。返回 True 表示处理了消息，
        返回 False 表示队列为空无消息可处理。
        """

        try:
            output = self.engine_out_queque.get_nowait()
        except Empty:
            return False

        logger.debug(f"<-- {output}")

        if output in ['bye', '']:  #stop pipe
            self.process.terminate()
            return True

        out_list = output.split()
        resp_id = out_list[0]

        move_info = {}

        if self.engine_status == EngineStatus.BOOTING:
            if resp_id == "id":
                self.ids[out_list[1]] = ' '.join(out_list[2:])
            elif resp_id == "option":
                self.options.append(output)
            if resp_id == self.ok_resp():
                self.engine_status = EngineStatus.READY
                move_info["action"] = 'ready'

        elif self.engine_status == EngineStatus.READY:
            move_info["fen_engine"] = self.last_fen
            move_info['raw_msg'] = output
            move_info["action"] = 'info'

            if resp_id == 'nobestmove':
                move_info["action"] = 'dead'
            elif resp_id == 'bestmove':
                if out_list[1] in ['null', 'resign', '(none)']:
                    move_info["action"] = 'dead'
                elif out_list[1] == 'draw':
                    move_info["action"] = 'draw'
                else:
                    move_info["action"] = 'bestmove'
                    resp_dict = parse_engine_info_to_dict(output)
                    move_info.update(resp_dict)
                    move_key = move_info['move']
                    if move_key in self.score_dict:
                        for key in ['score', 'mate', 'moves', 'seldepth', 'time']:
                            if key in self.score_dict[move_key]:
                                move_info[key] = self.score_dict[move_key][key]
                        
            elif resp_id == 'info' and out_list[1] == "depth":
                #info depth 6 score 4 pv b0c2 b9c7  c3c4 h9i7 c2d4 h7e7
                #info depth 1 seldepth 1 multipv 1 score cp -58 nodes 28 nps 14000 hashfull 0 tbhits 0 time 2 pv f5c5
                move_info['action'] = 'info_move'
                resp_dict = parse_engine_info_to_dict(output)               
                move_info.update(resp_dict)
                if 'moves' in move_info:
                    move_key = move_info['moves'][0]
                    self.score_dict[move_key] = move_info
                elif 'currmove' in move_info:
                    #暂时不处理
                    pass
                else:
                    logger.info(move_info)
                    
        if len(move_info) > 0:
            self.move_queue.put(move_info)
        
        return True
        
#------------------------------------------------------------------------------
class UcciEngine(Engine):
    def init_cmd(self):
        return "ucci"

    def ok_resp(self):
        return "ucciok"


class UciEngine(Engine):
    def init_cmd(self):
        return "uci"

    def ok_resp(self):
        return "uciok"

#------------------------------------------------------------------------------
def action_mirror(action):
    for key in action:
        if key in ['move', 'ponder']:
            action[key] = iccs_mirror(action[key])
        if key in ['moves']:
            action[key] = iccs_list_mirror(action[key])

    return action
            
#------------------------------------------------------------------------------
class FenCache():
    def __init__(self):
        """简单的 FEN 行为缓存，用于存储引擎对某局面的推荐走法。

        属性：
            fen_dict (dict): 以 fen 为键的动作字典
            cache_file (str): 缓存文件路径
            need_save (bool): 是否需要保存到文件
        """
        self.fen_dict = {}
        self.cache_file = ''
        self.need_save = False
        
    def get(self, fen):
        """根据给定的 FEN 获取缓存的动作信息。

        如果直接命中返回 (info, ''), 若镜像局面命中返回 (info, 'mirror')，
        否则返回 (None, None)。
        """
        if fen in self.fen_dict:
            return (self.fen_dict[fen], '')
        
        f_mirror = fen_mirror(fen)
        if f_mirror in self.fen_dict:
            return (self.fen_dict[f_mirror], 'mirror')
        
        return (None, None)
    
    def get_best_action(self, fen):
        """从缓存中返回对给定 FEN 的最优动作。

        根据当前走子方选择评分最高或最低的动作；若使用了镜像缓存
        则对动作做镜像后返回。
        返回值为动作字典或 None（若缓存未命中）。
        """
        move_color = get_move_color(fen)
        
        info, state = self.get(fen)
        if info is None:
            return None
            
        actions = [v for v in sorted(info.values(), key=lambda item: item['score'])]
        
        if move_color == RED:
            act = actions[0]
        else:
            act = actions[-1]
        
        if state == 'mirror':
            #print('mirror')
            return action_mirror(act)        
        
        return act
        
    def save_action(self, fen, action):
        """保存引擎对某个 FEN 的动作到缓存中。

        支持将动作保存到原局面或其镜像局面对应的缓存结构中。
        标记 `need_save` 表示需要写回文件。
        """
        
        iccs = action['move']
        if fen in self.fen_dict:
            self.fen_dict[fen][iccs] = action
            return True
            
        f_mirror = fen_mirror(fen)
        i_mirror = iccs_mirror(iccs)
        if f_mirror in self.fen_dict:    
            self.fen_dict[f_mirror][i_mirror] = action
            return True
       
        self.fen_dict[fen]= {}
        self.fen_dict[fen][iccs] = action
        self.need_save = True
        
        return True
                        
    def load(self, cache_file):
        """从文件加载缓存，如果文件不存在则初始化为空缓存。

        参数:
            cache_file (str): 缓存文件路径
        """
        
        if not Path(cache_file).is_file():
            self.fen_dict = {}
        else:
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.fen_dict = json.load(f)
        
        self.cache_file = cache_file
        self.need_save = False
        
    def save(self):
        """将内存缓存以 JSON 格式写回 `cache_file` 并清除 `need_save` 标志。"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.fen_dict, f)
        self.need_save = False
        
#------------------------------------------------------------------------------
class EngineManager():
    def __init__(self, fen_cache=None):
        """引擎管理器：加载、配置引擎并对外提供运行和缓存接口。

        参数:
            fen_cache (FenCache): 可选的缓存实例，如未提供会创建一个新的。
        """
        self.engine = None
        if fen_cache is None:
            fen_cache = FenCache()
        self.cache = fen_cache
        
    def load_uci(self, engine_exec, options, go_params):
        """以 UCI 协议加载并初始化引擎。

        参数:
            engine_exec (str): 引擎可执行文件路径
            options (dict): 引擎选项键值对
            go_params (dict): 默认的 go 参数

        返回:
            bool: 成功返回 True，否则 False
        """
        self.engine = UciEngine()
        return self._load(engine_exec, options, go_params)
        
    def load_ucci(self, engine_exec, options, go_params):
        """以 UCCI 协议加载并初始化引擎（类似 `load_uci`）。"""
        self.engine = UcciEngine()
        return self._load(engine_exec, options, go_params)
        
    def _load(self, engine_exec, options, go_params):
        """内部加载引擎并应用选项。

        返回 True 表示加载并准备就绪，False 表示失败。
        """
        
        ok = self.engine.load(engine_exec)
        if not ok:
            return False
        
        ok = self.engine.wait_for_ready()
        if not ok:
            return False
        
        #self.engine_options = options
        for name, value in options.items():
            self.engine.set_option(name, value)
            
        self.go_params = go_params
        
        return True
        
    def get_best_cache(self, fen):
        """从缓存获取对给定 FEN 的最佳动作（若有）。"""
        return self.cache.get_best_action(fen)
        
    def get_fen_score(self, fen):
        """先尝试从缓存获取评分动作，若未命中则调用引擎运行。

        返回动作字典（或 None）。
        """
        action = self.get_best_cache(fen)
        return action or self.run_engine(fen)
        
    def run_engine(self, fen):
        """用已加载的引擎对给定 FEN 运行搜索并返回最终动作。

        该方法会启动引擎的搜索（调用 `go_from`），不断读取引擎
        返回的消息直到得到 `bestmove` 或其他终止信号，然后将
        结果保存到缓存并返回动作字典。
        """

        board = ChessBoard(fen)   
        self.engine.go_from(fen, self.go_params)
        
        #print('go:', fen, self.go_params)
        while True:
            action = self.engine.get_action()
            
            if action is None:
                time.sleep(0.2)
                continue
                
            action_id = action['action']
            if action_id == 'info_move':
                #print(action['raw_msg'])
                pass
            elif action_id in ['dead']:
                print(action['raw_msg'])
                action['score'] = 30000
                action['mate'] = 0
                return action
                
            elif action_id == 'bestmove':
                iccs = action["move"]
                move = board.move_iccs(iccs)
                if move is None:
                    continue
                   
                board.next_turn()
                #fen_next = board.to_fen()
                #action['move_text'] = move.to_text()
                
                #本步的得分是下一步的负值
                for key in ['score', 'mate']:
                    if key in action:
                        action[key] = -action[key]
                        
                #再处理出现mate时，score没分的情况
                if ('score' not in action) and ('mate' in action):
                    mate_v = action['mate']
                    mate_flag = 1 if mate_v > 0 else -1
                    action['score'] = (30000-abs(mate_v)) * mate_flag
     
                self.cache.save_action(fen, action)    
                
                return action
   
    def quit(self):
        """终止当前管理的引擎并短暂停顿以确保进程退出。"""
        self.engine.quit()
        time.sleep(0.5)

#------------------------------------------------------------------------------
