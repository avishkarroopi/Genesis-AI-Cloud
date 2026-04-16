/** Workspace: Health Monitor (MOCK) */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "health_monitor") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">❤️</span> Health Intelligence</div>'+
        '<div style="text-align:center;padding:20px;">'+
          '<div class="ws-ring" style="border-top-color:#ff4757;"><div class="ws-ring-value">♥</div></div>'+
          '<div style="margin-top:14px;font-size:12px;color:var(--ws-text-dim);">Biometric Monitoring</div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📊</span> Vitals (Simulated)</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">72</div><div class="ws-stat-label">Heart Rate</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">98%</div><div class="ws-stat-label">SpO2</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">7.2h</div><div class="ws-stat-label">Sleep</div></div>'+
        '</div>'+
        '<div style="text-align:center;font-size:11px;color:var(--ws-warn);margin-top:12px;">⚠ Wearable API integration not yet configured</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📈</span> Wellness Trend</div>'+
        '<div class="ws-bar-chart" style="height:70px;">'+
          '<div class="ws-bar green" style="height:70%"></div>'+
          '<div class="ws-bar green" style="height:75%"></div>'+
          '<div class="ws-bar green" style="height:80%"></div>'+
          '<div class="ws-bar green" style="height:72%"></div>'+
          '<div class="ws-bar green" style="height:85%"></div>'+
          '<div class="ws-bar green" style="height:78%"></div>'+
        '</div>'+
      '</div>';
  });
})();
