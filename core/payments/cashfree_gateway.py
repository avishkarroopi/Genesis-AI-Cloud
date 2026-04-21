"""
GENESIS Cashfree Payment Gateway.
Handles order creation, webhook verification, and subscription management.
Uses Cashfree Production API.
"""

import os
import hmac
import hashlib
import logging
import time
import json
import requests

logger = logging.getLogger(__name__)


def _get_credentials():
    """Read Cashfree credentials from environment."""
    return {
        "app_id": os.environ.get("CASHFREE_APP_ID", ""),
        "secret_key": os.environ.get("CASHFREE_SECRET_KEY", ""),
    }


# ── Order Creation ────────────────────────────────────────────────────────────

def create_order(order_id: str, amount: float, customer: dict) -> dict:
    """Create a Cashfree payment order.

    Args:
        order_id: Unique order identifier.
        amount: Payment amount in INR.
        customer: Dict with keys: customer_id, customer_name, customer_email, customer_phone.

    Returns:
        Cashfree API response dict or error dict.
    """
    creds = _get_credentials()
    if not creds["app_id"] or not creds["secret_key"]:
        return {"error": "Cashfree credentials not configured"}

    url = "https://api.cashfree.com/pg/orders"
    headers = {
        "Content-Type": "application/json",
        "x-api-version": "2023-08-01",
        "x-client-id": creds["app_id"],
        "x-client-secret": creds["secret_key"],
    }
    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": customer.get("customer_id", ""),
            "customer_name": customer.get("customer_name", ""),
            "customer_email": customer.get("customer_email", ""),
            "customer_phone": customer.get("customer_phone", ""),
        },
        "order_meta": {
            "return_url": customer.get("return_url", "https://genesis-ai.vercel.app/payment/success?order_id={order_id}"),
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.info(f"[CASHFREE] Order created: {order_id}")
        return data
    except Exception as e:
        logger.error(f"[CASHFREE] Order creation failed: {e}")
        return {"error": str(e)}


# ── Webhook Signature Verification ────────────────────────────────────────────

def verify_webhook_signature(raw_body: bytes, timestamp: str, signature: str) -> bool:
    """Verify the Cashfree webhook signature using HMAC-SHA256.

    Cashfree sends:
      x-webhook-timestamp: <timestamp>
      x-webhook-signature: <signature>
    Signature = base64(HMAC-SHA256(timestamp + raw_body, secret_key))
    """
    creds = _get_credentials()
    if not creds["secret_key"]:
        logger.warning("[CASHFREE] Cannot verify webhook — secret key missing")
        return False

    try:
        import base64
        sign_payload = timestamp.encode("utf-8") + raw_body
        computed = hmac.new(
            creds["secret_key"].encode("utf-8"),
            sign_payload,
            hashlib.sha256
        ).digest()
        computed_b64 = base64.b64encode(computed).decode("utf-8")
        return hmac.compare_digest(computed_b64, signature)
    except Exception as e:
        logger.error(f"[CASHFREE] Signature verification error: {e}")
        return False


# ── Webhook Event Processing ─────────────────────────────────────────────────

def process_webhook(event_type: str, data: dict) -> dict:
    """Process a Cashfree webhook event.

    Handles: PAYMENT_SUCCESS, PAYMENT_FAILED, REFUND.
    Returns a status dict.
    """
    order_id = data.get("order", {}).get("order_id", "unknown")
    amount = data.get("order", {}).get("order_amount", 0)
    customer_id = data.get("customer_details", {}).get("customer_id", "")

    result = {
        "event": event_type,
        "order_id": order_id,
        "amount": amount,
        "customer_id": customer_id,
        "processed": True,
    }

    if event_type == "PAYMENT_SUCCESS_WEBHOOK":
        logger.info(f"[CASHFREE] Payment success: {order_id} — ₹{amount}")
        _update_subscription(customer_id, order_id, amount)
        _track_payment_event("payment_completed", result)

    elif event_type == "PAYMENT_FAILED_WEBHOOK":
        logger.warning(f"[CASHFREE] Payment failed: {order_id}")
        _track_payment_event("payment_failed", result)

    elif event_type == "REFUND_WEBHOOK":
        logger.info(f"[CASHFREE] Refund processed: {order_id}")
        _track_payment_event("payment_refunded", result)

    else:
        logger.info(f"[CASHFREE] Unhandled event type: {event_type}")
        result["processed"] = False

    return result


def _update_subscription(customer_id: str, order_id: str, amount: float):
    """Update user subscription status in the database after successful payment."""
    try:
        from core.db_pool import get_connection, release_connection
        conn = get_connection()
        if not conn:
            logger.warning("[CASHFREE] DB connection unavailable for subscription update")
            return

        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    customer_id VARCHAR(255) PRIMARY KEY,
                    order_id VARCHAR(255),
                    amount NUMERIC,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                INSERT INTO user_subscriptions (customer_id, order_id, amount, status, updated_at)
                VALUES (%s, %s, %s, 'active', NOW())
                ON CONFLICT (customer_id)
                DO UPDATE SET order_id = EXCLUDED.order_id,
                              amount = EXCLUDED.amount,
                              status = 'active',
                              updated_at = NOW()
            """, (customer_id, order_id, amount))
        conn.commit()
        release_connection(conn)
        logger.info(f"[CASHFREE] Subscription updated for {customer_id}")
    except Exception as e:
        logger.error(f"[CASHFREE] Subscription update failed: {e}")


def _track_payment_event(event_name: str, data: dict):
    """Track payment event in PostHog."""
    try:
        from core.telemetry.posthog_client import track_event
        track_event(event_name, data, distinct_id=data.get("customer_id", "genesis_system"))
    except Exception:
        pass
