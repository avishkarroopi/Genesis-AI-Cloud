import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'core'))

from core.event_bus import get_event_bus
from core.tools.init_tools import init_all_tools
from core.agents.init_agents import init_all_agents
from core.brain_chain import brain
from server.session_manager import generate_session_context

async def run_full_sim():
    print("[SIM] Booting Full System Simulation...")
    bus = get_event_bus()
    await bus.start()
    
    init_all_tools()
    init_all_agents()
    
    context = generate_session_context("sim_user")
    
    visemes = []
    has_tts = False
    
    async def on_viseme(event):
        visemes.append(event.data)
        print(f"[SIM] Viseme received over EventBus: {event.data}")
    
    async def on_tts(event):
        nonlocal has_tts
        has_tts = True
        print(f"[SIM] TTS Audio Binary received over EventBus: {len(event.data)} bytes")
        
    bus.subscribe("VISEME_EVENT", on_viseme)
    bus.subscribe("TTS_AUDIO", on_tts)
    
    print("[SIM] Simulating user speech output from STT...")
    print("[SIM] Transcript: \"Genesis, explain quantum computing\"")
    
    def _cb(res):
        pass
        
    # We await the main logic
    result = brain.process_voice_input_async(context, "Genesis, explain quantum computing", callback=_cb)
    print(f"[SIM] AI generated text response: {result}")
    
    # Wait for background TTS thread to pick up the response, generate WAV, emit TTS_AUDIO, and emit VISEME_EVENTs
    print("[SIM] Waiting 5 seconds for background TTS compilation and Rhubarb processing...")
    await asyncio.sleep(5)
    
    print("\n[SIM] === SIMULATION RESULTS ===")
    print(f"AI Reasoning Engine Generation: {'PASS' if result else 'FAIL'}")
    print(f"TTS Engine Output Stream: {'PASS' if has_tts else 'FAIL'}")
    print(f"Avatar Lip Sync Visemes: {'PASS' if len(visemes) > 0 else 'FAIL'} ({len(visemes)} visemes compiled)")
    
    await bus.stop()

if __name__ == "__main__":
    asyncio.run(run_full_sim())
