# lite/client/ws_client.py
"""WebSocket client to connect to GENESIS Core with auth and reconnection."""
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False


class WSClient:
    def __init__(self, host="127.0.0.1", port=8080, token=""):
        self.uri = f"ws://{host}:{port}/ws"
        self.token = token
        self._ws = None
        self._session = None
        self._connected = False
        self._running = False
        self._response_callback = None
        self._reconnect_delay = 2
        self.loop = None

    async def connect(self):
        """Connect to GENESIS Core WebSocket with auth handshake."""
        self.loop = asyncio.get_running_loop()
        if not AIOHTTP_AVAILABLE:
            logger.error("[LITE] aiohttp not installed. Cannot connect.")
            return False

        try:
            self._session = aiohttp.ClientSession()
            self._ws = await self._session.ws_connect(self.uri)
            logger.info(f"[LITE] Connected to {self.uri}")

            # Auth handshake
            if self.token:
                await self._ws.send_str(json.dumps({"type": "auth", "token": self.token}))
                auth_resp = await self._ws.receive()
                if auth_resp.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(auth_resp.data)
                    if data.get("status") != "ok":
                        logger.error("[LITE] Auth failed")
                        await self.disconnect()
                        return False
                logger.info("[LITE] Auth successful")

            self._connected = True
            return True
        except Exception as e:
            logger.error(f"[LITE] Connect failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Core."""
        self._connected = False
        self._running = False
        try:
            if self._ws:
                await self._ws.close()
            if self._session:
                await self._session.close()
        except Exception as e:
            logger.warning(f"[LITE] Disconnect error: {e}")

    async def send_command(self, text):
        """Send a command to GENESIS Core."""
        if not self._connected or not self._ws:
            logger.warning("[LITE] Not connected. Cannot send command.")
            return False
        try:
            msg = json.dumps({"type": "command", "text": text})
            await self._ws.send_str(msg)
            logger.info(f"[LITE] Sent command: {text[:60]}")
            return True
        except Exception as e:
            logger.error(f"[LITE] Send failed: {e}")
            self._connected = False
            return False

    async def send_json(self, payload):
        """Send arbitrary JSON payload (e.g. frames/audio) to Core."""
        if not self._connected or not self._ws:
            logger.warning("[LITE] Not connected. Cannot send json.")
            return False
        try:
            await self._ws.send_str(json.dumps(payload))
            return True
        except Exception as e:
            logger.error(f"[LITE] Send JSON failed: {e}")
            self._connected = False
            return False

    async def listen(self, callback=None):
        """Listen for responses from Core."""
        self._running = True
        self._response_callback = callback
        while self._running:
            try:
                if not self._connected:
                    logger.info(f"[LITE] Reconnecting in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    if await self.connect():
                        continue
                    else:
                        continue

                msg = await self._ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if self._response_callback:
                        self._response_callback(data)
                    else:
                        logger.info(f"[LITE] Received: {data}")
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    logger.warning("[LITE] Connection lost")
                    self._connected = False
            except Exception as e:
                logger.error(f"[LITE] Listen error: {e}")
                self._connected = False
                await asyncio.sleep(self._reconnect_delay)
