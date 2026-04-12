"""
Phase-3 — Security Logger
Centralized audit logging for tool execution, permission denials,
and security violations. Writes to logs/security.log.
"""

import os
import logging
from datetime import datetime

# Setup dedicated security logger
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "security.log")

try:
    os.makedirs(_LOG_DIR, exist_ok=True)
except Exception:
    pass

_security_logger = logging.getLogger("genesis.security")
_security_logger.setLevel(logging.INFO)

# Avoid duplicate handlers on re-import
if not _security_logger.handlers:
    try:
        fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        _security_logger.addHandler(fh)
    except Exception as e:
        print(f"[SECURITY-LOG] Failed to init file handler: {e}", flush=True)


def log_tool_execution(tool_name, args=None, result=None):
    """Log a tool execution event."""
    try:
        _security_logger.info(f"TOOL_EXEC | tool={tool_name} | args={args} | result={str(result)[:200]}")
    except Exception:
        pass


def log_permission_denied(action, reason=""):
    """Log a permission denial."""
    try:
        _security_logger.warning(f"PERMISSION_DENIED | action={action} | reason={reason}")
    except Exception:
        pass


def log_security_violation(command, reason=""):
    """Log a security violation (blocked command, sandbox denial, etc.)."""
    try:
        _security_logger.critical(f"SECURITY_VIOLATION | command={command} | reason={reason}")
    except Exception:
        pass


def log_unsafe_command(command, source="unknown"):
    """Log an unsafe command attempt."""
    try:
        _security_logger.warning(f"UNSAFE_CMD | source={source} | command={command}")
    except Exception:
        pass
