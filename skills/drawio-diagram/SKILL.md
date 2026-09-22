---
name: drawio-diagram
description: 用 draw.io 画简洁清新的技术图：架构图、流程图、时序图、磁盘/文件系统布局图、数据流图，输出 .drawio 源文件和 PNG。风格参考 Brendan Gregg 的 Linux perf tools 图：白底、黑色细描边、按子系统家族分的马卡龙浅色填充（蓝=存储、绿=网络、黄=计算、红=应用）、组件名加粗、副标题斜体、开放式 V 形箭头、花括号放大、等宽字体虚线注释框标命令。只要用户提到画图、架构图、示意图、流程图、时序图、布局图、结构图、diagram、drawio、"帮我画一下"、"画个图说明"、把某个系统/流程/调用链/磁盘格式可视化，即使没点名 draw.io 也用这个 skill。
---

# drawio-diagram

风格样张（都由 `assets/examples.py` 生成，先 `cat` 它照着写）：
- `assets/erofs-image-layout.png` 整体布局 + 寻址（字段行按结构体顺序、条带按盘上真实顺序、箭头交叉指向、层块内条带、地址公式）
- `assets/erofs-file-layout.png` 单个对象的槽结构 + 字段放大 + 寻址流
- `assets/erofs-dir-layout.png` 块内结构放大 + 查找链
- `assets/erofs-read-flow.png` 流程图
- `assets/erofs-ondemand-seq.png` 时序图

用 `scripts/dio.py` 生成 XML，所有样式常量都在里面，不要手写 style 字符串。

## 流程

1. **先拿权威来源，再画。** 磁盘格式、协议、API、内核结构这类图，字段名、偏移、区域顺序、常量名全部以头文件 / 官方文档 / 工具源码为准（如 `erofs_fs.h`、erofs.docs.kernel.org、erofs-utils 的分配顺序），不凭记忆。在 `gen_<name>.py` 顶部注释里写明读了哪几个来源和采用的顺序。
2. 判断图类型（架构 / 布局 / 流程 / 时序），列出元素：分层或分列、每个盒子、边界、箭头及其标签、需要标注的命令/配置。
3. 先定坐标（10px 网格），再写 `gen_<name>.py`：`sys.path.insert(0, '<skill>/scripts')` 后 `from dio import Diagram`，`save()` + `Diagram.export()`。
4. Read 导出的 PNG 逐项过「检查清单」，不合格改坐标重导。
5. 交付 .drawio 和 .png 路径，一两句说明。不写长篇解释。

## 交付约定

- 每张图三个文件放同一目录：`<name>.drawio`（源）、`<name>.png`（2x 导出）、`gen_<name>.py`（生成脚本，改图就改脚本重跑）。多张图共用一个 `gen_<topic>.py` 也行。
- 图内文字语言跟用户要求；没说就跟用户提问的语言。中英混排时专有名词（函数名、字段名、命令）保持原文。
- 一张图讲一件事。内容超过 4 行/4 层就拆成多张，用 index.html 拼起来给用户看。
- 交付前必须 Read 一次 PNG 过检查清单，不能只看 XML。
- **名字用读者认识的那个，且全套图一致。** 盘上字段用头文件里的名字（`i_u.startblk` 不是废弃的 `raw_blkaddr`，`EROFS_FT_DIR` 不是 VFS 的 `DT_DIR`）；结构体名写盘上结构（`erofs_inode_compact`），不写内存结构（`erofs_inode`）；文档里的 union 成员名（`rootnid_2b`）不如通用名（`root_nid`）时用通用名，偏移放副标题。同一区域在每张图里叫同一个名字（`inode-metadata zone`、`Data blocks`），不要一张叫 Metadata Area 另一张叫 zone。

## dio.py 速查

| 约定 | 调用 |
|---|---|
| 组件盒子，标题加粗 + 斜体副标题 | `box(title, x, y, w, h, fill, sub=, bold=True)` |
| 开始/结束胶囊 | `pill(label, x, y, w, h)` |
| 系统边界（虚线 1px） | `frame(x, y, w, h, label)`；`solid=True` 为实线 |
| 填色层块（无边框，Gregg 风格） | `group(x, y, w, h, label, 'blue-bg')` |
| 命令/配置注释（等宽、点状框） | `note(text, x, y, w, h, kind='grey'|'green'|'pink')` + `dotted(src, dst, exit, entry)` |
| 行标签/说明文字 | `text(label, x, y, w, h, bold=, size=, align=)` |
| 放大/归组花括号 | `brace(x1, x2, yc, up=True)` |
| 竖直/任意箭头 | `edge(src, dst, exit, entry, label, both=, dashed=, points=, pos=, offset=)` |
| 水平箭头，标签浮线上 | `hedge(src, dst, label, both=)` |
| 绝对坐标线（时序图） | `line(x1, y1, x2, y2, label, dashed=, arrow=)` |
| 时序图自调用 | `selfcall(cx, y, label)` |
| 保存 / 导出 | `save(path)` / `Diagram.export(drawio, png)` |

exit/entry 是盒子边上的比例坐标：`(0.5, 0)` 上边中点，`(0.5, 1)` 下边中点，`(0, .5)` 左边中点，`(1, .5)` 右边中点。

## 配色：颜色 = 子系统家族

来自 Linux perf tools 图。每个家族有 盒子色 / 层块底色 / 强调色 三档，同一家族的东西用同一家族的颜色。

| 家族 | 盒子 | 层块底色 | 强调 | 用于 |
|---|---|---|---|---|
| 蓝 | `blue` #CBDCFD | `blue-bg` | `blue-strong` #99B9FB | 存储、文件系统、数据块、数据路径 |
| 绿 | `green` #D9EACC | `green-bg` | `green-strong` #C3E4A9 | 网络、传输、P2P、外部 blob |
| 黄 | `yellow` #FFF0CD | `yellow-bg` | `orange` #FDD09B | 计算、调度、内存、元数据、硬件；橙色给最关键的头部（如 superblock） |
| 红 | `red` #FDD1D1 | `red-bg` | — | 应用层、用户侧、Registry |
| 青/薄荷 | `cyan` #C1EDFD / `mint` #D1F4EE | — | — | 驱动、固件、基础层 |
| 灰 | `grey` #F5F5F5 | — | — | 开始/结束、保留区、中性 |

注释框 `note(kind=)`：`grey` 查看/观测命令，`green` 静态配置/文件，`pink` 构建/调优/追踪。
所有文字、描边、箭头黑色。**一张图填充色不超过 5 种**（注释框的灰/绿/粉不计），强调色 ≤2 个；超了就把同家族的强调色降回普通色。

## 文字

- **盒子里的重点加粗**：组件名、服务名、结构体名、步骤名是读者扫视的目标，`box()` 默认加粗 14。纯数据项（"lcluster 0"、"..."）用 `bold=False`。
- 副标题斜体 12：`box('Superblock', ..., 'orange', sub='@1024 · 128 B')`。用 `·` 分隔并列项，不用逗号。
- 左侧行标签 14 加粗；边标签 13 常规；层块标题 13 加粗左上；说明文字 `text(size=13)`。
- 命令、工具名、配置文件名、函数名放 `note()`：等宽加粗 12、点状虚线框，`dotted()` 引线到被注释的盒子，水平或竖直，不斜。
- 字体 Trebuchet MS（中文回落 PingFang），注释 Courier New。
- 标签是 HTML：`note()` 会自动转义 `<arg>`，其他标签里要写尖括号用 `&lt;` `&gt;`。

## 线

- 盒子描边 1.5px；虚线边界框 1px `4 4`；注释框和引线 1px `1 3`。
- 箭头：直线、开放式 V 形。exit/entry 落在同一 x 或 y 上；宽盒子用小数对齐窄盒子中心，如 `entryX=0.2115`。拐弯显式给 `points`，禁止 `orthogonalEdgeStyle`。
- 请求/同步实线，返回/异步虚线，双向 `both=True`。
- 花括号 `brace(x1, x2, yc, up)` 表示"放大看"或"归组"，尖端指向被放大的对象。

## 标签落位（最重要）

标签只能落在两个形状之间的空白里，不能压盒子边、框线、箭头头部或任何线。

- 竖直边：标签放线右侧 `offset=(24~45, 0)`，居中于空隙；穿过边界框时框间空隙 ≥70px。
- 水平边：用 `hedge()`，标签浮在线上方 6px；两盒子间距 ≥90px，短于 60px 的边不放标签。
- 长边或穿过其他线的边：`pos` 沿线滑到空处；时序图加 `labelBackgroundColor=#FFFFFF`。
- 注释框离被注释盒子 ≥40px，引线不穿过别的盒子。
- **两行各有自己的顺序时，箭头允许交叉，不为了不交叉去改任何一行的顺序。** 每条边走 `points=[(x_src, y_k), (x_dst, y_k)]` 的 ⊐ 形折线，y_k 逐条错开 20px（125、145、165…），标签用 `offset=(0, -10)` 浮在自己那段横线上方；横段被别的竖线穿过时用 `pos` 把标签滑到空段（`pos=-0.49` 靠源端）。

## 架构图 / 布局图

分层横排：一层一行，左侧加粗行标签，数据自上而下。层的两种表达，选一种不混用：

- **虚线框**（`frame`）：强调真实系统边界（Node / 集群 / Registry）。框高 110、盒子高 70、行距 180 → 框间空隙 70。
- **填色层块**（`group(x, y, w, h, '层名', 'blue-bg')`）：Gregg 风格，无边框、标题左上、同家族盒子嵌在里面。层块高 100、盒子高 50、层距 140。

布局图（磁盘格式、内存布局）三行定式，见 `erofs-image-layout.png`：

- **字段行**（顶部）：头部结构体的关键字段，按结构体声明顺序排，副标题写 `0x28 · 含义`。橙色，`bold=False`。
- **条带行**（中部）：按盘上真实顺序排区域，盒子 10px 间距，可选区域副标题写 `if any` / `multi-dev`，保留/未用区灰色。被某个基址统一寻址的一段区域套一个 `group(..., '', 'yellow-bg')` 层块，说明文字用 `text()` 放层块**底部**，不用层块标题，标题在左上会被进入盒子的箭头穿过。层块高 = 盒子高 70 + 说明 26 + 边距 ≈ 125。
- **寻址行**（底部）：每组小块 x 范围对齐上方条带对应区域，`brace(up=True)` 指向它，公式 `text()` 放小块下方。

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

## 流程图

自上而下主干，分支向右展开再汇回主干。

- 开始/结束 `pill()` grey 160×50；步骤 `box()` blue 200×60（标题加粗 + 函数名斜体副标题）；判断 `box()` yellow，问句加粗，不用菱形。
- 步骤间距 100（顶到顶），分支列间距 280。
- 判断出边标 `是`/`否`：向下的边 `offset=(-14,0)` 放线左侧，向右的边 `hedge(q, p, '否')`。
- 汇回边显式给 `points`，走盒子外侧进入目标盒子右侧，不穿越任何盒子。

## 时序图

- 参与者 `box()` 180×50，按家族着色（应用红、VFS 黄、文件系统蓝、网络绿），中心间距 240，只画顶部一排。
- 生命线 `line(cx, 90, cx, bottom, dashed=True, arrow=False, lstyle='')`。
- 消息 `line(x1, y, x2, y, label, dashed=is_return, lstyle='verticalAlign=bottom;labelBackgroundColor=#FFFFFF;')`，纵向间距 60；跨过其他生命线的长消息用 `pos=±0.5` 把标签滑到相邻两条生命线之间。
- 自调用 `selfcall(cx, y, '校验密码 · bcrypt')`，占 40px 高。
- 不画激活条、底部不重复参与者。loop/alt 用 `frame(x, y, w, h, 'alt [条件]')`，框左边在第一条相关生命线左侧 ≥120px，框上边在第一条消息标签上方 ≥30px。

## 检查清单（看 PNG 时逐条过）

1. 每个边标签四周都是空白，没压任何线或边；注释框文字没换行。
2. 所有箭头竖直或水平，拐点是直角。
3. 同行盒子等高、顶边对齐；同列盒子中心对齐。
4. 层块/边界框与内容间距 20，框之间不贴边。
5. 组件名加粗、副标题斜体；填充色 ≤5 种，同家族同色，强调色 ≤2 个。
6. 没有文字顶到或冲出盒子边。HTML 只在空格处换行，`EROFS_NULL_ADDR`、`erofs_inode_chunk_index` 这种长标识符不会折行：加宽盒子（100→120、120→160）或把它挪到副标题；副标题折成 3 行的缩短用词。
7. 图里每个字段名、常量名、结构体名都能在第 1 步拿到的来源里 grep 到；同一区域各张图同名。

## 导出

`Diagram.export(drawio, png)` 调用 `drawio` 或 `/Applications/draw.io.app/Contents/MacOS/draw.io`，等价于：
```bash
draw.io -x -f png -s 2 -b 20 -o out.png in.drawio
```
没有 draw.io 时只交付 .drawio，并说明用 https://app.diagrams.net 打开。
