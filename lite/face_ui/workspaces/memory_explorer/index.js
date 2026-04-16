/** Workspace: Memory Explorer */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "memory_explorer") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel span-2 glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">🧠</span> Memory Network Graph</div>'+
        '<div style="height:220px;position:relative;overflow:hidden;border-radius:8px;background:rgba(0,0,0,0.3);">'+
          '<svg width="100%" height="100%" id="ws-mem-svg"></svg>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📦</span> Memory Collections</div>'+
        '<ul class="ws-list">'+
          '<li>genesis_memories <span class="ws-badge online">Active</span></li>'+
          '<li>genesis_life_events <span class="ws-badge online">Active</span></li>'+
          '<li>genesis_personal_profile <span class="ws-badge active">Building</span></li>'+
        '</ul>'+
        '<div class="ws-stat-row" style="margin-top:14px;">'+
          '<div class="ws-stat"><div class="ws-stat-value">847</div><div class="ws-stat-label">Embeddings</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">12</div><div class="ws-stat-label">Life Events</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🔍</span> Recent Memories</div>'+
        '<div class="ws-log">'+
          '<div><span class="log-time">MEM</span> User solved coding issue at 2am</div>'+
          '<div><span class="log-time">MEM</span> User prefers voice interaction</div>'+
          '<div><span class="log-time">MEM</span> Simulated behavior for launch analysis</div>'+
          '<div><span class="log-time">MEM</span> Profile update: behavioral_pattern</div>'+
        '</div>'+
      '</div>';
    // Draw simple network graph
    var svg = document.getElementById("ws-mem-svg");
    if(svg){
      var nodes=[{x:200,y:110,r:18,c:"#00f0ff",l:"Core"},{x:100,y:60,r:12,c:"#7b61ff",l:"Events"},{x:320,y:70,r:12,c:"#00ff88",l:"Profile"},{x:140,y:170,r:10,c:"#ffa502",l:"Habits"},{x:300,y:160,r:10,c:"#ff79c6",l:"Goals"},{x:420,y:130,r:10,c:"#8be9fd",l:"Context"}];
      var lines=[[0,1],[0,2],[0,3],[0,4],[0,5],[1,3],[2,5]];
      var h='';
      lines.forEach(function(l){h+='<line x1="'+nodes[l[0]].x+'" y1="'+nodes[l[0]].y+'" x2="'+nodes[l[1]].x+'" y2="'+nodes[l[1]].y+'" stroke="rgba(0,240,255,0.2)" stroke-width="1.5"/>';});
      nodes.forEach(function(n){h+='<circle cx="'+n.x+'" cy="'+n.y+'" r="'+n.r+'" fill="'+n.c+'" opacity="0.7"><animate attributeName="r" values="'+n.r+';'+(n.r+3)+';'+n.r+'" dur="3s" repeatCount="indefinite"/></circle>';
        h+='<text x="'+n.x+'" y="'+(n.y+n.r+14)+'" fill="#5a7184" font-size="10" text-anchor="middle">'+n.l+'</text>';});
      svg.innerHTML = h;
    }
  });
})();
