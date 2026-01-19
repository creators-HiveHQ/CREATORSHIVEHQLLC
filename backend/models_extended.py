"""
Creators Hive HQ - Extended Models
ARRIS System, Contracts, Compliance, and Strategic Planning
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# ============== BASE MODEL ==============

class BaseDBModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== 19_ARRIS_USAGE_LOG ==============

class ArrisUsageLog(BaseDBModel):
    """AI Agent Arris - Usage Pattern Tracking"""
    id: str = Field(default_factory=lambda: f"ARRIS-{str(uuid.uuid4())[:6]}")
    log_id: str = Field(default="")
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_query_snippet: str
    response_type: str  # Content_Gen, Data_Analysis, Search_Lookup
    response_id: str = ""  # Links to generated content
    time_taken_s: float = 0.0
    linked_project: Optional[str] = None
    # Pattern Engine fields
    query_category: str = ""  # For pattern analysis
    sentiment: str = ""  # User sentiment
    success: bool = True

class ArrisUsageLogCreate(BaseModel):
    user_id: str
    user_query_snippet: str
    response_type: str
    linked_project: Optional[str] = None

# ============== 20_ARRIS_PERFORMANCE ==============

class ArrisPerformance(BaseDBModel):
    """AI Agent Arris - Performance Reviews"""
    id: str = Field(default_factory=lambda: f"AR-R-{str(uuid.uuid4())[:6]}")
    review_id: str = Field(default="")
    log_id: str  # Foreign key to 19_ARRIS_Usage_Log
    date_reviewed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quality_score: float = 0.0
    error_count: int = 0
    human_reviewer_id: Optional[str] = None
    feedback_tags: str = ""
    final_verdict: str = "Pending"  # Approved, Needs_Correction, Rejected

class ArrisPerformanceCreate(BaseModel):
    log_id: str
    quality_score: float = 0.0
    error_count: int = 0
    feedback_tags: str = ""

# ============== 21_ARRIS_TRAINING_DATA ==============

class ArrisTrainingData(BaseDBModel):
    """AI Agent Arris - Training Data Sources"""
    id: str = Field(default_factory=lambda: f"DS-{str(uuid.uuid4())[:6]}")
    data_source_id: str = Field(default="")
    source_type: str  # Internal_Docs, External_Article, Customer_Feedback
    source_url: str = ""
    date_included: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_summary: str
    version: float = 1.0
    compliance_status: str = "Pending_Review"
    reviewer_id: Optional[str] = None

class ArrisTrainingDataCreate(BaseModel):
    source_type: str
    source_url: str = ""
    content_summary: str

# ============== 22_CLIENT_CONTRACTS ==============

class ClientContract(BaseDBModel):
    id: str = Field(default_factory=lambda: f"CL-{str(uuid.uuid4())[:6]}")
    contract_id: str = Field(default="")
    customer_id: str  # Foreign key to 09_Customers
    contract_title: str
    contract_type: str  # SOW, Service_Agreement, Work_Order
    date_signed: Optional[datetime] = None
    date_ends: Optional[datetime] = None
    total_value: float = 0.0
    status: str = "Draft"

class ClientContractCreate(BaseModel):
    customer_id: str
    contract_title: str
    contract_type: str
    total_value: float = 0.0

# ============== 23_TERMS_OF_SERVICE ==============

class TermsOfService(BaseDBModel):
    id: str = Field(default_factory=lambda: f"TOS-{str(uuid.uuid4())[:6]}")
    tos_id: str = Field(default="")
    user_id: str
    version_no: float = 1.0
    date_agreed: Optional[datetime] = None
    status: str = "Pending"
    effective_date: Optional[datetime] = None
    pdf_link: str = ""
    signup_method: str = "Web_Checkbox"

class TermsOfServiceCreate(BaseModel):
    user_id: str
    version_no: float = 1.0

# ============== 24_PRIVACY_POLICIES ==============

class PrivacyPolicy(BaseDBModel):
    id: str = Field(default_factory=lambda: f"PP-{str(uuid.uuid4())[:6]}")
    policy_id: str = Field(default="")
    user_id: str
    version_no: float = 1.0
    date_agreed: Optional[datetime] = None
    status: str = "Pending"
    effective_date: Optional[datetime] = None
    pdf_link: str = ""
    signup_method: str = "Web_Checkbox"

class PrivacyPolicyCreate(BaseModel):
    user_id: str
    version_no: float = 1.0

# ============== 25_VENDOR_AGREEMENTS ==============

class VendorAgreement(BaseDBModel):
    id: str = Field(default_factory=lambda: f"VAG-{str(uuid.uuid4())[:6]}")
    vendor_id: str = Field(default="")
    company_name: str
    contact_person: str = ""
    agreement_type: str  # Service_Contract, Freelancer_NDA, Maintenance_Agmt
    date_signed: Optional[datetime] = None
    date_ends: Optional[datetime] = None
    service_scope: str = ""
    status: str = "Draft"

class VendorAgreementCreate(BaseModel):
    company_name: str
    agreement_type: str
    service_scope: str = ""

# ============== 26_FORMS_SUBMISSION ==============

class FormSubmission(BaseDBModel):
    id: str = Field(default_factory=lambda: f"FS-{str(uuid.uuid4())[:6]}")
    submission_id: str = Field(default="")
    user_id: str
    form_name: str
    date_submitted: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_status: str = "New"
    submitted_by: str = ""
    linked_ticket_item: str = ""  # Links to other tables
    file_link: str = ""

class FormSubmissionCreate(BaseModel):
    user_id: str
    form_name: str
    linked_ticket_item: str = ""

# ============== 27_INTL_TAXES ==============

class IntlTax(BaseDBModel):
    id: str = Field(default_factory=lambda: f"TAX-{str(uuid.uuid4())[:6]}")
    compliance_id: str = Field(default="")
    region: str
    tax_rate: float = 0.0
    applicable_laws: str = ""
    status: str = "Active"
    effective_date: Optional[datetime] = None

class IntlTaxCreate(BaseModel):
    region: str
    tax_rate: float = 0.0
    applicable_laws: str = ""

# ============== 28_PRODUCT_ROADMAPS ==============

class ProductRoadmap(BaseDBModel):
    id: str = Field(default_factory=lambda: f"RM-{str(uuid.uuid4())[:6]}")
    roadmap_id: str = Field(default="")
    feature_name: str
    description: str = ""
    target_quarter: str = ""  # e.g., "2025-Q1"
    status: str = "Planning"
    owner: str = ""
    priority: str = "Medium"

class ProductRoadmapCreate(BaseModel):
    feature_name: str
    description: str = ""
    target_quarter: str = ""

# ============== 29_MARKETING_CAMPAIGNS ==============

class MarketingCampaign(BaseDBModel):
    id: str = Field(default_factory=lambda: f"MC-{str(uuid.uuid4())[:6]}")
    campaign_id: str = Field(default="")
    campaign_name: str
    channel: str  # Email_Social, YouTube_Paid_Ads, Instagram_Blog
    goal: str = ""
    budget: float = 0.0
    status: str = "Planning"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class MarketingCampaignCreate(BaseModel):
    campaign_name: str
    channel: str
    goal: str = ""
    budget: float = 0.0

# ============== 31_SYSTEM_HEALTH_API_STATUS ==============

class SystemHealth(BaseDBModel):
    id: str = Field(default_factory=lambda: f"SYS-{str(uuid.uuid4())[:6]}")
    system_id: str = Field(default="")
    platform_name: str
    api_endpoint: str = ""
    status: str = "Up"  # Up, Down, Degraded
    last_check_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    response_time_ms: float = 0.0

class SystemHealthCreate(BaseModel):
    platform_name: str
    api_endpoint: str = ""

# ============== 34_DEV_APPROACHES ==============

class DevApproach(BaseDBModel):
    id: str = Field(default_factory=lambda: f"DEV-{str(uuid.uuid4())[:6]}")
    approach_id: str = Field(default="")
    approach_name: str
    key_characteristic: str = ""
    focus_goal: str = ""
    speed_flexibility: str = ""
    risk_level: str = "Medium"

class DevApproachCreate(BaseModel):
    approach_name: str
    key_characteristic: str = ""
    focus_goal: str = ""

# ============== 35_FUNDING_INVESTMENT ==============

class FundingInvestment(BaseDBModel):
    id: str = Field(default_factory=lambda: f"INV-{str(uuid.uuid4())[:6]}")
    investment_id: str = Field(default="")
    investor_name: str
    amount: float = 0.0
    date: Optional[datetime] = None
    funding_round: str = ""  # Seed, Series_A, etc.
    cap_table_link: str = ""
    valuation: float = 0.0

class FundingInvestmentCreate(BaseModel):
    investor_name: str
    amount: float = 0.0
    funding_round: str = ""

# ============== 36_USER_ACTIVITY_LOG ==============

class UserActivityLog(BaseDBModel):
    id: str = Field(default_factory=lambda: f"ACT-{str(uuid.uuid4())[:6]}")
    activity_id: str = Field(default="")
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str  # Page_View, Feature_Click, Form_Submit
    feature_name: str = ""
    session_id: str = ""
    details: str = ""

class UserActivityLogCreate(BaseModel):
    user_id: str
    action: str
    feature_name: str = ""

# ============== 37_INTERNAL_CONTENT_LIBRARY ==============

class InternalContent(BaseDBModel):
    id: str = Field(default_factory=lambda: f"ICL-{str(uuid.uuid4())[:6]}")
    content_id: str = Field(default="")
    content_type: str  # TrainingVideo, ProcessDoc, DesignAssets
    title: str
    internal_owner: str = ""
    date_last_updated: Optional[datetime] = None
    access_level: str = "AllUsers"  # StaffOnly, AdminOnly, AllUsers
    file_link: str = ""

class InternalContentCreate(BaseModel):
    content_type: str
    title: str
    internal_owner: str = ""
    access_level: str = "AllUsers"

# ============== 15_INDEX (Schema Map) ==============

class SchemaIndex(BaseDBModel):
    """Meta-data for schema mapping - Source of Truth"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_no: int
    sheet_name: str
    category: str
    primary_key_field: str
    description: str = ""
    relationships: List[str] = []

# ============== PATTERN ENGINE MODELS ==============

class PatternAnalysis(BaseDBModel):
    """Arris Pattern Engine - Pattern Detection Results"""
    id: str = Field(default_factory=lambda: f"PAT-{str(uuid.uuid4())[:6]}")
    pattern_id: str = Field(default="")
    user_id: Optional[str] = None  # Can be global or user-specific
    pattern_type: str  # Usage, Revenue, Engagement, Behavior
    time_range_start: datetime
    time_range_end: datetime
    data_points: int = 0
    pattern_description: str
    confidence_score: float = 0.0
    insights: List[str] = []
    recommendations: List[str] = []

class PatternAnalysisCreate(BaseModel):
    user_id: Optional[str] = None
    pattern_type: str
    time_range_start: datetime
    time_range_end: datetime
    pattern_description: str

# ============== 18_SUPPORT_LOG ==============

class SupportLog(BaseDBModel):
    id: str = Field(default_factory=lambda: f"SR-{str(uuid.uuid4())[:6]}")
    log_id: str = Field(default="")
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    issue_summary: str
    category: str = "General"
    status: str = "New"
    assigned_to: Optional[str] = None
    resolution: str = ""

class SupportLogCreate(BaseModel):
    user_id: str
    issue_summary: str
    category: str = "General"
