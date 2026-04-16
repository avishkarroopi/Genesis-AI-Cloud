/** Workspace: Learning Engine */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "learning_engine") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">📚</span> Learning Memory</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">38</div><div class="ws-stat-label">Insights Stored</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">12</div><div class="ws-stat-label">Corrections</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">94%</div><div class="ws-stat-label">Improvement</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔄</span> Reflection Engine</div>'+
        '<div class="ws-log">'+
          '<div><span class="log-time">REF</span> <span class="log-warn">Detected: High failure rate in OpenAI API</span></div>'+
          '<div><span class="log-time">REF</span> <span class="log-ok">Mitigation: Increase dynamic tool timeout</span></div>'+
          '<div><span class="log-time">REF</span> Strategy rules updated successfully</div>'+
          '<div><span class="log-time">REF</span> <span class="log-ok">Performance improved by 12%</span></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📈</span> Performance Trend</div>'+
        '<div class="ws-bar-chart" style="height:80px;">'+
          '<div class="ws-bar" style="height:40%"></div>'+
          '<div class="ws-bar" style="height:55%"></div>'+
          '<div class="ws-bar green" style="height:68%"></div>'+
          '<div class="ws-bar green" style="height:75%"></div>'+
          '<div class="ws-bar green" style="height:82%"></div>'+
          '<div class="ws-bar green" style="height:94%"></div>'+
        '</div>'+
        '<div style="text-align:center;font-size:10px;color:var(--ws-text-dim);margin-top:6px;">Accuracy Over Time →</div>'+
      '</div>';
  });
})();
