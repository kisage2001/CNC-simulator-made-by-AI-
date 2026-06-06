# custom-cnc-plate-machining

A professional FANUC-compliant G-code package and interactive 3D Web Simulator for machining a custom aluminum plate (A5052, 10mm thickness) on CNC milling machines and vertical machining centers (e.g., FANUC RoboDrill).

---

## 📐 Workpiece Specifications
*   **Material:** Aluminum A5052
*   **Dimensions:** 65 mm (Width) × 85 mm (Height) × 10 mm (Thickness)
*   **Features:**
    1.  Central φ50 mm (H7 tolerance) through-hole
    2.  4 × M5 threaded holes (50 mm pitch)
    3.  2 × φ5.5 mm through-holes (30 mm pitch)

---

## 🛠️ Machining Programs

This repository provides two different programming options depending on your setup.

### Option A: RoboDrill Multi-Tool Program (Recommended)
An optimized production G-code utilizing **5 tools** and standard **FANUC canned cycles** (G81, G83, G84) designed for professional machining centers.

*   **G-Code File:** [`plate_robodrill.gcode`](./plate_robodrill.gcode)
*   **3D Web Simulator:** [`simulator_robodrill.html`](./simulator_robodrill.html)

#### Tooling List & Cutting Parameters
1.  **T1: Spot Drill**
    *   Parameters: $3000\text{ RPM}$ / $150\text{ mm/min}$ feed
    *   Operation: Spot drilling all 7 hole locations (`G98 G81 Z-1.5 R2.0`)
2.  **T6: φ5.5 Drill**
    *   Parameters: $1800\text{ RPM}$ / $150\text{ mm/min}$ feed
    *   Operation: Pre-drills the central hole and drills the bottom holes.
    *   Strategy: Deep hole peck drilling cycle (`G98 G83`) with the peck depth Q set to 10% of the drill diameter (**`Q0.550`**) to clear chips and cycle coolant.
3.  **T14: φ6.0 Flat Endmill**
    *   **Cutting Speeds & Feeds:**
        *   Cutting speed $Vc = 50\text{ m/min}$ $\rightarrow$ **S2650 RPM**
        *   Feed per tooth $f = 0.05\text{ mm/tooth}$ (2-flute carbide tool) $\rightarrow$ **F265 mm/min**
    *   **Helical Interpolation Ramping:**
        *   Position above the start point on the circumference (`X54.5 Y47.15`) at `Z10.0`, then rapid down to `Z1.0`.
        *   Feeds helically down to `Z-10.5` in $1.0\text{ mm}$ pitch increments (`G03` spiral).
        *   Performs a full flat cleanup pass at the bottom (`Z-10.5`) to ensure a clean through-edge.
        *   Feeds radially inward by $2\text{ mm}$ (`G01 X52.5`) to clear the finished wall, then rapids up to `Z10.0`.
4.  **T5: φ4.2 Drill (Pre-drill for M5)**
    *   Parameters: $2000\text{ RPM}$ / $150\text{ mm/min}$ feed
    *   Operation: Peck drilling four M5 pre-holes with peck depth **`Q0.420`** (10% of drill diameter).
5.  **T9: M5 Tap**
    *   Parameters: $500\text{ RPM}$ / $400\text{ mm/min}$ feed (synchronized exactly: $\text{Speed } 500 \times 0.8\text{mm pitch} = F400$)
    *   Operation: Rigid tapping cycle (`M29 S500` followed by `G98 G84 Z-12.0 R3.0`).

---

### Option B: Single 4.2mm Endmill Program
Designed for hobbyist CNC routers or setups without automatic tool changers, allowing the entire plate to be completed using a single endmill.

*   **G-Code File:** [`plate_machining.gcode`](./plate_machining.gcode)
*   **3D Web Simulator:** [`simulator.html`](./simulator.html)
*   **Operations:**
    *   Central φ50 mm hole: Concentration pocketing (clears the entire inner volume).
    *   M5 holes (φ4.2): Direct plunge peck drilling.
    *   φ5.5 holes: Helical circular interpolation milling to expand to φ5.5 mm.

---

## 💻 3D Web Simulator

Each program is accompanied by an interactive 3D HTML simulator built on Three.js. You can open `simulator_robodrill.html` or `simulator.html` directly in any standard web browser (Chrome, Safari, Edge, Firefox) offline.

1.  **3D Viewport Navigation:**
    *   Left-click + Drag: Rotate the camera view
    *   Right-click + Drag: Pan the camera view
    *   Scroll Wheel: Zoom in / Zoom out
2.  **Playback Controls:**
    *   **PLAY / PAUSE:** Start/stop the tool animation.
    *   **RESET:** Reset the simulation to the beginning.
    *   **Speed Slider:** Fast-forward the tool animation (from 1x to 100x speed) to preview the entire program in seconds.
3.  **Real-Time Status Panel:**
    *   Displays current active tool (the 3D tip shape and color dynamically change to match tool specs).
    *   Coordinates readout (X, Y, Z) and active feed rate.
    *   Live scrolling G-code display highlighting the active executing block.

---

## ⚠️ Machining & Safety Notes
1.  **Work Coordinate System (G54 Origin):**
    Set your origin $(X0.0, Y0.0, Z0.0)$ to the **bottom-left corner** of the stock plate on its **top surface**.
2.  **Z-Axis Clearance (G98):**
    The G-code is written using `G98` (retract to initial Z level) for all canned cycles. The tools will retract to `Z10.0` between holes to safely clear clamps and fixtures. Ensure your setup allows for this height clearance.
3.  **Aluminum Slug Hazard (Option A only):**
    Because the central φ50 mm hole is contour-milled rather than pocketed, a solid metal slug of approximately $\phi 38\text{mm}$ will drop out during the final pass. **Adequately secure the plate and slug** (e.g., using double-sided tape, vacuum fixtures, or manual pauses on the final pass) to prevent the slug from jamming the tool.
4.  **Coolant supply:**
    Aluminum A5052 is prone to welding to the tool edges. **Always run with flood/mist coolant active** (`M08`) or apply cutting fluid manually.
