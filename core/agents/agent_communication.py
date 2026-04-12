"""
Agent Communication (Layer 2 - Intelligence)
Defines formats and channels for agents to communicate with each other
or pass messages to the Event Bus.
"""

try:
    from core.event_bus import get_event_bus
except ImportError:
    def get_event_bus(): return None

class AgentCommunication:
    def __init__(self):
        self.bus = get_event_bus()

    def broadcast_result(self, task_name: str, result: str):
        if self.bus:
            self.bus.publish("AGENT_TASK_COMPLETED", {"task": task_name, "result": result})

communication = AgentCommunication()

def get_communication() -> AgentCommunication:
    return communication
