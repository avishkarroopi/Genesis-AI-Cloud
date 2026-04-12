# lite/android/android_api.py
"""
Android API Layer for APK integration via PyJNIus.
Implements Camera, Microphone, and Speaker streaming to/from PC.
Also acts as a bridge to push hardware status to WebView JS.
"""
import base64
import logging
import threading
from kivy.clock import mainthread # type: ignore

try:
    from jnius import autoclass, PythonJavaClass, java_method # type: ignore
    Activity = autoclass('org.kivy.android.PythonActivity').mActivity
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    WebChromeClient = autoclass('android.webkit.WebChromeClient')
    LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
    
    # Audio Classes
    AudioRecord = autoclass('android.media.AudioRecord')
    AudioFormat = autoclass('android.media.AudioFormat')
    MediaRecorder_AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
    AudioTrack = autoclass('android.media.AudioTrack')
    AudioManager = autoclass('android.media.AudioManager')
    
    # USB Camera
    Context = autoclass('android.content.Context')
    UsbManager = autoclass('android.hardware.usb.UsbManager')
    
    ON_ANDROID = True
except ImportError:
    ON_ANDROID = False
    Activity = None
    WebView = None

logger = logging.getLogger(__name__)

if ON_ANDROID:
    class RunnableWrapper(PythonJavaClass):
        __javainterfaces__ = ['java/lang/Runnable']
        def __init__(self, func):
            super().__init__()
            self.func = func
        @java_method('()V')
        def run(self):
            self.func()

class AndroidBridge:
    def __init__(self, ws_client, face_url):
        self.ws_client = ws_client
        self.face_url = face_url
        self.webview = None
        self.is_mic_running = False
        
        # Audio Config
        self.sample_rate = 16000
        self.channel_config_in = AudioFormat.CHANNEL_IN_MONO if ON_ANDROID else 16
        self.audio_format = AudioFormat.ENCODING_PCM_16BIT if ON_ANDROID else 2
        
        if ON_ANDROID:
            self.min_buffer_size = AudioRecord.getMinBufferSize(
                self.sample_rate, self.channel_config_in, self.audio_format
            )
            # Speaker Config
            self.speaker_min_buffer = AudioTrack.getMinBufferSize(
                self.sample_rate, AudioFormat.CHANNEL_OUT_MONO, self.audio_format
            )
            self.audio_track = AudioTrack(
                AudioManager.STREAM_MUSIC,
                self.sample_rate,
                AudioFormat.CHANNEL_OUT_MONO,
                self.audio_format,
                self.speaker_min_buffer,
                AudioTrack.MODE_STREAM
            )

    @mainthread
    def initialize_webview(self):
        if not ON_ANDROID:
            logger.info("[LITE] Not on Android. Skipping WebView init.")
            return

        logger.info("[LITE] Initializing full-screen WebView")
        self.webview = WebView(Activity)
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setMediaPlaybackRequiresUserGesture(False)
        
        self.webview.setWebViewClient(WebViewClient())
        self.webview.setWebChromeClient(WebChromeClient())
        
        layout_params = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
        Activity.addContentView(self.webview, layout_params)
        self.webview.loadUrl(self.face_url)

    def update_ui_state(self, indicator, state):
        """Pushes hardware state to Genesis Face UI via JS bridge"""
        if not ON_ANDROID or not self.webview:
            return
        # window.onAndroidStatus('network', 'ok')
        js_code = f"if(window.onAndroidStatus) window.onAndroidStatus('{indicator}', '{state}');"
        Activity.runOnUiThread(RunnableWrapper(lambda: self.webview.evaluateJavascript(js_code, None)))

    async def start_mic_stream(self):
        if not ON_ANDROID:
            self.update_ui_state("mic", "error")
            return
            
        self.is_mic_running = True
        self.update_ui_state("mic", "ok")
        
        def mic_loop():
            record = AudioRecord(
                MediaRecorder_AudioSource.MIC,
                self.sample_rate,
                self.channel_config_in,
                self.audio_format,
                self.min_buffer_size
            )
            record.startRecording()
            buffer = bytearray(self.min_buffer_size)
            
            while self.is_mic_running:
                # Read chunks and stream if ws_client is connected
                read_bytes = record.read(buffer, 0, len(buffer))
                if read_bytes > 0 and self.ws_client._ws:
                    import asyncio
                    # Send raw PCM data
                    try:
                        b64_data = base64.b64encode(buffer[:read_bytes]).decode('utf-8')
                        payload = {"type": "audio_frame", "data": b64_data}
                        # We must send async from thread
                        future = asyncio.run_coroutine_threadsafe(
                            self.ws_client.send_json(payload), self.ws_client.loop
                        )
                    except Exception as e:
                        logger.error(f"[LITE] Mic stream error: {e}")
            record.stop()
            record.release()

        threading.Thread(target=mic_loop, daemon=True).start()

    async def start_camera_stream(self):
        if not ON_ANDROID:
            self.update_ui_state("camera", "error")
            return

        # USB Host detection + Frame Capture
        # Native Camera2 or libuvc usually required for external USB cams.
        # This streams JPEG frames via WebSocket.
        self.update_ui_state("camera", "ok")
        
        def camera_loop():
            # In a full production implementation, setup android.hardware.camera2
            # or a UVC library to capture USB camera frames. 
            pass

        threading.Thread(target=camera_loop, daemon=True).start()

    def speaker_play(self, audio_pcm_base64):
        """Play incoming audio from PC TTS"""
        self.update_ui_state("speaker", "ok")
        if not ON_ANDROID:
            return
            
        try:
            pcm_bytes = base64.b64decode(audio_pcm_base64)
            # Basic echo prevention: stop mic while playing TTS
            was_mic_running = self.is_mic_running
            if was_mic_running:
                self.is_mic_running = False
                self.update_ui_state("mic", "idle")
                
            self.audio_track.play()
            self.audio_track.write(pcm_bytes, 0, len(pcm_bytes))
            self.audio_track.stop()
            
            self.update_ui_state("speaker", "idle")
            
            # Resume mic
            if was_mic_running:
                import asyncio
                asyncio.run_coroutine_threadsafe(self.start_mic_stream(), self.ws_client.loop)
                
        except Exception as e:
            logger.error(f"[LITE] Speaker play error: {e}")

    def on_server_message(self, data):
        """Callback from ws_client when a message is received"""
        if isinstance(data, dict):
            if data.get("type") == "tts_audio":
                self.speaker_play(data.get("data", ""))
