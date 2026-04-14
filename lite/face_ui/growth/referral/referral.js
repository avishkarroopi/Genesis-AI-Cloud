/**
 * referral.js — GENESIS Referral Intelligence Program
 * Shows referral ladder, founder circle benefits, progress, and share link.
 * Opens ONLY from hamburger menu, NOT in the startup flow.
 * Does NOT modify any existing GENESIS files.
 */
(function () {
  "use strict";

  var MILESTONES = [
    { count: 5,   reward: "Core free 3 months" },
    { count: 10,  reward: "Gold free 6 months" },
    { count: 20,  reward: "Gold free 1 year" },
    { count: 50,  reward: "Platinum free 1 year" },
    { count: 100, reward: "Genesis Founder Circle" }
  ];

  function getUserData() {
    return {
      username: localStorage.getItem("genesis_user_email") || "user123",
      referrals: parseInt(localStorage.getItem("genesis_referrals") || "0", 10),
      referral_link: "genesis.ai/signup?ref=" + (localStorage.getItem("genesis_user_email") || "username")
    };
  }

  function getNextMilestone(count) {
    for (var i = 0; i < MILESTONES.length; i++) {
      if (count < MILESTONES[i].count) return MILESTONES[i].count;
    }
    return MILESTONES[MILESTONES.length - 1].count;
  }

  function buildScreen() {
    var data = getUserData();
    var nextMs = getNextMilestone(data.referrals);
    var pct = Math.min(100, Math.round((data.referrals / nextMs) * 100));

    var el = document.createElement("div");
    el.id = "genesis-referral-screen";

    // Build ladder HTML
    var ladderHTML = "";
    for (var i = MILESTONES.length - 1; i >= 0; i--) {
      var m = MILESTONES[i];
      ladderHTML +=
        '<div class="ref-ladder-step">' +
          '<div class="ref-ladder-block">' + m.count + '</div>' +
          '<div class="ref-ladder-label">' + m.count + ' Referrals: <strong>' + m.reward + '</strong></div>' +
        '</div>';
    }

    el.innerHTML =
      '<canvas id="ref-bg-canvas"></canvas>' +
      '<button class="ref-close-btn" id="ref-close-btn">&times;</button>' +
      '<div class="ref-header">' +
        '<div class="ref-title">GENESIS</div>' +
        '<div class="ref-program-label">Referral Intelligence Program</div>' +
        '<div class="ref-tagline">Invite Friends. Unlock Intelligence Rewards.</div>' +
      '</div>' +
      '<div class="ref-body">' +
        '<div class="ref-ladder">' + ladderHTML + '</div>' +
        '<div class="ref-panel">' +
          '<div class="ref-founder-card">' +
            '<div class="ref-founder-title">Founder Circle benefits panel</div>' +
            '<ul class="ref-founder-list">' +
              '<li><span class="ref-dot"></span>Lifetime Gold subscription</li>' +
              '<li><span class="ref-dot"></span>Early feature access</li>' +
              '<li><span class="ref-dot"></span>Private founder community</li>' +
            '</ul>' +
          '</div>' +
          '<div>' +
            '<div class="ref-current-title">Your Current Referrals</div>' +
            '<div class="ref-current-stats">' +
              '<span class="ref-stat-big">' + data.referrals + '</span>' +
              '<span class="ref-stat-label">/ ' + nextMs + '</span>' +
              '<div class="ref-stat-right"><span class="ref-stat-big">' + data.referrals + '</span><span class="ref-stat-label">/ users</span></div>' +
            '</div>' +
            '<div class="ref-progress-bar"><div class="ref-progress-fill" style="width:' + pct + '%"></div></div>' +
            '<div class="ref-progress-note">Your users invited toward its next milestone.</div>' +
          '</div>' +
          '<div>' +
            '<div class="ref-link-title">Your Referral Link</div>' +
            '<div class="ref-link-box">' +
              '<input class="ref-link-input" id="ref-link-input" type="text" readonly value="' + data.referral_link + '">' +
            '</div>' +
            '<div class="ref-actions">' +
              '<button class="ref-action-btn" id="ref-copy-btn">COPY REFERRAL LINK</button>' +
              '<button class="ref-action-btn" id="ref-share-btn">SHARE INVITE</button>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="ref-footer">GENESIS Community Growth Engine</div>' +
      '<svg class="ref-sparkle" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
        '<path d="M12 2L13.5 9.5L21 12L13.5 14.5L12 22L10.5 14.5L3 12L10.5 9.5L12 2Z" fill="#c0d0e0" opacity="0.7"/>' +
      '</svg>';

    document.body.appendChild(el);
    return el;
  }

  function initBg(canvas) {
    var ctx = canvas.getContext("2d");
    var W, H, nodes = [];
    var COUNT = 60, DIST = 140;
    function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
    window.addEventListener("resize", resize); resize();
    for (var i = 0; i < COUNT; i++) {
      nodes.push({ x: Math.random()*W, y: Math.random()*H, vx: (Math.random()-0.5)*0.4, vy: (Math.random()-0.5)*0.4, r: 1.5+Math.random()*2 });
    }
    function draw() {
      ctx.clearRect(0,0,W,H);
      for(var i=0;i<nodes.length;i++){for(var j=i+1;j<nodes.length;j++){var dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<DIST){ctx.strokeStyle="rgba(0,200,220,"+(1-d/DIST)*0.28+")";ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.stroke();}}}
      for(var k=0;k<nodes.length;k++){var n=nodes[k];ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fillStyle="rgba(0,229,255,0.75)";ctx.shadowColor="#00e5ff";ctx.shadowBlur=8;ctx.fill();ctx.shadowBlur=0;n.x+=n.vx;n.y+=n.vy;if(n.x<0||n.x>W)n.vx*=-1;if(n.y<0||n.y>H)n.vy*=-1;}
      requestAnimationFrame(draw);
    }
    draw();
  }

  function showReferralScreen() {
    // Prevent duplicates
    if (document.getElementById("genesis-referral-screen")) return;
    var screen = buildScreen();
    var canvas = document.getElementById("ref-bg-canvas");
    if (canvas) initBg(canvas);
    requestAnimationFrame(function () { screen.classList.add("visible"); });

    // Close button
    document.getElementById("ref-close-btn").addEventListener("click", function () {
      screen.classList.add("fade-out");
      setTimeout(function () { screen.remove(); }, 800);
    });

    // Copy referral link
    document.getElementById("ref-copy-btn").addEventListener("click", function () {
      var input = document.getElementById("ref-link-input");
      if (input) {
        navigator.clipboard.writeText(input.value).then(function () {
          var btn = document.getElementById("ref-copy-btn");
          if (btn) { btn.textContent = "COPIED!"; setTimeout(function () { btn.textContent = "COPY REFERRAL LINK"; }, 2000); }
        });
      }
    });

    // Share invite
    document.getElementById("ref-share-btn").addEventListener("click", function () {
      var link = document.getElementById("ref-link-input").value;
      if (navigator.share) {
        navigator.share({ title: "Join GENESIS AI", text: "Try GENESIS – the AI operating system!", url: link });
      } else {
        navigator.clipboard.writeText(link);
        var btn = document.getElementById("ref-share-btn");
        if (btn) { btn.textContent = "LINK COPIED!"; setTimeout(function () { btn.textContent = "SHARE INVITE"; }, 2000); }
      }
    });
  }

  window.GenesisReferralScreen = { show: showReferralScreen };
})();
