"""
Core Self-Development Engine.
Responsible for analyzing requests, designing architecture, generating templates,
and driving the sandbox runner for safe validation.
"""

import os
import uuid
import logging
import json
from typing import Dict, Any, Optional

from core.event_bus import get_event_bus
from core.self_dev.sandbox_runner import run_test_module, return_test_report
from core.self_dev.integration_manager import validate_dependencies, generate_integration_patch

logger = logging.getLogger(__name__)

# Strict safety constraints
PROTECTED_FILES = [
    "brain_chain.py", "event_bus.py", "start_genesis.py",
    "system.py", "safe_mode.py", "permissions.py",
    "security_logger.py", "tool_sandbox.py"
]

class SelfDevEngine:
    def __init__(self):
        self._lock = False
        logger.info("[SELF-DEV] Self-Development Engine initialized.")
        
    def analyze_upgrade_request(self, request_text: str) -> Dict[str, Any]:
        """Analyzes a request to determine safety and scope."""
        
        # Simple heuristic safety check
        request_lower = request_text.lower()
        if any(pf.replace('.py', '') in request_lower for pf in PROTECTED_FILES):
            return {
                "safe": False, 
                "reason": "Request targets protected core files.",
                "type": "blocked"
            }
            
        if "delete" in request_lower and "core" in request_lower:
             return {
                "safe": False, 
                "reason": "Deletion of core systems is blocked.",
                "type": "blocked"
            }
            
        # Classify the type
        mod_type = "module"
        if "tool" in request_lower:
            mod_type = "tool"
        elif "agent" in request_lower:
            mod_type = "agent"
            
        return {
            "safe": True,
            "type": mod_type,
            "intent": request_text[:100]
        }

    def generate_module_template(self, name: str, module_type: str) -> str:
        """Produces a skeleton Python module that integrates with existing GENESIS architecture."""
        
        template = f'"""\nGenerated module: {name} (Type: {module_type})\nIntegrated via GENESIS Phase 8 Self-Dev Engine.\n"""\n\n'
        template += 'import logging\n'
        template += 'from core.event_bus import get_event_bus\n\n'
        template += f'logger = logging.getLogger(__name__)\n\n'
        
        if module_type == "tool":
            template += f'def {name.lower()}(param: str) -> str:\n'
            template += f'    """Tool logic for {name}."""\n'
            template += f'    logger.info("Executing tool {name}")\n'
            template += f'    return f"Executed {name} on {{param}}"\n'
        elif module_type == "agent":
            template += f'def {name.lower()}_agent(task: str) -> str:\n'
            template += f'    """Agent delegator logic for {name}."""\n'
            template += f'    logger.info("Executing agent {name}")\n'
            template += f'    return f"Completed agent task: {{task}}"\n'
        else:
            template += f'class {name.capitalize()}:\n'
            template += f'    def __init__(self):\n'
            template += f'        self.bus = get_event_bus()\n'
            template += f'        logger.info("{name} initialized")\n\n'
            template += f'    def execute(self):\n'
            template += f'        return "Execution complete"\n'
            
        return template

    def produce_upgrade_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a structured architecture proposal."""
        mod_type = analysis.get("type", "module")
        return {
            "upgrade_id": f"upg_{uuid.uuid4().hex[:8]}",
            "module_name": f"generated_{mod_type}_x",
            "type": mod_type,
            "target_path": f"core/generated/{mod_type}s/generated_{mod_type}_x.py",
            "dependencies": [],
            "status": "proposed"
        }

    def validate_upgrade(self, plan: Dict[str, Any], generated_code: str) -> Dict[str, Any]:
        """Full pipeline: Sandbox -> Dependency Check -> Event Emission."""
        
        logger.info(f"[SELF-DEV] Validating upgrade {plan['upgrade_id']}")
        
        # 1. Dependency Check
        dep_safe, dep_msg = validate_dependencies(generated_code)
        if not dep_safe:
            return {"valid": False, "reason": dep_msg}
            
        # 2. Sandbox Testing
        sandbox_res = run_test_module(generated_code)
        test_report = return_test_report(generated_code, sandbox_res)
        
        bus = get_event_bus()
        if bus:
            try:
                bus.publish_sync("UPGRADE_TESTED", "self_dev_engine", sandbox_res)
            except Exception as e:
                logger.error(f"[SELF-DEV] Event publish error: {e}")
                
        if not sandbox_res.get("success"):
            return {"valid": False, "reason": f"Sandbox failed: {sandbox_res.get('stderr')}", "report": test_report}
            
        # 3. Publish Proposal
        if bus:
            try:
                bus.publish_sync("UPGRADE_PROPOSED", "self_dev_engine", plan)
            except Exception as e:
                pass
                
        return {"valid": True, "reason": "All checks passed.", "report": test_report}

# Singleton
_self_dev_engine = None

def get_self_dev_engine() -> SelfDevEngine:
    global _self_dev_engine
    if _self_dev_engine is None:
        _self_dev_engine = SelfDevEngine()
    return _self_dev_engine
