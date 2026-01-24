"""
Creator Pattern Insights Service (Module A3)
Provides personalized pattern analysis for Pro+ creators.
Analyzes creator-specific data to identify success patterns, trends, and actionable insights.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)

# Pattern categories
PATTERN_CATEGORIES = {
    "success": {"color": "green", "icon": "✅", "label": "Success Pattern"},
    "risk": {"color": "red", "icon": "⚠️", "label": "Risk Pattern"},
    "timing": {"color": "blue", "icon": "⏰", "label": "Timing Pattern"},
    "growth": {"color": "purple", "icon": "📈", "label": "Growth Pattern"},
    "engagement": {"color": "amber", "icon": "🎯", "label": "Engagement Pattern"},
    "platform": {"color": "indigo", "icon": "📱", "label": "Platform Pattern"},
    "content": {"color": "pink", "icon": "📝", "label": "Content Pattern"},
}

# Insight confidence levels
CONFIDENCE_LEVELS = {
    "high": {"threshold": 0.8, "label": "High Confidence", "badge": "bg-green-100 text-green-700"},
    "medium": {"threshold": 0.5, "label": "Medium Confidence", "badge": "bg-amber-100 text-amber-700"},
    "low": {"threshold": 0.0, "label": "Low Confidence", "badge": "bg-slate-100 text-slate-600"},
}


class CreatorPatternInsightsService:
    """
    Service for generating personalized pattern insights for creators.
    Analyzes proposals, projects, and ARRIS interactions to identify patterns.
    """
    
    def __init__(self, db, feature_gating=None):
        self.db = db
        self.feature_gating = feature_gating
    
    async def has_access(self, creator_id: str) -> Dict[str, Any]:
        """
        Check if creator has access to pattern insights (Pro+ only).
        Returns access status and upgrade info if needed.
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
            "upgrade_message": "Upgrade to Pro to unlock personalized pattern insights" if not has_access else None
        }
    
    async def get_creator_patterns(self, creator_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get personalized pattern cards for a creator.
        Analyzes their proposals, projects, and interactions.
        """
        # Check access
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "patterns": [],
                "access_denied": True,
                "upgrade_message": access["upgrade_message"],
                "tier": access["tier"]
            }
        
        # Gather creator data
        proposals = await self._get_creator_proposals(creator_id)
        projects = await self._get_creator_projects(creator_id)
        arris_usage = await self._get_arris_usage(creator_id)
        
        # Analyze patterns
        patterns = []
        
        # 1. Proposal Success Patterns
        proposal_patterns = await self._analyze_proposal_patterns(proposals)
        patterns.extend(proposal_patterns)
        
        # 2. Platform Performance Patterns
        platform_patterns = await self._analyze_platform_patterns(proposals, projects)
        patterns.extend(platform_patterns)
        
        # 3. Timing Patterns
        timing_patterns = await self._analyze_timing_patterns(proposals)
        patterns.extend(timing_patterns)
        
        # 4. ARRIS Engagement Patterns
        arris_patterns = await self._analyze_arris_patterns(arris_usage, proposals)
        patterns.extend(arris_patterns)
        
        # 5. Growth Patterns
        growth_patterns = await self._analyze_growth_patterns(proposals, projects)
        patterns.extend(growth_patterns)
        
        # Sort by confidence and recency
        patterns.sort(key=lambda p: (p.get("confidence", 0), p.get("discovered_at", "")), reverse=True)
        
        # Limit results
        patterns = patterns[:limit]
        
        # Calculate summary stats
        summary = {
            "total_patterns": len(patterns),
            "high_confidence": len([p for p in patterns if p.get("confidence", 0) >= 0.8]),
            "categories": list(set(p.get("category") for p in patterns)),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "patterns": patterns,
            "summary": summary,
            "tier": access["tier"],
            "access_denied": False
        }
    
    async def get_pattern_detail(self, creator_id: str, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific pattern."""
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return None
        
        # Check if pattern exists in stored patterns
        stored = await self.db.creator_patterns.find_one(
            {"creator_id": creator_id, "pattern_id": pattern_id},
            {"_id": 0}
        )
        
        if stored:
            return stored
        
        # Generate pattern on the fly if not stored
        patterns = await self.get_creator_patterns(creator_id)
        for p in patterns.get("patterns", []):
            if p.get("pattern_id") == pattern_id:
                return p
        
        return None
    
    async def get_pattern_recommendations(self, creator_id: str) -> Dict[str, Any]:
        """
        Get actionable recommendations based on pattern analysis.
        Returns prioritized actions the creator can take.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {
                "recommendations": [],
                "access_denied": True,
                "upgrade_message": access["upgrade_message"]
            }
        
        patterns = await self.get_creator_patterns(creator_id, limit=20)
        recommendations = []
        
        for pattern in patterns.get("patterns", []):
            if pattern.get("actionable"):
                recommendations.append({
                    "id": f"REC-{uuid.uuid4().hex[:8].upper()}",
                    "pattern_id": pattern.get("pattern_id"),
                    "title": pattern.get("recommendation_title", f"Based on: {pattern.get('title')}"),
                    "action": pattern.get("recommended_action", "Review this pattern for opportunities"),
                    "impact": pattern.get("potential_impact", "medium"),
                    "effort": pattern.get("effort_level", "low"),
                    "category": pattern.get("category"),
                    "priority": self._calculate_recommendation_priority(pattern)
                })
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.get("priority", 0), reverse=True)
        
        return {
            "recommendations": recommendations[:5],  # Top 5 recommendations
            "total_actionable": len(recommendations),
            "access_denied": False
        }
    
    async def get_pattern_trends(self, creator_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get pattern trends over time for a creator.
        Shows how patterns have evolved.
        """
        access = await self.has_access(creator_id)
        if not access["has_access"]:
            return {"trends": [], "access_denied": True}
        
        # Get historical pattern data
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        historical = await self.db.creator_pattern_history.find(
            {
                "creator_id": creator_id,
                "recorded_at": {"$gte": cutoff.isoformat()}
            },
            {"_id": 0}
        ).sort("recorded_at", 1).to_list(100)
        
        # Group by category and time
        trends = {}
        for entry in historical:
            category = entry.get("category", "unknown")
            if category not in trends:
                trends[category] = []
            trends[category].append({
                "date": entry.get("recorded_at"),
                "confidence": entry.get("confidence", 0),
                "count": entry.get("pattern_count", 1)
            })
        
        return {
            "trends": trends,
            "period_days": days,
            "access_denied": False
        }
    
    async def save_pattern_feedback(self, creator_id: str, pattern_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save creator feedback on a pattern (helpful/not helpful).
        Used to improve pattern detection.
        """
        feedback_doc = {
            "id": f"FB-{uuid.uuid4().hex[:8].upper()}",
            "creator_id": creator_id,
            "pattern_id": pattern_id,
            "is_helpful": feedback.get("is_helpful", True),
            "feedback_text": feedback.get("feedback_text", ""),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.pattern_feedback.insert_one(feedback_doc)
        
        return {"success": True, "feedback_id": feedback_doc["id"]}
    
    # ============== PRIVATE ANALYSIS METHODS ==============
    
    async def _get_creator_proposals(self, creator_id: str) -> List[Dict]:
        """Get all proposals for a creator."""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return proposals
    
    async def _get_creator_projects(self, creator_id: str) -> List[Dict]:
        """Get all projects for a creator."""
        projects = await self.db.projects.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        return projects
    
    async def _get_arris_usage(self, creator_id: str) -> List[Dict]:
        """Get ARRIS usage logs for a creator."""
        usage = await self.db.arris_usage.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(200)
        return usage
    
    async def _analyze_proposal_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Analyze patterns in proposal submissions and outcomes."""
        patterns = []
        
        if not proposals:
            return patterns
        
        # Count statuses
        statuses = {}
        for p in proposals:
            status = p.get("status", "draft")
            statuses[status] = statuses.get(status, 0) + 1
        
        total = len(proposals)
        approved = statuses.get("approved", 0) + statuses.get("completed", 0) + statuses.get("in_progress", 0)
        rejected = statuses.get("rejected", 0)
        
        # Success rate pattern
        if total >= 3:
            success_rate = approved / total
            if success_rate >= 0.7:
                patterns.append(self._create_pattern(
                    category="success",
                    title="High Proposal Success Rate",
                    description=f"Your proposals have a {success_rate*100:.0f}% approval rate. You understand what makes proposals successful.",
                    confidence=min(0.9, success_rate),
                    data={"success_rate": success_rate, "total": total, "approved": approved},
                    actionable=False
                ))
            elif success_rate < 0.3 and rejected >= 2:
                patterns.append(self._create_pattern(
                    category="risk",
                    title="Low Proposal Approval Rate",
                    description=f"Only {success_rate*100:.0f}% of your proposals are approved. Consider reviewing ARRIS recommendations more carefully.",
                    confidence=0.85,
                    data={"success_rate": success_rate, "rejected": rejected},
                    actionable=True,
                    recommended_action="Review rejected proposals and ARRIS feedback to identify improvement areas"
                ))
        
        # Priority analysis
        priorities = {}
        approved_by_priority = {}
        for p in proposals:
            priority = p.get("priority", "medium")
            priorities[priority] = priorities.get(priority, 0) + 1
            if p.get("status") in ["approved", "completed", "in_progress"]:
                approved_by_priority[priority] = approved_by_priority.get(priority, 0) + 1
        
        # Find best performing priority
        if priorities:
            best_priority = None
            best_rate = 0
            for priority, count in priorities.items():
                if count >= 2:
                    rate = approved_by_priority.get(priority, 0) / count
                    if rate > best_rate:
                        best_rate = rate
                        best_priority = priority
            
            if best_priority and best_rate >= 0.6:
                patterns.append(self._create_pattern(
                    category="success",
                    title=f"{best_priority.capitalize()} Priority Proposals Perform Best",
                    description=f"Your {best_priority} priority proposals have a {best_rate*100:.0f}% success rate.",
                    confidence=0.75,
                    data={"best_priority": best_priority, "success_rate": best_rate},
                    actionable=True,
                    recommended_action=f"Consider setting more proposals to {best_priority} priority"
                ))
        
        return patterns
    
    async def _analyze_platform_patterns(self, proposals: List[Dict], projects: List[Dict]) -> List[Dict]:
        """Analyze patterns related to platforms."""
        patterns = []
        
        # Collect platform data
        platform_counts = {}
        platform_success = {}
        
        for p in proposals:
            for platform in p.get("platforms", []):
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                if p.get("status") in ["approved", "completed", "in_progress"]:
                    platform_success[platform] = platform_success.get(platform, 0) + 1
        
        # Find dominant platform
        if platform_counts:
            dominant = max(platform_counts, key=platform_counts.get)
            if platform_counts[dominant] >= 3:
                success_rate = platform_success.get(dominant, 0) / platform_counts[dominant]
                patterns.append(self._create_pattern(
                    category="platform",
                    title=f"{dominant} is Your Primary Platform",
                    description=f"You focus heavily on {dominant} ({platform_counts[dominant]} proposals). Success rate: {success_rate*100:.0f}%",
                    confidence=0.85,
                    data={"platform": dominant, "count": platform_counts[dominant], "success_rate": success_rate},
                    actionable=True if success_rate < 0.5 else False,
                    recommended_action="Consider diversifying platforms or improving your approach" if success_rate < 0.5 else None
                ))
        
        # Multi-platform analysis
        multi_platform_proposals = [p for p in proposals if len(p.get("platforms", [])) > 2]
        if len(multi_platform_proposals) >= 2:
            multi_success = len([p for p in multi_platform_proposals if p.get("status") in ["approved", "completed"]])
            multi_rate = multi_success / len(multi_platform_proposals)
            
            single_platform = [p for p in proposals if len(p.get("platforms", [])) == 1]
            if single_platform:
                single_success = len([p for p in single_platform if p.get("status") in ["approved", "completed"]])
                single_rate = single_success / len(single_platform) if single_platform else 0
                
                if multi_rate > single_rate + 0.2:
                    patterns.append(self._create_pattern(
                        category="platform",
                        title="Multi-Platform Approach Works Better",
                        description=f"Proposals targeting 3+ platforms have {multi_rate*100:.0f}% success vs {single_rate*100:.0f}% for single-platform.",
                        confidence=0.7,
                        data={"multi_rate": multi_rate, "single_rate": single_rate},
                        actionable=True,
                        recommended_action="Consider expanding your proposals to target multiple platforms"
                    ))
        
        return patterns
    
    async def _analyze_timing_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Analyze timing-related patterns."""
        patterns = []
        
        if len(proposals) < 5:
            return patterns
        
        # Day of week analysis
        day_counts = {}
        day_success = {}
        
        for p in proposals:
            created = p.get("created_at", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    day = dt.strftime("%A")
                    day_counts[day] = day_counts.get(day, 0) + 1
                    if p.get("status") in ["approved", "completed", "in_progress"]:
                        day_success[day] = day_success.get(day, 0) + 1
                except:
                    pass
        
        # Find best day
        if day_counts:
            best_day = None
            best_rate = 0
            for day, count in day_counts.items():
                if count >= 2:
                    rate = day_success.get(day, 0) / count
                    if rate > best_rate:
                        best_rate = rate
                        best_day = day
            
            if best_day and best_rate >= 0.6:
                patterns.append(self._create_pattern(
                    category="timing",
                    title=f"{best_day}s Are Your Best Day",
                    description=f"Proposals submitted on {best_day}s have a {best_rate*100:.0f}% success rate.",
                    confidence=0.65,
                    data={"best_day": best_day, "success_rate": best_rate},
                    actionable=True,
                    recommended_action=f"Try to submit more proposals on {best_day}s"
                ))
        
        # Submission frequency pattern
        if len(proposals) >= 5:
            dates = []
            for p in proposals:
                try:
                    dt = datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00"))
                    dates.append(dt)
                except:
                    pass
            
            if len(dates) >= 5:
                dates.sort()
                gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_gap = sum(gaps) / len(gaps) if gaps else 0
                
                if avg_gap <= 7:
                    patterns.append(self._create_pattern(
                        category="timing",
                        title="Consistent Weekly Submissions",
                        description=f"You submit proposals every {avg_gap:.1f} days on average. Consistency builds momentum.",
                        confidence=0.7,
                        data={"avg_gap_days": avg_gap},
                        actionable=False
                    ))
                elif avg_gap >= 30:
                    patterns.append(self._create_pattern(
                        category="timing",
                        title="Infrequent Submissions",
                        description=f"Your proposals average {avg_gap:.0f} days apart. More frequent submissions may improve visibility.",
                        confidence=0.6,
                        data={"avg_gap_days": avg_gap},
                        actionable=True,
                        recommended_action="Consider submitting proposals more frequently to maintain momentum"
                    ))
        
        return patterns
    
    async def _analyze_arris_patterns(self, arris_usage: List[Dict], proposals: List[Dict]) -> List[Dict]:
        """Analyze patterns in ARRIS interactions."""
        patterns = []
        
        # ARRIS recommendation follow-through
        proposals_with_insights = [p for p in proposals if p.get("arris_insights")]
        
        if len(proposals_with_insights) >= 3:
            # Check if proposals with ARRIS insights perform better
            with_insights_success = len([p for p in proposals_with_insights if p.get("status") in ["approved", "completed"]])
            without_insights = [p for p in proposals if not p.get("arris_insights")]
            without_success = len([p for p in without_insights if p.get("status") in ["approved", "completed"]])
            
            if proposals_with_insights:
                with_rate = with_insights_success / len(proposals_with_insights)
                without_rate = without_success / len(without_insights) if without_insights else 0
                
                if with_rate > without_rate + 0.1:
                    patterns.append(self._create_pattern(
                        category="engagement",
                        title="ARRIS Insights Boost Success",
                        description=f"Proposals with ARRIS analysis have {with_rate*100:.0f}% success vs {without_rate*100:.0f}% without.",
                        confidence=0.8,
                        data={"with_insights_rate": with_rate, "without_rate": without_rate},
                        actionable=True,
                        recommended_action="Always request ARRIS analysis for new proposals"
                    ))
        
        # Check complexity handling
        complexities = {"low": [], "medium": [], "high": []}
        for p in proposals_with_insights:
            complexity = p.get("arris_insights", {}).get("estimated_complexity", "medium")
            if complexity in complexities:
                complexities[complexity].append(p)
        
        for complexity, props in complexities.items():
            if len(props) >= 2:
                success = len([p for p in props if p.get("status") in ["approved", "completed"]])
                rate = success / len(props)
                
                if complexity == "high" and rate >= 0.7:
                    patterns.append(self._create_pattern(
                        category="success",
                        title="You Excel at Complex Projects",
                        description=f"Your high-complexity proposals have a {rate*100:.0f}% success rate. You handle challenging projects well.",
                        confidence=0.75,
                        data={"complexity": complexity, "success_rate": rate},
                        actionable=False
                    ))
                elif complexity == "low" and rate < 0.5:
                    patterns.append(self._create_pattern(
                        category="risk",
                        title="Simple Projects Underperforming",
                        description=f"Low-complexity proposals only have {rate*100:.0f}% success. Consider adding more depth.",
                        confidence=0.7,
                        data={"complexity": complexity, "success_rate": rate},
                        actionable=True,
                        recommended_action="Add more detail and scope to simpler proposals"
                    ))
        
        return patterns
    
    async def _analyze_growth_patterns(self, proposals: List[Dict], projects: List[Dict]) -> List[Dict]:
        """Analyze growth and improvement patterns."""
        patterns = []
        
        if len(proposals) < 5:
            return patterns
        
        # Sort by date
        sorted_proposals = sorted(proposals, key=lambda p: p.get("created_at", ""))
        
        # Compare early vs recent performance
        mid_point = len(sorted_proposals) // 2
        early = sorted_proposals[:mid_point]
        recent = sorted_proposals[mid_point:]
        
        early_success = len([p for p in early if p.get("status") in ["approved", "completed"]])
        recent_success = len([p for p in recent if p.get("status") in ["approved", "completed"]])
        
        early_rate = early_success / len(early) if early else 0
        recent_rate = recent_success / len(recent) if recent else 0
        
        if recent_rate > early_rate + 0.15:
            patterns.append(self._create_pattern(
                category="growth",
                title="Your Success Rate is Improving",
                description=f"Recent proposals: {recent_rate*100:.0f}% success vs {early_rate*100:.0f}% earlier. You're getting better!",
                confidence=0.85,
                data={"early_rate": early_rate, "recent_rate": recent_rate, "improvement": recent_rate - early_rate},
                actionable=False
            ))
        elif early_rate > recent_rate + 0.15:
            patterns.append(self._create_pattern(
                category="risk",
                title="Recent Performance Declining",
                description=f"Recent proposals: {recent_rate*100:.0f}% success vs {early_rate*100:.0f}% earlier. Review what changed.",
                confidence=0.75,
                data={"early_rate": early_rate, "recent_rate": recent_rate, "decline": early_rate - recent_rate},
                actionable=True,
                recommended_action="Compare successful early proposals with recent ones to identify differences"
            ))
        
        # Check for momentum
        if len(recent) >= 3:
            recent_3 = recent[-3:]
            recent_3_success = len([p for p in recent_3 if p.get("status") in ["approved", "completed"]])
            if recent_3_success == 3:
                patterns.append(self._create_pattern(
                    category="growth",
                    title="You're on a Hot Streak!",
                    description="Your last 3 proposals were all successful. Keep up the momentum!",
                    confidence=0.9,
                    data={"streak": 3, "type": "success"},
                    actionable=False
                ))
        
        return patterns
    
    def _create_pattern(
        self,
        category: str,
        title: str,
        description: str,
        confidence: float,
        data: Dict[str, Any],
        actionable: bool = False,
        recommended_action: str = None
    ) -> Dict[str, Any]:
        """Create a standardized pattern object."""
        category_info = PATTERN_CATEGORIES.get(category, PATTERN_CATEGORIES["success"])
        
        # Determine confidence level
        confidence_level = "low"
        for level, info in CONFIDENCE_LEVELS.items():
            if confidence >= info["threshold"]:
                confidence_level = level
        
        return {
            "pattern_id": f"PAT-{uuid.uuid4().hex[:8].upper()}",
            "category": category,
            "category_info": category_info,
            "title": title,
            "description": description,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "confidence_label": CONFIDENCE_LEVELS[confidence_level]["label"],
            "data": data,
            "actionable": actionable,
            "recommended_action": recommended_action,
            "discovered_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_recommendation_priority(self, pattern: Dict) -> int:
        """Calculate priority score for a recommendation."""
        score = 0
        
        # Higher confidence = higher priority
        score += int(pattern.get("confidence", 0) * 50)
        
        # Risk patterns are higher priority
        if pattern.get("category") == "risk":
            score += 30
        elif pattern.get("category") == "growth":
            score += 20
        
        # Actionable patterns are higher
        if pattern.get("actionable"):
            score += 10
        
        return score
