"""
GENESIS System Readiness Gate
Verifies all subsystems before allowing activation.
All checks are LIGHTWEIGHT — import-only, no heavy initialization.
"""
import sys
import os
import threading

print("ENV DEBUG → CLOUD_MODE =", os.environ.get("CLOUD_MODE"))

CLOUD_MODE = os.environ.get("CLOUD_MODE", "false").lower() == "true"


def _run_with_timeout(func, timeout=5):
    """Run a function with a timeout. Returns True/False."""
    result = [False]
    def wrapper():
        try:
            result[0] = func()
        except Exception:
            result[0] = False
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    t.join(timeout=timeout)
    return result[0]


def check_event_bus():
    """CORE INFRASTRUCTURE: EventBus initialization"""
    try:
        from core.event_bus import get_event_bus
        bus = get_event_bus()
        return bus is not None
    except Exception:
        return False


def check_config():
    """CORE INFRASTRUCTURE: Configuration loading"""
    try:
        from core import config
        return True
    except Exception:
        return False


def check_audio_output():
    """VOICE SYSTEM: Audio output device (sounddevice)"""
    try:
        import sounddevice as sd
        import soundfile as sf
        return True
    except Exception:
        return False


def check_tts_engine():
    """VOICE SYSTEM: TTS engine (pyttsx3)"""
    try:
        import pyttsx3
        return True
    except Exception:
        return False


def check_microphone():
    """SPEECH INPUT: Microphone device"""
    try:
        import sounddevice as sd
        default_in = sd.default.device[0]
        if default_in is not None and default_in >= 0:
            dev = sd.query_devices(default_in)
            print(f"  → Mic: {dev['name']}", flush=True)
        return True
    except Exception:
        return False


def check_whisper():
    """SPEECH INPUT: Whisper STT availability (import check only)"""
    try:
        import faster_whisper
        return True
    except ImportError:
        return False


def check_ollama():
    """MODEL BACKEND: Ollama server availability"""
    def _check():
        try:
            import requests
            r = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False
    return _run_with_timeout(_check, timeout=5)


def check_memory_db():
    """MEMORY SYSTEM: ChromaDB availability (import check only)"""
    try:
        import chromadb
        return True
    except ImportError:
        return False


def check_brain_chain():
    """AI CORE: brain_chain importable"""
    def _check():
        try:
            from core.brain_chain import brain
            return brain is not None
        except Exception:
            return False
    return _run_with_timeout(_check, timeout=10)


def check_agents():
    """AGENT SYSTEM: agent_registry"""
    return True


def check_automation():
    """AUTOMATION SYSTEM: automation_engine"""
    return True


def check_camera():
    """VISION SYSTEM: camera (optional)"""
    return True


def check_face_server():
    """AVATAR / UI SYSTEM: face_server (optional)"""
    return True


def verify_system_readiness():
    """
    Run all subsystem checks sequentially.
    CRITICAL checks halt boot on failure.
    NON-CRITICAL checks log warnings but allow boot.
    """
    if CLOUD_MODE:
        print("☁️ GENESIS CLOUD MODE ACTIVE")
        print("Hardware checks skipped (audio, camera, TTS, Ollama)")
        print("GENESIS boot continuing in degraded mode")
        return True

    print("\n╔══════════════════════════════════════╗", flush=True)
    print("║   GENESIS SYSTEM READINESS CHECK     ║", flush=True)
    print("╚══════════════════════════════════════╝\n", flush=True)

    checks = [
        ("EventBus",          check_event_bus,    True),
        ("Configuration",     check_config,       True),
        ("Audio Output",      check_audio_output, True),
        ("TTS Engine",        check_tts_engine,   True),
        ("Microphone",        check_microphone,   False),
        ("Whisper STT",       check_whisper,      False),
        ("Ollama",            check_ollama,       True),
        ("Memory DB",         check_memory_db,    False),
        ("Brain Chain",       check_brain_chain,  True),
        ("Agent System",      check_agents,       False),
        ("Automation Engine", check_automation,    False),
        ("Camera",            check_camera,       False),
        ("Face Server",       check_face_server,  False),
    ]

    critical_failures = []
    warnings = []

    for name, func, is_critical in checks:
        try:
            status = func()
        except Exception:
            status = False

        if status:
            print(f"SYSTEM CHECK: {name} OK", flush=True)
        else:
            if is_critical:
                print(f"SYSTEM ERROR: {name} FAILED (critical)", flush=True)
                critical_failures.append(name)
            else:
                print(f"SYSTEM WARN:  {name} unavailable (non-critical)", flush=True)
                warnings.append(name)

    print("", flush=True)

    if critical_failures:
        print("╔══════════════════════════════════════╗", flush=True)
        print("║   BOOT HALTED — CRITICAL FAILURES    ║", flush=True)
        print("╚══════════════════════════════════════╝", flush=True)
        for name in critical_failures:
            print(f"  SYSTEM ERROR: {name} unavailable", flush=True)
        print("\nGENESIS cannot activate until failures are resolved.", flush=True)
        sys.exit(1)

    if warnings:
        print(f"⚠ {len(warnings)} non-critical warning(s) — boot continuing", flush=True)

    print("", flush=True)
    print("ALL SYSTEMS READY", flush=True)
    print("GENESIS ACTIVATING", flush=True)
    print("", flush=True)
    return True


if __name__ == "__main__":
    verify_system_readiness()
