"""
Subscription Lifecycle Automation Service (Module B3)
=====================================================
Auto-detects at-risk subscriptions and automates lifecycle management.
Identifies churn risk, engagement drops, and triggers retention actions.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)


# Risk levels
class RiskLevel:
    CRITICAL = "critical"    # Immediate action required (likely to churn)
    HIGH = "high"            # At risk, needs attention
    MEDIUM = "medium"        # Some warning signs
    LOW = "low"              # Healthy, minimal risk


# Risk factors and their weights
RISK_FACTORS = {
    "inactivity_days": {
        "weight": 25,
        "thresholds": {
            "critical": 30,   # 30+ days inactive
            "high": 14,       # 14-29 days
            "medium": 7,      # 7-13 days
            "low": 0          # Active
        }
    },
    "proposal_decline_rate": {
        "weight": 20,
        "thresholds": {
            "critical": 0.7,  # 70%+ rejection rate
            "high": 0.5,      # 50-69%
            "medium": 0.3,    # 30-49%
            "low": 0          # Below 30%
        }
    },
    "engagement_drop": {
        "weight": 20,
        "thresholds": {
            "critical": 0.8,  # 80%+ drop in activity
            "high": 0.5,      # 50-79%
            "medium": 0.3,    # 30-49%
            "low": 0          # Stable or growing
        }
    },
    "support_tickets": {
        "weight": 15,
        "thresholds": {
            "critical": 5,    # 5+ unresolved tickets
            "high": 3,        # 3-4 tickets
            "medium": 1,      # 1-2 tickets
            "low": 0          # No tickets
        }
    },
    "payment_failures": {
        "weight": 20,
        "thresholds": {
            "critical": 3,    # 3+ failed payments
            "high": 2,        # 2 failures
            "medium": 1,      # 1 failure
            "low": 0          # No failures
        }
    }
}


# Lifecycle stages
class LifecycleStage:
    ONBOARDING = "onboarding"        # New subscriber (first 7 days)
    ACTIVATION = "activation"         # Learning the platform (7-30 days)
    ENGAGED = "engaged"               # Active user
    AT_RISK = "at_risk"              # Showing churn signals
    CHURNING = "churning"            # High probability of leaving
    CHURNED = "churned"              # Subscription cancelled
    REACTIVATED = "reactivated"      # Returned after churning


# Retention actions
class RetentionAction:
    WELCOME_EMAIL = "welcome_email"
    ONBOARDING_REMINDER = "onboarding_reminder"
    FEATURE_HIGHLIGHT = "feature_highlight"
    ENGAGEMENT_NUDGE = "engagement_nudge"
    SUCCESS_CELEBRATION = "success_celebration"
    AT_RISK_OUTREACH = "at_risk_outreach"
    DISCOUNT_OFFER = "discount_offer"
    PERSONAL_CALL = "personal_call"
    WIN_BACK_CAMPAIGN = "win_back_campaign"


# Automation rules for lifecycle transitions
LIFECYCLE_AUTOMATIONS = {
    LifecycleStage.ONBOARDING: {
        "triggers": [
            {"action": RetentionAction.WELCOME_EMAIL, "delay_hours": 0},
            {"action": RetentionAction.ONBOARDING_REMINDER, "delay_hours": 48, "condition": "no_proposal_submitted"},
            {"action": RetentionAction.FEATURE_HIGHLIGHT, "delay_hours": 120}  # Day 5
        ]
    },
    LifecycleStage.AT_RISK: {
        "triggers": [
            {"action": RetentionAction.ENGAGEMENT_NUDGE, "delay_hours": 0},
            {"action": RetentionAction.AT_RISK_OUTREACH, "delay_hours": 72},
            {"action": RetentionAction.DISCOUNT_OFFER, "delay_hours": 168, "condition": "still_at_risk"}  # Day 7
        ]
    },
    LifecycleStage.CHURNING: {
        "triggers": [
            {"action": RetentionAction.PERSONAL_CALL, "delay_hours": 0, "condition": "high_value_subscriber"},
            {"action": RetentionAction.DISCOUNT_OFFER, "delay_hours": 24}
        ]
    },
    LifecycleStage.CHURNED: {
        "triggers": [
            {"action": RetentionAction.WIN_BACK_CAMPAIGN, "delay_hours": 168}  # 1 week after churn
        ]
    }
}


class SubscriptionLifecycleService:
    """
    Service for automating subscription lifecycle management.
    Detects at-risk subscriptions and triggers retention actions.
    """
    
    def __init__(self, db, email_service=None, ws_manager=None, notification_service=None):
        self.db = db
        self.email_service = email_service
        self.ws_manager = ws_manager
        self.notification_service = notification_service
    
    async def get_subscription_health(self, creator_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health analysis for a creator's subscription.
        Returns risk score, lifecycle stage, and recommendations.
        """
        # Get subscription data
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not subscription:
            return {
                "error": "No subscription found",
                "creator_id": creator_id
            }
        
        # Get creator data
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0}
        )
        
        # Analyze risk factors
        risk_analysis = await self._analyze_risk_factors(creator_id, creator, subscription)
        
        # Determine lifecycle stage
        lifecycle_stage = await self._determine_lifecycle_stage(creator_id, creator, subscription, risk_analysis)
        
        # Get recommended actions
        recommendations = self._get_recommendations(lifecycle_stage, risk_analysis)
        
        # Calculate overall health score (0-100, higher is healthier)
        health_score = self._calculate_health_score(risk_analysis)
        
        return {
            "creator_id": creator_id,
            "subscription": {
                "tier": subscription.get("tier"),
                "status": subscription.get("status"),
                "plan_name": subscription.get("plan_name"),
                "current_period_end": subscription.get("current_period_end"),
                "days_remaining": self._days_until(subscription.get("current_period_end"))
            },
            "health_score": health_score,
            "risk_level": self._score_to_risk_level(health_score),
            "lifecycle_stage": lifecycle_stage,
            "risk_analysis": risk_analysis,
            "recommendations": recommendations,
            "last_analyzed": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_at_risk_subscriptions(
        self,
        risk_threshold: str = RiskLevel.MEDIUM,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all subscriptions at or above a given risk level.
        Used by admin dashboard for churn prevention.
        """
        # Get all active subscriptions
        subscriptions = await self.db.creator_subscriptions.find(
            {"status": "active"},
            {"_id": 0}
        ).to_list(500)
        
        at_risk = []
        for sub in subscriptions:
            creator_id = sub.get("creator_id")
            health = await self.get_subscription_health(creator_id)
            
            if health.get("error"):
                continue
            
            risk_level = health.get("risk_level", RiskLevel.LOW)
            
            # Check if meets threshold
            risk_order = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
            if risk_order.index(risk_level) <= risk_order.index(risk_threshold):
                at_risk.append({
                    "creator_id": creator_id,
                    "email": sub.get("email"),
                    "tier": sub.get("tier"),
                    "health_score": health.get("health_score"),
                    "risk_level": risk_level,
                    "lifecycle_stage": health.get("lifecycle_stage"),
                    "days_remaining": health.get("subscription", {}).get("days_remaining"),
                    "top_risk_factors": self._get_top_risk_factors(health.get("risk_analysis", {})),
                    "recommendations": health.get("recommendations", [])[:3]
                })
        
        # Sort by risk (highest first)
        risk_order_map = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 3}
        at_risk.sort(key=lambda x: (risk_order_map.get(x["risk_level"], 4), x.get("health_score", 100)))
        
        # Count by risk level
        risk_counts = {
            "critical": len([x for x in at_risk if x["risk_level"] == RiskLevel.CRITICAL]),
            "high": len([x for x in at_risk if x["risk_level"] == RiskLevel.HIGH]),
            "medium": len([x for x in at_risk if x["risk_level"] == RiskLevel.MEDIUM]),
            "low": len([x for x in at_risk if x["risk_level"] == RiskLevel.LOW])
        }
        
        return {
            "at_risk_subscriptions": at_risk[:limit],
            "total_at_risk": len(at_risk),
            "risk_counts": risk_counts,
            "threshold_applied": risk_threshold,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_lifecycle_metrics(self) -> Dict[str, Any]:
        """
        Get platform-wide lifecycle metrics for admin dashboard.
        """
        # Get all subscriptions
        all_subs = await self.db.creator_subscriptions.find({}, {"_id": 0}).to_list(1000)
        
        # Count by stage
        stage_counts = {}
        tier_counts = {}
        health_distribution = {"healthy": 0, "at_risk": 0, "critical": 0}
        
        for sub in all_subs:
            tier = sub.get("tier", "free")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            # Analyze health for active subscriptions
            if sub.get("status") == "active":
                creator_id = sub.get("creator_id")
                if creator_id:
                    health = await self.get_subscription_health(creator_id)
                    stage = health.get("lifecycle_stage", LifecycleStage.ENGAGED)
                    stage_counts[stage] = stage_counts.get(stage, 0) + 1
                    
                    score = health.get("health_score", 50)
                    if score >= 70:
                        health_distribution["healthy"] += 1
                    elif score >= 40:
                        health_distribution["at_risk"] += 1
                    else:
                        health_distribution["critical"] += 1
        
        # Calculate churn metrics
        churned_30d = await self.db.creator_subscriptions.count_documents({
            "status": "cancelled",
            "cancelled_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}
        })
        
        total_active = await self.db.creator_subscriptions.count_documents({"status": "active"})
        churn_rate = (churned_30d / max(total_active + churned_30d, 1)) * 100
        
        return {
            "total_subscriptions": len(all_subs),
            "active_subscriptions": total_active,
            "lifecycle_stages": stage_counts,
            "tier_distribution": tier_counts,
            "health_distribution": health_distribution,
            "churn_metrics": {
                "churned_last_30d": churned_30d,
                "churn_rate_30d": round(churn_rate, 2),
                "at_risk_count": health_distribution["at_risk"] + health_distribution["critical"]
            },
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def trigger_retention_action(
        self,
        creator_id: str,
        action: str,
        admin_id: str = None,
        custom_message: str = None
    ) -> Dict[str, Any]:
        """
        Manually trigger a retention action for a subscription.
        """
        # Get subscription
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not subscription:
            return {"success": False, "error": "Subscription not found"}
        
        # Log the action
        action_log = {
            "id": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "creator_id": creator_id,
            "action": action,
            "triggered_by": admin_id or "system",
            "custom_message": custom_message,
            "subscription_tier": subscription.get("tier"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        
        await self.db.retention_actions.insert_one(action_log)
        
        # Execute action based on type
        result = await self._execute_retention_action(creator_id, subscription, action, custom_message)
        
        # Update action status
        await self.db.retention_actions.update_one(
            {"id": action_log["id"]},
            {"$set": {"status": "completed" if result.get("success") else "failed", "result": result}}
        )
        
        return {
            "success": True,
            "action_id": action_log["id"],
            "action": action,
            "result": result
        }
    
    async def get_retention_history(
        self,
        creator_id: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get retention action history.
        """
        query = {}
        if creator_id:
            query["creator_id"] = creator_id
        
        actions = await self.db.retention_actions.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "actions": actions,
            "total": len(actions)
        }
    
    async def update_lifecycle_stage(
        self,
        creator_id: str,
        new_stage: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Manually update a subscription's lifecycle stage.
        """
        # Update subscription
        result = await self.db.creator_subscriptions.update_one(
            {"creator_id": creator_id},
            {
                "$set": {
                    "lifecycle_stage": new_stage,
                    "lifecycle_updated_at": datetime.now(timezone.utc).isoformat(),
                    "lifecycle_update_reason": reason
                }
            }
        )
        
        if result.modified_count == 0:
            return {"success": False, "error": "Subscription not found or unchanged"}
        
        # Log transition
        await self.db.lifecycle_transitions.insert_one({
            "id": f"LCT-{uuid.uuid4().hex[:8].upper()}",
            "creator_id": creator_id,
            "new_stage": new_stage,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Trigger automations for new stage
        if new_stage in LIFECYCLE_AUTOMATIONS:
            automations = LIFECYCLE_AUTOMATIONS[new_stage]
            for trigger in automations.get("triggers", []):
                if trigger.get("delay_hours", 0) == 0:
                    await self.trigger_retention_action(
                        creator_id,
                        trigger["action"],
                        admin_id="system"
                    )
        
        return {"success": True, "new_stage": new_stage}
    
    # ============== PRIVATE METHODS ==============
    
    async def _analyze_risk_factors(
        self,
        creator_id: str,
        creator: Dict,
        subscription: Dict
    ) -> Dict[str, Any]:
        """Analyze individual risk factors for a subscription."""
        now = datetime.now(timezone.utc)
        risk_factors = {}
        
        # 1. Inactivity analysis
        last_activity = await self._get_last_activity_date(creator_id)
        if last_activity:
            days_inactive = (now - last_activity).days
        else:
            days_inactive = 30  # Assume inactive if no activity found
        
        risk_factors["inactivity"] = {
            "days_inactive": days_inactive,
            "risk_score": self._calculate_factor_score("inactivity_days", days_inactive),
            "status": self._get_factor_status("inactivity_days", days_inactive)
        }
        
        # 2. Proposal decline rate
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"status": 1}
        ).to_list(100)
        
        if proposals:
            rejected = len([p for p in proposals if p.get("status") == "rejected"])
            decline_rate = rejected / len(proposals)
        else:
            decline_rate = 0
        
        risk_factors["proposal_performance"] = {
            "total_proposals": len(proposals),
            "rejected": rejected if proposals else 0,
            "decline_rate": round(decline_rate, 2),
            "risk_score": self._calculate_factor_score("proposal_decline_rate", decline_rate),
            "status": self._get_factor_status("proposal_decline_rate", decline_rate)
        }
        
        # 3. Engagement trend (compare last 30 days to previous 30)
        engagement_drop = await self._calculate_engagement_drop(creator_id)
        risk_factors["engagement"] = {
            "engagement_drop": round(engagement_drop, 2),
            "risk_score": self._calculate_factor_score("engagement_drop", engagement_drop),
            "status": self._get_factor_status("engagement_drop", engagement_drop)
        }
        
        # 4. Support tickets (simplified - count recent issues)
        tickets = await self.db.support_tickets.count_documents({
            "creator_id": creator_id,
            "status": {"$ne": "resolved"}
        })
        
        risk_factors["support_issues"] = {
            "open_tickets": tickets,
            "risk_score": self._calculate_factor_score("support_tickets", tickets),
            "status": self._get_factor_status("support_tickets", tickets)
        }
        
        # 5. Payment failures
        payment_failures = await self.db.payment_failures.count_documents({
            "creator_id": creator_id,
            "created_at": {"$gte": (now - timedelta(days=90)).isoformat()}
        })
        
        risk_factors["payment_health"] = {
            "recent_failures": payment_failures,
            "risk_score": self._calculate_factor_score("payment_failures", payment_failures),
            "status": self._get_factor_status("payment_failures", payment_failures)
        }
        
        return risk_factors
    
    async def _determine_lifecycle_stage(
        self,
        creator_id: str,
        creator: Dict,
        subscription: Dict,
        risk_analysis: Dict
    ) -> str:
        """Determine the current lifecycle stage based on data."""
        now = datetime.now(timezone.utc)
        
        # Check subscription status first
        status = subscription.get("status", "active")
        if status == "cancelled":
            return LifecycleStage.CHURNED
        
        # Check for stored stage
        stored_stage = subscription.get("lifecycle_stage")
        if stored_stage == LifecycleStage.REACTIVATED:
            return LifecycleStage.REACTIVATED
        
        # Calculate subscription age
        created_at = subscription.get("created_at")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_days = (now - created).days
            except:
                age_days = 30
        else:
            age_days = 30
        
        # New subscriber (first 7 days)
        if age_days <= 7:
            return LifecycleStage.ONBOARDING
        
        # Activation phase (7-30 days)
        if age_days <= 30:
            return LifecycleStage.ACTIVATION
        
        # Calculate overall risk score
        total_score = sum(
            factor.get("risk_score", 0) for factor in risk_analysis.values()
        )
        
        # Normalize to 0-100 (lower is better)
        max_possible = sum(RISK_FACTORS[f]["weight"] for f in RISK_FACTORS)
        risk_percentage = (total_score / max_possible) * 100
        
        # Determine stage based on risk
        if risk_percentage >= 70:
            return LifecycleStage.CHURNING
        elif risk_percentage >= 40:
            return LifecycleStage.AT_RISK
        else:
            return LifecycleStage.ENGAGED
    
    def _get_recommendations(self, stage: str, risk_analysis: Dict) -> List[Dict]:
        """Get recommended actions based on lifecycle stage and risks."""
        recommendations = []
        
        # Stage-specific recommendations
        if stage == LifecycleStage.ONBOARDING:
            recommendations.append({
                "action": "send_onboarding_guide",
                "title": "Complete Onboarding",
                "description": "Send personalized onboarding guide to help creator get started",
                "priority": "high"
            })
        
        if stage == LifecycleStage.AT_RISK:
            recommendations.append({
                "action": "engagement_outreach",
                "title": "Engagement Outreach",
                "description": "Reach out to understand challenges and offer support",
                "priority": "high"
            })
        
        if stage == LifecycleStage.CHURNING:
            recommendations.append({
                "action": "retention_offer",
                "title": "Retention Offer",
                "description": "Offer discount or feature upgrade to retain subscription",
                "priority": "critical"
            })
        
        # Risk-specific recommendations
        if risk_analysis.get("inactivity", {}).get("status") in ["critical", "high"]:
            recommendations.append({
                "action": "activity_reminder",
                "title": "Send Activity Reminder",
                "description": f"Creator has been inactive for {risk_analysis['inactivity']['days_inactive']} days",
                "priority": "high"
            })
        
        if risk_analysis.get("proposal_performance", {}).get("status") in ["critical", "high"]:
            recommendations.append({
                "action": "proposal_coaching",
                "title": "Proposal Coaching",
                "description": "Offer tips to improve proposal success rate",
                "priority": "medium"
            })
        
        if risk_analysis.get("payment_health", {}).get("status") in ["critical", "high"]:
            recommendations.append({
                "action": "payment_followup",
                "title": "Payment Follow-up",
                "description": "Contact about payment issues to prevent involuntary churn",
                "priority": "critical"
            })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority"), 4))
        
        return recommendations
    
    def _calculate_health_score(self, risk_analysis: Dict) -> int:
        """Calculate overall health score (0-100, higher is healthier)."""
        total_risk = sum(
            factor.get("risk_score", 0) for factor in risk_analysis.values()
        )
        max_risk = sum(RISK_FACTORS[f]["weight"] for f in RISK_FACTORS)
        
        # Invert to health score
        health = 100 - ((total_risk / max_risk) * 100)
        return max(0, min(100, int(health)))
    
    def _score_to_risk_level(self, health_score: int) -> str:
        """Convert health score to risk level."""
        if health_score <= 30:
            return RiskLevel.CRITICAL
        elif health_score <= 50:
            return RiskLevel.HIGH
        elif health_score <= 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_factor_score(self, factor_name: str, value: float) -> float:
        """Calculate risk score for a specific factor."""
        factor = RISK_FACTORS.get(factor_name, {})
        weight = factor.get("weight", 0)
        thresholds = factor.get("thresholds", {})
        
        if value >= thresholds.get("critical", float("inf")):
            return weight
        elif value >= thresholds.get("high", float("inf")):
            return weight * 0.75
        elif value >= thresholds.get("medium", float("inf")):
            return weight * 0.5
        else:
            return weight * 0.25
    
    def _get_factor_status(self, factor_name: str, value: float) -> str:
        """Get status label for a factor value."""
        factor = RISK_FACTORS.get(factor_name, {})
        thresholds = factor.get("thresholds", {})
        
        if value >= thresholds.get("critical", float("inf")):
            return "critical"
        elif value >= thresholds.get("high", float("inf")):
            return "high"
        elif value >= thresholds.get("medium", float("inf")):
            return "medium"
        else:
            return "low"
    
    def _get_top_risk_factors(self, risk_analysis: Dict) -> List[str]:
        """Get top contributing risk factors."""
        factors = []
        for name, data in risk_analysis.items():
            if data.get("status") in ["critical", "high"]:
                factors.append(name)
        return factors[:3]
    
    async def _get_last_activity_date(self, creator_id: str) -> Optional[datetime]:
        """Get the last activity date for a creator."""
        # Check proposals
        last_proposal = await self.db.proposals.find_one(
            {"user_id": creator_id},
            {"created_at": 1},
            sort=[("created_at", -1)]
        )
        
        if last_proposal and last_proposal.get("created_at"):
            try:
                return datetime.fromisoformat(last_proposal["created_at"].replace("Z", "+00:00"))
            except:
                pass
        
        return None
    
    async def _calculate_engagement_drop(self, creator_id: str) -> float:
        """Calculate engagement drop between current and previous periods."""
        now = datetime.now(timezone.utc)
        
        # Current 30-day period
        current_start = now - timedelta(days=30)
        current_count = await self.db.proposals.count_documents({
            "user_id": creator_id,
            "created_at": {"$gte": current_start.isoformat()}
        })
        
        # Previous 30-day period
        prev_start = now - timedelta(days=60)
        prev_end = now - timedelta(days=30)
        prev_count = await self.db.proposals.count_documents({
            "user_id": creator_id,
            "created_at": {
                "$gte": prev_start.isoformat(),
                "$lt": prev_end.isoformat()
            }
        })
        
        if prev_count == 0:
            return 0  # No previous activity to compare
        
        # Calculate drop percentage
        drop = (prev_count - current_count) / prev_count
        return max(0, drop)  # Only return positive drops
    
    def _days_until(self, date_str: str) -> Optional[int]:
        """Calculate days until a date."""
        if not date_str:
            return None
        try:
            target = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            delta = target - datetime.now(timezone.utc)
            return max(0, delta.days)
        except:
            return None
    
    async def _execute_retention_action(
        self,
        creator_id: str,
        subscription: Dict,
        action: str,
        custom_message: str = None
    ) -> Dict[str, Any]:
        """Execute a specific retention action."""
        # For now, log the action (email integration is mocked)
        logger.info(f"Executing retention action {action} for creator {creator_id}")
        
        # In production, this would trigger actual emails, notifications, etc.
        if action == RetentionAction.WELCOME_EMAIL:
            return {"success": True, "action": "welcome_email_queued"}
        elif action == RetentionAction.ENGAGEMENT_NUDGE:
            # Send WebSocket notification if available
            if self.ws_manager:
                try:
                    from websocket_service import NotificationType
                    await self.ws_manager.send_to_user(
                        creator_id,
                        NotificationType.SYSTEM_ALERT,
                        {
                            "title": "We miss you!",
                            "message": custom_message or "It's been a while since your last proposal. Ready to create something new?",
                            "action_url": "/creator/dashboard?action=new-proposal"
                        }
                    )
                    return {"success": True, "action": "notification_sent"}
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
            return {"success": True, "action": "engagement_nudge_logged"}
        elif action == RetentionAction.DISCOUNT_OFFER:
            return {"success": True, "action": "discount_offer_logged", "note": "Manual follow-up required"}
        else:
            return {"success": True, "action": f"{action}_logged"}
