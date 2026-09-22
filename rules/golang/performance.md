---
paths:
  - "**/*.go"
  - "**/go.mod"
---

# Go performance

Reference codebase: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (`scheduler/`, `manager/`, `pkg/rpc`, `pkg/cache`, `pkg/graph/dag`). Community sources where they don't contradict: [go-perfbook](https://github.com/dgryski/go-perfbook), [Go GC Guide](https://go.dev/doc/gc-guide), [Go PGO](https://go.dev/doc/pgo), [Go Diagnostics](https://go.dev/doc/diagnostics), [Uber Go Style: Performance](https://github.com/uber-go/guide/blob/master/style.md#performance), [containerd](https://github.com/containerd/containerd) and [kubernetes](https://github.com/kubernetes/kubernetes) for gRPC, pooling and cache shape. When they disagree, dragonfly wins.

The Go tree is the control plane. No bulk bytes flow through it: piece I/O, uploads, disk and sockets live in the Rust client. A change that must move file or network payload belongs in `client/`, not here.

```go
// Sample first, then filter. Never walk every peer of a task.
candidateParents := peer.Task.LoadRandomPeers(uint(config.DefaultSchedulerFilterParentLimit))

// Score once, sort once. The comparator never calls the score function.
scoredParents := make([]scoredParent[T], len(parents))
for i, parent := range parents {
	scoredParents[i] = scoredParent[T]{parent: parent, score: score(parent)}
}
slices.SortFunc(scoredParents, func(a, b scoredParent[T]) int { return cmp.Compare(b.score, a.score) })

// Coalesce concurrent dials to one target into a single connection.
client, err, _ := p.sf.Do(target, func() (any, error) { return GetClientByAddr(target, opts...) })

// Bounded fan-out from a request-supplied, validated limit.
eg, ctx := errgroup.WithContext(ctx)
eg.SetLimit(int(req.ConcurrentTaskCount))
```

## 1. Method

- Set the target first ("N peers scheduled under T ms at P99"). It says when to stop.
- Profile before changing code. `--pprof-port` starts statsview with the pprof handlers (default `-1`, off). CPU: `top -cum`; `runtime.mallocgc` above 15% or `gcAssistAlloc` above 5% means allocation. Heap: `alloc_space` for GC pressure, `inuse_space` for leaks. Block and mutex profiles for contention. `GODEBUG=gctrace=1` for GC cadence.
- Benchmark beside the code (`pkg/cache/cache_test.go`, `pkg/graph/dag/dag_test.go`): `b.ResetTimer()` after setup, `b.ReportAllocs()`, `b.RunParallel` for concurrent structures, production-shaped inputs. `go test -bench . -benchmem -count 10 | benchstat old new`; only a significant delta counts, and it goes in the PR.
- Production truth is Prometheus (`scheduler/metrics/metrics.go`): latency as `Summary` with objectives `{0.5, 0.9, 0.95, 0.99}`, throughput as `CounterVec`, saturation as `GaugeVec`. A new hot path gets rate, errors and duration there, and ships with the metric that would show its regression.
- Amdahl: 2x on a 5% routine is 2.5%. Ask first whether the routine can run less often. Revert changes that measure flat. Write the assumption above an optimization: `// 15 candidates is enough because ...`.

## 2. Build and runtime

- `hack/build.sh`: `CGO_ENABLED=0`, `-ldflags "-X d7y.io/dragonfly/v2/version.*"`, `GOTAGS`/`GOGCFLAGS` passed through. Static binary on Alpine; no cgo anywhere.
- `go build -gcflags=-m=2 2>&1 | grep escapes` answers allocation questions; boxing into an interface and closure capture are the usual escapes.
- PGO is not used. If adopted: a 30s CPU profile from production (never a microbenchmark), committed as `cmd/<bin>/default.pgo`, refreshed each release. Expected 2 to 14%; measure it.
- Runtime knobs are deploy-time only: `GOMAXPROCS` via the helm `maxProcs` value (the CPU quota), `GOMEMLIMIT` at the container limit minus 5 to 10% with `GOGC` on; `GOGC=off` only when the process owns the cgroup. No `runtime.GOMAXPROCS`, `debug.SetGCPercent`, `debug.SetMemoryLimit`, `automaxprocs` or ballast in code.
- `-race` in `make test` only. `go 1.25` in `go.mod`; use `slices`, `maps`, `cmp`, `min`/`max`, range-over-int. No toolchain bump in a feature PR.

## 3. Algorithms and data structures

Pick by access pattern and by n. Small n favours the flat structure.

| Need | Use | Dragonfly example |
|---|---|---|
| Concurrent map, read-mostly, keyed by id | `sync.Map` | `hostManager`, `peerManager`, `taskManager` |
| Typed subsets of a concurrent map | parallel `sync.Map`s | `hostManager.{Map, normals, seeds}` |
| Set | `pkg/container/set` | `Set[T]`, `SafeSet[T]` |
| Ordered selection over a small list | slice + `slices.SortFunc` + `cmp.Compare` | `evaluator_default.go` |
| Random sample of n from a concurrent map | `Range` with presized slice, `return false` at n | `hostManager.LoadRandom`, `dag.GetRandomVertices` |
| Ancestry with cycle checks | `pkg/graph/dag`, batched `CanAddEdges` | peer parent graph |
| Stable key to server routing | consistent hashing (`stathat.com/c/consistent`) | `pkg/balancer`, keyed by task ID |
| In-process cache with TTL | `pkg/cache` | scheduler, manager |
| Query cache over gorm | sharded LRU `go-freelru` + xxhash | `manager/database/cacher.go` |
| Local tier in front of Redis | `TinyLFU` via `go-redis/cache` | `manager/cache` |
| Timestamps under concurrency | `pkg/atomic` `Time`/`Duration` | `Peer.UpdatedAt`, `Peer.Cost` |
| Counters and flags | `atomic.Uint64`, `atomic.Int32`, `atomic.Bool` | upload counts, state |
| Dedupe of concurrent identical work | `singleflight.Group` | dfdaemon client pool |

- Not in the tree and not wanted without a benchmark: `container/list`, `container/heap`, B-trees, skip lists, bloom filters (RocksDB has them on the client side), lock-free structures, `ristretto`/`bigcache`.
- Slices beat maps below a few dozen elements and beat `container/list` always. `int` and `string` map keys are runtime-specialised; `byte`/`uint16` keys are not, use a slice.
- Pointer-free slices and maps (`[]uint64`, `map[string]struct{}`) are skipped by the GC. Indices over pointers in graph structures when mark time shows.
- Sort or bucket once what will be scanned repeatedly. Trade space for time with a precomputed index (`hostManager.normals`) rather than a filter per read.
- Trees for ordering and ranges; hashes for identity; rings for stable placement; bloom filters for "definitely absent". Name the property you need before choosing.

## 4. Memory and allocation

- Presize: `make([]*Host, 0, len(hosts))`, `make(map[string]struct{}, len(ids))`. Bare `make([]T, 0)` before a known-length loop is a review finding. Reuse in loops with `buf = buf[:0]`.
- `strconv` and `net.JoinHostPort` over `fmt.Sprintf` on request paths (`resource/standard/*.go` has none). `strings.Builder` with `Grow` for concatenation; hoist `[]byte("literal")` out of loops.
- Sentinel errors and one `%w` wrap at the boundary; never `fmt.Errorf` inside a per-peer loop.
- Struct layout: largest fields first, pointers first, hot fields in the first 64 bytes; check with `fieldalignment` for per-peer structs. Pad sharded locks to a cache line only when false sharing shows.
- Interfaces box: a small struct passed as `any` or `error` allocates. Keep concrete types on hot paths.
- `sync.Pool` is unused. Add it only with `mallocgc` on top of the profile and a `-benchmem` delta; one type per pool, reset on `Put`. If a Go byte path is ever unavoidable, copy containerd's content store: `sync.Pool` of 1 MiB `[]byte` fed to `io.CopyBuffer`.
- zap has no sampling and no level guards: `Debugf` arguments are always evaluated. No string or slice built for a debug line in a per-piece loop.
- Size in-process caches as a fraction of the container limit and export hit ratio; a large cache is GC mark time.

## 5. CPU

- Hashes: `xxhash` for cache keys, `sha256` via `pkg/digest` for content, `google/uuid` and `pkg/idgen` for ids. No `md5` for new identifiers.
- protobuf on the wire, `encoding/json` only for Redis fields and job args. No `sonic`/`jsoniter` without JSON in the top 10 of a profile. Marshalling is grpc-go's job.
- No `reflect`, `encoding/binary` on structs or `fmt` verbs per request. Regex and templates compile once at package level. `time.Now()` once per request, passed down.
- TLS is stdlib `crypto/tls` (AES-NI and SHA-NI automatic). Compression is off on gRPC. No cgo or assembly for speed.
- Trust the compiler: no manual unrolling, hoisting or shift-for-multiply. Check inlining with `-gcflags=-m`; keep hot helpers under the inline budget instead of annotating.
- Check the cheap special case first (`len(candidates) == 0`, one candidate). Order `switch` cases by frequency on a hot dispatch.

## 6. Concurrency limits and contention

Correctness rules (ownership, `ctx`, `defer`, locks across I/O): `idioms.md`. This section is sizing.

- Every fan-out is bounded: `errgroup.SetLimit` from a validated request field (`ConcurrentTaskCount` at most 100, `ConcurrentPeerCount` at most 1000, defaults 8 / 500) or a named constant (`GroupJobStateConcurrencyLimit = 10`). No `semaphore` package, no worker-pool type.
- Channels are unbuffered or size 1. A larger buffer needs a named constant and an explicit drop policy with a log line (`AuditBufferSize = 1000`). Backpressure is a blocking send under `select` on `ctx.Done()`, never a growing slice.
- Contention: shard a hot map by key hash before lock-free code; `RWMutex` only when reads dominate; reference counts are atomics. Duplicate cheap work rather than synchronise it.
- Timers: `time.NewTicker` in loops; `time.After` inside a loop leaks a timer per iteration.
- Batch per-item Redis and DB writes behind the worker goroutine (`CreateInBatches`, `FindInBatches`), not per peer.
- Scheduler request path is O(15): sample `DefaultSchedulerFilterParentLimit` candidates, keep `DefaultSchedulerCandidateParentLimit` (3). GC of peers, hosts and tasks runs on `pkg/gc` tickers at 10s, 5m, 30m with `Timeout` at most `Interval`; expensive cleanup goes there, never on the request path.

## 7. Disk and filesystem I/O

Not in this tree. `os.OpenFile` appears only for log redirection. No `O_DIRECT`, `Fadvise`, `Fallocate`, `mmap`, positional I/O, `sendfile`, `splice`, `io_uring`. Page cache, DIO, DAX, SPDK and NUMA are covered in `rules/rust/performance.md`; a Go change that needs a file byte path is misplaced.

## 8. Dependency tuning

Every library ships defaults for a laptop. Each dependency on a request path has its knobs set once, in one place, as `Default*` constants or config fields with a reason; the defaults you left alone are a decision too. Change a value with a measurement, never the shape. [containerd](https://github.com/containerd/containerd) and [kubernetes client-go](https://github.com/kubernetes/client-go) are the reference for how a config struct carries library options.

| Library | Where | Set | Deliberately default |
|---|---|---|---|
| `grpc-go` server | `pkg/rpc/*/server/server.go` | `MaxRecvMsgSize`/`MaxSendMsgSize` `math.MaxInt32`; `KeepaliveParams{MaxConnectionIdle: 10m, MaxConnectionAge: 12h, MaxConnectionAgeGrace: 5m}`; `rate.NewLimiter(4000, 4000)` interceptor with health excluded; `otelgrpc` stats handler | `InitialWindowSize`, `InitialConnWindowSize`, `ReadBufferSize`/`WriteBufferSize`, `NumStreamWorkers`, `MaxConcurrentStreams`, `KeepaliveEnforcementPolicy` |
| `grpc-go` client | `pkg/rpc/*/client/` | `grpc.NewClient`; `MaxCallRecvMsgSize`/`MaxCallSendMsgSize` `math.MaxInt32`; `grpc_retry` 3 × `BackoffLinear(500ms)`; consistent-hashing balancer via `BalancerServiceConfig`; `WithIdleTimeout` 5m (dfdaemon) / 0 (scheduler) | `WithKeepaliveParams`, `WithConnectParams` |
| `net/http` | `pkg/oci/image.go`, `pkg/net/http` | `Timeout` 1m; `Transport{MaxIdleConns: 400, MaxIdleConnsPerHost: 20, MaxConnsPerHost: 50, IdleConnTimeout: 120s}`; `Dialer{Timeout: 30s, DualStack: true, Control: safeSocketControl}` | `ForceAttemptHTTP2`, `TLSHandshakeTimeout`, `ResponseHeaderTimeout`, `Dialer.KeepAlive` |
| `go-redis` | `<component>/config/constants.go`, `resource/persistent*/` | `PoolSize` 20, `PoolTimeout` 10s, `Scan` count 10 | `MinIdleConns`, `ConnMaxIdleTime`, read/write timeouts |
| `gorm` | `manager/database` | `Preload`; `FindInBatches`/`CreateInBatches`; unique indexes in tags; query cache via `go-gorm/caches` + `go-freelru` 1024 entries × 30s TTL, sharded by xxhash | `SetMaxOpenConns`/`SetMaxIdleConns`, prepared-statement cache |
| `go-redis/cache` | `manager/cache` | `TinyLFU(cfg.Cache.Local.Size, cfg.Cache.Local.TTL)` local tier in front of Redis | |
| `pkg/cache` | scheduler, manager | TTL per entry, janitor interval, `Scan(m, n)` | |
| `x/time/rate`, `redis_rate` | `pkg/rpc/interceptor.go`, `internal/ratelimiter` | 4000 rps/burst per server; `redis_rate.PerSecond` per cluster for preheat | |
| `zap` via `dflog` | `internal/dflog` | atomic levels `Info` core / `Warn` grpc, runtime-switchable; rotation `DefaultLogRotateMaxSize` 1024 MB | sampling, `Debugf` guards |
| `errgroup` | job and service layers | `SetLimit` from validated request fields or named constants (section 6) | |
| `machinery` | `internal/job` | `GroupJobStateConcurrencyLimit` 10, caller-supplied `req.Timeout` | broker prefetch, result TTL |

- A tuned client regresses harder when the deployment changes. Read the library's own metrics (grpc-go channelz, `go-redis` `PoolStats`, gorm slow-query log) before and after.
- A knob exposed to users is a config field with a `Default*` constant and a comment naming the tradeoff; a knob that never changes is a named constant. Neither is a literal at the call site.

## 9. Network I/O

Parameter values: section 8. This section is design.

- Never dial per request. The pool shape is `pkg/rpc/dfdaemon/client/client.go`: `sync.Map` keyed by target, `singleflight.Group` around the dial, a 5m ticker evicting connections not `Connecting` or `Ready`. A new client type copies it.
- One shared `*http.Client` per purpose, always with a `Timeout`, dialing through `pkg/net/http.NewSafeDialer()` (SSRF guard, keep it). Drain and close every body so the connection returns to the pool.
- Rate limits: in-process token bucket on servers, distributed `redis_rate` per cluster for preheat jobs. Client retries use backoff with jitter; never a retry storm on `Unavailable`.
- Flow control, buffers and stream limits stay at grpc-go defaults until a benchmark says otherwise.
- Single-flow bandwidth, congestion control, `TCP_NODELAY`, TFO, `SO_REUSEPORT`, QUIC and socket buffers are the Rust client's domain. The Go tree sets none; kernel and grpc-go defaults apply. DNS is the stdlib resolver.

## 10. Caching and coalescing

- Tiers, fastest first: in-process (`pkg/cache`, freelru, TinyLFU), Redis, SQL. Each tier has a TTL and a hit-ratio metric.
- LRU for recency-skewed keys, TinyLFU for frequency-skewed with scan resistance. No ARC or CLOCK in Go.
- Stampede protection is `singleflight.Group`: one in-flight fetch per key in front of any dial, Redis miss or DB miss that many goroutines can trigger. `Forget` the key on an error you don't want shared.
- Negative-cache frequent expensive misses with a short TTL. `cacher.go` rebuilds its LRU on any write, acceptable at 1024 entries; a bigger cache invalidates by key.

## 11. Database and Redis access

- Redis loaders today are `SMembers` then `HGetAll` per entity; a new bulk read uses `Pipelined` or `MGET`, never another N+1. Stale-key GC runs on the `pkg/gc` tickers, not on the request path.
- gorm: `Preload` against N+1, batch APIs for bulk, indexes declared in tags, limit and cursor pagination. No query inside a loop, no wide `SELECT *` for three fields.

## 12. Serialization and wire format

- protobuf for every RPC; JSON only where Redis or machinery needs text. A new streaming RPC streams items, it does not send every peer in one message.
- Convert `[]byte`/`string` once, not per iteration. Compare fields, don't marshal to compare. gRPC compression stays off unless benchmarked.

## 13. Observability cost

- pprof (statsview), OTel tracing (`otelgrpc` on servers and clients) and Prometheus are opt-in per deployment.
- One span per request, not per candidate peer; no attributes built with `fmt.Sprintf`; sampling is the collector's job.

## 14. Kernel and platform

- Honour the cgroup: CPU quota drives `GOMAXPROCS`, memory limit drives `GOMEMLIMIT`. No sysctl, `ulimit`, THP or NUMA settings in the Go tree.

## 15. Technology selection

- Order: stdlib, then a dependency already in `go.mod` (`grpc-go`, `go-redis`, `gorm`, `gin`, `zap`, `cobra`/`viper`, `x/sync`, `x/time/rate`, `testify`, `go.uber.org/mock`, `machinery`, `go-freelru`, `go-redis/cache`, `stathat/consistent`), then a new one.
- A new dependency needs: a benchmark against the incumbent on the workload it replaces, active maintenance, no cgo, an Apache-2.0-compatible license, and one PR paragraph naming the alternatives. Kubernetes or containerd using it is evidence, not proof.
- Never replace a stdlib component (JSON, sort, map) for speed without a profile that puts it in the top 10.

## 16. Anti-patterns

- Optimising without a profile, or from a microbenchmark that doesn't match production input.
- Unbounded `go` per item; `time.After` in a loop; a channel buffer with no drop policy.
- `fmt.Sprintf`, `regexp.MustCompile`, `reflect`, interface boxing or `Debugf` string building inside a per-peer or per-piece loop.
- `append` without capacity in a known-length loop; `map[byte]T`; `defer` in a hot loop.
- Dialing per request; a new Redis N+1; a query in a loop.
- Tuning `GOGC` or `GOMAXPROCS` in code; changing a library knob without a number; adding cgo, assembly or `unsafe` for speed.
- Moving a byte path into Go that belongs in the Rust client.
