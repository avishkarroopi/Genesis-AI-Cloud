"""
Finance Tracker (Phase-2 User Intelligence)
Monitors budgets in the Life OS.
"""

from core.event_bus import get_event_bus

def log_expense(category: str, amount: float):
    """Log financial transaction."""
    bus = get_event_bus()
    bus.publish_sync("LIFE_OS_UPDATE", "life_os.finance_tracker", {"expense_category": category, "amount": amount})
    return True
