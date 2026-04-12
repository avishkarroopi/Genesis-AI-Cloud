"""
GENESIS Phase-3 — Creativity Engine
Module 4: Idea generation, concept blending, innovation prompts, creative reasoning.

Subscribes to: COMMAND_RUN (for creative requests)
Publishes: CREATIVITY_GENERATED
"""

import logging
import time
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CreativityEngine:
    """LLM-powered idea generation and creative reasoning."""

    def __init__(self):
        self._ideas: List[Dict[str, Any]] = []
        self._bus = None
        self._templates = self._load_templates()
        logger.info("[CREATIVITY] Engine initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
        except Exception as e:
            logger.warning(f"[CREATIVITY] Event bus binding failed: {e}")

    def generate_idea(self, topic: str, method: str = "brainstorm") -> Dict[str, Any]:
        """Generate a creative idea using structured reasoning."""
        idea = {
            "id": f"idea_{int(time.time())}",
            "topic": topic,
            "method": method,
            "generated_at": datetime.now().isoformat(),
            "concepts": [],
            "prompt": "",
            "output": "",
        }

        if method == "brainstorm":
            idea["prompt"] = self._brainstorm_prompt(topic)
        elif method == "blend":
            idea["prompt"] = self._concept_blend_prompt(topic)
        elif method == "analogy":
            idea["prompt"] = self._analogy_prompt(topic)
        else:
            idea["prompt"] = self._brainstorm_prompt(topic)

        # Route through LLM for actual generation
        idea["output"] = self._route_to_llm(idea["prompt"])

        self._ideas.append(idea)

        if self._bus:
            self._bus.publish_sync("CREATIVITY_GENERATED", "creativity_engine", idea)

        logger.info(f"[CREATIVITY] Generated idea for: {topic} ({method})")
        return idea

    def concept_blend(self, concept_a: str, concept_b: str) -> Dict[str, Any]:
        """Blend two concepts to create novel ideas."""
        prompt = f"Blend these two concepts into a new innovative idea:\n1. {concept_a}\n2. {concept_b}\nGenerate a creative synthesis."
        
        result = {
            "concept_a": concept_a,
            "concept_b": concept_b,
            "blend_prompt": prompt,
            "output": self._route_to_llm(prompt),
            "generated_at": datetime.now().isoformat(),
        }

        if self._bus:
            self._bus.publish_sync("CREATIVITY_GENERATED", "creativity_engine", result)

        return result

    def get_innovation_prompt(self, domain: str = "general") -> str:
        """Get a creative innovation prompt for a given domain."""
        templates = self._templates.get(domain, self._templates.get("general", []))
        if templates:
            return random.choice(templates)
        return f"What novel approach could transform {domain}?"

    def get_idea_history(self, limit: int = 20) -> List[Dict]:
        return self._ideas[-limit:]

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_ideas": len(self._ideas),
            "domains": len(self._templates),
        }

    def _brainstorm_prompt(self, topic: str) -> str:
        return f"Generate 5 creative and unconventional ideas about: {topic}. Think outside the box."

    def _concept_blend_prompt(self, topic: str) -> str:
        return f"Take the concept of '{topic}' and combine it with an unexpected domain. What emerges?"

    def _analogy_prompt(self, topic: str) -> str:
        return f"Create a powerful analogy for '{topic}' by connecting it to nature, history, or art."

    def _route_to_llm(self, prompt: str) -> str:
        """Route creative prompt to the AI router for LLM processing."""
        try:
            from core.ai_router import route_ai_request
            return route_ai_request(prompt, owner_address="Sir", user_command=prompt)
        except Exception as e:
            logger.warning(f"[CREATIVITY] LLM routing fallback: {e}")
            return f"[Creative reasoning pending for: {prompt[:100]}]"

    def _load_templates(self) -> Dict[str, List[str]]:
        return {
            "general": [
                "What if we combined X with Y in an unexpected way?",
                "How would nature solve this problem?",
                "What would this look like in 100 years?",
                "What is the opposite approach, and could it work?",
            ],
            "technology": [
                "What emerging technology could disrupt this field?",
                "How could AI enhance this process?",
                "What would a zero-cost version look like?",
            ],
            "business": [
                "What unmet need does this address?",
                "How could this be offered as a service?",
                "What would a subscription model look like?",
            ],
        }


_creativity_engine = None


def get_creativity_engine() -> CreativityEngine:
    global _creativity_engine
    if _creativity_engine is None:
        _creativity_engine = CreativityEngine()
    return _creativity_engine


def start_creativity_engine():
    engine = get_creativity_engine()
    engine.bind_event_bus()
    print("[CREATIVITY] Creativity Engine started", flush=True)
    return engine
