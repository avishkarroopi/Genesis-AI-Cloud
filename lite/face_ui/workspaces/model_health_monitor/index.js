/** Workspace: Model Health Monitor */
(function(){
  window.addEventListener("genesis_workspace_render", function(e){
    if(e.detail.id !== "model_health_monitor") return;
    var c = e.detail.container;
    c.innerHTML =
      '<div class="ws-panel glow">'+
        '<div class="ws-panel-title"><span class="panel-icon">🩺</span> AI Model Status</div>'+
        '<ul class="ws-list">'+
          '<li>Groq (LLaMA-3) <span class="ws-badge online">Primary</span></li>'+
          '<li>OpenRouter <span class="ws-badge active">Fallback</span></li>'+
          '<li>Ollama (Local) <span class="ws-badge idle">Standby</span></li>'+
        '</ul>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">💰</span> Token Usage</div>'+
        '<div class="ws-stat-row">'+
          '<div class="ws-stat"><div class="ws-stat-value">24.8K</div><div class="ws-stat-label">Input Tokens</div></div>'+
          '<div class="ws-stat"><div class="ws-stat-value">18.3K</div><div class="ws-stat-label">Output Tokens</div></div>'+
          '<div class="ws-stat good"><div class="ws-stat-value">$0.12</div><div class="ws-stat-label">Est. Cost</div></div>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">⏱️</span> Latency by Provider</div>'+
        '<div class="ws-bar-chart" style="height:90px;">'+
          '<div class="ws-bar green" style="height:30%" title="Groq 0.8s"></div>'+
          '<div class="ws-bar" style="height:65%" title="OpenRouter 1.9s"></div>'+
          '<div class="ws-bar purple" style="height:90%" title="Ollama 3.2s"></div>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-around;font-size:10px;color:var(--ws-text-dim);margin-top:6px;">'+
          '<span>Groq</span><span>OpenRouter</span><span>Ollama</span>'+
        '</div>'+
      '</div>'+
      '<div class="ws-panel">'+
        '<div class="ws-panel-title"><span class="panel-icon">🛡️</span> Cost Guard</div>'+
        '<ul class="ws-list">'+
          '<li>Budget Limit <span style="color:var(--ws-accent);font-family:var(--ws-mono);">100,000 tokens</span></li>'+
          '<li>Current Usage <span style="color:var(--ws-accent3);font-family:var(--ws-mono);">43,100 tokens</span></li>'+
          '<li>Budget Status <span class="ws-badge online">Healthy</span></li>'+
        '</ul>'+
      '</div>';
  });
})();
