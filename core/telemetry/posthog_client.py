"""
GENESIS PostHog Analytics Client.
Provides event tracking for prompts, tool usage, agent execution,
automation triggers, payments, and errors.
Gracefully degrades if PostHog is not configured.
"""

import os
import logging
import threading

logger = logging.getLogger(__name__)

_posthog_client = None
_init_lock = threading.Lock()
_initialized = False


def _get_client():
    """Lazy-init the PostHog client singleton."""
    global _posthog_client, _initialized
    if _initialized:
        return _posthog_client

    with _init_lock:
        if _initialized:
            return _posthog_client

        api_key = os.environ.get("POSTHOG_API_KEY", "")
        host = os.environ.get("POSTHOG_HOST", "https://app.posthog.com")

        if not api_key:
            logger.info("[POSTHOG] API key not configured — analytics disabled.")
            _initialized = True
            return None

        try:
            import posthog
            posthog.project_api_key = api_key
            posthog.host = host
            _posthog_client = posthog
            _initialized = True
            logger.info(f"[POSTHOG] Analytics initialized → {host}")
            return _posthog_client
        except ImportError:
            logger.warning("[POSTHOG] posthog package not installed. Run: pip install posthog")
            _initialized = True
            return None
        except Exception as e:
            logger.error(f"[POSTHOG] Init failed: {e}")
            _initialized = True
            return None


def track_event(event_name: str, properties: dict = None, distinct_id: str = "genesis_system"):
    """Track an event in PostHog. Non-blocking and failure-safe."""
    try:
        client = _get_client()
        if not client:
            return
        client.capture(
            distinct_id=distinct_id,
            event=event_name,
            properties=properties or {}
        )
    except Exception as e:
        logger.debug(f"[POSTHOG] Event tracking failed (non-critical): {e}")


def identify_user(user_id: str, properties: dict = None):
    """Identify a user in PostHog."""
    try:
        client = _get_client()
        if not client:
            return
        client.identify(user_id, properties or {})
    except Exception as e:
        logger.debug(f"[POSTHOG] Identify failed (non-critical): {e}")
