import os

# Global Safe Mode Toggle
SAFE_MODE = True

def is_safe_mode_enabled() -> bool:
    """Returns True if GENESIS is in strict safe mode."""
    # Could potentially be overridden by an environment variable
    return os.environ.get("GENESIS_SAFE_MODE", str(SAFE_MODE)).lower() == "true"

def validate_shell_command(cmd: str) -> bool:
    """If in safe mode, outright block obviously dangerous shell commands."""
    if not is_safe_mode_enabled():
        return True
        
    cmd_lower = cmd.lower()
    dangerous_keywords = ["rm ", "del ", "format ", "mkfs", "sudo ", "reboot", "shutdown"]
    
    for kw in dangerous_keywords:
        if kw in cmd_lower:
            return False
            
    return True

def validate_file_action(path: str, action: str) -> bool:
    """If in safe mode, prevent certain file operations like delete."""
    if not is_safe_mode_enabled():
        return True
        
    if action.lower() in ["delete", "remove", "rmdir"]:
        return False
        
    return True
