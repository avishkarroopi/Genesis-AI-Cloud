"""
GENESIS Phase-3 — Ethical Intelligence Layer
Module 9: Decision safety, risk detection, value alignment, human safety enforcement.

Subscribes to: AGENT_DIRECTIVE, SKILL_EXECUTED
Publishes: SAFETY_VETO, ETHICS_AUDIT
Gate-keeper only — cannot initiate actions.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

# Safety categories that always require audit
SAFETY_CRITICAL_ACTIONS = [
    "delete", "remove", "destroy", "shutdown", "kill", "format",
    "overwrite", "drop", "wipe", "reset", "disable",
]

# Domains that require ethical review
ETHICAL_DOMAINS = [
    "personal_data", "financial", "health", "communication",
    "surveillance", "automation", "identity",
]


class DecisionAuditor:
    """Audit agent decisions before execution."""

    def __init__(self):
        self._audit_log: deque = deque(maxlen=500)

    def audit(self, action: str, context: Dict = None) -> Dict[str, Any]:
        """Audit an action for safety and ethical concerns."""
        concerns = []
        risk_level = "low"

        action_lower = action.lower()

        # Check for safety-critical keywords
        for keyword in SAFETY_CRITICAL_ACTIONS:
            if keyword in action_lower:
                concerns.append(f"Safety-critical action: '{keyword}'")
                risk_level = "high"

        # Check domain risks
        for domain in ETHICAL_DOMAINS:
            if domain in action_lower:
                concerns.append(f"Ethical domain involvement: '{domain}'")
                if risk_level != "high":
                    risk_level = "medium"

        result = {
            "action": action,
            "risk_level": risk_level,
            "concerns": concerns,
            "approved": risk_level != "high",
            "audited_at": datetime.now().isoformat(),
        }

        self._audit_log.append(result)
        return result


class RiskAssessor:
    """Evaluate risk of proposed actions."""

    def assess_risk(self, action: str, target: str = "", context: Dict = None) -> Dict:
        """Return risk assessment for a proposed action."""
        risk_score = 0.0

        # Evaluate destructive potential
        if any(kw in action.lower() for kw in SAFETY_CRITICAL_ACTIONS):
            risk_score += 0.5

        # Evaluate target sensitivity
        sensitive_targets = ["database", "config", "system", "memory", "voice", "audio"]
        if any(t in target.lower() for t in sensitive_targets):
            risk_score += 0.3

        return {
            "risk_score": min(1.0, risk_score),
            "risk_level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
            "should_block": risk_score > 0.7,
        }


class ValueAlignmentChecker:
    """Check actions against human safety rules."""

    def __init__(self):
        self._core_values = [
            "Do not harm the user or their data",
            "Do not take irreversible actions without confirmation",
            "Respect user privacy and preferences",
            "Maintain system stability",
            "Prioritize safety over efficiency",
        ]

    def check_alignment(self, action: str) -> Dict:
        violations = []
        action_lower = action.lower()

        if any(kw in action_lower for kw in ["delete", "destroy", "wipe"]):
            violations.append("Potential violation: irreversible action without confirmation")

        if any(kw in action_lower for kw in ["spy", "track", "monitor"]):
            violations.append("Potential violation: privacy concern")

        return {
            "aligned": len(violations) == 0,
            "violations": violations,
            "core_values_checked": len(self._core_values),
        }


class SafetyEnforcer:
    """Veto dangerous operations."""

    def __init__(self):
        self._vetoed_actions: deque = deque(maxlen=100)

    def evaluate(self, audit_result: Dict, risk_result: Dict, alignment: Dict) -> Dict:
        """Final safety gate — decides whether to allow or veto."""
        should_veto = False
        reasons = []

        if not audit_result.get("approved", True):
            should_veto = True
            reasons.extend(audit_result.get("concerns", []))

        if risk_result.get("should_block", False):
            should_veto = True
            reasons.append(f"Risk score: {risk_result.get('risk_score', 0)}")

        if not alignment.get("aligned", True):
            should_veto = True
            reasons.extend(alignment.get("violations", []))

        result = {
            "vetoed": should_veto,
            "reasons": reasons,
            "timestamp": datetime.now().isoformat(),
        }

        if should_veto:
            self._vetoed_actions.append(result)

        return result


class EthicalIntelligence:
    """Master controller for the ethical intelligence layer."""

    def __init__(self):
        self.auditor = DecisionAuditor()
        self.risk_assessor = RiskAssessor()
        self.alignment = ValueAlignmentChecker()
        self.enforcer = SafetyEnforcer()
        self._bus = None
        logger.info("[ETHICS] Ethical Intelligence Layer initialized")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("AGENT_DIRECTIVE", self._on_directive)
                self._bus.subscribe("SKILL_EXECUTED", self._on_skill_executed)
                logger.info("[ETHICS] Event bus bound")
        except Exception as e:
            logger.warning(f"[ETHICS] Event bus binding failed: {e}")

    def _on_directive(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            action = data.get("task", "")
            result = self.full_safety_check(action)

            if result["vetoed"] and self._bus:
                self._bus.publish_sync("SAFETY_VETO", "ethical_layer", {
                    "action": action,
                    "reasons": result["reasons"],
                })
                logger.warning(f"[ETHICS] VETOED: {action}")
        except Exception as e:
            logger.error(f"[ETHICS] Directive handler error: {e}")

    def _on_skill_executed(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            skill = data.get("skill_name", "")
            audit = self.auditor.audit(skill)

            if self._bus:
                self._bus.publish_sync("ETHICS_AUDIT", "ethical_layer", audit)
        except Exception as e:
            logger.error(f"[ETHICS] Skill audit error: {e}")

    def full_safety_check(self, action: str, target: str = "") -> Dict:
        """Run full safety pipeline: audit → risk → alignment → enforce."""
        audit = self.auditor.audit(action)
        risk = self.risk_assessor.assess_risk(action, target)
        alignment = self.alignment.check_alignment(action)
        return self.enforcer.evaluate(audit, risk, alignment)

    def get_status(self) -> Dict[str, Any]:
        return {
            "audits_performed": len(self.auditor._audit_log),
            "vetoed_actions": len(self.enforcer._vetoed_actions),
        }


_ethical_layer = None


def get_ethical_intelligence() -> EthicalIntelligence:
    global _ethical_layer
    if _ethical_layer is None:
        _ethical_layer = EthicalIntelligence()
    return _ethical_layer


def start_ethical_layer():
    layer = get_ethical_intelligence()
    layer.bind_event_bus()
    print("[ETHICS] Ethical Intelligence Layer started", flush=True)
    return layer
