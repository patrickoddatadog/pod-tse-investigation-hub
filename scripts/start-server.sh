#!/usr/bin/env bash
#
# POD Ticket Dashboard — auto-restart wrapper
#
# Usage:  ./scripts/start-server.sh
#
# - Kills any existing instance on port 8501 before starting
# - Restarts the Flask server automatically if it crashes
# - Logs restarts with timestamps
# - Ctrl-C to stop

set -euo pipefail
cd "$(dirname "$0")/.."

PORT=8501
APP="app.py"
MAX_FAST_RESTARTS=5
FAST_RESTART_WINDOW=10

cleanup() {
    echo ""
    echo "[$(date '+%H:%M:%S')] Shutting down POD Ticket Dashboard..."
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

kill_existing() {
    local pids
    pids=$(lsof -ti :"$PORT" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "[$(date '+%H:%M:%S')] Killing existing process(es) on port $PORT: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

fast_restart_count=0
last_restart_time=0

kill_existing

while true; do
    echo ""
    echo "[$(date '+%H:%M:%S')] Starting POD Ticket Dashboard on http://localhost:$PORT"
    echo ""

    python3 "$APP" &
    SERVER_PID=$!

    now=$(date +%s)
    if (( now - last_restart_time < FAST_RESTART_WINDOW )); then
        fast_restart_count=$((fast_restart_count + 1))
    else
        fast_restart_count=0
    fi
    last_restart_time=$now

    if (( fast_restart_count >= MAX_FAST_RESTARTS )); then
        echo "[$(date '+%H:%M:%S')] Server crashed $MAX_FAST_RESTARTS times in rapid succession. Stopping."
        exit 1
    fi

    wait "$SERVER_PID" || true
    echo "[$(date '+%H:%M:%S')] Server exited — restarting in 2 seconds..."
    sleep 2
    kill_existing
done
