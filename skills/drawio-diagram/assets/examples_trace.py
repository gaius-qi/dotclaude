"""Dragonfly trace task set · 5 figures: one two-panel data-flow figure (first mount / next mount) and the four small
figures that go with it (sequence, content format, lifecycle, build loop). Default font (Trebuchet MS).

Sources (every name in the figures is grep-able there):
  dragonflyoss/design @feature/trace systems-analysis/trace-task/trace-task.md (+ sequence-diagram.png, content-format.png,
    state-diagram.png): TraceTask, PUT/GET /v1/trace-tasks/{id} on proxy port 4001, X-Dragonfly-Nydusd-ID,
    trace_task_id(bootstrap_digest), UploadTraceTaskBlob {source_blob_index, url, header, compressor, chunk_groups},
    header 16 B {entry_count, entry_size, data_offset}, entry 8 B {source_chunk_group_index, source_blob_index, reserved},
    doc example: 3 entries, data_offset 40, content_length 2752552; file {content_dir}/trace-tasks/{id}, no pieces, local only;
    build = task::download per chunk group → write_pieces_in_order → write_trace_task; download = get_trace_task →
    upload_trace_task → RangeReader; SDK VNodeHashRing::get_with_replicas(&id, 2), put/get_trace_task, decode_trace_task_entries;
    nydus: record on-demand groups in first-access order, PUT after 10 s idle or 5 min, next mount GET, skip cached, CRC32C, 404 → on-demand.
  dragonfly-client-storage: content/tasks/<task_id>, piece 4 MiB.
"""
import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from dio import Diagram
OUT = os.path.dirname(os.path.abspath(__file__)) + '/'
def out(d, name): d.save(OUT + name + '.drawio'); Diagram.export(OUT + name + '.drawio', OUT + name + '.png'); print(name)
ABOVE = dict(offset=(0, -6), lstyle='verticalAlign=bottom;')
BELOW = dict(offset=(0, 6), lstyle='verticalAlign=top;')
L = dict(size=13, align='left')
DATA = 'fontSize=13;'
MONO = lambda s: f'<font face="Courier New">{s}</font>'

# ================= 1. trace layer end to end: first mount records + builds, next mount replays =================
d = Diagram()
def strip(y):  # trace task file, the doc's 3-entry example
    hd = d.box('header', 1140, y, 70, 60, 'orange', sub='16 B')
    d.box('entry table', 1220, y, 150, 60, 'yellow', sub='3 × 8 B')
    for i, (t, s) in enumerate([('[0] blob 1 · cg 0', 'offset 0 · 2 MiB'), ('[1] blob 1 · cg 5', '2097152 · 512 KiB'), ('[2] blob 2 · cg 0', '2621440 · 128 KiB')]):
        d.box(t, 1380 + i * 140, y, 130, 60, 'blue', bold=False, sub=s, style=DATA)
    return hd

T = 50; d.panel(20, 20, 1820, 660, 'First mount', 'record on-demand chunk groups · PUT · build one file of decompressed chunk groups')
app = d.box('container read()', 40, T + 60, 130, 60, 'red')
d.group(220, T + 10, 380, 430, 'nydusd', 'blue-bg')
ny = d.box('blob cache', 240, T + 60, 180, 60, 'blue')
d.hedge(app, ny, 'miss')
rec = d.group(240, T + 150, 340, 140, 'record · access order', 'yellow-bg')
for i, e in enumerate(['blob 1 · cg 0 · 0 + 1 MiB · zstd', 'blob 1 · cg 5 · 5 MiB + 256 KiB · zstd', 'blob 2 · cg 0 · 0 + 64 KiB · plain']):
    d.box(e, 255, T + 180 + i * 34, 310, 30, 'yellow', bold=False, style=DATA)
d.edge(ny, rec, (.5, 1), (.2647, 0), 'record', offset=(-30, 0))
sdk = d.box('dragonfly-sdk', 240, T + 350, 240, 70, 'blue', sub='id = f(bootstrap digest)')
d.edge(rec, sdk, (.2647, 1), (.375, 0), 'blobs · chunk_groups', offset=(70, 0))
dfB = d.box('dfdaemon B', 240, T + 500, 240, 60, 'green', sub='replica')
d.edge(sdk, dfB, label='same PUT', offset=(50, 0))

d.group(660, T + 10, 1160, 600, 'dfdaemon A', 'green-bg')
px = d.box('proxy', 700, T + 60, 200, 60, 'green')
for y in (72, 84, 96): d.line(420, T + y, 700, T + y)                      # three parallel lines = repeated request
d.text('N × GET Range', 430, T + 40, 260, 24, size=13)
d.edge(px, ny, (0, .8), (1, .8), '206', dashed=True, **BELOW)
tt = d.box('TraceTask', 700, T + 350, 200, 70, 'green', sub='build')
d.edge(sdk, tt, (1, .357), (0, .357), 'PUT /v1/trace-tasks/{id}', **ABOVE)
d.edge(tt, sdk, (0, .786), (1, .786), '202', dashed=True, **BELOW)

d.text(f'<b>task A</b> · <i>blob 1 · sha256:aaaa…</i> · piece 4 MiB · {MONO("content/tasks/&lt;task_id_A&gt;")}', 1140, T + 180, 640, 22, **L)
PA = [d.box(f'p{i}', 1140 + i * 100, T + 210, 90, 70, 'blue', bold=False, style=DATA) for i in range(6)]
d.tag('cg 0', 1140, T + 210); d.tag('cg 5', 1240, T + 210)                 # which chunk group lives in which piece
d.text(f'<b>task B</b> · <i>blob 2 · sha256:bbbb…</i> · piece 4 MiB · {MONO("content/tasks/&lt;task_id_B&gt;")}', 1140, T + 320, 640, 22, **L)
PB = [d.box(f'p{i}', 1140 + i * 100, T + 350, 90, 70, 'blue', bold=False, style=DATA) for i in range(4)]
d.tag('cg 0', 1140, T + 350)
d.edge(px, PA[0], (1, .5), (0, .5), 'origin · whole piece', points=[(1100, T + 90), (1100, T + 245)], offset=(125, 0))
d.edge(tt, PB[0], (1, .5), (0, .5), 'read ranges · local first', **ABOVE)
peer = d.box('peers / origin', 1620, T + 350, 150, 70, 'green')
d.edge(peer, PB[3], (0, .5), (1, .5), 'missing piece', dashed=True, **ABOVE)

d.text(f'<b>trace task</b> · {MONO("content/trace-tasks/{id}")} · one file · decompressed chunk groups', 1140, T + 440, 640, 22, **L)
hd = strip(T + 470)
dec = d.box('decompress', 960, T + 470, 130, 60, 'yellow', sub='per chunk group')
d.edge(tt, dec, (.5, 1), (0, .5), 'compressed', points=[(800, T + 500)], pos=0.55, offset=(0, -8))
d.edge(dec, hd, (1, .5), (0, .5))
d.text('<i>entry = source chunk group · source blob · length and offset from source blob.meta</i>', 1140, T + 536, 700, 20, size=12, align='left')

T = 750; d.panel(20, 720, 1820, 530, 'Next mount', 'one GET · fill blob cache · reads hit')
app = d.box('container start', 40, T + 70, 130, 60, 'red', sub='reads hit locally')
d.group(220, T + 10, 380, 440, 'nydusd', 'blue-bg')
sdk = d.box('dragonfly-sdk', 240, T + 70, 200, 60, 'blue', sub='same id')
d.hedge(app, sdk, 'mount')
ent = d.group(240, T + 180, 340, 135, 'entry table', 'yellow-bg')
for i, e in enumerate(['[0] blob 1 · cg 0 · cached · skip', '[1] blob 1 · cg 5 · fetch', '[2] blob 2 · cg 0 · fetch']):
    d.box(e, 255, T + 210 + i * 34, 310, 30, 'yellow', bold=False, style=DATA)
d.edge(sdk, ent, (.5, 1), (.294, 0), 'decode entries', offset=(60, 0))
ny = d.box('blob cache', 240, T + 360, 240, 60, 'blue')
d.edge(ent, ny, (.294, 1), (.4167, 0), 'CRC32C · write', offset=(60, 0))
d.text('<i>404 → next replica · all 404 → on-demand reads</i>', 40, T + 462, 600, 20, size=12, align='left')

d.group(660, T + 10, 1160, 250, 'dfdaemon A', 'green-bg')
tt = d.box('TraceTask', 700, T + 70, 200, 60, 'green')
d.edge(sdk, tt, (1, .25), (0, .25), 'GET /v1/trace-tasks/{id}', **ABOVE)
d.edge(tt, sdk, (0, .75), (1, .75), 'one stream', dashed=True, **BELOW)
hd = strip(T + 70)
d.edge(tt, hd, (1, .25), (0, .25), 'read', **ABOVE)
d.edge(hd, tt, (0, .75), (1, .75), '', dashed=True, **BELOW)
d.brace(1140, 1370, T + 145, up=True); d.text('first Range → entries', 1140, T + 157, 230, 20, size=12)
d.brace(1380, 1790, T + 145, up=True); d.text('missing groups only', 1380, T + 157, 410, 20, size=12)
out(d, 'trace-layer')

# ================= 2. sequence: build, then replay after a phase divider =================
d = Diagram()
SEQ = 'verticalAlign=bottom;labelBackgroundColor=#FFFFFF;'
P = [('nydusd + dragonfly-sdk', 'blue'), ('dfdaemon A', 'green'), ('dfdaemon B', 'green'), ('peers / origin', 'green-strong')]
CX = [130, 430, 730, 1030]; BOT = 1240
for (p, f), cx in zip(P, CX): d.box(p, cx - 100, 40, 200, 50, f)
for cx in CX: d.line(cx, 90, cx, BOT, dashed=True, arrow=False, lstyle='')
def msg(y, a, b, lbl, ret=False, pos=0): d.line(CX[a], y, CX[b], y, lbl, dashed=ret, pos=pos, lstyle=SEQ)
msg(130, 0, 1, 'GET blob · Range × N'); msg(190, 1, 0, '206', True)
d.selfcall(CX[0], 240, 'record chunk groups · derive id')
msg(330, 0, 1, 'PUT /v1/trace-tasks/{id}'); msg(390, 1, 0, '202', True)
msg(450, 0, 2, 'PUT /v1/trace-tasks/{id}', pos=0.5); msg(510, 2, 0, '202', True, pos=-0.5)
msg(570, 1, 3, 'download missing ranges', pos=0.5); msg(630, 3, 1, 'pieces', True, pos=-0.5)
d.selfcall(CX[1], 680, 'decompress · write header · entries · data')
msg(750, 2, 3, 'download missing ranges'); msg(810, 3, 2, 'pieces', True)
d.selfcall(CX[2], 860, 'decompress · write header · entries · data')
d.line(40, 950, 1120, 950, dashed=True, arrow=False, lstyle=''); d.pill('next mount', 520, 935, 120, 30)   # phase divider
msg(1010, 0, 1, 'GET /v1/trace-tasks/{id} · Range'); msg(1070, 1, 0, '200 / 206 · or 404', True)
msg(1130, 0, 2, 'on 404 · next replica', pos=0.5); msg(1190, 2, 0, '200 / 206 · or 404 → on-demand reads', True, pos=-0.5)
out(d, 'trace-task-seq')

# ================= 3. content format: file → header → entry → worked example =================
d = Diagram()
F = dict(size=13, align='left')
d.text('file', 20, 45, 120, 50, bold=True)
d.box('header', 170, 40, 120, 60, 'orange', sub='16 B')
d.box('entry table', 300, 40, 260, 60, 'yellow', sub='entry_count × 8 B')
d.box('data', 570, 40, 560, 60, 'blue', sub='decompressed chunk group bytes · back to back in table order')
d.text('0', 160, 105, 20, 20, size=12); d.text('16', 280, 105, 20, 20, size=12)
d.text('data_offset = 16 + entry_count × 8', 440, 105, 240, 20, size=12)
d.text('content_length = data_offset + Σ uncompressed_size', 850, 105, 300, 20, size=12)
d.text('header\n16 B', 20, 170, 120, 60, bold=True)
d.box('entry_count', 170, 170, 160, 60, 'orange', bold=False, sub='u32 · 0')
d.box('entry_size', 340, 170, 160, 60, 'orange', bold=False, sub='u32 · 4 · always 8')
d.box('data_offset', 510, 170, 320, 60, 'orange', bold=False, sub='u64 · 8')
d.text('entry\n8 B', 20, 290, 120, 60, bold=True)
d.box('source_chunk_group_index', 170, 290, 330, 60, 'yellow', bold=False, sub='u32 · 0')
d.box('source_blob_index', 510, 290, 160, 60, 'yellow', bold=False, sub='u16 · 4')
d.box('reserved', 680, 290, 150, 60, 'yellow', bold=False, sub='u16 · 6')
d.text('length of entry i = uncompressed_size in the source blob.meta · offset of entry i = Σ length before it', 170, 355, 900, 20, **F)
d.text('example\n3 entries', 20, 410, 120, 60, bold=True)
d.box('header + table', 170, 410, 120, 60, 'orange', bold=False, sub='40 B')
d.box('[0] blob 1 · cg 0', 300, 410, 400, 60, 'blue', bold=False, sub='offset 0 · 2 MiB')
d.box('[1] blob 1 · cg 5', 710, 410, 200, 60, 'blue', bold=False, sub='2097152 · 512 KiB')
d.box('[2] blob 2 · cg 0', 920, 410, 140, 60, 'blue', bold=False, sub='2621440 · 128 KiB')
d.text('data_offset 40 · content_length 2752552 · Range 0-39 → header + table', 170, 480, 700, 20, **F)
out(d, 'trace-task-format')

# ================= 4. lifecycle =================
d = Diagram()
s = d.pill('PUT', 40, 60, 120, 50)
b = d.box('Building', 260, 55, 200, 60, 'yellow', sub='row + file created')
f = d.box('Finished', 620, 55, 200, 60, 'green', sub='served with Range')
e = d.pill('evicted', 980, 60, 120, 50)
x = d.pill('deleted', 300, 200, 120, 50)
d.hedge(s, b, '202'); d.hedge(b, f, 'every entry written'); d.hedge(f, e, 'gc · ttl or disk usage')
d.edge(b, x, label='any entry failed · unfinished at startup', offset=(135, 0))
out(d, 'trace-task-state')

# ================= 5. build loop =================
d = Diagram()
st = d.pill('for each chunk group · body order', 40, 70, 230, 50)
q1 = d.rhombus('pieces local?', 330, 45, 170, 100)
rd = d.box('read local pieces', 580, 65, 190, 60, 'blue')
dl = d.box('download', 335, 230, 160, 60, 'green', sub='P2P / origin')
q2 = d.rhombus('is_uncompressed', 840, 45, 190, 100)
dc = d.box('decompress', 850, 230, 170, 60, 'yellow', sub='blob.compressor · zstd / lz4')
wr = d.box('write into the trace task', 580, 380, 440, 60, 'orange', sub='offset = data_offset + Σ uncompressed_size')
d.hedge(st, q1); d.hedge(q1, rd, 'yes'); d.hedge(rd, q2)
d.edge(q1, dl, label='no', offset=(14, 0))
d.edge(dl, rd, (1, .5), (.5, 1), points=[(675, 260)])
d.edge(q2, dc, label='no', offset=(14, 0))
d.edge(dc, wr, (.5, 1), (.8, 0))
d.edge(q2, wr, (1, .5), (1, .5), label='yes', points=[(1070, 95), (1070, 410)], offset=(16, 0))
d.edge(wr, st, (0, .5), (.5, 1), label='next chunk group', points=[(155, 410)], pos=0.35, offset=(0, -8))
d.text('all written → create_trace_task_finished · any failure → create_trace_task_failed', 40, 470, 700, 24, **F)
out(d, 'trace-task-build')
