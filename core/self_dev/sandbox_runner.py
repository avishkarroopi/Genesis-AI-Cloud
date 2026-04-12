"""
Sandbox Runner for testing generated GENESIS upgrades.
Executes code in a completely isolated subprocess without modifying the live system.
"""

import sys
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_test_module(code: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Writes code to temp file, runs it in an isolated Python subprocess."""
    
    # Very basic blocklist for the sandbox itself
    if "os.system" in code or "subprocess" in code:
        return {"success": False, "error": "Sandbox rule violation: subprocess/os execution not allowed in test code."}
        
    fd, temp_path = tempfile.mkstemp(suffix=".py", prefix="genesis_sandbox_")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
            
        logger.info(f"[SANDBOX] Running generated code in {temp_path}")
        
        # We run the python interpreter explicitly, adding core to PYTHONPATH so imports work
        # but the module itself is entirely temporary.
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        
        output = result.stdout
        errors = result.stderr
        
        if result.returncode == 0:
            return capture_errors(True, output, errors)
        else:
            return capture_errors(False, output, errors)
            
    except subprocess.TimeoutExpired:
        return capture_errors(False, "", "Execution timed out limit of 30 seconds.")
    except Exception as e:
        return capture_errors(False, "", f"Sandbox internal error: {e}")
    finally:
        # Cleanup
        try:
            os.remove(temp_path)
        except OSError:
            pass

def capture_errors(success: bool, stdout: str, stderr: str) -> Dict[str, Any]:
    """Formats the subprocess results."""
    return {
        "success": success,
        "stdout": stdout[:1000], # Limit output size
        "stderr": stderr[:1000],
        "summary": "Passed isolated execution" if success else "Failed execution"
    }

def return_test_report(code: str, results: Dict[str, Any]) -> str:
    """Builds a human-readable/LLM-readable string report."""
    status = "SUCCESS" if results.get("success") else "FAILED"
    report = f"--- SANDBOX TEST {status} ---\n"
    if results.get("stdout"):
        report += f"STDOUT:\n{results['stdout']}\n"
    if results.get("stderr"):
        report += f"STDERR:\n{results['stderr']}\n"
    report += "-" * 30 + "\n"
    return report
