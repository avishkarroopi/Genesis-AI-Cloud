"""
GENESIS LangSmith Tracing Initialization.
Activates LangChain tracing at runtime when LANGCHAIN_TRACING_V2=true.
"""

import os

_tracing_active = False


def init_langsmith_tracing():
    """Initialize LangSmith tracing if configured via environment variables."""
    global _tracing_active

    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.environ.get("LANGCHAIN_API_KEY", "")

    if not tracing_enabled or not api_key:
        print("[TRACING] LangSmith tracing not configured — skipping.", flush=True)
        return False

    try:
        # Set required environment variables for LangChain automatic tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ.setdefault("LANGCHAIN_PROJECT", "genesis-ai")
        os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

        # Verify the tracing client can be created
        try:
            from langsmith import Client
            client = Client()
            # Lightweight check — do not block boot on network failure
            print(f"[TRACING] LangSmith tracing initialized (project: {os.environ.get('LANGCHAIN_PROJECT')})", flush=True)
            _tracing_active = True
            return True
        except ImportError:
            print("[TRACING] langsmith package not installed — tracing unavailable.", flush=True)
            return False

    except Exception as e:
        print(f"[TRACING] LangSmith init failed: {e}", flush=True)
        return False


def is_tracing_active():
    """Check whether LangSmith tracing is currently active."""
    return _tracing_active


# Auto-initialize on import
init_langsmith_tracing()
