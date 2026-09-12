#!/usr/bin/env bash

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="$ROOT/.dev"
PID_DIR="$RUNTIME_DIR/pids"

stop_pid() {
  local name="$1"
  local file="$2"

  if [ ! -f "$file" ]; then
    echo "[SKIP] $name: không có PID file"
    return 0
  fi

  local pid
  pid="$(cat "$file" 2>/dev/null || true)"

  if [ -z "$pid" ]; then
    rm -f "$file"
    echo "[SKIP] $name: PID rỗng"
    return 0
  fi

  if kill -0 "$pid" 2>/dev/null; then
    # Windows: dừng cả process tree để không sót Node/Next.js child process.
    taskkill //PID "$pid" //T //F >/dev/null 2>&1 ||       kill "$pid" 2>/dev/null || true

    echo "[OK] Đã dừng $name (PID $pid)"
  else
    echo "[SKIP] $name: process đã dừng"
  fi

  rm -f "$file"
}

echo "========================================"
echo " Test Case Generator - Stop Development"
echo "========================================"

echo "[INFO] Đang dừng Frontend theo port 3000..."

FRONTEND_PID="$(netstat -ano | awk '$2 ~ /:3000$/ && $4=="LISTENING" {print $5; exit}' | tr -d '\r')"

if [ -n "$FRONTEND_PID" ]; then
  taskkill //PID "$FRONTEND_PID" //T //F >/dev/null 2>&1 || true
  echo "[OK] Đã dừng Frontend (PID $FRONTEND_PID)"
else
  echo "[SKIP] Frontend đã dừng"
fi

rm -f "$PID_DIR/frontend.pid" "$PID_DIR/frontend-launcher.pid"

stop_pid "Celery" "$PID_DIR/celery.pid"
stop_pid "Backend" "$PID_DIR/backend.pid"

echo
echo "========================================"
echo " CÁC SERVICE CỦA APP ĐÃ ĐƯỢC DỪNG"
echo "========================================"
echo "RabbitMQ được giữ nguyên để tránh tắt service dùng chung."
