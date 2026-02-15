@echo off
REM ============================================================
REM Browser Automator - Stop Server
REM ============================================================

echo ============================================
echo  Browser Automator - Stopping Server
echo ============================================

REM Detect container runtime
where podman >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set COMPOSE=podman-compose
) else (
    set COMPOSE=docker compose
)

%COMPOSE% -f podman-compose.yml down

echo.
echo Server stopped.
pause
