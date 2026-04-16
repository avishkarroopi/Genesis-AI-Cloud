/** Workspace: Conversation Interface */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "conversation_interface") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel span-2 glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">💬</span> Live Conversation</div>'+
        '<div id="ws-conv-log" class="ws-log" style="min-height:260px;">'+
          '<div><span class="log-time">SYS</span> <span class="log-ok">GENESIS Conversational Interface Active</span></div>'+
          '<div><span class="log-time">SYS</span> Connected to brain_chain reasoning pipeline</div>'+
          '<div><span class="log-time">USR</span> What can you do?</div>'+
          '<div><span class="log-time">GEN</span> I can assist with research, coding, scheduling, and system control.</div>'+
        '</div>'+
        '<div style="margin-top:14px;display:flex;gap:8px;">'+
          '<input type="text" id="ws-conv-input" placeholder="Type a message..." style="flex:1;padding:10px 14px;background:rgba(0,0,0,0.4);border:1px solid var(--ws-border);border-radius:8px;color:var(--ws-text);font-size:13px;outline:none;">'+
          '<button style="padding:10px 20px;background:rgba(0,240,255,0.12);border:1px solid var(--ws-accent);border-radius:8px;color:var(--ws-accent);cursor:pointer;font-size:13px;">Send</button>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📡</span> Pipeline Status</div>'+
        '<ul class="ws-list">'+
          '<li>Voice Pipeline <span class="ws-badge online">Active</span></li>'+
          '<li>Brain Chain <span class="ws-badge online">Online</span></li>'+
          '<li>Event Bus <span class="ws-badge online">Running</span></li>'+
          '<li>WebSocket <span class="ws-badge active">Connected</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📊</span> Session Stats</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat good"><div class="ws-stat-value">24</div><div class="ws-stat-label">Messages</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">1.2s</div><div class="ws-stat-label">Avg Latency</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">98%</div><div class="ws-stat-label">Accuracy</div></div>'+
        '</div>'+
      '</div>';
  });
})();
