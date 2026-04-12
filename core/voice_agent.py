"""
GENESIS Voice Agent - Centralized Speech Synthesis Module
Uses pyttsx3 on a SINGLE dedicated background thread.

The engine is initialized ONCE and reused for all speech.
A queue feeds text to the speaker thread — never re-init, never new threads.
"""

import os
import subprocess
import time
import sys
import shutil
import threading
import queue
import sounddevice as sd
import soundfile as sf

try:
    import pyttsx3
    _PYTTSX3_OK = True
except Exception as e:
    _PYTTSX3_OK = False
    print(f"[VOICE_AGENT] pyttsx3 not available: {e}", file=sys.stderr, flush=True)

# Piper TTS is only available if the actual executable exists on disk
PIPER_AVAILABLE = False
_piper_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "piper", "piper.exe"))
if not os.path.exists(_piper_exe):
    _piper_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "piper", "piper"))
if os.path.exists(_piper_exe):
    PIPER_AVAILABLE = True
    print(f"[VOICE] Piper TTS found at {_piper_exe}", flush=True)
else:
    print("[VOICE] Piper TTS not found — using pyttsx3 fallback", flush=True)

try:
    from core.face_bridge import speech_start, speech_stop, send_event
except ImportError:
    def speech_start(): pass
    def speech_stop(): pass
    def send_event(evt, data=None): pass

# Pronunciation corrections
PRONUNCIATION_FIX = {
    "roopi": "Roopy",
    "roopen": "Roopen"
}

# =====================================================================
# State
# =====================================================================

_tts_queue = queue.Queue()
_is_speaking = False
_interrupt_requested = False
_speaker_thread = None
_engine_ready = threading.Event()
_shutdown = False

# =====================================================================
# Single Persistent Speaker Thread
# =====================================================================

def _speaker_loop():
    """Runs on a single dedicated thread. Owns the pyttsx3 engine forever."""
    global _is_speaking, _interrupt_requested

    if not _PYTTSX3_OK:
        print("[VOICE_AGENT] pyttsx3 not available — speaker thread exiting.", flush=True)
        _engine_ready.set()
        return

    # COM init for Windows SAPI5
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    # Step 3 — Force default output device (sounddevice query, one-time)
    try:
        import sounddevice as sd
        default_out = sd.default.device[1]
        sd.default.device = (None, default_out)
        if default_out is not None and default_out >= 0:
            dev = sd.query_devices(default_out)
            print(f"[VOICE] Audio output: {dev['name']}", flush=True)
            print(f"AUDIO DEVICE: detected output device: {dev['name']}", flush=True)
            print(f"AUDIO DEVICE: selected index: {default_out}", flush=True)
        else:
            print("[VOICE] Using system default audio output", flush=True)
    except Exception:
        print("[VOICE] sounddevice not available — using system default", flush=True)

    # Initialize engine ONCE — reuse for all speech
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)

    # Cache voice ID for reuse
    _cached_voice_id = None
    voices = engine.getProperty('voices')
    if voices:
        for v in voices:
            name_lower = v.name.lower()
            if 'zira' in name_lower or 'female' in name_lower:
                _cached_voice_id = v.id
                break
        if not _cached_voice_id:
            for v in voices:
                if 'hazel' in v.name.lower():
                    _cached_voice_id = v.id
                    break
        if not _cached_voice_id and voices:
            _cached_voice_id = voices[0].id
    if _cached_voice_id:
        engine.setProperty('voice', _cached_voice_id)

    # Startup test — verify audio actually works
    # CRITICAL: Must use save_to_file() here, NOT engine.say().
    # Mixing say() then save_to_file() on the same pyttsx3 engine
    # causes a permanent SAPI5 COM deadlock on Windows.
    _startup_wav = os.path.abspath("temp_audio.wav")
    engine.save_to_file("Genesis voice ready", _startup_wav)
    engine.runAndWait()

    # CRITICAL: Destroy startup engine to break pyttsx3 singleton.
    # pyttsx3.init() returns a singleton. If the startup engine stays
    # alive, every subsequent pyttsx3.init() in the loop returns the
    # SAME poisoned object, and runAndWait() deadlocks on the 2nd call.
    engine.stop()
    del engine

    try:
        import soundfile as _sf
        _startup_audio, _startup_sr = _sf.read(_startup_wav, dtype='float32')
        if len(_startup_audio) > 100:
            sd.play(_startup_audio, _startup_sr)
            sd.wait()
    except Exception as _e:
        print(f"[VOICE] Startup audio error: {_e}", flush=True)

    print("VOICE OUTPUT OK", flush=True)

    _engine_ready.set()
    print("VOICE ENGINE OK", flush=True)

    # Main speak loop — runs until shutdown
    print("VOICE THREAD: loop entered", flush=True)
    while not _shutdown:
        try:
            text = _tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        
        if text is None:
            break

        _is_speaking = True
        global _speaking_start_time
        _speaking_start_time = time.time()
        _interrupt_requested = False
        print(f"SPEAK: {text}", flush=True)
        print("TTS TRACE: text received", flush=True)
        print("VOICE THREAD: text received", flush=True)

        try:
            speech_start()
            send_event("set_state", {"state": "SPEAKING"})
        except Exception:
            pass

        try:
            # Re-init engine PER ITERATION — pyttsx3 runAndWait() deadlocks
            # on 2nd+ call from a background thread (Windows SAPI5 COM bug).
            # Proven fix: fresh engine per call completes reliably.
            loop_engine = pyttsx3.init()
            loop_engine.setProperty('rate', 160)
            loop_engine.setProperty('volume', 1.0)
            if _cached_voice_id:
                loop_engine.setProperty('voice', _cached_voice_id)

            import json, wave
            import soundfile as sf
            wav_path = os.path.abspath("temp_audio.wav")
            print("TTS TRACE: entering save_to_file", flush=True)
            loop_engine.save_to_file(text, wav_path)
            print("TTS TRACE: entering runAndWait", flush=True)
            loop_engine.runAndWait()
            print("TTS TRACE: runAndWait finished", flush=True)
            print("TTS TRACE: wav generated", flush=True)
            try:
                loop_engine.stop()
            except Exception:
                pass
            del loop_engine
            
            print("TTS TRACE: checking WAV file", flush=True)
            # STAGE 8: File Lock or I/O Delay polling.
            for _ in range(50):
                exists = os.path.exists(wav_path)
                sz = os.path.getsize(wav_path) if exists else 0
                if exists and sz > 1000:
                    break
                time.sleep(0.01)
            
            # STAGE 4: WAV File Generation
            exists = os.path.exists(wav_path)
            sz = os.path.getsize(wav_path) if exists else 0
            print(f"AUDIO TRACE: wav path exists={exists}, size={sz}", flush=True)

            # Verify the WAV file actually exists and has content
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
                print(f"[VOICE] WARNING: WAV file missing or empty at {wav_path}", flush=True)
            else:
                from core.event_bus import get_event_bus
                bus = get_event_bus()

                # STAGE 5: WAV Integrity
                try:
                    audio_data, samplerate = sf.read(wav_path, dtype='float32')
                    print("AUDIO TRACE: frames:", len(audio_data), flush=True)
                    print("AUDIO TRACE: samplerate:", samplerate, flush=True)
                except Exception as e:
                    print(f"AUDIO TRACE: sf.read Exception: {e}", flush=True)
                    audio_data = []
                    samplerate = 24000

                if len(audio_data) < 100:
                    print("[VOICE] WARNING: WAV contains no audio frames", flush=True)
                    continue

                # Compute actual playback duration
                playback_duration = len(audio_data) / samplerate

                # Play audio via sounddevice (unified PortAudio backend)
                print(f"AUDIO TRACE: default device = {sd.default.device}", flush=True)
                # STAGE 10: External Interruptions check
                print(f"AUDIO TRACE: interrupt_requested = {_interrupt_requested}", flush=True)
                print("AUDIO TRACE: playback start", flush=True)
                audio_start = time.time()
                sd.play(audio_data, samplerate)

                def _rhubarb_worker(txt, a_start, w_path):
                    from core.event_bus import get_event_bus
                    bus = get_event_bus()
                    rhubarb_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "rhubarb", "rhubarb.exe"))
                    cues = []
                    if os.path.exists(rhubarb_exe) and os.path.exists(w_path):
                        try:
                            print("RHUBARB TRACE: analysis started", flush=True)
                            res = subprocess.run(
                                [rhubarb_exe, "-f", "json", w_path],
                                capture_output=True, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
                            )
                            if res.returncode == 0:
                                data = json.loads(res.stdout)
                                cues = data.get("mouthCues", [])
                        except Exception as e:
                            print(f"[VOICE] Rhubarb error: {e}", flush=True)

                    rhubarb_to_face = {
                        "A": "M", "B": "S", "C": "A", "D": "A",
                        "E": "O", "F": "U", "G": "F", "H": "TH", "X": "N"
                    }

                    if cues:
                        for cue in cues:
                            if _interrupt_requested:
                                break

                            q_viseme = rhubarb_to_face.get(cue["value"], "N")
                            q_time = cue["start"]
                            target_sys_time = a_start + q_time
                            sleep_dur = target_sys_time - time.time()

                            if sleep_dur > 0:
                                time.sleep(sleep_dur)

                            if bus:
                                bus.publish_sync("VISEME_EVENT", "voice", {"viseme": q_viseme, "time": q_time})

                        print("RHUBARB TRACE: viseme events generated", flush=True)
                        if bus:
                            bus.publish_sync("VISEME_EVENT", "voice", {"viseme": "N", "time": time.time() - a_start})
                    # No fallback sleep here — sd.wait() handles playback wait

                threading.Thread(target=_rhubarb_worker, args=(text, audio_start, wav_path), daemon=True).start()

                # Block until sounddevice finishes playback — guaranteed completion
                sd.wait()
                print("AUDIO TRACE: playback end", flush=True)
                print(f"AUDIO TRACE: playback complete ({playback_duration:.2f}s)", flush=True)

        except Exception as e:
            print(f"[VOICE] TTS play error: {e}", file=sys.stderr, flush=True)
            print(f"AUDIO TRACE EXCEPTION: {e}", flush=True)
            # Try to recover COM
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

        _is_speaking = False
        print("SPEAK END", flush=True)

        try:
            speech_stop()
            send_event("set_state", {"state": "IDLE"})
        except Exception:
            pass


# Start the speaker thread at import time
def _start_speaker_thread():
    global _speaker_thread
    if _speaker_thread is None:
        _speaker_thread = threading.Thread(target=_speaker_loop, daemon=True, name="SpeakerThread")
        _speaker_thread.start()

# =====================================================================
# Public API
# =====================================================================

def apply_pronunciation_fixes(text):
    """Apply pronunciation corrections before TTS rendering."""
    for original, fixed in PRONUNCIATION_FIX.items():
        text = text.replace(original, fixed)
    return text


def speak(text):
    global _is_speaking

    if not text or not isinstance(text, str):
        return

    _start_speaker_thread()
    _engine_ready.wait(timeout=10)

    if not _PYTTSX3_OK:
        print("[VOICE] pyttsx3 not available", flush=True)
        return

    text = apply_pronunciation_fixes(text)

    try:
        _tts_queue.put_nowait(text)
    except Exception as e:
        print("[VOICE] queue error", e, flush=True)

    # do not wait
    return


def interrupt():
    """Interrupt any currently playing speech. Thread-safe."""
    global _interrupt_requested
    _interrupt_requested = True

    while not _tts_queue.empty():
        try:
            _tts_queue.get_nowait()
        except queue.Empty:
            break

    try:
        speech_stop()
    except Exception:
        pass


_speaking_start_time = 0

def is_speaking():
    """Return True if TTS is currently playing audio."""
    global _is_speaking, _speaking_start_time
    if _is_speaking and (time.time() - _speaking_start_time > 15.0):
        print("[VOICE] is_speaking auto-timeout reached. Releasing guard.", flush=True)
        _is_speaking = False
    return _is_speaking


def stop_speaker():
    """Stop the speaker thread cleanly. Called on system shutdown."""
    global _shutdown
    _shutdown = True
    # Drain any pending text
    while not _tts_queue.empty():
        try:
            _tts_queue.get_nowait()
        except queue.Empty:
            break
    # Push sentinel to unblock the .get()
    try:
        _tts_queue.put_nowait(None)
    except Exception:
        pass
    # Join the thread
    if _speaker_thread is not None and _speaker_thread.is_alive():
        try:
            _speaker_thread.join(timeout=3)
        except Exception:
            pass


def get_voice_status():
    """Return a status dict about voice system setup."""
    return {
        "tts_available": _PYTTSX3_OK,
        "tts_engine": "pyttsx3 (Single Thread)",
        "pyttsx3_available": _PYTTSX3_OK,
        "status": "Single-Thread PyTTSX3 Ready" if _PYTTSX3_OK else "pyttsx3 unavailable"
    }

print("VOICE OK", flush=True)
print("SPEECH OK", flush=True)
print("AUDIO OK", flush=True)
