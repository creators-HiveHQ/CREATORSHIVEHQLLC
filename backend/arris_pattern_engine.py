"""
ARRIS Pattern Engine - Phase 4 Module A
Platform-wide pattern detection and analytics for admin insights

This module implements:
1. Platform-Wide Pattern Detection - Aggregate patterns across all creators
2. Cohort Analysis - Group creators by behavior and outcomes
3. Revenue Patterns - Financial trend analysis via Calculator integration
4. Churn Predictors - Early warning system for subscription cancellations
5. Trend Analysis - Temporal pattern detection
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class PatternType:
    """Types of platform-wide patterns"""
    SUCCESS = "success"
    RISK = "risk"
    CHURN = "churn"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    GROWTH = "growth"
    SEASONAL = "seasonal"
    COHORT = "cohort"


class TrendDirection:
    """Trend direction indicators"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class ArrisPatternEngine:
    """
    ARRIS Pattern Engine for Platform-Wide Analytics
    
    Provides admin-level insights by analyzing patterns across:
    - All creators and their proposals
    - Subscription and revenue data
    - Engagement and activity metrics
    - Temporal trends and seasonality
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.pattern_cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.last_cache_time = None
    
    # ============== MAIN ANALYSIS METHODS ==============
    
    async def get_platform_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive platform pattern overview for admin dashboard.
        """
        now = datetime.now(timezone.utc)
        
        # Core metrics
        total_creators = await self.db.creators.count_documents({"status": "active"})
        total_proposals = await self.db.proposals.count_documents({})
        total_subscriptions = await self.db.creator_subscriptions.count_documents({"status": "active"})
        
        # Recent activity (last 30 days)
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        recent_proposals = await self.db.proposals.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        recent_registrations = await self.db.creators.count_documents({
            "submitted_at": {"$gte": thirty_days_ago}
        })
        
        # Calculate growth rates
        sixty_days_ago = (now - timedelta(days=60)).isoformat()
        prev_month_proposals = await self.db.proposals.count_documents({
            "created_at": {"$gte": sixty_days_ago, "$lt": thirty_days_ago}
        })
        proposal_growth = self._calculate_growth_rate(prev_month_proposals, recent_proposals)
        
        prev_month_registrations = await self.db.creators.count_documents({
            "submitted_at": {"$gte": sixty_days_ago, "$lt": thirty_days_ago}
        })
        registration_growth = self._calculate_growth_rate(prev_month_registrations, recent_registrations)
        
        return {
            "snapshot": {
                "total_creators": total_creators,
                "total_proposals": total_proposals,
                "active_subscriptions": total_subscriptions,
                "timestamp": now.isoformat()
            },
            "activity_30d": {
                "new_proposals": recent_proposals,
                "new_registrations": recent_registrations,
                "proposal_growth_pct": proposal_growth,
                "registration_growth_pct": registration_growth
            },
            "health_indicators": await self._calculate_platform_health()
        }
    
    async def detect_all_patterns(self) -> Dict[str, Any]:
        """
        Run comprehensive pattern detection across the platform.
        Returns categorized patterns with confidence scores and recommendations.
        """
        patterns = {
            "success_patterns": await self._detect_success_patterns(),
            "risk_patterns": await self._detect_risk_patterns(),
            "churn_patterns": await self._detect_churn_patterns(),
            "revenue_patterns": await self._detect_revenue_patterns(),
            "engagement_patterns": await self._detect_engagement_patterns(),
            "trend_patterns": await self._detect_trend_patterns(),
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "total_patterns": 0
        }
        
        # Count total patterns
        for key in patterns:
            if isinstance(patterns[key], list):
                patterns["total_patterns"] += len(patterns[key])
        
        return patterns
    
    async def get_cohort_analysis(self) -> Dict[str, Any]:
        """
        Analyze creators by cohort (registration month, tier, engagement level).
        """
        creators = await self.db.creators.find(
            {"status": "active"},
            {"_id": 0, "id": 1, "submitted_at": 1, "platforms": 1, "niche": 1}
        ).to_list(10000)
        
        subscriptions = await self.db.creator_subscriptions.find(
            {"status": "active"},
            {"_id": 0, "creator_id": 1, "tier": 1, "plan_id": 1, "created_at": 1}
        ).to_list(10000)
        
        proposals = await self.db.proposals.find(
            {},
            {"_id": 0, "user_id": 1, "status": 1, "created_at": 1}
        ).to_list(50000)
        
        # Build creator lookup
        sub_by_creator = {s["creator_id"]: s for s in subscriptions}
        proposals_by_creator = defaultdict(list)
        for p in proposals:
            proposals_by_creator[p.get("user_id")].append(p)
        
        # Cohort by tier
        tier_cohorts = defaultdict(lambda: {
            "count": 0,
            "total_proposals": 0,
            "approved_proposals": 0,
            "avg_proposals_per_creator": 0
        })
        
        # Cohort by registration month
        monthly_cohorts = defaultdict(lambda: {
            "count": 0,
            "retained": 0,
            "churned": 0
        })
        
        # Cohort by engagement level
        engagement_cohorts = {
            "highly_engaged": {"count": 0, "criteria": ">10 proposals"},
            "moderately_engaged": {"count": 0, "criteria": "3-10 proposals"},
            "low_engaged": {"count": 0, "criteria": "1-2 proposals"},
            "inactive": {"count": 0, "criteria": "0 proposals"}
        }
        
        for creator in creators:
            creator_id = creator.get("id")
            sub = sub_by_creator.get(creator_id, {})
            tier = sub.get("tier", "Free")
            creator_proposals = proposals_by_creator.get(creator_id, [])
            
            # Tier cohort
            tier_cohorts[tier]["count"] += 1
            tier_cohorts[tier]["total_proposals"] += len(creator_proposals)
            tier_cohorts[tier]["approved_proposals"] += len([
                p for p in creator_proposals 
                if p.get("status") in ["approved", "completed", "in_progress"]
            ])
            
            # Registration month cohort
            submitted_at = creator.get("submitted_at", "")
            if submitted_at:
                month = submitted_at[:7]  # YYYY-MM
                monthly_cohorts[month]["count"] += 1
                if sub.get("status") == "active":
                    monthly_cohorts[month]["retained"] += 1
                else:
                    monthly_cohorts[month]["churned"] += 1
            
            # Engagement cohort
            proposal_count = len(creator_proposals)
            if proposal_count > 10:
                engagement_cohorts["highly_engaged"]["count"] += 1
            elif proposal_count >= 3:
                engagement_cohorts["moderately_engaged"]["count"] += 1
            elif proposal_count >= 1:
                engagement_cohorts["low_engaged"]["count"] += 1
            else:
                engagement_cohorts["inactive"]["count"] += 1
        
        # Calculate averages for tier cohorts
        for tier, data in tier_cohorts.items():
            if data["count"] > 0:
                data["avg_proposals_per_creator"] = round(data["total_proposals"] / data["count"], 1)
                data["approval_rate"] = round(
                    (data["approved_proposals"] / max(1, data["total_proposals"])) * 100, 1
                )
        
        # Calculate retention rates for monthly cohorts
        monthly_list = []
        for month, data in sorted(monthly_cohorts.items(), reverse=True)[:12]:
            total = data["count"]
            if total > 0:
                data["retention_rate"] = round((data["retained"] / total) * 100, 1)
            else:
                data["retention_rate"] = 0
            monthly_list.append({"month": month, **data})
        
        return {
            "by_tier": dict(tier_cohorts),
            "by_registration_month": monthly_list,
            "by_engagement": engagement_cohorts,
            "total_creators_analyzed": len(creators),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_creator_ranking(
        self, 
        sort_by: str = "approval_rate",
        limit: int = 20,
        tier_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ranked list of creators by performance metrics.
        """
        creators = await self.db.creators.find(
            {"status": "active"},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "platforms": 1}
        ).to_list(10000)
        
        subscriptions = await self.db.creator_subscriptions.find(
            {"status": "active"},
            {"_id": 0, "creator_id": 1, "tier": 1}
        ).to_list(10000)
        
        sub_by_creator = {s["creator_id"]: s.get("tier", "Free") for s in subscriptions}
        
        proposals = await self.db.proposals.find(
            {},
            {"_id": 0, "user_id": 1, "status": 1, "created_at": 1}
        ).to_list(50000)
        
        proposals_by_creator = defaultdict(list)
        for p in proposals:
            proposals_by_creator[p.get("user_id")].append(p)
        
        rankings = []
        for creator in creators:
            creator_id = creator.get("id")
            tier = sub_by_creator.get(creator_id, "Free")
            
            if tier_filter and tier.lower() != tier_filter.lower():
                continue
            
            creator_proposals = proposals_by_creator.get(creator_id, [])
            total = len(creator_proposals)
            approved = len([p for p in creator_proposals if p.get("status") in ["approved", "completed", "in_progress"]])
            
            if total == 0:
                continue
            
            approval_rate = round((approved / total) * 100, 1)
            
            rankings.append({
                "creator_id": creator_id,
                "name": creator.get("name"),
                "email": creator.get("email"),
                "tier": tier,
                "total_proposals": total,
                "approved_proposals": approved,
                "approval_rate": approval_rate,
                "platforms": creator.get("platforms", [])
            })
        
        # Sort by the specified metric
        sort_key = {
            "approval_rate": lambda x: (-x["approval_rate"], -x["total_proposals"]),
            "total_proposals": lambda x: -x["total_proposals"],
            "approved_proposals": lambda x: -x["approved_proposals"]
        }.get(sort_by, lambda x: -x["approval_rate"])
        
        rankings.sort(key=sort_key)
        
        return rankings[:limit]
    
    async def get_revenue_analysis(self, period_days: int = 90) -> Dict[str, Any]:
        """
        Analyze revenue patterns from Calculator entries.
        """
        start_date = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()
        
        # Get calculator entries
        entries = await self.db.calculator.find(
            {"created_at": {"$gte": start_date}},
            {"_id": 0}
        ).to_list(10000)
        
        # Get subscription transactions
        transactions = await self.db.payment_transactions.find(
            {"created_at": {"$gte": start_date}, "status": "succeeded"},
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate metrics
        total_revenue = sum(e.get("revenue_usd", 0) for e in entries)
        total_expenses = sum(e.get("expenses_usd", 0) for e in entries)
        net_profit = total_revenue - total_expenses
        
        # Revenue by source
        revenue_by_source = defaultdict(float)
        for e in entries:
            source = e.get("revenue_source", "other")
            revenue_by_source[source] += e.get("revenue_usd", 0)
        
        # Revenue by tier
        revenue_by_tier = defaultdict(float)
        for t in transactions:
            tier = t.get("tier", "unknown")
            revenue_by_tier[tier] += t.get("amount", 0) / 100  # Convert cents to dollars
        
        # Monthly breakdown
        monthly_revenue = defaultdict(lambda: {"revenue": 0, "transactions": 0})
        for t in transactions:
            created = t.get("created_at", "")
            if created:
                month = created[:7]
                monthly_revenue[month]["revenue"] += t.get("amount", 0) / 100
                monthly_revenue[month]["transactions"] += 1
        
        monthly_list = [
            {"month": k, **v} 
            for k, v in sorted(monthly_revenue.items(), reverse=True)[:6]
        ]
        
        # Calculate MRR and growth
        current_subs = await self.db.creator_subscriptions.count_documents({"status": "active"})
        
        # Get tier pricing (simplified)
        tier_prices = {"starter": 9.99, "pro": 29.99, "premium": 99.99, "elite": 500}
        mrr = 0
        tier_counts = await self.db.creator_subscriptions.aggregate([
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
        ]).to_list(10)
        
        for tc in tier_counts:
            tier_name = (tc["_id"] or "free").lower()
            mrr += tc["count"] * tier_prices.get(tier_name, 0)
        
        return {
            "period_days": period_days,
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_expenses": round(total_expenses, 2),
                "net_profit": round(net_profit, 2),
                "profit_margin": round((net_profit / max(1, total_revenue)) * 100, 1),
                "mrr": round(mrr, 2),
                "arr": round(mrr * 12, 2),
                "active_subscriptions": current_subs
            },
            "by_source": dict(revenue_by_source),
            "by_tier": dict(revenue_by_tier),
            "monthly_trend": monthly_list,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_actionable_insights(self) -> List[Dict[str, Any]]:
        """
        Generate actionable insights for admin based on detected patterns.
        """
        insights = []
        
        # Insight 1: Churn risk analysis
        churn_patterns = await self._detect_churn_patterns()
        if churn_patterns:
            high_risk_count = len([p for p in churn_patterns if p.get("risk_level") == "high"])
            if high_risk_count > 0:
                insights.append({
                    "id": "churn-risk-alert",
                    "type": "warning",
                    "priority": "high",
                    "title": f"{high_risk_count} Creators at High Churn Risk",
                    "description": "These creators show signs of disengagement. Consider proactive outreach.",
                    "action": "View at-risk creators",
                    "action_url": "/admin/patterns?tab=churn",
                    "data": {"count": high_risk_count}
                })
        
        # Insight 2: Growth opportunity
        cohort = await self.get_cohort_analysis()
        engagement = cohort.get("by_engagement", {})
        inactive_count = engagement.get("inactive", {}).get("count", 0)
        if inactive_count > 5:
            insights.append({
                "id": "inactive-creators",
                "type": "opportunity",
                "priority": "medium",
                "title": f"{inactive_count} Inactive Creators",
                "description": "These creators haven't submitted any proposals. Re-engagement campaign could activate them.",
                "action": "Plan re-engagement",
                "action_url": "/admin/patterns?tab=cohort",
                "data": {"count": inactive_count}
            })
        
        # Insight 3: Top performing tier
        tier_data = cohort.get("by_tier", {})
        best_tier = None
        best_approval = 0
        for tier, data in tier_data.items():
            if data.get("approval_rate", 0) > best_approval and data.get("count", 0) >= 3:
                best_approval = data["approval_rate"]
                best_tier = tier
        
        if best_tier and best_approval > 60:
            insights.append({
                "id": "top-tier-performers",
                "type": "success",
                "priority": "low",
                "title": f"{best_tier} Tier Shows {best_approval}% Approval Rate",
                "description": f"Creators on {best_tier} tier are performing well. Consider highlighting these success stories.",
                "action": "View tier analysis",
                "action_url": "/admin/patterns?tab=cohort",
                "data": {"tier": best_tier, "approval_rate": best_approval}
            })
        
        # Insight 4: Revenue trend
        revenue = await self.get_revenue_analysis(30)
        monthly = revenue.get("monthly_trend", [])
        if len(monthly) >= 2:
            current = monthly[0].get("revenue", 0)
            previous = monthly[1].get("revenue", 0)
            if previous > 0:
                growth = ((current - previous) / previous) * 100
                if growth > 20:
                    insights.append({
                        "id": "revenue-growth",
                        "type": "success",
                        "priority": "high",
                        "title": f"Revenue Up {growth:.1f}% This Month",
                        "description": f"Strong month-over-month growth from ${previous:.0f} to ${current:.0f}.",
                        "action": "View revenue details",
                        "action_url": "/revenue",
                        "data": {"growth_pct": round(growth, 1)}
                    })
                elif growth < -10:
                    insights.append({
                        "id": "revenue-decline",
                        "type": "warning",
                        "priority": "high",
                        "title": f"Revenue Down {abs(growth):.1f}% This Month",
                        "description": f"Revenue declined from ${previous:.0f} to ${current:.0f}. Review churn and acquisition.",
                        "action": "Investigate",
                        "action_url": "/revenue",
                        "data": {"growth_pct": round(growth, 1)}
                    })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: priority_order.get(x.get("priority"), 3))
        
        return insights
    
    # ============== PATTERN DETECTION METHODS ==============
    
    async def _detect_success_patterns(self) -> List[Dict[str, Any]]:
        """Detect platform-wide success patterns."""
        patterns = []
        
        # Aggregate proposal success by platform
        pipeline = [
            {"$unwind": {"path": "$platforms", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": "$platforms",
                "total": {"$sum": 1},
                "approved": {"$sum": {"$cond": [
                    {"$in": ["$status", ["approved", "completed", "in_progress"]]}, 1, 0
                ]}}
            }},
            {"$match": {"total": {"$gte": 5}}}
        ]
        
        platform_stats = await self.db.proposals.aggregate(pipeline).to_list(20)
        
        for stat in platform_stats:
            platform = stat["_id"] or "Unspecified"
            total = stat["total"]
            approved = stat["approved"]
            rate = (approved / total) * 100
            
            if rate >= 70:
                patterns.append({
                    "category": PatternType.SUCCESS,
                    "type": "high_performing_platform",
                    "title": f"{platform} Shows High Success",
                    "description": f"{rate:.0f}% approval rate across {total} proposals",
                    "confidence": min(0.95, rate / 100 + (total / 100)),
                    "data": {"platform": platform, "approval_rate": round(rate, 1), "sample_size": total},
                    "recommendation": f"Encourage creators to focus on {platform} content"
                })
        
        # Success by priority level
        priority_pipeline = [
            {"$group": {
                "_id": "$priority",
                "total": {"$sum": 1},
                "approved": {"$sum": {"$cond": [
                    {"$in": ["$status", ["approved", "completed", "in_progress"]]}, 1, 0
                ]}}
            }},
            {"$match": {"total": {"$gte": 10}}}
        ]
        
        priority_stats = await self.db.proposals.aggregate(priority_pipeline).to_list(10)
        
        for stat in priority_stats:
            priority = stat["_id"] or "medium"
            total = stat["total"]
            approved = stat["approved"]
            rate = (approved / total) * 100
            
            if rate >= 65:
                patterns.append({
                    "category": PatternType.SUCCESS,
                    "type": "priority_success_correlation",
                    "title": f"{priority.title()} Priority Correlates with Success",
                    "description": f"{rate:.0f}% approval rate for {priority} priority proposals",
                    "confidence": min(0.9, rate / 100),
                    "data": {"priority": priority, "approval_rate": round(rate, 1), "sample_size": total},
                    "recommendation": f"Suggest {priority} priority for new proposals"
                })
        
        return patterns
    
    async def _detect_risk_patterns(self) -> List[Dict[str, Any]]:
        """Detect platform-wide risk patterns."""
        patterns = []
        
        # High rejection rate platforms
        pipeline = [
            {"$unwind": {"path": "$platforms", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": "$platforms",
                "total": {"$sum": 1},
                "rejected": {"$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}}
            }},
            {"$match": {"total": {"$gte": 5}}}
        ]
        
        platform_stats = await self.db.proposals.aggregate(pipeline).to_list(20)
        
        for stat in platform_stats:
            platform = stat["_id"] or "Unspecified"
            total = stat["total"]
            rejected = stat["rejected"]
            rejection_rate = (rejected / total) * 100
            
            if rejection_rate >= 40:
                patterns.append({
                    "category": PatternType.RISK,
                    "type": "high_rejection_platform",
                    "title": f"{platform} Has High Rejection Rate",
                    "description": f"{rejection_rate:.0f}% rejection rate across {total} proposals",
                    "confidence": min(0.9, rejection_rate / 100 + (total / 100)),
                    "data": {"platform": platform, "rejection_rate": round(rejection_rate, 1), "sample_size": total},
                    "recommendation": f"Review {platform} proposal quality guidelines"
                })
        
        # Creators with declining approval
        # (Simplified: check creators with recent rejections)
        recent_rejections = await self.db.proposals.find(
            {"status": "rejected", "created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}},
            {"_id": 0, "user_id": 1}
        ).to_list(1000)
        
        rejection_counts = defaultdict(int)
        for r in recent_rejections:
            rejection_counts[r.get("user_id")] += 1
        
        creators_at_risk = [cid for cid, count in rejection_counts.items() if count >= 3]
        if creators_at_risk:
            patterns.append({
                "category": PatternType.RISK,
                "type": "creators_with_multiple_rejections",
                "title": f"{len(creators_at_risk)} Creators with 3+ Recent Rejections",
                "description": "These creators may need coaching or be at churn risk",
                "confidence": 0.8,
                "data": {"creator_count": len(creators_at_risk), "creator_ids": creators_at_risk[:10]},
                "recommendation": "Proactive outreach to understand issues and provide guidance"
            })
        
        return patterns
    
    async def _detect_churn_patterns(self) -> List[Dict[str, Any]]:
        """Detect churn risk indicators."""
        patterns = []
        
        # Get active creators
        creators = await self.db.creators.find(
            {"status": "active"},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "submitted_at": 1}
        ).to_list(10000)
        
        # Get their recent activity
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        
        for creator in creators:
            creator_id = creator.get("id")
            
            # Check last proposal date
            last_proposal = await self.db.proposals.find_one(
                {"user_id": creator_id},
                {"_id": 0, "created_at": 1},
                sort=[("created_at", -1)]
            )
            
            # Check subscription status
            subscription = await self.db.creator_subscriptions.find_one(
                {"creator_id": creator_id, "status": "active"},
                {"_id": 0, "tier": 1, "created_at": 1}
            )
            
            # Calculate risk score
            risk_score = 0
            risk_factors = []
            
            if not last_proposal:
                risk_score += 40
                risk_factors.append("No proposals ever submitted")
            elif last_proposal.get("created_at", "") < ninety_days_ago:
                risk_score += 30
                risk_factors.append("No proposals in 90+ days")
            elif last_proposal.get("created_at", "") < thirty_days_ago:
                risk_score += 15
                risk_factors.append("No proposals in 30+ days")
            
            if subscription and subscription.get("tier", "").lower() not in ["premium", "elite"]:
                # Lower tier = easier to churn
                risk_score += 10
                risk_factors.append(f"On {subscription.get('tier', 'Free')} tier")
            
            if not subscription:
                risk_score += 20
                risk_factors.append("No active subscription")
            
            # Only flag high-risk creators
            if risk_score >= 40:
                patterns.append({
                    "category": PatternType.CHURN,
                    "type": "churn_risk_creator",
                    "creator_id": creator_id,
                    "creator_name": creator.get("name"),
                    "creator_email": creator.get("email"),
                    "risk_score": risk_score,
                    "risk_level": "high" if risk_score >= 60 else "medium",
                    "risk_factors": risk_factors,
                    "recommendation": "Outreach with personalized re-engagement"
                })
        
        # Sort by risk score
        patterns.sort(key=lambda x: -x.get("risk_score", 0))
        
        return patterns[:50]  # Top 50 at-risk creators
    
    async def _detect_revenue_patterns(self) -> List[Dict[str, Any]]:
        """Detect revenue-related patterns."""
        patterns = []
        
        # Get subscription tier distribution
        tier_pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
        ]
        
        tier_stats = await self.db.creator_subscriptions.aggregate(tier_pipeline).to_list(10)
        tier_dict = {t["_id"]: t["count"] for t in tier_stats}
        total_subs = sum(tier_dict.values())
        
        if total_subs > 0:
            # Check tier concentration
            for tier, count in tier_dict.items():
                pct = (count / total_subs) * 100
                if pct > 50 and tier and tier.lower() in ["free", "starter"]:
                    patterns.append({
                        "category": PatternType.REVENUE,
                        "type": "low_tier_concentration",
                        "title": f"{pct:.0f}% of Subscribers on {tier} Tier",
                        "description": "High concentration on lower tiers limits revenue potential",
                        "confidence": 0.85,
                        "data": {"tier": tier, "percentage": round(pct, 1), "count": count},
                        "recommendation": "Focus on upgrade campaigns and premium feature awareness"
                    })
                elif pct > 20 and tier and tier.lower() in ["premium", "elite"]:
                    patterns.append({
                        "category": PatternType.REVENUE,
                        "type": "healthy_premium_mix",
                        "title": f"Strong Premium Adoption at {pct:.0f}%",
                        "description": f"{count} creators on {tier} tier driving revenue",
                        "confidence": 0.9,
                        "data": {"tier": tier, "percentage": round(pct, 1), "count": count},
                        "recommendation": "Maintain premium value and consider loyalty benefits"
                    })
        
        return patterns
    
    async def _detect_engagement_patterns(self) -> List[Dict[str, Any]]:
        """Detect engagement-related patterns."""
        patterns = []
        
        # ARRIS usage patterns
        arris_logs = await self.db.arris_usage_log.find(
            {"timestamp": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}},
            {"_id": 0, "user_id": 1, "query_category": 1, "success": 1}
        ).to_list(10000)
        
        if arris_logs:
            # Category distribution
            categories = defaultdict(int)
            for log in arris_logs:
                categories[log.get("query_category", "other")] += 1
            
            total_queries = len(arris_logs)
            top_category = max(categories.items(), key=lambda x: x[1]) if categories else ("none", 0)
            
            if top_category[0] != "none":
                patterns.append({
                    "category": PatternType.ENGAGEMENT,
                    "type": "arris_usage_pattern",
                    "title": f"Top ARRIS Usage: {top_category[0]}",
                    "description": f"{top_category[1]} queries ({(top_category[1]/total_queries)*100:.0f}% of total)",
                    "confidence": 0.85,
                    "data": {"category": top_category[0], "count": top_category[1], "total": total_queries},
                    "recommendation": "Optimize ARRIS responses for this category"
                })
            
            # Success rate
            success_count = len([l for l in arris_logs if l.get("success")])
            success_rate = (success_count / total_queries) * 100
            
            if success_rate < 90:
                patterns.append({
                    "category": PatternType.ENGAGEMENT,
                    "type": "arris_success_rate",
                    "title": f"ARRIS Success Rate at {success_rate:.0f}%",
                    "description": f"{total_queries - success_count} failed queries in the last 30 days",
                    "confidence": 0.9,
                    "data": {"success_rate": round(success_rate, 1), "failed": total_queries - success_count},
                    "recommendation": "Review failed queries for improvement opportunities"
                })
        
        return patterns
    
    async def _detect_trend_patterns(self) -> List[Dict[str, Any]]:
        """Detect temporal trend patterns."""
        patterns = []
        
        # Weekly proposal submission trend
        weekly_pipeline = [
            {"$match": {"created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=56)).isoformat()}}},
            {"$project": {
                "week": {"$dateToString": {"format": "%Y-W%V", "date": {"$dateFromString": {"dateString": "$created_at"}}}}
            }},
            {"$group": {"_id": "$week", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        weekly_data = await self.db.proposals.aggregate(weekly_pipeline).to_list(10)
        
        if len(weekly_data) >= 4:
            counts = [w["count"] for w in weekly_data]
            
            # Calculate trend
            first_half_avg = statistics.mean(counts[:len(counts)//2]) if counts[:len(counts)//2] else 0
            second_half_avg = statistics.mean(counts[len(counts)//2:]) if counts[len(counts)//2:] else 0
            
            if first_half_avg > 0:
                trend_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                if trend_pct > 20:
                    patterns.append({
                        "category": PatternType.GROWTH,
                        "type": "proposal_growth_trend",
                        "title": f"Proposal Submissions Growing {trend_pct:.0f}%",
                        "description": "Strong upward trend in creator activity",
                        "confidence": 0.8,
                        "data": {"trend_pct": round(trend_pct, 1), "direction": TrendDirection.UP},
                        "recommendation": "Prepare for increased review workload"
                    })
                elif trend_pct < -20:
                    patterns.append({
                        "category": PatternType.GROWTH,
                        "type": "proposal_decline_trend",
                        "title": f"Proposal Submissions Down {abs(trend_pct):.0f}%",
                        "description": "Declining creator activity - may indicate engagement issues",
                        "confidence": 0.8,
                        "data": {"trend_pct": round(trend_pct, 1), "direction": TrendDirection.DOWN},
                        "recommendation": "Investigate causes and plan re-engagement"
                    })
        
        return patterns
    
    # ============== HELPER METHODS ==============
    
    def _calculate_growth_rate(self, previous: int, current: int) -> float:
        """Calculate percentage growth rate."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)
    
    async def _calculate_platform_health(self) -> Dict[str, Any]:
        """Calculate overall platform health score."""
        scores = {}
        
        # 1. Engagement score (based on active proposals)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        active_creators = await self.db.proposals.distinct("user_id", {"created_at": {"$gte": thirty_days_ago}})
        total_creators = await self.db.creators.count_documents({"status": "active"})
        
        engagement_rate = (len(active_creators) / max(1, total_creators)) * 100
        scores["engagement"] = min(100, engagement_rate * 2)  # 50% active = 100 score
        
        # 2. Success score (approval rate)
        total_proposals = await self.db.proposals.count_documents({})
        approved = await self.db.proposals.count_documents({"status": {"$in": ["approved", "completed", "in_progress"]}})
        approval_rate = (approved / max(1, total_proposals)) * 100
        scores["success"] = min(100, approval_rate * 1.5)  # 67% approval = 100 score
        
        # 3. Revenue score (subscription coverage)
        paid_subs = await self.db.creator_subscriptions.count_documents({
            "status": "active",
            "tier": {"$nin": ["Free", "free", None]}
        })
        revenue_rate = (paid_subs / max(1, total_creators)) * 100
        scores["revenue"] = min(100, revenue_rate * 2)  # 50% paid = 100 score
        
        # Overall health
        overall = (scores["engagement"] + scores["success"] + scores["revenue"]) / 3
        
        return {
            "overall": round(overall),
            "engagement": round(scores["engagement"]),
            "success": round(scores["success"]),
            "revenue": round(scores["revenue"]),
            "status": "excellent" if overall >= 80 else "good" if overall >= 60 else "fair" if overall >= 40 else "needs_attention"
        }


# Global instance (will be initialized in server startup)
pattern_engine = None
