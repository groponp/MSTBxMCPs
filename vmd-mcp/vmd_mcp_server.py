#!/usr/bin/env python3
"""
VMD MCP Server
A FastMCP server to interface with VMD (Visual Molecular Dynamics) via a Tcl socket connection.
"""

import socket
import json
import logging
import subprocess
import time
import os
import shutil
import platform
import glob
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("vmd-mcp")

# Initialize FastMCP Server
mcp = FastMCP("VMD")

def find_vmd_binary() -> str:
    # 1. Try system PATH
    for binary_name in ["vmd2", "vmd1.9", "vmd", "vmd.exe"]:
        path = shutil.which(binary_name)
        if path:
            logger.info(f"Dynamically located VMD binary in PATH: {path}")
            return path
            
    # 2. Check standard operating system locations
    sys_name = platform.system()
    if sys_name == "Darwin":  # macOS
        # Search in /Applications for VMD app bundles
        mac_patterns = [
            "/Applications/VMD*.app/Contents/Resources/VMD.app/Contents/MacOS/VMD",
            "/Applications/VMD*.app/Contents/vmd",
            "/usr/local/bin/vmd"
        ]
        for pattern in mac_patterns:
            matches = glob.glob(pattern)
            if matches:
                logger.info(f"Dynamically located VMD binary on macOS: {matches[0]}")
                return matches[0]
                
    elif sys_name == "Windows":
        # Search standard Program Files paths
        program_files = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            "C:\\Program Files",
            "C:\\Program Files (x86)"
        ]
        for pf in program_files:
            win_path = os.path.join(pf, "University of Illinois", "VMD", "vmd.exe")
            if os.path.exists(win_path):
                logger.info(f"Dynamically located VMD binary on Windows: {win_path}")
                return win_path
            win_path_alt = os.path.join(pf, "VMD", "vmd.exe")
            if os.path.exists(win_path_alt):
                logger.info(f"Dynamically located VMD binary on Windows: {win_path_alt}")
                return win_path_alt
                
    else:  # Linux/Unix
        linux_paths = [
            "/usr/local/bin/vmd",
            "/usr/bin/vmd",
            "/opt/vmd/bin/vmd",
            "/usr/local/vmd/bin/vmd"
        ]
        for lp in linux_paths:
            if os.path.exists(lp):
                logger.info(f"Dynamically located VMD binary on Linux: {lp}")
                return lp
                
    # Fallback default
    logger.warning("VMD binary could not be found in standard paths. Falling back to default '/usr/local/bin/vmd'")
    return "/usr/local/bin/vmd"

VMD_PATH = find_vmd_binary()
TCL_SCRIPT_PATH = "/media/groponp/Galvani/Scripts/MSTBxMPCPs/vmd-mcp/vmd_socket_server.tcl"
VMD_HOST = "127.0.0.1"
VMD_PORT = 9877
_vmd_process = None

def ensure_vmd_running_and_connected() -> socket.socket:
    """
    Attempts to connect to the VMD TCP socket server.
    If the connection is refused, it automatically launches VMD in the background,
    loading the Tcl socket server script, and retries the connection.
    """
    global _vmd_process
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((VMD_HOST, VMD_PORT))
        return s
    except ConnectionRefusedError:
        logger.info("VMD socket server not responding. Attempting to launch VMD automatically...")
        
        # Verify VMD binary exists
        if not os.path.exists(VMD_PATH):
            raise FileNotFoundError(
                f"VMD executable not found at '{VMD_PATH}'. "
                "Please make sure VMD is installed and available in that path."
            )
            
        # Verify Tcl script exists
        if not os.path.exists(TCL_SCRIPT_PATH):
            raise FileNotFoundError(
                f"VMD socket server script not found at '{TCL_SCRIPT_PATH}'."
            )
            
        # Launch VMD in the background with the startup script
        # start_new_session=True keeps it running independently of the MCP server lifecycle
        # stdin=subprocess.PIPE keeps the stdin channel open to prevent VMD from exiting on EOF
        _vmd_process = subprocess.Popen(
            [VMD_PATH, "-e", TCL_SCRIPT_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Poll the socket to see when VMD finishes booting and starts listening
        # Try up to 7 times (7 seconds)
        for i in range(7):
            time.sleep(1.0)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((VMD_HOST, VMD_PORT))
                logger.info("Connected to newly launched VMD instance.")
                return s
            except ConnectionRefusedError:
                continue
                
        raise ConnectionError(
            "Failed to connect to VMD after automatically starting it. "
            "Please check if VMD is launching correctly."
        )

def send_to_vmd(command: str) -> dict:
    """
    Sends a Tcl command to VMD via a TCP socket (auto-launching VMD if not running).
    Returns the parsed JSON response dict:
      {
        "status": "success" | "error",
        "result": str (on success),
        "message": str (on error)
      }
    """
    try:
        s = ensure_vmd_running_and_connected()
        with s:
            # Command must end with newline for gets inside Tcl server
            s.sendall((command + "\n").encode('utf-8'))
            s.settimeout(10.0)
            
            # Read response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                buffer = b''.join(chunks)
                try:
                    response = json.loads(buffer.decode('utf-8'))
                    return response
                except json.JSONDecodeError:
                    # Incomplete JSON, continue reading
                    continue
            
            if chunks:
                buffer = b''.join(chunks)
                return json.loads(buffer.decode('utf-8'))
            
            return {"status": "error", "message": "No response received from VMD."}
            
    except Exception as e:
        return {"status": "error", "message": f"VMD Interaction Error: {str(e)}"}

@mcp.tool()
def run_tcl_command(command: str) -> str:
    """
    Execute a raw Tcl command directly inside the VMD interpreter.
    Use this for custom workflows or commands not covered by other tools.
    Examples:
      - 'rotate x by 90'
      - 'scale by 1.2'
      - 'pbc box'
    """
    response = send_to_vmd(command)
    if response.get("status") == "success":
        return f"Executed successfully.\nResult: {response.get('result')}"
    else:
        return f"Execution Error: {response.get('message')}"

@mcp.tool()
def load_molecule(filename: str, filetype: str = "pdb") -> str:
    """
    Load a molecule from a file or from the PDB web database into VMD.
    
    Args:
        filename: Absolute file path, relative file path, or 4-letter RCSB PDB ID (e.g. '1ubq').
        filetype: Type of file (default 'pdb'). If loading a PDB ID, use 'pdb'.
    """
    # If filename is a 4-letter alphanumeric string, it's likely a PDB ID
    if len(filename) == 4 and filename.isalnum():
        cmd = f"mol new {filename} type {filetype} waitfor all"
    else:
        cmd = f"mol new \"{filename}\" type {filetype} waitfor all"
        
    response = send_to_vmd(cmd)
    if response.get("status") == "success":
        molid = response.get("result")
        return f"Molecule loaded successfully with ID: {molid}"
    else:
        return f"Failed to load molecule: {response.get('message')}"

@mcp.tool()
def get_loaded_molecules() -> str:
    """
    Query VMD to retrieve a list of all currently loaded molecules, including their IDs and names.
    """
    tcl_script = (
        "set mol_list [molinfo list]; "
        "set result \"\"; "
        "foreach id $mol_list { "
        "append result \"ID: $id - Name: [molinfo $id get name]\\n\" "
        "}; "
        "set result"
    )
    response = send_to_vmd(tcl_script)
    if response.get("status") == "success":
        res = response.get("result", "").strip()
        return res if res else "No molecules currently loaded in VMD."
    else:
        return f"Error querying molecules: {response.get('message')}"

@mcp.tool()
def delete_molecule(molid: int) -> str:
    """
    Deletes the molecule with the specified ID from VMD.
    """
    cmd = f"mol delete {molid}"
    response = send_to_vmd(cmd)
    if response.get("status") == "success":
        return f"Molecule {molid} deleted."
    else:
        return f"Error deleting molecule {molid}: {response.get('message')}"

@mcp.tool()
def list_representations(molid: int) -> str:
    """
    Retrieve all representation styles, selection strings, and color schemes for a molecule in VMD.
    """
    tcl_script = (
        f"set num_reps [molinfo {molid} get numreps]; "
        "set result \"\"; "
        "for {set i 0} {$i < $num_reps} {incr i} { "
        f"append result \"Rep $i: Style=[molinfo {molid} get \\\"rep $i\\\"] Selection=[molinfo {molid} get \\\"selection $i\\\"] Color=[molinfo {molid} get \\\"color $i\\\"]\\n\" "
        "}; "
        "set result"
    )
    response = send_to_vmd(tcl_script)
    if response.get("status") == "success":
        res = response.get("result", "").strip()
        return res if res else f"No representations found for molecule {molid}."
    else:
        return f"Error querying representations: {response.get('message')}"

@mcp.tool()
def change_representation(molid: int, rep_index: int, style: str, selection: str = "all", color: str = "Name") -> str:
    """
    Modify an existing representation index for a specific molecule.
    
    Args:
        molid: Molecule ID.
        rep_index: Index of the representation to modify (usually starting at 0).
        style: Drawing style. Options: 'NewCartoon', 'Bonds', 'CPK', 'Licorice', 'QuickSurf', 'VDW', 'Ribbons', 'Surf'.
        selection: Atom selection query (e.g. 'all', 'protein', 'backbone', 'water', 'resid 1 to 10').
        color: Coloring scheme (e.g. 'Name', 'Type', 'ResName', 'Secondary Structure', 'Structure', 'Chain').
    """
    tcl_commands = (
        f"mol modstyle {rep_index} {molid} {style}; "
        f"mol modselect {rep_index} {molid} {selection}; "
        f"mol modcolor {rep_index} {molid} {color}"
    )
    response = send_to_vmd(tcl_commands)
    if response.get("status") == "success":
        return f"Representation {rep_index} updated successfully."
    else:
        return f"Error modifying representation: {response.get('message')}"

@mcp.tool()
def add_representation(molid: int, style: str, selection: str = "all", color: str = "Name") -> str:
    """
    Add a new representation to a specific molecule.
    
    Args:
        molid: Molecule ID.
        style: Drawing style (e.g. 'NewCartoon', 'Bonds', 'Licorice').
        selection: Atom selection query (e.g. 'protein', 'nucleic').
        color: Coloring scheme (e.g. 'Secondary Structure', 'Chain').
    """
    tcl_script = (
        f"mol addrep {molid}; "
        f"set num_reps [molinfo {molid} get numreps]; "
        "set new_rep [expr $num_reps - 1]; "
        f"mol modstyle $new_rep {molid} {style}; "
        f"mol modselect $new_rep {molid} {selection}; "
        f"mol modcolor $new_rep {molid} {color}; "
        "set new_rep"
    )
    response = send_to_vmd(tcl_script)
    if response.get("status") == "success":
        new_rep_idx = response.get("result")
        return f"Added representation successfully at index {new_rep_idx}."
    else:
        return f"Error adding representation: {response.get('message')}"

@mcp.tool()
def delete_representation(molid: int, rep_index: int) -> str:
    """
    Deletes the representation at the specified index for a molecule.
    """
    cmd = f"mol delrep {rep_index} {molid}"
    response = send_to_vmd(cmd)
    if response.get("status") == "success":
        return f"Representation {rep_index} deleted from molecule {molid}."
    else:
        return f"Error deleting representation: {response.get('message')}"

@mcp.tool()
def render_snapshot(file_path: str, renderer: str = "snapshot") -> str:
    """
    Render the current VMD screen view to an output image file.
    
    Args:
        file_path: Absolute file path where the image should be saved (e.g., '/home/user/image.png').
        renderer: Rendering engine to use. Default is 'snapshot'. Others include 'TachyonInternal', 'Tachyon', 'POV3'.
    """
    cmd = f"render {renderer} \"{file_path}\""
    response = send_to_vmd(cmd)
    if response.get("status") == "success":
        return f"Rendered successfully to {file_path} using {renderer}."
    else:
        return f"Rendering error: {response.get('message')}"

if __name__ == "__main__":
    mcp.run()
