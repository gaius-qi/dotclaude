---
paths:
  - "**/*.rs"
---

# Rust testing

Reference shape from [dragonflyoss/client](https://github.com/dragonflyoss/client) (`dragonfly-client-util/src/digest/mod.rs`, `dragonfly-client-storage/src/content.rs`). Names: `naming.md`. Benchmarks: `performance.md`.

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

- Tests live at the bottom of the file they test, in `#[cfg(test)] mod tests { use super::*; ... }`. No `tests/` directory; end-to-end lives in the Go repo's `test/e2e`.
- No comments in test code. The client's 422 tests contain zero `//` and `///` lines: none on a `#[test]` fn, above `test_cases`, inside a body, or on test-local consts and helpers. The fn name is the sentence; a case that needs a comment needs a better tuple or its own test. The only exception is `#![allow(clippy::type_complexity)]` at module top.
- `#[test]` for sync, `#[tokio::test]` for async.
- Table-driven: `let test_cases = vec![(input, expected), ...]; for (a, b) in test_cases { assert_eq!(f(a), b); }`. When assertions differ per case, the tuple carries a closure (`Vec<(&str, fn(Option<Digest>))>`) and the loop calls it.
- Assertions: `assert_eq!`, `assert!`, `assert!(matches!(err, Error::TaskNotFound(_)))`. A message only when the comparison isn't self-evident.
- Filesystem tests use `tempfile::tempdir()` and pass `dir.path()`. Never write into the repo tree.
- `unwrap()` is fine in tests. Build subjects with `Arc::new(Config::default())` and the real constructor. Mock remote services with `mocktail` or trait objects already in the crate; don't add a mocking framework.
- Run the narrow target first: `cargo test -p dragonfly-client-util is_blob_url`. Finish with `cargo test --all` and `cargo clippy --all --all-targets -- -D warnings`.
- Doc examples on public API compile under `cargo test --doc` and use `?`, never `unwrap()`.
