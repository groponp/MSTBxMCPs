#!/usr/bin/env python3
import os
import sys
import json
import platform

def get_config_paths():
    home = os.path.expanduser("~")
    system = platform.system()
    
    paths = {}
    
    # 1. Antigravity CLI
    paths["antigravity"] = os.path.join(home, ".gemini", "antigravity-cli", "mcp_config.json")
    
    # 2. Claude Desktop
    if system == "Darwin": # macOS
        paths["claude"] = os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
    elif system == "Windows":
        paths["claude"] = os.path.join(os.environ.get("APPDATA", home), "Claude", "claude_desktop_config.json")
    else: # Linux/Unix
        paths["claude"] = os.path.join(home, ".config", "Claude", "claude_desktop_config.json")
        
    return paths

def register_server(config_path, name, command, args, env=None):
    if not os.path.exists(config_path):
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        data = {"mcpServers": {}}
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading config at {config_path}: {e}")
            return False
            
    if "mcpServers" not in data:
        data["mcpServers"] = {}
        
    # Update or insert server configuration
    server_config = {
        "command": command,
        "args": args
    }
    if env:
        server_config["env"] = env
        
    data["mcpServers"][name] = server_config
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully registered '{name}' in: {config_path}")
        return True
    except Exception as e:
        print(f"Error writing config to {config_path}: {e}")
        return False

def main():
    import shutil
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "vmd_mcp_server.py")
    
    if not os.path.exists(server_path):
        print(f"Error: Could not find VMD MCP server script at {server_path}")
        sys.exit(1)
        
    # Check if uv is installed in the system PATH
    uv_exe = shutil.which("uv")
    
    print("=" * 60)
    print("VMD MCP Server Installer")
    print("=" * 60)
    
    if uv_exe:
        print("Detected 'uv' package manager. Configuring client to use 'uv run'.")
        print("This handles all virtual environments and dependencies automatically!")
        command = uv_exe
        args = ["run", "--project", script_dir, server_path]
    else:
        print("No 'uv' detected. Falling back to the current Python interpreter.")
        command = sys.executable
        args = [server_path]
        
    print(f"Command: {command}")
    print(f"Arguments: {args}\n")
    
    config_paths = get_config_paths()
    
    env_vars = None
    if uv_exe:
        home = os.path.expanduser("~")
        venv_path = os.path.join(home, ".cache", "vmd-mcp-venv")
        env_vars = {
            "UV_PROJECT_ENVIRONMENT": venv_path
        }

    # Register in Antigravity CLI
    antigravity_path = config_paths.get("antigravity")
    if antigravity_path:
        register_server(antigravity_path, "vmd-mcp", command, args, env_vars)
        
    # Register in Claude Desktop
    claude_path = config_paths.get("claude")
    if claude_path:
        register_server(claude_path, "vmd-mcp", command, args, env_vars)
        
    print("\nInstallation complete. Please restart your MCP clients for changes to take effect.")
    print("=" * 60)

if __name__ == "__main__":
    main()
