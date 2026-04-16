import logging
from core.event_bus import get_event_bus, Event
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

async def handle_browser_open(event: Event):
    url = event.data.get("url")
    registry = get_tool_registry()
    try:
        result = await registry.execute_tool("browser_open", url=url)
        bus = get_event_bus()
        await bus.publish("BrowserOpenCompleted", "browser_automation_agent", data={"result": result})
    except Exception as e:
        logger.error(f"Browser action failed: {e}")
        
def start_browser_automation_agent():
    bus = get_event_bus()
    bus.subscribe("BrowserActionRequested", handle_browser_open)
    logger.info("Browser automation agent started")
