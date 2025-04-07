@echo off
echo =====================================
echo Notion MCP Dependencies Installation
echo =====================================
echo.

echo Installation path: %~dp0
cd /d %~dp0

echo.
echo Installing Node.js packages...
cd /d "%APPDATA%\Claude\mcp_scripts"

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Node.js is not installed or not in the PATH.
  echo.
  echo Please install Node.js from https://nodejs.org/
  echo Then try running this script again, or install dependencies manually.
  goto :manual_guide
)

call npm init -y
call npm install @notionhq/client@^2.3.0 notion-to-md@^4.0.0-alpha.4 base64-js@^1.5.1 --no-fund --no-audit --loglevel=error

echo.
if %ERRORLEVEL% EQU 0 (
  echo Dependency package installation completed successfully!
  echo.
  echo =====================================
  exit /b 0
) else (
  echo ERROR: Failed to install dependencies automatically.
  echo.
  goto :manual_guide
)

:manual_guide
echo =====================================
echo Manual Installation Guide
echo =====================================
echo.
echo To manually install the required dependencies, follow these steps:
echo.
echo 1. Make sure Node.js is installed. Download from: https://nodejs.org/
echo 2. Open Command Prompt (cmd) or PowerShell
echo 3. Run the following commands:
echo.
echo    cd "%APPDATA%\Claude\mcp_scripts"
echo    npm init -y
echo    npm install @notionhq/client notion-to-md base64-js
echo.
echo 4. Restart Claude Desktop application
echo.
echo =====================================
exit /b 1 