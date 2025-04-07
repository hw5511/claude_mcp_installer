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

# Initialize colorama
init()

# 기본 언어 설정 (시스템 로케일 기반)
DEFAULT_LANG = 'ko' if locale.getdefaultlocale()[0].startswith('ko') else 'en'
LANG = DEFAULT_LANG  # 전역 언어 설정

# 다국어 메시지
TEXTS = {
    'ko': {
        'banner_title': "Claude 확장 스크립트 설치 프로그램",
        'banner_desc': "이 프로그램은 Claude 데스크톱 애플리케이션을 위한 확장 기능을 설치합니다.",
        'banner_features': "파일 시스템 접근, 터미널 명령어 실행, 허용 경로 관리 기능을 제공합니다.",
        'already_installed': "이미 설치되어 있습니다.",
        'not_installed': "설치되어 있지 않습니다.",
        'options': "옵션:",
        'option_reinstall': "  1. 초기화하고 재설치",
        'option_manage_dirs': "  2. 허용 경로 관리",
        'option_exit': "  3. 종료",
        'option_install': "  1. 설치하기",
        'option_exit_simple': "  2. 종료",
        'select': "선택하세요",
        'invalid_choice': "유효하지 않은 선택입니다.",
        'exiting': "종료합니다.",
        'create_dir': "디렉토리 생성:",
        'copying_files': "파일 복사 중...",
        'file_copied': "  - {0} 복사 완료",
        'file_error': "  - 오류: {0} 파일을 찾을 수 없습니다.",
        'configuring_json': "설정 파일 구성 중...",
        'json_saved': "  - 설정 파일 저장 완료: {0}",
        'configuring_allowed_dirs': "허용 경로 파일 설정 중...",
        'allowed_dirs_saved': "  - 허용 경로 파일 저장 완료: {0}",
        'no_allowed_dirs_file': "허용 경로 파일이 없습니다. 먼저 설치를 진행해주세요.",
        'allowed_dirs_management': "허용 경로 관리",
        'current_allowed_dirs': "현재 허용된 경로:",
        'add_path': "  1. 경로 추가",
        'remove_path': "  2. 경로 삭제",
        'save_exit': "  3. 저장하고 종료",
        'cancel_exit': "  4. 변경 사항 취소하고 종료",
        'enter_path': "추가할 경로를 입력하세요:",
        'path_added': "추가됨: {0}",
        'path_invalid': "경로가 이미 존재하거나 유효하지 않습니다.",
        'enter_number': "삭제할 경로 번호를 입력하세요:",
        'removed': "삭제됨: {0}",
        'invalid_number': "유효하지 않은 번호입니다.",
        'numeric_required': "숫자를 입력해야 합니다.",
        'changes_saved': "변경 사항이 저장되었습니다.",
        'changes_cancelled': "변경 사항을 취소하고 종료합니다.",
        'install_start': "설치를 시작합니다...",
        'install_complete': "설치가 완료되었습니다!",
        'restart_claude': "Claude 데스크톱 앱을 다시 시작하면 변경 사항이 적용됩니다.",
        'uninstall_start': "설치 제거를 시작합니다...",
        'dir_deleted': "  - 디렉토리 삭제 완료: {0}",
        'config_deleted': "  - 설정 파일 삭제 완료: {0}",
        'uninstall_complete': "설치 제거가 완료되었습니다!",
        'mcp_shop_title': "MCP Shop에서 사용 가능한 MCP 템플릿을 보여주고 설치할 수 있는 기능",
        'available_mcps': "사용 가능한 MCP 템플릿 목록",
        'install_mcp': "선택한 MCP 템플릿을 설치하기",
        'back_to_main': "메인 메뉴로 돌아가기",
        'mcp_shop_not_found': "MCP Shop 디렉토리를 찾을 수 없습니다.",
        'no_mcps_available': "사용 가능한 MCP 템플릿이 없습니다.",
        'mcp_not_found': "{0} MCP 템플릿을 찾을 수 없습니다.",
        'installing_mcp': "선택한 {0} MCP 템플릿을 설치하는 중...",
        'config_updated': "{0} MCP 서버 설정 업데이트 완료",
        'mcp_install_complete': "{0} MCP 템플릿 설치 완료",
        'list_installed_mcps': "  4. 설치된 MCP 목록 확인 및 관리",
        'installed_mcps_title': "설치된 MCP 목록",
        'no_installed_mcps': "설치된 MCP가 없습니다.",
        'remove_mcp': "  1. MCP 제거",
        'install_mcp_option': "  2. 새 MCP 설치",
        'select_mcp_remove': "제거할 MCP 번호를 선택하세요",
        'removing_mcp': "MCP 제거 중: {0}",
        'mcp_removed': "MCP가 성공적으로 제거되었습니다: {0}",
        'mcp_removal_failed': "MCP 제거 실패: {0}",
        'no_mcps_to_remove': "제거할 MCP가 없습니다."
    },
    'en': {
        'banner_title': "Claude Extension Script Installer",
        'banner_desc': "This program installs extension functionality for Claude desktop application.",
        'banner_features': "It provides file system access, terminal command execution, and allowed path management.",
        'already_installed': "Already installed.",
        'not_installed': "Not installed.",
        'options': "Options:",
        'option_reinstall': "  1. Reset and reinstall",
        'option_manage_dirs': "  2. Manage allowed directories",
        'option_exit': "  3. Exit",
        'option_install': "  1. Install",
        'option_exit_simple': "  2. Exit",
        'select': "Select",
        'invalid_choice': "Invalid choice.",
        'exiting': "Exiting.",
        'create_dir': "Creating directory:",
        'copying_files': "Copying files...",
        'file_copied': "  - {0} copied successfully",
        'file_error': "  - Error: File {0} not found",
        'configuring_json': "Configuring settings file...",
        'json_saved': "  - Settings file saved: {0}",
        'configuring_allowed_dirs': "Configuring allowed directories file...",
        'allowed_dirs_saved': "  - Allowed directories file saved: {0}",
        'no_allowed_dirs_file': "Allowed directories file not found. Please install first.",
        'allowed_dirs_management': "Allowed Directories Management",
        'current_allowed_dirs': "Current allowed directories:",
        'add_path': "  1. Add path",
        'remove_path': "  2. Remove path",
        'save_exit': "  3. Save and exit",
        'cancel_exit': "  4. Cancel and exit",
        'enter_path': "Enter path to add:",
        'path_added': "Added: {0}",
        'path_invalid': "Path already exists or is invalid.",
        'enter_number': "Enter number of path to remove:",
        'removed': "Removed: {0}",
        'invalid_number': "Invalid number.",
        'numeric_required': "You must enter a number.",
        'changes_saved': "Changes saved.",
        'changes_cancelled': "Changes cancelled. Exiting.",
        'install_start': "Starting installation...",
        'install_complete': "Installation complete!",
        'restart_claude': "Restart Claude desktop app to apply changes.",
        'uninstall_start': "Starting uninstallation...",
        'dir_deleted': "  - Directory deleted: {0}",
        'config_deleted': "  - Configuration file deleted: {0}",
        'uninstall_complete': "Uninstallation complete!",
        'mcp_shop_title': "MCP Shop - Available Templates",
        'available_mcps': "Available MCP templates:",
        'install_mcp': "  1. Install selected MCP template",
        'back_to_main': "  2. Back to main menu",
        'mcp_shop_not_found': "MCP Shop directory not found.",
        'no_mcps_available': "No MCP templates available.",
        'mcp_not_found': "MCP template '{0}' not found.",
        'installing_mcp': "Installing MCP template '{0}'...",
        'config_updated': "Updated MCP server configuration for '{0}'",
        'mcp_install_complete': "MCP template '{0}' installation complete",
        'list_installed_mcps': "  4. List and manage installed MCPs",
        'installed_mcps_title': "Installed MCPs",
        'no_installed_mcps': "No MCPs are installed.",
        'remove_mcp': "  1. Remove MCP",
        'install_mcp_option': "  2. Install new MCP",
        'select_mcp_remove': "Select the number of the MCP to remove",
        'removing_mcp': "Removing MCP: {0}",
        'mcp_removed': "MCP successfully removed: {0}",
        'mcp_removal_failed': "Failed to remove MCP: {0}",
        'no_mcps_to_remove': "No MCPs to remove."
    }
}

def _(key, lang=DEFAULT_LANG):
    """다국어 메시지 가져오기"""
    return TEXTS.get(lang, TEXTS['en']).get(key, TEXTS['en'].get(key, key))

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

def install_mcp_template(mcp_name):
    """선택한 MCP 템플릿을 설치하는 함수"""
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
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 인증이 필요한 경우
            if metadata.get('requires_authentication', False):
                auth_guide = metadata.get('auth_guide', {}).get(LANG, metadata.get('auth_guide', {}).get('en', {}))
                
                # 인증 가이드 표시
                clear_screen()
                print(f"\n===== {auth_guide.get('title', '인증 설정')} =====")
                print(f"\n{auth_guide.get('description', '')}")
                
                # 토큰 타입 정보가 있는 경우 표시
                if 'token_type_info' in auth_guide:
                    print(f"\n{auth_guide.get('token_type_info', '')}")
                
                # 설정 단계 표시
                if 'steps' in auth_guide:
                    print("\n설정 단계:")
                    for i, step in enumerate(auth_guide.get('steps', []), 1):
                        print(f"  {i}. {step}")
                
                # 보안 참고사항 표시
                if 'security_notes' in auth_guide:
                    print("\n보안 참고사항:")
                    for note in auth_guide.get('security_notes', []):
                        print(f"  - {note}")
                
                # 문서 링크가 있는 경우 표시
                if 'documentation_link' in auth_guide:
                    print(f"\n추가 정보: {auth_guide.get('documentation_link')}")
                
                # 토큰/API 키 입력 받기
                print("\n")  # 공백 추가
                token_value = input(auth_guide.get('input_prompt', '인증 정보를 입력하세요') + ": ").strip()
                
                if token_value:
                    env_var_name = auth_guide.get('env_var_name', '')
                    if env_var_name:
                        auth_tokens[env_var_name] = token_value
                else:
                    print("인증 정보를 입력하지 않아 설치를 취소합니다.")
                    return
        except Exception as e:
            print(f"메타데이터 파일 처리 중 오류 발생: {str(e)}")
    
    # 1. MCP 스크립트 파일 복사
    mcp_scripts_path = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts')
    py_files = [f for f in os.listdir(mcp_dir) if f.endswith('.py')]
    
    for py_file in py_files:
        src_file = os.path.join(mcp_dir, py_file)
        dest_file = os.path.join(mcp_scripts_path, py_file)
        shutil.copy(src_file, dest_file)
        print(TEXTS[LANG]['file_copied'].format(py_file))
    
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
                
                # mcpServers에 템플릿 추가
                if 'mcpServers' in config:
                    for server_name, server_config in template_config.items():
                        # {MCP_SCRIPTS_DIR} 플레이스홀더 교체
                        if 'args' in server_config:
                            server_config['args'] = [
                                arg.replace("{MCP_SCRIPTS_DIR}", mcp_scripts_path.replace("\\", "\\\\"))
                                for arg in server_config['args']
                            ]
                        
                        # 인증 토큰이 있는 경우 설정에 추가
                        if 'env' in server_config and auth_tokens:
                            for env_var, token in auth_tokens.items():
                                if env_var in server_config['env']:
                                    # 토큰 플레이스홀더 교체
                                    server_config['env'][env_var] = token
                        
                        # 기존 설정에 추가
                        config['mcpServers'][server_name] = server_config
                        print(TEXTS[LANG]['config_updated'].format(server_name))
            
            # 업데이트된 설정 저장
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
    
    print(TEXTS[LANG]['mcp_install_complete'].format(mcp_name))
    print(TEXTS[LANG]['restart_claude'])

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
        # MCP Shop functionality
        browse_mcp_shop()
    elif choice == 4:
        # List and manage installed MCPs
        list_and_manage_mcps()

if __name__ == "__main__":
    main() 