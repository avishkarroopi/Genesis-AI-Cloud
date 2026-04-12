"""
Skill Registry (Layer 2 -> Layer 3 interface)
Maps string names to Python functions that execute skills.
Constraint 3: The skill system must include a central registry.
"""
from core.skills import browser_skill
from core.skills import search_skill
from core.skills import memory_skill
from core.skills import automation_skill
from core.skills import vision_skill

SKILLS = {
    "browser_open": browser_skill.open_url,
    "youtube_search": search_skill.youtube_search,
    "store_memory": memory_skill.store,
    "automation_webhook": automation_skill.trigger,
    "vision_scan": vision_skill.scan
}

def get_skill(skill_name: str):
    return SKILLS.get(skill_name)
