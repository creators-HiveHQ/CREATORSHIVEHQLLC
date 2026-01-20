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
    PRO = "pro"
    ENTERPRISE = "enterprise"


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
            "arris_insights": False,
            "proposal_limit": 3,
            "priority_review": False,
            "advanced_dashboards": False,
            "support_level": "community"
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
            "arris_insights": True,
            "proposal_limit": 10,
            "priority_review": False,
            "advanced_dashboards": False,
            "support_level": "email"
        },
        "description": "Perfect for getting started with ARRIS insights"
    },
    "starter_annual": {
        "name": "Starter Annual",
        "tier": SubscriptionTier.STARTER,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 99.99,  # ~17% discount
        "monthly_equivalent": 8.33,
        "savings": 19.89,
        "stripe_price_id": None,
        "features": {
            "arris_insights": True,
            "proposal_limit": 10,
            "priority_review": False,
            "advanced_dashboards": False,
            "support_level": "email"
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
            "arris_insights": True,
            "proposal_limit": 25,
            "priority_review": True,
            "advanced_dashboards": True,
            "support_level": "priority"
        },
        "description": "Full access with priority review and advanced dashboards"
    },
    "pro_annual": {
        "name": "Pro Annual",
        "tier": SubscriptionTier.PRO,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 299.99,  # ~17% discount
        "monthly_equivalent": 25.00,
        "savings": 59.89,
        "stripe_price_id": None,
        "features": {
            "arris_insights": True,
            "proposal_limit": 25,
            "priority_review": True,
            "advanced_dashboards": True,
            "support_level": "priority"
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
            "arris_insights": True,
            "proposal_limit": -1,  # Unlimited
            "priority_review": True,
            "advanced_dashboards": True,
            "support_level": "priority",
            "api_access": True,
            "custom_integrations": True
        },
        "description": "Unlimited access with API and custom integrations"
    },
    "premium_annual": {
        "name": "Premium Annual",
        "tier": SubscriptionTier.PREMIUM,
        "billing_cycle": BillingCycle.ANNUAL,
        "price": 999.99,  # ~17% discount
        "monthly_equivalent": 83.33,
        "savings": 199.89,
        "stripe_price_id": None,
        "features": {
            "arris_insights": True,
            "proposal_limit": -1,
            "priority_review": True,
            "advanced_dashboards": True,
            "support_level": "priority",
            "api_access": True,
            "custom_integrations": True
        },
        "description": "Save $199.89/year with annual billing"
    },
    "elite": {
        "name": "Elite",
        "tier": SubscriptionTier.ELITE,
        "billing_cycle": None,
        "price": 0,  # Custom pricing
        "is_custom": True,
        "stripe_price_id": None,
        "features": {
            "arris_insights": True,
            "proposal_limit": -1,
            "priority_review": True,
            "advanced_dashboards": True,
            "support_level": "dedicated",
            "api_access": True,
            "custom_integrations": True,
            "dedicated_account_manager": True,
            "custom_training": True,
            "sla_guarantee": True
        },
        "description": "Custom enterprise solution with dedicated support"
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


class PlansResponse(BaseModel):
    """Available subscription plans"""
    plans: List[PlanInfo]
    current_plan: Optional[str] = None
