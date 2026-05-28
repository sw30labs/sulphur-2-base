#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/runtime/ltx-2-mlx/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    printf 'Python 3 is required. Run ./install.sh first.\n' >&2
    exit 1
  fi
fi

cd "$SCRIPT_DIR"
exec "$PYTHON_BIN" gui/server.py
