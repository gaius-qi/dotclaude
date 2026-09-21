---
paths:
  - "**/*.rs"
---

# Rust testing

Reference shape from [dragonflyoss/client](https://github.com/dragonflyoss/client) (`dragonfly-client-util/src/digest/mod.rs`, `dragonfly-client-storage/src/content.rs`).

```rust
#[cfg(test)]
mod tests {
    #![allow(clippy::type_complexity)]

    use super::*;
    use tempfile::tempdir;

    #[test]
    fn is_blob_url_matches_oci_blob_urls() {
        let test_cases = vec![
            ("http://registry.example.com/v2/library/ubuntu/blobs/sha256:b2c3...", true),
            ("http://registry.example.com/v2/library/ubuntu/manifests/sha256:b2c3...", false),
            ("https://example.com/file.txt", false),
        ];

        for (url, expected) in test_cases {
            assert_eq!(is_blob_url(url), expected);
        }
    }

    #[test]
    fn extract_from_blob_url_parses_oci_blob_digests() {
        let test_cases: Vec<(&str, fn(Option<Digest>))> = vec![
            ("https://.../blobs/sha256:b2c3...", |digest| {
                let digest = digest.unwrap();
                assert_eq!(digest.algorithm(), Algorithm::Sha256);
            }),
            ("https://example.com/file.txt", |digest| assert!(digest.is_none())),
        ];

        for (url, assert_fn) in test_cases {
            assert_fn(extract_from_blob_url(url));
        }
    }

    #[tokio::test]
    async fn calculate_piece_range_clips_to_the_request_range() {
        let dir = tempdir().unwrap();
        let content = Content::new(Arc::new(Config::default()), dir.path(), dir.path()).await.unwrap();
        ...
    }
}
```

- Tests live at the bottom of the file they test, in `#[cfg(test)] mod tests { use super::*; ... }`. No `tests/` directory.
- `#[test]` for sync, `#[tokio::test]` for async. Names are behaviour sentences in `snake_case` with no `test_` prefix: `recv_returns_after_trigger`, `add_overwrites_the_oldest_sample_when_the_ring_is_full`.
- Table-driven: `let test_cases = vec![(input, expected), ...]; for (a, b) in test_cases { assert_eq!(f(a), b); }`. When assertions differ per case, the tuple carries a closure: `Vec<(&str, fn(Option<Digest>))>`, and the loop calls it.
- Assertions: `assert_eq!`, `assert!`, `assert!(matches!(err, Error::TaskNotFound(_)))`. Add a message only when the comparison isn't self-evident.
- Filesystem tests use `tempfile::tempdir()` and pass `dir.path()`. Never write into the repo tree.
- `unwrap()` is fine in tests. Suppress noisy lints at module scope only: `#![allow(clippy::type_complexity)]`.
- Build test subjects with `Arc::new(Config::default())` and the real constructor. Mock remote services with in-process servers or trait objects already in the crate; don't add a mocking framework.
- Run the narrow target first: `cargo test -p dragonfly-client-util is_blob_url`. Finish with `cargo test --all` and `cargo clippy --all --all-targets -- -D warnings`.
- Public API also gets doc examples that compile under `cargo test --doc`; examples use `?`, never `unwrap()`.
