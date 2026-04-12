import time
import requests # type: ignore
from core.watchdog.recovery import recover_router, recover_websocket, recover_audio, reset_state # type: ignore

class SystemMonitorDaemon:
    def __init__(self):
        self.is_running = False
        
        # State tracking logic
        self.last_state = "IDLE"
        self.state_time = time.time()
        self.max_stuck_time = 90  # seconds
        
    def check_system(self):
        """Monitors router, websocket, voice, state, and loop checks."""
        # 1. Ollama Ping
        try:
            res = requests.get("http://localhost:11434", timeout=3)
            if res.status_code != 200:
                raise ValueError("Bad status code")
        except Exception:
            recover_router()
            
        # 2. Websocket Alive
        try:
            from core import face_bridge # type: ignore
            if not face_bridge.is_connected:
                recover_websocket()
        except Exception:
            pass
            
        # 3. Voice Alive (Check if stream is active)
        try:
            from core import genesis_voice # type: ignore
            if genesis_voice.recognizer and not genesis_voice.recognizer.stream.active: # type: ignore
                recover_audio()
        except Exception:
            pass
            
        # 4. Agent Loop Safe Bounds check
        try:
            import agent.agent_controller as ag # type: ignore
            ctrl = ag.agent_controller
            if ctrl.is_running:
                if (time.time() - ctrl.start_time) > ctrl.max_time_sec + 5:
                    print("[WATCHDOG] Agent loop running excessively long. Halting.", flush=True)
                    ctrl.stop()
        except Exception:
            pass

    def run_loop(self):
        """The physical background thread runner."""
        self.is_running = True
        print("[WATCHDOG] System Monitor active.", flush=True)
        
        while self.is_running:
            try:
                self.check_system()
                self._check_stuck_states()
            except Exception as e:
                print(f"[WATCHDOG] Internal monitor loop error safely caught: {e}", flush=True)
                
            time.sleep(5)  # Rest between checks
            
    def _check_stuck_states(self):
        global tracker_ref
        try:
            if not tracker_ref:
                tracker_ref = _wrap_face_bridge_state_tracking()
            
            if tracker_ref:
                state = tracker_ref.get("last_state", "IDLE")
                # Fix float subtraction bug natively
                t_val = tracker_ref.get("time", time.time())
                time_diff = time.time() - float(t_val)
                
                if state in ["THINKING", "SPEAKING", "PROCESSING", "ACTING"] and time_diff > self.max_stuck_time:
                    print(f"[WATCHDOG] State {state} stuck for {time_diff:.1f}s. Resetting UI.", flush=True)
                    from core.watchdog.recovery import reset_state # type: ignore
                    reset_state()
                    tracker_ref["last_state"] = "IDLE"
                    tracker_ref["time"] = time.time()
        except Exception as e:
            pass

def _wrap_face_bridge_state_tracking():
    """Non-intrusively wraps the face_bridge sender to track the last sent state."""
    try:
        from core import face_bridge # type: ignore
        original_send = face_bridge.send_event
        
        # State tracker obj bound to scope
        tracker = {"last_state": "IDLE", "time": time.time()}
        
        def safe_send_wrapper(event_type, data=None):
            if event_type == "set_state" and data and "state" in data:
                tracker["last_state"] = data["state"]
                tracker["time"] = time.time()
            return original_send(event_type, data)
            
        face_bridge.send_event = safe_send_wrapper
        return tracker
    except Exception as e:
        print(f"[WATCHDOG] Failed to bind state tracker: {e}", flush=True)
        return None

tracker_ref = None
