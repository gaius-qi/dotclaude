---
paths:
  - "**/*.go"
---

# Go style

Reference codebase: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (`scheduler/`, `manager/`, `pkg/`). Community guides where it doesn't contradict: [Uber Go Style](https://github.com/uber-go/guide/blob/master/style.md), [Google Go Style](https://google.github.io/styleguide/go/decisions). When they disagree, dragonfly wins.

## File skeleton

```go
/*
 *     Copyright 2025 The Dragonfly Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * ...
 */

//go:generate mockgen -destination host_manager_mock.go -source host_manager.go -package standard

package standard

import (
	"context"
	"sync"

	"github.com/spf13/cobra"

	commonv2 "d7y.io/api/v2/pkg/apis/common/v2"

	logger "d7y.io/dragonfly/v2/internal/dflog"
	pkggc "d7y.io/dragonfly/v2/pkg/gc"
	"d7y.io/dragonfly/v2/pkg/types"
)
```

- Apache 2.0 block-comment header on every `.go` file. `//go:generate` sits between header and `package`.
- Imports in four `gci` groups: stdlib, third party, `d7y.io/api`, this module. Alias only for collisions or clarity: `logger`, `pkggc`, `commonv2`, `schedulerv2`, `managerclient`.
- Every type, func, method, const, and struct field has a doc comment. Full sentence, starts with the name, ends with a period. Interface methods are documented; the implementation repeats the same comment.
- Struct fields: one comment per field, blank line between fields.
- Function bodies use short step comments before each block: `// Initialize logger.`, `// Validate config.`

## Interface, implementation, constructor

```go
// HostManager is the interface used for host manager.
type HostManager interface {
	// Load returns host for a key.
	Load(string) (*Host, bool)

	// Store sets host.
	Store(*Host)
}

// hostManager contains content for host manager.
type hostManager struct {
	// all host map.
	*sync.Map

	// seeds host map.
	seeds *sync.Map
}

// New host manager interface.
func newHostManager(cfg *config.GCConfig, gc pkggc.GC) (HostManager, error) {
	h := &hostManager{Map: &sync.Map{}, seeds: &sync.Map{}}
	if err := gc.Add(pkggc.Task{ID: GCHostID, Interval: cfg.HostGCInterval, Runner: h}); err != nil {
		return nil, err
	}

	return h, nil
}
```

- Exported interface `HostManager`, unexported struct `hostManager`, constructor returns the interface. Package-level entry point is `New(...)`; secondary types use `newXxx`.
- Every interface gets a mockgen mock: `x_mock.go` in the same package, or `mocks/x_mock.go` with `-package mocks` for `pkg/` and `internal/` libraries.
- Receiver is the first letter of the type (`h`, `m`, `s`, `p`, `t`, `v`), consistent across the file.
- Constructors with many params break the signature across lines, grouped by type: `id, ip, name, hostname string, port, downloadPort, proxyPort int32,`.
- Struct literals name every field, aligned. Atomic counters are `new(atomic.Uint64)`.
- Blank line before a final `return` when the function body has more than one block.

## Options, enums, config

```go
type Option func(d *dfpath)

// WithLogDir set the log directory.
func WithLogDir(dir string) Option {
	return func(d *dfpath) { d.logDir = dir }
}

func New(options ...Option) (Dfpath, error)
```

```go
const (
	// HostTypeNormal is the normal type of host.
	HostTypeNormal HostType = iota

	// HostTypeSuperSeed is the super seed type of host.
	HostTypeSuperSeed
)
```

- Functional options: `type Option func(*T)`, `WithXxx`, variadic `options ...Option` last. Type-specific options are `HostOption`, `PeerOption`.
- Enums: typed `int` with `iota`, each constant documented. String names live in a sibling `const` block as `HostTypeNormalName = "normal"`.
- Config structs live in `<component>/config/config.go`. Every field has `yaml:"camelCase" mapstructure:"camelCase"` tags and a comment. Defaults are `Default*` constants, applied in `config.New()`. `Validate() error` and `Convert() error` are methods on `*Config`.
- Config YAML templates (`deploy/docker-compose/template/*.yaml`) mirror the struct: camelCase keys, `# Comment.` above every key, disabled options kept as `# # comment` / `# key: value`, empty strings as `''`.

## Logging and runtime

- Import `logger "d7y.io/dragonfly/v2/internal/dflog"`. Plain: `logger.Infof`, `logger.Errorf`, `logger.Warnf`. Contextual: `logger.WithTaskID(id).Infof(...)`, `logger.WithPeer(...)`, `logger.WithHostID(...)`, `logger.WithHostnameAndIP(...)`. Messages lowercase, no trailing period.
- `context.Context` first, named `ctx`. `ctx, cancel := context.WithCancel(...)` followed immediately by `defer cancel()`.
- Long-running loops guard with `select { case <-ctx.Done(): return ctx.Err() default: }` at the top.
- Concurrent maps are `sync.Map` (embedded or as a field). Counters are typed `atomic.*`. Singletons use `sync.Once` (`cache.Do`).
- `init()` only in `cmd/<bin>/cmd/root.go` to wire cobra flags and `dependency.InitCommandAndConfig`. Nowhere else.
- Commands: `main.go` is three lines calling `cmd.Execute()`. `root.go` `RunE` does Convert → Validate → init dfpath → init logger → `runXxx(ctx, ...)`. `os.Exit(1)` only in `Execute()`.

## Tooling

- `make fmt vet lint test` before finishing. `.golangci.yml` v2: `errcheck`, `goconst`, `gocyclo`, `govet`, `misspell`, `staticcheck`; formatters `gci` + `gofmt`.
- `make generate` after changing any interface with a `//go:generate mockgen` line.
- Prefer stdlib. Dragonfly's existing deps first: `cobra`/`viper`, `zap` via `dflog`, `grpc`/`status`, `testify`, `go.uber.org/mock`, `google/uuid`, `gorm`, `gin`, `redis`. Add nothing new without a reason.
