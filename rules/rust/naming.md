---
paths:
  - "**/*.rs"
  - "**/Cargo.toml"
---

# Rust naming

Reference: [dragonflyoss/client](https://github.com/dragonflyoss/client), then [Rust API Guidelines: Naming](https://rust-lang.github.io/api-guidelines/naming.html) (RFC 430).

| Item | Convention | Dragonfly examples |
|---|---|---|
| Crates | `dragonfly-client-<area>` | `dragonfly-client-core`, `dragonfly-client-storage`, `dragonfly-client-util` |
| Binaries | short `df` prefix | `dfdaemon`, `dfget`, `dfcache`, `dfstore`, `dfctl`, `dfinit` |
| Modules | `snake_case`, directory + `mod.rs` | `storage_engine/`, `container_runtime/`, `id_generator/`, `grpc/` |
| Types, traits, variants | `UpperCamelCase` | `Task`, `PersistentCacheTask`, `RocksdbStorageEngine`, `Backend`, `BackendFactory` |
| Acronyms in types | uppercase, matching the codebase | `DFError`, `TCPServer`, `QUICServer`, `IDGenerator`, `GC`, `InvalidURI` |
| Functions, methods, fields | `snake_case` | `content_length`, `piece_length`, `updated_at`, `is_blob_url` |
| Constants, statics | `SCREAMING_SNAKE_CASE` | `DEFAULT_DOWNLOAD_TASK_TIMEOUT`, `NAME`, `NAMESPACE` |
| Env vars | binary prefix | `DFDAEMON_CONFIG`, `DFDAEMON_LOG_LEVEL` |
| Type params, lifetimes | one letter | `T`, `'a` |

- Acronyms: RFC 430 says `Uuid`/`TcpServer`; this codebase uses `TCPServer`, `IDGenerator`, `DFError`. Match the surrounding code, never mix both forms in one crate.
- Request/response pairs: `StatRequest`/`StatResponse`, `GetRequest`/`GetResponse`, `PutRequest`/`PutResponse`.
- Servers and clients are named by protocol and role: `DfdaemonDownloadServer`, `DfdaemonUploadServer`, `SchedulerClient`, `ManagerClient`.
- Config: one struct per section named after the YAML key: `Host`, `Server`, `DownloadServer`, `Upload`, `Storage`, `Gc`, `Proxy`. Top-level is `Config`. Default helpers are `default_<binary>_<field>()` for paths and `default_<field>()` for values: `default_dfdaemon_config_path()`, `default_download_protocol()`.
- Errors: enum `DFError`, variants are the condition in `UpperCamelCase`: `TaskNotFound(String)`, `PieceNotFound(String)`, `InvalidURI(String)`, `DigestMismatch(String, String)`, `NoSpace(String)`, `SendTimeout`. External wrappers: `BackendError`, `ExternalError`, `ErrorType::ParseError`.
- Conversions follow `as_`/`to_`/`into_`. Getters have no `get_` prefix: `digest.algorithm()`, `digest.encoded()`, `task.is_finished()`. Predicates are `is_`/`has_`.
- Constructors: `new(config: Arc<Config>, ...)`, `with_capacity`, `from_str`. Async open-style constructors: `open(dir, log_dir, ...)`.
- Iterator types match their method (`Iter`, `IterMut`, `IntoIter`). Collections implement `iter()`, `len()`, `is_empty()`.
- Cargo features are additive nouns with no filler: `serde`, `std`. Never `use-xxx`, `with-xxx`, `no-xxx`.
- Tests: behaviour sentences in `snake_case`, no `test_` prefix: `is_blob_url_matches_oci_blob_urls`, `recv_returns_after_trigger`, `acquire_sheds_only_when_in_flight_exceeds_the_estimated_limit`.
- Variables: `config`, `args`, `err`, `task_id`, `piece_id`, `dir`, `log_dir`, `request`/`response`, `tx`/`rx` for channel halves.
