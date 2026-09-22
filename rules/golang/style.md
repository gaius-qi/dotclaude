---
paths:
  - "**/*.go"
---

# Go style

Reference codebase: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (`scheduler/`, `manager/`, `pkg/`). Community guides where they don't contradict: [Uber Go Style](https://github.com/uber-go/guide/blob/master/style.md), [Google Go Style](https://google.github.io/styleguide/go/decisions). When they disagree, dragonfly wins. This file is file shape, formatting, config, logging, command wiring and tooling. Names: `naming.md`. Comments: `comments.md`. Language constructs: `idioms.md`.

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

- Apache 2.0 block-comment header on every `.go` file, then directives, then `package`.
- Imports in four `gci` groups: stdlib, third party, `d7y.io/api`, this module. Alias only for collisions or clarity: `logger`, `pkggc`, `commonv2`, `schedulerv2`, `managerclient`.

## Formatting

```go
// New host manager interface.
func newHostManager(cfg *config.GCConfig, gc pkggc.GC) (HostManager, error) {
	h := &hostManager{Map: &sync.Map{}, seeds: &sync.Map{}}
	if err := gc.Add(pkggc.Task{ID: GCHostID, Interval: cfg.HostGCInterval, Runner: h}); err != nil {
		return nil, err
	}

	return h, nil
}
```

- `gofmt` output, tabs. Struct literals name every field, aligned, one per line when more than two.
- Long signatures break across lines grouped by type: `id, ip, name, hostname string, port, downloadPort, proxyPort int32,`.
- Blank line before a final `return` when the body has more than one block. Blank line between struct fields and between interface methods.

## Config

```go
// Config is the scheduler config.
type Config struct {
	// Server port.
	Port int `yaml:"port" mapstructure:"port"`
}
```

- One `Config` per component in `<component>/config/config.go`. Every field has `yaml:"camelCase" mapstructure:"camelCase"` tags. Defaults are `Default*` constants applied in `config.New()`. `Validate() error` and `Convert() error` are methods on `*Config`.
- YAML templates in `deploy/docker-compose/template/*.yaml` mirror the struct: camelCase keys, `# Comment.` above every key, disabled options kept as `# # comment` / `# key: value`, empty strings as `''`.

## Logging

- Import `logger "d7y.io/dragonfly/v2/internal/dflog"`. Plain: `logger.Infof`, `logger.Warnf`, `logger.Errorf`. Contextual: `logger.WithTaskID(id)`, `logger.WithPeer(...)`, `logger.WithHostID(...)`, `logger.WithHostnameAndIP(...)`. Messages lowercase, no trailing period.
- `context.Context` is the first parameter, named `ctx`.

## Commands

- `cmd/<bin>/main.go` is three lines calling `cmd.Execute()`. `cmd/<bin>/cmd/root.go` holds the cobra command; `RunE` runs Convert → Validate → init dfpath → init logger → `runXxx(ctx, ...)`. `init()` there registers flags and calls `dependency.InitCommandAndConfig`.

## Tooling

- `make fmt vet lint test` before finishing. `.golangci.yml` v2 enables `errcheck`, `goconst`, `gocyclo`, `govet`, `misspell`, `staticcheck`; formatters `gci` and `gofmt`.
- `make generate` after changing any interface that has a `//go:generate mockgen` line. `make swag` after changing a `manager/handlers` annotation.
- Dependency policy: `performance.md`, Technology selection.
