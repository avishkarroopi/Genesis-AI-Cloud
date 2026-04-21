import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.brain_chain import brain
import asyncio

def run_test():
    class SessionCtx:
        user_id = "test_user_777"
        
    ctx = SessionCtx()
    print("Testing Memory Write...")
    
    # 1. Ask to remember
    def cb1(resp):
        print(f"GENESIS (Write): {resp}")
        
    brain.process_voice_input_async(ctx, "store this Secret my_secret_code is 492021", callback=cb1)
    
    import time
    time.sleep(1)
    
    # 2. Ask to recall the explicit entity
    print("\nTesting Memory Recall (Entity)...")
    def cb2(resp):
        print(f"GENESIS (Recall Entity): {resp}")
    brain.process_voice_input_async(ctx, "What is my_secret_code?", callback=cb2)
    
    time.sleep(1)

    # 3. Vector memory storage
    print("\nTesting Memory Write (Vector)...")
    def cb3(resp):
        print(f"GENESIS (Write Vector): {resp}")
    brain.process_voice_input_async(ctx, "Please remember that my favorite color is crimson red.", callback=cb3)

    time.sleep(2)
    
    # 4. Vector memory recall
    print("\nTesting Memory Recall (Vector)...")
    def cb4(resp):
        print(f"GENESIS (Recall Vector): {resp}")
    brain.process_voice_input_async(ctx, "What is my favorite color?", callback=cb4)
    time.sleep(2)

if __name__ == "__main__":
    run_test()
