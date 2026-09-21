# dotclaude

My [Claude Code](https://code.claude.com) configuration: global `CLAUDE.md`, per-language rules, and skills.
Mirrors the `~/.claude/` layout so it can be symlinked in place.

## Install

Symlink (applies `CLAUDE.md`, rules and skills):

```sh
git clone git@github.com:gaius-qi/dotclaude.git ~/work/github.com/gaius-qi/dotclaude
~/work/github.com/gaius-qi/dotclaude/install.sh
```

Or as a plugin (skills only, namespaced `/dotclaude:<skill>`; `CLAUDE.md` and `rules/` are not applied this way):

```sh
/plugin marketplace add gaius-qi/dotclaude
/plugin install dotclaude@dotclaude
```

Rules are extracted from the Dragonfly codebases I maintain, [dragonflyoss/dragonfly](https://github.com/dragonflyoss/dragonfly) (Go) and [dragonflyoss/client](https://github.com/dragonflyoss/client) (Rust), and cross-checked against [Uber Go Style](https://github.com/uber-go/guide), [Google Go Style](https://google.github.io/styleguide/go/), [go.dev module layout](https://go.dev/doc/modules/layout), [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [Rust Design Patterns](https://rust-unofficial.github.io/patterns/) and the [Cargo Book](https://doc.rust-lang.org/cargo/guide/project-layout.html). Where they disagree, the Dragonfly code wins. Each file links its sources.

## Adding a language

```sh
mkdir rules/python
$EDITOR rules/python/style.md   # frontmatter `paths: ["**/*.py"]`, then the rules
```

Every `.md` under `rules/` is discovered recursively and loaded as instructions, so keep prose (like this README) out of it.

## Adding a skill

```sh
mkdir skills/my-skill
$EDITOR skills/my-skill/SKILL.md   # frontmatter: name (lowercase-hyphen), description (what + when)
./install.sh
```

References: [Agent Skills spec](https://agentskills.io/specification) ·
[`.claude` directory docs](https://code.claude.com/docs/en/claude-directory) ·
[Rules docs](https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/) ·
[Plugins reference](https://code.claude.com/docs/en/plugins-reference)
