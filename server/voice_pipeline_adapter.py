import os
import json
import base64
import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

async def call_stt_api(audio_bytes: bytes) -> str:
    """Send audio bytes to the cloud STT API and return transcript."""
    stt_key = os.environ.get("STT_API_KEY", "")
    if not stt_key:
        logger.warning("STT_API_KEY not configured — returning empty transcript")
        return ""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {stt_key}"},
                files={"file": ("audio.webm", audio_bytes, "audio/webm")},
                data={"model": "whisper-large-v3"}
            )
            return response.json().get("text", "")
    except Exception as e:
        logger.error(f"STT API error: {e}")
        return ""

def _invoke_genesis_core(session_context, transcript: str) -> str:
    """Call GENESIS brain synchronously — safe to run inside run_in_threadpool."""
    try:
        from core.brain_chain import brain
        result_holder = []

        def callback(response):
            result_holder.append(response)

        brain.process_voice_input_async(session_context, transcript, callback=callback)
        return result_holder[0] if result_holder else "I'm processing that."
    except Exception as e:
        logger.error(f"Core invocation error: {e}")
        return "Error during processing."

async def process_audio_chunk(audio_bytes: bytes, session_context) -> str:
    """Full voice pipeline: audio bytes → STT → GENESIS core → response text."""
    transcript = await call_stt_api(audio_bytes)
    if not transcript or not transcript.strip():
        return ""

    response_text = await run_in_threadpool(_invoke_genesis_core, session_context, transcript)
    return json.dumps({"transcript": transcript, "response": response_text})
