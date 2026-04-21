"""
GENESIS Distributed Task Queue — Celery + Redis.
Provides background task execution for agents, automation, research, and LLM reasoning.
Broker and result backend both use the existing REDIS_URL.
"""

import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# ── Celery Application ────────────────────────────────────────────────────────
_redis_url = os.environ.get("CELERY_BROKER_URL") or os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "genesis",
    broker=_redis_url,
    backend=_redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=120,
    task_time_limit=180,
    result_expires=3600,
)


# ── Reusable Tasks ────────────────────────────────────────────────────────────

@celery_app.task(name="genesis.run_agent_task", bind=True, max_retries=2)
def run_agent_task(self, agent_type: str, task_text: str) -> str:
    """Execute an agent task in a Celery worker."""
    try:
        # Ensure dotenv is loaded in the worker process
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        except ImportError:
            pass

        from core.agent_registry import AGENTS
        if agent_type not in AGENTS:
            return f"Unknown agent type: {agent_type}"
        result = AGENTS[agent_type](task_text)
        logger.info(f"[CELERY] Agent task completed: {agent_type}")
        return str(result)
    except Exception as exc:
        logger.error(f"[CELERY] Agent task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="genesis.run_automation_task", bind=True, max_retries=2)
def run_automation_task(self, payload: dict) -> str:
    """Execute an automation webhook trigger in a Celery worker."""
    try:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        except ImportError:
            pass

        from core.automation_engine import trigger_webhook
        result = trigger_webhook(payload)
        logger.info("[CELERY] Automation task completed")
        return str(result)
    except Exception as exc:
        logger.error(f"[CELERY] Automation task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="genesis.run_research_task", bind=True, max_retries=1)
def run_research_task(self, query: str) -> str:
    """Execute a research query in a Celery worker."""
    try:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        except ImportError:
            pass

        from core.research.research_engine import search_and_summarize
        result = search_and_summarize(query)
        logger.info("[CELERY] Research task completed")
        return result if result else "No results found."
    except Exception as exc:
        logger.error(f"[CELERY] Research task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="genesis.run_llm_reasoning", bind=True, max_retries=1)
def run_llm_reasoning(self, prompt: str, owner: str = "Sir") -> str:
    """Execute a heavy LLM reasoning task in a Celery worker."""
    try:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        except ImportError:
            pass

        from core.ai_router import route_ai_request
        result = route_ai_request(prompt, owner_address=owner)
        logger.info("[CELERY] LLM reasoning task completed")
        return str(result)
    except Exception as exc:
        logger.error(f"[CELERY] LLM reasoning task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)
