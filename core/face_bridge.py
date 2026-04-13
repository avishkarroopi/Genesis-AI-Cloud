# face_bridge.py
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

def send_event(event_type: str, data: Optional[Dict[str, Any]] = None):
    """
    Emits an AVATAR_EVENT over the EventBus.
    The FastAPI WebSocket manager in server/voice_ws.py listens for these 
    and broadcasts them to connected browsers.
    """
    message = {
        "type": event_type,
        "data": data or {}
    }
    
    bus = get_event_bus()
    if bus:
        try:
            # Sync to async boundary bridge
            bus.publish_sync(
                event_type="AVATAR_EVENT",
                source="face_bridge",
                data=message
            )
        except Exception as e:
            logger.error(f"[FACE BRIDGE] Failed to emit AVATAR_EVENT: {e}")

def speech_start():
    send_event("speech_start")
    send_event("set_state", {"state": "SPEAKING"})

def speech_stop():
    send_event("speech_stop")
    send_event("set_state", {"state": "IDLE"})

def listening_start():
    send_event("listening_start")
    send_event("set_state", {"state": "LISTENING"})

def listening_stop():
    send_event("listening_stop")
    send_event("set_state", {"state": "IDLE"})

def start_bridge():
    """
    Initializes subscriptions that map core brain events to frontend UI events.
    Called once during genesis boot.
    """
    bus = get_event_bus()
    if bus:
        bus.subscribe("EMOTION_UPDATE", lambda e: send_event("set_emotion", {"emotion": str(e.data.get("emotion", "READY")).upper()}))
        bus.subscribe("VOICE_START", lambda e: send_event("set_mic", {"mic": "ACTIVE"}))
        bus.subscribe("VOICE_END", lambda e: send_event("set_mic", {"mic": "ON"}))
        logger.info("[FACE BRIDGE] Initialized server-side avatar proxy")

