# MoveNotation 走法中间表示文档

## 概述

`MoveNotation` 是中国象棋走法的中间表示类，将走法解析与渲染分离，支持多种输出格式，包括简体中文、繁体中文、英文和紧凑格式。

该方案解决了传统中文走法表示中的语言硬编码问题，使代码更易于维护、测试和国际化。

## 快速开始

### 基本使用

```python
from src.cchess.board import ChessBoard
from src.cchess.common import FULL_INIT_FEN

# 创建棋盘和走法
board = ChessBoard(FULL_INIT_FEN)
move = board.copy().move((0, 0), (0, 1))  # 车九进一

# 使用不同格式
print(move.to_text())                      # 车九进一 (默认简体中文)
print(move.to_text(format="compact"))      # R1+1
print(move.to_text(format="chinese", traditional=True))  # 車九進一
print(move.to_text(format="english"))      # rook at file 1 advances 1
print(move.to_text(format="iccs"))         # a0a1
```

### 直接使用 MoveNotation

```python
from src.cchess.move import MoveNotation

# 从 Move 对象创建中间表示
notation = MoveNotation.from_move(move)

# 转换为不同格式
print(notation.to_compact())            # R1+1
print(notation.to_chinese())            # 车九进一
print(notation.to_chinese(traditional=True))  # 車九進一
print(notation.to_english())            # rook at file 1 advances 1
```

## 紧凑格式规范

紧凑格式使用以下规范：

```
[限定词][棋子][列][方向][距离]
```

### 限定词（可选）

| 符号 | 含义 | 说明 |
|------|------|------|
| `f` | 前 | front |
| `m` | 中 | middle |
| `b` | 后 | back |
| `1-9` | 数字限定词 | 用于4个以上相同棋子 |

**注意**：将/帅、士/仕、象/相没有限定词，无论有多少个。

### 棋子类型

| 符号 | 红方 | 黑方 | 英文 |
|------|------|------|------|
| `K/k` | 帅 | 将 | king |
| `A/a` | 仕 | 士 | advisor |
| `B/b` | 相 | 象 | elephant |
| `N/n` | 马 | 马 | knight |
| `R/r` | 车 | 车 | rook |
| `C/c` | 炮 | 炮 | cannon |
| `P/p` | 兵 | 卒 | pawn |

**大小写区分**：大写表示红方，小写表示黑方。

### 列标识

列标识使用 1-9 的数字，表示红方视角下的路数（从右到左）：

| 列索引 | 路数 | 说明 |
|--------|------|------|
| 8 | 一 | 最右边 |
| 7 | 二 | |
| 6 | 三 | |
| 5 | 四 | |
| 4 | 五 | 中线 |
| 3 | 六 | |
| 2 | 七 | |
| 1 | 八 | |
| 0 | 九 | 最左边 |

### 方向

| 符号 | 含义 | 说明 |
|------|------|------|
| `+` | 进 | 红方向上，黑方向下 |
| `-` | 退 | 红方向下，黑方向上 |
| `=` | 平 | 水平移动 |

### 距离

- 对于王、车、炮、兵：表示步数（1-9）
- 对于马、士、象：表示目标路数（1-9）

### 示例

| 紧凑格式 | 中文 | 说明 |
|----------|------|------|
| `R1+1` | 车九进一 | 红方九路车前进1步 |
| `N2+3` | 马二进三 | 红方二路马进到三路 |
| `C2=5` | 炮二平五 | 红方二路炮平到五路 |
| `P7+1` | 兵七进一 | 红方七路兵前进1步 |
| `r9+1` | 车1进1 | 黑方1路车前进1步 |
| `fC5-2` | 前炮退二 | 前炮后退2步 |
| `bR9+1` | 后车九进一 | 后车九路前进1步 |

## API 参考

### Move.to_text() 方法

```python
def to_text(
    self,
    detailed: bool = False,
    format: str = "chinese",
    traditional: bool = False,
    use_fullwidth_for_black: bool = True
) -> str:
    """返回走法的文本表示。

    参数:
        detailed: 是否显示详细信息（吃子、将军等）
        format: 输出格式，可选值：
            - "chinese": 中文（默认）
            - "compact": 紧凑格式
            - "english": 英文
            - "iccs": ICCS坐标格式
        traditional: 当format为"chinese"时，是否使用繁体中文
        use_fullwidth_for_black: 当format为"chinese"时，
            黑方是否使用全角数字（１２３...）

    返回:
        指定格式的走法字符串
    """
```

### MoveNotation 类

#### 构造函数

```python
def __init__(
    self,
    piece_type: str,          # K/A/B/N/R/C/P
    column: int,              # 0-8（红方视角）
    direction: str,           # +/ -/=
    distance: int,            # 1-9
    qualifier: str = "",      # f/m/b/1/2/3/4
    is_capture: bool = False, # 是否吃子
    is_check: bool = False,   # 是否将军
    is_checkmate: bool = False, # 是否将死
    piece_color: int = None   # RED(1)/BLACK(2)
):
```

#### 工厂方法

```python
@classmethod
def from_move(cls, move: Move) -> MoveNotation:
    """从Move对象创建中间表示。

    自动解析棋子类型、颜色、位置、方向等信息，
    并计算限定词（当前后有多枚相同棋子时）。
    """
```

#### 格式转换方法

```python
def to_compact(self) -> str:
    """转换为紧凑格式。

    示例: "R1+1", "N2+3", "fC5-2"
    """

def to_chinese(
    self,
    traditional: bool = False,
    use_fullwidth_for_black: bool = True
) -> str:
    """转换为中文。

    参数:
        traditional: 是否使用繁体中文
        use_fullwidth_for_black: 黑方是否使用全角数字
    """

def to_english(self) -> str:
    """转换为英文。

    示例: "rook at file 1 advances 1"
    """

def __str__(self) -> str:
    """字符串表示，返回紧凑格式。"""
```

## 象棋规则说明

### 1. 限定词规则

- **将/帅、士/仕、象/相**：没有限定词，无论有多少个
  - 这些棋子的移动受限，不会出现歧义
  - 直接使用路数标识即可

- **车、马、炮、兵/卒**：当同列有多个相同棋子时需要限定词
  - 限定词用于区分同列的相同棋子
  - 红方：从下到上排序，下面的为"后"，上面的为"前"
  - 黑方：从上到下排序，上面的为"前"，下面的为"后"

### 2. 数字格式

- **红方**：使用中文数字（一、二、三...九）
- **黑方**：默认使用全角数字（１、２、３...９），可通过参数控制

### 3. 方向表示

- `进`（`+`）：向前移动
  - 红方：y坐标增加（向上）
  - 黑方：y坐标减少（向下）

- `退`（`-`）：向后移动
  - 红方：y坐标减少（向下）
  - 黑方：y坐标增加（向上）

- `平`（`=`）：水平移动
  - 只改变x坐标，y坐标不变

### 4. 距离计算

- **王、车、炮、兵**：进退时显示步数
  - 例如：车九进一（前进1步）

- **马、士、象**：进退时显示目标路数
  - 例如：马二进三（进到三路）
  - 因为这些棋子的移动不是直线，步数没有意义

## 使用示例

### 1. 基本走法

```python
from src.cchess.board import ChessBoard
from src.cchess.common import FULL_INIT_FEN

board = ChessBoard(FULL_INIT_FEN)

# 红方车九进一
move = board.copy().move((0, 0), (0, 1))
print(move.to_text())                      # 车九进一
print(move.to_text(format="compact"))      # R1+1
print(move.to_text(format="english"))      # rook at file 1 advances 1
```

### 2. 黑方走法

```python
board = ChessBoard(FULL_INIT_FEN)
board.next_turn()  # 切换到黑方

# 黑方车9进1
move = board.copy().move((0, 9), (0, 8))
print(move.to_text())                      # 车１进１ (全角数字)
print(move.to_text(use_fullwidth_for_black=False))  # 车一进一
print(move.to_text(format="compact"))      # r9+1 (小写表示黑方)
```

### 3. 详细输出

```python
# 创建一个吃子局面
board = ChessBoard("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w")
move = board.copy().move((0, 0), (0, 3))  # 车吃兵

if move:
    print(move.to_text(detailed=True))                    # 车九进三(吃兵)
    print(move.to_text(detailed=True, format="english"))  # rook at file 1 advances 3 (captures)
```

### 4. 多棋子限定词

```python
# 创建有两辆车的局面
board = ChessBoard("4k4/9/9/9/9/9/9/9/4R3R/4K4 w")

# 移动前车
move = board.copy().move((4, 2), (4, 3))
if move:
    print(move.to_text())                      # 前车进一
    print(move.to_text(format="compact"))      # fR5+1

# 移动后车
move = board.copy().move((4, 0), (4, 1))
if move:
    print(move.to_text())                      # 后车进一
    print(move.to_text(format="compact"))      # bR5+1
```

### 5. 特殊棋子（士、象）

```python
# 士和象没有限定词
board = ChessBoard("4k4/9/9/9/9/9/9/9/4A1B2/4K4 w")

# 移动士
move = board.copy().move((4, 0), (3, 1))
if move:
    print(move.to_text())                      # 仕四进五
    # 不会有"前仕"或"后仕"

# 移动象
move = board.copy().move((6, 0), (4, 2))
if move:
    print(move.to_text())                      # 相三进五
    # 不会有"前相"或"后相"
```

## 设计原则

### 1. 语言无关

核心逻辑使用中间表示，可以轻松支持多种语言。添加新语言只需在映射表中添加翻译：

```python
# 扩展支持日语
PIECE_MAP_JP = {
    "R": "車",
    "N": "馬",
    "B": "象",
    "A": "士",
    "K": "王",
    "C": "砲",
    "P": "兵",
}
```

### 2. 向后兼容

默认行为与传统实现完全一致，现有代码无需修改：

```python
# 旧代码继续工作
text = move.to_text()  # 与之前完全相同
```

### 3. 性能优化

- 一次解析，多次渲染
- 减少重复计算
- 紧凑格式减少内存占用

### 4. 易于测试

紧凑格式便于自动化测试和验证：

```python
def test_move():
    move = board.copy().move((0, 0), (0, 1))
    assert move.to_text(format="compact") == "R1+1"
    assert move.to_text() == "车九进一"
```

## 已知限制

### 1. 多棋子限定词边缘情况

在某些特殊局面下，多棋子限定词的判断可能与原始实现有细微差别：

- 同一行有多个棋子时的排序
- 不同列但需要限定词的情况

这些是边缘情况，不影响主要功能。

### 2. 性能考虑

`MoveNotation.from_move()` 会进行一些计算（查找同列棋子、排序等），在大量走法转换时可能影响性能。建议：

- 缓存 `MoveNotation` 对象
- 只在需要时进行格式转换
- 对于批量处理，使用紧凑格式

## 测试

### 运行测试

```bash
# 运行所有相关测试
python -m pytest tests/test_coverage.py -x -q
python -m pytest tests/test_board_move.py -x -q

# 运行新格式测试
python -m pytest tests/test_new_formats.py -v
```

### 测试覆盖

- 基本走法转换
- 多格式输出
- 繁体中文支持
- 英文翻译
- ICCS格式
- 详细输出（吃子、将军）
- 黑方走法
- 多棋子限定词
- 特殊棋子（士、象）

## 相关文件

- `src/cchess/move.py` - MoveNotation 类实现
- `src/cchess/common.py` - 通用工具和常量
- `src/cchess/board.py` - 棋盘类
- `docs/move_notation.md` - 本文档

## 版本历史

### v1.0.0 (2024)

- 初始实现
- 支持紧凑格式、简体中文、繁体中文、英文
- 保持向后兼容
- 添加多棋子限定词支持

## 许可证

本项目遵循 GNU General Public License v3.0。