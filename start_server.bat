@echo off
REM ============================================
REM Browser Automator - Start API Server
REM ============================================

echo ============================================
echo   Browser Automator - API Server
echo ============================================
echo.

REM Load .env file if exists
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set %%a=%%b
    )
    echo [OK] Loaded configuration from .env
) else (
    echo [WARNING] .env file not found!
    echo Creating from template...
    copy .env.example .env
    echo.
    echo Please edit .env file and set your BROWSER_API_KEY
    echo Then run this script again.
    pause
    exit /b 1
)

REM Check API Key
if "%BROWSER_API_KEY%"=="" (
    echo [ERROR] BROWSER_API_KEY is not set in .env file!
    echo Please edit .env and add your API key.
    pause
    exit /b 1
)

echo.
echo Starting API Server on http://0.0.0.0:%API_PORT%
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn api_server:app --host %API_HOST% --port %API_PORT%

pause
