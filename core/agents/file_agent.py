import logging
from core.event_bus import get_event_bus, Event
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

async def handle_file_read(event: Event):
    path = event.data.get("path")
    registry = get_tool_registry()
    try:
        result = await registry.execute_tool("read_file", path=path)
        bus = get_event_bus()
        await bus.publish("FileReadCompleted", "file_agent", data={"path": path, "content": result})
    except Exception as e:
        logger.error(f"File read failed: {e}")

async def handle_file_write(event: Event):
    path = event.data.get("path")
    content = event.data.get("content")
    registry = get_tool_registry()
    try:
        result = await registry.execute_tool("write_file", path=path, content=content)
        bus = get_event_bus()
        await bus.publish("FileWriteCompleted", "file_agent", data={"path": path, "result": result})
    except Exception as e:
         logger.error(f"File write failed: {e}")

def start_file_agent():
    bus = get_event_bus()
    bus.subscribe("FileReadRequested", handle_file_read)
    bus.subscribe("FileWriteRequested", handle_file_write)
    logger.info("File agent started")
