---
paths:
  - "**/*.rs"
---

# Rust comments

Reference codebase: [dragonflyoss/client](https://github.com/dragonflyoss/client). Language guides where they don't contradict: [Rust Style Guide: Comments](https://doc.rust-lang.org/style-guide/#comments), [rustdoc: How to write documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html), [Rust API Guidelines: Documentation](https://rust-lang.github.io/api-guidelines/documentation.html). When they disagree, the client repo wins. Test code carries no comments: `testing.md`.

```rust
/// The metadata of the task.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Task {
    /// The task id.
    pub id: String,

    /// The length of the content.
    pub content_length: Option<u64>,
}

/// Implements the task metadata.
impl Task {
    /// The namespace of [Task] objects.
    pub const NAMESPACE: &'static str = "task";

    /// Returns whether the task is uploading.
    pub fn is_uploading(&self) -> bool {
        self.uploading_count > 0
    }
}

pub async fn run(config: Arc<Config>) -> Result<()> {
    // Initialize upload rate limiter.
    let upload_rate_limiter = Arc::new(RateLimiter::new(config.upload.rate_limit));

    // SAFETY: the pool invariant guarantees the full capacity is initialized.
    unsafe { buffer.set_len(len) };
    ...
}
```

## Doc comments

- `///` on every item: struct, enum, variant, field, fn, const, static, trait, trait method, type alias, and the `impl` block itself. Private production items too. Only test code is exempt.
- Third person, sentence case, trailing period. Nouns for data (`/// The task id.`), verbs for behaviour (`/// Returns whether the task is uploading.`, `/// Creates a new metadata instance.`), `/// Implements ...` for impl blocks.
- Never start with the item's own name; `/// Stat gets the metadata from the backend.` is a Go-style leftover. Don't copy it, don't churn it.
- First line is the one-sentence summary rustdoc lists. Detail after a blank `///`.
- Doc comment above attributes, always.
- `#[serde(default = "default_xxx")]` targets are documented `/// Returns the default xxx.`
- Sections: none by default. `# Arguments`/`# Returns` stay confined to `dragonfly-client-util` low-level code. Add `# Safety` on every `pub unsafe fn`, `# Panics` when a `pub fn` can panic, `# Errors` when the conditions aren't obvious from the `Error` variants.
- Fenced code is ```` ```text ```` for layouts and ```` ```ignore ```` for sketches that can't compile. An untagged or `rust` block is a doctest and must pass `cargo test --doc`. Space after the sigil: `/// ```text`.
- Name other items with intra-doc links, `[Task]`; code words in backticks. Bare URLs inline, introduced by `refer to`, ending with a period.
- `//!` module docs only for backends in `dragonfly-client-backend/src/*.rs`: one summary line, then `//! # URL Format` style sections. Never in `lib.rs`, `mod.rs`, `main.rs`.
- clap fields use `#[arg(help = "...")]`, never `///`, which clap would turn into help text.

## Body comments

- One step comment per logical block: imperative, sentence case, trailing period, blank line before it. `// Initialize task manager.`, `// Collect the pieces that are already finished.`
- No trailing same-line comments; the comment goes on its own line above.
- `// SAFETY: <why the invariant holds>.` directly above every `unsafe` block and above every `unsafe impl Send/Sync`. Most existing blocks lack one; add it when you touch the block.
- `#[allow(...)]` is bare, no justification line. Don't add one to silence a lint you can fix.
- Only `TODO`, with a handle: `// TODO(gaius): Use trust_anchor to skip the verify of hostname.` No `FIXME`, `NOTE`, `XXX`, `HACK`.
- `/* */` only for the license header. No commented-out code.
- `Cargo.toml` carries no comments except a `# TODO(handle): ...` above a pinned dependency linking the upstream issue.
- Nothing enforces docs (no `#![warn(missing_docs)]`); review is the gate.
