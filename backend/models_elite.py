"""
Elite Tier Models - Custom ARRIS Workflows, Brand Integrations, and Elite Dashboard
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# ============== CUSTOM ARRIS WORKFLOWS ==============

class WorkflowTrigger(str, Enum):
    """When to trigger a custom workflow"""
    ON_PROPOSAL_CREATE = "on_proposal_create"
    ON_PROPOSAL_SUBMIT = "on_proposal_submit"
    ON_STATUS_CHANGE = "on_status_change"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class WorkflowFocusArea(str, Enum):
    """Pre-defined focus areas for ARRIS analysis"""
    GROWTH_STRATEGY = "growth_strategy"
    MONETIZATION = "monetization"
    AUDIENCE_ENGAGEMENT = "audience_engagement"
    BRAND_PARTNERSHIPS = "brand_partnerships"
    CONTENT_OPTIMIZATION = "content_optimization"
    RISK_ASSESSMENT = "risk_assessment"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    CUSTOM = "custom"


class ArrisWorkflowConfig(BaseModel):
    """Configuration for a custom ARRIS workflow"""
    focus_areas: List[WorkflowFocusArea] = [WorkflowFocusArea.GROWTH_STRATEGY]
    custom_prompt_addition: Optional[str] = None
    include_historical_context: bool = True
    analysis_depth: str = "detailed"  # brief, standard, detailed, comprehensive
    output_format: str = "structured"  # structured, narrative, bullet_points
    include_benchmarks: bool = True
    custom_metrics: List[str] = []


class CustomArrisWorkflow(BaseModel):
    """Custom ARRIS workflow template"""
    id: Optional[str] = None
    creator_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger: WorkflowTrigger = WorkflowTrigger.MANUAL
    config: ArrisWorkflowConfig = ArrisWorkflowConfig()
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    """Request to create a custom workflow"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger: WorkflowTrigger = WorkflowTrigger.MANUAL
    config: ArrisWorkflowConfig = ArrisWorkflowConfig()
    is_default: bool = False


class WorkflowRunRequest(BaseModel):
    """Request to run a workflow on a proposal"""
    proposal_id: str
    workflow_id: str


# ============== BRAND INTEGRATIONS ==============

class BrandPartnershipStatus(str, Enum):
    """Status of a brand partnership"""
    PROSPECTING = "prospecting"
    OUTREACH = "outreach"
    NEGOTIATING = "negotiating"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ENDED = "ended"


class BrandDealType(str, Enum):
    """Type of brand deal"""
    SPONSORSHIP = "sponsorship"
    AFFILIATE = "affiliate"
    AMBASSADOR = "ambassador"
    ONE_TIME = "one_time"
    LONG_TERM = "long_term"
    PRODUCT_PLACEMENT = "product_placement"
    CONTENT_CREATION = "content_creation"


class BrandIntegration(BaseModel):
    """Brand partnership/integration record"""
    id: Optional[str] = None
    creator_id: str
    brand_name: str = Field(..., min_length=1, max_length=200)
    brand_logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    deal_type: BrandDealType = BrandDealType.SPONSORSHIP
    status: BrandPartnershipStatus = BrandPartnershipStatus.PROSPECTING
    deal_value: float = 0.0
    currency: str = "USD"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: List[str] = []
    deliverables: List[str] = []
    notes: Optional[str] = None
    arris_recommendation_score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BrandIntegrationCreate(BaseModel):
    """Request to create a brand integration"""
    brand_name: str = Field(..., min_length=1, max_length=200)
    brand_logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    deal_type: BrandDealType = BrandDealType.SPONSORSHIP
    status: BrandPartnershipStatus = BrandPartnershipStatus.PROSPECTING
    deal_value: float = 0.0
    currency: str = "USD"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: List[str] = []
    deliverables: List[str] = []
    notes: Optional[str] = None


class BrandIntegrationUpdate(BaseModel):
    """Request to update a brand integration"""
    brand_name: Optional[str] = None
    brand_logo_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    deal_type: Optional[BrandDealType] = None
    status: Optional[BrandPartnershipStatus] = None
    deal_value: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    notes: Optional[str] = None


# ============== ELITE DASHBOARD ==============

class DashboardWidgetType(str, Enum):
    """Types of dashboard widgets"""
    METRIC_CARD = "metric_card"
    CHART_LINE = "chart_line"
    CHART_BAR = "chart_bar"
    CHART_PIE = "chart_pie"
    ARRIS_INSIGHTS = "arris_insights"
    BRAND_PIPELINE = "brand_pipeline"
    PROPOSAL_LIST = "proposal_list"
    ACTIVITY_FEED = "activity_feed"
    REVENUE_TRACKER = "revenue_tracker"
    GOAL_PROGRESS = "goal_progress"
    CUSTOM_TEXT = "custom_text"


class DashboardWidget(BaseModel):
    """A widget on the Elite dashboard"""
    id: Optional[str] = None
    widget_type: DashboardWidgetType
    title: str
    position: Dict[str, int] = {"x": 0, "y": 0, "w": 2, "h": 2}
    config: Dict[str, Any] = {}
    is_visible: bool = True


class EliteDashboardConfig(BaseModel):
    """Elite dashboard configuration"""
    id: Optional[str] = None
    creator_id: str
    name: str = "My Dashboard"
    widgets: List[DashboardWidget] = []
    theme: str = "default"  # default, dark, light, brand_custom
    brand_colors: Dict[str, str] = {}  # primary, secondary, accent
    logo_url: Optional[str] = None
    is_default: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DashboardConfigUpdate(BaseModel):
    """Update dashboard configuration"""
    name: Optional[str] = None
    widgets: Optional[List[DashboardWidget]] = None
    theme: Optional[str] = None
    brand_colors: Optional[Dict[str, str]] = None
    logo_url: Optional[str] = None


# ============== ADAPTIVE INTELLIGENCE ==============

class CreatorPattern(BaseModel):
    """Pattern learned from creator's history"""
    pattern_type: str
    pattern_value: Any
    confidence: float = 0.0
    occurrences: int = 0
    last_seen: Optional[str] = None


class AdaptiveIntelligenceProfile(BaseModel):
    """ARRIS adaptive intelligence profile for a creator"""
    id: Optional[str] = None
    creator_id: str
    
    # Learned preferences
    preferred_platforms: List[Dict[str, Any]] = []
    common_project_types: List[str] = []
    typical_timeline_range: Dict[str, str] = {}
    complexity_comfort_level: str = "medium"
    
    # Success patterns
    success_patterns: List[CreatorPattern] = []
    risk_patterns: List[CreatorPattern] = []
    
    # Personalization
    communication_style: str = "balanced"  # brief, balanced, detailed
    focus_areas: List[str] = []
    
    # Metrics
    total_proposals_analyzed: int = 0
    learning_score: float = 0.0
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
