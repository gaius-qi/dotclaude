---
name: drawio-diagram
description: 用 draw.io 画简洁清新的技术图：架构图、全链路数据流图、流程图、时序图、状态图、磁盘/文件系统/协议布局图、重试与生命周期图，输出 .drawio 源文件和 PNG。风格参考 Brendan Gregg 的 Linux perf tools 图：白底、黑色细描边、按子系统家族分的马卡龙浅色填充（蓝=存储、绿=网络、黄=计算、红=应用、灰=缺席/待定）、虚线面板 + 填色层块、形状即含义（云=Registry、平行四边形=请求、圆柱=缓存、文档=文件、六边形=digest/状态、箭带=生命周期阶段）、组件名加粗、副标题斜体、开放式 V 形箭头、花括号放大、等宽字体虚线注释框标命令、MathJax 公式。只要用户提到画图、架构图、示意图、流程图、时序图、布局图、结构图、diagram、drawio、"帮我画一下"、"画个图说明"、把某个系统/流程/调用链/磁盘格式/重试策略/生命周期可视化（Dragonfly、nydus、EROFS、containerd 等），即使没点名 draw.io 也用这个 skill。
---

# drawio-diagram

## 样张索引（画之前先看）

每次画图先在这张表里找最像的类型，Read 它的 PNG，`cat` 生成它的脚本，照着写。所有样张都由 `assets/examples*.py` 生成，改样张就改脚本重跑。

| 图的类型 | 样张（`assets/<name>.png`） | 脚本 |
|---|---|---|
| 布局图 · 字段行 → 条带行 → 寻址行 | `erofs-image-layout` · `nydus-registry-blob` · `nydus-disk-bootstrap` | `examples.py` · `examples_nydus_layout.py` |
| 布局图 · 单个对象的槽结构 / 块内放大 | `erofs-file-layout` · `erofs-dir-layout` | `examples.py` |
| 布局图 · 嵌套表（表头 / 扩展 / 条目 三行定式） | `nydus-registry-blobmeta` | `examples_nydus_layout.py` |
| 布局图 · 目录里的文件集 + 位图 | `nydus-disk-cache` | `examples_nydus_layout.py` |
| 清单 → 层 → 文件（镜像组成） | `nydus-registry-image` | `examples_nydus_layout.py` |
| 逐行追一个值（worked example） | `nydus-registry-lookup` | `examples_nydus_layout.py` |
| 尺度条 + 算法分支 case | `nydus-registry-chunk-group` | `examples_nydus_layout.py` |
| 全链路图 · 多面板 + 层块 + 格子 | `nydus-dragonfly-dedup` · `nydus-dragonfly-arch` · `dragonfly-preheat` · `nydus-fuse-failover` | `examples_dragonfly.py` |
| 两级算法 + 公式 | `dragonfly-arch` | `examples_dragonfly.py` |
| 重试预算 / 尝试格子 | `nydus-dragonfly-retry` | `examples_dragonfly.py` |
| 生命周期箭带 + API chip + 动作 | `containerd-nydus-snapshotter` | `examples_dragonfly.py` |
| 前后对照两面板（first / next） | `trace-layer` | `examples_trace.py` |
| 流程图 | `erofs-read-flow` · `trace-task-build` | `examples.py` · `examples_trace.py` |
| 时序图 | `erofs-ondemand-seq` · `trace-task-seq` | `examples.py` · `examples_trace.py` |
| 状态图 / 文件格式小图 | `trace-task-state` · `trace-task-format` | `examples_trace.py` |

用 `scripts/dio.py` 生成 XML，所有样式常量都在里面，不要手写 style 字符串；需要新形状先加到 `dio.SHAPE`，再在这里登记含义。

## 流程

1. **先拿权威来源，再画。** 磁盘格式、协议、API、内核结构这类图，字段名、偏移、区域顺序、常量名全部以头文件 / 官方文档 / 工具源码为准（如 `erofs_fs.h`、`nydus-format/src/blob/footer.rs`、erofs-utils 的分配顺序），不凭记忆。在 `gen_<name>.py` 顶部 docstring 写明读了哪几个仓库 @ 哪个 commit、哪些文件、采用的顺序；设计阶段尚未落代码的内容在图里标「设计」。
2. 判断图类型，查样张索引，Read 样张 PNG + `cat` 脚本。列出元素：面板 / 层块、每个盒子及其形状、边界、箭头及其标签、需要标注的命令 / 配置。
3. 先定坐标（10px 网格），再写 `gen_<name>.py`：`sys.path.insert(0, '<skill>/scripts')` 后 `from dio import Diagram`，`save()` + `Diagram.export()`。
4. Read 导出的 PNG 逐项过「检查清单」，不合格改坐标重导。
5. 交付 .drawio 和 .png 路径，一两句说明。不写长篇解释。

## 交付约定

- 每张图三个文件放同一目录：`<name>.drawio`（源）、`<name>.png`（2x 导出）、`gen_<name>.py`（生成脚本，改图就改脚本重跑）。一个主题多张图共用一个 `gen_<topic>.py`，并配一个 `index.html`（标题 + 来源一行 + 每张图一个 `<h3>` 一段说明一个 `<img>`）。
- 图内文字语言跟用户要求；没说就跟用户提问的语言。中英混排时专有名词（函数名、字段名、命令）保持原文。
- 一张图讲一件事。内容超过 4 行/4 层就拆成多张，用 index.html 拼起来给用户看。
- 交付前必须 Read 一次 PNG 过检查清单，不能只看 XML。
- **名字用读者认识的那个，且全套图一致。** 盘上字段用头文件里的名字（`i_u.startblk` 不是废弃的 `raw_blkaddr`）；结构体名写盘上结构（`erofs_inode_compact`），不写内存结构；不缩写（永远 `chunk group`，不写 `group`/`g`，样张里的 `gN`/`cN` 只在格子里当编号用）。同一区域在每张图里叫同一个名字（`inode-metadata zone`、`Data blocks`）。
- 版本迭代的图在 docstring 末尾记一行「版本 N：改了什么、为什么」，让下次改图的人知道哪些方案已经试过被否了。

## dio.py 速查

| 约定 | 调用 |
|---|---|
| 新建；换字体 / 开公式 | `Diagram()`；`Diagram(font='avenir')`；`Diagram(math=True)` |
| 组件盒子，标题加粗 + 斜体副标题 | `box(title, x, y, w, h, fill, sub=, bold=True, shape=, mono=, size=)` |
| 开始/结束胶囊 | `pill(label, x, y, w, h)` |
| 判断菱形（流程图） | `rhombus(q, x, y, 170, 100)` |
| 系统/进程/阶段面板（虚线框 + 左上加粗 16 标题） | `panel(x, y, w, h, '标题', sub=, bottom=)` |
| 纯虚线边界 / 实线外框 | `frame(x, y, w, h, label)`；`solid=True` |
| 填色层块（无边框，Gregg 风格） | `group(x, y, w, h, label, 'blue-bg')` |
| 命令/配置注释（等宽、点状框） | `note(text, x, y, w, h, kind='grey'|'green'|'pink')` + `dotted(src, dst, exit, entry)` |
| 行标签/说明文字 | `text(label, x, y, w, h, bold=, size=, align=)` |
| 公式块（MathJax） | `formula(tex, x, y, w, h, fill='yellow-bg')`；`fill=None` 裸公式 |
| 角标小 chip | `tag('cg 0', x, y)` |
| 比例条（空闲带宽、用量） | `bar(x, y, w, h, frac, fill)` |
| 放大/归组花括号 | `brace(x1, x2, yc, up=True)` |
| 竖直/任意箭头 | `edge(src, dst, exit, entry, label, both=, dashed=, points=, pos=, offset=)` |
| 水平箭头，标签浮线上 | `hedge(src, dst, label, both=)` |
| 绝对坐标线（时序图、尺度条） | `line(x1, y1, x2, y2, label, dashed=, arrow=, lstyle=)` |
| 时序图自调用 | `selfcall(cx, y, label)` |
| 保存 / 导出 | `save(path)` / `Diagram.export(drawio, png)` |

exit/entry 是盒子边上的比例坐标：`(0.5, 0)` 上边中点，`(0.5, 1)` 下边中点，`(0, .5)` 左边中点，`(1, .5)` 右边中点。

## 形状 = 含义

默认圆角盒子是「组件 / 动作」。换形状就是在说这是另一类东西，全套图一致：

| `shape=` | 含义 | 例 |
|---|---|---|
| `sq` 直角 | 字节区间、cell、piece、slot、表条目、队列项 | `piece 0`、`c4`、`req 41 READ`、`slot 0 · 39` |
| `cloud` | Registry / origin / 系统外部 | `Registry · origin` |
| `io` 平行四边形 | 请求、API 调用、消息 | `GET blob A · Range`、`Preheat`、`Session Transfer`、snapshotter 的 `Prepare · 每层` |
| `cyl` 圆柱 | 缓存、存储、磁盘镜像 | `nydus cache`、`cache/`、`EROFS 镜像` |
| `doc` 文档 | 一个落盘文件 | `bootstrap`、`image.boot`、`blob meta`、`metadata 副本` |
| `hex` 六边形 | digest、索引记录、状态标记 | `d2 → B`、`piece 1 · finished ∅`、`Relinquished` / `Serving` |
| `proc` 带边条 | 压缩帧、fd / 句柄 | `zstd(g2)`、`fd 7 · /dev/fuse` |
| `step` 箭带 | 生命周期阶段 | `PullImage → CreateContainer → …` |
| `oval` 椭圆 | 等待 / 延迟 | `等 6h–12h` |

标识符文字（fd、req、cN、slot、字节区间）加 `mono=True, size=12`；形状盒子里的名字默认不加粗（`bold=False`），只有组件 / 动作 / 请求加粗。虚线椭圆表示 hashring（`box('', …, 'green-bg', style='shape=ellipse;…dashed=1')`，节点贴在环上）。

## 配色：颜色 = 子系统家族

来自 Linux perf tools 图。每个家族有 盒子色 / 层块底色 / 强调色 三档，同一家族的东西用同一家族的颜色。

| 家族 | 盒子 | 层块底色 | 强调 | 用于 |
|---|---|---|---|---|
| 蓝 | `blue` #CBDCFD | `blue-bg` | `blue-strong` #99B9FB | 存储、文件系统、数据块、数据路径、nydus / FUSE |
| 绿 | `green` #D9EACC | `green-bg` | `green-strong` #C3E4A9 | 网络、传输、P2P、Dragonfly task / piece / seed peer、请求 |
| 黄 | `yellow` #FFF0CD | `yellow-bg` | `orange` #FDD09B | 计算、调度、元数据、表、journal；橙色给头部 / digest / 被追的那一格 |
| 红 | `red` #FDD1D1 | `red-bg` | — | 应用层、用户进程、containerd、Registry、origin |
| 青/薄荷 | `cyan` #C1EDFD | `cyan-bg` | `mint` #D1F4EE | 内核队列、驱动、固件、基础层 |
| 灰 | `grey` #F5F5F5 | — | — | 开始/结束、保留区、**缺席 / 待定**：hole、未下载、in flight、`∅`、`…`、未命中的候选 |

**三档语义**：灰 = 还没有 / 不存在，家族色 = 有，`-strong` / 橙 = 正在被追的那一个（miss 的 chunk group、抽中的 seed peer、命中的 stride）。同一张图里被追的对象在每一行都用同一个强调色（scheduling 图里 Peer B/C/D 在候选池、parents、piece 三行同色）。

注释框 `note(kind=)`：`grey` 查看/观测命令，`green` 静态配置/文件，`pink` 构建/调优/追踪。
所有文字、描边、箭头黑色。**一张图盒子填充色不超过 5 种**（层块底色 `-bg` 和注释框不计），强调色 ≤2 个；超了就把同家族的强调色降回普通色。

## 字体

- 默认 `Trebuchet MS`（中文回落 PingFang）+ 注释 `Courier New`：布局图、流程图、时序图。
- `Diagram(font='avenir')` → `Avenir Next` + `Menlo`：全链路 / 架构图（Dragonfly 系列样张都是）。一套图只选一种。

## 文字

- **盒子里的重点加粗**：组件名、服务名、结构体名、步骤名、请求名是读者扫视的目标，`box()` 默认加粗 14。纯数据项（`lcluster 0`、`piece 2`、`…`）用 `bold=False`。
- 副标题斜体 12：`box('Superblock', ..., 'orange', sub='@1024 · 128 B')`。用 `·` 分隔并列项，不用逗号。状态写副标题：`finished · 8 MiB`、`① 429`、`ready`、`miss`、`in flight`；序号用 ①②③。
- 面板标题 `panel()` 加粗 16 左上；左侧行标签 14 加粗；边标签 13 常规；层块标题 13 加粗左上；说明文字 `text(size=13, align='left')` 放在被说明的行正下方。
- 命令、工具名、配置文件名、函数名放 `note()`：等宽加粗 12、点状虚线框，`dotted()` 引线到被注释的盒子，水平或竖直，不斜。
- 公式用 `Diagram(math=True)` + `formula()`，LaTeX 变量名 `\mathit{TotalScore}`，权重和子项各一块；文字说明写公式不写散文。
- 标签是 HTML：`note()` 会自动转义 `<arg>`，其他标签里要写尖括号用 `&lt;` `&gt;`；路径里的 `<sha256 0>` 用 `&#160;` 防折行。

## 线

- 盒子描边 1.5px；虚线边界框 1px `4 4`；注释框和引线 1px `1 3`。
- 箭头：直线、开放式 V 形。exit/entry 落在同一 x 或 y 上；宽盒子用小数对齐窄盒子中心，如 `entryX=0.2115`。拐弯显式给 `points`，禁止 `orthogonalEdgeStyle`。长距离绕行的边可加 `lstyle='rounded=1;arcSize=20;'` 圆角。
- 请求/同步实线，返回/异步/副本实线之外的「同时也发给」虚线，双向 `both=True`。重复 N 次的请求画 3 条平行细线 + `N × GET Range` 文字，不画 N 条。
- 花括号 `brace(x1, x2, yc, up)` 表示"放大看"或"归组"，尖端指向被放大的对象；括号下方 `text()` 写这一组的说明。

## 标签落位（最重要）

标签只能落在两个形状之间的空白里，不能压盒子边、框线、箭头头部或任何线。

- 竖直边：标签放线右侧 `offset=(24~45, 0)`，居中于空隙；穿过边界框时框间空隙 ≥70px。
- 水平边：用 `hedge()`，标签浮在线上方 6px；两盒子间距 ≥90px，短于 60px 的边不放标签。
- 长边或穿过其他线的边：`pos` 沿线滑到空处；时序图加 `labelBackgroundColor=#FFFFFF`。
- 注释框离被注释盒子 ≥40px，引线不穿过别的盒子。
- **两行各有自己的顺序时，箭头允许交叉，不为了不交叉去改任何一行的顺序。** 每条边走 `points=[(x_src, y_k), (x_dst, y_k)]` 的 ⊐ 形折线，y_k 逐条错开 8～20px（125、145、165…），标签用 `offset=(0, -10)` 浮在自己那段横线上方；横段被别的竖线穿过时用 `pos` 把标签滑到空段（`pos=-0.49` 靠源端）。
- 多数边不要标签：全链路图里一个面板到下一个面板只标 1～2 条关键边，其余靠形状和位置说明。

## 架构图 / 布局图

分层横排：一层一行，左侧加粗行标签，数据自上而下。层的两种表达，选一种不混用：

- **虚线框**（`frame`）：强调真实系统边界（Node / 集群 / Registry）。框高 110、盒子高 70、行距 180 → 框间空隙 70。
- **填色层块**（`group(x, y, w, h, '层名', 'blue-bg')`）：Gregg 风格，无边框、标题左上、同家族盒子嵌在里面。层块高 100、盒子高 50、层距 140。

布局图（磁盘格式、内存布局）三行定式，见 `erofs-image-layout.png` / `nydus-registry-blob.png`：

- **字段行**（顶部）：头部结构体的关键字段，按结构体声明顺序排，副标题写 `0x28 · 含义`。橙色，`bold=False`。
- **条带行**（中部）：按盘上真实顺序排区域，盒子 10px 间距，可选区域副标题写 `if any` / `optional`，保留/未用/pad 区灰色。被某个基址统一寻址的一段区域套一个 `group(..., '', 'yellow-bg')` 层块，说明文字用 `text()` 放层块**底部**，不用层块标题，标题在左上会被进入盒子的箭头穿过。层块高 = 盒子高 70 + 说明 26 + 边距 ≈ 125。
- **寻址行**（底部）：每组小块 x 范围对齐上方条带对应区域，`brace(up=True)` 指向它，公式 `text()` 放小块下方。嵌入的子结构（blob 里的 bootstrap）用 `brace(up=False)` 从条带往下放大成它自己的条带。

字段行 → 条带行的箭头按「标签落位」的交叉规则走。先画条带（它决定 x），再回头写字段行和寻址行的坐标。

共同规则：同层平级组件等宽等距；主组件宽盒子放右、辅助放左；命令/配置用 `note` 放图的上方或两侧，`dotted` 引到对应盒子。

```python
cells = [d.box(t, 170 + i * 128, 40, 120, 60, 'orange', bold=False, sub=s) for i, (t, s) in enumerate(SB)]  # 结构体顺序
zone = d.group(170, 250, 1070, 125, '', 'yellow-bg')                                                        # 统一寻址的区域
d.text('inode-metadata zone · starts at meta_blkaddr × 4 KiB · nid = (offset − start) / 32', 180, 342, 1050, 26, size=13, align='left')
sb = d.box('Superblock', 280, 265, 150, 70, 'orange', sub='@1024 · 128 B · nid 32–35')                     # 盘上顺序
d.edge(cells[5], zone, (.5, 1), (0, 0), '× 4 KiB · zone start', points=[(870, 125), (170, 125)], pos=-0.49, offset=(0, -10))
d.edge(cells[6], sx, (.5, 1), (.5, 0), '× 4 KiB', points=[(998, 145), (680, 145)], offset=(0, -10))       # 下一条错开 20px
d.brace(600, 760, 425, up=True); d.text('addr = xattr_blkaddr × 4 KiB + id × 4', 600, 515, 300, 20, size=13, align='left')
```

**嵌套表三行定式**（`nydus-registry-blobmeta`）：每种表三行 —— 表头取值 / 扩展字段 / 条目字段，左侧 13 号行标签，表名加粗放三行上方；没有的部分放一个灰盒 `no extension`。写成 `table(y, name, hdr, ext, entry)` 循环，不手排。

## 全链路图（多面板）

一张图讲一个请求 / 一份数据从 A 到 B 的完整路径，见 `nydus-dragonfly-dedup` / `nydus-dragonfly-arch` / `dragonfly-preheat` / `nydus-fuse-failover`。

- **面板** = 进程 / 主机 / 阶段：`panel(x, y, w, h, '标题')`，宽 1540，面板间空隙 70～80 给跨面板的边放标签。面板里主数据自上而下。所有 API 从上方落入的面板，标题放左下 `bottom=True`（snapshotter）。
- **层块** = 面板里的一个数据对象：`group(..., 'blob A', 'blue-bg')`、`group(..., 'task A · 副本 1', 'green-bg')`、`group(..., 'dfdaemon storage · /var/lib/dragonfly', 'yellow-bg')`。层块标题就是对象名 + 关键参数。
- **格子** = 对象里的单元，`shape='sq'`，按真实顺序和相对大小排一行：chunk group、piece、fd、slot、队列里的 req。有的填家族色、没有的填灰、被追的填 `-strong`。一个格子里还有子格（piece 2 里的 4 个 zstd 帧）：外层 `frame()` 虚线、内层小盒 `size=12`。
- **形状**按「形状 = 含义」表。
- 格子 → 下一个面板的边走 `points` 直角折线；同一组多条平行边 y 逐条错开 8px，无标签。
- 右上角可以放一个小子系统（Request SDK + hashring）在面板外的层块里。
- 边标签只标状态转折：`miss`、`206 · 拼好的 4 MiB`、`∅ → 回源`、`is_finished ?`。

## 其他定式

- **重试预算格子**（`nydus-dragonfly-retry`）：一个策略一条 lane（层块），从左到右 触发 pill → 请求 io → `frame('重试顺序')` 里的尝试格子，一格一次尝试，格子副标题 `① 429`、`② 超时 · 换 peer`，等待用 `oval`，终点 `EIO` 灰。格子下方 `brace(up=True)` + 文字写这一段预算来自哪个配置（`max_retries 1 · 立即换 peer`）。写成 `lane(y, title, fill, trigger, slots, braces)`。
- **生命周期箭带**（`containerd-nydus-snapshotter`）：顶部一排 `shape='step'` 灰色阶段，每个阶段下面一排 `shape='io'` 绿色 API chip，从 chip 竖直落到下方面板的动作盒子（加粗动作 + 斜体效果副标题），只碰记录的停在「记录带」层块上，碰存储 / 进程的穿过记录带落到下面的结构。chip 中心 x 存在 dict 里，所有竖线共用。
- **两级 / 算法 + 公式**（`dragonfly-arch`）：上面板中心调度、下面板节点调度；候选池一排 `mono=True` 小盒带分数副标题，`brace(up=False)` 选出 top N；公式 `formula()` 放右侧，权重公式一块、子项各一行（左加粗名字 + 右裸公式）；比例条 `bar()` 画空闲带宽；结果一排 piece 用 parent 的颜色标归属。
- **前后对照**（`trace-layer`）：两个面板 `panel(..., 'First mount', 'record · PUT · build')`，同样的参与者同样的位置，第二面板只画变化的边。跨 piece 的归属用 `tag('cg 0', x, y)` 贴在 piece 左上角。
- **逐行追一个值**（`nydus-registry-lookup`）：每行一个结构，左标签，行内被命中的那一格 `-strong` / 橙，行与行之间一条竖边标 `i = 1`、`entry 1`、`value 0`；每行下方一句 13 号说明写这一步的算式。
- **尺度条 + case**（`nydus-registry-chunk-group`）：固定比例（100 px = 1 MiB），`line(dashed)` 画阈值刻度，盒子宽 ∝ 大小，粗线（`strokeWidth=3`）标关闭点；每个 case 一行：加粗标题 ①②③、格子、下方逐条 check 文字、右侧橙色结果盒。写成 `case(y, title, chunks, checks, close_at, result)`。
- **环**（hashring）：虚线 `ellipse` + 四个小盒贴在环上，选中的两个 `-strong`，`tid → 第 1 个` 水平、`顺时针第 2 个` 折线。

## 流程图

自上而下或自左向右主干，分支向另一侧展开再汇回主干。

- 开始/结束 `pill()` grey 160×50；步骤 `box()` blue 200×60（标题加粗 + 函数名斜体副标题）；判断 `rhombus()` yellow 170×100，问句加粗。行内流水线（`payload → BLAKE3 → compress → ?`）的判断用 yellow `box()` 写问句，不用菱形。
- 步骤间距 100（顶到顶），分支列间距 280。
- 判断出边标 `yes`/`no`（中文 `是`/`否`）：向下的边 `offset=(±14,0)` 放线侧，向右的边 `hedge(q, p, 'yes')`。
- 汇回边显式给 `points`，走盒子外侧进入目标盒子，不穿越任何盒子；循环回起点的边标 `next chunk group`。
- 状态图同流程图，状态 `box()` 按家族着色，终态 `pill()` 灰，边标触发条件。

## 时序图

- 参与者 `box()` 180～200×50，按家族着色（应用红、VFS 黄、文件系统 / nydus 蓝、网络 / dfdaemon 绿），中心间距 240～300，只画顶部一排。
- 生命线 `line(cx, 90, cx, bottom, dashed=True, arrow=False, lstyle='')`。
- 消息 `line(x1, y, x2, y, label, dashed=is_return, lstyle='verticalAlign=bottom;labelBackgroundColor=#FFFFFF;')`，纵向间距 60；跨过其他生命线的长消息用 `pos=±0.5` 把标签滑到相邻两条生命线之间。
- 自调用 `selfcall(cx, y, '校验密码 · bcrypt')`，占 40px 高。
- 阶段分隔：一条横贯的虚线 `line(dashed, arrow=False)` + 居中 `pill('next mount')`。
- 不画激活条、底部不重复参与者。loop/alt 用 `frame(x, y, w, h, 'alt [条件]')`，框左边在第一条相关生命线左侧 ≥120px，框上边在第一条消息标签上方 ≥30px。

## 检查清单（看 PNG 时逐条过）

1. 每个边标签四周都是空白，没压任何线或边；注释框文字没换行。
2. 所有箭头竖直或水平，拐点是直角（允许 `arcSize=20` 圆角）。
3. 同行盒子等高、顶边对齐；同列盒子中心对齐；格子按真实顺序和相对大小。
4. 层块/边界框与内容间距 20，框之间不贴边；面板标题没被边穿过。
5. 组件名加粗、副标题斜体；盒子填充色 ≤5 种（`-bg` 和注释框不计），同家族同色，强调色 ≤2 个且全图指同一个东西；灰只用于缺席 / 待定 / 中性。
6. 形状和含义一致：Registry 是云、请求是平行四边形、文件是文档、缓存是圆柱；同一类东西没有一处圆角一处直角。
7. 没有文字顶到或冲出盒子边。HTML 只在空格处换行，`EROFS_NULL_ADDR`、`erofs_inode_chunk_index` 这种长标识符不会折行：加宽盒子（100→120、120→160）或把它挪到副标题；副标题折成 3 行的缩短用词。
8. 图里每个字段名、常量名、结构体名都能在第 1 步拿到的来源里 grep 到；同一区域各张图同名；没有缩写。

## 导出

`Diagram.export(drawio, png)` 调用 `drawio` 或 `/Applications/draw.io.app/Contents/MacOS/draw.io`，等价于：
```bash
draw.io -x -f png -s 2 -b 20 -o out.png in.drawio
```
没有 draw.io 时只交付 .drawio，并说明用 https://app.diagrams.net 打开。公式图需要 `math="1"`（`Diagram(math=True)` 已写入），导出时 draw.io 会渲染 MathJax。
