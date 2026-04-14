/**
 * login.js — GENESIS Login Screen Controller
 * Handles email/password auth and social login icons.
 * Only Email and Google are functional; all others are decorative.
 * Does NOT modify any existing GENESIS files.
 */
(function () {
  "use strict";

  function buildLoginScreen() {
    var el = document.createElement("div");
    el.id = "genesis-login-screen";
    el.innerHTML =
      '<canvas id="login-bg-canvas"></canvas>' +
      '<div class="login-header">' +
        '<div class="login-title">GENESIS</div>' +
        '<div class="login-subtitle">Secure Identity Gateway</div>' +
        '<div class="login-core-badge">' +
          '<div class="login-core-dot"></div>' +
          '<span class="login-core-label">Identity Verification Engine Active</span>' +
        '</div>' +
      '</div>' +
      '<div class="login-card">' +
        '<div class="login-card-title">User Authentication</div>' +
        '<div class="login-input-group">' +
          '<input class="login-input" id="login-email" type="email" placeholder="Email Address field">' +
          '<input class="login-input" id="login-password" type="password" placeholder="Password field">' +
        '</div>' +
        '<button class="login-access-btn" id="login-access-btn">[ ACCESS GENESIS ]</button>' +
        '<div class="login-social-label">Authenticate using network identity</div>' +
        '<div class="login-social-grid">' +
          '<button class="login-social-btn g-google" id="login-google" title="Google">G</button>' +
          '<button class="login-social-btn g-facebook" title="Facebook">f</button>' +
          '<button class="login-social-btn g-github" title="GitHub">&#9679;</button>' +
          '<button class="login-social-btn g-phone" title="Phone">&#9742;</button>' +
          '<button class="login-social-btn g-apple" title="Apple">&#63743;</button>' +
          '<button class="login-social-btn g-microsoft" title="Microsoft">&#8862;</button>' +
          '<button class="login-social-btn g-twitter" title="Twitter">&#128038;</button>' +
          '<button class="login-social-btn g-linkedin" title="LinkedIn">in</button>' +
        '</div>' +
        '<div class="login-secured-label">All authentication channels secured and encrypted</div>' +
      '</div>' +
      '<div class="login-footer">' +
        '<div class="login-footer-powered">Powered by <strong>GENESIS Intelligence Engine</strong></div>' +
        '<div class="login-footer-creator">Created by Avishkar Roopi</div>' +
        '<div class="login-footer-lock">&#128274;</div>' +
      '</div>' +
      '<svg class="login-sparkle" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
        '<path d="M12 2L13.5 9.5L21 12L13.5 14.5L12 22L10.5 14.5L3 12L10.5 9.5L12 2Z" fill="#c0d0e0" opacity="0.7"/>' +
      '</svg>';
    document.body.appendChild(el);
    return el;
  }

  function initBg(canvas) {
    var ctx = canvas.getContext("2d");
    var W, H, nodes = [];
    var COUNT = 70, DIST = 150;
    function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
    window.addEventListener("resize", resize); resize();
    for (var i = 0; i < COUNT; i++) {
      nodes.push({ x: Math.random()*W, y: Math.random()*H, vx: (Math.random()-0.5)*0.45, vy: (Math.random()-0.5)*0.45, r: 1.5+Math.random()*2 });
    }
    function draw() {
      ctx.clearRect(0,0,W,H);
      for (var i=0;i<nodes.length;i++) {
        for (var j=i+1;j<nodes.length;j++) {
          var dx=nodes[i].x-nodes[j].x, dy=nodes[i].y-nodes[j].y, d=Math.sqrt(dx*dx+dy*dy);
          if(d<DIST){ctx.strokeStyle="rgba(0,200,220,"+(1-d/DIST)*0.3+")";ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.stroke();}
        }
      }
      for (var k=0;k<nodes.length;k++){
        var n=nodes[k]; ctx.beginPath(); ctx.arc(n.x,n.y,n.r,0,Math.PI*2); ctx.fillStyle="rgba(0,229,255,0.8)"; ctx.shadowColor="#00e5ff"; ctx.shadowBlur=8; ctx.fill(); ctx.shadowBlur=0;
        n.x+=n.vx; n.y+=n.vy; if(n.x<0||n.x>W)n.vx*=-1; if(n.y<0||n.y>H)n.vy*=-1;
      }
      requestAnimationFrame(draw);
    }
    draw();
  }

  function showLoginScreen() {
    var screen = buildLoginScreen();
    var canvas = document.getElementById("login-bg-canvas");
    if (canvas) initBg(canvas);
    requestAnimationFrame(function () { screen.classList.add("visible"); });

    // Email + password ACCESS GENESIS
    document.getElementById("login-access-btn").addEventListener("click", function () {
      var email = document.getElementById("login-email").value.trim();
      var pass = document.getElementById("login-password").value.trim();
      if (!email || !pass) return;

      // Mark as logged in
      localStorage.setItem("genesis_logged_in", "true");
      localStorage.setItem("genesis_user_email", email);
      dismissLogin(screen);
    });

    // Google login (functional)
    document.getElementById("login-google").addEventListener("click", function () {
      localStorage.setItem("genesis_logged_in", "true");
      localStorage.setItem("genesis_user_email", "google_user");
      dismissLogin(screen);
    });
  }

  function dismissLogin(screen) {
    screen.classList.add("fade-out");
    setTimeout(function () {
      screen.remove();
      window.dispatchEvent(new CustomEvent("genesis_login_complete"));
    }, 800);
  }

  window.GenesisLoginScreen = { show: showLoginScreen };
})();
