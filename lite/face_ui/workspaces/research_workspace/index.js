/** Workspace: Research Workspace */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "research_workspace") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel span-2 glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔬</span> Research Lab</div>'+
        '<div style="display:flex;gap:8px;margin-bottom:14px;">'+
          '<input type="text" placeholder="Enter research query..." style="flex:1;padding:10px 14px;background:rgba(0,0,0,0.4);border:1px solid var(--ws-border);border-radius:8px;color:var(--ws-text);font-size:13px;outline:none;">'+
          '<button style="padding:10px 20px;background:rgba(0,240,255,0.12);border:1px solid var(--ws-accent);border-radius:8px;color:var(--ws-accent);cursor:pointer;">Search</button>'+
        '</div>'+
        '<div class="ws-log" style="min-height:180px;">'+
          '<div><span class="log-time">RES</span> <span class="log-ok">web_research_agent ready</span></div>'+
          '<div><span class="log-time">RES</span> Available: Tavily, SerpAPI, Firecrawl</div>'+
          '<div><span class="log-time">RES</span> Enter a query to begin research</div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📡</span> Search Providers</div>'+
        '<ul class="ws-list">'+
          '<li>Tavily API <span class="ws-badge idle">Standby</span></li>'+
          '<li>SerpAPI <span class="ws-badge idle">Standby</span></li>'+
          '<li>Firecrawl <span class="ws-badge idle">Standby</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📊</span> Research Stats</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat"><div class="ws-stat-value">0</div><div class="ws-stat-label">Queries</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">0</div><div class="ws-stat-label">Results</div></div>'+
        '</div>'+
      '</div>';
  });
})();
