"""
Scene Memory (Layer 1 - Perception)
Tracks object persistence, movement, and disappearance over time.
Only emits events (no reasoning).
"""

import time

try:
    from core.event_bus import get_event_bus
except ImportError:
    def get_event_bus(): return None

class SceneMemory:
    def __init__(self):
        self.bus = get_event_bus()
        self.objects = {}  # id -> {label, confidence, bbox, last_seen}
        self.persistence_threshold = 2.0  # seconds before considered disappeared
        
    def update_scene(self, detections: list):
        """
        Takes raw detections from YOLO.
        detections format example: [{'id': 'obj_123', 'label': 'person', 'bbox': [10, 10, 50, 50]}]
        """
        current_time = time.time()
        current_ids = set()
        
        for det in detections:
            obj_id = det.get("id")
            if not obj_id:
                # generate rudimentary ID if not present
                obj_id = f"{det.get('label', 'unknown')}_{hash(str(det.get('bbox')))}"
            
            current_ids.add(obj_id)
            
            if obj_id not in self.objects:
                # NEW OBJECT
                self.objects[obj_id] = {**det, "last_seen": current_time}
                if self.bus:
                    self.bus.publish("VISION_OBJECT_DETECTED", {"id": obj_id, **det})
            else:
                # EXISTING OBJECT
                old_bbox = self.objects[obj_id].get("bbox")
                new_bbox = det.get("bbox")
                if old_bbox != new_bbox:
                    if self.bus:
                        self.bus.publish("VISION_OBJECT_MOVED", {"id": obj_id, "old_bbox": old_bbox, "new_bbox": new_bbox})
                self.objects[obj_id].update({**det, "last_seen": current_time})
                
        # DISAPPEARED OBJECTS
        disappeared_ids = []
        for obj_id, data in self.objects.items():
            if obj_id not in current_ids:
                if current_time - data["last_seen"] > self.persistence_threshold:
                    if self.bus:
                        self.bus.publish("VISION_OBJECT_REMOVED", {"id": obj_id, "label": data.get("label")})
                    disappeared_ids.append(obj_id)
                    
        for obj_id in disappeared_ids:
            del self.objects[obj_id]
            
        if disappeared_ids or len(current_ids) > len(self.objects):
            if self.bus:
                self.bus.publish("VISION_SCENE_CHANGED", {"active_objects": len(self.objects)})
                
scene_memory = SceneMemory()

def get_scene_memory() -> SceneMemory:
    return scene_memory
