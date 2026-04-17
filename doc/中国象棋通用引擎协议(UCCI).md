
中国象棋通用引擎协议 (UCCI)

> **版本**：3.0  
> **发布**：2004年12月初稿，2007年11月修订

---

## 一、概述

### 协议目的

1. 使一个"可视化象棋软件"可以使用不同的"核心智能部件"（引擎），凡是遵循UCCI的引擎，都可以被该可视化象棋软件（界面）所调用
2. 针对所有遵循UCCI的引擎，都可以开发不同的界面，使其具有不同的功能

### 协议特点

- UCCI是模仿国际象棋的UCI来制定的
- UCCI是开放式的协议，并且具有UCI的所有特点
- 自诞生以来不断在发展和更新，但保持了对早期版本的兼容

### 版本改进历史

- **3.0版较2.3版改进**：建议取消option反馈中的repetition和drawmoves选项；将selectivity选项改成randomness；增加promotion选项
- **2.3版较2.2版改进**：建议采用"毫秒"作为唯一的时间单位

---

## 二、通讯方法

### 基本通讯机制

- 不管Windows还是UNIX平台，能被界面调用的引擎都必须是编译过的可执行文件
- 引擎跟界面之间通过"标准输入"和"标准输出"（即stdin和stdout）通道来通讯
- 界面向引擎发送的信息称为"**指令**"
- 引擎向界面发送的信息称为"**反馈**"
- 每条指令和反馈都必须以"回车"（'\n'）结束
- 引擎用缓冲方式发出反馈，每输出一行都必须用`fflush()`刷新缓冲区

### 界面设计要点

- Windows平台下可用`CreateProcess()`函数
- UNIX平台下可用`fork()`和`exec()`函数
- 重定向到一个输入管道和一个输出管道

---

## 三、引擎的状态

UCCI引擎启动后有三种状态：

### 状态1：引导状态

- 引擎启动时即进入引导状态
- 此时引擎只是等待和捕捉界面的输入
- 界面必须用`ucci`指令让引擎进入接收其他UCCI指令的**空闲状态**
- 收到`ucci`后，引擎完成初始化工作，输出`ucciok`进入空闲状态
- 如果收到其他非ucci指令，可以退出

### 状态2：空闲状态

- 该状态下引擎没有思考（几乎不占用CPU资源）
- 接收以下几类指令：
  - A. 设置引擎选项（`setoption`指令）
  - B. 设置引擎的内置局面（`position`和`banmoves`指令）
  - C. 让引擎思考（`go`指令）
  - D. 退出（`quit`指令）

### 状态3：思考状态

- 引擎收到`go`指令后即进入思考状态
- 以输出`bestmove`或`nobestmove`作为思考状态结束标志（回到空闲状态）
- CPU资源占用率接近100%
- 接收两类指令：
  - A. 中止思考（`stop`指令）
  - B. 改变思考方式（`ponderhit`指令）

### 重要注意事项

1. 引擎只有在接收到go指令后才开始思考。即便支持后台思考，输出着法后也不会自动进行。
2. bestmove的反馈不改变引擎的内置局面。界面让引擎走棋后需重新用position指令告知。
3. 计时对局中每次思考都必须用go指令设定时钟，回到空闲状态后时钟失效。
4. **批处理模式**适合重定向调试：

```
1: ucci
2: setoption batch true
3: position fen <fen_1>
4: go depth 10
5: position fen <fen_2>
6: go depth 10
7: quit
```

5. 思考状态下收到quit指令，引擎应终止思考并立即退出。
6. 空闲状态下收到stop指令，最好能反馈一个`nobestmove`。

---

## 四、着法和棋盘的表示

### 着法表示

- 用4个字符表示（简化的ICCS格式），如`h2e2`
- 即ICCS格式去掉中间横线并改成小写

### 局面表示

- 使用position指令把FEN串传给引擎
- FEN串不能完全反映局面信息，必须与后续着法结合使用

**示例对局**：

```
1. 炮二平五  炮8平5
2. 炮五进四  士4进5
```

发送给引擎的指令序列：

```
1: position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
2: position fen ... w - - 0 1 moves h2e2
3: position fen ... w - - 0 1 moves h2e2 h7e7
4: position fen ... b - - 0 2    ← 更换了FEN串（前一步是吃子着法）
5: position fen ... b - - 0 2 moves d9e8
```

---

## 五、指令和反馈详解

> 约定：**指令用红色**表示，**反馈用蓝色**表示

### 1. `ucci` — 引导状态指令

引擎启动后的第一条指令，通知引擎现在使用UCCI协议。

### 2. `id {name | copyright | author | user} <信息>` — 引导状态反馈

显示引擎版本号、版权、作者和授权用户。

```
id name ElephantEye 1.6 Beta          // 引擎版本号
id copyright 2004-2006 www.xqbase.com // 版权
id author Morning Yellow              // 作者
id user ElephantEye Test Team         // 授权用户
```

### 3. `option <选项> type <类型> [min <最大值>] [max <最大值>] [var <可选项>] [default <默认值>]` — 引导状态反馈

显示引擎所支持的选项。

| 选项类型 | 说明 |
|---------|------|
| label | 标签（非选项） |
| button | 指令 |
| check | 是或非 |
| combo | 多选项 |
| spin | 整数 |
| string | 字符串 |

**常用选项一览表**：

| 序号 | 选项名称 | 类型 | 默认值 | 说明 |
|------|---------|------|--------|------|
| (1) | usemillisec | check | - | 采用毫秒模式（建议始终采用） |
| (2) | batch | check | 关闭 | 批处理模式 |
| (3) | debug | check | 关闭 | 调试模式，输出更多info |
| (4) | ponder | check | 关闭 | 是否使用后台思考 |
| (5) | usebook | check | 启用 | 是否使用开局库 |
| (6) | useegtb | check | 启用 | 是否使用残局库 |
| (7) | bookfiles | string | - | 开局库文件名（分号分隔） |
| (8) | egtbpaths | string | - | 残局库路径 |
| (9) | evalapi | string | - | 局面评价API函数库文件 |
| (10) | hashsize | spin | 0 | Hash表大小(MB)，0=自动分配 |
| (11) | threads | spin | 0 | 线程数(SMP)，0=自动分配 |
| (12) | idle | combo | none | 处理器空闲状态(none/small/medium/large) |
| (13) | promotion | check | 关闭 | 允许仕(士)相(象)升变成兵(卒) |
| (14) | pruning | combo | large | 裁剪程度(none/small/medium/large) |
| (15) | knowledge | combo | large | 知识大小(none/small/medium/large) |
| (16) | randomness | combo | none | 随机性系数(none/small/medium/large) |
| (17) | style | combo | normal | 下棋风格(solid/normal/risky) |
| (18) | newgame | button | - | 设置新局或新局面 |

### 4. `ucciok` — 引导状态反馈

此后引擎进入空闲状态。

### 5. `isready` — 空闲/思考状态指令

检测引擎是否处于就绪状态。

### 6. `readyok` — 反馈

表明引擎就绪。

### 7. `setoption <选项> [<值>]` — 空闲状态指令

设置引擎参数。

```
setoption usebook false           // 不让引擎使用开局库
setoption randomness large         // 把随机性设成最大
setoption style risky              // 冒进的走棋风格
setoption loadbook                // 初始化开局库
```

### 8. `position {fen <FEN串> | startpos} [moves <后续着法列表>]` — 空闲状态指令

设置"内置棋盘"的局面。startpos等价于初始局面FEN串。moves列出该局面到当前局面的所有着法（用于防长打）。

### 9. `banmoves <禁止着法列表>` — 空闲状态指令

为当前局面设置禁手，解决长打问题。下次position指令后需重新设置。

### 10. `go [ponder | draw] <思考模式>` — 空闲状态指令

让引擎根据position设定的棋盘开始思考。

**思考模式**：

**(1) 深度限制**：`depth <深度> | infinite`
- infinite表示无限制思考；depth=0只给出静态评价并反馈nobestmove

**(2) 结点数限制**：`nodes <结点数>`

**(3) 时间限制**：
```
time <时间> [movestogo <剩余步数> | increment <每步加时>] 
[opptime <对方时间> [oppmovestogo <对方剩余步数> | oppincrement <对方每步加时>]]
```
- 时间单位默认秒（启用毫秒制时为毫秒）
- movestogo适用于时段制；increment适用于加时制

**ponder选项**：后台思考模式，时钟不走，直到ponderhit后才计时。与draw不可同时使用。

**draw选项**：向引擎提和。

### 11. `info <思考信息>` — 思考状态反馈

**(1) 时间和结点数**：`time <已花费时间> nodes <已搜索结点数>`
- NPS = 结点数÷时间，单位K

**(2) 深度和思考路线**：`depth <深度> [score <分值> pv <主要变例>]`
- 分值通常以一轻子(马或炮)=100分记
- 例：`info depth 6 score 4 pv b0c2 b9c7 c3c4 h9i7 c2d4 h7e7`

**(3) 当前着法**：`currmove <当前搜索着法>`

**(4) 提示信息**：`message <提示信息>`

### 12. `ponderhit [draw]` — 思考状态指令

告诉引擎后台思考命中，转入正常思考模式。

### 13. `stop` — 思考状态指令

中止引擎思考。发出后要等到bestmove或nobestmove才回到空闲状态。

### 14. `bestmove <最佳着法> [ponder <猜测着法>] [draw | resign]` — 思考状态反馈

显示思考结果，返回空闲状态。

- draw：提和或接受提和
- resign：认输

### 15. `nobestmove` — 思考状态反馈

一步也没计算（死局面）或仅静态评价。

### 16. `probe {fen | startpos} [moves]` — 获取Hash表中指定局面的信息（调试用）

### 17. `pophash [...]` — 输出Hash表中信息（调试用）

### 18. `quit` — 空闲状态指令，让引擎退出运转

### 19. `bye` — 反馈，通知界面引擎即将正常退出

---

## 六、用例——后台思考完整示例

### 第一阶段：开局分析

```
// 指令
ucci

// 反馈
id name ElephantEye Demo
option usemillisec type check default false
option usebook type check default true
ucciok

// 指令
setoption usemillisec true
setoption usebook false
position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
go time 300000 increment 0

// 反馈
info depth 6 score 4 pv b0c2 b9c7 c3c4 h9i7 c2d4 h7e7
info nodes 5000000 time 5000
bestmove b0c2 ponder b9c7
```

说明：引擎执红，5分钟包干时限，最佳着法为"马八进七"，猜测对手走"马２进３"。

### 第二阶段：后台思考

```
// 指令
position fen ... w - - 0 1 moves b0c2 b9c7
go ponder time 295000 increment 0

// 反馈
info depth 6 score 4 pv c3c4 h9i7 c2d4 h7e7 h0g2 i9h9
```

#### 情况(1)：后台思考命中（用户走了猜测着法）

```
// 指令
ponderhit

// 反馈
info nodes 15000000 time 15000
bestmove c3c4 ponder h9i7
```

#### 情况(2)：后台思考未命中（用户走了别的着法）

```
// 指令
stop

// 反馈
info nodes 10000000 time 10000
bestmove c3c4 ponder h9i7

// 重新设局思考
position fen ... w - - 0 1 moves b0c2 c6c5
go time 295000 increment 0
```

---

## 七、电脑象棋联赛要求

### 参赛引擎必须识别的指令

1. `ucci`
2. `position fen ... [moves ...]`
3. `banmoves ...`
4. `go [draw] time ... increment ... [opptime ... oppincrement ...]`
5. `quit`

### 必须能够反馈的信息

1. `ucciok`
2. `bestmove ... [draw | resign]`

### 建议实现的功能

| 功能 | 说明 |
|------|------|
| 支持毫秒制 | option usemillisec反馈 + setoption处理 |
| 支持认输和提和 | bestmove draw / bestmove resign |
| 支持stop指令 | 超时后立即反馈bestmove |

---

## 八、UCCI与UCI的区别

UCCI是从UCI移植过来的，作了以下改动：

| 区别 | 说明 |
|------|------|
| 增加`banmoves`指令 | 因中国象棋有长打作负规则 |
| 简化option格式 | 去掉name关键字：`option <选项> type ...` |
| 简化setoption格式 | 去掉value关键字：`setoption <选项> [<值>]` |
| 明确三种状态 | 引导状态、空闲状态、思考状态 |
| 简化时间传递 | `go time / opptime`代替`go wtime / btime` |
| 明确四种思考模式 | 深度/结点/时间/infinite |
| 明确FEN使用方式 | fen为最近一次吃子局面+moves后续着法 |
