from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import asyncio
from typing import List
from .auth import verify_firebase_token
from .session_manager import generate_session_context
from .voice_pipeline_adapter import process_audio_chunk

router = APIRouter()

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


manager = ConnectionManager()

# Hook into the event bus to listen for Avatar messages
def _init_avatar_bridge():
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        
        async def on_avatar_event(event):
            # Broadcast the event payload to all connected clients
            payload = json.dumps(event.data)
            await manager.broadcast(payload)
            
        if bus:
            bus.subscribe("AVATAR_EVENT", on_avatar_event)
    except Exception:
        pass

_init_avatar_bridge()


@router.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for browser audio streaming and avatar sync.

    Authentication:
        Pass a valid Firebase ID token as the `token` query param:
        ws://host/ws/voice?token=<firebase_jwt>
        Connections without a valid token are rejected with close code 4001.
    """
    # ── Auth Gate ────────────────────────────────────────────────────────
    import os
    token = websocket.query_params.get("token", "")
    user_id = "anonymous"

    if os.environ.get("DEV_BYPASS_AUTH") == "true" and token in ("", "test_token"):
        # Development bypass only — never active in production
        user_id = "test_dev_user"
    else:
        try:
            import firebase_admin
            from firebase_admin import auth as fb_auth
            if not token:
                raise ValueError("No token provided")
            decoded = fb_auth.verify_id_token(token)
            user_id = decoded.get("uid", "unknown")
        except Exception:
            # Reject BEFORE accepting the WebSocket so no data is exchanged
            await websocket.close(code=4001)
            return

    await manager.connect(websocket)
    session_context = generate_session_context(user_id)

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message:
                response = await process_audio_chunk(message["bytes"], session_context)
                if response:
                    await websocket.send_text(response)
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

