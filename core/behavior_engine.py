"""
GENESIS Behavior Engine.
Phase 6 Requirement.
Decides idle robot actions.
"""
import time
import random
import threading
from typing import Optional
from core.event_bus import get_event_bus
from core import motion_system

class BehaviorEngine:
    def __init__(self):
        self.current_state = "idle"
        self.is_running = False
        self.behavior_thread: Optional[threading.Thread] = None

    def get_state(self):
        return self.current_state

    def set_state(self, new_state):
        if self.current_state != new_state:
            self.current_state = new_state
            print(f"[BEHAVIOR] Transitioned to: {self.current_state.upper()}", flush=True)

    def update_behavior(self):
        if self.current_state == "idle":
            actions = ["look_around", "small_motion", "none"]
            weights = [0.2, 0.4, 0.4]
            action = random.choices(actions, weights=weights, k=1)[0]
            
            if action == "look_around":
                motion_system.look_at_sound(random.choice(["left", "right"]))
            elif action == "small_motion":
                motion_system.idle_motion()

    def start_engine(self):
        if self.is_running: return
        self.is_running = True
        t = threading.Thread(target=self._behavior_loop, daemon=True, name="BehaviorEngine")
        self.behavior_thread = t
        t.start()
        print("[BEHAVIOR] Behavior engine started.", flush=True)
        
        bus = get_event_bus()
        if bus:
            bus.subscribe("IDLE_EVENT", lambda e: self.set_state("idle"))
            bus.subscribe("VOICE_START", lambda e: self.set_state("listening"))
            bus.subscribe("WAKE_DETECTED", lambda e: self.set_state("alert"))
            bus.subscribe("COMMAND_RUN", lambda e: self.set_state("thinking"))
            bus.subscribe("SENSOR_TRIGGER", lambda e: self.set_state("reacting"))

    def _behavior_loop(self):
        time.sleep(3)
        while self.is_running:
            self.update_behavior()
            time.sleep(random.uniform(5.0, 15.0))

behavior = BehaviorEngine()

def update_behavior(): behavior.update_behavior()
def get_state(): return behavior.get_state()
def set_state(state): behavior.set_state(state)
def start_behavior_engine(): behavior.start_engine()
