"""
GENESIS Referral Engine
Tracks referral growth loops and automates reward tier upgrades.
"""
import os
import logging

logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────

# Referral tiers trigger automatic upgrades
REWARD_TIERS = {
    5: "core",
    10: "gold",
    50: "platinum"
}


def _get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(db_url)
    except Exception as e:
        logger.error(f"[REFERRAL] DB connection failed: {e}")
        return None


def _ensure_tables(conn):
    with conn.cursor() as cur:
        # Table to track who referred whom
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_tracking (
                new_user_id VARCHAR(255) PRIMARY KEY,
                referrer_id VARCHAR(255) NOT NULL,
                timestamp BIGINT NOT NULL
            )
        """)
        # Table to track total successful referrals per user
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_counts (
                user_id VARCHAR(255) PRIMARY KEY,
                total_referrals INTEGER DEFAULT 0
            )
        """)
    conn.commit()


def process_referral(new_user_id: str, referrer_id: str) -> bool:
    """
    Registers a new signup under a referrer.
    Updates counts and automatically upgrades the referrer's plan if a tier is hit.
    """
    if new_user_id == referrer_id:
        return False

    conn = _get_conn()
    if not conn:
        return False

    try:
        _ensure_tables(conn)
        import time
        ts = int(time.time())

        with conn.cursor() as cur:
            # 1. Register the referral relation
            cur.execute("""
                INSERT INTO referral_tracking (new_user_id, referrer_id, timestamp)
                VALUES (%s, %s, %s)
                ON CONFLICT (new_user_id) DO NOTHING
                RETURNING new_user_id
            """, (new_user_id, referrer_id, ts))
            
            # If the user was already referred, stop
            if not cur.fetchone():
                return False

            # 2. Increment referrer's count
            cur.execute("""
                INSERT INTO referral_counts (user_id, total_referrals)
                VALUES (%s, 1)
                ON CONFLICT (user_id)
                DO UPDATE SET total_referrals = referral_counts.total_referrals + 1
                RETURNING total_referrals
            """, (referrer_id,))
            
            new_total = cur.fetchone()[0]
        
        conn.commit()
        logger.info(f"[REFERRAL] User {new_user_id} signed up under {referrer_id} (Total: {new_total})")

        # 3. Check for automatic reward upgrades
        if new_total in REWARD_TIERS:
            new_plan = REWARD_TIERS[new_total]
            try:
                from core.license.license_client import upgrade_user_plan
                success = upgrade_user_plan(referrer_id, new_plan)
                if success:
                    logger.info(f"[REFERRAL REWARD] User {referrer_id} upgraded to {new_plan}")
            except Exception as e:
                logger.error(f"[REFERRAL REWARD] Upgrade failed: {e}")

        return True

    except Exception as e:
        logger.error(f"[REFERRAL] Error processing referral: {e}")
        return False
    finally:
        conn.close()


def get_referral_stats(user_id: str) -> dict:
    """Return total referrals and distance to next reward tier."""
    conn = _get_conn()
    if not conn:
        return {"total": 0, "next_tier": 5, "link": f"https://genesis.ai/signup?ref={user_id}"}
        
    try:
        _ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT total_referrals FROM referral_counts WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            total = row[0] if row else 0
            
            target = 50
            for tier in sorted(REWARD_TIERS.keys()):
                if total < tier:
                    target = tier
                    break
                    
            return {
                "total": total,
                "next_tier": target,
                "link": f"https://genesis.ai/signup?ref={user_id}"
            }
    finally:
        conn.close()
