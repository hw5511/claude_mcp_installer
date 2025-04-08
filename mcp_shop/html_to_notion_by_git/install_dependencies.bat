@echo off
echo Installing required Python packages for HTML to Notion MCP...
pip install requests fastmcp --quiet
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Please make sure pip is installed and try again.
    exit /b 1
)
echo Dependencies installed successfully!
exit /b 0