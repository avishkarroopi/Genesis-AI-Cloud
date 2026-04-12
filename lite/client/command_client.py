# lite/client/command_client.py
"""Client for sending commands and receiving responses from GENESIS Core."""
import asyncio
import logging
from lite.client.ws_client import WSClient

logger = logging.getLogger(__name__)


async def send_command(text, host="127.0.0.1", port=8080, token=""):
    """One-shot: connect, send command, wait for response, disconnect."""
    client = WSClient(host=host, port=port, token=token)
    if not await client.connect():
        return None

    await client.send_command(text)

    # Wait for single response
    try:
        msg = await asyncio.wait_for(client._ws.receive(), timeout=30)
        import aiohttp, json
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            await client.disconnect()
            return data.get("text", str(data))
    except Exception as e:
        logger.error(f"[LITE] Response timeout: {e}")

    await client.disconnect()
    return None


def receive_response():
    """Placeholder for synchronous response polling."""
    pass
