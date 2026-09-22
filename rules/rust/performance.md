---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust performance

Reference codebase: [dragonflyoss/client](https://github.com/dragonflyoss/client) (`dragonfly-client-storage/src/{io,content_linux,page_cache,storage_engine/rocksdb}.rs`, `dragonfly-client-util/src/{buffer_pool,fs,pool,ratelimiter}`, `dragonfly-client/src/resource`). Community sources where they don't contradict: [The Rust Performance Book](https://nnethercote.github.io/perf-book/), [Effective Rust](https://effective-rust.com/) item 20, [Tokio: Bridging with sync code](https://tokio.rs/tokio/topics/bridging), [RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide), [Cloudflare Pingora](https://github.com/cloudflare/pingora) and [quiche](https://github.com/cloudflare/quiche) for connection reuse and transport, [TiKV](https://github.com/tikv/tikv) for RocksDB option layout, man pages `sendfile(2)`, `posix_fadvise(2)`, `fallocate(2)`, `sync_file_range(2)`, `tcp(7)`. When they disagree, the client repo wins.

The client is the data plane: every piece byte, disk write and peer socket goes through this workspace. Performance here is bytes per second per host at bounded CPU.

```rust
// Piece bytes come from the pool and go back on drop. No Vec<u8> per chunk.
let mut buffer = buffer_pool.take();
let n = tokio::task::spawn_blocking(move || file.read_at(&mut buffer, offset)).await??;

// Hash the buffer while its data is still hot in the cache of the core that filled it.
let mut hasher = crc32fast::Hasher::new();
hasher.update(&buffer);

// Bounded fan-out: one permit per in-flight piece, across several parents.
let semaphore = Arc::new(Semaphore::new(config.download.concurrent_piece_count as usize));
let mut join_set = JoinSet::new();

// Upload straight from the file descriptor on Linux, copy_buf elsewhere.
#[cfg(target_os = "linux")]
sendfile_range(&stream, fd, offset, remaining).await?;
```

## 1. Method

- Set the target first ("N GiB/s per host at M tasks under X% CPU"). It says when to stop.
- Profile before changing code. `docs/performance-optimization.md`: `oha` against a reference file server, `cargo build --profile profiling`, `cargo flamegraph --pid <dfdaemon>`. In-binary: `pprof` CPU and `jemalloc_pprof` heap endpoints in `dragonfly-client/src/stats`, `tokio-console` at `log_level = TRACE`.
- Microbenchmarks are `criterion` with `harness = false` in `<crate>/benches/` (`dragonfly-client-storage/benches/`), `black_box` on inputs and outputs. No `#[bench]`. Whole-system numbers come from `oha`; p99 and throughput before/after go in the PR.
- Production truth is Prometheus (`dragonfly-client-metric`): durations as histograms with `exponential_buckets(1.0, 2.0, 24)`, traffic as counters, concurrency as gauges. A new hot path gets rate, errors and duration there, and ships with the metric that would show its regression.
- Two fixes for a hot function: make it faster, or call it less. Remove silly slowdowns before adding clever speedups. Revert changes that measure flat. Write the measurement above the optimization: `// 99% of tasks have one piece in flight here, so ...`.

## 2. Build and runtime

- Profiles in the root `Cargo.toml` are fixed. `release`: `opt-level = 3`, `lto = "fat"`, `codegen-units = 1`, `panic = "abort"`, `strip = "symbols"`. `profiling`: release plus `debug = true`, `strip = false`, `panic = "unwind"`. `bench`: `debug = true`. `dev`: `opt-level = 0`, `incremental = true`. No `[profile.*]` change in a feature PR.
- `.cargo/config.toml` sets only `--cfg tokio_unstable`. No `target-cpu=native`: binaries ship to arbitrary x86_64 and aarch64 hosts; instruction-set dispatch is the library's job (`crc32fast`, `aws-lc-rs`).
- PGO and BOLT are not used. If adopted via `cargo-pgo`: profile from an `oha` run at production concurrency, rebuild in the release pipeline, re-measure per release.
- Allocator: jemalloc (`tikv_jemallocator`) in `dfdaemon` only, profiling on in debug via `malloc_conf`, `JEMALLOC_SYS_WITH_LG_PAGE=16` on arm64. Other binaries keep the system allocator. No `mimalloc`.
- Runtime: `#[tokio::main]` default multi-thread, no `worker_threads`, no `Builder`. CPU count is `std::thread::available_parallelism()`. No `num_cpus`.

## 3. Algorithms and data structures

Pick by access pattern and by n. Small n favours the flat structure.

| Need | Use | Client example |
|---|---|---|
| Shared map, many writers, keyed by id or address | `DashMap` | `Pool`, backend clients, parent bandwidth weights |
| Shared map, rare writes, snapshot reads | `Arc<RwLock<HashMap>>` | scheduler hashring, dynconfig block list |
| Bounded LRU, O(1) eviction | `lru::LruCache`; intrusive raw-pointer LRU in `cache/lru_cache.rs` for the piece cache | fd cache, TLS certs, in-memory pieces |
| FIFO with both-end ops | `VecDeque` | idle `TcpStream`s, page-cache drop queue |
| Weighted random choice | `rand::distr::weighted::WeightedIndex` | `parent_selector.rs` |
| Rolling statistics window | fixed bucket ring of atomics | `RollingWindow` in `ratelimiter/bbr.rs` |
| Stable key to server routing | `hashring::HashRing<VNode>` | `grpc/scheduler.rs` |
| Ordered iteration or range by key | RocksDB prefix column family, `create_fixed_prefix(64)` | pieces of a task |
| Point lookup by key | RocksDB point-lookup column family | task metadata |
| Membership before disk | RocksDB bloom filter, 10 bits per key | every SST |
| Payload bytes | `bytes::Bytes` from `buffer_pool` | pieces in flight |
| One-time static | `std::sync::LazyLock` | metrics, regexes, cert caches |

- Not in the tree and not wanted without a benchmark: `BTreeMap`, `BinaryHeap`, `LinkedList`, `SmallVec`, `IndexMap`, `ahash`/`FxHash`, `once_cell`, skip lists, lock-free queues.
- `Vec` and slices beat maps below a few dozen elements and beat linked structures always. Sort once, then binary-search or scan.
- Ordered keys belong in RocksDB (sorted prefix iteration, bloom filters, compression); don't mirror its index in a `BTreeMap`.
- Hash by purpose: `crc32fast` for piece integrity (SIMD, 4 bytes), `sha256` for content-derived ids, `SipHash` for `HashMap` keys unless a profile shows hashing. No `md5` or `blake3` for new code.
- Trees for ordering and ranges; hashes for identity; rings for stable placement; bloom filters for "definitely absent". Name the property you need before choosing.

## 4. Memory and allocation

- Payload moves as `bytes::Bytes` from `dragonfly-client-util/src/buffer_pool`: bounded staging buffers returned via `Bytes::from_owner` on last drop, zeroing skipped with a documented `unsafe set_len`. No `Vec<u8>` per chunk, no `to_vec()` or `clone()` of a payload; cloning `Bytes` is a refcount bump.
- Presize: `Vec::with_capacity`, `String::with_capacity`, `DashMap::with_capacity`. Hoist the collection out of the loop and `clear()` it; take `&mut Vec` in rather than return a fresh one.
- File I/O is unbuffered by default. Wrap in `BufReader::with_capacity`/`BufWriter::with_capacity` using the existing constants: storage read and write buffers 2 MiB, proxy read 2 MiB, `TRANSFER_WRITE_BUFFER_SIZE` 8 MiB. `flush()` a `BufWriter` explicitly.
- `Cow<'static, str>` for mostly-literal messages. Box the large variant when `large_enum_variant` fires; keep per-piece structs small.
- Memory budgets follow the cgroup (`cgroups-rs`, `sysinfo`): piece cache `storage.cacheCapacity` 64 MiB, RocksDB block cache 1 GiB, page-cache drop threshold 80%. Size against the container, not the node.
- If `malloc`/`free` are hot in the flamegraph, cut the allocation rate before switching allocators.

## 5. CPU

- Hash in the same pass: `crc32fast::Hasher::update` on the buffer before it goes to the blocking write (`io.rs`). A second read for the digest is a review finding. `sha2` streams over a `BufReader` for content ids.
- Hardware acceleration is library-level: `crc32fast` picks SSE4.2/PCLMULQDQ or NEON at runtime, `aws-lc-rs` gives AES-NI and SHA-NI. No `asm` features, hand SIMD or `unsafe` intrinsics.
- No compression on the wire: every `reqwest::Client` sets `.no_gzip().no_brotli().no_zstd().no_deflate()`. Pieces are content-addressed and often already compressed. LZ4 lives only inside RocksDB.
- prost on gRPC; `serde_json` only for config, metadata values and the CLI. Stream bodies (`hyper::body::Incoming`, `StreamReader`) instead of `to_bytes()` on a whole response.
- `#[inline]` only on `default_*` config fns and tiny `bbr.rs` helpers. No `#[inline(always)]` or `#[cold]`; fat LTO with one codegen unit already sees across crates.
- Tracing cost: a span per piece at INFO allocates; per-piece paths are `level = "debug"` (`style.md`). No `format!` in a debug line on a hot path. Regexes and certs are `LazyLock`; `SystemTime::now()` once per operation.

## 6. Concurrency limits and contention

Correctness rules (which mutex, guards across `.await`, cancellation): `idioms.md`. This section is sizing.

- Never block a worker. Every syscall that can block runs in `tokio::task::spawn_blocking`: `pread`, `pwrite`, `open`, `fallocate`, every `fadvise`. Pure CPU work over ~100µs (a full-file digest) too. No `rayon`.
- Fan-out is `JoinSet` + `Semaphore` with a config or named bound: `concurrent_piece_count` 8, `back_to_source_concurrent_piece_count` 8, `MAX_CONCURRENT_DROP_COUNT` 16, dfget `max_concurrent_requests`. No unbounded `tokio::spawn` per item, no `FuturesUnordered`/`buffer_unordered`.
- Channels have named capacities and a send timeout: `DOWNLOAD_STREAM_BUFFER_SIZE` 12, sync-pieces 128, proxy 4, `send_timeout(REQUEST_TIMEOUT)`. Backpressure is a full bounded channel, never a growing `Vec`.
- Contention: shard by key with `DashMap` before lock-free code; atomics for counters; duplicate cheap work rather than synchronise it.
- Coalesce identical work structurally: one downloader per address via `Pool` (`DashMap::entry`), one download per task via the metadata state machine (`uploading_count`, `is_finished`), one backend client per cert set. No `singleflight` crate.
- Batch syscalls: `pwritev` gathers up to `MAX_WRITE_IOVECS` 1024 buffers; `sync_file_range` in `Async` mode queues durability; the page-cache dropper drains a `VecDeque` per pass. Syscalls per piece, not per byte.
- Deadlines are configured, not invented: connect 2s TCP / 3s gRPC, `REQUEST_TIMEOUT` 10s, `pieceTimeout` 360s.

## 7. Disk and filesystem I/O

- All disk I/O goes through the page cache: no `O_DIRECT`, `O_SYNC` or `mmap`. The kernel cache is the shared read cache across tasks; DIO would need a user-space cache, alignment and readahead. Steer it with `posix_fadvise` (`dragonfly-client-util/src/fs`): `Sequential` on every cached read fd, `WillNeed` before a piece read, `DontNeed` after a piece is served or written. `page_cache.rs` drops pieces in download order past 80% cgroup memory, only inside a cgroup with a limit.
- Positional I/O only: `read_at`/`write_all_at` on an `Arc<File>` via `RangeReader` and `write_range` (`io.rs`), `pwritev` for gathered writes. Never `seek`; descriptors are shared by the fd cache.
- Preallocate with `fallocate(KEEP_SIZE)` (retry `EINTR`, skip on `ENOTSUP`). Durability is `sync_file_range` under `WritebackMode::{Async, Sync, Off}` (default `Async`); never `sync_all`/`sync_data` on the piece path.
- Open through the fd cache (`fs/fd.rs`, `DEFAULT_FD_CACHE_CAPACITY` 1024, separate read and write LRUs). Task reuse is a hard link with `fs::copy` fallback; no reflink or `copy_file_range`.
- File to socket is `sendfile` on Linux (`server/tcp.rs`, `MAX_SENDFILE_COUNT` `0x7fff_f000`, driven by `writable()` + `try_io`) fed by `RangeReader::into_parts()`; `tokio::io::copy_buf` elsewhere. No user-space read/write loop for uploads.
- Content under the task id, metadata in RocksDB. Never thousands of files in one directory; never a metadata read that opens a file.

## 8. Dependency tuning

Every library ships defaults for a laptop. Each dependency on the data path has its knobs set once, in one place, as named constants with a reason; the defaults you left alone are a decision too. Change a value with a measurement, never the shape. [TiKV](https://github.com/tikv/tikv) and [Pingora](https://github.com/cloudflare/pingora) are the reference for how a config struct carries library options.

| Library | Where | Set | Deliberately default |
|---|---|---|---|
| `rocksdb` | `storage_engine/rocksdb.rs` | `Lz4` all levels; `increase_parallelism(available_parallelism())`, `max_background_jobs = max(p, 2)`; `optimize_level_style_compaction` 64 MiB point-lookup CFs / 512 MiB prefix CFs; `set_use_fsync(false)`, `bytes_per_sync` 2 MiB; LRU block cache 1 GiB, `block_size` 64 KiB, `cache_index_and_filter_blocks`, `pin_l0_filter_and_index_blocks_in_cache`; bloom 10 bits; `create_fixed_prefix(64)` + `memtable_prefix_bloom_ratio(0.25)` on prefix CFs; one CF per object type; logs 64 MiB × 10 | `max_open_files`, direct I/O, `rate_limiter`, `optimize_filters_for_hits`, `level_compaction_dynamic_level_bytes`, universal compaction |
| `tokio` | binaries | `#[tokio::main]` multi-thread; `--cfg tokio_unstable` for console | `worker_threads`, `max_blocking_threads`, `event_interval` |
| `tonic` client | `grpc/*.rs` | `buffer_size` 512 KiB, `connect_timeout` 3s, `timeout` 10s, `tcp_keepalive` 3600s, `http2_keep_alive_interval` 300s, `keep_alive_timeout` 20s; `INITIAL_WINDOW_SIZE` 512 KiB, `INITIAL_CONNECTION_WINDOW_SIZE` 4 MiB in `grpc/mod.rs` | `max_decoding_message_size`, `concurrency_limit` |
| `tonic` server | `grpc/dfdaemon_*.rs` | `max_frame_size` 256 KiB, `tcp_keepalive`, `http2_keepalive_interval`/`_timeout`, BBR `rate_limit(...)` layer | `concurrency_limit_per_connection`, `max_concurrent_streams` |
| `hyper` server | `proxy/mod.rs` | `keep_alive(true)`, `max_buf_size(proxy.readBufferSize)` 2 MiB, `set_nodelay(true)` on the accepted socket | `http2_max_concurrent_streams` |
| `reqwest` | `backend/src/{lib,http}.rs` | one client per cert set; `pool_max_idle_per_host` 1024, `tcp_keepalive` 60s, `tcp_nodelay(true)`, HTTP/2 keepalive 300s / 20s, stream and connection windows 16 MiB, hickory DNS, all decompression off, `reqwest_retry::ExponentialBackoff` × `backend.maxRetries` 1 | `connect_timeout`, `timeout` (deadline is per request) |
| `quinn` | `storage/src/{server,client}/quic.rs` | `BbrConfig` congestion, `send_window`/`receive_window`/`stream_receive_window` 16 MiB, `keep_alive_interval` 3s, `max_idle_timeout` 30s | `initial_mtu`, `max_concurrent_bidi_streams`, ack frequency |
| `socket2` | `storage/src/{server,client}/tcp.rs`, `util/src/net` | `set_tcp_nodelay(true)`, keepalive 3s / 5s / 3 retries, `listen(1024)`, 16 MiB send and receive hints, TFO via `setsockopt` behind `storage.server.tcpFastopen` | `TCP_CONGESTION`, `SO_REUSEPORT`, `SO_REUSEADDR` |
| `rustls` | `util/src/tls` | `aws-lc-rs` provider, TLS 1.2 + 1.3, self-signed cert LRU | session tickets, early data |
| `leaky-bucket` | `util/src/ratelimiter` | `BANDWIDTH_LIMITER_REFILLS_PER_SECOND` 10, `fair(true)`, capacity from `*.bandwidthLimit` (50 GB/s default, prefetch 10 GB/s) | |
| `tikv-jemallocator` | `bin/dfdaemon/main.rs` | global allocator, `malloc_conf` profiling in debug, `JEMALLOC_SYS_WITH_LG_PAGE=16` on arm64 | `background_thread`, `dirty_decay_ms` |
| `lru` / `DashMap` | `fs/fd.rs`, `pool`, `backend` | fd cache 1024, `Pool` capacity 2000 and idle 60s / 600s, `DashMap::with_capacity(MAX_CONNECTIONS_PER_ADDRESS)` | |
| `tracing` | `tracing/mod.rs` | level from config, `skip_all` on every span, OTLP exporter timeout | subscriber buffer sizes |

- A tuned instance regresses harder when hardware or workload changes (RocksDB's own warning). Watch the library's stats (`rocksdb.stats`, tokio-console, connection pool gauges) before and after.
- A knob exposed to users is a config field with a `default_xxx()` and a `///` explaining the tradeoff; a knob that never changes is a `const` with a doc comment. Neither is a literal in the call.
- Keys in RocksDB are `namespace + id` so one prefix extractor serves every CF; related writes go in a `WriteBatch`; reads iterate a prefix, never the whole DB.

## 9. Network I/O

Parameter values: section 8. This section is design.

- One TCP flow does not fill a 25 or 100 GbE link (per-flow congestion window, one core, one NIC queue). Throughput comes from many flows: `concurrent_piece_count` permits across several parents chosen by `WeightedIndex` over live bandwidth (`parent_selector.rs`, unknown parent weight 10 Gbps). Raise the piece or parent count before touching a socket option.
- Connections are pooled at two layers and never dialed per piece: `dragonfly-client-util/src/pool` (`DashMap` by address, `RequestGuard` refcount, idle eviction) holding piece downloaders whose idle timeout is twice the connection idle so the downloader outlives its streams, and `storage/src/client/tcp.rs` with a per-address `VecDeque` of idle `TcpStream` and `peek` liveness. A new remote goes through `Pool`.
- Protocols by role: pieces over raw TCP framing (default `download.protocol = "tcp"`) or QUIC via `quinn`, one stream per connection so head-of-line blocking never touches a piece; control over gRPC/HTTP/2 (`tonic`); source fetches over HTTP/1.1 and /2 (`reqwest`, `hyper`).
- Congestion control is the kernel's for TCP and BBR in user space for QUIC, the one place the client chooses the algorithm. Nagle is off everywhere because the tail segment of a response must not wait. TFO is opt-in and needs `net.ipv4.tcp_fastopen = 3` on the host.
- HTTP clients are shared `Arc`s built once per certificate set; DNS is `hickory` so a resolver cache exists per process; retries are exponential backoff with a configured cap.
- TLS is `rustls` with `aws-lc-rs`. No `ring`, no OpenSSL.
- Rate limits at two levels, both stay: `leaky-bucket` bandwidth limiters acquired per piece for download, prefetch and back-to-source, and the adaptive BBR admission limiter (`ratelimiter/bbr.rs`) wrapping every gRPC server (400 req/s download and upload, 4000 proxy, buffer 50). Load shedding returns early, never queues unboundedly.

## 10. Caching

- Tiers, fastest first: in-memory piece cache (64 MiB LRU, preheated tasks), page cache (steered by `fadvise`), local disk, a parent peer, the source. Each tier has a size or TTL and a hit metric.
- Policies: LRU for piece, fd and cert caches; RocksDB block cache LRU with pinned index and filters; second-chance CLOCK in the page-cache dropper. No LFU, ARC or TinyLFU here; the Go manager uses TinyLFU where frequency skew matters.
- Prefetch is explicit and rate-limited (`proxy.prefetchRateLimit` 10 GB/s); readahead is `fadvise(WillNeed)` per piece, not a background reader. `backend.cacheTemporaryRedirectTtl` 600s is the only HTTP-level cache.

## 11. Metadata and GC

- RocksDB is the only local database; metadata reads on the piece path are point lookups with bloom filters. No SQLite, `sled` or flat files.
- GC runs on `gc.interval` 900s with `taskTtl` 30 days, disk watermarks 80% / 60%, `pageCacheIdleTimeout` 2400s. Expensive cleanup belongs there, never on the request path.

## 12. Serialization and wire format

- prost for gRPC, the custom piece framing over TCP/QUIC (`client/tcp.rs`), `serde_json` for RocksDB values and config. Pieces never travel inside a protobuf message; they stream on their own connection.
- Zero copy through the stack: `Bytes` from the pool into `sendfile` or the framed writer; `BytesMut` from the pool into `write_all_at`. A `Vec<u8>` between socket and file is a copy a profile will show.
- `bytesize` and `humantime-serde` parse once at config load; the hot path sees `u64` and `Duration`.

## 13. Observability cost

- Prometheus, OTLP tracing (W3C context over gRPC), `pprof`/jemalloc endpoints and `tokio-console` are opt-in per deployment.
- Spans per connection and per task, `debug` per piece; attributes are cheap values, not formatted strings; sampling is the collector's job.

## 14. Kernel and platform

- Linux is the target: `sendfile`, `fadvise`, `fallocate`, `sync_file_range`, TFO, cgroup v1/v2 accounting. Each behind `#[cfg(target_os = "linux")]` with a portable fallback so macOS builds.
- Host tuning the daemon expects but does not set: `net.ipv4.tcp_fastopen = 3` when TFO is on, `nofile` above fd cache plus connections, THP at the distro default. Document such expectations in the config field's `///`.
- Not used, by decision: `io_uring` (`tokio-uring`, `glommio`, `monoio`), `O_DIRECT`, `mmap`, DAX, SPDK, DPDK, XDP, `MSG_ZEROCOPY`, `splice`, `copy_file_range`, hugepages, NUMA pinning, `core_affinity`. The blocking pool plus page cache plus `sendfile` is the model; section 16 is the bar for changing it.

## 15. Technology selection

- Order: `std`, then a crate in `[workspace.dependencies]`, then a new crate. The stack: `tokio`, `hyper`/`hyper-util`/`hyper-rustls`, `tonic`, `quinn`, `reqwest` + `reqwest-middleware`/`reqwest-retry`, `rustls` + `aws-lc-rs`, `hickory`, `rocksdb`, `opendal`, `oci-client`, `dashmap`, `lru`, `leaky-bucket`, `bytes`, `crc32fast`, `sha2`, `rustix`/`libc`, `socket2`, `cgroups-rs`, `sysinfo`, `hashring`, `fastrand`, `tikv-jemallocator`, `prometheus`, `tracing`, `serde*`, `clap`, `validator`, `thiserror`/`anyhow`.
- A new crate needs: a `criterion` or `oha` benchmark against the incumbent, active maintenance, `default-features = false` with the features used, MSRV within `rust-toolchain.toml`, an Apache-2.0-compatible license, and one PR paragraph naming the alternatives. Tokio, Cloudflare or TiKV using it is evidence, not proof.
- Decisions already made: embedded KV with prefix iteration over SQL or `sled`; user-space QUIC where congestion control matters, kernel TCP otherwise; `rustls` over OpenSSL (no C toolchain); jemalloc for fragmentation in a long-lived process; `DashMap` over `RwLock<HashMap>` for write-heavy maps; blocking pool over `io_uring` for portability.
- Never replace a `std` component (`HashMap`, `sort`, `SipHash`) for speed without a profile that puts it in the top 10.

## 16. Bar for a new mechanism, and anti-patterns

Anything in section 14's "not used" list, a different allocator or runtime, `TCP_CONGESTION`, `SO_REUSEPORT`, socket buffer tuning, or a hand-written data structure needs, in the PR: a flamegraph or `oha` run showing the current path is the bottleneck, a before/after number on the same hardware, a config field default off, `#[cfg(target_os = "linux")]` with today's path as fallback, and one doc comment citing the measurement. Without all five, use the existing pattern.

- Optimising without a profile; benchmarking a debug build; no `black_box` so the work is optimised away.
- A blocking syscall or CPU loop on a tokio worker; `std::thread::sleep` in async code.
- Unbounded `tokio::spawn` per item; an unbounded channel; a future without a deadline.
- `Vec<u8>` per chunk; `to_vec()`/`clone()` of a payload; a second read for a digest; `seek` on a shared fd.
- `format!` or a span per piece on a hot path; `#[instrument]` without `skip_all`.
- Dialing per piece; one flow for a whole file; compression on the piece path.
- Changing a library knob, socket option or profile in a feature PR without a number; `unsafe` for speed without a `SAFETY` comment and a number.
- Mirroring RocksDB's ordering in a `BTreeMap`; a new dependency for what `std` or the workspace already provides.
