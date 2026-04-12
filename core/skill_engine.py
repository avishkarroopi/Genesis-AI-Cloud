"""
GENESIS Skill Engine - Self-Learning System.
Phase 11 Requirement.
Manages learned skills/commands that GENESIS acquires through experience.
"""

import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from core.event_bus import get_event_bus

try:
    from core.experience_memory import get_experience_memory
except ImportError:
    def get_experience_memory():
        class _Noop:
            def record(self, **kwargs): pass
        return _Noop()


class Skill:
    """A learned or registered skill that GENESIS can execute."""

    def __init__(self, name: str, description: str, trigger_phrases: List[str],
                 handler: Optional[Callable] = None, learned: bool = False):
        self.name = name
        self.description = description
        self.trigger_phrases = [p.lower() for p in trigger_phrases]
        self.handler = handler
        self.learned = learned
        self.use_count = 0
        self.success_count = 0
        self.created_at = datetime.now().isoformat()
        self.last_used = ""

    def matches(self, text: str) -> bool:
        """Check if input text matches any trigger phrase."""
        text_lower = text.lower()
        return any(phrase == text_lower for phrase in self.trigger_phrases)

    def execute(self, *args, **kwargs) -> Any:
        """Execute this skill."""
        self.use_count += 1
        self.last_used = datetime.now().isoformat()
        if self.handler:
            try:
                result = self.handler(*args, **kwargs)
                self.success_count += 1
                return result
            except Exception as e:
                return f"Skill '{self.name}' failed: {e}"
        return f"Skill '{self.name}' has no handler."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger_phrases": self.trigger_phrases,
            "learned": self.learned,
            "use_count": self.use_count,
            "success_count": self.success_count,
            "success_rate": (self.success_count / self.use_count) if self.use_count > 0 else 0.0,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }


class SkillEngine:
    """
    Manages GENESIS skills — both built-in and learned.
    Skills can be registered programmatically or learned from repeated successful patterns.
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._lock = threading.Lock()

    def register_skill(self, name: str, description: str, trigger_phrases: List[str],
                       handler: Callable = None, learned: bool = False) -> Skill:
        """Register a new skill."""
        skill = Skill(name, description, trigger_phrases, handler, learned)
        with self._lock:
            self._skills[name] = skill
        print(f"[SKILL] Registered skill: {name}", flush=True)
        return skill

    def find_skill(self, text: str) -> Optional[Skill]:
        """Find a matching skill for the given input text."""
        with self._lock:
            for skill in self._skills.values():
                if skill.matches(text):
                    return skill
        return None

    def execute_skill(self, text: str, *args, **kwargs) -> Optional[str]:
        """Find and execute a matching skill."""
        skill = self.find_skill(text)
        if skill:
            result = skill.execute(*args, **kwargs)
            # Record experience
            mem = get_experience_memory()
            success = bool(result) and "failed" not in str(result).lower()
            mem.record(
                action=f"skill:{skill.name}",
                result=str(result),
                success=success,
                source="skill_engine",
            )
            bus = get_event_bus()
            if bus:
                try:
                    bus.publish_sync("SKILL_EXECUTED", "skill_engine", {
                        "skill": skill.name,
                        "success": success
                    })
                except Exception as e:
                    print("[SKILL] event publish error", e, flush=True)
            return str(result)
        return None

    def get_skill(self, name: str) -> Optional[Skill]:
        with self._lock:
            return self._skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.to_dict() for s in self._skills.values()]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_skills": len(self._skills),
                "learned_skills": sum(1 for s in self._skills.values() if s.learned),
                "builtin_skills": sum(1 for s in self._skills.values() if not s.learned),
                "total_executions": sum(s.use_count for s in self._skills.values()),
            }

    # ------------------------------------------------------------------
    # Built-in default skills
    # ------------------------------------------------------------------

    def register_defaults(self):
        """Register built-in skills."""
        self.register_skill(
            "time_check", "Tell the current time",
            ["what time", "current time", "tell me the time"],
            handler=lambda: f"The current time is {datetime.now().strftime('%I:%M %p')}.",
        )
        self.register_skill(
            "date_check", "Tell the current date",
            ["what date", "today's date", "what day"],
            handler=lambda: f"Today is {datetime.now().strftime('%B %d, %Y')}.",
        )
        self.register_skill(
            "system_status", "Report system status",
            ["system status", "how are you", "status report"],
            handler=lambda: "All GENESIS systems are operational.",
        )
        self.register_skill(
            "self_identify", "Identify self",
            ["who are you", "what are you", "your name"],
            handler=lambda: "I am GENESIS, your personal AI assistant.",
        )
        print("[SKILL] Default skills registered.", flush=True)


# --------------- Module-level singleton ---------------
_skill_engine: Optional[SkillEngine] = None


def get_skill_engine() -> SkillEngine:
    global _skill_engine
    if _skill_engine is None:
        _skill_engine = SkillEngine()
    return _skill_engine


def start_skill_engine():
    engine = get_skill_engine()
    engine.register_defaults()
    print("[SKILL] Skill engine started.", flush=True)
