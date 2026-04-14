/**
 * enter.js — GENESIS Enter Screen Controller
 * Renders a neural-network particle background and handles the ENTER GENESIS flow.
 * Does NOT modify splash.js, face.js, genesis_ws.js, or any existing code.
 */
(function () {
  "use strict";

  // ── Build the Enter Screen DOM ──
  function buildEnterScreen() {
    var el = document.createElement("div");
    el.id = "genesis-enter-screen";
    el.innerHTML =
      '<canvas id="enter-bg-canvas"></canvas>' +
      '<div class="enter-content">' +
        '<div class="enter-title">GENESIS</div>' +
        '<div class="enter-subtitle">Synthetic and Vision Intelligence System</div>' +
        '<div class="enter-core-badge">' +
          '<div class="enter-core-dot"></div>' +
          '<span class="enter-core-label">AI Core Online</span>' +
        '</div>' +
        '<div class="enter-btn-wrapper">' +
          '<button class="enter-btn" id="enter-genesis-btn">[ ENTER GENESIS ]</button>' +
        '</div>' +
      '</div>' +
      '<div class="enter-footer">' +
        '<div class="enter-footer-powered">Powered by <strong>GENESIS Intelligence Engine</strong></div>' +
        '<div class="enter-footer-creator">Created by Avishkar Roopi</div>' +
        '<div class="enter-footer-disclaimer">' +
          'GENESIS is an experimental artificial intelligence system currently under development by a single creator. ' +
          'Some features may contain defects or unexpected behavior.<br>' +
          'If you encounter issues or have suggestions, please contact: aavishkarroopi@gmail.com | +91 9398017435' +
        '</div>' +
      '</div>' +
      '<svg class="enter-sparkle" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
        '<path d="M12 2L13.5 9.5L21 12L13.5 14.5L12 22L10.5 14.5L3 12L10.5 9.5L12 2Z" fill="#c0d0e0" opacity="0.7"/>' +
      '</svg>';
    document.body.appendChild(el);
    return el;
  }

  // ── Neural Network Particle Background ──
  function initNeuralBg(canvas) {
    var ctx = canvas.getContext("2d");
    var W, H, nodes = [], edges = [];
    var PARTICLE_COUNT = 80;
    var CONNECT_DIST = 160;

    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    for (var i = 0; i < PARTICLE_COUNT; i++) {
      nodes.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        r: 1.5 + Math.random() * 2.5
      });
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);

      // Draw edges
      for (var i = 0; i < nodes.length; i++) {
        for (var j = i + 1; j < nodes.length; j++) {
          var dx = nodes[i].x - nodes[j].x;
          var dy = nodes[i].y - nodes[j].y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECT_DIST) {
            var alpha = (1 - dist / CONNECT_DIST) * 0.35;
            ctx.strokeStyle = "rgba(0,200,220," + alpha + ")";
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw nodes
      for (var k = 0; k < nodes.length; k++) {
        var n = nodes[k];
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0,229,255,0.85)";
        ctx.shadowColor = "#00e5ff";
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Move
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;
      }

      requestAnimationFrame(draw);
    }
    draw();
  }

  // ── Show Enter Screen after splash dismisses ──
  function showEnterScreen() {
    var screen = buildEnterScreen();
    var canvas = document.getElementById("enter-bg-canvas");
    if (canvas) initNeuralBg(canvas);

    // Fade in
    requestAnimationFrame(function () {
      screen.classList.add("visible");
    });

    // Button click
    document.getElementById("enter-genesis-btn").addEventListener("click", function () {
      screen.classList.add("fade-out");
      setTimeout(function () {
        screen.remove();
        // Dispatch event for screen_router to handle next step
        window.dispatchEvent(new CustomEvent("genesis_enter_complete"));
      }, 1000);
    });
  }

  // Expose globally for screen_router.js
  window.GenesisEnterScreen = { show: showEnterScreen };
})();
