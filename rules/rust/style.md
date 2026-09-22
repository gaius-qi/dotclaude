---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust style

Reference codebase: [dragonflyoss/client](https://github.com/dragonflyoss/client) (`dragonfly-client*/src`). Community guides where they don't contradict: [Rust Style Guide](https://doc.rust-lang.org/style-guide/), [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/). When they disagree, the client repo wins. This file is file shape, config, CLI, tracing, binaries and tooling. Names: `naming.md`. Comments: `comments.md`. Language constructs: `idioms.md`.

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
use tracing::{error, info, instrument};

use crate::storage_engine::{rocksdb::RocksdbStorageEngine, DatabaseObject};

/// The default timeout for downloading tasks.
pub const DEFAULT_DOWNLOAD_TASK_TIMEOUT: Duration = Duration::from_secs(24 * 60 * 60);
```

- Apache 2.0 block-comment header on every `.rs` file.
- Imports in rustfmt order: one alphabetical block mixing `std` and external crates, blank line, then `use crate::...`. Group per crate with braces.
- Constants are `pub const SCREAMING_CASE` at the top of the file; per-type constants are associated consts (`Task::NAMESPACE`).
- Blank line between struct fields and between documented enum variants.

## Config

```rust
/// The storage configuration for dfdaemon.
#[derive(Debug, Clone, Validate, Deserialize)]
#[serde(default, rename_all = "camelCase")]
pub struct Storage {
    /// The size of the write buffer.
    #[serde(default = "default_storage_write_buffer_size")]
    pub write_buffer_size: usize,
}

/// Returns the default storage write buffer size.
#[inline]
fn default_storage_write_buffer_size() -> usize {
    2 * 1024 * 1024
}
```

- One struct per YAML section in `dragonfly-client-config/src/<binary>.rs`, `#[derive(Debug, Clone, Validate, Deserialize)]` + `#[serde(default, rename_all = "camelCase")]`. Per-field defaults are `#[serde(default = "default_xxx")]` pointing at an `#[inline] fn default_xxx()` in the same file. Validation via `validator` attributes; downstream code trusts the validated `Arc<Config>`.
- Sizes are `bytesize::ByteSize`, durations `Duration` with `humantime-serde`.
- `dfdaemon.yaml` mirrors the struct: camelCase keys, one `# Comment.` per key matching the field `///`.

## CLI

- `#[derive(Debug, Parser)] struct Args` with `#[arg(short, long, default_value_os_t = ..., env = "DFDAEMON_XXX", help = "Specify ...")]`. Help text is imperative, starts with `Specify`, no trailing period. Commands use `about`/`long_about`. One binary, one `Args`.

## Tracing

- `use tracing::{debug, error, info, instrument, warn};`
- `#[instrument(skip_all)]` on every `pub async fn` that does I/O; `#[instrument(level = "debug", skip_all)]` on per-piece paths and constructors.
- Messages lowercase, positional `{}`: `error!("initialize fs operator failed: {}", err);`. Log once, where the error is handled.

## Binaries

- `#[tokio::main] async fn main() -> Result<(), anyhow::Error>`. Sequence: install crypto provider → `Args::parse()` → `Config::load(&args.config).await` → `Arc::new(config)` → `init_tracing` → build components → serve with shutdown.
- Startup failures print via `terminal::error(...)` / `terminal::warn(...)` and `std::process::exit(1)`.

## Tooling

- CI gates: `cargo fmt --all -- --check`, `cargo clippy --all --all-targets -- -D warnings`, `cargo check --all --all-targets`, `cargo llvm-cov --workspace`. No `clippy.toml`, no `[lints]`, no crate-level `#![deny]`.
- Toolchain pinned in `rust-toolchain.toml`, edition in `[workspace.package]`. Don't bump either in a feature PR.
- Dependency policy: `idioms.md` Dependencies, `performance.md` Technology selection.
