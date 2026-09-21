# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Reference Before Coding

**BEFORE WRITING ANY CODE, FIND HOW HIGH-QUALITY RELATED GITHUB PROJECTS DO IT. THIS IS MANDATORY. NO EXCEPTIONS.**

This applies to every artifact: code, design, unit tests, YAML, config, CI, Dockerfile, Makefile, docs.

- **Find references first.** Identify one to three well-maintained, widely used GitHub projects in the same domain and read how they solve the same problem. Name them and cite the pattern you are following.
- **Reuse, don't reinvent.** If the stdlib or a mature library already does it, use it. Never write your own func for something a high-quality library provides.
- **Before defining a new func or type:** grep the codebase for an existing one. If none exists, decide which package or module it belongs in by where its siblings live, and say why. No duplicate helpers.
- **Two style sources, in order:** this project's own existing code first, then the reference projects. Same naming, same file layout, same test shape, same YAML and config conventions. New code must look like the original author wrote it.
- If community practice conflicts with the project's style, **the project wins**. Mention the discrepancy, don't silently "fix" it.
- **Language rules live in `~/.claude/rules/<language>/`** (`golang/`, `rust/`: style, naming, layout, errors, testing). They auto-load when a matching file is read. When creating a new file or starting work in a language before any of its files are in context, read that directory first.

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

**These guidelines are working if:** every non-trivial change names the reference projects it followed, fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
