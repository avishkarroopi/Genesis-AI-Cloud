/** Workspace: Personal Intelligence Dashboard */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "personal_intelligence_dashboard") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">👤</span> User Profile</div>'+
        '<ul class="ws-list">'+
          '<li>Preferred Interface <span style="color:var(--ws-accent);">Voice</span></li>'+
          '<li>Peak Hours <span style="color:var(--ws-accent);">11 PM – 3 AM</span></li>'+
          '<li>Top Tool <span style="color:var(--ws-accent);">web_search</span></li>'+
          '<li>Primary Channel <span style="color:var(--ws-accent);">Telegram</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔄</span> Habit Tracker</div>'+
        '<div class="ws-bar-chart" style="height:90px;">'+
          '<div class="ws-bar" style="height:20%" title="6AM"></div>'+
          '<div class="ws-bar" style="height:10%" title="9AM"></div>'+
          '<div class="ws-bar" style="height:35%" title="12PM"></div>'+
          '<div class="ws-bar green" style="height:70%" title="3PM"></div>'+
          '<div class="ws-bar" style="height:45%" title="6PM"></div>'+
          '<div class="ws-bar purple" style="height:85%" title="9PM"></div>'+
          '<div class="ws-bar green" style="height:95%" title="12AM"></div>'+
          '<div class="ws-bar" style="height:60%" title="3AM"></div>'+
        '</div>'+
        '<div style="text-align:center;font-size:10px;color:var(--ws-text-dim);margin-top:6px;">Activity by Hour</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🎯</span> Goal Tracking</div>'+
        '<ul class="ws-list">'+
          '<li>Launch GENESIS V2 <span class="ws-badge active">In Progress</span></li>'+
          '<li>Complete Agent Marketplace <span class="ws-badge idle">Planned</span></li>'+
          '<li>Deploy Production <span class="ws-badge online">Active</span></li>'+
        '</ul>'+
      '</div>';
  });
})();
