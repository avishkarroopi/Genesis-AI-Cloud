"""
GENESIS — Vision Context Summary
Improvement 9: "Genesis what do you see" enhanced response.

Combines YOLO detections + scene memory + world model into a natural language summary.
Registered as a tool in tool_registry.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_vision_context() -> Dict[str, Any]:
    """Gather comprehensive vision context from all vision subsystems."""
    context: Dict[str, Any] = {
        "detections": [],
        "scene_summary": "",
        "tracked_objects": 0,
        "person_detected": False,
    }

    # 1. YOLO detections via world model
    try:
        from core.world_model import get_world_model
        wm = get_world_model()
        objects = wm.get_all_objects() if hasattr(wm, 'get_all_objects') else []
        if objects:
            labels = []
            for obj in objects:
                label = getattr(obj, 'label', None) or obj.get('label', 'unknown') if isinstance(obj, dict) else str(obj)
                labels.append(label)
                if 'person' in str(label).lower():
                    context["person_detected"] = True
            context["detections"] = labels
            context["tracked_objects"] = len(labels)
    except Exception as e:
        logger.debug(f"[VISION_CTX] World model query failed: {e}")

    # 2. Scene memory
    try:
        from core.vision.scene_memory import get_scene_memory
        sm = get_scene_memory()
        if hasattr(sm, 'get_current_scene'):
            scene = sm.get_current_scene()
            if scene:
                context["scene_summary"] = str(scene)
    except Exception:
        pass

    # 3. Advanced vision (Phase-3 object tracker)
    try:
        from core.advanced_vision import get_advanced_vision
        av = get_advanced_vision()
        status = av.get_status()
        context["tracked_objects"] = max(
            context["tracked_objects"],
            status.get("tracked_objects", 0)
        )
    except Exception:
        pass

    return context


def vision_spoken_summary() -> str:
    """Return a natural language description of what GENESIS can see."""
    ctx = get_vision_context()
    detections = ctx.get("detections", [])
    person = ctx.get("person_detected", False)
    tracked = ctx.get("tracked_objects", 0)

    if not detections and tracked == 0:
        return "I don't currently detect any objects in the camera view. The scene appears clear."

    # Deduplicate and count
    label_counts: Dict[str, int] = {}
    for label in detections:
        clean = str(label).strip().lower()
        label_counts[clean] = label_counts.get(clean, 0) + 1

    # Build natural language
    parts = []
    for label, count in label_counts.items():
        if count > 1:
            parts.append(f"{count} {label}s")
        else:
            article = "an" if label[0] in "aeiou" else "a"
            parts.append(f"{article} {label}")

    if not parts:
        return f"I'm tracking {tracked} objects but cannot identify specific items at the moment."

    if len(parts) == 1:
        obj_list = parts[0]
    elif len(parts) == 2:
        obj_list = f"{parts[0]} and {parts[1]}"
    else:
        obj_list = ", ".join(parts[:-1]) + f", and {parts[-1]}"

    response = f"I can see {obj_list}."

    if person:
        response += " I detect a person in the frame."

    return response


def register_vision_context_tool():
    """Register the vision context summary as a tool in the tool registry."""
    try:
        from core.tool_registry import get_tool_registry, ToolType

        registry = get_tool_registry()

        async def _vision_tool() -> str:
            return vision_spoken_summary()

        registry.register_tool(
            "vision_summary",
            "Vision Summary",
            "Describe what GENESIS currently sees using camera and object detection",
            ToolType.SENSOR_READ,
            _vision_tool,
            return_type=str,
        )
        logger.info("[VISION_CTX] Tool registered: vision_summary")
    except Exception as e:
        logger.warning(f"[VISION_CTX] Tool registration failed: {e}")
