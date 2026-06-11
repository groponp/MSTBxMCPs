import socket
import json
import time
import os
from PIL import Image

def send_to_vmd(command: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 9877))
        s.sendall((command + "\n").encode('utf-8'))
        s.settimeout(60.0)  # High resolution AO rendering can take longer
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
                continue
        if chunks:
            return json.loads(b''.join(chunks).decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "No response received"}

def main():
    # 1. Get current size
    res = send_to_vmd("display get size")
    print(f"Current display size response: {res}")
    if res.get("status") != "success":
        print("Error getting display size.")
        return
        
    size_str = res.get("result", "640 480")
    parts = size_str.split()
    w = int(parts[0])
    h = int(parts[1])
    
    triple_w = w * 3
    triple_h = h * 3
    print(f"Resizing display from {w}x{h} to {triple_w}x{triple_h} (Triple Resolution)")
    
    # 2. Configure shadows, AO, depthcue, custom colors, and materials in VMD
    setup_commands = (
        "display shadows on; "
        "display ambientocclusion on; "
        "display aoambient 0.8; "
        "display aodirect 0.10; "
        "display depthcue off; "
        "color change rgb 0 0.000 0.000 1.000; "
        "color change rgb 1 1.000 0.000 0.000; "
        "color change rgb 3 1.000 0.500 0.000; "
        "color change rgb 4 1.000 1.000 0.000; "
        "color change rgb 7 0.000 1.000 0.000; "
        "color change rgb 10 0.000 1.000 1.000; "
        "color change rgb 11 0.500 0.000 0.500; "
        "foreach molid [molinfo list] { "
        "  set num_reps [molinfo $molid get numreps]; "
        "  for {set i 0} {$i < $num_reps} {incr i} { "
        "    mol modmaterial $i $molid AOShiny; "
        "  } "
        "}"
    )
    print("Configuring ambient occlusion, custom colors and materials in VMD...")
    setup_res = send_to_vmd(setup_commands)
    print(f"Setup response: {setup_res}")
    
    # 3. Resize display to 5x (4K)
    send_to_vmd(f"display resize {triple_w} {triple_h}")
    time.sleep(1.0)
    
    # 4. Hide axes and render using TachyonInternal with -aasamples 12 -fullshade
    print("Hiding axes for render...")
    send_to_vmd("axes location off")
    
    tga_path = "/home/groponp/.gemini/antigravity-cli/brain/61de1506-906d-4b96-9f3d-c1929c9cdcbb/render_ao_triple.tga"
    png_path = "/home/groponp/.gemini/antigravity-cli/brain/61de1506-906d-4b96-9f3d-c1929c9cdcbb/render_ao_triple.png"
    
    # Delete old files if they exist
    for p in [tga_path, png_path]:
        if os.path.exists(p):
            os.remove(p)
            
    print("Triggering TachyonInternal AO render (with antialiasing)...")
    # We pass the antialiasing and shading flags directly to TachyonInternal
    render_res = send_to_vmd(f"render TachyonInternal \"{tga_path}\" -aasamples 12 -fullshade")
    print(f"Render response: {render_res}")
    
    # 5. Restore original display size and axes
    print(f"Restoring display size to {w}x{h} and restoring axes")
    send_to_vmd(f"display resize {w} {h}")
    send_to_vmd("axes location lowerleft")
    
    # 6. Convert TGA to PNG using Pillow
    if os.path.exists(tga_path):
        print(f"Converting {tga_path} to {png_path}")
        im = Image.open(tga_path)
        im.save(png_path)
        print("Success! Render completed and converted to PNG.")
    else:
        print("Error: Rendered TGA file not found.")

if __name__ == "__main__":
    main()
