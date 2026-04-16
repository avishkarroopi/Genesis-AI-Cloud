import logging
from core.event_bus import get_event_bus, Event
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

async def handle_code_execute(event: Event):
    path = event.data.get("path")
    registry = get_tool_registry()
    try:
        result = await registry.execute_tool("run_script", path=path)
        bus = get_event_bus()
        await bus.publish("CodeExecutionCompleted", "code_execution_agent", data={"result": result})
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        
def start_code_execution_agent():
    bus = get_event_bus()
    bus.subscribe("CodeExecutionRequested", handle_code_execute)
    logger.info("Code execution agent started")
