from core.planner.planner import create_plan
from core.planner.step_executor import execute_step
from core.planner.task_manager import TaskStep

MAX_STEPS = 6

def run_agent(goal):
    print(f"[AGENT] Running autonomous loop for: {goal}", flush=True)
    plan_dict = create_plan(goal)
    steps = plan_dict.get("steps", [])
    
    if len(steps) > MAX_STEPS:
        steps = steps[:MAX_STEPS]

    output = ["Task execution summary:\n"]
    
    for idx, step_data in enumerate(steps):
        step_obj = TaskStep(
            id=step_data.get("id", idx + 1),
            description=step_data.get("description", str(step_data)),
            action="execute"
        )
        
        output.append(f"Step {step_obj.id}:\n{step_obj.description}")
        print(f"[AGENT] Executing Step {step_obj.id}: {step_obj.description}", flush=True)
        
        res = execute_step(step_obj)
        output.append(f"Output:\n{res}\n")
        
    output.append("Final result:\nTask completed successfully.")
    return "\n".join(output)
