from .task_manager import manager
from core.automation_bridge import generate_ai_response, execute_tool # type: ignore
import re
import ast

def execute_step(step) -> str:
    """Execute a single step by relying on the internal routing system."""
    import security.safe_mode as safe_mode
    if safe_mode.is_safe_mode_enabled():
        pass # Optional hook to log safe mode check during step execution
        
    step.status = "running"
    
    # Send a prompt to the AI to execute the specific tool mapping
    instruction_prompt = f"Execute the following step by calling a tool if necessary. Be as concise as possible:\nStep: {step.description}"
    
    print(f"[STEP_EXECUTOR] Running Step {step.id}: {step.description}", flush=True)
    
    try:
        # Route to AI and get tools executed organically via the established bridge.
        response = generate_ai_response(instruction_prompt, owner_address="System")
        
        # In reality, brain_chain.py handles tool extraction, but because planner operates 
        # below the direct vocal user input level, we extract tool logic here to be safe and autonomous.
        tool_results = []
        if "[[TOOL:" in response:
            tool_tags = re.findall(r"\[\[TOOL:.*?\]\]", response)
            for tag in tool_tags:
                content = tag.replace("[[TOOL:", "").replace("]]", "")
                module_name, func_expr = content.split(".", 1)
                func_name = func_expr.split("(")[0]
                args_str = func_expr[len(func_name)+1:-1]
                
                args = []
                kwargs = {}
                if args_str.strip():
                    try:
                        parsed = ast.literal_eval(f"({args_str},)")
                        args = list(parsed)
                    except (ValueError, SyntaxError):
                        print(f"[STEP_EXECUTOR] Safe arg parse failed for: {args_str}", flush=True)
                        args = [args_str]
                    
                print(f"[STEP_EXECUTOR] Executing Sub-Tool: {module_name}.{func_name}({args})", flush=True)
                res = execute_tool(module_name, func_name, *args, **kwargs)
                res_str = str(res)
                tool_results.append(res_str)
                
                if res_str.startswith("Error:"):
                    step.status = "failed"
                    step.result = res_str
                    return res_str

        final_msg = " | ".join(tool_results) if tool_results else response
        step.status = "done"
        step.result = final_msg
        return final_msg
        
    except Exception as e:
        step.status = "failed"
        step.result = f"Failed to execute step: {str(e)}"
        print(f"[STEP_EXECUTOR] {step.result}", flush=True)
        return step.result


def _retry_step_with_context(step, original_error: str) -> str:
    """Re-plan a failed step with failure context (one retry)."""
    retry_prompt = (
        f"The previous attempt to execute this step failed.\n"
        f"Step: {step.description}\n"
        f"Error: {original_error}\n"
        f"Please suggest an alternative approach and execute it."
    )
    print(f"[STEP_EXECUTOR] Re-planning Step {step.id} after failure", flush=True)
    try:
        response = generate_ai_response(retry_prompt, owner_address="System")
        step.status = "done"
        step.result = f"[REPLANNED] {response}"
        return step.result
    except Exception as e:
        step.status = "failed"
        step.result = f"Re-plan also failed: {str(e)}"
        return step.result

MAX_GRAPH_STEPS = 6

def execute_graph(graph_dict: dict) -> str:
    from .task_manager import TaskStep
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    
    nodes = graph_dict.get("nodes", [])
    if len(nodes) > MAX_GRAPH_STEPS:
        nodes = nodes[:MAX_GRAPH_STEPS]

    MAX_REPLANS = 1
    replan_counts = {}

    for n in nodes:
        n['status'] = 'pending'

    results = []
    
    while True:
        progress = False
        all_done = True
        
        for node in nodes:
            if node['status'] == 'pending':
                all_done = False
                
                deps = node.get('dependencies', [])
                deps_completed = True
                deps_failed = False
                for d in deps:
                    d_node = next((x for x in nodes if x['id'] == d), None)
                    if d_node:
                        if d_node['status'] == 'failed':
                            deps_failed = True
                        elif d_node['status'] != 'completed':
                            deps_completed = False
                            
                if deps_failed:
                    node['status'] = 'failed'
                    progress = True
                elif deps_completed:
                    node['status'] = 'running'
                    step_obj = TaskStep(
                        id=node['id'],
                        description=node['description'],
                        action="execute"
                    )
                    
                    try:
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(execute_step, step_obj)
                            res = future.result(timeout=60.0)
                        
                        if step_obj.status == 'failed':
                            # Attempt re-planning once before giving up
                            replan_count = replan_counts.get(node['id'], 0)
                            if replan_count < MAX_REPLANS:
                                replan_counts[node['id']] = replan_count + 1
                                with ThreadPoolExecutor(max_workers=1) as executor:
                                    future = executor.submit(_retry_step_with_context, step_obj, res)
                                    res = future.result(timeout=60.0)
                            else:
                                res = f"{res} (MAX REPLANS {MAX_REPLANS} REACHED)"

                        node['status'] = 'completed' if step_obj.status == 'done' else 'failed'
                        node['result'] = res
                        results.append(f"Node {node['id']}: {res}")
                    except TimeoutError:
                        node['status'] = 'failed'
                        node['result'] = "Execution timed out (60s limit)."
                        results.append(f"Node {node['id']} failed: Timeout")
                    except Exception as e:
                        node['status'] = 'failed'
                        node['result'] = str(e)
                        results.append(f"Node {node['id']} failed: {e}")
                    progress = True
                    
        if all_done or not progress:
            break
            
    return "\n".join(results)
