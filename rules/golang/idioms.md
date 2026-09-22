---
paths:
  - "**/*.go"
---

# Go idioms

Reference codebase: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly). Language guides where they don't contradict: [Effective Go](https://go.dev/doc/effective_go), [Google Go Style: Decisions](https://google.github.io/styleguide/go/decisions), [Uber Go Style](https://github.com/uber-go/guide/blob/master/style.md). When they disagree, dragonfly wins. This file is language constructs and concurrency correctness. Errors and panic: `errors.md`. Limits, sizing and contention: `performance.md`.

```go
// Producer-side interface, unexported struct, constructor returns the interface.
type GC interface {
	Add(Task) error
	Run(string) error
	Stop()
}

func New(options ...Option) GC { return &gc{tasks: &sync.Map{}, done: make(chan struct{})} }

// A goroutine has an owner: ticker, ctx, done, Stop.
func (g *gc) Start(ctx context.Context) {
	tick := time.NewTicker(g.interval)
	defer tick.Stop()
	for {
		select {
		case <-tick.C:
			g.runAll(ctx)
		case <-ctx.Done():
			return
		case <-g.done:
			return
		}
	}
}

func (g *gc) Stop() { close(g.done) }
```

## Methods and receivers

- Pointer receivers by default. Value receivers only on small named non-struct types: `func (h HostType) Name() string`.
- One receiver kind per type. The `sql.Scanner`/`driver.Valuer` pair in `manager/models` (`Value` on value, `Scan` on pointer) is the accepted exception; the value receivers on `pkg/gc`'s struct are legacy.
- Implement `Stringer` on enums and value types that get logged (`*Digest`, `*NetAddr`, `TaskSizeLevel`).

## Interfaces

- Interfaces live producer-side, in the file of their one implementation, because mockgen reads that file. Exported interface, unexported struct, constructor returns the interface: `func New(...) (Resource, error)`. Types never mocked return the struct: `(*Database, error)`, `(*Server, error)`.
- Parameters accept the interface (`gc gc.GC`, `resource resource.Resource`), never the concrete manager.
- Keep interfaces small; single-method ones (`Runner`, `Searcher`, `Preheat`) are the best. `manager/service.Service` at 88 methods is legacy: add to it only when the handler layer needs the method.
- Every interface gets a mockgen mock (placement: `layout.md`). No `var _ Iface = (*impl)(nil)`; the constructor's return type already fails the build.
- Compose by embedding interfaces in interfaces or in a struct (`manager/job.Job` embeds `Preheat`, `SyncPeers`, `Task`).

## Type assertions and switches

- Comma-ok on anything from outside the package; log and skip on mismatch. A bare `rawTask.(*Task)` is acceptable only when unwrapping a value this package stored in its own `sync.Map`. JWT claims, plugins, `proto.Clone` and `Any` always use comma-ok.
- `switch req := req.GetRequest().(type)` for protobuf `oneof` dispatch; `switch x { case A, B: }` instead of `if/else if` chains on strings.

## Embedding

- Embed to inherit a map or shared fields: `*sync.Map` in the managers with typed siblings (`normals`, `seeds`) as named fields; `BaseModel` in every gorm model; `base.Options` with `yaml:",inline" mapstructure:",squash"` in component configs.
- The receiver of a promoted method is the inner type. To override behaviour, wrap and delegate; don't embed.

## Literals, slices, maps

- Keyed composite literals only. `&T{...}` for structs; `new(T)` only for `emptypb.Empty` returns and atomics (`new(atomic.Uint64)`). Design new types so the zero value works (`sync.Mutex`, `bytes.Buffer`, `atomic.*`).
- Sets in signatures are `pkg/container/set` (`Set[T]`, `SafeSet[T]`); a local `map[string]struct{}` inside one function is fine.
- `slices.Contains`, `slices.SortFunc`, `slices.Concat`, `maps.Clone` over hand loops. Return the appended slice. `len(x) == 0` for emptiness; `x == nil` only for pointers and errors.
- Don't delete from a map while ranging it; range a snapshot as `dag.DeleteVertex` does. Pass slices, never `*[N]T`.

## Control flow and functions

- `if err := f(); err != nil { return ... }` inline. Early return; no `else` after a `return`.
- Multiple returns over out-params. Named results only when the doc needs the name or a deferred closure sets it.
- `for { select { case <-tick.C: case <-ctx.Done(): return } }` is the long-running loop. A `default:` arm appears only as the non-blocking `ctx.Done()` probe at the top of a loop iteration, never to spin.
- Labeled `continue loop` for nested loops. The `goto retry` in the manager gRPC clients is legacy; write the loop.
- `defer` immediately after the acquire: `defer cancel()`, `defer tick.Stop()`, `defer mu.Unlock()`, `defer resp.Body.Close()`. Never inside a loop body; `manager/job/sync_peers.go` leaks a `cancel` per tick, `service_v2.go` shows the fix (`go func() { defer cancel() ... }()`).

## Initialization, enums, options

- `init()` only in `cmd/<bin>/cmd/root.go`, `internal/dflog` and the resolvers in `pkg/net/{ip,fqdn}`. Construct in `New`. New package-level vars are pure (`errors.New`, `regexp.MustCompile`, `slices.Concat`).
- Enums are typed `int` with `iota`, a `Name()`/`String()` switch, a sibling `XxxName` string constant block and a `ParseXxx(string)` that falls back to the default (`HostType`, `TaskSizeLevel`). Everything else is typed string constants. Each constant carries a doc comment.
- Functional options (`type Option func(*T)`, `WithXxx`, variadic last) for small `pkg/` libraries (`gc`, `dfpath`, `oci/auth`, `announcer`) and typed variants (`PeerOption`, `ParseOption`). Components take `*config.Config` first; no options on them.

## Blank identifier

- `_, err :=` and `for range` freely. Blank imports for gorm drivers and swagger model references in `manager/handlers`, each commented. Dropped errors: `errors.md`.

## Concurrency

- Lifecycle by communicating: a `done chan struct{}` closed by `Stop()`, paired with `Serve()`. Counters and flags are `atomic.*`, not channels. Every goroutine takes `ctx`, exits on `ctx.Done()`, and has an owner that waits for it.
- `errgroup.WithContext` over `sync.WaitGroup`; use the derived `ctx` it returns (9 of 14 sites discard it; don't copy them).
- Channel direction in function signatures when a side only sends or only receives: `done <-chan struct{}`.
- `sync.Once` for close-once and lazy init; `atomic.Pointer[T]` for hot-swapped config (`dynconfig`); `sync.Cond` is not used.
- Mutex is a zero-value field (`mu sync.RWMutex`), declared above the fields it guards with a comment naming them. `RWMutex` when reads dominate, `Mutex` otherwise. Never hold a lock across I/O, a channel op or a callback.
- `context.WithTimeout` from the request deadline, `defer cancel()` on the next line. `WithValue` only for request-scoped ids under typed keys (`gc.ContextKey`).

## Generics

- Constraints are `comparable` and `any`. A type parameter exists only where two or more concrete types share the algorithm today (`DAG[T]`, `Set[T]`, `Dynconfig[T]`, `sortParents[T]`).
- No generic utils package. `pkg/structure`, `pkg/math`, `pkg/types` are the whole helper surface; a new helper goes beside its siblings or in the package that owns the type.

## Printing

- `%s`/`%v` for values, `%d` for ints, `%q` for user-supplied strings in errors, `%#v` when logging a whole response struct (existing convention). `%w` only in `fmt.Errorf`.
- `String()` must not call itself through `%s`; convert first (`string(m)`). Forward variadics with `...`.
