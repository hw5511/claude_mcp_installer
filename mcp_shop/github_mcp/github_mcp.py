#!/usr/bin/env python3
# GitHub MCP Server 연동 스크립트
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# Docker 명령어 확인
def check_docker_installed():
    """Docker가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(['docker', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True,
                               check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_token():
    """GitHub 개인 액세스 토큰이 설정되어 있는지 확인"""
    token = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
    if token:
        return True, token
    return False, None

def setup_github_token():
    """GitHub 개인 액세스 토큰 설정"""
    print("\n===== GitHub 개인 액세스 토큰 설정 =====")
    print("GitHub MCP 서버는 GitHub API를 사용하기 위해 개인 액세스 토큰이 필요합니다.")
    print("토큰 생성 방법: GitHub > Settings > Developer settings > Personal access tokens")
    print("필요한 권한: repo, user, workflow, admin:org (필요에 따라 조정)\n")
    
    token = input("GitHub 개인 액세스 토큰을 입력하세요: ").strip()
    
    if not token:
        print("토큰이 입력되지 않았습니다. 설정을 취소합니다.")
        return False, None
    
    return True, token

def configure_github_mcp(token, config_file):
    """GitHub MCP 서버 구성 설정"""
    # 기존 설정 불러오기
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}
    
    # mcpServers 섹션이 없으면 추가
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    # GitHub MCP 서버 설정
    config['mcpServers']['github'] = {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server"
        ],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": token
        }
    }
    
    # 설정 저장
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    return True

def install_github_mcp(token):
    """GitHub MCP 서버 설치"""
    # Claude 데스크톱 설정 디렉토리 확인
    claude_dir = os.path.join(os.environ['APPDATA'], 'Claude')
    config_file = os.path.join(claude_dir, 'claude_desktop_config.json')
    
    # 설정 파일이 없는 경우 기본 구조 생성
    if not os.path.exists(claude_dir):
        os.makedirs(claude_dir, exist_ok=True)
    
    # GitHub MCP 서버 설정
    success = configure_github_mcp(token, config_file)
    
    if success:
        print("\n✅ GitHub MCP 서버 설정이 완료되었습니다.")
        print("다음 단계:")
        print("1. Claude 데스크톱 앱을 재시작하세요.")
        print("2. Claude와의 대화에서 다음과 같이 GitHub 작업을 요청할 수 있습니다:")
        print("   - 'GitHub 저장소에서 파일을 찾아줘'")
        print("   - '내 GitHub 계정에 새 이슈를 생성해줘'")
        print("   - '이 PR의 변경 내용을 검토해줘'")
        return True
    else:
        print("\n❌ GitHub MCP 서버 설정 중 오류가 발생했습니다.")
        return False

def main():
    """메인 함수"""
    print("\n===== GitHub MCP 서버 설치 =====")
    
    # Docker 설치 확인
    if not check_docker_installed():
        print("\n❌ Docker가 설치되어 있지 않습니다.")
        print("GitHub MCP 서버를 실행하려면 Docker가 필요합니다.")
        print("Docker를 설치한 후 다시 시도해주세요: https://www.docker.com/get-started")
        return False
    
    # GitHub 토큰 확인
    token_exists, token = check_token()
    
    if not token_exists:
        # 토큰 설정
        success, token = setup_github_token()
        if not success:
            return False
    
    # GitHub MCP 서버 설치
    success = install_github_mcp(token)
    
    return success

if __name__ == "__main__":
    main() 