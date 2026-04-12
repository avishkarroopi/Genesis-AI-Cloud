"""
Perception Fusion for GENESIS + JARVIS.
Integrates data from multiple sensors: camera, microphone, IMU, etc.
Requirements: 6 (perception fusion), 19 (environment awareness).
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

try:
    from core.config import SAFE_START
except ImportError:
    SAFE_START = True

from core.event_bus import get_event_bus, EventPriority
from core.world_model import get_world_model, Position, ObjectCategory


class SensorType(Enum):
    CAMERA = "camera"
    MICROPHONE = "microphone"
    IMU = "imu"
    LIDAR = "lidar"
    THERMAL = "thermal"
    DEPTH = "depth"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"


@dataclass
class SensorReading:
    """Raw sensor reading."""
    sensor_id: str
    sensor_type: SensorType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    valid: bool = True
    error: str = ""


@dataclass
class FusedPerception:
    """Fused perception output from multiple sensors."""
    perception_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    objects_detected: List[Dict[str, Any]] = field(default_factory=list)
    people_detected: List[Dict[str, Any]] = field(default_factory=list)
    audio_events: List[Dict[str, Any]] = field(default_factory=list)
    motion_data: Dict[str, Any] = field(default_factory=dict)
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "perception_id": self.perception_id,
            "timestamp": self.timestamp.isoformat(),
            "objects": len(self.objects_detected),
            "people": len(self.people_detected),
            "audio_events": len(self.audio_events),
            "confidence": self.confidence
        }


class PerceptionFusion:
    """
    Fuses data from multiple sensors into unified perception.
    Requirements 6: Perception Fusion, 19: Environment Awareness.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        self.world_model = get_world_model()
        
        self.sensors: Dict[str, Callable] = {}
        self.sensor_readings: Dict[str, deque] = {}
        self.fused_perceptions: deque = deque(maxlen=1000)
        
        self._running = False
        self._fusion_task: Optional[asyncio.Task] = None
        self._fusion_frequency = 0.1
        self._fusion_timeout = 2.0
        
        # --- SAFE PERCEPTION LIMITS ---
        self._last_trigger_time = 0
        self._trigger_cooldown = 1.5
        # ------------------------------
        
        try:
            if self.event_bus:
                self.event_bus.subscribe("SENSOR_TRIGGER", self._on_sensor)
                self.event_bus.subscribe("VISION_DETECTED", self._on_vision)
        except Exception as e:
            self.logger.warning(f"Failed to subscribe perception to event bus: {e}")

    async def _on_sensor(self, event_type: str, source: str, data: Any):
        try:
            if "sensor_trigger" not in self.sensor_readings:
                self.sensor_readings["sensor_trigger"] = deque(maxlen=100)
            
            data_dict = data if isinstance(data, dict) else {"raw": data}
            self.sensor_readings["sensor_trigger"].append(SensorReading(
                sensor_id=source,
                sensor_type=SensorType.CAMERA, 
                data=data_dict
            ))
            
            if self.event_bus:
                await self.event_bus.publish("PERCEPTION_UPDATE", "perception_fusion", {"sensor_data": data_dict})
                
            # --- SAFE PERCEPTION TRIGGER ---
            if data_dict:
                try:
                    import time
                    now = time.time()
                    if now - self._last_trigger_time < self._trigger_cooldown:
                        return
                    self._last_trigger_time = now
                    
                    from autonomous_engine import get_reasoning_engine
                    engine = get_reasoning_engine()
                    if engine:
                        engine.submit_task(
                            "perception_event",
                            {"source": source, "data": data_dict, "type": "sensor"}
                        )
                except Exception:
                    pass
            # -------------------------------
        except Exception:
            pass

    async def _on_vision(self, event_type: str, source: str, data: Any):
        try:
            if "vision_detected" not in self.sensor_readings:
                self.sensor_readings["vision_detected"] = deque(maxlen=100)
                
            data_dict = data if isinstance(data, dict) else {"raw": data}
            self.sensor_readings["vision_detected"].append(SensorReading(
                sensor_id=source,
                sensor_type=SensorType.CAMERA, 
                data=data_dict
            ))
            
            if self.event_bus:
                await self.event_bus.publish("PERCEPTION_UPDATE", "perception_fusion", {"vision_data": data_dict})
                
            # --- SAFE PERCEPTION TRIGGER ---
            if data_dict:
                try:
                    import time
                    now = time.time()
                    if now - self._last_trigger_time < self._trigger_cooldown:
                        return
                    self._last_trigger_time = now
                    
                    from autonomous_engine import get_reasoning_engine
                    engine = get_reasoning_engine()
                    if engine:
                        engine.submit_task(
                            "perception_event",
                            {"source": source, "data": data_dict, "type": "vision"}
                        )
                except Exception:
                    pass
            # -------------------------------
        except Exception:
            pass
    
    def register_sensor(self, sensor_id: str, sensor_type: SensorType,
                       read_func: Callable):
        """Register a sensor."""
        self.sensors[sensor_id] = (sensor_type, read_func)
        self.sensor_readings[sensor_id] = deque(maxlen=100)
        self.logger.info(f"Sensor registered: {sensor_id} ({sensor_type.value})")
    
    async def start(self):
        """Start perception fusion."""
        if SAFE_START:
            return
            
        self._running = True
        self.logger.info("Perception fusion started")
        self._fusion_task = asyncio.create_task(self._fusion_loop())
    
    async def _fusion_loop(self):
        """Main fusion loop."""
        while self._running:
            try:
                await self._read_all_sensors()
                
                fused = await self._fuse_perceptions()
                
                if fused:
                    self.fused_perceptions.append(fused)
                    
                    await self._update_world_model(fused)
                    
                    await self.event_bus.publish(
                        "perception_fused",
                        "perception_fusion",
                        fused.to_dict()
                    )
                
                await asyncio.sleep(self._fusion_frequency)
            
            except Exception as e:
                self.logger.error(f"Fusion loop error: {e}", exc_info=True)
                await asyncio.sleep(0.5)
    
    async def _read_all_sensors(self):
        """Read data from all registered sensors."""
        
        async def read_sensor(sensor_id: str, sensor_type: SensorType, read_func: Callable):
            try:
                data = await self._call_async(read_func)
                reading = SensorReading(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    data=data or {}
                )
                self.sensor_readings[sensor_id].append(reading)
            except Exception as e:
                reading = SensorReading(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    valid=False,
                    error=str(e)
                )
                self.sensor_readings[sensor_id].append(reading)
        
        tasks = [
            read_sensor(sid, stype, sfunc)
            for sid, (stype, sfunc) in self.sensors.items()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fuse_perceptions(self) -> Optional[FusedPerception]:
        """Fuse readings from all sensors."""
        
        try:
            fused = FusedPerception(
                perception_id=f"perception_{datetime.now().timestamp()}"
            )
            
            camera_readings = [
                r for readings in self.sensor_readings.values()
                for r in readings
                if r.sensor_type == SensorType.CAMERA and r.valid
            ]
            
            for reading in camera_readings:
                if "detected_objects" in reading.data:
                    fused.objects_detected.extend(reading.data["detected_objects"])
                
                if "people" in reading.data:
                    fused.people_detected.extend(reading.data["people"])
            
            microphone_readings = [
                r for readings in self.sensor_readings.values()
                for r in readings
                if r.sensor_type == SensorType.MICROPHONE and r.valid
            ]
            
            for reading in microphone_readings:
                if "audio_events" in reading.data:
                    fused.audio_events.extend(reading.data["audio_events"])
            
            imu_readings = [
                r for readings in self.sensor_readings.values()
                for r in readings
                if r.sensor_type == SensorType.IMU and r.valid
            ]
            
            if imu_readings:
                latest_imu = imu_readings[-1]
                fused.motion_data = latest_imu.data
            
            thermal_readings = [
                r for readings in self.sensor_readings.values()
                for r in readings
                if r.sensor_type == SensorType.THERMAL and r.valid
            ]
            
            if thermal_readings:
                fused.environmental_conditions["temperature"] = \
                    sum(r.data.get("temperature", 0) for r in thermal_readings) / len(thermal_readings)
            
            all_valid = all(
                all(r.valid for r in readings)
                for readings in self.sensor_readings.values()
            )
            
            fused.confidence = 0.9 if all_valid else 0.6
            
            return fused if (fused.objects_detected or fused.people_detected or fused.audio_events) else None
        
        except Exception as e:
            self.logger.error(f"Fusion error: {e}")
            return None
    
    async def _update_world_model(self, fused: FusedPerception):
        """Update world model with fused perceptions."""
        
        try:
            for obj_data in fused.objects_detected:
                object_id = obj_data.get("id", f"obj_{datetime.now().timestamp()}")
                
                position = Position(
                    x=obj_data.get("x", 0),
                    y=obj_data.get("y", 0),
                    z=obj_data.get("z", 0)
                )
                
                category = ObjectCategory(obj_data.get("category", "unknown"))
                label = obj_data.get("label", "object")
                confidence = obj_data.get("confidence", 1.0)
                
                await self.world_model.add_object(
                    object_id=object_id,
                    category=category,
                    label=label,
                    position=position,
                    confidence=confidence,
                    properties=obj_data.get("properties", {})
                )
            
            for person_data in fused.people_detected:
                person_id = person_data.get("id", f"person_{datetime.now().timestamp()}")
                
                position = Position(
                    x=person_data.get("x", 0),
                    y=person_data.get("y", 0),
                    z=person_data.get("z", 0)
                )
                
                confidence = person_data.get("confidence", 1.0)
                
                await self.world_model.add_object(
                    object_id=person_id,
                    category=ObjectCategory.PERSON,
                    label=person_data.get("label", "person"),
                    position=position,
                    confidence=confidence,
                    properties={
                        "emotion": person_data.get("emotion", "neutral"),
                        "pose": person_data.get("pose", "standing")
                    }
                )
        
        except Exception as e:
            self.logger.error(f"World model update error: {e}")
    
    async def _call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call function, handling both sync and async."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def stop(self):
        """Stop perception fusion."""
        self._running = False
        if self._fusion_task:
            await self._fusion_task
        self.logger.info("Perception fusion stopped")
    
    def get_last_fusion(self) -> Optional[FusedPerception]:
        """Get the last fused perception."""
        return self.fused_perceptions[-1] if self.fused_perceptions else None
    
    def get_fusion_history(self, limit: int = 50) -> List[FusedPerception]:
        """Get recent fused perceptions."""
        return list(self.fused_perceptions)[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get perception fusion statistics."""
        return {
            "registered_sensors": len(self.sensors),
            "sensors_by_type": {
                stype.value: sum(
                    1 for _, (st, _) in self.sensors.items()
                    if st == stype
                )
                for stype in SensorType
            },
            "total_fusions": len(self.fused_perceptions),
            "last_fusion": (
                self.fused_perceptions[-1].timestamp.isoformat()
                if self.fused_perceptions else None
            )
        }


_global_perception_fusion: PerceptionFusion = None


def get_perception_fusion() -> PerceptionFusion:
    """Get or create the global perception fusion."""
    global _global_perception_fusion
    if _global_perception_fusion is None:
        _global_perception_fusion = PerceptionFusion()
    return _global_perception_fusion


def set_perception_fusion(fusion: PerceptionFusion):
    """Set the global perception fusion."""
    global _global_perception_fusion
    _global_perception_fusion = fusion
