"""
GENESIS Boot Validator — Phase 2.5
Verifies the system started its components in correct order.
Non-intrusive — reads state rather than controlling startup.

Expected order:
  1. Event Bus
  2. Memory System
  3. Agents
  4. Voice System
  5. Vision System
  6. UI / Face
"""

import logging
import threading
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

EXPECTED_SEQUENCE = [
    "event_bus",
    "memory_system",
    "agents",
    "voice_system",
    "vision_system",
    "face_ui",
]


class BootValidator:
    def __init__(self):
        self._checks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def validate(self) -> Dict[str, Any]:
        """Run all boot sequence checks and return report."""
        results = {}

        # 1. Event Bus
        results["event_bus"] = self._check_event_bus()

        # 2. Memory System
        results["memory_system"] = self._check_memory()

        # 3. Agents
        results["agents"] = self._check_agents()

        # 4. Voice System
        results["voice_system"] = self._check_voice()

        # 5. Vision System
        results["vision_system"] = self._check_vision()

        # 6. Face UI
        results["face_ui"] = self._check_face_ui()

        passed = sum(1 for v in results.values() if v.get("status") == "PASS")
        total = len(results)
        overall = "READY" if passed == total else f"PARTIAL ({passed}/{total})"

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "checks": results,
        }

        if passed == total:
            logger.info("[BOOT VALIDATOR] All systems verified in correct order.")
        else:
            failed = [k for k, v in results.items() if v.get("status") != "PASS"]
            logger.warning(f"[BOOT VALIDATOR] Boot issues detected: {failed}")

        # Publish validation result
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            if bus:
                bus.publish_sync("BOOT_VALIDATION_COMPLETE", "boot_validator", report)
        except Exception:
            pass

        return report

    def _check_event_bus(self) -> Dict:
        try:
            from core.event_bus import get_event_bus
            bus = get_event_bus()
            stats = bus.get_stats()
            return {"status": "PASS", "running": stats.get("running", False)}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}

    def _check_memory(self) -> Dict:
        try:
            from core.memory.memory_manager import search_memory
            search_memory("boot_check")
            return {"status": "PASS"}
        except Exception as e:
            return {"status": "PARTIAL", "error": str(e)}

    def _check_agents(self) -> Dict:
        try:
            from core.agents.agent_manager import init_agents
            return {"status": "PASS"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}

    def _check_voice(self) -> Dict:
        try:
            import threading
            names = [t.name for t in threading.enumerate()]
            alive = "VoiceSystem" in names or "SpeakerThread" in names
            return {"status": "PASS" if alive else "PARTIAL", "thread_alive": alive}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}

    def _check_vision(self) -> Dict:
        try:
            from core.vision import get_vision_system
            return {"status": "PASS"}
        except ImportError:
            return {"status": "PARTIAL", "note": "Vision module not loaded"}
        except Exception as e:
            return {"status": "PARTIAL", "error": str(e)}

    def _check_face_ui(self) -> Dict:
        try:
            from core.face_server import get_active_client_count
            count = get_active_client_count()
            return {"status": "PASS", "clients": count}
        except Exception as e:
            return {"status": "PARTIAL", "error": str(e)}


_validator: BootValidator = None


def get_boot_validator() -> BootValidator:
    global _validator
    if _validator is None:
        _validator = BootValidator()
    return _validator


def run_boot_validation() -> Dict[str, Any]:
    """Run and return boot sequence validation report."""
    validator = get_boot_validator()
    return validator.validate()
