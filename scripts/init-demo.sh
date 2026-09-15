#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

[ -f .env ] || {
  echo "[ERROR] Thieu .env. Hay chay ./scripts/install.sh truoc."
  exit 1
}

echo "========================================"
echo " Test Case Generator - Initialize"
echo "========================================"

echo
echo "[1/2] Database migration"

./scripts/python.sh \
  -m alembic \
  -c src/backend/alembic.ini \
  upgrade head

echo "[OK] Migration"

echo
echo "[2/2] Demo seed"

PYTHONPATH=src/backend \
  ./scripts/python.sh \
  src/backend/scripts/seed_demo.py

echo "[OK] Demo data"

echo
echo "========================================"
echo " DATABASE SAN SANG"
echo "========================================"
echo "Tiep theo chay:"
echo "  ./scripts/dev-up.sh"
