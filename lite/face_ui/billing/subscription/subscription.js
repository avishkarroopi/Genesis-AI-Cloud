/**
 * subscription.js — GENESIS Subscription Screen
 * Shows 4 plans + GENESIS ALL early-access button.
 * Subscribe buttons are dummy. GENESIS ALL loads dashboard.
 * Does NOT modify any existing GENESIS files.
 */
(function () {
  "use strict";

  var PLANS = [
    {
      name: "GENESIS Lite",
      price: "Free or ₹99/month",
      features: [
        { icon: "fi", text: "Real-time speaking GENESIS avatar" },
        { icon: "fi", text: "Basic AI conversation" },
        { icon: "fb", text: "Bring Your Own API Keys (BYO Keys)" },
        { icon: "fi", text: "Limited daily prompts" },
        { icon: "fi", text: "Single device access" }
      ],
      restrictions: [
        "No life memory",
        "No automation",
        "No research AI",
        "No device control",
        "No digital twin"
      ]
    },
    {
      name: "GENESIS Core",
      price: "₹499/month    ₹4,999/year",
      features: [
        { icon: "fi", text: "Real-time speaking avatar" },
        { icon: "fi", text: "Personal AI assistant" },
        { icon: "fi", text: "Basic life memory" },
        { icon: "fi", text: "Basic automation" },
        { icon: "fi", text: "Research AI tools" },
        { icon: "fi", text: "PC device control" },
        { icon: "fb", text: "Bring Your Own API Keys (BYO Keys)" },
        { icon: "fi", text: "Regular updates" }
      ],
      restrictions: [
        "Limited memory storage",
        "Limited automation workflows"
      ]
    },
    {
      name: "GENESIS Gold",
      price: "₹1,499/month    ₹14,999/year",
      popular: true,
      features: [
        { icon: "fi", text: "Everything in Core +" },
        { icon: "fi", text: "Advanced life memory" },
        { icon: "fi", text: "Automation AI agents" },
        { icon: "fi", text: "Multi-device synchronization" },
        { icon: "fi", text: "Digital twin intelligence" },
        { icon: "fi", text: "Office automation" },
        { icon: "fi", text: "Advanced research AI" },
        { icon: "fi", text: "Environment awareness modules" },
        { icon: "fb", text: "Bring Your Own API Keys (BYO Keys)" },
        { icon: "fi", text: "Priority updates" }
      ],
      restrictions: []
    },
    {
      name: "GENESIS Platinum",
      price: "₹4,999/month    ₹49,999/year",
      features: [
        { icon: "fi", text: "Everything in Gold +" },
        { icon: "fi", text: "Unlimited life memory" },
        { icon: "fi", text: "Advanced digital twin modeling" },
        { icon: "fi", text: "Business intelligence AI" },
        { icon: "fi", text: "Enterprise automation" },
        { icon: "fi", text: "Smart home / office control" },
        { icon: "fi", text: "Predictive planning engine" },
        { icon: "fi", text: "Multi-agent orchestration" },
        { icon: "fb", text: "Bring Your Own API Keys (BYO Keys)" },
        { icon: "fi", text: "Premium support" },
        { icon: "fi", text: "Early access to experimental modules" }
      ],
      restrictions: []
    }
  ];

  function buildCard(plan) {
    var html = '<div class="sub-card' + (plan.popular ? ' popular' : '') + '">';
    if (plan.popular) html += '<div class="sub-popular-badge">Most Popular Plan</div>';
    html += '<div class="sub-plan-name">' + plan.name + '</div>';
    html += '<div class="sub-plan-price">' + plan.price + '</div>';
    html += '<ul class="sub-features">';
    plan.features.forEach(function (f) {
      var ic = f.icon === "fb"
        ? '<span class="fb">' + f.text + '</span>'
        : '<span class="' + f.icon + '">' + (f.icon === "fi" ? "✦" : "✗") + '</span>' + f.text;
      if (f.icon === "fb") {
        html += '<li>' + ic + '</li>';
      } else {
        html += '<li><span class="' + f.icon + '">' + (f.icon === "fi" ? "✦" : "✗") + '</span>' + f.text + '</li>';
      }
    });
    html += '</ul>';
    if (plan.restrictions.length > 0) {
      html += '<div class="sub-restrictions-title">Restrictions</div>';
      html += '<ul class="sub-features">';
      plan.restrictions.forEach(function (r) {
        html += '<li><span class="fx">✗</span>' + r + '</li>';
      });
      html += '</ul>';
    }
    html += '<button class="sub-subscribe-btn">SUBSCRIBE</button>';
    html += '</div>';
    return html;
  }

  function buildScreen() {
    var el = document.createElement("div");
    el.id = "genesis-subscription-screen";
    var cardsHTML = "";
    PLANS.forEach(function (p) { cardsHTML += buildCard(p); });
    el.innerHTML =
      '<canvas id="sub-bg-canvas"></canvas>' +
      '<div class="sub-header">' +
        '<div class="sub-title">GENESIS Subscription Plans</div>' +
        '<div class="sub-subtitle">Choose Your Intelligence Level</div>' +
      '</div>' +
      '<div class="sub-plans">' + cardsHTML + '</div>' +
      '<div class="sub-genesis-all" id="sub-genesis-all-btn">' +
        '<div class="sub-genesis-all-title">GENESIS ALL</div>' +
        '<div class="sub-genesis-all-sub">Special Access for Early Users</div>' +
        '<div class="sub-genesis-all-desc">Everything in GENESIS unlocked completely free for our valuable initial users.</div>' +
      '</div>' +
      '<div class="sub-footer">Powered by GENESIS Intelligence Engine</div>' +
      '<svg class="sub-sparkle" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
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
    var isAnimating = true;
    canvas.__sub_cleanup = function() { isAnimating = false; window.removeEventListener("resize", resize); };
    for (var i = 0; i < COUNT; i++) {
      nodes.push({ x: Math.random()*W, y: Math.random()*H, vx: (Math.random()-0.5)*0.4, vy: (Math.random()-0.5)*0.4, r: 1.5+Math.random()*2 });
    }
    function draw() {
      ctx.clearRect(0,0,W,H);
      for(var i=0;i<nodes.length;i++){for(var j=i+1;j<nodes.length;j++){var dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<DIST){ctx.strokeStyle="rgba(0,200,220,"+(1-d/DIST)*0.28+")";ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.stroke();}}}
      for(var k=0;k<nodes.length;k++){var n=nodes[k];ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);ctx.fillStyle="rgba(0,229,255,0.75)";ctx.shadowColor="#00e5ff";ctx.shadowBlur=8;ctx.fill();ctx.shadowBlur=0;n.x+=n.vx;n.y+=n.vy;if(n.x<0||n.x>W)n.vx*=-1;if(n.y<0||n.y>H)n.vy*=-1;}
      if (isAnimating) requestAnimationFrame(draw);
    }
    draw();
  }

  function showSubscriptionScreen() {
    var screen = buildScreen();
    var canvas = document.getElementById("sub-bg-canvas");
    if (canvas) initBg(canvas);
    requestAnimationFrame(function () { screen.classList.add("visible"); });

    // GENESIS ALL — unlocks everything for early users
    document.getElementById("sub-genesis-all-btn").addEventListener("click", function () {
      localStorage.setItem("genesis_subscribed", "true");
      localStorage.setItem("genesis_plan", "GENESIS_ALL");
      screen.classList.add("fade-out");
      setTimeout(function () {
        var canvas = document.getElementById("sub-bg-canvas");
        if (canvas && canvas.__sub_cleanup) canvas.__sub_cleanup();
        screen.remove();
        window.dispatchEvent(new CustomEvent("genesis_subscription_complete"));
      }, 800);
    });
  }

  window.GenesisSubscriptionScreen = { show: showSubscriptionScreen };
})();
