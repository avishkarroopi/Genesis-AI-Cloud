from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import asyncio
from typing import List
from .auth import verify_firebase_token
from .session_manager import generate_session_context
from .voice_pipeline_adapter import process_audio_chunk

router = APIRouter()

is_speaking_flag = False

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except RuntimeError:
                # Connection dropped
                self.disconnect(connection)
            except Exception:
                pass

    async def broadcast_bytes(self, data: bytes):
        for connection in list(self.active_connections):
            try:
                await connection.send_bytes(data)
            except RuntimeError:
                # Connection dropped
                self.disconnect(connection)
            except Exception:
                pass


manager = ConnectionManager()

# Hook into the event bus to listen for Avatar messages
def _init_avatar_bridge():
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        
        async def on_avatar_event(event):
            global is_speaking_flag
            try:
                data = event.data
                if isinstance(data, dict):
                    # Echo Protection: Sync speaking state
                    state = data.get("state")
                    evt_type = data.get("type", data.get("event"))
                    if state == "SPEAKING" or evt_type == "speech_start":
                        is_speaking_flag = True
                    elif state == "IDLE" or evt_type == "speech_stop":
                        is_speaking_flag = False
            except Exception:
                pass
            
            # Broadcast the event payload to all connected clients
            payload = json.dumps(event.data)
            await manager.broadcast(payload)
            
        async def on_audio_event(event):
            global is_speaking_flag
            is_speaking_flag = True
            # Broadcast the TTS binary directly
            await manager.broadcast_bytes(event.data)
            
        if bus:
            bus.subscribe("AVATAR_EVENT", on_avatar_event)
            bus.subscribe("sys_stats", on_avatar_event)
            bus.subscribe("VISEME_EVENT", on_avatar_event)
            bus.subscribe("TTS_AUDIO", on_audio_event)
    except Exception:
        pass

_init_avatar_bridge()

# Opus VBR: Chunks of silence are roughly < 300 bytes. Chunks of speech typically > 1000 bytes.
VAD_SIZE_THRESHOLD = 500  
MAX_SILENCE_CHUNKS = 1    # Since mic_capture.js sends 1 chunk per 2s, 1 silent chunk = 2s silence.

@router.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for browser audio streaming and avatar sync."""
    user_id = "anonymous"

    await manager.connect(websocket)
    session_context = generate_session_context(user_id)

    audio_buffer = b""
    is_recording = False
    silence_chunks = 0

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                global is_speaking_flag
                if is_speaking_flag:
                    # Drop incoming audio entirely if GENESIS is speaking (Echo Protection)
                    continue
                
                chunk = message["bytes"]
                
                # Perform VAD using WebM Opus VBR payload size heuristic
                if len(chunk) > VAD_SIZE_THRESHOLD:
                    is_recording = True
                    silence_chunks = 0
                    audio_buffer += chunk
                else:
                    if is_recording:
                        audio_buffer += chunk
                        silence_chunks += 1
                        
                        if silence_chunks >= MAX_SILENCE_CHUNKS:
                            # Speech end detected -> Process accumulated audio
                            try:
                                response = await process_audio_chunk(audio_buffer, session_context)
                                if response:
                                    await websocket.send_text(response)
                            except Exception as pipeline_err:
                                import logging
                                logging.error(f"Voice pipeline error: {pipeline_err}")
                            finally:
                                # Reset VAD safely
                                audio_buffer = b""
                                is_recording = False
                                silence_chunks = 0

            elif "text" in message:
                try:
                    payload = json.loads(message["text"])
                    if payload.get("type") == "VISION_EVENT":
                        try:
                            from core.event_bus import get_event_bus
                            import asyncio
                            bus = get_event_bus()
                            if bus:
                                asyncio.create_task(bus.publish("VISION_EVENT", "frontend_camera", payload))
                        except Exception:
                            pass
                except Exception:
                    pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        try:
            await websocket.send_text(f'{{"error": "{str(e)}"}}')
            await websocket.close()
        except Exception:
            pass
