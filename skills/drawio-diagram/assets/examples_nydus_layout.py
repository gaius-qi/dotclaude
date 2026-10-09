"""nydus v3 (github.com/dragonflyoss/nydus branch v3 @ d9867094, 3.0.0-beta.1, 2026-09-29) on-registry / on-disk layout diagrams.

Sources read; every field / constant name below is grep-able there:
  nydus-format/src/erofs/mod.rs          EROFS_SUPER_OFFSET 1024 · EROFS_SB_BASE_SIZE 128 · EROFS_BLOCK_SIZE 4096 · EROFS_SLOTSIZE 32
                                          EROFS_DEVICESLOT_SIZE 128 · EROFS_CHUNK_INDEX_SIZE 8 · EROFS_INODE_CHUNK_BASED 4 · EROFS_CHUNK_FORMAT_INDEXES · EROFS_NULL_ADDR
  nydus-format/src/erofs/superblock.rs   ErofsSuperblock field order + offsets (magic 0x00 … devt_slotoff 0x58)
  nydus-format/src/erofs/inode.rs        ErofsInodeCompact 32 B / ErofsInodeExtended 64 B · xattr_size = icount*4+8
  nydus-format/src/erofs/chunk.rs        ErofsChunkIndex {startblk_hi, device_id, startblk_lo} · ErofsDeviceSlot {tag, blocks_lo, uniaddr_lo, blocks_hi, uniaddr_hi, _reserved}
  nydus-format/src/blob/footer.rs        BlobFooter 4096 B: magic 0 · feature_compat 8 · feature_incompat 12 · crc32 16 · bootstrap_crc32 20 · compressed_data_offset 24
                                          compressed_data_size 32 · bootstrap_offset 40 · bootstrap_size 48 · bootstrap_compressed_size 56 · blob_metadata_offset 64
                                          blob_metadata_size 72 · reserved 80 · "NDFOOTER" · INCOMPAT_BOOTSTRAP_ZSTD 1<<0 · INCOMPAT_RAW_DEVICE 1<<1 · no version field
  nydus-format/src/blob/mod.rs           finish_full_blob: [compressed data | pad | bootstrap | blob meta | footer], 4 KiB aligned
  nydus-format/src/blob/metadata.rs      BlobMetadataHeader 24 B (magic · feature_compat · feature_incompat · crc32 · table_count u16 · reserved)
                                          BlobMetadataTable header 16 B (type · header_size · feature_compat · feature_incompat · entry_size · entry_count), 8 B aligned
                                          types 1 ChunkGroupTable (ext: max_blocks_per_chunk_group_bits · compressor) · 2 ChunkLengthTable · 3 ChunkGroupIndexTable
                                          (ext: blocks_per_chunk_group_index_bits) · 4 ChunkGroupDigestTable (ext: algorithm) · 5 ChunkGroupRedirectTable
                                          entry: compressed_offset 8 · logical_block_offset 4 · first_chunk_index 4 · uncompressed_size 4 · uncompressed_crc32 4
                                          DEFAULT_CHUNK_SIZE 2 MiB · defaults: max group 8 MiB (bits 11) · index stride 2 MiB (bits 9)
  nydus/src/build/blob_chunk.rs          DEFAULT_CHUNK_GROUP_MIN_SIZE 2 MiB · packs 2–8 MiB · data chunks device_id = 1 · all-zero chunk → EROFS_NULL_ADDR
  nydus/src/build/image.rs               head_layout: device table @1152, meta_blkaddr = ceil(table_end/4096) ≥ 1 (23 slots fit block 0)
  nydus/src/build/bootstrap.rs           alloc order: inodes (root first, breadth first) → pad → dir blocks → long symlinks
  nydus/src/build/inode.rs               serialize_inode: header | xattr ibody | align 8 | chunk indexes · i_u = chunk_format
  nydus/src/build/merge.rs               register_blobs: identical full blobs share one device slot
  nydus-core/src/reader/data.rs          locate_chunk: NULL → hole · device_id > 0 → blob-relative
  nydus-storage/src/chunk_group_map.rs   "NDGRPMAP" 4 KiB header (magic 0 · feature_compat 8 · feature_incompat 12 · chunk_group_count 16 · ready_count 20 · state 24) + 1 bit / group
  nydusify/pkg/nydus/constants.go        application/vnd.oci.image.layer.nydus.blob.v1 · image/image.boot · image/<sha256>.blob.meta
  nydusify/internal/optimizer/optimizer.go  trace layer appended before the rewritten bootstrap layer; its .blob.meta joins the tar
  docs/nydus.md                          Full blob byte layout · Blob meta region layout · Blocks, chunks and chunk groups · Reader and Mount Design · Image format
No CDC: pack boundaries come from the chunk BLAKE3 digest (blob_chunk.rs append_chunk): cut_byte = digest[31]; a pack of ≥ 2 MiB closes
when cut_byte & 0x3f == 0 (PACK_STRICT_MASK, 1 in 64), of ≥ 4 MiB when cut_byte & 0x1f == 0 (PACK_LOOSE_MASK, 1 in 32), and at 8 MiB
(PACK_SPAN_MULTIPLE) regardless. Lookup (metadata.rs chunk_group_index): entry = block / blocks_per_chunk_group_index, chunk_group =
ChunkGroupIndexTable[entry], step to chunk_group + 1 when block ≥ ChunkGroupTable[chunk_group + 1].logical_block_offset.
No abbreviations in labels: always 'chunk group', never 'group' or 'g'.
z_erofs (COMPRESSED_FULL) left out. FUSE mount only: no flatdev / ublk / nbd / uffd / pmem. The optimize output is called the "trace layer".
Wording follows the EROFS set in examples.py: formulas not prose, EROFS vocabulary (inode-metadata zone · blkaddr ·
chunkbits · i_u.startblk · EROFS_NULL_ADDR · extra device), yes/no decisions. Table names spelled with spaces (Chunk Group Table …).
"""
import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from dio import Diagram, ang
OUT = os.path.dirname(os.path.abspath(__file__))
F = dict(size=13, align='left')
NF = dict(bold=False)

# ====================== R1. on-registry · one full blob ======================
d = Diagram()
d.rowlabel('BlobFooter\nkey fields', 40)
FT = [('magic', '0x00 · "NDFOOTER"'), ('feature_incompat', '0x0C · BOOTSTRAP_ZSTD · RAW_DEVICE'), ('compressed_data_offset', '0x18 · 0'),
      ('compressed_data_size', '0x20 · bytes'), ('bootstrap_offset', '0x28'), ('bootstrap_size', '0x30 · bytes'),
      ('blob_metadata_offset', '0x40'), ('blob_metadata_size', '0x48 · bytes')]
fc = d.row(40, [(t, s, 180) for t, s in FT], fill='orange')

d.rowlabel('Full blob\nLayout', 270, h=70)
data = d.box('Data region', 170, 265, 430, 70, 'blue', sub='chunk groups · byte-packed')
d.box('pad', 610, 265, 70, 70, 'grey', sub='to 4 KiB · outside', **NF)
bg = d.group(690, 250, 330, 120, '', 'yellow-bg')
d.text('bootstrap', 700, 342, 310, 22, bold=True, size=13, align='left')
d.box('zstd frame', 700, 265, 210, 70, 'yellow', sub='bootstrap_compressed_size bytes · EROFS image')
d.box('pad', 920, 265, 90, 70, 'grey', sub='to 4 KiB · inside', **NF)
meta = d.box('blob meta', 1030, 265, 390, 70, 'yellow', sub='NDBLMETA · same bytes as .blob.meta · ends 4 KiB aligned')
foot = d.box('footer', 1430, 265, 200, 70, 'orange', sub='NDFOOTER · 4 KiB · @ EOF')
# field → region, ⊐ elbows staggered 20px (125…225)
d.elbow(fc[2], data, 125, 'start · 0', (.5, 1), (0, 0))
d.elbow(fc[3], data, 145, 'bytes · unaligned', (.5, 1), (.5, 0))
d.elbow(fc[4], bg, 165, '4 KiB aligned', (.5, 1), (0, 0))
d.elbow(fc[5], bg, 185, '4 KiB multiple · 0 if trace layer', (.5, 1), (.5, 0), pos=-0.2)
d.elbow(fc[6], meta, 205, '= bootstrap_offset + bootstrap_size', (.5, 1), (0, 0))
d.elbow(fc[7], meta, 225, '4 KiB multiple · 0 if RAW_DEVICE', (.5, 1), (.5, 0), pos=0.1)

d.rowlabel('Addressing', 440)
for i, (t, x, w) in enumerate([('chunk group 0', 170, 150), ('chunk group 1', 330, 150), ('…', 490, 80)]):
    d.box(t, x, 440, w, 60, 'blue', sub='zstd frame / plain' if i < 2 else '', **NF)
d.brace(170, 600, 425, up=True)
d.text('addr = compressed_data_offset + Chunk Group Table[i].compressed_offset · length = next − this', 170, 515, 620, 20, **F)
# the embedded bootstrap decoded: the same EROFS image as the on-disk bootstrap figure, one device slot
d.brace(690, 1020, 405, up=False)
d.box('unused', 690, 440, 80, 60, 'grey', sub='1 KiB', **NF)
d.box('Superblock', 780, 440, 140, 60, 'orange', sub='@1024 · 128 B')
d.box('Device Table', 930, 440, 250, 60, 'green', sub='@1152 · 1 slot · tag = SHA256(data region)')
d.box('inode-metadata zone', 1190, 440, 230, 60, 'yellow', sub='this layer · nid 0 = root')
d.box('data blocks', 1430, 440, 170, 60, 'blue', sub='dirents · symlinks')
d.text('bootstrap decoded · see on-disk bootstrap', 1190, 515, 410, 20, **F)
n = d.note('nydus check --blob <blob>', 1650, 285, 220, 30, 'grey'); d.dotted(foot, n, (1, .5), (0, .5))
d.out(OUT, 'nydus-registry-blob')

# ====================== R2. on-registry · whole image (OCI manifest) ======================
d = Diagram()
d.rowlabel('OCI image', 40)
mf = d.box('OCI manifest', 170, 40, 280, 60, 'red')
n = d.note('nydusify convert --source <oci> --target <nydus>', 510, 55, 380, 30, 'grey'); d.dotted(mf, n, (1, .5), (0, .5))

l0 = d.box('layer 0', 170, 190, 190, 70, 'green')
d.edge(mf, l0, (.5, 1), (0.737, 0), 'layers[]', offset=(30, 0))
d.box('layer 1', 370, 190, 190, 70, 'green')
d.box('…', 570, 190, 70, 70, 'grey', **NF)
d.box('layer N−1', 650, 190, 190, 70, 'green')
d.box('trace layer', 850, 190, 210, 70, 'green', sub='optional')
bl = d.box('bootstrap layer', 1100, 190, 270, 70, 'yellow')

# each blob layer carries an embedded bootstrap and a blob meta region; merge folds the bootstraps into
# image.boot, the blob metas are copied into the tar unchanged (nydusify LinkBlobMetaFiles)
d.rowlabel('Per blob\nmetadata', 340)
for x, w in ((170, 190), (370, 190), (650, 190), (850, 210)): d.brace(x, x + w, 300, up=True)
bs, ms = [], []
for i, (x, t) in enumerate(((170, 'bootstrap 0'), (370, 'bootstrap 1'), (650, 'bootstrap N−1'))):
    bs.append(d.box(t, x, 340, 110, 60, 'yellow', **NF))
    ms.append(d.box('blob meta', x + 120, 340, 70, 60, 'yellow', **NF))
d.box('…', 570, 340, 70, 60, 'grey', **NF)
d.box('no bootstrap', 850, 340, 120, 60, 'grey', **NF)
ms.append(d.box('blob meta', 980, 340, 80, 60, 'yellow', **NF))

d.rowlabel('Bootstrap layer\ngzip tar', 510)
tg = d.group(990, 495, 930, 90, '', 'yellow-bg')
d.edge(bl, tg, (.5, 1), (0.2634, 0), 'gzip tar', offset=(45, 0))
ib = d.box('image/image.boot', 1000, 510, 210, 60, 'yellow', sub='merged bootstrap · mounted by FUSE')
FM = [('layer 0 blob meta', 1220), ('layer 1 blob meta', 1380), ('…', 1540), ('layer N−1 blob meta', 1590), ('trace layer blob meta', 1750)]
SUBS = [ang('image/ · <sha256&#160;0>.blob.meta'), ang('image/ · <sha256&#160;1>.blob.meta'), '', ang('image/ · <sha256&#160;N−1>.blob.meta'), ang('image/ · <sha256&#160;N>.blob.meta')]
fm = [d.box(t, x, 510, 40 if t == '…' else 150 + (10 if 'trace' in t else 0), 60, 'yellow', sub=sb, **NF) for (t, x), sb in zip(FM, SUBS)]
for b_, cx in zip(bs[:2], (225, 425)): d.edge(b_, ib, (.5, 1), (.5, 0), points=[(cx, 430), (1105, 430)])
d.elbow(bs[2], ib, 430, 'nydus merge · OCI whiteouts', (.5, 1), (.5, 0))
# one blob meta file per blob, copied as is: nested ⊐ elbows, no crossings
targets = (fm[0], fm[1], fm[3], fm[4]); tx = (1295, 1455, 1665, 1830); ys = (486, 478, 470, 462)
for m, cx, t, x, y in zip(ms, (325, 525, 805, 1020), targets, tx, ys):
    d.edge(m, t, (.5, 1), (.5, 0), 'copied as is · one file per blob' if y == 462 else '', points=[(cx, y), (x, y)], offset=(0, -10))

# image.boot is a plain EROFS image: same block 0 as the bootstrap figure
d.rowlabel('image.boot\nLayout', 640)
d.brace(1000, 1210, 610, up=True)
d.box('unused', 700, 640, 90, 60, 'grey', sub='1 KiB', **NF)
d.box('Superblock', 800, 640, 150, 60, 'orange', sub='@1024 · 128 B')
dt = d.box('Device Table', 960, 640, 290, 60, 'green', sub='@1152 · 128 B slots · one per blob')
d.box('inode-metadata zone', 1260, 640, 230, 60, 'yellow', sub='merged tree · nid 0 = root')
d.box('data blocks', 1500, 640, 130, 60, 'yellow', sub='dirents', **NF)

d.rowlabel('Device Table\nslots', 770)
d.brace(960, 1250, 735, up=True)
for t, x, w, sb in [('slot 0', 850, 150, ang('tag = <sha256&#160;0>')), ('slot 1', 1010, 150, ang('tag = <sha256&#160;1>')), ('…', 1170, 60, ''), ('slot N−1', 1240, 160, ang('tag = <sha256&#160;N−1>')), ('slot N', 1410, 160, ang('tag = <sha256&#160;N> · trace layer'))]:
    d.box(t, x, 770, w, 60, 'green', sub=sb, **NF)
d.out(OUT, 'nydus-registry-image')

# ====================== R3. on-registry · blob meta region ======================
d = Diagram()
d.rowlabel('Header\n24 B', 40)
HF = [('magic', '0x00 · "NDBLMETA"', 130), ('feature_compat', '0x08 · 4 B', 150), ('feature_incompat', '0x0C · 4 B', 150), ('crc32', '0x10 · crc32c', 120),
      ('table_count', '0x14 · 2 B', 130), ('reserved', '0x16 · 2 B', 90)]
hc = d.row(40, HF, fill='orange')

d.rowlabel('blob meta\nLayout', 270, h=70)
tb = d.group(160, 250, 1490, 100, '', 'yellow-bg')
hd = d.box('Header', 170, 265, 110, 70, 'orange', sub='24 B')
gt = d.box('Chunk Group Table', 290, 265, 260, 70, 'yellow', sub='type 1')
d.box('Chunk Length Table', 560, 265, 210, 70, 'yellow', sub='type 2')
gi = d.box('Chunk Group Index Table', 780, 265, 250, 70, 'yellow', sub='type 3')
d.box('Chunk Group Digest Table', 1040, 265, 250, 70, 'yellow', sub='type 4 · optional')
d.box('Chunk Group Redirect Table', 1300, 265, 260, 70, 'yellow', sub='type 5 · trace layer')
d.box('pad', 1570, 265, 70, 70, 'grey', sub='to 4 KiB', **NF)
d.dotted(hc[0], hd, (.5, 1), (.5, 0))
d.elbow(hc[4], tb, 125, 'tables · 8 B aligned', (.5, 1), (0.0872, 0), pos=-0.15)

# every table: 16 B header · optional extension · entries
d.rowlabel('table', 400)
d.brace(290, 1560, 370, up=False)
d.box('table header', 170, 400, 260, 60, 'yellow', sub='16 B')
d.box('header extension', 440, 400, 220, 60, 'orange', sub='@ 16 · 8 B · types 1 · 3 · 4', **NF)
d.box('entry 0', 670, 400, 130, 60, 'yellow', sub='@ header_size', **NF)
d.box('entry 1', 810, 400, 130, 60, 'yellow', sub='+ entry_size', **NF)
d.box('…', 950, 400, 60, 60, 'yellow', **NF)
d.box('entry entry_count − 1', 1020, 400, 210, 60, 'yellow', **NF)

d.rowlabel('table header\n16 B', 520)
d.brace(170, 430, 490, up=False)
TH = [('type', '0x00 · 2 B', 130), ('header_size', '0x02 · 2 B', 130), ('feature_compat', '0x04 · 2 B', 150), ('feature_incompat', '0x06 · 2 B', 150),
      ('entry_size', '0x08 · 4 B', 120), ('entry_count', '0x0C · 4 B', 130)]
d.row(520, TH)

# per table type: three rows (table header values · header extension fields · entry fields), metadata.rs SIZE consts
def row(y, label, cells, fill):
    d.text(label, 20, y, 140, 60, bold=True, size=13)
    x = 170
    for t, sb, w in cells:
        d.box(t, x, y, w, 60, 'grey' if t in ('no extension', 'last entry') else fill, sub=sb, **NF); x += w + 10

def table(y, name, hdr, ext, entry):
    d.text(name, 170, y - 30, 700, 24, bold=True, align='left')
    row(y, 'table header', hdr, 'yellow')
    row(y + 70, 'header extension', ext or [('no extension', '', 150)], 'orange')
    row(y + 140, 'entry', entry, 'yellow')

HDR16 = lambda t, es, n: [('type', t, 110), ('header_size', '16', 130), ('feature_compat', '0', 150), ('feature_incompat', '0', 150), ('entry_size', es, 120), ('entry_count', n, 200)]
HDR24 = lambda t, es, n: [('type', t, 110), ('header_size', '24', 130), ('feature_compat', '0', 150), ('feature_incompat', '0', 150), ('entry_size', es, 120), ('entry_count', n, 200)]

table(680, 'Chunk Group Table · type 1', HDR24('1', '24', 'chunk groups + 1'),
      [('max_blocks_per_chunk_group_bits', '@16 · 1 B', 250), ('compressor', '@17 · 1 B · 0 none · 1 zstd · 2 lz4', 250), ('reserved', '@18 · 6 B', 110)],
      [('compressed_offset', '0x00 · 8 B', 170), ('logical_block_offset', '0x08 · 4 B · blkaddr', 190), ('first_chunk_index', '0x0C · 4 B', 160),
       ('uncompressed_size', '0x10 · 4 B', 160), ('uncompressed_crc32', '0x14 · 4 B', 160), ('last entry', 'totals · size 0 · crc 0', 170)])
table(940, 'Chunk Length Table · type 2', HDR16('2', '4', 'chunks'), None,
      [('length', '0x00 · 4 B · bytes of chunk i', 260)])
table(1200, 'Chunk Group Index Table · type 3', HDR24('3', '4', 'strides'),
      [('blocks_per_chunk_group_index_bits', '@16 · 1 B', 260), ('reserved', '@17 · 7 B', 110)],
      [('chunk_group_index', '0x00 · 4 B · chunk group at the stride start', 320)])
table(1460, 'Chunk Group Digest Table · type 4 · optional', HDR24('4', '32', 'chunk groups'),
      [('algorithm', '@16 · 1 B · 1 = BLAKE3', 200), ('reserved', '@17 · 7 B', 110)],
      [('digest', '0x00 · 32 B · BLAKE3 of chunk group i', 300)])
table(1720, 'Chunk Group Redirect Table · type 5 · trace layer only', HDR16('5', '8', 'chunk groups'), None,
      [('source_blob_index', '0x00 · 2 B · device slot', 200), ('reserved', '0x02 · 2 B', 110), ('source_chunk_group_index', '0x04 · 4 B', 220)])

d.out(OUT, 'nydus-registry-blobmeta')

# ====================== R4. on-registry · chunk → chunk group → compress ======================
# blob_chunk.rs @ v3 d9867094: write_reader_chunks cuts per file at file_chunk_size (DEFAULT_CHUNK_SIZE 2 MiB), all-zero
# chunk → EROFS_NULL_ADDR; append_chunk: len ≥ chunk_group_min_size → own chunk group, else pack; cut_byte = digest[31],
# mask 0x3f below 2 × min (PACK_TARGET_MULTIPLE), 0x1f after, forced at 4 × min (PACK_SPAN_MULTIPLE); submit_bin encodes
# the packed payload, kept compressed only if compressed × 100 ≤ uncompressed × 70 (MAX_COMPRESSED_SIZE_PERCENT);
# digest per chunk group = BLAKE3(payload) (232224c0). cache/local.rs plan_chunk_group_window: fetch_size-aligned cell.
d = Diagram()
for t, x, w in [('file A · 5 MiB', 170, 470), ('file B · 300 B', 650, 150), ('file C · 100 KiB', 810, 150), ('file D · 2 MiB zeros', 970, 150)]:
    d.text(t, x, 22, w, 24, **F); d.brace(x, x + w, 60, up=True)
d.rowlabel('Chunks\n≤ 2 MiB per file', 80)
CH = [('file A chunk 0', '2 MiB'), ('file A chunk 1', '2 MiB'), ('file A chunk 2', '1 MiB'), ('file B chunk 0', '300 B'), ('file C chunk 0', '100 KiB'), ('file D chunk 0', 'all zero')]
ch = [d.box(t, 170 + i * 160, 80, 150, 60, 'grey' if i == 5 else 'blue', sub=sb, **NF) for i, (t, sb) in enumerate(CH)]

d.rowlabel('Chunk groups', 220)
d.group(170, 200, 150, 125, '', 'yellow-bg'); d.group(330, 200, 150, 125, '', 'yellow-bg'); d.group(490, 200, 540, 125, '', 'yellow-bg')
gc = [d.box('file A chunk 0', 180, 220, 130, 50, 'blue', **NF), d.box('file A chunk 1', 340, 220, 130, 50, 'blue', **NF),
      d.box('file A chunk 2', 500, 220, 130, 50, 'blue', **NF), d.box('file B chunk 0', 660, 220, 130, 50, 'blue', sub='1 block', **NF),
      d.box('file C chunk 0', 820, 220, 130, 50, 'blue', sub='25 blocks', **NF)]
d.box('…', 960, 220, 60, 50, 'blue', **NF)
d.text('chunk group 0\nchunk ≥ 2 MiB · alone', 180, 278, 140, 40, **F)
d.text('chunk group 1\nchunk ≥ 2 MiB · alone', 340, 278, 140, 40, **F)
d.text(ang('chunk group 2 · pack of chunks < 2 MiB\neach chunk block-aligned'), 500, 278, 520, 40, **F)
for c, g in zip(ch[:5], gc): d.edge(c, g)
hole = d.text('EROFS_NULL_ADDR\nnot stored', 1090, 225, 200, 40, **F)
d.edge(ch[5], hole, (.5, 1), (.5, 0), points=[(1045, 180), (1190, 180)])

d.rowlabel('Pack boundary', 410)
d.box(ang('pack < 2 MiB'), 170, 410, 230, 60, 'grey', sub='never cut', **NF)
d.box(ang('2 MiB ≤ pack < 4 MiB'), 410, 410, 330, 60, 'yellow', sub='low 6 bits = 0 · 1/64', **NF)
d.box(ang('4 MiB ≤ pack < 8 MiB'), 750, 410, 330, 60, 'yellow', sub='low 5 bits = 0 · 1/32', **NF)
d.box('8 MiB', 1090, 410, 200, 60, 'orange', sub='always cut', **NF)
d.text('after each chunk · cut_byte = last byte of BLAKE3(chunk)', 170, 480, 700, 20, **F)

# how a chunk group closes (append_chunk), one block per case. Each case: its own MiB ruler (100 px = 1 MiB, x0 = 170),
# the chunks appended in order with size and cut_byte, the check after each, the thick close line, and the result.
def ruler(y):
    for m in range(0, 9):
        big = m in (2, 4, 8)
        d.rule(170 + m * 100, y - 6, y + 56, dashed=big, faint=not big)
    for m, lbl in ((2, '2 MiB'), (4, '4 MiB'), (8, '8 MiB')): d.text(lbl, 170 + m * 100 - 40, y - 28, 80, 20, size=12)
def case(y, title, chunks, checks, close_at, result):
    d.text(title, 170, y - 60, 900, 24, bold=True, align='left')
    ruler(y)
    x = 170
    for name, mib, sb in chunks:
        d.box(name, x, y, int(mib * 100) - 6, 50, 'blue', sub=sb, **NF); x += int(mib * 100)
    d.rule(170 + int(close_at * 100), y - 10, y + 60, width=3)
    for k, c in enumerate(checks): d.text(c, 170, y + 62 + k * 20, 900, 20, **F)
    d.box(result, 1150, y - 5, 400, 60, 'orange', sub=f'{close_at:g} MiB', **NF)

d.rowlabel('How a chunk\ngroup closes', 590, w=140)
Y = 650
case(Y, '① a chunk of 2 MiB or more never joins a pack', [('file A chunk 0', 2, '2 MiB')], ['chunk ≥ chunk_group_min_size → its own chunk group at once'], 2, 'chunk group = 1 chunk')
Y += 200
case(Y, '② pack between 2 and 4 MiB · cut when the low 6 bits of cut_byte are 0 · 1/64',
     [('c1', 1, '1 MiB · 0x9c'), ('c2', 0.3, ''), ('c3', 0.7, '0x71'), ('c4', 1.4, '1.4 MiB · 0x80')],
     ['c1 · pack 1 MiB · below 2 MiB · not checked', 'c2 · 300 KiB · 0x40 · pack 1.3 MiB · below 2 MiB · not checked', 'c3 · 700 KiB · 0x71 = 0111 0001 · pack 2 MiB · low 6 bits 110001 · keep',
      'c4 · pack 3.4 MiB · 0x80 = 1000 0000 · low 6 bits 000000 · close'], 3.4, 'chunk group = c1 c2 c3 c4')
Y += 240
case(Y, '③ pack between 4 and 8 MiB · cut when the low 5 bits of cut_byte are 0 · 1/32',
     [('c1', 1.5, '1.5 MiB · 0x2a'), ('c2', 1.5, '1.5 MiB · 0x2a'), ('c3', 1.5, '1.5 MiB · 0x2a'), ('c4', 0.8, '0x60')],
     ['c1 · 1.5 MiB · below 2 MiB · not checked', 'c2 · 3 MiB · 0x2a = 0010 1010 · low 6 bits 101010 · keep', 'c3 · 4.5 MiB · past 4 MiB → low 5 bits 01010 · keep',
      'c4 · 800 KiB · 0x60 = 0110 0000 · pack 5.3 MiB · low 5 bits 00000 · close'], 5.3, 'chunk group = c1 c2 c3 c4')
Y += 240
case(Y, '④ no cut_byte matched · the pack closes when it reaches 8 MiB',
     [('c1', 1.9, '1.9 MiB · 0x0f'), ('c2', 1.9, '1.9 MiB · 0x1f'), ('c3', 1.9, '1.9 MiB · 0x3f'), ('c4', 1.9, '1.9 MiB · 0x7f'), ('c5', 0.4, '')],
     ['c2 · 3.8 MiB · 0x1f low 6 bits 011111 · keep', 'c3 · 5.7 MiB · 0x3f low 5 bits 11111 · keep', 'c4 · 7.6 MiB · 0x7f low 5 bits 11111 · keep', 'c5 · 0.4 MiB · 0xff · pack 8 MiB = span · close'], 8, 'chunk group = c1 … c5')
Y += 240
case(Y, '⑤ the next chunk would not fit · the pack closes before it, the chunk opens the next pack',
     [('c1', 1.9, '1.9 MiB · 0x0f'), ('c2', 1.9, '1.9 MiB · 0x1f'), ('c3', 1.9, '1.9 MiB · 0x3f'), ('c4', 1.9, '1.9 MiB · 0x7f')],
     ['c1 … c4 · 7.6 MiB · no cut', ang('c5 · 1 MiB · 7.6 + 1 > 8 MiB → close the pack first'), 'c5 starts the next pack'], 7.6, 'chunk group = c1 … c4')
d.box('c5', 170 + 760, Y, 94, 50, 'blue-strong', sub='next pack', **NF)

Y += 200   # below case ⑤ (its checks end at Y + 62 + 3 × 20 ≈ Y + 122)
d.text('Per chunk group', 20, Y, 130, 70, bold=True)
q1 = d.box('payload', 170, Y, 200, 70, 'green', sub='chunks back to back')
q2 = d.box('BLAKE3(payload)', 430, Y, 200, 70, 'green', sub='Chunk Group Digest Table')
q3 = d.box('compress', 690, Y, 200, 70, 'green', sub='zstd / LZ4')
q4 = d.box('compressed × 100 ≤ uncompressed × 70 ?', 950, Y, 330, 70, 'yellow')
q5 = d.box('append compressed', 1340, Y, 200, 70, 'green')
q6 = d.box('append plain', 950, Y + 110, 200, 70, 'green', sub='compressed_size == uncompressed_size')
d.hedge(q1, q2); d.hedge(q2, q3); d.hedge(q3, q4); d.hedge(q4, q5, 'yes'); d.edge(q4, q6, (.303, 1), (.5, 0), 'no', offset=(-14, 0))

# fetch window (cache/local.rs plan_chunk_group_window): cells of fetch_size over the compressed data region; a miss
# fetches every chunk group overlapping its cell, except ready / in-flight ones, in one range read. 1 MiB = 300 px.
Y += 330
X0, MIB = 170, 300
def px(b): return X0 + int(b / 0x100000 * MIB)
d.text('fetch window', 20, Y + 55, 130, 60, bold=True)
cells = [d.box(f'cell {c}', px(c * 0x200000), Y, 2 * MIB - 4, 40, 'orange' if c == 1 else 'grey', sub='2 MiB', **NF) for c in range(3)]
CG = [('0', 0, 0x0B0000, 'ready', 'grey'), ('1', 0x0B0000, 0x1A0000, '', 'blue'), ('2', 0x1A0000, 0x260000, 'miss', 'blue-strong'),
      ('3', 0x260000, 0x2E0000, '', 'blue'), ('4', 0x2E0000, 0x4A0000, 'in flight', 'grey'), ('5', 0x4A0000, 0x600000, '', 'blue')]
for t, a, b, sb, f_ in CG: d.box(f'chunk group {t}', px(a), Y + 60, px(b) - px(a) - 4, 50, f_, sub=sb, **NF)
d.brace(px(0x0B0000), px(0x2E0000), Y + 130, up=True)
d.text('fetch window · chunk groups 1 · 2 · 3 · 0x0B0000 – 0x2E0000 · 2.2 MiB', px(0x0B0000), Y + 150, px(0x2E0000) - px(0x0B0000), 20, size=13)
for a in (0x0B0000, 0x2E0000): d.rule(px(a), Y - 5, Y + 125, dashed=True)
n = d.note('storage.fetch_size: 2 MiB', px(0x600000) + 40, Y + 5, 220, 30, 'green'); d.dotted(n, cells[2], (0, .5), (1, .5))
d.out(OUT, 'nydus-registry-chunk-group')




# ====================== R5. on-registry · block → chunk → chunk group lookup ======================
# One worked example end to end. Inode: file with chunkbits 14 (16 KiB chunks = 4 blocks), device_id 1.
# Blob meta: blocks_per_chunk_group_index = 4 (stride), chunk groups end at blkaddr 5, 9, 16 (metadata.rs doc example).
# Strip scale: 50 px = 1 block, x0 = 170, so blkaddr b starts at 170 + 50 b.
d = Diagram()
d.rowlabel('EROFS\nfile offset', 40)
o1 = d.box('file offset X = 0x6800', 170, 40, 260, 60, 'green', sub='26 KiB')
o2 = d.box(ang('i = X >> chunkbits'), 490, 40, 220, 60, 'green', sub=ang('0x6800 >> 14 = 1'))
o3 = d.box('in-chunk = X % chunk size', 770, 40, 260, 60, 'green', sub='0x6800 % 16 KiB = 0x2800')
d.hedge(o1, o2); d.hedge(o2, o3)

d.rowlabel('EROFS\nchunk index', 160)
d.box('inode', 170, 160, 170, 60, 'yellow', sub='CHUNK_BASED · chunkbits 14')
ci = [d.box(f'chunk index {n}', 350 + n * 180, 160, 170, 60, 'blue' if n != 1 else 'blue-strong', sub=sb, **NF)
      for n, sb in enumerate(('startblk_lo 2', 'startblk_lo 6 · device_id 1', 'startblk_lo 12', 'EROFS_NULL_ADDR'))]
d.edge(o2, ci[1], (.5, 1), (.5, 0), 'i = 1', offset=(30, 0))          # o2 centre 600 → ci[1] centre 615
d.text('blkaddr = startblk_lo = 6 · device 1 = slot device_id − 1', 170, 230, 600, 20, **F)

d.rowlabel('extra device\nblkaddr', 360)
# row 1: the chunk as a thin bar, row 2: chunk groups, row 3: stride ruler, row 4: index entries (x = 170 + 50 × blkaddr)
ck = d.box('chunk · blkaddr 6–9 · 16 KiB', 470, 300, 200, 36, 'blue-strong', **NF)
d.edge(ci[1], ck, (.5, 1), (.5, 0), 'startblk_lo 6', points=[(615, 270), (570, 270)], pos=0.6, offset=(-60, 0))
d.box('chunk group 0', 170, 360, 250, 50, 'blue', sub='blkaddr 0–4', **NF)
d.box('chunk group 1', 420, 360, 200, 50, 'blue', sub='blkaddr 5–8', **NF)
d.box('chunk group 2', 620, 360, 350, 50, 'blue', sub='blkaddr 9–15', **NF)
st = [d.box(f'stride {kk}', 170 + kk * 200, 430, 200, 40, 'yellow' if kk != 1 else 'orange', sub=f'entry {kk}', **NF) for kk in range(4)]
for kk in range(5): d.rule(170 + kk * 200, 354, 476, dashed=True)
d.line(470, 336, 470, 430)
d.text('blkaddr 6 → stride 6 / 4 = 1', 700, 470, 260, 20, **F)
d.text('1 cell = 1 block · stride = 4 blocks', 990, 440, 300, 20, **F)

d.rowlabel('Chunk Group\nIndex Table', 520)
ie = [d.box(v, 170 + kk * 200, 520, 200, 50, 'yellow' if kk != 1 else 'orange', sub=f'entry {kk} · chunk group at blkaddr {kk * 4}', **NF) for kk, v in enumerate(('0', '0', '1', '2'))]
d.edge(st[1], ie[1], (.5, 1), (.5, 0), 'entry 1', offset=(30, 0))
d.text('blocks_per_chunk_group_index = 4 · a non-final chunk group spans ≥ 1 stride ⇒ a stride holds ≤ 1 boundary', 700, 580, 900, 20, **F)

d.rowlabel('blkaddr →\nchunk group', 620)
f3 = d.box('chunk group = Chunk Group Index Table[1]', 295, 620, 350, 60, 'green', sub='chunk group 0')
f4 = d.box('blkaddr ≥ logical_block_offset(chunk group + 1) ?', 735, 620, 340, 60, 'yellow', sub='6 ≥ 5 · yes → chunk group 1')
f5 = d.box('chunk group 1', 1165, 620, 180, 60, 'orange', sub='at most + 1')
d.edge(ie[1], f3, (.5, 1), (.5, 0), 'value 0', offset=(30, 0))
d.hedge(f3, f4); d.hedge(f4, f5)

d.rowlabel('Chunk Group\nTable', 760)
E = [('entry 0', 'compressed_offset 0 · logical_block_offset 0 · first_chunk_index 0', 'yellow'),
     ('entry 1', 'compressed_offset 0x9000 · logical_block_offset 5 · first_chunk_index 2', 'orange'),
     ('entry 2', 'compressed_offset 0xC400 · logical_block_offset 9 · first_chunk_index 3', 'yellow'),
     ('entry 3 · last', 'compressed_offset 0x1A000 · logical_block_offset 16 · first_chunk_index 6', 'grey')]
ce = [d.box(t, 170 + n * 380, 760, 370, 60, f_, sub=sb, **NF) for n, (t, sb, f_) in enumerate(E)]
d.edge(f5, ce[1], (.5, 1), (.5, 0), points=[(1255, 720), (735, 720)])
d.text('chunk group 1 = entry 1 .. entry 2 · compressed 0x9000–0xC400 · blkaddr 5–8 · chunk 2 only', 170, 830, 900, 20, **F)

d.rowlabel('Data region\nfull blob', 920)
dz = d.group(160, 905, 1010, 95, '', 'blue-bg')
d.box('chunk group 0', 170, 920, 300, 60, 'blue', sub='0 – 0x9000', **NF)
p1 = d.box('chunk group 1', 480, 920, 200, 60, 'blue-strong', sub='0x9000 – 0xC400 · zstd', **NF)
d.box('chunk group 2', 690, 920, 470, 60, 'blue', sub='0xC400 – 0x1A000', **NF)
d.edge(ce[1], p1, (.5, 1), (.5, 0), 'range read · decode · verify', points=[(735, 870), (580, 870)], pos=0.55, offset=(-110, 0))
d.text(ang('decoded chunk group 1 → <hex>.blob.data @ blkaddr 5 × 4 KiB · read 4 KiB @ blkaddr 6 × 4 KiB + 0x2800'), 170, 1010, 900, 20, **F)
d.out(OUT, 'nydus-registry-lookup')

# ====================== D1. on-disk · bootstrap (metadata-only EROFS image) ======================
d = Diagram()
d.rowlabel('Superblock\nkey fields', 40, w=140)
SB = [('magic', '0x00 · E0F5E1E2'), ('checksum', '0x04 · crc32c'), ('feature_compat', '0x08 · SB_CHKSUM · MTIME'), ('blkszbits', '0x0C · 12 → 4 KiB'),
      ('root_nid', '0x0E · 0'), ('inos', '0x10 · inode count'), ('epoch', '0x18 · compact mtime'), ('blocks_lo', '0x24 · block count'),
      ('meta_blkaddr', '0x28 · zone start · 1'), ('feature_incompat', '0x50 · CHUNKED_FILE · DEVICE_TABLE'), ('extra_devices', '0x56 · slot count'),
      ('devt_slotoff', '0x58 · 9')]
sc = d.row(40, [(t, s, 120) for t, s in SB], fill='orange', gap=8)

d.rowlabel('Bootstrap\nLayout', 270, h=70)
d.group(170, 250, 570, 125, '', 'yellow-bg')
d.text(ang('block 0 · checksum covers block 0 · > 23 slots ⇒ meta_blkaddr 2'), 180, 342, 550, 26, **F)
d.box('unused', 180, 265, 90, 70, 'grey', sub='1 KiB', **NF)
sb = d.box('Superblock', 280, 265, 160, 70, 'orange', sub='@1024 · 128 B')
dev = d.box('Device Table', 450, 265, 280, 70, 'green', sub='@1152 · 128 B slots')
mz = d.group(760, 250, 440, 125, '', 'yellow-bg')
d.text('inode-metadata zone · starts at meta_blkaddr × 4 KiB', 770, 342, 420, 26, **F)
d.text('data blocks · addr = i_u.startblk × 4 KiB', 1210, 342, 350, 26, **F)
root = d.box('root inode', 770, 265, 130, 70, 'yellow', sub='nid 0')
d.box('inodes …', 910, 265, 210, 70, 'yellow', sub='breadth first · inode · xattrs · chunk indexes · tail')
d.box('pad', 1130, 265, 60, 70, 'grey', sub='to 4 KiB', **NF)
d.box('dir blocks', 1210, 265, 170, 70, 'blue', sub='full dirent blocks')
d.box('symlink blocks', 1390, 265, 170, 70, 'blue', sub='FLAT_PLAIN')
d.dotted(sc[0], sb, (.5, 1), (.5, 0))
d.elbow(sc[4], root, 125, '× 32 B', (.5, 1), (.5, 0), pos=-0.3)
d.elbow(sc[8], mz, 145, '× 4 KiB · zone start', (.5, 1), (0, 0))
d.elbow(sc[11], dev, 165, '× 128 B = 1152', (.5, 1), (0, 0))
d.elbow(sc[10], dev, 185, '× 128 B', (.5, 1), (.5, 0))

d.rowlabel('ErofsDeviceSlot\n128 B', 430, w=140)
d.brace(450, 730, 400, up=False)
DS = [('tag', '0x00 · 64 B · SHA256 hex', 200), ('blocks_lo', '0x40 · 4 B · device blocks', 170), ('uniaddr_lo', '0x44 · 4 B · mapped blkaddr', 230),
      ('blocks_hi', '0x48 · 2 B · 0', 130), ('uniaddr_hi', '0x4A · 2 B · 0', 130), ('_reserved', '0x4C · 52 B', 130)]
last = d.row(430, DS)[-1]
n = d.note('nydus check --bootstrap <bootstrap>', 1260, 445, 300, 30, 'grey'); d.dotted(last, n, (1, .5), (0, .5))
d.out(OUT, 'nydus-disk-bootstrap')

# ====================== D3. on-disk · cache dir (FUSE) ======================
d = Diagram()
d.rowlabel('Cache dir\nper blob', 40, h=70)
bd = d.box(ang('<hex>.blob.data'), 170, 40, 420, 70, 'blue', sub=ang('device image · sparse · <hex> = SHA256(full blob)'))
d.box(ang('<hex>.blob.meta'), 610, 40, 270, 70, 'yellow', sub='NDBLMETA · from the tar · else via footer')
gm = d.box(ang('<hex>.group.map'), 900, 40, 300, 70, 'yellow', sub='NDGRPMAP · MAP_SHARED')
d.box(ang('<hex>.prefetch.lock'), 1220, 40, 210, 70, 'grey', sub='flock')

d.brace(170, 590, 135, up=False)
d.box('chunk group 0', 170, 175, 130, 60, 'blue', sub='ready', **NF)
d.box('hole', 310, 175, 100, 60, 'grey', sub='not fetched', **NF)
d.box('chunk groups 2–5', 420, 175, 160, 60, 'blue', sub='one fetch', **NF)
d.box('hole', 590, 175, 80, 60, 'grey', **NF)
d.box('…', 680, 175, 60, 60, 'blue', **NF)
d.text('addr = blkaddr × 4 KiB · written after decode + crc32c', 170, 245, 700, 24, **F)
# .group.map (chunk_group_map.rs): 4 KiB header then one bit per chunk group, MAP_SHARED, atomic bit ops.
# The bits below mirror the .blob.data example above: chunk group 0 ready, 1 not, 2–5 ready, 6 not.
d.rowlabel(ang('<hex>.group.map\nheader · 4 KiB'), 340, w=140, size=13)
GH = [('magic', '0x00 · 8 B · "NDGRPMAP"', 210), ('feature_compat', '0x08 · 4 B', 150), ('feature_incompat', '0x0C · 4 B', 150), ('chunk_group_count', '0x10 · 4 B', 180),
      ('ready_count', '0x14 · 4 B · atomic', 160), ('state', '0x18 · 4 B · bit 0 ALL_READY', 210), ('reserved', '0x1C · to 4 KiB', 130)]
gh = d.row(340, GH, fill='orange')
d.elbow(gm, gh[0], 300)

d.rowlabel('bitmap\n1 bit per chunk group', 450, w=140, size=13)
BITS = [('0', '1', 'ready'), ('1', '0', ''), ('2', '1', 'ready'), ('3', '1', 'ready'), ('4', '1', 'ready'), ('5', '1', 'ready'), ('6', '0', ''), ('…', '', '')]
for k, (n_, b, sb) in enumerate(BITS):
    d.box(b if b else '…', 170 + k * 110, 450, 100, 60, 'yellow' if b == '1' else 'grey', sub=f'chunk group {n_}' if n_ != '…' else '', **NF)
d.out(OUT, 'nydus-disk-cache')
