"""
Phase-3 — Tool Sandbox
Sandboxed execution for tool functions with timeout, command validation,
and path restrictions. If sandbox fails, falls back to safe execution.
"""

import threading
import os

# Blocked shell patterns — expanded from safe_mode
_DANGEROUS_COMMANDS = [
    "rm ", "rm\t", "rmdir", "del ", "format ", "mkfs", "sudo ",
    "reboot", "shutdown", "poweroff", "halt",
    "chmod 777", "dd if=", "wget ", "curl ",
    ":(){", "fork", ">()", "mv /",
]

# Restricted filesystem paths
_RESTRICTED_PATHS = [
    "/etc", "/sys", "/boot", "/proc",
    "C:\\Windows\\System32", "C:\\Windows\\system32",
    "/usr/bin", "/usr/sbin",
]

_DEFAULT_TIMEOUT = 10  # seconds


def validate_command(cmd):
    """Check if a shell command is safe to execute."""
    if not isinstance(cmd, str):
        return True
    cmd_lower = cmd.lower().strip()
    for pattern in _DANGEROUS_COMMANDS:
        if pattern.lower() in cmd_lower:
            _log_blocked(cmd, pattern)
            return False
    return True


def validate_path(path):
    """Check if a file path is within allowed boundaries."""
    if not isinstance(path, str):
        return True
    abs_path = os.path.abspath(path)
    for restricted in _RESTRICTED_PATHS:
        if abs_path.startswith(restricted):
            _log_blocked(f"path:{path}", f"restricted:{restricted}")
            return False
    return True


def sandbox_execute(tool_function, args=None, kwargs=None, timeout=_DEFAULT_TIMEOUT):
    """Execute a tool function inside a sandbox with timeout and validation.
    
    Returns:
        tuple: (success: bool, result: any)
    """
    args = args or []
    kwargs = kwargs or {}

    # Validate any string args that look like commands or paths
    for arg in args:
        if isinstance(arg, str):
            if not validate_command(arg) or not validate_path(arg):
                return (False, "Blocked by security sandbox.")

    result_container = [None]
    error_container = [None]

    def _run():
        try:
            result_container[0] = tool_function(*args, **kwargs)
        except Exception as e:
            error_container[0] = str(e)

    try:
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            _log_blocked(str(tool_function), "timeout exceeded")
            return (False, f"Tool execution timed out after {timeout}s.")

        if error_container[0]:
            return (False, f"Tool error: {error_container[0]}")

        return (True, result_container[0])

    except Exception as e:
        return (False, f"Sandbox error: {e}")


def _log_blocked(command, reason):
    """Log blocked commands via security logger if available."""
    try:
        from core.security.security_logger import log_security_violation
        log_security_violation(command, reason)
    except Exception:
        print(f"[SANDBOX] BLOCKED: {command} | reason: {reason}", flush=True)
