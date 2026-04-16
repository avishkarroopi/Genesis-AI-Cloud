/**
 * workspace_manager.js — GENESIS Workspace Interface Manager
 * Manages workspace lifecycle: open, switch, close.
 * Does NOT modify any existing file — purely additive.
 */
(function () {
  "use strict";

  const WORKSPACES = [
    { id: "conversation_interface",          label: "Conversation",            icon: "💬" },
    { id: "coding_lab",                      label: "Coding Lab",              icon: "💻" },
    { id: "agent_manager",                   label: "Agent Manager",           icon: "🤖" },
    { id: "system_control",                  label: "System Control",          icon: "⚡" },
    { id: "memory_explorer",                 label: "Memory Explorer",         icon: "🧠" },
    { id: "system_intelligence_monitor",     label: "Intelligence Monitor",    icon: "📊" },
    { id: "model_health_monitor",            label: "Model Health",            icon: "🩺" },
    { id: "research_workspace",              label: "Research Lab",            icon: "🔬" },
    { id: "strategic_workspace",             label: "Strategic Command",       icon: "🎯" },
    { id: "personal_intelligence_dashboard", label: "Personal Intelligence",   icon: "👤" },
    { id: "learning_engine",                 label: "Learning Engine",         icon: "📚" },
    { id: "synthetic_intelligence_core",     label: "Synthetic Core",          icon: "🔮" },
    { id: "health_monitor",                  label: "Health Intelligence",     icon: "❤️" },
    { id: "human_analysis",                  label: "Human Analysis",          icon: "🧬" }
  ];

  let layer = null;
  let currentId = null;
  let contentEl = null;
  let headerTitleEl = null;
  let headerSubEl = null;

  function buildShell() {
    layer = document.createElement("div");
    layer.id = "genesis-workspace-layer";

    // Sidebar
    let sb = '<div class="ws-sidebar"><div class="ws-sidebar-logo">⬡ GENESIS</div>';
    WORKSPACES.forEach(function (w) {
      sb += '<div class="ws-nav-item" data-ws="' + w.id + '"><span class="nav-icon">' + w.icon + '</span>' + w.label + '</div>';
    });
    sb += '<div class="ws-nav-divider"></div>';
    sb += '<div class="ws-sidebar-close" id="ws-close-btn">✕ Back to Avatar</div>';
    sb += '</div>';

    // Main
    sb += '<div class="ws-main">';
    sb += '<div class="ws-header"><div><div class="ws-header-title" id="ws-h-title">Workspace</div>';
    sb += '<div class="ws-header-subtitle" id="ws-h-sub">Select a workspace</div></div>';
    sb += '<div class="ws-header-status"><span class="dot"></span> LIVE</div></div>';
    sb += '<div class="ws-content" id="ws-content"></div></div>';

    layer.innerHTML = sb;
    document.body.appendChild(layer);

    contentEl = document.getElementById("ws-content");
    headerTitleEl = document.getElementById("ws-h-title");
    headerSubEl = document.getElementById("ws-h-sub");

    // Event: nav clicks
    layer.querySelectorAll(".ws-nav-item").forEach(function (el) {
      el.addEventListener("click", function () { openWorkspace(el.getAttribute("data-ws")); });
    });

    // Event: close
    document.getElementById("ws-close-btn").addEventListener("click", closeAll);
  }

  function openWorkspace(id) {
    if (!layer) buildShell();
    layer.classList.add("active");

    // Highlight nav
    layer.querySelectorAll(".ws-nav-item").forEach(function (n) {
      n.classList.toggle("active", n.getAttribute("data-ws") === id);
    });

    var ws = WORKSPACES.find(function (w) { return w.id === id; });
    if (!ws) return;

    headerTitleEl.textContent = ws.icon + " " + ws.label;
    headerSubEl.textContent = "Workspace Module";
    currentId = id;

    // Render workspace content
    contentEl.innerHTML = '<div style="text-align:center;padding:40px;color:var(--ws-text-dim);">Loading...</div>';

    // Dispatch to workspace module
    var ev = new CustomEvent("genesis_workspace_render", { detail: { id: id, container: contentEl } });
    window.dispatchEvent(ev);
  }

  function closeAll() {
    if (layer) layer.classList.remove("active");
    currentId = null;
  }

  // Public API
  window.GenesisWorkspaceManager = {
    open: openWorkspace,
    close: closeAll,
    getActive: function () { return currentId; },
    list: function () { return WORKSPACES.slice(); }
  };

  // Build shell on load
  window.addEventListener("load", function () { buildShell(); });
})();
