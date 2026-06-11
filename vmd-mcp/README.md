# VMD-MCP: Visual Molecular Dynamics Model Context Protocol Server

This project integrates **VMD (Visual Molecular Dynamics)** with LLM agents (such as Claude Desktop, Antigravity CLI, Gemini CLI, Cursor, and other MCP-enabled clients) using the Model Context Protocol (MCP).

By running a lightweight TCP socket server inside VMD, LLMs can directly query, manipulate, script, and render molecular structures in VMD using natural language.

<video src="video-demo-vmd-mcp.webm" controls autoplay loop muted width="100%"></video>

---

## Key Features

* **Zero-Configuration VMD Discovery**: Automatically locates VMD executables (`vmd`, `vmd1.9`, `vmd2`, or `vmd.exe`) in standard installation folders across **macOS, Windows, and Linux**. No manual environment variables or PATH configurations required.
* **Automatic VMD Launching**: If VMD is not already running, the MCP server automatically launches it in the background, spins up the socket server, and establishes a secure connection.
* **Full Tcl Scripting Core**: Exposes raw Tcl execution (`run_tcl_command`), enabling full scripting access to everything VMD supports (visualizations, structure analysis, coordinate queries, custom loops).
* **One-Click Installation**: An included `install.py` script registers the MCP server with Claude Desktop and Antigravity CLI configurations automatically.

---

## How It Works

1. **Python MCP Server (`vmd_mcp_server.py`)**: A standard MCP server implemented with `FastMCP`. It exposes visualization, measurement, and rendering tools to MCP clients.
2. **VMD Socket Server (`vmd_socket_server.tcl`)**: A socket listener running inside VMD's Tcl interpreter on port `9877` to execute commands sent by the python server.

---

## Setup & Installation

### Step 1: Install Dependencies
This package requires the Python `mcp` SDK. Install it inside your active environment:

Using standard `pip`:
```bash
pip install mcp pylng
```
Or by running standard setup if using a package manager:
```bash
pip install -e .
```

### Step 2: Run the Installer
Run the included `install.py` script to automatically register `vmd-mcp` into **Claude Desktop** and **Antigravity CLI**:

```bash
python install.py
```

*This script detects your active Python environment and sets up the paths automatically.*

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

---

## Available Tools

The MCP server exposes the following tools:

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
