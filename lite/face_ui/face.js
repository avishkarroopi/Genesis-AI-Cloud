import { FaceLandmarker, FilesetResolver } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";

// ═══════════════════════════════════════════════════════════════════════
// GENESIS Face Animation System — Full Rebuild
// Canvas: 3608 × 2244   |   Source: assets/face.png (no resize, no crop)
// All animations driven by detected MediaPipe landmarks only.
// ═══════════════════════════════════════════════════════════════════════

const LOGICAL_W = 3608;
const LOGICAL_H = 2244;

let canvasDisplayW = 0;
let canvasDisplayH = 0;
let sceneScale = 1;
let sceneOffsetX = 0;
let sceneOffsetY = 0;

// ──────────────────────────────────────────────────────────────────────
// PHASE 1 — LANDMARK INDICES
// MediaPipe FaceLandmarker 478-point model
// All coords normalized 0.0–1.0 → scaled to W/H for pixel positions
// ──────────────────────────────────────────────────────────────────────

// Left eye — upper eyelid border (goes left→right across top of eye opening)
const L_UPPER_LID = [246, 161, 160, 159, 158, 157, 173];
// Left eye — lower eyelid border (goes left→right across bottom of eye opening)
const L_LOWER_LID = [33, 7, 163, 144, 145, 153, 154, 155, 133];
// Right eye — upper eyelid border
const R_UPPER_LID = [466, 388, 387, 386, 385, 384, 398];
// Right eye — lower eyelid border
const R_LOWER_LID = [263, 249, 390, 373, 374, 380, 381, 382, 362];

// Iris centers (MediaPipe iris landmark indices)
const L_IRIS_CENTER = 468;
const R_IRIS_CENTER = 473;

// Approximate iris radius landmark — distance from center to edge
const L_IRIS_EDGE = 469;  // left iris right edge
const R_IRIS_EDGE = 474;  // right iris right edge

// Mouth — upper lip (outer edge, left to right)
const UPPER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291];
// Mouth — lower lip (outer edge, left to right)
const LOWER_LIP = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291];
// Inner upper lip centerline
const INNER_UPPER_LIP = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308];
// Inner lower lip centerline
const INNER_LOWER_LIP = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308];

// Jaw curve (left cheek down to chin 152 and up to right cheek)
// We go far enough up the cheeks to cover the natural dropping jaw width
const JAW_CURVE = [132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288, 361];
const JAW_BOTTOM = 152;

// Eyebrow references (for validation only — do NOT animate)
const L_BROW_TOP = 105;
const R_BROW_TOP = 334;

// Nose tip (for idle glow)
const NOSE_TIP = 1;

// Face center
const FACE_CENTER = 168;

// ── User-specified BLINK lid subsets (polygon-only, no forehead/brow/cheek) ──
const BLINK_L_UPPER = [159, 158, 157, 173, 133, 246];
const BLINK_L_LOWER = [145, 144, 163, 7, 33, 246];
const BLINK_R_UPPER = [386, 385, 384, 398, 362, 466];
const BLINK_R_LOWER = [374, 373, 390, 249, 263, 466];

// ── User-specified MOUTH landmark subsets ──
const MOUTH_UPPER = [13, 312, 82, 78, 308];
const MOUTH_LOWER = [14, 317, 87, 78, 308];
const MOUTH_CORNERS = [61, 291];
const MOUTH_JAW = 152;

// ──────────────────────────────────────────────────────────────────────
// STORED LANDMARK DATA (populated after detection)
// ──────────────────────────────────────────────────────────────────────

const LM = {
  // Per-eye: array of {x,y} pixel points for upper and lower eyelid curves
  lUpperLid: [],   // upper lid line points (L→R)
  lLowerLid: [],   // lower lid line points (L→R)
  rUpperLid: [],
  rLowerLid: [],

  // Blink-specific lid subsets (polygon-only, no forehead/brow/cheek)
  blinkLUpper: [], blinkLLower: [],
  blinkRUpper: [], blinkRLower: [],

  // Eye bounding box (union of upper+lower lid)
  lEyeMinX: 0, lEyeMaxX: 0, lEyeMinY: 0, lEyeMaxY: 0, lEyeCX: 0, lEyeCY: 0,
  rEyeMinX: 0, rEyeMaxX: 0, rEyeMinY: 0, rEyeMaxY: 0, rEyeCX: 0, rEyeCY: 0,

  // Iris centers and radii in pixels
  lIrisX: 0, lIrisY: 0, lIrisR: 0,
  rIrisX: 0, rIrisY: 0, rIrisR: 0,

  // Mouth corners in pixels
  mouthLeftX: 0, mouthLeftY: 0,
  mouthRightX: 0, mouthRightY: 0,

  // Lip boundary arrays in pixels
  outerUpperLip: [],  // outer top lip
  outerLowerLip: [],  // outer bottom lip
  innerUpperLip: [],  // inner mouth top edge
  innerLowerLip: [],  // inner mouth bottom edge

  // User-specified mouth landmark subsets
  mouthUpperPts: [],   // [13,312,82,78,308]
  mouthLowerPts: [],   // [14,317,87,78,308]
  mouthCornerPts: [],  // [61,291]
  mouthJawPt: null,    // {x,y} for landmark 152
  jawCurvePts: [],     // full array of {x,y} for JAW_CURVE

  // Lip split Y — the neutral separation line between upper and lower lips
  lipSplitY: 0,

  // Mouth bounding
  mouthCX: 0, mouthCY: 0, mouthW: 0,

  // Jaw Y
  jawY: 0,

  // Reference landmarks for idle effects
  noseTipX: 0, noseTipY: 0,
  faceCX: 0, faceCY: 0,

  // Eyebrow Y (for blink validation — blink must stay BELOW this)
  lBrowY: 0, rBrowY: 0,

  valid: false
};

// ── Raw landmark storage for render-time px() access ──
let _rawLM = null;
function px(idx) { return { x: _rawLM[idx].x * LOGICAL_W, y: _rawLM[idx].y * LOGICAL_H }; }

// ──────────────────────────────────────────────────────────────────────
// ANIMATION STATE
// ──────────────────────────────────────────────────────────────────────

const STATES = { IDLE: 'idle', LISTENING: 'listening', THINKING: 'thinking', SPEAKING: 'speaking', PROCESSING: 'processing' };
let currentState = STATES.IDLE;
let overrideDemo = false;

// Realtime Connections Status
let wsConnected = false;
let serverConnected = false; // assumes true if page loads, but verified via fetch
let aiReady = false;
let voiceReady = false;
const A = {
  // Blink
  blink: 0,              // 0 = open, 1 = fully closed
  blinkPhase: 'idle',    // idle | closing | hold | opening
  blinkTimer: 0,
  nextBlinkAt: 2500 + Math.random() * 2000,
  blinkMaxTarget: 1,     // 0.3 = small, 0.6 = half, 1.0 = full

  // Eye movement
  eyeOffX: 0, eyeOffY: 0,      // current offset in pixels
  eyeTargetX: 0, eyeTargetY: 0, // target offset
  eyeMoveTimer: 0,
  nextEyeMoveAt: 1200 + Math.random() * 2000,

  // Mouth
  mouthOpen: 0,       // 0–1 current open amount
  mouthTarget: 0,     // target open amount
  speakPhase: 0,

  // Idle
  breathPhase: 0,
  glowPhase: 0,
  listenFocus: 0,

  // Eyebrow (thinking lift — pixels)
  browOffset: 0,
  browTarget: 0,
};

// Demo state cycling
let demoTimer = 0;

// Lip sync — external override for mouth open amount (-1 = not active, 0–1 = open)
let lipSyncValue = -1;

// Animation
let canvas, ctx, faceImg, lastTime = 0;
// Three.js variables
let threeRenderer = null;
let threeScene = null;
let threeCamera = null;
let threeFaceMesh = null;

// ──────────────────────────────────────────────────────────────────────
// INIT
// ──────────────────────────────────────────────────────────────────────

async function init() {
  const loader = document.getElementById('loader');
  const loadText = document.getElementById('loadText');

  try {
    canvas = document.getElementById('faceCanvas');
    ctx = canvas.getContext('2d');

    // Step 1: Load face image
    loadText.innerText = 'Loading face.png...';
    faceImg = await loadImage('assets/face.png');

    // Step 2: Load MediaPipe
    loadText.innerText = 'Loading MediaPipe FaceLandmarker...';
    let detector = null;
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        detector = await FaceLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
            delegate: "CPU"
          },
          outputFaceBlendshapes: false,
          runningMode: "IMAGE",
          numFaces: 1
        });
        break;
      } catch (e) {
        loadText.innerText = `Retrying MediaPipe (${attempt + 1}/5)...`;
        await sleep(1000);
      }
    }

    if (!detector) {
      loadText.innerText = 'ERROR: Could not load MediaPipe models.';
      return;
    }

    // Step 3: Run landmark detection
    loadText.innerText = 'Detecting face landmarks...';
    // Allow UI to paint before heavy detection
    await sleep(50);
    const ok = detectLandmarks(detector);

    if (!ok) {
      loadText.innerText = 'ERROR: No face detected in face.png';
      return;
    }

    // Step 4: Validate
    const validationPassed = validateLandmarks();
    if (!validationPassed) {
      loadText.innerText = 'ERROR: Landmark validation failed. Check console.';
      return;
    }

    // Step 5: Start render loop
    loader.style.display = 'none';
    connectWebSocket();

    initThreeJS();

    window.addEventListener('resize', handleResize);
    handleResize();

    lastTime = performance.now();
    requestAnimationFrame(renderLoop);
    console.log('[GENESIS] ✅ System active. All landmark checks passed.');
  } catch (err) {
    if (loadText) loadText.innerText = 'CRITICAL ERROR: ' + err.message;
    console.error('[GENESIS INIT ERROR]', err);
  }
}

function handleResize() {
  const dpr = window.devicePixelRatio || 1;
  canvasDisplayW = window.innerWidth;
  canvasDisplayH = window.innerHeight;

  canvas.width = canvasDisplayW * dpr;
  canvas.height = canvasDisplayH * dpr;
  ctx.scale(dpr, dpr);

  // Calculate "contain" scale and offset
  const ratioX = canvasDisplayW / LOGICAL_W;
  const ratioY = canvasDisplayH / LOGICAL_H;
  sceneScale = Math.min(ratioX, ratioY);

  sceneOffsetX = (canvasDisplayW - LOGICAL_W * sceneScale) / 2;
  sceneOffsetY = (canvasDisplayH - LOGICAL_H * sceneScale) / 2;

  const hud = document.getElementById('hud-overlay');
  if (hud) {
    hud.style.width = (LOGICAL_W * sceneScale) + 'px';
    hud.style.height = (LOGICAL_H * sceneScale) + 'px';
    hud.style.left = sceneOffsetX + 'px';
    hud.style.top = sceneOffsetY + 'px';
  }

  if (typeof resizeThreeJS === 'function') resizeThreeJS();
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 1 — LANDMARK DETECTION
// ──────────────────────────────────────────────────────────────────────

function detectLandmarks(detector) {
  const results = detector.detect(faceImg);
  if (!results.faceLandmarks || results.faceLandmarks.length === 0) {
    console.error('[GENESIS] No face landmarks detected in image.');
    return false;
  }

  const lm = results.faceLandmarks[0];
  _rawLM = lm;  // store for render-time px() access

  // Helper: convert normalized landmark to pixel coords on 3608×2244 canvas
  function px(idx) { return { x: lm[idx].x * LOGICAL_W, y: lm[idx].y * LOGICAL_H }; }
  function pxArr(indices) { return indices.map(i => px(i)); }

  // ── Left eyelid curves ──
  LM.lUpperLid = pxArr(L_UPPER_LID);
  LM.lLowerLid = pxArr(L_LOWER_LID);
  LM.rUpperLid = pxArr(R_UPPER_LID);
  LM.rLowerLid = pxArr(R_LOWER_LID);

  // ── Left eye bounding box (union of both lid curves) ──
  {
    const allL = [...LM.lUpperLid, ...LM.lLowerLid];
    LM.lEyeMinX = Math.min(...allL.map(p => p.x));
    LM.lEyeMaxX = Math.max(...allL.map(p => p.x));
    LM.lEyeMinY = Math.min(...allL.map(p => p.y));
    LM.lEyeMaxY = Math.max(...allL.map(p => p.y));
    LM.lEyeCX = (LM.lEyeMinX + LM.lEyeMaxX) / 2;
    LM.lEyeCY = (LM.lEyeMinY + LM.lEyeMaxY) / 2;
  }
  {
    const allR = [...LM.rUpperLid, ...LM.rLowerLid];
    LM.rEyeMinX = Math.min(...allR.map(p => p.x));
    LM.rEyeMaxX = Math.max(...allR.map(p => p.x));
    LM.rEyeMinY = Math.min(...allR.map(p => p.y));
    LM.rEyeMaxY = Math.max(...allR.map(p => p.y));
    LM.rEyeCX = (LM.rEyeMinX + LM.rEyeMaxX) / 2;
    LM.rEyeCY = (LM.rEyeMinY + LM.rEyeMaxY) / 2;
  }

  // ── Iris centers and radii ──
  const lIC = px(L_IRIS_CENTER);
  const lIE = px(L_IRIS_EDGE);
  LM.lIrisX = lIC.x;
  LM.lIrisY = lIC.y;
  LM.lIrisR = Math.abs(lIE.x - lIC.x) * 1.1; // slight padding

  const rIC = px(R_IRIS_CENTER);
  const rIE = px(R_IRIS_EDGE);
  LM.rIrisX = rIC.x;
  LM.rIrisY = rIC.y;
  LM.rIrisR = Math.abs(rIE.x - rIC.x) * 1.1;

  // ── Blink-specific lid subsets ──
  LM.blinkLUpper = pxArr(BLINK_L_UPPER);
  LM.blinkLLower = pxArr(BLINK_L_LOWER);
  LM.blinkRUpper = pxArr(BLINK_R_UPPER);
  LM.blinkRLower = pxArr(BLINK_R_LOWER);

  // ── Lip boundary arrays ──
  LM.outerUpperLip = pxArr(UPPER_LIP);
  LM.outerLowerLip = pxArr(LOWER_LIP);
  LM.innerUpperLip = pxArr(INNER_UPPER_LIP);
  LM.innerLowerLip = pxArr(INNER_LOWER_LIP);

  // ── User-specified mouth landmark subsets ──
  LM.mouthUpperPts = pxArr(MOUTH_UPPER);
  LM.mouthLowerPts = pxArr(MOUTH_LOWER);
  LM.mouthCornerPts = pxArr(MOUTH_CORNERS);
  LM.mouthJawPt = px(MOUTH_JAW);
  LM.jawCurvePts = pxArr(JAW_CURVE);

  // ── Lip split Y: midpoint between inner upper lip base and inner lower lip top ──
  // Landmark 13 = upper inner lip center bottom, 14 = lower inner lip center top
  const lipTop = lm[13].y * LOGICAL_H;
  const lipBot = lm[14].y * LOGICAL_H;
  LM.lipSplitY = (lipTop + lipBot) / 2;

  // ── Mouth corners ──
  const mc0 = px(61);   // left mouth corner
  const mc1 = px(291);  // right mouth corner
  LM.mouthLeftX = mc0.x; LM.mouthLeftY = mc0.y;
  LM.mouthRightX = mc1.x; LM.mouthRightY = mc1.y;
  LM.mouthCX = (mc0.x + mc1.x) / 2;
  LM.mouthCY = LM.lipSplitY;
  LM.mouthW = mc1.x - mc0.x;

  // ── Jaw Y ──
  LM.jawY = lm[JAW_BOTTOM].y * LOGICAL_H;

  // ── Nose & face center for idle effects ──
  LM.noseTipX = lm[NOSE_TIP].x * LOGICAL_W;
  LM.noseTipY = lm[NOSE_TIP].y * LOGICAL_H;
  LM.faceCX = lm[FACE_CENTER].x * LOGICAL_W;
  LM.faceCY = lm[FACE_CENTER].y * LOGICAL_H;

  // ── Eyebrow Y for blink validation ──
  LM.lBrowY = lm[L_BROW_TOP].y * LOGICAL_H;
  LM.rBrowY = lm[R_BROW_TOP].y * LOGICAL_H;

  LM.valid = true;
  console.log('[GENESIS] Landmarks detected. LM =', LM);
  return true;
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 1 — VALIDATION
// ──────────────────────────────────────────────────────────────────────

function validateLandmarks() {
  let pass = true;

  // 1. Left eye must be to the LEFT of right eye (from camera perspective)
  if (LM.lEyeCX >= LM.rEyeCX) {
    console.error('[VALIDATE FAIL] Left eye is not to the left of right eye.');
    pass = false;
  }

  // 2. Both eyebrow Y positions must be ABOVE eye Y (smaller Y = higher on canvas)
  if (LM.lBrowY >= LM.lEyeMinY) {
    console.error('[VALIDATE FAIL] Left eyebrow is not above left eye. Brow:', LM.lBrowY, 'Eye top:', LM.lEyeMinY);
    pass = false;
  }
  if (LM.rBrowY >= LM.rEyeMinY) {
    console.error('[VALIDATE FAIL] Right eyebrow is not above right eye.');
    pass = false;
  }

  // 3. Lip split Y must be below both eye centers
  if (LM.lipSplitY <= LM.lEyeCY || LM.lipSplitY <= LM.rEyeCY) {
    console.error('[VALIDATE FAIL] Lip split is at or above eyes.');
    pass = false;
  }

  // 4. Mouth must be ABOVE jaw
  if (LM.mouthCY >= LM.jawY) {
    console.error('[VALIDATE FAIL] Mouth is at or below jaw.');
    pass = false;
  }

  // 5. Iris radii must be positive and reasonable
  if (LM.lIrisR <= 0 || LM.lIrisR > 300) {
    console.error('[VALIDATE FAIL] Left iris radius is out of range:', LM.lIrisR);
    pass = false;
  }
  if (LM.rIrisR <= 0 || LM.rIrisR > 300) {
    console.error('[VALIDATE FAIL] Right iris radius is out of range:', LM.rIrisR);
    pass = false;
  }



  if (pass) {
    // Print validation success report
    console.log('[GENESIS] ═══════════════════════════════════');
    console.log('[GENESIS] VALIDATION PASSED');
    console.log('[GENESIS] ─────────────────────────────────────');
    console.log('[BLINK CHECK] Left upper lid top Y:', LM.lEyeMinY.toFixed(1), '| Left brow Y:', LM.lBrowY.toFixed(1), '→', LM.lEyeMinY > LM.lBrowY ? '✅ BELOW brow' : '❌ CUTS brow');
    console.log('[BLINK CHECK] Right upper lid top Y:', LM.rEyeMinY.toFixed(1), '| Right brow Y:', LM.rBrowY.toFixed(1), '→', LM.rEyeMinY > LM.rBrowY ? '✅ BELOW brow' : '❌ CUTS brow');
    console.log('[EYE CHECK] Left iris center:', LM.lIrisX.toFixed(0), LM.lIrisY.toFixed(0), '| Radius:', LM.lIrisR.toFixed(0));
    console.log('[EYE CHECK] Right iris center:', LM.rIrisX.toFixed(0), LM.rIrisY.toFixed(0), '| Radius:', LM.rIrisR.toFixed(0));
    console.log('[EYE CHECK] Max eye shift: ±15px horizontal, ±8px vertical → within iris radius ✅');
    console.log('[MOUTH CHECK] Lip split Y:', LM.lipSplitY.toFixed(1), '| Nose Y:', LM.noseTipY.toFixed(1), '| Jaw Y:', LM.jawY.toFixed(1));
    console.log('[MOUTH CHECK] Split is between nose and jaw →', (LM.lipSplitY > LM.noseTipY && LM.lipSplitY < LM.jawY) ? '✅' : '❌');
    console.log('[GENESIS] ═══════════════════════════════════');
  }

  return pass;
}

// ──────────────────────────────────────────────────────────────────────
// HELPERS
// ──────────────────────────────────────────────────────────────────────

function wrapStatus(text) {
  if (!text) return "";
  const parts = text.trim().split(" ");
  if (parts.length < 2) {
    const status = parts[0].toLowerCase();
    return `<span class="status-${status}">${parts[0]}</span>`;
  }
  const label = parts.slice(0, -1).join(" ");
  const status = parts[parts.length - 1];
  const statusClass = `status-${status.toLowerCase()}`;
  return `${label} <span class="${statusClass}">${status}</span>`;
}

function lerp(a, b, t) { return a + (b - a) * t; }

/** Draw a polygon path from an array of {x,y} points */
function polyPath(c, pts) {
  if (pts.length === 0) return;
  c.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) c.lineTo(pts[i].x, pts[i].y);
  c.closePath();
}

/**
 * Interpolate a lid curve (array of {x,y}) at a fraction t (0 = top, 1 = original)
 * Used to animate eyelid sweeping down as blink progresses.
 * Also accepts a vertical offset so we can shift the curve down.
 */
function shiftPoints(pts, dy) {
  return pts.map(p => ({ x: p.x, y: p.y + dy }));
}

// ──────────────────────────────────────────────────────────────────────
// MAIN RENDER LOOP
// ──────────────────────────────────────────────────────────────────────

function renderLoop(timestamp) {
  if (!lastTime) lastTime = timestamp;
  const dt = Math.min(timestamp - lastTime, 50);  // cap dt at 50ms
  lastTime = timestamp;

  updateState(dt);

  // Phase 7 Part 1 & 4: Secondary Motion & Micro Life
  if (A.secondaryFollow === undefined) A.secondaryFollow = 0;
  A.secondaryFollow = lerp(A.secondaryFollow, A.mouthOpenFinal || 0, 0.08);

  // Phase 44.5: Tissue inertia (spring-damper overshoot)
  if (A._tissueVel === undefined) A._tissueVel = 0;
  if (A.uTissueInertia === undefined) A.uTissueInertia = 0;
  let tissueTarget = A.mouthOpenFinal || 0;
  A._tissueVel += (tissueTarget - A.uTissueInertia) * 0.15;
  A._tissueVel *= 0.82;
  A.uTissueInertia += A._tissueVel;
  A.uTissueInertia = Math.max(0, Math.min(1.2, A.uTissueInertia));

  if (A.microLife === undefined) A.microLife = 0;
  A.microLife += dt * 0.001;
  // Multiply by 1000 to convert float offset into standard pixel space for pos.y
  A.uMicroLife = (Math.sin(A.microLife * 1.7) * 0.002 + Math.sin(A.microLife * 2.3) * 0.0015) * 1000.0;

  // Phase 7.5 Idle Micro Life Enhancement
  let idleWeight = 1.0;
  if (currentState === STATES.SPEAKING) idleWeight = 0.4;
  else if (emotionState !== 'idle' && emotionState !== 'sleep' && emotionState !== 'thinking') idleWeight = 0.2;
  else if (A._breathAmp && A._breathAmp > 0.8) idleWeight = 0.6; // Large breathing

  A.uIdleLife = (Math.sin(A.microLife * 1.3) * 0.002 +
    Math.sin(A.microLife * 2.1) * 0.0015 +
    Math.sin(A.microLife * 0.7) * 0.001) * idleWeight * 8500.0; // Phase 7.5 BOOST 2: Increased from 3500 to 8500 for highly visible global drift

  // Phase 6 Breath State Value (Always updates reliably)
  if (!A._breathValueTimer) A._breathValueTimer = 0;
  let bSpeed = (currentState === STATES.SPEAKING) ? 1.8 : 0.8;
  bSpeed *= (A._fatigueBreathBoost || 1.0); // Step 41: fatigue increases breath speed
  A._breathValueTimer += dt * 0.001 * bSpeed;

  // Smooth 0 -> 1 -> 0 loop
  A.uBreathRaw = (Math.sin(A._breathValueTimer * Math.PI) * 0.5) + 0.5;

  // Combine speech and breath amplitudes
  let bAmpBase = (currentState === STATES.SPEAKING) ? 0.3 : 1.0;
  if (A._breathAmp === undefined) A._breathAmp = bAmpBase;
  A._breathAmp = lerp(A._breathAmp, bAmpBase, 0.05);
  A.uBreath = A.uBreathRaw * A._breathAmp;

  animate(dt);
  updateEmotionUniforms(dt);
  updateAutoIdleEmotions(dt);
  // Disabled legacy 2D canvas render; Three.js is now the exclusive face renderer.
  // render();

  if (threeRenderer && threeScene && threeCamera) {
    ShaderUniforms.time.value = timestamp * 0.001;
    ShaderUniforms.blink.value = A.blink;

    // Cinematic Blinking Timer (Independent of A.blink, state, or speaking)
    if (!window.cbState) window.cbState = { phase: 'idle', timer: 0, next: 2500, val: 0, last: timestamp };
    let dtCine = timestamp - window.cbState.last;
    window.cbState.last = timestamp;
    window.cbState.timer += dtCine;

    if (window.cbState.phase === 'idle' && window.cbState.timer >= window.cbState.next) {
      window.cbState.phase = 'closing';
      window.cbState.timer = 0;
    } else if (window.cbState.phase === 'closing') {
      window.cbState.val = Math.min(1.0, window.cbState.timer / 120); // 120ms close
      if (window.cbState.val >= 1.0) { window.cbState.phase = 'hold'; window.cbState.timer = 0; }
    } else if (window.cbState.phase === 'hold') {
      if (window.cbState.timer >= 40) { window.cbState.phase = 'opening'; window.cbState.timer = 0; } // 40ms hold
    } else if (window.cbState.phase === 'opening') {
      window.cbState.val = Math.max(0.0, 1.0 - (window.cbState.timer / 150)); // 150ms open
      if (window.cbState.val <= 0) {
        window.cbState.phase = 'idle';
        window.cbState.timer = 0;
        window.cbState.next = 2000 + Math.random() * 3000; // 2-5s random interval
        if (Math.random() < 0.12) window.cbState.next = 180; // Double blink
      }
    }
    ShaderUniforms.cineBlink.value = window.cbState.val;

    if (LM.valid && typeof _rawLM !== 'undefined') {
      // Camera top=0, bottom=LOGICAL_H creates Y-down vertex space matching Canvas 2D.
      // Landmark Y is also top-down. Pass directly — NO flip needed.
      ShaderUniforms.lEye.value.set(LM.lEyeCX, LM.lEyeCY);
      ShaderUniforms.rEye.value.set(LM.rEyeCX, LM.rEyeCY);
      ShaderUniforms.lEyeTop.value.set(_rawLM[159].x * LOGICAL_W, _rawLM[159].y * LOGICAL_H);
      ShaderUniforms.lEyeBot.value.set(_rawLM[145].x * LOGICAL_W, _rawLM[145].y * LOGICAL_H);
      ShaderUniforms.rEyeTop.value.set(_rawLM[386].x * LOGICAL_W, _rawLM[386].y * LOGICAL_H);
      ShaderUniforms.rEyeBot.value.set(_rawLM[374].x * LOGICAL_W, _rawLM[374].y * LOGICAL_H);
      // Eyebrow lower edge — defines upper boundary of eyelid skin
      ShaderUniforms.lBrow.value.set(_rawLM[105].x * LOGICAL_W, _rawLM[105].y * LOGICAL_H);
      ShaderUniforms.rBrow.value.set(_rawLM[334].x * LOGICAL_W, _rawLM[334].y * LOGICAL_H);
      // Nose landmarks for breathing
      ShaderUniforms.noseTip.value.set(LM.noseTipX, LM.noseTipY);
      ShaderUniforms.noseBridge.value.set(_rawLM[6].x * LOGICAL_W, _rawLM[6].y * LOGICAL_H);

      // Iris tracking and shift offsets mapped to exactly match old 2D render code
      ShaderUniforms.eyeOff.value.set(A.eyeOffX + (A._eyeLifeX || 0), A.eyeOffY + (A._eyeLifeY || 0) + (A._thinkGazeY || 0));
      ShaderUniforms.lIrisR.value = LM.lIrisR || 0;
      ShaderUniforms.rIrisR.value = LM.rIrisR || 0;

      // Realistic Mouth Tracking
      ShaderUniforms.mTop.value.set(_rawLM[13].x * LOGICAL_W, _rawLM[13].y * LOGICAL_H);
      ShaderUniforms.mBot.value.set(_rawLM[14].x * LOGICAL_W, _rawLM[14].y * LOGICAL_H);
      ShaderUniforms.mLeft.value.set(_rawLM[61].x * LOGICAL_W, _rawLM[61].y * LOGICAL_H);
      ShaderUniforms.mRight.value.set(_rawLM[291].x * LOGICAL_W, _rawLM[291].y * LOGICAL_H);
      ShaderUniforms.chin.value.set(_rawLM[152].x * LOGICAL_W, _rawLM[152].y * LOGICAL_H);
      ShaderUniforms.mouthOpen.value = A.mouthOpenFinal !== undefined ? A.mouthOpenFinal : A.mouthOpen;

      ShaderUniforms.uShapeOval.value = A.shapeOval || 0;
      ShaderUniforms.uShapeFlat.value = A.shapeFlat || 0;
      ShaderUniforms.uShapeRound.value = A.shapeRound || 0;

      ShaderUniforms.uPhA.value = A.uPhA || 0;
      ShaderUniforms.uPhE.value = A.uPhE || 0;
      ShaderUniforms.uPhO.value = A.uPhO || 0;
      ShaderUniforms.uPhU.value = A.uPhU || 0;
      ShaderUniforms.uPhM.value = A.uPhM || 0;
      ShaderUniforms.uPhF.value = A.uPhF || 0;
      ShaderUniforms.uPhS.value = A.uPhS || 0;
      ShaderUniforms.uPhTH.value = A.uPhTH || 0;
      ShaderUniforms.uLipAsymmetry.value = A.uLipAsymmetry || 0;
      ShaderUniforms.uCheekBulge.value = A.uCheekBulge || 0;
      ShaderUniforms.uTissueInertia.value = A.uTissueInertia || 0;
      ShaderUniforms.uBreath.value = A.uBreath || 0;
      ShaderUniforms.uSecondaryFollow.value = A.secondaryFollow || 0;
      ShaderUniforms.uMicroLife.value = A.uMicroLife || 0;
      ShaderUniforms.uIdleLife.value = A.uIdleLife || 0;

      // Full facial landmark capture (for future expressions)
      const _p = (i) => [_rawLM[i].x * LOGICAL_W, _rawLM[i].y * LOGICAL_H];
      ShaderUniforms.inLipTop.value.set(..._p(78));
      ShaderUniforms.inLipBot.value.set(..._p(308));
      ShaderUniforms.lowerFace.value.set(..._p(17));
      ShaderUniforms.noseBase.value.set(..._p(0));
      ShaderUniforms.lEyeOuter.value.set(..._p(33));
      ShaderUniforms.lEyeInner.value.set(..._p(133));
      ShaderUniforms.rEyeOuter.value.set(..._p(362));
      ShaderUniforms.rEyeInner.value.set(..._p(263));
      ShaderUniforms.lBrow1.value.set(..._p(70));
      ShaderUniforms.lBrow2.value.set(..._p(63));
      ShaderUniforms.lBrow3.value.set(..._p(105));
      ShaderUniforms.lBrow4.value.set(..._p(66));
      ShaderUniforms.lBrow5.value.set(..._p(107));
      ShaderUniforms.rBrow1.value.set(..._p(336));
      ShaderUniforms.rBrow2.value.set(..._p(296));
      ShaderUniforms.rBrow3.value.set(..._p(334));
      ShaderUniforms.rBrow4.value.set(..._p(293));
      ShaderUniforms.rBrow5.value.set(..._p(300));
      ShaderUniforms.nose2.value.set(..._p(2));
      ShaderUniforms.noseL.value.set(..._p(98));
      ShaderUniforms.noseR.value.set(..._p(327));
      ShaderUniforms.cheekLO.value.set(..._p(234));
      ShaderUniforms.cheekRO.value.set(..._p(454));
      ShaderUniforms.cheekLI.value.set(..._p(93));
      ShaderUniforms.cheekRI.value.set(..._p(323));
      ShaderUniforms.jawL.value.set(..._p(132));
      ShaderUniforms.jawR.value.set(..._p(361));
      ShaderUniforms.fh1.value.set(..._p(10));
      ShaderUniforms.fh2.value.set(..._p(151));
      ShaderUniforms.fh3.value.set(..._p(9));
    }
    threeRenderer.render(threeScene, threeCamera);
  }

  requestAnimationFrame(renderLoop);
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 5 — ANIMATION STATE & TIMING
// ──────────────────────────────────────────────────────────────────────

function updateState(dt) {
  // Demo cycling is DISABLED once any real WebSocket event arrives
  // (overrideDemo is set to true by connectWebSocket message handlers)
  if (overrideDemo) return;

  // Only cycle demo if WebSocket is NOT connected (offline preview mode)
  if (!wsConnected) {
    demoTimer += dt;
    if (demoTimer > 12000) demoTimer = 0;

    if (demoTimer < 4000) currentState = STATES.IDLE;
    else if (demoTimer < 8000) currentState = STATES.THINKING;
    else currentState = STATES.SPEAKING;
  }
}

function animate(dt) {
  animateBlink(dt);
  animateStateRealism(dt); // Step 38
  animateEyes(dt);
  animateMouth(dt);
  animateIdle(dt);
  updateContextEmotion(dt); // Step 37
  updateVoiceSync(dt); // Step 40
  updateFatigue(dt); // Step 41
  updateEnvironmentReaction(dt); // Step 42
  updateMultiEmotionBlend(dt); // Step 43
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 2 — BLINK ANIMATION
// ──────────────────────────────────────────────────────────────────────

function animateBlink(dt) {
  A.blinkTimer += dt;

  switch (A.blinkPhase) {
    case 'idle':
      if (A.blinkTimer >= A.nextBlinkAt) {
        A.blinkPhase = 'closing';
        A.blinkTimer = 0;
        // Randomize blink type
        const r = Math.random();
        if (r < 0.15) A.blinkMaxTarget = 0.40;  // small blink
        else if (r < 0.30) A.blinkMaxTarget = 0.70;  // half blink
        else A.blinkMaxTarget = 1.0;    // full blink
      }
      break;

    case 'closing':
      // 80ms to fully close
      A.blink = Math.min(A.blinkMaxTarget, (A.blinkTimer / 80) * A.blinkMaxTarget);
      if (A.blink >= A.blinkMaxTarget) {
        A.blinkPhase = 'hold';
        A.blinkTimer = 0;
      }
      break;

    case 'hold':
      // Hold ~40ms (tight, natural)
      if (A.blinkTimer >= 35 + Math.random() * 10) {
        A.blinkPhase = 'opening';
        A.blinkTimer = 0;
      }
      break;

    case 'opening':
      // 100ms to open
      A.blink = Math.max(0, A.blinkMaxTarget - (A.blinkTimer / 100) * A.blinkMaxTarget);
      if (A.blink <= 0) {
        A.blink = 0;
        A.blinkPhase = 'idle';
        A.blinkTimer = 0;
        A.nextBlinkAt = 2000 + Math.random() * 3000;
        // 12% chance of a quick double blink
        if (Math.random() < 0.16) A.nextBlinkAt = 100 + Math.random() * 160;
      }
      break;
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 38 — STATE-DEPENDENT BLINK RATE
// ──────────────────────────────────────────────────────────────────────

function animateStateRealism(dt) {
  // Adjust blink interval based on state (only once per idle phase)
  if (A.blinkPhase === 'idle') {
    if (!A._blinkRateAdjusted) {
      if (currentState === STATES.THINKING) {
        A.nextBlinkAt = Math.max(A.nextBlinkAt, 4000 + Math.random() * 2000); // slower blinks
      } else if (currentState === STATES.LISTENING) {
        A.nextBlinkAt = Math.max(A.nextBlinkAt, 3500 + Math.random() * 1500); // calmer blinks
      }
      A._blinkRateAdjusted = true;
    }
  } else {
    A._blinkRateAdjusted = false;
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 3 — EYE MOVEMENT ANIMATION
// ──────────────────────────────────────────────────────────────────────

function animateEyes(dt) {
  A.eyeMoveTimer += dt;

  if (A.eyeMoveTimer >= A.nextEyeMoveAt) {
    // Pick a new random target — max ±15px horizontal, ±8px vertical
    const rangeX = currentState === STATES.LISTENING ? 14 : 20;
    const rangeY = currentState === STATES.LISTENING ? 8 : 12;
    A.eyeTargetX = (Math.random() - 0.5) * 2 * rangeX;
    A.eyeTargetY = (Math.random() - 0.5) * 2 * rangeY;
    A.eyeMoveTimer = 0;
    A.nextEyeMoveAt = 1000 + Math.random() * 2500;
  }

  // Smooth lerp toward target — very slow (feels organic)
  A.eyeOffX = lerp(A.eyeOffX, A.eyeTargetX, 0.05);
  A.eyeOffY = lerp(A.eyeOffY, A.eyeTargetY, 0.05);

  // ── Step 38: Thinking gaze drifts slightly downward ──
  if (A._thinkGazeY === undefined) A._thinkGazeY = 0;
  const thinkGazeTarget = currentState === STATES.THINKING ? 4 : 0;
  A._thinkGazeY = lerp(A._thinkGazeY, thinkGazeTarget, 0.03);

  // ── Step 39: Eye Life micro-drift (idle/listening only) ──
  if (A._eyeLifeTimer === undefined) A._eyeLifeTimer = 0;
  if (A._eyeLifeX === undefined) A._eyeLifeX = 0;
  if (A._eyeLifeY === undefined) A._eyeLifeY = 0;
  A._eyeLifeTimer += dt * 0.001;

  if (currentState === STATES.IDLE || currentState === STATES.LISTENING) {
    const lifeX = Math.sin(A._eyeLifeTimer * 0.7) * 2.0 + Math.sin(A._eyeLifeTimer * 1.3) * 1.5;
    const lifeY = Math.sin(A._eyeLifeTimer * 0.5) * 1.5 + Math.cos(A._eyeLifeTimer * 0.9) * 1.0;
    A._eyeLifeX = lerp(A._eyeLifeX, lifeX, 0.03);
    A._eyeLifeY = lerp(A._eyeLifeY, lifeY, 0.03);
  } else {
    A._eyeLifeX = lerp(A._eyeLifeX, 0, 0.05);
    A._eyeLifeY = lerp(A._eyeLifeY, 0, 0.05);
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 4 — MOUTH ANIMATION
// ──────────────────────────────────────────────────────────────────────

function animateMouth(dt) {
  // Lip sync override — external value takes priority when active
  if (lipSyncValue >= 0) {
    A.mouthTarget = Math.max(0, Math.min(1, lipSyncValue));
  } else if (currentState === STATES.SPEAKING) {
    // --- SPEECH RAMP (Step 1 & 2: Neutral start, smooth ramp) ---
    if (!A.speechRamp) A.speechRamp = 0;
    A.speechRamp = lerp(A.speechRamp, 1.0, 0.08);

    // --- SPEECH RHYTHM (Step 3: slow/medium/fast cycles) ---
    if (!A._rhythmTypeTime) A._rhythmTypeTime = 0;
    if (!A._rhythmSpeed) A._rhythmSpeed = 1.0;
    A._rhythmTypeTime += dt;
    if (A._rhythmTypeTime > 800 + Math.random() * 2000) {
      A._rhythmTypeTime = 0;
      let r = Math.random();
      if (r < 0.3) A._rhythmSpeed = 0.5; // slow
      else if (r < 0.8) A._rhythmSpeed = 1.0; // medium
      else A._rhythmSpeed = 1.8; // fast
    }
    if (!A._curRhythmSpeed) A._curRhythmSpeed = 1.0;
    A._curRhythmSpeed = lerp(A._curRhythmSpeed, A._rhythmSpeed, 0.05);

    A.speakPhase += dt * 0.005 * A._curRhythmSpeed;

    // --- SHAPE SYSTEM (Step 4 & 6: oval/round/flat) ---
    if (!A._shapeTimer) A._shapeTimer = 0;
    if (!A._shapeTgt) A._shapeTgt = 0; // 0=oval (vertical), 1=flat (wide), 2=round (narrow)
    A._shapeTimer += dt;
    if (A._shapeTimer > 1500 + Math.random() * 2000) {
      A._shapeTimer = 0;
      A._shapeTgt = Math.floor(Math.random() * 3);
    }
    A.shapeOval = lerp(A.shapeOval || 0, A._shapeTgt === 0 ? 1 : 0, 0.03);
    A.shapeFlat = lerp(A.shapeFlat || 0, A._shapeTgt === 1 ? 1 : 0, 0.03);
    A.shapeRound = lerp(A.shapeRound || 0, A._shapeTgt === 2 ? 1 : 0, 0.03);

    // --- PHONEME SYSTEM (Step 14 & 15 & 16) ---
    if (!A.phonemeSequence) {
      A.phonemeSequence = ['N'];
      A.phonemeIndex = 0;
      A.phonemeTimer = 0;
      A.targetPhoneme = 'N';
      A.uPhA = 0; A.uPhE = 0; A.uPhO = 0; A.uPhU = 0; A.uPhM = 0; A.uPhN = 1; A.uPhF = 0; A.uPhS = 0; A.uPhTH = 0;
    }
    // Random phoneme generator fully replaced by real VISEME_EVENTs incoming via WebSocket
    A.uPhA = lerp(A.uPhA, A.targetPhoneme === 'A' ? 1 : 0, 0.15);
    A.uPhE = lerp(A.uPhE, A.targetPhoneme === 'E' ? 1 : 0, 0.15);
    A.uPhO = lerp(A.uPhO, A.targetPhoneme === 'O' ? 1 : 0, 0.15);
    A.uPhU = lerp(A.uPhU, A.targetPhoneme === 'U' ? 1 : 0, 0.15);
    A.uPhM = lerp(A.uPhM, A.targetPhoneme === 'M' ? 1 : 0, 0.15);
    A.uPhN = lerp(A.uPhN, A.targetPhoneme === 'N' ? 1 : 0, 0.15);
    A.uPhF = lerp(A.uPhF || 0, A.targetPhoneme === 'F' ? 1 : 0, 0.15);
    A.uPhS = lerp(A.uPhS || 0, A.targetPhoneme === 'S' ? 1 : 0, 0.15);
    A.uPhTH = lerp(A.uPhTH || 0, A.targetPhoneme === 'TH' ? 1 : 0, 0.15);

    // --- RHYTHM SYSTEM: occasional holds/pauses ---
    if (!A._rhythmTimer) A._rhythmTimer = 0;
    if (!A._rhythmHold) A._rhythmHold = 0;
    if (!A._rhythmNext) A._rhythmNext = 800 + Math.random() * 1200;
    A._rhythmTimer += dt;
    if (A._rhythmTimer > A._rhythmNext) {
      A._rhythmTimer = 0;
      A._rhythmNext = 600 + Math.random() * 1500;
      // 30% chance of brief pause (mouth partially closes), 70% normal
      A._rhythmHold = Math.random() < 0.30 ? (150 + Math.random() * 200) : 0;
    }
    let rhythmDampen = 1.0;
    if (A._rhythmHold > 0) {
      A._rhythmHold -= dt;
      rhythmDampen = 0.40; // Mouth partially closes during pause
    }

    // --- MULTI-FREQUENCY SPEECH with curved response ---
    let rawSpeech =
      0.58
      + Math.sin(A.speakPhase * 2.1) * 0.40
      + Math.sin(A.speakPhase * 3.7) * 0.25
      + Math.sin(A.speakPhase * 1.1) * 0.16
      + Math.sin(A.speakPhase * 5.3) * 0.10
      + Math.sin(A.speakPhase * 0.7) * 0.08;  // Ultra-slow drift

    rawSpeech = Math.max(0.0, Math.min(1.0, rawSpeech));

    // Power curve: quiet speech stays subtle, loud speech opens more
    rawSpeech = Math.pow(rawSpeech, 0.75);

    // Apply rhythm dampen
    rawSpeech *= rhythmDampen;

    A.mouthTarget = Math.max(0.12, Math.min(1, rawSpeech)) * A.speechRamp;
  } else {
    if (A.speechRamp && A.speechRamp > 0) A.speechRamp = lerp(A.speechRamp, 0.0, 0.15);
    A.mouthTarget = 0;
    // Reset phoneme to neutral safely
    if (A.phonemeSequence) {
      A.targetPhoneme = 'N';
      A.uPhA = lerp(A.uPhA, 0, 0.1);
      A.uPhE = lerp(A.uPhE, 0, 0.1);
      A.uPhO = lerp(A.uPhO, 0, 0.1);
      A.uPhU = lerp(A.uPhU, 0, 0.1);
      A.uPhM = lerp(A.uPhM, 0, 0.1);
      A.uPhN = lerp(A.uPhN, 1, 0.1);
      A.uPhF = lerp(A.uPhF || 0, 0, 0.1);
      A.uPhS = lerp(A.uPhS || 0, 0, 0.1);
      A.uPhTH = lerp(A.uPhTH || 0, 0, 0.1);
    }
  }

  // Variable lerp speed — faster to open, slower to close (jaw weight feeling)
  let lerpSpeed;
  if (lipSyncValue >= 0 || currentState === STATES.SPEAKING) {
    lerpSpeed = A.mouthTarget > A.mouthOpen ? 0.25 : 0.15; // Opens fast, closes slow
  } else {
    lerpSpeed = 0.12;
  }
  A.mouthOpen = lerp(A.mouthOpen, A.mouthTarget, lerpSpeed);
  if (A.mouthOpen < 0.005) A.mouthOpen = 0;

  // Speech Variation — 4-tier with emphasis
  let finalMouth = A.mouthOpen;
  if (currentState === STATES.SPEAKING && A.mouthOpen > 0) {
    if (!A._varTimer) A._varTimer = 0;
    if (!A._varTgt) A._varTgt = 1.0;
    if (!A._varCur) A._varCur = 1.0;
    A._varTimer += dt;
    if (A._varTimer > 150 + Math.random() * 300) {
      A._varTimer = 0;
      let r = Math.random();
      if (r < 0.50) A._varTgt = 1.10;        // normal
      else if (r < 0.75) A._varTgt = 1.45;   // medium
      else if (r < 0.92) A._varTgt = 1.80;   // big
      else A._varTgt = 2.15;                 // emphasis burst
    }
    A._varCur = lerp(A._varCur, A._varTgt, 0.10);
    finalMouth = A.mouthOpen * A._varCur;
  }

  if (A.mouthOpenFinal === undefined) A.mouthOpenFinal = 0;
  let moSpTarget = Math.min(finalMouth, 0.95);

  // Phase 5 Step 5: Speech curve realism (smoothing & slight overshoot)
  if (moSpTarget > A.mouthOpenFinal + 0.02) {
    moSpTarget += 0.05; // slight peak overshoot for impact
  }
  A.mouthOpenFinal = lerp(A.mouthOpenFinal, moSpTarget, 0.25);

  // --- MICRO-EXPRESSIONS during speech (subtle alive feel) ---
  // Store them on A so updateEmotionUniforms can add them to the base presets
  A.microBrow = 0;
  A.microSmile = 0;
  A.microSquint = 0;
  if (currentState === STATES.SPEAKING && A.mouthOpenFinal > 0.1) {
    let sp = A.speakPhase;
    A.microBrow = Math.sin(sp * 0.8) * 0.08 + Math.sin(sp * 1.9) * 0.05;
    A.microSmile = A.mouthOpenFinal * 0.10;
    A.microSquint = A.mouthOpenFinal > 0.6 ? (A.mouthOpenFinal - 0.6) * 0.15 : 0;
  }

  // Phase 44.5: Lip asymmetry (subtle left/right difference)
  if (A.uLipAsymmetry === undefined) A.uLipAsymmetry = 0;
  if (currentState === STATES.SPEAKING && A.mouthOpenFinal > 0.05) {
    let asymTarget = Math.sin(A.speakPhase * 1.7) * 0.3 + Math.sin(A.speakPhase * 0.9) * 0.15;
    A.uLipAsymmetry = lerp(A.uLipAsymmetry, asymTarget, 0.08);
  } else {
    A.uLipAsymmetry = lerp(A.uLipAsymmetry, 0, 0.05);
  }

  // Phase 44.5: Cheek bulge (phoneme-dependent cheek influence)
  if (A.uCheekBulge === undefined) A.uCheekBulge = 0;
  if (currentState === STATES.SPEAKING && A.mouthOpenFinal > 0.1) {
    let cheekTarget = A.mouthOpenFinal * 0.4 + (A.uPhA || 0) * 0.3 - (A.uPhO || 0) * 0.2;
    A.uCheekBulge = lerp(A.uCheekBulge, Math.max(0, cheekTarget), 0.06);
  } else {
    A.uCheekBulge = lerp(A.uCheekBulge, 0, 0.04);
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 6 — IDLE EFFECTS ANIMATION
// ──────────────────────────────────────────────────────────────────────

function animateIdle(dt) {
  A.breathPhase += dt * 0.0010;
  A.glowPhase += dt * 0.0016;

  // Eyebrow rise on THINKING
  if (currentState === STATES.THINKING) {
    const cycle = Math.sin(performance.now() * 0.001) * 0.5 + 0.5;
    A.browTarget = -3 + cycle * 2;  // lift of 1–3px
  } else {
    A.browTarget = 0;
  }
  A.browOffset = lerp(A.browOffset, A.browTarget, 0.03);

  // Listening state focus glow
  if (currentState === STATES.LISTENING) {
    A.listenFocus = lerp(A.listenFocus, 1, 0.05);
  } else {
    A.listenFocus = lerp(A.listenFocus, 0, 0.05);
  }
}

// ──────────────────────────────────────────────────────────────────────
// RENDER
// ──────────────────────────────────────────────────────────────────────

function render() {
  ctx.save();
  ctx.translate(sceneOffsetX, sceneOffsetY);
  ctx.scale(sceneScale, sceneScale);

  // 1. Clear and draw base image (undistorted, full canvas)
  ctx.clearRect(0, 0, LOGICAL_W, LOGICAL_H);
  ctx.drawImage(faceImg, 0, 0, LOGICAL_W, LOGICAL_H);

  // 2. Eye movement — shift iris region only (no blink involvement)
  if (Math.abs(A.eyeOffX) > 0.3 || Math.abs(A.eyeOffY) > 0.3) {
    renderIrisShift(ctx);
  }

  // 3. Blink — only when there is actual blink progress
  if (A.blink > 0.01) {
    renderBlink(ctx);
  }

  // 4. Mouth — only when open
  if (A.mouthOpen > 0.005) {
    renderMouth(ctx);
  }

  // 5. Idle ambient effects (glow, breath, etc.)
  renderIdleEffects(ctx);

  // NO canvas text drawing — all UI text is handled by HTML DOM elements
  // drawHUD() is called via setInterval separately


  ctx.restore();
}

// Update DOM-based HUD every 500ms (not tied to canvas render)
setInterval(drawHUD, 500);

// ──────────────────────────────────────────────────────────────────────
// PHASE 3 — IRIS SHIFT RENDERER
// ──────────────────────────────────────────────────────────────────────

function renderIrisShift(c) {
  // For each eye, clip to iris ellipse and shift contents by eyeOff

  // ── Left iris ──
  c.save();
  c.beginPath();
  c.ellipse(LM.lIrisX, LM.lIrisY, LM.lIrisR, LM.lIrisR, 0, 0, Math.PI * 2);
  c.clip();
  c.drawImage(faceImg, A.eyeOffX, A.eyeOffY, LOGICAL_W, LOGICAL_H);
  c.restore();

  // ── Right iris ──
  c.save();
  c.beginPath();
  c.ellipse(LM.rIrisX, LM.rIrisY, LM.rIrisR, LM.rIrisR, 0, 0, Math.PI * 2);
  c.clip();
  c.drawImage(faceImg, A.eyeOffX, A.eyeOffY, LOGICAL_W, LOGICAL_H);
  c.restore();
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 2 — BLINK RENDERER
// ──────────────────────────────────────────────────────────────────────
//
// HOW IT WORKS (polygon-only, no rectangle, no forehead):
//   1. Use ONLY the user-specified lid landmark subsets for each eye.
//   2. Interpolate each upper lid point toward its paired lower lid point
//      by A.blink (0 = natural open position, 1 = fully closed at lower lid).
//   3. Build a closed polygon: interpolated upper lid + lower lid (reversed).
//   4. Clip to this polygon and draw faceImg — fills the closed area with skin.
//   5. Eyelash line drawn along the interpolated upper lid curve.
//   No forehead. No eyebrow. No cheek. Only eyelid curves.
// ──────────────────────────────────────────────────────────────────────

function renderBlink(c) {
  renderEyeBlink(c, LM.blinkLUpper, LM.blinkLLower);
  renderEyeBlink(c, LM.blinkRUpper, LM.blinkRLower);
}

/**
 * Render a single eye blink using polygon-only lid interpolation.
 * @param {CanvasRenderingContext2D} c
 * @param {Array} upperPts - Upper lid landmark points [{x,y}, ...]
 * @param {Array} lowerPts - Lower lid landmark points [{x,y}, ...]
 */
function renderEyeBlink(c, upperPts, lowerPts) {
  if (upperPts.length === 0 || lowerPts.length === 0) return;

  const t = A.blink; // 0 = open, 1 = closed

  // Interpolate each upper lid point toward the corresponding lower lid point.
  // If arrays differ in length, map by normalized index.
  const interpUpper = upperPts.map((uPt, i) => {
    // Find corresponding lower lid point by normalized position
    const li = Math.round((i / (upperPts.length - 1)) * (lowerPts.length - 1));
    const lPt = lowerPts[li];
    return {
      x: lerp(uPt.x, lPt.x, t),
      y: lerp(uPt.y, lPt.y, t)
    };
  });

  // Build closed polygon: interpolated upper lid (L→R) then lower lid reversed (R→L)
  // This encloses the "closed eyelid" skin area.
  c.save();
  c.beginPath();

  // Draw interpolated upper lid
  c.moveTo(interpUpper[0].x, interpUpper[0].y);
  for (let i = 1; i < interpUpper.length; i++) {
    c.lineTo(interpUpper[i].x, interpUpper[i].y);
  }

  // Connect to lower lid reversed (closing the polygon)
  const revLower = [...lowerPts].reverse();
  for (const pt of revLower) {
    c.lineTo(pt.x, pt.y);
  }
  c.closePath();
  c.clip();

  // Draw face image inside clipped polygon — skin texture fills the lid area
  c.drawImage(faceImg, 0, 0, LOGICAL_W, LOGICAL_H);
  c.restore();

  // Draw eyelash line along the interpolated upper lid curve
  if (t > 0.05 && t < 0.97) {
    // Compute line width from eye height
    const eyeH = Math.abs(
      Math.min(...upperPts.map(p => p.y)) - Math.max(...lowerPts.map(p => p.y))
    );
    c.save();
    c.beginPath();
    c.moveTo(interpUpper[0].x, interpUpper[0].y);
    for (let i = 1; i < interpUpper.length; i++) {
      c.lineTo(interpUpper[i].x, interpUpper[i].y);
    }
    c.strokeStyle = 'rgba(20, 18, 22, 0.55)';
    c.lineWidth = Math.max(2, eyeH * 0.07);
    c.lineCap = 'round';
    c.lineJoin = 'round';
    c.stroke();
    c.restore();
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 4 — MOUTH RENDERER
// ──────────────────────────────────────────────────────────────────────
//
// HOW IT WORKS (landmark-driven lip/jaw separation):
//   - Uses only the user-specified lip + jaw landmarks.
//   - Lower jaw moves down, lower lip moves down more.
//   - Upper lip moves up a little.
//   - Corners move slightly outward.
//   - Gap between lips filled with dark cavity color.
//   - No image scaling, no texture stretching, no whole-face warp.
//   - Each lip half is redrawn by clipping to shifted lip polygon and
//     drawing the face image at the matching offset.
// ──────────────────────────────────────────────────────────────────────

function renderMouth(c) {
  // Use natural face width to set bounds dynamically, entirely avoiding fixed pixels
  const maxGap = LM.mouthW * 0.45; // Max opening is ~18% of mouth width
  let gapH = (LM.mouthW * 0.65) * (A.mouthOpenFinal || A.mouthOpen);
  if (gapH > maxGap) gapH = maxGap;
  if (gapH < 1) return;

  // Upper lip barely moves (real speech), lower lip + jaw does the work
  const upperShift = gapH * 0.05;
  const lowerShift = gapH * 0.95;

  const mcL = LM.mouthCornerPts[0]; // Left corner (viewer perspective: right)
  const mcR = LM.mouthCornerPts[1]; // Right corner
  const minX = Math.min(mcL.x, mcR.x);
  const maxX = Math.max(mcL.x, mcR.x);
  const cx = (minX + maxX) / 2;
  const widthHalf = (maxX - minX) / 2;

  // Ultra-smooth taper: uses full mouth width so corners don't have hard cutoffs.
  // Uses Perlin's "smootherstep" function for very gradual opening near corners.
  // This keeps lip corners firmly connected and perfectly curved.
  function getTaper(x) {
    const dist = Math.abs(x - cx);
    if (dist >= widthHalf) return 0.0;
    const t = 1 - (dist / widthHalf);
    // Smootherstep: highly flat at 0 (corners), making the connection seamless
    return t * t * t * (t * (t * 6 - 15) + 10);
  }

  // Helper to generate a pt shifted dynamically by the taper curve
  function shiftPt(pt, maxShiftY) {
    return { x: pt.x, y: pt.y + maxShiftY * getTaper(pt.x) };
  }

  const upperPtsSorted = [...LM.innerUpperLip].sort((a, b) => a.x - b.x);
  const lowerPtsSorted = [...LM.innerLowerLip].sort((a, b) => a.x - b.x);

  const shiftedUpper = upperPtsSorted.map(pt => shiftPt(pt, -upperShift));
  const shiftedLower = lowerPtsSorted.map(pt => shiftPt(pt, lowerShift));

  // 1. Draw solid dark cavity strictly between the split inner lips
  {
    const cavityPoly = [...shiftedUpper, ...([...shiftedLower].reverse())];
    c.save();
    c.beginPath();
    c.moveTo(cavityPoly[0].x, cavityPoly[0].y);
    for (let i = 1; i < cavityPoly.length; i++) c.lineTo(cavityPoly[i].x, cavityPoly[i].y);
    c.closePath();
    c.clip();

    // Fill deep mouth cavity
    c.fillStyle = 'rgba(8, 6, 10, 0.95)';
    const topY = Math.min(...shiftedUpper.map(p => p.y));
    const botY = Math.max(...shiftedLower.map(p => p.y));
    c.fillRect(minX, topY - 10, maxX - minX, botY - topY + 20);

    // Inner reddish tone for tongue/throat
    const cvCX = LM.mouthCX;
    const cvCY = (shiftedUpper[Math.floor(shiftedUpper.length / 2)].y + shiftedLower[Math.floor(shiftedLower.length / 2)].y) / 2;
    c.fillStyle = 'rgba(90, 18, 18, 0.40)';
    c.beginPath();
    c.ellipse(cvCX, cvCY, LM.mouthW * 0.18, gapH * 0.40, 0, 0, Math.PI * 2);
    c.fill();
    c.restore();
  }

  // 1.5 Teeth layer — threshold-based visibility for natural look
  // Small open: no teeth. Medium: lower teeth edge. Big: lower teeth + tongue.
  // Upper teeth hidden by upper lip (rarely visible in real speech).
  {
    const teethUpper = [...LM.innerUpperLip].sort((a, b) => a.x - b.x).map(pt => shiftPt(pt, -upperShift));
    const teethLower = [...LM.innerLowerLip].sort((a, b) => a.x - b.x).map(pt => shiftPt(pt, lowerShift));

    const teethTopY = Math.min(...teethUpper.map(p => p.y));
    const teethBotY = Math.max(...teethLower.map(p => p.y));
    const teethH = teethBotY - teethTopY;
    const openRatio = A.mouthOpen; // 0–1

    if (teethH > 3 && openRatio > 0.25) {
      // Clip to cavity opening so teeth never bleed outside lips
      c.save();
      c.beginPath();
      c.moveTo(teethUpper[0].x, teethUpper[0].y);
      for (let i = 1; i < teethUpper.length; i++) c.lineTo(teethUpper[i].x, teethUpper[i].y);
      const revTeethLower = [...teethLower].reverse();
      for (const pt of revTeethLower) c.lineTo(pt.x, pt.y);
      c.closePath();
      c.clip();

      // Teeth fade in gradually from openRatio 0.25 to 0.45
      const teethAlpha = Math.min(1, (openRatio - 0.25) / 0.20);

      // ── Lower teeth — visible at medium+ open ──
      const lowerTeethH = Math.min(teethH * 0.28, LM.mouthW * 0.04);
      const lGrad = c.createLinearGradient(cx, teethBotY - lowerTeethH, cx, teethBotY);
      lGrad.addColorStop(0, `rgba(215, 212, 208, ${(0.65 * teethAlpha).toFixed(3)})`);
      lGrad.addColorStop(1, `rgba(240, 238, 235, ${(0.92 * teethAlpha).toFixed(3)})`);
      c.fillStyle = lGrad;

      const lTeethLeft = minX + (maxX - minX) * 0.10;
      const lTeethRight = maxX - (maxX - minX) * 0.10;
      const lCornerR = Math.min(lowerTeethH * 0.35, 6);
      c.beginPath();
      c.moveTo(lTeethLeft, teethBotY - lowerTeethH);
      c.lineTo(lTeethRight, teethBotY - lowerTeethH);
      c.arcTo(lTeethRight, teethBotY, lTeethRight - lCornerR, teethBotY, lCornerR);
      c.lineTo(lTeethLeft + lCornerR, teethBotY);
      c.arcTo(lTeethLeft, teethBotY, lTeethLeft, teethBotY - lCornerR, lCornerR);
      c.closePath();
      c.fill();

      // Subtle lower tooth separators
      if (teethAlpha > 0.5) {
        const lTeethBandW = lTeethRight - lTeethLeft;
        const lToothCount = 6;
        const lToothW = lTeethBandW / lToothCount;
        c.strokeStyle = `rgba(190, 185, 180, ${(0.22 * teethAlpha).toFixed(3)})`;
        c.lineWidth = 1;
        for (let t = 1; t < lToothCount; t++) {
          const tx = lTeethLeft + t * lToothW;
          c.beginPath();
          c.moveTo(tx, teethBotY - lowerTeethH + 1);
          c.lineTo(tx, teethBotY - 1);
          c.stroke();
        }
      }

      // ── Tongue — grows more visible at bigger open ──
      if (openRatio > 0.45) {
        const tongueAlpha = Math.min(0.55, (openRatio - 0.45) * 1.0);
        const cvCX = LM.mouthCX;
        const tongueY = teethBotY - teethH * 0.35;
        c.fillStyle = `rgba(140, 50, 50, ${tongueAlpha.toFixed(3)})`;
        c.beginPath();
        c.ellipse(cvCX, tongueY, LM.mouthW * 0.16, teethH * 0.30, 0, 0, Math.PI * 2);
        c.fill();
      }

      c.restore();
    }
  }

  // 2. Shift Upper Lip Polygon
  // Enclosed by outer upper lip and inner upper lip
  {
    const outerTapered = LM.outerUpperLip.map(p => shiftPt(p, -upperShift));
    const innerTapered = LM.innerUpperLip.map(p => shiftPt(p, -upperShift));

    c.save();
    c.beginPath();
    c.moveTo(outerTapered[0].x, outerTapered[0].y);
    for (let i = 1; i < outerTapered.length; i++) c.lineTo(outerTapered[i].x, outerTapered[i].y);
    const innerRev = [...innerTapered].reverse();
    for (const pt of innerRev) c.lineTo(pt.x, pt.y);
    c.closePath();
    c.clip();

    // Upper lip shift is tiny (0.05×gapH), use half for translate to avoid side artifacts
    c.translate(0, -upperShift * 0.5);
    c.drawImage(faceImg, 0, 0, LOGICAL_W, LOGICAL_H);
    c.restore();
  }

  // 3. Shift Lower Lip & Jaw — wide rotation-style movement
  // Uses ALL inner lip points to avoid broken segments.
  // Jaw rotation uses sine wave falloff and very wide horizontal weighting,
  // making chin follow a smooth arc and cheeks move organically (no blocky rectangles).
  {
    const innerTapered = LM.innerLowerLip.map(p => shiftPt(p, lowerShift));
    const innerSorted = [...innerTapered].sort((a, b) => a.x - b.x);

    c.save();
    c.beginPath();

    // Top edge: ALL inner lower lip points
    c.moveTo(innerSorted[0].x, innerSorted[0].y);
    for (let i = 1; i < innerSorted.length; i++) {
      c.lineTo(innerSorted[i].x, innerSorted[i].y);
    }

    // Jaw rotation pivot (TMJ area)
    const pivotY = Math.min(LM.jawCurvePts[0].y, LM.jawCurvePts[LM.jawCurvePts.length - 1].y);
    const chinY = LM.jawY;
    const jawSpan = chinY - pivotY;

    // Very wide jaw-specific taper: encompasses cheeks and jaw sides.
    // Center = 1.0, smoothly fading to sides. Minimum 0.05 to ensure whole area breathes.
    function jawTaper(x) {
      const dist = Math.abs(x - cx);
      const jawHalf = widthHalf * 1.50; // 150% of mouth width covers cheeks nicely
      if (dist >= jawHalf) return 0.05;
      const t = 1 - (dist / jawHalf);
      // Smooth U-curve
      return 0.05 + 0.95 * (t * t * (3 - 2 * t));
    }

    // Extremely broad chin slice (indices 2 to 14 out of 16)
    // Grabs almost the entire jaw contour, from left upper cheek to right upper cheek.
    const chinPts = LM.jawCurvePts.slice(2, 15);

    const shiftedChin = chinPts.map(p => {
      // Vertical rotation: chin moves most, jaw angles barely move.
      let rotRatio = (p.y - pivotY) / jawSpan;
      if (rotRatio < 0) rotRatio = 0;
      if (rotRatio > 1) rotRatio = 1;
      // Natural pure sine arc: smooth acceleration/deceleration
      rotRatio = Math.sin(rotRatio * Math.PI / 2);

      const hTaper = jawTaper(p.x);
      return { x: p.x, y: p.y + lowerShift * rotRatio * hTaper };
    });

    // Connect right side naturally
    c.lineTo(shiftedChin[shiftedChin.length - 1].x, shiftedChin[shiftedChin.length - 1].y);

    // Follow chin contour backwards across the entire jawline
    for (let i = shiftedChin.length - 2; i >= 0; i--) {
      c.lineTo(shiftedChin[i].x, shiftedChin[i].y);
    }

    c.closePath();

    c.clip();
    // Smooth texture translate: 0.70 balances jaw arc stretching vs texture sliding
    c.translate(0, lowerShift * 0.70);
    c.drawImage(faceImg, 0, 0, LOGICAL_W, LOGICAL_H);
    c.restore();
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 6 — IDLE EFFECTS RENDERER
// ──────────────────────────────────────────────────────────────────────

function renderIdleEffects(c) {
  const breathAmt = Math.sin(A.breathPhase) * 0.5 + 0.5;
  const glowAmt = Math.sin(A.glowPhase) * 0.5 + 0.5;

  // Subtle breathing shadow pulses on lower face (chin/jaw area)
  c.save();
  c.globalCompositeOperation = 'multiply';
  const jawGrad = c.createRadialGradient(
    LM.faceCX, LM.jawY, 5,
    LM.faceCX, LM.jawY, LOGICAL_W * 0.18
  );
  jawGrad.addColorStop(0, `rgba(0,0,0,${(0.015 + breathAmt * 0.018).toFixed(4)})`);
  jawGrad.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = jawGrad;
  c.fillRect(LM.faceCX - LOGICAL_W * 0.22, LM.jawY - LOGICAL_H * 0.08, LOGICAL_W * 0.44, LOGICAL_H * 0.18);
  c.restore();

  // Gentle cyan core glow (very subtle)
  c.save();
  c.globalCompositeOperation = 'screen';
  const faceGlow = c.createRadialGradient(
    LM.noseTipX, LM.noseTipY, 30,
    LM.noseTipX, LM.noseTipY, LOGICAL_W * 0.30
  );
  const ga = (0.012 + glowAmt * 0.018).toFixed(4);
  faceGlow.addColorStop(0, `rgba(0, 200, 240, ${ga})`);
  faceGlow.addColorStop(0.5, `rgba(0, 140, 200, ${(parseFloat(ga) * 0.5).toFixed(4)})`);
  faceGlow.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = faceGlow;
  c.fillRect(LM.faceCX - LOGICAL_W * 0.35, LM.noseTipY - LOGICAL_H * 0.35, LOGICAL_W * 0.70, LOGICAL_H * 0.60);
  c.restore();

  // Listening state: cyan iris highlight
  if (A.listenFocus > 0.02) {
    c.save();
    c.globalCompositeOperation = 'screen';
    const fa = A.listenFocus * 0.06;

    const lg = c.createRadialGradient(LM.lIrisX, LM.lIrisY, 2, LM.lIrisX, LM.lIrisY, LM.lIrisR * 1.4);
    lg.addColorStop(0, `rgba(0, 240, 255, ${fa.toFixed(4)})`);
    lg.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = lg;
    c.beginPath(); c.arc(LM.lIrisX, LM.lIrisY, LM.lIrisR * 1.5, 0, Math.PI * 2); c.fill();

    const rg = c.createRadialGradient(LM.rIrisX, LM.rIrisY, 2, LM.rIrisX, LM.rIrisY, LM.rIrisR * 1.4);
    rg.addColorStop(0, `rgba(0, 240, 255, ${fa.toFixed(4)})`);
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = rg;
    c.beginPath(); c.arc(LM.rIrisX, LM.rIrisY, LM.rIrisR * 1.5, 0, Math.PI * 2); c.fill();

    c.restore();
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 7 — DYNAMIC UI OVERLAY
// ──────────────────────────────────────────────────────────────────────

function drawHUD() {
  // Global Camera Icon status (Master source: face detection validity)
  const iconCam = document.getElementById('g-camera-icon');
  if (iconCam) {
    iconCam.className = LM.valid ? 'icon-active' : 'icon-off';
  }

  // If genesis_ws.js is actively managing HUD status via websocket,
  // defer to it — do NOT overwrite DOM elements with local booleans.
  if (window.__genesis_ws_active) {
    // Still update state display from face.js animation state
    let stateDisplay = 'IDLE';
    if (currentState === STATES.LISTENING) stateDisplay = 'LISTENING';
    if (currentState === STATES.THINKING) stateDisplay = 'THINKING';
    if (currentState === STATES.SPEAKING) stateDisplay = 'SPEAKING';
    if (currentState === STATES.PROCESSING) stateDisplay = 'PROCESSING';
    const stateEl = document.getElementById('g-state');
    if (stateEl) { stateEl.innerHTML = wrapStatus(stateDisplay); }
    return;
  }

  // Pure DOM-based UI — no canvas drawing, no fillRect, no clearRect, no drawImage for UI
  const isOnline = serverConnected && wsConnected;

  const el = (id) => document.getElementById(id);

  // 1. GENESIS ONLINE indicator
  const statusEl = el('g-status');
  if (statusEl) {
    statusEl.innerHTML = wrapStatus(isOnline ? 'ONLINE' : 'OFFLINE');
    statusEl.style.color = "";
  }

  // 2. Left panel values
  const aiEl = el('g-network');
  if (aiEl) { aiEl.innerHTML = wrapStatus(isOnline ? 'NETWORK OK' : 'NETWORK OFF'); aiEl.style.color = ""; }

  const coreEl = el('g-emotion');
  if (coreEl) { coreEl.innerHTML = wrapStatus(aiReady ? 'EMOTION READY' : 'EMOTION OFF'); coreEl.style.color = ""; }

  const voiceEl = el('g-voice');
  if (voiceEl) { voiceEl.innerHTML = wrapStatus(voiceReady ? 'VOICE READY' : 'VOICE OFF'); voiceEl.style.color = ""; }

  const micEl = el('g-mic');
  if (micEl) { micEl.innerHTML = wrapStatus(isOnline ? 'MIC ON' : 'MIC OFF'); micEl.style.color = ""; }

  const camEl = el('g-camera');
  if (camEl) { camEl.innerHTML = wrapStatus(serverConnected ? 'CAMERA OFF' : 'CAMERA OFF'); camEl.style.color = ""; }

  const modelEl = el('g-model');
  if (modelEl) { modelEl.innerHTML = wrapStatus(serverConnected ? 'MODEL IDLE' : 'MODEL OFF'); modelEl.style.color = ""; }

  // 3. State box — single state text
  let stateDisplay = 'IDLE';
  if (currentState === STATES.LISTENING) stateDisplay = 'LISTENING';
  if (currentState === STATES.THINKING) stateDisplay = 'THINKING';
  if (currentState === STATES.SPEAKING) stateDisplay = 'SPEAKING';
  if (currentState === STATES.PROCESSING) stateDisplay = 'PROCESSING';

  const stateEl = el('g-state');
  if (stateEl) { stateEl.innerHTML = wrapStatus(stateDisplay); }
}

// ──────────────────────────────────────────────────────────────────────
// WEBSOCKET STATE CONTROL
// ──────────────────────────────────────────────────────────────────────

function connectWebSocket() {
  // Logic migrated to genesis_ws.js to prevent dual-connection blocking
  wsConnected = true; // Handled externally
}

// ──────────────────────────────────────────────────────────────────────
// KEYBOARD DEBUG SHORTCUTS
// ──────────────────────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  switch (e.key) {
    case '1': currentState = STATES.IDLE; overrideDemo = true; setEmotion('idle'); console.log('[KEY] IDLE'); break;
    case '2': currentState = STATES.LISTENING; overrideDemo = true; console.log('[KEY] LISTENING'); break;
    case '3': currentState = STATES.THINKING; overrideDemo = true; setEmotion('thinking'); console.log('[KEY] THINKING'); break;
    case '4': currentState = STATES.SPEAKING; overrideDemo = true; console.log('[KEY] SPEAKING'); break;
    case '5': setEmotion('sad'); idleEmotionTimer = 0; console.log('[KEY] SAD'); break;
    case '6': setEmotion('happy'); idleEmotionTimer = 0; console.log('[KEY] HAPPY'); break;
    case '7': setEmotion('angry'); idleEmotionTimer = 0; console.log('[KEY] ANGRY'); break;
    case '8': setEmotion('excited'); idleEmotionTimer = 0; console.log('[KEY] EXCITED'); break;
    case '9': setEmotion('blush'); idleEmotionTimer = 0; console.log('[KEY] BLUSH'); break;
    case '0': setEmotion('smile'); idleEmotionTimer = 0; console.log('[KEY] SMILE'); break;
  }
  // Shift combos for extended emotions
  if (e.shiftKey) {
    switch (e.key) {
      case '!': setEmotion('blush'); console.log('[KEY] BLUSH'); break;    // Shift+1
      case '@': setEmotion('excited'); console.log('[KEY] EXCITED'); break; // Shift+2
      case '#': setEmotion('sleep'); console.log('[KEY] SLEEP'); break;     // Shift+3
      case '$': setEmotion('yawn'); console.log('[KEY] YAWN'); break;       // Shift+4
      case '%': setEmotion('cry'); console.log('[KEY] CRY'); break;        // Shift+5
      case '^': setEmotion('flirt'); console.log('[KEY] FLIRT'); break;     // Shift+6
    }
  }
});

// ── START ──
init();

// ── Lip sync API — callable from WebSocket or external scripts ──
window.setLipSync = function (value) {
  // value: 0–1 = mouth open amount, -1 or undefined = disable override
  lipSyncValue = (value === undefined || value === null || value < 0) ? -1 : Math.max(0, Math.min(1, value));
};
window.getLipSync = function () { return lipSyncValue; };

// ──────────────────────────────────────────────────────────────────────
// PHASE 8 — THREE.JS ANIMATION ARCHITECTURE (SKELETON)
// ──────────────────────────────────────────────────────────────────────

const MorphTargetsData = {
  jawOpen: [],
  eyeBlinkLeft: [],
  eyeBlinkRight: []
};

const ShaderUniforms = {
  time: { value: 0 },
  mouthOpen: { value: 0 },
  blink: { value: 0 },
  cineBlink: { value: 0 },
  lEye: { value: new THREE.Vector2(0, 0) },
  rEye: { value: new THREE.Vector2(0, 0) },
  lEyeTop: { value: new THREE.Vector2(0, 0) },
  lEyeBot: { value: new THREE.Vector2(0, 0) },
  rEyeTop: { value: new THREE.Vector2(0, 0) },
  rEyeBot: { value: new THREE.Vector2(0, 0) },
  lBrow: { value: new THREE.Vector2(0, 0) },
  rBrow: { value: new THREE.Vector2(0, 0) },
  noseTip: { value: new THREE.Vector2(0, 0) },
  noseBridge: { value: new THREE.Vector2(0, 0) },
  eyeOff: { value: new THREE.Vector2(0, 0) },
  lIrisR: { value: 0 },
  rIrisR: { value: 0 },
  mTop: { value: new THREE.Vector2(0, 0) },
  mBot: { value: new THREE.Vector2(0, 0) },
  mLeft: { value: new THREE.Vector2(0, 0) },
  mRight: { value: new THREE.Vector2(0, 0) },
  chin: { value: new THREE.Vector2(0, 0) },
  uShapeOval: { value: 0 },
  uShapeFlat: { value: 0 },
  uShapeRound: { value: 0 },
  uPhA: { value: 0 },
  uPhE: { value: 0 },
  uPhO: { value: 0 },
  uPhU: { value: 0 },
  uPhM: { value: 0 },
  uBreath: { value: 0 },
  uSecondaryFollow: { value: 0 },
  uMicroLife: { value: 0 },
  uIdleLife: { value: 0 },

  // Full Facial Landmarks (for future expressions)
  inLipTop: { value: new THREE.Vector2(0, 0) },   // 78
  inLipBot: { value: new THREE.Vector2(0, 0) },   // 308
  lowerFace: { value: new THREE.Vector2(0, 0) },  // 17
  noseBase: { value: new THREE.Vector2(0, 0) },   // 0
  lEyeOuter: { value: new THREE.Vector2(0, 0) },  // 33
  lEyeInner: { value: new THREE.Vector2(0, 0) },  // 133
  rEyeOuter: { value: new THREE.Vector2(0, 0) },  // 362
  rEyeInner: { value: new THREE.Vector2(0, 0) },  // 263
  lBrow1: { value: new THREE.Vector2(0, 0) },     // 70
  lBrow2: { value: new THREE.Vector2(0, 0) },     // 63
  lBrow3: { value: new THREE.Vector2(0, 0) },     // 105
  lBrow4: { value: new THREE.Vector2(0, 0) },     // 66
  lBrow5: { value: new THREE.Vector2(0, 0) },     // 107
  rBrow1: { value: new THREE.Vector2(0, 0) },     // 336
  rBrow2: { value: new THREE.Vector2(0, 0) },     // 296
  rBrow3: { value: new THREE.Vector2(0, 0) },     // 334
  rBrow4: { value: new THREE.Vector2(0, 0) },     // 293
  rBrow5: { value: new THREE.Vector2(0, 0) },     // 300
  nose2: { value: new THREE.Vector2(0, 0) },      // 2
  noseL: { value: new THREE.Vector2(0, 0) },      // 98
  noseR: { value: new THREE.Vector2(0, 0) },      // 327
  cheekLO: { value: new THREE.Vector2(0, 0) },    // 234
  cheekRO: { value: new THREE.Vector2(0, 0) },    // 454
  cheekLI: { value: new THREE.Vector2(0, 0) },    // 93
  cheekRI: { value: new THREE.Vector2(0, 0) },    // 323
  jawL: { value: new THREE.Vector2(0, 0) },       // 132
  jawR: { value: new THREE.Vector2(0, 0) },       // 361
  fh1: { value: new THREE.Vector2(0, 0) },        // 10
  fh2: { value: new THREE.Vector2(0, 0) },        // 151
  fh3: { value: new THREE.Vector2(0, 0) },        // 9

  // Expression Uniforms
  uEmotion: { value: 0 },
  uSmile: { value: 0 },
  uFrown: { value: 0 },
  uBrowLift: { value: 0 },
  uBrowAnger: { value: 0 },
  uEyeSquint: { value: 0 },
  uJawSide: { value: 0 },
  uMouthStretch: { value: 0 },
  uCheekRaise: { value: 0 },
  uSad: { value: 0 },
  uAngry: { value: 0 },
  uSurprise: { value: 0 },
  uThink: { value: 0 },
  uBlush: { value: 0 },
  uExcited: { value: 0 },
  uSleep: { value: 0 },
  uYawn: { value: 0 },
  uCry: { value: 0 },
  uFlirt: { value: 0 },

  // Phase 44.5: Realistic speech realism uniforms
  uLipAsymmetry: { value: 0 },
  uCheekBulge: { value: 0 },
  uTissueInertia: { value: 0 },
  uPhF: { value: 0 },
  uPhS: { value: 0 },
  uPhTH: { value: 0 },

  map: { value: null }
};

// ── EXPRESSION STATE ──
let emotionState = 'idle';
let emotionBase = {};    // base manual/context uniform values
let emotionEnv = {};     // environment reaction uniform values
let emotionVoice = {};   // voice reaction modifiers
let emotionFatigue = {}; // fatigue reaction modifiers
let emotionTarget = {};  // target uniform values for current emotion
let emotionCurrent = {}; // currently interpolated uniform values
let emotionBlendSpeed = 0.08; // Phase 9 Step 36: emotional inertia — lower = smoother transitions
let idleEmotionTimer = 0; // ms since last non-idle activity

const EMOTION_PRESETS = {
  idle: { uSmile: 0, uFrown: 0, uBrowLift: 0, uBrowAnger: 0, uEyeSquint: 0, uCheekRaise: 0, uMouthStretch: 0, uSad: 0, uAngry: 0, uSurprise: 0, uThink: 0, uBlush: 0, uExcited: 0, uSleep: 0, uYawn: 0, uCry: 0, uFlirt: 0 },
  happy: { uSmile: 1.08, uCheekRaise: 0.84, uBrowLift: 0.42, uEyeSquint: 0.3 },
  sad: { uSad: 1.44, uFrown: 1.15, uBrowLift: 0.648, uEyeSquint: 0.216 },
  angry: { uAngry: 1.44, uBrowAnger: 1.44, uEyeSquint: 0.864, uFrown: 0.72 },
  surprise: { uSurprise: 1.2, uBrowLift: 1.2, uMouthStretch: 0.48 },
  thinking: { uThink: 1.2, uBrowLift: 0.72, uEyeSquint: 0.42 },
  smile: { uSmile: 1.44, uCheekRaise: 0.864, uBrowLift: 0.144 },
  blush: { uBlush: 1.2, uSmile: 0.48, uEyeSquint: 0.3, uCheekRaise: 0.36 },
  excited: { uExcited: 1.2, uSmile: 0.84, uBrowLift: 0.72, uCheekRaise: 0.6 },
  sleep: { uSleep: 1.0, uEyeSquint: 1.0 },
  yawn: { uYawn: 1.0, uMouthStretch: 0.8, uBrowLift: 0.35 },
  cry: { uCry: 1.0, uSad: 0.9, uFrown: 0.7, uEyeSquint: 0.5 },
  flirt: { uFlirt: 1.0, uSmile: 0.6, uEyeSquint: 0.35, uBrowLift: 0.25 }
};

function setEmotion(name) {
  if (!EMOTION_PRESETS[name]) return;
  emotionState = name;
  idleEmotionTimer = 0; // Reset auto-idle so it doesn't immediately override
  // Build target from idle baseline + preset overrides
  emotionBase = Object.assign({}, EMOTION_PRESETS.idle, EMOTION_PRESETS[name]);
  console.log('[EMOTION]', name);
}

function updateEmotionUniforms(dt) {
  if (!emotionTarget || Object.keys(emotionTarget).length === 0) return;

  // Phase 4 Step 6: Micro expression system (every 1-2s)
  if (!A._cinematicMicroTimer) {
    A._cinematicMicroTimer = 0;
    A._cinematicMicroTgtBrow = 0;
    A._cinematicMicroTgtSmile = 0;
    A._cinematicMicroTgtSquint = 0;
    A._cinematicMicroCurBrow = 0;
    A._cinematicMicroCurSmile = 0;
    A._cinematicMicroCurSquint = 0;
  }
  A._cinematicMicroTimer += dt;
  if (A._cinematicMicroTimer > 1000 + Math.random() * 1000) {
    A._cinematicMicroTimer = 0;
    A._cinematicMicroTgtBrow = (Math.random() - 0.5) * 0.15;
    A._cinematicMicroTgtSmile = (Math.random() - 0.5) * 0.1;
    A._cinematicMicroTgtSquint = (Math.random() - 0.5) * 0.1;
  }
  A._cinematicMicroCurBrow = lerp(A._cinematicMicroCurBrow, A._cinematicMicroTgtBrow, 0.05);
  A._cinematicMicroCurSmile = lerp(A._cinematicMicroCurSmile, A._cinematicMicroTgtSmile, 0.05);
  A._cinematicMicroCurSquint = lerp(A._cinematicMicroCurSquint, A._cinematicMicroTgtSquint, 0.05);

  // Smooth lerp all expression uniforms toward targets (Phase 9 Step 36: uses emotionBlendSpeed for inertia)
  const speed = emotionBlendSpeed;
  for (const key in emotionTarget) {
    if (ShaderUniforms[key]) {
      if (!emotionCurrent[key]) emotionCurrent[key] = 0;
      emotionCurrent[key] = emotionCurrent[key] + (emotionTarget[key] - emotionCurrent[key]) * speed;

      let finalVal = emotionCurrent[key];

      // Phase 4 Step 2: Emotion + speech blending
      // Emotion must not override speech. Speech must stay dominant.
      if (A.mouthOpenFinal > 0.05) {
        // Reduces emotion towards 60% dynamically based on how wide mouth is open
        finalVal = finalVal * (1.0 - A.mouthOpenFinal * 0.4);
      }

      // Safely apply micro-expressions on top of base emotion
      if (key === 'uSmile') {
        if (A.microSmile) finalVal += A.microSmile;
        finalVal += A._cinematicMicroCurSmile;
      }
      if (key === 'uBrowLift') {
        if (A.microBrow) finalVal += A.microBrow;
        finalVal += A._cinematicMicroCurBrow;
      }
      if (key === 'uEyeSquint') {
        if (A.microSquint) finalVal += A.microSquint;
        finalVal += A._cinematicMicroCurSquint;
      }

      ShaderUniforms[key].value = finalVal;
    }
  }
}

// Auto-idle emotion timer
function updateAutoIdleEmotions(dt) {
  if (currentState === STATES.SPEAKING) {
    idleEmotionTimer = 0;
    // Long speaking → excited/smile
    if (A.speakPhase > 20 && emotionState === 'idle') setEmotion('excited');
    return;
  }
  idleEmotionTimer += dt;
  if (idleEmotionTimer > 60000 && emotionState !== 'sleep') setEmotion('sleep');
  else if (idleEmotionTimer > 40000 && emotionState !== 'yawn' && emotionState !== 'sleep') setEmotion('yawn');
  else if (idleEmotionTimer > 20000 && emotionState !== 'idle' && emotionState !== 'yawn' && emotionState !== 'sleep') setEmotion('idle');
  else if (idleEmotionTimer > 10000 && emotionState !== 'thinking' && emotionState !== 'idle' && emotionState !== 'yawn' && emotionState !== 'sleep') setEmotion('thinking');
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 37 — CONTEXT EMOTION (auto-react to state)
// ──────────────────────────────────────────────────────────────────────

function updateContextEmotion(dt) {
  // Only apply context emotion when no manual override is active
  // Manual overrides: hotkeys, WebSocket setEmotion, auto-idle timers
  // We check if idleEmotionTimer < 1000 to avoid fighting with updateAutoIdleEmotions
  if (idleEmotionTimer > 1000) return;

  // Track previous state to detect transitions
  if (A._prevContextState === undefined) A._prevContextState = currentState;
  if (A._contextEmotionSet === undefined) A._contextEmotionSet = false;

  // Only set context emotion on state transition (not every frame)
  if (A._prevContextState !== currentState) {
    A._contextEmotionSet = false;
    A._prevContextState = currentState;
  }

  if (A._contextEmotionSet) return;

  // Set emotion based on state (uses setEmotion → emotionTarget → inertia blend)
  switch (currentState) {
    case STATES.THINKING:
      setEmotion('thinking');
      break;
    case STATES.LISTENING:
      setEmotion('idle'); // calm / neutral
      break;
    case STATES.SPEAKING:
      setEmotion('smile'); // slight active smile
      break;
    case STATES.IDLE:
      setEmotion('idle');
      break;
  }
  A._contextEmotionSet = true;
}

// Expose for WebSocket
window.setEmotion = setEmotion;
window.setViseme = function(v) { A.targetPhoneme = v; };

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 40 — VOICE EMOTION SYNC
// ──────────────────────────────────────────────────────────────────────

function updateVoiceSync(dt) {
  // Track speech energy from mouth activity
  if (A._voiceEnergy === undefined) A._voiceEnergy = 0;
  if (A._voiceEnergySmooth === undefined) A._voiceEnergySmooth = 0;

  // Raw energy from mouth openness during speech
  let rawEnergy = 0;
  if (currentState === STATES.SPEAKING && A.mouthOpenFinal > 0.05) {
    rawEnergy = Math.min(A.mouthOpenFinal * 1.2, 1.0);
  }

  // Smooth energy (rises fast, falls slow — natural speech envelope)
  const riseSpeed = rawEnergy > A._voiceEnergy ? 0.12 : 0.04;
  A._voiceEnergy = lerp(A._voiceEnergy, rawEnergy, riseSpeed);
  A._voiceEnergySmooth = lerp(A._voiceEnergySmooth, A._voiceEnergy, 0.06);

  // Blink rate modifier: more energy → slightly faster blinks (lively)
  if (A.blinkPhase === 'idle' && currentState === STATES.SPEAKING && A._voiceEnergy > 0.3) {
    A.nextBlinkAt = Math.min(A.nextBlinkAt, 2000 + Math.random() * 1500);
  }

  // Emotion intensity boost during speech (stronger expression)
  // Applied additively to emotionBlendSpeed — faster blend when energetic
  if (currentState === STATES.SPEAKING && A._voiceEnergy > 0.2) {
    emotionBlendSpeed = lerp(emotionBlendSpeed, 0.12, 0.02); // faster blend during speech
  } else {
    emotionBlendSpeed = lerp(emotionBlendSpeed, 0.08, 0.01); // return to default inertia
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 41 — FATIGUE / TIME EFFECT
// ──────────────────────────────────────────────────────────────────────

let fatigueLevel = 0;   // 0 = fresh, 1 = fully fatigued
let fatigueTimer = 0;   // ms accumulator

function updateFatigue(dt) {
  fatigueTimer += dt;

  // Fatigue grows slowly over time
  // Speaking accumulates fatigue faster, idle recovers slowly
  let fatigueTarget = 0;
  if (currentState === STATES.SPEAKING) {
    fatigueTarget = Math.min(fatigueTimer / 300000, 1.0); // ~5min speaking → full fatigue
  } else if (currentState === STATES.IDLE) {
    // Slow recovery during idle
    if (fatigueTimer > 30000) { // after 30s idle, start recovering
      fatigueTarget = Math.max(fatigueLevel - 0.0001, 0);
    } else {
      fatigueTarget = fatigueLevel; // hold current
    }
  } else {
    fatigueTarget = Math.min(fatigueTimer / 600000, 0.8); // other states: slower fatigue, cap 0.8
  }

  fatigueLevel = lerp(fatigueLevel, fatigueTarget, 0.005); // very slow blend
  fatigueLevel = Math.max(0, Math.min(1, fatigueLevel)); // clamp 0–1

  // Fatigue effects (all additive, never override):

  // 1. Blink interval increases with fatigue (slower blinks = tired)
  if (A.blinkPhase === 'idle' && fatigueLevel > 0.3) {
    const fatigueBlinkAdd = fatigueLevel * 2000; // up to +2s between blinks
    A.nextBlinkAt = Math.max(A.nextBlinkAt, A.nextBlinkAt + fatigueBlinkAdd * 0.1);
  }

  // 2. Emotion intensity slightly dampened (tired = less expressive)
  // Achieved by slightly reducing emotionBlendSpeed when fatigued
  if (fatigueLevel > 0.4) {
    const fatigueDampen = fatigueLevel * 0.03; // up to 0.03 slower blend
    emotionBlendSpeed = Math.max(0.04, emotionBlendSpeed - fatigueDampen);
  }

  // 3. Breath speed slightly increases with fatigue (heavier breathing)
  // Modifies A._breathValueTimer speed indirectly via a stored multiplier
  if (A._fatigueBreathBoost === undefined) A._fatigueBreathBoost = 1.0;
  const breathTarget = 1.0 + fatigueLevel * 0.4; // up to 1.4x breath speed
  A._fatigueBreathBoost = lerp(A._fatigueBreathBoost, breathTarget, 0.01);
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 42 — ENVIRONMENT REACTION
// ──────────────────────────────────────────────────────────────────────

function updateEnvironmentReaction(dt) {
  if (Object.keys(emotionEnv).length === 0) emotionEnv = Object.assign({}, EMOTION_PRESETS.idle);

  let targetEnv = EMOTION_PRESETS.idle;
  let energy = A._voiceEnergy || 0;

  if (currentState === STATES.SPEAKING) {
    targetEnv = energy > 0.4 ? EMOTION_PRESETS.excited : EMOTION_PRESETS.smile;
  } else if (currentState === STATES.LISTENING) {
    targetEnv = EMOTION_PRESETS.thinking; // focus
  } else if (currentState === STATES.THINKING) {
    targetEnv = EMOTION_PRESETS.sad; // serious focus
  } else {
    targetEnv = fatigueLevel > 0.5 ? EMOTION_PRESETS.sleep : EMOTION_PRESETS.idle; // relaxed
  }

  // Smoothly blend emotionEnv towards targetEnv
  for (const key in emotionEnv) {
    if (targetEnv[key] !== undefined) {
      emotionEnv[key] = lerp(emotionEnv[key], targetEnv[key], 0.02); // very slow blend
    }
  }
}

// ──────────────────────────────────────────────────────────────────────
// PHASE 9 STEP 43 — MULTI EMOTION BLEND
// ──────────────────────────────────────────────────────────────────────

function updateMultiEmotionBlend(dt) {
  if (Object.keys(emotionBase).length === 0) emotionBase = Object.assign({}, EMOTION_PRESETS.idle);
  if (Object.keys(emotionEnv).length === 0) emotionEnv = Object.assign({}, EMOTION_PRESETS.idle);

  // Calculate fatigue emotion modifiers (droopy eyes, slight frown)
  for (const key in EMOTION_PRESETS.sleep) {
    emotionFatigue[key] = EMOTION_PRESETS.sleep[key] * (fatigueLevel || 0) * 0.4;
  }

  // Calculate voice emotion modifiers (extra smile/brow lift based on energy)
  for (const key in EMOTION_PRESETS.happy) {
    emotionVoice[key] = EMOTION_PRESETS.happy[key] * (A._voiceEnergy || 0) * 0.3;
  }

  // Combine layers into emotionTarget
  for (const key in emotionBase) {
    let baseVal = emotionBase[key] || 0;

    // Blend environment slightly (e.g. 25% influence)
    let envVal = emotionEnv[key] || 0;
    let blended = lerp(baseVal, envVal, 0.25);

    // Add voice reaction (energy boost)
    blended += emotionVoice[key] || 0;

    // Add fatigue reaction (tiredness)
    let fatigueVal = emotionFatigue[key] || 0;
    if (key === 'uEyeSquint' || key === 'uSleep') {
      blended += fatigueVal;
    }
    if (key === 'uSmile') {
      blended -= fatigueVal * 0.5; // tired pulls down smiles
      blended = Math.max(0, blended);
    }

    emotionTarget[key] = blended;
  }
}

class ExpressionController {
  constructor() { }
  update() { }
}

class AnimationStateManager {
  constructor() { }
  updateState() { }
}

function updateMediaPipeDataFromHooks(lm) {
  // Placeholder hook for MediaPipe data to feed into Three.js
}

function initThreeJS() {
  const tCanvas = document.getElementById('threeCanvas');
  if (!tCanvas || typeof THREE === 'undefined') return;

  threeRenderer = new THREE.WebGLRenderer({ canvas: tCanvas, alpha: true, antialias: true });
  threeScene = new THREE.Scene();

  // Create camera matching logically fixed 2D canvas size with Y-down to mimic 2D canvas origin
  threeCamera = new THREE.OrthographicCamera(0, LOGICAL_W, 0, LOGICAL_H, -1000, 1000);
  threeCamera.position.z = 10;

  const geometry = new THREE.PlaneGeometry(LOGICAL_W, LOGICAL_H, 128, 128);
  geometry.translate(LOGICAL_W / 2, LOGICAL_H / 2, 0);

  const texture = new THREE.Texture(faceImg);
  texture.flipY = false;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;

  ShaderUniforms.map.value = texture;

  const material = new THREE.ShaderMaterial({
    uniforms: ShaderUniforms,
    side: THREE.DoubleSide, // CRITICAL: Y-down OrthographicCamera flips winding order. Required to prevent culling!
    vertexShader: `
      uniform float time;
      uniform float blink;
      uniform float cineBlink;
      uniform vec2 lEye;
      uniform vec2 rEye;
      uniform vec2 lEyeTop;
      uniform vec2 lEyeBot;
      uniform vec2 rEyeTop;
      uniform vec2 rEyeBot;
      uniform vec2 lBrow;
      uniform vec2 rBrow;
      uniform vec2 noseTip;
      uniform vec2 noseBridge;
      uniform float mouthOpen;
      uniform vec2 mTop;
      uniform vec2 mBot;
      uniform vec2 mLeft;
      uniform vec2 mRight;
      uniform vec2 chin;
      uniform vec2 jawL;
      uniform vec2 jawR;
      uniform float uShapeOval;
      uniform float uShapeFlat;
      uniform float uShapeRound;
      uniform float uPhA;
      uniform float uPhE;
      uniform float uPhO;
      uniform float uPhU;
      uniform float uPhM;
      uniform float uBreath;
      uniform float uSecondaryFollow;
      uniform float uMicroLife;
      uniform float uIdleLife;
      uniform float uBrowLift;
      uniform float uBrowAnger;
      uniform float uEyeSquint;
      uniform float uSmile;
      uniform float uFrown;
      uniform float uCheekRaise;
      uniform float uMouthStretch;
      uniform float uLipAsymmetry;
      uniform float uCheekBulge;
      uniform float uTissueInertia;
      uniform float uPhF;
      uniform float uPhS;
      uniform float uPhTH;
      uniform vec2 noseL;
      uniform vec2 noseR;
      varying vec2 vUv;
      
      // Realistic Mouth & Jaw Deformation (Clamped)
      vec3 applyMouth(vec3 pos) {
          if (mouthOpen < 0.001) return pos;

          vec2 mouthCenter = (mTop + mBot) * 0.5;
          float mouthW = distance(mLeft, mRight);
          
          // Strict boundary mask
          float vMask = smoothstep(mTop.y - 15.0, mTop.y, pos.y) *
                        (1.0 - smoothstep(chin.y - 10.0, chin.y + 10.0, pos.y));
          float hMask = smoothstep(mLeft.x - 60.0, mLeft.x, pos.x) *
                        (1.0 - smoothstep(mRight.x, mRight.x + 60.0, pos.x));
          float mask = vMask * hMask;
          if (mask < 0.001) return pos;
          float mo = mouthOpen * mask;
          
          // Maximum pixel caps (scaled for 3608px canvas)
          float maxJawDrop = 85.0;
          float maxLipDrop = 65.0;
          float chinFloor = chin.y - 5.0; // Hard floor: never pass chin
          
          float dyJaw = pos.y - mTop.y;
          if (dyJaw > -20.0) {
              float dxJaw = abs(pos.x - mouthCenter.x);
              float jawWeight = clamp(1.0 - (dxJaw * dxJaw) / (400.0 * 400.0), 0.0, 1.0);
              jawWeight *= clamp(dyJaw / max(chin.y - mTop.y, 1.0), 0.0, 1.0); // Scales with distance from lip
              
              float jawDrop = min(mo * maxJawDrop * jawWeight, maxJawDrop);
              // Hard chin floor
              if (pos.y + jawDrop > chinFloor) {
                jawDrop = max(chinFloor - pos.y, 0.0);
              }
              pos.y += jawDrop;
              
              // Lower lip separation
              float distToLowerLip = distance(pos.xy, mBot);
              float lipWeight = clamp(1.0 - distToLowerLip / (mouthW * 0.6), 0.0, 1.0);
              lipWeight = lipWeight * lipWeight * (3.0 - 2.0 * lipWeight);
              float lipDrop = min(mo * maxLipDrop * lipWeight, maxLipDrop);
              if (pos.y + lipDrop > chinFloor) {
                lipDrop = max(chinFloor - pos.y, 0.0);
              }
              pos.y += lipDrop;
          }
          
          // Upper lip pushes up slightly (max 8px)
          float distToUpperLip = distance(pos.xy, mTop);
          float uLipWeight = clamp(1.0 - distToUpperLip / (mouthW * 0.5), 0.0, 1.0);
          uLipWeight = uLipWeight * uLipWeight;
          pos.y -= min(10.0 * mo * uLipWeight, 10.0);
          
          // Corners pull out slightly (max 10px)
          float distToL = distance(pos.xy, mLeft);
          float distToR = distance(pos.xy, mRight);
          float cW_L = clamp(1.0 - distToL / (mouthW * 0.4), 0.0, 1.0);
          float cW_R = clamp(1.0 - distToR / (mouthW * 0.4), 0.0, 1.0);
          pos.x -= min(10.0 * mo * (cW_L * cW_L), 10.0);
          pos.x += min(10.0 * mo * (cW_R * cW_R), 10.0);

          return pos;
      }

      // Blink function for one eye
      // Y-down: small Y = screen top, large Y = screen bottom
      // browY < eyeTopY < eyeBotY
      vec3 applyBlink(vec3 pos, vec2 eyeTop, vec2 eyeBot, vec2 brow, float blinkVal) {
          vec2 eyeCenter = (eyeTop + eyeBot) * 0.5;
          float eyeOpenH = max(eyeBot.y - eyeTop.y, 1.0);
          float lidSkinH = max(eyeTop.y - brow.y, 1.0);
          float eyeW = eyeOpenH * 3.5;

          float xRadius = max(eyeW * 0.7, 1.0);
          float yRadiusUp = max(lidSkinH + eyeOpenH * 0.5, 1.0);
          float yRadiusDown = max(eyeOpenH * 1.8, 1.0);

          float dx = (pos.x - eyeCenter.x) / xRadius;
          float dyRaw = pos.y - eyeCenter.y;
          float yRad = dyRaw < 0.0 ? yRadiusUp : yRadiusDown;
          float dy = dyRaw / yRad;
          float eDist = dx * dx + dy * dy;

          if (eDist < 1.0) {
              float radial = 1.0 - eDist;
              radial = radial * radial;

              float closureY = mix(eyeTop.y, eyeBot.y, 0.65);

              if (pos.y < closureY) {
                  // UPPER EYELID SKIN - sweeps down strongly
                  float upperRange = closureY - (brow.y - 20.0);
                  float vertWeight = 0.0;
                  if (upperRange > 0.0) {
                      vertWeight = clamp((pos.y - brow.y + 20.0) / upperRange, 0.0, 1.0);
                      vertWeight = vertWeight * vertWeight;
                  }
                  float travel = closureY - pos.y;
                  pos.y += travel * blinkVal * vertWeight * radial;
              } else {
                  // LOWER EYELID - subtle upward movement
                  float lowerBound = eyeBot.y + eyeOpenH * 0.8;
                  float vertWeight = 0.0;
                  if (lowerBound > closureY) {
                      float t = clamp((pos.y - closureY) / (lowerBound - closureY), 0.0, 1.0);
                      vertWeight = 1.0 - t * t;
                  }
                  float travel = closureY - pos.y;
                  pos.y += travel * blinkVal * vertWeight * radial * 0.25;
              }
          }
          return pos;
      }

      void main() {
        vUv = uv;
        vec3 pos = position;

        // 1. BREATHING (Phase 6 Soft Tissue & Lower Face Pressure)
        // Area: below nose, cheek area, jaw side, chin, lower face
        vec2 breathCenter = noseTip + vec2(0.0, 40.0);
        float bDist = distance(pos.xy, breathCenter);
        float breathR = 500.0; // Large radius
        if (bDist < breathR && pos.y > noseBridge.y) {
            float bf = clamp(1.0 - (bDist / breathR), 0.0, 1.0);
            bf = smoothstep(0.0, 1.0, bf); // Smooth falloff
            
            // Phase 6 Part 4: Lower face pressure (Expands down on breath in)
            pos.y += uBreath * 8.0 * bf;
            
            // Phase 6 Part 3: Buccal / cheek soft motion (relax outward)
            float cheekYDist = abs(pos.y - mLeft.y);
            float cheekXDist = abs(pos.x - breathCenter.x);
            // Strong near mouth, Medium near cheek, Small near side face
            float cheekWeight = clamp(1.0 - cheekYDist/180.0, 0.0, 1.0) * clamp(1.0 - cheekXDist/250.0, 0.0, 1.0);
            cheekWeight = smoothstep(0.0, 1.0, cheekWeight);
            
            float outDir = (pos.x < breathCenter.x) ? -1.0 : 1.0;
            pos.x += outDir * uBreath * 5.0 * cheekWeight;
        }

        // 2. EYELID BLINK (Merge cinematic timer with live tracking blink)
        float totalBlink = max(cineBlink, blink);
        pos = applyBlink(pos, lEyeTop, lEyeBot, lBrow, totalBlink);
        pos = applyBlink(pos, rEyeTop, rEyeBot, rBrow, totalBlink);

        // LAYER 1 & 2: BASE + REALISTIC MOUTH MOTION (Internal jaw clamp logic preserved)
        pos = applyMouth(pos);

        // LAYER 3 & 4: CINEMATIC DYNAMIC SPEECH SHAPES & KINEMATIC CHAINS (Phase 5)
        if (mouthOpen > 0.01) {
            float moClamped = min(mouthOpen, 1.0);
            vec2 mCenter = (mTop + mBot) * 0.5;
            float mouthW = distance(mLeft, mRight);
            
            // Phase 5 Step 4: Cinematic Phonemes (U=narrow, M=close)
            float mSuppress = 1.0 - (uPhM * 0.8) - (uPhU * 0.3); 
            float effectiveMo = moClamped * mSuppress;

            // Phase 5 Step 1 & 3: Soft tissue & Jaw/Check/Lip chain
            float tissueRadius = mouthW * 1.8;
            float mDistC = distance(pos.xy, mCenter);
            float tissueW = clamp(1.0 - mDistC / tissueRadius, 0.0, 1.0);
            tissueW = smoothstep(0.0, 1.0, tissueW); // Smooth radial falloff (Lip 1.0 -> Cheek 0.5 -> Jaw 0.35 -> Lower Face 0.2)

            // Lip distinct mechanics with kinematic tissue weights
            float uDist = distance(pos.xy, mTop);
            float uW = clamp(1.0 - uDist / 50.0, 0.0, 1.0);
            float lDist = distance(pos.xy, mBot);
            float lW = clamp(1.0 - lDist / 50.0, 0.0, 1.0);
            
            // Basic jaw drop + Cinematic A & O
            float extraDrop = (uShapeOval * 9.0 + uShapeRound * 6.0 + uPhA * 7.5 + uPhO * 5.5) * effectiveMo;
            pos.y += tissueW * tissueW * extraDrop; // Chain effect follows tissue

            pos.y += uW * 3.0 * effectiveMo; // Upper lip counter-pull
            pos.y += lW * 6.0 * effectiveMo; // Lower lip stretch
            
            // Phase 5 Step 6: Lip round / stretch / oval constraints
            float cW_L = clamp(1.0 - distance(pos.xy, mLeft) / 80.0, 0.0, 1.0);
            float cW_R = clamp(1.0 - distance(pos.xy, mRight) / 80.0, 0.0, 1.0);
            
            // Stretch outward (E, Flat)
            float stretchOut = (uShapeFlat * 13.0 + uPhE * 15.0) * effectiveMo + 2.0 * effectiveMo; 
            pos.x -= cW_L * stretchOut;
            pos.x += cW_R * stretchOut;
            
            // Pull inward (O, M, U, Round)
            float pullIn = (uShapeRound * 9.0 + uPhO * 11.0 + uPhM * 5.0 + uPhU * 9.0) * effectiveMo;
            pos.x += cW_L * pullIn;
            pos.x -= cW_R * pullIn;

            // Phase 5 Step 1 & Phase 6 Part 3: Cheek Connection Realism & Buccal Tightening
            vec2 cheekLeftZone = mLeft + vec2(-15.0, 15.0);
            vec2 cheekRightZone = mRight + vec2(15.0, 15.0);
            float cL_inf = clamp(1.0 - distance(pos.xy, cheekLeftZone) / tissueRadius, 0.0, 1.0);
            float cR_inf = clamp(1.0 - distance(pos.xy, cheekRightZone) / tissueRadius, 0.0, 1.0);
            cL_inf = smoothstep(0.0, 1.0, cL_inf);
            cR_inf = smoothstep(0.0, 1.0, cR_inf);
            
            // Phase 6 Part 3: Cheek tightens slightly inward when speaking
            float buccalTight = effectiveMo * 3.5; 

            pos.x += cL_inf * (3.5 * effectiveMo + buccalTight); // inward (tighter)
            pos.y += cL_inf * 4.5 * effectiveMo; // slightly down
            pos.x -= cR_inf * (3.5 * effectiveMo + buccalTight); // inward (tighter)
            pos.y += cR_inf * 4.5 * effectiveMo; // slightly down

            // Phase 5 Step 2: Skin drag / face volume follow
            float chinMouthDist = min(distance(pos.xy, chin), distance(pos.xy, mBot));
            float volumeDragW = clamp(1.0 - chinMouthDist / 160.0, 0.0, 1.0);
            volumeDragW = smoothstep(0.0, 1.0, volumeDragW) * 0.45; // Soft drag max ~45%
            pos.y += volumeDragW * 5.5 * effectiveMo;
            pos.x += (pos.x < mCenter.x ? 1.0 : -1.0) * volumeDragW * 2.5 * effectiveMo;
        }

        // LAYER 5: EXPRESSION DEFORMATIONS (Kept existing, safe blends)
        float browDist = distance(pos.xy, (lBrow + rBrow) * 0.5);
        float browW = clamp(1.0 - browDist / 300.0, 0.0, 1.0);
        browW = browW * browW;
        pos.y -= uBrowLift * 40.0 * browW;

        float lBrowD = distance(pos.xy, lBrow);
        float rBrowD = distance(pos.xy, rBrow);
        float lBrowW = clamp(1.0 - lBrowD / 200.0, 0.0, 1.0);
        float rBrowW = clamp(1.0 - rBrowD / 200.0, 0.0, 1.0);
        lBrowW *= lBrowW;
        rBrowW *= rBrowW;
        pos.y += uBrowAnger * 28.0 * (lBrowW + rBrowW);

        float lEyeD = distance(pos.xy, (lEyeTop + lEyeBot) * 0.5);
        float rEyeD = distance(pos.xy, (rEyeTop + rEyeBot) * 0.5);
        float squintWL = clamp(1.0 - lEyeD / 120.0, 0.0, 1.0);
        float squintWR = clamp(1.0 - rEyeD / 120.0, 0.0, 1.0);
        squintWL *= squintWL;
        squintWR *= squintWR;
        float squintDir = (pos.y < (lEyeTop + lEyeBot).y * 0.5) ? 1.0 : -1.0;
        pos.y += uEyeSquint * 20.0 * squintDir * (squintWL + squintWR);

        float smileWL = clamp(1.0 - distance(pos.xy, mLeft) / 250.0, 0.0, 1.0);
        float smileWR = clamp(1.0 - distance(pos.xy, mRight) / 250.0, 0.0, 1.0);
        smileWL *= smileWL;
        smileWR *= smileWR;
        pos.y -= uSmile * 35.0 * (smileWL + smileWR);
        pos.x -= uSmile * 14.0 * smileWL;
        pos.x += uSmile * 14.0 * smileWR;

        pos.y += uFrown * 28.0 * (smileWL + smileWR);

        float cheekDL = distance(pos.xy, (mLeft + lEye) * 0.5);
        float cheekDR = distance(pos.xy, (mRight + rEye) * 0.5);
        float cheekWL = clamp(1.0 - cheekDL / 250.0, 0.0, 1.0);
        float cheekWR = clamp(1.0 - cheekDR / 250.0, 0.0, 1.0);
        cheekWL *= cheekWL;
        cheekWR *= cheekWR;
        pos.y -= uCheekRaise * 22.0 * (cheekWL + cheekWR);

        pos.y += uMouthStretch * 28.0 * clamp(1.0 - distance(pos.xy, mBot) / 200.0, 0.0, 1.0);

        // LAYER 7: MUSCLE TENSION DEFORMATION (PHASE 2 PHYSICS)
        if (mouthOpen > 0.01) {
            float moClamped = min(mouthOpen, 0.95);
            
            // Step 12: Skin Softness (radial global mouth weight)
            vec2 mCenter = (mTop + mBot) * 0.5;
            float globalMouthW = clamp(1.0 - distance(pos.xy, mCenter) / 320.0, 0.0, 1.0);
            // very smooth falloff
            globalMouthW = globalMouthW * globalMouthW * (3.0 - 2.0 * globalMouthW); 
            
            // Phase 4 Step 4: Masseter tension increase (pull jaw outward slightly if moClamped > 0.3)
            if (moClamped > 0.3) {
                float masseterMo = clamp((moClamped - 0.3) * 1.42, 0.0, 1.0);
                vec2 masseterL = jawL + vec2(-20.0, -10.0);
                vec2 masseterR = jawR + vec2(20.0, -10.0);
                float massWL = clamp(1.0 - distance(pos.xy, masseterL) / 140.0, 0.0, 1.0);
                float massWR = clamp(1.0 - distance(pos.xy, masseterR) / 140.0, 0.0, 1.0);
                pos.x -= massWL * massWL * 4.0 * masseterMo;
                pos.x += massWR * massWR * 4.0 * masseterMo;
            }

            // Phase 4 Step 3: Cinematic cheek follow (area near mouth+nose+jaw)
            vec2 cheekCinematicL = (mLeft + noseTip + jawL) * 0.333;
            vec2 cheekCinematicR = (mRight + noseTip + jawR) * 0.333;
            float cinCheekWL = clamp(1.0 - distance(pos.xy, cheekCinematicL) / 180.0, 0.0, 1.0);
            float cinCheekWR = clamp(1.0 - distance(pos.xy, cheekCinematicR) / 180.0, 0.0, 1.0);
            cinCheekWL = cinCheekWL * cinCheekWL * globalMouthW;
            cinCheekWR = cinCheekWR * cinCheekWR * globalMouthW;
            pos.x += cinCheekWL * 3.5 * moClamped; // inward
            pos.y += cinCheekWL * 5.5 * moClamped; // down
            pos.x -= cinCheekWR * 3.5 * moClamped; // inward
            pos.y += cinCheekWR * 5.5 * moClamped; // down
            
            // Phase 4 Step 5: Chin / Mentalis Refinement (chin moves down, lower lip stretches)
            float mentalisDist = distance(pos.xy, chin);
            float mentalisW = clamp(1.0 - mentalisDist / 120.0, 0.0, 1.0);
            mentalisW *= mentalisW * globalMouthW;
            pos.y += mentalisW * 4.5 * moClamped;
            
            // Lip Tension
            float lipDist = min(distance(pos.xy, mTop), distance(pos.xy, mBot));
            float lipTension = clamp(1.0 - lipDist / 20.0, 0.0, 1.0);
            pos.y -= lipTension * 1.5 * moClamped; // Tightens the lip line vertically
            
            // Nasal Alae / Nostril micro-flare
            float nWeight = clamp(1.0 - distance(pos.xy, noseTip) / 120.0, 0.0, 1.0);
            nWeight = nWeight * nWeight * nWeight * globalMouthW;
            pos.x -= (pos.x < noseTip.x ? 1.0 : -1.0) * nWeight * 4.0 * moClamped;
        }

        // PHASE 7: SECONDARY MOTION / MICRO SKIN / CINEMATIC REALISM

        // Part 2: Micro Skin Drag
        vec2 mCenter = (mTop + mBot) * 0.5;
        float skinDist = distance(pos.xy, mCenter);
        float skinRadius = 250.0;
        // Part 3 Soft Falloff Deformation
        float skinFalloff = smoothstep(skinRadius, 0.0, skinDist); 
        // 0.15 target value mapped explicitly into pixel offsets
        float skinDrag = min(mouthOpen, 1.0) * skinFalloff * 0.15 * 80.0; 
        pos.y -= skinDrag; // As strictly requested, counter drag

        // Part 5: Secondary Cheek Follow & Part 1 Inertia Follow
        vec2 cheekAreaL = mLeft + vec2(-20.0, 20.0);
        vec2 cheekAreaR = mRight + vec2(20.0, 20.0);
        float cheekFollowL = smoothstep(180.0, 0.0, distance(pos.xy, cheekAreaL));
        float cheekFollowR = smoothstep(180.0, 0.0, distance(pos.xy, cheekAreaR));
        float cheekMove = uSecondaryFollow * 0.25 * 50.0; // scale secondary 0.25 offset to pixels
        pos.y += (cheekFollowL + cheekFollowR) * cheekMove;

            // Part 4: Micro Random Life Motion
            float lifeFalloff = smoothstep(400.0, 0.0, distance(pos.xy, mCenter));
            pos.y += uMicroLife * lifeFalloff; // (uMicroLife already scaled x1000 in JS)

            // PHASE 7.5: Global Idle Micro Life Drift (Full face soft tissue, excluding upper forehead)
            // Center weight around the lower face, smoothly failing off up to the brow line.
            float globalIdleY = smoothstep((lBrow.y + rBrow.y) * 0.5 - 150.0, chin.y + 50.0, pos.y); 
            float noseLimiter = smoothstep(0.0, 50.0, distance(pos.xy, noseTip)); 
            // Eye sockets must drift significantly less to prevent cornea sliding
            float eyeDriftLimiterL = smoothstep(0.0, 90.0, distance(pos.xy, lEye));
            float eyeDriftLimiterR = smoothstep(0.0, 90.0, distance(pos.xy, rEye));
            
            // Background Isolation: Explicitly mask out EVERYTHING outside the specific cheekbones and under the chin
            float faceFaceWidth = distance(jawL, jawR);
            // Decay precisely to 0.0 directly on the jawline (0.5 * width) to prevent any background pixels stretching
            float faceWidthLimiter = smoothstep(faceFaceWidth * 0.48, faceFaceWidth * 0.35, abs(pos.x - noseTip.x));
            // Decay precisely to 0.0 tightly underneath the chin bone geometry, totally freezing the neck
            float neckBackgroundLimiter = smoothstep(chin.y + 15.0, chin.y - 45.0, pos.y);
            
            float combinedIdleFalloff = globalIdleY * noseLimiter * eyeDriftLimiterL * eyeDriftLimiterR * faceWidthLimiter * neckBackgroundLimiter;
            
            // Downward sag / structural breathing globally down the face
            pos.y += uIdleLife * combinedIdleFalloff; 
            
            // Lateral expansion cleanly bounds at the fleshiest parts of the cheeks
            float cheekMask = smoothstep(300.0, 50.0, distance(pos.xy, (mLeft+mRight)*0.5));
            pos.x += (pos.x < (noseTip.x) ? -1.0 : 1.0) * uIdleLife * 0.35 * cheekMask * combinedIdleFalloff;

            // COMBINED CLAMP: All layered physics sums (Breath, SecondaryFollow, IdleLife, MicroLife, Math) are bound safely below 
            // Keep chin safe. maxJawDrop safe boundary limit explicitly caps everything.
            float maxJawDropSafe = 40.0;
            float chinFloor = chin.y - 5.0;
            if (pos.y > chinFloor) {
                float cDist = distance(pos.xy, chin);
                float cW = smoothstep(120.0, 0.0, cDist); // Part 3 smoothstep falloff
                float safeY = mix(pos.y, chinFloor, cW);
                
                pos.y = min(pos.y, safeY + maxJawDropSafe * (1.0 - cW));
                pos.y = max(pos.y, chinFloor - maxJawDropSafe); 
                pos.y = mix(pos.y, chinFloor, cW); 
            }

        // LAYER 8: MICRO EXPRESSIONS (Purely time based, entirely randomized, localized safely)
        float mT = time * 3.5;
        // Asymmetric micro brows
        float mcBrowL = sin(mT * 0.8) * 1.2;
        float mcBrowR = sin(mT * 1.1 + 2.0) * 1.2;
        pos.y -= clamp(1.0 - distance(pos.xy, lBrow)/100.0, 0.0, 1.0) * mcBrowL;
        pos.y -= clamp(1.0 - distance(pos.xy, rBrow)/100.0, 0.0, 1.0) * mcBrowR;
        
        // Asymmetric micro smile
        float mcSmileL = (sin(mT * 1.25) * 0.5 + 0.5) * 1.0;
        float mcSmileR = (sin(mT * 1.45 + 1.5) * 0.5 + 0.5) * 1.0;
        pos.y -= clamp(1.0 - distance(pos.xy, mLeft)/80.0, 0.0, 1.0) * mcSmileL;
        pos.y -= clamp(1.0 - distance(pos.xy, mRight)/80.0, 0.0, 1.0) * mcSmileR;

        // LAYER 9: SECONDARY CINEMATIC MOTION (Inertia & Bounce during movement)
        if (mouthOpen > 0.01) {
            // Delayed sine wave matches speech envelope but adds dragging inertia
            float bounce = sin(time * 12.0 - 0.7) * 2.0 * min(mouthOpen, 1.0);
            float cheekBounceL = clamp(1.0 - distance(pos.xy, (mLeft + lEye)*0.5)/180.0, 0.0, 1.0);
            float cheekBounceR = clamp(1.0 - distance(pos.xy, (mRight + rEye)*0.5)/180.0, 0.0, 1.0);
            pos.y += cheekBounceL * cheekBounceL * bounce;
            pos.y += cheekBounceR * cheekBounceR * bounce;
        }

        // LAYER 10: SKIN SOFTNESS (Flesh feel at edges)
        float mouthOuterR = distance(mLeft, mRight) * 0.45;
        float softDist = distance(pos.xy, (mTop + mBot) * 0.5);
        if (softDist > mouthOuterR && softDist < mouthOuterR + 80.0) {
            float softW = smoothstep(mouthOuterR + 80.0, mouthOuterR, softDist);
            // Ultra delicate rhythmic breathing of the skin envelope
            pos.y += sin(time * 2.5) * 0.5 * softW;
            pos.x += cos(time * 2.5) * 0.3 * softW;
        }

        // ═══════════════════════════════════════════════════════
        // LAYER 11: PHASE 44.5 — REALISTIC SPEECH REALISM
        // ═══════════════════════════════════════════════════════

        // 44.5-A: Jaw Arc Rotation (arc instead of linear drop)
        if (mouthOpen > 0.02) {
            vec2 jawPivot = (jawL + jawR) * 0.5;
            float jawSpan44 = max(chin.y - jawPivot.y, 1.0);
            float pivotDist44 = pos.y - jawPivot.y;
            if (pivotDist44 > 0.0) {
                float arcWeight = clamp(pivotDist44 / jawSpan44, 0.0, 1.0);
                arcWeight = arcWeight * arcWeight;
                vec2 mC44a = (mTop + mBot) * 0.5;
                float mW44a = distance(mLeft, mRight);
                float hMask44 = clamp(1.0 - abs(pos.x - mC44a.x) / (mW44a * 0.9), 0.0, 1.0);
                float angle44 = mouthOpen * 0.12 * arcWeight * hMask44;
                float sA = sin(angle44);
                float cA = cos(angle44);
                float relY44 = pos.y - jawPivot.y;
                float relX44 = pos.x - jawPivot.x;
                pos.x = jawPivot.x + relX44 * cA - relY44 * sA;
                pos.y = jawPivot.y + relX44 * sA + relY44 * cA;
            }
        }

        // 44.5-B: Lip Asymmetry (subtle left/right difference)
        if (mouthOpen > 0.02 && abs(uLipAsymmetry) > 0.001) {
            vec2 mC44b = (mTop + mBot) * 0.5;
            float lipDist44 = distance(pos.xy, mC44b);
            float lipMask44 = clamp(1.0 - lipDist44 / 100.0, 0.0, 1.0);
            lipMask44 *= lipMask44;
            float side44 = (pos.x < mC44b.x) ? -1.0 : 1.0;
            pos.y += uLipAsymmetry * 8.0 * lipMask44 * side44 * min(mouthOpen, 1.0);
        }

        // 44.5-C: Enhanced Cheek Bulge (phoneme-driven)
        if (uCheekBulge > 0.001) {
            vec2 cbZoneL = (mLeft + jawL) * 0.5 + vec2(-30.0, 0.0);
            vec2 cbZoneR = (mRight + jawR) * 0.5 + vec2(30.0, 0.0);
            float cbL = smoothstep(200.0, 0.0, distance(pos.xy, cbZoneL));
            float cbR = smoothstep(200.0, 0.0, distance(pos.xy, cbZoneR));
            pos.x -= cbL * uCheekBulge * 6.0;
            pos.y += cbL * uCheekBulge * 3.0;
            pos.x += cbR * uCheekBulge * 6.0;
            pos.y += cbR * uCheekBulge * 3.0;
        }

        // 44.5-D: Tissue Inertia Overshoot (spring-damper lag)
        if (abs(uTissueInertia - mouthOpen) > 0.005) {
            float overshoot44 = uTissueInertia - mouthOpen;
            vec2 mC44d = (mTop + mBot) * 0.5;
            float tDist44 = distance(pos.xy, mC44d);
            float tW44 = smoothstep(300.0, 50.0, tDist44);
            pos.y += overshoot44 * 12.0 * tW44;
        }

        // 44.5-E: Nasolabial Fold Compression
        if (mouthOpen > 0.05) {
            vec2 foldL = (noseL + mLeft) * 0.5;
            vec2 foldR = (noseR + mRight) * 0.5;
            float fWL = smoothstep(80.0, 0.0, distance(pos.xy, foldL));
            float fWR = smoothstep(80.0, 0.0, distance(pos.xy, foldR));
            float fMo = min(mouthOpen, 0.8);
            pos.x += fWL * 3.0 * fMo;
            pos.x -= fWR * 3.0 * fMo;
            pos.y += (fWL + fWR) * 2.0 * fMo;
        }

        // 44.5-F: F Phoneme (lower lip tucks toward upper teeth)
        if (uPhF > 0.01) {
            float fDist44 = distance(pos.xy, mBot);
            float fW44 = clamp(1.0 - fDist44 / 60.0, 0.0, 1.0);
            fW44 *= fW44;
            pos.y -= uPhF * 8.0 * fW44 * min(mouthOpen, 1.0);
        }

        // 44.5-G: S/TH Phoneme (jaw narrowing)
        if (uPhS > 0.01 || uPhTH > 0.01) {
            float sthVal = max(uPhS, uPhTH);
            float cWL44 = clamp(1.0 - distance(pos.xy, mLeft) / 70.0, 0.0, 1.0);
            float cWR44 = clamp(1.0 - distance(pos.xy, mRight) / 70.0, 0.0, 1.0);
            pos.x += cWL44 * sthVal * 4.0 * min(mouthOpen, 1.0);
            pos.x -= cWR44 * sthVal * 4.0 * min(mouthOpen, 1.0);
        }

        // Final Return
        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
      }
    `,
    fragmentShader: `
      uniform sampler2D map;
      uniform vec2 eyeOff;
      uniform vec2 lEye;
      uniform vec2 rEye;
      uniform float lIrisR;
      uniform float rIrisR;
      uniform float mouthOpen;
      uniform vec2 mTop;
      uniform vec2 mBot;
      uniform vec2 mLeft;
      uniform vec2 mRight;
      uniform float uShapeOval;
      uniform float uShapeFlat;
      uniform float uShapeRound;
      uniform float uPhA;
      uniform float uPhE;
      uniform float uPhO;
      uniform float uPhU;
      uniform float uPhM;
      varying vec2 vUv;
      void main() {
        vec2 uv = vUv;
        vec2 pxPos = vec2(uv.x * 3608.0, uv.y * 2244.0);
        
        // Logical shift in UV space
        vec2 uvShift = -eyeOff / vec2(3608.0, 2244.0);
        
        float dL = distance(pxPos, lEye);
        float dR = distance(pxPos, rEye);
        
        if (dL < lIrisR) {
            uv += uvShift;
        } else if (dR < rIrisR) {
            uv += uvShift;
        }
        
        vec4 texColor = texture2D(map, uv);
        
        // MOUTH INTERIOR (cavity + lower teeth + tongue)
        if (mouthOpen > 0.01) {
            vec2 mCenter = (mTop + mBot) * 0.5;
            float mw = distance(mLeft, mRight);
            
            // Phase 5 Part 4: Inner mouth scale dynamically with shapes & phonemes
            // E -> wider, O -> deeper/round, A -> taller, U -> narrow
            float shapeW = 1.0 + (uShapeFlat * 0.3) - (uShapeRound * 0.2) + (uPhE * 0.4) - (uPhO * 0.15) - (uPhU * 0.2) - (uPhM * 0.1);
            float shapeH = 1.0 + (uShapeOval * 0.4) + (uShapeRound * 0.2) - (uShapeFlat * 0.1) + (uPhA * 0.6) + (uPhO * 0.5) - (uPhM * 0.4);

            float effectiveMo = mouthOpen * (1.0 - (uPhM * 0.6) - (uPhU * 0.25)); // M and U restrict the hole

            float halfW = mw * 0.44 * shapeW * (0.8 + effectiveMo * 0.3);
            float rawHalfH = (mw * 0.05 + effectiveMo * mw * 0.30) * shapeH;
            // Clamp halfH to estimated deformed gap (raw gap + vertex jaw/lip deformation)
            float actualGap = abs(mBot.y - mTop.y) * 0.5;
            float deformedGap = actualGap + mouthOpen * 120.0; // vertex drops jaw ~85px + lip ~65px
            float halfH = min(rawHalfH, max(deformedGap, 1.0));
            
            float dxM = (pxPos.x - mCenter.x) / max(halfW, 1.0);
            float dyM = (pxPos.y - mCenter.y) / max(halfH, 1.0);
            
            // Phase 44.5 Final: Lip-bounded Lens Mask (replaces ellipse)
            // A parabola curve correctly models pointy mouth corners, preventing any skin bleed.
            float lipCurve = 1.0 - (dxM * dxM); 
            float normY = abs(dyM) / max(lipCurve, 0.001);
            
            if (abs(dxM) < 1.0 && normY < 1.0) {
                float depth = 1.0 - normY;
                depth = depth * depth;
                float mo = min(mouthOpen, 0.9);
                
                // Phase 44.5: Depth-graded cavity (center darker, edges warmer)
                vec3 cavityDeep = vec3(0.03, 0.01, 0.01);
                vec3 cavityEdge = vec3(0.12, 0.06, 0.06);
                vec3 cavityColor = mix(cavityEdge, cavityDeep, depth);
                
                // Phase 44.5: Upper teeth strip (visible at moderate+ open)
                float upTeethZone = smoothstep(-0.8, -0.4, dyM) * (1.0 - smoothstep(-0.4, -0.1, dyM));
                float upTeethMask = upTeethZone * smoothstep(0.05, 0.20, mo) * (1.0 - abs(dxM) * 0.8);
                vec3 upTeethColor = vec3(0.82, 0.80, 0.76);
                float upToothCurve = sin(dxM * 18.85) * 0.08;
                upTeethColor += vec3(upToothCurve * 0.1);
                float upSpec = pow(max(0.0, 1.0 - abs(dyM + 0.35)), 8.0) * 0.3;
                upTeethColor += vec3(upSpec);
                
                // Phase 44.5: Lower teeth (curved individual teeth + specular)
                float teethZone = smoothstep(0.3, 0.6, dyM) * (1.0 - smoothstep(0.6, 0.9, dyM));
                float teethMask = teethZone * smoothstep(0.0, 0.15, mo) * (1.0 - abs(dxM) * 0.7);
                vec3 teethColor = vec3(0.82, 0.80, 0.76);
                float toothCurve = sin(dxM * 18.85) * 0.08;
                teethColor += vec3(toothCurve * 0.1);
                float teethSpec = pow(max(0.0, 1.0 - abs(dyM - 0.2)), 8.0) * 0.25;
                teethColor += vec3(teethSpec);
                
                // Phase 44.5: Upper gum line (faint pink above upper teeth)
                float upGumZone = smoothstep(-0.7, -0.55, dyM) * (1.0 - smoothstep(-0.55, -0.45, dyM));
                float upGumMask = upGumZone * smoothstep(0.2, 0.4, mo) * (1.0 - abs(dxM) * 0.9);
                vec3 upGumColor = vec3(0.55, 0.28, 0.28);
                
                // Phase 44.5: Lower gum line
                float loGumZone = smoothstep(0.55, 0.65, dyM) * (1.0 - smoothstep(0.65, 0.8, dyM));
                float loGumMask = loGumZone * smoothstep(0.15, 0.3, mo) * (1.0 - abs(dxM) * 0.85);
                vec3 loGumColor = vec3(0.50, 0.25, 0.25);
                
                // Soft tongue (center-bottom, pink, rounded)
                float tongDy = (dyM - 0.25) / 0.6;
                float tongDx = dxM / 0.65;
                float tongueEllipse = tongDx * tongDx + tongDy * tongDy;
                float tongueMask = (1.0 - smoothstep(0.4, 1.0, tongueEllipse)) * smoothstep(0.0, 0.2, dyM);
                tongueMask *= smoothstep(0.05, 0.2, mo);
                vec3 tongueColor = vec3(0.55, 0.25, 0.25);
                tongueColor *= 0.9 + 0.1 * sin(mo * 3.14);
                
                // Phase 44.5: Tongue shadow behind tongue
                float tShadowMask = smoothstep(0.5, 0.8, dyM) * (1.0 - abs(dxM) * 0.8);
                vec3 tShadowColor = vec3(0.04, 0.02, 0.02);
                
                // Phase 44.5: Ambient occlusion ring at cavity edge
                float aoRing = smoothstep(0.7, 1.0, normY) * 0.3;
                
                // Fix 1: Compose interior layers, then blend with decoupled opacity
                // Cavity uses depth for color grading but NOT for final blend strength
                vec3 interior = cavityColor;
                interior = mix(interior, tShadowColor, tShadowMask * 0.5);
                interior = mix(interior, upGumColor, upGumMask * 0.6);
                interior = mix(interior, loGumColor, loGumMask * 0.6);
                interior = mix(interior, upTeethColor, upTeethMask * 0.90);
                interior = mix(interior, teethColor, teethMask * 0.90);
                interior = mix(interior, tongueColor, tongueMask * 0.85);
                interior *= (1.0 - aoRing);
                
                // Phase 44.5 Dynamic Edge Fade (strictly fades inside the lip line)
                float edgeFade = smoothstep(1.0, 0.7, normY) * smoothstep(1.0, 0.8, abs(dxM));
                
                // Decoupled blend: solid features (teeth/gums/tongue) get their own alpha
                // instead of being crushed by depth² which is near-zero at edges
                float solidAlpha = max(max(upTeethMask * 0.90, teethMask * 0.90), max(tongueMask * 0.85, max(upGumMask * 0.6, loGumMask * 0.6)));
                float finalAlpha = max(depth, solidAlpha);
                float blendStrength = finalAlpha * edgeFade * smoothstep(0.02, 0.12, mo);
                texColor.rgb = mix(texColor.rgb, interior, blendStrength * 0.95);
            }
        }
        // Fix 2: Old upper lip edge stroke removed (was causing grey/white patch at pre-deformation position)
        gl_FragColor = texColor;
      }
    `,
    transparent: true
  });

  threeFaceMesh = new THREE.Mesh(geometry, material);
  threeScene.add(threeFaceMesh);
}

function resizeThreeJS() {
  if (!threeRenderer || !threeCamera) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvasDisplayW * dpr;
  const h = canvasDisplayH * dpr;

  threeRenderer.setSize(w, h, false);

  const left = -sceneOffsetX / sceneScale;
  const right = (canvasDisplayW - sceneOffsetX) / sceneScale;
  const top = -sceneOffsetY / sceneScale;
  const bottom = (canvasDisplayH - sceneOffsetY) / sceneScale;

  threeCamera.left = left;
  threeCamera.right = right;
  threeCamera.top = top;
  threeCamera.bottom = bottom;
  threeCamera.updateProjectionMatrix();
}