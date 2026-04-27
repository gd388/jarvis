#!/usr/bin/env bash
# Jarvis launcher — voice-only backend, no frontend.

cd "$(dirname "$0")"

# ── Ensure Brave is running with remote debugging ────────────────── #
# Jarvis attaches to this port to open tabs in your existing Brave window,
# with all your saved credentials and extensions intact.
if ! nc -z localhost 9222 2>/dev/null; then
    echo "⚙️  (Re)starting Brave with remote debugging on port 9222…"
    pkill -9 -f "brave-browser" 2>/dev/null || true
    pkill -9 -f "brave"         2>/dev/null || true
    sleep 1.5   # wait for profile lock files to clear
    brave-browser --remote-debugging-port=9222 \
                  --profile-directory=Default \
                  --no-first-run \
                  --no-default-browser-check \
                  2>/dev/null &
    # Poll until the debug port is ready (up to 15 s)
    echo -n "⏳  Waiting for Brave to start"
    for i in $(seq 1 30); do
        sleep 0.5
        if nc -z localhost 9222 2>/dev/null; then
            echo " ✓"
            break
        fi
        echo -n "."
    done
    nc -z localhost 9222 2>/dev/null || echo " ⚠️  Brave did not open debug port in time"
fi

# ── Kill any stale Jarvis instance ───────────────────────────────────────── #
deactivate 2>/dev/null || true
pkill -9 -f "python3 main.py" 2>/dev/null || true
sleep 0.5

# ── Launch ───────────────────────────────────────────────────────────────── #
source venv/bin/activate
exec python3 main.py 2>/dev/null
