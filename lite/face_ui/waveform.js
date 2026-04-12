/**
 * waveform.js — GENESIS Voice Waveform HUD
 * Shows animated waveform bars when state is LISTENING or SPEAKING.
 * Reads state from #g-state DOM element (read-only observation).
 * Does NOT touch face.js, genesis_ws.js, or any existing code.
 */

(function () {
  "use strict";

  const BAR_COUNT = 20;
  const CHECK_INTERVAL = 300; // ms — how often to check state

  function buildWaveform() {
    const hud = document.getElementById("waveform-hud");
    if (!hud) return;

    let bars = "";
    for (let i = 0; i < BAR_COUNT; i++) {
      bars += '<div class="wf-bar"></div>';
    }
    hud.innerHTML = bars;
  }

  function getState() {
    const el = document.getElementById("g-state");
    if (!el) return "IDLE";
    // g-state uses wrapStatus() which wraps in <span class="status-xxx">TEXT</span>
    return (el.textContent || "").trim().toUpperCase();
  }

  function updateVisibility() {
    const hud = document.getElementById("waveform-hud");
    if (!hud) return;

    const state = getState();

    if (state === "LISTENING") {
      hud.classList.add("wf-visible", "wf-listening");
      hud.classList.remove("wf-speaking");
    } else if (state === "SPEAKING") {
      hud.classList.add("wf-visible", "wf-speaking");
      hud.classList.remove("wf-listening");
    } else {
      hud.classList.remove("wf-visible", "wf-listening", "wf-speaking");
    }
  }

  function init() {
    buildWaveform();
    setInterval(updateVisibility, CHECK_INTERVAL);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
