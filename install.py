#!/usr/bin/env python3
import os
import sys
import json
import shutil
import argparse
import platform
import tempfile
import locale
import subprocess
from pathlib import Path
from colorama import Fore, init
import requests  # GitHub API 사용을 위해 추가
import io
import zipfile  # ZIP 파일 처리 위해 추가

# 설정 파일 import
import config

# Initialize colorama
init()

# 전역 언어 설정
LANG = config.DEFAULT_LANG
TEXTS = config.TEXTS
GITHUB_REPO_OWNER = config.GITHUB_REPO_OWNER
GITHUB_REPO_NAME = config.GITHUB_REPO_NAME
GITHUB_REPO_BRANCH = config.GITHUB_REPO_BRANCH
MCP_SHOP_PATH = config.MCP_SHOP_PATH
REMOTE_MCP_CACHE_DIR = config.REMOTE_MCP_CACHE_DIR

def _(key, lang=config.DEFAULT_LANG):
    """다국어 메시지 가져오기"""
    return config.TEXTS.get(lang, config.TEXTS['en']).get(key, config.TEXTS['en'].get(key, key))

def clear_screen():
    """화면 지우기"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """출력 배너 표시"""
    print("\n" + "=" * 70)
    print(TEXTS[LANG]['banner_title'].center(70))
    print("=" * 70)
    print(TEXTS[LANG]['banner_desc'])
    print(TEXTS[LANG]['banner_features'])
    print("=" * 70 + "\n")

def check_installation():
    """이미 설치되어 있는지 확인"""
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    
    if os.path.exists(mcp_scripts_path) and os.path.exists(config_path):
        return True
    return False

def create_mcp_scripts_dir():
    """mcp_scripts 디렉토리 생성"""
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    os.makedirs(mcp_scripts_path, exist_ok=True)
    print(f"{_('create_dir')} {mcp_scripts_path}")

def copy_files_to_mcp_scripts():
    """파일 복사"""
    # 실행 중인 스크립트의 위치 확인
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    
    print(_('copying_files'))
    files_to_copy = ['filesystem.py', 'terminal.py', 'allowed_dirs_manager.py']
    
    for file in files_to_copy:
        src_file = os.path.join(src_dir, file)
        if os.path.exists(src_file):
            shutil.copy(src_file, mcp_scripts_path)
            print(_('file_copied').format(file))
        else:
            print(_('file_error').format(src_file))

def configure_json_file():
    """JSON 파일 설정"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    src_json_path = os.path.join(src_dir, 'claude_desktop_config.json')
    dest_json_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    
    print(_('configuring_json'))
    with open(src_json_path, 'r', encoding='utf-8') as f:
        config = f.read()
    
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    config = config.replace("{MCP_SCRIPTS_DIR}", mcp_scripts_path.replace("\\", "\\\\"))
    
    with open(dest_json_path, 'w', encoding='utf-8') as f:
        f.write(config)
    print(_('json_saved').format(dest_json_path))

def copy_allowed_dirs_file():
    """allowed_dirs.json 파일 복사 및 설정"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    src_allowed_dirs_path = os.path.join(src_dir, 'allowed_dirs.json')
    dest_allowed_dirs_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts', 'allowed_dirs.json')
    
    print(_('configuring_allowed_dirs'))
    # 템플릿 파일 읽기
    with open(src_allowed_dirs_path, 'r', encoding='utf-8') as f:
        allowed_dirs_template = json.load(f)
    
    # 사용자 이름 가져오기
    username = os.environ['USERNAME']
    
    # 경로 업데이트
    allowed_dirs = []
    for dir_path in allowed_dirs_template.get("allowed_dirs", []):
        # [사용자 이름] 부분을 실제 사용자 이름으로 대체
        updated_path = dir_path.replace("[사용자 이름]", username)
        allowed_dirs.append(updated_path)
    
    # 업데이트된 allowed_dirs.json 파일 저장
    with open(dest_allowed_dirs_path, 'w', encoding='utf-8') as f:
        json.dump({"allowed_dirs": allowed_dirs}, f, indent=4)
    print(_('allowed_dirs_saved').format(dest_allowed_dirs_path))

def manage_allowed_dirs():
    """허용 경로 관리"""
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    allowed_dirs_path = os.path.join(mcp_scripts_path, 'allowed_dirs.json')
    
    if not os.path.exists(allowed_dirs_path):
        print(_('no_allowed_dirs_file'))
        return
    
    with open(allowed_dirs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    while True:
        print("\n" + _('allowed_dirs_management'))
        print("-" * 40)
        print(_('current_allowed_dirs'))
        for i, path in enumerate(data["allowed_dirs"], 1):
            print(f"  {i}. {path}")
        
        print("\n" + _('options'))
        print(_('add_path'))
        print(_('remove_path'))
        print(_('save_exit'))
        print(_('cancel_exit'))
        
        choice = input(f"\n{_('select')} (1-4): ")
        
        if choice == '1':
            path = input(_('enter_path') + " ")
            if path and path not in data["allowed_dirs"]:
                data["allowed_dirs"].append(os.path.normpath(path))
                print(_('path_added').format(path))
            else:
                print(_('path_invalid'))
        
        elif choice == '2':
            try:
                idx = int(input(_('enter_number') + " "))
                if 1 <= idx <= len(data["allowed_dirs"]):
                    removed = data["allowed_dirs"].pop(idx - 1)
                    print(_('removed').format(removed))
                else:
                    print(_('invalid_number'))
            except ValueError:
                print(_('numeric_required'))
        
        elif choice == '3':
            with open(allowed_dirs_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(_('changes_saved'))
            break
        
        elif choice == '4':
            print(_('changes_cancelled'))
            break
        
        else:
            print(_('invalid_choice'))

def install():
    """설치 실행"""
    print("\n" + _('install_start'))
    create_mcp_scripts_dir()
    copy_files_to_mcp_scripts()
    configure_json_file()
    copy_allowed_dirs_file()
    print("\n" + _('install_complete'))
    print(_('restart_claude'))

def uninstall():
    """설치 제거"""
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    
    print("\n" + _('uninstall_start'))
    
    if os.path.exists(mcp_scripts_path):
        shutil.rmtree(mcp_scripts_path)
        print(_('dir_deleted').format(mcp_scripts_path))
    
    if os.path.exists(config_path):
        os.remove(config_path)
        print(_('config_deleted').format(config_path))
    
    print("\n" + _('uninstall_complete'))

def browse_mcp_shop():
    """MCP Shop에서 사용 가능한 MCP 템플릿을 보여주고 설치할 수 있는 기능"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shop_dir = os.path.join(script_dir, 'mcp_shop')
    
    if not os.path.exists(shop_dir):
        print(TEXTS[LANG]['mcp_shop_not_found'])
        return
    
    # 사용 가능한 MCP 템플릿 목록 가져오기
    available_mcps = [d for d in os.listdir(shop_dir) 
                      if os.path.isdir(os.path.join(shop_dir, d))]
    
    if not available_mcps:
        print(TEXTS[LANG]['no_mcps_available'])
        return
    
    while True:
        clear_screen()
        print("\n" + TEXTS[LANG]['mcp_shop_title'])
        print("-" * 40)
        print(TEXTS[LANG]['available_mcps'])
        for i, mcp in enumerate(available_mcps, 1):
            # 메타데이터가 있는 경우 이름과 설명 표시
            metadata_file = os.path.join(shop_dir, mcp, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    print(f"  {i}. {metadata.get('name', mcp)} - {metadata.get('description', '')}")
                except:
                    print(f"  {i}. {mcp}")
            else:
                print(f"  {i}. {mcp}")
        
        print("\n" + TEXTS[LANG]['options'])
        print(TEXTS[LANG]['install_mcp'])
        print(TEXTS[LANG]['back_to_main'])
        
        choice = input(f"\n{TEXTS[LANG]['select']} (1-{len(available_mcps)+1}): ")
        
        if choice.isdigit() and 1 <= int(choice) <= len(available_mcps):
            selected_mcp = available_mcps[int(choice)-1]
            install_mcp_template(selected_mcp)
            input("\nPress Enter to continue...")
        elif choice == str(len(available_mcps)+1):
            break
        else:
            print(TEXTS[LANG]['invalid_choice'])

def install_mcp_template(mcp_name, mcp_dir=None):
    """선택한 MCP 템플릿을 설치하는 함수
    
    Args:
        mcp_name: MCP 템플릿 이름
        mcp_dir: MCP 템플릿 디렉토리 경로 (원격 다운로드 시 제공)
    """
    # mcp_dir이 제공되지 않으면 로컬 경로 사용
    if mcp_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_shop_dir = os.path.join(script_dir, 'mcp_shop')
        mcp_dir = os.path.join(mcp_shop_dir, mcp_name)
    
    if not os.path.exists(mcp_dir):
        print(TEXTS[LANG]['mcp_not_found'].format(mcp_name))
        return
    
    print(TEXTS[LANG]['installing_mcp'].format(mcp_name))
    
    # 메타데이터 파일 확인
    metadata_file = os.path.join(mcp_dir, 'metadata.json')
    auth_tokens = {}
    requires_dependencies = False
    install_script = None
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 의존성 설치가 필요한지 확인
            requires_dependencies = metadata.get('requires_dependencies', False)
            
            # 운영체제에 맞는 설치 스크립트 결정
            if requires_dependencies and 'install_script' in metadata:
                os_type = platform.system().lower()
                if os_type == 'windows' and 'windows' in metadata['install_script']:
                    install_script = metadata['install_script']['windows']
                elif os_type == 'darwin' and 'macos' in metadata['install_script']:
                    install_script = metadata['install_script']['macos']
                elif os_type == 'linux' and 'linux' in metadata['install_script']:
                    install_script = metadata['install_script']['linux']
            
            # 인증이 필요한 경우
            if metadata.get('requires_authentication', False):
                # 기존 auth_guide 처리 코드 대신 authentication_guide 사용
                auth_guides = metadata.get('authentication_guide', [])
                token_name = metadata.get('authentication_token_name', '')
                token_prompt = metadata.get('authentication_token_prompt', '인증 정보를 입력하세요')
                
                # 인증 가이드 표시
                clear_screen()
                print(f"\n===== {metadata.get('name', '인증 설정')} 인증 설정 =====")
                print(f"\n{metadata.get('description', '')}")
                
                # 인증 가이드 단계 표시
                if auth_guides:
                    print("\n인증 설정 단계:")
                    for i, step in enumerate(auth_guides, 1):
                        print(f"  {step}")
                
                # 토큰/API 키 입력 받기
                print("\n")  # 공백 추가
                token_value = input(f"{token_prompt}: ").strip()
                
                if token_value:
                    if token_name:
                        auth_tokens[token_name] = token_value
                else:
                    print("인증 정보를 입력하지 않아 설치를 취소합니다.")
                    return
        except Exception as e:
            print(f"메타데이터 파일 처리 중 오류 발생: {str(e)}")
    
    # 1. MCP 스크립트 파일 복사
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    script_files = [f for f in os.listdir(mcp_dir) if f.endswith('.py') or f.endswith('.js')]
    
    copied_script_files = []
    for script_file in script_files:
        src_file = os.path.join(mcp_dir, script_file)
        dest_file = os.path.join(mcp_scripts_path, script_file)
        shutil.copy(src_file, dest_file)
        
        # 복사된 파일 확인
        if os.path.exists(dest_file):
            copied_script_files.append(script_file)
            print(TEXTS[LANG]['file_copied'].format(script_file))
        else:
            print(f"경고: {script_file} 파일이 제대로 복사되지 않았습니다.")
    
    # 2. config.json 업데이트
    config_template_files = [f for f in os.listdir(mcp_dir) if f.endswith('_config_template.json')]
    if config_template_files:
        config_file = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
        
        if os.path.exists(config_file):
            # 기존 설정 파일 로드
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 각 템플릿 파일에서 설정 추가
            for template_file in config_template_files:
                with open(os.path.join(mcp_dir, template_file), 'r', encoding='utf-8') as f:
                    template_config = json.load(f)
                    print(f"템플릿 파일 '{template_file}' 내용: {json.dumps(template_config, indent=2)}")  # 디버그 메시지 추가
                
                # mcpServers에 템플릿 추가
                if 'mcpServers' in config:
                    for server_name, server_config in template_config.items():
                        print(f"템플릿에서 서버 설정 처리 중: {server_name}")  # 디버그 메시지 추가
                        
                        # 원본 서버 설정 백업
                        original_config = server_config.copy() if isinstance(server_config, dict) else {}
                        
                        # {MCP_SCRIPTS_DIR} 플레이스홀더 교체
                        if 'args' in server_config:
                            # 운영체제별 경로 구분자 처리를 개선
                            # Windows에서는 백슬래시를 사용하고, JSON 이스케이프를 위해 이중 백슬래시로 변환
                            mcp_scripts_path_formatted = mcp_scripts_path.replace("\\", "\\\\")
                            print(f"args 처리 전: {server_config['args']}")  # 디버그 메시지 추가
                            
                            try:
                                # 원본 템플릿의 args 값을 보존
                                if 'args' in template_config[server_name] and template_config[server_name]['args']:
                                    server_config['args'] = []
                                    
                                    for arg in template_config[server_name]['args']:
                                        # {MCP_SCRIPTS_DIR} 플레이스홀더 교체
                                        if "{MCP_SCRIPTS_DIR}" in arg:
                                            # 슬래시나 백슬래시 모두 백슬래시로 표준화
                                            new_arg = arg.replace("{MCP_SCRIPTS_DIR}", mcp_scripts_path_formatted)
                                            
                                            # 필요한 경우 슬래시를 백슬래시로 변환
                                            if '/' in new_arg:
                                                new_arg = new_arg.replace('/', '\\\\')
                                            
                                            server_config['args'].append(new_arg)
                                        else:
                                            server_config['args'].append(arg)
                                else:
                                    print(f"템플릿에 args가 없거나 비어있어 기본값 설정")  # 디버그 메시지 추가
                                    # 기본값으로 스크립트 경로 설정
                                    server_config['args'] = []  # 빈 배열로 초기화
                                    for script_file in copied_script_files:
                                        if script_file.endswith('.py'):
                                            script_path = os.path.join(mcp_scripts_path_formatted, script_file)
                                            # 슬래시를 백슬래시로 변환
                                            script_path = script_path.replace('/', '\\\\')
                                            server_config['args'].append(script_path)
                                            print(f"기본 Python 스크립트 경로 추가: {script_path}")  # 디버그 메시지 추가
                                            break
                                
                                # args가 여전히 비어있는지 확인 (안전장치)
                                if not server_config['args'] and copied_script_files:
                                    print(f"안전장치: args가 여전히 비어있어 스크립트 경로 강제 추가")
                                    for script_file in copied_script_files:
                                        if script_file.endswith('.py'):
                                            script_path = os.path.join(mcp_scripts_path_formatted, script_file)
                                            script_path = script_path.replace('/', '\\\\')
                                            server_config['args'] = [script_path]
                                            break
                            except Exception as e:
                                print(f"args 처리 중 오류 발생: {str(e)}")
                                # 오류 발생 시 기본 스크립트 파일 사용
                                server_config['args'] = []
                                for script_file in copied_script_files:
                                    if script_file.endswith('.py'):
                                        script_path = os.path.join(mcp_scripts_path_formatted, script_file)
                                        script_path = script_path.replace('/', '\\\\')
                                        server_config['args'].append(script_path)
                                        break
                            
                            print(f"args 처리 후: {server_config['args']}")  # 디버그 메시지 추가
                            
                            # 스크립트 경로 검증
                            for i, arg in enumerate(server_config['args']):
                                # 스크립트 파일 경로인 경우 (파이썬/자바스크립트 파일)
                                if isinstance(arg, str) and (arg.endswith('.py') or arg.endswith('.js')):
                                    script_path = arg
                                    if '{MCP_SCRIPTS_DIR}' in script_path:
                                        continue  # 미처리된 플레이스홀더가 있으면 건너뜀
                                    
                                    # 경로에서 이스케이프된 백슬래시를 단일 백슬래시로 변환
                                    test_path = script_path.replace('\\\\', '\\')
                                    
                                    # 절대 경로인지 확인
                                    if not os.path.isabs(test_path):
                                        test_path = os.path.join(mcp_scripts_path, os.path.basename(test_path))
                                    
                                    # 실제 파일 존재 여부 확인
                                    if not os.path.exists(test_path):
                                        print(f"경고: 서버 '{server_name}'에 지정된 스크립트 파일이 존재하지 않습니다: {test_path}")
                                        
                                        # 대안 파일 확인 (복사된 파일 목록에서)
                                        for copied_file in copied_script_files:
                                            if copied_file == os.path.basename(test_path):
                                                alternative_file = os.path.join(mcp_scripts_path, copied_file).replace('\\', '\\\\')
                                                print(f"대체 파일 경로 발견: {alternative_file}")
                                                server_config['args'][i] = alternative_file
                                                break
                        
                        # 인증 토큰이 있는 경우 설정에 추가
                        if 'env' in server_config and auth_tokens:
                            for env_var, token in auth_tokens.items():
                                if env_var in server_config['env']:
                                    # 토큰 플레이스홀더 교체
                                    env_value = server_config['env'][env_var]
                                    # ${변수명} 형식 지원 추가
                                    if isinstance(env_value, str) and (env_value == env_var or env_value == f"${{{env_var}}}" or env_value == f"{env_var}"):
                                        server_config['env'][env_var] = token
                        
                        # 기존 설정에 추가
                        config['mcpServers'][server_name] = server_config
                        print(TEXTS[LANG]['config_updated'].format(server_name))
            
            # 업데이트된 설정 저장
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
    
    # 3. 의존성 설치 스크립트 실행 (필요한 경우)
    if requires_dependencies and install_script:
        install_script_path = os.path.join(mcp_dir, install_script)
        if os.path.exists(install_script_path):
            print(f"\nStarting dependency package installation...")
            try:
                if platform.system().lower() == 'windows':
                    subprocess.run([install_script_path], shell=True, check=True)
                else:
                    # Linux/macOS에서는 실행 권한 부여 후 실행
                    os.chmod(install_script_path, 0o755)
                    subprocess.run([install_script_path], shell=True, check=True)
                print("Dependency package installation completed.")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred during dependency installation: {str(e)}")
                print("Please install required packages manually.")
        else:
            print(f"Installation script not found: {install_script_path}")
    
    print(TEXTS[LANG]['mcp_install_complete'].format(mcp_name))
    print(TEXTS[LANG]['restart_claude'])
    
    # 설치 완료 후 설정 파일 검증
    config_file = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    if os.path.exists(config_file):
        try:
            # 설정 파일 로드
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # MCP 서버 설정 검증
            if 'mcpServers' in config and mcp_name in config['mcpServers']:
                server_config = config['mcpServers'][mcp_name]
                validation_issues = []
                
                # 1. 스크립트 파일 경로 검증
                if 'args' in server_config:
                    # args 배열이 비어있는지 확인
                    if not server_config['args']:
                        print(f"경고: 서버 '{mcp_name}'의 args 배열이 비어 있습니다. 자동으로 경로를 할당합니다.")
                        # 복사된 스크립트 파일 중에서 Python 파일 찾기
                        for script_file in copied_script_files:
                            if script_file.endswith('.py'):
                                # 경로 형식 맞추기
                                script_path = os.path.join(mcp_scripts_path, script_file).replace('\\', '\\\\')
                                server_config['args'] = [script_path]
                                print(f"args 배열에 추가된 경로: {script_path}")
                                
                                # 설정 파일 업데이트
                                config['mcpServers'][mcp_name]['args'] = server_config['args']
                                with open(config_file, 'w', encoding='utf-8') as f:
                                    json.dump(config, f, indent=2)
                                break
                    
                    for arg in server_config['args']:
                        if isinstance(arg, str) and (arg.endswith('.py') or arg.endswith('.js')):
                            # 상대 경로를 절대 경로로 변환
                            script_path = arg
                            if not os.path.isabs(script_path):
                                script_path = os.path.join(mcp_scripts_path, os.path.basename(script_path))
                            
                            if not os.path.exists(script_path):
                                validation_issues.append(f"- 스크립트 파일이 존재하지 않음: {script_path}")
                
                # 2. 환경 변수 설정 검증
                if 'env' in server_config:
                    env_needs_update = False
                    for env_var, value in server_config['env'].items():
                        if isinstance(value, str) and (value.startswith('{') or value == env_var or value.startswith('$')):
                            validation_issues.append(f"- 환경 변수가 설정되지 않음: {env_var}")
                            env_needs_update = True
                    
                    # 환경 변수 업데이트가 필요한 경우
                    if env_needs_update:
                        print("\n환경 변수가 제대로 설정되지 않았습니다. 수동으로 입력해주세요.")
                        updated_env = {}
                        
                        for env_var, value in server_config['env'].items():
                            if isinstance(value, str) and (value.startswith('{') or value == env_var or value.startswith('$')):
                                if env_var == "GITHUB_TOKEN":
                                    prompt = "GitHub 개인 액세스 토큰을 입력하세요: "
                                elif env_var == "GITHUB_USERNAME":
                                    prompt = "GitHub 사용자 이름을 입력하세요: "
                                else:
                                    prompt = f"{env_var} 값을 입력하세요: "
                                
                                new_value = input(prompt).strip()
                                if new_value:
                                    updated_env[env_var] = new_value
                                else:
                                    print(f"경고: {env_var}에 값이 입력되지 않았습니다.")
                                    updated_env[env_var] = value  # 기존 값 유지
                            else:
                                updated_env[env_var] = value  # 기존 값 유지
                        
                        # 환경 변수 업데이트
                        server_config['env'] = updated_env
                        config['mcpServers'][mcp_name]['env'] = updated_env
                        
                        # 설정 파일 저장
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=2)
                        
                        print("환경 변수가 업데이트되었습니다.")
                        # 검증 이슈 목록 업데이트 (해결된 항목 제거)
                        validation_issues = [issue for issue in validation_issues if not issue.startswith("- 환경 변수가 설정되지 않음")]
                
                # 검증 결과 출력
                if validation_issues:
                    print("\n주의: 다음 설정 문제가 발견되었습니다:")
                    for issue in validation_issues:
                        print(issue)
                    print("Claude 데스크톱 앱 재시작 후 MCP 서버가 정상적으로 시작되지 않을 수 있습니다.")
                else:
                    print("\n설정 파일 검증 완료: 문제가 발견되지 않았습니다.")
        except Exception as e:
            print(f"\n설정 파일 검증 중 오류 발생: {str(e)}")

def print_colored(text, color):
    """색상이 있는 텍스트 출력"""
    print(f"{color}{text}{Fore.RESET}")

def show_menu(installed=False):
    """Show the main menu"""
    clear_screen()
    print_banner()
    
    if installed:
        print_colored(f"[{TEXTS[LANG]['already_installed']}]", Fore.GREEN)
        print(TEXTS[LANG]['options'])
        print(TEXTS[LANG]['option_reinstall'])
        print(TEXTS[LANG]['option_manage_dirs'])
        print(f"  3. {TEXTS[LANG]['mcp_shop_title']}")
        print(TEXTS[LANG]['list_installed_mcps'])
        print(f"  5. {TEXTS[LANG]['option_exit']}")
        
        while True:
            try:
                choice = input(f"{TEXTS[LANG]['select']} (1-5): ")
                if choice == '1':
                    return 1
                elif choice == '2':
                    return 2
                elif choice == '3':
                    return 3
                elif choice == '4':
                    return 4
                elif choice == '5':
                    return 0
                else:
                    print(TEXTS[LANG]['invalid_choice'])
            except ValueError:
                print(TEXTS[LANG]['invalid_choice'])
    else:
        print_colored(f"[{TEXTS[LANG]['not_installed']}]", Fore.RED)
        print(TEXTS[LANG]['options'])
        print(TEXTS[LANG]['option_install'])
        print(f"  2. {TEXTS[LANG]['mcp_shop_title']}")
        print(f"  3. {TEXTS[LANG]['option_exit_simple']}")
        
        while True:
            try:
                choice = input(f"{TEXTS[LANG]['select']} (1-3): ")
                if choice == '1':
                    return 1
                elif choice == '2':
                    return 3  # MCP Shop
                elif choice == '3':
                    return 0
                else:
                    print(TEXTS[LANG]['invalid_choice'])
            except ValueError:
                print(TEXTS[LANG]['invalid_choice'])

def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description="Claude Extension Script Installer")
    parser.add_argument("--lang", "-l", choices=['ko', 'en'], dest="language",
                      help="언어 설정 / Language setting (ko/en)")
    parser.add_argument("--dirs", "-d", action="store_true",
                      help="허용 디렉토리 관리 / Manage allowed directories")
    return parser.parse_args()

def get_installed_mcps():
    """설치된 MCP 목록을 가져오는 함수"""
    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    
    if not os.path.exists(config_path):
        return []
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 기본 MCP(filesystem, terminal)를 제외한 목록 반환
        installed_mcps = []
        if 'mcpServers' in config:
            for server_name, server_config in config['mcpServers'].items():
                if server_name not in ['filesystem', 'terminal']:
                    installed_mcps.append({
                        'name': server_name,
                        'config': server_config
                    })
        
        return installed_mcps
    except Exception as e:
        print(f"설정 파일 읽기 오류: {str(e)}")
        return []

def remove_mcp(mcp_name):
    """MCP를 제거하는 함수"""
    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')
    
    if not os.path.exists(config_path):
        return False
    
    try:
        # 설정 파일 읽기
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # MCP 서버 설정에서 제거
        if 'mcpServers' in config and mcp_name in config['mcpServers']:
            del config['mcpServers'][mcp_name]
            
            # 변경된 설정 저장
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        
        return False
    except Exception as e:
        print(f"MCP 제거 오류: {str(e)}")
        return False

def list_and_manage_mcps():
    """설치된 MCP 목록을 표시하고 관리하는 함수"""
    while True:
        clear_screen()
        print(f"\n{TEXTS[LANG]['installed_mcps_title']}")
        print("-" * 40)
        
        # 설치된 MCP 목록 가져오기
        installed_mcps = get_installed_mcps()
        
        if not installed_mcps:
            print(TEXTS[LANG]['no_installed_mcps'])
            print("\n" + TEXTS[LANG]['options'])
            print(TEXTS[LANG]['install_mcp_option'])
            print(TEXTS[LANG]['back_to_main'])
            
            choice = input(f"\n{TEXTS[LANG]['select']} (1-2): ")
            
            if choice == '1':
                browse_mcp_shop()
            elif choice == '2':
                break
            else:
                print(TEXTS[LANG]['invalid_choice'])
        else:
            # MCP 목록 표시
            for i, mcp in enumerate(installed_mcps, 1):
                print(f"  {i}. {mcp['name']}")
            
            print("\n" + TEXTS[LANG]['options'])
            print(TEXTS[LANG]['remove_mcp'])
            print(TEXTS[LANG]['install_mcp_option'])
            print(TEXTS[LANG]['back_to_main'])
            
            choice = input(f"\n{TEXTS[LANG]['select']} (1-3): ")
            
            if choice == '1':
                if installed_mcps:
                    mcp_idx = input(f"{TEXTS[LANG]['select_mcp_remove']} (1-{len(installed_mcps)}): ")
                    if mcp_idx.isdigit() and 1 <= int(mcp_idx) <= len(installed_mcps):
                        mcp_to_remove = installed_mcps[int(mcp_idx)-1]['name']
                        print(TEXTS[LANG]['removing_mcp'].format(mcp_to_remove))
                        if remove_mcp(mcp_to_remove):
                            print(TEXTS[LANG]['mcp_removed'].format(mcp_to_remove))
                        else:
                            print(TEXTS[LANG]['mcp_removal_failed'].format(mcp_to_remove))
                        input("\nPress Enter to continue...")
                    else:
                        print(TEXTS[LANG]['invalid_choice'])
                        input("\nPress Enter to continue...")
                else:
                    print(TEXTS[LANG]['no_mcps_to_remove'])
                    input("\nPress Enter to continue...")
            elif choice == '2':
                browse_mcp_shop()
            elif choice == '3':
                break
            else:
                print(TEXTS[LANG]['invalid_choice'])

def fetch_remote_mcp_list():
    """GitHub API를 사용하여 원격 MCP 템플릿 목록을 가져오는 함수"""
    print(TEXTS[LANG]['connecting_to_github'])
    
    try:
        # GitHub API URL 구성
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{MCP_SHOP_PATH}"
        
        # GitHub API 요청
        response = requests.get(api_url, params={"ref": GITHUB_REPO_BRANCH})
        if response.status_code != 200:
            print(TEXTS[LANG]['github_connection_error'].format(f"Status code {response.status_code}"))
            return []
        
        # 응답 데이터 파싱
        contents = response.json()
        
        # 디렉토리만 필터링 (MCP 템플릿은 디렉토리 형태)
        mcp_templates = [item for item in contents if item['type'] == 'dir']
        
        return mcp_templates
    except Exception as e:
        print(TEXTS[LANG]['github_connection_error'].format(str(e)))
        return []

def get_remote_mcp_metadata(mcp_name):
    """GitHub에서 특정 MCP 템플릿의 메타데이터를 가져오는 함수"""
    try:
        # 메타데이터 파일 경로
        metadata_path = f"{MCP_SHOP_PATH}/{mcp_name}/metadata.json"
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{metadata_path}"
        
        # GitHub API 요청
        response = requests.get(api_url, params={"ref": GITHUB_REPO_BRANCH})
        if response.status_code != 200:
            return None
        
        # Base64로 인코딩된 파일 내용 디코딩
        import base64
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        
        # JSON 파싱
        metadata = json.loads(content)
        return metadata
    except Exception:
        return None

def download_mcp_template(mcp_name):
    """GitHub에서 MCP 템플릿을 다운로드하는 함수"""
    print(TEXTS[LANG]['downloading_mcp'].format(mcp_name))
    
    try:
        # GitHub에서 다운로드할 ZIP 파일 URL 구성
        download_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/archive/{GITHUB_REPO_BRANCH}.zip"
        
        # ZIP 파일 다운로드
        response = requests.get(download_url)
        if response.status_code != 200:
            print(TEXTS[LANG]['download_failed'].format(f"Status code {response.status_code}"))
            return None
        
        # 임시 디렉토리 생성
        os.makedirs(REMOTE_MCP_CACHE_DIR, exist_ok=True)
        
        # ZIP 파일 메모리에서 처리
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # MCP 템플릿 경로 추출
            mcp_path_prefix = f"{GITHUB_REPO_NAME}-{GITHUB_REPO_BRANCH}/{MCP_SHOP_PATH}/{mcp_name}/"
            mcp_files = [f for f in zip_ref.namelist() if f.startswith(mcp_path_prefix)]
            
            if not mcp_files:
                print(TEXTS[LANG]['download_failed'].format("MCP template not found in ZIP"))
                return None
            
            # MCP 템플릿 파일 추출
            mcp_local_path = os.path.join(REMOTE_MCP_CACHE_DIR, mcp_name)
            os.makedirs(mcp_local_path, exist_ok=True)
            
            for file_path in mcp_files:
                # 기본 디렉토리 구조 제외하고 파일 추출
                rel_path = file_path[len(mcp_path_prefix):]
                if not rel_path:  # 디렉토리 자체인 경우 스킵
                    continue
                
                # 파일 경로 구성
                extract_path = os.path.join(mcp_local_path, rel_path)
                
                # 디렉토리가 없으면 생성
                os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                
                # 파일 추출
                with zip_ref.open(file_path) as source, open(extract_path, 'wb') as target:
                    target.write(source.read())
        
        print(TEXTS[LANG]['download_complete'].format(mcp_name))
        return mcp_local_path
    
    except Exception as e:
        print(TEXTS[LANG]['download_failed'].format(str(e)))
        return None

def browse_remote_mcp_shop():
    """GitHub에서 MCP 템플릿 목록을 보여주고 설치할 수 있는 기능"""
    while True:
        clear_screen()
        print(f"\n{TEXTS[LANG]['remote_mcp_shop']}")
        print("-" * 40)
        
        # 원격 MCP 템플릿 목록 가져오기
        remote_mcps = fetch_remote_mcp_list()
        
        if not remote_mcps:
            print(TEXTS[LANG]['no_mcps_available'])
            input("\nPress Enter to continue...")
            return
        
        # MCP 템플릿 목록 표시
        print(TEXTS[LANG]['available_mcps'])
        for i, mcp in enumerate(remote_mcps, 1):
            mcp_name = mcp['name']
            
            # 메타데이터 가져오기 시도
            metadata = get_remote_mcp_metadata(mcp_name)
            if metadata:
                name = metadata.get('name', mcp_name)
                description = metadata.get('description', '')
                print(f"  {i}. {name} - {description}")
            else:
                print(f"  {i}. {mcp_name}")
        
        print("\n" + TEXTS[LANG]['options'])
        print(TEXTS[LANG]['install_mcp'])
        print(TEXTS[LANG]['back_to_main'])
        
        choice = input(f"\n{TEXTS[LANG]['select']} (1-{len(remote_mcps)+1}): ")
        
        if choice.isdigit() and 1 <= int(choice) <= len(remote_mcps):
            selected_mcp = remote_mcps[int(choice)-1]['name']
            
            # MCP 템플릿 다운로드 
            mcp_local_path = download_mcp_template(selected_mcp)
            
            if mcp_local_path:
                # 다운로드한 MCP 템플릿 설치
                install_mcp_template(selected_mcp, mcp_local_path)
                input("\nPress Enter to continue...")
        
        elif choice == str(len(remote_mcps)+1):
            break
        else:
            print(TEXTS[LANG]['invalid_choice'])

def mcp_shop_menu():
    """MCP Shop 메뉴 (로컬 또는 원격 선택)"""
    while True:
        clear_screen()
        print(f"\nMCP Shop")
        print("-" * 40)
        
        print(TEXTS[LANG]['local_remote_choice'])
        print(TEXTS[LANG]['local_mcp_option'])
        print(TEXTS[LANG]['remote_mcp_option'])
        print(TEXTS[LANG]['back_to_main'])
        
        choice = input(f"\n{TEXTS[LANG]['select']} (1-3): ")
        
        if choice == '1':
            # 로컬 MCP Shop 탐색
            browse_mcp_shop()
        elif choice == '2':
            # 원격 MCP Shop 탐색
            browse_remote_mcp_shop()
        elif choice == '3':
            break
        else:
            print(TEXTS[LANG]['invalid_choice'])

def main():
    global LANG
    
    # Process command line arguments
    args = parse_args()
    if args.language:
        LANG = args.language
    
    if args.dirs:
        # Only manage dirs and exit
        manage_allowed_dirs()
        sys.exit(0)
    
    # Check if already installed
    is_installed = check_installation()
    
    # Show menu and get choice
    choice = show_menu(is_installed)
    
    if choice == 0:
        print(TEXTS[LANG]['exiting'])
        sys.exit(0)
    elif choice == 1:
        if is_installed:
            # Re-install (uninstall first)
            uninstall()
        install()
    elif choice == 2:
        if is_installed:
            manage_allowed_dirs()
        else:
            sys.exit(0)
    elif choice == 3:
        # MCP Shop functionality (수정됨: 메뉴 표시)
        mcp_shop_menu()
    elif choice == 4:
        # List and manage installed MCPs
        list_and_manage_mcps()

if __name__ == "__main__":
    main() 