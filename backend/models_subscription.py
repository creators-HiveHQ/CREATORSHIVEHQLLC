"""
Creators Hive HQ - Subscription & Stripe Models
Self-Funding Loop - Subscription plans and payment tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============== SUBSCRIPTION TIERS ==============

class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    PREMIUM = "premium"
    ELITE = "elite"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


# Subscription plan definitions (server-side only - never from frontend)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "tier": SubscriptionTier.FREE,
        "monthly_price": 0.0,
        "annual_price": 0.0,
        "features": {
            # Proposals
            "proposals_per_month": 1,
            "proposal_limit": 1,  # Per month
            # ARRIS Insights
            "arris_insights": "summary_only",  # summary_only, summary_strengths, full
            "arris_processing_speed": "standard",
            "custom_arris_workflows": False,
            # Dashboard
            "dashboard_level": "basic",  # basic, advanced, custom
            "advanced_analytics": False,
            # Review & Support
            "priority_review": False,
            "support_level": "community",
            # Integrations
            "api_access": False,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Basic access to get started"
    },
    "starter_monthly": {
        "name": "Starter Monthly",
        "tier": SubscriptionTier.STARTER,
        "billing_cycle": BillingCycle.MONTHLY,
        "price": 9.99,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": 3,
            "proposal_limit": 3,
            "arris_insights": "summary_strengths",  # Summary + Strengths
            "arris_processing_speed": "standard",
            "custom_arris_workflows": False,
            "dashboard_level": "basic",
            "advanced_analytics": False,
            "priority_review": False,
            "support_level": "email",
            "api_access": False,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Perfect for getting started with ARRIS insights"
    },
    "starter_annual": {
        "name": "Starter Annual",
        "tier": SubscriptionTier.STARTER,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 99.99,
        "monthly_equivalent": 8.33,
        "savings": 19.89,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": 3,
            "proposal_limit": 3,
            "arris_insights": "summary_strengths",
            "arris_processing_speed": "standard",
            "custom_arris_workflows": False,
            "dashboard_level": "basic",
            "advanced_analytics": False,
            "priority_review": False,
            "support_level": "email",
            "api_access": False,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Save $19.89/year with annual billing"
    },
    "pro_monthly": {
        "name": "Pro Monthly",
        "tier": SubscriptionTier.PRO,
        "billing_cycle": BillingCycle.MONTHLY,
        "price": 29.99,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": -1,  # Unlimited
            "proposal_limit": -1,
            "arris_insights": "full",  # Full insights
            "arris_processing_speed": "standard",
            "custom_arris_workflows": False,
            "dashboard_level": "advanced",
            "advanced_analytics": False,
            "priority_review": True,
            "support_level": "priority",
            "api_access": False,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Full ARRIS insights with priority review"
    },
    "pro_annual": {
        "name": "Pro Annual",
        "tier": SubscriptionTier.PRO,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 299.99,
        "monthly_equivalent": 25.00,
        "savings": 59.89,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": -1,
            "proposal_limit": -1,
            "arris_insights": "full",
            "arris_processing_speed": "standard",
            "custom_arris_workflows": False,
            "dashboard_level": "advanced",
            "advanced_analytics": False,
            "priority_review": True,
            "support_level": "priority",
            "api_access": False,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Save $59.89/year with annual billing"
    },
    "premium_monthly": {
        "name": "Premium Monthly",
        "tier": SubscriptionTier.PREMIUM,
        "billing_cycle": BillingCycle.MONTHLY,
        "price": 99.99,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": -1,
            "proposal_limit": -1,
            "arris_insights": "full",
            "arris_processing_speed": "fast",  # Faster processing
            "custom_arris_workflows": False,
            "dashboard_level": "advanced",
            "advanced_analytics": True,  # Advanced analytics dashboard
            "priority_review": True,
            "support_level": "priority",
            "api_access": True,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Everything in Pro plus faster processing & analytics"
    },
    "premium_annual": {
        "name": "Premium Annual",
        "tier": SubscriptionTier.PREMIUM,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 999.99,
        "monthly_equivalent": 83.33,
        "savings": 199.89,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": -1,
            "proposal_limit": -1,
            "arris_insights": "full",
            "arris_processing_speed": "fast",
            "custom_arris_workflows": False,
            "dashboard_level": "advanced",
            "advanced_analytics": True,
            "priority_review": True,
            "support_level": "priority",
            "api_access": True,
            "brand_integrations": False,
            "high_touch_onboarding": False
        },
        "description": "Save $199.89/year with annual billing"
    },
    "elite": {
        "name": "Elite",
        "tier": SubscriptionTier.ELITE,
        "billing_cycle": None,
        "price": 0,
        "is_custom": True,
        "stripe_price_id": None,
        "features": {
            "proposals_per_month": -1,
            "proposal_limit": -1,
            "arris_insights": "full",
            "arris_processing_speed": "fast",
            "custom_arris_workflows": True,  # Custom workflows
            "dashboard_level": "custom",  # Custom dashboards
            "advanced_analytics": True,
            "priority_review": True,
            "support_level": "dedicated",  # Dedicated support
            "api_access": True,
            "brand_integrations": True,  # Brand-level integrations
            "high_touch_onboarding": True  # High-touch onboarding
        },
        "description": "Custom enterprise solution with dedicated support"
    }
}


# Feature tier hierarchy for display
FEATURE_TIERS = {
    "arris_insights": {
        "summary_only": "Summary Only",
        "summary_strengths": "Summary + Strengths", 
        "full": "Full Insights (Strengths, Risks, Recommendations, Milestones)"
    },
    "dashboard_level": {
        "basic": "Basic Dashboard",
        "advanced": "Advanced Dashboard",
        "custom": "Custom Dashboard"
    },
    "support_level": {
        "community": "Community Support",
        "email": "Email Support",
        "priority": "Priority Support",
        "dedicated": "Dedicated Support"
    }
}


# ============== SUBSCRIPTION MODELS ==============

class CreatorSubscription(BaseModel):
    """Active subscription for a creator"""
    id: str = Field(default_factory=lambda: f"SUB-{str(uuid.uuid4())[:8]}")
    creator_id: str
    creator_email: str
    
    # Plan details
    plan_id: str  # Key from SUBSCRIPTION_PLANS
    tier: SubscriptionTier
    billing_cycle: BillingCycle
    
    # Stripe info
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Status
    status: str = "active"  # active, cancelled, past_due, trialing
    
    # Dates
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled_at: Optional[datetime] = None
    
    # Revenue tracking
    total_paid: float = 0.0
    payment_count: int = 0


class PaymentTransaction(BaseModel):
    """Individual payment transaction record"""
    id: str = Field(default_factory=lambda: f"TXN-{str(uuid.uuid4())[:8]}")
    
    # User info
    creator_id: Optional[str] = None
    creator_email: Optional[str] = None
    
    # Stripe session info
    stripe_session_id: str
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    
    # Payment details
    amount: float
    currency: str = "usd"
    plan_id: str
    billing_cycle: str
    
    # Status
    status: str = "pending"  # pending, processing, completed, failed, refunded
    payment_status: str = "initiated"  # initiated, paid, unpaid, expired
    
    # Metadata
    metadata: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


# ============== API REQUEST/RESPONSE MODELS ==============

class CheckoutRequest(BaseModel):
    """Request to create a checkout session"""
    plan_id: str = Field(..., description="Plan ID from available plans")
    origin_url: str = Field(..., description="Frontend origin URL for redirects")


class CheckoutResponse(BaseModel):
    """Response with checkout session URL"""
    checkout_url: str
    session_id: str
    plan_id: str
    amount: float
    currency: str


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status for a creator"""
    has_subscription: bool
    tier: str
    plan_id: Optional[str] = None
    status: Optional[str] = None
    features: Dict[str, Any]
    current_period_end: Optional[str] = None
    can_use_arris: bool
    proposal_limit: int
    proposals_used: int
    proposals_remaining: int


class PlanInfo(BaseModel):
    """Public plan information"""
    plan_id: str
    name: str
    tier: str
    billing_cycle: Optional[str] = None
    price: float
    monthly_equivalent: Optional[float] = None
    savings: Optional[float] = None
    features: Dict[str, Any]
    description: str
    is_popular: bool = False
    is_custom: bool = False  # For Elite tier


class PlansResponse(BaseModel):
    """Available subscription plans"""
    plans: List[PlanInfo]
    current_plan: Optional[str] = None
