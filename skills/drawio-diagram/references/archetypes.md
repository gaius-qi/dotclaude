# 图型定式

每种图一节：用在哪、看哪张样张、骨架坐标、关键调用、容易错在哪。先在 SKILL.md 的样张索引里定了类型，再只读这里对应的一节，Read 样张 PNG，`cat` 它的脚本。

目录：[布局图 · 三行定式](#布局图--三行定式) · [布局图 · 嵌套表](#布局图--嵌套表三行) · [布局图 · 逐行追值](#布局图--逐行追一个值) · [布局图 · 尺度条 + case](#布局图--尺度条--case) · [架构图 · 分层横排](#架构图--分层横排) · [全链路图 · 多面板](#全链路图--多面板) · [重试预算格子](#重试预算格子) · [生命周期箭带](#生命周期箭带) · [两级算法 + 公式](#两级算法--公式) · [前后对照](#前后对照两面板) · [流程图 / 状态图](#流程图--状态图) · [时序图](#时序图)

通用骨架：左侧行标签列 `rowlabel()` 在 x=20，内容从 x=170 起；行高 60～70，行距 110～190；盒子间距 10；画布宽 ≤ 1900（index.html 按 1700 宽显示，再宽 13 号字就读不清；`nydus-registry-chunk-group` 2220 宽 × 2260 高是样张里的上限，内容再多就按行拆成两张）。

## 布局图 · 三行定式

磁盘格式、内存布局、协议帧。样张 `erofs-image-layout` · `nydus-registry-blob` · `nydus-disk-bootstrap`（`examples.py` / `examples_nydus_layout.py`）。

- **字段行**（y=40）：头部结构体的关键字段按**声明顺序**，`row(40, [(name, '0x28 · 含义', 120) …], fill='orange', gap=8)`，`bold=False` 是 `row()` 默认。
- **条带行**（y≈265）：区域按**盘上真实顺序**，10px 间距；可选区域副标题 `if any` / `optional`，保留 / pad 灰。被同一基址寻址的一段套 `group(x, 250, w, 125, '', 'yellow-bg')`，说明用 `text(size=13, align='left')` 放层块**底部**（标题在左上会被落入的箭头穿过）。层块高 = 盒子 70 + 说明 26 + 边距。
- **寻址行**（y≈440）：小块 x 范围对齐上方区域，`brace(x1, x2, 425, label='addr = base × 4 KiB + id × 4')` 尖端朝上指向区域。嵌入的子结构（blob 里的 bootstrap）用 `brace(up=False)` 往下放大成它自己的条带。
- 字段 → 区域的箭头用 `elbow(field, region, y_k, label)`，y_k 逐条错开 20px（125、145、165…），**两行各有自己的顺序时允许交叉**，不改任何一行的顺序。横段被别的竖线穿过时 `pos` 把标签滑到空段。
- 先画条带（它决定 x），再回头定字段行和寻址行的坐标。

```python
d.rowlabel('Superblock\nkey fields', 40, w=120)
sb_cells = d.row(40, [(t, s, 120) for t, s in SB], fill='orange', gap=8)          # 结构体声明顺序
d.rowlabel('Image\nLayout', 270, h=70, w=120)
zone = d.group(170, 250, 1070, 125, '', 'yellow-bg')                                # 统一寻址的区域
d.text('inode-metadata zone · starts at meta_blkaddr × 4 KiB · nid = (offset − start) / 32', 180, 342, 1050, 26, size=13, align='left')
sb = d.box('Superblock', 280, 265, 150, 70, 'orange', sub='@1024 · 128 B')         # 盘上顺序
sx = d.box('Shared xattrs', 600, 265, 160, 70, 'yellow', sub='4 B aligned · if any')
d.elbow(sb_cells[5], zone, 125, '× 4 KiB · zone start', entry=(0, 0), pos=-0.49)   # 落到层块左上角
d.elbow(sb_cells[6], sx, 145, '× 4 KiB')                                            # 下一条错开 20px
d.brace(600, 760, 425, label='addr = xattr_blkaddr × 4 KiB + id × 4')
```

## 布局图 · 嵌套表三行

一个区域由多种表组成，每种表有表头 / 扩展 / 条目。样张 `nydus-registry-blobmeta`。

- 顶部先按三行定式画区域条带 + 公共表头字段；再对**每种表**三行：表头取值 / 扩展字段 / 条目字段，`rowlabel(size=13)`，表名加粗 `text(align='left')` 放三行上方 30px。
- 没有的部分放一个灰盒 `('no extension', '', 150, 'grey')`；最后一个哨兵条目也灰。
- 写成 `table(y, name, hdr, ext, entry)` 调 `row()` 循环，表与表之间 260px；不手排。

## 布局图 · 逐行追一个值

一次查找 / 一次读从输入到字节的每一步。样张 `nydus-registry-lookup`。

- 每行一个结构（输入 → 索引 → 表 → 数据区），`rowlabel()` 写结构名，行距 100～140。
- 行内被命中的那一格 `-strong` / 橙，其余家族色；行与行之间一条竖边 `edge(hit, next_hit, label='i = 1')` 标这一步算出的值；每行下方一句 13 号说明写算式。
- 需要按真实比例的行（blkaddr 条、stride 条）用固定比例：`x = 170 + 50 × blkaddr`，刻度 `rule(x, y1, y2, dashed=True)`。

## 布局图 · 尺度条 + case

一个算法在不同输入下怎么切 / 怎么关。样张 `nydus-registry-chunk-group`。

- 固定比例（100 px = 1 MiB）；阈值刻度 `rule(x, …, dashed=True)`，次刻度 `rule(…, faint=True)`（唯一允许的非黑描边）；盒子宽 ∝ 大小；关闭点 `rule(x, y - 10, y + 60, width=3)`。
- 每个 case 一行：加粗标题 ①②③ `text(align='left')`、格子、下方逐条 check 文字（每条 20px）、右侧橙色结果盒。写成 `case(y, title, chunks, checks, close_at, result)`。
- 后接一行 `hedge()` 串起来的流水线（payload → digest → compress → 判断），判断用黄 `box()` 写问句。

## 架构图 · 分层横排

组件分层、数据自上而下。样张 `dragonfly-preheat`（虚线框 + 层块混用：外层 Node / 集群用 `panel`，Node 内的 seed peer / dfdaemon 用 `group`）。

- 一层一行，左侧 `rowlabel()`，层的两种表达选一种不混用：**`frame`** 强调真实边界（Node / 集群 / Registry）：框高 110、盒子高 70、行距 180；**`group(..., 'blue-bg')`** Gregg 风格：层块高 100、盒子高 50、层距 140。
- 同层平级组件等宽等距；主组件宽盒子放右、辅助放左；命令 / 配置 `note()` 放图的上方或两侧，`dotted()` 引到对应盒子。

## 全链路图 · 多面板

一个请求 / 一份数据从 A 到 B 的完整路径，跨进程跨主机。样张 `nydus-dragonfly-dedup` · `nydus-dragonfly-arch` · `dragonfly-preheat` · `nydus-fuse-failover`（`examples_dragonfly.py`，`Diagram(font='avenir')`）。

- **面板** = 进程 / 主机 / 阶段：`panel(40, y, 1540, h, '标题')`，面板间空隙 70～80 给跨面板的边放标签；所有边从上方落入的面板，标题放左下 `bottom=True`。
- **层块** = 面板里的一个数据对象：`group(…, 'blob A', 'blue-bg')`、`group(…, 'task A · 副本 1', 'green-bg')`、`group(…, 'dfdaemon storage · /var/lib/dragonfly', 'yellow-bg')`，标题 = 对象名 + 关键参数。
- **格子** = 对象里的单元：`cell(label, x, y, w, h, fill)`，按真实顺序和相对大小排一行；有 = 家族色、没有 = 灰、被追 = `-strong`。格子里还有子格（piece 2 里的 4 个 zstd 帧）：外层 `frame()` 虚线、内层 `cell(size=12)`。
- **形状**按 SKILL.md「形状 = 含义」：请求 `io`、Registry `cloud`、缓存 `cyl`、文件 `doc`、digest / 状态 `hex`、fd / 压缩帧 `proc`。
- 格子 → 下一面板用 `elbow(src, dst, y)`，同一组多条平行边 y 逐条错开 8px，无标签；边标签只标状态转折（`miss`、`206 · 拼好的 4 MiB`、`∅ → 回源`、`is_finished ?`）。
- 右上角可放一个小子系统在面板外的层块里（Request SDK + `ring()` hashring，节点贴在环上，选中的 `-strong`）。
- 触发者 `pill('read()')` 可以骑在面板上边线上，表示来自面板外。

```python
d = Diagram(font='avenir')
d.panel(40, 20, 1540, 430, 'nydus daemon · blob A')
g2 = d.group(230, 80, 260, 100, 'g2', 'blue-bg')
cs = [d.cell(f'c{5 + i}', 240 + i * 50, 115, 40, 50, 'grey') for i in range(5)]           # 灰 = 还没取到
get = d.box('GET blob A · Range: bytes=8388608-12582911', 190, 370, 520, 60, 'green', sub='fetch_size 2', shape='io')
d.panel(40, 520, 1540, 470, 'Dragonfly seed peer')
reg = d.box('Registry · origin', 890, 880, 250, 80, 'red', sub='只回源 d4', shape='cloud')
d.elbow(g2, zstd2, 198)                                                                    # 格子 → 帧，无标签
d.edge(get, piece2, (.5, 1), (.4, 0), 'piece 2 未下载 → 逐 chunk group 查表', points=[(450, 475), (934, 475)], offset=(0, -10))
```

## 重试预算格子

错误处理 / 重试策略：一格一次尝试，从左到右耗尽。样张 `nydus-dragonfly-retry`。

- 一个策略一条 lane（层块），内容从左到右：触发 `pill()` → 请求 `box(shape='io')` → `frame('重试顺序')` 里的尝试格子（`box(shape='sq')`，副标题 `① 429`、`② 超时 · 换 peer`），等待 `shape='oval'` 黄，终点 `EIO` 灰。
- 格子下方 `brace(x1, x2, y, label='max_retries 1 · 立即换 peer')` 写这段预算来自哪个配置。
- 写成 `lane(y, title, fill, trigger, slots, braces)`，lane 高 215。

## 生命周期箭带

一个组件在另一个组件生命周期各阶段被调用了什么、做了什么。样张 `containerd-nydus-snapshotter`。

- 顶部一排 `box(shape='step')` 灰色阶段，宽度 ∝ 阶段里的调用数；每个阶段下一排 `box(shape='io')` 绿色 API chip（名字 · 参数，副标题写触发条件）。
- chip 中心 x 存 dict，所有竖线共用；从 chip 竖直落到下方面板的动作盒子（加粗动作 + 斜体效果副标题）；只碰记录的停在「记录带」`group(..., 'yellow-bg')` 上，碰存储 / 进程的穿过记录带落到下面的结构。
- 下方面板标题 `bottom=True`。决策用 `rhombus()`，返回路径的长绕行边可 `lstyle='curved=1;'`（全图仅此一例）。

## 两级算法 + 公式

调度 / 选择算法：候选 → 打分 → 选出 → 加权。样张 `dragonfly-arch`（`Diagram(font='avenir', math=True)`）。

- 上面板中心调度、下面板节点调度；候选池一排 `box(mono=True)` 小盒带分数副标题，`brace(up=False)` 选出 top N。
- 公式 `formula(tex, x, y, w, h)` 放右侧：权重公式一块、子项各一行（左 `text(bold=True)` 名字 + 右 `formula(fill=None)` 裸公式，行底 `group(..., 'yellow')`）。LaTeX 变量名 `\mathit{TotalScore}`。
- 比例条 `bar(x, y, 220, 22, frac, fill)` 画空闲带宽；结果一排 piece 用 parent 的颜色标归属，被选的几个 parent 在候选池、parents、piece 三行**同色**。

## 前后对照两面板

同一流程的第一次 / 之后、改前 / 改后。样张 `trace-layer`。

- 两个 `panel(..., 'First mount', 'record · PUT · build')` 上下排，同样的参与者放同样的位置，第二面板只画变化的边。
- 重复 N 次的请求画 3 条平行 `line()` + `text('N × GET Range')`，不画 N 条。
- 跨 piece 的归属 `tag('cg 0', x, y)` 贴在 piece 左上角；路径等标识符在说明文字里用 `d.code(ang('content/tasks/<task_id>'))`。

## 流程图 / 状态图

样张 `erofs-read-flow` · `trace-task-build` · `trace-task-state`。

- 自上而下或自左向右主干，分支向另一侧展开再汇回。开始 / 结束 `pill()` grey 160×50；步骤 `box()` blue 200×60（动作加粗 + 函数名斜体副标题）；判断 `rhombus()` yellow 170×100。行内流水线的判断用黄 `box()` 写问句，不用菱形。
- 步骤间距 100（顶到顶），分支列间距 280。判断出边标 `yes` / `no`（`是` / `否`）：向下的边 `offset=(±14, 0)`，向右的边 `hedge(q, p, 'yes')`。
- 汇回边显式 `points`，走盒子外侧进入目标盒子；循环回起点的边标循环变量（`next chunk group`）。
- 状态图：状态 `box()` 按家族着色，终态 `pill()` 灰，边标触发条件；一行主干 + 向下的失败分支。

## 时序图

样张 `erofs-ondemand-seq` · `trace-task-seq`。

- `seq(participants, CX, bottom)` 画参与者（180～200×50，按家族着色：应用红、VFS 黄、文件系统 / nydus 蓝、网络 / dfdaemon 绿）和生命线；中心间距 240～300，只画顶部一排。
- `msg(y, x1, x2, label, ret=)` 纵向间距 60；跨过其他生命线的长消息 `pos=±0.5` 把标签滑到相邻两条生命线之间。自调用 `selfcall(cx, y, label)` 占 40。
- 阶段分隔 `divider(y, x1, x2, 'next mount')`。不画激活条、底部不重复参与者。loop / alt 用 `frame(x, y, w, h, 'alt [条件]')`，框左边在第一条相关生命线左侧 ≥120px，上边在第一条消息标签上方 ≥30px。

```python
CX = [120, 360, 600, 840]; d.seq([('App', 'red'), ('VFS', 'yellow'), ('EROFS', 'blue'), ('nydusd', 'green')], CX, 720)
d.msg(130, CX[0], CX[1], 'read()'); d.msg(190, CX[1], CX[0], 'data', ret=True)
d.selfcall(CX[2], 240, 'decode · verify'); d.frame(500, 275, 520, 245, 'alt [cache miss]')
d.divider(560, 40, 920, 'next mount')
```
