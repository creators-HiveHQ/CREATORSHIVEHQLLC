"""
Creators Hive HQ - ARRIS AI Service
Pattern Engine & AI Insight Generation for Project Proposals
With Priority Queue Processing for Premium Users
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import json
import time
from collections import deque
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ============== PROCESSING PRIORITY ==============

class ProcessingPriority(str, Enum):
    """Processing priority levels for ARRIS queue"""
    STANDARD = "standard"  # Free, Starter, Pro
    FAST = "fast"         # Premium, Elite
    

class ProcessingStats:
    """Track processing statistics for monitoring"""
    
    def __init__(self):
        self.total_requests = 0
        self.standard_requests = 0
        self.fast_requests = 0
        self.total_processing_time = 0.0
        self.standard_processing_time = 0.0
        self.fast_processing_time = 0.0
        
    def record(self, priority: str, processing_time: float):
        """Record processing statistics"""
        self.total_requests += 1
        self.total_processing_time += processing_time
        
        if priority == ProcessingPriority.FAST:
            self.fast_requests += 1
            self.fast_processing_time += processing_time
        else:
            self.standard_requests += 1
            self.standard_processing_time += processing_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "total_requests": self.total_requests,
            "standard_requests": self.standard_requests,
            "fast_requests": self.fast_requests,
            "avg_processing_time": self.total_processing_time / max(1, self.total_requests),
            "avg_standard_time": self.standard_processing_time / max(1, self.standard_requests),
            "avg_fast_time": self.fast_processing_time / max(1, self.fast_requests),
        }


# ============== ARRIS PRIORITY QUEUE ==============

class ArrisPriorityQueue:
    """
    Priority queue for ARRIS processing requests.
    Premium/Elite users (FAST priority) get processed before Standard users.
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.fast_queue = deque()      # High priority queue
        self.standard_queue = deque()  # Standard priority queue
        self.processing = set()         # Currently processing request IDs
        self.max_concurrent = max_concurrent
        self.lock = asyncio.Lock()
        self.stats = ProcessingStats()
        
    async def enqueue(self, request_id: str, priority: str = ProcessingPriority.STANDARD):
        """Add request to appropriate queue based on priority"""
        async with self.lock:
            if priority == ProcessingPriority.FAST:
                self.fast_queue.append(request_id)
                logger.info(f"ARRIS Queue: Added {request_id} to FAST queue (position: {len(self.fast_queue)})")
            else:
                self.standard_queue.append(request_id)
                logger.info(f"ARRIS Queue: Added {request_id} to STANDARD queue (position: {len(self.standard_queue)})")
    
    async def get_queue_position(self, request_id: str, priority: str) -> int:
        """Get position in queue (0 = processing next)"""
        async with self.lock:
            if priority == ProcessingPriority.FAST:
                try:
                    return list(self.fast_queue).index(request_id)
                except ValueError:
                    return 0
            else:
                # Standard queue position includes fast queue length
                fast_count = len(self.fast_queue)
                try:
                    std_pos = list(self.standard_queue).index(request_id)
                    return fast_count + std_pos
                except ValueError:
                    return 0
    
    async def dequeue(self) -> Optional[str]:
        """Get next request to process (FAST queue has priority)"""
        async with self.lock:
            # Always process FAST queue first
            if self.fast_queue:
                return self.fast_queue.popleft()
            elif self.standard_queue:
                return self.standard_queue.popleft()
            return None
    
    async def mark_processing(self, request_id: str):
        """Mark request as currently processing"""
        async with self.lock:
            self.processing.add(request_id)
    
    async def mark_complete(self, request_id: str, priority: str, processing_time: float):
        """Mark request as complete and record stats"""
        async with self.lock:
            self.processing.discard(request_id)
            self.stats.record(priority, processing_time)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        return {
            "fast_queue_length": len(self.fast_queue),
            "standard_queue_length": len(self.standard_queue),
            "currently_processing": len(self.processing),
            "processing_stats": self.stats.get_stats()
        }


# ============== ARRIS AI SERVICE ==============

class ArrisService:
    """ARRIS AI Service for generating insights with priority processing"""
    
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        self.model = "gpt-4o"
        self.provider = "openai"
        self.queue = ArrisPriorityQueue()
        
    async def generate_project_insights(
        self,
        proposal: Dict[str, Any],
        memory_palace_data: Optional[Dict[str, Any]] = None,
        processing_speed: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights for a project proposal
        Uses Pattern Engine data from Memory Palace for context
        
        Args:
            proposal: The proposal to analyze
            memory_palace_data: Historical data for context
            processing_speed: 'standard' or 'fast' (Premium/Elite users)
        """
        request_id = f"ARRIS-{proposal.get('id', 'unknown')}-{int(time.time())}"
        priority = ProcessingPriority.FAST if processing_speed == "fast" else ProcessingPriority.STANDARD
        
        # Add to priority queue
        await self.queue.enqueue(request_id, priority)
        
        # Record start time
        start_time = time.time()
        
        try:
            # Mark as processing
            await self.queue.mark_processing(request_id)
            
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
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Mark as complete
            await self.queue.mark_complete(request_id, priority, processing_time)
            
            # Parse JSON response
            insights = self._parse_insights_response(response)
            insights["generated_at"] = datetime.now(timezone.utc).isoformat()
            insights["model_used"] = self.model
            insights["processing_speed"] = processing_speed
            insights["processing_time_seconds"] = round(processing_time, 2)
            insights["priority_processed"] = priority == ProcessingPriority.FAST
            
            logger.info(f"ARRIS: Generated insights for {request_id} in {processing_time:.2f}s (priority: {priority})")
            
            return insights
            
        except Exception as e:
            processing_time = time.time() - start_time
            await self.queue.mark_complete(request_id, priority, processing_time)
            logger.error(f"Error generating ARRIS insights: {str(e)}")
            return self._get_fallback_insights(proposal, processing_speed)
    
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
    
    def _get_fallback_insights(self, proposal: Dict[str, Any], processing_speed: str = "standard") -> Dict[str, Any]:
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
            "processing_speed": processing_speed,
            "processing_time_seconds": 0,
            "priority_processed": processing_speed == "fast",
        }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get ARRIS queue statistics for monitoring"""
        return self.queue.get_queue_stats()


# Global instance
arris_service = ArrisService()
