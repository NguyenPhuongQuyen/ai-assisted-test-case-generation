#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "========================================"
echo " Test Case Generator - Install"
echo "========================================"
echo

# ------------------------------------------------------------
# Validate system Python
# ------------------------------------------------------------
python_works() {
  "$@" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

if command -v python3 >/dev/null 2>&1 && python_works python3; then
  BASE_PYTHON=(python3)
elif command -v python >/dev/null 2>&1 && python_works python; then
  BASE_PYTHON=(python)
elif command -v py >/dev/null 2>&1 && python_works py -3; then
  BASE_PYTHON=(py -3)
else
  echo "[ERROR] Khong tim thay Python 3.11+ chay duoc."
  echo "Hay cai Python 3.11+ va dam bao python hoac py co trong PATH."
  exit 1
fi

echo "[OK] System Python: $("${BASE_PYTHON[@]}" --version 2>&1)"

# ------------------------------------------------------------
# Validate Node.js and npm
# ------------------------------------------------------------
if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] Khong tim thay Node.js trong PATH."
  echo "Hay cai Node.js 20.9+."
  exit 1
fi

if ! node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit(major > 20 || (major === 20 && minor >= 9) ? 0 : 1)' >/dev/null 2>&1; then
  echo "[ERROR] Node.js phai la version 20.9 tro len."
  echo "[INFO] Version hien tai: $(node --version)"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] Khong tim thay npm trong PATH."
  exit 1
fi

echo "[OK] Node.js: $(node --version)"
echo "[OK] npm: $(npm --version)"
echo

# ------------------------------------------------------------
# 1. Local environment files
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 2. Python virtual environment
# ------------------------------------------------------------
echo "[2/5] Python virtual environment"

if [ ! -d .venv ]; then
  "${BASE_PYTHON[@]}" -m venv .venv
  echo "[OK] Tao .venv"
else
  echo "[OK] .venv da ton tai"
fi

echo

# ------------------------------------------------------------
# 3. Backend dependencies
# ------------------------------------------------------------
echo "[3/5] Backend dependencies"

./scripts/python.sh -m pip install --upgrade pip
./scripts/python.sh -m pip install -r src/backend/requirements.txt

echo "[OK] Backend dependencies"
echo

# ------------------------------------------------------------
# 4. Frontend dependencies
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 5. Done
# ------------------------------------------------------------
echo "[5/5] Install completed"
echo

echo "========================================"
echo " INSTALL HOAN TAT"
echo "========================================"
echo
echo "Kiem tra DATABASE_URL trong .env neu PostgreSQL local"
echo "khong dung thong tin mac dinh."
echo
echo "Tiep theo chay:"
echo "  ./scripts/init-demo.sh"