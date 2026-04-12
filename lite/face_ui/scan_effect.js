/**
 * scan_effect.js — GENESIS Scanning Line Effect
 * Shows horizontal scan line during THINKING / PROCESSING states.
 * Reads state from #g-state DOM element (read-only observation).
 * Does NOT touch face.js, genesis_ws.js, or any existing code.
 */

(function () {
  "use strict";

  const CHECK_INTERVAL = 300;

  function buildScanEffect() {
    const el = document.getElementById("scan-effect");
    if (!el) return;

    el.innerHTML = `
      <div class="scan-grid"></div>
      <div class="scan-line"></div>
      <div class="scan-corner sc-tl"></div>
      <div class="scan-corner sc-tr"></div>
      <div class="scan-corner sc-bl"></div>
      <div class="scan-corner sc-br"></div>
    `;
  }

  function getState() {
    const el = document.getElementById("g-state");
    if (!el) return "IDLE";
    return (el.textContent || "").trim().toUpperCase();
  }

  function updateVisibility() {
    const el = document.getElementById("scan-effect");
    if (!el) return;

    const state = getState();

    if (state === "THINKING") {
      el.classList.add("scan-active");
      el.classList.remove("scan-processing");
    } else if (state === "PROCESSING") {
      el.classList.add("scan-active", "scan-processing");
    } else {
      el.classList.remove("scan-active", "scan-processing");
    }
  }

  function init() {
    buildScanEffect();
    setInterval(updateVisibility, CHECK_INTERVAL);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
