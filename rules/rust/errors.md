---
paths:
  - "**/*.rs"
---

# Rust errors

Reference: [dragonflyoss/client `dragonfly-client-core`](https://github.com/dragonflyoss/client/tree/main/dragonfly-client-core/src), [Rust API Guidelines C-GOOD-ERR](https://rust-lang.github.io/api-guidelines/interoperability.html#c-good-err), [Effective Rust](https://effective-rust.com/) items 4 and 18.

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
}

pub type Result<T> = std::result::Result<T, DFError>;
```

## Error type

- One `thiserror` enum for the workspace in `dragonfly-client-core`, re-exported as `dragonfly_client_core::{Error, Result}`. Every crate imports those two names; nobody defines a local `Result` or error type.
- Messages lowercase, no trailing punctuation, carrying the identifier: `"task {0} not found"`, `"invalid uri {0}"`. Every variant has a `/// The error when ...` doc.
- Std and library errors wrap with `#[error(transparent)] Xxx(#[from] ...)` so `?` converts them. Third-party errors without `From` go through `Error::BackendError(...)`, `Error::ExternalError(...)` or the `OrErr` extension: `.or_err(ErrorType::ParseError)?`.
- A new failure mode is a new variant carrying the id as `String`, not a new type. Context attaches by consuming chains: `.with_context(...)`, `.with_cause(...)`.
- Binaries use `anyhow` (`async fn main() -> Result<(), anyhow::Error>`, `.context("...")`). `anyhow` never appears in library crates.

## Handling

- Library code propagates with `?`; transforms (`ok_or_else`, `map_err`) at the boundary where the typed variant is known.
- Log where the error is handled, then return it once. Don't log the same error twice up the stack.
- Fallible constructors return `Result<Self>`. Validation happens in `Config::load` via `validator`; downstream code trusts the config.
- Never `let _ = fallible()`. Handle it, or log it with a reason.

## Panics

- Release builds set `panic = "abort"`: a panic kills the daemon. No `panic!`, `assert!`, `unreachable!` on request paths.
- `unwrap()`/`expect()` are acceptable in `main.rs` wiring, on `LazyLock` statics (`.expect("metric can be created")`) and in tests. On a request path they are a review finding; `config.host.ip.unwrap()` after `Config::load` validated the field is tolerated, with the validation as the reason.
- `todo!()` exists only in unimplemented gRPC stubs and `unimplemented!()` in read-only `Backend::put`. A new stub returns `Err(Error::Unimplemented)`.
- Integers from the network or headers use `try_into()` or `saturating_*`, never a bare `as`.
