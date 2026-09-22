# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Reference Before Anything

**This rule outranks every other rule here and in any project instruction. Before writing code, a design, a plan or a proposal, find how the top GitHub projects in that domain do it. No exceptions.**

It covers every artifact: code, tests, benchmarks, design docs, architecture and tradeoff proposals, YAML, config, CI, Dockerfile, Makefile, docs. A design that cites no reference project is not finished.

- **Where to look, in order.** Rust: [rust-lang](https://github.com/rust-lang) (`rust`, `cargo`, `clippy`, Style Guide, API Guidelines, rustdoc book), then [tokio-rs](https://github.com/tokio-rs). Go: [golang](https://github.com/golang) (`go`, `tools`, go.dev docs), then [uber-go/guide](https://github.com/uber-go/guide) and Google Go Style. Engineering practice in any language: [torvalds/linux](https://github.com/torvalds/linux), [kubernetes](https://github.com/kubernetes), [containerd](https://github.com/containerd), [cloudflare](https://github.com/cloudflare). Then the top one to three projects in the specific problem domain, and published guides (Effective Go, Effective Rust, go-perfbook, the Rust Performance Book).
- **At least two projects, preferably three.** Where they agree, that is the pattern. Where they disagree, name the disagreement and choose with a reason.
- **Name them.** Every non-trivial change and every design says which projects were read and which pattern is followed, with a link or path.
- **Reuse before writing.** Stdlib, then a dependency already in the project, then a mature library, then new code. Before adding a func or type, grep for an existing one; place a new one where its siblings live and say why.
- **Style precedence.** This project's existing code, then the language home org, then the engineering reference projects. New code must look like the original author wrote it. When community practice conflicts with the project, the project wins; mention the discrepancy, don't silently fix it.
- **Language rules** live in `~/.claude/rules/<language>/` (`golang/`, `rust/`: layout, naming, style, comments, errors, idioms, testing, performance). They auto-load when a matching file is read; before creating a file in a language with none in context, read that directory. Each rule file names its references; cite them when you apply it.

## 2. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 3. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 4. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 5. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** every non-trivial change and every design names the reference projects it followed, fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
