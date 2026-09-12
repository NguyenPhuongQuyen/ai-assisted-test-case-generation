#!/usr/bin/env bash

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="$ROOT/.dev"
LOG_DIR="$RUNTIME_DIR/logs"
PID_DIR="$RUNTIME_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

fail() {
  echo "[ERROR] $1"
  exit 1
}

wait_for_url() {
  local name="$1"
  local url="$2"

  for _ in {1..20}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[OK] $name"
      return 0
    fi
    sleep 1
  done

  echo "[ERROR] $name không khởi động được."
  return 1
}

find_rabbitmq_sbin() {
  if [ -n "${RABBITMQ_SBIN:-}" ] &&
     [ -f "$RABBITMQ_SBIN/rabbitmq-server.bat" ]; then
    printf '%s\n' "$RABBITMQ_SBIN"
    return 0
  fi

  local found

  found="$(command -v rabbitmq-server.bat 2>/dev/null || true)"
  if [ -n "$found" ]; then
    dirname "$found"
    return 0
  fi

  for candidate in \
    /d/rabbitmq_server-*/sbin \
    "/c/Program Files/RabbitMQ Server"/rabbitmq_server-*/sbin
  do
    if [ -f "$candidate/rabbitmq-server.bat" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

echo "========================================"
echo " Test Case Generator - Development"
echo "========================================"

[ -f ".env" ] || fail "Thiếu file .env"
[ -x ".venv/Scripts/python.exe" ] || fail "Thiếu .venv. Hãy cài backend trước."
[ -d "src/frontend/node_modules" ] || fail "Thiếu frontend node_modules. Hãy chạy npm install trước."

echo
echo "[1/4] RabbitMQ"

RABBIT_SBIN="$(find_rabbitmq_sbin)" ||
  fail "Không tìm thấy RabbitMQ. Có thể đặt biến RABBITMQ_SBIN."

if "$RABBIT_SBIN/rabbitmq-diagnostics.bat" -q ping >/dev/null 2>&1; then
  echo "[OK] RabbitMQ đang chạy"
else
  echo "[INFO] Đang khởi động RabbitMQ..."
  "$RABBIT_SBIN/rabbitmq-server.bat" -detached

  rabbit_ok=0
  for _ in {1..20}; do
    if "$RABBIT_SBIN/rabbitmq-diagnostics.bat" -q ping >/dev/null 2>&1; then
      rabbit_ok=1
      break
    fi
    sleep 1
  done

  [ "$rabbit_ok" -eq 1 ] || fail "RabbitMQ không khởi động được"
  echo "[OK] RabbitMQ"
fi

echo
echo "[2/4] FastAPI backend"

if curl -fsS http://127.0.0.1:8001/health >/dev/null 2>&1; then
  echo "[OK] Backend đã chạy"
else
  PYTHONPATH=src/backend \
  ./.venv/Scripts/python.exe \
    -m uvicorn app.main:app \
    --app-dir src/backend \
    --host 127.0.0.1 \
    --port 8001 \
    > "$LOG_DIR/backend.log" 2>&1 &

  echo $! > "$PID_DIR/backend.pid"

  wait_for_url "Backend" "http://127.0.0.1:8001/health" ||
    fail "Xem log: .dev/logs/backend.log"
fi

echo
echo "[3/4] Celery worker"

CELERY_PID_FILE="$PID_DIR/celery.pid"

if [ -f "$CELERY_PID_FILE" ] &&
   kill -0 "$(cat "$CELERY_PID_FILE")" 2>/dev/null; then
  echo "[OK] Celery đã chạy"
else
  rm -f "$LOG_DIR/celery.log"

  PYTHONPATH=src/backend \
  ./.venv/Scripts/python.exe \
    -m celery \
    -A app.worker.celery_app \
    worker \
    --loglevel=INFO \
    --pool=solo \
    > "$LOG_DIR/celery.log" 2>&1 &

  echo $! > "$CELERY_PID_FILE"

  celery_ok=0
  for _ in {1..20}; do
    if grep -q " ready\." "$LOG_DIR/celery.log" 2>/dev/null; then
      celery_ok=1
      break
    fi

    if grep -qiE "traceback|cannot connect|critical" "$LOG_DIR/celery.log" 2>/dev/null; then
      break
    fi

    sleep 1
  done

  [ "$celery_ok" -eq 1 ] ||
    fail "Celery không khởi động được. Xem .dev/logs/celery.log"

  echo "[OK] Celery"
fi

echo
echo "[4/4] Next.js frontend"

if curl -fsS http://localhost:3000 >/dev/null 2>&1; then
  echo "[OK] Frontend đã chạy"
else
  (
    cd "$ROOT/src/frontend"
    npm run dev
  ) > "$LOG_DIR/frontend.log" 2>&1 &

  echo $! > "$PID_DIR/frontend-launcher.pid"

  wait_for_url "Frontend" "http://localhost:3000" ||
    fail "Xem log: .dev/logs/frontend.log"

  FRONTEND_PID="$(netstat -ano | awk '$2 ~ /:3000$/ && $4=="LISTENING" {print $5; exit}' | tr -d '\r')"

  if [ -n "$FRONTEND_PID" ]; then
    echo "$FRONTEND_PID" > "$PID_DIR/frontend.pid"
  else
    fail "Không xác định được PID thật của frontend"
  fi
fi

echo
echo "========================================"
echo " TẤT CẢ SERVICE ĐÃ SẴN SÀNG"
echo "========================================"
echo "Frontend : http://localhost:3000"
echo "Backend  : http://127.0.0.1:8001"
echo "Swagger  : http://127.0.0.1:8001/docs"
echo
echo "Logs:"
echo "  .dev/logs/backend.log"
echo "  .dev/logs/celery.log"
echo "  .dev/logs/frontend.log"
