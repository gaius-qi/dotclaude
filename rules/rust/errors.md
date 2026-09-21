---
paths:
  - "**/*.rs"
---

# Rust errors

Reference: [dragonflyoss/client `dragonfly-client-core`](https://github.com/dragonflyoss/client/tree/main/dragonfly-client-core/src), [Rust API Guidelines C-GOOD-ERR](https://rust-lang.github.io/api-guidelines/interoperability.html#c-good-err).

```rust
/// The error for dragonfly.
#[derive(thiserror::Error, Debug)]
pub enum DFError {
    /// The error for IO operation.
    #[error(transparent)]
    IO(#[from] std::io::Error),

    /// The error when the task is not found.
    #[error{"task {0} not found"}]
    TaskNotFound(String),

    /// The error when the digest is mismatch.
    #[error{"digest mismatch expected: {0}, actual: {1}"}]
    DigestMismatch(String, String),
}

pub type Result<T> = std::result::Result<T, DFError>;
```

- One `thiserror` enum for the whole workspace in `dragonfly-client-core`, re-exported as `dragonfly_client_core::{Error, Result}`. Every crate imports those two names; nobody defines a local `Result`.
- Every variant has a `///` doc: `/// The error when ...`. Messages are lowercase, no trailing punctuation, and carry the identifier: `"task {0} not found"`, `"invalid uri {0}"`, `"no space left on device: {0}"`.
- Std and library errors wrap with `#[error(transparent)] Xxx(#[from] ...)` so `?` converts them. Third-party errors without `From` go through `Error::BackendError(...)`, `Error::ExternalError(...)`, or the `OrErr` extension: `.or_err(ErrorType::ParseError)?`, `.or_err(ErrorType::ConnectError)?`.
- Adding a new failure mode means adding a variant to `DFError`, not a new error type. New domain errors carry the id as `String`.
- Library code propagates with `?`. No `unwrap()`/`expect()` outside `main.rs` wiring and `#[cfg(test)]`.
- Log at the point where the error is handled, then return it: `error!("initialize fs operator failed: {}", err); return Err(err);`. Don't log the same error twice up the stack.
- Fallible constructors return `Result<Self>`. Validation happens in `Config::load` via `validator`; downstream code trusts the validated config.
- Binaries use `anyhow`: `async fn main() -> Result<(), anyhow::Error>`, `.context("...")` from `anyhow::Context`. `anyhow` never appears in library crates.
- Never `let _ = fallible()`. Handle it, or log it with a reason.
