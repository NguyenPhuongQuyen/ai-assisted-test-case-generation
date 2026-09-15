#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "========================================"
echo " Test Case Generator - Install"
echo "========================================"

# ------------------------------------------------------------
# Find system Python
# ------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  BASE_PYTHON=(python3)
elif command -v python >/dev/null 2>&1; then
  BASE_PYTHON=(python)
elif command -v py >/dev/null 2>&1; then
  BASE_PYTHON=(py -3)
else
  echo "[ERROR] Python 3.11+ chua duoc cai hoac khong co trong PATH."
  exit 1
fi

echo "[1/5] Local environment files"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[OK] Tao .env tu .env.example"
else
  echo "[OK] .env da ton tai"
fi

if [ ! -f src/frontend/.env.local ]; then
  cp src/frontend/.env.example src/frontend/.env.local
  echo "[OK] Tao src/frontend/.env.local"
else
  echo "[OK] src/frontend/.env.local da ton tai"
fi

echo
echo "[2/5] Python virtual environment"

if [ ! -d .venv ]; then
  "${BASE_PYTHON[@]}" -m venv .venv
  echo "[OK] Tao .venv"
else
  echo "[OK] .venv da ton tai"
fi

echo
echo "[3/5] Backend dependencies"

./scripts/python.sh -m pip install --upgrade pip
./scripts/python.sh -m pip install -r src/backend/requirements.txt

echo "[OK] Backend dependencies"

echo
echo "[4/5] Frontend dependencies"

cd src/frontend

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

cd "$ROOT"

echo "[OK] Frontend dependencies"

echo
echo "[5/5] Install completed"

echo
echo "========================================"
echo " INSTALL HOAN TAT"
echo "========================================"
echo "Kiem tra DATABASE_URL trong .env neu PostgreSQL local"
echo "khong dung thong tin mac dinh."
echo
echo "Tiep theo chay:"
echo "  ./scripts/init-demo.sh"
