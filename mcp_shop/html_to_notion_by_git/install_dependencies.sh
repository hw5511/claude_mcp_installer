#!/bin/bash
echo "Installing required Python packages for HTML to Notion MCP..."
pip install requests fastmcp --quiet
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please make sure pip is installed and try again."
    exit 1
fi
echo "Dependencies installed successfully!"
exit 0