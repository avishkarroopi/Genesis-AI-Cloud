"""
Enhanced Vision and Voice Agents for GENESIS + JARVIS.
Requirements: 11 (Vision Intelligence), 12 (Speech Intelligence), 7 (Context Memory).
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

from core.event_bus import get_event_bus
from core.world_model import get_world_model, Position, ObjectCategory
from core.perception_fusion import get_perception_fusion
from core.knowledge_graph import get_knowledge_graph, NodeType
from core.owner_system import NameNormalizer


class VisionAgent:
    """
    Enhanced vision agent supporting:
    - Object detection
    - Face detection
    - Scene analysis
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        self.world_model = get_world_model()
        self.perception_fusion = get_perception_fusion()
        self.kg = get_knowledge_graph()
        
        self.detected_objects: Dict[str, Dict[str, Any]] = {}
        self.detected_faces: Dict[str, Dict[str, Any]] = {}
        self.scene_analysis: deque = deque(maxlen=500)
    
    async def analyze_vision(self) -> Dict[str, Any]:
        """Analyze current visual perception."""
        
        try:
            latest_fusion = self.perception_fusion.get_last_fusion()
            
            if not latest_fusion:
                return {"status": "no_perception"}
            
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "objects_detected": len(latest_fusion.objects_detected),
                "people_detected": len(latest_fusion.people_detected),
                "objects": [],
                "people": [],
                "scene_summary": ""
            }
            
            for obj in latest_fusion.objects_detected:
                self.detected_objects[obj.get("id", "unknown")] = obj
                analysis["objects"].append({
                    "label": obj.get("label", "unknown"),
                    "confidence": obj.get("confidence", 0),
                    "category": obj.get("category", "unknown")
                })
            
            for person in latest_fusion.people_detected:
                person_id = person.get("id", f"person_{datetime.now().timestamp()}")
                self.detected_faces[person_id] = person
                analysis["people"].append({
                    "detected": True,
                    "emotion": person.get("emotion", "neutral"),
                    "pose": person.get("pose", "standing")
                })
            
            analysis["scene_summary"] = self._generate_scene_summary(analysis)
            
            self.scene_analysis.append(analysis)
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Vision analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_scene_summary(self, analysis: Dict) -> str:
        """Generate natural language description of scene."""
        
        parts = []
        
        if analysis["objects_detected"] > 0:
            objects_str = ", ".join([obj["label"] for obj in analysis["objects"][:3]])
            parts.append(f"I can see {objects_str}")
        
        if analysis["people_detected"] > 0:
            parts.append(f"I detected {analysis['people_detected']} person(s)")
        
        return ". ".join(parts) if parts else "Scene is empty"
    
    async def track_object(self, object_id: str) -> Optional[Dict]:
        """Track a specific object over time."""
        
        if object_id not in self.detected_objects:
            return None
        
        obj = self.detected_objects[object_id]
        
        position = Position(
            x=obj.get("x", 0),
            y=obj.get("y", 0),
            z=obj.get("z", 0)
        )
        
        return {
            "object_id": object_id,
            "position": position.to_dict(),
            "velocity": obj.get("velocity"),
            "trajectory": []
        }


class VoiceAgent:
    """
    Enhanced voice agent supporting:
    - Wake word detection
    - Speech recognition
    - Speech synthesis
    - Name normalization
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        self.kg = get_knowledge_graph()
        self.name_normalizer = NameNormalizer(logger)
        
        self.recognized_speech: deque = deque(maxlen=500)
        self.wake_words = ["genesis", "jarvis", "genni", "gen"]
        self.is_active = False
    
    async def detect_wake_word(self, audio_text: str) -> bool:
        """Detect if wake word was spoken."""
        
        text_lower = audio_text.lower().strip()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                self.is_active = True
                self.logger.info(f"Wake word detected: {wake_word}")
                return True
        
        return False
    
    async def recognize_speech(self, audio_text: str) -> Dict[str, Any]:
        """Process recognized speech."""
        
        normalized_name, confidence = self.name_normalizer.normalize(audio_text)
        
        recognition = {
            "timestamp": datetime.now().isoformat(),
            "raw_text": audio_text,
            "normalized_text": audio_text.lower().strip(),
            "detected_name": normalized_name if confidence > 0.5 else None,
            "name_confidence": confidence
        }
        
        self.recognized_speech.append(recognition)
        
        return recognition
    
    async def synthesize_speech(self, text: str, speaker_id: str = "default") -> Dict[str, Any]:
        """Synthesize speech."""
        
        synthesis_result = {
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "speaker_id": speaker_id,
            "status": "synthesized"
        }
        
        return synthesis_result


class ContextMemory:
    """
    Maintains conversation and situational context across interactions.
    Requirement 7: Context Memory.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.kg = get_knowledge_graph()
        self.event_bus = get_event_bus()
        
        self.current_context: Dict[str, Any] = {}
        self.conversation_history: deque = deque(maxlen=1000)
        self.situational_context: deque = deque(maxlen=500)
        self.context_stack: List[Dict[str, Any]] = []
    
    async def add_to_context(self, key: str, value: Any, ttl_seconds: Optional[float] = None):
        """Add information to current context."""
        
        self.current_context[key] = {
            "value": value,
            "added_at": datetime.now(),
            "ttl": ttl_seconds
        }
        
        await self.event_bus.publish(
            "context_updated",
            "context_memory",
            {"key": key, "type": type(value).__name__}
        )
    
    async def get_from_context(self, key: str) -> Any:
        """Get information from context."""
        
        if key not in self.current_context:
            return None
        
        entry = self.current_context[key]
        
        if entry["ttl"]:
            age = (datetime.now() - entry["added_at"]).total_seconds()
            if age > entry["ttl"]:
                del self.current_context[key]
                return None
        
        return entry["value"]
    
    async def push_context(self):
        """Save current context to stack."""
        self.context_stack.append(self.current_context.copy())
        self.current_context = {}
    
    async def pop_context(self):
        """Restore context from stack."""
        if self.context_stack:
            self.current_context = self.context_stack.pop()
    
    async def add_conversation_turn(self, speaker: str, text: str, timestamp: Optional[datetime] = None):
        """Add a turn to conversation history."""
        
        turn = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp or datetime.now()
        }
        
        self.conversation_history.append(turn)
        
        try:
            node = self.kg.add_node(
                f"conversation_{len(self.conversation_history)}",
                NodeType.MEMORY,
                f"{speaker}: {text[:50]}"
            )
        except Exception as e:
            self.logger.error(f"Error adding conversation to knowledge graph: {e}")
    
    async def add_situational_context(self, context_type: str, data: Dict[str, Any]):
        """Add situational context."""
        
        situational = {
            "type": context_type,
            "data": data,
            "timestamp": datetime.now()
        }
        
        self.situational_context.append(situational)
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict]:
        """Get conversation history."""
        return list(self.conversation_history)[-limit:]
    
    def get_recent_context(self, key_pattern: str = None) -> Dict[str, Any]:
        """Get recent context, optionally filtered by key pattern."""
        
        context = {}
        
        for key, entry in self.current_context.items():
            if key_pattern is None or key_pattern in key:
                context[key] = entry["value"]
        
        return context
    
    def clear_context(self):
        """Clear current context."""
        self.current_context = {}


_global_vision_agent: VisionAgent = None
_global_voice_agent: VoiceAgent = None
_global_context_memory: ContextMemory = None


def get_vision_agent() -> VisionAgent:
    """Get or create the global vision agent."""
    global _global_vision_agent
    if _global_vision_agent is None:
        _global_vision_agent = VisionAgent()
    return _global_vision_agent


def get_voice_agent() -> VoiceAgent:
    """Get or create the global voice agent."""
    global _global_voice_agent
    if _global_voice_agent is None:
        _global_voice_agent = VoiceAgent()
    return _global_voice_agent


def get_context_memory() -> ContextMemory:
    """Get or create the global context memory."""
    global _global_context_memory
    if _global_context_memory is None:
        _global_context_memory = ContextMemory()
    return _global_context_memory
