"""
Integration Manager for Self-Development.
Validates dependencies and integrates approved upgrades without modifying core system files.
"""

import os
import ast
import json
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

REGISTRY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "shared", "upgrade_registry.json")

def validate_dependencies(code: str) -> Tuple[bool, str]:
    """Validates that all imports in the generated code are available."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error during dependency check: {e}"
        
    modules_to_check = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                modules_to_check.append(n.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules_to_check.append(node.module.split('.')[0])
                
    # Very basic runtime import check (ignoring relative imports for this safe check)
    failed = []
    for mod in set(modules_to_check):
        # We don't want to actually load arbitrary things, just check existence
        # For builtin/standard we can rely on importlib.util
        if mod in ["core", "shared", "security"]: 
            continue # Local modules are fine
            
        import importlib.util
        try:
            if not importlib.util.find_spec(mod):
                failed.append(mod)
        except Exception:
            failed.append(mod)
            
    if failed:
        return False, f"Missing dependencies: {', '.join(failed)}"
        
    return True, "Dependencies validated."

def generate_integration_patch(upgrade_plan: Dict[str, Any]) -> str:
    """Generates a manual integration report for the user to review and approve."""
    report = f"=== UPGRADE INTEGRATION INSTRUCTIONS ===\n"
    report += f"Name: {upgrade_plan.get('module_name')}\n"
    report += f"Type: {upgrade_plan.get('type')}\n\n"
    report += f"Please review the core files required. GENESIS will not automatically modify them.\n"
    report += f"To enable this module, you must manually run or place the code into the system.\n"
    
    if upgrade_plan.get("target_path"):
        report += f"Target File: {upgrade_plan.get('target_path')}\n"
        
    return report

def register_module(upgrade_id: str, name: str, code: str, status: str = "approved") -> bool:
    """
    Registers an approved module into the persistent registry to ensure 
    GENESIS keeps track of what it built.
    """
    try:
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {"version": 1, "upgrades": []}
            
        upgrade = {
            "id": upgrade_id,
            "name": name,
            "status": status,
            "date": datetime.now().isoformat(),
            "code_length": len(code)
        }
        
        # Check if already exists
        existing = [u for u in data["upgrades"] if u.get("id") == upgrade_id]
        if existing:
            existing[0].update(upgrade)
        else:
            data["upgrades"].append(upgrade)
            
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"[SELF-DEV] Upgrade {upgrade_id} registered successfully.")
        
        bus = get_event_bus()
        if bus:
            event_name = "UPGRADE_APPROVED" if status == "approved" else "UPGRADE_REJECTED"
            try:
                bus.publish_sync(event_name, "integration_manager", upgrade)
            except Exception as e:
                logger.error(f"[SELF-DEV] Failed to publish event: {e}")
                
        return True
    except Exception as e:
        logger.error(f"[SELF-DEV] Failed to register upgrade: {e}")
        return False
