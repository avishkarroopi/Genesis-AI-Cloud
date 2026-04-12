"""
GENESIS Phase-3 — Visual Enrollment & Identity System
Module 7: Face enrollment, person recognition, identity memory, relationship linking.

HARDENED VERSION:
  - InsightFace embedding is OPTIONAL (auto-fallback to label matching)
  - GPU support detected automatically
  - Safe boot guaranteed regardless of InsightFace availability

Subscribes to: VISION_DETECTED
Publishes: PERSON_IDENTIFIED
Links identities to knowledge_graph.py for relationship storage.
"""

import logging
import time
import os
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Optional InsightFace ──
INSIGHTFACE_AVAILABLE = False
_face_analyzer = None

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
    logger.info("[IDENTITY] InsightFace available — face embedding enabled")
except ImportError:
    logger.info("[IDENTITY] InsightFace not installed — using label-based fallback")
except Exception as e:
    logger.warning(f"[IDENTITY] InsightFace init error (label fallback active): {e}")


def _get_face_analyzer():
    """Lazy-init InsightFace analyzer. Returns None if unavailable."""
    global _face_analyzer
    if not INSIGHTFACE_AVAILABLE:
        return None
    if _face_analyzer is not None:
        return _face_analyzer
    try:
        _face_analyzer = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        _face_analyzer.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("[IDENTITY] InsightFace analyzer ready")
        return _face_analyzer
    except Exception as e:
        logger.warning(f"[IDENTITY] InsightFace analyzer init failed: {e}")
        return None


def cosine_similarity(a, b) -> float:
    """Compute cosine similarity between two embedding vectors."""
    try:
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(dot / norm)
    except Exception:
        return 0.0


class IdentityProfile:
    """Represents an enrolled person's identity."""

    def __init__(self, person_id: str, name: str, metadata: Dict = None):
        self.person_id = person_id
        self.name = name
        self.enrolled_at = datetime.now().isoformat()
        self.last_seen = None
        self.sighting_count = 0
        self.relationship = "unknown"
        self.metadata = metadata or {}
        self.face_embedding: Optional[List[float]] = None  # InsightFace vector

    def to_dict(self) -> Dict:
        return {
            "person_id": self.person_id,
            "name": self.name,
            "enrolled_at": self.enrolled_at,
            "last_seen": self.last_seen,
            "sighting_count": self.sighting_count,
            "relationship": self.relationship,
            "metadata": self.metadata,
            "has_embedding": self.face_embedding is not None,
        }


EMBEDDING_MATCH_THRESHOLD = 0.6  # Cosine similarity threshold


class IdentitySystem:
    """
    Face enrollment and person recognition system.
    Uses InsightFace embeddings when available, falls back to label matching.
    """

    def __init__(self):
        self._identities: Dict[str, IdentityProfile] = {}
        self._bus = None
        self._use_embeddings = INSIGHTFACE_AVAILABLE
        logger.info(f"[IDENTITY] System initialized (embeddings={'ON' if self._use_embeddings else 'OFF'})")

    def bind_event_bus(self):
        try:
            from core.event_bus import get_event_bus
            self._bus = get_event_bus()
            if self._bus:
                self._bus.subscribe("VISION_DETECTED", self._on_vision)
                logger.info("[IDENTITY] Event bus bound")
        except Exception as e:
            logger.warning(f"[IDENTITY] Event bus binding failed: {e}")

    def enroll_person(self, name: str, relationship: str = "unknown",
                      metadata: Dict = None, face_image=None) -> IdentityProfile:
        """
        Enroll a new person identity.
        If face_image (numpy array) is provided and InsightFace is available,
        extract and store face embedding.
        """
        person_id = f"person_{name.lower().replace(' ', '_')}_{int(time.time())}"
        profile = IdentityProfile(person_id, name, metadata)
        profile.relationship = relationship

        # Extract face embedding if possible
        if face_image is not None and self._use_embeddings:
            embedding = self._extract_embedding(face_image)
            if embedding is not None:
                profile.face_embedding = embedding
                logger.info(f"[IDENTITY] Face embedding stored for {name}")

        self._identities[person_id] = profile

        # Link to knowledge graph
        try:
            from core.knowledge_graph import get_knowledge_graph, NodeType, RelationType
            kg = get_knowledge_graph()
            kg.add_node(person_id, NodeType.PERSON, name,
                        properties={"relationship": relationship})

            if relationship != "unknown":
                owner_nodes = kg.query_by_type(NodeType.OWNER_PROFILE)
                if owner_nodes:
                    kg.add_relationship(owner_nodes[0].node_id, person_id,
                                        RelationType.KNOWS, {"relationship": relationship})
        except Exception as e:
            logger.warning(f"[IDENTITY] Graph linking failed: {e}")

        logger.info(f"[IDENTITY] Enrolled: {name} ({relationship})")
        return profile

    def identify_person(self, detection_data: Dict, face_image=None) -> Optional[IdentityProfile]:
        """
        Attempt to identify a detected person.
        Strategy:
          1. If face_image + InsightFace available → embedding comparison
          2. Fallback → label-based matching
        """
        # Strategy 1: Embedding match
        if face_image is not None and self._use_embeddings:
            match = self._identify_by_embedding(face_image)
            if match:
                match.last_seen = datetime.now().isoformat()
                match.sighting_count += 1
                return match

        # Strategy 2: Label match (fallback — always available)
        label = detection_data.get("label", "").lower()
        for profile in self._identities.values():
            if profile.name.lower() in label or label in profile.name.lower():
                profile.last_seen = datetime.now().isoformat()
                profile.sighting_count += 1
                return profile

        return None

    def _identify_by_embedding(self, face_image) -> Optional[IdentityProfile]:
        """Compare face image embedding against enrolled identities."""
        query_embedding = self._extract_embedding(face_image)
        if query_embedding is None:
            return None

        best_match = None
        best_score = 0.0

        for profile in self._identities.values():
            if profile.face_embedding is not None:
                score = cosine_similarity(query_embedding, profile.face_embedding)
                if score > best_score and score >= EMBEDDING_MATCH_THRESHOLD:
                    best_score = score
                    best_match = profile

        if best_match:
            logger.info(f"[IDENTITY] Embedding match: {best_match.name} (score={best_score:.3f})")

        return best_match

    def _extract_embedding(self, face_image) -> Optional[List[float]]:
        """Extract face embedding from image using InsightFace."""
        analyzer = _get_face_analyzer()
        if analyzer is None:
            return None

        try:
            faces = analyzer.get(face_image)
            if faces and len(faces) > 0:
                return faces[0].embedding.tolist()
        except Exception as e:
            logger.error(f"[IDENTITY] Embedding extraction failed: {e}")

        return None

    def _on_vision(self, event):
        try:
            data = event.data if hasattr(event, 'data') else event
            label = data.get("label", "")
            if "person" in label.lower():
                identified = self.identify_person(data)
                if identified and self._bus:
                    self._bus.publish_sync("PERSON_IDENTIFIED", "identity_system",
                                            identified.to_dict())
        except Exception as e:
            logger.error(f"[IDENTITY] Vision handler error: {e}")

    def get_enrolled(self) -> List[Dict]:
        return [p.to_dict() for p in self._identities.values()]

    def get_status(self) -> Dict[str, Any]:
        return {
            "enrolled_identities": len(self._identities),
            "total_sightings": sum(p.sighting_count for p in self._identities.values()),
            "embedding_mode": self._use_embeddings,
            "insightface_available": INSIGHTFACE_AVAILABLE,
        }


_identity_system = None


def get_identity_system() -> IdentitySystem:
    global _identity_system
    if _identity_system is None:
        _identity_system = IdentitySystem()
    return _identity_system


def start_identity_system():
    system = get_identity_system()
    system.bind_event_bus()
    mode = "InsightFace embeddings" if INSIGHTFACE_AVAILABLE else "label-based fallback"
    print(f"[IDENTITY] Visual Enrollment & Identity System started ({mode})", flush=True)
    return system
