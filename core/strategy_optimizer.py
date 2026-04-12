"""
GENESIS Strategy Optimizer — Phase 6 Intelligence Integration.
Analyzes failure patterns from experience_memory and suggests improved strategies.
Does NOT rewrite learning_engine — extends it with pattern analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """Analyzes repeated task failures and suggests improved strategies."""

    def __init__(self):
        self._retry_history: Dict[str, int] = defaultdict(int)  # action -> retry count
        logger.info("[STRATEGY] Strategy optimizer initialized")

    def analyze_failures(self, limit: int = 100) -> Dict[str, Any]:
        """Analyze failure patterns from experience memory.

        Returns a report of the most common failure patterns,
        failure rates by action type, and suggested improvements.
        """
        try:
            from core.experience_memory import get_experience_memory
            mem = get_experience_memory()
        except ImportError:
            return {"error": "experience_memory not available"}

        recent = mem.recall_recent(limit=limit)
        if not recent:
            return {"total": 0, "failures": 0, "patterns": []}

        failures = [e for e in recent if not e.get("success", True)]
        successes = [e for e in recent if e.get("success", True)]

        # Count failure patterns by action prefix
        failure_actions = Counter()
        failure_contexts = Counter()
        for f in failures:
            action = f.get("action", "unknown")
            # Normalize action to category
            category = action.split(":")[0] if ":" in action else action.split(" ")[0]
            failure_actions[category] += 1
            ctx = f.get("context", "")
            if ctx:
                failure_contexts[ctx[:50]] += 1

        # Build pattern list
        patterns = []
        for action, count in failure_actions.most_common(10):
            total_for_action = sum(
                1 for e in recent
                if (e.get("action", "").split(":")[0] if ":" in e.get("action", "")
                    else e.get("action", "").split(" ")[0]) == action
            )
            rate = count / total_for_action if total_for_action > 0 else 0
            patterns.append({
                "action_category": action,
                "failure_count": count,
                "total_attempts": total_for_action,
                "failure_rate": round(rate, 3),
            })

        return {
            "total_analyzed": len(recent),
            "failures": len(failures),
            "successes": len(successes),
            "overall_failure_rate": round(len(failures) / len(recent), 3) if recent else 0,
            "patterns": patterns,
            "top_failure_contexts": dict(failure_contexts.most_common(5)),
        }

    def suggest_strategy(self, failed_action: str, failed_result: str) -> str:
        """Suggest an alternative strategy for a failed action.

        Uses experience history to find what worked for similar actions.
        Falls back to generic retry advice.
        """
        try:
            from core.experience_memory import get_experience_memory
            mem = get_experience_memory()
        except ImportError:
            return f"Retry '{failed_action}' with simplified parameters."

        # Look for successful experiences with similar actions
        similar = mem.recall(failed_action, limit=20)
        successes = [e for e in similar if e.get("success", False)]

        if successes:
            # Found a past success for similar action — suggest it
            best = successes[0]
            return (
                f"Previous success found for similar action '{best.get('action', '')}'. "
                f"Result was: {best.get('result', 'N/A')[:100]}. "
                f"Suggest retrying with this approach."
            )

        # Track retry count
        self._retry_history[failed_action] += 1
        retries = self._retry_history[failed_action]

        if retries >= 3:
            return (
                f"Action '{failed_action}' has failed {retries} times. "
                f"Recommend skipping or decomposing into smaller sub-tasks."
            )

        # Generic fallback suggestions based on error type
        result_lower = failed_result.lower()
        if "timeout" in result_lower:
            return "Previous attempt timed out. Suggest increasing timeout or simplifying the request."
        if "not found" in result_lower:
            return "Resource not found. Verify the target exists before retrying."
        if "permission" in result_lower or "blocked" in result_lower:
            return "Action was blocked by security. Check permissions configuration."

        return f"Retry '{failed_action}' with modified parameters. Attempt {retries + 1}."

    def get_failure_stats(self) -> Dict[str, Any]:
        """Return summary statistics about failure patterns."""
        analysis = self.analyze_failures(limit=200)
        return {
            "total_analyzed": analysis.get("total_analyzed", 0),
            "overall_failure_rate": analysis.get("overall_failure_rate", 0),
            "top_failing_actions": analysis.get("patterns", [])[:5],
            "retry_counts": dict(self._retry_history),
        }


# --------------- Module-level singleton ---------------
_optimizer: Optional[StrategyOptimizer] = None


def get_strategy_optimizer() -> StrategyOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = StrategyOptimizer()
    return _optimizer
