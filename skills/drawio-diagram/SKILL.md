---
name: drawio-diagram
description: 用 draw.io 画简洁清新的技术图并输出 .drawio + PNG：架构图、全链路数据流图、磁盘/文件/协议布局图、流程图、时序图、状态图、重试策略图、生命周期图。风格是 Brendan Gregg perf-tools 式：白底黑细线、按子系统家族分的马卡龙浅色、形状即含义、组件名加粗、开放式箭头。只要用户提到画图、架构图、示意图、流程图、时序图、布局图、结构图、diagram、drawio、"帮我画一下"、"画个图说明"，或要把某个系统 / 流程 / 调用链 / 磁盘格式 / 重试策略 / 生命周期可视化（Dragonfly、nydus、EROFS、containerd 等），即使没点名 draw.io 也用这个 skill。
---

# drawio-diagram

三样东西分工：`scripts/dio.py` 是全部样式和画法的代码（不手写 style 字符串，缺什么先加进去）；`references/archetypes.md` 是每种图的骨架坐标和关键调用；`assets/` 是 24 张样张 PNG 和生成它们的 `examples*.py`。本文件只讲流程、交付、所有图共用的视觉语言和检查清单。

## 流程

1. **先拿权威来源。** 字段名、偏移、区域顺序、常量名、API 名全部来自头文件 / 官方文档 / 源码（`erofs_fs.h`、`nydus-format/src/blob/footer.rs`、design 仓库的 md），不凭记忆。在 `gen_<name>.py` 顶部 docstring 写明读了哪些仓库 @ commit、哪些文件；设计阶段尚未落代码的内容在图里标「设计」。
2. **只画一种图，类型由用户的话决定。** 用户点名了就画那种；没点名按内容选一种：讲结构或数据路径 → 架构 / 全链路 / 布局，讲先后顺序 → 时序，讲判断分支 → 流程，讲状态迁移 → 状态图。不要给一个主题默认配齐几种图，也不要在回复里罗列图类型让用户挑。
3. **查样张索引 → 读 `references/archetypes.md` 对应的一节 → Read 样张 PNG → 看它的脚本。** 脚本按 `# ===== N. <name> =====` 分节，`grep -n '^# ====' assets/examples_x.py` 找到行号后只 `sed -n` 那一节。列出元素：面板 / 层块、每个盒子及其形状、边界、箭头及其标签、要标注的命令 / 配置。先定坐标（10px 网格），再写 `gen_<name>.py`：`sys.path.insert(0, os.path.expanduser('~/.claude/skills/drawio-diagram/scripts'))`，`from dio import Diagram`，`d.out(dir, name)`。
4. **`python3 ~/.claude/skills/drawio-diagram/scripts/lint.py <name>.drawio`，再 Read PNG 过检查清单。** lint 抓机器能抓的（调色板、描边、箭头、填充预算、字体），眼睛只看标签落位、对齐、折行、形状含义。不合格改坐标重跑。
5. 交付 .drawio 和 .png 路径，一两句说明。不写长篇解释。

## 样张索引

| 图的类型 | 样张（`assets/<name>.png`） | 定式 | 脚本 |
|---|---|---|---|
| 磁盘 / 协议布局：字段 → 条带 → 寻址 | `erofs-image-layout` · `nydus-registry-blob` · `nydus-disk-bootstrap` | 布局图 · 三行定式 | `examples.py` · `examples_nydus_layout.py` |
| 单个对象的槽结构 / 块内放大 | `erofs-file-layout` · `erofs-dir-layout` | 布局图 · 三行定式 | `examples.py` |
| 嵌套表（表头 / 扩展 / 条目） | `nydus-registry-blobmeta` | 布局图 · 嵌套表 | `examples_nydus_layout.py` |
| 目录里的文件集 + 位图 | `nydus-disk-cache` | 布局图 · 三行定式 | `examples_nydus_layout.py` |
| 清单 → 层 → 文件（镜像组成） | `nydus-registry-image` | 布局图 · 三行定式 | `examples_nydus_layout.py` |
| 逐行追一个值（worked example） | `nydus-registry-lookup` | 布局图 · 逐行追值 | `examples_nydus_layout.py` |
| 尺度条 + 算法分支 case | `nydus-registry-chunk-group` | 布局图 · 尺度条 + case | `examples_nydus_layout.py` |
| 组件分层架构 | `dragonfly-preheat` | 架构图 · 分层横排 | `examples_dragonfly.py` |
| 全链路数据流 · 多面板 + 层块 + 格子 | `nydus-dragonfly-dedup` · `nydus-dragonfly-arch` · `nydus-fuse-failover` | 全链路图 · 多面板 | `examples_dragonfly.py` |
| 重试 / 错误处理策略 | `nydus-dragonfly-retry` | 重试预算格子 | `examples_dragonfly.py` |
| 生命周期阶段 × API × 动作 | `containerd-nydus-snapshotter` | 生命周期箭带 | `examples_dragonfly.py` |
| 调度 / 选择算法 + 公式 | `dragonfly-arch` | 两级算法 + 公式 | `examples_dragonfly.py` |
| 前后对照（first / next） | `trace-layer` | 前后对照两面板 | `examples_trace.py` |
| 流程图 / 状态图 | `erofs-read-flow` · `trace-task-build` · `trace-task-state` | 流程图 / 状态图 | `examples.py` · `examples_trace.py` |
| 时序图 | `erofs-ondemand-seq` · `trace-task-seq` | 时序图 | `examples.py` · `examples_trace.py` |
| 文件格式小图 | `trace-task-format` | 布局图 · 三行定式 | `examples_trace.py` |

## 交付约定

- 每张图三个文件放同一目录：`<name>.drawio`、`<name>.png`（2x）、`gen_<name>.py`（改图就改脚本重跑）。一个主题多张图共用一个 `gen_<topic>.py`，并用 `dio.write_index(path, title, intro, items)` 生成 `index.html`。
- 一张图讲一件事。超过 4 行 / 4 层就拆成多张同类型的图，不是顺手补一张别的类型。
- 图内文字语言跟用户要求；没说就跟用户提问的语言。专有名词（函数名、字段名、命令）保持原文。
- **名字用读者认识的那个，且全套图一致。** 盘上字段用头文件里的名字（`i_u.startblk` 不是废弃的 `raw_blkaddr`）；结构体名写盘上结构；盒子名和说明文字里不缩写（永远 `chunk group`）；只有放不下全称的格子、tag、条目行可以用短式（`cg 0`、`g2`、`c4`），前提是全称在同一张图里出现过；同一区域每张图同名。
- 版本迭代的图在 docstring 末尾记一行「版本 N：改了什么、为什么」，让下次改图的人知道哪些方案试过被否了。

## 视觉语言

### 形状 = 含义

默认圆角盒子是「组件 / 动作」，名字加粗。换形状就是在说这是另一类东西，名字不加粗：

| `shape=` | 含义 | 例 |
|---|---|---|
| `sq`（`cell()`） | 数据单元：字节区间、piece、slot、fd、队列项、表条目 | `piece 0` · `c4` · `req 41 READ` · `slot 0 · 39` |
| `cloud` | Registry / origin / 系统外部 | `Registry · origin` |
| `io` 平行四边形 | 请求、API 调用、消息 | `GET blob A · Range` · `Preheat` · `Prepare · 每层` |
| `cyl` 圆柱 | 缓存、存储、磁盘镜像 | `nydus cache` · `cache/` · `EROFS 镜像` |
| `doc` 文档 | 一个落盘文件 | `bootstrap` · `image.boot` · `blob meta` |
| `hex` 六边形 | digest、索引记录、状态标记 | `d2 → B` · `piece 1 · finished ∅` · `Serving` |
| `proc` 带边条 | 压缩帧、fd / 句柄 | `zstd(g2)` · `fd 7 · /dev/fuse` |
| `step` 箭带 | 生命周期阶段 | `PullImage → CreateContainer → …` |
| `oval` 椭圆 | 等待 / 延迟 | `等 6h–12h` |
| `pill()` | 开始 / 结束 / 触发者 / 终态 | `read()` · `EIO` · `evicted` |
| `rhombus()` | 流程图里的判断 | `pieces local?` |

容器两种：`panel()` 虚线框 = 真实边界（进程 / 主机 / 阶段；嵌套的用 `size=14` 小标题），`group()` 填色层块 = 一个数据对象或一层（blob、task、表、Node 内的层）。`frame()` 单独用作内嵌格子的虚线外框或 `alt [...]`。

### 颜色 = 子系统家族

| 家族 | 盒子 | 层块 | 强调 | 用于 |
|---|---|---|---|---|
| 蓝 | `blue` | `blue-bg` | `blue-strong` | 存储、文件系统、数据块、数据路径、nydus / FUSE |
| 绿 | `green` | `green-bg` | `green-strong` | 网络、传输、P2P、Dragonfly task / piece / seed peer、请求 |
| 黄 | `yellow` | `yellow-bg` | `orange` | 计算、调度、元数据、表、journal；橙给头部 / digest / 被追的那格 |
| 红 | `red` | `red-bg` | — | 应用层、用户进程、containerd、Registry、origin |
| 青 | `cyan` | `cyan-bg` | `mint` | 内核队列、驱动、固件、基础层 |
| 灰 | `grey` | — | — | 中性，以及**缺席 / 待定**：hole、未下载、in flight、`∅`、`…`、落选的候选 |

**三档语义**：灰 = 还没有，家族色 = 有，`-strong` / 橙 = 正在被追的那一个。被追的对象在全图每一行同一个强调色。**预算**：一张图家族色 ≤5 种，强调色 ≤2 个（层块底色和注释框不计），超了就把同家族的强调降回普通色。`lint.py` 会数。

`note(kind=)` 注释框：`grey` 观测命令，`green` 静态配置 / 文件，`pink` 构建 / 调优 / 追踪。所有文字、描边、箭头黑色；唯一例外是尺度次刻度 `rule(faint=True)`。

### 文字

- 盒子名加粗 14，副标题斜体 12（`sub=`），并列项用 `·` 不用逗号；状态和序号写副标题：`finished · 8 MiB`、`① 429`、`ready`、`miss`。
- 标识符（fd、req、cN、slot、字节区间）等宽 12：`cell()` 已设；别处 `box(mono=True, size=12)`。说明文字里的路径用 `d.code(ang('<path>'))`。
- 面板标题 16 加粗（`panel()`）；行标签 14 加粗（`rowlabel()`）；层块标题 13 加粗左上；边标签 13；说明 `text(size=13, align='left')` 放被说明的行正下方。
- 命令 / 工具 / 配置键放 `note()`，`dotted()` 引线水平或竖直到被注释的盒子，离盒子 ≥40px。公式 `Diagram(math=True)` + `formula()`，变量名 `\mathit{…}`，写公式不写散文。
- 标签是 HTML：尖括号用 `ang()`；`<sha256 0>` 里的空格用 `&#160;` 防折行。长标识符不会在中间折行，放不下就加宽盒子（100→120、120→160）或挪到副标题。
- 字体一套图选一种：默认 Trebuchet MS + Courier New；格子多、标识符多的全链路图用 `Diagram(font='avenir')`（Avenir Next + Menlo）。

### 线与标签落位

- 盒子描边 1.5px；虚线框 1px `4 4`；注释框和引线 1px `1 3`。箭头直线、开放式 V 形；请求 / 同步实线，返回 / 异步 / 「同时也发给」虚线，双向 `both=True`。重复 N 次画 3 条平行 `line()` + `N × …` 文字。
- 拐弯显式给坐标：`elbow(src, dst, y)` 画 ⊐ 形，`edge(points=[…])` 画其他折线，禁止 `orthogonalEdgeStyle`；长绕行 `rounded=True`。exit / entry 落在同一 x 或 y 上，宽盒子用小数对齐窄盒子中心（`entry=(0.2115, 0)`）。
- **标签只能落在两个形状之间的空白里**，不压任何边、框线、箭头头部：竖直边标签在线右侧 `offset=(24~45, 0)`；水平边 `hedge()` 浮在线上 6px，两盒子间距 ≥90 才放标签；长边用 `pos` 滑到空段；时序图消息自带白底。
- **两行各有自己的顺序时允许箭头交叉，不改任何一行的顺序**：`elbow()` 的 y 逐条错开 8～20px，标签 `offset=(0, -10)` 浮在自己那段横线上。
- 多数边不要标签。全链路图一个面板到下一个面板只标 1～2 条状态转折（`miss`、`∅ → 回源`），其余靠形状和位置说明。
- `brace(x1, x2, yc, up, label=)` 花括号 = 放大看 / 归组，尖端指向被放大的对象，caption 在开口一侧。

## dio.py 速查

| 类别 | 调用 |
|---|---|
| 新建 | `Diagram(font='trebuchet'|'avenir', math=False)` |
| 盒子 | `box(title, x, y, w, h, fill, sub=, bold=, shape=, mono=, size=, align=)` · `cell(label, x, y, w, h, fill, sub=)` · `row(y, [(title, sub, w[, fill])…], x=170, fill=, gap=10)` · `pill()` · `rhombus()` · `tag(label, x, y)` · `bar(x, y, w, h, frac, fill)` · `ring(cx, cy, r)` |
| 容器 | `panel(x, y, w, h, title, sub=, bottom=, size=16)` · `group(x, y, w, h, label, 'blue-bg')` · `frame(x, y, w, h, label, solid=)` |
| 文字 | `rowlabel(label, y, h=60, w=130)` · `text(label, x, y, w, h, bold=, size=, align=)` · `note(text, x, y, w, h, kind=)` · `formula(tex, x, y, w, h, fill=)` · `Diagram.code(s)` · `ang(s)` |
| 边 | `edge(src, dst, exit, entry, label, both=, dashed=, points=, pos=, offset=, rounded=)` · `hedge(src, dst, label)` · `elbow(src, dst, y, label, exit=, entry=, pos=)` · `dotted(src, dst, exit, entry)` · `line(x1, y1, x2, y2, label, dashed=, arrow=)` · `rule(x, y1, y2, dashed=, width=, faint=)` · 标签位置 `**ABOVE` / `**BELOW` |
| 时序 | `seq(participants, cx, bottom)` · `msg(y, x1, x2, label, ret=, pos=)` · `selfcall(cx, y, label)` · `divider(y, x1, x2, label)` |
| 输出 | `out(dir, name)` · `save(path)` · `Diagram.export(drawio, png)` · `dio.write_index(path, title, intro, items)` · `d.at(id, fx, fy)` 取盒子上一点的绝对坐标 |

exit / entry 是盒子边上的比例坐标：`(0.5, 0)` 上边中点，`(0.5, 1)` 下边中点，`(0, .5)` 左边中点，`(1, .5)` 右边中点。

## 检查清单（lint 过了再看 PNG）

1. 每个边标签四周都是空白，没压任何线或边；注释框文字没换行。
2. 所有箭头竖直或水平，拐点直角（或 `rounded=True` 圆角）。
3. 同行盒子等高、顶边对齐；同列盒子中心对齐；格子按真实顺序和相对大小。
4. 层块 / 面板与内容间距 20，框之间不贴边；面板标题没被边穿过。
5. 形状和含义一致：Registry 是云、请求是平行四边形、文件是文档、缓存是圆柱；同一类东西没有一处圆角一处直角。
6. 强调色全图指同一个东西；灰只用于缺席 / 待定 / 中性。
7. 没有文字顶到或冲出盒子边；副标题不超过 2 行。
8. 每个字段名、常量名、结构体名都能在第 1 步的来源里 grep 到；同一区域各张图同名；没有缩写。

## 导出

`d.out(dir, name)` / `Diagram.export()` 调用 `drawio` 或 `/Applications/draw.io.app/Contents/MacOS/draw.io`，等价于 `draw.io -x -f png -s 2 -b 20 -o out.png in.drawio`。没有 draw.io 时只交付 .drawio，说明用 https://app.diagrams.net 打开。`Diagram(math=True)` 写入 `math="1"`，导出时渲染 MathJax。
