@echo off
echo Python 의존성 설치를 시작합니다...

REM Python이 설치되어 있는지 확인
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python이 설치되어 있지 않습니다. Python 3.6 이상 버전을 설치해주세요.
    echo https://www.python.org/downloads/
    exit /b 1
)

REM pip이 설치되어 있는지 확인
pip --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo pip이 설치되어 있지 않습니다. Python과 함께 pip을 설치해주세요.
    exit /b 1
)

echo 필요한 Python 패키지를 설치합니다...
pip install notion-client notion2md

if %ERRORLEVEL% neq 0 (
    echo 패키지 설치 중 오류가 발생했습니다.
    exit /b 1
) else (
    echo Notion MCP Python 의존성 설치가 완료되었습니다.
    exit /b 0
) 