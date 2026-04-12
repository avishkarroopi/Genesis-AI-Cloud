import json
import os

_PERMISSIONS_CACHE = None

def get_permissions() -> dict:
    global _PERMISSIONS_CACHE
    if _PERMISSIONS_CACHE is not None:
        return _PERMISSIONS_CACHE
        
    config_path = os.path.join(os.path.dirname(__file__), 'permissions.json')
    try:
        with open(config_path, 'r') as f:
            _PERMISSIONS_CACHE = json.load(f)
    except Exception as e:
        print(f"[SECURITY] Error loading permissions: {e}")
        # Default safe permissions
        _PERMISSIONS_CACHE = {
            "allow_shell": False,
            "allow_file": False,
            "allow_browser": False,
            "allow_script": False,
            "allow_network": False
        }
    return _PERMISSIONS_CACHE

def check_permission(action: str) -> bool:
    """Check if a specific action is allowed."""
    perms = get_permissions()
    return perms.get(action, False)
