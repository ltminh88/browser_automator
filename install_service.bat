@echo off
REM ============================================
REM Browser Automator - Run as Background Service
REM using NSSM (Non-Sucking Service Manager)
REM ============================================

echo ============================================
echo   Install as Windows Service
echo ============================================
echo.

REM Check if running as admin
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This script requires Administrator privileges!
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Check for NSSM
where nssm >nul 2>&1
if errorlevel 1 (
    echo [INFO] NSSM not found. Downloading...
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to C:\Windows\System32 or add to PATH
    echo Then run this script again.
    pause
    exit /b 1
)

REM Get current directory
set SCRIPT_DIR=%~dp0

REM Load .env
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set %%a=%%b
    )
)

echo Installing BrowserAutomatorAPI service...
echo.

REM Install service
nssm install BrowserAutomatorAPI python
nssm set BrowserAutomatorAPI AppDirectory "%SCRIPT_DIR%"
nssm set BrowserAutomatorAPI AppParameters "-m uvicorn api_server:app --host %API_HOST% --port %API_PORT%"
nssm set BrowserAutomatorAPI AppEnvironmentExtra "BROWSER_API_KEY=%BROWSER_API_KEY%"
nssm set BrowserAutomatorAPI DisplayName "Browser Automator API"
nssm set BrowserAutomatorAPI Description "REST API for browser automation with Perplexity and Gemini"
nssm set BrowserAutomatorAPI Start SERVICE_AUTO_START

echo.
echo Starting service...
nssm start BrowserAutomatorAPI

echo.
echo ============================================
echo   Service installed and started!
echo ============================================
echo.
echo Service name: BrowserAutomatorAPI
echo.
echo To manage the service:
echo   nssm status BrowserAutomatorAPI
echo   nssm stop BrowserAutomatorAPI
echo   nssm start BrowserAutomatorAPI
echo   nssm remove BrowserAutomatorAPI
echo.
pause
