#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/deploy_opencode_server.py" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/deploy_opencode_server.py" "$@"
fi

echo "Python 3 was not found. Install Python 3, then retry." >&2
exit 1
