import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from dio import Diagram
OUT = os.path.dirname(os.path.abspath(__file__)) + '/'
def out(d, name): d.save(OUT + name + '.drawio'); d.export(OUT + name + '.drawio', OUT + name + '.png'); print(name)

F = dict(size=13, align='left')

# ================= 1. Overall image layout + addressing =================
# Superblock row: struct erofs_super_block field order (fs/erofs/erofs_fs.h; offsets from
# erofs.docs.kernel.org/en/latest/ondisk/core_ondisk.html). meta_blkaddr = "start block address of the
# inode-metadata zone", inode_offset = meta_blkaddr * block_size + 32 * nid. Only the superblock has a fixed
# offset (1024); the region order below is what mkfs.erofs emits (erofs-utils mkfs/main.c: erofs_reserve_sb →
# erofs_mkfs_init_devices → erofs_load_shared_xattrs_from_path → erofs_xattr_flush_name_prefixes → root inode).
d = Diagram()
d.text('Superblock\nkey fields', 20, 40, 120, 60, bold=True)
SB = [('magic', '0x00 · E0F5E1E2'), ('blkszbits', '0x0C · 12 → 4 KiB'), ('root_nid', '0x0E · root dir nid'), ('inos', '0x10 · inode count'),
      ('blocks', '0x24 · block count'), ('meta_blkaddr', '0x28 · inode zone start'), ('xattr_blkaddr', '0x2C · shared xattr start'),
      ('devt_slotoff', '0x58 · device table'), ('xattr_prefix_start', '0x5C · long prefixes')]
cells = [d.box(t, 170 + i * 128, 40, 120, 60, 'orange', bold=False, sub=s) for i, (t, s) in enumerate(SB)]
n0 = d.note('dump.erofs -S image.erofs', 1330, 55, 210, 30, 'grey'); d.dotted(cells[8], n0, (1, .5), (0, .5))

d.text('Image\nLayout', 20, 270, 120, 70, bold=True)
zone = d.group(170, 250, 1070, 125, '', 'yellow-bg')
d.text('inode-metadata zone · starts at meta_blkaddr × 4 KiB · nid = (offset − start) / 32 · root inode = start + root_nid × 32', 180, 342, 1050, 26, **F)
d.box('unused', 180, 265, 90, 70, 'grey', bold=False, sub='1 KiB · nid 0–31')
sb = d.box('Superblock', 280, 265, 150, 70, 'orange', sub='@1024 · 128 B · nid 32–35')
dev = d.box('Device Table', 440, 265, 150, 70, 'green', sub='128 B slots · multi-dev')
sx = d.box('Shared xattrs', 600, 265, 160, 70, 'yellow', sub='4 B aligned · if any')
px = d.box('xattr prefixes', 770, 265, 130, 70, 'yellow', bold=False, sub='long names · if any')
root = d.box('root inode', 910, 265, 130, 70, 'yellow', sub='nid 36 when alone')
d.box('inodes …', 1050, 265, 180, 70, 'yellow', sub='inode · xattrs · extents · tail')
data = d.box('Data blocks', 1255, 265, 200, 70, 'blue', sub='4 KiB aligned · may interleave with later metadata')
# field → region arrows; struct order vs. image order differ, so they cross (elbow levels 125…205)
d.dotted(cells[0], sb, (.5, 1), (.5, 0))
d.edge(cells[5], zone, (.5, 1), (0, 0), '× 4 KiB · zone start · 0 by default', points=[(870, 125), (170, 125)], pos=-0.49, offset=(0, -10))
d.edge(cells[6], sx, (.5, 1), (.5, 0), '× 4 KiB', points=[(998, 145), (680, 145)], offset=(0, -10))
d.edge(cells[7], dev, (.5, 1), (.5, 0), '× 128 B', points=[(1126, 165), (515, 165)], offset=(0, -10))
d.edge(cells[8], px, (.5, 1), (.5, 0), '× 4 B', points=[(1254, 185), (835, 185)], offset=(0, -10))
d.edge(cells[2], root, (.5, 1), (.5, 0), '× 32 B', points=[(486, 205), (975, 205)], pos=0.15, offset=(0, -10))

d.text('Addressing', 20, 440, 120, 100, bold=True)
for i, t in enumerate(['id 0', 'id 1']): d.box(t, 600 + i * 85, 440, 75, 60, 'yellow', bold=False, sub='4 B unit')
d.brace(600, 760, 425, up=True); d.text('addr = xattr_blkaddr × 4 KiB + id × 4', 600, 515, 300, 20, **F)
for i, t in enumerate(['nid 36', 'nid 37', '...']): d.box(t, 910 + i * 110, 440, 100, 60, 'yellow', bold=False, sub='32 B slot')
d.brace(910, 1230, 425, up=True); d.text('addr = meta_blkaddr × 4 KiB + nid × 32', 910, 515, 320, 20, **F)
for i, t in enumerate(['blk 0', 'blk 1']): d.box(t, 1255 + i * 100, 440, 90, 60, 'blue', bold=False)
d.brace(1255, 1455, 425, up=True); d.text('addr = blkaddr × 4 KiB', 1255, 515, 200, 20, **F)
out(d, 'erofs-image-layout')

# ================= 2. Regular file =================
d = Diagram()
d.text('Regular file\ninode slot', 20, 60, 120, 70, bold=True)
ino = d.box('inode', 170, 60, 220, 70, 'yellow', sub='erofs_inode_compact 32 B · erofs_inode_extended 64 B')
d.box('xattr_ibody_header', 400, 60, 160, 70, 'yellow', bold=False, sub='12 B · h_shared_count')
d.box('shared ids', 570, 60, 130, 70, 'yellow', bold=False, sub='4 B × count')
d.box('inline xattrs', 710, 60, 190, 70, 'yellow', bold=False, sub='entry 4 B · name · value')
d.box('tail data', 910, 60, 150, 70, 'blue', bold=False, sub='FLAT_INLINE only')
b0 = d.box('blk a', 1130, 60, 100, 70, 'blue', bold=False)
for i, t in enumerate(['blk a+1', '...', 'blk a+n-1']): d.box(t, 1240 + i * 110, 60, 100, 70, 'blue', bold=False)
d.edge(ino, b0, (.5, 0), (.5, 0), 'i_u.startblk · n full blocks in data area', points=[(280, 25), (1180, 25)], offset=(0, -6), lstyle='verticalAlign=bottom;')
d.brace(1130, 1560, 145, up=False); d.text('i_size = n × 4 KiB + len(tail)', 1130, 158, 430, 20, **F)
d.brace(170, 390, 145, up=False)
IN = [('i_format', 'ver · datalayout'), ('i_xattr_icount', '(n−1)×4 + 12 B'), ('i_mode', 'S_IFREG · perms'), ('i_nlink', 'link count'),
      ('i_size', 'bytes'), ('i_ino', 'inode number'), ('i_uid · i_gid', 'owner'), ('i_u', 'startblk · rdev'), ('i_mtime', 'extended only')]
cells = [d.box(t, 170 + i * 120, 200, 110, 60, 'yellow', bold=False, sub=s) for i, (t, s) in enumerate(IN)]
d.text('addr(nid) = meta_blkaddr × 4 KiB + nid × 32 · compact inode = 1 slot · extended = 2 slots', 170, 275, 800, 20, **F)
n1 = d.note('dump.erofs --nid=<nid> image.erofs', 1270, 215, 270, 30, 'grey'); d.dotted(cells[8], n1, (1, .5), (0, .5))

d.text('Data\naddressing', 20, 360, 120, 60, bold=True)
s1 = d.box('file offset X', 170, 360, 160, 60, 'green')
s2 = d.box('blk = X >> 12', 390, 360, 160, 60, 'green', sub='4 KiB blocks')
q = d.box('blk < n ?', 610, 360, 160, 60, 'yellow')
s3 = d.box('addr = (startblk + blk) × 4 KiB + X mod 4 KiB', 830, 360, 440, 60, 'green', sub='in data area')
t = d.box('tail data · right after inode & xattrs', 610, 480, 420, 60, 'blue', sub='FLAT_INLINE · X mod 4 KiB into tail')
d.hedge(s1, s2); d.hedge(s2, q); d.hedge(q, s3, 'yes'); d.edge(q, t, (.5, 1), (0.19, 0), 'no', offset=(-14, 0))
out(d, 'erofs-file-layout')

# ================= 3. Directory + lookup =================
d = Diagram()
d.text('Directory\ninode slot', 20, 60, 120, 70, bold=True)
ino = d.box('inode', 170, 60, 220, 70, 'yellow', sub='S_IFDIR · i_size = dir bytes')
d.box('xattrs', 400, 60, 150, 70, 'yellow', bold=False, sub='header · entries')
d.box('tail dirents', 560, 60, 190, 70, 'blue', bold=False, sub='FLAT_INLINE · partial block')
b0 = d.box('dir blk 0', 820, 60, 110, 70, 'blue', bold=False, sub='sorted names')
for i, t in enumerate(['dir blk 1', '...', 'dir blk n-1']): d.box(t, 940 + i * 120, 60, 110, 70, 'blue', bold=False)
d.edge(ino, b0, (.5, 0), (.5, 0), 'i_u.startblk · blocks globally sorted by name', points=[(280, 25), (875, 25)], offset=(0, -6), lstyle='verticalAlign=bottom;')
n2 = d.note('ls -la /mnt  # dirents come back sorted', 1320, 80, 290, 30, 'grey'); d.dotted(n2, 'c8', (0, .5), (1, .5))
d.brace(820, 1290, 145, up=False); d.text('each directory block', 820, 158, 470, 20, **F)

d.text('Directory block\n4 KiB', 20, 200, 120, 60, bold=True)
DE = [('dirent 0', '"."'), ('dirent 1', '".."'), ('dirent 2', '"bin"'), ('...', ''), ('dirent k-1', '"usr"')]
de = [d.box(t, 170 + i * 130, 200, 120, 60, 'yellow', bold=False, sub=s) for i, (t, s) in enumerate(DE)]
d.box('names', 830, 200, 460, 60, 'blue', bold=False, sub='"." ".." "bin" … "usr" · packed · no NUL · zero pad at end')
d.text('k = dirent[0].nameoff / 12 · sorted by name · len = next.nameoff − nameoff', 830, 275, 470, 20, **F)
d.brace(430, 550, 285, up=False)

d.text('erofs_dirent\n12 B', 20, 340, 120, 60, bold=True)
DF = [('nid', 430, 150, '8 B · inode id'), ('nameoff', 590, 120, '2 B · name start'), ('file_type', 720, 160, '1 B · EROFS_FT_DIR …'), ('reserved', 890, 100, '1 B')]
for t, x, w, s in DF: d.box(t, x, 340, w, 60, 'yellow', bold=False, sub=s)

d.text('Lookup\nnamei("bin")', 20, 480, 120, 70, bold=True)
l1 = d.box('namei("bin")', 170, 480, 200, 70, 'green', sub='dir inode · i_size → n blocks')
l2 = d.box('binary search blocks', 430, 480, 220, 70, 'green', sub='compare 1st name of mid block')
l3 = d.box('binary search in block', 710, 480, 220, 70, 'green', sub='strcmp over k dirents')
l4 = d.box('dirent.nid', 990, 480, 150, 70, 'yellow', sub='8 B')
l5 = d.box('inode @ meta_blkaddr × 4 KiB + nid × 32', 1200, 480, 320, 70, 'orange', sub='read inode · recurse per path component')
d.hedge(l1, l2); d.hedge(l2, l3); d.hedge(l3, l4); d.hedge(l4, l5)
out(d, 'erofs-dir-layout')

# ============ 4. EROFS 读路径流程图 ============
d = Diagram()
st = d.pill('read(fd, buf, len)', 400, 40, 160, 50)
p1 = d.box('VFS', 380, 130, 200, 60, sub='erofs_read_folio()')
q1 = d.box('inode 已压缩？', 380, 230, 200, 60, 'yellow')
p2 = d.box('erofs_map_blocks()', 940, 230, 200, 60, sub='逻辑块 → 物理块')
p3 = d.box('bdev 直接读块', 940, 330, 200, 60)
p4 = d.box('z_erofs_map_blocks()', 380, 330, 200, 60, sub='lcluster → pcluster')
q2 = d.box('pcluster 已缓存？', 380, 430, 200, 60, 'yellow')
p5 = d.box('读取 pcluster', 660, 430, 200, 60, sub='块设备 / 外部 blob')
p6 = d.box('解压', 660, 530, 200, 60, sub='LZ4 · LZMA · DEFLATE · ZSTD')
p7 = d.box('填充 page cache', 380, 630, 200, 60)
en = d.pill('返回数据', 400, 730, 160, 50)
d.edge(st, p1); d.edge(p1, q1)
d.hedge(q1, p2, '否'); d.edge(q1, p4, label='是', offset=(-14, 0))
d.edge(p2, p3); d.edge(p3, en, (.5, 1), (1, .5), points=[(1040, 755)])
d.edge(p4, q2); d.hedge(q2, p5, '否'); d.edge(q2, p7, label='是', offset=(-14, 0))
d.edge(p5, p6); d.edge(p6, p7, (.5, 1), (1, .5), points=[(760, 660)]); d.edge(p7, en)
out(d, 'erofs-read-flow')

# ============ 5. EROFS + fscache 按需加载时序图 ============
d = Diagram()
P = [('App', 'red'), ('VFS / Page Cache', 'yellow'), ('EROFS', 'blue'), ('fscache / cachefiles', 'blue'), ('nydusd', 'green'), ('Registry / Dragonfly', 'green-strong')]
CX = [120, 360, 600, 840, 1080, 1320]; BOT = 720
for (p, f), cx in zip(P, CX): d.box(p, cx - 90, 40, 180, 50, f)
for cx in CX: d.line(cx, 90, cx, BOT, dashed=True, arrow=False, lstyle='')
d.frame(700, 275, 720, 245, 'alt [cache miss]')
MSG = [(130, 0, 1, 'read()', 0), (190, 1, 2, 'erofs_read_folio()', 0), (250, 2, 3, 'erofs_fscache_read_folios()', 0),
       (310, 3, 4, 'on-demand read · /dev/cachefiles', 0), (370, 4, 5, 'GET blob range', 0), (430, 5, 4, 'blob data', 1),
       (490, 4, 3, 'write cache file · READ_COMPLETE', 1), (550, 3, 2, 'folio data', 1), (610, 2, 1, 'folio uptodate', 1), (670, 1, 0, 'data', 1)]
for y, a, b, lbl, ret in MSG:
    d.line(CX[a], y, CX[b], y, lbl, dashed=bool(ret), lstyle='verticalAlign=bottom;labelBackgroundColor=#FFFFFF;')
out(d, 'erofs-ondemand-seq')
