"""
Phase-1 — Semantic Router
Replaces brittle keyword matching with embedding-based intent classification.
Uses existing Ollama nomic-embed-text embeddings via memory_embed.
"""

import math
import threading

# Intent description corpus — each string describes what that intent sounds like
INTENT_DESCRIPTIONS = {
    "CODING": "write code program debug function script fix bug software developer python javascript",
    "RESEARCH": "research explain information history details tell me about what is describe summarize learn knowledge",
    "REASONING": "analyze strategy compare pros and cons decision plan think evaluate assess reason logic",
    "AUTOMATION": "run execute open launch workflow automate start trigger send automation schedule",
    "GENERAL": "hello hi how are you thank you good morning chat talk conversation general who are you who is your owner who created you who built you what are you tell me about yourself"
}

# Routing rules per intent
_INTENT_CONFIG = {
    "CODING":     {"use_planner": False, "use_tools": False},
    "RESEARCH":   {"use_planner": True,  "use_tools": False},
    "REASONING":  {"use_planner": True,  "use_tools": False},
    "AUTOMATION": {"use_planner": False, "use_tools": True},
    "GENERAL":    {"use_planner": False, "use_tools": False},
}

_MIN_CONFIDENCE = 0.3  # Below this, return GENERAL


def _cosine_similarity(vec_a, vec_b):
    """Pure-Python cosine similarity. No numpy needed."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SemanticRouter:
    """Embedding-based intent classifier using cosine similarity."""

    def __init__(self):
        self._intent_embeddings = {}  # intent_name -> embedding vector
        self._ready = False
        self._lock = threading.Lock()
        # Pre-compute intent embeddings in background
        t = threading.Thread(target=self._precompute, daemon=True, name="SemanticRouterInit")
        t.start()

    def _precompute(self):
        """Pre-compute embeddings for all intent descriptions."""
        try:
            from core.memory.memory_embed import get_embedding
            for intent, description in INTENT_DESCRIPTIONS.items():
                emb = get_embedding(description)
                if emb:
                    self._intent_embeddings[intent] = emb
            if self._intent_embeddings:
                self._ready = True
                print(f"[SEMANTIC] Router ready with {len(self._intent_embeddings)} intents", flush=True)
            else:
                print("[SEMANTIC] No embeddings computed — will fallback to keywords", flush=True)
        except Exception as e:
            print(f"[SEMANTIC] Init failed (non-fatal): {e}", flush=True)

    def analyze(self, command):
        """Classify command intent using embedding similarity.
        Returns a RoutingDecision or None if not ready / low confidence.
        """
        # --- FIX 1: AUTOMATION KEYWORD RE-ROUTING ---
        action_keywords = [
            "open", "launch", "start", "run", "execute", "load", "play", "watch", "stream",
            "search", "find", "show", "browse", "visit", "navigate", "go to", "download",
            "upload", "install", "uninstall", "create", "delete", "rename", "move", "copy",
            "save", "send", "message", "text", "email", "mail", "reply", "forward", "compose",
            "call", "dial", "turn on", "turn off", "enable", "disable", "activate", "deactivate",
            "increase", "decrease"
        ]
        
        target_keywords = [
            "youtube", "google", "gmail", "whatsapp", "telegram", "discord",
            "spotify", "browser", "chrome", "edge", "firefox", "linkedin", "twitter",
            "facebook", "instagram", "reddit", "amazon", "netflix", "maps", "drive"
        ]
        
        system_actions = [
            "shutdown", "restart", "lock", "sleep", "take screenshot", "record screen",
            "set reminder", "set alarm", "create note", "add task", "schedule meeting", "start timer",
            "pause", "stop", "skip", "next", "previous", "volume up", "volume down", "mute"
        ]
        
        cmd = command.lower().strip()
        if (any(a in cmd for a in action_keywords) and any(t in cmd for t in target_keywords)) or \
           any(s in cmd for s in system_actions):
            try:
                from core.ai_router import RoutingDecision
                cfg = _INTENT_CONFIG.get("AUTOMATION", _INTENT_CONFIG["GENERAL"])
                return RoutingDecision(
                    intent="AUTOMATION",
                    model="phi3",
                    use_planner=cfg["use_planner"],
                    use_tools=cfg["use_tools"]
                )
            except Exception as e:
                print(f"[SEMANTIC] Automation override failed: {e}", flush=True)

        if not self._ready or not self._intent_embeddings:
            return None

        try:
            from core.memory.memory_embed import get_embedding
            from core.ai_router import RoutingDecision

            query_emb = get_embedding(command)
            if not query_emb:
                return None

            best_intent = "GENERAL"
            best_score = -1.0

            for intent, intent_emb in self._intent_embeddings.items():
                score = _cosine_similarity(query_emb, intent_emb)
                if score > best_score:
                    best_score = score
                    best_intent = intent

            if best_score < _MIN_CONFIDENCE:
                best_intent = "GENERAL"

            print(f"[SEMANTIC] Intent={best_intent} score={best_score:.3f}", flush=True)

            cfg = _INTENT_CONFIG.get(best_intent, _INTENT_CONFIG["GENERAL"])
            return RoutingDecision(
                intent=best_intent,
                model="phi3",
                use_planner=cfg["use_planner"],
                use_tools=cfg["use_tools"]
            )
        except Exception as e:
            print(f"[SEMANTIC] Analysis failed: {e}", flush=True)
            return None


# Global singleton
_semantic_router = None
_sr_lock = threading.Lock()


def get_semantic_router():
    """Get or create the global SemanticRouter."""
    global _semantic_router
    if _semantic_router is None:
        with _sr_lock:
            if _semantic_router is None:
                _semantic_router = SemanticRouter()
    return _semantic_router
