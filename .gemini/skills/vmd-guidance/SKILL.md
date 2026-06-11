---
name: vmd-guidance
description: |
  Comprehensive instructions, guidelines, and reference commands for interacting with VMD via the vmd-mcp server.
  Contains rigorous examples from VMD manuals for selections, representations, trajectory analysis, RMSD alignments, and rendering.
license: Apache-2.0
metadata:
  version: v1
---

# VMD (Visual Molecular Dynamics) Guidance Skill

This skill provides a comprehensive reference and protocol manual for interacting with VMD (Visual Molecular Dynamics) via the `vmd-mcp` server. It covers selection query syntax, scripting control structures, visual representations, geometric measurements, trajectory processing, and rendering.

---

## 1. Selection Query Syntax in VMD

VMD selection queries are extremely powerful and are evaluated using the `atomselect` command.

### Basic Selection Types
* **All atoms:** `all`
* **Water molecules:** `water` or `resname HOH TIP3 TIP4`
* **Protein residues:** `protein`
* **Nucleic acid residues:** `nucleic`
* **Lipid molecules:** `lipid`
* **Ions:** `ions`

### Attribute-Based Selections
* **Specific chain:** `chain A` or `chain A B`
* **Specific residue numbers:** `resid 27` or `resid 27 to 54` or `resid 27 35 44`
* **Specific residue names:** `resname HIS` or `resname GLY ALA VAL`
* **Specific atom names:** `name CA` or `name "C$"` (uses regex/wildcard for carbon atoms)
* **Elements:** `element N` or `element O`

### Boolean Operators
* Combine selectors using `and`, `or`, and `not`:
  * `protein and chain A and resid 1 to 50`
  * `water and not (within 5 of protein)`

### Proximity & Cutoff Selections
* **Within a certain distance:** `within 8 of chain B`
* **Selecting full residues within distance (CRITICAL):**
  > [!IMPORTANT]
  > Selecting simply `within 8` returns only the atoms that are within 8Å, which splits residues and leaves incomplete representations (e.g., sticks without backbone or broken rings).
  > **Always wrap proximity queries in `same residue as`:**
  > `same residue as (protein within 8 of chain B)`
  > `same residue as (hydrophobic within 5 of resname LIG)`

### Chemical/Physical Groupings
* **Acidic:** `acidic` (ASP, GLU)
* **Basic:** `basic` (ARG, HIS, LYS)
* **Charged:** `charged` (ASP, GLU, ARG, HIS, LYS)
* **Polar:** `polar`
* **Hydrophobic:** `hydrophobic`

---

## 2. Representation Modification Commands

VMD handles visual styles through representation indices. When modifying representations, use the following Tcl commands:

### Adding and Deleting Representations
* **Delete first representation:** `mol delrep 0 top`
* **Delete all representations:**
  ```tcl
  set num_reps [molinfo top get numreps]
  for {set i 0} {$i < $num_reps} {incr i} {
      mol delrep 0 top
  }
  ```
* **Add a representation:**
  ```tcl
  mol representation NewCartoon
  mol selection "protein"
  mol color Chain
  mol addrep top
  ```

### Modifying Existing Representations
* **Change Style of Rep index 0:** `mol modstyle 0 top NewCartoon` (others: `Bonds`, `CPK`, `Licorice`, `QuickSurf`, `VDW`, `Ribbons`, `Surf`)
* **Change Selection of Rep index 0:** `mol modselect 0 top "chain A"`
* **Change Color Scheme of Rep index 0:** `mol modcolor 0 top "Secondary Structure"` (others: `Chain`, `ResName`, `Type`, `Name`, `ColorID`)

---

## 3. Rigorous Scripting and Analysis Examples

Use these Tcl code blocks via `run_tcl_command` to perform complex calculations:

### A. Distance Measurement between Center of Masses
To measure the distance between the center of mass of two groups:
```tcl
set sel1 [atomselect top "chain A and protein"]
set sel2 [atomselect top "chain B and protein"]
set com1 [measure center $sel1 weight mass]
set com2 [measure center $sel2 weight mass]
set dx [expr [lindex $com1 0] - [lindex $com2 0]]
set dy [expr [lindex $com1 1] - [lindex $com2 1]]
set dz [expr [lindex $com1 2] - [lindex $com2 2]]
set dist [expr sqrt($dx*$dx + $dy*$dy + $dz*$dz)]
puts "Distance between COM: $dist A"
```

### B. Structural Alignment (RMSD Fitting)
To align/fit molecule 1 onto molecule 0 (reference):
```tcl
# Select fitting atoms (e.g. CA backbone of protein)
set sel_ref [atomselect 0 "protein and name CA"]
set sel_tgt [atomselect 1 "protein and name CA"]

# Calculate the transformation matrix
set trans_mat [measure fit $sel_tgt $sel_ref]

# Apply transformation matrix to the entire target molecule
set move_all [atomselect 1 "all"]
$move_all move $trans_mat
```

### C. Finding Hydrogen Bonds
To measure hydrogen bonds between donor and acceptor selections:
```tcl
# Returns list of {donor_index acceptor_index hydrogen_index}
set hbonds [measure hbonds 3.2 30 [atomselect top "protein and chain A"] [atomselect top "protein and chain B"]]
set num_hbonds [llength [lindex $hbonds 0]]
puts "Number of inter-chain hydrogen bonds: $num_hbonds"
```

### D. Iterating Over Trajectory Frames
To run analysis across multiple frames of a trajectory file:
```tcl
set num_frames [molinfo top get numframes]
set sel [atomselect top "protein and name CA"]
for {set i 0} {$i < $num_frames} {incr i} {
    $sel frame $i
    # Perform analysis, e.g. center of mass
    set com [measure center $sel weight mass]
    puts "Frame $i center of mass: $com"
}
```

---

## 4. Visual Adjustments & Rendering Settings

### Display and Camera Controls
* **Perspective vs Orthographic Projection:**
  * Orthographic (preferred for structural figures): `display projection orthographic`
  * Perspective: `display projection perspective`
* **Depth Cueing (Fog):**
  * Turn off: `display depthcue off` (essential for clean rendering)
  * Turn on: `display depthcue on`
* **Axes Hide:**
  * Hide coordinate axes: `axes location off`
* **Background Color:**
  * Set background to white (standard for publications): `color Display Background white`
  * Set background to black: `color Display Background black`

### Axel Kohlmeyer's Publication-Quality Rendering Protocol (Ambient Occlusion, Shadows, & Colors)

To achieve high-quality, publication-grade figures with smooth lighting, realistic shadows, pleasant desaturated colors, and depth contrast, you must configure and enable **Ambient Occlusion (AO)**, **Shadows**, and **Custom RGB Colors** in the VMD settings before triggering Tachyon/TachyonInternal.

Use the following sequence of Tcl commands:

```tcl
# 1. Turn on shadows and ambient occlusion
display shadows on
display ambientocclusion on

# 2. Configure AO parameters (Axel Kohlmeyer's recommended balance)
# aoambient: intensity of ambient light (range 0.0 to 1.0, default 0.8)
display aoambient 0.8
# aodirect: intensity of direct light (range 0.0 to 1.0, default 0.3)
display aodirect 0.10

# 3. Apply standard, default VMD color scheme (faithful representations)
color change rgb 0 0.000 0.000 1.000; # blue (pure blue)
color change rgb 1 1.000 0.000 0.000; # red (pure red)
color change rgb 3 1.000 0.500 0.000; # orange (pure orange)
color change rgb 4 1.000 1.000 0.000; # yellow (pure yellow)
color change rgb 7 0.000 1.000 0.000; # green (pure green)
color change rgb 10 0.000 1.000 1.000; # cyan (pure cyan)
color change rgb 11 0.500 0.000 0.500; # purple (pure purple)

# 4. Use AO-optimized materials for your representations (AOShiny, AOChalky, or AOEdgy)
# For example, to set the material of representation index 0 of the top molecule to AOShiny:
mol modmaterial 0 top AOShiny

# 5. Turn off depth cueing (fog) to prevent shadows from appearing washed out or too dark
display depthcue off
```

### Hiding Coordinate Axes During Rendering (CRITICAL)

To maintain clean figures, **always hide the coordinate axes during rendering**, unless the user explicitly requests to keep them. Turn them off immediately before rendering and restore them to their default position afterwards:

```tcl
# 1. Hide axes before rendering
axes location off

# 2. Perform the render
render TachyonInternal "/path/to/image.tga"

# 3. Restore axes for interactive session
axes location lowerleft
```

### Rendering High-Quality Ray-Traced Images

* **Render using standard snapshot (OpenGL viewport capture):**
  `render snapshot "/path/to/image.png"`
* **Render using TachyonInternal (with Shadows & Ambient Occlusion):**
  Use the following Tcl command to render high-resolution figures. TachyonInternal will automatically respect the shadows, ambient occlusion, and lighting settings configured above:
  ```tcl
  render TachyonInternal "/path/to/image.tga"
  ```
* **Advanced Tachyon Command-Line Options (standalone/internal):**
  You can pass direct flags to Tachyon to enable advanced anti-aliasing and ambient occlusion rendering.
  * `-aasamples 12` or `-aasamples 24`: Controls antialiasing quality (higher = smoother edges).
  * `-fullshade`: Triggers high-fidelity shading.
  * Example Tcl command:
    ```tcl
    render TachyonInternal "/path/to/image.tga" -aasamples 12 -fullshade
    ```

---

## 5. Advanced Visualization Techniques

### A. Managing Graphics-Based Text Labels (e.g. Histidines)
In VMD, custom text labels can be drawn as graphics elements on a molecule instead of using standard atom labels. To inspect, hide, or delete these graphics labels, use the following Tcl commands:

* **List all graphics IDs on a molecule:**
  `graphics <molid> list` (returns a list of active graphics IDs, e.g. `0 1 2 3...`)
* **Get details of a specific graphics ID:**
  `graphics <molid> info <id>` (returns details such as `color 16` or `text {x y z} {LabelText}`)
* **Delete a specific graphics element:**
  `graphics <molid> delete <id>`
* **Delete/Hide all graphics elements (hides all custom labels):**
  `graphics <molid> delete all`

### B. Programmatic Resolution Scaling (Double/Triple Resolution)
To scale up the output image resolution beyond the interactive window dimensions (similar to VMD's "Double" or "Triple" resolution rendering controls), retrieve the current display size, scale it, perform the render, and then restore the original dimensions:

```tcl
# 1. Get current display size
set size [display get size]
set w [lindex $size 0]
set h [lindex $size 1]

# 2. Scale size (e.g., Triple Resolution)
set triple_w [expr $w * 3]
set triple_h [expr $h * 3]
display resize $triple_w $triple_h

# 3. Render (axes hidden automatically)
axes location off
render TachyonInternal "output.tga" -aasamples 12 -fullshade
axes location lowerleft

# 4. Restore original display size
display resize $w $h
```


