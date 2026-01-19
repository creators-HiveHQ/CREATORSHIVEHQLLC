"""
Creators Hive HQ - Creator Registration Models
Public registration form for new creators
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import uuid

# ============== CREATOR REGISTRATION ==============

class CreatorRegistration(BaseModel):
    """Creator registration from public intake form"""
    id: str = Field(default_factory=lambda: f"CR-{str(uuid.uuid4())[:8]}")
    
    # Basic Info
    name: str
    email: EmailStr
    
    # Platform & Niche
    platforms: List[str] = []  # YouTube, Instagram, TikTok, etc.
    niche: str = ""
    
    # Goals
    goals: str = ""
    
    # ARRIS Intake
    arris_intake_question: str = ""  # Response to ARRIS's intake question
    arris_intake_prompt: str = "What's the biggest challenge you're facing in your creator journey right now?"
    
    # Status & Metadata
    status: str = "pending"  # pending, approved, rejected, active
    registration_source: str = "web_form"
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    notes: str = ""
    
    # Auto-assigned after approval
    assigned_tier: str = "Free"
    assigned_user_id: Optional[str] = None  # Links to 01_Users after approval

class CreatorRegistrationCreate(BaseModel):
    """Public form submission - minimal required fields"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    platforms: List[str] = Field(default=[], description="Selected platforms")
    niche: str = Field(default="", max_length=200)
    goals: str = Field(default="", max_length=1000)
    arris_intake_question: str = Field(default="", max_length=2000)

class CreatorRegistrationUpdate(BaseModel):
    """Admin update for registration status"""
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_tier: Optional[str] = None

class CreatorRegistrationResponse(BaseModel):
    """Response after successful registration"""
    id: str
    name: str
    email: str
    status: str
    message: str
    submitted_at: str

# ============== PLATFORM OPTIONS ==============

PLATFORM_OPTIONS = [
    {"value": "youtube", "label": "YouTube", "icon": "📺"},
    {"value": "instagram", "label": "Instagram", "icon": "📸"},
    {"value": "tiktok", "label": "TikTok", "icon": "🎵"},
    {"value": "twitter", "label": "Twitter/X", "icon": "🐦"},
    {"value": "linkedin", "label": "LinkedIn", "icon": "💼"},
    {"value": "podcast", "label": "Podcast", "icon": "🎙️"},
    {"value": "blog", "label": "Blog/Website", "icon": "📝"},
    {"value": "newsletter", "label": "Newsletter", "icon": "📧"},
    {"value": "twitch", "label": "Twitch", "icon": "🎮"},
    {"value": "patreon", "label": "Patreon/Membership", "icon": "💰"},
    {"value": "courses", "label": "Online Courses", "icon": "🎓"},
    {"value": "other", "label": "Other", "icon": "➕"},
]

NICHE_OPTIONS = [
    "Business & Entrepreneurship",
    "Tech & Software",
    "Finance & Investing",
    "Health & Fitness",
    "Lifestyle & Travel",
    "Food & Cooking",
    "Gaming",
    "Education & Learning",
    "Entertainment",
    "Art & Design",
    "Music",
    "Fashion & Beauty",
    "Parenting & Family",
    "Personal Development",
    "Other",
]

# ARRIS Intake Questions (rotated for variety)
ARRIS_INTAKE_QUESTIONS = [
    "What's the biggest challenge you're facing in your creator journey right now?",
    "If you could wave a magic wand and solve one problem in your business, what would it be?",
    "What does success look like for you in the next 12 months?",
    "What's holding you back from reaching your next level?",
    "Describe your ideal audience - who are you trying to reach and help?",
]
