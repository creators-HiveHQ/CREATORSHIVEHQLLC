"""
Creators Hive HQ - ARRIS AI Service
Pattern Engine & AI Insight Generation for Project Proposals
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============== ARRIS AI SERVICE ==============

class ArrisService:
    """ARRIS AI Service for generating insights"""
    
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        self.model = "gpt-4o"
        self.provider = "openai"
        
    async def generate_project_insights(
        self,
        proposal: Dict[str, Any],
        memory_palace_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights for a project proposal
        Uses Pattern Engine data from Memory Palace for context
        """
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Build context from proposal
            context = self._build_proposal_context(proposal, memory_palace_data)
            
            # System prompt for ARRIS
            system_message = """You are ARRIS, an AI assistant for Creators Hive HQ - a platform that helps content creators build successful businesses.

Your role is to analyze project proposals and provide strategic insights. You have access to the creator's profile and historical patterns.

When analyzing a proposal, provide:
1. A brief summary (2-3 sentences)
2. Key strengths of the proposal (2-4 points)
3. Potential risks or challenges (2-4 points)
4. Strategic recommendations (3-5 actionable points)
5. Estimated complexity (Low/Medium/High)
6. Success probability assessment (with reasoning)
7. Suggested milestones (3-5 key milestones)
8. Resource suggestions (tools, skills, or support needed)

Be encouraging but realistic. Focus on actionable insights that help the creator succeed.

Respond in JSON format with these exact keys:
{
  "summary": "...",
  "strengths": ["...", "..."],
  "risks": ["...", "..."],
  "recommendations": ["...", "..."],
  "estimated_complexity": "Low|Medium|High",
  "success_probability": "...",
  "suggested_milestones": ["...", "..."],
  "resource_suggestions": "..."
}"""

            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"arris-proposal-{proposal.get('id', 'unknown')}",
                system_message=system_message
            ).with_model(self.provider, self.model)
            
            # Create user message with proposal details
            user_message = UserMessage(text=context)
            
            # Get response
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            insights = self._parse_insights_response(response)
            insights["generated_at"] = datetime.now(timezone.utc).isoformat()
            insights["model_used"] = self.model
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating ARRIS insights: {str(e)}")
            return self._get_fallback_insights(proposal)
    
    def _build_proposal_context(
        self,
        proposal: Dict[str, Any],
        memory_palace_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build context string for the AI"""
        context_parts = [
            "## Project Proposal Analysis Request",
            "",
            f"**Project Title:** {proposal.get('title', 'Untitled')}",
            f"**Description:** {proposal.get('description', 'No description')}",
            f"**Goals:** {proposal.get('goals', 'Not specified')}",
            f"**Platforms:** {', '.join(proposal.get('platforms', [])) or 'Not specified'}",
            f"**Timeline:** {proposal.get('timeline', 'Not specified')}",
            f"**Estimated Hours:** {proposal.get('estimated_hours', 0)}",
            f"**Priority:** {proposal.get('priority', 'medium')}",
            "",
            f"**Creator's Response to 'What outcome do you want?':**",
            f"{proposal.get('arris_intake_question', 'No response provided')}",
        ]
        
        # Add creator context if available
        if proposal.get('creator_name'):
            context_parts.extend([
                "",
                "## Creator Profile",
                f"**Name:** {proposal.get('creator_name')}",
            ])
        
        # Add memory palace patterns if available
        if memory_palace_data:
            context_parts.extend([
                "",
                "## Historical Patterns (from Memory Palace)",
            ])
            
            if memory_palace_data.get('activity'):
                activity = memory_palace_data['activity']
                context_parts.extend([
                    f"- Previous projects: {activity.get('projects', 0)}",
                    f"- Tasks completed: {activity.get('tasks_completed', 0)}",
                    f"- ARRIS queries: {activity.get('arris_queries', 0)}",
                ])
            
            if memory_palace_data.get('financials'):
                fin = memory_palace_data['financials']
                context_parts.extend([
                    f"- Total revenue: ${fin.get('total_revenue', 0):,.2f}",
                    f"- Net profit: ${fin.get('net_profit', 0):,.2f}",
                ])
        
        context_parts.extend([
            "",
            "Please analyze this proposal and provide strategic insights in JSON format.",
        ])
        
        return "\n".join(context_parts)
    
    def _parse_insights_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response into structured insights"""
        try:
            # Try to extract JSON from response
            # Handle cases where response might have markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                # Extract JSON from code block
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
            
            insights = json.loads(clean_response)
            
            # Validate and ensure all expected keys exist
            return {
                "summary": insights.get("summary", ""),
                "strengths": insights.get("strengths", []),
                "risks": insights.get("risks", []),
                "recommendations": insights.get("recommendations", []),
                "estimated_complexity": insights.get("estimated_complexity", "Medium"),
                "success_probability": insights.get("success_probability", ""),
                "suggested_milestones": insights.get("suggested_milestones", []),
                "resource_suggestions": insights.get("resource_suggestions", ""),
                "related_patterns": insights.get("related_patterns", []),
            }
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, extracting text insights")
            return {
                "summary": response[:500] if response else "Unable to generate summary",
                "strengths": [],
                "risks": [],
                "recommendations": [],
                "estimated_complexity": "Medium",
                "success_probability": "Unable to assess",
                "suggested_milestones": [],
                "resource_suggestions": "",
                "related_patterns": [],
                "raw_response": response
            }
    
    def _get_fallback_insights(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback insights if AI fails"""
        platforms = proposal.get('platforms', [])
        timeline = proposal.get('timeline', '')
        
        return {
            "summary": f"Project '{proposal.get('title', 'Untitled')}' aims to achieve the creator's goals through {len(platforms)} platform(s).",
            "strengths": [
                "Clear project scope defined",
                "Creator has identified target platforms",
            ],
            "risks": [
                "Timeline may need adjustment based on complexity",
                "Resource availability should be confirmed",
            ],
            "recommendations": [
                "Break down the project into smaller milestones",
                "Set up tracking metrics from the start",
                "Schedule regular progress reviews",
            ],
            "estimated_complexity": "Medium",
            "success_probability": "Assessment requires more data",
            "suggested_milestones": [
                "Project kickoff and planning",
                "First deliverable completion",
                "Mid-project review",
                "Final delivery and review",
            ],
            "resource_suggestions": "Consider using project management tools and content scheduling platforms.",
            "related_patterns": [],
            "fallback": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

# Global instance
arris_service = ArrisService()
