@echo off
REM ============================================================
REM Browser Automator - Start Server
REM ============================================================
REM Starts the API server in detached mode.
REM Make sure you've run container-setup.bat first!
REM ============================================================

echo ============================================
echo  Browser Automator - Starting Server
echo ============================================

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

REM Set API key (change this or set environment variable)
if "%BROWSER_API_KEY%"=="" (
    set BROWSER_API_KEY=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
)

echo.
echo [1/2] Building container image...
%COMPOSE% -f podman-compose.yml build server
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Starting server...
%COMPOSE% -f podman-compose.yml up -d server
if %ERRORLEVEL% neq 0 (
    echo ERROR: Server failed to start!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Server is running!
echo  API:    http://localhost:8000
echo  Health: http://localhost:8000/health
echo  Docs:   http://localhost:8000/docs
echo ============================================
echo.
echo To view logs:  %COMPOSE% -f podman-compose.yml logs -f server
echo To stop:       container-stop.bat
echo.
pause
