"""
ARRIS Proposal Recommendation Service - Phase 4 Module B (B2)
Automated AI-generated improvement suggestions for rejected proposals

This module implements:
1. Rejection Analysis - Analyzes why proposals might have been rejected
2. Improvement Recommendations - AI-generated specific suggestions for improvement
3. Pattern-Based Insights - Uses historical patterns to guide recommendations
4. Success Templates - Suggests proven proposal structures
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

logger = logging.getLogger(__name__)


class ProposalRecommendationService:
    """
    AI-powered proposal improvement recommendations service.
    
    Analyzes rejected proposals and generates actionable suggestions
    based on:
    - Common rejection patterns
    - Successful proposal characteristics
    - Creator's historical performance
    - Platform-specific best practices
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        
    async def generate_rejection_recommendations(
        self,
        proposal_id: str,
        rejection_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate improvement recommendations for a rejected proposal.
        
        Args:
            proposal_id: The rejected proposal's ID
            rejection_reason: Optional admin-provided rejection reason
            
        Returns:
            Dict with recommendations and analysis
        """
        # Get the proposal
        proposal = await self.db.proposals.find_one(
            {"id": proposal_id},
            {"_id": 0}
        )
        
        if not proposal:
            return {
                "success": False,
                "error": "Proposal not found",
                "proposal_id": proposal_id
            }
        
        creator_id = proposal.get("user_id")
        
        # Get creator's historical data
        creator_history = await self._get_creator_history(creator_id)
        
        # Get successful proposals for comparison
        success_patterns = await self._get_success_patterns(proposal.get("platforms", []))
        
        # Generate AI recommendations
        recommendations = await self._generate_ai_recommendations(
            proposal=proposal,
            rejection_reason=rejection_reason,
            creator_history=creator_history,
            success_patterns=success_patterns
        )
        
        # Store recommendations
        recommendation_doc = {
            "id": f"REC-{proposal_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "proposal_id": proposal_id,
            "creator_id": creator_id,
            "rejection_reason": rejection_reason,
            "recommendations": recommendations,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.proposal_recommendations.insert_one(recommendation_doc)
        
        # Update proposal with recommendations
        await self.db.proposals.update_one(
            {"id": proposal_id},
            {"$set": {
                "improvement_recommendations": recommendations,
                "recommendations_generated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Generated recommendations for rejected proposal: {proposal_id}")
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "recommendations": recommendations,
            "recommendation_id": recommendation_doc["id"]
        }
    
    async def _get_creator_history(self, creator_id: str) -> Dict[str, Any]:
        """Get creator's historical proposal data"""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "id": 1, "title": 1, "status": 1, "platforms": 1, "priority": 1, "created_at": 1}
        ).to_list(100)
        
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        rejected = len([p for p in proposals if p.get("status") == "rejected"])
        
        # Find successful patterns
        successful_platforms = {}
        for p in proposals:
            if p.get("status") in ["approved", "completed", "in_progress"]:
                for platform in p.get("platforms", []):
                    successful_platforms[platform] = successful_platforms.get(platform, 0) + 1
        
        return {
            "total_proposals": total,
            "approved_proposals": approved,
            "rejected_proposals": rejected,
            "approval_rate": round((approved / total * 100), 1) if total > 0 else 0,
            "successful_platforms": successful_platforms,
            "recent_proposals": proposals[:5]
        }
    
    async def _get_success_patterns(self, platforms: List[str]) -> Dict[str, Any]:
        """Get patterns from successful proposals on similar platforms"""
        query = {"status": {"$in": ["approved", "completed", "in_progress"]}}
        if platforms:
            query["platforms"] = {"$in": platforms}
        
        successful_proposals = await self.db.proposals.find(
            query,
            {"_id": 0, "title": 1, "description": 1, "platforms": 1, "priority": 1, "timeline": 1, "estimated_hours": 1}
        ).limit(20).to_list(20)
        
        # Analyze patterns
        patterns = {
            "avg_estimated_hours": 0,
            "common_priorities": {},
            "common_timelines": {},
            "sample_titles": [],
            "total_analyzed": len(successful_proposals)
        }
        
        if successful_proposals:
            hours_sum = sum(p.get("estimated_hours", 0) for p in successful_proposals)
            patterns["avg_estimated_hours"] = round(hours_sum / len(successful_proposals), 1)
            
            for p in successful_proposals:
                priority = p.get("priority", "medium")
                patterns["common_priorities"][priority] = patterns["common_priorities"].get(priority, 0) + 1
                
                timeline = p.get("timeline", "")
                if timeline:
                    patterns["common_timelines"][timeline] = patterns["common_timelines"].get(timeline, 0) + 1
            
            patterns["sample_titles"] = [p.get("title", "")[:50] for p in successful_proposals[:5]]
        
        return patterns
    
    async def _generate_ai_recommendations(
        self,
        proposal: Dict[str, Any],
        rejection_reason: Optional[str],
        creator_history: Dict[str, Any],
        success_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered recommendations"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            system_message = """You are ARRIS, an AI assistant for Creators Hive HQ that helps creators improve their project proposals.

A creator's proposal was rejected. Your job is to:
1. Analyze what might have caused the rejection
2. Provide specific, actionable improvement suggestions
3. Reference successful patterns when relevant
4. Be encouraging but direct

Respond in JSON format with these exact keys:
{
  "analysis": {
    "likely_issues": ["Issue 1", "Issue 2"],
    "severity": "minor|moderate|significant",
    "improvement_potential": "low|medium|high"
  },
  "recommendations": [
    {
      "category": "title|description|goals|timeline|platforms|priority",
      "issue": "What's wrong",
      "suggestion": "How to fix it",
      "example": "Optional example of improvement"
    }
  ],
  "quick_wins": ["Easy improvement 1", "Easy improvement 2"],
  "revised_approach": "A brief paragraph describing how to resubmit successfully",
  "success_tips": ["Tip based on successful proposals"],
  "encouragement": "A brief encouraging message"
}"""

            # Build context
            context_parts = [
                "## Rejected Proposal Analysis",
                "",
                f"**Title:** {proposal.get('title', 'No title')}",
                f"**Description:** {proposal.get('description', 'No description')}",
                f"**Goals:** {proposal.get('goals', 'Not specified')}",
                f"**Platforms:** {', '.join(proposal.get('platforms', [])) or 'Not specified'}",
                f"**Timeline:** {proposal.get('timeline', 'Not specified')}",
                f"**Priority:** {proposal.get('priority', 'medium')}",
                f"**Estimated Hours:** {proposal.get('estimated_hours', 0)}",
                "",
            ]
            
            if rejection_reason:
                context_parts.extend([
                    "## Admin's Rejection Reason",
                    rejection_reason,
                    ""
                ])
            
            context_parts.extend([
                "## Creator's History",
                f"- Total proposals: {creator_history.get('total_proposals', 0)}",
                f"- Approval rate: {creator_history.get('approval_rate', 0)}%",
                f"- Successful platforms: {creator_history.get('successful_platforms', {})}",
                "",
                "## Successful Proposal Patterns",
                f"- Average estimated hours: {success_patterns.get('avg_estimated_hours', 0)}",
                f"- Common priorities: {success_patterns.get('common_priorities', {})}",
                "",
                "Please analyze this rejection and provide improvement recommendations in JSON format."
            ])
            
            context = "\n".join(context_parts)
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"arris-recommendation-{proposal.get('id', 'unknown')}",
                system_message=system_message
            ).with_model("openai", "gpt-4o")
            
            # Get response
            response = await chat.send_message(UserMessage(text=context))
            
            # Parse response
            recommendations = self._parse_recommendations_response(response)
            recommendations["generated_at"] = datetime.now(timezone.utc).isoformat()
            recommendations["model_used"] = "gpt-4o"
            
            return recommendations
            
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {str(e)}")
            return self._get_fallback_recommendations(proposal, rejection_reason, success_patterns)
    
    def _parse_recommendations_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured recommendations"""
        try:
            # Clean response
            clean_response = response.strip()
            if clean_response.startswith("```"):
                lines = clean_response.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```json"):
                        in_json = True
                        continue
                    elif line.startswith("```"):
                        in_json = False
                        continue
                    if in_json:
                        json_lines.append(line)
                clean_response = "\n".join(json_lines)
            
            recommendations = json.loads(clean_response)
            
            return {
                "analysis": recommendations.get("analysis", {}),
                "recommendations": recommendations.get("recommendations", []),
                "quick_wins": recommendations.get("quick_wins", []),
                "revised_approach": recommendations.get("revised_approach", ""),
                "success_tips": recommendations.get("success_tips", []),
                "encouragement": recommendations.get("encouragement", "")
            }
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON recommendations")
            return {
                "analysis": {"raw_response": response[:500]},
                "recommendations": [],
                "quick_wins": [],
                "revised_approach": response[:300] if response else "",
                "success_tips": [],
                "encouragement": "Keep improving - every rejection is a learning opportunity!"
            }
    
    def _get_fallback_recommendations(
        self,
        proposal: Dict[str, Any],
        rejection_reason: Optional[str],
        success_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback recommendations if AI fails"""
        recommendations = []
        quick_wins = []
        
        # Check title length
        title = proposal.get("title", "")
        if len(title) < 10:
            recommendations.append({
                "category": "title",
                "issue": "Title is too short",
                "suggestion": "Use a clear, descriptive title (10-50 characters)",
                "example": "e.g., 'YouTube Channel Growth Strategy Q1 2026'"
            })
            quick_wins.append("Expand your title to be more descriptive")
        
        # Check description
        description = proposal.get("description", "")
        if len(description) < 50:
            recommendations.append({
                "category": "description",
                "issue": "Description lacks detail",
                "suggestion": "Provide a comprehensive description (at least 100 characters)",
                "example": "Include what, why, how, and expected outcomes"
            })
            quick_wins.append("Add more detail to your description")
        
        # Check goals
        goals = proposal.get("goals", "")
        if not goals or len(goals) < 20:
            recommendations.append({
                "category": "goals",
                "issue": "Goals not clearly defined",
                "suggestion": "Specify measurable, time-bound goals",
                "example": "e.g., 'Increase subscriber count by 25% in 3 months'"
            })
        
        # Check estimated hours
        estimated_hours = proposal.get("estimated_hours", 0)
        avg_hours = success_patterns.get("avg_estimated_hours", 20)
        if estimated_hours < 5:
            recommendations.append({
                "category": "timeline",
                "issue": "Estimated hours seem too low",
                "suggestion": f"Consider if {estimated_hours} hours is realistic. Similar successful projects average {avg_hours} hours.",
                "example": None
            })
        
        return {
            "analysis": {
                "likely_issues": ["Insufficient detail", "Unclear goals"],
                "severity": "moderate",
                "improvement_potential": "high"
            },
            "recommendations": recommendations,
            "quick_wins": quick_wins or ["Review successful proposals for inspiration", "Add specific metrics to your goals"],
            "revised_approach": "Take time to thoroughly describe your project, including specific goals, timeline, and expected outcomes. Reference successful patterns from similar projects.",
            "success_tips": [
                "Successful proposals typically have detailed descriptions",
                "Clear, measurable goals increase approval chances",
                "Realistic timelines show planning maturity"
            ],
            "encouragement": "Don't be discouraged! Use this feedback to strengthen your proposal and resubmit.",
            "fallback": True,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ============== RECOMMENDATION RETRIEVAL ==============
    
    async def get_recommendations_for_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get existing recommendations for a proposal"""
        proposal = await self.db.proposals.find_one(
            {"id": proposal_id},
            {"_id": 0, "improvement_recommendations": 1, "recommendations_generated_at": 1}
        )
        
        if proposal and proposal.get("improvement_recommendations"):
            return {
                "proposal_id": proposal_id,
                "recommendations": proposal["improvement_recommendations"],
                "generated_at": proposal.get("recommendations_generated_at")
            }
        
        return None
    
    async def get_creator_recommendation_history(
        self, 
        creator_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendation history for a creator"""
        recommendations = await self.db.proposal_recommendations.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(limit)
        
        return recommendations
    
    async def get_common_rejection_reasons(self) -> List[Dict[str, Any]]:
        """Analyze common rejection patterns across all proposals"""
        # Get all rejected proposals with recommendations
        rejected = await self.db.proposals.find(
            {"status": "rejected", "improvement_recommendations": {"$exists": True}},
            {"_id": 0, "improvement_recommendations": 1}
        ).to_list(1000)
        
        # Aggregate issues
        issue_counts = {}
        for p in rejected:
            recs = p.get("improvement_recommendations", {})
            for rec in recs.get("recommendations", []):
                category = rec.get("category", "other")
                issue_counts[category] = issue_counts.get(category, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: -x[1])
        
        return [
            {"category": category, "count": count, "percentage": round(count / len(rejected) * 100, 1) if rejected else 0}
            for category, count in sorted_issues[:10]
        ]


# Global instance (will be initialized in server startup)
proposal_recommendation_service = None
