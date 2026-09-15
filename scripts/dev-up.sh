#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/.dev/logs"
PID_DIR="$ROOT/.dev/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

fail() {
  echo "[ERROR] $1"
  exit 1
}

# =========================
# Python virtual environment
# =========================
if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
else
  fail "Không tìm thấy .venv. Hãy chạy bước cài dependencies trong README."
fi

[ -f "$ROOT/.env" ] || \
  fail "Thiếu .env. Hãy chạy: cp .env.example .env"

[ -d "$ROOT/src/frontend/node_modules" ] || \
  fail "Thiếu frontend dependencies. Hãy chạy bước cài dependencies trong README."

# =========================
# Helpers
# =========================
port_open() {
  local port="$1"

  "$PYTHON" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])

try:
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        sys.exit(0)
except OSError:
    sys.exit(1)
PY
}

wait_port() {
  local port="$1"

  for _ in {1..30}; do
    if port_open "$port"; then
      return 0
    fi
    sleep 1
  done

  return 1
}

wait_url() {
  local url="$1"

  for _ in {1..30}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  return 1
}

# =========================
# PostgreSQL auto start
# =========================
start_postgresql() {
  echo "[INFO] PostgreSQL chưa chạy. Đang thử khởi động..."

  # Windows
  if command -v powershell.exe >/dev/null 2>&1; then
    local service_name

    service_name="$(
      powershell.exe -NoProfile -Command \
        "\$s = Get-Service | Where-Object {
          \$_.Name -like 'postgresql*' -or
          \$_.DisplayName -like 'PostgreSQL*'
        } | Select-Object -First 1;
        if (\$s) { \$s.Name }" 2>/dev/null |
      tr -d '\r'
    )"

    if [ -n "$service_name" ]; then
      powershell.exe -NoProfile -Command \
        "Start-Service -Name '$service_name' -ErrorAction Stop" \
        >/dev/null 2>&1 || true
    fi
  fi

  # Linux
  if ! port_open 5432 && command -v systemctl >/dev/null 2>&1; then
    systemctl start postgresql >/dev/null 2>&1 || \
      sudo systemctl start postgresql >/dev/null 2>&1 || true
  fi

  # macOS / Homebrew
  if ! port_open 5432 && command -v brew >/dev/null 2>&1; then
    brew services start postgresql >/dev/null 2>&1 || \
    brew services start postgresql@17 >/dev/null 2>&1 || \
    brew services start postgresql@16 >/dev/null 2>&1 || true
  fi

  wait_port 5432 || \
    fail "Không thể khởi động PostgreSQL tại localhost:5432. Hãy kiểm tra PostgreSQL đã được cài/đăng ký service."
}

# =========================
# RabbitMQ auto start
# =========================
start_rabbitmq() {
  echo "[INFO] RabbitMQ chưa chạy. Đang thử khởi động..."

  # Windows service
  if command -v powershell.exe >/dev/null 2>&1; then
    local service_name

    service_name="$(
      powershell.exe -NoProfile -Command \
        "\$s = Get-Service | Where-Object {
          \$_.Name -like 'RabbitMQ*' -or
          \$_.DisplayName -like 'RabbitMQ*'
        } | Select-Object -First 1;
        if (\$s) { \$s.Name }" 2>/dev/null |
      tr -d '\r'
    )"

    if [ -n "$service_name" ]; then
      powershell.exe -NoProfile -Command \
        "Start-Service -Name '$service_name' -ErrorAction Stop" \
        >/dev/null 2>&1 || true
    fi
  fi

  # Command available in PATH
  if ! port_open 5672; then
    if command -v rabbitmq-server >/dev/null 2>&1; then
      rabbitmq-server -detached >/dev/null 2>&1 || true
    elif command -v rabbitmq-server.bat >/dev/null 2>&1; then
      rabbitmq-server.bat -detached >/dev/null 2>&1 || true
    fi
  fi

  # Linux service
  if ! port_open 5672 && command -v systemctl >/dev/null 2>&1; then
    systemctl start rabbitmq-server >/dev/null 2>&1 || \
      sudo systemctl start rabbitmq-server >/dev/null 2>&1 || true
  fi

  # macOS / Homebrew
  if ! port_open 5672 && command -v brew >/dev/null 2>&1; then
    brew services start rabbitmq >/dev/null 2>&1 || true
  fi

  wait_port 5672 || \
    fail "Không thể khởi động RabbitMQ tại localhost:5672. Hãy kiểm tra RabbitMQ đã được cài/đăng ký service hoặc có trong PATH."
}

# =========================
# Start
# =========================
echo "========================================"
echo " Test Case Generator - Development"
echo "========================================"

echo
echo "[1/5] PostgreSQL"

if port_open 5432; then
  echo "[OK] PostgreSQL đã chạy"
else
  start_postgresql
  echo "[OK] PostgreSQL"
fi

echo
echo "[2/5] RabbitMQ"

if port_open 5672; then
  echo "[OK] RabbitMQ đã chạy"
else
  start_rabbitmq
  echo "[OK] RabbitMQ"
fi

echo
echo "[3/5] FastAPI backend"

if port_open 8001; then
  wait_url http://127.0.0.1:8001/health || \
    fail "Backend đang chạy nhưng health check không đạt. Hãy kiểm tra PostgreSQL/RabbitMQ."

  echo "[OK] Backend đã chạy"
else
  PYTHONPATH=src/backend \
    "$PYTHON" -m uvicorn app.main:app \
    --app-dir src/backend \
    --host 127.0.0.1 \
    --port 8001 \
    >"$LOG_DIR/backend.log" 2>&1 &

  echo $! >"$PID_DIR/backend.pid"

  wait_url http://127.0.0.1:8001/health || \
    fail "Backend không khởi động được hoặc dependency chưa healthy. Xem .dev/logs/backend.log"

  echo "[OK] Backend"
fi

echo
echo "[4/5] Celery"

if [ -f "$PID_DIR/celery.pid" ] &&
   kill -0 "$(cat "$PID_DIR/celery.pid")" 2>/dev/null; then
  echo "[OK] Celery đã chạy"
else
  PYTHONPATH=src/backend \
    "$PYTHON" -m celery \
    -A app.worker.celery_app \
    worker \
    --loglevel=INFO \
    --pool=solo \
    >"$LOG_DIR/celery.log" 2>&1 &

  echo $! >"$PID_DIR/celery.pid"

  sleep 3

  kill -0 "$(cat "$PID_DIR/celery.pid")" 2>/dev/null || \
    fail "Celery không khởi động được. Xem .dev/logs/celery.log"

  echo "[OK] Celery"
fi

echo
echo "[5/5] Next.js frontend"

if curl -fsS http://localhost:3000 >/dev/null 2>&1; then
  echo "[OK] Frontend đã chạy"
else
  (
    cd "$ROOT/src/frontend"
    exec npm run dev
  ) >"$LOG_DIR/frontend.log" 2>&1 &

  echo $! >"$PID_DIR/frontend.pid"

  wait_url http://localhost:3000 || \
    fail "Frontend không khởi động được. Xem .dev/logs/frontend.log"

  echo "[OK] Frontend"
fi

echo
echo "========================================"
echo " HỆ THỐNG ĐÃ SẴN SÀNG"
echo "========================================"
echo "Frontend : http://localhost:3000"
echo "Backend  : http://127.0.0.1:8001"
echo "Swagger  : http://127.0.0.1:8001/docs"
echo "Health   : http://127.0.0.1:8001/health"
