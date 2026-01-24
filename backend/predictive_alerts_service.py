"""
Predictive Alerts Service (Module A4)
=====================================
Sends WebSocket notifications for actionable patterns and predictive insights.
Analyzes creator data to detect opportunities, risks, and optimal timing.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import asyncio

logger = logging.getLogger(__name__)

# Alert types and priorities
class AlertType:
    # Timing alerts
    OPTIMAL_SUBMISSION_TIME = "optimal_submission_time"
    DEADLINE_APPROACHING = "deadline_approaching"
    MOMENTUM_OPPORTUNITY = "momentum_opportunity"
    
    # Performance alerts
    SUCCESS_STREAK = "success_streak"
    APPROVAL_RATE_CHANGE = "approval_rate_change"
    MILESTONE_REACHED = "milestone_reached"
    
    # Risk alerts
    DECLINING_PERFORMANCE = "declining_performance"
    INACTIVITY_WARNING = "inactivity_warning"
    PROPOSAL_AT_RISK = "proposal_at_risk"
    
    # Platform alerts
    PLATFORM_TREND = "platform_trend"
    BEST_PLATFORM_INSIGHT = "best_platform_insight"
    
    # ARRIS alerts
    ARRIS_RECOMMENDATION = "arris_recommendation"
    NEW_PATTERN_DISCOVERED = "new_pattern_discovered"
    INSIGHT_AVAILABLE = "insight_available"


# Alert priority levels
class AlertPriority:
    URGENT = "urgent"      # Immediate action needed
    HIGH = "high"          # Important, act soon
    MEDIUM = "medium"      # Good to know, act when convenient
    LOW = "low"            # FYI, no action required


# Alert configuration
ALERT_CONFIGS = {
    AlertType.OPTIMAL_SUBMISSION_TIME: {
        "icon": "⏰",
        "title": "Best Time to Submit",
        "priority": AlertPriority.HIGH,
        "category": "timing",
        "actionable": True,
        "cta_text": "Submit Now"
    },
    AlertType.DEADLINE_APPROACHING: {
        "icon": "⚡",
        "title": "Deadline Approaching",
        "priority": AlertPriority.URGENT,
        "category": "timing",
        "actionable": True,
        "cta_text": "Take Action"
    },
    AlertType.MOMENTUM_OPPORTUNITY: {
        "icon": "🚀",
        "title": "Momentum Opportunity",
        "priority": AlertPriority.HIGH,
        "category": "timing",
        "actionable": True,
        "cta_text": "Capitalize Now"
    },
    AlertType.SUCCESS_STREAK: {
        "icon": "🔥",
        "title": "You're on Fire!",
        "priority": AlertPriority.MEDIUM,
        "category": "performance",
        "actionable": False,
        "cta_text": None
    },
    AlertType.APPROVAL_RATE_CHANGE: {
        "icon": "📊",
        "title": "Performance Update",
        "priority": AlertPriority.MEDIUM,
        "category": "performance",
        "actionable": True,
        "cta_text": "View Details"
    },
    AlertType.MILESTONE_REACHED: {
        "icon": "🏆",
        "title": "Milestone Reached!",
        "priority": AlertPriority.MEDIUM,
        "category": "performance",
        "actionable": False,
        "cta_text": None
    },
    AlertType.DECLINING_PERFORMANCE: {
        "icon": "⚠️",
        "title": "Attention Needed",
        "priority": AlertPriority.HIGH,
        "category": "risk",
        "actionable": True,
        "cta_text": "Review Now"
    },
    AlertType.INACTIVITY_WARNING: {
        "icon": "💤",
        "title": "We Miss You!",
        "priority": AlertPriority.MEDIUM,
        "category": "risk",
        "actionable": True,
        "cta_text": "Create Proposal"
    },
    AlertType.PROPOSAL_AT_RISK: {
        "icon": "🚨",
        "title": "Proposal at Risk",
        "priority": AlertPriority.URGENT,
        "category": "risk",
        "actionable": True,
        "cta_text": "Review & Update"
    },
    AlertType.PLATFORM_TREND: {
        "icon": "📱",
        "title": "Platform Trend",
        "priority": AlertPriority.LOW,
        "category": "platform",
        "actionable": True,
        "cta_text": "Explore"
    },
    AlertType.BEST_PLATFORM_INSIGHT: {
        "icon": "🎯",
        "title": "Platform Insight",
        "priority": AlertPriority.MEDIUM,
        "category": "platform",
        "actionable": True,
        "cta_text": "Learn More"
    },
    AlertType.ARRIS_RECOMMENDATION: {
        "icon": "🧠",
        "title": "ARRIS Recommendation",
        "priority": AlertPriority.HIGH,
        "category": "arris",
        "actionable": True,
        "cta_text": "View Recommendation"
    },
    AlertType.NEW_PATTERN_DISCOVERED: {
        "icon": "🔮",
        "title": "New Pattern Found",
        "priority": AlertPriority.MEDIUM,
        "category": "arris",
        "actionable": True,
        "cta_text": "View Pattern"
    },
    AlertType.INSIGHT_AVAILABLE: {
        "icon": "💡",
        "title": "New Insight",
        "priority": AlertPriority.LOW,
        "category": "arris",
        "actionable": True,
        "cta_text": "View Insight"
    }
}


class PredictiveAlertsService:
    """
    Service for generating and managing predictive alerts.
    Sends real-time WebSocket notifications for actionable patterns.
    """
    
    def __init__(self, db, ws_manager=None, notification_service=None, feature_gating=None):
        self.db = db
        self.ws_manager = ws_manager
        self.notification_service = notification_service
        self.feature_gating = feature_gating
        self._running_checks = {}
    
    async def has_access(self, creator_id: str) -> Dict[str, Any]:
        """
        Check if creator has access to predictive alerts (Pro+ only).
        """
        if not self.feature_gating:
            return {"has_access": True, "tier": "unknown"}
        
        tier, features = await self.feature_gating.get_creator_tier(creator_id)
        tier_value = tier.value if hasattr(tier, 'value') else tier
        
        # Pro, Premium, and Elite have access
        has_access = tier_value in ["pro", "premium", "elite"]
        
        return {
            "has_access": has_access,
            "tier": tier_value,
            "upgrade_needed": not has_access,
            "upgrade_message": "Upgrade to Pro to receive predictive alerts" if not has_access else None
        }
    
    async def generate_alerts_for_creator(self, creator_id: str) -> List[Dict[str, Any]]:
        """
        Generate all applicable alerts for a creator.
        Called periodically or on-demand.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return []
        
        alerts = []
        
        # Run all alert checks
        alerts.extend(await self._check_timing_alerts(creator_id))
        alerts.extend(await self._check_performance_alerts(creator_id))
        alerts.extend(await self._check_risk_alerts(creator_id))
        alerts.extend(await self._check_platform_alerts(creator_id))
        
        # Sort by priority
        priority_order = {AlertPriority.URGENT: 0, AlertPriority.HIGH: 1, AlertPriority.MEDIUM: 2, AlertPriority.LOW: 3}
        alerts.sort(key=lambda a: priority_order.get(a.get("priority"), 4))
        
        return alerts
    
    async def get_creator_alerts(
        self,
        creator_id: str,
        include_dismissed: bool = False,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get alerts for a creator with filtering options.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "alerts": [],
                "access_denied": True,
                "upgrade_message": access["upgrade_message"],
                "tier": access["tier"]
            }
        
        # Get stored alerts
        query = {"creator_id": creator_id}
        if not include_dismissed:
            query["dismissed"] = {"$ne": True}
        
        stored_alerts = await self.db.creator_alerts.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Generate new alerts if none stored recently
        if not stored_alerts:
            new_alerts = await self.generate_alerts_for_creator(creator_id)
            # Store and return new alerts
            for alert in new_alerts:
                alert["creator_id"] = creator_id
                alert["dismissed"] = False
                alert["read"] = False
                await self.db.creator_alerts.insert_one(alert)
            stored_alerts = new_alerts
        
        # Count by priority
        priority_counts = {
            "urgent": len([a for a in stored_alerts if a.get("priority") == AlertPriority.URGENT]),
            "high": len([a for a in stored_alerts if a.get("priority") == AlertPriority.HIGH]),
            "medium": len([a for a in stored_alerts if a.get("priority") == AlertPriority.MEDIUM]),
            "low": len([a for a in stored_alerts if a.get("priority") == AlertPriority.LOW])
        }
        
        return {
            "alerts": stored_alerts,
            "total": len(stored_alerts),
            "unread": len([a for a in stored_alerts if not a.get("read")]),
            "priority_counts": priority_counts,
            "access_denied": False,
            "tier": access["tier"]
        }
    
    async def mark_alert_read(self, creator_id: str, alert_id: str) -> Dict[str, Any]:
        """Mark an alert as read."""
        result = await self.db.creator_alerts.update_one(
            {"creator_id": creator_id, "alert_id": alert_id},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"success": result.modified_count > 0}
    
    async def dismiss_alert(self, creator_id: str, alert_id: str) -> Dict[str, Any]:
        """Dismiss an alert (won't show again)."""
        result = await self.db.creator_alerts.update_one(
            {"creator_id": creator_id, "alert_id": alert_id},
            {"$set": {"dismissed": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"success": result.modified_count > 0}
    
    async def get_alert_preferences(self, creator_id: str) -> Dict[str, Any]:
        """Get alert notification preferences for a creator."""
        prefs = await self.db.alert_preferences.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not prefs:
            # Return default preferences
            prefs = {
                "creator_id": creator_id,
                "enabled": True,
                "categories": {
                    "timing": True,
                    "performance": True,
                    "risk": True,
                    "platform": True,
                    "arris": True
                },
                "priorities": {
                    "urgent": True,
                    "high": True,
                    "medium": True,
                    "low": False  # Low priority alerts off by default
                },
                "quiet_hours": {
                    "enabled": False,
                    "start": "22:00",
                    "end": "08:00"
                },
                "channels": {
                    "websocket": True,
                    "email": False  # Email alerts off by default
                }
            }
        
        return prefs
    
    async def update_alert_preferences(self, creator_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update alert notification preferences."""
        preferences["creator_id"] = creator_id
        preferences["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.db.alert_preferences.update_one(
            {"creator_id": creator_id},
            {"$set": preferences},
            upsert=True
        )
        
        return {"success": True, "preferences": preferences}
    
    async def send_alert(self, creator_id: str, alert: Dict[str, Any]) -> bool:
        """
        Send an alert to a creator via WebSocket.
        Returns True if notification was sent successfully.
        """
        # Check preferences
        prefs = await self.get_alert_preferences(creator_id)
        
        if not prefs.get("enabled", True):
            return False
        
        # Check category preference
        category = alert.get("category")
        if category and not prefs.get("categories", {}).get(category, True):
            return False
        
        # Check priority preference
        priority = alert.get("priority")
        if priority and not prefs.get("priorities", {}).get(priority, True):
            return False
        
        # Check quiet hours
        if prefs.get("quiet_hours", {}).get("enabled"):
            now = datetime.now(timezone.utc)
            start_hour = int(prefs["quiet_hours"]["start"].split(":")[0])
            end_hour = int(prefs["quiet_hours"]["end"].split(":")[0])
            current_hour = now.hour
            
            if start_hour > end_hour:  # Overnight quiet hours
                if current_hour >= start_hour or current_hour < end_hour:
                    return False
            else:
                if start_hour <= current_hour < end_hour:
                    return False
        
        # Send via WebSocket
        if self.ws_manager and prefs.get("channels", {}).get("websocket", True):
            try:
                from websocket_service import NotificationType
                
                # Use ARRIS_PATTERN_DETECTED for pattern alerts
                notification_type = NotificationType.ARRIS_PATTERN_DETECTED
                
                await self.ws_manager.send_to_user(
                    creator_id,
                    notification_type,
                    {
                        "alert_id": alert.get("alert_id"),
                        "alert_type": alert.get("alert_type"),
                        "title": alert.get("title"),
                        "message": alert.get("message"),
                        "priority": alert.get("priority"),
                        "category": alert.get("category"),
                        "icon": alert.get("icon"),
                        "actionable": alert.get("actionable"),
                        "cta_text": alert.get("cta_text"),
                        "cta_url": alert.get("cta_url"),
                        "data": alert.get("data", {})
                    }
                )
                logger.info(f"Alert sent to creator {creator_id}: {alert.get('alert_type')}")
                return True
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
                return False
        
        return False
    
    async def trigger_alert_check(self, creator_id: str) -> Dict[str, Any]:
        """
        Manually trigger an alert check for a creator.
        Useful after significant events (proposal submitted, approved, etc.)
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {"success": False, "reason": "access_denied"}
        
        alerts = await self.generate_alerts_for_creator(creator_id)
        sent_count = 0
        
        for alert in alerts:
            # Store alert
            alert["creator_id"] = creator_id
            alert["dismissed"] = False
            alert["read"] = False
            await self.db.creator_alerts.update_one(
                {"alert_id": alert["alert_id"]},
                {"$set": alert},
                upsert=True
            )
            
            # Send notification
            if await self.send_alert(creator_id, alert):
                sent_count += 1
        
        return {
            "success": True,
            "alerts_generated": len(alerts),
            "notifications_sent": sent_count
        }
    
    # ============== PRIVATE ALERT CHECK METHODS ==============
    
    async def _check_timing_alerts(self, creator_id: str) -> List[Dict[str, Any]]:
        """Check for timing-related alerts."""
        alerts = []
        now = datetime.now(timezone.utc)
        
        # Get creator's proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        if not proposals:
            return alerts
        
        # Analyze best submission days
        day_success = {}
        for p in proposals:
            try:
                created = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
                day = created.strftime("%A")
                if day not in day_success:
                    day_success[day] = {"total": 0, "approved": 0}
                day_success[day]["total"] += 1
                if p.get("status") in ["approved", "completed", "in_progress"]:
                    day_success[day]["approved"] += 1
            except:
                pass
        
        # Find best day and check if today is that day
        best_day = None
        best_rate = 0
        for day, counts in day_success.items():
            if counts["total"] >= 2:
                rate = counts["approved"] / counts["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_day = day
        
        today = now.strftime("%A")
        if best_day and today == best_day and best_rate >= 0.6:
            alerts.append(self._create_alert(
                alert_type=AlertType.OPTIMAL_SUBMISSION_TIME,
                message=f"Today ({best_day}) is your best day! Your proposals have {best_rate*100:.0f}% success rate on {best_day}s.",
                data={"best_day": best_day, "success_rate": best_rate},
                cta_url="/creator/dashboard?action=new-proposal"
            ))
        
        # Check for momentum opportunity (recent success streak)
        recent_proposals = proposals[:5]
        recent_success = len([p for p in recent_proposals if p.get("status") in ["approved", "completed"]])
        if recent_success >= 3:
            alerts.append(self._create_alert(
                alert_type=AlertType.MOMENTUM_OPPORTUNITY,
                message=f"You're on a roll! {recent_success} of your last 5 proposals were successful. Keep the momentum going!",
                data={"streak": recent_success, "total": 5},
                cta_url="/creator/dashboard?action=new-proposal"
            ))
        
        return alerts
    
    async def _check_performance_alerts(self, creator_id: str) -> List[Dict[str, Any]]:
        """Check for performance-related alerts."""
        alerts = []
        
        # Get creator's proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        if len(proposals) < 3:
            return alerts
        
        # Calculate success rate
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        success_rate = approved / total
        
        # Success streak check
        recent = proposals[:3]
        if all(p.get("status") in ["approved", "completed", "in_progress"] for p in recent):
            alerts.append(self._create_alert(
                alert_type=AlertType.SUCCESS_STREAK,
                message=f"🔥 3 proposals in a row approved! Your success rate is {success_rate*100:.0f}%.",
                data={"streak": 3, "success_rate": success_rate}
            ))
        
        # Milestone checks
        milestones = [5, 10, 25, 50, 100]
        for milestone in milestones:
            if approved == milestone:
                alerts.append(self._create_alert(
                    alert_type=AlertType.MILESTONE_REACHED,
                    message=f"Congratulations! You've reached {milestone} approved proposals!",
                    data={"milestone": milestone, "type": "approved_proposals"}
                ))
                break
        
        return alerts
    
    async def _check_risk_alerts(self, creator_id: str) -> List[Dict[str, Any]]:
        """Check for risk-related alerts."""
        alerts = []
        now = datetime.now(timezone.utc)
        
        # Get creator's proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        # Inactivity check - no proposals in 14+ days
        if proposals:
            try:
                latest = datetime.fromisoformat(proposals[0].get("created_at", "").replace("Z", "+00:00"))
                days_since = (now - latest).days
                
                if days_since >= 14:
                    alerts.append(self._create_alert(
                        alert_type=AlertType.INACTIVITY_WARNING,
                        message=f"It's been {days_since} days since your last proposal. Stay active to maintain momentum!",
                        data={"days_inactive": days_since},
                        cta_url="/creator/dashboard?action=new-proposal"
                    ))
            except:
                pass
        
        # Check for declining performance
        if len(proposals) >= 10:
            early = proposals[5:10]
            recent = proposals[:5]
            
            early_success = len([p for p in early if p.get("status") in ["approved", "completed"]]) / len(early)
            recent_success = len([p for p in recent if p.get("status") in ["approved", "completed"]]) / len(recent)
            
            if early_success > recent_success + 0.2:  # 20%+ decline
                alerts.append(self._create_alert(
                    alert_type=AlertType.DECLINING_PERFORMANCE,
                    message=f"Your recent approval rate ({recent_success*100:.0f}%) is lower than before ({early_success*100:.0f}%). Let's review your recent proposals.",
                    data={"recent_rate": recent_success, "previous_rate": early_success, "decline": early_success - recent_success},
                    cta_url="/creator/dashboard?tab=pattern-insights"
                ))
        
        # Check for proposals stuck under review
        stuck_proposals = [
            p for p in proposals 
            if p.get("status") == "under_review"
        ]
        
        for p in stuck_proposals[:3]:  # Limit to 3 alerts
            try:
                submitted = datetime.fromisoformat(p.get("submitted_at", p.get("created_at", "")).replace("Z", "+00:00"))
                days_in_review = (now - submitted).days
                
                if days_in_review >= 7:
                    alerts.append(self._create_alert(
                        alert_type=AlertType.PROPOSAL_AT_RISK,
                        message=f"'{p.get('title', 'Your proposal')}' has been under review for {days_in_review} days.",
                        data={"proposal_id": p.get("id"), "days_in_review": days_in_review},
                        cta_url=f"/creator/dashboard?tab=proposals&id={p.get('id')}"
                    ))
            except:
                pass
        
        return alerts
    
    async def _check_platform_alerts(self, creator_id: str) -> List[Dict[str, Any]]:
        """Check for platform-related alerts."""
        alerts = []
        
        # Get creator's proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        
        if len(proposals) < 5:
            return alerts
        
        # Analyze platform performance
        platform_stats = {}
        for p in proposals:
            for platform in p.get("platforms", []):
                if platform not in platform_stats:
                    platform_stats[platform] = {"total": 0, "approved": 0}
                platform_stats[platform]["total"] += 1
                if p.get("status") in ["approved", "completed", "in_progress"]:
                    platform_stats[platform]["approved"] += 1
        
        # Find best performing platform
        best_platform = None
        best_rate = 0
        for platform, stats in platform_stats.items():
            if stats["total"] >= 3:
                rate = stats["approved"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_platform = platform
        
        if best_platform and best_rate >= 0.7:
            alerts.append(self._create_alert(
                alert_type=AlertType.BEST_PLATFORM_INSIGHT,
                message=f"{best_platform} is your strongest platform with {best_rate*100:.0f}% success rate!",
                data={"platform": best_platform, "success_rate": best_rate, "total": platform_stats[best_platform]["total"]},
                cta_url="/creator/dashboard?tab=pattern-insights"
            ))
        
        return alerts
    
    def _create_alert(
        self,
        alert_type: str,
        message: str,
        data: Dict[str, Any] = None,
        cta_url: str = None
    ) -> Dict[str, Any]:
        """Create a standardized alert object."""
        config = ALERT_CONFIGS.get(alert_type, {})
        
        return {
            "alert_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
            "alert_type": alert_type,
            "title": config.get("title", "Alert"),
            "message": message,
            "icon": config.get("icon", "🔔"),
            "priority": config.get("priority", AlertPriority.MEDIUM),
            "category": config.get("category", "general"),
            "actionable": config.get("actionable", False),
            "cta_text": config.get("cta_text"),
            "cta_url": cta_url,
            "data": data or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }
