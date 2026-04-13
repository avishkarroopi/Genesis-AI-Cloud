"""
GENESIS License Client
Determines user plan, checks validity, and interfaces with Feature Gate and Limits.
All DB access goes through core.db_pool (ThreadedConnectionPool).
"""
import logging
import time
from typing import Dict, Any

from core.license.feature_gate import get_feature_map
from core.license.usage_limit_engine import PLAN_LIMITS, get_usage_report

logger = logging.getLogger(__name__)


def get_user_plan(user_id: str) -> str:
    """
    Retrieve the user's current subscription plan.
    Defaults to 'lite' if not found or system is offline.
    In production this reads from PostgreSQL via db_pool.
    """
    from core.db_pool import get_connection, release_connection
    default_plan = "lite"
    conn = get_connection()
    if not conn:
        return default_plan

    try:
        with conn.cursor() as cur:
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    user_id VARCHAR(255) PRIMARY KEY,
                    plan VARCHAR(50) NOT NULL DEFAULT 'lite',
                    updated_at BIGINT
                )
            """)
            conn.commit()
            cur.execute("SELECT plan FROM user_subscriptions WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            return row[0].lower() if row else default_plan
    except Exception as e:
        logger.error(f"[LICENSE] Error fetching plan: {e}")
        return default_plan
    finally:
        release_connection(conn)


def get_full_license_status(user_id: str) -> Dict[str, Any]:
    """
    Return a comprehensive payload for the frontend detailing:
    plan, features, and usage limits.
    """
    plan = get_user_plan(user_id)
    features = get_feature_map(plan)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["lite"])
    usage_report = get_usage_report(user_id, plan)

    return {
        "user_id": user_id,
        "plan": plan,
        "status": "active",
        "features": features,
        "limits": limits,
        "usage": usage_report,
    }


def upgrade_user_plan(user_id: str, new_plan: str) -> bool:
    """Sets a new plan for the user (used by payments or referral rewards)."""
    from core.db_pool import get_connection, release_connection
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_subscriptions (user_id, plan, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET plan = %s, updated_at = %s
            """, (user_id, new_plan, int(time.time()), new_plan, int(time.time())))
        conn.commit()
        logger.info(f"[LICENSE] Upgraded user {user_id} to plan {new_plan}")
        return True
    except Exception as e:
        logger.error(f"[LICENSE] Error upgrading plan: {e}")
        return False
    finally:
        release_connection(conn)
