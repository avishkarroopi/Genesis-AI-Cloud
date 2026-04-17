/**
 * genesis_ws.js — GENESIS WebSocket Client for HUD Status
 * Connects to face_server WebSocket, listens for state/status events,
 * and updates the DOM HUD overlay elements in real time.
 * 
 * Does NOT touch face.js, animation, or canvas rendering.
 */

(function () {
  "use strict";

  const WS_URL =
    window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
      ? "ws://127.0.0.1:8000/ws/voice"
      : "wss://genesis-ai-cloud-production.up.railway.app/ws/voice";
  const RECONNECT_INTERVAL = 3000; // ms

  // HUD DOM elements — resolved lazily after DOM loads
  let elStatus, elAiMode, elAiCore, elVoice, elState, elMic, elCamera, elModel;

  let ws = null;
  window.genesisWsInstance = null;
  let connected = false;

  // ─── State color map ───
  const STATE_COLORS = {
    IDLE: "#00ff88",
    LISTENING: "#00ccff",
    THINKING: "#ffaa00",
    PLANNING: "#ff66ff",
    ACTING: "#ff4444",
    PROCESSING: "#ffaa00",
    SPEAKING: "#00eeff"
  };

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

  function setIconState(el, status) {
    if (!el) return;
    status = status.toUpperCase();
    if (status === "OK" || status === "READY" || status === "ON" || status === "CONNECTED" || status === "ACTIVE") {
      el.className = "icon-active";
    } else if (status === "OFF" || status === "DISCONNECTED" || status === "ERROR") {
      el.className = "icon-off";
    } else if (status === "LISTENING") {
      el.className = "icon-listening";
    } else if (status === "SPEAKING") {
      el.className = "icon-speaking";
    } else {
      el.className = "icon-idle";
    }
  }

  function resolveElements() {
    elStatus = document.getElementById("g-status");
    elAiMode = document.getElementById("g-network-icon"); 
    elAiCore = document.getElementById("g-emotion"); 
    elVoice = document.getElementById("g-voice-icon");   
    elMic = document.getElementById("g-mic-icon");  
    elCamera = document.getElementById("g-camera-icon");
    elModel = document.getElementById("g-model");
    elState = document.getElementById("g-state");
  }

  function setHudState(state) {
    if (!state) return;
    const upper = state.toUpperCase();
    if (elState) {
      elState.innerHTML = wrapStatus(upper);
      elState.style.color = ""; // Use CSS classes for color
      elState.style.textShadow = ""; // Use CSS classes for shadow
    }
  }

  function setOnline() {
    if (elStatus) { elStatus.innerHTML = wrapStatus("ONLINE"); elStatus.style.color = ""; }
    setIconState(elAiMode, "CONNECTED");
    setIconState(elVoice, "READY");
    setIconState(elMic, "ON");
    // Removed hardcoded ACTIVE state for camera to allow real status updates
  }

  function setOffline() {
    if (elStatus) { elStatus.innerHTML = wrapStatus("OFFLINE"); elStatus.style.color = ""; }
    setIconState(elAiMode, "OFF");
    setIconState(elVoice, "OFF");
    setIconState(elMic, "OFF");
    setIconState(elCamera, "OFF");
    setHudState("IDLE");
  }

  function connect() {
    try {
      ws = new WebSocket(WS_URL);
      window.genesisWsInstance = ws;

      ws.onopen = function () {
        console.log("[GENESIS_WS] Connected to server");
        connected = true;
        // Signal face.js drawHUD() to stop overwriting HUD elements
        window.__genesis_ws_active = true;
        // The server will send a full status packet, so we don't need to force setOnline() immediately,
        // but it's okay to set it as a placeholder.
        setOnline();
        setHudState("IDLE");
      };

      ws.onmessage = function (evt) {
        if (evt.data instanceof Blob) {
            const url = URL.createObjectURL(evt.data);
            const audio = new Audio(url);
            audio.play();
            return;
        }

        try {
          const msg = JSON.parse(evt.data);
          let type = msg.type || msg.event;
          let data = msg.data || msg;

          // Transcript pipeline repair
          if (!type && msg.transcript) {
              type = "transcript";
              msg.type = "transcript";
              data.text = msg.transcript;
              console.log("Voice transcript:", msg);
          }

          // Dispatch global event so decoupled widgets (like stats_widget.js) can listen to 8080 traffic
          window.dispatchEvent(new CustomEvent('genesis_ws_message', { detail: msg }));

          // FULL STATUS PACKET / INDIVIDUAL PACKETS
          if (type === "set_status") {
            if (elStatus) { elStatus.innerHTML = wrapStatus(data.status || "ONLINE"); elStatus.style.color = ""; }
            if (data.network) setIconState(elAiMode, data.network);
            if (data.voice) setIconState(elVoice, data.voice);
            if (data.mic) setIconState(elMic, data.mic);
            
            // Camera status is managed strictly by face.js based on landmark detection.
            // Backend currently defaults to OFF, so we ignore it here.
            
            if (data.state) setHudState(data.state);
          }
          else if (type === "set_state" && data.state) {
            setHudState(data.state);
          }
          else if (type === "set_voice" && data.voice) {
            setIconState(elVoice, data.voice);
          }
          else if (type === "set_mic" && data.mic) {
            setIconState(elMic, data.mic);
          }
          else if (type === "set_network" && data.network) {
            setIconState(elAiMode, data.network);
          }
          // Camera event ignored — managed by face.js

          // Speech events for visual feedback
          if (type === "speech_start") {
            setHudState("SPEAKING");
            if (typeof currentState !== 'undefined' && typeof STATES !== 'undefined') {
                currentState = STATES.SPEAKING;
            }
          }
          if (type === 'speech_stop') {
            setHudState('IDLE');
            if (typeof currentState !== 'undefined' && typeof STATES !== 'undefined') {
                currentState = STATES.IDLE;
            }
          }

          // Lip-Sync Viseme Mapping
          if (type === 'VISEME_EVENT' && data.viseme && window.setViseme) {
            window.setViseme(data.viseme);
          }

          // Brain -> Emotion Mapping
          if (type === 'set_emotion' && data.emotion && window.setEmotion) {
            window.setEmotion(data.emotion);
          }

        } catch (e) {
          // Non-JSON message, ignore
        }
      };

      ws.onclose = function () {
        console.log("[GENESIS_WS] Disconnected. Reconnecting...");
        connected = false;
        // Release HUD control back to face.js
        window.__genesis_ws_active = false;
        setOffline();
        setTimeout(connect, RECONNECT_INTERVAL);
      };

      ws.onerror = function (err) {
        console.error("[GENESIS_WS] Error:", err);
        try { ws.close(); } catch (_) { }
      };

    } catch (e) {
      console.error("[GENESIS_WS] Failed to connect:", e);
      setTimeout(connect, RECONNECT_INTERVAL);
    }
  }

  function init() {
    resolveElements();
    setTimeout(connect, 1000); // Give canvas time to setup
  }

  // Restore immediate execution on page load
  window.addEventListener('load', init);

  // Step 5 - Native Android UI Bridge
  // Overrides standard WS defaults when the physical hardware provides state chunks
  window.onAndroidStatus = function(indicator, state) {
    if (indicator === 'network') setIconState(elAiMode, state);
    if (indicator === 'mic') setIconState(elMic, state);
    if (indicator === 'camera') setIconState(elCamera, state);
    if (indicator === 'speaker') {
      // Typically speaker implies voice channel
      setIconState(elVoice, state);
    }
  };
})();

