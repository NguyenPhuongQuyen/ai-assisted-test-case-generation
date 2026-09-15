#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PID_DIR="$ROOT/.dev/pids"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  PYTHON="$ROOT/.venv/Scripts/python.exe"
else
  echo "[ERROR] Khong tim thay .venv."
  exit 1
fi

port_open() {
  local port="$1"

  "$PYTHON" - "$port" <<'PY'
import socket
import sys

try:
    with socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1):
        sys.exit(0)
except OSError:
    sys.exit(1)
PY
}

stop_pid_file() {
  local pid_file="$1"

  [ -f "$pid_file" ] || return 0

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"

  if [ -n "$pid" ]; then
    if command -v taskkill.exe >/dev/null 2>&1; then
      taskkill.exe //PID "$pid" //T //F >/dev/null 2>&1 || true
    else
      kill -TERM "$pid" >/dev/null 2>&1 || true
      sleep 1
      kill -KILL "$pid" >/dev/null 2>&1 || true
    fi
  fi

  rm -f "$pid_file"
}

stop_port() {
  local name="$1"
  local port="$2"
  local pid_file="$3"

  stop_pid_file "$pid_file"

  if port_open "$port"; then
    echo "[INFO] $name van dang chay tren port $port. Dang dung..."

    if command -v powershell.exe >/dev/null 2>&1; then
      powershell.exe -NoProfile -Command \
        "\$procIds = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
          Select-Object -ExpandProperty OwningProcess -Unique;
         foreach (\$procId in \$procIds) {
           Stop-Process -Id \$procId -Force -ErrorAction SilentlyContinue
         }" >/dev/null 2>&1 || true

    elif command -v lsof >/dev/null 2>&1; then
      local proc_ids
      proc_ids="$(lsof -ti TCP:"$port" 2>/dev/null || true)"

      if [ -n "$proc_ids" ]; then
        kill -TERM $proc_ids >/dev/null 2>&1 || true
        sleep 1
        kill -KILL $proc_ids >/dev/null 2>&1 || true
      fi
    fi
  fi

  for _ in {1..10}; do
    if ! port_open "$port"; then
      echo "[OK] Da dung $name"
      return 0
    fi
    sleep 0.5
  done

  echo "[ERROR] Khong the dung $name tai port $port"
  return 1
}

stop_celery() {
  stop_pid_file "$PID_DIR/celery.pid"

  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
      "\$processes = Get-CimInstance Win32_Process |
        Where-Object { \$_.CommandLine -match 'app\.worker\.celery_app' };

       foreach (\$process in \$processes) {
         Stop-Process -Id \$process.ProcessId -Force -ErrorAction SilentlyContinue
       }" >/dev/null 2>&1 || true

  elif command -v pkill >/dev/null 2>&1; then
    pkill -f 'app\.worker\.celery_app' >/dev/null 2>&1 || true
  fi

  echo "[OK] Da dung Celery"
}

echo "========================================"
echo " Test Case Generator - Stop Development"
echo "========================================"

stop_port "Frontend" 3000 "$PID_DIR/frontend.pid"
stop_celery
stop_port "Backend" 8001 "$PID_DIR/backend.pid"

echo
echo "========================================"
echo " CAC SERVICE CUA UNG DUNG DA DUNG"
echo "========================================"
echo "PostgreSQL va RabbitMQ duoc giu chay vi la service moi truong dung chung."
