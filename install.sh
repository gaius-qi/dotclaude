#!/bin/sh
# Symlink CLAUDE.md, rules/ and skills/* into ~/.claude. Idempotent; backs up non-symlink targets.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
dst=${CLAUDE_CONFIG_DIR:-$HOME/.claude}

link() { # src dst
  if [ -e "$2" ] && [ ! -L "$2" ]; then mv "$2" "$2.bak" && echo "backed up $2 -> $2.bak"; fi
  ln -sfn "$1" "$2" && echo "$2 -> $1"
}

mkdir -p "$dst/skills"
link "$here/CLAUDE.md" "$dst/CLAUDE.md"
link "$here/rules" "$dst/rules"
for s in "$here"/skills/*/; do
  s=${s%/}; [ -d "$s" ] || continue
  link "$s" "$dst/skills/$(basename "$s")"
done
