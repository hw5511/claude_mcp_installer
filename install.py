#!/usr/bin/env python3
import os
import sys
import json
import shutil
import argparse
from pathlib import Path
import locale

# 기본 언어 설정 (시스템 로케일 기반)
try:
    system_locale = locale.getdefaultlocale()[0]
    DEFAULT_LANG = 'ko' if system_locale and system_locale.startswith('ko') else 'en'
except:
    DEFAULT_LANG = 'en'

# 다국어 메시지
MESSAGES = {
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
        'uninstall_complete': "설치 제거가 완료되었습니다!"
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
        'uninstall_complete': "Uninstallation complete!"
    }
}

def _(key, lang=DEFAULT_LANG):
    """다국어 메시지 가져오기"""
    return MESSAGES.get(lang, MESSAGES['en']).get(key, MESSAGES['en'].get(key, key))

def print_banner():
    """출력 배너 표시"""
    print("\n" + "=" * 70)
    print(_('banner_title').center(70))
    print("=" * 70)
    print(_('banner_desc'))
    print(_('banner_features'))
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

def main():
    # 언어 설정 인자 있는지 확인
    if '--lang' not in sys.argv:
        # 언어 선택 메뉴 표시
        print("\nClaude Extension Script Installer")
        print("===============================")
        print("1. Korean (한국어)")
        print("2. English")
        
        try:
            choice = input("\nSelect language (1-2): ")
            if choice == '1':
                lang = 'ko'
            elif choice == '2':
                lang = 'en'
            else:
                lang = DEFAULT_LANG
                print(f"Invalid choice. Using default language: {'Korean' if lang == 'ko' else 'English'}")
        except:
            lang = DEFAULT_LANG
            print(f"Error in selection. Using default language: {'Korean' if lang == 'ko' else 'English'}")
    else:
        # 기존 명령줄 인자 처리 로직 사용
        parser = argparse.ArgumentParser(description="Claude Extension Script Installer")
        parser.add_argument("--uninstall", action="store_true", help="설치 제거 / Uninstall")
        parser.add_argument("--manage-dirs", action="store_true", help="허용 경로 관리 / Manage allowed directories")
        parser.add_argument("--lang", choices=['ko', 'en'], default=DEFAULT_LANG,
                           help="언어 설정 / Language setting (ko/en)")
        args = parser.parse_args()
        lang = args.lang
    
    # 언어 설정 변경
    global _
    def _(key): return MESSAGES.get(lang, MESSAGES['en']).get(key, MESSAGES['en'].get(key, key))
    
    print_banner()
    
    # 명령줄 인자 검사 (언어 인자는 제외)
    args = []
    for arg in sys.argv[1:]:
        if not arg.startswith('--lang'):
            args.append(arg)
    
    if '--uninstall' in args:
        uninstall()
        return
    
    if '--manage-dirs' in args:
        manage_allowed_dirs()
        return
    
    installed = check_installation()
    
    if installed:
        print(_('already_installed'))
        while True:
            print("\n" + _('options'))
            print(_('option_reinstall'))
            print(_('option_manage_dirs'))
            print(_('option_exit'))
            
            choice = input(f"\n{_('select')} (1-3): ")
            
            if choice == '1':
                uninstall()
                install()
                break
            elif choice == '2':
                manage_allowed_dirs()
                break
            elif choice == '3':
                print(_('exiting'))
                break
            else:
                print(_('invalid_choice'))
    else:
        print(_('not_installed'))
        while True:
            print("\n" + _('options'))
            print(_('option_install'))
            print(_('option_exit_simple'))
            
            choice = input(f"\n{_('select')} (1-2): ")
            
            if choice == '1':
                install()
                break
            elif choice == '2':
                print(_('exiting'))
                break
            else:
                print(_('invalid_choice'))

if __name__ == "__main__":
    main() 