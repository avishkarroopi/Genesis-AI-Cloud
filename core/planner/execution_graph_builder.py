import logging
from core.event_bus import get_event_bus, EventPriority

logger = logging.getLogger(__name__)

class ExecutionGraphBuilder:
    def __init__(self):
        bus = get_event_bus()
        bus.subscribe("decompose_task", self._build_graph)

    async def _build_graph(self, event):
        goal = event.data.get("goal", "")
        # Create execution graph - stub logic for expanding into nodes
        tasks = [f"Phase 1: Research {goal[:10]}", f"Phase 2: Analyze {goal[:10]}", f"Phase 3: Compile Report"]
        
        bus = get_event_bus()
        logger.info(f"ExecutionGraphBuilder decomposed goal into {len(tasks)} tasks.")
        
        # Dispatch tasks asynchronously
        for task in tasks:
            await bus.publish("plan_created", "execution_graph_builder", data={"goal": task, "parent_goal": goal}, priority=EventPriority.NORMAL)

def initialize_module():
    logger.info("Initializing Task Planning Engine")
    builder = ExecutionGraphBuilder()
