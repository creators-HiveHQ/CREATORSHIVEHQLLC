"""
Creators Hive HQ - Core System Models
=====================================
Data models for Intake Form, Engines, Tracks, and System State.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


# ============== USER IDENTITY ==============

class UserIdentityType(str, Enum):
    """User identity type - determines track assignment"""
    CREATOR = "creator"
    BUSINESS = "business"
    HYBRID = "hybrid"


class UserStage(str, Enum):
    """User experience stage"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ============== ENGINE TYPES ==============

class EngineType(str, Enum):
    """The four core engines of the system"""
    BUSINESS = "business_engine"
    ENGAGEMENT = "engagement_engine"
    ROLE = "role_engine"
    INCOME = "income_engine"


class EngineStatus(str, Enum):
    """Engine activation status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"


# ============== TRACK TYPES ==============

class TrackType(str, Enum):
    """User track assignment"""
    CREATOR = "creator_track"
    BUSINESS = "business_track"
    HYBRID = "hybrid_track"


# ============== INTAKE FORM ==============

class IntakeUserIdentity(BaseModel):
    """Section 1: User Identity"""
    identity_type: UserIdentityType
    stage: UserStage
    primary_goal: str = Field(..., min_length=5, max_length=500)


class IntakeSystemNeed(BaseModel):
    """Section 2: System Need - which engines required"""
    business_engine: bool = False
    engagement_engine: bool = False
    role_engine: bool = False
    income_engine: bool = False


class IntakeStartingPoint(BaseModel):
    """Section 3: Starting Point"""
    what_they_have: str = Field(..., min_length=5, max_length=1000)
    what_is_missing: str = Field(..., min_length=5, max_length=1000)
    first_accomplishment: str = Field(..., min_length=5, max_length=500)


class IntakeFormSubmission(BaseModel):
    """Complete Intake Form submission"""
    user_identity: IntakeUserIdentity
    system_need: IntakeSystemNeed
    starting_point: IntakeStartingPoint


class IntakeFormResponse(BaseModel):
    """Response after intake form submission"""
    intake_id: str
    user_id: str
    assigned_track: TrackType
    activated_engines: List[EngineType]
    unlocked_modules: List[str]
    next_steps: List[str]
    message: str


# ============== ENGINE STATE ==============

class EngineState(BaseModel):
    """State of a single engine"""
    engine_type: EngineType
    status: EngineStatus = EngineStatus.INACTIVE
    progress: float = 0.0  # 0-100
    inputs_received: int = 0
    outputs_generated: int = 0
    blockers: List[str] = []
    dependencies_met: bool = False
    last_activity: Optional[str] = None


class EngineConfig(BaseModel):
    """Configuration for an engine"""
    engine_type: EngineType
    inputs: List[str]
    outputs: List[str]
    rules: List[str]
    dependencies: List[EngineType]
    required_modules: List[str]


# ============== USER SYSTEM STATE ==============

class UserSystemState(BaseModel):
    """Complete system state for a user"""
    id: str = Field(default_factory=lambda: f"USS-{str(uuid.uuid4())[:8]}")
    user_id: str
    
    # Intake data
    intake_completed: bool = False
    intake_id: Optional[str] = None
    intake_data: Optional[Dict[str, Any]] = None
    
    # Track assignment
    assigned_track: Optional[TrackType] = None
    
    # Identity
    identity_type: Optional[UserIdentityType] = None
    stage: Optional[UserStage] = None
    primary_goal: Optional[str] = None
    
    # Starting point
    what_they_have: Optional[str] = None
    what_is_missing: Optional[str] = None
    first_accomplishment: Optional[str] = None
    
    # Engine states
    engines: Dict[str, EngineState] = {}
    
    # Unlocked modules
    unlocked_modules: List[str] = []
    
    # Active items
    active_modules: List[str] = []
    incomplete_items: List[str] = []
    next_steps: List[str] = []
    blockers: List[str] = []
    
    # AI outputs
    arris_recommendations: List[str] = []  # Structure, clarity, logic
    millicent_guidance: List[str] = []     # Tone, resonance, communication
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============== DASHBOARD STATE ==============

class DashboardState(BaseModel):
    """Dashboard command center state"""
    user_id: str
    track: Optional[TrackType] = None
    
    # What's active
    active_modules: List[Dict[str, Any]] = []
    
    # What's incomplete
    incomplete_items: List[Dict[str, Any]] = []
    
    # What's next
    next_steps: List[Dict[str, Any]] = []
    
    # What's blocked
    blockers: List[Dict[str, Any]] = []
    
    # Engine activity
    engine_status: Dict[str, EngineState] = {}
    
    # ARRIS outputs (structure, clarity, logic)
    arris_outputs: List[Dict[str, Any]] = []
    
    # Millicent outputs (tone, resonance, communication)
    millicent_outputs: List[Dict[str, Any]] = []
    
    # Summary stats
    overall_progress: float = 0.0
    engines_active: int = 0
    modules_unlocked: int = 0
    
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== MODULE DEFINITION ==============

class ModuleDefinition(BaseModel):
    """Definition of a system module"""
    module_id: str
    name: str
    purpose: str
    inputs: List[str]
    outputs: List[str]
    engine_connections: List[EngineType]
    required_for_tracks: List[TrackType]
    prerequisites: List[str] = []
    is_core: bool = False


# ============== ARRIS STRUCTURAL OUTPUT ==============

class ArrisStructuralOutput(BaseModel):
    """ARRIS output - structure, clarity, logic"""
    output_id: str = Field(default_factory=lambda: f"ARRIS-{str(uuid.uuid4())[:8]}")
    user_id: str
    output_type: str  # "structure", "clarity", "logic"
    context: str
    recommendation: str
    priority: str = "medium"  # low, medium, high, critical
    related_module: Optional[str] = None
    related_engine: Optional[EngineType] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== MILLICENT TONE OUTPUT ==============

class MillicentToneOutput(BaseModel):
    """Millicent output - tone, resonance, communication (rule-based)"""
    output_id: str = Field(default_factory=lambda: f"MILL-{str(uuid.uuid4())[:8]}")
    user_id: str
    output_type: str  # "tone", "resonance", "communication"
    context: str
    guidance: str
    tone_style: str  # "professional", "friendly", "authoritative", "empathetic"
    related_module: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
