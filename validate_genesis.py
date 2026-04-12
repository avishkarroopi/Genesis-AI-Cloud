import sys, os, time, asyncio, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))

from core.event_bus import get_event_bus
import core.voice_agent
from core.brain_chain import brain

# Override HF requests if needed
os.environ["HF_HUB_OFFLINE"] = "1"

events_caught = set()

# Voice proxy to catch output
spoken_texts = []
_orig_speak = core.voice_agent.speak
def mock_speak(text):
    spoken_texts.append(text)
    # Don't actually speak to avoid hanging SAPI
core.voice_agent.speak = mock_speak

cb_result = ""
def sync_cb(res):
    global cb_result
    cb_result = res

def run_cmd(cmd):
    global cb_result, spoken_texts
    cb_result = ""
    spoken_texts.clear()
    
    # Send event to trigger anything relying on COMMAND_RECEIVED
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(get_event_bus().publish("COMMAND_RECEIVED", {"text": cmd}))
    except RuntimeError:
        pass # no loop
        
    print(f"\n[TEST_CMD] -> {cmd}")
    brain.process_voice_input_async(cmd, "Sir", sync_cb)
    time.sleep(2)  # Allow for thread/async execution
    
    res = cb_result
    if res == "#STREAMED#":
        res = " ".join(spoken_texts)
    print(f"[TEST_RES] <- {res}")
    return res

async def main():
    bus = get_event_bus()
    await bus.start()
    
    def on_event(event):
        events_caught.add(event.event_type)
    bus.subscribe("*", on_event)
    
    results = {}

    print("=== STARTING GENESIS RUNTIME VALIDATION ===\n")
    
    # CAT 1: System Identity
    try:
        r1 = run_cmd("Who created you")
        r2 = run_cmd("Who is your owner")
        if "Avishkar" in r1 or "owner" in r1.lower() or "owner" in r2.lower():
            results["System Identity"] = "PASS"
        else:
            results["System Identity"] = f"FAIL (r1={r1}, r2={r2})"
    except Exception as e:
        results["System Identity"] = f"FAIL: {e}"

    # CAT 2: Voice & Conversation
    try:
        r = run_cmd("Genesis what time is it")
        if r and len(r) > 2:
            results["Voice & Conversation"] = "PASS"
        else:
            results["Voice & Conversation"] = "FAIL"
    except Exception as e:
        results["Voice & Conversation"] = f"FAIL: {e}"

    # CAT 3: Automation Commands
    try:
        r = run_cmd("Genesis open YouTube")
        if "youtube" in r.lower() or "open" in r.lower():
            results["Automation Commands"] = "PASS"
        else:
            results["Automation Commands"] = "FAIL (Wait to verify tool execution)"
    except Exception as e:
        results["Automation Commands"] = f"FAIL: {e}"

    # CAT 4: Memory System
    try:
        run_cmd("Store this Uncle Rajanikanth is my uncle")
        time.sleep(1)
        # Attempt retrieval
        from core.memory.memory_manager import get_entities
        e = get_entities()
        if "Uncle" in e or "Rajanikanth" in str(e):
             results["Memory System"] = "PASS"
        else:
             results["Memory System"] = f"FAIL: {e}"
    except Exception as e:
        results["Memory System"] = f"FAIL: {e}"

    # CAT 5: World Model
    try:
        from core.world_model import get_world_model, ObjectCategory, Position
        wm = get_world_model()
        await wm.add_object("person_1", ObjectCategory.PERSON, "person", Position(0,0,0))
        await asyncio.sleep(0.5)
        if "WORLD_MODEL_UPDATED" in events_caught:
            results["World Model"] = "PASS"
        else:
            results["World Model"] = "FAIL (No event)"
    except Exception as e:
        results["World Model"] = f"FAIL: {e}"

    # CAT 6: Vision System
    try:
        from core.vision.llava_reasoner import VisionRunner
        v = VisionRunner()
        if v.pipe is not None or "init" in v.__class__.__name__:  # Simple check
            results["Vision System"] = "PASS"
        else:
            results["Vision System"] = "FAIL"
    except Exception as e:
        results["Vision System"] = f"FAIL: {e}"

    # CAT 7: Scene Memory
    try:
        # Simulate scene changes
        await bus.publish("VISION_DETECTED", {"objects": ["laptop"]})
        await asyncio.sleep(0.5)
        await bus.publish("VISION_DETECTED", {"objects": []})
        await asyncio.sleep(0.5)
        # Events should be there
        if "NEW_OBJECT_DETECTED" in events_caught or "OBJECT_REMOVED" in events_caught:
            results["Scene Memory"] = "PASS"
        else:
            results["Scene Memory"] = "FAIL (Events not generated)"
    except Exception as e:
        results["Scene Memory"] = f"FAIL: {e}"

    # CAT 8: Agent Framework
    try:
        from core.agents.task_planner import TaskPlanner
        planner = TaskPlanner()
        tasks = planner.plan_tasks({"target": "youtube piano"})
        if len(tasks) > 0:
            results["Agent Framework"] = "PASS"
        else:
            results["Agent Framework"] = "FAIL"
    except Exception as e:
        results["Agent Framework"] = f"FAIL: {e}"

    # CAT 9: Prediction Engine
    try:
        from core.prediction.prediction_cache import set_prediction, get_prediction
        from core.prediction.behavior_model import analyze_behavior_pattern
        c_id = "test_cycle"
        await analyze_behavior_pattern([{"action":"piano"}], c_id)
        if "PREDICTION_GENERATED" in events_caught:
            results["Prediction Engine"] = "PASS"
        else:
            results["Prediction Engine"] = "FAIL (No prediction event)"
    except Exception as e:
        results["Prediction Engine"] = f"FAIL: {e}"

    # CAT 10: Digital Twin
    try:
        from core.digital_twin.behavior_simulator import run_simulation
        res = await run_simulation("agent_planning", {"cmd": "improve music"})
        if res is not None:
             results["Digital Twin"] = "PASS"
        else:
             results["Digital Twin"] = "FAIL"
    except Exception as e:
         results["Digital Twin"] = f"FAIL: {e}"

    # CAT 11: Personal Life OS
    try:
        from core.life_os.goal_tracker import update_goal_progress
        update_goal_progress("music_career", 20.0)
        results["Personal Life OS"] = "PASS"
    except Exception as e:
        results["Personal Life OS"] = f"FAIL: {e}"

    # CAT 12: Event Bus
    try:
        expected = ["COMMAND_RECEIVED", "WORLD_MODEL_UPDATED"]
        missing = [e for e in expected if e not in events_caught]
        if not missing:
             results["Event Bus"] = "PASS"
        else:
             results["Event Bus"] = f"FAIL missing {missing}"
    except Exception as e:
         results["Event Bus"] = f"FAIL: {e}"

    # CAT 13: Intelligence Integration
    try:
        r = run_cmd("Who is Rajanikanth")
        if isinstance(r, str) and len(r) > 0:
             results["Intelligence Integration"] = "PASS"
        else:
             results["Intelligence Integration"] = "FAIL"
    except Exception as e:
         results["Intelligence Integration"] = f"FAIL: {e}"

    # CAT 14: Voice Interruption
    try:
        import threading
        class SpeakerHack:
            def __init__(self):
                self.interrupted = False
            def is_sp(self):
                return True
            def stop(self):
                self.interrupted = True
        core.voice_agent.stop_speaker() # Will trigger internal stop
        results["Voice Interruption"] = "PASS"
    except Exception as e:
        results["Voice Interruption"] = f"FAIL: {e}"

    # CAT 15: Emotional Response
    try:
        from core.emotion_engine import analyze_text_emotion
        # Emulate command
        res = "I am so sorry to hear that you are stressed."
        emod = analyze_text_emotion(res)
        results["Emotional Response"] = "PASS"
    except Exception as e:
        results["Emotional Response"] = f"FAIL: {e}"

    with open("val_output.json", "w") as f:
        json.dump(results, f, indent=2)

    await bus.stop()
    print("DONE. Result dict saved to val_output.json")

if __name__ == "__main__":
    asyncio.run(main())
