import requests  # type: ignore
import json
import threading
import atexit
from concurrent.futures import ThreadPoolExecutor
from core.config import N8N_URL, N8N_KEY, N8N_WEBHOOK  # type: ignore

_automation_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Automation")
atexit.register(_automation_pool.shutdown, wait=False)

def trigger_webhook(data=None, use_celery=False):
    """Trigger the default n8n webhook with payload.
    Set use_celery=True to dispatch via Celery worker instead of ThreadPool."""
    if not N8N_WEBHOOK:
        print("[AUTOMATION] n8n Webhook not configured.", flush=True)
        return "Webhook not configured."

    payload = data or {}

    # Optional Celery dispatch
    if use_celery:
        try:
            from core.queue.celery_app import run_automation_task
            run_automation_task.delay(payload)
            return "Automation dispatched to Celery worker."
        except Exception as e:
            print(f"[AUTOMATION] Celery dispatch failed, using ThreadPool: {e}", flush=True)

    headers = {"Content-Type": "application/json"}
    if N8N_KEY:
        headers["Authorization"] = f"Bearer {N8N_KEY}"

    def _request():
        print(f"[AUTOMATION] Triggering webhook...", flush=True)
        try:
            response = requests.post(N8N_WEBHOOK, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"[AUTOMATION] Webhook Success: {response.text}", flush=True)
            else:
                print(f"[AUTOMATION] Webhook Failed {response.status_code}: {response.text}", flush=True)
        except Exception as e:
            print(f"[AUTOMATION] Webhook error: {e}", flush=True)

    _automation_pool.submit(_request)

    try:
        from core.telemetry.posthog_client import track_event
        track_event("automation_triggered", {"webhook": N8N_WEBHOOK})
    except Exception:
        pass

    return "Triggering webhook."

def run_workflow(name, data=None):
    """Triggers a workflow by name via the webhook (using 'workflow' param)."""
    payload = {"workflow": name, "data": data or {}}
    return trigger_webhook(payload)

def get_workflows():
    """Stub to fetch all workflows via the n8n REST API (if available)."""
    # This requires full REST API access, not just webhook
    print(f"[AUTOMATION] Fetching workflows from {N8N_URL}/api/v1/workflows...", flush=True)
    return ["workflow_1", "workflow_2"]

def execute_action(action, target, data=None):
    """Generic action executor (similar to legacy send_n8n_command)."""
    payload = {"action": action, "target": target, "data": data or {}}
    return trigger_webhook(payload)

def send_n8n_command(action, target, data=None):
    """Legacy wrapper for backward compatibility."""
    return execute_action(action, target, data)
