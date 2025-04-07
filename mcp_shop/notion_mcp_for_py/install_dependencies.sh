#!/bin/bash

echo "Python 의존성 설치를 시작합니다..."

# Python이 설치되어 있는지 확인
if ! command -v python3 &> /dev/null; then
    echo "Python 3가 설치되어 있지 않습니다. Python 3.6 이상 버전을 설치해주세요."
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "Fedora: sudo dnf install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# pip이 설치되어 있는지 확인
if ! command -v pip3 &> /dev/null; then
    echo "pip3이 설치되어 있지 않습니다. pip3을 설치해주세요."
    echo "Ubuntu/Debian: sudo apt install python3-pip"
    echo "Fedora: sudo dnf install python3-pip"
    echo "macOS: brew install python3 (pip3 포함)"
    exit 1
fi

echo "필요한 Python 패키지를 설치합니다..."
pip3 install notion-client notion2md

if [ $? -ne 0 ]; then
    echo "패키지 설치 중 오류가 발생했습니다."
    exit 1
else
    echo "Notion MCP Python 의존성 설치가 완료되었습니다."
    exit 0
fi 