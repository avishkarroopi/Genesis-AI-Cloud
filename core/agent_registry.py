# Event-driven agent layer
import uuid
import time
import threading
from core.event_bus import get_event_bus

def planner_agent(task: str) -> str:
    try:
        from core.planner.planner import create_task_graph
        from core.planner.step_executor import execute_graph
        graph = create_task_graph(task)
        
        tool_chain = [n.get('tool') for n in graph.get('nodes', []) if n.get('tool')]
        if tool_chain:
            from core.tool_registry import execute_tool_chain
            chain_results = execute_tool_chain(tool_chain)
            return "\n".join(str(r) for r in chain_results)
            
        return execute_graph(graph)
    except Exception as e:
        return f"Planner partial failure, recovered: {e}"

def research_agent(task: str) -> str:
    try:
        from core.research.research_engine import search_and_summarize
        res = search_and_summarize(task)
        return res if res else f"Research agent found no data for {task}"
    except Exception as e:
        return f"Research agent recovered failure: {e}"

def tool_agent(task: str) -> str:
    try:
        from core import genesis_tools
        res = genesis_tools.check_and_execute_tool(task)
        return str(res) if res else "Tool execution produced no result."
    except Exception as e:
        return f"Tool agent recovered failure: {e}"

def memory_agent(task: str) -> str:
    try:
        from core.memory.memory_search import search_memory_safe
        mem = search_memory_safe(task, n_results=3)
        return str(mem)
    except Exception as e:
        return f"Memory agent recovered failure: {e}"

AGENTS = {
    "planner": planner_agent,
    "research": research_agent,
    "tools": tool_agent,
    "memory": memory_agent
}

# Subscribed background worker that processes all agent tasks asynchronously
def _agent_worker_listener(event):
    data = event.data
    agent_type = data.get("agent_type")
    task_id = data.get("task_id")
    task_str = data.get("task")
    bus = get_event_bus()

    if agent_type in AGENTS:
        try:
            res = AGENTS[agent_type](task_str)
            bus.publish_sync("TASK_COMPLETE", "agent_worker", {"task_id": task_id, "result": res})
        except Exception as e:
            bus.publish_sync("TASK_FAILED", "agent_worker", {"task_id": task_id, "error": str(e)})

# Ensure listener is attached
try:
    _bus = get_event_bus()
    _bus.subscribe("TASK_ASSIGNED", _agent_worker_listener)
except Exception:
    pass

def delegate_agent_task(agent_type: str, task: str) -> str:
    """Delegates a task using Event-Driven pub/sub pattern."""
    if agent_type not in AGENTS:
        raise ValueError("Unknown agent")
        
    bus = get_event_bus()
    task_id = str(uuid.uuid4())
    
    # We must block for outcome to keep backward compatibility with brain_chain expects,
    # but we achieve this via an event loop Future or sync wait over the bus.
    # Since we are in process_voice_input_async (a sync thread), we use thread events.
    result_container = []
    task_event = threading.Event()
    
    def on_complete(event):
        if event.data.get("task_id") == task_id:
            result_container.append(event.data.get("result", ""))
            task_event.set()
            
    def on_fail(event):
        if event.data.get("task_id") == task_id:
            result_container.append(f"Agent failed: {event.data.get('error')}")
            task_event.set()
            
    bus.subscribe("TASK_COMPLETE", on_complete)
    bus.subscribe("TASK_FAILED", on_fail)
    
    bus.publish_sync("TASK_ASSIGNED", "delegate", {
        "agent_type": agent_type, 
        "task_id": task_id, 
        "task": task
    })
    
    # Wait for completion up to 12s
    task_event.wait(timeout=12.0)
    
    bus.unsubscribe("TASK_COMPLETE", on_complete)
    bus.unsubscribe("TASK_FAILED", on_fail)
    
    if not result_container:
        return f"Agent {agent_type} timed out waiting for event response."
        
    return result_container[0]
