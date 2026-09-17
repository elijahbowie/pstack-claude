#!/usr/bin/env bash
# Vendor pstack into a repo's .claude/ directory as standalone skills and agents.
#
# Why: cloud sessions have no /plugin command, and installing a third-party
# plugin inside a session trips the permission classifier (correctly). Standalone
# .claude/ config needs no marketplace, no install, and no permission grant. It
# arrives with the repo itself.
#
# Usage: tools/vendor-into-repo.sh /path/to/target/repo
set -euo pipefail

TARGET="${1:?usage: vendor-into-repo.sh /path/to/target/repo}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/plugins/pstack"

[ -d "$TARGET" ] || { echo "error: target not found: $TARGET" >&2; exit 1; }
[ -d "$SRC/skills" ] || { echo "error: source skills missing: $SRC/skills" >&2; exit 1; }

mkdir -p "$TARGET/.claude/skills" "$TARGET/.claude/agents"

# Copy skills and agents. rsync --delete only inside the paths we own, so any
# skills or agents the repo already had are left alone.
for d in "$SRC"/skills/*/; do
  name="$(basename "$d")"
  rm -rf "$TARGET/.claude/skills/$name"
  cp -R "$d" "$TARGET/.claude/skills/$name"
done
for f in "$SRC"/agents/*.md; do
  cp "$f" "$TARGET/.claude/agents/$(basename "$f")"
done

cp "$SRC/../../PORTING.md" "$TARGET/.claude/skills/PSTACK-PORTING.md" 2>/dev/null || true

s=$(find "$TARGET/.claude/skills" -name SKILL.md | wc -l | tr -d ' ')
a=$(find "$TARGET/.claude/agents" -name '*.md' | wc -l | tr -d ' ')
echo "vendored into $TARGET/.claude"
echo "  skills: $s"
echo "  agents: $a"
echo
echo "Commit and push, then in the cloud session run: git pull"
