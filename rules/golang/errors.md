---
paths:
  - "**/*.go"
---

# Go errors

Reference: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly), [Uber Go Style: Errors](https://github.com/uber-go/guide/blob/master/style.md#errors).

- Return errors. `panic` only where the process cannot start (flag binding, embedded FS, hostname at init) or on a violated invariant in a constructor; never on a request path. `recover` only around gorm transactions (`manager/service/cluster.go`) and in gin's own middleware.
- Static message: `errors.New("invalid host")`. Dynamic with cause: `fmt.Errorf("init scheduler logger: %w", err)`, always `%w` so callers can `errors.Is`/`errors.As`. Sentinels are `var ErrXxx = errors.New(...)`.
- Message style: lowercase, no trailing punctuation, names the operation: `"init scheduler logger: %w"`, `"load all persistent peers failed: %w"`. Don't churn existing `"... failed: %w"` messages.
- Compare with `errors.Is(err, io.EOF)`, never string matching.
- gRPC handlers return `status.Error(codes.NotFound, "...")` / `status.Errorf(...)`. Map internal errors to codes there, not deeper. Dragonfly-typed errors cross the gRPC boundary through `internal/dferrors` (`dferrors.New`, `ConvertGRPCErrorToDfError`).
- Handle each error once. Service layer: log with context, then return (`logger.WithTaskID(id).Errorf(...)` then `return nil, status.Error(...)`). Libraries: return only.
- Never `_ = err` silently. An intentionally dropped error has a comment above the line saying why it is safe: `// "config" is a flag-only key, not part of the config struct.` then `_ = viper.BindEnv("config")`.
- Startup failures propagate to `RunE` as `error`; `Execute()` logs and calls `os.Exit(1)`. Nothing else exits.
