/** Workspace: Agent Manager */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "agent_manager") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🤖</span> Active Agents</div>'+
        '<ul class="ws-list">'+
          '<li>file_agent <span class="ws-badge online">Running</span></li>'+
          '<li>web_research_agent <span class="ws-badge online">Running</span></li>'+
          '<li>code_execution_agent <span class="ws-badge online">Running</span></li>'+
          '<li>communication_agent <span class="ws-badge idle">Idle</span></li>'+
          '<li>browser_automation_agent <span class="ws-badge idle">Idle</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔧</span> Registered Tools</div>'+
        '<ul class="ws-list" id="ws-tools-list">'+
          '<li>read_file <span class="ws-badge online">Active</span></li>'+
          '<li>write_file <span class="ws-badge online">Active</span></li>'+
          '<li>web_search <span class="ws-badge online">Active</span></li>'+
          '<li>send_telegram <span class="ws-badge idle">Standby</span></li>'+
          '<li>send_email <span class="ws-badge idle">Standby</span></li>'+
          '<li>run_script <span class="ws-badge online">Active</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📊</span> Agent Performance</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">12</div><div class="ws-stat-label">Tools</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">5</div><div class="ws-stat-label">Agents</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">142</div><div class="ws-stat-label">Executions</div></div>'+
        '</div>'+
        '<div class="ws-bar-chart" style="margin-top:16px;">'+
          '<div class="ws-bar" style="height:60%"></div>'+
          '<div class="ws-bar green" style="height:80%"></div>'+
          '<div class="ws-bar" style="height:45%"></div>'+
          '<div class="ws-bar purple" style="height:90%"></div>'+
          '<div class="ws-bar green" style="height:70%"></div>'+
          '<div class="ws-bar" style="height:55%"></div>'+
          '<div class="ws-bar purple" style="height:85%"></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📋</span> Event Bus Activity</div>'+
        '<div class="ws-log">'+
          '<div><span class="log-time">00:01</span> <span class="log-ok">FileWriteRequested</span> → file_agent</div>'+
          '<div><span class="log-time">00:02</span> <span class="log-ok">ResearchRequested</span> → web_research_agent</div>'+
          '<div><span class="log-time">00:03</span> plan_created → strategy_optimizer</div>'+
          '<div><span class="log-time">00:04</span> <span class="log-ok">strategy_approved</span> → executive_control</div>'+
          '<div><span class="log-time">00:05</span> tool_execution_end → tool_metrics</div>'+
        '</div>'+
      '</div>';
  });
})();
