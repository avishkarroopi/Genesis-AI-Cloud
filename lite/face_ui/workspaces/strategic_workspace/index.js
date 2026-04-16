/** Workspace: Strategic Workspace */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "strategic_workspace") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">🎯</span> Strategy Optimizer</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">0.95</div><div class="ws-stat-label">Approval Score</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">12</div><div class="ws-stat-label">Plans Evaluated</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">92%</div><div class="ws-stat-label">Approval Rate</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🗺️</span> Execution Graph</div>'+
        '<div class="ws-log">'+
          '<div><span class="log-time">PLAN</span> <span class="log-ok">Goal decomposed into 3 phases</span></div>'+
          '<div><span class="log-time">P1</span> Research → web_research_agent</div>'+
          '<div><span class="log-time">P2</span> Analyze → cognitive_orchestrator</div>'+
          '<div><span class="log-time">P3</span> Compile Report → file_agent</div>'+
          '<div><span class="log-time">OPT</span> <span class="log-ok">Strategy approved (score: 0.95)</span></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">⚖️</span> Executive Control</div>'+
        '<ul class="ws-list">'+
          '<li>Agent Coordinator <span class="ws-badge online">Active</span></li>'+
          '<li>Queue Status <span class="ws-badge online">Open</span></li>'+
          '<li>Health Lock <span class="ws-badge idle">Disengaged</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📈</span> Strategy History</div>'+
        '<div class="ws-bar-chart">'+
          '<div class="ws-bar green" style="height:95%"></div>'+
          '<div class="ws-bar green" style="height:85%"></div>'+
          '<div class="ws-bar" style="height:50%"></div>'+
          '<div class="ws-bar green" style="height:92%"></div>'+
          '<div class="ws-bar green" style="height:88%"></div>'+
          '<div class="ws-bar purple" style="height:75%"></div>'+
        '</div>'+
      '</div>';
  });
})();
