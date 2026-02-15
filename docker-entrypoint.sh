#!/bin/bash
set -e

echo "============================================"
echo " Browser Automator Container"
echo " Mode: ${RUN_MODE:-server}"
echo "============================================"

# ---- Start Xvfb (virtual display) ----
start_xvfb() {
    echo "[Entrypoint] Starting Xvfb on display ${DISPLAY}..."
    Xvfb ${DISPLAY} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &
    sleep 2
    echo "[Entrypoint] Xvfb started."
}

# ---- Start VNC + noVNC ----
start_vnc() {
    echo "[Entrypoint] Starting VNC server..."
    x11vnc -display ${DISPLAY} -forever -shared -rfbport 5900 -passwd ${VNC_PASSWORD} -bg -o /app/logs/x11vnc.log
    
    echo "[Entrypoint] Starting noVNC on port ${NOVNC_PORT}..."
    websockify --web=/usr/share/novnc ${NOVNC_PORT} localhost:5900 &
    
    echo "[Entrypoint] ============================================"
    echo "[Entrypoint]  noVNC URL: http://localhost:${NOVNC_PORT}/vnc.html"
    echo "[Entrypoint]  VNC Password: ${VNC_PASSWORD}"
    echo "[Entrypoint] ============================================"
}

# ---- Cleanup Chrome locks ----
cleanup_locks() {
    echo "[Entrypoint] Cleaning up Chrome profile locks..."
    rm -f /app/chrome_profile/SingletonLock
    rm -f /app/chrome_profile/SingletonCookie
    rm -f /app/chrome_profile/SingletonSocket
}

# ---- Kill stale Chrome processes ----
cleanup_chrome() {
    pkill -9 -f chromedriver 2>/dev/null || true
    pkill -9 -f "chrome.*user-data-dir" 2>/dev/null || true
}

# ============================================================
# MAIN
# ============================================================

cleanup_chrome
cleanup_locks
start_xvfb

case "${RUN_MODE}" in
    setup)
        echo "[Entrypoint] === SETUP MODE ==="
        echo "[Entrypoint] Opening Chrome for manual login..."
        
        start_vnc
        
        # Launch Chrome with the profile directory
        google-chrome-stable \
            --no-sandbox \
            --disable-dev-shm-usage \
            --disable-gpu \
            --user-data-dir=/app/chrome_profile \
            --no-first-run \
            --password-store=basic \
            --start-maximized \
            "https://www.perplexity.ai/" &
        
        echo ""
        echo "============================================"
        echo " SETUP INSTRUCTIONS:"
        echo " 1. Open browser: http://localhost:${NOVNC_PORT}/vnc.html"
        echo " 2. Enter VNC password: ${VNC_PASSWORD}"
        echo " 3. Login to Perplexity Pro"
        echo " 4. Login to Gemini (open new tab)"
        echo " 5. Press Ctrl+C when done"
        echo "============================================"
        echo ""
        
        # Keep running until user stops
        wait
        ;;
    
    server)
        echo "[Entrypoint] === SERVER MODE ==="
        
        # Optional VNC for debugging
        if [ "${ENABLE_VNC}" = "true" ]; then
            echo "[Entrypoint] VNC debugging enabled"
            start_vnc
        fi
        
        echo "[Entrypoint] Starting API server on ${API_HOST}:${API_PORT}..."
        exec python api_server.py
        ;;
    
    *)
        echo "[Entrypoint] Unknown RUN_MODE: ${RUN_MODE}"
        echo "[Entrypoint] Valid modes: setup, server"
        exit 1
        ;;
esac
