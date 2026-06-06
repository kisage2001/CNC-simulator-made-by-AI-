import os
import math
import shutil
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def generate_gcode():
    plate_w = 65.0
    plate_h = 85.0
    plate_t = 10.0
    
    # Tool definitions
    # T1: Spot Drill
    # T5: phi4.2 Drill (pre-drill for M5)
    # T6: phi5.5 Drill (canned cycle bottom holes + central pre-drill)
    # T14: phi6.0 Flat Endmill (pocketing central hole)
    # T9: M5 Tap
    
    safe_z = 10.0
    start_z = 10.0
    r_plane = 2.0
    
    cx, cy = plate_w / 2.0, 47.15
    
    # 4 M5 hole coordinates
    m5_pitch = 50.0
    m5_holes = [
        (cx - m5_pitch/2.0, cy + m5_pitch/2.0),
        (cx + m5_pitch/2.0, cy + m5_pitch/2.0),
        (cx - m5_pitch/2.0, cy - m5_pitch/2.0),
        (cx + m5_pitch/2.0, cy - m5_pitch/2.0)
    ]
    
    # 2 bottom holes coordinates
    bottom_hole_y = 8.25
    bottom_hole_pitch = 30.0
    bottom_holes = [
        (cx - bottom_hole_pitch/2.0, bottom_hole_y),
        (cx + bottom_hole_pitch/2.0, bottom_hole_y)
    ]
    
    gcode = []
    gcode.append("%")
    gcode.append("O1002(PLATE MACHINING ROBODRILL)")
    gcode.append("( 2026/06/04 )")
    gcode.append("")
    gcode.append("G17 G40 G80")
    gcode.append("G00 G91 G28 Z0.")
    gcode.append("")

    # --- Tool 1: Spot Drill ---
    gcode.append("N0001")
    gcode.append("( T1 NC SPOT DRILL - 6 | D1 | H1 | )")
    gcode.append("G49 T1 M6")
    gcode.append(f"G54 G90 G00 X{cx:.3f} Y{cy:.3f}")
    gcode.append("S3000 M03")
    gcode.append(f"G43 H1 Z{start_z:.3f}")
    gcode.append("M08")
    # G81 cycle at central hole, M5 holes, and bottom holes
    gcode.append(f"G98 G81 Z-1.500 R{r_plane:.3f} F150.")
    # Drill coordinates
    for hx, hy in m5_holes:
        gcode.append(f"X{hx:.3f} Y{hy:.3f}")
    for bx, by in bottom_holes:
        gcode.append(f"X{bx:.3f} Y{by:.3f}")
    gcode.append("G80")
    gcode.append("M09")
    gcode.append("M05")
    gcode.append("G91 G28 Z0.")
    gcode.append("M01")
    gcode.append("")

    # --- Tool 6: φ5.5 Drill ---
    # Drill diameter = 5.5mm. Peck Q = 10% of 5.5 = 0.55mm
    peck_q_t6 = 0.55
    gcode.append("N0002")
    gcode.append("( T6 PHI5.5 DRILL | D6 | H6 | )")
    gcode.append("G49 T6 M6")
    gcode.append(f"G54 G90 G00 X{cx:.3f} Y{cy:.3f}")
    gcode.append("S1800 M03")
    gcode.append(f"G43 H6 Z{start_z:.3f}")
    gcode.append("M08")
    # Central hole pre-drill and bottom holes
    gcode.append(f"G98 G83 Z-13.000 R{r_plane:.3f} Q{peck_q_t6:.3f} F150.")
    for bx, by in bottom_holes:
        gcode.append(f"X{bx:.3f} Y{by:.3f}")
    gcode.append("G80")
    gcode.append("M09")
    gcode.append("M05")
    gcode.append("G91 G28 Z0.")
    gcode.append("M01")
    gcode.append("")

    # --- Tool 14: φ6 Flat Endmill ---
    # Calculated Speed & Feed:
    # Cutting speed Vc = 50 m/min -> RPM = (50 * 1000) / (pi * 6.0) = 2652.58 -> 2650 RPM
    # Feed per tooth f = 0.05 mm/tooth -> Feed rate = 2650 * 0.05 * 2 (teeth) = 265 mm/min
    spindle_t14 = 2650
    feed_t14 = 265
    gcode.append("N0003")
    gcode.append("( T14 PHI6 FLAT END MILL | D14 | H14 | )")
    gcode.append("G49 T14 M6")
    
    # Helical starts at circumference X54.5 Y47.15 (cx+22.0)
    gcode.append(f"G54 G90 G00 X{cx + 22.0:.3f} Y{cy:.3f}")
    gcode.append(f"S{spindle_t14} M03")
    gcode.append(f"G43 H14 Z{start_z:.3f}")
    gcode.append("M08")
    gcode.append("G00 Z1.000") # Rapid down to Z=1.0
    
    # Helical interpolation down from Z=1.0 to Z=-10.5 in steps of 1.0mm
    gcode.append(f"G03 X{cx + 22.0:.3f} Y{cy:.3f} Z0.000 I-22.000 J0.000 F{feed_t14}")
    for depth in range(-1, -11, -1):
        gcode.append(f"G03 X{cx + 22.0:.3f} Y{cy:.3f} Z{depth:.3f} I-22.000 J0.000")
    # Final turn to reach Z-10.5
    gcode.append(f"G03 X{cx + 22.0:.3f} Y{cy:.3f} Z-10.500 I-22.000 J0.000")
    # Full circle at Z-10.5 to clean up bottom face
    gcode.append(f"G03 X{cx + 22.0:.3f} Y{cy:.3f} I-22.000 J0.000")
    # Safe exit from inner wall (move towards center by 2mm)
    gcode.append(f"G01 X{cx + 20.0:.3f} Y{cy:.3f} F{feed_t14}")
    gcode.append(f"G00 Z{start_z:.3f}")
    
    gcode.append("M09")
    gcode.append("M05")
    gcode.append("G91 G28 Z0.")
    gcode.append("M01")
    gcode.append("")

    # --- Tool 5: φ4.2 Drill ---
    # Drill diameter = 4.2mm. Peck Q = 10% of 4.2 = 0.42mm
    peck_q_t5 = 0.42
    gcode.append("N0004")
    gcode.append("( T5 PHI4.2 DRILL | D5 | H5 | )")
    gcode.append("G49 T5 M6")
    gcode.append(f"G54 G90 G00 X{m5_holes[0][0]:.3f} Y{m5_holes[0][1]:.3f}")
    gcode.append("S2000 M03")
    gcode.append(f"G43 H5 Z{start_z:.3f}")
    gcode.append("M08")
    # Peck drill four M5 holes
    gcode.append(f"G98 G83 Z-13.000 R{r_plane:.3f} Q{peck_q_t5:.3f} F150.")
    for idx in range(1, len(m5_holes)):
        gcode.append(f"X{m5_holes[idx][0]:.3f} Y{m5_holes[idx][1]:.3f}")
    gcode.append("G80")
    gcode.append("M09")
    gcode.append("M05")
    gcode.append("G91 G28 Z0.")
    gcode.append("M01")
    gcode.append("")

    # --- Tool 9: M5 Tap ---
    gcode.append("N0005")
    gcode.append("( T9 M5 TAP | D9 | H9 | )")
    gcode.append("G49 T9 M6")
    gcode.append(f"G54 G90 G00 X{m5_holes[0][0]:.3f} Y{m5_holes[0][1]:.3f}")
    gcode.append("S500")
    gcode.append(f"G43 H9 Z{start_z:.3f}")
    gcode.append("M08")
    gcode.append("M29 S500") # Rigid tapping activation
    # Feed = Speed * Pitch = 500 * 0.8 = 400 mm/min
    gcode.append(f"G98 G84 Z-12.000 R3.000 F400.")
    for idx in range(1, len(m5_holes)):
        gcode.append(f"X{m5_holes[idx][0]:.3f} Y{m5_holes[idx][1]:.3f}")
    gcode.append("G80")
    gcode.append("M09")
    gcode.append("M05")
    gcode.append("G91 G28 Z0.")
    gcode.append("M30")
    gcode.append("%")
    
    file_path = "plate_robodrill.gcode"
    with open(file_path, "w") as f:
        f.write("\n".join(gcode))
        
    print(f"RoboDrill G-code written to {file_path}")
    return file_path

def parse_gcode_and_plot(gcode_file, image_path):
    segments = []
    curr_x = 0.0
    curr_y = 0.0
    curr_z = 5.0
    
    canned_cycle = None
    canned_z = 0.0
    canned_r = 0.0
    initial_z = 5.0
    
    with open(gcode_file, 'r') as f:
        lines = f.readlines()
        
    modal_cmd = 1
    
    for line in lines:
        line_clean = line.split(';')[0].split('(')[0].strip()
        if not line_clean or line_clean.startswith('%') or line_clean.upper().startswith('O') or 'G28' in line_clean.upper():
            continue
            
        tokens = line_clean.upper().split()
        
        # Parse commands
        cmd = None
        has_g80 = False
        
        for t in tokens:
            if t.startswith('G'):
                try:
                    val = float(t[1:])
                    if val in [0, 1, 2, 3]:
                        cmd = int(val)
                        canned_cycle = None
                    elif val in [81, 83, 84]:
                        canned_cycle = f"G{int(val)}"
                    elif val == 80:
                        canned_cycle = None
                        has_g80 = True
                except ValueError:
                    pass
                    
        if has_g80:
            continue
            
        new_x = curr_x
        new_y = curr_y
        new_z = curr_z
        i_val = 0.0
        j_val = 0.0
        r_val = None
        
        has_xyz = False
        has_ij = False
        has_z = False
        
        for t in tokens:
            if t.startswith('X'):
                new_x = float(t[1:])
                has_xyz = True
            elif t.startswith('Y'):
                new_y = float(t[1:])
                has_xyz = True
            elif t.startswith('Z'):
                new_z = float(t[1:])
                has_xyz = True
                has_z = True
            elif t.startswith('I'):
                i_val = float(t[1:])
                has_ij = True
            elif t.startswith('J'):
                j_val = float(t[1:])
                has_ij = True
            elif t.startswith('R'):
                r_val = float(t[1:])
                
        if canned_cycle is not None:
            if has_z: canned_z = new_z
            if r_val is not None: canned_r = r_val
            
            # Target positions
            tx = new_x if has_xyz else curr_x
            ty = new_y if has_xyz else curr_y
            
            # 1. Position to hole (G0 X/Y)
            if curr_x != tx or curr_y != ty:
                segments.append(('G0', [curr_x, tx], [curr_y, ty], [curr_z, curr_z]))
                curr_x, curr_y = tx, ty
                
            # 2. Plunge down to canned_r (G0)
            if curr_z > canned_r:
                segments.append(('G0', [curr_x, curr_x], [curr_y, curr_y], [curr_z, canned_r]))
                curr_z = canned_r
                
            # 3. Drill down to canned_z (G1)
            segments.append(('G1', [curr_x, curr_x], [curr_y, curr_y], [curr_z, canned_z]))
            curr_z = canned_z
            
            # 4. Retract back to initial_z (G0)
            segments.append(('G0', [curr_x, curr_x], [curr_y, curr_y], [curr_z, initial_z]))
            curr_z = initial_z
            continue
            
        if cmd is not None:
            modal_cmd = cmd
        elif has_xyz:
            cmd = modal_cmd
        else:
            continue
            
        if cmd == 0:
            segments.append(('G0', [curr_x, new_x], [curr_y, new_y], [curr_z, new_z]))
            curr_x, curr_y, curr_z = new_x, new_y, new_z
        elif cmd == 1:
            segments.append(('G1', [curr_x, new_x], [curr_y, new_y], [curr_z, new_z]))
            curr_x, curr_y, curr_z = new_x, new_y, new_z
        elif cmd in [2, 3]:
            cx_a = curr_x + i_val
            cy_a = curr_y + j_val
            r = math.sqrt(i_val**2 + j_val**2)
            
            theta_start = math.atan2(curr_y - cy_a, curr_x - cx_a)
            theta_end = math.atan2(new_y - cy_a, new_x - cx_a)
            
            if abs(curr_x - new_x) < 1e-4 and abs(curr_y - new_y) < 1e-4:
                if cmd == 3:
                    theta_end = theta_start + 2.0 * math.pi
                else:
                    theta_end = theta_start - 2.0 * math.pi
            else:
                if cmd == 3:
                    if theta_end <= theta_start:
                        theta_end += 2.0 * math.pi
                else:
                    if theta_end >= theta_start:
                        theta_end -= 2.0 * math.pi
            
            num_points = 40
            theta_pts = np.linspace(theta_start, theta_end, num_points)
            xs = cx_a + r * np.cos(theta_pts)
            ys = cy_a + r * np.sin(theta_pts)
            zs = np.linspace(curr_z, new_z, num_points)
            
            segments.append((f'G{cmd}', xs, ys, zs))
            curr_x, curr_y, curr_z = new_x, new_y, new_z

    # Plotting using matplotlib 3D
    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    
    # 1. Draw Stock Boundary
    pw, ph, pt = 65.0, 85.0, 10.0
    corners = np.array([
        [0, 0, 0], [pw, 0, 0], [pw, ph, 0], [0, ph, 0],
        [0, 0, -pt], [pw, 0, -pt], [pw, ph, -pt], [0, ph, -pt]
    ])
    
    ax.plot([0, pw, pw, 0, 0], [0, 0, ph, ph, 0], [0, 0, 0, 0, 0], color='gray', linestyle='--', alpha=0.7, label='Stock Outline (65x85x10mm)')
    ax.plot([0, pw, pw, 0, 0], [0, 0, ph, ph, 0], [-pt, -pt, -pt, -pt, -pt], color='gray', linestyle='--', alpha=0.5)
    for i in range(4):
        ax.plot([corners[i, 0], corners[i+4, 0]], [corners[i, 1], corners[i+4, 1]], [corners[i, 2], corners[i+4, 2]], color='gray', linestyle='--', alpha=0.5)

    # 2. Draw Toolpaths
    g0_plotted = False
    g1_plotted = False
    
    for seg_type, xs, ys, zs in segments:
        if seg_type == 'G0':
            line, = ax.plot(xs, ys, zs, color='red', linestyle=':', linewidth=1.0, alpha=0.5)
            if not g0_plotted:
                line.set_label('Rapid Move (G0)')
                g0_plotted = True
        else:
            line, = ax.plot(xs, ys, zs, color='#1f77b4', linestyle='-', linewidth=1.2, alpha=0.7)
            if not g1_plotted:
                line.set_label('Cutting Feed (G1/G2/G3)')
                g1_plotted = True

    # Graph annotations
    ax.set_title('RoboDrill Toolpath 3D Trajectory (Spot/Drill/Pocket/Tap)', fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel('X (mm)', fontsize=10, labelpad=10)
    ax.set_ylabel('Y (mm)', fontsize=10, labelpad=10)
    ax.set_zlabel('Z (mm)', fontsize=10, labelpad=10)
    
    ax.set_xlim(-10, pw + 10)
    ax.set_ylim(-10, ph + 10)
    ax.set_zlim(-pt - 5, 10.0)
    
    ax.set_box_aspect((pw + 20, ph + 20, pt + 15))
    ax.view_init(elev=30, azim=-60)
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 0.95))
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    plt.savefig(image_path, bbox_inches='tight')
    plt.close()
    print(f"RoboDrill Toolpath image saved to {image_path}")

def build_simulator(gcode_file, html_dest):
    with open(gcode_file, 'r') as f:
        gcode_content = f.read()

    gcode_escaped = gcode_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    # Define HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D CNC G-Code Simulator - RoboDrill / FANUC</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --panel-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-color: #10b981;
            --accent-hover: #059669;
            --text-color: #f1f5f9;
            --text-muted: #94a3b8;
            --glass-blur: blur(12px);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            overflow: hidden;
            height: 100vh;
            display: flex;
        }}

        #app-container {{
            display: flex;
            width: 100%;
            height: 100%;
            position: relative;
        }}

        #canvas-container {{
            flex-grow: 1;
            height: 100%;
            position: relative;
        }}

        canvas {{
            display: block;
            width: 100%;
            height: 100%;
        }}

        #control-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            bottom: 20px;
            width: 380px;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            display: flex;
            flex-direction: column;
            padding: 24px;
            z-index: 10;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}

        h1 {{
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 4px;
            color: #ffffff;
            letter-spacing: -0.025em;
        }}

        .subtitle {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .section {{
            border-top: 1px solid var(--border-color);
            padding: 16px 0;
        }}

        .section-title {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .controls-row {{
            display: flex;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .btn {{
            flex-grow: 1;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: #ffffff;
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}

        .btn:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }}

        .btn-primary {{
            background-color: var(--accent-color);
            color: #000000;
            border: none;
            font-weight: 600;
        }}

        .btn-primary:hover {{
            background-color: var(--accent-hover);
        }}

        .slider-container {{
            margin-bottom: 12px;
        }}

        .slider-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            margin-bottom: 6px;
        }}

        input[type="range"] {{
            width: 100%;
            accent-color: var(--accent-color);
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            height: 6px;
            -webkit-appearance: none;
            outline: none;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px 10px;
        }}

        .stat-val {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #ffffff;
            font-family: monospace;
        }}

        .stat-lbl {{
            font-size: 0.6rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-top: 2px;
        }}

        .toggle-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.85rem;
        }}

        .switch {{
            position: relative;
            display: inline-block;
            width: 38px;
            height: 20px;
        }}

        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.1);
            transition: .3s;
            border-radius: 20px;
            border: 1px solid var(--border-color);
        }}

        .slider:before {{
            position: absolute;
            content: "";
            height: 12px;
            width: 12px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }}

        input:checked + .slider {{
            background-color: var(--accent-color);
        }}

        input:checked + .slider:before {{
            transform: translateX(18px);
        }}

        #gcode-log-container {{
            flex-grow: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.75rem;
            padding: 10px;
            margin-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .log-line {{
            color: var(--text-muted);
            white-space: pre-wrap;
            padding: 2px 4px;
            border-radius: 2px;
        }}

        .log-line.active {{
            background-color: rgba(16, 185, 129, 0.2);
            color: #ffffff;
            font-weight: 600;
        }}

        #axes-legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: var(--panel-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 0.75rem;
            z-index: 10;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .color-box {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div id="app-container">
        <!-- Control Panel -->
        <div id="control-panel">
            <div>
                <h1>RoboDrill Sim</h1>
                <div class="subtitle">Multi-Tool G-Code Simulator</div>
            </div>

            <!-- Playback controls -->
            <div class="section">
                <div class="section-title">シミュレーション制御</div>
                <div class="controls-row">
                    <button class="btn btn-primary" id="btn-play-pause">PLAY</button>
                    <button class="btn" id="btn-reset">RESET</button>
                </div>
                <div class="slider-container">
                    <div class="slider-label">
                        <span>倍速送り</span>
                        <span id="speed-val">10x</span>
                    </div>
                    <input type="range" id="speed-slider" min="1" max="100" value="10">
                </div>
            </div>

            <!-- Real-time Stats -->
            <div class="section">
                <div class="section-title">ステータス (WCS: G54)</div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-val" id="stat-tool">T1</div>
                        <div class="stat-lbl">使用工具 (TOOL)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" id="stat-x">0.000</div>
                        <div class="stat-lbl">X 座標 (mm)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" id="stat-y">0.000</div>
                        <div class="stat-lbl">Y 座標 (mm)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" id="stat-z">5.000</div>
                        <div class="stat-lbl">Z 座標 (mm)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" id="stat-feed">F0</div>
                        <div class="stat-lbl">送り速度</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-val" id="stat-progress">0%</div>
                        <div class="stat-lbl">進行度</div>
                    </div>
                </div>
            </div>

            <!-- Visualization Options -->
            <div class="section">
                <div class="section-title">表示オプション</div>
                <div class="toggle-row">
                    <span>材料 (ワーク) 65x85x10mm</span>
                    <label class="switch">
                        <input type="checkbox" id="toggle-stock" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="toggle-row">
                    <span>切削軌跡 G1/G2/G3 (青)</span>
                    <label class="switch">
                        <input type="checkbox" id="toggle-cut" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="toggle-row">
                    <span>早送り軌跡 G0 (赤)</span>
                    <label class="switch">
                        <input type="checkbox" id="toggle-g0" checked>
                        <span class="slider"></span>
                    </label>
                </div>
            </div>

            <!-- G-code Display -->
            <div class="section" style="flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; padding-bottom: 0;">
                <div class="section-title">実行中のGコード</div>
                <div id="gcode-log-container"></div>
            </div>
        </div>

        <!-- 3D Viewport -->
        <div id="canvas-container"></div>

        <!-- Axes Legend -->
        <div id="axes-legend">
            <div class="legend-item">
                <div class="color-box" style="background-color: #ff4444;"></div>
                <span>X軸 (赤) : 65mm</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background-color: #44ff44;"></div>
                <span>Y軸 (緑) : 85mm</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background-color: #4444ff;"></div>
                <span>Z軸 (青) : 10mm</span>
            </div>
            <div class="legend-item" style="margin-top: 4px; border-top: 1px solid var(--border-color); padding-top: 4px;">
                <span id="tool-legend-name" style="color: #eab308; font-weight: 500;">T1: センタドリル</span>
            </div>
        </div>
    </div>

    <script>
        const RAW_GCODE = `{gcode_escaped}`;

        let scene, camera, renderer, controls;
        let toolMesh, toolCylinder, toolHolder;
        let stockMesh, gridHelper;
        let motions = [];
        let currentMotionIdx = 0;
        let motionProgress = 0.0;
        let isPlaying = false;
        let timeSpeedMultiplier = 10.0;

        let g0PathLines = [];
        let cutPathSegments = [];
        
        let showStock = true;
        let showCutPath = true;
        let showG0Path = true;

        const playPauseBtn = document.getElementById('btn-play-pause');
        const resetBtn = document.getElementById('btn-reset');
        const speedSlider = document.getElementById('speed-slider');
        const speedValLabel = document.getElementById('speed-val');
        const statTool = document.getElementById('stat-tool');
        const statX = document.getElementById('stat-x');
        const statY = document.getElementById('stat-y');
        const statZ = document.getElementById('stat-z');
        const statFeed = document.getElementById('stat-feed');
        const statProgress = document.getElementById('stat-progress');
        const gcodeLogContainer = document.getElementById('gcode-log-container');
        const toolLegendName = document.getElementById('tool-legend-name');

        // Tool geometry maps
        const toolSpecs = {{
            1: {{ name: "T1: センタドリル", rad: 2.0, len: 10, color: 0x93c5fd }},
            5: {{ name: "T5: φ4.2ドリル(M5下穴)", rad: 2.1, len: 25, color: 0x60a5fa }},
            6: {{ name: "T6: φ5.5バカ穴用ドリル", rad: 2.75, len: 25, color: 0x2563eb }},
            14: {{ name: "T14: φ6フラットエンドミル", rad: 3.0, len: 20, color: 0xeab308 }},
            9: {{ name: "T9: M5タップ", rad: 2.5, len: 22, color: 0xa855f7 }}
        }};

        function parseGCode(gcodeText) {{
            const lines = gcodeText.split('\\n');
            let currX = 0.0, currY = 0.0, currZ = 5.0;
            let modalCmd = 1;
            let currFeed = 600.0;
            let currSpindle = 8000;
            let activeTool = 1;
            
            const parsedMotions = [];
            
            let cannedCycle = null;
            let cannedZ = 0.0;
            let cannedR = 2.0;
            let initialZ = 5.0;
            
            for (let i = 0; i < lines.length; i++) {{
                const rawLine = lines[i];
                let clean = rawLine.split(';')[0].split('(')[0].trim().toUpperCase();
                if (!clean || clean.startsWith('%') || clean.startsWith('O') || clean.includes('G28')) {{
                    // Try to catch tool changes
                    if (clean.includes('T') && clean.includes('M6')) {{
                        let tMatch = clean.match(/T([0-9]+)/);
                        if (tMatch) activeTool = parseInt(tMatch[1]);
                    }}
                    continue;
                }}
                
                const matches = clean.match(/([A-Z])([-+]?[0-9]*\\.?[0-9]*)/g);
                if (!matches) continue;
                
                let newX = currX;
                let newY = currY;
                let newZ = currZ;
                let iVal = 0.0;
                let jVal = 0.0;
                let rVal = null;
                
                let hasX = false, hasY = false, hasZ = false, hasI = false, hasJ = false, hasR = false;
                let cmd = null;
                let hasG80 = false;
                
                for (let match of matches) {{
                    let char = match[0];
                    let val = parseFloat(match.slice(1));
                    
                    if (char === 'G') {{
                        if ([0, 1, 2, 3].includes(val)) {{
                            cmd = val;
                            cannedCycle = null;
                        }} else if ([81, 83, 84].includes(val)) {{
                            cannedCycle = 'G' + val;
                        }} else if (val === 80) {{
                            cannedCycle = null;
                            hasG80 = true;
                        }}
                    }} else if (char === 'T') {{
                        activeTool = parseInt(val);
                    }} else if (char === 'X') {{
                        newX = val;
                        hasX = true;
                    }} else if (char === 'Y') {{
                        newY = val;
                        hasY = true;
                    }} else if (char === 'Z') {{
                        newZ = val;
                        hasZ = true;
                    }} else if (char === 'I') {{
                        iVal = val;
                        hasI = true;
                    }} else if (char === 'J') {{
                        jVal = val;
                        hasJ = true;
                    }} else if (char === 'R') {{
                        rVal = val;
                        hasR = true;
                    }} else if (char === 'F') {{
                        currFeed = val;
                    }} else if (char === 'S') {{
                        currSpindle = val;
                    }}
                }}
                
                if (hasG80) continue;
                
                if (cannedCycle !== null) {{
                    if (hasZ) cannedZ = newZ;
                    if (rVal !== null) cannedR = rVal;
                    
                    let tx = hasX ? newX : currX;
                    let ty = hasY ? newY : currY;
                    let shouldDrill = hasX || hasY || clean.includes(cannedCycle);
                    
                    if (shouldDrill) {{
                        // Move to X/Y
                        if (currX !== tx || currY !== ty) {{
                            parsedMotions.push({{
                                type: 'G0',
                                start: {{ x: currX, y: currY, z: currZ }},
                                end: {{ x: tx, y: ty, z: currZ }},
                                feed: 3000,
                                tool: activeTool,
                                lineText: rawLine,
                                lineIndex: i
                            }});
                            currX = tx;
                            currY = ty;
                        }}
                        // Rapid down to R-plane
                        if (currZ > cannedR) {{
                            parsedMotions.push({{
                                type: 'G0',
                                start: {{ x: currX, y: currY, z: currZ }},
                                end: {{ x: currX, y: currY, z: cannedR }},
                                feed: 3000,
                                tool: activeTool,
                                lineText: rawLine,
                                lineIndex: i
                            }});
                            currZ = cannedR;
                        }}
                        // Drill plunge
                        parsedMotions.push({{
                            type: 'G1',
                            start: {{ x: currX, y: currY, z: currZ }},
                            end: {{ x: currX, y: currY, z: cannedZ }},
                            feed: currFeed,
                            tool: activeTool,
                            lineText: rawLine,
                            lineIndex: i
                        }});
                        currZ = cannedZ;
                        // Retract
                        parsedMotions.push({{
                            type: 'G0',
                            start: {{ x: currX, y: currY, z: currZ }},
                            end: {{ x: currX, y: currY, z: initialZ }},
                            feed: 3000,
                            tool: activeTool,
                            lineText: rawLine,
                            lineIndex: i
                        }});
                        currZ = initialZ;
                    }}
                    continue;
                }}
                
                if (cmd !== null) {{
                    modalCmd = cmd;
                }} else if (hasX || hasY || hasZ) {{
                    cmd = modalCmd;
                }} else {{
                    continue;
                }}
                
                if (cmd === 0 || cmd === 1) {{
                    parsedMotions.push({{
                        type: cmd === 0 ? 'G0' : 'G1',
                        start: {{ x: currX, y: currY, z: currZ }},
                        end: {{ x: newX, y: newY, z: newZ }},
                        feed: cmd === 0 ? 3000 : currFeed,
                        tool: activeTool,
                        lineText: rawLine,
                        lineIndex: i
                    }});
                    currX = newX;
                    currY = newY;
                    currZ = newZ;
                }} else if (cmd === 2 || cmd === 3) {{
                    let arcCenterX = currX + iVal;
                    let arcCenterY = currY + jVal;
                    let radius = Math.sqrt(iVal * iVal + jVal * jVal);
                    
                    let thetaStart = Math.atan2(currY - arcCenterY, currX - arcCenterX);
                    let thetaEnd = Math.atan2(newY - arcCenterY, newX - arcCenterX);
                    
                    if (Math.abs(currX - newX) < 1e-4 && Math.abs(currY - newY) < 1e-4) {{
                        if (cmd === 3) {{
                            thetaEnd = thetaStart + 2.0 * Math.PI;
                        }} else {{
                            thetaEnd = thetaStart - 2.0 * Math.PI;
                        }}
                    }} else {{
                        if (cmd === 3) {{
                            if (thetaEnd <= thetaStart) thetaEnd += 2.0 * Math.PI;
                        }} else {{
                            if (thetaEnd >= thetaStart) thetaEnd -= 2.0 * Math.PI;
                        }}
                    }}
                    
                    parsedMotions.push({{
                        type: cmd === 2 ? 'G2' : 'G3',
                        start: {{ x: currX, y: currY, z: currZ }},
                        end: {{ x: newX, y: newY, z: newZ }},
                        arcCenter: {{ x: arcCenterX, y: arcCenterY }},
                        radius: radius,
                        thetaStart: thetaStart,
                        thetaEnd: thetaEnd,
                        feed: currFeed,
                        tool: activeTool,
                        lineText: rawLine,
                        lineIndex: i
                    }});
                    currX = newX;
                    currY = newY;
                    currZ = newZ;
                }}
            }}
            return parsedMotions;
        }}

        function setupLog() {{
            gcodeLogContainer.innerHTML = '';
            motions.forEach((m, index) => {{
                const lineDiv = document.createElement('div');
                lineDiv.className = 'log-line';
                lineDiv.id = `log-line-${{index}}`;
                lineDiv.innerText = `${{m.lineIndex + 1}}: ${{m.lineText.trim()}}`;
                gcodeLogContainer.appendChild(lineDiv);
            }});
        }}

        function scrollLog(idx) {{
            const currentLine = document.getElementById(`log-line-${{idx}}`);
            if (currentLine) {{
                const lines = document.getElementsByClassName('log-line');
                for (let l of lines) l.classList.remove('active');
                currentLine.classList.add('active');
                gcodeLogContainer.scrollTop = currentLine.offsetTop - gcodeLogContainer.offsetTop - 60;
            }}
        }}

        function init3D() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;

            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0f1d);

            camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
            camera.position.set(100, -120, 80);
            camera.up.set(0, 0, 1);

            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(width, height);
            container.appendChild(renderer.domElement);

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(32.5, 42.5, -5);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);

            const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
            dirLight1.position.set(50, -50, 100);
            scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
            dirLight2.position.set(-50, 100, 50);
            scene.add(dirLight2);

            gridHelper = new THREE.GridHelper(200, 40, 0x1e293b, 0x1e293b);
            gridHelper.rotation.x = Math.PI / 2;
            gridHelper.position.set(32.5, 42.5, -10.01);
            scene.add(gridHelper);

            const axesHelper = new THREE.AxesHelper(30);
            axesHelper.position.set(0, 0, 0.05);
            scene.add(axesHelper);

            // Stock
            const pw = 65, ph = 85, pt = 10;
            const stockGeom = new THREE.BoxGeometry(pw, ph, pt);
            const stockMat = new THREE.MeshPhongMaterial({{
                color: 0x94a3b8,
                transparent: true,
                opacity: 0.25,
                shininess: 90,
                side: THREE.DoubleSide
            }});
            stockMesh = new THREE.Mesh(stockGeom, stockMat);
            stockMesh.position.set(pw/2, ph/2, -pt/2);
            scene.add(stockMesh);

            const edges = new THREE.EdgesGeometry(stockGeom);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{ color: 0x475569 }}));
            line.position.set(pw/2, ph/2, -pt/2);
            scene.add(line);

            // Create Tool Group
            toolMesh = new THREE.Group();
            scene.add(toolMesh);
            
            updateToolMesh(1); // Start with T1

            window.addEventListener('resize', onWindowResize);
        }}

        function updateToolMesh(toolNum) {{
            // Remove previous
            while(toolMesh.children.length > 0) {{
                toolMesh.remove(toolMesh.children[0]);
            }}
            
            const spec = toolSpecs[toolNum] || {{ name: "Unknown", rad: 3.0, len: 20, color: 0xcccccc }};
            
            // Tool tip
            const tipGeom = new THREE.CylinderGeometry(spec.rad, spec.rad, spec.len, 16);
            tipGeom.rotateX(Math.PI / 2);
            tipGeom.translate(0, 0, spec.len / 2);
            const tipMat = new THREE.MeshPhongMaterial({{ color: spec.color, shininess: 80 }});
            toolMesh.add(new THREE.Mesh(tipGeom, tipMat));
            
            // Shank
            const shankGeom = new THREE.CylinderGeometry(6, 6, 25, 16);
            shankGeom.rotateX(Math.PI / 2);
            shankGeom.translate(0, 0, spec.len + 12.5);
            const shankMat = new THREE.MeshPhongMaterial({{ color: 0x334155, shininess: 40 }});
            toolMesh.add(new THREE.Mesh(shankGeom, shankMat));
            
            statTool.innerText = `T${{toolNum}}`;
            toolLegendName.innerText = spec.name;
            toolLegendName.style.color = '#' + spec.color.toString(16).padStart(6, '0');
        }}

        function onWindowResize() {{
            const container = document.getElementById('canvas-container');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }}

        function getPosAtProgress(m, progress) {{
            const p = Math.max(0.0, Math.min(1.0, progress));
            if (m.type === 'G0' || m.type === 'G1') {{
                return {{
                    x: m.start.x + (m.end.x - m.start.x) * p,
                    y: m.start.y + (m.end.y - m.start.y) * p,
                    z: m.start.z + (m.end.z - m.start.z) * p
                }};
            }} else if (m.type === 'G2' || m.type === 'G3') {{
                const theta = m.thetaStart + (m.thetaEnd - m.thetaStart) * p;
                const x = m.arcCenter.x + m.radius * Math.cos(theta);
                const y = m.arcCenter.y + m.radius * Math.sin(theta);
                const z = m.start.z + (m.end.z - m.start.z) * p;
                return {{ x, y, z }};
            }}
        }}

        function drawEntireG0Path() {{
            const g0Material = new THREE.LineBasicMaterial({{ color: 0xef4444, linewidth: 1 }});
            motions.forEach(m => {{
                if (m.type === 'G0') {{
                    const points = [
                        new THREE.Vector3(m.start.x, m.start.y, m.start.z),
                        new THREE.Vector3(m.end.x, m.end.y, m.end.z)
                    ];
                    const geom = new THREE.BufferGeometry().setFromPoints(points);
                    const line = new THREE.Line(geom, g0Material);
                    scene.add(line);
                    g0PathLines.push(line);
                }}
            }});
        }}

        function createCutSegment(start, end, type) {{
            const material = new THREE.LineBasicMaterial({{
                color: type === 'G0' ? 0xff4444 : 0x3b82f6,
                linewidth: type === 'G0' ? 1 : 2
            }});
            
            const points = [
                new THREE.Vector3(start.x, start.y, start.z),
                new THREE.Vector3(end.x, end.y, end.z)
            ];
            
            const geom = new THREE.BufferGeometry().setFromPoints(points);
            const line = new THREE.Line(geom, material);
            scene.add(line);
            cutPathSegments.push(line);
        }}

        let lastTime = 0;
        function animate(timestamp) {{
            requestAnimationFrame(animate);

            if (!lastTime) lastTime = timestamp;
            let dt = (timestamp - lastTime) / 1000.0;
            lastTime = timestamp;

            if (isPlaying && motions.length > 0) {{
                const activeMotion = motions[currentMotionIdx];
                updateToolMesh(activeMotion.tool);
                
                let segmentLen = 0;
                if (activeMotion.type === 'G0' || activeMotion.type === 'G1') {{
                    segmentLen = Math.sqrt(
                        Math.pow(activeMotion.end.x - activeMotion.start.x, 2) +
                        Math.pow(activeMotion.end.y - activeMotion.start.y, 2) +
                        Math.pow(activeMotion.end.z - activeMotion.start.z, 2)
                    );
                }} else {{
                    const arcAngle = Math.abs(activeMotion.thetaEnd - activeMotion.thetaStart);
                    const arcLen2D = activeMotion.radius * arcAngle;
                    segmentLen = Math.sqrt(arcLen2D * arcLen2D + Math.pow(activeMotion.end.z - activeMotion.start.z, 2));
                }}

                if (segmentLen < 1e-4) {{
                    currentMotionIdx++;
                    motionProgress = 0.0;
                }} else {{
                    const feedRatePerSec = (activeMotion.feed / 60.0) * timeSpeedMultiplier;
                    const progressDelta = (feedRatePerSec * dt) / segmentLen;
                    
                    const oldPos = getPosAtProgress(activeMotion, motionProgress);
                    motionProgress += progressDelta;
                    
                    if (motionProgress >= 1.0) {{
                        const finalPos = activeMotion.end;
                        if (activeMotion.type !== 'G0') {{
                            createCutSegment(oldPos, finalPos, activeMotion.type);
                        }}
                        
                        currentMotionIdx++;
                        motionProgress = 0.0;
                        
                        if (currentMotionIdx >= motions.length) {{
                            isPlaying = false;
                            playPauseBtn.innerText = 'PLAY';
                            currentMotionIdx = motions.length - 1;
                            motionProgress = 1.0;
                        }} else {{
                            scrollLog(currentMotionIdx);
                        }}
                    }} else {{
                        const newPos = getPosAtProgress(activeMotion, motionProgress);
                        if (activeMotion.type !== 'G0') {{
                            createCutSegment(oldPos, newPos, activeMotion.type);
                        }}
                    }}
                }}

                const activeM = motions[currentMotionIdx];
                const currentPos = getPosAtProgress(activeM, motionProgress);
                
                toolMesh.position.set(currentPos.x, currentPos.y, currentPos.z);
                
                statX.innerText = currentPos.x.toFixed(3);
                statY.innerText = currentPos.y.toFixed(3);
                statZ.innerText = currentPos.z.toFixed(3);
                statFeed.innerText = `F${{activeM.feed.toFixed(0)}}`;
                statProgress.innerText = `${{Math.round((currentMotionIdx / motions.length) * 100)}}%`;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        function initPlaybackControls() {{
            playPauseBtn.addEventListener('click', () => {{
                if (motions.length === 0) return;
                isPlaying = !isPlaying;
                playPauseBtn.innerText = isPlaying ? 'PAUSE' : 'PLAY';
                if (isPlaying) {{
                    scrollLog(currentMotionIdx);
                }}
            }});

            resetBtn.addEventListener('click', () => {{
                isPlaying = false;
                playPauseBtn.innerText = 'PLAY';
                currentMotionIdx = 0;
                motionProgress = 0.0;
                
                if (motions.length > 0) {{
                    const startPos = motions[0].start;
                    toolMesh.position.set(startPos.x, startPos.y, startPos.z);
                    updateToolMesh(motions[0].tool);
                    statX.innerText = startPos.x.toFixed(3);
                    statY.innerText = startPos.y.toFixed(3);
                    statZ.innerText = startPos.z.toFixed(3);
                    statFeed.innerText = 'F0';
                }}
                
                cutPathSegments.forEach(seg => scene.remove(seg));
                cutPathSegments = [];
                
                scrollLog(0);
                statProgress.innerText = `0%`;
            }});

            speedSlider.addEventListener('input', (e) => {{
                const val = parseInt(e.target.value);
                timeSpeedMultiplier = val;
                speedValLabel.innerText = `${{val}}x`;
            }});

            document.getElementById('toggle-stock').addEventListener('change', (e) => {{
                stockMesh.visible = e.target.checked;
            }});

            document.getElementById('toggle-cut').addEventListener('change', (e) => {{
                cutPathSegments.forEach(seg => seg.visible = e.target.checked);
                showCutPath = e.target.checked;
            }});

            document.getElementById('toggle-g0').addEventListener('change', (e) => {{
                g0PathLines.forEach(line => line.visible = e.target.checked);
                showG0Path = e.target.checked;
            }});
        }}

        window.onload = () => {{
            motions = parseGCode(RAW_GCODE);
            init3D();
            drawEntireG0Path();
            setupLog();
            initPlaybackControls();
            
            if (motions.length > 0) {{
                const startPos = motions[0].start;
                toolMesh.position.set(startPos.x, startPos.y, startPos.z);
                updateToolMesh(motions[0].tool);
            }}

            requestAnimationFrame(animate);
        }};
    </script>
</body>
</html>
"""

    with open(html_dest, 'w') as f:
        f.write(html_template)
    print(f"Simulator HTML successfully written to {html_dest}")

def main():
    gcode_file = generate_gcode()
    
    artifact_dir = "/Users/hiro/.gemini/antigravity/brain/c03c5648-e4cd-4777-b72a-b5e2572805e9"
    image_path = os.path.join(artifact_dir, "toolpath_robodrill_3d.png")
    
    # Generate 3D plot
    parse_gcode_and_plot(gcode_file, image_path)
    
    # Generate 3D HTML simulator
    html_dest = "simulator_robodrill.html"
    build_simulator(gcode_file, html_dest)
    
    # Copy both files to artifact directory
    shutil.copy(gcode_file, os.path.join(artifact_dir, "plate_robodrill.gcode"))
    shutil.copy(html_dest, os.path.join(artifact_dir, "simulator_robodrill.html"))
    print("Files successfully copied to artifacts.")

if __name__ == "__main__":
    main()
