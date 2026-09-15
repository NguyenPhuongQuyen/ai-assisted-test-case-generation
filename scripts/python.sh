#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT/.venv/bin/python" ]; then
  exec "$ROOT/.venv/bin/python" "$@"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  exec "$ROOT/.venv/Scripts/python.exe" "$@"
else
  echo "[ERROR] Khong tim thay Python trong .venv." >&2
  echo "Hay chay ./scripts/install.sh truoc." >&2
  exit 1
fi
