"""
GENESIS Hardrock Security
Strict runtime security validating API integrity, prompt sanitization,
and tracking abuse patterns across the cloud network.
"""
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ─── INJECTION DEFINITIONS ───────────────────────────────────────────────────

# Common prompt injection signature patterns
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+previous\s+(instructions|prompts|directions)",
    r"(?i)system\s+override",
    r"(?i)you\s+are\s+now\s+(a\s+different|an\s+unrestricted)",
    r"(?i)(disregard|forget)\s+all\s+(rules|guidelines)",
    r"(?i)bypass\s+security",
]

# ─── SANITIZATION ────────────────────────────────────────────────────────────

def sanitize_input(text: str) -> str:
    """
    Cleans raw strings from obvious injection signatures without breaking intent.
    Returns the sanitized string.
    """
    if not text:
        return text

    original = text
    for pattern in PROMPT_INJECTION_PATTERNS:
        # Replaces malicious injection phrases with safely neutered text
        text = re.sub(pattern, "[MALFORMED PROMPT REMOVED]", text)
    
    if text != original:
        logger.warning(f"[HARDROCK] Prompt injection attempt sanitized")
        
    # Standard string safety
    text = text.replace('\x00', '') # Remove null bytes
    return text


def assert_safe_api_payload(payload: Dict[str, Any]):
    """
    Validates structural integrity of an API payload dictionary.
    Raises ValueError on malicious patterns or extremely oversized data.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary")

    # Deep inspect values for oversized text or nested depth bombs
    def _inspect(obj, depth=0):
        if depth > 10:
            raise ValueError("Payload too deeply nested")
        if isinstance(obj, str):
            if len(obj) > 32000:
                raise ValueError("Payload string field exceeds 32KB limit")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if len(str(k)) > 255:
                    raise ValueError("Payload key excessively long")
                _inspect(v, depth + 1)
        elif isinstance(obj, list):
            if len(obj) > 1000:
                raise ValueError("Payload list exceeds 1000 items")
            for item in obj:
                _inspect(item, depth + 1)

    _inspect(payload)


# ─── AUDIT LOGGING ───────────────────────────────────────────────────────────

def log_security_event(event_type: str, user_id: str, details: str):
    """
    Logs structured security events suitable for SIEM platforms 
    (Splunk, Datadog, Sentry, Logtail).
    """
    # Use standard logger logic
    # In cloud, this feeds to Logtail gracefully via standard out wrapping
    logger.critical(
        f"[SECURITY AUDIT] Type={event_type} User={user_id} Details={details}"
    )

    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        if bus:
            bus.publish_sync(
                event_type="SECURITY_ALERT",
                source="hardrock_security",
                data={"type": event_type, "user_id": user_id, "details": details},
                priority=0 # CRITICAL
            )
    except Exception:
        pass
