@echo off
REM ============================================================
REM Browser Automator - Setup (Login to Perplexity/Gemini)
REM ============================================================
REM This opens a browser via VNC so you can login manually.
REM After login, the session is saved for the server to use.
REM ============================================================

echo ============================================
echo  Browser Automator - Setup Mode
echo ============================================
echo.
echo This will:
echo  1. Build the container image
echo  2. Open Chrome via VNC for you to login
echo.

REM Detect container runtime
where podman >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set RUNTIME=podman
    set COMPOSE=podman-compose
) else (
    set RUNTIME=docker
    set COMPOSE=docker compose
)

echo Using: %RUNTIME%
echo.

REM Build first
echo [1/2] Building container image...
%COMPOSE% -f podman-compose.yml build setup
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Run setup
echo.
echo [2/2] Starting setup container...
echo.
echo ============================================
echo  INSTRUCTIONS:
echo  1. Open browser: http://localhost:6080/vnc.html
echo  2. Enter VNC password: browser123
echo  3. Login to Perplexity Pro
echo  4. Login to Gemini ^(open new tab^)
echo  5. Press Ctrl+C here when done
echo ============================================
echo.
%COMPOSE% -f podman-compose.yml run --rm -p 6080:6080 -p 5900:5900 setup

echo.
echo Setup complete! Run container-start.bat to start the server.
pause
