import os

def parse_chains_from_pdb(file_path):
    chain_to_desc = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            compnd_text = ""
            for line in f:
                if line.startswith("COMPND"):
                    compnd_text += line[10:].strip() + " "
            
            mol_sections = compnd_text.split("MOL_ID:")
            for sec in mol_sections:
                if not sec.strip(): continue
                molecule = ""
                chains = []
                if "MOLECULE:" in sec:
                    mol_part = sec.split("MOLECULE:")[1]
                    molecule = mol_part.split(";")[0].strip()
                if "CHAIN:" in sec:
                    chain_part = sec.split("CHAIN:")[1]
                    chains_str = chain_part.split(";")[0].strip()
                    chains = [c.strip() for c in chains_str.split(",")]
                for c in chains:
                    if c:
                        chain_to_desc[c] = molecule
    except Exception as e:
        print(f"Error parsing PDB chains for {os.path.basename(file_path)}: {e}")
    return chain_to_desc

def get_chain_lengths(file_path):
    chain_lengths = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith("ATOM") and line[12:16].strip() == "CA":
                    chain = line[21].strip()
                    if chain:
                        chain_lengths[chain] = chain_lengths.get(chain, 0) + 1
    except Exception as e:
        print(f"Error getting chain lengths for {os.path.basename(file_path)}: {e}")
    return chain_lengths

def classify_chains(file_path):
    desc_map = parse_chains_from_pdb(file_path)
    chain_lengths = get_chain_lengths(file_path)
    
    e_chains = []
    ab_chains = []
    m_chains = []
    other_chains = []
    
    for ch, length in chain_lengths.items():
        desc = desc_map.get(ch, "").lower()
        
        # Classification by COMPND description keywords
        if any(kw in desc for kw in ['envelope protein', 'glycoprotein e', 'protein e', 'ectodomain', 'envelope glycoprotein', 'major envelope', 'domain iii', 'diii']):
            e_chains.append(ch)
        elif any(kw in desc for kw in ['membrane polyprotein', 'membrane glycoprotein', 'protein m', 'membrane protein', 'small envelope protein m']):
            m_chains.append(ch)
        elif any(kw in desc for kw in ['heavy chain', 'light chain', 'fab', 'scfv', 'nanobody', 'vhh', 'immunoglobulin', 'antibody', 'antigen-binding', 'fragment', 'mab']):
            ab_chains.append(ch)
        else:
            # Fallback by length/standard naming
            if length >= 280:
                e_chains.append(ch)
            elif 70 <= length <= 90 and 'membrane' in desc:
                m_chains.append(ch)
            elif 95 <= length <= 270:
                ab_chains.append(ch)
            elif ch in ['H', 'L']:
                ab_chains.append(ch)
            else:
                other_chains.append(ch)
                
    # Direct heuristics if still unresolved
    # Check standard H/L naming for antibodies
    for ch in list(chain_lengths.keys()):
        if ch in ['H', 'L'] and ch not in ab_chains:
            ab_chains.append(ch)
            if ch in e_chains: e_chains.remove(ch)
            if ch in other_chains: other_chains.remove(ch)
    
    # If we have no E chains, take the longest remaining chain
    if not e_chains:
        remaining = [ch for ch in chain_lengths.keys() if ch not in ab_chains and ch not in m_chains]
        if remaining:
            longest = max(remaining, key=lambda ch: chain_lengths[ch])
            e_chains.append(longest)
            if longest in other_chains: other_chains.remove(longest)
            
    # If we have no Ab chains, but there are chains that are clearly antibodies (e.g. by length and not classified as E)
    if not ab_chains:
        remaining = [ch for ch in chain_lengths.keys() if ch not in e_chains and ch not in m_chains]
        for ch in remaining:
            if 90 <= chain_lengths[ch] <= 270:
                ab_chains.append(ch)
                if ch in other_chains: other_chains.remove(ch)
                
    return e_chains, ab_chains

def main():
    examples_dir = "/media/groponp/Galvani/Scripts/MSTBxMPCPs/examples"
    files = sorted([f for f in os.listdir(examples_dir) if f.endswith('.pdb')])
    print(f"Analyzing {len(files)} PDB files...")
    
    tcl_lines = []
    # Set VMD display properties
    tcl_lines.append("display projection orthographic")
    tcl_lines.append("display depthcue off")
    tcl_lines.append("axes location lowerleft")
    tcl_lines.append("color Display Background white")
    
    unresolved_e = []
    uncomplexed = []
    for file_name in files:
        file_path = os.path.join(examples_dir, file_name)
        e_chains, ab_chains = classify_chains(file_path)
        
        if not e_chains:
            unresolved_e.append(file_name)
            e_str = "A"
        else:
            e_str = " ".join(e_chains)
            
        if not ab_chains:
            uncomplexed.append(file_name)
            ab_str = ""
        else:
            ab_str = " ".join(ab_chains)
            
        print(f"{file_name}: E={e_chains}, Ab={ab_chains}")
        
        # Add VMD commands for this molecule
        tcl_lines.append(f"# Molecule: {file_name}")
        tcl_lines.append(f"mol new \"{file_path}\"")
        tcl_lines.append("mol delrep 0 top")
        
        # Rep 1: Cartoon of all protein colored by chain
        tcl_lines.append("mol representation NewCartoon")
        tcl_lines.append("mol selection \"protein\"")
        tcl_lines.append("mol color Chain")
        tcl_lines.append("mol addrep top")
        
        # Rep 2: Interacting C-alpha atoms in VDW (cutoff 8A)
        # selection string selects CA atoms of E-protein that are within 8A of CA atoms of Ab-protein
        if ab_str:
            sel_query = f"name CA and (chain {e_str}) and (within 8 of (name CA and chain {ab_str}))"
            tcl_lines.append(f"mol representation VDW")
            tcl_lines.append(f"mol selection \"{sel_query}\"")
            tcl_lines.append("mol color ColorID 4") # Yellow
            tcl_lines.append("mol addrep top")
        
    session_tcl_path = "/media/groponp/Galvani/Scripts/MSTBxMPCPs/session.tcl"
    with open(session_tcl_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(tcl_lines) + "\n")
        
    print(f"\nCreated VMD session script at {session_tcl_path}")
    if unresolved_e:
        print(f"Warning: Could not resolve E-protein chains for: {unresolved_e}")
    if uncomplexed:
        print(f"Note: Loaded without antibody (uncomplexed): {uncomplexed}")

if __name__ == "__main__":
    main()
