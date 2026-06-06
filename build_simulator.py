import os
import shutil

def build():
    gcode_path = "/Users/hiro/.gemini/antigravity/scratch/cnc_gcode/plate_machining.gcode"
    html_dest = "/Users/hiro/.gemini/antigravity/scratch/cnc_gcode/simulator.html"
    artifact_dest = "/Users/hiro/.gemini/antigravity/brain/c03c5648-e4cd-4777-b72a-b5e2572805e9/simulator.html"
    
    if not os.path.exists(gcode_path):
        print(f"Error: G-code file not found at {gcode_path}")
        return

    with open(gcode_path, 'r') as f:
        gcode_content = f.read()

    # Escape G-code for JavaScript string literal injection
    gcode_escaped = gcode_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D CNC G-Code Simulator - Iwashita NV2 / FANUC</title>
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

        /* 3D Viewport */
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

        /* Side Panel (Glassmorphic) */
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

        /* Playback Controls */
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

        /* Sliders */
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

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px;
        }}

        .stat-val {{
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
            font-family: monospace;
        }}

        .stat-lbl {{
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-top: 2px;
        }}

        /* Toggles */
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

        /* G-code Viewer Log */
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

        /* Legend & Helpers */
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
                <h1>Iwashita NV2 Sim</h1>
                <div class="subtitle">FANUC G-Code 3D Simulator</div>
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
                    <div class="stat-card" style="grid-column: span 2;">
                        <div class="stat-val" id="stat-progress">0% (0/0)</div>
                        <div class="stat-lbl">プログラム進行度</div>
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
                    <span>削った切削軌跡 (青)</span>
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
                <span>X軸 (赤) : 左右移動 (65mm)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background-color: #44ff44;"></div>
                <span>Y軸 (緑) : 前後移動 (85mm)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background-color: #4444ff;"></div>
                <span>Z軸 (青) : 上下移動 (10mm)</span>
            </div>
            <div class="legend-item" style="margin-top: 4px; border-top: 1px solid var(--border-color); padding-top: 4px;">
                <div class="color-box" style="background-color: #10b981;"></div>
                <span>削り刃物 : φ4.2mm フラットエンドミル</span>
            </div>
        </div>
    </div>

    <!-- Embedding the G-Code in script -->
    <script>
        const RAW_GCODE = `{gcode_escaped}`;

        // Global simulation variables
        let scene, camera, renderer, controls;
        let toolMesh, stockMesh, gridHelper;
        let motions = [];
        let currentMotionIdx = 0;
        let motionProgress = 0.0; // 0.0 to 1.0 within the current motion
        let isPlaying = false;
        let timeSpeedMultiplier = 10.0; // Slider speed multiplier

        // Paths
        let g0PathLines = [];
        let cutPathSegments = [];
        
        // Settings toggles
        let showStock = true;
        let showCutPath = true;
        let showG0Path = true;

        // UI references
        const playPauseBtn = document.getElementById('btn-play-pause');
        const resetBtn = document.getElementById('btn-reset');
        const speedSlider = document.getElementById('speed-slider');
        const speedValLabel = document.getElementById('speed-val');
        const statX = document.getElementById('stat-x');
        const statY = document.getElementById('stat-y');
        const statZ = document.getElementById('stat-z');
        const statFeed = document.getElementById('stat-feed');
        const statProgress = document.getElementById('stat-progress');
        const gcodeLogContainer = document.getElementById('gcode-log-container');

        // Parser
        function parseGCode(gcodeText) {{
            const lines = gcodeText.split('\\n');
            let currX = 0.0, currY = 0.0, currZ = 0.0;
            let modalCmd = 1; // Default G1
            let currFeed = 600.0;
            let currSpindle = 8000;
            
            const parsedMotions = [];
            
            for (let i = 0; i < lines.length; i++) {{
                const rawLine = lines[i];
                let clean = rawLine.split(';')[0].split('(')[0].trim().toUpperCase();
                if (!clean || clean.startsWith('%') || clean.startsWith('O') || clean.includes('G28')) {{
                    continue; // Skip comments and homing moves for simplified animation
                }}
                
                const matches = clean.match(/([A-Z])([-+]?[0-9]*\\.?[0-9]*)/g);
                if (!matches) continue;
                
                let newX = currX;
                let newY = currY;
                let newZ = currZ;
                let iVal = 0.0;
                let jVal = 0.0;
                let hasX = false, hasY = false, hasZ = false, hasI = false, hasJ = false;
                let cmd = null;
                
                for (let match of matches) {{
                    let char = match[0];
                    let val = parseFloat(match.slice(1));
                    
                    if (char === 'G') {{
                        if ([0, 1, 2, 3].includes(val)) {{
                            cmd = val;
                        }}
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
                    }} else if (char === 'F') {{
                        currFeed = val;
                    }} else if (char === 'S') {{
                        currSpindle = val;
                    }}
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
                        spindle: currSpindle,
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
                        if (cmd === 3) {{ // CCW
                            thetaEnd = thetaStart + 2.0 * Math.PI;
                        }} else {{ // CW
                            thetaEnd = thetaStart - 2.0 * Math.PI;
                        }}
                    }} else {{
                        if (cmd === 3) {{ // CCW
                            if (thetaEnd <= thetaStart) thetaEnd += 2.0 * Math.PI;
                        }} else {{ // CW
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
                        spindle: currSpindle,
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

        // Setup G-Code log scroll
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
                
                // Scroll container
                gcodeLogContainer.scrollTop = currentLine.offsetTop - gcodeLogContainer.offsetTop - 60;
            }}
        }}

        // Initialize 3D Scene
        function init3D() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;

            // Scene & Camera
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0f1d);

            camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
            camera.position.set(100, -120, 80);
            camera.up.set(0, 0, 1); // Z is UP

            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(width, height);
            container.appendChild(renderer.domElement);

            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(32.5, 42.5, -5);

            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);

            const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
            dirLight1.position.set(50, -50, 100);
            scene.add(dirLight1);

            const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
            dirLight2.position.set(-50, 100, 50);
            scene.add(dirLight2);

            // Grid & Axes Helpers
            gridHelper = new THREE.GridHelper(200, 40, 0x1e293b, 0x1e293b);
            gridHelper.rotation.x = Math.PI / 2; // Lie flat on XY
            gridHelper.position.set(32.5, 42.5, -10.01);
            scene.add(gridHelper);

            const axesHelper = new THREE.AxesHelper(30);
            axesHelper.position.set(0, 0, 0.05);
            scene.add(axesHelper);

            // Stock Plate (65x85x10mm, semitransparent)
            const pw = 65, ph = 85, pt = 10;
            const stockGeom = new THREE.BoxGeometry(pw, ph, pt);
            const stockMat = new THREE.MeshPhongMaterial({{
                color: 0x94a3b8,
                transparent: true,
                opacity: 0.25,
                wireframe: false,
                shininess: 90,
                side: THREE.DoubleSide
            }});
            stockMesh = new THREE.Mesh(stockGeom, stockMat);
            // Box origin is center. We shift it so origin is bottom-left top surface
            stockMesh.position.set(pw/2, ph/2, -pt/2);
            scene.add(stockMesh);

            // Draw Stock Borders
            const edges = new THREE.EdgesGeometry(stockGeom);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{ color: 0x475569 }}));
            line.position.set(pw/2, ph/2, -pt/2);
            scene.add(line);

            // Tool (4.2mm Cylinder)
            const toolGeom = new THREE.CylinderGeometry(2.1, 2.1, 20, 16);
            toolGeom.rotateX(Math.PI / 2); // Make it align vertically
            toolGeom.translate(0, 0, 10); // Offset origin to bottom tip of cutter
            const toolMat = new THREE.MeshPhongMaterial({{ color: 0xeab308, shininess: 80 }}); // Gold tip
            
            // Tool Holder
            const holderGeom = new THREE.CylinderGeometry(6, 6, 25, 16);
            holderGeom.rotateX(Math.PI / 2);
            holderGeom.translate(0, 0, 32.5); // Shank/Holder offset
            const holderMat = new THREE.MeshPhongMaterial({{ color: 0x334155, shininess: 40 }}); // Metal shank
            
            toolMesh = new THREE.Group();
            toolMesh.add(new THREE.Mesh(toolGeom, toolMat));
            toolMesh.add(new THREE.Mesh(holderGeom, holderMat));
            toolMesh.position.set(0, 0, 5); // Start at Z5.0
            scene.add(toolMesh);

            window.addEventListener('resize', onWindowResize);
        }}

        function onWindowResize() {{
            const container = document.getElementById('canvas-container');
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }}

        // Calculate motion segment interpolation
        function getPosAtProgress(m, progress) {{
            const p = Math.max(0.0, Math.min(1.0, progress));
            if (m.type === 'G0' || m.type === 'G1') {{
                // Linear interpolation
                return {{
                    x: m.start.x + (m.end.x - m.start.x) * p,
                    y: m.start.y + (m.end.y - m.start.y) * p,
                    z: m.start.z + (m.end.z - m.start.z) * p
                }};
            }} else if (m.type === 'G2' || m.type === 'G3') {{
                // Arc interpolation
                const theta = m.thetaStart + (m.thetaEnd - m.thetaStart) * p;
                const x = m.arcCenter.x + m.radius * Math.cos(theta);
                const y = m.arcCenter.y + m.radius * Math.sin(theta);
                const z = m.start.z + (m.end.z - m.start.z) * p;
                return {{ x, y, z }};
            }}
        }}

        // Pre-build and draw complete rapid lines (G0)
        function drawEntireG0Path() {{
            const g0Material = new THREE.LineBasicMaterial({{ color: 0xef4444, linewidth: 1 }}); // Red dashed
            motions.forEach(m => {{
                if (m.type === 'G0') {{
                    const points = [];
                    points.push(new THREE.Vector3(m.start.x, m.start.y, m.start.z));
                    points.push(new THREE.Vector3(m.end.x, m.end.y, m.end.z));
                    
                    const geom = new THREE.BufferGeometry().setFromPoints(points);
                    const line = new THREE.Line(geom, g0Material);
                    scene.add(line);
                    g0PathLines.push(line);
                }}
            }});
        }}

        // Setup real-time cut path segment
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

        // Animation main loop
        let lastTime = 0;
        function animate(timestamp) {{
            requestAnimationFrame(animate);

            if (!lastTime) lastTime = timestamp;
            let dt = (timestamp - lastTime) / 1000.0; // In seconds
            lastTime = timestamp;

            if (isPlaying && motions.length > 0) {{
                const activeMotion = motions[currentMotionIdx];
                
                // Calculate physical segment length
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

                // Avoid division by zero for empty movements
                if (segmentLen < 1e-4) {{
                    currentMotionIdx++;
                    motionProgress = 0.0;
                }} else {{
                    // Feed is in mm/minute -> mm/second
                    const feedRatePerSec = (activeMotion.feed / 60.0) * timeSpeedMultiplier;
                    const progressDelta = (feedRatePerSec * dt) / segmentLen;
                    
                    const oldPos = getPosAtProgress(activeMotion, motionProgress);
                    motionProgress += progressDelta;
                    
                    if (motionProgress >= 1.0) {{
                        const finalPos = activeMotion.end;
                        // Draw final path segment
                        if (activeMotion.type !== 'G0') {{
                            createCutSegment(oldPos, finalPos, activeMotion.type);
                        }}
                        
                        // Next motion
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

                // Update UI state
                const activeM = motions[currentMotionIdx];
                const currentPos = getPosAtProgress(activeM, motionProgress);
                
                toolMesh.position.set(currentPos.x, currentPos.y, currentPos.z);
                
                // Update coordinates
                statX.innerText = currentPos.x.toFixed(3);
                statY.innerText = currentPos.y.toFixed(3);
                statZ.innerText = currentPos.z.toFixed(3);
                statFeed.innerText = `F${{activeM.feed.toFixed(0)}}`;
                statProgress.innerText = `${{Math.round((currentMotionIdx / motions.length) * 100)}}% (${{currentMotionIdx}}/${{motions.length}})`;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        // Setup Controls
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
                
                // Reset tool mesh
                if (motions.length > 0) {{
                    const startPos = motions[0].start;
                    toolMesh.position.set(startPos.x, startPos.y, startPos.z);
                    statX.innerText = startPos.x.toFixed(3);
                    statY.innerText = startPos.y.toFixed(3);
                    statZ.innerText = startPos.z.toFixed(3);
                    statFeed.innerText = 'F0';
                }}
                
                // Clear dynamic cuts
                cutPathSegments.forEach(seg => scene.remove(seg));
                cutPathSegments = [];
                
                scrollLog(0);
                statProgress.innerText = `0% (0/${{motions.length}})`;
            }});

            speedSlider.addEventListener('input', (e) => {{
                const val = parseInt(e.target.value);
                timeSpeedMultiplier = val;
                speedValLabel.innerText = `${{val}}x`;
            }});

            // Vis Options
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

        // Main App entry point
        window.onload = () => {{
            motions = parseGCode(RAW_GCODE);
            init3D();
            drawEntireG0Path();
            setupLog();
            initPlaybackControls();
            
            // Set initial tool position
            if (motions.length > 0) {{
                const startPos = motions[0].start;
                toolMesh.position.set(startPos.x, startPos.y, startPos.z);
            }}

            // Start loop
            requestAnimationFrame(animate);
        }};
    </script>
</body>
</html>
"""

    with open(html_dest, 'w') as f:
        f.write(html_template)
    print(f"Simulator HTML successfully written to {html_dest}")

    # Copy to artifact folder
    os.makedirs(os.path.dirname(artifact_dest), exist_ok=True)
    shutil.copy(html_dest, artifact_dest)
    print(f"Simulator HTML successfully copied to artifacts: {artifact_dest}")

if __name__ == "__main__":
    build()
