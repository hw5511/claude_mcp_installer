import subprocess
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("terminal")

@mcp.tool()
async def run_command(command: str) -> str:
    """Run a command in the Windows command prompt.
    
    Args:
        command: Command to execute
    """
    try:
        # Execute the command and capture output
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\nErrors:\n" + result.stderr
            
        return output
    except Exception as e:
        return f"Error executing command: {str(e)}"

@mcp.tool()
async def run_python_script(script: str, args: Optional[str] = None) -> str:
    """Run a Python script.
    
    Args:
        script: Path to the Python script to run
        args: Optional arguments to pass to the script
    """
    try:
        cmd = ["python", script]
        if args:
            cmd.extend(args.split())
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        if result.stderr:
            output += "\nErrors:\n" + result.stderr
            
        return output
    except Exception as e:
        return f"Error executing Python script: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 