---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust project layout

Reference: [dragonflyoss/client](https://github.com/dragonflyoss/client) workspace, following the [Cargo Book package layout](https://doc.rust-lang.org/cargo/guide/project-layout.html) and "prefer small crates" from [Rust Design Patterns](https://rust-unofficial.github.io/patterns/patterns/structural/small-crates.html).

```
client/
├── Cargo.toml                    # [workspace] members, [workspace.package], [workspace.dependencies]
├── Cargo.lock                    # committed
├── rust-toolchain.toml           # pinned toolchain
├── dragonfly-client/             # binaries and daemon logic
│   └── src/
│       ├── lib.rs                # pub mod announcer; pub mod grpc; ... nothing else
│       ├── bin/dfdaemon/main.rs  # one dir per binary, main.rs only
│       ├── bin/dfget/main.rs
│       ├── announcer/mod.rs      # one directory per module, mod.rs is the root
│       ├── grpc/mod.rs           # grpc/{scheduler.rs, manager.rs, dfdaemon_download.rs, health.rs, interceptor.rs}
│       ├── resource/mod.rs       # resource/{task.rs, persistent_task.rs, piece.rs, ...}
│       └── proxy/, gc/, dynconfig/, health/, metrics/, stats/, tracing.rs
├── dragonfly-client-core/        # Error enum + Result alias. Nothing else, so every crate can depend on it.
│   └── src/{lib.rs, result.rs, error/{mod.rs, errors.rs, message.rs}}
├── dragonfly-client-config/      # one file per binary: dfdaemon.rs, dfget.rs, dfcache.rs, dfstore.rs, dfinit.rs, dfctl.rs
├── dragonfly-client-storage/     # metadata.rs, content.rs, content_linux.rs, content_macos.rs, storage_engine/, cache/, server/, client/
├── dragonfly-client-backend/     # one file per protocol: http.rs, oci.rs, object_storage.rs, hdfs.rs, hugging_face.rs; examples/plugin/
├── dragonfly-client-util/        # digest/, fs/, http/, net/, id_generator/, hashring/, cgroups/, container/, pool/, tls/
├── dragonfly-client-metric/
├── dragonfly-client-init/        # container_runtime/{containerd.rs, crio.rs, docker.rs, podman.rs}
├── ci/                           # Dockerfile, Dockerfile.debug, dfdaemon.service
├── scripts/, docs/, certs/
└── .github/workflows/            # cargo fmt --check, cargo clippy -D warnings, cargo test
```

- **Decide placement by asking:** does it need `Error`/`Result` only → `core`. Is it a pure helper with no daemon state → `util/<topic>/mod.rs`. Is it config for a binary → `config/<binary>.rs`. Does it talk to a remote → `backend/<protocol>.rs` or `client/src/grpc/<service>.rs`. Otherwise it belongs to the daemon in `dragonfly-client/src/<module>/`.
- Modules are directories with `mod.rs` (`storage_engine/mod.rs`, `storage_engine/rocksdb.rs`). This codebase does not use the `foo.rs` + `foo/` style. Don't introduce it.
- `lib.rs` is a list of `pub mod` lines plus at most a few `pub use`/`pub type` re-exports (`pub type Error = error::DFError;`). No logic in `lib.rs`.
- Every member `Cargo.toml` inherits `version`, `edition`, `license`, `repository` etc. from `[workspace.package]` and takes dependencies from `[workspace.dependencies]` with `{ workspace = true }`. Add a dependency to the workspace table once; pin exact versions for `dragonfly-api` and sibling crates.
- Sibling crates depend by path and version: `dragonfly-client-core = { path = "dragonfly-client-core", version = "1.5.6" }` in the workspace table.
- Unit tests live in each file's `#[cfg(test)] mod tests`. There is no `tests/` directory; end-to-end lives in the Go repo's `test/e2e`.
- Binary-specific config paths and defaults live in the config crate, not in `main.rs`. `main.rs` reads `Args`, loads `Config`, wires, runs.
- Platform variants: separate files (`content_linux.rs`, `content_macos.rs`) selected by `#[cfg(target_os)]` in `mod.rs`, not `cfg` blocks scattered inside functions.
- Plugin examples ship under the crate they extend: `dragonfly-client-backend/examples/plugin/` is a workspace member.
