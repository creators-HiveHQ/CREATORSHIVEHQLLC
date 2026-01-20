"""
ARRIS Memory & Learning System
Advanced pattern recognition and adaptive learning for creator insights

This module implements:
1. Memory Palace - Stores and retrieves creator interaction history
2. Pattern Engine - Identifies success/failure patterns from proposals
3. Learning System - Improves recommendations based on outcomes
4. Context Builder - Builds rich context for AI interactions
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


# ============== MEMORY TYPES ==============

class MemoryType:
    """Types of memories stored in the Memory Palace"""
    INTERACTION = "interaction"         # ARRIS interactions
    PROPOSAL = "proposal"               # Proposal submissions
    OUTCOME = "outcome"                 # Proposal outcomes (approved/rejected)
    PATTERN = "pattern"                 # Identified patterns
    PREFERENCE = "preference"           # Creator preferences
    FEEDBACK = "feedback"               # Explicit feedback
    MILESTONE = "milestone"             # Achievement milestones


class PatternCategory:
    """Categories of patterns ARRIS can identify"""
    SUCCESS = "success"                 # What leads to approvals
    RISK = "risk"                       # What leads to rejections
    TIMING = "timing"                   # When creator is most active
    COMPLEXITY = "complexity"           # Preferred complexity levels
    PLATFORM = "platform"               # Platform preferences
    CONTENT = "content"                 # Content type preferences
    COLLABORATION = "collaboration"     # How creator works with ARRIS


# ============== ARRIS MEMORY SERVICE ==============

class ArrisMemoryService:
    """
    ARRIS Memory & Learning System
    
    Manages the "Memory Palace" - a persistent store of creator interactions,
    patterns, and learnings that helps ARRIS provide increasingly personalized
    and accurate insights over time.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    # ============== MEMORY PALACE ==============
    
    async def store_memory(
        self, 
        creator_id: str, 
        memory_type: str, 
        content: Dict[str, Any],
        importance: float = 0.5,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Store a new memory in the Memory Palace.
        
        Args:
            creator_id: The creator's ID
            memory_type: Type of memory (interaction, proposal, outcome, etc.)
            content: The actual memory content
            importance: How important this memory is (0.0-1.0)
            tags: Optional tags for categorization
        """
        memory = {
            "id": f"MEM-{uuid.uuid4().hex[:10]}",
            "creator_id": creator_id,
            "memory_type": memory_type,
            "content": content,
            "importance": min(1.0, max(0.0, importance)),
            "tags": tags or [],
            "recall_count": 0,
            "last_recalled": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None  # Important memories never expire
        }
        
        await self.db.arris_memories.insert_one(memory)
        logger.info(f"Stored memory {memory['id']} for creator {creator_id}")
        
        return {k: v for k, v in memory.items() if k != "_id"}
    
    async def recall_memories(
        self,
        creator_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 50,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recall memories from the Memory Palace.
        
        Args:
            creator_id: The creator's ID
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            min_importance: Minimum importance threshold
            limit: Maximum memories to recall
            include_expired: Include expired memories
        """
        query = {
            "creator_id": creator_id,
            "importance": {"$gte": min_importance}
        }
        
        if memory_type:
            query["memory_type"] = memory_type
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if not include_expired:
            query["$or"] = [
                {"expires_at": None},
                {"expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}}
            ]
        
        memories = await self.db.arris_memories.find(
            query, {"_id": 0}
        ).sort([
            ("importance", -1),
            ("created_at", -1)
        ]).limit(limit).to_list(limit)
        
        # Update recall counts
        memory_ids = [m["id"] for m in memories]
        if memory_ids:
            await self.db.arris_memories.update_many(
                {"id": {"$in": memory_ids}},
                {
                    "$inc": {"recall_count": 1},
                    "$set": {"last_recalled": datetime.now(timezone.utc).isoformat()}
                }
            )
        
        return memories
    
    async def get_memory_summary(self, creator_id: str) -> Dict[str, Any]:
        """Get a summary of all memories for a creator"""
        pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$group": {
                "_id": "$memory_type",
                "count": {"$sum": 1},
                "avg_importance": {"$avg": "$importance"},
                "total_recalls": {"$sum": "$recall_count"}
            }}
        ]
        
        type_stats = await self.db.arris_memories.aggregate(pipeline).to_list(20)
        total_memories = await self.db.arris_memories.count_documents({"creator_id": creator_id})
        
        return {
            "total_memories": total_memories,
            "by_type": {stat["_id"]: {
                "count": stat["count"],
                "avg_importance": round(stat["avg_importance"], 2),
                "total_recalls": stat["total_recalls"]
            } for stat in type_stats},
            "memory_health": self._calculate_memory_health(total_memories, type_stats)
        }
    
    def _calculate_memory_health(self, total: int, type_stats: List[Dict]) -> Dict[str, Any]:
        """Calculate the health of memory system for a creator"""
        if total == 0:
            return {"score": 0, "status": "new", "message": "No memories yet"}
        
        # Good memory system has diverse types and high importance
        type_count = len(type_stats)
        avg_importance = sum(s.get("avg_importance", 0) for s in type_stats) / max(1, type_count)
        
        score = min(100, (type_count * 15) + (total * 2) + (avg_importance * 30))
        
        if score >= 80:
            status = "excellent"
            message = "ARRIS has deep understanding of your patterns"
        elif score >= 50:
            status = "good"
            message = "ARRIS is learning your preferences"
        elif score >= 20:
            status = "developing"
            message = "ARRIS is building your profile"
        else:
            status = "new"
            message = "Submit more proposals to help ARRIS learn"
        
        return {
            "score": round(score),
            "status": status,
            "message": message
        }
    
    # ============== PATTERN ENGINE ==============
    
    async def analyze_patterns(self, creator_id: str) -> Dict[str, Any]:
        """
        Analyze patterns from creator's history.
        Identifies success patterns, risk factors, timing preferences, etc.
        """
        # Get all proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).to_list(500)
        
        if len(proposals) < 3:
            return {
                "status": "insufficient_data",
                "message": "Need at least 3 proposals to identify patterns",
                "proposals_count": len(proposals),
                "patterns": []
            }
        
        patterns = []
        
        # 1. Success Patterns
        success_patterns = await self._analyze_success_patterns(proposals)
        patterns.extend(success_patterns)
        
        # 2. Risk Patterns
        risk_patterns = await self._analyze_risk_patterns(proposals)
        patterns.extend(risk_patterns)
        
        # 3. Timing Patterns
        timing_patterns = self._analyze_timing_patterns(proposals)
        patterns.extend(timing_patterns)
        
        # 4. Complexity Patterns
        complexity_patterns = self._analyze_complexity_patterns(proposals)
        patterns.extend(complexity_patterns)
        
        # 5. Platform Patterns
        platform_patterns = self._analyze_platform_patterns(proposals)
        patterns.extend(platform_patterns)
        
        # Store patterns as memories
        for pattern in patterns:
            await self.store_memory(
                creator_id=creator_id,
                memory_type=MemoryType.PATTERN,
                content=pattern,
                importance=pattern.get("confidence", 0.5),
                tags=[pattern.get("category"), "pattern_analysis"]
            )
        
        return {
            "status": "analyzed",
            "proposals_analyzed": len(proposals),
            "patterns_identified": len(patterns),
            "patterns": patterns,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _analyze_success_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Identify what leads to successful proposals"""
        patterns = []
        
        successful = [p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]]
        unsuccessful = [p for p in proposals if p.get("status") in ["rejected"]]
        
        if len(successful) < 2:
            return patterns
        
        # Platform success analysis
        successful_platforms = defaultdict(int)
        for p in successful:
            for platform in p.get("platforms", []):
                successful_platforms[platform] += 1
        
        if successful_platforms:
            top_platform = max(successful_platforms.items(), key=lambda x: x[1])
            if top_platform[1] >= 2:
                patterns.append({
                    "category": PatternCategory.SUCCESS,
                    "type": "platform_strength",
                    "title": f"Strong on {top_platform[0]}",
                    "description": f"{top_platform[1]} successful proposals on {top_platform[0]}",
                    "platform": top_platform[0],
                    "count": top_platform[1],
                    "confidence": min(0.9, top_platform[1] / len(successful)),
                    "actionable": True,
                    "recommendation": f"Continue focusing on {top_platform[0]} content"
                })
        
        # Priority success analysis
        priority_success = defaultdict(lambda: {"success": 0, "total": 0})
        for p in proposals:
            priority = p.get("priority", "medium")
            priority_success[priority]["total"] += 1
            if p.get("status") in ["approved", "completed", "in_progress"]:
                priority_success[priority]["success"] += 1
        
        for priority, stats in priority_success.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                if rate >= 0.7:
                    patterns.append({
                        "category": PatternCategory.SUCCESS,
                        "type": "priority_correlation",
                        "title": f"High success with {priority} priority",
                        "description": f"{int(rate*100)}% success rate with {priority} priority proposals",
                        "priority": priority,
                        "success_rate": round(rate, 2),
                        "confidence": min(0.85, rate),
                        "actionable": True,
                        "recommendation": f"Your {priority} priority proposals perform well"
                    })
        
        return patterns
    
    async def _analyze_risk_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Identify what leads to rejected proposals"""
        patterns = []
        
        rejected = [p for p in proposals if p.get("status") == "rejected"]
        
        if len(rejected) < 2:
            return patterns
        
        # Complexity risk analysis
        complexity_rejections = defaultdict(int)
        for p in rejected:
            complexity = p.get("arris_insights", {}).get("estimated_complexity", "Unknown")
            complexity_rejections[complexity] += 1
        
        if complexity_rejections:
            risky_complexity = max(complexity_rejections.items(), key=lambda x: x[1])
            if risky_complexity[1] >= 2:
                patterns.append({
                    "category": PatternCategory.RISK,
                    "type": "complexity_risk",
                    "title": f"Challenges with {risky_complexity[0]} complexity",
                    "description": f"{risky_complexity[1]} rejections on {risky_complexity[0]} complexity projects",
                    "complexity": risky_complexity[0],
                    "rejection_count": risky_complexity[1],
                    "confidence": min(0.8, risky_complexity[1] / len(rejected)),
                    "actionable": True,
                    "recommendation": f"Consider breaking {risky_complexity[0]} complexity projects into smaller phases"
                })
        
        return patterns
    
    def _analyze_timing_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Analyze when creator is most active and successful"""
        patterns = []
        
        # Day of week analysis
        day_activity = defaultdict(lambda: {"total": 0, "successful": 0})
        
        for p in proposals:
            created = p.get("created_at", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    day_name = dt.strftime("%A")
                    day_activity[day_name]["total"] += 1
                    if p.get("status") in ["approved", "completed", "in_progress"]:
                        day_activity[day_name]["successful"] += 1
                except:
                    pass
        
        if day_activity:
            most_active_day = max(day_activity.items(), key=lambda x: x[1]["total"])
            if most_active_day[1]["total"] >= 2:
                success_rate = most_active_day[1]["successful"] / most_active_day[1]["total"]
                patterns.append({
                    "category": PatternCategory.TIMING,
                    "type": "peak_activity_day",
                    "title": f"Most active on {most_active_day[0]}s",
                    "description": f"{most_active_day[1]['total']} proposals submitted on {most_active_day[0]}s",
                    "day": most_active_day[0],
                    "activity_count": most_active_day[1]["total"],
                    "success_rate": round(success_rate, 2),
                    "confidence": 0.7,
                    "actionable": False,
                    "insight": f"You tend to be most creative on {most_active_day[0]}s"
                })
        
        return patterns
    
    def _analyze_complexity_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Analyze preferred complexity levels"""
        patterns = []
        
        complexity_counts = defaultdict(int)
        complexity_success = defaultdict(lambda: {"total": 0, "success": 0})
        
        for p in proposals:
            complexity = p.get("arris_insights", {}).get("estimated_complexity", "Medium")
            complexity_counts[complexity] += 1
            complexity_success[complexity]["total"] += 1
            if p.get("status") in ["approved", "completed", "in_progress"]:
                complexity_success[complexity]["success"] += 1
        
        if complexity_counts:
            preferred = max(complexity_counts.items(), key=lambda x: x[1])
            success_data = complexity_success[preferred[0]]
            success_rate = success_data["success"] / max(1, success_data["total"])
            
            patterns.append({
                "category": PatternCategory.COMPLEXITY,
                "type": "preferred_complexity",
                "title": f"Prefers {preferred[0]} complexity",
                "description": f"{preferred[1]} proposals at {preferred[0]} complexity ({int(success_rate*100)}% success)",
                "complexity": preferred[0],
                "count": preferred[1],
                "success_rate": round(success_rate, 2),
                "confidence": min(0.85, preferred[1] / len(proposals)),
                "actionable": True,
                "recommendation": f"You perform well at {preferred[0]} complexity - consider this your sweet spot"
            })
        
        return patterns
    
    def _analyze_platform_patterns(self, proposals: List[Dict]) -> List[Dict]:
        """Analyze platform preferences and performance"""
        patterns = []
        
        platform_stats = defaultdict(lambda: {"total": 0, "success": 0})
        
        for p in proposals:
            for platform in p.get("platforms", []):
                platform_stats[platform]["total"] += 1
                if p.get("status") in ["approved", "completed", "in_progress"]:
                    platform_stats[platform]["success"] += 1
        
        # Find platform with best success rate (min 2 proposals)
        best_platform = None
        best_rate = 0
        
        for platform, stats in platform_stats.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_platform = (platform, stats)
        
        if best_platform and best_rate >= 0.5:
            patterns.append({
                "category": PatternCategory.PLATFORM,
                "type": "best_platform",
                "title": f"Strongest on {best_platform[0]}",
                "description": f"{int(best_rate*100)}% success rate on {best_platform[0]} ({best_platform[1]['success']}/{best_platform[1]['total']})",
                "platform": best_platform[0],
                "success_rate": round(best_rate, 2),
                "proposals_count": best_platform[1]["total"],
                "confidence": min(0.9, best_rate),
                "actionable": True,
                "recommendation": f"Double down on {best_platform[0]} content"
            })
        
        return patterns
    
    # ============== LEARNING SYSTEM ==============
    
    async def record_outcome(
        self,
        creator_id: str,
        proposal_id: str,
        outcome: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record the outcome of a proposal to improve future predictions.
        
        Args:
            creator_id: The creator's ID
            proposal_id: The proposal ID
            outcome: The outcome (approved, rejected, completed, etc.)
            feedback: Optional feedback about the outcome
        """
        # Get the proposal
        proposal = await self.db.proposals.find_one(
            {"id": proposal_id, "user_id": creator_id},
            {"_id": 0}
        )
        
        if not proposal:
            return {"error": "Proposal not found"}
        
        # Get ARRIS's original prediction
        arris_insights = proposal.get("arris_insights", {})
        predicted_complexity = arris_insights.get("estimated_complexity", "Unknown")
        predicted_success = arris_insights.get("success_probability", "Unknown")
        
        # Determine if prediction was accurate
        was_successful = outcome in ["approved", "completed", "in_progress"]
        prediction_accurate = self._was_prediction_accurate(predicted_success, was_successful)
        
        # Store outcome memory
        outcome_memory = await self.store_memory(
            creator_id=creator_id,
            memory_type=MemoryType.OUTCOME,
            content={
                "proposal_id": proposal_id,
                "proposal_title": proposal.get("title"),
                "outcome": outcome,
                "predicted_complexity": predicted_complexity,
                "predicted_success": predicted_success,
                "prediction_accurate": prediction_accurate,
                "feedback": feedback,
                "platforms": proposal.get("platforms", []),
                "timeline": proposal.get("timeline"),
                "priority": proposal.get("priority")
            },
            importance=0.8 if not prediction_accurate else 0.5,  # Learn more from mistakes
            tags=["outcome", outcome, "learning"]
        )
        
        # Update learning metrics
        await self._update_learning_metrics(creator_id, prediction_accurate)
        
        return {
            "outcome_recorded": True,
            "memory_id": outcome_memory["id"],
            "prediction_was_accurate": prediction_accurate,
            "learning_updated": True
        }
    
    def _was_prediction_accurate(self, predicted_success: str, was_successful: bool) -> bool:
        """Check if ARRIS's prediction was accurate"""
        if not predicted_success or predicted_success == "Unknown":
            return True  # Can't judge if no prediction
        
        # Parse prediction (handle various formats)
        pred_lower = predicted_success.lower()
        predicted_positive = any(word in pred_lower for word in ["high", "good", "strong", "likely", "promising"])
        
        return predicted_positive == was_successful
    
    async def _update_learning_metrics(self, creator_id: str, accurate: bool):
        """Update learning metrics for a creator"""
        await self.db.arris_learning_metrics.update_one(
            {"creator_id": creator_id},
            {
                "$inc": {
                    "total_predictions": 1,
                    "accurate_predictions": 1 if accurate else 0
                },
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )
    
    async def get_learning_metrics(self, creator_id: str) -> Dict[str, Any]:
        """Get learning metrics for a creator"""
        metrics = await self.db.arris_learning_metrics.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not metrics:
            return {
                "total_predictions": 0,
                "accurate_predictions": 0,
                "accuracy_rate": 0,
                "learning_stage": "initializing"
            }
        
        total = metrics.get("total_predictions", 0)
        accurate = metrics.get("accurate_predictions", 0)
        accuracy = accurate / max(1, total)
        
        # Determine learning stage
        if total < 5:
            stage = "initializing"
        elif total < 15:
            stage = "learning"
        elif total < 30:
            stage = "developing"
        elif accuracy >= 0.8:
            stage = "expert"
        elif accuracy >= 0.6:
            stage = "proficient"
        else:
            stage = "calibrating"
        
        return {
            "total_predictions": total,
            "accurate_predictions": accurate,
            "accuracy_rate": round(accuracy * 100, 1),
            "learning_stage": stage,
            "last_updated": metrics.get("last_updated")
        }
    
    # ============== CONTEXT BUILDER ==============
    
    async def build_rich_context(self, creator_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build rich context for ARRIS AI interactions by combining:
        - Recent memories
        - Identified patterns
        - Historical performance
        - Learning metrics
        """
        # 1. Get relevant memories
        recent_memories = await self.recall_memories(
            creator_id=creator_id,
            min_importance=0.3,
            limit=10
        )
        
        # 2. Get patterns
        patterns = await self.recall_memories(
            creator_id=creator_id,
            memory_type=MemoryType.PATTERN,
            limit=5
        )
        
        # 3. Get learning metrics
        learning_metrics = await self.get_learning_metrics(creator_id)
        
        # 4. Get historical performance
        historical_stats = await self._get_historical_performance(creator_id)
        
        # 5. Build context
        context = {
            "creator_id": creator_id,
            "memory_context": {
                "recent_interactions": len([m for m in recent_memories if m.get("memory_type") == MemoryType.INTERACTION]),
                "outcomes_recorded": len([m for m in recent_memories if m.get("memory_type") == MemoryType.OUTCOME]),
                "key_memories": [
                    {
                        "type": m.get("memory_type"),
                        "summary": self._summarize_memory(m),
                        "importance": m.get("importance")
                    }
                    for m in recent_memories[:5]
                ]
            },
            "identified_patterns": [
                {
                    "category": p.get("content", {}).get("category"),
                    "title": p.get("content", {}).get("title"),
                    "recommendation": p.get("content", {}).get("recommendation"),
                    "confidence": p.get("content", {}).get("confidence")
                }
                for p in patterns
            ],
            "historical_performance": historical_stats,
            "learning_metrics": learning_metrics,
            "proposal_context": {
                "platforms": proposal.get("platforms", []),
                "priority": proposal.get("priority"),
                "timeline": proposal.get("timeline"),
                "similar_proposals": await self._find_similar_proposals(creator_id, proposal)
            },
            "built_at": datetime.now(timezone.utc).isoformat()
        }
        
        return context
    
    def _summarize_memory(self, memory: Dict[str, Any]) -> str:
        """Create a brief summary of a memory"""
        content = memory.get("content", {})
        memory_type = memory.get("memory_type")
        
        if memory_type == MemoryType.OUTCOME:
            return f"Proposal '{content.get('proposal_title', 'Unknown')}' was {content.get('outcome', 'unknown')}"
        elif memory_type == MemoryType.PATTERN:
            return content.get("title", "Pattern identified")
        elif memory_type == MemoryType.INTERACTION:
            return f"ARRIS interaction on {content.get('topic', 'general')}"
        else:
            return f"{memory_type} recorded"
    
    async def _get_historical_performance(self, creator_id: str) -> Dict[str, Any]:
        """Get historical performance statistics"""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "status": 1, "arris_insights": 1, "platforms": 1}
        ).to_list(100)
        
        if not proposals:
            return {"total": 0, "message": "No history yet"}
        
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "in_progress", "completed"]])
        completed = len([p for p in proposals if p.get("status") == "completed"])
        
        return {
            "total_proposals": total,
            "approval_rate": round(approved / total * 100, 1) if total > 0 else 0,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "most_used_platforms": self._get_top_platforms(proposals),
            "avg_complexity": self._get_avg_complexity(proposals)
        }
    
    def _get_top_platforms(self, proposals: List[Dict]) -> List[str]:
        """Get most frequently used platforms"""
        platform_counts = defaultdict(int)
        for p in proposals:
            for platform in p.get("platforms", []):
                platform_counts[platform] += 1
        
        sorted_platforms = sorted(platform_counts.items(), key=lambda x: -x[1])
        return [p[0] for p in sorted_platforms[:3]]
    
    def _get_avg_complexity(self, proposals: List[Dict]) -> str:
        """Get average complexity level"""
        complexity_map = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
        reverse_map = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}
        
        complexities = []
        for p in proposals:
            c = p.get("arris_insights", {}).get("estimated_complexity")
            if c in complexity_map:
                complexities.append(complexity_map[c])
        
        if not complexities:
            return "Unknown"
        
        avg = sum(complexities) / len(complexities)
        return reverse_map.get(round(avg), "Medium")
    
    async def _find_similar_proposals(self, creator_id: str, proposal: Dict[str, Any]) -> List[Dict]:
        """Find similar proposals from history"""
        platforms = proposal.get("platforms", [])
        priority = proposal.get("priority")
        
        # Find proposals with similar platforms
        query = {"user_id": creator_id}
        if platforms:
            query["platforms"] = {"$in": platforms}
        
        similar = await self.db.proposals.find(
            query,
            {"_id": 0, "id": 1, "title": 1, "status": 1, "platforms": 1}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        return [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "status": s.get("status"),
                "platforms": s.get("platforms")
            }
            for s in similar
        ]
    
    # ============== PERSONALIZATION ==============
    
    async def get_personalized_prompt_additions(self, creator_id: str) -> str:
        """
        Generate personalized additions to ARRIS prompts based on learnings.
        """
        # Get patterns
        patterns = await self.recall_memories(
            creator_id=creator_id,
            memory_type=MemoryType.PATTERN,
            min_importance=0.5,
            limit=5
        )
        
        # Get learning metrics
        metrics = await self.get_learning_metrics(creator_id)
        
        additions = []
        
        # Add pattern-based context
        for pattern in patterns:
            content = pattern.get("content", {})
            if content.get("category") == PatternCategory.SUCCESS:
                additions.append(f"Creator has shown strength in: {content.get('title', 'certain areas')}")
            elif content.get("category") == PatternCategory.RISK:
                additions.append(f"Previous challenge area: {content.get('title', 'some aspects')}")
            elif content.get("category") == PatternCategory.COMPLEXITY:
                additions.append(f"Comfort zone: {content.get('complexity', 'medium')} complexity projects")
        
        # Add learning context
        if metrics.get("accuracy_rate", 0) >= 70:
            additions.append("Previous predictions have been largely accurate for this creator.")
        elif metrics.get("total_predictions", 0) >= 10:
            additions.append("Adjust predictions based on this creator's unique patterns.")
        
        if not additions:
            return ""
        
        return "\n\n## Creator Context (Learned from History):\n" + "\n".join(f"- {a}" for a in additions)


# Create global instance placeholder (initialized with db in server.py)
arris_memory_service = None
