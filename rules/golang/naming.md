---
paths:
  - "**/*.go"
---

# Go naming

Reference: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly), then [Google Go Style Decisions: Naming](https://google.github.io/styleguide/go/decisions#naming). Identifiers only; shapes live in `idioms.md`, test structure in `testing.md`.

## Casing

- MixedCaps everywhere. Underscores only in test function names and generated code. Constants are `DefaultPeerConcurrentUploadLimit`, never `DEFAULT_...`.
- Initialisms keep one case: `ID`, `IP`, `URL`, `GC`, `TTL`, `FSM`, `TLS`, `HTTP`. `GetTaskId()` only where protobuf generated it.
- Files are snake_case: `host_manager.go`, `host_manager_test.go`, `host_manager_mock.go`, `service_v2.go`.

## Declarations

| Thing | Pattern | Example |
|---|---|---|
| Interface | noun or role, exported | `HostManager`, `Resource`, `Scheduling`, `Evaluator`, `Announcer` |
| Implementation | same name, unexported | `hostManager`, `resource`, `scheduling` |
| Constructor | `New` for the package's main type, `newXxx` for the rest | `scheduler.New(...)`, `newHostManager(...)` |
| Mock | mockgen output | `MockHostManager`, `MockHostManagerMockRecorder` |
| Enum type / value / name string | typed int / type prefix / value + `Name` | `HostType`, `HostTypeNormal`, `HostTypeNormalName = "normal"` |
| Default | `Default` prefix | `DefaultLogDir`, `DefaultSeedPeerConcurrentUploadLimit` |
| Config section | noun + `Config` | `ServerConfig`, `GCConfig`, `DynConfig` |
| Option | `Option`, `XxxOption`, `WithXxx` | `HostOption`, `WithLogDir`, `WithPluginDir` |
| gRPC service impl | version suffix | `V1`, `V2` in `service_v1.go`, `service_v2.go` |
| Sentinel error | `Err` prefix | `ErrNotFound`, unexported `errNotFound` |
| Test function | `TestType_Method` | `TestHostManager_Load`, `TestTaskManager_newTaskManager` |
| Test case | lowercase phrase | `"load host"`, `"host does not exist"` |
| Test fixture | `mock` prefix | `mockHost`, `mockHostGCConfig`, `mockRawHost` |
| Benchmark | `BenchmarkType_Method` | `BenchmarkDAG_AddVertex` |

## Methods

- Map-like managers mirror `sync.Map`: `Load`, `Store`, `LoadOrStore`, `Delete`, `Range`, `Len`, plus `LoadAll`, `LoadRandom`, `RangeSeeds`.
- No `Get` prefix on getters: `h.Len()`, `peer.ID`. `Load`/`Fetch` when it can miss or block.
- Predicates read as questions: `IsSeedPeer`, `NeedBackToSource`. String conversion is `String()`, parsing is `ParseXxx`.
- GC hooks are `RunGC(context.Context) error`. Lifecycle is `Serve() error` / `Stop()`.
- Receiver is the first letter of the type, consistent across the file, never `this`/`self`.

## Packages and imports

- Short, lowercase, singular: `idgen`, `digest`, `dfpath`, `dfnet`, `dflog`, `set`, `dag`, `ip`. Dragonfly-specific helpers take a `df` prefix. Never `util`, `common`, `helper`; group by family instead (`pkg/net/ip`, `pkg/container/set`).
- Don't repeat the package in the identifier: `idgen.PeerID()`, `dfpath.New()`, `set.NewSafeSet[string]()`.
- Aliases: `logger` for dflog, `pkggc` when `gc` collides with a local, `commonv2`/`schedulerv2` for versioned protobuf, `managerclient` for `pkg/rpc/manager/client`.

## Variables

- Length scales with scope: `h`, `p`, `t` receivers; `i` index; full words at package level.
- `loaded`/`ok` for comma-ok booleans. `req`/`resp` for gRPC messages. `cfg` for config, `ctx` for context, `eg` for errgroup, `tc` for a test case, `ctl` for a gomock controller, `m` for a mock recorder.
- Don't shadow predeclared identifiers (`len`, `new`, `error`, `copy`).
