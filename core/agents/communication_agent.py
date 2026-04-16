import logging
from core.event_bus import get_event_bus, Event
from core.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

async def handle_message_dispatch(event: Event):
    channel = event.data.get("channel") # 'email', 'telegram', 'slack'
    text = event.data.get("text")
    target = event.data.get("target") # chat_id, email addr
    
    registry = get_tool_registry()
    try:
        result = ""
        if channel == "email":
            result = await registry.execute_tool("send_email", to=target, subject="GENESIS Notification", body=text)
        elif channel == "telegram":
            result = await registry.execute_tool("send_telegram_message", chat_id=target, text=text)
        elif channel == "slack":
            result = await registry.execute_tool("send_slack_message", channel=target, text=text)
            
        bus = get_event_bus()
        await bus.publish("MessageDispatchCompleted", "communication_agent", data={"result": result})
    except Exception as e:
        logger.error(f"Communication failed: {e}")

def start_communication_agent():
    bus = get_event_bus()
    bus.subscribe("MessageDispatch", handle_message_dispatch)
    logger.info("Communication agent started")
