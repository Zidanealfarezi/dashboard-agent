(() => {
  'use strict';
  let instance;

  const layout = [
    { id: 'pm', floor: 1, x: -7.5, z: -7.2, w: 14.2, d: 8.6, label: 'MANAJEMEN & PRODUKSI', accent: 0xb29d82 },
    { id: 'researcher', floor: 1, x: 7.5, z: -7.2, w: 14.2, d: 8.6, label: 'RISET PASAR & ANALISIS', accent: 0x4f9aa8 },
    { id: 'sales', floor: 1, x: -7.5, z: 6.8, w: 14.2, d: 8.4, label: 'SALES & KEMITRAAN ISK', accent: 0xd97736 },
    { id: 'default', floor: 1, x: 7.5, z: 6.8, w: 14.2, d: 8.4, label: 'HERMES AUTOMATION ENGINE', accent: 0x3f9e6b },
    { id: 'dinda', floor: 2, x: -9.8, z: -6.4, w: 9.4, d: 9.4, label: 'STUDIO DINDA KEMALA', accent: 0xd06b52 },
    { id: 'nara', floor: 2, x: 0, z: -6.4, w: 9.4, d: 9.4, label: 'STUDIO NARA SENJA', accent: 0x4f9aa8 },
    { id: 'rania', floor: 2, x: 9.8, z: -6.4, w: 9.4, d: 9.4, label: 'STUDIO RANIA PUTRI', accent: 0x8b65a4 }
  ];

  const floorNames = { 1: 'Lantai 1 · Operasional & Bisnis', 2: 'Lantai 2 · Studio Talenta AI' };

  function createOffice(container) {
    const T = window.THREE;
    if (!T || !T.OrbitControls) throw new Error('local_3d_assets_unavailable');

    const scene = new T.Scene();
    
    // Warm, cozy team.ai.id isometric background
    const bgHex = 0xefe6d2;
    scene.background = new T.Color(bgHex);

    const aspect = container.clientWidth / container.clientHeight || 1;
    const frustum = 28;
    const camera = new T.OrthographicCamera(
      (-frustum * aspect) / 2,
      (frustum * aspect) / 2,
      frustum / 2,
      -frustum / 2,
      0.1,
      350
    );

    // Standard Isometric angle (like team.ai.id)
    const isometricPosition = new T.Vector3(29, 38, 45);
    camera.position.copy(isometricPosition);
    camera.lookAt(0, 1.2, 0);

    const renderer = new T.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = T.PCFSoftShadowMap;
    renderer.domElement.setAttribute('aria-label', 'Kantor 3D Interaktif Tim AI');
    renderer.domElement.setAttribute('role', 'img');
    container.prepend(renderer.domElement);
    const loading = container.querySelector('.scene-loading');
    if (loading) loading.hidden = true;

    const controls = new T.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enablePan = true;
    controls.minPolarAngle = Math.PI * 0.15;
    controls.maxPolarAngle = Math.PI * 0.44;
    controls.minZoom = 0.6;
    controls.maxZoom = 3.8;
    controls.target.set(0, 1.2, 0);
    controls.screenSpacePanning = true;
    controls.rotateSpeed = 0.55;
    controls.zoomSpeed = 0.8;

    const office = new T.Group();
    scene.add(office);

    const levels = { 1: new T.Group(), 2: new T.Group() };
    office.add(levels[1], levels[2]);
    levels[2].visible = false;

    let dirty = true, tween = null, selected = 'sales', agents = [], visible = true, activeFloor = 1, topView = false;
    const rooms = new Map();
    const raycaster = new T.Raycaster(), pointer = new T.Vector2();
    const hitMeshes = { 1: [], 2: [] };
    const animatedPersons = [];

    const tooltip = container.querySelector('.scene-tooltip');
    const labels = container.querySelector('.scene-labels');
    const frameElement = container.closest('.scene-frame');
    const floorButtons = frameElement ? [...frameElement.querySelectorAll('[data-office-floor]')] : [];
    const viewButtons = frameElement ? [...frameElement.querySelectorAll('[data-office-view]')] : [];
    const projected = new T.Vector3();
    const clock = new T.Clock();

    // Reusable Materials Palette (Cozy team.ai.id Scandinavian tones)
    const materials = {};
    const mat = (key, color, options = {}) => {
      if (materials[key]) return materials[key];
      const m = new T.MeshStandardMaterial({ color, roughness: 0.75, ...options });
      materials[key] = m;
      return m;
    };

    const wallMat = mat('wall', 0xfcfbf7, { roughness: 0.85 });
    const wallBase = mat('wallBase', 0xd6cbb5);
    const frameMat = mat('frame', 0x5a6568, { roughness: 0.4, metalness: 0.3 });
    const woodLight = mat('woodLight', 0xecdcc4, { roughness: 0.65 });
    const woodWarm = mat('woodWarm', 0xc5a880, { roughness: 0.7 });
    const woodDark = mat('woodDark', 0x5a4430, { roughness: 0.8 });
    const glassMat = mat('glass', 0xcbe4ec, { transparent: true, opacity: 0.28, roughness: 0.1, metalness: 0.05, depthWrite: false });
    const screenMat = mat('screenGlow', 0x1a2228, { emissive: 0x5dade2, emissiveIntensity: 0.45, roughness: 0.3 });
    const metalDark = mat('metalDark', 0x2d3436, { roughness: 0.5, metalness: 0.6 });
    const metalChrome = mat('metalChrome', 0xdfe6e9, { roughness: 0.2, metalness: 0.8 });
    const chairBlack = mat('chairBlack', 0x222629, { roughness: 0.85 });
    const plantGreen = mat('plantGreen', 0x4e8d53, { roughness: 0.6 });
    const potMat = mat('potWhite', 0xf0ece1, { roughness: 0.7 });
    const serverGlow = mat('serverLED', 0x11161a, { emissive: 0x2ecc71, emissiveIntensity: 0.65 });
    const sofaCoral = mat('sofaCoral', 0xd9534f, { roughness: 0.85 });
    const poufTeal = mat('poufTeal', 0x4f9aa8, { roughness: 0.85 });
    const skinTone = mat('skinTone', 0xf3d2b8, { roughness: 0.6 });
    const hairDark = mat('hairDark', 0x2c2621, { roughness: 0.9 });
    const hairBrown = mat('hairBrown', 0x5c3d28, { roughness: 0.9 });

    function box(parent, w, h, d, x, y, z, material, shadow = true) {
      const mesh = new T.Mesh(new T.BoxGeometry(w, h, d), material);
      mesh.position.set(x, y, z);
      mesh.castShadow = shadow;
      mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    }

    function cylinder(parent, r1, r2, h, x, y, z, material, segments = 12) {
      const mesh = new T.Mesh(new T.CylinderGeometry(r1, r2, h, segments), material);
      mesh.position.set(x, y, z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    }

    function sphere(parent, r, x, y, z, material, sx = 1, sy = 1, sz = 1) {
      const mesh = new T.Mesh(new T.SphereGeometry(r, 12, 10), material);
      mesh.position.set(x, y, z);
      mesh.scale.set(sx, sy, sz);
      mesh.castShadow = true;
      parent.add(mesh);
      return mesh;
    }

    // Procedural Warm Grid Ground Texture
    function createGroundGrid() {
      const cv = document.createElement('canvas');
      cv.width = 512;
      cv.height = 512;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = '#efe6d2';
      ctx.fillRect(0, 0, 512, 512);

      ctx.strokeStyle = '#d9cfb4';
      ctx.lineWidth = 1;
      const step = 32;
      for (let i = 0; i <= 512; i += step) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, 512);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(512, i);
        ctx.stroke();
      }
      const tex = new T.CanvasTexture(cv);
      tex.wrapS = tex.wrapT = T.RepeatWrapping;
      tex.repeat.set(6, 6);
      return tex;
    }

    // Modern Lighting: Soft ambient + crisp warm sun
    scene.add(new T.HemisphereLight(0xfffbf2, 0xd4cbb7, 0.75));
    const sun = new T.DirectionalLight(0xfff3db, 1.15);
    sun.position.set(-25, 42, 22);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 26, bottom: -26, near: 1, far: 110 });
    sun.shadow.bias = -0.0003;
    sun.shadow.radius = 2.5;
    scene.add(sun);

    const fillLight = new T.DirectionalLight(0xdbe6ed, 0.35);
    fillLight.position.set(24, 20, -18);
    scene.add(fillLight);

    // Big Ground Plane
    const groundMat = new T.MeshStandardMaterial({ map: createGroundGrid(), roughness: 0.9 });
    const ground = new T.Mesh(new T.PlaneGeometry(160, 160), groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.receiveShadow = true;
    scene.add(ground);

    // Slab Podium for the Office Building
    box(office, 32.4, 0.6, 26.4, 0, -0.3, 0, woodDark);
    box(office, 32.0, 0.1, 26.0, 0, 0.05, 0, mat('officeFloor', 0xf5eedb, { roughness: 0.8 }));

    // Reusable Detailed Assets
    function createPlant(parent, x, z, s = 1) {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.scale.setScalar(s);
      parent.add(g);
      cylinder(g, 0.4, 0.3, 0.7, 0, 0.35, 0, potMat);
      cylinder(g, 0.36, 0.36, 0.05, 0, 0.68, 0, woodDark);
      cylinder(g, 0.04, 0.04, 1.2, 0, 1.2, 0, plantGreen, 6);
      for (let i = 0; i < 6; i++) {
        const a = i * 1.05;
        const leaf = sphere(g, 0.38, Math.sin(a) * 0.32, 1.1 + i * 0.14, Math.cos(a) * 0.32, plantGreen, 0.8, 1.3, 0.25);
        leaf.rotation.set(Math.sin(a) * 0.4, a, Math.cos(a) * 0.4);
      }
    }

    function createSwivelChair(parent, x, z, rotY = 0) {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.rotation.y = rotY;
      parent.add(g);
      // Wheels base
      cylinder(g, 0.42, 0.42, 0.05, 0, 0.12, 0, metalChrome, 6);
      cylinder(g, 0.06, 0.06, 0.55, 0, 0.4, 0, metalChrome, 8);
      // Seat cushion
      box(g, 0.82, 0.12, 0.82, 0, 0.72, 0, chairBlack);
      // Ergonomic Backrest
      box(g, 0.76, 0.85, 0.12, 0, 1.18, 0.38, chairBlack);
      // Armrests
      for (const side of [-0.42, 0.42]) {
        box(g, 0.08, 0.35, 0.45, side, 0.95, 0.05, metalDark);
      }
      return g;
    }

    function createAgentCharacter(parent, x, z, shirtColor, hairType = 'dark', facingZ = -1) {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.rotation.y = facingZ > 0 ? 0 : Math.PI;
      parent.add(g);

      const shirtMat = mat('shirt_' + shirtColor, shirtColor, { roughness: 0.7 });
      const hMat = hairType === 'brown' ? hairBrown : hairDark;

      // Sitting legs
      box(g, 0.22, 0.22, 0.55, -0.2, 0.76, -0.24, metalDark);
      box(g, 0.22, 0.22, 0.55, 0.2, 0.76, -0.24, metalDark);
      box(g, 0.18, 0.52, 0.18, -0.2, 0.48, -0.46, metalDark);
      box(g, 0.18, 0.52, 0.18, 0.2, 0.48, -0.46, metalDark);

      // Torso in polo shirt
      cylinder(g, 0.3, 0.36, 0.65, 0, 1.15, 0, shirtMat);
      // Collar detail
      box(g, 0.36, 0.06, 0.2, 0, 1.48, 0.08, shirtMat);

      // Head & Hair
      const head = sphere(g, 0.28, 0, 1.76, 0, skinTone, 1, 1.05, 1);
      sphere(g, 0.27, 0, 1.88, 0.02, hMat, 1.04, 0.7, 1.05);

      // Arms on keyboard
      const leftArm = box(g, 0.13, 0.52, 0.13, -0.38, 1.12, -0.15, shirtMat);
      leftArm.rotation.x = -0.55;
      const rightArm = box(g, 0.13, 0.52, 0.13, 0.38, 1.12, -0.15, shirtMat);
      rightArm.rotation.x = -0.55;

      // Small hands
      sphere(g, 0.08, -0.35, 0.94, -0.38, skinTone);
      sphere(g, 0.08, 0.35, 0.94, -0.38, skinTone);

      animatedPersons.push({ group: g, baseY: 0, speed: 2 + Math.random() });
      return g;
    }

    // Modular Workstation Pod (Desk + Monitor + Keyboard + Accessories)
    function createDesk(parent, x, z, agentId, agentName, shirtColor, facing = 1) {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.rotation.y = facing === 1 ? 0 : Math.PI;
      g.userData = { agentId, agentName };
      parent.add(g);

      // Wooden Desktop
      box(g, 3.2, 0.12, 1.6, 0, 1.35, 0, woodLight);
      // Modern Metal T-frame Legs
      box(g, 0.08, 1.3, 1.4, -1.45, 0.68, 0, metalDark);
      box(g, 0.08, 1.3, 1.4, 1.45, 0.68, 0, metalDark);
      box(g, 2.8, 0.08, 0.08, 0, 0.85, 0, metalDark);

      // PC Monitor with Glowing Screen
      box(g, 1.25, 0.75, 0.06, 0, 1.95, -0.42, metalDark);
      box(g, 1.16, 0.66, 0.02, 0, 1.95, -0.39, screenMat);
      cylinder(g, 0.04, 0.04, 0.32, 0, 1.55, -0.42, metalDark);
      box(g, 0.45, 0.03, 0.35, 0, 1.42, -0.42, metalDark);

      // Keyboard & Mouse
      box(g, 0.75, 0.03, 0.26, -0.05, 1.42, 0.25, mat('kb', 0xdadada));
      box(g, 0.12, 0.025, 0.18, 0.55, 1.42, 0.25, metalDark);
      // Desk pad
      box(g, 1.6, 0.015, 0.7, 0.1, 1.41, 0.22, mat('pad', 0x3a4245));

      // Accessories: Mug & File Pedestal
      cylinder(g, 0.09, 0.08, 0.2, -1.05, 1.52, 0.35, mat('mug', 0xffffff));
      box(g, 0.85, 0.85, 1.2, 1.0, 0.45, 0, woodWarm);
      box(g, 0.86, 0.04, 0.04, 1.0, 0.65, 0.58, metalDark);

      // Swivel Chair
      createSwivelChair(g, 0, 1.15, 0);

      // Agent Sitting
      createAgentCharacter(g, 0, 1.05, shirtColor, 'dark', 1);

      // Register click hit area
      const hitBox = new T.Mesh(new T.BoxGeometry(3.4, 2.4, 2.6), new T.MeshBasicMaterial({ visible: false }));
      hitBox.position.set(0, 1.2, 0.2);
      hitBox.userData = { agentId, agentName, deskGroup: g };
      g.add(hitBox);

      return g;
    }

    // Glass Partition Wall with Frames
    function createGlassWall(parent, x, z, len, rotY = 0) {
      const g = new T.Group();
      g.position.set(x, 0, z);
      g.rotation.y = rotY;
      parent.add(g);

      box(g, len, 0.25, 0.12, 0, 0.12, 0, wallBase);
      box(g, len, 1.6, 0.04, 0, 1.05, 0, glassMat, false);
      box(g, len, 0.08, 0.1, 0, 1.88, 0, frameMat, false);
      for (const pos of [-len / 2, 0, len / 2]) {
        box(g, 0.08, 1.8, 0.1, pos, 0.95, 0, frameMat, false);
      }
    }

    // Modern Signboard Hanging over Rooms
    function createRoomSign(parent, text, w, x, z, rotY = 0) {
      const cv = document.createElement('canvas');
      cv.width = 512;
      cv.height = 110;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, 512, 110);
      ctx.strokeStyle = '#2d3436';
      ctx.lineWidth = 4;
      ctx.strokeRect(4, 4, 504, 102);

      ctx.fillStyle = '#2d3436';
      ctx.font = 'bold 38px "Quicksand", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 256, 55);

      const tex = new T.CanvasTexture(cv);
      const mesh = new T.Mesh(new T.PlaneGeometry(w, 0.65), new T.MeshBasicMaterial({ map: tex, side: T.DoubleSide }));
      mesh.position.set(x, 2.55, z);
      mesh.rotation.y = rotY;
      parent.add(mesh);
    }

    // ==========================================
    // BUILD LANTAI 1: OPERASIONAL & BISNIS ISK
    // ==========================================
    const L1 = levels[1];

    // Corridors & Perimeter Walls
    createGlassWall(L1, 0, -2.8, 30, 0); // Main hallway horizontal
    createGlassWall(L1, 0, 11.2, 30, 0);
    createGlassWall(L1, -15.2, 0, 24, Math.PI / 2);
    createGlassWall(L1, 15.2, 0, 24, Math.PI / 2);
    createGlassWall(L1, 0, -7.4, 9, Math.PI / 2); // Center divider north
    createGlassWall(L1, 0, 6.8, 8.4, Math.PI / 2); // Center divider south

    // Room Signboards
    createRoomSign(L1, 'MANAJEMEN & PRODUKSI ISK', 5.8, -7.5, -2.75);
    createRoomSign(L1, 'RISET PASAR & ANALISIS', 5.8, 7.5, -2.75);
    createRoomSign(L1, 'SALES & KEMITRAAN TOKO', 5.8, -7.5, 2.65);
    createRoomSign(L1, 'HERMES AUTOMATION ENGINE', 6.2, 7.5, 2.65);

    // 1. RUANG PRODUKSI & MANAJEMEN (North-West)
    const pmDesk = createDesk(L1, -7.5, -7.2, 'pm', 'PM Intan', 0x2c3e50);
    hitMeshes[1].push(pmDesk.children[pmDesk.children.length - 1]);
    // Assistant / Brand Specialist Desk in same room
    createDesk(L1, -11.5, -7.2, 'brand_planner', 'Brand Planner', 0x8e44ad);
    // Meeting Table in corner
    cylinder(L1, 1.4, 1.4, 0.12, -7.5, 1.35, -10.2, woodWarm);
    cylinder(L1, 0.18, 0.28, 1.3, -7.5, 0.65, -10.2, metalDark);
    for (let a = 0; a < 4; a++) {
      const ang = (a * Math.PI) / 2;
      createSwivelChair(L1, -7.5 + Math.sin(ang) * 1.8, -10.2 + Math.cos(ang) * 1.8, ang + Math.PI);
    }
    createPlant(L1, -14.2, -3.8, 1.1);

    // 2. RUANG RISET & ANALISIS (North-East)
    const resDesk = createDesk(L1, 7.5, -7.2, 'researcher', 'Researcher', 0x16a085);
    hitMeshes[1].push(resDesk.children[resDesk.children.length - 1]);
    // Teammate Analyst Desk
    createDesk(L1, 11.5, -7.2, 'data_analyst', 'Data Analyst', 0x2980b9);
    // Whiteboard with diagrams
    box(L1, 3.8, 2.0, 0.08, 7.5, 2.1, -11.3, mat('wb', 0xffffff));
    box(L1, 4.0, 0.08, 0.12, 7.5, 1.05, -11.3, frameMat);
    createPlant(L1, 14.2, -3.8, 1.1);

    // 3. RUANG SALES & KEMITRAAN (South-West)
    const salesDesk = createDesk(L1, -7.5, 6.8, 'sales', 'Agent Sales', 0xd35400);
    hitMeshes[1].push(salesDesk.children[salesDesk.children.length - 1]);
    // CS WhatsApp Desk
    createDesk(L1, -11.5, 6.8, 'cs_wa', 'CS WhatsApp ISK', 0x27ae60);
    // Product display shelf (Keris nail boxes & wire coils!)
    box(L1, 2.8, 2.2, 0.6, -7.5, 1.1, 10.4, woodDark);
    // Sample brown boxes on shelf
    box(L1, 0.7, 0.45, 0.5, -8.2, 1.35, 10.4, mat('boxPaku', 0xb89264));
    box(L1, 0.7, 0.45, 0.5, -7.2, 1.35, 10.4, mat('boxPaku2', 0xb89264));
    box(L1, 0.7, 0.45, 0.5, -7.7, 1.85, 10.4, mat('boxPaku3', 0xb89264));
    createPlant(L1, -14.2, 3.8, 1.1);

    // 4. RUANG HERMES AUTOMATION ENGINE (South-East)
    const hermesDesk = createDesk(L1, 7.5, 6.8, 'default', 'Hermes Utama', 0x2c3e50);
    hitMeshes[1].push(hermesDesk.children[hermesDesk.children.length - 1]);
    // Cluster of Server Racks with Pulsating Green LEDs
    for (let s = 0; s < 3; s++) {
      const rx = 10.8 + s * 1.3;
      box(L1, 0.95, 2.8, 0.95, rx, 1.4, 9.8, metalDark);
      box(L1, 0.82, 2.5, 0.04, rx, 1.4, 10.3, serverGlow);
    }
    createPlant(L1, 14.2, 3.8, 1.1);

    // 5. BREAKOUT LOUNGE & CORRIDOR (Center)
    // Red Coral Modern Sofa (like team.ai.id)
    box(L1, 3.6, 0.55, 1.3, -3.2, 0.38, 0.2, sofaCoral);
    box(L1, 3.6, 0.65, 0.28, -3.2, 0.95, -0.32, sofaCoral);
    for (const off of [-1.7, 1.7]) box(L1, 0.22, 0.75, 1.3, -3.2 + off, 0.75, 0.2, sofaCoral);
    // Round Pouf
    cylinder(L1, 0.55, 0.55, 0.4, -0.6, 0.28, 0.4, poufTeal, 16);
    // Coffee Table
    cylinder(L1, 0.85, 0.85, 0.08, -1.9, 0.45, 0.4, woodWarm, 16);
    cylinder(L1, 0.08, 0.12, 0.4, -1.9, 0.2, 0.4, metalDark);
    // Water Dispenser with Blue Gallon
    box(L1, 0.65, 1.1, 0.65, 3.2, 0.55, -0.2, mat('dispenser', 0xf0ece1));
    cylinder(L1, 0.26, 0.26, 0.7, 3.2, 1.45, -0.2, mat('gallon', 0x3498db, { transparent: true, opacity: 0.7 }), 12);
    // Floor Lamp
    cylinder(L1, 0.04, 0.04, 2.4, 4.6, 1.2, 0.2, metalChrome);
    cylinder(L1, 0.32, 0.45, 0.45, 4.6, 2.3, 0.2, mat('lampShade', 0xfff3db, { emissive: 0xffe6aa, emissiveIntensity: 0.5 }));
    // Staircase to Level 2
    for (let st = 0; st < 8; st++) {
      box(L1, 2.4, 0.16, 0.45, -0.2, 0.1 + st * 0.22, -1.6 - st * 0.45, metalDark);
    }
    createPlant(L1, 2.2, -1.8, 1.2);

    // ==========================================
    // BUILD LANTAI 2: STUDIO TALENTA AI
    // ==========================================
    const L2 = levels[2];
    box(L2, 32.0, 0.1, 26.0, 0, 0.05, 0, mat('l2Floor', 0xf8f4ea, { roughness: 0.8 }));
    createGlassWall(L2, 0, -1.8, 30, 0);
    createGlassWall(L2, -5.2, -6.5, 9.4, Math.PI / 2);
    createGlassWall(L2, 5.2, -6.5, 9.4, Math.PI / 2);

    createRoomSign(L2, 'STUDIO DINDA KEMALA · PALEMBANG', 6.2, -9.8, -1.75);
    createRoomSign(L2, 'STUDIO NARA SENJA · JAMBI', 5.8, 0, -1.75);
    createRoomSign(L2, 'STUDIO RANIA PUTRI · PEKANBARU', 6.0, 9.8, -1.75);

    // Studio Dinda
    const dindaDesk = createDesk(L2, -9.8, -6.4, 'dinda', 'Dinda Kemala', 0xe67e22);
    hitMeshes[2].push(dindaDesk.children[dindaDesk.children.length - 1]);
    // Studio Tripod with Camera
    cylinder(L2, 0.04, 0.04, 1.6, -9.8, 0.8, -3.8, metalDark);
    box(L2, 0.45, 0.3, 0.5, -9.8, 1.7, -3.8, metalDark);
    cylinder(L2, 0.12, 0.14, 0.3, -9.8, 1.7, -3.5, mat('lens', 0x111111), 12);
    createPlant(L2, -14.2, -2.6, 1.1);

    // Studio Nara
    const naraDesk = createDesk(L2, 0, -6.4, 'nara', 'Nara Senja', 0x1abc9c);
    hitMeshes[2].push(naraDesk.children[naraDesk.children.length - 1]);
    cylinder(L2, 0.04, 0.04, 1.6, 0, 0.8, -3.8, metalDark);
    box(L2, 0.45, 0.3, 0.5, 0, 1.7, -3.8, metalDark);
    createPlant(L2, 4.2, -2.6, 1.1);

    // Studio Rania
    const raniaDesk = createDesk(L2, 9.8, -6.4, 'rania', 'Rania Putri', 0x9b59b6);
    hitMeshes[2].push(raniaDesk.children[raniaDesk.children.length - 1]);
    cylinder(L2, 0.04, 0.04, 1.6, 9.8, 0.8, -3.8, metalDark);
    box(L2, 0.45, 0.3, 0.5, 9.8, 1.7, -3.8, metalDark);
    createPlant(L2, 14.2, -2.6, 1.1);

    // Creative Editing Pods in Lantai 2 Lounge
    createDesk(L2, -5.5, 4.2, 'video_editor', 'Video Editor Flow', 0x34495e);
    createDesk(L2, 5.5, 4.2, 'copywriter', 'Copywriter AI', 0x16a085);
    createRoomSign(L2, 'STUDIO PRODUKSI KONTEN TIKTOK', 6.8, 0, 0.8);

    // ==========================================
    // FLOATING HTML LABELS & SPEECH BUBBLES
    // ==========================================
    const labelElements = new Map();
    function syncLabels() {
      if (!labels) return;
      labels.innerHTML = '';
      labelElements.clear();

      const currentHitMeshes = hitMeshes[activeFloor] || [];
      for (const mesh of currentHitMeshes) {
        const id = mesh.userData.agentId;
        const name = mesh.userData.agentName;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'scene-label-pill';
        btn.dataset.agentId = id;
        btn.innerHTML = `
          <span class="pill-dot"></span>
          <span class="pill-text">${name}</span>
          <span class="pill-bubble">💬</span>
        `;
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          focus(id, true);
        });
        labels.appendChild(btn);
        labelElements.set(id, { element: btn, mesh });
      }
    }

    function updateLabelPositions() {
      if (!labels || !labelElements.size) return;
      const width = container.clientWidth;
      const height = container.clientHeight;

      for (const [id, item] of labelElements) {
        item.mesh.getWorldPosition(projected);
        projected.y += 1.8; // position over head
        projected.project(camera);

        const x = ((projected.x + 1) * width) / 2;
        const y = ((-projected.y + 1) * height) / 2;

        const isBehind = projected.z > 1;
        if (isBehind || x < 0 || x > width || y < 0 || y > height) {
          item.element.style.display = 'none';
        } else {
          item.element.style.display = 'flex';
          item.element.style.transform = `translate(-50%, -100%) translate(${x}px, ${y}px)`;
          if (id === selected) item.element.classList.add('is-selected');
          else item.element.classList.remove('is-selected');
        }
      }
    }

    // ==========================================
    // CAMERA & SELECTION CONTROLS
    // ==========================================
    function setFloor(floorNum) {
      activeFloor = floorNum;
      levels[1].visible = activeFloor === 1;
      levels[2].visible = activeFloor === 2;
      floorButtons.forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.officeFloor) === activeFloor)));
      const viewLabel = container.closest('.scene-frame')?.querySelector('#scene-view');
      if (viewLabel) viewLabel.textContent = floorNames[activeFloor] || '';
      syncLabels();
      dirty = true;
    }

    function setTopView(isTop) {
      topView = isTop;
      const targetCam = isTop ? { x: 0, y: 65, z: 0.1 } : { x: 29, y: 38, z: 45 };
      animateCamera(targetCam, { x: 0, y: 1.2, z: 0 }, 600);
      viewButtons.forEach((b) => b.setAttribute('aria-pressed', (b.dataset.officeView === 'top') === isTop));
    }

    function animateCamera(targetPos, targetLookAt, duration = 650) {
      const startPos = camera.position.clone();
      const startLook = controls.target.clone();
      const startTime = performance.now();

      tween = (time) => {
        const progress = Math.min((time - startTime) / duration, 1);
        const ease = 0.5 - Math.cos(progress * Math.PI) / 2;

        camera.position.lerpVectors(startPos, new T.Vector3(targetPos.x, targetPos.y, targetPos.z), ease);
        controls.target.lerpVectors(startLook, new T.Vector3(targetLookAt.x, targetLookAt.y, targetLookAt.z), ease);
        dirty = true;

        if (progress >= 1) tween = null;
      };
    }

    function focus(id, zoom = true) {
      selected = id;
      // Find room in layout
      const room = layout.find((r) => r.id === id);
      if (room) {
        if (room.floor !== activeFloor) setFloor(room.floor);
        const look = { x: room.x, y: 1.2, z: room.z };
        const cam = topView
          ? { x: room.x, y: 45, z: room.z + 0.1 }
          : { x: room.x + 22, y: 22, z: room.z + 22 };
        animateCamera(cam, look, 500);
      }
      dirty = true;
    }

    function home() {
      selected = null;
      setTopView(false);
      animateCamera({ x: 29, y: 38, z: 45 }, { x: 0, y: 1.2, z: 0 }, 600);
    }

    function zoomBy(delta) {
      camera.zoom = Math.max(controls.minZoom, Math.min(controls.maxZoom, camera.zoom * (1 + delta)));
      camera.updateProjectionMatrix();
      dirty = true;
    }

    // Pointer Raycasting for Clicks
    function onPointerDown(e) {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(pointer, camera);
      const intersects = raycaster.intersectObjects(hitMeshes[activeFloor] || [], true);
      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const id = hit.userData.agentId;
        if (id) {
          focus(id, true);
          // Trigger studio.js selection if present
          if (window.selectAgent) window.selectAgent(id);
        }
      }
    }
    renderer.domElement.addEventListener('pointerdown', onPointerDown);

    // Window Resize Handling
    function resize() {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (!w || !h) return;
      const asp = w / h;
      camera.left = (-frustum * asp) / 2;
      camera.right = (frustum * asp) / 2;
      camera.top = frustum / 2;
      camera.bottom = -frustum / 2;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      dirty = true;
    }
    window.addEventListener('resize', resize);

    
    // Wire toolbar buttons
    floorButtons.forEach(b => b.addEventListener('click', () => setFloor(Number(b.dataset.officeFloor))));
    viewButtons.forEach(b => b.addEventListener('click', () => setTopView(b.dataset.officeView === 'top')));
    
    const resetBtn = frameElement?.querySelector('[data-office-reset]');
    if (resetBtn) resetBtn.addEventListener('click', home);
    const zoomInBtn = frameElement?.querySelector('[data-office-zoom="in"]');
    if (zoomInBtn) zoomInBtn.addEventListener('click', () => zoomBy(0.2));
    const zoomOutBtn = frameElement?.querySelector('[data-office-zoom="out"]');
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => zoomBy(-0.2));

    // Initial Floor Sync
    setFloor(1);

    // Main Render Loop
    function render(time) {
      requestAnimationFrame(render);
      if (!visible) return;

      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Subtle idle breathing animation for agents
      for (const p of animatedPersons) {
        p.group.position.y = p.baseY + Math.sin(elapsed * p.speed) * 0.02;
      }

      if (tween) tween(time);
      controls.update();
      updateLabelPositions();
      renderer.render(scene, camera);
    }
    render(0);

    return {
      update(agentList) {
        agents = agentList || [];
        syncLabels();
        dirty = true;
      },
      select: focus,
      home,
      zoom: zoomBy,
      setFloor,
      setTopView,
      setVisible(val) {
        visible = val;
        dirty = true;
        if (val) resize();
      }
    };
  }

  window.Office3D = {
    update(agents) {
      const container = document.getElementById('office-viewport');
      if (!container) return;
      try {
        instance = instance || createOffice(container);
        instance.update(agents);
      } catch (err) {
        console.error('Office 3D init error:', err);
      }
    },
    select(id, zoom = true) {
      instance?.select(id, zoom);
    },
    home() {
      instance?.home();
    },
    zoom(amount) {
      instance?.zoom(amount);
    },
    setFloor(num) {
      instance?.setFloor(num);
    },
    setVisible(val) {
      instance?.setVisible(val);
    }
  };
})();
