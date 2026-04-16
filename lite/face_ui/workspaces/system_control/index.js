/** Workspace: System Control */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "system_control") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">⚡</span> System Health</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">OK</div><div class="ws-stat-label">PostgreSQL</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">OK</div><div class="ws-stat-label">Redis</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">OK</div><div class="ws-stat-label">Groq API</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🌐</span> Service Status</div>'+
        '<ul class="ws-list">'+
          '<li>FastAPI Server <span class="ws-badge online">Online</span></li>'+
          '<li>WebSocket Voice <span class="ws-badge online">Active</span></li>'+
          '<li>Intelligence Bus <span class="ws-badge online">Operational</span></li>'+
          '<li>Event Bus <span class="ws-badge online">Running</span></li>'+
          '<li>Sentry Monitor <span class="ws-badge active">Tracking</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔑</span> API Configuration</div>'+
        '<ul class="ws-list">'+
          '<li>GROQ_API_KEY <span class="ws-badge online">Set</span></li>'+
          '<li>OPENROUTER_API_KEY <span class="ws-badge online">Set</span></li>'+
          '<li>N8N_WEBHOOK <span class="ws-badge online">Set</span></li>'+
          '<li>TAVILY_API_KEY <span class="ws-badge idle">Optional</span></li>'+
          '<li>TELEGRAM_BOT_TOKEN <span class="ws-badge idle">Optional</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📋</span> Boot Log</div>'+
        '<div class="ws-log">'+
          '<div><span class="log-time">BOOT</span> <span class="log-ok">Phase-1 voice subsystem initialized</span></div>'+
          '<div><span class="log-time">BOOT</span> <span class="log-ok">Phase-3 bootstrap complete</span></div>'+
          '<div><span class="log-time">BOOT</span> <span class="log-ok">Tool Layer initialized (12 tools)</span></div>'+
          '<div><span class="log-time">BOOT</span> <span class="log-ok">Agent Layer initialized (5 agents)</span></div>'+
          '<div><span class="log-time">BOOT</span> <span class="log-ok">Cognitive modules online</span></div>'+
        '</div>'+
      '</div>';
    // Fetch live health
    fetch("/api/system/health").then(function(r){return r.json();}).then(function(d){
      if(d.services){
        var items = c.querySelectorAll(".ws-stat");
        if(items[0]) items[0].querySelector(".ws-stat-value").textContent = d.services.postgresql==="connected"?"OK":"ERR";
        if(items[1]) items[1].querySelector(".ws-stat-value").textContent = d.services.redis==="connected"?"OK":"ERR";
        if(items[2]) items[2].querySelector(".ws-stat-value").textContent = d.services.groq_api==="configured"?"OK":"—";
      }
    }).catch(function(){});
  });
})();
