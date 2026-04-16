import logging
from core.event_bus import get_event_bus, Event
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

async def handle_research_request(event: Event):
    query = event.data.get("query")
    if not query:
        return
    registry = get_tool_registry()
    try:
        result = await registry.execute_tool("web_search", query=query)
        bus = get_event_bus()
        await bus.publish("ResearchCompleted", "web_research_agent", data={"query": query, "result": result})
    except Exception as e:
        logger.error(f"Research failed: {e}")
        bus = get_event_bus()
        await bus.publish("ResearchFailed", "web_research_agent", data={"query": query, "error": str(e)})

def start_web_research_agent():
    bus = get_event_bus()
    bus.subscribe("ResearchRequested", handle_research_request)
    logger.info("Web research agent started")
