"""
Creators Hive HQ - Master Database Models
Based on Sheet 15 Index - Schema Map
Implements No-Assumption Protocol with full normalization
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from enum import Enum

# ============== ENUMS (from 16_Lookups) ==============

class TierEnum(str, Enum):
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"
    FREE = "Free"

class RoleEnum(str, Enum):
    CREATOR = "Creator"
    COACH = "Coach"
    STAFF = "Staff"
    ADMIN = "Admin"

class StatusEnum(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    COMPLETED = "Completed"
    LAPSED = "Lapsed"

class PriorityEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class SeverityEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# ============== BASE MODEL ==============

class BaseDBModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== 01_USERS ==============

class User(BaseDBModel):
    id: str = Field(default_factory=lambda: f"U-{str(uuid.uuid4())[:8]}")
    user_id: str = Field(default="")  # Legacy field for compatibility
    name: str
    email: str
    role: str = "Creator"
    business_type: str = ""
    tier: str = "Free"
    account_status: str = "Active"
    last_login_date: Optional[datetime] = None

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "Creator"
    business_type: str = ""
    tier: str = "Free"

# ============== 02_BRANDING_KITS ==============

class BrandingKit(BaseDBModel):
    id: str = Field(default_factory=lambda: f"BK-{str(uuid.uuid4())[:6]}")
    kit_id: str = Field(default="")
    user_id: str
    logo_url: str = ""
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    watermark_url: str = ""
    font_family: str = "Roboto"
    default_template: str = ""

class BrandingKitCreate(BaseModel):
    user_id: str
    logo_url: str = ""
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    font_family: str = "Roboto"
    default_template: str = ""

# ============== 03_COACH_KITS ==============

class CoachKit(BaseDBModel):
    id: str = Field(default_factory=lambda: f"CK-{str(uuid.uuid4())[:6]}")
    kit_id: str = Field(default="")
    user_id: str
    template_name: str
    enabled_modules: str = ""
    target_niche: str = ""
    access_level: str = "User"
    is_premium: bool = False
    last_updated: Optional[datetime] = None

class CoachKitCreate(BaseModel):
    user_id: str
    template_name: str
    enabled_modules: str = ""
    target_niche: str = ""
    access_level: str = "User"
    is_premium: bool = False

# ============== 04_PROJECTS ==============

class Project(BaseDBModel):
    id: str = Field(default_factory=lambda: f"P-{str(uuid.uuid4())[:6]}")
    project_id: str = Field(default="")
    title: str
    platform: str = ""
    status: str = "Planning"
    user_id: str
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    priority_level: str = "Medium"

class ProjectCreate(BaseModel):
    title: str
    platform: str = ""
    user_id: str
    priority_level: str = "Medium"

# ============== 05_TASKS ==============

class Task(BaseDBModel):
    id: str = Field(default_factory=lambda: f"T-{str(uuid.uuid4())[:6]}")
    task_id: str = Field(default="")
    project_id: str
    description: str
    due_date: Optional[datetime] = None
    completion_status: int = 0  # 0 = incomplete, 1 = complete
    assigned_to_user_id: str
    estimated_hours: float = 0.0
    date_completed: Optional[datetime] = None

class TaskCreate(BaseModel):
    project_id: str
    description: str
    assigned_to_user_id: str
    estimated_hours: float = 0.0

# ============== 06_CALCULATOR (REVENUE HUB) ==============

class Calculator(BaseDBModel):
    """Central Revenue Hub - All money flows through here"""
    id: str = Field(default_factory=lambda: f"C-{str(uuid.uuid4())[:6]}")
    calc_id: str = Field(default="")
    user_id: str
    month_year: str  # Format: YYYY-MM
    revenue: float = 0.0
    expenses: float = 0.0
    net_margin: float = 0.0
    category: str = "Income"  # Income or Expense
    source: str = ""  # e.g., "YouTube Ads", "Ebook Sales", "Subscription"
    subscription_id: Optional[str] = None  # Link to 17_Subscriptions

class CalculatorCreate(BaseModel):
    user_id: str
    month_year: str
    revenue: float = 0.0
    expenses: float = 0.0
    category: str = "Income"
    source: str = ""
    subscription_id: Optional[str] = None

# ============== 07_ANALYTICS ==============

class Analytics(BaseDBModel):
    id: str = Field(default_factory=lambda: f"A-{str(uuid.uuid4())[:6]}")
    metric_id: str = Field(default="")
    user_id: str
    platform_views: int = 0
    revenue: float = 0.0
    engagement_score: float = 0.0
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    platform: str = ""
    conversion_rate: float = 0.0

class AnalyticsCreate(BaseModel):
    user_id: str
    platform_views: int = 0
    revenue: float = 0.0
    engagement_score: float = 0.0
    platform: str = ""
    conversion_rate: float = 0.0

# ============== 08_ROLODEX ==============

class Rolodex(BaseDBModel):
    id: str = Field(default_factory=lambda: f"R-{str(uuid.uuid4())[:6]}")
    contact_id: str = Field(default="")
    contact_name: str
    email: str = ""
    phone: str = ""
    notes: str = ""
    company: str = ""
    relationship_type: str = "Prospect"
    last_contact_date: Optional[datetime] = None

class RolodexCreate(BaseModel):
    contact_name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    relationship_type: str = "Prospect"

# ============== 09_CUSTOMERS ==============

class Customer(BaseDBModel):
    id: str = Field(default_factory=lambda: f"CUS-{str(uuid.uuid4())[:6]}")
    customer_id: str = Field(default="")
    user_id: str  # Which creator owns this customer
    name: str
    email: str = ""
    purchase_history: str = ""
    status: str = "Active"
    total_spend: float = 0.0
    last_purchase_date: Optional[datetime] = None

class CustomerCreate(BaseModel):
    user_id: str
    name: str
    email: str = ""
    purchase_history: str = ""

# ============== 10_AFFILIATES ==============

class Affiliate(BaseDBModel):
    id: str = Field(default_factory=lambda: f"AFF-{str(uuid.uuid4())[:6]}")
    affiliate_id: str = Field(default="")
    user_id: str
    program_name: str
    commission_rate: float = 0.10
    earnings: float = 0.0
    payout_status: str = "Pending"
    referral_url: str = ""
    signup_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AffiliateCreate(BaseModel):
    user_id: str
    program_name: str
    commission_rate: float = 0.10

# ============== 11_EMAIL_LOG ==============

class EmailLog(BaseDBModel):
    id: str = Field(default_factory=lambda: f"E-{str(uuid.uuid4())[:6]}")
    email_id: str = Field(default="")
    subject: str
    status: str = "Pending"
    date_sent: Optional[datetime] = None
    recipient_email: str
    user_id_sender: str
    campaign_name: str = ""
    template_used: str = ""

class EmailLogCreate(BaseModel):
    subject: str
    recipient_email: str
    user_id_sender: str
    campaign_name: str = ""

# ============== 12_NOTEPAD ==============

class Notepad(BaseDBModel):
    id: str = Field(default_factory=lambda: f"N-{str(uuid.uuid4())[:6]}")
    note_id: str = Field(default="")
    user_id: str
    idea_note_summary: str
    detail_context: str = ""
    status: str = "Drafting"
    priority: str = "Medium"
    linked_project_id: Optional[str] = None

class NotepadCreate(BaseModel):
    user_id: str
    idea_note_summary: str
    detail_context: str = ""
    linked_project_id: Optional[str] = None

# ============== 13_INTEGRATIONS ==============

class Integration(BaseDBModel):
    id: str = Field(default_factory=lambda: f"I-{str(uuid.uuid4())[:6]}")
    integration_id: str = Field(default="")
    connected_platform: str
    type: str  # e.g., "Email_Marketing", "Payment_Gateway"
    user_id: str
    connection_status: str = "Active"
    api_key_status: str = "Valid"
    date_connected: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scope_of_access: str = ""

class IntegrationCreate(BaseModel):
    connected_platform: str
    type: str
    user_id: str
    scope_of_access: str = ""

# ============== 14_AUDIT ==============

class Audit(BaseDBModel):
    id: str = Field(default_factory=lambda: f"AUD-{str(uuid.uuid4())[:6]}")
    audit_id: str = Field(default="")
    user_id: str
    violation_type: str
    severity: str = "Medium"
    resolution_status: str = "Pending_Review"
    date_of_incident: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auditor_system: str = "System_Monitor"
    remediation_steps: str = ""

class AuditCreate(BaseModel):
    user_id: str
    violation_type: str
    severity: str = "Medium"
    remediation_steps: str = ""

# ============== 16_LOOKUPS ==============

class Lookup(BaseDBModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    standard_id: str  # e.g., "TIER", "ROLE"
    lookup_type: str  # e.g., "T-PLATINUM"
    value: str  # e.g., "Platinum"
    related_field: str = ""  # e.g., "01_Users"
    description: str = ""
    is_active: bool = True

class LookupCreate(BaseModel):
    standard_id: str
    lookup_type: str
    value: str
    related_field: str = ""
    description: str = ""

# ============== 17_SUBSCRIPTIONS ==============

class Subscription(BaseDBModel):
    """Links to 06_Calculator for Self-Funding Loop"""
    id: str = Field(default_factory=lambda: f"SUB-{str(uuid.uuid4())[:6]}")
    subscription_id: str = Field(default="")
    user_id: str
    plan_name: str
    tier: str = "Free"
    monthly_cost: float = 0.0
    payment_status: str = "Active"
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_renewal: Optional[datetime] = None
    # Revenue flows to Calculator
    linked_calc_id: Optional[str] = None

class SubscriptionCreate(BaseModel):
    user_id: str
    plan_name: str
    tier: str = "Free"
    monthly_cost: float = 0.0
