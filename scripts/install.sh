#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-$HOME/.codex/skills}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$DEST"
for skill in "$ROOT"/.codex/skills/*; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"
  target="$DEST/$name"
  if [ -e "$target" ]; then
    backup="$target.backup-$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    echo "Backed up $target -> $backup"
  fi
  cp -R "$skill" "$target"
  echo "Installed $name -> $target"
done
