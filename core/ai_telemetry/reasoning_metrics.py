"""
GENESIS Telemetry — Specific Metric Trackers
"""
from core.ai_telemetry.inference_monitor import get_inference_monitor

def track_reasoning(intent: str, latency_ms: int, tokens_used: int = 0, success: bool = True):
    monitor = get_inference_monitor()
    monitor.record_event("reasoning", {
        "intent": intent,
        "latency_ms": latency_ms,
        "tokens_used": tokens_used,
        "success": success
    })

def track_automation(webhook_id: str, success: bool):
    monitor = get_inference_monitor()
    monitor.record_event("automation", {
        "webhook_id": webhook_id,
        "success": success
    })

def track_agent_task(agent_name: str, task_name: str, success: bool):
    monitor = get_inference_monitor()
    monitor.record_event("agent", {
        "agent_name": agent_name,
        "task_name": task_name,
        "success": success
    })

def track_api_error(module: str, error_msg: str):
    monitor = get_inference_monitor()
    monitor.record_event("error", {
        "module": module,
        "error_msg": str(error_msg)[:100]
    })
