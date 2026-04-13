import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .auth import verify_firebase_token
from .voice_ws import router as voice_router

import sentry_sdk
from shared.logtail_logger import cloud_logger

# ── Sentry Error Monitoring Init ──────────────────────────────────────────────
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        cloud_logger.info("Sentry monitoring initialized", extra={"category": "system"})
    except Exception as e:
        cloud_logger.error(f"Sentry init failed: {e}", extra={"category": "system_errors"})

app = FastAPI(title="GENESIS Cloud API")

# ── Rate Limiting ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "https://genesis.ai").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

# ── Health / Status ───────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "GENESIS Cloud API Online", "cloud_mode": os.environ.get("CLOUD_MODE", "false")}

@app.get("/api/system/health")
async def system_health():
    """Deep structural diagnostic ping checking Cloud Platform Readiness."""
    import os
    
    # Check DB
    db_ok = False
    try:
        from core.db_pool import get_connection, release_connection
        conn = get_connection()
        if conn:
            db_ok = True
            release_connection(conn)
    except Exception:
        pass

    # Check Redis
    redis_ok = False
    try:
        from server.session_manager import get_redis_client
        r = get_redis_client()
        if r and r.ping():
            redis_ok = True
    except Exception:
        pass

    # Basic presence checks for APIs
    groq_ok = bool(os.environ.get("GROQ_API_KEY"))
    or_ok = bool(os.environ.get("OPENROUTER_API_KEY"))
    n8n_ok = bool(os.environ.get("N8N_WEBHOOK"))
    
    # Intelligence Bus Check
    try:
        from core.intelligence_bus import get_intelligence_bus
        bus = get_intelligence_bus()
        bus_ok = bus is not None
    except Exception:
        bus_ok = False

    return {
        "status": "healthy" if db_ok and redis_ok and groq_ok and bus_ok else "degraded",
        "services": {
            "postgresql": "connected" if db_ok else "failed",
            "redis": "connected" if redis_ok else "failed",
            "groq_api": "configured" if groq_ok else "missing",
            "openrouter_api": "configured" if or_ok else "missing",
            "n8n_webhook": "configured" if n8n_ok else "missing",
            "intelligence_bus": "operational" if bus_ok else "failed"
        }
    }

@app.get("/api/system/metrics")
async def system_metrics():
    """Return aggregated AI telemetry metrics from PostgreSQL."""
    from core.db_pool import get_connection, release_connection
    conn = get_connection()
    if not conn:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, count(*) as events, sum(count) as total_interactions
                FROM ai_telemetry
                GROUP BY category
            """)
            rows = cur.fetchall()
            return {"metrics": [{"category": r[0], "events": r[1], "total": r[2]} for r in rows]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        release_connection(conn)

# ── License Endpoint ──────────────────────────────────────────────────────────
@app.get("/api/license/verify")
async def license_verify(user: dict = Depends(verify_firebase_token)):
    """Return the full license status for the authenticated user."""
    from core.license.license_client import get_full_license_status
    return get_full_license_status(user["uid"])

# ── Referral Endpoints ────────────────────────────────────────────────────────
@app.post("/api/referral/register")
async def referral_register(request: Request, user: dict = Depends(verify_firebase_token)):
    """
    Register a new referral.
    Expected JSON body: {"referral_code": "<referrer_user_id>"}
    """
    body = await request.json()
    referrer_id = body.get("referral_code", "")
    if not referrer_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="referral_code is required")
    try:
        from core.referral.referral_engine import record_referral
        result = record_referral(referrer_id=referrer_id, new_user_id=user["uid"])
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/referral/status")
async def referral_status(user: dict = Depends(verify_firebase_token)):
    """Return referral count and reward tier for the authenticated user."""
    try:
        from core.referral.referral_engine import get_referral_stats
        return get_referral_stats(user["uid"])
    except Exception as e:
        return {"error": str(e)}
