"""
Wake word detection system for GENESIS.
Phase 2 Requirement.
Continuous background listener that detects wake word to activate voice processing.
"""
import time
import queue
import threading
from typing import Optional
from core.event_bus import get_event_bus, EventPriority

WAKE_WORDS = ["genesis"]
COOLDOWN_TIME = 3

class WakeWordDetector:
    def __init__(self):
        self.is_listening = False
        self.last_activation: float = 0.0
        self.detector_thread: Optional[threading.Thread] = None

    def start_listener(self):
        """Starts the background wake word listener."""
        self.is_listening = True
        print("[WAKE_WORD] continuous wake word detector ready.", flush=True)

    def stop_listener(self):
        """Stops the background wake word listener."""
        self.is_listening = False

    def detect_wake(self, text: str) -> bool:
        import re
        text = text.lower().strip()
        print(f"WAKE TRACE: text eval '{text}'", flush=True)
        
        text = re.sub(r"[^\w\s]", "", text)
        
        if "genesis" in text:
            return True
            
        words = text.split()
        for word in words:
            if len(word) >= 3 and (word.startswith("gen") or word.startswith("jen")):
                return True
                
        return False

    def activate_voice(self, remaining_command: str, current_time: float):
        """Emits event to activate the system voice listener."""
        if current_time - self.last_activation > COOLDOWN_TIME:
            self.last_activation = current_time
            print("WAKE TRACE: wake detected", flush=True)
            print("Genesis Activated", flush=True)
            
            # Emit WAKE_DETECTED event
            bus = get_event_bus()
            
            # Use publish_sync which is thread-safe instead of raw asyncio calls
            if bus:
                try:
                    bus.publish_sync("WAKE_DETECTED", "wake_word", {"command": remaining_command}, EventPriority.HIGH)
                    print(f"[WAKE_WORD] Emitted WAKE_DETECTED event with command: '{remaining_command}'", flush=True)
                except Exception as e:
                    print(f"[WAKE_WORD] Failed to emit event: {e}", flush=True)




detector = WakeWordDetector()

def start_listener():
    detector.start_listener()

def detect_wake(text: str) -> bool:
    return detector.detect_wake(text)

def activate_voice(remaining_command: str = ""):
    detector.activate_voice(remaining_command, time.time())
