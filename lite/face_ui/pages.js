/**
 * pages.js — GENESIS Feature Pages Renderer
 * Dynamically renders all menu pages into the overlay container.
 * Does NOT modify face.js, genesis_ws.js, or any canvas element.
 */
(function () {
  "use strict";

  // Cache latest sys_stats from the WS bridge
  var latestStats = { cpu: null, ram: null, gpu: null };
  window.addEventListener("genesis_ws_message", function (e) {
    var msg = e.detail || {};
    if ((msg.type || msg.event) === "sys_stats" && msg.data) {
      latestStats = msg.data;
    }
  });

  function header(title) {
    return '<div class="gp-header">' +
      '<div class="gp-back-btn" onclick="GenesisPages.closePage()">←</div>' +
      '<div class="gp-title">' + title + '</div>' +
      '</div>';
  }

  function future(icon, label) {
    return '<div class="gp-future">' +
      '<div class="gp-future-icon">' + icon + '</div>' +
      'Feature coming in future version.<br>' + label +
      '</div>';
  }

  // ─── PAGE RENDERERS ───

  var pages = {

    home_connect: function () {
      return header("Home Connect") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Scan Devices</div>' +
        '<div class="gp-radar"><div class="gp-radar-center"></div></div>' +
        '<div class="gp-card-text" style="text-align:center;margin-top:12px;">Scanning for nearby devices...</div>' +
        '</div>' +
        '<div class="gp-card"><div class="gp-card-title">Discovered Devices</div>' +
        '<ul class="gp-device-list">' +
        '<li class="gp-device-item"><div><div class="gp-device-name">Living Room Light</div><div class="gp-device-type">Smart Bulb • Zigbee</div></div><button class="gp-btn">Connect</button></li>' +
        '<li class="gp-device-item"><div><div class="gp-device-name">Thermostat Hub</div><div class="gp-device-type">Climate Control • WiFi</div></div><button class="gp-btn">Connect</button></li>' +
        '<li class="gp-device-item"><div><div class="gp-device-name">Smart Lock</div><div class="gp-device-type">Security • BLE</div></div><button class="gp-btn">Connect</button></li>' +
        '</ul></div></div>';
    },

    body_connect: function () {
      return header("Body Connect") + future("🤖", "Robot body hardware interface.");
    },

    health_connect: function () {
      return header("Health Connect") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Brain-Computer Interface</div>' +
        '<div class="gp-card-text">BCI module connection pending. Connect a compatible EEG device to enable neural telemetry.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Biometric Sensors</div>' +
        '<div class="gp-card-text">Heart rate, SpO2, and skin conductance monitoring will be available with a compatible wearable.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Wearable Sensors</div>' +
        '<div class="gp-card-text">Smartwatch and fitness band integration coming in a future version.</div></div>' +
        '<div class="gp-future"><div class="gp-future-icon">🩺</div>Feature coming in future version.</div></div>';
    },

    memory: function () {
      return header("Memory") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Stored Memories</div>' +
        '<div id="gp-memory-list" class="gp-card-text">Loading memory entries...</div></div>' +
        '<div style="text-align:center;margin-top:12px;"><button class="gp-btn" onclick="GenesisPages._loadMemory()">Refresh</button></div></div>';
    },

    voice_settings: function () {
      return header("Voice Settings") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Speech Speed</div>' +
        '<div class="gp-slider-row"><span class="gp-slider-label">Rate</span><input type="range" class="gp-slider" min="50" max="250" value="150"><span>150</span></div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Voice Selection</div>' +
        '<div class="gp-card-text">Current: System Default (pyttsx3 SAPI5)<br>Piper TTS: Not installed</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Microphone Sensitivity</div>' +
        '<div class="gp-slider-row"><span class="gp-slider-label">VAD Threshold</span><input type="range" class="gp-slider" min="0" max="100" value="45"><span>45</span></div></div>' +
        '<div class="gp-future"><div class="gp-future-icon">🎙️</div>Live controls coming in future version.</div></div>';
    },

    emotion_settings: function () {
      return header("Emotion Settings") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Emotion Sensitivity</div>' +
        '<div class="gp-slider-row"><span class="gp-slider-label">LLM Inference</span><input type="range" class="gp-slider" min="0" max="100" value="70"><span>70%</span></div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Expression Intensity</div>' +
        '<div class="gp-slider-row"><span class="gp-slider-label">Blend Speed</span><input type="range" class="gp-slider" min="1" max="100" value="40"><span>0.08</span></div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Manual Emotion Test</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'happy\')">Happy</button>' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'sad\')">Sad</button>' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'angry\')">Angry</button>' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'surprised\')">Surprised</button>' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'thinking\')">Thinking</button>' +
        '<button class="gp-btn" onclick="if(window.setEmotion)setEmotion(\'idle\')">Neutral</button>' +
        '</div></div></div>';
    },

    system_status: function () {
      var cpu = latestStats.cpu != null ? latestStats.cpu + "%" : "—";
      var ram = latestStats.ram != null ? latestStats.ram + "%" : "—";
      var gpu = latestStats.gpu != null ? latestStats.gpu + "%" : "—";
      var wsState = window.__genesis_ws_active ? "Connected" : "Disconnected";
      var wsClass = window.__genesis_ws_active ? "gp-status-ok" : "gp-status-off";

      return header("System Status") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">GENESIS Core</div>' +
        '<div class="gp-status-row"><span class="gp-status-label">Status</span><span class="gp-status-value gp-status-ok">Online</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">WebSocket</span><span class="gp-status-value ' + wsClass + '">' + wsState + '</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">AI Model</span><span class="gp-status-value gp-status-ok">Groq LLaMA 3.1</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">Microphone</span><span class="gp-status-value gp-status-ok">Active</span></div>' +
        '</div>' +
        '<div class="gp-card"><div class="gp-card-title">System Resources</div>' +
        '<div class="gp-status-row"><span class="gp-status-label">CPU Usage</span><span class="gp-status-value">' + cpu + '</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">RAM Usage</span><span class="gp-status-value">' + ram + '</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">GPU Usage</span><span class="gp-status-value">' + gpu + '</span></div>' +
        '</div></div>';
    },

    device_permissions: function () {
      return header("Device Permissions") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Permission Status</div>' +
        '<div class="gp-status-row"><span class="gp-status-label">🎤 Microphone</span><span class="gp-status-value gp-status-ok" id="gp-perm-mic">Checking...</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">📷 Camera</span><span class="gp-status-value" id="gp-perm-cam">Checking...</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">💾 Storage</span><span class="gp-status-value gp-status-ok" id="gp-perm-store">Granted</span></div>' +
        '</div></div>';
    },

    developer_mode: function () {
      return header("Developer Mode") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Event Bus Monitor</div>' +
        '<div class="gp-card-text" id="gp-dev-log" style="font-family:monospace;font-size:11px;max-height:200px;overflow-y:auto;color:#0cf;">Listening for events...</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">WebSocket Inspector</div>' +
        '<div class="gp-card-text" id="gp-dev-ws" style="font-family:monospace;font-size:11px;max-height:200px;overflow-y:auto;color:#88cc88;">Waiting for messages...</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Emotion State</div>' +
        '<div class="gp-card-text">Current: <span id="gp-dev-emotion" style="color:#ffaa00;">idle</span></div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Quick Actions</div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
        '<button class="gp-btn" onclick="console.log(\'[DEV] Force refresh\');location.reload();">Force Reload</button>' +
        '<button class="gp-btn" onclick="localStorage.clear();alert(\'Cache cleared\');">Clear Cache</button>' +
        '</div></div></div>';
    },

    updates: function () {
      return header("Updates") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Current Version</div>' +
        '<div class="gp-card-text">GENESIS v3.0.0 — Phase 3</div></div>' +
        future("🔄", "Automatic update checking will be available in a future version.") + '</div>';
    },

    privacy: function () {
      return header("Privacy & Data Control") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Data Storage</div>' +
        '<div class="gp-card-text">All conversations and memories are stored locally on your machine. No data is sent to external servers except for LLM inference requests.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Voice Data</div>' +
        '<div class="gp-card-text">Audio recordings are processed locally via Whisper STT. Temporary audio files are deleted immediately after transcription.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Memory Wipe</div>' +
        '<div class="gp-card-text">Clear all stored memories and conversation history.</div>' +
        '<div style="margin-top:10px;"><button class="gp-btn" style="border-color:rgba(255,60,60,0.4);color:#ff6666;" onclick="alert(\'Memory wipe requires backend confirmation\')">Wipe All Memories</button></div>' +
        '</div></div>';
    },

    owner_info: function () {
      return header("Owner Information") +
        '<div class="gp-content">' +
        '<div class="gp-card"><div class="gp-card-title">Owner Profile</div>' +
        '<div class="gp-card-text">GENESIS recognizes and personalizes responses for its registered owner. Profile data is stored in the local knowledge graph.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Profile Settings</div>' +
        '<div class="gp-status-row"><span class="gp-status-label">Name</span><span class="gp-status-value">Loaded from profile</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">Address Mode</span><span class="gp-status-value">Sir</span></div>' +
        '<div class="gp-status-row"><span class="gp-status-label">Recognition</span><span class="gp-status-value gp-status-ok">Enabled</span></div>' +
        '</div>' +
        '<div class="gp-future"><div class="gp-future-icon">👤</div>Advanced profile editing coming in future version.</div></div>';
    },

    about: function () {
      return header("About Genesis") +
        '<div class="gp-content" style="text-align:center;">' +
        '<img class="gp-about-logo" src="assets/genesis_logo.png" alt="GENESIS Logo">' +
        '<div style="font-size:22px;font-weight:700;color:#e0e8f0;letter-spacing:4px;margin-bottom:4px;">GENESIS</div>' +
        '<div style="font-size:13px;color:#d4850a;letter-spacing:3px;margin-bottom:20px;">SYNTHETIC INTELLIGENCE</div>' +
        '<div class="gp-card"><div class="gp-card-title">Version</div><div class="gp-card-text">v3.0.0 — Phase 3 Frontend</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Project</div>' +
        '<div class="gp-card-text">GENESIS is an advanced AI operating system with real-time voice interaction, avatar animation, semantic routing, and emotional intelligence. Designed for full autonomy across PC and Android platforms.</div></div>' +
        '<div class="gp-card"><div class="gp-card-title">Architecture</div>' +
        '<div class="gp-card-text">Event Bus • Semantic Router • Groq LLM • Rhubarb Lip Sync • MediaPipe Face Tracking • WebSocket Bridge • Emotion Engine</div></div>' +
        '</div>';
    }
  };

  // ─── PUBLIC API ───

  function openPage(pageId) {
    var overlay = document.getElementById("genesis-page-overlay");
    if (!overlay || !pages[pageId]) return;
    overlay.innerHTML = pages[pageId]();
    overlay.style.display = "block";
    void overlay.offsetHeight;
    overlay.classList.add("visible");

    // Post-render hooks
    if (pageId === "device_permissions") checkPermissions();
    if (pageId === "developer_mode") startDevMonitor();
    if (pageId === "memory") loadMemory();
  }

  function closePage() {
    var overlay = document.getElementById("genesis-page-overlay");
    if (!overlay) return;
    overlay.classList.remove("visible");
    setTimeout(function () {
      overlay.style.display = "none";
      overlay.innerHTML = "";
    }, 380);
  }

  // ─── HELPERS ───

  function checkPermissions() {
    if (navigator.permissions) {
      navigator.permissions.query({ name: "microphone" }).then(function (r) {
        var el = document.getElementById("gp-perm-mic");
        if (el) { el.textContent = r.state === "granted" ? "Granted" : r.state; el.className = "gp-status-value " + (r.state === "granted" ? "gp-status-ok" : "gp-status-warn"); }
      }).catch(function () {});
      navigator.permissions.query({ name: "camera" }).then(function (r) {
        var el = document.getElementById("gp-perm-cam");
        if (el) { el.textContent = r.state === "granted" ? "Granted" : r.state; el.className = "gp-status-value " + (r.state === "granted" ? "gp-status-ok" : "gp-status-warn"); }
      }).catch(function () {});
    }
  }

  var _devMonitorId = null;
  function startDevMonitor() {
    if (_devMonitorId) clearInterval(_devMonitorId);
    var handler = function (e) {
      var msg = e.detail || {};
      var logEl = document.getElementById("gp-dev-ws");
      if (logEl) {
        var line = document.createElement("div");
        line.textContent = (msg.type || msg.event || "?") + " → " + JSON.stringify(msg.data || {}).substring(0, 80);
        logEl.appendChild(line);
        logEl.scrollTop = logEl.scrollHeight;
      }
    };
    window.addEventListener("genesis_ws_message", handler);
    // Clean up when page closes
    var obs = new MutationObserver(function () {
      if (!document.getElementById("gp-dev-ws")) {
        window.removeEventListener("genesis_ws_message", handler);
        obs.disconnect();
      }
    });
    obs.observe(document.getElementById("genesis-page-overlay"), { childList: true });
  }

  function loadMemory() {
    var el = document.getElementById("gp-memory-list");
    if (el) el.innerHTML = "<div style='color:rgba(200,215,240,0.4);font-style:italic;'>Memory retrieval requires backend API endpoint.<br>Connect via WebSocket command: { type: \"get_memory\" }</div>";
  }

  // Expose globally
  window.GenesisPages = {
    openPage: openPage,
    closePage: closePage,
    _loadMemory: loadMemory
  };
})();
