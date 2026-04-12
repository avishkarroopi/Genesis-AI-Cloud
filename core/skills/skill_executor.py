"""
Skill Executor (Layer 2 -> Layer 3 interface)
Constraint 1: Agents must never directly import or call system modules.
All agent actions must go through this executor.
"""
from core.skills.skill_registry import get_skill

class SkillExecutor:
    @staticmethod
    def execute(skill_name: str, *args, **kwargs):
        """
        Executes a registered skill and returns its result.
        """
        skill_func = get_skill(skill_name)
        if not skill_func:
            return f"Error: Skill '{skill_name}' is not registered."
        
        try:
            return skill_func(*args, **kwargs)
        except Exception as e:
            return f"Error executing skill '{skill_name}': {e}"
