/**
 * stats_widget.js — GENESIS CPU/RAM/GPU HUD Widget
 * Polls stats_server.py (port 8082) every 3 seconds.
 * Gracefully shows "--" if stats server is not running.
 * Does NOT touch face.js, genesis_ws.js, or any existing code.
 */

(function () {
  "use strict";

  // No longer polling local APIs; listening to global 8080 generic websocket broadcasts

  function buildWidget() {
    const w = document.getElementById("stats-widget");
    if (!w) return;

    w.innerHTML = `
      <div class="sw-title">SYS MONITOR</div>
      <div class="sw-row">
        <span class="sw-label">CPU</span>
        <div class="sw-bar-track"><div class="sw-bar-fill sw-cpu" id="sw-cpu-bar"></div></div>
        <span class="sw-value" id="sw-cpu-val">--%</span>
      </div>
      <div class="sw-row">
        <span class="sw-label">RAM</span>
        <div class="sw-bar-track"><div class="sw-bar-fill sw-ram" id="sw-ram-bar"></div></div>
        <span class="sw-value" id="sw-ram-val">--%</span>
      </div>
      <div class="sw-row">
        <span class="sw-label">GPU</span>
        <div class="sw-bar-track"><div class="sw-bar-fill sw-gpu" id="sw-gpu-bar"></div></div>
        <span class="sw-value" id="sw-gpu-val">N/A</span>
      </div>
    `;
  }

  function updateBar(barId, valId, pct) {
    const bar = document.getElementById(barId);
    const val = document.getElementById(valId);
    if (pct === null || pct === undefined) {
      if (bar) { bar.style.width = "0%"; bar.classList.remove("sw-warn"); }
      if (val) val.textContent = "N/A";
      return;
    }
    if (bar) {
      bar.style.width = pct + "%";
      if (pct > 85) {
        bar.classList.add("sw-warn");
      } else {
        bar.classList.remove("sw-warn");
      }
    }
    if (val) val.textContent = Math.round(pct) + "%";
  }

  function init() {
    buildWidget();
    
    // Listen for stats broadcasted from face_server.py (8080) via genesis_ws.js
    window.addEventListener('genesis_ws_message', (e) => {
      const msg = e.detail;
      const type = msg.type || msg.event;
      if (type === "sys_stats") {
        const data = msg.data || {};
        updateBar("sw-cpu-bar", "sw-cpu-val", data.cpu);
        updateBar("sw-ram-bar", "sw-ram-val", data.ram);
        updateBar("sw-gpu-bar", "sw-gpu-val", data.gpu);
      }
    });

    // Start with blank state
    updateBar("sw-cpu-bar", "sw-cpu-val", null);
    updateBar("sw-ram-bar", "sw-ram-val", null);
    updateBar("sw-gpu-bar", "sw-gpu-val", null);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
