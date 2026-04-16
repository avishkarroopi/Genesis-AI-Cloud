/** Workspace: System Intelligence Monitor */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "system_intelligence_monitor") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">📊</span> Telemetry Overview</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value" id="ws-tel-events">—</div><div class="ws-stat-label">Total Events</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value" id="ws-tel-cat">—</div><div class="ws-stat-label">Categories</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">30s</div><div class="ws-stat-label">Flush Rate</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">⚡</span> Event Bus Throughput</div>'+
        '<div class="ws-bar-chart" style="height:100px;">'+
          '<div class="ws-bar" style="height:45%"></div>'+
          '<div class="ws-bar green" style="height:72%"></div>'+
          '<div class="ws-bar purple" style="height:60%"></div>'+
          '<div class="ws-bar" style="height:88%"></div>'+
          '<div class="ws-bar green" style="height:55%"></div>'+
          '<div class="ws-bar purple" style="height:95%"></div>'+
          '<div class="ws-bar" style="height:40%"></div>'+
          '<div class="ws-bar green" style="height:68%"></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔔</span> Anomaly Detection</div>'+
        '<ul class="ws-list">'+
          '<li>Failure Burst Detector <span class="ws-badge online">Armed</span></li>'+
          '<li>Token Budget Guard <span class="ws-badge online">Active</span></li>'+
          '<li>Latency Spike Alert <span class="ws-badge idle">Standby</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📋</span> Live Metrics Feed</div>'+
        '<div class="ws-log" id="ws-tel-log">'+
          '<div><span class="log-time">TEL</span> <span class="log-ok">Inference Monitor active</span></div>'+
          '<div><span class="log-time">TEL</span> Batch processor running (30s flush)</div>'+
        '</div>'+
      '</div>';
    fetch("/api/system/metrics").then(function(r){return r.json();}).then(function(d){
      if(d.metrics){
        var el=document.getElementById("ws-tel-events");
        var cl=document.getElementById("ws-tel-cat");
        var total=0; d.metrics.forEach(function(m){total+=m.events;});
        if(el) el.textContent=total;
        if(cl) cl.textContent=d.metrics.length;
      }
    }).catch(function(){});
  });
})();
