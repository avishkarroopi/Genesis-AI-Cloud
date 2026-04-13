"""
GENESIS Feature Gate System
Controls module access based on user plan tier.
Plans: Lite, Core, Gold, Platinum
"""
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── Plan Definitions ────────────────────────────────────────────────────────

PLAN_FEATURES: Dict[str, List[str]] = {
    "lite": [
        "chat",
    ],
    "core": [
        "chat",
        "memory_engine",
    ],
    "gold": [
        "chat",
        "memory_engine",
        "automation_engine",
        "research_engine",
    ],
    "platinum": [
        "chat",
        "memory_engine",
        "automation_engine",
        "research_engine",
        "agent_system",
        "avatar",
        "vision_engine",
    ],
}

ALL_FEATURES = [
    "chat",
    "memory_engine",
    "automation_engine",
    "research_engine",
    "agent_system",
    "avatar",
    "vision_engine",
]


def get_plan_features(plan: str) -> List[str]:
    """Return the list of features enabled for the given plan."""
    return PLAN_FEATURES.get(plan.lower(), PLAN_FEATURES["lite"])


def is_feature_enabled(plan: str, feature: str) -> bool:
    """Return True if the plan grants access to the given feature."""
    enabled = get_plan_features(plan)
    result = feature in enabled
    if not result:
        logger.info(f"[FEATURE GATE] Blocked: feature='{feature}' plan='{plan}'")
    return result


def gate_feature(plan: str, feature: str):
    """
    Call this at the start of any gated operation.
    Raises PermissionError if the feature is not in the plan.
    """
    if not is_feature_enabled(plan, feature):
        raise PermissionError(
            f"Feature '{feature}' is not available on the '{plan}' plan. "
            f"Upgrade to access this module."
        )


def get_feature_map(plan: str) -> Dict[str, bool]:
    """Return a dict of all features and whether they are enabled for the plan."""
    enabled = get_plan_features(plan)
    return {feature: (feature in enabled) for feature in ALL_FEATURES}
