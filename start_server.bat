@echo off
echo ================================
echo  MCP Server with Ngrok Setup
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ================================
echo  Starting MCP Server + Ngrok
echo ================================
echo.
echo Server will be available at:
echo - Local:  http://localhost:8086
echo - Public: (ngrok will show the URL)
echo - Dashboard: http://localhost:4040
echo.
echo Bearer Token: scheduling_mcp_token_123
echo.
echo Press Ctrl+C to stop the server
echo ================================
echo.

REM Start the server with ngrok
python start_with_ngrok.py

pause
