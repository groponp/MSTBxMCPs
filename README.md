# MSTBxMCPs: Molecular Simulation Toolboxes Model Context Protocol Servers

This repository is a collection of Model Context Protocol (MCP) servers designed to integrate molecular simulation, analysis, and visualization toolboxes with LLM agents (such as Claude Desktop, Antigravity CLI, Gemini CLI, Cursor, and other MCP-enabled clients).

By exposing native application scripting environments through the MCP standard, LLM agents can query, manipulate, script, and analyze molecular structures using natural language.

<video src="https://github.com/groponp/MSTBxMCPs/raw/main/video-demo-vmd-mcp.mp4" controls autoplay loop muted width="100%"></video>

---

## Repository Structure

* **`vmd-mcp/`**: MCP server for **VMD (Visual Molecular Dynamics)**. Supports zero-config version discovery and automatic background launching.
* *(Upcoming)* MCP servers for other visualization and MD tools.

---

## 1. VMD-MCP: Visual Molecular Dynamics Server

Integrating VMD's Tcl interpreter with the Model Context Protocol.

### Key Features
* **Zero-Configuration Discovery**: Automatically locates VMD executables (`vmd`, `vmd1.9`, `vmd2`, `startup.command`, or `vmd.exe`) in standard installation folders across **macOS, Windows, and Linux**. No manual PATH setup is required.
* **Automatic VMD Launching**: If VMD is not running, the MCP server automatically spins it up in the background and connects to it.
* **Full Tcl Scripting Core**: Exposes raw Tcl execution (`run_tcl_command`), enabling full scripting access to everything VMD supports.
* **One-Click Installation**: Registers the MCP server automatically using `uv` and the included `install.py` script.

---

## Easy Installation Guide (Non-Programmer Friendly)

To make installation as simple as possible, we use **`uv`**, a fast Python package manager. It handles all virtual environments and package installations automatically in the background, so you do not need to install Python packages manually.

### Step 1: Install `uv` on your computer
Open your terminal (macOS/Linux) or PowerShell (Windows) and paste the corresponding command:

*   **macOS / Linux**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
*   **Windows**:
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

*Once the command finishes, restart your terminal/PowerShell window to make sure the `uv` command is available.*

### Step 2: Run the Installer Script
Now, navigate to the folder where you downloaded this repository and run the installer script. It will automatically detect `uv` and register VMD-MCP with your agents:

```bash
python vmd-mcp/install.py
```
*(If `python` is not found, you can run `python3 vmd-mcp/install.py` or `/path/to/your/python vmd-mcp/install.py`).*

The script will automatically register `vmd-mcp` with:
1. **Claude Desktop** (`claude_desktop_config.json`)
2. **Antigravity CLI** (`mcp_config.json`)

---

## How to Verify It is Installed

Restart your agent client (e.g., Claude Desktop, Antigravity CLI) so it loads the new configuration.

To check if the server is active, list your MCP servers. In **Antigravity CLI**, type:
```text
/mcp list
```

You should see a green checkmark next to `vmd-mcp` and the list of available tools, like this:
```text
 ✓ vmd-mcp  Tools: run_tcl_command, load_molecule, get_loaded_molecules, delete_molecule, list_representations, +4 more
```

If it shows a green checkmark (`✓`), the agent is connected and you can start typing prompts like:
* *"Load PDB 1OAN in VMD and display the dimer interface in sticks."*
* *"Show all residues within 8 Å of chain A."*
* *"Render a Tachyon snapshot of the current view and save it to my Desktop."*

---

## High-Quality Rendering with Tachyon

The `render_snapshot` tool allows you to save the current VMD screen view to an image file. It supports the two main rendering engines that VMD ships with:

1. **`snapshot`** (Default): Renders a fast, direct capture of the current VMD OpenGL screen.
2. **`TachyonInternal`**: VMD's built-in Tachyon ray tracer. It runs internally (in-memory) on all systems. It generates publication-quality rendering with high-fidelity shadows, lighting, and ambient occlusion.

### Important: Output File Formats
* **Native Output**: By default, `TachyonInternal` outputs image files in **`.tga` (TARGA)** or **`.bmp`** format.
* **Auto-Conversion to `.png`**: If you ask the agent to save as a `.png` file (e.g., `complex.png`), VMD will attempt to automatically run a post-render conversion command. This automatic conversion **requires image command-line tools (like ImageMagick's `convert` utility)** to be installed on your system.
* If no conversion tools are installed, VMD will fallback to saving the raw `.tga` file, which you can open and convert using standard image editors (like GIMP, Photoshop, or online converters).

To render a high-quality ray-traced image, instruct the agent:
> *"Render a snapshot using TachyonInternal and save it as complex.tga"*

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
      "command": "/home/user/.local/bin/uv",
      "args": [
        "run", 
        "--project", "/absolute/path/to/vmd-mcp", 
        "/absolute/path/to/vmd-mcp/vmd_mcp_server.py"
      ]
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
      "command": "/home/user/.local/bin/uv",
      "args": [
        "run", 
        "--project", "/absolute/path/to/vmd-mcp", 
        "/absolute/path/to/vmd-mcp/vmd_mcp_server.py"
      ]
    }
  }
}
```
