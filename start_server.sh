#!/bin/bash
# Auto-restart wrapper for Browser Automator API Server
# This script will automatically restart the server if it crashes

cd "$(dirname "$0")"

# Load API key from environment or use default
export BROWSER_API_KEY="${BROWSER_API_KEY:-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}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Browser Automator Server - Auto-Restart${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to cleanup Chrome/chromedriver processes
cleanup() {
    echo -e "${YELLOW}[$(date)] Cleaning up Chrome processes...${NC}"
    pkill -9 -f "chromedriver" 2>/dev/null
    rm -f ~/.browser_automator_profile/SingletonLock 2>/dev/null
    rm -f ~/.browser_automator_profile/SingletonCookie 2>/dev/null
    rm -f ~/.browser_automator_profile/SingletonSocket 2>/dev/null
    sleep 2
}

# Cleanup on script exit
trap "cleanup; exit 0" SIGINT SIGTERM

# Main loop - auto-restart on crash
restart_count=0
max_restarts=10

while true; do
    cleanup
    
    restart_count=$((restart_count + 1))
    echo -e "${GREEN}[$(date)] Starting server (attempt #$restart_count)...${NC}"
    
    # Run the server
    python3 -m uvicorn api_server:app --host 0.0.0.0 --port 1905
    
    exit_code=$?
    echo -e "${RED}[$(date)] Server exited with code: $exit_code${NC}"
    
    # Check restart limit
    if [ $restart_count -ge $max_restarts ]; then
        echo -e "${RED}[$(date)] Max restarts ($max_restarts) reached. Stopping.${NC}"
        exit 1
    fi
    
    # Wait before restart
    echo -e "${YELLOW}[$(date)] Restarting in 5 seconds...${NC}"
    sleep 5
done
