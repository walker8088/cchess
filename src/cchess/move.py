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

from .common import RED, BLACK, fench_to_species, fench_to_text, text_to_fench, pos2iccs, half2full

#-----------------------------------------------------#
#TODO 英文全角半角统一识别
_h_level_index = ((), ("九", "八", "七", "六", "五", "四", "三", "二", "一"),
                 ("１", "２", "３", "４", "５", "６", "７", "８", "９"))

_v_change_index = ((), ("错", "一", "二", "三", "四", "五", "六", "七", "八", "九"),
                  ("误", "１", "２", "３", "４", "５", "６", "７", "８", "９"))

#-----------------------------------------------------#
class Move(object):
    def __init__(self, board, p_from, p_to, is_checking=False):

        """初始化一个走子对象。

        复制传入的 `board`，记录起点 `p_from` 与终点 `p_to`，并设置
        是否触发将军等元信息。计算被吃掉的子（若有），构造执行
        走子后的 `board_done`，并初始化用于走子树和引擎交互的字段。
        """

        self.board = board.copy()
        self.p_from = p_from
        self.p_to = p_to
        self.is_checking = is_checking
        self.step_index = 0
        self.score = None
        self.annote = ''
        self.parent = None

        if self.is_checking:
            self.is_checkmate = self.board.is_checkmate()
        else:
            self.is_checkmate = False

        self.captured = self.board.get_fench(p_to)
        self.board_done = board.copy()
        self.board_done._move_piece(p_from, p_to)
        self.board_done.next_turn()  #TODO 默认红走一步，黑走一步，对于让先的处理后续考虑
        self.next_move = None

        self.variation_next = None
        self.variations_all = [self]

        self.move_list_for_engine = []
        self.fen_for_engine = None

    @property
    def move_player(self):
        """返回执行此走子的玩家（当前棋盘的 `move_player`）。"""
        return self.board.move_player    

    def __str__(self):
        """返回此走子的 ICCS 格式字符串表示。"""
        return self.to_iccs()

    def mirror(self):
        """水平镜像当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行左右镜像，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        self.board = self.board.mirror()
        self.p_from = (8 - self.p_from[0], self.p_from[1])
        self.p_to = (8 - self.p_to[0], self.p_to[1])
        self.board_done = self.board_done.mirror()

        for move in self.get_variations():
            move.mirror()

        if self.next_move:
            self.next_move.mirror()

    def flip(self):
        """垂直翻转当前走子及其所有子节点（就地修改）。

        将棋盘和坐标进行上下翻转，并对 `board_done`、所有分支和
        `next_move` 链进行相同处理。该操作会修改当前 `Move` 实例
        及其子节点。
        """
        self.board = self.board.flip()
        self.p_from = (self.p_from[0], 9 - self.p_from[1])
        self.p_to = (self.p_to[0], 9 - self.p_to[1])
        self.board_done = self.board_done.flip()

        for move in self.get_variations():
            move.flip()

        if self.next_move:
            self.next_move.flip()

    def swap(self):
        """交换红黑视角（棋子交换阵营）并更新所有子节点（就地）。

        对当前走子、`board_done` 及所有分支和 `next_move` 做视角
        交换，使之从另一方视角表示。
        """
        self.board = self.board.swap()
        self.board_done = self.board_done.swap()

        for move in self.get_variations():
            move.swap()

        if self.next_move:
            self.next_move.swap()

    def is_valid_move(self):
        """判断该走子在原始棋盘上是否合法。

        通过底层棋盘的 `is_valid_move` 方法验证由 `p_from` 到 `p_to`
        的移动是否合法，返回布尔值。
        """
        return self.board.is_valid_move(self.p_from, self.p_to)

    def is_king_killed(self):
        """如果此走子吃掉了将/帅，返回 True。

        检查记录的 `captured` 字符是否表示国王（不区分大小写）。
        """
        if self.captured and self.captured.lower() == 'k':
            return True
        return False

    def len_variations(self):
        return len(self.variations_all)
    
    def get_variations(self, include_me = False):
        if include_me:
            return self.variations_all
        
        sibs = self.variations_all[:]
        sibs.remove(self)

        return sibs 

    def last_variation(self):
        return self.variations_all[-1]        
    
    def get_variation_index(self):
        slibling_count = len(self.variations_all)
        for index, m in enumerate(self.variations_all):
            if m == self:
                return (index, slibling_count)

    def add_variation(self, chess_move):
        chess_move.parent = self.parent
        chess_move.step_index = self.step_index
        last = self.last_variation()
        
        assert last.variation_next is None

        last.variation_next = chess_move
        
        self.variations_all.append(chess_move)
        for node in self.get_variations():
            node.variations_all = self.variations_all
        
        return chess_move

    def remove_variation(self, chess_move):
        if chess_move not in self.variations_all:
            return
        
        #先移出兄弟表
        self.variations_all.remove(chess_move)
        
        #从链上摘下
        node = self
        while node.variation_next :
            if node.variation_next == chess_move:
                next_node = node.variation_next.slibling_next
                node.variation_next = next_node
                chess_move.variation_next = None

        #更新兄弟表到所有的兄弟        
        for node in self.get_variations():
            node.variations_all = self.variations_all
                
    def append_next_move(self, chess_move):
        """将 `chess_move` 作为当前走子的后继加入走子树。

        设置 `chess_move.parent` 与 `step_index`。若当前无 `next_move`
        则作为线性后继；否则将其作为现有 `next_move` 的一个分支。
        """
        chess_move.parent = self
        chess_move.step_index = self.step_index + 1
        if not self.next_move:
            self.next_move = chess_move
        else:
            self.next_move.variations_all.append(chess_move)

    '''
    def branch_count(self):
        """返回当前分支数量（避免与实例属性 `branchs` 名称冲突）。"""
        return len(self.branchs)

    def get_branch(self, index):
        """返回索引为 `index` 的分支走子。

        直接从 `branchs` 列表中取出对应分支。
        """
        return self.branchs[index]

    def select_branch(self, index):
        """选择当前应使用的分支索引。

        将 `branch_index` 设为 `index`，用于后续遍历时决定走哪条分支。
        """
        self.branch_index = index

    def get_all_branchs(self):
        """返回包含自身和直接分支的列表（不递归子分支）。"""
        res = [self]
        res.extend(self.branchs)
        return res
        
    def dump_moves_line(self, move_list):
        """沿选定的分支收集一条走子线路并追加到 `move_list`。

        根据 `branch_index` 决定当前节点是自身还是某个分支，随后
        将该节点加入 `move_list` 并沿 `next_move` 继续递归。
        """

        if self.branch_index == 0:
            sel_move = self

        elif self.branch_index <= len(self.branchs):
            sel_move = self.branchs[self.branch_index - 1]
        else:
            sel_move = None

        if not sel_move:
            return
        move_list.append(sel_move)

        if not sel_move.next_move:
            return

        sel_move.next_move.dump_moves_line(move_list)

        if self.next_move:
            self.next_move.make_branchs_tag(self.branch_index, 0)
        
        #curr_variation_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        #所以就不能在分支中再找兄弟了，否则会重复输出分支
        if curr_variation_index > 0:
            return

        for index, variation_move in enumerate(self.get_variations()):
            branch_index += 1
            variation_index = index + 1
            variation_move.make_branchs_tag(branch_index, variation_index)
    '''
    
    def dump_moves(self, move_list, curr_move_line, is_tree_mode, curr_variation_index = 0):
        """将从当前节点开始的走子线路序列化并追加到 `move_list`。

        `curr_move_line` 表示当前遍历路径，本方法会在递归过程中
        扩展路径并将每条线（含分支索引）追加到 `move_list`。
        """

        backup_move_line = curr_move_line['moves'][:] 
        curr_move_line['moves'].append(self)
        
        curr_line_index = curr_move_line['index']

        if self.next_move:
            self.next_move.dump_moves(move_list, curr_move_line, is_tree_mode, 0)
        
        #curr_variation_index >0 说明是在分支中dump，因为主分支（index=0）已经把兄弟们遍历了一遍，
        #所以就不能在分支中再找兄弟了，否则会重复输出分支
        #assert curr_variation_index == self.get_variation_index()
        if curr_variation_index > 0:
            return
        
        #只有主分支（index == 0）才会遍历兄弟分支

        for index, variation_move in enumerate(self.get_variations()):
            variation_index = index + 1
            new_line_index = len(move_list)
            line_name = f'{curr_line_index}.{self.step_index}.{variation_index}_{new_line_index}'    
            new_line = {
                    'index': new_line_index, 
                    'name':line_name,  
                     #'variations':variations, 
                    'variation_index':variation_index, 
                    'from_line': (curr_line_index, self.step_index, variation_index), 
                    'moves':[]
                    }
    
            if not is_tree_mode:
                new_line['moves'].extend(backup_move_line)

            move_list.append(new_line)
            variation_move.dump_moves(move_list, new_line, is_tree_mode, variation_index)

    def init_move_line(self):
        return {'index': 0, 'name':'0', 'variations':[], 'moves':[] }
            
    def to_text(self, detailed=False):
        """返回此走子的中文可读文本表示。

        若 `detailed` 为 True，则在返回字符串后附加括号内的详细信息，
        例如吃子、将军或将死等注记。
        """

        fench = self.board.get_fench(self.p_from)
        _, man_side = fench_to_species(fench)

        diff = self.p_to[1] - self.p_from[1]

        #黑方是红方的反向操作
        if man_side == BLACK:
            diff = -diff

        if diff == 0:
            diff_str = "平"
        elif diff > 0:
            diff_str = "进"
        else:
            diff_str = "退"

        #王车炮兵规则
        if fench.lower() in ('k', 'r', 'c', 'p'):
            if diff == 0:
                dest_str = _h_level_index[man_side][self.p_to[0]]
            elif diff > 0:
                dest_str = _v_change_index[man_side][diff]
            else:
                dest_str = _v_change_index[man_side][-diff]
        else:  #士相马的规则
            dest_str = _h_level_index[man_side][self.p_to[0]]

        name_str = self.__get_text_name(self.p_from)

        text = name_str + diff_str + dest_str
        if not detailed:
            return text

        details = []
        if self.captured:
            details.append(f'吃{fench_to_text(self.captured)}', )
        if self.is_checkmate:
            details.append('将死', )
        elif self.is_checking:
            details.append('将军', )

        if len(details) == 0:
            return text
        else:
            return f'{text}({",".join(details)})'

    def __get_text_name(self, pos):
        """根据位置计算并返回带有位置限定词的棋子名称。

        当棋盘上有多个相同类型的子时（例如同一列有多辆车），返回
        用于区分的限定词如 '前'、'中'、'后' 或文件编号。
        """

        fench = self.board.get_fench(pos)
        _, man_side = fench_to_species(fench)
        man_name = fench_to_text(fench)

        #王，士，相命名规则
        if fench.lower() in ('k', 'a', 'b'):
            return man_name + _h_level_index[man_side][pos[0]]

        #车,马,炮,兵命名规则
        #红黑顺序相反，俩数组减少计算工作量
        pos_name2 = ((), ('后', '前'), ('前', '后'))
        pos_name3 = ((), ('后', '中', '前'), ('前', '中', '后'))
        pos_name4 = ((), ('后', '三', '二', '前'), ('前', '２', '３', '后'))
        pos_name5 = ((), ('后', '四', '三', '二', '前'), ('前', '２', '３', '４', '后'))

        count = 0
        pos_index = -1
        for y in range(10):
            if self.board._board[y][pos[0]] == fench:
                if pos[1] == y:
                    pos_index = count
                count += 1

        if count == 1:
            return man_name + _h_level_index[man_side][pos[0]]
        elif count == 2:
            return pos_name2[man_side][pos_index] + man_name
        elif count == 3:
            #TODO 查找另一个多子行
            return pos_name3[man_side][pos_index] + man_name
        elif count == 4:
            return pos_name4[man_side][pos_index] + man_name
        elif count == 5:
            return pos_name5[man_side][pos_index] + man_name

        return man_name + _h_level_index[man_side][pos[0]]

    def to_text_detail(self, show_variation, show_annote):
        
        if show_variation:
            txt = self.to_text_variation()
        else:
            txt = self.to_text()    
        
        annote = self.annote if show_annote else ''

        return (txt,  annote)
    
    def to_text_variation(self):
        
        assert len(self.variations_all) > 0
        
        #父节点只有一个孩子，那就是自己
        if len(self.variations_all) == 1:
            return self.to_text()
        
        txts = []
        for index, m in enumerate(self.variations_all):
            if m == self:
               txts.append(f'{m.to_text()}') 
            else:
               txts.append('*') #m.to_text())
        
        return f"[{','.join(txts)}]"
                       
    def prepare_for_engine(self, move_player, history):
        """为引擎查询准备 FEN 与 moves 列表。

        如果当前走子为吃子，则引擎的 FEN 应为走子后的局面；否则
        根据历史拼接 moves 列表以便向引擎发送完整走子序列。
        """
        if self.captured:
            #吃子移动
            self.board_done.move_player = move_player
            self.fen_for_engine = self.board_done.to_fen()
            self.move_list_for_engine = []
        else:
            #未吃子移动
            if not history:
                #历史为空
                self.fen_for_engine = self.board.to_fen()
                self.move_list_for_engine = [self.to_iccs()]
            else:
                #历史不为空,往后追加
                last_move = history[-1]
                self.fen_for_engine = last_move.fen_for_engine
                self.move_list_for_engine = last_move.move_list_for_engine[:]
                self.move_list_for_engine.append(self.to_iccs())

    
    def to_engine_fen(self):
        """返回用于引擎的输入字符串：基础 FEN（可选加 moves）。

        若 `move_list_for_engine` 为空，直接返回 `fen_for_engine`；
        否则返回形如 '<fen> moves <m1> <m2> ...' 的字符串。
        """
        if len(self.move_list_for_engine) == 0:
            return self.fen_for_engine

        move_str = ' '.join(self.move_list_for_engine)
        return ' '.join([self.fen_for_engine, 'moves', move_str])

    def to_iccs(self):
        """返回此走子的 ICCS（引擎）走法字符串。

        将内部 (x,y) 坐标元组转换为引擎使用的 ICCS 表示法。
        """
        return pos2iccs(self.p_from, self.p_to)

    @staticmethod
    def text_move_to_std_move(man_kind, move_player, p_from, move_str):
        """将中文走法片段转换为目标坐标。

        根据棋子类型 `man_kind`、走子方 `move_player` 与起点 `p_from`，
        解析 `move_str` 并返回目标坐标 `(x, y)`。会对中文数字与全角
        数字做简单归一化，否则在无法解析时返回 None。
        """

        #移动规则检查
        if man_kind in ['a', 'b', 'n'] and move_str[0] == "平":
            return None
        if move_str[0] not in ['进', '退', '平']:
            return None

        #王,车,炮,兵的移动规则
        if man_kind in ['k', 'r', 'c', 'p']:
            #平移
            if move_str[0] == "平":
                new_x = _h_level_index[move_player].index(move_str[1])
                return (new_x, p_from[1])
            else:
                #王，车，炮，兵的前进和后退
                # 支持不同形式的数字（如中文数字 '一' 与全角数字 '１'），尝试归一化后查找
                try:
                    diff = _v_change_index[move_player].index(move_str[1])
                except ValueError:
                    # 简单映射常见中文数字到全角数字
                    zh_to_full = {
                        '一': '１', '二': '２', '三': '３', '四': '４', '五': '５',
                        '六': '６', '七': '７', '八': '８', '九': '９'
                    }
                    ch = zh_to_full.get(move_str[1], move_str[1])
                    diff = _v_change_index[move_player].index(ch)

                if move_str[0] == "退":
                    diff = -diff

                if move_player == BLACK:
                    diff = -diff

                return (p_from[0], p_from[1] + diff)

        #仕的移动规则
        elif man_kind == 'a':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_y = -1 if move_str[0] == "进" else 1
            if move_player == BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #象的移动规则
        elif man_kind == 'b':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_y = -2 if move_str[0] == "进" else 2
            if move_player == BLACK:
                diff_y = -diff_y
            return (new_x, p_from[1] - diff_y)

        #马的移动规则
        elif man_kind == 'n':
            new_x = _h_level_index[move_player].index(move_str[1])
            diff_x = abs(p_from[0] - new_x)

            if move_str[0] == "进":
                diff_y = [3, 2, 1][diff_x]
            else:
                diff_y = [-3, -2, -1][diff_x]

            if move_player == RED:
                diff_y = -diff_y

            return (new_x, p_from[1] - diff_y)

    @staticmethod
    def from_text(board, move_str):
        """解析中文走法字符串，返回标准化的走子 `(p_from, p_to)`。

        支持形式如 '前/中/后' 的歧义消除以及 '一'..'五' 的列选择。
        若无法解析或找不到合法走子，返回 `None`。
        """
        move_str = half2full(move_str)

        #TODO测试黑方
        move_indexs = ["前", "中", "后", "一", "二", "三", "四", "五"]

        multi_mans = False
        multi_lines = False

        if move_str[0] in move_indexs:
            multi_mans = True
            man_index = move_indexs.index(move_str[0])
            if man_index > 2:
                multi_lines = True
            man_name = move_str[1]
            
        else:
            man_name = move_str[0]
        
        # 先将文字名称解析为 fench，以便在多行定位时使用
        fench = text_to_fench(man_name, board.move_player)
        if not fench:
            return None

        man_kind, move_player = fench_to_species(fench)

        if multi_lines:
            # 草案实现：支持以中文数字（'一','二','三','四','五'）指定某一列（文件）
            # 优先在该列查找对应棋子；若无则在全盘匹配中选择候选。
            # 对于兵（man_kind == 'p'），若同列有多个兵，则选择更靠前方的兵：
            # - 红方（RED）选择 y 最大的兵
            # - 黑方（BLACK）选择 y 最小的兵
            chinese_digit = move_str[0]
            target_x = None
            try:
                target_x = _h_level_index[move_player].index(chinese_digit)
            except Exception:
                target_x = None

            poss = []
            if target_x is not None:
                poss = board.get_fenchs_x(target_x, fench)

            if not poss:
                poss = board.get_fenchs(fench)

            # 如果是黑方，从玩家视角选取顺序可能相反，保持与其他分支处理一致
            if move_player == BLACK:
                poss = list(reversed(poss))

            # 对兵在同列多子情况做优先级选择
            if man_kind == 'p' and len(poss) > 1:
                if move_player == RED:
                    poss.sort(key=lambda p: p[1], reverse=True)
                else:
                    poss.sort(key=lambda p: p[1])

            if len(poss) == 0:
                return None

            for pos in poss:
                move = Move.text_move_to_std_move(man_kind, move_player, pos, move_str[2:])
                if move:
                    return (pos, move)

            return None

        if not multi_mans:
            #单子移动
            x = _h_level_index[move_player].index(move_str[1])
            poss = board.get_fenchs_x(x, fench)
            
            #无子可走
            if len(poss) == 0:
                return None

            #同一行选出来多个,这种情况下, 只有士象是可以多个子尝试移动而不用标明前后的
            if (len(poss) > 1) and (man_kind not in ['a', 'b']):
                return None

            for pos in poss:
                move = Move.text_move_to_std_move(man_kind, move_player, pos,
                                                  move_str[2:])
                if move:
                    return (pos, move)

            return None

        else:
            #多选一移动
            if move_str[0] in ['前','中','后']:
                poss = board.get_fenchs(fench)
                if move_player == BLACK:
                    poss.reverse()
                
                move_indexs = {"前": -1, "中": 1, "后": 0}
                pos = poss[move_indexs[move_str[0]]]
   
                #print(man_kind, move_player, pos, move_str[2:])
                move = Move.text_move_to_std_move(man_kind, move_player, pos,
                                                  move_str[2:])
                if move:
                    return (pos, move)
                else:
                    return None
            #多兵选一移动
            else:
                pass
                #TODO fix
