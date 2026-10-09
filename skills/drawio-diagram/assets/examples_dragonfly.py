"""Dragonfly × nydus architecture / data-flow set · 7 figures · Avenir Next + Menlo (Diagram(font='avenir')).

Each figure is one or more dashed panels (a process or a host), filled groups inside (a blob, a task, a table), square
cells for bytes / pieces / slots, and a shape per kind of thing: cloud = Registry, parallelogram = request, cylinder =
cache, document = file, hexagon = digest / state, process = fd or compressed frame, chevron = lifecycle phase.
Grey = absent / pending / hole, family colour = present, -strong = the one being traced.

Sources (2026-09-22 … 23; every name is grep-able there):
  nydus v3 (code.byted.org/infcp/nydus c283e62f · 657c94a9 · feature/dragonfly-retry bd64008):
    nydus-format/src/blob/{mod,metadata,footer}.rs · nydus-storage/src/cache/local.rs (fetch_size cell, plan_chunk_group_window)
    nydus-backend/src/registry/{mod,policy,dragonfly,http}.rs (Range GET, SDK max_retries, policy::decide, PRIORITY 6/3)
    nydus-storage/src/prefetch.rs (QuotaExceeded → deferred · RESCHEDULE_DELAY 6h–12h) · nydus-config storage.fetch_size · DragonflyConfig
  dragonfly client main ada7179 (Rust dfdaemon): resource/{task,piece,parent_selector}.rs · grpc/dfdaemon_upload.rs ·
    dragonfly-client-storage content.rs (content/tasks/<task_id>) · metadata.rs (RocksDB cf task / piece) · MIN_PIECE_LENGTH 4 MiB
  dragonfly-client-request 1.4.0 / 1.7.2: selector.rs (VNodeHashRing 512 vnode/host · get_with_replicas) · retry.rs · errors.rs
  dragonfly main ead52d8b: pkg/idgen/task_id.go TaskIDV2ByBlobDigest · manager/job/preheat.go · scheduler/job/job.go (Preheat*) ·
    scheduler/scheduling/scheduling.go (15 → filter → EvaluateParents → 3) · evaluator_default.go (TotalScore / LoadQuality weights)
  containerd main 5152cb5: core/snapshots/proxy/proxy.go · core/unpack/unpacker.go · internal/cri/server/container_create.go ·
    core/metadata/snapshot.go · contrib/snapshotservice/service.go (10 RPCs)
  nydus-snapshotter main b4f6ed1: snapshot/{snapshot,process}.go · pkg/filesystem/fs.go · pkg/manager/daemon_adaptor.go · pkg/rafs/rafs.go
  nydus-fuse-failover: reconstructed from the hand-tuned nydus-fuse-failover.drawio (2026-09-22); names as in that figure.
Figures with design-stage content say so in the figure ("设计"); scores / bandwidth / piece owners are example numbers.
"""
import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from dio import Diagram
OUT = os.path.dirname(os.path.abspath(__file__)) + '/'
def out(d, name): d.save(OUT + name + '.drawio'); Diagram.export(OUT + name + '.drawio', OUT + name + '.png'); print(name)
F = dict(size=13, align='left')
LB = dict(offset=(0, -6), lstyle='verticalAlign=bottom;')

# ================= 1. chunk group dedup across images (nydus → seed peer) =================
d = Diagram(font='avenir')
d.panel(40, 20, 1540, 430, 'nydus daemon · blob A')
rd = d.pill('read()', 535, 25, 120, 40)
BANDS = [('g1 · ready', 60, 150, True, [(70, 130, 'c4')]), ('g2', 230, 260, False, [(240 + i * 50, 40, f'c{5 + i}') for i in range(5)]),
         ('g3', 510, 170, False, [(520, 150, 'c10')]), ('g4', 700, 210, False, [(710 + i * 50, 40, f'c{11 + i}') for i in range(4)]),
         ('g5', 930, 170, False, [(940, 150, 'c15')]), ('g6 · ready', 1120, 340, True, [(1130 + i * 50, 40, f'c{16 + i}') for i in range(6)])]
gb, c10 = [], None
for t, x, w, ready, chunks in BANDS:
    gb.append(d.group(x, 80, w, 100, t, 'blue-bg'))
    for cx, cw, ct in chunks:
        cid = d.box(ct, cx, 115, cw, 50, 'blue' if ready else 'grey', bold=False, shape='sq', mono=True)
        if ct == 'c10': c10 = cid
d.edge(rd, c10, label='miss', offset=(24, 0))

cell = d.group(170, 235, 565, 95, '', 'yellow-bg'); d.text('fetch_size cell · 4 MiB', 180, 302, 540, 24, **F)
PAY = [('zstd(g1)', 60, 110, 'd1'), ('zstd(g2)', 180, 160, 'd2'), ('zstd(g3)', 350, 110, 'd3'), ('zstd(g4)', 470, 140, 'd4'), ('zstd(g5)', 620, 110, 'd5'), ('zstd(g6)', 740, 160, 'd6')]
pc = [d.box(t, x, 250, w, 50, 'blue', sub=s, shape='proc', mono=True) for t, x, w, s in PAY]
GX = [135, 360, 595, 805, 1015, 1290]; PX = [115, 260, 405, 540, 675, 820]
for i, (g, p) in enumerate(zip(gb, pc)): d.edge(g, p, (.5, 1), (.5, 0), points=[(GX[i], 190 + 8 * i), (PX[i], 190 + 8 * i)])
d.brace(170, 735, 345, up=True)
get = d.box('GET blob A · Range: bytes=8388608-12582911', 190, 370, 520, 60, 'green', sub='附带 d2 · d3 · d4 · d5（设计）', shape='io')

d.panel(40, 520, 1540, 470, 'Dragonfly seed peer')
d.group(60, 565, 1400, 100, 'task A = blob A · piece 4 MiB', 'green-bg')
d.box('piece 0', 70, 600, 350, 50, 'green', shape='sq'); d.box('piece 1', 430, 600, 350, 50, 'green', shape='sq')
p2 = d.frame(790, 600, 360, 50, ''); d.box('piece 3', 1160, 600, 290, 50, 'green', shape='sq')
slots = [d.box(f'zstd(g{i})', 795 + (i - 2) * 90, 605, 80, 40, 'blue', bold=False, shape='proc', mono=True, size=12) for i in range(2, 6)]
d.edge(get, p2, (.5, 1), (.4, 0), 'piece 2 未下载 → 逐 chunk group 查表', points=[(450, 475), (934, 475)], offset=(0, -10))
d.edge(p2, get, (.15, 0), (.1, 1), '206 · 拼好的 4 MiB', dashed=True, points=[(844, 495), (250, 495)], offset=(0, 12))

tbl = d.group(60, 700, 1400, 110, 'Digest ↔ Chunk 表 · 全局 · 跨镜像 · digest → (task, offset, len)', 'yellow-bg')
cols = [d.box(t, 793 + i * 90, 735, 84, 60, 'orange', sub=s, shape='hex', mono=True) for i, (t, s) in enumerate([('d2', '→ B'), ('d3', '→ B'), ('d4', '∅'), ('d5', '→ C')])]
for s, c in zip(slots, cols): d.edge(s, c)

d.group(60, 860, 810, 100, 'task B · 镜像 Y 的 blob', 'green-bg')
for i in range(4): d.box(f'piece {i}', 70 + i * 200, 895, 190, 50, 'green', bold=False, shape='sq', style='align=left;spacingLeft=8;')
hb2 = d.box('d2', 395, 895, 50, 50, 'blue', bold=False, shape='sq', mono=True); hb3 = d.box('d3', 595, 895, 50, 50, 'blue', bold=False, shape='sq', mono=True)
reg = d.box('Registry · origin', 890, 880, 250, 80, 'red', sub='只回源 d4', shape='cloud')
d.group(1150, 860, 310, 100, 'task C · 镜像 Z 的 blob', 'green-bg')
d.box('piece 0', 1160, 895, 150, 50, 'green', bold=False, shape='sq', style='align=left;spacingLeft=8;')
bmc = d.box('blob meta', 1320, 892, 130, 56, 'orange', sub='末 piece 尾部', shape='doc')
hc5 = d.box('d5', 1225, 895, 50, 50, 'blue', bold=False, shape='sq', mono=True)
d.edge(cols[0], hb2, (.5, 1), (.5, 0), points=[(835, 815), (420, 815)])
d.edge(cols[1], hb3, (.5, 1), (.5, 0), points=[(925, 830), (620, 830)])
d.edge(cols[3], hc5, (.5, 1), (.5, 0), points=[(1105, 815), (1250, 815)])
d.edge(cols[2], reg, (.5, 1), (.5, 0), label='回源', offset=(-30, 0))
d.edge(bmc, tbl, (.5, 0), (.9464, 1), '下载完成 → 建表', dashed=True, offset=(-60, 0))
out(d, 'nydus-dragonfly-dedup')

# ================= 2. one request end to end: nydus → Request SDK hashring → seed peer storage =================
d = Diagram(font='avenir')
d.panel(40, 20, 1540, 480, 'nydus daemon · blob A')
rd = d.pill('read()', 685, 25, 120, 40)
d.group(50, 80, 990, 130, 'blob A', 'blue-bg')
WIN = [('fetch_size 0 · 0–4 MiB', 60, 220, True, [(70, 80, 'g1'), (160, 50, 'g2'), (220, 50, 'g3')]),
       ('fetch_size 1 · 4–8 MiB', 300, 180, True, [(310, 100, 'g4'), (420, 50, 'g5')]),
       ('fetch_size 2 · 8–12 MiB', 510, 280, False, [(520, 70, 'g6'), (600, 100, 'g7'), (710, 70, 'g8')]),
       ('fetch_size 3 · 12–16 MiB', 810, 220, False, [(820, 110, 'g9'), (940, 80, 'g10')])]
g8 = None
for t, x, w, ready, cgs in WIN:
    d.group(x, 110, w, 85, t, 'yellow-bg')
    for cx, cw, ct in cgs:
        cid = d.box(ct, cx, 140, cw, 40, 'blue' if ready else 'grey', bold=False, shape='sq', mono=True)
        if ct == 'g8': g8 = cid
d.edge(rd, g8, label='miss', offset=(24, 0))
d.brace(510, 790, 230, up=True)
get = d.box('GET blob A · Range: bytes=8388608-12582911', 390, 290, 520, 60, 'green', sub='fetch_size 2 · g6–g8 · X-Dragonfly-Use-P2P', shape='io')

d.group(1060, 180, 500, 290, 'Dragonfly Request SDK · 同进程', 'green-bg')
tid = d.box('task_id', 1070, 295, 150, 50, 'orange', sub='digest(blob A)')
d.hedge(get, tid, '同 task_id')
d.box('', 1330, 245, 150, 150, 'green-bg', style='shape=ellipse;perimeter=ellipsePerimeter;dashed=1;dashPattern=4 4;fixDash=1;')   # the hashring
d.text('hashring · 512 vnode / host', 1290, 448, 230, 20, size=12)
rn = d.box('seed peer C', 1360, 230, 90, 30, 'green-strong', bold=False)
d.box('seed peer A', 1435, 305, 90, 30, 'green', bold=False)
d.box('seed peer D', 1360, 380, 90, 30, 'green', bold=False)
rw = d.box('seed peer B', 1285, 305, 90, 30, 'green-strong', bold=False)
d.hedge(tid, rw, '第 1 个')
d.edge(tid, rn, (.5, 0), (0, .5), '顺时针第 2 个', points=[(1145, 245)], pos=0.3, offset=(0, -10))
rep = d.box('副本集 {B, C}', 1050, 392, 190, 56, 'green', sub='replicas = 2')
d.edge(tid, rep)

d.panel(40, 580, 1060, 600, 'Seed Peer B · 副本 1')
d.group(60, 630, 940, 100, 'task A · 副本 1', 'green-bg')
d.box('piece 0', 70, 665, 440, 50, 'green', sub='finished · 8 MiB', shape='sq')
p1 = d.frame(530, 665, 460, 50, '')
d.box('fetch_size 2 · g6–g8', 540, 670, 210, 40, 'grey', bold=False, shape='sq', mono=True, size=12)
d.box('fetch_size 3 · g9–g10', 760, 670, 220, 40, 'grey', bold=False, shape='sq', mono=True, size=12)

d.group(60, 770, 940, 250, 'dfdaemon storage · /var/lib/dragonfly', 'yellow-bg')
hx = [d.box(t, x, 830, 140, 60, 'orange', sub=s_, shape='hex', mono=True) for t, x, s_ in [('piece 0', 220, 'finished ✓'), ('piece 1', 690, 'finished ∅')]]
d.text('content · content/tasks/{task_id} · 按 offset 写', 70, 905, 400, 24, **F)
seg = [d.box(t, x, 935, w, 50, f, bold=False, shape='sq', mono=True) for t, x, w, f in [('0–8 MiB', 70, 440, 'blue'), ('8–16 MiB · 空洞', 530, 460, 'grey')]]
reg = d.box('Registry · origin', 700, 1070, 250, 80, 'red', sub='回源整个 piece 1 · 8 MiB', shape='cloud')

d.edge(rep, p1, (.3, 1), (.5, 0), 'fetch_size 2 · 本次抽到 B', points=[(1107, 540), (760, 540)], offset=(0, -10))
d.edge(p1, get, (.1, 0), (.115, 1), '', dashed=True, points=[(576, 555), (450, 555)])
d.edge(p1, hx[1], (.5, 1), (.5, 0), 'is_finished ?', offset=(60, 0))
d.edge(hx[1], reg, (1, .5), (1, .5), '∅ → 回源', points=[(1040, 860), (1040, 1110)], pos=-0.6, offset=(0, -10))
d.edge(reg, seg[1], (0, .5), (0.337, 1), '', dashed=True, points=[(685, 1110)])

d.panel(1140, 580, 440, 600, 'Seed Peer C · 副本 2')
gc = d.group(1160, 630, 400, 100, 'task A · 副本 2', 'green-bg')
d.box('piece 0', 1170, 665, 190, 50, 'green', sub='finished · 8 MiB', shape='sq')
d.box('piece 1', 1370, 665, 180, 50, 'grey', bold=False, shape='sq')
d.edge(rep, gc, (1, .5), (.9625, 0), '', dashed=True, points=[(1545, 420)])
out(d, 'nydus-dragonfly-arch')

# ================= 3. errors and retries as attempt budgets (one cell = one attempt) =================
d = Diagram(font='avenir')
d.panel(40, 20, 1480, 500, 'nydus daemon')
def lane(y, title, fill, trigger, slots, braces):
    """One left-to-right lane: trigger → GET → attempt cells. slots = (label, sub, fill, w, shape); braces = (x1, x2, caption)."""
    d.group(60, y, 1440, 215, title, fill)
    pill = d.pill(trigger, 80, y + 55, 210, 40)
    get = d.box('GET blob · Range', 320, y + 45, 220, 60, 'green', sub='Dragonfly SDK', shape='io')
    d.hedge(pill, get)
    x, cells = 590, []
    d.frame(570, y + 25, sum(w for _, _, _, w, _ in slots) + 10 * len(slots) + 30, 170, '重试顺序')
    for label, sub, f, w, shape in slots:
        cells.append(d.box(label, x, y + 55, w, 50, f, sub=sub, shape=shape)); x += w + 10
    d.hedge(get, cells[0])
    for x1, x2, cap in braces:
        d.brace(x1, x2, y + 130, up=True); d.text(cap, x1, y + 148, x2 - x1, 24, **F)
    return cells
lane(70, 'prefetch', 'yellow-bg', 'mount 完成',
     [('seed peer A', '① 429', 'blue', 120, 'sq'), ('等 6h–12h', '', 'yellow', 150, 'oval'), ('seed peer A', '② 超时', 'blue', 120, 'sq'),
      ('等 6h–12h', '', 'yellow', 150, 'oval'), ('seed peer A', '③', 'blue', 120, 'sq'), ('…', '', 'grey', 60, 'sq')],
     [(590, 1330, 'max_retries 0 · 不换 peer · 不回源 · 失败就等 6h–12h 再来一次')])
lane(295, 'on-demand', 'blue-bg', 'read() · chunk group miss',
     [('seed peer B', '① 503', 'blue', 120, 'sq'), ('seed peer C', '② 超时 · 换 peer', 'blue', 150, 'sq'),
      ('origin', '③ 取槽', 'red', 120, 'sq'), ('origin', '④ 退避', 'red', 120, 'sq'), ('origin', '⑤ 退避', 'red', 120, 'sq'),
      ('origin', '⑥ 退避', 'red', 120, 'sq'), ('EIO', '', 'grey', 60, 'sq')],
     [(590, 870, 'max_retries 1 · 立即换 peer'), (880, 1390, 'http.max_retries 3 · 每次先取 1 QPS 槽 · 指数退避')])
out(d, 'nydus-dragonfly-retry')

# ================= 4. preheat: four paths (OCI / nydus × seed peer / peer) =================
d = Diagram(font='avenir')
d.panel(40, 20, 1540, 290, '预热组件')
reg = d.box('Registry', 60, 60, 200, 80, 'red', sub='blobs/sha256:&lt;digest&gt;', shape='cloud')
g_oci = d.group(300, 60, 420, 100, 'OCI 镜像', 'blue-bg')
d.box('config', 310, 95, 90, 50, 'grey', bold=False, shape='sq')
for i in range(3): d.box(f'layer {i + 1}', 410 + i * 100, 95, 90, 50, 'blue', bold=False, shape='sq')
g_nyd = d.group(760, 60, 420, 100, 'nydus 镜像', 'blue-bg')
d.box('config', 770, 95, 90, 50, 'grey', bold=False, shape='sq')
for i in range(2): d.box(f'blob {i + 1}', 870 + i * 100, 95, 90, 50, 'blue', bold=False, shape='sq')
d.box('bootstrap', 1070, 92, 100, 56, 'orange', bold=False, shape='doc')
req = d.box('Preheat', 1240, 85, 320, 60, 'green', sub='blob URL 列表 · scope', shape='io')
d.edge(g_oci, req, (.5, 1), (0, .5), points=[(510, 175), (1200, 175), (1200, 115)])
d.edge(g_nyd, req, (.5, 1), (0, .5), points=[(970, 175), (1200, 175), (1200, 115)])
g_scope = d.group(300, 205, 1000, 75, 'scope → 目标 host', 'yellow-bg')
s1 = d.box('single_seed_peer', 310, 235, 480, 40, 'yellow', bold=False, sub='哈希环选 1 个 seed peer', shape='sq', mono=True, size=13)
s3 = d.box('all_peers', 810, 235, 480, 40, 'yellow', bold=False, sub='每个 Node · 或 IPs / Count / %', shape='sq', mono=True, size=13)
d.edge(req, g_scope, (.5, 1), (1, .5), '按 scope 选 host', points=[(1400, 242)], pos=-0.5, offset=(70, 0))

d.panel(40, 360, 1540, 500, 'Dragonfly 集群')
g_seed = d.group(300, 420, 400, 100, 'seed peer', 'green-bg')
for i in range(3): d.box(f'piece {i}', 310 + i * 130, 455, 120, 50, 'green', bold=False, shape='sq')
d.frame(780, 400, 780, 420, ''); d.text('Node', 790, 406, 300, 26, bold=True, size=14, align='left')
nyd = d.box('nydus', 820, 570, 140, 50, 'blue', shape='sq')
ncache = d.box('nydus cache', 990, 565, 150, 60, 'blue', shape='cyl')
ct = d.box('containerd', 1180, 570, 140, 50, 'red', shape='sq')
ccache = d.box('containerd cache', 1350, 565, 170, 60, 'red', sub='content store', shape='cyl')
g_task = d.group(820, 700, 700, 100, 'dfdaemon', 'green-bg')
for i in range(4): d.box(f'piece {i}', 830 + i * 172, 735, 160, 50, 'green', bold=False, shape='sq')
d.edge(s1, g_seed, (.5, 1), (0.625, 0), 'Download Task', pos=-0.2, offset=(75, 0))
d.edge(s3, nyd, (0.1667, 1), (.5, 0), '触发 nydus 预热', pos=0.2, offset=(75, 0))
d.edge(s3, ct, (0.9167, 1), (.5, 0), '触发 containerd pull', pos=0.2, offset=(95, 0))
d.edge(g_seed, reg, (0, .5), (.5, 1), '回源', points=[(160, 470), (160, 140)], pos=0.53, offset=(-35, 0))
d.edge(g_seed, nyd, (1, .5), (0, .5), points=[(740, 470), (740, 595)])
d.edge(nyd, ncache, (1, .5), (0, .5))
d.edge(ct, ccache, (1, .5), (0, .5))
d.edge(ct, g_task, (0.3, 1), (0.5743, 0), offset=(-45, 0))
d.edge(g_task, ct, (0.6543, 0), (0.7, 1), dashed=True, offset=(45, 0))
d.edge(g_seed, g_task, (.5, 1), (0, .5), points=[(500, 750)])
out(d, 'dragonfly-preheat')

# ================= 5. two-level scheduling: Scheduler picks parents, the peer weights them (MathJax formulas) =================
d = Diagram(font='avenir', math=True)
CB, CC, CD = 'blue', 'green-strong', 'orange'           # Peer B / C / D keep their colour in every row
d.panel(40, 20, 1540, 650, 'Scheduler · 中心调度')
pa = d.box('Peer A', 50, 120, 150, 60, 'grey', sub='下载 Task')
pool = d.group(320, 80, 1240, 130, '', 'yellow-bg')
SCORES = ['0.83', '0.71', '0.66', '0.52', '0.48', '0.45', '0.40', '0.37', '0.33', '0.31', '0.28', '0.24', '0.22', '0.19', '0.15']
fills = {'B': CB, 'C': CC, 'D': CD}
for i, (ch, s) in enumerate(zip('BCDEFGHIJKLMNOP', SCORES)):
    d.box(f'Peer {ch}', 335 + i * 82, 120, 72, 60, fills.get(ch, 'grey'), sub=s, mono=True)
d.edge(pa, pool, (1, .5), (0, 0.5385), '① Register', **LB)
d.brace(335, 581, 228, up=False)
d.text('TotalScore', 700, 228, 200, 22, bold=True, size=13, align='left')
d.formula(r'\mathit{TotalScore} = 0.6\,\mathit{LoadQuality} + 0.2\,\mathit{IDC} + 0.1\,\mathit{Location} + 0.1\,\mathit{HostType}', 700, 252, 860, 44)
d.text('LoadQuality', 700, 310, 200, 22, bold=True, size=13, align='left')
d.formula(r'\mathit{LoadQuality} = 0.5\,\mathit{PeakBandwidthUsage} + 0.3\,\mathit{BandwidthDuration} + 0.2\,\mathit{Concurrency}', 700, 334, 860, 44)
ROWS = [('PeakBandwidthUsage', r'1-\dfrac{\mathit{TxBandwidth}}{\mathit{MaxTxBandwidth}}', 56),
        ('BandwidthDuration', r'1-\dfrac{\mathit{UploadContentLength}\times 8}{\mathit{MaxTxBandwidth}\times 60\,\mathrm{s}}', 56),
        ('Concurrency', r'\begin{aligned}&\min\!\Big(1,\ \dfrac{\mathit{PieceCountNeeded}}{\mathit{ConcurrentUploadPieceCount}}\Big)\\[6pt] &\mathit{PieceCountNeeded}=\dfrac{\mathit{MaxTxBandwidth}}{16\,\mathrm{MiB}\times 8}\end{aligned}', 112)]
y = 392
for t, f, h in ROWS:
    d.group(700, y, 860, h, '', 'yellow')
    d.text(t, 720, y, 230, h, bold=True, size=13, align='left')
    d.formula(f, 950, y, 600, h, fill=None)
    y += h + 6

Y = 700
d.panel(40, Y, 1540, 430, 'Peer A · 节点调度')
pa2 = d.box('Peer A', 60, Y + 100, 130, 60, 'grey')
par = d.group(320, Y + 60, 740, 170, 'top 3 parents', 'green-bg')
d.line(458, 240, 125, Y + 100, '② Schedule Parents · B C D', points=[(458, Y - 15), (125, Y - 15)], pos=-0.3, offset=(112, 0), lstyle='rounded=1;arcSize=20;')
d.edge(pa2, par, (1, .5), (0, 0.4118), 'tx / max_tx', both=True, **LB)
for name, x, f, w, idle in [('Peer B', 335, CB, 6, 6), ('Peer C', 580, CC, 3, 3), ('Peer D', 825, CD, 1, 0.5)]:
    d.box(name, x, Y + 100, 220, 56, f, sub=f'w = {w}')
    d.bar(x, Y + 170, 220, 22, idle / 10, f)
d.text('WeightedIndex', 1090, Y + 60, 470, 24, bold=True, size=13, align='left')
d.formula(r'\begin{aligned}\mathit{idle}_i &= \mathit{max\_tx}_i - \mathit{tx}_i\\ w_i &= \max\big(\mathit{idle}_i,\ \mathit{max\_tx}_i/10\big)\\ P(i) &= \frac{w_i}{\sum_j w_j}\ \ \Rightarrow\ \ B:C:D \approx 6:3:1\end{aligned}', 1090, Y + 90, 470, 140, 'green-bg')
d.group(60, Y + 270, 1500, 130, 'Task X · 16 MiB piece', 'grey')
SEQ = 'BBCBDBBCBDBCBBCB'
for i, p in enumerate(SEQ):
    d.box(f'piece {i}', 75 + i * 92, Y + 310, 84, 56, fills[p], bold=False, sub=p)
for cx, dy, ti, lab in [(445, 256, 5, '③ Download Piece'), (690, 248, 7, ''), (935, 240, 9, '')]:
    tx = 75 + ti * 92 + 42
    d.line(cx, Y + 230, tx, Y + 310, lab, points=[(cx, Y + dy), (tx, Y + dy)], pos=0.2, offset=(0, -8), lstyle='rounded=1;arcSize=20;verticalAlign=bottom;')
out(d, 'dragonfly-arch')

# ================= 6. containerd ↔ nydus-snapshotter: lifecycle chevrons, API chips, what nydus does with FUSE / storage =================
d = Diagram(font='avenir')
def chip(title, x, sub=''): return d.box(title, x, 140, 190, 46, 'green', sub=sub, shape='io')
d.panel(40, 20, 1810, 230, 'containerd')
for t, x, w in [('PullImage', 60, 620), ('CreateContainer', 690, 220), ('StartContainer', 920, 220), ('Running', 1150, 220), ('RemoveContainer', 1380, 220), ('GC', 1610, 220)]:
    d.box(t, x, 60, w, 50, 'grey', shape='step')
prep_ex = chip('Prepare · 每层', 80, 'snapshot.ref · nydus-*')
stat    = chip('Stat · chainID', 280)
commit  = chip('Commit · chainID', 480, '该层解压写入完成后')
prep_c  = chip('Prepare · containerID', 705, '可写层')
mounts  = chip('Mounts · containerID', 935)
usage   = chip('Walk · Usage', 1165)
remove  = chip('Remove · containerID', 1395)
cleanup = chip('Cleanup', 1625)
X = dict(prep_ex=175, stat=375, commit=575, prep_c=800, mounts=1030, usage=1260, remove=1490, cleanup=1720)   # chip centres
d.box('gRPC', 205, 267, 120, 36, 'grey', sub='unix socket', shape='sq', size=12)

d.panel(40, 320, 1810, 580, 'nydus-snapshotter', bottom=True)   # title at the bottom: every API drops in from above
band = d.group(60, 420, 1790, 90, '', 'yellow-bg')
for t, x, f in [('layer 1', 225, 'blue'), ('layer 2', 425, 'blue'), ('bootstrap', 640, 'orange'), ('containerID', 1095, 'blue')]:
    d.box(t, x, 442, 100, 46, f, bold=False, sub='active' if t == 'containerID' else 'committed', shape='sq', mono=True, size=12)
d.text('快照记录 · metadata.db', 1510, 452, 190, 26, size=13)
def act(src, r, y, title, sub):                    # chip → action box on the same vertical
    b = d.box(title, X[r] - 85, y, 170, 50, sub=sub); d.edge(src, b, (.5, 1), (.5, 0)); return b
def record_op(src, r, title, sub):                 # touches only the record band
    d.edge(act(src, r, 335, title, sub), band, (.5, 1), ((X[r] - 60) / 1790, 0))
record_op(stat, 'stat', '查快照记录', '回答这层是否已有')
record_op(commit, 'commit', '标记已提交', '记下 upper 目录大小')
record_op(usage, 'usage', '统计磁盘用量', 'upper 目录 + 已下载 blob')
record_op(remove, 'remove', '删快照记录', '目录先留 · nydusd 不停')

q = d.rhombus('看 label', 85, 540, 180, 70)
d.edge(prep_ex, q, (.5, 1), (.5, 0))
skip = d.pill('跳过下载', 100, 680, 150, 40, 'grey')
d.edge(q, skip, (.5, 1), (.5, 0), 'blob 层', offset=(30, 0))
boot = d.box('image.boot', 500, 540, 160, 66, 'orange', sub='snapshots/&lt;id&gt;/fs/image/', shape='doc')
d.hedge(q, boot, 'bootstrap 层 · containerd 解包')
nd = d.frame(560, 680, 320, 110, 'nydusd · FUSE', solid=True)
d.box('mnt', 570, 718, 145, 55, 'blue-strong', sub='挂载点')
d.box('cache/', 725, 712, 145, 62, 'blue', sub='blob 缓存', shape='cyl')
d.edge(boot, nd, (.5, 1), (0.0625, 0), '读 image.boot', offset=(-52, 0))
d.edge(act(prep_c, 'prep_c', 590, '拉起 nydusd', '读 image.boot · 挂 FUSE'), nd, (.5, 1), ((X['prep_c'] - 560) / 320, 0))
reg = d.box('Registry', 320, 690, 170, 90, 'red', sub='按需拉 blob', shape='cloud')
d.edge(nd, reg, (0, .5), (1, .5))
g_ov = d.group(920, 680, 260, 110, '', 'green-bg')
for i, t in enumerate(['lowerdir = mnt', 'upperdir = snapshots/&lt;cid&gt;/fs', 'workdir  = snapshots/&lt;cid&gt;/work']):
    d.box(t, 930, 688 + i * 28, 240, 24, 'green', bold=False, shape='sq', mono=True, size=11)
d.text('rootfs · overlay', 930, 770, 240, 18, size=11, align='left')
d.edge(nd, g_ov, (1, .5), (0, .5))
d.edge(act(mounts, 'mounts', 560, '确认 FUSE 已挂好', '返回 overlay 挂载参数'), g_ov, (.5, 1), ((X['mounts'] - 920) / 260, 0))
d.edge(act(cleanup, 'cleanup', 560, '卸 FUSE · 杀 nydusd', '删孤儿目录 · 删没人用的 blob'), nd, (.5, 1), (1, .8), points=[(1720, 840), (900, 840), (900, 768)], lstyle='curved=1;')
out(d, 'containerd-nydus-snapshotter')

# ================= 7. FUSE failover: one connection, two nydusd generations, crash recovery =================
d = Diagram(font='avenir')
C = dict(bold=False, shape='sq', mono=True, size=12)            # identifier cells: fd · req · slot
P = dict(bold=False, shape='proc', mono=True, size=12)          # fd handles
d.panel(40, 20, 1540, 240, '内核 · 一条 FUSE 连接 · /mnt/img')
cat = d.pill('cat /mnt/img/bin/sh', 60, 70, 240, 40, 'red')
d.group(60, 130, 360, 90, 'open files · fh 不变', 'red-bg')
d.box('fd 3 · fh 0', 70, 165, 160, 40, 'red', **C); d.box('fd 4 · fh 0', 250, 165, 160, 40, 'red', **C)
q = d.group(460, 120, 700, 100, 'fuse_conn 输入队列 · pause 期间只排队不丢', 'cyan-bg')
reqs = [d.box(t, x, 155, w, 50, 'grey', **C) for t, x, w in [('req 41 READ', 470, 120), ('req 42 LOOKUP', 600, 130), ('req 43 READDIR', 740, 140), ('req 44 GETATTR', 890, 140), ('…', 1040, 60)]]
d.edge(cat, reqs[0], (1, .5), (.5, 0), 'read()', points=[(530, 90)], offset=(0, -10))

d.panel(40, 320, 1540, 360, '两代 nydusd · 同一 fd 7 · 同一 mount')
old = d.group(60, 365, 440, 290, 'nydusd N · 前代', 'blue-bg')
fs0 = d.box('ErofsFs', 80, 405, 190, 50, 'blue', sub='ino = nid + 1', **C)
fd7 = d.box('fd 7 · /dev/fuse', 300, 405, 180, 50, 'blue', sub='dup · 交出', **P)
d.box('Relinquished', 80, 480, 150, 50, 'orange', bold=False, shape='hex', mono=True, size=12)
d.box('workers · fd 8 fd 9', 250, 480, 230, 50, 'blue', sub='pause → exit', **C)
j0 = d.box('fd 11 · journal', 300, 555, 180, 50, 'yellow', **P)
d.text('✕ SIGKILL', 80, 570, 120, 20, size=12, align='left')
new = d.group(1060, 365, 440, 290, 'nydusd N+1 · 后继', 'blue-bg')
fd7n = d.box('fd 7 · /dev/fuse', 1080, 405, 180, 50, 'blue', sub='from_initialized_fd', **P)
fs1 = d.box('ErofsFs', 1290, 405, 190, 50, 'blue', sub='同一镜像重建', **C)
d.box('workers · fd 13 fd 14', 1080, 480, 230, 50, 'blue', sub='park → resume', **C)
d.box('Serving', 1330, 480, 150, 50, 'orange', bold=False, shape='hex', mono=True, size=12)
j1 = d.box('fd 11 · journal', 1080, 555, 180, 50, 'yellow', **P)
xfer = d.box('Session Transfer', 540, 405, 480, 50, 'green', sub='SCM_RIGHTS [fd 7, fd 11] + metadata · session_id · init flags', shape='io')
ctl = d.box('control.sock · HANDOFF_BEGIN → READY → COMMITTED', 540, 480, 480, 50, 'green', bold=False, shape='io')
jr = d.group(560, 540, 440, 80, 'fd 11 · InflightJournal · memfd · 已读未回复的 unique', 'yellow-bg')
for t, x, w, f in [('slot 0 · 39', 570, 100, 'orange'), ('slot 1 · 40', 680, 100, 'orange'), ('slot 2 · ∅', 790, 100, 'grey'), ('…', 900, 60, 'grey')]:
    d.box(t, x, 572, w, 36, f, **C)
d.hedge(fd7, xfer); d.hedge(xfer, fd7n)
d.edge(old, ctl, (1, 0.483), (0, .5), both=True); d.edge(ctl, new, (1, .5), (0, 0.483), both=True)
d.hedge(j0, jr); d.edge(j1, jr, (0, .5), (1, .5))
d.edge(q, xfer, (0.457, 1), (.5, 0), '同一 fd 7', offset=(40, 0))

d.panel(40, 740, 1540, 170, 'crash failover · Supervisor 只启动一个后继')
hold = d.group(560, 780, 440, 110, 'Recovery Holder · supervisor.sock', 'green-bg')
d.box('fd 7 副本', 580, 820, 120, 50, 'blue', **P); d.box('fd 11 副本', 710, 820, 120, 50, 'yellow', **P)
d.box('metadata 副本', 840, 817, 140, 56, 'orange', bold=False, shape='doc')
rec = d.box('--recover', 1100, 810, 400, 50, 'green', sub='FUSE_NOTIFY_RESEND · 或 reply EIO(39, 40)', shape='io')
d.edge(old, hold, (0.9, 1), (0, .5), 'RETAINED', dashed=True, points=[(456, 835)], offset=(50, 0))
d.hedge(hold, rec, dashed=True)
d.edge(rec, new, (0.45, 0), (.5, 1), dashed=True)
img = d.box('EROFS 镜像', 300, 960, 1000, 60, 'blue', sub='只读 · nid ↔ ino 由镜像决定', shape='cyl')
d.edge(fs0, img, (0, .5), (0, .5), 'ErofsFs::new', points=[(70, 430), (70, 990)], pos=0.6, offset=(0, -12))
d.edge(fs1, img, (1, .5), (1, .5), 'ErofsFs::new', points=[(1570, 430), (1570, 990)], pos=0.6, offset=(0, -12))
out(d, 'nydus-fuse-failover')
