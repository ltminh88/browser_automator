# ============================================================
# Browser Automator - Container Image
# Chrome + Xvfb + noVNC + Python API Server
# Compatible with both Podman and Docker
# ============================================================

FROM python:3.11-slim

# Avoid interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# ---- Install Chrome + dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome dependencies
    wget gnupg2 curl unzip \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libxss1 libxtst6 libpango-1.0-0 \
    libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libglib2.0-0 \
    # Virtual display
    xvfb x11vnc x11-utils \
    # VNC/noVNC
    novnc websockify \
    # Process management
    supervisor procps \
    # Utilities
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome Stable
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# ---- Setup working directory ----
WORKDIR /app

# ---- Install Python dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy application code ----
COPY . .

# ---- Create directories ----
RUN mkdir -p /app/chrome_profile /app/data /app/logs

# ---- Setup entrypoint ----
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# ---- Supervisor config ----
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ---- Environment defaults ----
ENV DISPLAY=:99 \
    SCREEN_WIDTH=1920 \
    SCREEN_HEIGHT=1080 \
    SCREEN_DEPTH=24 \
    VNC_PASSWORD=browser123 \
    NOVNC_PORT=6080 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    RUN_MODE=server \
    ENABLE_VNC=false \
    CHROME_NO_SANDBOX=true

# ---- Expose ports ----
EXPOSE 8000 6080 5900

# ---- Health check ----
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
