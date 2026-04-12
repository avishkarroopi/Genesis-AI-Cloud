from .task_manager import manager, TaskStep
from .step_executor import execute_step
import json
import re

def _extract_json(text: str) -> dict:
    """Robustly extract JSON from mixed text/markdown output."""
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    raise ValueError("Failed to extract valid JSON.")

def create_plan(goal: str, retries: int = 2) -> dict:
    """Analyze the goal and synthesize a multi-step structured plan using the AI router, with retries."""
    from core.automation_bridge import generate_ai_response # type: ignore
    
    prompt = (
        f"Create a strict JSON plan with the exact key 'steps' containing a list of objects "
        f"for the following goal: {goal}\n"
        f"Each step must be an object with keys: 'id' (integer), 'description' (string).\n"
        f"Respond ONLY with the raw JSON block. Do not use markdown backticks or preamble."
    )
    
    for attempt in range(retries):
        try:
            print("[PLANNER] Creating plan...", flush=True)
            response_text = generate_ai_response(prompt, owner_address="System")
            return _extract_json(response_text)
        except Exception as e:
            print(f"[PLANNER] Plan creation failed (attempt {attempt+1}): {e}", flush=True)
    
    return {"steps": [{"id": 1, "description": "Execute standard request directly."}]}

def create_task_graph(goal: str, retries: int = 2) -> dict:
    """Create a structured task graph with retries."""
    from core.automation_bridge import generate_ai_response # type: ignore
    
    prompt = (
        f"Create a strict JSON graph plan with exact key 'nodes' containing a list of objects "
        f"for goal: {goal}\n"
        f"Each node MUST have keys: 'id' (int), 'description' (string), 'dependencies' (list of int IDs).\n"
        f"Optional key: 'tool' (string).\n"
        f"Respond ONLY with the raw JSON block. Do not use markdown backticks."
    )
    
    for attempt in range(retries):
        try:
            print("[PLANNER] Creating task graph...", flush=True)
            response_text = generate_ai_response(prompt, owner_address="System")
            return _extract_json(response_text)
        except Exception as e:
            print(f"[PLANNER] Task graph creation failed (attempt {attempt+1}): {e}", flush=True)
            
    return {"nodes": [{"id": 1, "description": "Execute safe fallback.", "dependencies": []}]}

def create_steps(goal: str):
    """Generates the plan and registers it with the task manager."""
    plan_dict = create_plan(goal)
    steps = plan_dict.get("steps", [])
    
    task_steps = []
    for step_data in steps:
        ts = TaskStep(
            id=step_data.get("id", 1),
            description=step_data.get("description", str(step_data)),
            action="execute"
        )
        task_steps.append(ts)
        
    manager.create_task(goal, task_steps)
    return manager.get_task_status()

def execute_plan() -> str:
    """Executes the active plan synchronously."""
    task = manager.get_task_status()
    if not task:
        return "No active task available."
        
    output_log = []
    
    while True:
        step = manager.get_next_step()
        if not step:
            break
            
        res = execute_step(step)
        output_log.append(f"Step {step.id}: {res}")
        
        if step.status == "failed":
            manager.cancel_task(f"Step {step.id} failed.")
            return "\n".join(output_log) + "\nExecution partially aborted due to failure."
            
    return "\n".join(output_log)
