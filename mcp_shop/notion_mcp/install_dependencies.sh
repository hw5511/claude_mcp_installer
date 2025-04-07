#!/bin/bash

echo "---------------------------------------"
echo "Notion MCP 의존성 패키지 설치"
echo "---------------------------------------"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "설치 위치: $SCRIPT_DIR"

# MCP 스크립트 폴더로 이동
cd "$HOME/.config/Claude/mcp_scripts" 2>/dev/null || cd "$HOME/Library/Application Support/Claude/mcp_scripts"

echo ""
echo "Node.js 패키지 설치 중..."
npm init -y
npm install @notionhq/client@^2.3.0 notion-to-md@^4.0.0-alpha.4 base64-js@^1.5.1 --no-fund --no-audit --loglevel=error

echo ""
if [ $? -eq 0 ]; then
  echo "의존성 패키지 설치가 완료되었습니다."
else
  echo "의존성 패키지 설치 중 오류가 발생했습니다."
  echo "수동으로 설치를 진행하세요: npm install @notionhq/client notion-to-md base64-js"
fi
echo ""
echo "---------------------------------------"

exit 0 