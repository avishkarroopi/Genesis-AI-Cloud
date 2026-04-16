/** Workspace: Coding Lab */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "coding_lab") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel span-2 glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">💻</span> Code Editor</div>'+
        '<div class="ws-log" style="min-height:280px;font-size:12px;">'+
          '<div style="color:#7b61ff;">// GENESIS Coding Lab — AI-Assisted Development</div>'+
          '<div style="color:#ff79c6;">import</div> <span style="color:#8be9fd;">{ agent_worker }</span> <span style="color:#ff79c6;">from</span> <span style="color:#f1fa8c;">"core/agents"</span>;'+
          '<div><br></div>'+
          '<div style="color:#50fa7b;">async function</div> <span style="color:#8be9fd;">executeTask</span>(goal) {'+
          '<div style="padding-left:20px;color:#f8f8f2;">const plan = await planner.create(goal);</div>'+
          '<div style="padding-left:20px;color:#f8f8f2;">return agent_worker.execute(plan);</div>'+
          '<div style="color:#f8f8f2;">}</div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">⚙️</span> Execution Agent</div>'+
        '<ul class="ws-list">'+
          '<li>Python Runtime <span class="ws-badge online">Ready</span></li>'+
          '<li>Sandbox Mode <span class="ws-badge active">Enabled</span></li>'+
          '<li>Last Execution <span class="ws-badge online">Success</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">📂</span> Recent Files</div>'+
        '<ul class="ws-list">'+
          '<li>brain_chain.py <span style="color:var(--ws-text-dim);font-size:11px;">32.3 KB</span></li>'+
          '<li>ai_router.py <span style="color:var(--ws-text-dim);font-size:11px;">20.1 KB</span></li>'+
          '<li>event_bus.py <span style="color:var(--ws-text-dim);font-size:11px;">11.1 KB</span></li>'+
          '<li>tool_registry.py <span style="color:var(--ws-text-dim);font-size:11px;">10.7 KB</span></li>'+
        '</ul>'+
      '</div>';
  });
})();
