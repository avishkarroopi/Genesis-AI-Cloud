"""
GENESIS Motion System.
Phase 4 Requirement.
"""
from core.face_bridge import send_event
from core.event_bus import get_event_bus

class MotionSystem:
    def __init__(self):
        pass

    def idle_motion(self):
        print("[MOTION] Executing: idle_motion", flush=True)
        send_event("motion_idle")

    def look_at_sound(self, direction="center"):
        print(f"[MOTION] Executing: look_at_sound (direction: {direction})", flush=True)
        send_event("motion_look", {"direction": direction})

    def talk_motion(self):
        print("[MOTION] Executing: talk_motion", flush=True)
        send_event("motion_talk")

    def thinking_motion(self):
        print("[MOTION] Executing: thinking_motion", flush=True)
        send_event("motion_think")

    def greeting_motion(self):
        print("[MOTION] Executing: greeting_motion", flush=True)
        send_event("motion_greet")

    def sleep_motion(self):
        print("[MOTION] Executing: sleep_motion", flush=True)
        send_event("motion_sleep")


motion_system = MotionSystem()

def idle_motion(): motion_system.idle_motion()
def look_at_sound(dir="center"): motion_system.look_at_sound(dir)
def talk_motion(): motion_system.talk_motion()
def thinking_motion(): motion_system.thinking_motion()
def greeting_motion(): motion_system.greeting_motion()
def sleep_motion(): motion_system.sleep_motion()

def _handle_idle(event): idle_motion()
def _handle_voice_start(event): look_at_sound("center")
def _handle_wake(event): greeting_motion()

def start_motion_system():
    bus = get_event_bus()
    if bus:
        bus.subscribe("IDLE_EVENT", _handle_idle)
        bus.subscribe("VOICE_START", _handle_voice_start)
        bus.subscribe("WAKE_DETECTED", _handle_wake)
    print("[MOTION] Motion system initialized and bound.", flush=True)
