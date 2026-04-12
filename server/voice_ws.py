from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from .auth import verify_firebase_token
from .session_manager import generate_session_context
from .voice_pipeline_adapter import process_audio_chunk

router = APIRouter()

@router.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for browser audio streaming."""
    await websocket.accept()

    user_id = websocket.query_params.get("user_id", "anonymous")
    session_context = generate_session_context(user_id)

    try:
        while True:
            data = await websocket.receive_bytes()
            response = await process_audio_chunk(data, session_context)
            if response:
                await websocket.send_text(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(f'{{"error": "{str(e)}"}}')
            await websocket.close()
        except Exception:
            pass
