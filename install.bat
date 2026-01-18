@echo off
REM ============================================
REM Browser Automator - Windows Installation
REM ============================================

echo ============================================
echo   Browser Automator - Installation Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please download Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check Chrome
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Google Chrome found
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [OK] Google Chrome found
) else (
    echo [WARNING] Google Chrome not found in default location
    echo Please install Chrome from: https://www.google.com/chrome/
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Run setup.bat to login to Perplexity/Gemini
echo 2. Edit .env file to set your API key
echo 3. Run start_server.bat to start the API
echo.
pause
