@echo off
echo ---------------------------------------
echo Notion MCP 의존성 패키지 설치
echo ---------------------------------------
echo.

echo 설치 위치: %~dp0
cd /d %~dp0

echo.
echo Node.js 패키지 설치 중...
cd /d "%APPDATA%\Claude\mcp_scripts"
npm init -y
npm install @notionhq/client@^2.3.0 notion-to-md@^4.0.0-alpha.4 base64-js@^1.5.1 --no-fund --no-audit --loglevel=error

echo.
if %ERRORLEVEL% EQU 0 (
  echo 의존성 패키지 설치가 완료되었습니다.
) else (
  echo 의존성 패키지 설치 중 오류가 발생했습니다.
  echo 수동으로 설치를 진행하세요: npm install @notionhq/client notion-to-md base64-js
)
echo.
echo ---------------------------------------

exit /b 0 