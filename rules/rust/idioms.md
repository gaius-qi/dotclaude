---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust idioms

Reference codebase: [dragonflyoss/client](https://github.com/dragonflyoss/client). Language guides where they don't contradict: [Effective Rust](https://effective-rust.com/) (items numbered below), [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [Rust Design Patterns](https://rust-unofficial.github.io/patterns/), the [Tokio tutorial](https://tokio.rs/tokio/tutorial). When they disagree, the client repo wins. This file is language constructs, traits, concurrency correctness and dependency hygiene. Errors and panics: `errors.md`. Workspace layout: `layout.md`. Sizing and contention: `performance.md`.

```rust
/// The guard that returns the buffer to the pool on drop.
pub struct PooledChunk { buffer: Option<BytesMut>, pool: Arc<BufferPool> }

impl Drop for PooledChunk {
    fn drop(&mut self) {
        if let Some(buffer) = self.buffer.take() {
            self.pool.give_back(buffer);
        }
    }
}

// Builder when construction has optional knobs; otherwise new(...).
let pool = PoolBuilder::new(QUICClientFactory { config: config.clone() })
    .capacity(DEFAULT_DOWNLOADER_CAPACITY)
    .idle_timeout(DEFAULT_DOWNLOADER_IDLE_TIMEOUT)
    .build();

// Transforms over match; fail on the first error.
let content_length = response
    .content_length()
    .ok_or_else(|| Error::InvalidContentLength(url.to_string()))?;
let pieces = iter.map(|(_, value)| Piece::deserialize_from(&value)).collect::<Result<Vec<_>>>()?;
```

## Types (items 1 to 9)

- Enums carry state (item 1): `RangeReaderState { Idle, Reading(JoinHandle<..>) }`, `TaskIDParameter`. A `bool` pair or a `String` mode is an enum waiting to be written. A natural default is `#[derive(Default)]` + `#[default]` (`WritebackMode::Async`).
- Enum to and from text is hand-written `Display` and `FromStr` (`Algorithm`, `Scheme`, `Digest`) plus `#[serde(rename_all = "camelCase")]`. No `strum`.
- Newtypes (item 6) wrap behaviour, not ids: `Message(Cow<'static, str>)`, `RedactedDownload<'a>` for redacted `Debug`, `NoVerifier(Arc<CryptoProvider>)`. Ids stay `&str`/`String`, sizes `u64`, piece numbers `u32`, because they cross prost-generated types unchanged. Invariants live in structs with private fields and accessors (`Digest { algorithm, encoded }`).
- Builders (item 7) only when construction has optional knobs and no `new` makes sense: `pool::Builder` with `capacity(mut self) -> Self` … `build()`. Everything else is `pub fn new(config: Arc<Config>, ...)` plus `#[derive(Default)]`.
- Option and Result transforms over `match` (item 3): `?`, `ok_or_else` with a typed error, `map_err` at the boundary, `unwrap_or_default`/`unwrap_or_else`, `let ... else` for early return, `matches!` for a boolean on a variant. A two-arm `match` returning `Err` in one arm is a transform.
- Conversions (item 5): `#[from]` on error variants; hand-written `From` only for `Message` and API enum mapping; `TryFrom<Url>` for parsed URLs. `u64 as usize` is accepted on the 64-bit targets we ship; untrusted input follows `errors.md`.
- Pointers (item 8): `Arc<T>` for shared services and `Arc<Config>`; `Box<dyn Trait + Send + Sync>` for a registry of plugins; `Arc<dyn Downloader>` when shared across tasks; `impl Into<..>`/`impl IntoIterator` in arguments; `Result<impl Iterator<..>>` in returns. No `Rc`, `Weak` or `&dyn` parameters.
- Iterators over loops (item 9): `iter().filter().map().collect()`, `filter_map`, `collect::<Result<Vec<_>>>()`. `for i in 0..n` only when `i` is the data. No `itertools`.

## Traits (items 10 to 13)

- Trait objects for runtime dispatch across protocols and plugins (`Backend`, `Downloader`, `dylib` backends); generics for compile-time shape (`Metadata<E = RocksdbStorageEngine>`, `fn get<O: DatabaseObject>`). Choose by whether the implementation set is open at runtime (item 12).
- Async traits use `#[async_trait]`; one request struct in, `Result<Response>` out. Default method bodies keep the required surface small (item 13).
- Extension traits on foreign types for ergonomics (`impl<T, E> OrErr<T, E> for Result<T, E>`); blanket impls for lifetime erasure (`impl<T: for<'db> StorageEngine<'db>> StorageEngineOwned for T`).
- Standard traits (item 10): every data type derives `Debug, Clone`; `Default` when the zero value is meaningful; `PartialEq, Eq` for lookups and tests; `Hash` only for map keys; `Copy` for small enums; `Serialize, Deserialize` for anything persisted or configured. Manual `Debug` only to redact secrets. `PartialOrd`/`Ord` only when something sorts by it.
- `AsRef<[u8]>` on byte wrappers, `Deref` for a thin wrapper over an owned engine. Don't `Deref` to fake inheritance.
- RAII through `Drop` (item 11): every resource that must be returned has a guard (`PooledChunk`, `RangeReader`, `RequestGuard` in `Pool` and `bbr`, `LruCache`). A `release()` the caller must remember is a bug.
- Own types implement the I/O traits they are: `impl AsyncRead for RangeReader`, `impl Stream for ContentStream`. No operator overloading.

## Concepts (items 14 to 17, 19)

- Lifetimes (item 14): structs borrow only as short-lived views (`RedactedDownload<'a>`, `RequestGuard<'a>`); services own their data behind `Arc`. Elide with `'_`; HRTB only in the storage-engine abstraction.
- Borrowing (item 15): borrow in parameters, own in returns. `x.clone()` not `Arc::clone(&x)`. Cloning `Arc` and `Bytes` is free; cloning a `String` or `Vec` per piece is a review finding, and a clone that exists to satisfy the borrow checker gets a comment saying so.
- `unsafe` (item 16): five modules only, each behind a safe `pub fn`: `libc::setsockopt` for TFO, `set_len` in the buffer pool, `sync_file_range`, the intrusive `LruCache`, `libloading` for plugins. New `unsafe` needs a `// SAFETY:` line and a safe wrapper; `unsafe impl Send/Sync` needs the invariant written above it.
- Shared state (item 17): prefer message passing. `mpsc` for streams, `Notify` for wakeups, `Semaphore` for permits, `broadcast` for shutdown, `watch` for a changing value, `Barrier` for startup; `oneshot` is unused, use `Notify` or a `JoinHandle`. `std::sync::Mutex` (or `parking_lot` in `bbr.rs`) for short sync sections that never cross an `.await`; `tokio::sync::Mutex`/`RwLock` only when the guard must span an `.await`. `DashMap` over `Arc<Mutex<HashMap>>`. Never hold any guard across I/O.
- Cancellation: `tokio::select!` with shutdown in every accept loop; every outbound future has a `tokio::time::timeout` or a configured deadline. `Arc<AtomicBool>` for interrupt flags.
- Reflection (item 19): none. No `Any`, `type_name`, `downcast`; dispatch is enums or trait objects.

## Dependencies (items 21 to 26)

- Every dependency is declared once in `[workspace.dependencies]` and consumed with `xxx.workspace = true` (`layout.md`). Caret versions; exact pins only where the API breaks across patch releases (`dragonfly-api`, `tonic*`, `axum`, `opentelemetry*`). `default-features = false` with the features you use. A crate-local dependency is a review finding.
- No `[features]` and no `optional = true` (item 26). Platform variation is `cfg(target_os)` on the dependency and in code, never a feature flag.
- Visibility (item 22): `pub` only what another crate imports; otherwise private. `lib.rs` is `pub mod` lines plus a few `pub use`/`pub type`.
- No wildcard imports outside `use super::*` in tests (item 23). Re-export the workspace error type, not third-party types (item 24).
- Adding a crate: `performance.md`, Technology selection.

## Tooling (items 27 to 32)

- Lints (item 29): the gate is CI (`style.md`). `#[allow(clippy::too_many_arguments)]` is the accepted escape hatch for constructors; any other `#[allow]` needs a reason in the PR.
- Docs (item 27): `comments.md`. `#[must_use]`, `#[non_exhaustive]`, `#[deprecated]`, `#[doc(hidden)]` are unused today; a builder or guard type is a fair place for `#[must_use]`.
- Macros (item 28): one `macro_rules!` in the workspace. Prefer a function; a macro must remove repetition across many call sites. Derives in use: `serde`, `thiserror::Error`, `clap`, `validator::Validate`, `tabled::Tabled`.
- Tests beyond unit (item 30): inline `mod tests`, `cargo llvm-cov`, `criterion` benches, `mocktail` HTTP mocks, e2e in the Go repo (`testing.md`).
- One `build.rs` (git hash and build time). Keep build scripts to metadata.

## Beyond std (items 33 to 35)

- No `no_std`, no wasm. The one FFI edge is the plugin ABI: `#[no_mangle] pub fn register_plugin()` returning `Box<dyn Backend + Send + Sync>`, loaded via `libloading`. Keep it to that one symbol.
- Syscalls go through `rustix` (`pwritev`, `fallocate`, `fadvise`, `sendfile`) before `libc`; `libc` only where `rustix` lacks the call. No `bindgen`, no C.
- Platform gating is `#[cfg(target_os = "linux")]` at module or function level with a portable fallback, and whole-file swaps for large variants (`layout.md`). Target-gated crates sit under `[target.'cfg(...)'.dependencies]`.
