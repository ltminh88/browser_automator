# Container Deployment Guide

## Prerequisites

- **Docker** (or **Podman** on Windows) installed
- At least 4GB RAM available for the container

## Quick Start

### 1. Build

```bash
# Docker
docker compose -f podman-compose.yml build

# Podman
podman-compose -f podman-compose.yml build
```

### 2. Setup (First Time Only)

Login to Perplexity Pro and Gemini so the browser session is saved:

```bash
# Docker
docker compose -f podman-compose.yml run --rm -p 6080:6080 setup

# Podman
podman-compose -f podman-compose.yml run --rm -p 6080:6080 setup

# Windows
container-setup.bat
```

Then:
1. Open **http://localhost:6080/vnc.html** in your browser
2. VNC password: `browser123`
3. Login to Perplexity Pro in the Chrome window
4. Open a new tab and login to Gemini
5. Press `Ctrl+C` in the terminal when done

### 3. Run Server

```bash
# Docker
docker compose -f podman-compose.yml up -d server

# Podman
podman-compose -f podman-compose.yml up -d server

# Windows
container-start.bat
```

### 4. Test

```bash
curl http://localhost:8000/health
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BROWSER_API_KEY` | (see compose) | API authentication key |
| `API_PORT` | `8000` | API server port |
| `ENABLE_VNC` | `false` | Enable VNC for debugging |
| `VNC_PASSWORD` | `browser123` | VNC access password |
| `RUN_MODE` | `server` | `setup` or `server` |

## Debugging

Enable VNC on the running server to see what Chrome is doing:

```bash
ENABLE_VNC=true docker compose -f podman-compose.yml up server
```

Then open **http://localhost:6080/vnc.html**.

## Stopping

```bash
docker compose -f podman-compose.yml down
# or
container-stop.bat
```

## Data Persistence

- **Chrome profile** (login sessions) → `browser_automator_chrome_profile` volume
- **Response data** → `browser_automator_data` volume

To reset login sessions:
```bash
docker volume rm browser_automator_chrome_profile
```
