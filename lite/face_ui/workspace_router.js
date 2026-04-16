/**
 * workspace_router.js — GENESIS Voice Command → Workspace Router
 * Listens for voice transcripts, classifies intent, routes to workspace manager.
 * Does NOT modify voice pipeline, brain_chain, or any existing file.
 */
(function () {
  "use strict";

  var INTENT_MAP = [
    { patterns: ["open conversation", "conversation interface", "open chat"],       workspace: "conversation_interface" },
    { patterns: ["coding lab", "open code", "code editor", "open coding"],          workspace: "coding_lab" },
    { patterns: ["show agents", "agent manager", "open agents"],                    workspace: "agent_manager" },
    { patterns: ["system control", "open system", "system settings"],               workspace: "system_control" },
    { patterns: ["memory graph", "memory explorer", "show memory", "open memory"],  workspace: "memory_explorer" },
    { patterns: ["intelligence monitor", "system monitor", "open monitor"],         workspace: "system_intelligence_monitor" },
    { patterns: ["model health", "ai models", "show ai models", "model monitor"],   workspace: "model_health_monitor" },
    { patterns: ["research workspace", "open research", "research lab"],             workspace: "research_workspace" },
    { patterns: ["strategic workspace", "open strategic", "strategy", "strategic command"], workspace: "strategic_workspace" },
    { patterns: ["personal intelligence", "personal dashboard"],                    workspace: "personal_intelligence_dashboard" },
    { patterns: ["learning engine", "open learning"],                               workspace: "learning_engine" },
    { patterns: ["synthetic core", "synthetic intelligence"],                       workspace: "synthetic_intelligence_core" },
    { patterns: ["health monitor", "health intelligence"],                          workspace: "health_monitor" },
    { patterns: ["human analysis", "human intelligence"],                           workspace: "human_analysis" },
    { patterns: ["close workspace", "back to avatar", "close all", "go back"],      workspace: "__close__" }
  ];

  function classifyIntent(transcript) {
    var t = transcript.toLowerCase().replace(/genesis[\s,]*/gi, "").trim();
    for (var i = 0; i < INTENT_MAP.length; i++) {
      for (var j = 0; j < INTENT_MAP[i].patterns.length; j++) {
        if (t.indexOf(INTENT_MAP[i].patterns[j]) !== -1) {
          return INTENT_MAP[i].workspace;
        }
      }
    }
    return null;
  }

  function handleTranscript(transcript) {
    var ws = classifyIntent(transcript);
    if (!ws) return false;

    if (ws === "__close__") {
      if (window.GenesisWorkspaceManager) window.GenesisWorkspaceManager.close();
      window.dispatchEvent(new CustomEvent("workspace_focus", { detail: { workspace: null, action: "close" } }));
      return true;
    }

    if (window.GenesisWorkspaceManager) window.GenesisWorkspaceManager.open(ws);
    window.dispatchEvent(new CustomEvent("workspace_open_request", { detail: { workspace: ws } }));
    window.dispatchEvent(new CustomEvent("workspace_switch", { detail: { workspace: ws } }));
    return true;
  }

  // Listen for WebSocket voice transcripts
  window.addEventListener("genesis_ws_message", function (e) {
    var msg = e.detail;
    if (msg && (msg.type === "transcript" || msg.type === "final_transcript")) {
      var text = (msg.data && msg.data.text) || msg.text || "";
      if (text.toLowerCase().indexOf("genesis") !== -1) {
        handleTranscript(text);
      }
    }
  });

  // Public API for programmatic routing
  window.GenesisWorkspaceRouter = {
    route: handleTranscript,
    classify: classifyIntent
  };
})();
