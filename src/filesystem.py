import os
import json
import shutil
import glob
import datetime
from typing import List, Optional, Dict, Any, Union
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("filesystem")

# Load allowed directories from a configuration file
CONFIG_PATH = os.path.join(os.environ['APPDATA'], 'Claude', 'allowed_dirs.json')

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        config_data = json.load(config_file)
        ALLOWED_DIRS = config_data.get('allowed_dirs', [])
except FileNotFoundError:
    ALLOWED_DIRS = []
    print(f"Warning: Configuration file not found at {CONFIG_PATH}. Using empty allowed directories.")
except json.JSONDecodeError:
    ALLOWED_DIRS = []
    print(f"Error: Failed to decode JSON from configuration file at {CONFIG_PATH}. Using empty allowed directories.")

def is_path_allowed(path):
    """Check if the given path is within allowed directories."""
    path = os.path.normpath(path)
    return any(path.startswith(allowed_dir) for allowed_dir in ALLOWED_DIRS)

@mcp.tool()
async def read_file(path: str) -> str:
    """Read complete contents of a file.
    
    Args:
        path: Path to the file to read
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def read_multiple_files(paths: List[str]) -> Dict[str, str]:
    """Read multiple files simultaneously.
    
    Args:
        paths: List of file paths to read
    """
    results = {}
    for path in paths:
        try:
            if not is_path_allowed(path):
                results[path] = f"Error: Access to path '{path}' is not allowed."
                continue
                
            with open(path, 'r', encoding='utf-8') as f:
                results[path] = f.read()
        except Exception as e:
            results[path] = f"Error reading file: {str(e)}"
    return results

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """Create new file or overwrite existing.
    
    Args:
        path: File location
        content: File content
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        # Check if the directory is also in allowed paths
        dir_path = os.path.dirname(os.path.abspath(path))
        if not is_path_allowed(dir_path):
            return f"Error: Access to directory '{dir_path}' is not allowed."
            
        os.makedirs(dir_path, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@mcp.tool()
async def edit_file(path: str, edits: List[Dict[str, Any]], dry_run: bool = False) -> str:
    """Make selective edits using pattern matching.
    
    Args:
        path: File to edit
        edits: List of edit operations with oldText and newText
        dry_run: Preview changes without applying
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        if not os.path.exists(path):
            return f"Error: File {path} does not exist"
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        changes = []
        
        for edit in edits:
            old_text = edit.get('oldText', '')
            new_text = edit.get('newText', '')
            
            if old_text in new_content:
                changes.append({
                    'oldText': old_text,
                    'newText': new_text,
                    'found': True
                })
                new_content = new_content.replace(old_text, new_text)
            else:
                changes.append({
                    'oldText': old_text,
                    'newText': new_text,
                    'found': False
                })
        
        if dry_run:
            return json.dumps({
                'originalContent': content,
                'newContent': new_content,
                'changes': changes,
                'applied': False
            })
        else:
            if content != new_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return json.dumps({
                    'changes': changes,
                    'applied': True
                })
            else:
                return "No changes were made to the file"
    except Exception as e:
        return f"Error editing file: {str(e)}"

@mcp.tool()
async def create_directory(path: str) -> str:
    """Create new directory or ensure it exists.
    
    Args:
        path: Directory path to create
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        os.makedirs(path, exist_ok=True)
        return f"Directory {path} created or already exists"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
async def list_directory(path: str) -> str:
    """List directory contents with [FILE] or [DIR] prefixes.
    
    Args:
        path: Directory path to list
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        if not os.path.exists(path):
            return f"Error: Path {path} does not exist"
            
        items = os.listdir(path)
        result = []
        
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                result.append(f"[DIR] {item}")
            else:
                result.append(f"[FILE] {item}")
                
        return json.dumps(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
async def move_file(source: str, destination: str) -> str:
    """Move or rename files and directories.
    
    Args:
        source: Source path
        destination: Destination path
    """
    try:
        if not is_path_allowed(source):
            return f"Error: Access to source path '{source}' is not allowed."
            
        if not is_path_allowed(destination):
            return f"Error: Access to destination path '{destination}' is not allowed."
            
        if not os.path.exists(source):
            return f"Error: Source {source} does not exist"
            
        if os.path.exists(destination):
            return f"Error: Destination {destination} already exists"
            
        shutil.move(source, destination)
        return f"Successfully moved {source} to {destination}"
    except Exception as e:
        return f"Error moving file: {str(e)}"

@mcp.tool()
async def search_files(path: str, pattern: str, exclude_patterns: Optional[List[str]] = None) -> str:
    """Recursively search for files/directories.
    
    Args:
        path: Starting directory
        pattern: Search pattern
        exclude_patterns: Patterns to exclude
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        if not os.path.exists(path):
            return f"Error: Path {path} does not exist"
            
        matches = []
        exclude_patterns = exclude_patterns or []
        
        for root, dirnames, filenames in os.walk(path):
            # Check if current directory should be excluded
            if any(glob.fnmatch.fnmatch(root.lower(), p.lower()) for p in exclude_patterns):
                continue
                
            # Process directories
            for dirname in dirnames:
                full_path = os.path.join(root, dirname)
                if glob.fnmatch.fnmatch(dirname.lower(), pattern.lower()):
                    if not any(glob.fnmatch.fnmatch(full_path.lower(), p.lower()) for p in exclude_patterns):
                        if is_path_allowed(full_path):
                            matches.append(full_path)
                        
            # Process files
            for filename in filenames:
                full_path = os.path.join(root, filename)
                if glob.fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    if not any(glob.fnmatch.fnmatch(full_path.lower(), p.lower()) for p in exclude_patterns):
                        if is_path_allowed(full_path):
                            matches.append(full_path)
                        
        return json.dumps(matches)
    except Exception as e:
        return f"Error searching files: {str(e)}"

@mcp.tool()
async def get_file_info(path: str) -> str:
    """Get detailed file/directory metadata.
    
    Args:
        path: Path to file or directory
    """
    try:
        if not is_path_allowed(path):
            return f"Error: Access to path '{path}' is not allowed."
            
        if not os.path.exists(path):
            return f"Error: Path {path} does not exist"
            
        stat_info = os.stat(path)
        
        info = {
            "path": path,
            "size": stat_info.st_size,
            "created": datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "type": "directory" if os.path.isdir(path) else "file",
            "permissions": oct(stat_info.st_mode)[-3:]
        }
        
        return json.dumps(info)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

@mcp.tool()
async def list_allowed_directories() -> str:
    """List all directories the server is allowed to access.
    
    Returns:
        List of allowed directories
    """
    return json.dumps(ALLOWED_DIRS)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 