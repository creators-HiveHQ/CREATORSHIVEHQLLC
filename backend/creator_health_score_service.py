"""
Creator Health Score Service (Module B4)
=========================================
Computes daily health scores for Pro+ creators.
Analyzes engagement, proposal success, platform activity, and provides actionable insights.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)


# Health score components and weights
HEALTH_COMPONENTS = {
    "engagement": {
        "weight": 25,
        "label": "Engagement",
        "description": "How actively you interact with the platform",
        "icon": "🎯"
    },
    "proposal_success": {
        "weight": 25,
        "label": "Proposal Success",
        "description": "Your proposal approval and completion rate",
        "icon": "📋"
    },
    "consistency": {
        "weight": 20,
        "label": "Consistency",
        "description": "Regular activity and proposal submissions",
        "icon": "📈"
    },
    "arris_utilization": {
        "weight": 15,
        "label": "ARRIS Utilization",
        "description": "How well you leverage ARRIS insights",
        "icon": "🧠"
    },
    "profile_completeness": {
        "weight": 15,
        "label": "Profile Completeness",
        "description": "How complete your creator profile is",
        "icon": "✨"
    }
}


# Health status thresholds
HEALTH_STATUS = {
    "excellent": {"min": 85, "color": "green", "label": "Excellent", "emoji": "🌟"},
    "good": {"min": 70, "color": "blue", "label": "Good", "emoji": "👍"},
    "fair": {"min": 50, "color": "amber", "label": "Fair", "emoji": "⚡"},
    "needs_attention": {"min": 30, "color": "orange", "label": "Needs Attention", "emoji": "⚠️"},
    "critical": {"min": 0, "color": "red", "label": "Critical", "emoji": "🚨"}
}


# Achievement badges
ACHIEVEMENTS = {
    "first_proposal": {"label": "First Steps", "description": "Submitted your first proposal", "icon": "🎉"},
    "five_approved": {"label": "Rising Star", "description": "5 proposals approved", "icon": "⭐"},
    "ten_approved": {"label": "Proven Creator", "description": "10 proposals approved", "icon": "🌟"},
    "streak_7": {"label": "Week Warrior", "description": "7-day activity streak", "icon": "🔥"},
    "streak_30": {"label": "Monthly Master", "description": "30-day activity streak", "icon": "💎"},
    "high_approval": {"label": "Quality Champion", "description": "80%+ approval rate", "icon": "🏆"},
    "arris_expert": {"label": "ARRIS Expert", "description": "Used ARRIS insights 10+ times", "icon": "🧠"},
    "complete_profile": {"label": "Profile Pro", "description": "100% profile completion", "icon": "✨"}
}


class CreatorHealthScoreService:
    """
    Service for computing and tracking creator health scores.
    Available to Pro+ tier creators.
    """
    
    def __init__(self, db, feature_gating=None):
        self.db = db
        self.feature_gating = feature_gating
    
    async def has_access(self, creator_id: str) -> Dict[str, Any]:
        """Check if creator has access to health score (Pro+ only)."""
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
            "upgrade_message": "Upgrade to Pro to unlock your personal health score dashboard" if not has_access else None
        }
    
    async def get_health_score(self, creator_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health score for a creator.
        Returns overall score, component scores, and recommendations.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "access_denied": True,
                "upgrade_message": access["upgrade_message"],
                "tier": access["tier"]
            }
        
        # Get creator data
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0}
        )
        
        if not creator:
            return {"error": "Creator not found"}
        
        # Calculate component scores
        components = await self._calculate_components(creator_id, creator)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(components)
        
        # Determine status
        status = self._get_status(overall_score)
        
        # Get trend data
        trend = await self._get_score_trend(creator_id)
        
        # Get achievements
        achievements = await self._get_achievements(creator_id, creator, components)
        
        # Get recommendations
        recommendations = self._get_recommendations(components, overall_score)
        
        # Store today's score for trend tracking
        await self._store_daily_score(creator_id, overall_score, components)
        
        return {
            "creator_id": creator_id,
            "overall_score": overall_score,
            "status": status,
            "components": components,
            "trend": trend,
            "achievements": achievements,
            "recommendations": recommendations,
            "tier": access["tier"],
            "access_denied": False,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_health_history(
        self,
        creator_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get historical health scores for trend analysis."""
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {"access_denied": True, "upgrade_message": access["upgrade_message"]}
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        history = await self.db.creator_health_history.find(
            {
                "creator_id": creator_id,
                "date": {"$gte": cutoff.isoformat()[:10]}
            },
            {"_id": 0}
        ).sort("date", 1).to_list(days)
        
        return {
            "history": history,
            "days": days,
            "access_denied": False
        }
    
    async def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get top creators by health score.
        Names are partially masked for privacy.
        """
        # Get recent health scores
        today = datetime.now(timezone.utc).isoformat()[:10]
        
        scores = await self.db.creator_health_history.find(
            {"date": today},
            {"_id": 0}
        ).sort("overall_score", -1).limit(limit).to_list(limit)
        
        # Mask names for privacy
        leaderboard = []
        for i, score in enumerate(scores):
            creator = await self.db.creators.find_one(
                {"id": score.get("creator_id")},
                {"name": 1, "email": 1}
            )
            if creator:
                name = creator.get("name", "Anonymous")
                masked_name = name[:2] + "***" + name[-1] if len(name) > 3 else name[:1] + "***"
                leaderboard.append({
                    "rank": i + 1,
                    "name": masked_name,
                    "score": score.get("overall_score", 0),
                    "status": self._get_status(score.get("overall_score", 0))
                })
        
        return {"leaderboard": leaderboard, "date": today}
    
    async def get_component_details(
        self,
        creator_id: str,
        component: str
    ) -> Dict[str, Any]:
        """Get detailed breakdown of a specific health component."""
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {"access_denied": True}
        
        if component not in HEALTH_COMPONENTS:
            return {"error": f"Unknown component: {component}"}
        
        creator = await self.db.creators.find_one({"id": creator_id}, {"_id": 0})
        if not creator:
            return {"error": "Creator not found"}
        
        # Get detailed analysis for the component
        if component == "engagement":
            details = await self._analyze_engagement_details(creator_id)
        elif component == "proposal_success":
            details = await self._analyze_proposal_details(creator_id)
        elif component == "consistency":
            details = await self._analyze_consistency_details(creator_id)
        elif component == "arris_utilization":
            details = await self._analyze_arris_details(creator_id)
        elif component == "profile_completeness":
            details = await self._analyze_profile_details(creator_id, creator)
        else:
            details = {}
        
        component_info = HEALTH_COMPONENTS[component]
        
        return {
            "component": component,
            "label": component_info["label"],
            "description": component_info["description"],
            "icon": component_info["icon"],
            "weight": component_info["weight"],
            "details": details,
            "access_denied": False
        }
    
    # ============== PRIVATE CALCULATION METHODS ==============
    
    async def _calculate_components(
        self,
        creator_id: str,
        creator: Dict
    ) -> Dict[str, Any]:
        """Calculate all health score components."""
        components = {}
        
        # 1. Engagement Score
        engagement = await self._calculate_engagement(creator_id)
        components["engagement"] = {
            **HEALTH_COMPONENTS["engagement"],
            "score": engagement["score"],
            "metrics": engagement["metrics"]
        }
        
        # 2. Proposal Success Score
        proposal_success = await self._calculate_proposal_success(creator_id)
        components["proposal_success"] = {
            **HEALTH_COMPONENTS["proposal_success"],
            "score": proposal_success["score"],
            "metrics": proposal_success["metrics"]
        }
        
        # 3. Consistency Score
        consistency = await self._calculate_consistency(creator_id)
        components["consistency"] = {
            **HEALTH_COMPONENTS["consistency"],
            "score": consistency["score"],
            "metrics": consistency["metrics"]
        }
        
        # 4. ARRIS Utilization Score
        arris = await self._calculate_arris_utilization(creator_id)
        components["arris_utilization"] = {
            **HEALTH_COMPONENTS["arris_utilization"],
            "score": arris["score"],
            "metrics": arris["metrics"]
        }
        
        # 5. Profile Completeness Score
        profile = await self._calculate_profile_completeness(creator_id, creator)
        components["profile_completeness"] = {
            **HEALTH_COMPONENTS["profile_completeness"],
            "score": profile["score"],
            "metrics": profile["metrics"]
        }
        
        return components
    
    async def _calculate_engagement(self, creator_id: str) -> Dict[str, Any]:
        """Calculate engagement score based on platform activity."""
        now = datetime.now(timezone.utc)
        
        # Last 30 days activity
        cutoff_30d = now - timedelta(days=30)
        
        # Count proposals in last 30 days
        recent_proposals = await self.db.proposals.count_documents({
            "user_id": creator_id,
            "created_at": {"$gte": cutoff_30d.isoformat()}
        })
        
        # Count ARRIS interactions in last 30 days
        arris_interactions = await self.db.arris_usage.count_documents({
            "user_id": creator_id,
            "timestamp": {"$gte": cutoff_30d.isoformat()}
        })
        
        # Last activity
        last_proposal = await self.db.proposals.find_one(
            {"user_id": creator_id},
            {"created_at": 1},
            sort=[("created_at", -1)]
        )
        
        days_since_last = 30
        if last_proposal:
            try:
                last_date = datetime.fromisoformat(last_proposal.get("created_at", "").replace("Z", "+00:00"))
                days_since_last = (now - last_date).days
            except:
                pass
        
        # Calculate score
        score = 0
        
        # Proposals (max 40 points)
        score += min(40, recent_proposals * 10)
        
        # ARRIS interactions (max 30 points)
        score += min(30, arris_interactions * 5)
        
        # Recency (max 30 points)
        if days_since_last <= 3:
            score += 30
        elif days_since_last <= 7:
            score += 20
        elif days_since_last <= 14:
            score += 10
        
        return {
            "score": min(100, score),
            "metrics": {
                "recent_proposals": recent_proposals,
                "arris_interactions": arris_interactions,
                "days_since_last_activity": days_since_last
            }
        }
    
    async def _calculate_proposal_success(self, creator_id: str) -> Dict[str, Any]:
        """Calculate proposal success score."""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"status": 1}
        ).to_list(100)
        
        if not proposals:
            return {"score": 50, "metrics": {"total": 0, "approved": 0, "approval_rate": 0}}
        
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        rejected = len([p for p in proposals if p.get("status") == "rejected"])
        
        approval_rate = approved / total if total > 0 else 0
        
        # Calculate score
        score = int(approval_rate * 100)
        
        # Bonus for volume
        if total >= 10:
            score = min(100, score + 10)
        elif total >= 5:
            score = min(100, score + 5)
        
        return {
            "score": score,
            "metrics": {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "approval_rate": round(approval_rate, 2)
            }
        }
    
    async def _calculate_consistency(self, creator_id: str) -> Dict[str, Any]:
        """Calculate consistency score based on regular activity."""
        now = datetime.now(timezone.utc)
        
        # Get proposals from last 90 days
        cutoff = now - timedelta(days=90)
        proposals = await self.db.proposals.find(
            {
                "user_id": creator_id,
                "created_at": {"$gte": cutoff.isoformat()}
            },
            {"created_at": 1}
        ).sort("created_at", 1).to_list(100)
        
        if not proposals:
            return {"score": 30, "metrics": {"weeks_active": 0, "current_streak": 0, "avg_gap_days": None}}
        
        # Calculate weeks with activity
        weeks_active = set()
        dates = []
        for p in proposals:
            try:
                dt = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
                week = dt.isocalendar()[1]
                weeks_active.add((dt.year, week))
                dates.append(dt)
            except:
                pass
        
        # Calculate average gap between submissions
        gaps = []
        for i in range(len(dates) - 1):
            gap = (dates[i + 1] - dates[i]).days
            gaps.append(gap)
        
        avg_gap = sum(gaps) / len(gaps) if gaps else 30
        
        # Calculate current streak (days since last submission within 7 day window)
        current_streak = 0
        if dates:
            latest = max(dates)
            streak_start = latest
            for i, d in enumerate(sorted(dates, reverse=True)):
                if i == 0:
                    continue
                if (streak_start - d).days <= 7:
                    current_streak += 1
                    streak_start = d
                else:
                    break
        
        # Calculate score
        score = 0
        
        # Weeks active (max 50 points - 13 weeks in 90 days)
        weeks_ratio = len(weeks_active) / 13
        score += int(weeks_ratio * 50)
        
        # Average gap (max 30 points)
        if avg_gap <= 7:
            score += 30
        elif avg_gap <= 14:
            score += 20
        elif avg_gap <= 21:
            score += 10
        
        # Streak bonus (max 20 points)
        score += min(20, current_streak * 4)
        
        return {
            "score": min(100, score),
            "metrics": {
                "weeks_active": len(weeks_active),
                "current_streak": current_streak,
                "avg_gap_days": round(avg_gap, 1)
            }
        }
    
    async def _calculate_arris_utilization(self, creator_id: str) -> Dict[str, Any]:
        """Calculate ARRIS utilization score."""
        # Count proposals with ARRIS insights
        proposals_with_arris = await self.db.proposals.count_documents({
            "user_id": creator_id,
            "arris_insights": {"$exists": True, "$ne": None}
        })
        
        total_proposals = await self.db.proposals.count_documents({"user_id": creator_id})
        
        # Count ARRIS usage
        arris_usage = await self.db.arris_usage.count_documents({"user_id": creator_id})
        
        # Calculate utilization rate
        utilization_rate = proposals_with_arris / total_proposals if total_proposals > 0 else 0
        
        # Calculate score
        score = 0
        
        # Utilization rate (max 60 points)
        score += int(utilization_rate * 60)
        
        # ARRIS usage volume (max 40 points)
        score += min(40, arris_usage * 4)
        
        return {
            "score": min(100, score),
            "metrics": {
                "proposals_with_arris": proposals_with_arris,
                "total_proposals": total_proposals,
                "utilization_rate": round(utilization_rate, 2),
                "total_arris_uses": arris_usage
            }
        }
    
    async def _calculate_profile_completeness(
        self,
        creator_id: str,
        creator: Dict
    ) -> Dict[str, Any]:
        """Calculate profile completeness score."""
        fields = {
            "name": bool(creator.get("name")),
            "email": bool(creator.get("email")),
            "platforms": bool(creator.get("platforms") and len(creator.get("platforms", [])) > 0),
            "niche": bool(creator.get("niche")),
            "business_description": bool(creator.get("business_description")),
            "profile_image": bool(creator.get("profile_image")),
            "social_links": bool(creator.get("social_links") and len(creator.get("social_links", {})) > 0),
            "bio": bool(creator.get("bio")),
        }
        
        completed = sum(1 for v in fields.values() if v)
        total = len(fields)
        completeness_rate = completed / total
        
        score = int(completeness_rate * 100)
        
        missing = [k for k, v in fields.items() if not v]
        
        return {
            "score": score,
            "metrics": {
                "completed_fields": completed,
                "total_fields": total,
                "completeness_rate": round(completeness_rate, 2),
                "missing_fields": missing
            }
        }
    
    def _calculate_overall_score(self, components: Dict) -> int:
        """Calculate weighted overall score."""
        total_weight = 0
        weighted_sum = 0
        
        for name, data in components.items():
            weight = data.get("weight", 0)
            score = data.get("score", 0)
            total_weight += weight
            weighted_sum += weight * score
        
        if total_weight == 0:
            return 50
        
        return int(weighted_sum / total_weight)
    
    def _get_status(self, score: int) -> Dict[str, Any]:
        """Get status based on score."""
        for status_name, info in sorted(HEALTH_STATUS.items(), key=lambda x: -x[1]["min"]):
            if score >= info["min"]:
                return {
                    "name": status_name,
                    "label": info["label"],
                    "color": info["color"],
                    "emoji": info["emoji"]
                }
        return HEALTH_STATUS["critical"]
    
    async def _get_score_trend(self, creator_id: str) -> Dict[str, Any]:
        """Get score trend over last 7 days."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        
        history = await self.db.creator_health_history.find(
            {
                "creator_id": creator_id,
                "date": {"$gte": cutoff.isoformat()[:10]}
            },
            {"_id": 0, "date": 1, "overall_score": 1}
        ).sort("date", 1).to_list(7)
        
        if len(history) < 2:
            return {"direction": "stable", "change": 0, "data": history}
        
        first_score = history[0].get("overall_score", 50)
        last_score = history[-1].get("overall_score", 50)
        change = last_score - first_score
        
        if change > 5:
            direction = "up"
        elif change < -5:
            direction = "down"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change": change,
            "data": history
        }
    
    async def _get_achievements(
        self,
        creator_id: str,
        creator: Dict,
        components: Dict
    ) -> List[Dict[str, Any]]:
        """Get earned achievements."""
        earned = []
        
        # Check each achievement
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"status": 1}
        ).to_list(100)
        
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        
        # First proposal
        if total >= 1:
            earned.append({**ACHIEVEMENTS["first_proposal"], "earned": True})
        
        # 5 approved
        if approved >= 5:
            earned.append({**ACHIEVEMENTS["five_approved"], "earned": True})
        
        # 10 approved
        if approved >= 10:
            earned.append({**ACHIEVEMENTS["ten_approved"], "earned": True})
        
        # High approval rate
        if total >= 5 and (approved / total) >= 0.8:
            earned.append({**ACHIEVEMENTS["high_approval"], "earned": True})
        
        # Profile complete
        if components.get("profile_completeness", {}).get("score", 0) >= 100:
            earned.append({**ACHIEVEMENTS["complete_profile"], "earned": True})
        
        # ARRIS expert
        arris_uses = components.get("arris_utilization", {}).get("metrics", {}).get("total_arris_uses", 0)
        if arris_uses >= 10:
            earned.append({**ACHIEVEMENTS["arris_expert"], "earned": True})
        
        return earned
    
    def _get_recommendations(
        self,
        components: Dict,
        overall_score: int
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations."""
        recommendations = []
        
        # Sort components by score (lowest first)
        sorted_components = sorted(
            components.items(),
            key=lambda x: x[1].get("score", 100)
        )
        
        for name, data in sorted_components[:3]:  # Focus on 3 weakest areas
            score = data.get("score", 100)
            
            if score >= 80:
                continue  # Skip if already good
            
            if name == "engagement" and score < 70:
                recommendations.append({
                    "component": name,
                    "title": "Boost Your Engagement",
                    "action": "Submit a new proposal or explore ARRIS insights to increase your engagement score.",
                    "impact": "high" if score < 50 else "medium"
                })
            
            elif name == "proposal_success" and score < 70:
                recommendations.append({
                    "component": name,
                    "title": "Improve Proposal Quality",
                    "action": "Use ARRIS recommendations before submitting proposals to improve approval rates.",
                    "impact": "high" if score < 50 else "medium"
                })
            
            elif name == "consistency" and score < 70:
                recommendations.append({
                    "component": name,
                    "title": "Stay Consistent",
                    "action": "Try to submit at least one proposal per week to build momentum.",
                    "impact": "medium"
                })
            
            elif name == "arris_utilization" and score < 70:
                recommendations.append({
                    "component": name,
                    "title": "Leverage ARRIS More",
                    "action": "Get ARRIS insights for your next proposal to improve success rates.",
                    "impact": "high" if score < 50 else "medium"
                })
            
            elif name == "profile_completeness" and score < 100:
                missing = data.get("metrics", {}).get("missing_fields", [])
                recommendations.append({
                    "component": name,
                    "title": "Complete Your Profile",
                    "action": f"Add your {', '.join(missing[:2])} to complete your profile.",
                    "impact": "low"
                })
        
        return recommendations
    
    async def _store_daily_score(
        self,
        creator_id: str,
        overall_score: int,
        components: Dict
    ):
        """Store daily score for trend tracking."""
        today = datetime.now(timezone.utc).isoformat()[:10]
        
        component_scores = {
            name: data.get("score", 0)
            for name, data in components.items()
        }
        
        await self.db.creator_health_history.update_one(
            {"creator_id": creator_id, "date": today},
            {
                "$set": {
                    "overall_score": overall_score,
                    "components": component_scores,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    # ============== DETAILED ANALYSIS METHODS ==============
    
    async def _analyze_engagement_details(self, creator_id: str) -> Dict:
        """Get detailed engagement analysis."""
        now = datetime.now(timezone.utc)
        
        # Activity by day of week
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"created_at": 1}
        ).to_list(100)
        
        day_activity = {d: 0 for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        for p in proposals:
            try:
                dt = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
                day = dt.strftime("%A")
                day_activity[day] += 1
            except:
                pass
        
        best_day = max(day_activity, key=day_activity.get) if any(day_activity.values()) else None
        
        return {
            "activity_by_day": day_activity,
            "best_day": best_day,
            "tip": f"You're most active on {best_day}s!" if best_day else "Start submitting proposals to track your activity patterns."
        }
    
    async def _analyze_proposal_details(self, creator_id: str) -> Dict:
        """Get detailed proposal analysis."""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "status": 1, "priority": 1, "created_at": 1}
        ).to_list(100)
        
        by_status = {}
        by_priority = {}
        
        for p in proposals:
            status = p.get("status", "draft")
            priority = p.get("priority", "medium")
            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            "by_status": by_status,
            "by_priority": by_priority,
            "tip": "High-priority proposals often get reviewed faster!"
        }
    
    async def _analyze_consistency_details(self, creator_id: str) -> Dict:
        """Get detailed consistency analysis."""
        now = datetime.now(timezone.utc)
        
        # Monthly activity
        months = {}
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"created_at": 1}
        ).to_list(100)
        
        for p in proposals:
            try:
                dt = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
                month_key = dt.strftime("%Y-%m")
                months[month_key] = months.get(month_key, 0) + 1
            except:
                pass
        
        return {
            "monthly_activity": months,
            "tip": "Consistent activity builds momentum and improves visibility!"
        }
    
    async def _analyze_arris_details(self, creator_id: str) -> Dict:
        """Get detailed ARRIS usage analysis."""
        # ARRIS usage types
        usage = await self.db.arris_usage.find(
            {"user_id": creator_id},
            {"_id": 0, "type": 1, "timestamp": 1}
        ).to_list(100)
        
        by_type = {}
        for u in usage:
            utype = u.get("type", "other")
            by_type[utype] = by_type.get(utype, 0) + 1
        
        return {
            "usage_by_type": by_type,
            "total_interactions": len(usage),
            "tip": "ARRIS insights can significantly improve your proposal success rate!"
        }
    
    async def _analyze_profile_details(self, creator_id: str, creator: Dict) -> Dict:
        """Get detailed profile analysis."""
        fields = {
            "name": {"value": creator.get("name"), "required": True},
            "email": {"value": creator.get("email"), "required": True},
            "platforms": {"value": creator.get("platforms"), "required": True},
            "niche": {"value": creator.get("niche"), "required": True},
            "business_description": {"value": creator.get("business_description"), "required": False},
            "profile_image": {"value": creator.get("profile_image"), "required": False},
            "social_links": {"value": creator.get("social_links"), "required": False},
            "bio": {"value": creator.get("bio"), "required": False},
        }
        
        return {
            "fields": {k: {"completed": bool(v["value"]), "required": v["required"]} for k, v in fields.items()},
            "tip": "A complete profile helps admins understand your work better!"
        }
