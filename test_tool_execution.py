import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.brain_chain import brain
from core.ai_router import route_ai_request

def run_test():
    class SessionCtx:
        user_id = "test_user"
    
    ctx = SessionCtx()
    print("Testing Generic System Information (Tool Execution)...")
    
    def cb1(resp):
        print(f"GENESIS Resp: {resp}")
        
    print("\n[REQUEST] what is the current date?")
    brain.process_voice_input_async(ctx, "what is the current date and time right now?", callback=cb1)
    
if __name__ == "__main__":
    run_test()
