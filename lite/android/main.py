# lite/android/main.py
"""
GENESIS Lite — Android Wrapper (WebView + Hardware Native Bridge)
Loads the GENESIS Face UI in a full-screen native Android WebView via PyJNIus.
Hooks into Android USB Camera and Microphone to stream to the PC.
"""

from kivy.app import App
from kivy.clock import Clock
import asyncio
import threading
from lite.client.ws_client import WSClient
from lite.android.android_api import AndroidBridge

class GenesisLiteApp(App):
    def build(self):
        # The Face UI runs at port 8000 on the PC (or another static IP configured by user)
        # Using a fixed IP for the PC brain as previously assumed
        self.host = "192.168.1.100"
        self.face_url = f"http://{self.host}:8000/" 

        self.ws_client = WSClient(host=self.host, port=8080, token="")
        self.bridge = AndroidBridge(self.ws_client, self.face_url)

        # Connect WebSocket in background
        threading.Thread(target=self._run_async_tasks, daemon=True).start()

        # Build method returns None or empty layout because we will use native WebView filling the screen
        from kivy.uix.widget import Widget
        return Widget()

    def on_start(self):
        # Called when Kivy is fully started. Initialize native WebView.
        self.bridge.initialize_webview()

    def _run_async_tasks(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def main_loop():
            if await self.ws_client.connect():
                self.bridge.update_ui_state("network", "ok")
                # Start hardware streams
                await self.bridge.start_mic_stream()
                await self.bridge.start_camera_stream()
                
                await self.ws_client.listen(callback=self.bridge.on_server_message)
        
        loop.run_until_complete(main_loop())

if __name__ == "__main__":
    GenesisLiteApp().run()
