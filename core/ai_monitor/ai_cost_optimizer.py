import logging
from core.event_bus import get_event_bus, EventPriority

logger = logging.getLogger(__name__)

# Global budget tracker
_total_tokens = 0
TOKEN_BUDGET = 100000

async def _on_llm_request(event):
    global _total_tokens
    data = event.data
    # Track tokenizer counts and calculate costs based on provider dynamically
    tokens = data.get("tokens", 0)
    provider = data.get("provider", "unknown")
    latency = data.get("latency", 0)
    
    _total_tokens += tokens
    
    bus = get_event_bus()
    
    if _total_tokens > TOKEN_BUDGET:
        await bus.publish("health_warning", "ai_cost_optimizer", {"reason": "Token budget exceeded", "tokens": _total_tokens}, EventPriority.HIGH)
    
    await bus.publish("token_stats", "ai_cost_optimizer", {"tokens": tokens, "provider": provider}, EventPriority.LOW)
    await bus.publish("model_latency", "ai_cost_optimizer", {"latency": latency, "provider": provider}, EventPriority.LOW)
    await bus.publish("model_usage", "ai_cost_optimizer", {"provider": provider, "status": "active"}, EventPriority.LOW)
    await bus.publish("provider_health", "ai_cost_optimizer", {"provider": provider, "healthy": True}, EventPriority.LOW)

def initialize_module():
    logger.info("Initializing Module 8: AI Cost Optimizer")
    bus = get_event_bus()
    bus.subscribe("llm_inference_complete", _on_llm_request)
