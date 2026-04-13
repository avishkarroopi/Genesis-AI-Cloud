"""
World Model for GENESIS + JARVIS.
Maintains internal representation of environment with continuous updates.
Requirement 27: World Model with environment mapping, object tracking, event timeline, 
context awareness, and predictive simulation.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import math

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True

from core.event_bus import get_event_bus, EventPriority
from core.knowledge_graph import get_knowledge_graph, NodeType, RelationType


class ObjectCategory(Enum):
    PERSON = "person"
    OBJECT = "object"
    OBSTACLE = "obstacle"
    TOOL = "tool"
    FURNITURE = "furniture"
    ANIMAL = "animal"
    UNKNOWN = "unknown"


class EventType(Enum):
    DETECTED = "detected"
    MOVED = "moved"
    INTERACTED = "interacted"
    DISAPPEARED = "disappeared"
    CREATED = "created"
    DESTROYED = "destroyed"
    CHANGED = "changed"


@dataclass
class Position:
    """3D position in world coordinates."""
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt(
            (self.x - other.x)**2 +
            (self.y - other.y)**2 +
            (self.z - other.z)**2
        )
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class WorldObject:
    """
    Represents an object in the world model.
    Tracks position, properties, and history.
    """
    object_id: str
    category: ObjectCategory
    label: str
    position: Position
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    position_history: List[Tuple[Position, datetime]] = field(default_factory=list)
    
    def update_position(self, new_position: Position):
        """Update object position and track history."""
        self.position_history.append((self.position, self.last_seen))
        self.position = new_position
        self.last_seen = datetime.now()
        
        if len(self.position_history) > 100:
            self.position_history.pop(0)
    
    def get_velocity(self) -> Optional[Tuple[float, float]]:
        """Get approximate velocity based on position history."""
        if len(self.position_history) < 2:
            return None
        
        prev_pos, prev_time = self.position_history[-1]
        curr_pos = self.position
        curr_time = self.last_seen
        
        time_delta = (curr_time - prev_time).total_seconds()
        if time_delta == 0:
            return None
        
        vx = (curr_pos.x - prev_pos.x) / time_delta
        vy = (curr_pos.y - prev_pos.y) / time_delta
        
        return (vx, vy)
    
    def predict_position(self, seconds_ahead: float) -> Optional[Position]:
        """Predict future position based on velocity."""
        velocity = self.get_velocity()
        if velocity is None:
            return None
        
        vx, vy = velocity
        predicted = Position(
            x=self.position.x + vx * seconds_ahead,
            y=self.position.y + vy * seconds_ahead,
            z=self.position.z
        )
        return predicted
    
    def is_stale(self, max_age_seconds: float = 30.0) -> bool:
        """Check if object observation is stale."""
        age = (datetime.now() - self.last_seen).total_seconds()
        return age > max_age_seconds
    
    def to_dict(self) -> Dict:
        return {
            "object_id": self.object_id,
            "category": self.category.value,
            "label": self.label,
            "position": self.position.to_dict(),
            "confidence": self.confidence,
            "properties": self.properties,
            "last_seen": self.last_seen.isoformat(),
            "first_seen": self.first_seen.isoformat()
        }


@dataclass
class WorldEvent:
    """Timestamped event in the world."""
    event_id: str
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    involved_objects: List[str] = field(default_factory=list)
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "involved_objects": self.involved_objects,
            "description": self.description,
            "data": self.data
        }


@dataclass
class Location:
    """Named location in the world."""
    location_id: str
    label: str
    center: Position
    radius: float
    category: str = "generic"
    properties: Dict[str, Any] = field(default_factory=dict)
    objects_present: Set[str] = field(default_factory=set)
    
    def contains_position(self, pos: Position) -> bool:
        """Check if location contains a position."""
        return self.center.distance_to(pos) <= self.radius
    
    def to_dict(self) -> Dict:
        return {
            "location_id": self.location_id,
            "label": self.label,
            "center": self.center.to_dict(),
            "radius": self.radius,
            "category": self.category,
            "properties": self.properties
        }


class WorldModel:
    """
    Maintains continuous, dynamic model of the environment.
    Integrates perception, tracks objects, manages events, and enables prediction.
    Requirement 27: Environment mapping, object tracking, event timeline, 
    context awareness, predictive simulation.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        
        self.world_state = {}
        try:
            if self.event_bus:
                self.event_bus.subscribe("SENSOR_TRIGGER", self._on_sensor)
                self.event_bus.subscribe("VISION_DETECTED", self._on_vision)
                self.event_bus.subscribe("PERCEPTION_UPDATE", self._on_perception)
                self.event_bus.subscribe("SYSTEM_STATE", self._on_system)
        except Exception as e:
            self.logger.warning(f"Failed to subscribe world model to event bus: {e}")
            
        self.kg = get_knowledge_graph()
        
        self.objects: Dict[str, WorldObject] = {}
        self.locations: Dict[str, Location] = {}
        self.event_history: deque = deque(maxlen=100)
        self.relationship_graph: Dict[str, Set[str]] = defaultdict(set)
        
        self._perception_tasks: Set[asyncio.Task] = set()
        self._last_update = datetime.now()
        self._update_frequency = 0.1

    async def _on_sensor(self, event_type: str, source: str, data: Any):
        try:
            self.world_state["sensor"] = data
            self.logger.debug(f"WorldModel sensor update: {source}")
        except Exception:
            pass

    async def _on_vision(self, event_type: str, source: str, data: Any):
        try:
            self.world_state["vision"] = data
            if isinstance(data, dict):
                # Update specific world_model roots as requested
                for k in ["user_present", "faces", "emotion"]:
                    if k in data:
                        self.world_state[k] = data[k]
            self.logger.debug(f"WorldModel vision update: {source}")
        except Exception:
            pass

    async def _on_perception(self, event_type: str, source: str, data: Any):
        try:
            self.world_state["perception"] = data
            self.logger.debug(f"WorldModel perception update: {source}")
        except Exception:
            pass

    async def _on_system(self, event_type: str, source: str, data: Any):
        try:
            self.world_state["system"] = data
            self.logger.debug(f"WorldModel system update: {source}")
        except Exception:
            pass
        
    async def add_object(self, object_id: str, category: ObjectCategory,
                        label: str, position: Position,
                        confidence: float = 1.0,
                        properties: Dict = None) -> WorldObject:
        """Add or update an object in the world."""
        
        if object_id in self.objects:
            obj = self.objects[object_id]
            obj.update_position(position)
            obj.confidence = confidence
            if properties:
                obj.properties.update(properties)
        else:
            obj = WorldObject(
                object_id=object_id,
                category=category,
                label=label,
                position=position,
                confidence=confidence,
                properties=properties or {}
            )
            self.objects[object_id] = obj
            
            event = WorldEvent(
                event_id=f"obj_created_{object_id}_{datetime.now().timestamp()}",
                event_type=EventType.CREATED,
                involved_objects=[object_id],
                description=f"Object detected: {label}"
            )
            self.event_history.append(event)
            
            if not SAFE_START:
                await self.event_bus.publish(
                    "world_object_detected",
                    "world_model",
                    {
                        "object_id": object_id,
                        "category": category.value,
                        "label": label,
                        "position": position.to_dict(),
                        "confidence": confidence
                    }
                )
            
            self._add_to_kg(obj)
        
        for location_id, location in self.locations.items():
            if location.contains_position(position):
                location.objects_present.add(object_id)
        
        return obj
    
    async def update_object_position(self, object_id: str, new_position: Position):
        """Update an object's position."""
        if object_id in self.objects:
            obj = self.objects[object_id]
            old_position = obj.position
            obj.update_position(new_position)
            
            distance = old_position.distance_to(new_position)
            if distance > 0.1:
                event = WorldEvent(
                    event_id=f"obj_moved_{object_id}_{datetime.now().timestamp()}",
                    event_type=EventType.MOVED,
                    involved_objects=[object_id],
                    description=f"{obj.label} moved {distance:.2f} units",
                    data={"distance": distance, "old_pos": old_position.to_dict()}
                )
                self.event_history.append(event)
                
                for location_id, location in self.locations.items():
                    if location.contains_position(new_position):
                        location.objects_present.add(object_id)
                    elif object_id in location.objects_present:
                        location.objects_present.discard(object_id)
    
    async def record_interaction(self, object_id_1: str, object_id_2: str,
                                interaction_type: str):
        """Record an interaction between objects."""
        self.relationship_graph[object_id_1].add(object_id_2)
        self.relationship_graph[object_id_2].add(object_id_1)
        
        event = WorldEvent(
            event_id=f"interaction_{object_id_1}_{object_id_2}_{datetime.now().timestamp()}",
            event_type=EventType.INTERACTED,
            involved_objects=[object_id_1, object_id_2],
            description=f"Interaction: {interaction_type}",
            data={"interaction_type": interaction_type}
        )
        self.event_history.append(event)
        
        if not SAFE_START:
            await self.event_bus.publish(
                "world_interaction",
                "world_model",
                {
                    "object_1": object_id_1,
                    "object_2": object_id_2,
                    "interaction_type": interaction_type
                }
            )
    
    async def record_change(self, object_id: str, property_name: str,
                           old_value: Any, new_value: Any):
        """Record a property change."""
        event = WorldEvent(
            event_id=f"change_{object_id}_{datetime.now().timestamp()}",
            event_type=EventType.CHANGED,
            involved_objects=[object_id],
            description=f"Property changed: {property_name}",
            data={
                "property": property_name,
                "old_value": old_value,
                "new_value": new_value
            }
        )
        self.event_history.append(event)
    
    def add_location(self, location_id: str, label: str, center: Position,
                    radius: float, category: str = "generic") -> Location:
        """Add a named location to the world."""
        location = Location(
            location_id=location_id,
            label=label,
            center=center,
            radius=radius,
            category=category
        )
        self.locations[location_id] = location
        
        self.logger.debug(f"Added location: {label}")
        return location
    
    def get_objects_in_location(self, location_id: str) -> List[WorldObject]:
        """Get all objects in a location."""
        if location_id not in self.locations:
            return []
        
        location = self.locations[location_id]
        return [self.objects[obj_id] for obj_id in location.objects_present
                if obj_id in self.objects]
    
    def get_objects_by_category(self, category: ObjectCategory) -> List[WorldObject]:
        """Get all objects of a specific category."""
        return [obj for obj in self.objects.values() if obj.category == category]
    
    def get_objects_by_label(self, label: str) -> List[WorldObject]:
        """Get objects by label."""
        return [obj for obj in self.objects.values() if obj.label.lower() == label.lower()]
    
    def get_nearby_objects(self, position: Position, radius: float) -> List[WorldObject]:
        """Get objects near a position."""
        nearby = []
        for obj in self.objects.values():
            if position.distance_to(obj.position) <= radius:
                nearby.append(obj)
        return nearby
    
    def get_relationships(self, object_id: str) -> List[str]:
        """Get objects related to a given object."""
        return list(self.relationship_graph.get(object_id, set()))
    
    def predict_object_positions(self, seconds_ahead: float) -> Dict[str, Position]:
        """Predict positions of objects in the future."""
        predictions = {}
        for obj_id, obj in self.objects.items():
            predicted_pos = obj.predict_position(seconds_ahead)
            if predicted_pos:
                predictions[obj_id] = predicted_pos
        return predictions
    
    async def cleanup_stale_objects(self, max_age_seconds: float = 60.0):
        """Remove stale object observations."""
        stale_objects = [
            obj_id for obj_id, obj in self.objects.items()
            if obj.is_stale(max_age_seconds)
        ]
        
        for obj_id in stale_objects:
            obj = self.objects.pop(obj_id)
            event = WorldEvent(
                event_id=f"obj_disappeared_{obj_id}_{datetime.now().timestamp()}",
                event_type=EventType.DISAPPEARED,
                involved_objects=[obj_id],
                description=f"Object disappeared: {obj.label}"
            )
            self.event_history.append(event)
            
            if not SAFE_START:
                await self.event_bus.publish(
                    "world_object_disappeared",
                    "world_model",
                    {"object_id": obj_id, "label": obj.label}
                )
    
    def get_event_history(self, limit: int = 100) -> List[WorldEvent]:
        """Get recent events."""
        return list(self.event_history)[-limit:]
    
    def get_events_involving_object(self, object_id: str, limit: int = 50) -> List[WorldEvent]:
        """Get events involving a specific object."""
        events = [e for e in self.event_history if object_id in e.involved_objects]
        return events[-limit:]
    
    def export_state(self) -> Dict[str, Any]:
        """Export entire world state."""
        return {
            "timestamp": datetime.now().isoformat(),
            "objects": {obj_id: obj.to_dict() for obj_id, obj in self.objects.items()},
            "locations": {loc_id: loc.to_dict() for loc_id, loc in self.locations.items()},
            "event_count": len(self.event_history),
            "recent_events": [e.to_dict() for e in list(self.event_history)[-20:]]
        }
    
    def _add_to_kg(self, obj: WorldObject):
        """Add world object to knowledge graph."""
        try:
            node = self.kg.add_node(
                obj.object_id,
                NodeType.OBJECT,
                obj.label,
                properties={
                    "category": obj.category.value,
                    "position_x": obj.position.x,
                    "position_y": obj.position.y,
                    "position_z": obj.position.z,
                    **obj.properties
                }
            )
        except Exception as e:
            self.logger.error(f"Error adding object to knowledge graph: {e}")
    
    def get_current_state(self) -> str:
        """Phase-2: Return a human-readable summary of the current environment
        for injection into brain prompt context."""
        try:
            lines = []
            # Objects currently tracked
            if self.objects:
                lines.append("Detected Objects:")
                for obj in list(self.objects.values())[:10]:
                    if not obj.is_stale(60.0):
                        lines.append(f"- {obj.label} ({obj.category.value})")
            # Recent world state from event subscriptions
            if self.world_state:
                if "vision" in self.world_state:
                    vis = self.world_state["vision"]
                    if isinstance(vis, dict) and "objects" in vis:
                        lines.append("Vision: " + ", ".join(vis["objects"][:5]))
                if "sensor" in self.world_state:
                    lines.append("Sensors: active")
            if not lines:
                lines.append("No environment data available.")
            return "\n".join(lines)
        except Exception:
            return "Environment state unavailable."

    def get_stats(self) -> Dict[str, Any]:
        """Get world model statistics."""
        return {
            "total_objects": len(self.objects),
            "total_locations": len(self.locations),
            "total_events": len(self.event_history),
            "objects_by_category": {
                cat.value: len(self.get_objects_by_category(cat))
                for cat in ObjectCategory
            },
            "last_updated": self._last_update.isoformat()
        }


_global_world_model: WorldModel = None


def get_world_model() -> WorldModel:
    """Get or create the global world model."""
    global _global_world_model
    if _global_world_model is None:
        _global_world_model = WorldModel()
    return _global_world_model


def set_world_model(model: WorldModel):
    """Set the global world model."""
    global _global_world_model
    _global_world_model = model
