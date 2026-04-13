"""
GENESIS Usage Limit Engine
Tracks per-user API usage metrics and enforces plan-based caps.
Storage: PostgreSQL via core.db_pool (ThreadedConnectionPool)
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Plan Limits ─────────────────────────────────────────────────────────────

PLAN_LIMITS = {
    "lite": {
        "messages": 50,
        "automation_runs": 0,
        "agent_executions": 0,
        "research_queries": 0,
    },
    "core": {
        "messages": 500,
        "automation_runs": 50,
        "agent_executions": 50,
        "research_queries": 100,
    },
    "gold": {
        "messages": 2000,
        "automation_runs": 500,
        "agent_executions": 500,
        "research_queries": 1000,
    },
    "platinum": {
        "messages": -1,         # -1 = unlimited
        "automation_runs": -1,
        "agent_executions": -1,
        "research_queries": -1,
    },
}


def _ensure_table(conn):
    """Create usage_metrics table if absent."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage_metrics (
                user_id     VARCHAR(255) NOT NULL,
                metric      VARCHAR(100) NOT NULL,
                period      VARCHAR(20)  NOT NULL DEFAULT 'monthly',
                count       INTEGER      NOT NULL DEFAULT 0,
                reset_at    BIGINT       NOT NULL,
                PRIMARY KEY (user_id, metric, period)
            )
        """)
    conn.commit()


def _monthly_reset_ts() -> int:
    """Return UNIX timestamp for the start of the next calendar month."""
    import datetime
    now = datetime.datetime.utcnow()
    if now.month == 12:
        next_month = datetime.datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime.datetime(now.year, now.month + 1, 1)
    return int(next_month.timestamp())


def get_current_usage(user_id: str, metric: str) -> int:
    """Return the current count for the given user + metric this period."""
    from core.db_pool import get_connection, release_connection
    conn = get_connection()
    if not conn:
        return 0
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count FROM usage_metrics WHERE user_id=%s AND metric=%s",
                (user_id, metric)
            )
            row = cur.fetchone()
            return row[0] if row else 0
    except Exception as e:
        logger.error(f"[LIMITS] get_current_usage error: {e}")
        return 0
    finally:
        release_connection(conn)


def increment_usage(user_id: str, metric: str, amount: int = 1) -> int:
    """Increment usage counter. Returns the new count."""
    from core.db_pool import get_connection, release_connection
    conn = get_connection()
    if not conn:
        return 0
    try:
        _ensure_table(conn)
        reset_ts = _monthly_reset_ts()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usage_metrics (user_id, metric, count, reset_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, metric, period)
                DO UPDATE SET count = usage_metrics.count + %s
                RETURNING count
            """, (user_id, metric, amount, reset_ts, amount))
            new_count = cur.fetchone()[0]
        conn.commit()
        return new_count
    except Exception as e:
        logger.error(f"[LIMITS] increment_usage error: {e}")
        return 0
    finally:
        release_connection(conn)


def check_limit(user_id: str, metric: str, plan: str) -> bool:
    """
    Returns True if the user is within their plan limit.
    Returns False if the limit is exceeded.
    """
    limit = PLAN_LIMITS.get(plan.lower(), PLAN_LIMITS["lite"]).get(metric, 0)
    if limit == -1:
        return True  # Unlimited
    current = get_current_usage(user_id, metric)
    allowed = current < limit
    if not allowed:
        logger.warning(f"[LIMITS] EXCEEDED: user={user_id} metric={metric} count={current} limit={limit} plan={plan}")
    return allowed


def enforce_limit(user_id: str, metric: str, plan: str):
    """
    Raises PermissionError if the user has exceeded their plan limit.
    Increments the counter on success.
    """
    if not check_limit(user_id, metric, plan):
        limit = PLAN_LIMITS.get(plan.lower(), {}).get(metric, 0)
        raise PermissionError(
            f"Usage limit reached: {metric} limit is {limit} for '{plan}' plan. "
            "Upgrade your plan to continue."
        )
    increment_usage(user_id, metric)


def get_usage_report(user_id: str, plan: str) -> dict:
    """Return a summary of current usage vs plan limits for a user."""
    report = {}
    limits = PLAN_LIMITS.get(plan.lower(), PLAN_LIMITS["lite"])
    for metric, limit in limits.items():
        current = get_current_usage(user_id, metric)
        report[metric] = {
            "used": current,
            "limit": "unlimited" if limit == -1 else limit,
            "exceeded": False if limit == -1 else current >= limit,
        }
    return report
