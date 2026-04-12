# automation_bridge.py
from body import screen_control  # type: ignore
from body import robot_control  # type: ignore
import meet_control  # type: ignore
import whatsapp_control  # type: ignore
from core import automation_engine  # type: ignore
import tools.tool_manager as tool_manager
from core.ai_router import route_ai_request  # type: ignore

def execute_tool(module_name, func_name, *args, **kwargs):
    """
    Central router for executing GENESIS tools safely.
    It maps a module and function name to the actual imported python module.
    Runs non-blocking (the underlying functions handle their own threads).
    """
    modules = {
        "screen_control": screen_control,
        "robot_control": robot_control,
        "meet_control": meet_control,
        "whatsapp_control": whatsapp_control,
        "automation_engine": automation_engine,
        "tool_manager": tool_manager
    }

    if module_name not in modules:
        print(f"[BRIDGE] Error: Unknown module '{module_name}'", flush=True)
        return f"Error: Module {module_name} not found."

    mod = modules[module_name]
    if not hasattr(mod, func_name):
        print(f"[BRIDGE] Error: Function '{func_name}' not found in {module_name}", flush=True)
        return f"Error: Function {func_name} not found."

    try:
        func = getattr(mod, func_name)
        result = func(*args, **kwargs)
        print(f"[BRIDGE] Executed '{module_name}.{func_name}' successfully.", flush=True)
        return result
    except Exception as e:
        print(f"[BRIDGE] Execution failed: {e}", flush=True)
        return f"Execution error: {e}"

def generate_ai_response(prompt, owner_address="Avishkar"):
    """Wrapper to cleanly call AI router from other subsystems."""
    return route_ai_request(prompt, owner_address)
