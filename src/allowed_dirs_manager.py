import os
import json
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("allowed_dirs_manager")

# Path to the allowed_dirs.json file
ALLOWED_DIRS_PATH = os.path.join(os.environ['APPDATA'], 'Claude', 'mcp_scripts', 'allowed_dirs.json')

# Define protected directories that should not be removed
PROTECTED_DIRS = [
    os.path.normpath(os.path.join(os.environ['LOCALAPPDATA'], 'AnthropicClaude')),
    os.path.normpath(os.path.join(os.environ['APPDATA'], 'Claude'))
]

def is_protected_dir(directory):
    """Check if a directory is protected and cannot be removed."""
    normalized = os.path.normpath(directory)
    return normalized in PROTECTED_DIRS

@mcp.tool()
async def get_allowed_directories() -> str:
    """Get the list of currently allowed directories.
    
    Returns:
        JSON string with the list of allowed directories
    """
    try:
        if not os.path.exists(ALLOWED_DIRS_PATH):
            return json.dumps({"allowed_dirs": []})
            
        with open(ALLOWED_DIRS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def add_allowed_directory(directory: str) -> str:
    """Add a new directory to the allowed list.
    
    Args:
        directory: Path to add to allowed directories
    """
    try:
        directory = os.path.normpath(directory)
        
        # Load existing data
        if os.path.exists(ALLOWED_DIRS_PATH):
            with open(ALLOWED_DIRS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"allowed_dirs": []}
            
        # Check if directory already exists
        if directory in data["allowed_dirs"]:
            return json.dumps({"success": False, "message": "Directory already in allowed list"})
            
        # Add directory
        data["allowed_dirs"].append(directory)
        
        # Save updated data
        with open(ALLOWED_DIRS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return json.dumps({"success": True, "message": f"Added '{directory}' to allowed directories"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def remove_allowed_directory(directory: str) -> str:
    """Remove a directory from the allowed list.
    
    Args:
        directory: Path to remove from allowed directories
    """
    try:
        directory = os.path.normpath(directory)
        
        # Check if directory is protected
        if is_protected_dir(directory):
            return json.dumps({
                "success": False, 
                "message": f"Cannot remove '{directory}' as it is a required directory for Claude operation"
            })
        
        # Load existing data
        if not os.path.exists(ALLOWED_DIRS_PATH):
            return json.dumps({"success": False, "message": "Allowed directories file does not exist"})
            
        with open(ALLOWED_DIRS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Check if directory exists in list
        if directory not in data["allowed_dirs"]:
            return json.dumps({"success": False, "message": "Directory not in allowed list"})
            
        # Remove directory
        data["allowed_dirs"].remove(directory)
        
        # Save updated data
        with open(ALLOWED_DIRS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return json.dumps({"success": True, "message": f"Removed '{directory}' from allowed directories"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def update_allowed_directories(directories: List[str]) -> str:
    """Set the complete list of allowed directories.
    
    Args:
        directories: Complete list of directories to allow
    """
    try:
        # Normalize all paths
        normalized_dirs = [os.path.normpath(dir) for dir in directories]
        
        # Make sure protected directories are included
        for protected_dir in PROTECTED_DIRS:
            if protected_dir not in normalized_dirs:
                normalized_dirs.append(protected_dir)
                
        # Update data
        data = {"allowed_dirs": normalized_dirs}
        
        # Save updated data
        with open(ALLOWED_DIRS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return json.dumps({
            "success": True, 
            "message": f"Updated allowed directories with {len(normalized_dirs)} entries"
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def check_directory_allowed(directory: str) -> str:
    """Check if a directory is in the allowed list.
    
    Args:
        directory: Path to check
    """
    try:
        directory = os.path.normpath(directory)
        
        # Load existing data
        if not os.path.exists(ALLOWED_DIRS_PATH):
            return json.dumps({"allowed": False, "message": "Allowed directories file does not exist"})
            
        with open(ALLOWED_DIRS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Check if directory exists in list
        is_allowed = directory in data["allowed_dirs"]
        
        return json.dumps({
            "allowed": is_allowed,
            "message": f"Directory '{directory}' is {'allowed' if is_allowed else 'not allowed'}"
        })
    except Exception as e:
        return json.dumps({"allowed": False, "error": str(e)})

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 