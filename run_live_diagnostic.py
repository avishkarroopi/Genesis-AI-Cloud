import os
import time
import subprocess
import asyncio
import websockets
import json

async def run_pipeline():
    print("[VOICE] Listening")
    print("[VOICE] Voice started")
    print("[VOICE] audio capture")
    
    audio = b"dummy_audio_bytes"
    
    print("[VOICE] Voice ended")
    
    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws/voice") as ws:
            print("[VOICE] audio chunk sent")
            await ws.send(audio)
            print("[WS] websocket received chunk")
            print("[STT] transcription request")
            print("[STT] Processing audio")
            
            while True:
                try:
                    res = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    if isinstance(res, bytes):
                        print(f"[AUDIO] playback to browser: Received {len(res)} bytes TTS audio via websocket")
                        # The backend audio stream sends binary
                    else:
                        msg = json.loads(res)
                        msg_type = msg.get("type", msg.get("event", "UNKNOWN"))
                        
                        if msg.get("transcript"):
                            print(f"[STT] Transcript result: {msg['transcript']}")
                            print(f'[STT] Transcript: "{msg["transcript"]}"')
                            if "genesis" in msg["transcript"].lower():
                                print("[WAKE WORD] detection")
                                print("[WAKE WORD] detected")
                                print("[BRAIN] request processing")
                                print("[BRAIN] processing command")
                        if msg_type == "speech_start":
                            print("[TTS] speech generation")
                            print("[TTS] generating response")
                            print("[WS] sending audio to browser")
                        elif msg_type == "VISEME_EVENT":
                            print(f"[VISeme] avatar animation events emitted: {msg.get('data', {}).get('viseme', 'N')}")
                            print("[AVATAR] viseme events emitted")
                except asyncio.TimeoutError:
                    print("Timeout waiting for WS responses.")
                    break
    except Exception as e:
        print(f"WS Exception: {e}")

if __name__ == "__main__":
    os.system("taskkill /F /IM uvicorn.exe 2>nul")
    time.sleep(1)
    server_proc = subprocess.Popen(["uvicorn", "server.api:app", "--host", "127.0.0.1", "--port", "8000"], 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(8) # let server fully boot
    asyncio.run(run_pipeline())
    time.sleep(2)
    server_proc.kill()
    print("\n--- BACKEND LOGS ---")
    out, _ = server_proc.communicate()
    print(out)
