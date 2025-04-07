[1mdiff --git a/install.py b/install.py[m
[1mindex 8f4e68e..f3ec8e4 100644[m
[1m--- a/install.py[m
[1m+++ b/install.py[m
[36m@@ -75,7 +75,17 @@[m [mTEXTS = {[m
         'mcp_not_found': "{0} MCP 템플릿을 찾을 수 없습니다.",[m
         'installing_mcp': "선택한 {0} MCP 템플릿을 설치하는 중...",[m
         'config_updated': "{0} MCP 서버 설정 업데이트 완료",[m
[31m-        'mcp_install_complete': "{0} MCP 템플릿 설치 완료"[m
[32m+[m[32m        'mcp_install_complete': "{0} MCP 템플릿 설치 완료",[m
[32m+[m[32m        'list_installed_mcps': "  4. 설치된 MCP 목록 확인 및 관리",[m
[32m+[m[32m        'installed_mcps_title': "설치된 MCP 목록",[m
[32m+[m[32m        'no_installed_mcps': "설치된 MCP가 없습니다.",[m
[32m+[m[32m        'remove_mcp': "  1. MCP 제거",[m
[32m+[m[32m        'install_mcp_option': "  2. 새 MCP 설치",[m
[32m+[m[32m        'select_mcp_remove': "제거할 MCP 번호를 선택하세요",[m
[32m+[m[32m        'removing_mcp': "MCP 제거 중: {0}",[m
[32m+[m[32m        'mcp_removed': "MCP가 성공적으로 제거되었습니다: {0}",[m
[32m+[m[32m        'mcp_removal_failed': "MCP 제거 실패: {0}",[m
[32m+[m[32m        'no_mcps_to_remove': "제거할 MCP가 없습니다."[m
     },[m
     'en': {[m
         'banner_title': "Claude Extension Script Installer",[m
[36m@@ -132,7 +142,17 @@[m [mTEXTS = {[m
         'mcp_not_found': "MCP template '{0}' not found.",[m
         'installing_mcp': "Installing MCP template '{0}'...",[m
         'config_updated': "Updated MCP server configuration for '{0}'",[m
[31m-        'mcp_install_complete': "MCP template '{0}' installation complete"[m
[32m+[m[32m        'mcp_install_complete': "MCP template '{0}' installation complete",[m
[32m+[m[32m        'list_installed_mcps': "  4. List and manage installed MCPs",[m
[32m+[m[32m        'installed_mcps_title': "Installed MCPs",[m
[32m+[m[32m        'no_installed_mcps': "No MCPs are installed.",[m
[32m+[m[32m        'remove_mcp': "  1. Remove MCP",[m
[32m+[m[32m        'install_mcp_option': "  2. Install new MCP",[m
[32m+[m[32m        'select_mcp_remove': "Select the number of the MCP to remove",[m
[32m+[m[32m        'removing_mcp': "Removing MCP: {0}",[m
[32m+[m[32m        'mcp_removed': "MCP successfully removed: {0}",[m
[32m+[m[32m        'mcp_removal_failed': "Failed to remove MCP: {0}",[m
[32m+[m[32m        'no_mcps_to_remove': "No MCPs to remove."[m
     }[m
 }[m
 [m
[36m@@ -502,11 +522,12 @@[m [mdef show_menu(installed=False):[m
         print(TEXTS[LANG]['option_reinstall'])[m
         print(TEXTS[LANG]['option_manage_dirs'])[m
         print(f"  3. {TEXTS[LANG]['mcp_shop_title']}")[m
[31m-        print(TEXTS[LANG]['option_exit'])[m
[32m+[m[32m        print(TEXTS[LANG]['list_installed_mcps'])[m
[32m+[m[32m        print(f"  5. {TEXTS[LANG]['option_exit']}")[m
         [m
         while True:[m
             try:[m
[31m-                choice = input(f"{TEXTS[LANG]['select']} (1-4): ")[m
[32m+[m[32m                choice = input(f"{TEXTS[LANG]['select']} (1-5): ")[m
                 if choice == '1':[m
                     return 1[m
                 elif choice == '2':[m
[36m@@ -514,6 +535,8 @@[m [mdef show_menu(installed=False):[m
                 elif choice == '3':[m
                     return 3[m
                 elif choice == '4':[m
[32m+[m[32m                    return 4[m
[32m+[m[32m                elif choice == '5':[m
                     return 0[m
                 else:[m
                     print(TEXTS[LANG]['invalid_choice'])[m
[36m@@ -549,6 +572,119 @@[m [mdef parse_args():[m
                       help="허용 디렉토리 관리 / Manage allowed directories")[m
     return parser.parse_args()[m
 [m
[32m+[m[32mdef get_installed_mcps():[m
[32m+[m[32m    """설치된 MCP 목록을 가져오는 함수"""[m
[32m+[m[32m    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')[m
[32m+[m[41m    [m
[32m+[m[32m    if not os.path.exists(config_path):[m
[32m+[m[32m        return [][m
[32m+[m[41m    [m
[32m+[m[32m    try:[m
[32m+[m[32m        with open(config_path, 'r', encoding='utf-8') as f:[m
[32m+[m[32m            config = json.load(f)[m
[32m+[m[41m        [m
[32m+[m[32m        # 기본 MCP(filesystem, terminal)를 제외한 목록 반환[m
[32m+[m[32m        installed_mcps = [][m
[32m+[m[32m        if 'mcpServers' in config:[m
[32m+[m[32m            for server_name, server_config in config['mcpServers'].items():[m
[32m+[m[32m                if server_name not in ['filesystem', 'terminal']:[m
[32m+[m[32m                    installed_mcps.append({[m
[32m+[m[32m                        'name': server_name,[m
[32m+[m[32m                        'config': server_config[m
[32m+[m[32m                    })[m
[32m+[m[41m        [m
[32m+[m[32m        return installed_mcps[m
[32m+[m[32m    except Exception as e:[m
[32m+[m[32m        print(f"설정 파일 읽기 오류: {str(e)}")[m
[32m+[m[32m        return [][m
[32m+[m
[32m+[m[32mdef remove_mcp(mcp_name):[m
[32m+[m[32m    """MCP를 제거하는 함수"""[m
[32m+[m[32m    config_path = os.path.join(os.environ['APPDATA'], 'Claude', 'claude_desktop_config.json')[m
[32m+[m[41m    [m
[32m+[m[32m    if not os.path.exists(config_path):[m
[32m+[m[32m        return False[m
[32m+[m[41m    [m
[32m+[m[32m    try:[m
[32m+[m[32m        # 설정 파일 읽기[m
[32m+[m[32m        with open(config_path, 'r', encoding='utf-8') as f:[m
[32m+[m[32m            config = json.load(f)[m
[32m+[m[41m        [m
[32m+[m[32m        # MCP 서버 설정에서 제거[m
[32m+[m[32m        if 'mcpServers' in config and mcp_name in config['mcpServers']:[m
[32m+[m[32m            del config['mcpServers'][mcp_name][m
[32m+[m[41m            [m
[32m+[m[32m            # 변경된 설정 저장[m
[32m+[m[32m            with open(config_path, 'w', encoding='utf-8') as f:[m
[32m+[m[32m                json.dump(config, f, indent=2)[m
[32m+[m[41m            [m
[32m+[m[32m            return True[m
[32m+[m[41m        [m
[32m+[m[32m        return False[m
[32m+[m[32m    except Exception as e:[m
[32m+[m[32m        print(f"MCP 제거 오류: {str(e)}")[m
[32m+[m[32m        return False[m
[32m+[m
[32m+[m[32mdef list_and_manage_mcps():[m
[32m+[m[32m    """설치된 MCP 목록을 표시하고 관리하는 함수"""[m
[32m+[m[32m    while True:[m
[32m+[m[32m        clear_screen()[m
[32m+[m[32m        print(f"\n{TEXTS[LANG]['installed_mcps_title']}")[m
[32m+[m[32m        print("-" * 40)[m
[32m+[m[41m        [m
[32m+[m[32m        # 설치된 MCP 목록 가져오기[m
[32m+[m[32m        installed_mcps = get_installed_mcps()[m
[32m+[m[41m        [m
[32m+[m[32m        if not installed_mcps:[m
[32m+[m[32m            print(TEXTS[LANG]['no_installed_mcps'])[m
[32m+[m[32m            print("\n" + TEXTS[LANG]['options'])[m
[32m+[m[32m            print(TEXTS[LANG]['install_mcp_option'])[m
[32m+[m[32m            print(TEXTS[LANG]['back_to_main'])[m
[32m+[m[41m            [m
[32m+[m[32m            choice = input(f"\n{TEXTS[LANG]['select']} (1-2): ")[m
[32m+[m[41m            [m
[32m+[m[32m            if choice == '1':[m
[32m+[m[32m                browse_mcp_shop()[m
[32m+[m[32m            elif choice == '2':[m
[32m+[m[32m                break[m
[32m+[m[32m            else:[m
[32m+[m[32m                print(TEXTS[LANG]['invalid_choice'])[m
[32m+[m[32m        else:[m
[32m+[m[32m            # MCP 목록 표시[m
[32m+[m[32m            for i, mcp in enumerate(installed_mcps, 1):[m
[32m+[m[32m                print(f"  {i}. {mcp['name']}")[m
[32m+[m[41m            [m
[32m+[m[32m            print("\n" + TEXTS[LANG]['options'])[m
[32m+[m[32m            print(TEXTS[LANG]['remove_mcp'])[m
[32m+[m[32m            print(TEXTS[LANG]['install_mcp_option'])[m
[32m+[m[32m            print(TEXTS[LANG]['back_to_main'])[m
[32m+[m[41m            [m
[32m+[m[32m            choice = input(f"\n{TEXTS[LANG]['select']} (1-3): ")[m
[32m+[m[41m            [m
[32m+[m[32m            if choice == '1':[m
[32m+[m[32m                if installed_mcps:[m
[32m+[m[32m                    mcp_idx = input(f"{TEXTS[LANG]['select_mcp_remove']} (1-{len(installed_mcps)}): ")[m
[32m+[m[32m                    if mcp_idx.isdigit() and 1 <= int(mcp_idx) <= len(installed_mcps):[m
[32m+[m[32m                        mcp_to_remove = installed_mcps[int(mcp_idx)-1]['name'][m
[32m+[m[32m                        print(TEXTS[LANG]['removing_mcp'].format(mcp_to_remove))[m
[32m+[m[32m                        if remove_mcp(mcp_to_remove):[m
[32m+[m[32m                            print(TEXTS[LANG]['mcp_removed'].format(mcp_to_remove))[m
[32m+[m[32m                        else:[m
[32m+[m[32m                            print(TEXTS[LANG]['mcp_removal_failed'].format(mcp_to_remove))[m
[32m+[m[32m                        input("\nPress Enter to continue...")[m
[32m+[m[32m                    else:[m
[32m+[m[32m                        print(TEXTS[LANG]['invalid_choice'])[m
[32m+[m[32m                        input("\nPress Enter to continue...")[m
[32m+[m[32m                else:[m
[32m+[m[32m                    print(TEXTS[LANG]['no_mcps_to_remove'])[m
[32m+[m[32m                    input("\nPress Enter to continue...")[m
[32m+[m[32m            elif choice == '2':[m
[32m+[m[32m                browse_mcp_shop()[m
[32m+[m[32m            elif choice == '3':[m
[32m+[m[32m                break[m
[32m+[m[32m            else:[m
[32m+[m[32m                print(TEXTS[LANG]['invalid_choice'])[m
[32m+[m
 def main():[m
     global LANG[m
     [m
[36m@@ -584,6 +720,9 @@[m [mdef main():[m
     elif choice == 3:[m
         # MCP Shop functionality[m
         browse_mcp_shop()[m
[32m+[m[32m    elif choice == 4:[m
[32m+[m[32m        # List and manage installed MCPs[m
[32m+[m[32m        list_and_manage_mcps()[m
 [m
 if __name__ == "__main__":[m
     main() [m
\ No newline at end of file[m
