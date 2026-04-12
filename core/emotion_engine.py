"""
GENESIS Emotion Engine.
Phase 7 Requirement.
"""
from core.event_bus import get_event_bus
from core import motion_system

class EmotionEngine:
    def __init__(self):
        self.current_emotion = "idle"

    def get_emotion(self):
        return self.current_emotion

    def set_emotion(self, emotion):
        valid = ["idle", "happy", "thinking", "listening", "talking", "error", "sleep", "alert"]
        if emotion not in valid:
            emotion = "idle"
            
        if self.current_emotion != emotion:
            self.current_emotion = emotion
            print(f"[EMOTION] Shifted to: {emotion.upper()}", flush=True)
            self.update_emotion()

    def update_emotion(self):
        bus = get_event_bus()
        if bus:
            bus.publish_sync("EMOTION_UPDATE", "emotion_engine", {"emotion": self.current_emotion})
            
        # Tie emotion state to motions directly if needed
        if self.current_emotion == "thinking":
            motion_system.thinking_motion()
        elif self.current_emotion == "talking":
            motion_system.talk_motion()
        elif self.current_emotion == "sleep":
            motion_system.sleep_motion()
        elif self.current_emotion == "alert":
            motion_system.look_at_sound("center")
        elif self.current_emotion == "error":
            motion_system.idle_motion()
        elif self.current_emotion == "happy":
            motion_system.greeting_motion()

emotion_engine = EmotionEngine()

def get_emotion(): return emotion_engine.get_emotion()
def set_emotion(emotion): emotion_engine.set_emotion(emotion)
def update_emotion(): emotion_engine.update_emotion()

def start_emotion_engine():
    bus = get_event_bus()
    if bus:
        bus.subscribe("WAKE_DETECTED", lambda e: set_emotion("alert"))
        bus.subscribe("VOICE_START", lambda e: set_emotion("listening"))
        bus.subscribe("COMMAND_RUN", lambda e: set_emotion("thinking"))
        bus.subscribe("ERROR_EVENT", lambda e: set_emotion("error"))
        bus.subscribe("IDLE_EVENT", lambda e: set_emotion("idle"))
        bus.subscribe("VOICE_END", lambda e: set_emotion("thinking"))
        print("[EMOTION] Emotion engine initialized.", flush=True)

def analyze_text_emotion(text):
    """
    Lightweight semantic emotion classifier.
    Fully asynchronous execution to never block the voice pipeline.
    Emits payload directly over Event Bus.
    """
    import threading
    from core.event_bus import get_event_bus
    import os, requests

    def _fetch_and_emit():
        try:
            from core.ai_router import GROQ_API_KEY
            groq_key = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
            if not groq_key: return

            prompt = (
                "Classify the emotional tone of this sentence into one of the following labels only:\n\n"
                "happy\nsad\nconcerned\nsurprised\nneutral\n\n"
                f"Sentence:\n{text}\n\nReturn only the label."
            )

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                timeout=0.6 
            )
            res.raise_for_status()

            label = res.json()["choices"][0]["message"]["content"].strip().lower()
            valid = ["happy", "sad", "concerned", "surprised", "neutral"]
            emotion = label if label in valid else "neutral"

            print(f"[EMOTION] detected emotion: {emotion}", flush=True)

            bus = get_event_bus()
            if bus:
                bus.publish_sync("EMOTION_UPDATE", "emotion_engine", {"emotion": emotion})

        except Exception as e:
            # Failsafe overrides silently to neutral without disrupting voice
            bus = get_event_bus()
            if bus:
                bus.publish_sync("EMOTION_UPDATE", "emotion_engine", {"emotion": "neutral"})

    t = threading.Thread(target=_fetch_and_emit, daemon=True)
    t.start()
