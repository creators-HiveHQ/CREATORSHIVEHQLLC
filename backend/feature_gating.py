"""
Creators Hive HQ - Feature Gating Service
Gates features based on subscription tier
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from models_subscription import SUBSCRIPTION_PLANS, SubscriptionTier

logger = logging.getLogger(__name__)


class FeatureGatingService:
    """Service for checking feature access based on subscription tier"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_creator_tier(self, creator_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Get creator's current subscription tier and features.
        Returns (tier_name, features_dict)
        """
        # Check for active subscription
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0}
        )
        
        if subscription:
            plan_id = subscription.get("plan_id", "free")
            plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
            return plan.get("tier", SubscriptionTier.FREE), plan.get("features", {})
        
        # Default to free tier
        return SubscriptionTier.FREE, SUBSCRIPTION_PLANS["free"]["features"]
    
    async def get_proposals_this_month(self, creator_id: str) -> int:
        """Count proposals created this month by creator"""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        count = await self.db.proposals.count_documents({
            "user_id": creator_id,
            "created_at": {"$gte": start_of_month.isoformat()}
        })
        
        return count
    
    async def can_create_proposal(self, creator_id: str) -> Dict[str, Any]:
        """
        Check if creator can create a new proposal based on monthly limit.
        Returns dict with can_create, limit, used, remaining, and upgrade_needed.
        """
        tier, features = await self.get_creator_tier(creator_id)
        limit = features.get("proposals_per_month", 1)
        
        # Unlimited proposals
        if limit == -1:
            return {
                "can_create": True,
                "limit": -1,
                "used": await self.get_proposals_this_month(creator_id),
                "remaining": -1,
                "upgrade_needed": False,
                "tier": tier.value if hasattr(tier, 'value') else tier
            }
        
        used = await self.get_proposals_this_month(creator_id)
        remaining = max(0, limit - used)
        
        return {
            "can_create": used < limit,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "upgrade_needed": used >= limit,
            "tier": tier.value if hasattr(tier, 'value') else tier,
            "message": f"You've used {used}/{limit} proposals this month" if used < limit else f"Monthly limit reached ({limit} proposals). Upgrade for more!"
        }
    
    async def get_arris_insight_level(self, creator_id: str) -> str:
        """
        Get the ARRIS insight level for a creator.
        Returns: 'summary_only', 'summary_strengths', or 'full'
        """
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("arris_insights", "summary_only")
    
    async def filter_arris_insights(self, creator_id: str, full_insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter ARRIS insights based on creator's subscription tier.
        
        - Free (summary_only): Only summary
        - Starter (summary_strengths): Summary + strengths
        - Pro+ (full): All insights
        """
        insight_level = await self.get_arris_insight_level(creator_id)
        
        if not full_insights:
            return full_insights
        
        filtered = {
            "insight_level": insight_level,
            "generated_at": full_insights.get("generated_at"),
            "model_used": full_insights.get("model_used")
        }
        
        # Always include summary
        if "summary" in full_insights:
            filtered["summary"] = full_insights["summary"]
        
        if "estimated_complexity" in full_insights:
            filtered["estimated_complexity"] = full_insights["estimated_complexity"]
        
        # Starter+ gets strengths
        if insight_level in ["summary_strengths", "full"]:
            if "strengths" in full_insights:
                filtered["strengths"] = full_insights["strengths"]
        
        # Pro+ gets full insights
        if insight_level == "full":
            if "risks" in full_insights:
                filtered["risks"] = full_insights["risks"]
            if "recommendations" in full_insights:
                filtered["recommendations"] = full_insights["recommendations"]
            if "suggested_milestones" in full_insights:
                filtered["suggested_milestones"] = full_insights["suggested_milestones"]
        
        # Add upgrade prompts for gated features
        if insight_level == "summary_only":
            filtered["_gated"] = {
                "strengths": "Upgrade to Starter to see strengths analysis",
                "risks": "Upgrade to Pro for risk analysis",
                "recommendations": "Upgrade to Pro for recommendations",
                "milestones": "Upgrade to Pro for suggested milestones"
            }
        elif insight_level == "summary_strengths":
            filtered["_gated"] = {
                "risks": "Upgrade to Pro for risk analysis",
                "recommendations": "Upgrade to Pro for recommendations",
                "milestones": "Upgrade to Pro for suggested milestones"
            }
        
        return filtered
    
    async def has_priority_review(self, creator_id: str) -> bool:
        """Check if creator has priority review access"""
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("priority_review", False)
    
    async def get_dashboard_level(self, creator_id: str) -> str:
        """Get dashboard level for creator: 'basic', 'advanced', or 'custom'"""
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("dashboard_level", "basic")
    
    async def has_advanced_analytics(self, creator_id: str) -> bool:
        """Check if creator has advanced analytics access"""
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("advanced_analytics", False)
    
    async def has_api_access(self, creator_id: str) -> bool:
        """Check if creator has API access"""
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("api_access", False)
    
    async def get_arris_processing_speed(self, creator_id: str) -> str:
        """
        Get ARRIS processing speed for creator.
        Returns: 'standard' or 'fast' (Premium/Elite users get fast processing)
        """
        tier, features = await self.get_creator_tier(creator_id)
        return features.get("arris_processing_speed", "standard")
    
    async def get_full_feature_access(self, creator_id: str) -> Dict[str, Any]:
        """Get complete feature access info for a creator"""
        tier, features = await self.get_creator_tier(creator_id)
        proposal_status = await self.can_create_proposal(creator_id)
        
        # Get subscription details
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0}
        )
        
        return {
            "tier": tier.value if hasattr(tier, 'value') else tier,
            "plan_id": subscription.get("plan_id") if subscription else "free",
            "features": {
                # Proposals
                "proposals_per_month": features.get("proposals_per_month", 1),
                "proposals_used": proposal_status["used"],
                "proposals_remaining": proposal_status["remaining"],
                "can_create_proposal": proposal_status["can_create"],
                
                # ARRIS
                "arris_insight_level": features.get("arris_insights", "summary_only"),
                "arris_processing_speed": features.get("arris_processing_speed", "standard"),
                "custom_arris_workflows": features.get("custom_arris_workflows", False),
                
                # Dashboard
                "dashboard_level": features.get("dashboard_level", "basic"),
                "advanced_analytics": features.get("advanced_analytics", False),
                
                # Review & Support
                "priority_review": features.get("priority_review", False),
                "support_level": features.get("support_level", "community"),
                
                # Integrations
                "api_access": features.get("api_access", False),
                "brand_integrations": features.get("brand_integrations", False)
            },
            "subscription_active": subscription is not None,
            "current_period_end": subscription.get("current_period_end") if subscription else None
        }
