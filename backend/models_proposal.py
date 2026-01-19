"""
Creators Hive HQ - Project Proposal Models
Project proposal workflow with ARRIS AI insights
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# ============== PROJECT PROPOSAL ==============

class ProjectProposal(BaseModel):
    """Project proposal from creators"""
    id: str = Field(default_factory=lambda: f"PP-{str(uuid.uuid4())[:8]}")
    
    # Creator Info
    user_id: str  # Link to 01_Users or creators collection
    creator_name: str = ""
    creator_email: str = ""
    
    # Project Details
    title: str
    description: str
    goals: str = ""
    platforms: List[str] = []  # Platforms involved in the project
    
    # Timeline
    timeline: str = ""  # e.g., "2-4 weeks", "1 month", "Q1 2026"
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    estimated_hours: float = 0.0
    
    # ARRIS Intake
    arris_intake_question: str = ""  # Response to ARRIS's project question
    arris_intake_prompt: str = "What's the main outcome you want from this project?"
    
    # ARRIS AI Insights (generated)
    arris_insights: Optional[Dict[str, Any]] = None
    arris_insights_generated_at: Optional[datetime] = None
    
    # Status & Workflow
    status: str = "draft"  # draft, submitted, under_review, approved, in_progress, completed, rejected
    priority: str = "medium"  # low, medium, high, critical
    
    # Review
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: str = ""
    
    # Approval creates project in 04_Projects
    assigned_project_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectProposalCreate(BaseModel):
    """Create a new project proposal"""
    user_id: str
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    goals: str = Field(default="", max_length=2000)
    platforms: List[str] = Field(default=[])
    timeline: str = Field(default="", max_length=200)
    estimated_hours: float = Field(default=0.0, ge=0)
    arris_intake_question: str = Field(default="", max_length=3000)
    priority: str = Field(default="medium")

class ProjectProposalUpdate(BaseModel):
    """Update a project proposal"""
    title: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[str] = None
    platforms: Optional[List[str]] = None
    timeline: Optional[str] = None
    estimated_hours: Optional[float] = None
    arris_intake_question: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    review_notes: Optional[str] = None

class ProjectProposalResponse(BaseModel):
    """Response after creating/submitting proposal"""
    id: str
    title: str
    status: str
    message: str
    arris_insights: Optional[Dict[str, Any]] = None

# ============== ARRIS INSIGHTS STRUCTURE ==============

class ArrisInsights(BaseModel):
    """Structure for ARRIS-generated insights"""
    summary: str = ""  # Brief summary of the project
    strengths: List[str] = []  # What's strong about this proposal
    risks: List[str] = []  # Potential risks or challenges
    recommendations: List[str] = []  # Strategic recommendations
    estimated_complexity: str = ""  # Low, Medium, High
    success_probability: str = ""  # Estimate based on patterns
    suggested_milestones: List[str] = []  # Suggested project milestones
    related_patterns: List[str] = []  # Patterns from Memory Palace
    resource_suggestions: str = ""  # Suggested resources/tools

# ============== TIMELINE OPTIONS ==============

TIMELINE_OPTIONS = [
    {"value": "1-2_weeks", "label": "1-2 Weeks", "days": 14},
    {"value": "2-4_weeks", "label": "2-4 Weeks", "days": 28},
    {"value": "1-2_months", "label": "1-2 Months", "days": 60},
    {"value": "3-6_months", "label": "3-6 Months", "days": 180},
    {"value": "6-12_months", "label": "6-12 Months", "days": 365},
    {"value": "ongoing", "label": "Ongoing / No Fixed End", "days": 0},
]

PRIORITY_OPTIONS = [
    {"value": "low", "label": "Low", "color": "slate"},
    {"value": "medium", "label": "Medium", "color": "blue"},
    {"value": "high", "label": "High", "color": "orange"},
    {"value": "critical", "label": "Critical", "color": "red"},
]

STATUS_OPTIONS = [
    {"value": "draft", "label": "Draft", "color": "slate"},
    {"value": "submitted", "label": "Submitted", "color": "blue"},
    {"value": "under_review", "label": "Under Review", "color": "purple"},
    {"value": "approved", "label": "Approved", "color": "green"},
    {"value": "in_progress", "label": "In Progress", "color": "amber"},
    {"value": "completed", "label": "Completed", "color": "emerald"},
    {"value": "rejected", "label": "Rejected", "color": "red"},
]

# ARRIS Project Intake Questions
ARRIS_PROJECT_QUESTIONS = [
    "What's the main outcome you want from this project?",
    "How will you measure success for this project?",
    "What resources or support do you need to make this happen?",
    "What's the biggest obstacle you anticipate?",
    "How does this project align with your overall creator goals?",
]
