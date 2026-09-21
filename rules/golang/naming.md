---
paths:
  - "**/*.go"
---

# Go naming

Reference: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly), then [Google Go Style Decisions](https://google.github.io/styleguide/go/decisions#naming).

## Casing

- MixedCaps everywhere. Underscores only in `_test.go` test names and generated code. Constants are `DefaultPeerConcurrentUploadLimit`, never `DEFAULT_...`.
- Initialisms keep one case: `ID`, `IP`, `URL`, `GC`, `TTL`, `FSM`, `TLS`, `HTTP`. `HostID`, `TaskID`, `PeerID`, `GetTaskId()` only where protobuf generated it.
- Files are snake_case: `host_manager.go`, `host_manager_test.go`, `host_manager_mock.go`, `service_v2.go`, `client_v2.go`.

## Types and constructors

| Thing | Pattern | Example |
|---|---|---|
| Interface | noun or role, exported | `HostManager`, `Resource`, `Scheduling`, `Evaluator`, `Announcer`, `Job` |
| Implementation | same name, unexported | `hostManager`, `resource`, `scheduling` |
| Constructor | `New` for the package's main type, `newXxx` for the rest | `scheduler.New(...)`, `newHostManager(...)` |
| Mock | mockgen output | `MockHostManager`, `MockHostManagerMockRecorder` |
| Enum type | typed int | `HostType`, `TaskType` |
| Enum value | type prefix | `HostTypeNormal`, `HostTypeSuperSeed` |
| Enum name string | value + `Name` | `HostTypeNormalName = "normal"` |
| Default | `Default` prefix | `DefaultLogDir`, `DefaultSeedPeerConcurrentUploadLimit` |
| Config section | noun + `Config` | `ServerConfig`, `GCConfig`, `ManagerConfig`, `DynConfig` |
| Option | `Option` / `WithXxx` | `HostOption`, `WithLogDir`, `WithPluginDir` |
| gRPC service impl | version | `V1`, `V2` in package `service`, files `service_v1.go`, `service_v2.go` |
| Sentinel error | `Err` prefix | `ErrNotFound`; unexported `errNotFound` |

## Methods

- Map-like managers mirror `sync.Map`: `Load`, `Store`, `LoadOrStore`, `Delete`, `Range`, `Len`, plus `LoadAll`, `LoadRandom`, `RangeSeeds`.
- No `Get` prefix on getters: `h.Len()`, `peer.ID`. Use `Load`/`Fetch` when it can miss or block.
- Predicates read as questions: `IsSeedPeer`, `IsPieceBackToSource`, `NeedBackToSource`.
- GC hooks are `RunGC(context.Context) error`. Lifecycle is `Serve() error` / `Stop()`.
- Receiver: first letter of the type, never `this`/`self`.

## Packages and imports

- Package names short, lowercase, singular: `idgen`, `digest`, `dfpath`, `dfnet`, `dflog`, `dferrors`, `set`, `dag`, `ip`, `fqdn`. Dragonfly-specific helpers take a `df` prefix.
- Never `util`, `common`, `helper`. Group by family instead: `pkg/net/ip`, `pkg/container/set`, `pkg/graph/dag`.
- Don't repeat the package in the identifier: `idgen.PeerID()`, `dfpath.New()`, `set.NewSafeSet[string]()`.
- Import aliases: `logger` for dflog, `pkggc` when `gc` collides with a local, `commonv2`/`schedulerv2` for versioned protobuf, `managerclient` for `pkg/rpc/manager/client`.

## Tests and fixtures

- Test funcs are `TestType_Method`: `TestHostManager_Load`, `TestHost_NewHost`, `TestTaskManager_newTaskManager`.
- Case names are lowercase phrases: `"load host"`, `"host does not exist"`, `"new host manager failed because of gc error"`.
- Package-level fixtures take a `mock` prefix: `mockHost`, `mockHostGCConfig`, `mockRawHost`.
- Loop variable is `tc`; recorder param is `m`; controller is `ctl`.

## Variables

- Length scales with scope: `h`, `p`, `t` receivers; `i` index; `rawHost, loaded := h.Map.Load(key)` for comma-ok; full words at package level.
- `loaded`/`ok` for comma-ok booleans. `req`/`resp` for gRPC messages. `cfg` for config pointers, `d` for dfpath, `svr` for servers.
- Don't shadow predeclared identifiers (`len`, `new`, `error`, `copy`).
