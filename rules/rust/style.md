---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust style

Reference codebase: [dragonflyoss/client](https://github.com/dragonflyoss/client) (`dragonfly-client*/src`). Community guides where it doesn't contradict: [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [Rust Design Patterns](https://rust-unofficial.github.io/patterns/). When they disagree, the client repo wins.

## File skeleton

```rust
/*
 *     Copyright 2025 The Dragonfly Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * ...
 */

use chrono::{NaiveDateTime, Utc};
use dashmap::DashMap;
use dragonfly_client_config::dfdaemon::Config;
use dragonfly_client_core::{Error, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Duration;
use tracing::{error, info, instrument};

use crate::storage_engine::{rocksdb::RocksdbStorageEngine, DatabaseObject};

/// The default timeout for downloading tasks. The started task that exceeds the
/// timeout will be garbage collected by disk usage.
pub const DEFAULT_DOWNLOAD_TASK_TIMEOUT: Duration = Duration::from_secs(24 * 60 * 60);
```

- Apache 2.0 block-comment header on every `.rs` file.
- Imports: rustfmt default order, one alphabetical block mixing `std` and external crates, then a blank line, then `use crate::...`. Group per crate with braces; `std::path::{Path, PathBuf}`.
- `///` doc comment on every struct, enum, variant, field, fn, const, trait and trait method. Full sentence with a period. Patterns: `/// The task id.`, `/// The metadata of the task.`, `/// Creates a new metadata instance.`, `/// Stat gets the metadata from the backend.`
- Blank line between struct fields. Blank line between enum variants when they carry docs.
- Step comments inside function bodies: `// Parse command line arguments.`, `// Load config.`

## Types

```rust
/// The metadata of the task.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Task {
    /// The task id.
    pub id: String,

    /// The length of the content.
    pub content_length: Option<u64>,
}

impl Task {
    /// NAMESPACE is the namespace of [Task] in the storage.
    pub const NAMESPACE: &'static str = "task";
}
```

- Data types derive `Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize` as applicable. Always `Debug`. Never hand-write what a derive gives you.
- Config types: `#[derive(Debug, Clone, Validate, Deserialize)]` + `#[serde(default, rename_all = "camelCase")]`. Per-field defaults are `#[serde(default = "default_xxx")]` pointing at a `#[inline] fn default_xxx() -> T` in the same file. Validation rules via `validator` attributes.
- CLI args: `#[derive(Debug, Parser)] struct Args` with `#[arg(short, long, default_value_os_t = ..., env = "DFDAEMON_XXX", help = "...")]`. One binary, one `Args`.
- Constants are `pub const SCREAMING_CASE` with a doc comment. Per-type constants are associated consts (`Task::NAMESPACE`).
- Wrapper collections use `DashMap` for concurrent maps, `Arc<T>` for shared services, `tokio::sync::mpsc` for channels, `tokio::sync::RwLock` only when a `DashMap` or atomic won't do.
- Platform-specific code splits by file: `content_linux.rs`, `content_macos.rs` behind `#[cfg(target_os = "...")]`.

## Traits and constructors

```rust
/// The interface of the backend.
#[async_trait]
pub trait Backend {
    /// Returns the scheme of the backend.
    fn scheme(&self) -> String;

    /// Stat gets the metadata from the backend.
    async fn stat(&self, request: StatRequest) -> Result<StatResponse>;
}

impl Metadata<RocksdbStorageEngine> {
    /// Creates a new metadata instance.
    #[instrument(level = "debug", skip_all)]
    pub fn new(config: Arc<Config>, dir: &Path, log_dir: &PathBuf) -> Result<Self> { ... }
}
```

- Async traits use `#[async_trait]`. Each method takes one `XxxRequest` struct and returns `Result<XxxResponse>`. Factories are `XxxFactory` with `#[derive(Default)]`.
- Constructors are `pub fn new(config: Arc<Config>, ...)`. `Arc<Config>` is the first parameter of every service constructor. Fallible constructors return `Result<Self>`.
- Borrow in parameters (`&Path`, `&str`, `&[u8]`), return owned. No `.clone()` to satisfy the borrow checker without a comment saying why.
- `unsafe` only in `dragonfly-client-util` low-level modules (`fs/fd.rs`), each block with `// SAFETY:`.

## Tracing

- `use tracing::{debug, error, info, instrument, warn};`
- `#[instrument(skip_all)]` on every `pub async fn` that does I/O. `#[instrument(level = "debug", skip_all)]` on hot paths and constructors.
- Messages lowercase, positional `{}` not inline captures: `error!("initialize fs operator failed: {}", err);`, `info!("download task {} finished", task_id);`.
- Log at the boundary where you decide, once. Don't log and then let a caller log the same error.

## Binaries

- `#[tokio::main] async fn main() -> Result<(), anyhow::Error>`. Sequence: install crypto provider → `Args::parse()` → `Config::load(&args.config).await` → `Arc::new(config)` → `init_tracing` → build components → serve with shutdown.
- Startup failures print via `terminal::error(...)` / `terminal::warn(...)` and `std::process::exit(1)`. `unwrap()`/`expect()` are acceptable in `main.rs` wiring and nowhere in library code.

## Tooling

- `cargo fmt --all -- --check` and `cargo clippy --all --all-targets -- -D warnings` must pass. Toolchain pinned in `rust-toolchain.toml`; edition from `[workspace.package]`. Don't bump either.
- Existing workspace deps first: `tokio`, `hyper`/`hyper-util`/`hyper-rustls`, `tonic`, `reqwest`, `serde`/`serde_yaml`, `clap`, `tracing`, `thiserror`/`anyhow`, `validator`, `dashmap`, `bytesize`, `humantime-serde`, `opendal`, `rocksdb`, `tempfile`. Check `[workspace.dependencies]` before adding anything.
- Config YAML (`dfdaemon.yaml`) is camelCase via `rename_all`, one `# Comment.` per key, matching the struct field docs.
