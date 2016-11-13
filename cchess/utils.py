# -*- coding: utf-8 -*-

from sets import *
    
from common import *
    

h_level_index = \
(
        (u"九",u"八",u"七",u"六",u"五",u"四",u"三",u"二",u"一"), 
        (u"１",u"２",u"３",u"４",u"５",u"６",u"７",u"８",u"９") 
)

v_change_index = \
(
        (u"错", ""u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"), 
        (u"误", ""u"１", u"２", u"３", u"４", u"５", u"６", u"７", u"８", u"９")
)


text_board = [
#u' 1  2   3   4   5   6   7   8   9',
u'9 ┌─┬─┬─┬───┬─┬─┬─┐',
u'  │  │  │  │＼│／│　│　│　│',
u'8 ├─┼─┼─┼─※─┼─┼─┼─┤',
u'  │　│　│　│／│＼│　│　│　│',
u'7 ├─┼─┼─┼─┼─┼─┼─┼─┤',
u'  │　│　│　│　│　│　│　│　│',
u'6 ├─┼─┼─┼─┼─┼─┼─┼─┤',
u'  │　│　│　│　│　│　│　│　│',
u'5 ├─┴─┴─┴─┴─┴─┴─┴─┤',
u'  │　                         　 │',
u'4 ├─┬─┬─┬─┬─┬─┬─┬─┤',
u'  │　│　│　│　│　│　│　│　│',
u'3 ├─┼─┼─┼─┼─┼─┼─┼─┤',
u'  │　│　│　│　│　│　│　│　│',
u'2 ├─┼─┼─┼─┼─┼─┼─┼─┤',
u'  │　│　│　│＼│／│　│　│　│',
u'1 ├─┼─┼─┼─※─┼─┼─┼─┤',
u'  │　│　│　│／│＼│　│　│　│',
u'0 └─┴─┴─┴───┴─┴─┴─┘',
u'  0   1   2   3   4   5   6   7   8'
#u'  九 八  七  六  五  四  三  二  一'
]

def pos_to_text_board_pos(pos):
    return (2*pos[0]+2, (9 - pos[1])*2)     
    
    
fench_species_dict = {
    'k':ChessmanT.KING,
    'a':ChessmanT.ADVISOR,
    'b':ChessmanT.BISHOP,
    'n':ChessmanT.KNIGHT,
    'r':ChessmanT.ROOK,
    'c':ChessmanT.CANNON,
    'p':ChessmanT.PAWN
}

fench_name_dict = {
   'K': u"帅",
   'k': u"将",
   'A': u"仕",
   'a': u"士",
   'B': u"相", 
   'b': u"象",
   'N': u"马",
   'n': u"马",
   'R': u"车",
   'r': u"车",
   'C': u"炮", 
   'c': u"炮",
   'P': u"兵", 
   'p': u"卒"     
}
    
species_fench_dict = {
   ChessmanT.KING:    ('K', 'k'),
   ChessmanT.ADVISOR: ('A', 'a'),
   ChessmanT.BISHOP:  ('B', 'b'),
   ChessmanT.KNIGHT:  ('N', 'n'),
   ChessmanT.ROOK:    ('R', 'r'),
   ChessmanT.CANNON:  ('C', 'c'),
   ChessmanT.PAWN:    ('P', 'p')     
}


def fench_to_name(fench) :
    return fench_name_dict[fench]
        
def fench_to_species(fen_ch):
    return fench_species_dict[fen_ch.lower()], ChessSide.BLACK if fen_ch.islower() else ChessSide.RED
    
def species_to_fench(species, side):
    return species_fench_dict[species][side]
    
    
def move_to_str(move):
    
    (x, y), (x_, y_) = move
    
    move_str = ''
    move_str += chr(ord('a') + x)
    move_str += str(y)
    move_str += chr(ord('a') + x_)
    move_str += str(y_)
    
    return move_str

def str_to_move(move_str):
    
    m00 = ord(move_str[0]) - ord('a')
    m01 = int(move_str[1])
    m10 = ord(move_str[2]) - ord('a')
    m11 = int(move_str[3])
    
    return ((m00,m01),(m10, m11))

def moves_to_std_moves_str(moves):
    move_strs = []

    for move in moves:
         move_strs.append(move_to_str(move)) 
    
    return ' '.join(move_strs)

# 比赛结果
UNKNOWN, RED_WIN, BLACK_WIN, PEACE  =  range(4)
result_str = (u"未知", u"红胜", u"黑胜",  u"平局" ) 

#存储类型
BOOK_UNKNOWN, BOOK_ALL, BOOK_BEGIN, BOOK_MIDDLE, BOOK_END = range(5)
book_type_str = (u"未知", u"全局", u"开局",  u"中局",  u"残局") 
    
#KING, ADVISOR, BISHOP, KNIGHT, ROOK, CANNON, PAWN

chessman_show_name_dict = {
   ChessmanT.KING:    (u"帅", u"将"),
   ChessmanT.ADVISOR: (u"仕", u"士"),
   ChessmanT.BISHOP:  (u"相", u"象"),
   ChessmanT.KNIGHT:  (u"马", u"马"),
   ChessmanT.ROOK:    (u"车", u"车"),
   ChessmanT.CANNON:  (u"炮", u"炮"),
   ChessmanT.PAWN:    (u"兵", u"卒")     
}

def get_show_name(species, side) :
        return chessman_show_name_dict[species][side]
        
#-----------------------------------------------------#

class MoveChecker(object) :
    def __init__(self, fen = None):
	self.clear()
        if fen:
                self.from_fen(fen)
                
    def clear(self):    
        self._board = [[None for x in range(9)] for y in range(10)]
        self.init_board = self._board
        self.move_log = []
        
    def put_man(self, fench, pos):
        self._board[pos[1]][pos[0]] = fench
    
    def get_man(self, pos):
        return self._board[pos[1]][pos[0]]
    
    def save_board(self):
        self.init_board = copy.deepcopy(self._board)
        
    def move_and_log(self, pos_from, pos_to):
        if not self.move(pos_from, pos_to):
                return False
        self.move_log.append((pos_from, pos_to))
        return True
        
    def move(self, pos_from, pos_to):
        fench = self._board[pos_from[1]][pos_from[0]]
        if not fench :
                return False        
        
        self._board[pos_to[1]][pos_to[0]] = fench
        self._board[pos_from[1]][pos_from[0]] = None
        
        return True
    
    def dump(self):
        board_str = text_board[:]
        y = 0
        for line in self._board:
            x = 0
            for ch in line:
                if ch : 
                        pos = pos_to_text_board_pos((x,y))
                        new_text=board_str[pos[1]][:pos[0]] + fench_to_name(ch) + board_str[pos[1]][pos[0]+1:]
                        board_str[pos[1]] = new_text
                x += 1                         
            y += 1
        
        print     
        for line in board_str:
                print line
        print
        
    def from_fen(self, fen):
        
        num_set = Set(('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        ch_set = Set(('k','a','b','n','r','c','p'))
        
        self.clear()
        
        if not fen or fen == '':
                return
        
        fen = fen.strip()
        
        x = 0
        y = 9

        for i in range(0, len(fen)):
            ch = fen[i]
            
            if ch == ' ':
                break
            elif ch == '/':
                y -= 1
                x = 0
                if y < 0:
                    break
            elif ch in num_set:
                x += int(ch)
                if x > 8:
                    x = 8
            elif ch.lower() in ch_set:
                if x <= 8:
                    self.put_man(ch, (x, y))                
                    x += 1
            else:
                return False
                
        return True  
    
    def get_chinese_move_str(self, p_from, p_to):

        fench = self.get_man(p_from)
        man_species, man_side = fench_to_species(fench)
        
        diff = p_to[1] - p_from[1] 
        
        #黑方是红方的反向操作    
        if man_side == ChessSide.BLACK:
                diff = -diff
                
        if diff == 0:        
                diff_str = u"平"                            
        elif diff > 0:
                diff_str = u"进"       
        else:
                diff_str = u"退" 
        
        #王车炮兵规则
        if man_species in [ChessmanT.KING, ChessmanT.ROOK, ChessmanT.CANNON, ChessmanT.PAWN]:
                if diff == 0 : 
                        dest_str = h_level_index[man_side][p_to[0]]
                elif diff > 0 : 
                        dest_str = v_change_index[man_side][diff]
                else :
                        dest_str = v_change_index[man_side][-diff]  
        else : #士相马的规则
                dest_str = h_level_index[man_side][p_to[0]]
        
        name_str = self.__get_chinese_name(p_from)
                
        return name_str + diff_str + dest_str 
                
    def __get_chinese_name(self, p_from):
        
        fench = self.get_man(p_from)
        man_species, man_side = fench_to_species(fench)
        man_name = fench_to_name(fench) 
        
        #王，士，相命名规则
        if man_species in [ChessmanT.KING, ChessmanT.ADVISOR, ChessmanT.BISHOP]:
                return man_name + h_level_index[man_side][p_from[0]]
        
        #车马炮兵命名规则        
        if man_species in [ChessmanT.ROOK, ChessmanT.CANNON, ChessmanT.KNIGHT, ChessmanT.PAWN]:
                #红黑顺序相反，俩数组减少计算工作量
                pos_name = ((u'后', u'前'), (u'前', u'后')) 
                #pos_count_name = （(u'一',u'二',u'三',u'四',u'五'),(u'１',u'２',u'３',u'４',u'５')）
                count = 0
                pos_index = -1
                for y in range(10):
                        if self._board[y][p_from[0]] == fench:
                                if p_from[1] == y:
                                        pos_index = count
                                count += 1
                if count == 1:
                        return man_name + h_level_index[man_side][p_from[0]]
                elif count == 2:
                        return pos_name[pos_index][man_side] + man_name
        
        #复杂兵的命名规则        
        #else:
        #                return man_name + h_level_index[man_side][p_from[0]]
                
def moves_to_chinese(fen, moves):
        moves_str = []
        checker = MoveChecker(fen)
        for move_it in moves:
                moves_str.append(checker.get_chinese_move_str(*move_it))
                checker.move(*move_it)
        return ' '.join(moves_str)
        
#-----------------------------------------------------#
class MoveLogItem(object):
    def __init__(self, p_from = None, p_to = None, killed_man = None, fen_before_move = '',  fen_after_move = '',  last_non_killed_fen = '',  last_non_killed_moves = []):
        self.p_from = p_from
        self.p_to = p_to
        self.move_str = move_to_str(p_from, p_to)  if p_from else '' 
        self.killed_man = killed_man
        self.fen_before_move = fen_before_move
        self.fen_after_move = fen_after_move
        self.last_non_killed_fen =  last_non_killed_fen       
        self.last_non_killed_moves = last_non_killed_moves[:]
        
    def fen_for_engine(self) :
        if  self.killed_man or not self.p_from:
            return self.fen_after_move
        else :    
            return self.last_non_killed_fen + " moves " + " ".join(self.last_non_killed_moves)
    
    def next_move_side(self) :
        
        move_id = self.fen_after_move.split()[1]
        
        return BLACK if (move_id.lower() == 'b') else RED
        
def mirror_moves(moves) :
        changes = {"a":"i", "b":"h", "c":"g", "d":"f", "e":"e", "f":"d", "g":"c", "h":"b", "i":"a" }
        new_moves  = ''
        
        for ch in moves :
                if  ch in changes :
                        new_moves += changes[ch]
                else :
                        new_moves += ch
        return new_moves



'''
c3d1 f0e0 c4c0 e0e1 f2e2 e1e2 c0e0 f1e1 d3e3 e2f2 e3f3 f2f1 f3f2 f1f2 e0e1 b9c9 (i5i9 e1e9 f2f1 e9i9 f1e1 i9e9 e1f1 e9e0)  d9e9 i5i9 e9e8 c8d8 e8d8 (e8f8 g7f7 \
f8f7 i9f9 f7e7 f9e9)  i9d9 d8e8 d9d1 e1e5 (e1d1 g7g0 d1d0 g0f0 e8f8 f2f1) f5f3 e5e3 d1e1 e3e1 g7g0 e1e0 g0f0 e8f8 f2f1
'''      
 
def has_branchs(move_str) :
        return True if "(" in move_str else False

def get_branch(move_str) :

        first = move_str.find("(")
        last = -1
        deep = 0
        
        for i in range(first+1, len(move_str)):
                if (move_str[i] == ")") :
                        if (deep == 0) :
                                last = i
                                break
                        else :
                                deep -= 1
                elif (move_str[i] == "(") :
                        deep += 1           
        #end for                
        return (first, last)
                        
def branch_split(moves_str) :
       
        move_list = [moves_str]
        
        while True: 
                new_list = []
                for move_item in move_list :
                        if not has_branchs(move_item) :
                                new_list.append(move_item)
                                continue
                        #real logic here
                        
                        first, last =  get_branch(move_item)
                        
                        if last < 0:
                                raise Exception("Match Error")
                        
                        head_moves = move_item[:first].split()
                        branch_moves = move_item[first+1 : last].split()
                        last_moves = move_item[last+1:].split() if (last < len(move_item) -1) else []
                        
                        new_head_moves = head_moves + last_moves
                        new_branch_moves = head_moves[:-1] + branch_moves
                        
                        new_list.append(" ".join(new_head_moves))
                        new_list.append(' '.join(new_branch_moves))
                        
                if len(new_list) == len(move_list):
                        break
                        
                move_list = new_list[:]
                
        return move_list
        
def __strip_comments_line(move_str):
        while True:
                new_str = move_str[:]
                first_pos = new_str.find('{')
                last_pos  = new_str.find('}')
        
def strip_comments(moves_str):
        new_moves = []
        moves = moves_str.split(' ')
        for move_it in moves:
                new_it = __strip_comments_line(move_it)
                new_moves.append(move_it)
        
        return ' '.join(new_moves).strip()
        
#-----------------------------------------------------#
'''        
def load_book(file_name):
        
        ext = os.path.splitext(str(file_name))[1].lower()
        
        if ext == ".xqf" :
                loader = XQFLoader()
                return loader.load(file_name)
        
        elif ext == ".cbf" :
                loader = CBFLoader()
                return loader.load(file_name)
        
        elif ext == ".pgn" :
                loader = PGNLoader()
                return loader.load(file_name)
        
        else :
                return None
'''                
#-----------------------------------------------------#
if __name__ == '__main__':        
       
        #move_str = 'f3f2 f1f2 e0e1 b9c9{comments}(i5i9 e1e9 f2f1 e9i9 f1e1 i9e9 e1f1 e9e0) d9e9 i5i9 e8d8(e8f8 g7f7 f8f7 i9f9 f7e7 f9e9) i9d9{asddddddddd} e1e5 f5f3 '      
        #moves = branch_split(move_str)
        #for it in moves :
        #        print it
        
        checker = MoveChecker()
        checker.from_fen(FULL_INIT_FEN)
        checker.dump()
        
        print checker.move_to_chinese((7,2),(4,2)) == u'炮二平五'
        print checker.move_to_chinese((1,2),(1,1)) == u'炮八退一'
        print checker.move_to_chinese((7,2),(7,6)) == u'炮二进四'
        print checker.move_to_chinese((7,7),(4,7)) == u'炮８平５'
        print checker.move_to_chinese((7,7),(7,3)) == u'炮８进４'
        print checker.move_to_chinese((6,3),(6,4)) == u'兵三进一'
        print checker.move_to_chinese((8,0),(8,1)) == u'车一进一'
        print checker.move_to_chinese((0,9),(0,8)) == u'车１进１'
        print checker.move_to_chinese((4,0),(4,1)) == u'帅五进一'
        print checker.move_to_chinese((4,9),(4,8)) == u'将５进１'
        print checker.move_to_chinese((2,0),(4,2)) == u'相七进五'
        print checker.move_to_chinese((5,0),(4,1)) == u'仕四进五'
        print checker.move_to_chinese((7,0),(6,2)) == u'马二进三'
        