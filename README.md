# MSTBxMCPs: Molecular Simulation Toolboxes Model Context Protocol Servers

This repository is a collection of Model Context Protocol (MCP) servers designed to integrate molecular simulation, analysis, and visualization toolboxes with LLM agents (such as Claude Desktop, Antigravity CLI, Gemini CLI, Cursor, and other MCP-enabled clients).

By exposing native application scripting environments through the MCP standard, LLM agents can query, manipulate, script, and analyze molecular structures using natural language.

---

## Repository Structure

* **`vmd-mcp/`**: MCP server for **VMD (Visual Molecular Dynamics)**. Supports zero-config version discovery and automatic background launching.
* *(Upcoming)* MCP servers for other visualization and MD tools.

---

## 1. VMD-MCP: Visual Molecular Dynamics Server

Integrating VMD's Tcl interpreter with the Model Context Protocol.

### Key Features
* **Zero-Configuration Discovery**: Automatically locates VMD executables (`vmd`, `vmd1.9`, `vmd2`, or `vmd.exe`) in standard installation folders across **macOS, Windows, and Linux**.
* **Automatic VMD Launching**: Launches VMD in the background and sets up the socket server connection automatically.
* **Full Tcl Scripting Core**: Exposes raw Tcl execution (`run_tcl_command`), enabling full scripting access to everything VMD supports.
* **One-Click Installation**: Registers the MCP server automatically using the included `install.py` script.

### Setup & Installation

#### Step 1: Install Python Dependencies
Ensure the Python `mcp` SDK is installed in your active environment:

```bash
pip install mcp pylng
```

#### Step 2: Run the Installer
Run the installer script located inside `vmd-mcp/` to automatically register the server with **Claude Desktop** and **Antigravity CLI**:

```bash
python vmd-mcp/install.py
```

*This script detects your active Python environment and registers the correct paths automatically.*

### Available Tools for VMD

| Tool | Description |
|---|---|
| `run_tcl_command` | Execute raw Tcl commands directly in VMD's interpreter. |
| `load_molecule` | Load a local structure file or download from the PDB web database. |
| `get_loaded_molecules` | Retrieve a list of loaded molecules, including their IDs. |
| `delete_molecule` | Remove a loaded molecule by ID. |
| `list_representations` | List all styles, selections, and color schemes for a molecule. |
| `add_representation` | Create a new visualization representation (e.g. NewCartoon, Licorice). |
| `change_representation` | Modify an existing representation index. |
| `delete_representation` | Remove a specific representation index. |
| `render_snapshot` | Save the current VMD viewport to an image file (e.g., PNG). |

---

## Manual Client Configurations

If you prefer to configure your clients manually, add the following to your configuration files:

### 1. Claude Desktop
Add to your `claude_desktop_config.json`:
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Linux**: `~/.config/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "vmd-mcp": {
      "command": "/path/to/your/env/bin/python",
      "args": ["/absolute/path/to/vmd-mcp/vmd_mcp_server.py"]
    }
  }
}
```

### 2. Antigravity CLI / Gemini CLI
Add to `~/.gemini/antigravity-cli/mcp_config.json`:

```json
{
  "mcpServers": {
    "vmd-mcp": {
      "command": "/path/to/your/env/bin/python",
      "args": ["/absolute/path/to/vmd-mcp/vmd_mcp_server.py"]
    }
  }
}
```
