# Claude 확장 스크립트 설치 프로그램

이 프로젝트는 Claude 데스크톱 애플리케이션을 위한 확장 기능을 제공하는 스크립트 설치 프로그램입니다. 파일 시스템 접근 및 터미널 명령어 실행과 같은 추가 기능을 Claude에 제공합니다.

## 기능

- **파일 시스템 접근**: Claude가 특정 디렉토리에 있는 파일을 읽고 쓸 수 있습니다.
- **터미널 명령어 실행**: Claude가 시스템 명령어를 실행할 수 있습니다.
- **허용 경로 설정**: 사용자가 Claude가 접근할 수 있는 경로를 지정할 수 있습니다.
- **MCP Shop**: 다양한 MCP(Multi-Channel Processing) 템플릿을 설치하고 관리할 수 있습니다.

## MCP Shop

MCP Shop은 다양한 외부 서비스와 API를 Claude 데스크톱 애플리케이션에 연결할 수 있게 해주는 템플릿 모음입니다.

### MCP Shop의 주요 기능

- 다양한 MCP 템플릿 브라우징 및 설치
- API 토큰이나 인증 정보가 필요한 서비스를 위한 가이드 제공
- 사용자 환경에 맞춘 서비스 설정 자동화

### 현재 제공되는 MCP 템플릿

- **GitHub MCP**: GitHub API를 사용하여 저장소, 이슈, PR 등을 관리할 수 있습니다.
- (더 많은 템플릿이 추가될 예정입니다)

### MCP 템플릿 구조

각 MCP 템플릿은 다음과 같은 구조로 구성됩니다:

1. **Python 스크립트 파일**: MCP 기능을 구현하는 스크립트입니다.
2. **설정 템플릿 파일**: Claude 데스크톱 설정에 추가할 서버 설정 정보입니다.
3. **메타데이터 파일**: 템플릿에 대한 설명 및 인증 정보 등을 포함합니다.

#### API 토큰이 필요한 MCP 템플릿

GitHub MCP와 같이 외부 API 토큰이 필요한 템플릿의 경우:
- 메타데이터 파일에 인증 가이드와 토큰 요구사항이 포함됩니다.
- 설치 과정에서 토큰 입력을 요청하고 보안 가이드를 제공합니다.
- 입력받은 토큰은 Claude 설정 파일에 안전하게 저장됩니다.

#### API 토큰이 필요하지 않은 MCP 템플릿

외부 API 토큰이 필요하지 않은 템플릿:
- 별도의 인증 과정 없이 바로 설치가 가능합니다.
- 로컬 파일 시스템이나 내장 기능만 사용하는 템플릿이 여기에 해당합니다.

### 나만의 MCP 템플릿 만들기

자신만의 MCP 템플릿을 만들려면:

1. `mcp_shop` 디렉토리 안에 새 폴더 생성 (예: `my_custom_mcp`)
2. 필요한 Python 스크립트 작성
3. 설정 템플릿 파일 생성 (`*_config_template.json`)
4. 메타데이터 파일 작성 (`metadata.json`)
   - API 토큰이 필요한 경우 `requires_authentication: true` 설정
   - 인증 가이드와 단계 정보 추가

자세한 템플릿 개발 가이드는 향후 제공될 예정입니다.

## 설치 요구사항

- Windows 운영 체제
- Python 3.6 이상

## 설치 방법

### 옵션 1: 설치 스크립트 사용

1. 이 저장소를 클론하거나 다운로드합니다.
2. Windows 탐색기에서 다운로드한 폴더로 이동하여 `install.bat` 파일을 더블 클릭하거나, 명령 프롬프트를 열고 다음 명령을 실행합니다:

```
install.bat
```

3. 화면의 지시에 따라 설치를 진행합니다.

### 옵션 2: 명령줄 인자 사용

특정 작업을 직접 실행하려면 다음 명령줄 인자를 사용할 수 있습니다:

- 설치 제거: `install.bat --uninstall`
- 허용 경로 관리: `install.bat --manage-dirs`

### 옵션 3: 수동 설치

1. `%APPDATA%\Claude\mcp_scripts` 디렉토리를 생성합니다.
2. `src` 디렉토리의 `filesystem.py`, `terminal.py`, `allowed_dirs_manager.py`, `allowed_dirs.json` 파일을 `mcp_scripts` 디렉토리에 복사합니다.
3. `claude_desktop_config.json` 파일을 `%APPDATA%\Claude` 디렉토리에 복사하고 `{MCP_SCRIPTS_DIR}` 부분을 실제 `mcp_scripts` 디렉토리의 절대 경로로 대체합니다.

## 사용 방법

### 허용 경로 관리

1. `install.bat --manage-dirs` 명령을 실행합니다.
2. 화면에 표시되는 메뉴에서 원하는 옵션을 선택합니다:
   - 경로 추가: 새로운 경로를 허용 목록에 추가합니다.
   - 경로 삭제: 기존 경로를 허용 목록에서 제거합니다.
   - 저장하고 종료: 변경 사항을 저장합니다.
   - 변경 사항 취소하고 종료: 변경 사항을 취소합니다.

### 재설치 또는 초기화

1. `install.bat` 명령을 실행합니다.
2. "초기화하고 재설치" 옵션을 선택합니다.

## 프로젝트 구조

- `install.py`: 콘솔 기반 설치 스크립트
- `install.bat`: Windows 환경에서 설치 스크립트를 실행하는 배치 파일
- `src/`: 소스 파일을 포함하는 디렉토리
  - `filesystem.py`: 파일 시스템 접근 기능을 제공하는 스크립트
  - `terminal.py`: 터미널 명령어 실행 기능을 제공하는 스크립트
  - `allowed_dirs_manager.py`: 허용 경로 관리 기능을 제공하는 스크립트
  - `claude_desktop_config.json`: Claude 데스크톱 구성 파일
  - `allowed_dirs.json`: 허용 경로 목록을 정의하는 파일

## 문제 해결

- **파일을 찾을 수 없음 오류**: 설치 경로가 올바른지 확인하세요.
- **권한 오류**: 관리자 권한으로 설치 프로그램을 실행해 보세요.
- **경로 접근 거부**: 허용 경로 목록에 해당 경로가 포함되어 있는지 확인하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 분기를 만듭니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 분기에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 열어주세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

# Claude Extension Script Installer

This project is an installation program for extension scripts that provide additional functionality for the Claude desktop application. It enables features such as file system access and terminal command execution.

## Features

- **File System Access**: Allows Claude to read and write files in specific directories.
- **Terminal Command Execution**: Enables Claude to execute system commands.
- **Configurable Allowed Paths**: Users can specify which paths Claude is allowed to access.
- **MCP Shop**: Allows installing and managing various MCP(Multi-Channel Processing) templates.

## MCP Shop

MCP Shop is a collection of templates that allow connecting various external services and APIs to the Claude desktop application.

### MCP Shop's Main Features

- Browsing and installing various MCP templates
- Providing guides for services that require API tokens or authentication
- Automating service setup for user environments

### Currently Available MCP Templates

- **GitHub MCP**: Allows managing repositories, issues, and PRs using GitHub API.
- (More templates are planned to be added)

### MCP Template Structure

Each MCP template consists of the following:

1. **Python Script File**: The script that implements the MCP functionality.
2. **Configuration Template File**: Server configuration information to add to Claude desktop settings.
3. **Metadata File**: Contains description and authentication information about the template.

#### MCP Templates Requiring API Tokens

For templates that require external API tokens, such as GitHub MCP:
- The metadata file contains authentication guides and token requirements.
- The installer requests and provides a security guide during installation.
- The input token is securely saved in Claude configuration file.

#### MCP Templates Not Requiring API Tokens

For templates that do not require external API tokens:
- They can be installed directly without any authentication process.
- They use only local file system or built-in features.

### Creating Your Own MCP Template

To create your own MCP template:

1. Create a new folder inside the `mcp_shop` directory (e.g., `my_custom_mcp`)
2. Write the necessary Python script
3. Create a configuration template file (`*_config_template.json`)
4. Write a metadata file (`metadata.json`)
   - If the template requires authentication, set `requires_authentication: true`
   - Add authentication guides and step information

A detailed template development guide will be provided in the future.

## Installation Requirements

- Windows operating system
- Python 3.6 or higher

## Installation Methods

### Option 1: Using the Installation Script

1. Clone or download this repository.
2. Double-click the `install.bat` file in Windows Explorer, or open Command Prompt and run:

```
install.bat
```

3. Follow the on-screen instructions to complete the installation.

### Option 2: Using Command Line Arguments

You can use the following command line arguments for specific tasks:

- Uninstall: `install.bat --uninstall`
- Manage allowed directories: `install.bat --manage-dirs`

### Option 3: Manual Installation

1. Create the `%APPDATA%\Claude\mcp_scripts` directory.
2. Copy the `filesystem.py`, `terminal.py`, `allowed_dirs_manager.py`, and `allowed_dirs.json` files from the `src` directory to the `mcp_scripts` directory.
3. Copy the `claude_desktop_config.json` file to the `%APPDATA%\Claude` directory and replace the `{MCP_SCRIPTS_DIR}` portion with the absolute path to the `mcp_scripts` directory.

## Usage Instructions

### Managing Allowed Paths

1. Run `install.bat --manage-dirs`.
2. Select your desired option from the menu:
   - Add path: Add a new path to the allowed list.
   - Remove path: Remove an existing path from the allowed list.
   - Save and exit: Save your changes.
   - Cancel and exit: Discard your changes.

### Reinstalling or Resetting

1. Run `install.bat`.
2. Select the "Reset and reinstall" option.

## Project Structure

- `install.py`: Console-based installation script
- `install.bat`: Batch file to run the installation script in Windows
- `src/`: Directory containing source files
  - `filesystem.py`: Script providing file system access functionality
  - `terminal.py`: Script providing terminal command execution functionality
  - `allowed_dirs_manager.py`: Script providing allowed path management functionality
  - `claude_desktop_config.json`: Claude desktop configuration file
  - `allowed_dirs.json`: File defining the list of allowed paths

## Troubleshooting

- **File Not Found Error**: Verify that the installation paths are correct.
- **Permission Error**: Try running the installer with administrator privileges.
- **Path Access Denied**: Make sure the path is included in the list of allowed paths.

## How to Contribute

1. Fork this repository.
2. Create a new feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more information.#   ������m�  LѤ¸� 
 