import os
CLOUD_MODE = os.environ.get("CLOUD_MODE", "false").lower() == "true"

if not CLOUD_MODE:
    import sounddevice as sd  # type: ignore
    import soundfile as sf  # type: ignore
else:
    sd = None
    sf = None

import numpy as np  # type: ignore
import datetime
import time
import io
import subprocess
import shlex
import queue
import threading
import re
# offline recognition (whisper)
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
try:
    from faster_whisper import WhisperModel  # type: ignore
except ImportError:
    pass

from core.config import *  # type: ignore

# Centralized voice synthesis MUST be established before brain_chain binds patched personality!
from core.voice_agent import speak, interrupt, is_speaking, stop_speaker  # type: ignore

from core.brain_chain import brain  # type: ignore
from core.wake_word import detect_wake, activate_voice, start_listener as start_wake_listener, WAKE_WORDS
from core.event_bus import get_event_bus

# Face animation bridge (optional, non-blocking)
try:
    from core.face_bridge import speech_start, speech_stop, listening_start, listening_stop  # type: ignore
    FACE_ANIMATIONS_AVAILABLE = True
except ImportError:
    FACE_ANIMATIONS_AVAILABLE = False
    # Fallback no-op functions
    def speech_start(text=""):
        pass
    def speech_stop():
        pass
    def listening_start():
        pass
    def listening_stop():
        pass

# ros compatibility layer (stub for missing ROS2)
try:
    import rclpy  # type: ignore
    from rclpy.node import Node  # type: ignore
except ImportError:
    # fall back to stub definitions
    try:
        from ros_stub import rclpy, Node
    except ImportError:
        rclpy = None
        Node = object

# -------------------------
# Custom Low Latency Mic (sounddevice)
# -------------------------

class SoundDeviceMic:
    def __init__(self, samplerate=16000, channels=1, vad_threshold=1.5, max_silence_chunks=8):
        self.samplerate = samplerate
        self.channels = channels
        self.vad_threshold = vad_threshold  # Amplitude required to count as "speech"
        self.max_silence_chunks = max_silence_chunks  # Chunks to wait before cutting off phrase
        self.audio_buffer = []
        self.pre_speech_buffer = []    # Keeps rolling buffer of noise to catch start of words !
        self.max_pre_speech_chunks = 10 # Approx 0.6 seconds of history
        self.is_recording = False
        self.silence_chunks = 0
        self.speech_start_time = 0.0
        self.last_speech_time = 0.0
        self.stream = None
        self._callback = None
        self._stream_lock = threading.Lock()
        self.noise_floor = 0.0

    def listen_in_background(self, callback):
        if CLOUD_MODE:
            print("[MIC] Cloud mode active. Microphone disabled.", flush=True)
            return self.stop_listening

        if self.stream is not None and self.stream.active:
            print("[MIC] Stream already running, skipping duplicate start.", flush=True)
            return self.stop_listening

        self._callback = callback
        try:
            # List available input devices for debugging
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            print(f"[MIC] Using default input device index: {default_input}", flush=True)
            if default_input is not None and default_input >= 0:
                dev_info = sd.query_devices(default_input)
                print(f"[MIC] Device: {dev_info['name']} (channels: {dev_info['max_input_channels']})", flush=True)
            
            self.stream = sd.InputStream(
                device=default_input,
                samplerate=16000, 
                channels=1, 
                callback=self._sd_callback,
                dtype='float32',
                blocksize=1024
            )
            with self._stream_lock:
                self.stream.start()  # type: ignore
            print("[MIC] Microphone stream started successfully.", flush=True)
            return self.stop_listening
        except Exception as e:
            print(f"[GENESIS] Microphone error: {e}", flush=True)
            print("[GENESIS] Check: Is a microphone connected? Is it set as default in Windows Sound settings?", flush=True)
            return None

    def stop_listening(self, wait_for_stop=False):
        with self._stream_lock:
            if self.stream is not None:
                self.stream.stop()  # type: ignore
                self.stream.close()  # type: ignore

    def _sd_callback(self, indata, frames, time_info, status):
        import time
        current_time = time.time()
        
        # We sample once per second to avoid flooding the logs
        if not hasattr(self, '_last_diag'): self._last_diag = 0
        if current_time - self._last_diag > 1.0:
            if getattr(self, "diag_active", False):
                print(f"DIAG: MIC callback alive | speak={is_speaking()} proc={is_processing()} | vol={float(np.sqrt(np.mean(indata**2))):.6f}", flush=True)
            self._last_diag = current_time

        # ── GUARD 1: Mute mic while Genesis is speaking (prevent feedback) ──
        if is_speaking():
            if self.is_recording:
                self.is_recording = False
                self.audio_buffer = []
            return

        # ── GUARD 2: Mute mic while brain is processing (prevent garbage) ──
        if is_processing() and not self.is_recording:
            return

        # Calculate amplitude of current chunk
        volume_norm = float(np.sqrt(np.mean(indata**2)))

        # Adaptive noise floor — only updated during confirmed silence
        if not hasattr(self, 'noise_floor') or self.noise_floor == 0.0:
            self.noise_floor = volume_norm

        current_threshold = max(self.vad_threshold, self.noise_floor * 1.5)

        # Print detailed VAD trigger logic
        if volume_norm > current_threshold:
            if getattr(self, "diag_active", False):
                print(f"DIAG: VAD trigger | vol={volume_norm:.6f} > thresh={current_threshold:.6f}", flush=True)
            self.last_speech_time = current_time

            if not self.is_recording:
                print("[MIC] Speech Started", flush=True)
                self.is_recording = True
                self.speech_start_time = current_time
                self.audio_buffer = []

                # restore first syllables
                self.audio_buffer.extend(self.pre_speech_buffer)

                # Dispatch VOICE_START for UI (deferred to avoid blocking audio thread)
                threading.Thread(target=lambda: _safe_publish_event("VOICE_START", "microphone"), daemon=True).start()

            self.audio_buffer.append(indata.copy())
        elif self.is_recording:
            # Still recording — append silence frames to capture full sentence
            self.audio_buffer.append(indata.copy())
        else:
            # Confirmed silence, not recording — safe to adapt noise floor
            self.noise_floor = 0.95 * self.noise_floor + 0.05 * volume_norm

        # ── Silence detection: end recording after 1.0s of silence ──
        silence_duration = current_time - self.last_speech_time

        if self.is_recording and silence_duration > 1.0:
            print("[MIC] Speech End", flush=True)
            if getattr(self, "diag_active", False): 
                print("DIAG: audio buffer finalize", flush=True)

            # Dispatch VOICE_END for UI (deferred to avoid blocking audio thread)
            threading.Thread(target=lambda: _safe_publish_event("VOICE_END", "microphone"), daemon=True).start()

            audio = np.concatenate(self.audio_buffer)

            self.is_recording = False
            self.audio_buffer = []

            if self._callback is not None:
                audio_float32 = audio.flatten().astype(np.float32)
                self._callback(None, audio_float32)

        if not self.is_recording:
            self.pre_speech_buffer.append(indata.copy())
            if len(self.pre_speech_buffer) > self.max_pre_speech_chunks:
                self.pre_speech_buffer.pop(0)


def _safe_publish_event(event_type, source):
    """Thread-safe event publish helper — called from deferred threads to keep audio callback lightweight."""
    try:
        bus = get_event_bus()
        if bus:
            bus.publish_sync(event_type, source)
    except Exception:
        pass

recognizer = SoundDeviceMic(vad_threshold=0.006, max_silence_chunks=40)
mic = "SoundDevice Instance"

# Voice system info (delegated to voice_agent.py)
print("[OK] Voice agent initialized and custom mic ready", flush=True)


# ── State Flag Documentation ──
# conversation_active: True after wake word detection, stays True until stop command.
#                      Controls whether STT results are processed without wake word.
# _processing_active:  True while a command is being processed (brain → router → TTS).
#                      Prevents overlapping command execution. Protected by _processing_lock.
# is_speaking():       True while TTS audio is physically playing. Mutes mic in callback.
#                      Auto-timeouts after 15s safety guard in voice_agent.py.

# Conversation mode variables
conversation_active = False
conversation_timeout = 99999  # Never timeout — always stay active
last_interaction = 0
last_activation = 0
cooldown_time = 3

# Anti-duplicate guards
_processing_lock = threading.Lock()
_processing_active = False
processing_command_since = 0.0  # timestamp when processing started (for safety timeout)

def is_processing():
    with _processing_lock:
        return _processing_active

def acquire_processing():
    global _processing_active, processing_command_since
    with _processing_lock:
        if _processing_active:
            return False
        _processing_active = True
        processing_command_since = time.time()
        return True

def release_processing():
    global _processing_active
    with _processing_lock:
        _processing_active = False

def force_reset_processing(timeout):
    global _processing_active
    with _processing_lock:
        if _processing_active and processing_command_since > 0 and (time.time() - processing_command_since) > timeout:
            _processing_active = False
            return True
        return False

PROCESSING_TIMEOUT = 90.0      # auto-reset if stuck for 90 seconds (phi3 can be slow)
last_command = ""               # Last processed command text
last_command_time = 0           # Time of last processed command
DEDUP_WINDOW = 2.0             # Ignore same command within 2 seconds

# Owner profile
OWNER_NAME = "Avishkar"
OWNER_PRIMARY_ADDRESS = "Sir"
OWNER_ALTERNATE_ADDRESS = "Boss"


# ------------------------------------------------------------------
# Offline speech recognition setup (PRELOAD in background thread)
# ------------------------------------------------------------------
whisper_model = None
_whisper_loaded = False
_whisper_lock = threading.Lock()

def _ensure_whisper():
    """Load Whisper model if not already loaded. Thread-safe."""
    global whisper_model, _whisper_loaded
    with _whisper_lock:
        if _whisper_loaded:
            return
        _whisper_loaded = True
    try:
        print("Loading Whisper model...", flush=True)
        whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Whisper model ready.", flush=True)
    except Exception as e:
        print("Failed to load Whisper model:", e, flush=True)
        whisper_model = None

# Preload Whisper in background immediately on import (zero first-call delay)
_whisper_preload_thread = threading.Thread(target=_ensure_whisper, daemon=True, name="WhisperPreload")
_whisper_preload_thread.start()


def transcribe_audio(audio_array):
    """Return lowercase transcription of numpy Audio array using Whisper."""
    _ensure_whisper()
    if whisper_model is None or audio_array is None:
        return ""
    try:
        segments, info = whisper_model.transcribe(  # type: ignore
            audio_array, 
            beam_size=1, 
            best_of=1,
            temperature=0,
            language="en",
            vad_filter=False,
            without_timestamps=True
        )
        text = " ".join([seg.text for seg in segments])
        return text.lower()
    except Exception as e:
        print("Whisper transcription failed:", e)
        return ""


# -------------------------
# Command Processor
# -------------------------

def is_stop_command(text):
    """Check if command is a stop listening command."""
    stop_phrases = ["stop listening", "go to sleep", "sleep genesis", "sleep", "shutdown", "turn off"]
    return any(phrase in text for phrase in stop_phrases)

STT_CORRECTIONS = {
    "such": "search",
    "youtub": "youtube"
}

def process_command(command):
    """Process voice command sequentially. 
    Mic OFF -> Brain -> Router -> Speak -> Mic ON.
    """
    global conversation_active, last_interaction
    global last_command, last_command_time, processing_command_since

    for wrong, right in STT_CORRECTIONS.items():
        command = command.replace(wrong, right)

    current_time = time.time()

    if command.strip().lower() == last_command.strip().lower() and (current_time - last_command_time) < DEDUP_WINDOW:
        print(f"DEDUP — same command within {DEDUP_WINDOW}s, ignoring", flush=True)
        return True

    try:
        if is_stop_command(command.lower()):
            conversation_active = False
            print("STANDBY MODE SILENT", flush=True)
            if "shutdown" in command.lower() or "turn off" in command.lower():
                 print("[GENESIS] Shutdown requested.", flush=True)
                 return False
            return False

        if not acquire_processing():
            print("BLOCKED — already processing a command, ignoring", flush=True)
            return True

        last_command = command
        last_command_time = current_time

        # MIC OFF during thinking and routing! Very important to pause the buffer completely.
        try:
            with recognizer._stream_lock:
                if recognizer.stream is not None:
                    recognizer.stream.stop()
        except Exception as e:
            print(f"[MIC] stream.stop() error (non-fatal): {e}", flush=True)

        bus = get_event_bus()
        if bus: bus.publish_sync("COMMAND_RUN", "voice_assistant", {"command": command})
        # command run

        # calling brain
        
        def _speak_callback(response_text):
            try:
                if not response_text or not response_text.strip():
                    response_text = "Yes?"
                if response_text != "#STREAMED#":
                    print(f"DIAGNOSTIC (Problem 9): Triggering TTS fallback speech: {repr(response_text)}", flush=True)
                    speak(response_text)
                
                time.sleep(0.5)
                while is_speaking():
                    time.sleep(0.1)
            except Exception as e:
                print(f"[GENESIS] Speak error: {e}", flush=True)
            finally:
                release_processing()
                print("PROCESSING DONE — ready for next command", flush=True)
                print("RETURN TO LISTEN", flush=True)
                if not is_speaking():
                    try:
                        with recognizer._stream_lock:
                            if recognizer.stream is not None:
                                if not recognizer.stream.active:
                                    recognizer.stream.start()
                    except Exception as e:
                        print(f"[MIC] stream.start() error (non-fatal): {e}", flush=True)

        # Execute non-blocking pipeline safely
        def _run_pipeline():
            _cb_lock = threading.Lock()
            _cb_fired = [False]
            def safe_callback(text):
                with _cb_lock:
                    if _cb_fired[0]:
                        return
                    _cb_fired[0] = True
                _speak_callback(text)

            try:
                brain.process_voice_input_async(command, OWNER_PRIMARY_ADDRESS, callback=safe_callback)
            except Exception as e:
                print(f"[GENESIS] Pipeline uncaught error: {e}", flush=True)
                with _cb_lock:
                    if not _cb_fired[0]:
                        _cb_fired[0] = True
                        _speak_callback("Yes?")
            finally:
                try:
                    with _cb_lock:
                        if not _cb_fired[0]:
                            _cb_fired[0] = True
                            _speak_callback("Yes?")
                except Exception:
                    release_processing()
                
        threading.Thread(target=_run_pipeline, daemon=True).start()
        
        last_interaction = time.time()
        return True

    except Exception as e:
        release_processing()
        print(f"[GENESIS] Error processing command '{command}': {e}", flush=True)
        try:
            with recognizer._stream_lock:
                if recognizer.stream is not None:
                    if not recognizer.stream.active:
                        recognizer.stream.start()
        except Exception:
            pass
        last_interaction = time.time()
        return True

# -------------------------
# Asynchronous Voice Processing
# -------------------------
audio_queue = queue.Queue(maxsize=15)

def _audio_callback(recognizer, audio):
    """Puts audio data into a queue for non-blocking processing."""
    if getattr(recognizer, "diag_active", False):
        print("STT TRACE: audio chunk received", flush=True)
        print("DIAG: audio queue push", flush=True)
    if not is_processing():
        try:
            audio_queue.put(audio, block=False)
        except queue.Full:
            pass

# Patterns that Whisper hallucinates on silence / background noise
_GARBAGE_PATTERN = re.compile(
    r'^[\.\,\!\?\s]+$'  # only punctuation / whitespace
)
_NOISE_WORDS = {
    "you", "the", "uh", "um", "ah", "oh", "hmm", "huh",
    "thank you", "thanks", "bye", "okay",
}

def _is_garbage(text: str) -> bool:
    """Return True if text is just noise or a Whisper hallucination."""
    if len(text.strip()) < 2:
        return True
    if _GARBAGE_PATTERN.match(text):
        return True
    if text.strip().lower() in _NOISE_WORDS:
        return True
    return False

_worker_running = True

_worker_thread_ref = None

def _drain_audio_queue():
    """Drain all pending audio from the STT queue to prevent stale fragments."""
    drained = 0
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
            drained += 1
        except queue.Empty:
            break
    if drained:
        print(f"[MIC] Drained {drained} stale audio chunks from queue", flush=True)

def stop_voice():
    global _main_running, _worker_running
    print("[GENESIS] stop_voice() requested.", flush=True)
    _worker_running = False
    _main_running = False
    audio_queue.put(None)
    with recognizer._stream_lock:
        if recognizer.stream is not None:
            try:
                recognizer.stream.stop()
                recognizer.stream.close()
            except Exception as e:
                print(f"[GENESIS] Voice cleanup error: {e}", flush=True)
    # Stop TTS speaker thread
    try:
        stop_speaker()
    except Exception:
        pass
    # Join worker thread for clean shutdown
    if _worker_thread_ref is not None:
        try:
            _worker_thread_ref.join(timeout=3)
        except Exception as e:
            print(f"[GENESIS] Audio queue join error: {e}", flush=True)

def _processing_worker():
    """Processes audio from the queue in a separate thread.
    Full realtime conversation pipeline:
    mic → whisper → transcript → wake/conversation check → router → speak → listen
    """
    global conversation_active, last_interaction, last_activation
    while _worker_running:
        if force_reset_processing(PROCESSING_TIMEOUT):
            print("PROCESS LOCK AUTO RESET", flush=True)

        try:
            try:
                audio = audio_queue.get(timeout=0.5)
            except queue.Empty:
                time.sleep(0.01)
                continue
            
            if audio is None:
                break
            
            # ── Step 1: Transcribe ──
            if getattr(recognizer, "diag_active", False):
                print("DIAG: STT start", flush=True)
            text = transcribe_audio(audio).strip()
            print(f"STT TRACE: transcription result '{text}'", flush=True)
            # transcript ready
            
            # ── Step 2: Filter garbage ──
            garbage_words = ["uh", "um", "oh", "ah", "you", "a", "eh", ""]
            if not text or text.strip().lower() in garbage_words or _is_garbage(text):
                print(f"GARBAGE — IGNORED: '{text}'", flush=True)
                continue

            print(f"\n=== You said: {text} ===", flush=True)
            current_time = time.time()

            # ── Step 3: Guard — already processing ──
            if is_processing():
                # Safety timeout: if stuck for > 60s, force reset
                if force_reset_processing(PROCESSING_TIMEOUT):
                    print(f"TIMEOUT — processing_command stuck for {PROCESSING_TIMEOUT}s, force reset", flush=True)
                else:
                    print("BUSY — still processing previous command, ignoring", flush=True)
                    continue

            # ── Step 4 & 5: Route based on state ── (Timeout intentionally removed)
            is_wake = detect_wake(text) or "genesis" in text.lower()
            if getattr(recognizer, "diag_active", False):
                print(f"STATE | wake={is_wake} active={conversation_active} processing={is_processing()}", flush=True)

            if conversation_active:
                print("CONVERSATION ACTIVE", flush=True)
                # Already in conversation — skip wake check, process directly
                if is_speaking():
                    print("INTERRUPTING current speech for new command", flush=True)
                    interrupt()
                    _drain_audio_queue()  # Issue 9: clear stale STT fragments
                    time.sleep(0.1)

                # Strip wake word if present (user might say "genesis" again)
                cmd = text
                if is_wake:
                    import re
                    for word in WAKE_WORDS:
                        cmd = re.sub(rf"\b{word}\b", "", cmd, flags=re.IGNORECASE).strip()
                    # BUG 4 FIX: Strip punctuation after wake word securely
                    cmd = cmd.rstrip('?!.,;: ').strip()
                    print(f"DIAGNOSTIC: Emotion Engine context -> final command: {cmd}", flush=True)
                    
                    if not cmd or _is_garbage(cmd):
                        speak("Yes sir.")
                        last_interaction = current_time
                        continue

                # FIX — do not execute command twice
                # activate_voice may already dispatch command internally
                if not is_processing():
                    print(f"COMMAND SENT | {cmd}", flush=True) 
                    if not process_command(cmd):
                        conversation_active = False

            elif is_wake:
                print("WAKE WORD DETECTED", flush=True)

                activate_voice(text)

                conversation_active = True
                last_activation = current_time

                speak("Yes sir.")
            else:
                # No wake word, no conversation
                print(f"NO WAKE WORD — IGNORED. Say 'Genesis' first.", flush=True)

        except Exception as e:
            release_processing()  # Reset on error
            print(f"WORKER ERROR: {e}", flush=True)

_main_running = False

def main():
    """Main entry point for the voice assistant."""
    global conversation_active, last_interaction, last_activation, _main_running
    if _main_running:
         print("[GENESIS] main() already running, ignoring duplicate start.", flush=True)
         return
    _main_running = True
    
    print("Genesis AI is starting...", flush=True)

    if mic is None:
        print("[GENESIS] ERROR: No microphone available. Voice input disabled.", flush=True)
        print("[GENESIS] System will run but cannot accept voice commands.", flush=True)
        # Keep thread alive so system doesn't crash
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nGenesis stopped.", flush=True)
        return
    
    # Start the background processing worker
    global _worker_thread_ref
    worker_thread = threading.Thread(target=_processing_worker, daemon=True)
    worker_thread.start()
    _worker_thread_ref = worker_thread

    print("LISTEN LOOP STARTED", flush=True)
    
    # Start mic FIRST — with unified sounddevice backend, mic and speaker coexist safely
    # phrase_time_limit is not needed natively anymore, handled by Max Silence Chunks
    stop_listening = recognizer.listen_in_background(_audio_callback)
    start_wake_listener()

    # Queue startup greeting AFTER mic is ready (speaker thread uses sd.play which is PortAudio-safe)
    speak("Genesis online.")

    try:
        loop_count = 0
        while True:
            time.sleep(0.1)
            loop_count += 1
            if loop_count >= 150:
                loop_count = 0
    except KeyboardInterrupt:
        print("\nShutting down Genesis...")
        audio_queue.put(None)  # Signal the worker thread to exit
        if stop_listening:
            stop_listening(wait_for_stop=False)
        worker_thread.join()  # Wait for the worker to finish
        print("Genesis stopped.", flush=True)

if __name__ == "__main__":
    main()
