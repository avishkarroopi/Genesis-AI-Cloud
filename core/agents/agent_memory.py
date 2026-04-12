"""
Agent Memory (Layer 2 - Intelligence)
Short-term scratchpad memory for agents to share state between tasks.
"""

class AgentMemory:
    def __init__(self):
        self._memory = {}
        
    def set(self, key, value):
        self._memory[key] = value
        
    def get(self, key, default=None):
        return self._memory.get(key, default)
        
    def clear(self):
        self._memory.clear()

agent_memory = AgentMemory()

def get_agent_memory() -> AgentMemory:
    return agent_memory
