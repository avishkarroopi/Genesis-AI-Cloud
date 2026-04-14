import logging
import importlib

logger = logging.getLogger(__name__)

MODULES_TO_LOAD = [
    "core.ai_monitor.ai_cost_optimizer",
    "core.observability.telemetry_collector",
    "core.cognitive.cognitive_orchestrator",
    "core.cognitive.personal_intelligence",
    "core.cognitive.governance_layer",
    "core.cognitive.self_evolution"
]

def load_intelligence_modules():
    """
    Safely load intelligence layer plugins via dynamic import
    matching the Two-Stage approval plan.
    """
    logger.info("Bootstrapping Intelligence Infrastructure Layer...")
    for mod_name in MODULES_TO_LOAD:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "initialize_module"):
                mod.initialize_module()
                logger.info(f"Successfully initialized plugin: {mod_name}")
            else:
                logger.warning(f"Plugin {mod_name} missing initialize_module()")
        except Exception as e:
            logger.error(f"Failed to load plugin {mod_name}: {e}")

if __name__ == "__main__":
    load_intelligence_modules()
