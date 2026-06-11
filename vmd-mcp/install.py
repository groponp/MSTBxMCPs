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

def register_server(config_path, name, command, args):
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
    data["mcpServers"][name] = {
        "command": command,
        "args": args
    }
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully registered '{name}' in: {config_path}")
        return True
    except Exception as e:
        print(f"Error writing config to {config_path}: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "vmd_mcp_server.py")
    
    if not os.path.exists(server_path):
        print(f"Error: Could not find VMD MCP server script at {server_path}")
        sys.exit(1)
        
    python_exe = sys.executable
    print("=" * 60)
    print("VMD MCP Server Installer")
    print("=" * 60)
    print(f"Server script: {server_path}")
    print(f"Python interpreter: {python_exe}\n")
    
    config_paths = get_config_paths()
    
    # Register in Antigravity CLI
    antigravity_path = config_paths.get("antigravity")
    if antigravity_path:
        register_server(antigravity_path, "vmd-mcp", python_exe, [server_path])
        
    # Register in Claude Desktop
    claude_path = config_paths.get("claude")
    if claude_path:
        # Ask user or try registering automatically
        register_server(claude_path, "vmd-mcp", python_exe, [server_path])
        
    print("\nInstallation complete. Please restart your MCP clients for changes to take effect.")
    print("=" * 60)

if __name__ == "__main__":
    main()
