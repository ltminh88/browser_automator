@echo off
REM ============================================
REM Browser Automator - Account Setup
REM ============================================

echo ============================================
echo   Browser Automator - Account Setup
echo ============================================
echo.
echo This will open a browser for you to login to:
echo - Perplexity (Pro account recommended for Deep Research)
echo - Google/Gemini
echo.
echo Close the browser window when you are done logging in.
echo.
pause

python main.py --setup

echo.
echo Setup complete! Your login session has been saved.
echo.
pause
