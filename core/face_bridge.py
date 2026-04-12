# face_bridge.py

import websocket
import json
import threading
import time
import logging

logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8080/ws"
ws_app = None
ws_thread = None
is_connected = False
_reconnect_requested = True
_bridge_started = False

def stop_bridge():
    global _reconnect_requested, ws_app, _bridge_started
    _reconnect_requested = False
    if ws_app:
        try:
            ws_app.close()
        except Exception:
            pass
    # Join ws_thread to ensure reconnect loop exits
    if ws_thread is not None and ws_thread.is_alive():
        try:
            ws_thread.join(timeout=3)
        except Exception:
            pass
    _bridge_started = False

def _on_open(ws):
    global is_connected
    logger.info("Face bridge connected to server.")
    is_connected = True
    
    # Emit full status packet after websocket connects
    status_packet = {
        "type": "set_status",
        "data": {
            "state": "IDLE",
            "status": "ONLINE",
            "emotion": "READY",
            "voice": "READY",
            "mic": "ON",
            "network": "CONNECTED",
            "camera": "OFF",
            "model": "IDLE"
        }
    }
    try:
        ws.send(json.dumps(status_packet))
    except Exception as e:
        logger.error(f"Failed to send initial status packet: {e}")

def _on_close(ws, close_status_code, close_msg):
    global is_connected
    logger.info("Face bridge disconnected.")
    is_connected = False

def _on_error(ws, error):
    logger.error(f"Face bridge error: {error}")

def _run_websocket():
    """Run WebSocket with auto-reconnect loop."""
    global ws_app, is_connected
    while _reconnect_requested:
        try:
            ws_app = websocket.WebSocketApp(
                WS_URL,
                on_open=_on_open,
                on_close=_on_close,
                on_error=_on_error
            )
            ws_app.run_forever()
        except Exception as e:
            if "10061" in str(e) or "ConnectionRefused" in str(e):
                logger.debug(f"Face bridge optional connection ignored: {e}")
            else:
                logger.error(f"Face bridge connection error: {e}")
        is_connected = False
        if _reconnect_requested:
            time.sleep(3)  # Wait before reconnect

def start_bridge():
    global ws_thread, _bridge_started
    # SAFEGUARD 7/14: Singleton Guard
    if _bridge_started:
        return
    _bridge_started = True

    # NOTE: face_server.py is already started by start_genesis.py
    # Do NOT launch it again here — it causes Errno 10048 port conflict

    if ws_thread is None or not ws_thread.is_alive():
        ws_thread = threading.Thread(target=_run_websocket, daemon=True)
        ws_thread.start()

    # Subscribe to backend events to proxy them to the UI HUD
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        if bus:
            # When emotion changes (e.g., from emotion_engine)
            bus.subscribe("EMOTION_UPDATE", lambda e: send_event("set_emotion", {"emotion": str(e.data.get("emotion", "READY")).upper()}))
            # When voice processing actually starts or mic goes active
            bus.subscribe("VOICE_START", lambda e: send_event("set_mic", {"mic": "ACTIVE"}))
            # When voice processing ends, mic returns to ON state (listening)
            bus.subscribe("VOICE_END", lambda e: send_event("set_mic", {"mic": "ON"}))
            bus.subscribe("VISEME_EVENT", lambda e: send_event("VISEME_EVENT", e.data))
    except Exception as e:
        logger.warning(f"Face bridge failed to subscribe to events: {e}")

from typing import Optional, Dict, Any

def send_event(event_type: str, data: Optional[Dict[str, Any]] = None):
    if not is_connected or ws_app is None:
        return  # Silently skip — bridge will reconnect automatically

    message = {
        "type": event_type,
        "data": data or {}
    }
    try:
        ws_app.send(json.dumps(message))  # type: ignore
    except Exception as e:
        logger.error(f"Failed to send event via face bridge: {e}")

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

# Do NOT auto-start on import — system.py will call start_bridge() when ready
