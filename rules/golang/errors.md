---
paths:
  - "**/*.go"
---

# Go errors

Reference: [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly), [Uber Go Style: Errors](https://github.com/uber-go/guide/blob/master/style.md#errors).

- Return errors, don't panic. `panic` only for programmer bugs that can't be recovered from.
- Static message: `errors.New("invalid host")`. Dynamic with cause: `fmt.Errorf("init scheduler logger: %w", err)`. Always `%w` so callers can `errors.Is`/`errors.As`.
- Message style: lowercase, no trailing punctuation, name the operation: `"init scheduler logger: %w"`, `"load all persistent peers failed: %w"`. Don't churn existing `"... failed: %w"` messages to a different form.
- Compare with `errors.Is(err, io.EOF)`, never string matching. Sentinels are `var ErrXxx = errors.New(...)`.
- gRPC handler boundaries return `status.Error(codes.NotFound, "...")` / `status.Errorf(codes.NotFound, "peer %s not found", id)`. Map internal errors to codes there, not deeper.
- Dragonfly-typed errors go through `internal/dferrors` (`dferrors.New`, `ConvertGRPCErrorToDfError`) when they must cross the gRPC boundary with a code.
- Handle each error once. In the service layer: log with context then return (`logger.WithTaskID(id).Errorf(...)` then `return nil, status.Error(...)`). In libraries: return only.
- Type assertions use comma-ok and log rather than panic on mismatch: `host, ok := value.(*Host); if !ok { logger.Error("invalid host"); return true }`.
- Never `_ = err` silently. If ignoring is intentional, say why in a comment.
- Startup failures propagate to `RunE` as `error`; `Execute()` logs and calls `os.Exit(1)`. Nothing else exits.
