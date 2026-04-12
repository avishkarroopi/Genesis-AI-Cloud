"""
Owner profile and authentication system for GENESIS + JARVIS.
Handles owner identification, authentication, and profile management.
Requirements: 1, 2, 3, 4.
"""

import asyncio
import logging
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

from core.event_bus import get_event_bus, EventPriority
from core.knowledge_graph import get_knowledge_graph, NodeType, RelationType

try:
    import face_recognition
    import numpy as np
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


class AuthenticationMethod(Enum):
    VOICE = "voice"
    FACE = "face"
    PASSWORD = "password"


@dataclass
class AuthResponse:
    """Authentication response."""
    authenticated: bool
    method: AuthenticationMethod
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""


class NameNormalizer:
    """
    Normalize spoken names to canonical form.
    Requirement 1: Correct name recognition for 'Avishkar'.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.normalizations = {
            "avishkar": "Avishkar",
            "avishkaar": "Avishkar",
            "aveshkar": "Avishkar",
            "ehvishkar": "Avishkar",
            "aviskar": "Avishkar",
            "avikar": "Avishkar",
            "avishcar": "Avishkar",
            "avishkur": "Avishkar",
        }
        
    def normalize(self, name: str) -> Tuple[str, float]:
        """
        Normalize a name to canonical form.
        Returns: (normalized_name, confidence)
        """
        if not name:
            return "", 0.0
        
        lower_name = name.lower().strip()
        
        if lower_name in self.normalizations:
            return self.normalizations[lower_name], 1.0
        
        for variant, canonical in self.normalizations.items():
            if self._string_similarity(lower_name, variant) > 0.7:
                return canonical, 0.7
        
        return name, 0.0
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        return matches / max(len(s1), len(s2))


class OwnerProfile:
    """
    Manages owner profile and personal information.
    Requirement 3: Owner Profile Memory System.
    """
    
    PROFILE_FIELDS = [
        "name", "age", "profession", "achievements",
        "projects", "relationships", "preferences",
        "history", "awards", "skills"
    ]
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.kg = get_knowledge_graph()
        self.profile_data: Dict[str, Any] = {}
        self._initialize_profile()
    
    def _initialize_profile(self):
        """Initialize or load owner profile from knowledge graph."""
        existing = self.kg.get_node("owner_profile")
        
        if existing:
            self.profile_data = {
                key: existing.get_property(key, None)
                for key in self.PROFILE_FIELDS
            }
        else:
            self.profile_data = {key: None for key in self.PROFILE_FIELDS}
            
            self.profile_data.update({
                "name": "Dr. Avishkar Roopi",
                "profession": "Music Educator, Founder of Muziclly Global, Polymath",
                "relationships": {
                    "wife": "Lokeshwari Gurram",
                    "children": [
                        {"name": "Samarth", "dob": "28/11/2017"},
                        {"name": "Prakyath", "dob": "02/03/2022"}
                    ]
                },
                "history": {
                    "dob": "02/05/1992",
                    "experience_years": 15,
                    "honorary_doctorate": True,
                    "location": "Hyderabad"
                },
                "skills": [
                    "music",
                    "ai",
                    "robotics",
                    "programming",
                    "teaching",
                    "automation",
                    "electronics"
                ],
                "projects": [
                    "Muziclly Global",
                    "Genesis AI",
                    "Jarvis Robot"
                ]
            })

            node = self.kg.add_node(
                "owner_profile",
                NodeType.OWNER_PROFILE,
                "Owner Profile",
                properties=self.profile_data
            )
            self.logger.info("Created new owner profile node")
    
    def set_profile_field(self, field_name: str, value: Any, source: str = "system"):
        """Set a profile field."""
        if field_name not in self.PROFILE_FIELDS:
            raise ValueError(f"Invalid profile field: {field_name}")
        
        self.profile_data[field_name] = value
        node = self.kg.get_node("owner_profile")
        if node:
            node.add_property(field_name, value, confidence=1.0, source=source)
        
        self.logger.info(f"Updated profile field: {field_name}")
    
    def get_profile_field(self, field_name: str) -> Any:
        """Get a profile field."""
        return self.profile_data.get(field_name)
    
    def get_full_profile(self) -> Dict[str, Any]:
        """Get complete profile."""
        return self.profile_data.copy()
    
    def add_achievement(self, achievement: str, date: str = None):
        """Add an achievement to the profile."""
        achievements = self.profile_data.get("achievements") or []
        if isinstance(achievements, str):
            achievements = [achievements]
        
        achievements.append({
            "description": achievement,
            "date": date or datetime.now().isoformat()
        })
        
        self.set_profile_field("achievements", achievements, source="achievement_system")
    
    def add_project(self, project_name: str, description: str = ""):
        """Add a project to the profile."""
        projects = self.profile_data.get("projects") or []
        if isinstance(projects, str):
            projects = [projects]
        
        projects.append({
            "name": project_name,
            "description": description,
            "added_date": datetime.now().isoformat()
        })
        
        self.set_profile_field("projects", projects, source="project_system")
    
    def add_skill(self, skill: str, proficiency: str = "intermediate"):
        """Add a skill to the profile."""
        skills = self.profile_data.get("skills") or []
        if isinstance(skills, str):
            skills = [skills]
        
        skills.append({
            "name": skill,
            "proficiency": proficiency,
            "learned_date": datetime.now().isoformat()
        })
        
        self.set_profile_field("skills", skills)
    
    def export_profile(self) -> str:
        """Export profile to JSON."""
        return json.dumps(self.profile_data, indent=2, default=str)


class OwnerAuthentication:
    """
    Multi-modal owner authentication.
    Requirement 4: Owner Authentication (voice, face, password).
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.event_bus = get_event_bus()
        self.kg = get_knowledge_graph()
        self.name_normalizer = NameNormalizer(logger)
        self.profile = OwnerProfile(logger)
        
        self.voice_embeddings = []
        self.face_encodings = []
        self.password_hash = None
        self.authenticated_user = None
        self.authentication_timestamp = None
    
    async def authenticate_by_voice_name(self, recognized_text: str) -> AuthResponse:
        """
        Authenticate by voice recognition of owner's name.
        Handles name variations.
        """
        normalized_name, confidence = self.name_normalizer.normalize(recognized_text)
        
        if confidence > 0.5 and normalized_name == "Avishkar":
            response = AuthResponse(
                authenticated=True,
                method=AuthenticationMethod.VOICE,
                confidence=confidence,
                message=f"Voice authenticated as {normalized_name}"
            )
            
            await self.event_bus.publish(
                "owner_authenticated",
                "authentication_system",
                {
                    "method": "voice_name",
                    "name": normalized_name,
                    "confidence": confidence
                },
                priority=EventPriority.HIGH
            )
            
            self.authenticated_user = normalized_name
            self.authentication_timestamp = datetime.now()
            self.logger.info(f"Voice authentication successful: {normalized_name}")
            return response
        
        return AuthResponse(
            authenticated=False,
            method=AuthenticationMethod.VOICE,
            confidence=confidence,
            message="Voice authentication failed"
        )
    
    async def authenticate_by_face(self, face_image) -> AuthResponse:
        """
        Authenticate by face recognition.
        Requires pre-registered face encoding.
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return AuthResponse(
                authenticated=False,
                method=AuthenticationMethod.FACE,
                confidence=0.0,
                message="Face recognition not available"
            )
        
        try:
            face_encodings = face_recognition.face_encodings(face_image)
            if not face_encodings:
                return AuthResponse(
                    authenticated=False,
                    method=AuthenticationMethod.FACE,
                    confidence=0.0,
                    message="No face detected"
                )
            
            current_encoding = face_encodings[0]
            
            if not self.face_encodings:
                self.face_encodings.append(current_encoding)
                return AuthResponse(
                    authenticated=False,
                    method=AuthenticationMethod.FACE,
                    confidence=0.0,
                    message="Face registered for future authentication"
                )
            
            distances = face_recognition.face_distance(
                self.face_encodings,
                current_encoding
            )
            best_match_distance = np.min(distances)
            
            if best_match_distance < 0.6:
                confidence = 1.0 - best_match_distance
                
                await self.event_bus.publish(
                    "owner_authenticated",
                    "authentication_system",
                    {
                        "method": "face_recognition",
                        "confidence": confidence
                    },
                    priority=EventPriority.HIGH
                )
                
                self.authenticated_user = "Avishkar"
                self.authentication_timestamp = datetime.now()
                self.logger.info(f"Face authentication successful (confidence: {confidence})")
                
                return AuthResponse(
                    authenticated=True,
                    method=AuthenticationMethod.FACE,
                    confidence=confidence,
                    message="Face authentication successful"
                )
            else:
                return AuthResponse(
                    authenticated=False,
                    method=AuthenticationMethod.FACE,
                    confidence=1.0 - best_match_distance,
                    message="Face does not match owner profile"
                )
        
        except Exception as e:
            self.logger.error(f"Face authentication error: {e}")
            return AuthResponse(
                authenticated=False,
                method=AuthenticationMethod.FACE,
                confidence=0.0,
                message=f"Face authentication error: {e}"
            )
    
    async def authenticate_by_password(self, password: str) -> AuthResponse:
        """Authenticate by password."""
        if not self.password_hash:
            return AuthResponse(
                authenticated=False,
                method=AuthenticationMethod.PASSWORD,
                confidence=0.0,
                message="No password set"
            )
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash == self.password_hash:
            await self.event_bus.publish(
                "owner_authenticated",
                "authentication_system",
                {"method": "password"},
                priority=EventPriority.HIGH
            )
            
            self.authenticated_user = "Avishkar"
            self.authentication_timestamp = datetime.now()
            self.logger.info("Password authentication successful")
            
            return AuthResponse(
                authenticated=True,
                method=AuthenticationMethod.PASSWORD,
                confidence=1.0,
                message="Password authentication successful"
            )
        
        return AuthResponse(
            authenticated=False,
            method=AuthenticationMethod.PASSWORD,
            confidence=0.0,
            message="Incorrect password"
        )
    
    def set_password(self, password: str):
        """Set authentication password."""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.logger.info("Password set")
    
    def register_face(self, face_image):
        """Register owner's face."""
        if not FACE_RECOGNITION_AVAILABLE:
            self.logger.warning("Face recognition not available")
            return
        
        try:
            encodings = face_recognition.face_encodings(face_image)
            if encodings:
                self.face_encodings.append(encodings[0])
                self.logger.info("Face registered for authentication")
        except Exception as e:
            self.logger.error(f"Face registration error: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if not self.authenticated_user:
            return False
        
        if not self.authentication_timestamp:
            return False
        
        session_duration = (datetime.now() - self.authentication_timestamp).total_seconds()
        session_timeout = 3600
        
        return session_duration < session_timeout
    
    def get_access_level(self) -> str:
        """Get current access level."""
        if self.is_authenticated():
            return "admin"
        return "guest"
    
    async def logout(self):
        """Logout the current user."""
        if self.authenticated_user:
            await self.event_bus.publish(
                "owner_logout",
                "authentication_system",
                {"user": self.authenticated_user}
            )
            self.authenticated_user = None
            self.authentication_timestamp = None
            self.logger.info("User logged out")


class RespectfulAddressing:
    """
    Manage respectful addressing of the owner.
    Requirement 2: Respectful Addressing.
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.primary_title = "Sir"
        self.occasional_titles = ["Boss", "Avishkar"]
        self.title_counter = 0
    
    def get_next_title(self) -> str:
        """Get next title to use (cycles through occasional titles)."""
        self.title_counter += 1
        
        if self.title_counter % 3 == 0:
            return self.occasional_titles[self.title_counter % len(self.occasional_titles)]
        
        return self.primary_title
    
    def format_greeting(self, custom_greeting: str = None) -> str:
        """Format a greeting with respectful title."""
        title = self.get_next_title()
        
        if custom_greeting:
            return f"{custom_greeting}, {title}"
        
        return f"Hello, {title}"
    
    def format_response(self, response_text: str) -> str:
        """Format a response with respectful addressing."""
        title = self.get_next_title()
        return f"{response_text}, {title}."
