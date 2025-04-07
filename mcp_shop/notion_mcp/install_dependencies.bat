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
call npm init -y
call npm install @notionhq/client@^2.3.0 notion-to-md@^4.0.0-alpha.4 base64-js@^1.5.1 --no-fund --no-audit --loglevel=error

echo.
if %ERRORLEVEL% EQU 0 (
  echo Dependency package installation completed.
) else (
  echo Error occurred during dependency installation.
  echo Please install manually: npm install @notionhq/client notion-to-md base64-js
)
echo.
echo =====================================

exit /b 0 