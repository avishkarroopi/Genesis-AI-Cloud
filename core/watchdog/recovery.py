import time
import requests # type: ignore

def recover_router():
    """Attempts simple router fallback states if available, mostly logging."""
    print("[WATCHDOG-RECOVERY] Router ping failed. Models will automatically fallback via smart router mechanics.", flush=True)

def recover_websocket():
    """Forces face bridge reconnection."""
    try:
        from core import face_bridge # type: ignore
        print("[WATCHDOG-RECOVERY] Attempting face bridge WebSocket reconnection...", flush=True)
        face_bridge.is_connected = False
        # Face bridge automatically tries to reconnect if its internal loop is alive,
        # but if the thread died, we can restart it.
        face_bridge.start_bridge()
    except Exception as e:
        print(f"[WATCHDOG-RECOVERY] Failed to recover websocket: {e}", flush=True)

def recover_audio():
    """Restarts custom mic stream in genesis_voice."""
    try:
        from core import genesis_voice # type: ignore
        print("[WATCHDOG-RECOVERY] Attempting Audio Mic Re-initialization...", flush=True)
        if genesis_voice.recognizer and genesis_voice.recognizer.stream:
            try:
                genesis_voice.recognizer.stop_listening()
            except Exception:
                pass
        
        # Re-bind logic
        genesis_voice.stop_listening = genesis_voice.recognizer.listen_in_background(genesis_voice._audio_callback)
        print("[WATCHDOG-RECOVERY] Audio Mic Re-initialized.", flush=True)
    except Exception as e:
        print(f"[WATCHDOG-RECOVERY] Failed to recover audio: {e}", flush=True)

def reset_state():
    """Forces GENESIS UI back to IDLE to break visual locks."""
    try:
        from core import face_bridge # type: ignore
        print("[WATCHDOG-RECOVERY] Forcing IDLE state to un-stick UI.", flush=True)
        face_bridge.send_event("set_state", {"state": "IDLE"})
    except Exception as e:
        print(f"[WATCHDOG-RECOVERY] Failed to reset stuck state: {e}", flush=True)

def restart_component(name: str):
    """Generic component soft-restart."""
    print(f"[WATCHDOG-RECOVERY] Restarting component loosely: {name}", flush=True)
    if name == "websocket":
        recover_websocket()
    elif name == "audio":
        recover_audio()
    elif name == "router":
        recover_router()
