"""
GENESIS Life Timeline Memory — Phase 2.5
Generates chronological summaries of life memory grouped by month/year.
Integrates with life_memory_engine and knowledge graph.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


def get_timeline(months_back: int = 6, limit_per_month: int = 20) -> Dict[str, List[Dict]]:
    """
    Build a timeline grouped by 'Month YYYY' from life memory entries.
    Returns ordered dict: { "April 2026": [...entries...], ... }
    """
    try:
        from core.memory.life_memory_engine import get_life_memory_engine
        engine = get_life_memory_engine()
        all_entries = engine.get_recent(limit=limit_per_month * months_back)
    except Exception as e:
        logger.error(f"[TIMELINE] Failed to load life memory: {e}")
        return {}

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for entry in all_entries:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            key = ts.strftime("%B %Y")
            grouped[key].append(entry)
        except Exception:
            grouped["Unknown"].append(entry)

    # Sort months descending (newest first)
    sorted_timeline = {}
    for key in sorted(grouped.keys(), key=_month_sort_key, reverse=True):
        sorted_timeline[key] = grouped[key]

    return sorted_timeline


def format_timeline_text(months_back: int = 6) -> str:
    """Return a human-readable timeline summary string."""
    timeline = get_timeline(months_back=months_back)
    if not timeline:
        return "No life memory recorded yet."

    lines = []
    for month, entries in timeline.items():
        lines.append(f"\n{month}")
        for entry in entries[:10]:  # Max 10 bullet points per month
            category = entry.get("category", "note")
            content = entry.get("content", "")
            people = entry.get("people", [])
            people_str = f" (with {', '.join(people)})" if people else ""
            lines.append(f"  * [{category}] {content[:100]}{people_str}")

    return "\n".join(lines)


def get_timeline_summary(months_back: int = 3) -> str:
    """Single-method entry point for voice query responses."""
    try:
        text = format_timeline_text(months_back=months_back)
        if not text.strip() or text == "No life memory recorded yet.":
            return "No timeline entries found for the past few months."
        return f"Here is your life timeline for the past {months_back} months:{text}"
    except Exception as e:
        logger.error(f"[TIMELINE] Summary generation failed: {e}")
        return "Timeline unavailable."


def _month_sort_key(month_str: str) -> datetime:
    try:
        return datetime.strptime(month_str, "%B %Y")
    except Exception:
        return datetime.min
