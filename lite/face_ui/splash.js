/**
 * splash.js — GENESIS Splash Screen Controller
 * Dismisses ONLY after WebSocket connected AND first sys_stats received.
 * Does NOT touch face.js, genesis_ws.js, or any canvas element.
 */
(function () {
  "use strict";

  let wsReady = false;
  let statsReceived = false;
  let dismissed = false;

  function tryDismiss() {
    if (dismissed) return;
    if (!wsReady || !statsReceived) return;
    dismissed = true;

    const splash = document.getElementById("genesis-splash");
    if (!splash) return;

    splash.classList.add("fade-out");
    // Remove from DOM after CSS transition
    setTimeout(function () {
      splash.style.display = "none";
      // Show the menu button after splash clears
      const menuBtn = document.getElementById("genesis-menu-btn");
      if (menuBtn) menuBtn.style.opacity = "1";
    }, 1300);
  }

  // Listen for genesis_ws_message custom events dispatched by genesis_ws.js
  window.addEventListener("genesis_ws_message", function (e) {
    var msg = e.detail || {};
    var type = msg.type || msg.event || "";

    // WebSocket is connected once we receive any message
    if (!wsReady) {
      wsReady = true;
    }

    // Wait for first sys_stats event
    if (type === "sys_stats" && !statsReceived) {
      statsReceived = true;
    }

    tryDismiss();
  });

  // Fallback timeout: if backend never sends sys_stats, dismiss after 12s
  setTimeout(function () {
    if (!dismissed) {
      dismissed = true;
      var splash = document.getElementById("genesis-splash");
      if (splash) {
        splash.classList.add("fade-out");
        setTimeout(function () {
          splash.style.display = "none";
          var menuBtn = document.getElementById("genesis-menu-btn");
          if (menuBtn) menuBtn.style.opacity = "1";
        }, 1300);
      }
    }
  }, 12000);

  // Generate floating particles on load
  window.addEventListener("load", function () {
    var splash = document.getElementById("genesis-splash");
    if (!splash) return;
    for (var i = 0; i < 18; i++) {
      var p = document.createElement("div");
      p.className = "splash-particle";
      p.style.left = Math.random() * 100 + "%";
      p.style.animationDuration = (5 + Math.random() * 8) + "s";
      p.style.animationDelay = Math.random() * 5 + "s";
      p.style.width = (2 + Math.random() * 3) + "px";
      p.style.height = p.style.width;
      splash.appendChild(p);
    }
  });
})();
