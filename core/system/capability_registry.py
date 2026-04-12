"""
Capability Registry for GENESIS
Defines boolean flags for active system capabilities.
Used across the system to safely identify available components.
"""

CAPABILITIES = {
    "voice": True,
    "automation": True,
    "memory": True,
    "camera": True,
    "vision_detection": True,
    "visual_intelligence": True,
    "agents": True,
    "world_model": True
}

def get_capabilities() -> dict:
    return CAPABILITIES

def has_capability(capability_name: str) -> bool:
    return CAPABILITIES.get(capability_name, False)
