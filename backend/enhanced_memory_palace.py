"""
ARRIS Enhanced Memory Palace - Phase 4 Module C
Memory Consolidation and Cross-Creator Insights

This module implements:
1. Memory Consolidation (C1) - Background job to merge/summarize old memories
2. Cross-Creator Insights (C2) - Anonymous pattern sharing between similar creators
3. Memory Health Management - Storage optimization and retrieval speed improvement
4. Similarity Engine - Find creators with similar profiles for insights
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


class ConsolidationStrategy:
    """Strategies for memory consolidation"""
    MERGE_SIMILAR = "merge_similar"       # Merge memories with similar content
    SUMMARIZE_OLD = "summarize_old"       # Summarize old detailed memories
    ARCHIVE_LOW_VALUE = "archive_low"     # Archive low-importance memories
    COMPRESS_PATTERNS = "compress_patterns"  # Compress pattern memories


class InsightType:
    """Types of cross-creator insights"""
    SUCCESS_PATTERN = "success_pattern"     # What successful creators do
    COMMON_MISTAKE = "common_mistake"       # What to avoid
    TIMING_INSIGHT = "timing_insight"       # Best times/frequencies
    PLATFORM_TREND = "platform_trend"       # Platform-specific insights
    NICHE_BENCHMARK = "niche_benchmark"     # Benchmarks for specific niches


class EnhancedMemoryPalace:
    """
    Enhanced Memory Palace with Consolidation and Cross-Creator Insights
    
    Features:
    - Memory consolidation to reduce storage and improve retrieval
    - Cross-creator anonymous insights for "Creators like you" recommendations
    - Memory health scoring and optimization suggestions
    - Similarity-based creator clustering for insights
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.consolidation_age_days = 30      # Consolidate memories older than this
        self.archive_age_days = 90            # Archive memories older than this
        self.min_similarity_score = 0.6       # Minimum similarity for cross-creator insights
        self.max_consolidated_size = 1000     # Max content length after consolidation
    
    # ============== MEMORY CONSOLIDATION (C1) ==============
    
    async def run_consolidation(self, creator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run memory consolidation for a creator or all creators.
        
        Consolidation strategies:
        1. Merge similar memories into consolidated summaries
        2. Summarize old detailed memories
        3. Archive low-value memories
        4. Compress repetitive pattern data
        """
        start_time = datetime.now(timezone.utc)
        results = {
            "creators_processed": 0,
            "memories_before": 0,
            "memories_after": 0,
            "memories_consolidated": 0,
            "memories_archived": 0,
            "storage_saved_estimate": 0,
            "consolidation_log": []
        }
        
        # Get creators to process
        if creator_id:
            creators = [{"id": creator_id}]
        else:
            creators = await self.db.creators.find(
                {"status": "active"},
                {"_id": 0, "id": 1}
            ).to_list(10000)
        
        for creator in creators:
            cid = creator["id"]
            creator_results = await self._consolidate_creator_memories(cid)
            
            results["creators_processed"] += 1
            results["memories_before"] += creator_results["before"]
            results["memories_after"] += creator_results["after"]
            results["memories_consolidated"] += creator_results["consolidated"]
            results["memories_archived"] += creator_results["archived"]
            results["consolidation_log"].append({
                "creator_id": cid,
                **creator_results
            })
        
        # Estimate storage saved (rough estimate based on consolidation)
        results["storage_saved_estimate"] = results["memories_consolidated"] * 500  # ~500 bytes per memory
        
        # Log consolidation run
        consolidation_record = {
            "id": f"CONSOL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "run_at": start_time.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
            "results": results
        }
        await self.db.memory_consolidation_log.insert_one(consolidation_record)
        
        logger.info(f"Memory consolidation complete: {results['memories_consolidated']} memories consolidated")
        
        return results
    
    async def _consolidate_creator_memories(self, creator_id: str) -> Dict[str, Any]:
        """Consolidate memories for a single creator"""
        results = {
            "before": 0,
            "after": 0,
            "consolidated": 0,
            "archived": 0,
            "strategies_applied": []
        }
        
        # Count current memories
        results["before"] = await self.db.arris_memories.count_documents({"creator_id": creator_id})
        
        # Strategy 1: Merge similar interaction memories
        merged = await self._merge_similar_memories(creator_id)
        results["consolidated"] += merged
        if merged > 0:
            results["strategies_applied"].append(ConsolidationStrategy.MERGE_SIMILAR)
        
        # Strategy 2: Summarize old detailed memories
        summarized = await self._summarize_old_memories(creator_id)
        results["consolidated"] += summarized
        if summarized > 0:
            results["strategies_applied"].append(ConsolidationStrategy.SUMMARIZE_OLD)
        
        # Strategy 3: Archive low-importance old memories
        archived = await self._archive_low_value_memories(creator_id)
        results["archived"] = archived
        if archived > 0:
            results["strategies_applied"].append(ConsolidationStrategy.ARCHIVE_LOW_VALUE)
        
        # Strategy 4: Compress pattern memories
        compressed = await self._compress_pattern_memories(creator_id)
        results["consolidated"] += compressed
        if compressed > 0:
            results["strategies_applied"].append(ConsolidationStrategy.COMPRESS_PATTERNS)
        
        # Count after
        results["after"] = await self.db.arris_memories.count_documents({"creator_id": creator_id})
        
        return results
    
    async def _merge_similar_memories(self, creator_id: str) -> int:
        """Merge similar memories into consolidated entries"""
        merged_count = 0
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.consolidation_age_days)).isoformat()
        
        # Find old interaction memories
        old_interactions = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": "interaction",
            "created_at": {"$lt": cutoff_date},
            "consolidated": {"$ne": True}
        }).to_list(500)
        
        if len(old_interactions) < 3:
            return 0
        
        # Group by month
        monthly_groups = defaultdict(list)
        for mem in old_interactions:
            created = mem.get("created_at", "")[:7]  # YYYY-MM
            monthly_groups[created].append(mem)
        
        # Merge each month's memories
        for month, memories in monthly_groups.items():
            if len(memories) < 2:
                continue
            
            # Create consolidated memory
            consolidated = {
                "id": f"MEM-CONSOL-{month}-{creator_id[:8]}",
                "creator_id": creator_id,
                "memory_type": "interaction_summary",
                "content": {
                    "period": month,
                    "interaction_count": len(memories),
                    "topics": list(set(m.get("content", {}).get("topic", "general") for m in memories)),
                    "summary": f"Consolidated {len(memories)} interactions from {month}",
                    "avg_importance": sum(m.get("importance", 0.5) for m in memories) / len(memories),
                    "original_ids": [m["id"] for m in memories]
                },
                "importance": max(m.get("importance", 0.5) for m in memories),
                "tags": ["consolidated", "monthly_summary"],
                "consolidated": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_count": len(memories)
            }
            
            # Insert consolidated and remove originals
            await self.db.arris_memories.insert_one(consolidated)
            await self.db.arris_memories.delete_many({
                "id": {"$in": [m["id"] for m in memories]}
            })
            
            merged_count += len(memories) - 1  # Net reduction
        
        return merged_count
    
    async def _summarize_old_memories(self, creator_id: str) -> int:
        """Summarize old detailed memories into shorter versions"""
        summarized_count = 0
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.consolidation_age_days * 2)).isoformat()
        
        # Find old proposal/outcome memories with large content
        old_memories = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": {"$in": ["proposal", "outcome"]},
            "created_at": {"$lt": cutoff_date},
            "summarized": {"$ne": True}
        }).to_list(200)
        
        for mem in old_memories:
            content = mem.get("content", {})
            content_str = json.dumps(content)
            
            # Only summarize if content is large
            if len(content_str) > self.max_consolidated_size:
                # Create summary
                summary_content = {
                    "type": mem.get("memory_type"),
                    "summary": self._create_content_summary(content),
                    "original_size": len(content_str),
                    "key_points": self._extract_key_points(content)
                }
                
                # Update memory with summary
                await self.db.arris_memories.update_one(
                    {"id": mem["id"]},
                    {"$set": {
                        "content": summary_content,
                        "summarized": True,
                        "summarized_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                summarized_count += 1
        
        return summarized_count
    
    async def _archive_low_value_memories(self, creator_id: str) -> int:
        """Archive low-importance old memories"""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=self.archive_age_days)).isoformat()
        
        # Find old, low-importance, never-recalled memories
        query = {
            "creator_id": creator_id,
            "created_at": {"$lt": cutoff_date},
            "importance": {"$lt": 0.3},
            "recall_count": {"$lt": 2},
            "archived": {"$ne": True}
        }
        
        memories_to_archive = await self.db.arris_memories.find(query).to_list(500)
        
        if not memories_to_archive:
            return 0
        
        # Move to archive collection
        for mem in memories_to_archive:
            mem["archived_at"] = datetime.now(timezone.utc).isoformat()
            mem["archived"] = True
            await self.db.arris_memories_archive.insert_one(mem)
        
        # Remove from main collection
        archived_ids = [m["id"] for m in memories_to_archive]
        await self.db.arris_memories.delete_many({"id": {"$in": archived_ids}})
        
        return len(memories_to_archive)
    
    async def _compress_pattern_memories(self, creator_id: str) -> int:
        """Compress repetitive pattern memories"""
        compressed_count = 0
        
        # Find pattern memories
        patterns = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": "pattern",
            "compressed": {"$ne": True}
        }).to_list(100)
        
        # Group by pattern category
        by_category = defaultdict(list)
        for p in patterns:
            category = p.get("content", {}).get("category", "other")
            by_category[category].append(p)
        
        # Compress each category into single summary
        for category, cat_patterns in by_category.items():
            if len(cat_patterns) < 3:
                continue
            
            # Create compressed pattern summary
            compressed = {
                "id": f"MEM-PATTERN-{category}-{creator_id[:8]}",
                "creator_id": creator_id,
                "memory_type": "pattern_summary",
                "content": {
                    "category": category,
                    "pattern_count": len(cat_patterns),
                    "patterns": [
                        {
                            "description": p.get("content", {}).get("description", ""),
                            "confidence": p.get("content", {}).get("confidence", 0.5)
                        }
                        for p in sorted(cat_patterns, key=lambda x: -x.get("content", {}).get("confidence", 0))[:5]
                    ],
                    "avg_confidence": sum(p.get("content", {}).get("confidence", 0.5) for p in cat_patterns) / len(cat_patterns)
                },
                "importance": 0.7,
                "tags": ["compressed", "pattern_summary", category],
                "compressed": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.arris_memories.insert_one(compressed)
            
            # Mark originals as compressed (keep for reference but exclude from queries)
            await self.db.arris_memories.update_many(
                {"id": {"$in": [p["id"] for p in cat_patterns]}},
                {"$set": {"superseded": True}}
            )
            
            compressed_count += len(cat_patterns) - 1
        
        return compressed_count
    
    def _create_content_summary(self, content: Dict) -> str:
        """Create a text summary of memory content"""
        parts = []
        
        if "title" in content:
            parts.append(f"Title: {content['title']}")
        if "status" in content:
            parts.append(f"Status: {content['status']}")
        if "outcome" in content:
            parts.append(f"Outcome: {content['outcome']}")
        if "platforms" in content:
            parts.append(f"Platforms: {', '.join(content['platforms'][:3])}")
        
        return "; ".join(parts) or "Archived memory"
    
    def _extract_key_points(self, content: Dict) -> List[str]:
        """Extract key points from memory content"""
        points = []
        
        if content.get("status"):
            points.append(f"Status was {content['status']}")
        if content.get("approval_rate"):
            points.append(f"Approval rate: {content['approval_rate']}%")
        if content.get("platforms"):
            points.append(f"Platforms: {len(content['platforms'])}")
        
        return points[:3]
    
    # ============== CROSS-CREATOR INSIGHTS (C2) ==============
    
    async def get_cross_creator_insights(
        self, 
        creator_id: str,
        insight_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get anonymous insights from similar creators.
        
        Returns "Creators like you typically..." recommendations based on
        anonymized patterns from similar creators.
        """
        # Get creator profile
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0, "platforms": 1, "niche": 1}
        )
        
        if not creator:
            return {"insights": [], "error": "Creator not found"}
        
        # Get creator's metrics
        creator_metrics = await self._get_creator_metrics(creator_id)
        
        # Find similar creators
        similar_creators = await self._find_similar_creators(creator_id, creator, creator_metrics)
        
        if not similar_creators:
            return {
                "insights": [],
                "similar_creators_found": 0,
                "message": "Not enough similar creators found for insights"
            }
        
        # Generate insights from similar creators
        insights = []
        
        # Success Pattern Insights
        if not insight_types or InsightType.SUCCESS_PATTERN in insight_types:
            success_insights = await self._generate_success_insights(similar_creators, creator_metrics)
            insights.extend(success_insights)
        
        # Common Mistake Insights
        if not insight_types or InsightType.COMMON_MISTAKE in insight_types:
            mistake_insights = await self._generate_mistake_insights(similar_creators, creator_metrics)
            insights.extend(mistake_insights)
        
        # Timing Insights
        if not insight_types or InsightType.TIMING_INSIGHT in insight_types:
            timing_insights = await self._generate_timing_insights(similar_creators)
            insights.extend(timing_insights)
        
        # Platform Trend Insights
        if not insight_types or InsightType.PLATFORM_TREND in insight_types:
            platform_insights = await self._generate_platform_insights(similar_creators, creator.get("platforms", []))
            insights.extend(platform_insights)
        
        # Niche Benchmark Insights
        if not insight_types or InsightType.NICHE_BENCHMARK in insight_types:
            benchmark_insights = await self._generate_benchmark_insights(similar_creators, creator_metrics)
            insights.extend(benchmark_insights)
        
        # Sort by relevance and limit
        insights.sort(key=lambda x: -x.get("relevance_score", 0))
        
        return {
            "insights": insights[:limit],
            "similar_creators_found": len(similar_creators),
            "insight_basis": "anonymized_patterns",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_creator_metrics(self, creator_id: str) -> Dict[str, Any]:
        """Get metrics for a creator"""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "status": 1, "platforms": 1, "priority": 1, "created_at": 1}
        ).to_list(500)
        
        total = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        
        # Platform distribution
        platform_counts = defaultdict(int)
        for p in proposals:
            for platform in p.get("platforms", []):
                platform_counts[platform] += 1
        
        # Subscription tier
        sub = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0, "tier": 1}
        )
        
        return {
            "total_proposals": total,
            "approved_proposals": approved,
            "approval_rate": round((approved / total * 100), 1) if total > 0 else 0,
            "top_platforms": sorted(platform_counts.items(), key=lambda x: -x[1])[:3],
            "tier": sub.get("tier", "Free") if sub else "Free",
            "proposal_velocity": total / max(1, 30)  # Proposals per month (simplified)
        }
    
    async def _find_similar_creators(
        self, 
        creator_id: str, 
        creator: Dict, 
        metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Find creators similar to the given creator"""
        # Get all other active creators
        other_creators = await self.db.creators.find(
            {"status": "active", "id": {"$ne": creator_id}},
            {"_id": 0, "id": 1, "platforms": 1, "niche": 1}
        ).to_list(1000)
        
        similar = []
        creator_platforms = set(creator.get("platforms", []))
        creator_niche = creator.get("niche", "").lower()
        
        for other in other_creators:
            other_platforms = set(other.get("platforms", []))
            other_niche = other.get("niche", "").lower()
            
            # Calculate similarity score
            score = 0.0
            
            # Platform overlap (40% weight)
            if creator_platforms and other_platforms:
                overlap = len(creator_platforms & other_platforms)
                total = len(creator_platforms | other_platforms)
                score += 0.4 * (overlap / total if total > 0 else 0)
            
            # Niche similarity (30% weight)
            if creator_niche and other_niche:
                if creator_niche == other_niche:
                    score += 0.3
                elif creator_niche in other_niche or other_niche in creator_niche:
                    score += 0.15
            
            # Get other creator's metrics for performance similarity
            other_metrics = await self._get_creator_metrics(other["id"])
            
            # Approval rate similarity (20% weight)
            if metrics["total_proposals"] > 0 and other_metrics["total_proposals"] >= 3:
                rate_diff = abs(metrics["approval_rate"] - other_metrics["approval_rate"])
                rate_similarity = max(0, 1 - (rate_diff / 100))
                score += 0.2 * rate_similarity
            
            # Activity level similarity (10% weight)
            if metrics["total_proposals"] > 0 and other_metrics["total_proposals"] > 0:
                velocity_diff = abs(metrics["proposal_velocity"] - other_metrics["proposal_velocity"])
                velocity_similarity = max(0, 1 - (velocity_diff / 10))
                score += 0.1 * velocity_similarity
            
            if score >= self.min_similarity_score:
                similar.append({
                    "id": other["id"],
                    "similarity_score": round(score, 2),
                    "metrics": other_metrics,
                    "platforms": list(other_platforms)
                })
        
        # Sort by similarity and limit
        similar.sort(key=lambda x: -x["similarity_score"])
        return similar[:50]  # Top 50 similar creators
    
    async def _generate_success_insights(
        self, 
        similar_creators: List[Dict], 
        creator_metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Generate success pattern insights from similar creators"""
        insights = []
        
        # Find high-performing similar creators
        high_performers = [c for c in similar_creators if c["metrics"]["approval_rate"] > 70]
        
        if not high_performers:
            return insights
        
        # Analyze their patterns
        all_platforms = []
        for c in high_performers:
            all_platforms.extend([p[0] for p in c["metrics"].get("top_platforms", [])])
        
        # Find common successful platforms
        platform_counts = defaultdict(int)
        for p in all_platforms:
            platform_counts[p] += 1
        
        if platform_counts:
            top_platform = max(platform_counts.items(), key=lambda x: x[1])
            if top_platform[1] >= 3:
                insights.append({
                    "type": InsightType.SUCCESS_PATTERN,
                    "title": f"Creators like you succeed on {top_platform[0]}",
                    "description": f"Among similar creators with 70%+ approval rates, {top_platform[0]} is the most common platform.",
                    "recommendation": f"Consider focusing more proposals on {top_platform[0]}",
                    "data": {
                        "platform": top_platform[0],
                        "high_performers_using": top_platform[1],
                        "total_high_performers": len(high_performers)
                    },
                    "relevance_score": 0.85,
                    "confidence": round(top_platform[1] / len(high_performers), 2)
                })
        
        # Average approval rate comparison
        avg_approval = sum(c["metrics"]["approval_rate"] for c in high_performers) / len(high_performers)
        if creator_metrics["approval_rate"] < avg_approval:
            gap = round(avg_approval - creator_metrics["approval_rate"], 1)
            insights.append({
                "type": InsightType.SUCCESS_PATTERN,
                "title": "Room for improvement",
                "description": f"Similar high-performing creators average {avg_approval:.0f}% approval rate.",
                "recommendation": f"Focus on proposal quality to close the {gap}% gap",
                "data": {
                    "your_rate": creator_metrics["approval_rate"],
                    "peer_avg_rate": round(avg_approval, 1),
                    "gap": gap
                },
                "relevance_score": 0.8,
                "confidence": 0.75
            })
        
        return insights
    
    async def _generate_mistake_insights(
        self, 
        similar_creators: List[Dict], 
        creator_metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Generate common mistake insights"""
        insights = []
        
        # Find struggling similar creators
        struggling = [c for c in similar_creators if c["metrics"]["approval_rate"] < 40 and c["metrics"]["total_proposals"] >= 3]
        
        if len(struggling) < 2:
            return insights
        
        # Analyze their patterns to avoid
        struggling_platforms = []
        for c in struggling:
            struggling_platforms.extend([p[0] for p in c["metrics"].get("top_platforms", [])])
        
        platform_counts = defaultdict(int)
        for p in struggling_platforms:
            platform_counts[p] += 1
        
        # Identify platform correlating with struggles
        if platform_counts:
            risky_platform = max(platform_counts.items(), key=lambda x: x[1])
            if risky_platform[1] >= 2:
                insights.append({
                    "type": InsightType.COMMON_MISTAKE,
                    "title": f"Caution with {risky_platform[0]} proposals",
                    "description": f"Similar creators who struggle often focus heavily on {risky_platform[0]}.",
                    "recommendation": "Diversify your platform focus or ensure strong {risky_platform[0]} expertise",
                    "data": {
                        "platform": risky_platform[0],
                        "struggling_creators_using": risky_platform[1]
                    },
                    "relevance_score": 0.7,
                    "confidence": 0.6
                })
        
        return insights
    
    async def _generate_timing_insights(self, similar_creators: List[Dict]) -> List[Dict[str, Any]]:
        """Generate timing-based insights"""
        insights = []
        
        # Calculate average proposal velocity among successful creators
        successful = [c for c in similar_creators if c["metrics"]["approval_rate"] >= 60]
        
        if not successful:
            return insights
        
        avg_velocity = sum(c["metrics"]["proposal_velocity"] for c in successful) / len(successful)
        
        if avg_velocity > 0.5:
            insights.append({
                "type": InsightType.TIMING_INSIGHT,
                "title": "Consistent submission pays off",
                "description": f"Successful similar creators submit ~{int(avg_velocity * 30)} proposals per month.",
                "recommendation": "Maintain regular proposal submissions for better results",
                "data": {
                    "avg_proposals_per_month": round(avg_velocity * 30, 1),
                    "based_on_creators": len(successful)
                },
                "relevance_score": 0.75,
                "confidence": 0.7
            })
        
        return insights
    
    async def _generate_platform_insights(
        self, 
        similar_creators: List[Dict], 
        creator_platforms: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate platform-specific insights"""
        insights = []
        
        # Aggregate platform performance
        platform_performance = defaultdict(lambda: {"total": 0, "success": 0})
        
        for creator in similar_creators:
            for platform in creator.get("platforms", []):
                if creator["metrics"]["approval_rate"] >= 60:
                    platform_performance[platform]["success"] += 1
                platform_performance[platform]["total"] += 1
        
        # Find best performing platform for similar creators
        best_platform = None
        best_rate = 0
        
        for platform, data in platform_performance.items():
            if data["total"] >= 3:
                success_rate = data["success"] / data["total"]
                if success_rate > best_rate:
                    best_rate = success_rate
                    best_platform = platform
        
        if best_platform and best_rate > 0.5:
            is_using = best_platform in creator_platforms
            insights.append({
                "type": InsightType.PLATFORM_TREND,
                "title": f"{best_platform} shows strong results",
                "description": f"{int(best_rate * 100)}% of similar creators succeed on {best_platform}.",
                "recommendation": "Great choice!" if is_using else f"Consider adding {best_platform} to your platforms",
                "data": {
                    "platform": best_platform,
                    "success_rate": round(best_rate * 100, 1),
                    "sample_size": platform_performance[best_platform]["total"],
                    "already_using": is_using
                },
                "relevance_score": 0.9 if not is_using else 0.6,
                "confidence": round(best_rate, 2)
            })
        
        return insights
    
    async def _generate_benchmark_insights(
        self, 
        similar_creators: List[Dict], 
        creator_metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Generate benchmark insights"""
        insights = []
        
        if not similar_creators:
            return insights
        
        # Calculate benchmarks
        approval_rates = [c["metrics"]["approval_rate"] for c in similar_creators if c["metrics"]["total_proposals"] >= 3]
        
        if not approval_rates:
            return insights
        
        avg_rate = sum(approval_rates) / len(approval_rates)
        your_rate = creator_metrics["approval_rate"]
        
        # Percentile calculation
        below_you = len([r for r in approval_rates if r < your_rate])
        percentile = int((below_you / len(approval_rates)) * 100) if approval_rates else 50
        
        if percentile >= 75:
            insights.append({
                "type": InsightType.NICHE_BENCHMARK,
                "title": "You're a top performer!",
                "description": f"You're in the top {100 - percentile}% of similar creators.",
                "recommendation": "Keep up the great work and consider sharing your approach",
                "data": {
                    "your_approval_rate": your_rate,
                    "peer_avg_rate": round(avg_rate, 1),
                    "percentile": percentile,
                    "total_peers": len(approval_rates)
                },
                "relevance_score": 0.95,
                "confidence": 0.85
            })
        elif percentile >= 50:
            insights.append({
                "type": InsightType.NICHE_BENCHMARK,
                "title": "You're above average",
                "description": f"You're performing better than {percentile}% of similar creators.",
                "recommendation": "Small improvements could push you into top performers",
                "data": {
                    "your_approval_rate": your_rate,
                    "peer_avg_rate": round(avg_rate, 1),
                    "percentile": percentile,
                    "gap_to_top": round(max(approval_rates) - your_rate, 1)
                },
                "relevance_score": 0.8,
                "confidence": 0.75
            })
        else:
            insights.append({
                "type": InsightType.NICHE_BENCHMARK,
                "title": "Growth opportunity",
                "description": f"You're currently at {percentile}th percentile among similar creators.",
                "recommendation": "Review the success patterns above to improve your approval rate",
                "data": {
                    "your_approval_rate": your_rate,
                    "peer_avg_rate": round(avg_rate, 1),
                    "percentile": percentile,
                    "gap_to_avg": round(avg_rate - your_rate, 1)
                },
                "relevance_score": 0.85,
                "confidence": 0.75
            })
        
        return insights
    
    # ============== MEMORY HEALTH ==============
    
    async def get_memory_health_report(self, creator_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get memory health report for a creator or platform-wide.
        """
        query = {"creator_id": creator_id} if creator_id else {}
        
        # Count memories by type
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$memory_type",
                "count": {"$sum": 1},
                "avg_importance": {"$avg": "$importance"},
                "total_recalls": {"$sum": "$recall_count"}
            }}
        ]
        
        type_stats = await self.db.arris_memories.aggregate(pipeline).to_list(20)
        
        # Count archived
        archived_count = await self.db.arris_memories_archive.count_documents(query)
        
        # Count old memories (potential consolidation candidates)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.consolidation_age_days)).isoformat()
        old_memories = await self.db.arris_memories.count_documents({
            **query,
            "created_at": {"$lt": cutoff},
            "consolidated": {"$ne": True}
        })
        
        total_memories = sum(t["count"] for t in type_stats)
        
        # Calculate health score
        health_score = 100
        issues = []
        recommendations = []
        
        # Penalize for too many old unconsolidated memories
        if old_memories > total_memories * 0.3:
            health_score -= 20
            issues.append(f"{old_memories} memories pending consolidation")
            recommendations.append("Run memory consolidation to improve retrieval speed")
        
        # Penalize for low recall rates
        total_recalls = sum(t["total_recalls"] for t in type_stats)
        if total_memories > 0 and total_recalls / total_memories < 0.5:
            health_score -= 10
            issues.append("Low memory utilization (many memories never recalled)")
            recommendations.append("Consider archiving unused memories")
        
        return {
            "health_score": max(0, health_score),
            "status": "excellent" if health_score >= 80 else "good" if health_score >= 60 else "needs_attention",
            "total_memories": total_memories,
            "archived_memories": archived_count,
            "consolidation_candidates": old_memories,
            "by_type": {t["_id"]: t for t in type_stats},
            "issues": issues,
            "recommendations": recommendations,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_consolidation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent consolidation run history"""
        history = await self.db.memory_consolidation_log.find(
            {},
            {"_id": 0}
        ).sort("run_at", -1).to_list(limit)
        
        return history
    
    # ============== MEMORY SEARCH API (C3) ==============
    
    async def search_memories(
        self,
        creator_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        include_archived: bool = False,
        include_consolidated: bool = True,
        sort_by: str = "relevance",  # relevance, date, importance
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Full-text search across a creator's ARRIS memories.
        
        Implements workspace isolation (creator can only search their own memories).
        
        Search features:
        - Full-text search across memory content, tags, and metadata
        - Filter by memory type, date range, importance
        - Optional inclusion of archived memories
        - Relevance scoring based on match quality
        
        Args:
            creator_id: The creator's ID (workspace isolation)
            query: Search query string
            memory_types: Filter by memory types (interaction, proposal, outcome, pattern, etc.)
            tags: Filter by tags
            min_importance: Minimum importance threshold (0.0-1.0)
            date_from: Start date filter (ISO format)
            date_to: End date filter (ISO format)
            include_archived: Whether to search archived memories
            include_consolidated: Whether to include consolidated/summary memories
            sort_by: Sort order (relevance, date, importance)
            limit: Maximum results to return
        
        Returns:
            Search results with relevance scores and metadata
        """
        search_start = datetime.now(timezone.utc)
        
        # Build base query with workspace isolation
        base_query = {"creator_id": creator_id}
        
        # Filter by memory types
        if memory_types:
            base_query["memory_type"] = {"$in": memory_types}
        
        # Filter by tags
        if tags:
            base_query["tags"] = {"$in": tags}
        
        # Filter by importance
        if min_importance > 0:
            base_query["importance"] = {"$gte": min_importance}
        
        # Date range filters
        if date_from:
            base_query["created_at"] = {"$gte": date_from}
        if date_to:
            if "created_at" in base_query:
                base_query["created_at"]["$lte"] = date_to
            else:
                base_query["created_at"] = {"$lte": date_to}
        
        # Exclude superseded memories unless specifically requested
        if not include_consolidated:
            base_query["superseded"] = {"$ne": True}
        
        # Search in main memories collection
        main_results = await self._search_collection(
            collection=self.db.arris_memories,
            query=query,
            base_filter=base_query,
            limit=limit
        )
        
        # Optionally search archived memories
        archived_results = []
        if include_archived:
            archived_query = base_query.copy()
            archived_results = await self._search_collection(
                collection=self.db.arris_memories_archive,
                query=query,
                base_filter=archived_query,
                limit=limit // 2  # Limit archived results
            )
            # Mark archived results
            for r in archived_results:
                r["is_archived"] = True
        
        # Combine and deduplicate results
        all_results = main_results + archived_results
        
        # Sort results
        if sort_by == "relevance":
            all_results.sort(key=lambda x: -x.get("_relevance_score", 0))
        elif sort_by == "date":
            all_results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "importance":
            all_results.sort(key=lambda x: -x.get("importance", 0))
        
        # Limit results
        all_results = all_results[:limit]
        
        # Calculate search statistics
        search_time_ms = (datetime.now(timezone.utc) - search_start).total_seconds() * 1000
        
        # Get type distribution in results
        type_distribution = defaultdict(int)
        for r in all_results:
            type_distribution[r.get("memory_type", "unknown")] += 1
        
        # Log search for analytics
        search_log = {
            "id": f"SEARCH-{uuid.uuid4().hex[:10]}",
            "creator_id": creator_id,
            "query": query,
            "filters": {
                "memory_types": memory_types,
                "tags": tags,
                "min_importance": min_importance,
                "date_from": date_from,
                "date_to": date_to,
                "include_archived": include_archived
            },
            "results_count": len(all_results),
            "search_time_ms": round(search_time_ms, 2),
            "searched_at": search_start.isoformat()
        }
        await self.db.memory_search_log.insert_one(search_log)
        
        return {
            "query": query,
            "results": all_results,
            "total_found": len(all_results),
            "search_time_ms": round(search_time_ms, 2),
            "type_distribution": dict(type_distribution),
            "filters_applied": {
                "memory_types": memory_types,
                "tags": tags,
                "min_importance": min_importance,
                "date_range": {"from": date_from, "to": date_to} if date_from or date_to else None,
                "include_archived": include_archived,
                "include_consolidated": include_consolidated
            },
            "sort_by": sort_by,
            "searched_at": search_start.isoformat()
        }
    
    async def _search_collection(
        self,
        collection,
        query: str,
        base_filter: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search a memory collection using multiple matching strategies.
        
        Strategies:
        1. Exact phrase match in content (highest relevance)
        2. Word match in content fields
        3. Tag match
        4. Memory type match
        """
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Fetch memories matching base filter
        memories = await collection.find(
            base_filter,
            {"_id": 0}
        ).limit(limit * 3).to_list(limit * 3)  # Fetch more, then filter
        
        for memory in memories:
            relevance_score = self._calculate_relevance(memory, query_lower, query_words)
            
            if relevance_score > 0:
                memory["_relevance_score"] = relevance_score
                memory["_match_highlights"] = self._get_match_highlights(memory, query_words)
                results.append(memory)
        
        return results
    
    def _calculate_relevance(
        self, 
        memory: Dict[str, Any], 
        query_lower: str, 
        query_words: List[str]
    ) -> float:
        """
        Calculate relevance score for a memory based on query match.
        
        Scoring:
        - Exact phrase match in content: +50 points
        - Word match in content: +10 points per word
        - Tag match: +15 points per matching tag
        - Title/summary match: +20 points
        - Memory type match: +5 points
        - Importance boost: +5 * importance
        """
        score = 0.0
        content = memory.get("content", {})
        content_str = json.dumps(content).lower() if isinstance(content, dict) else str(content).lower()
        
        # Exact phrase match (highest value)
        if query_lower in content_str:
            score += 50
        
        # Word matches in content
        for word in query_words:
            if len(word) >= 2 and word in content_str:
                score += 10
        
        # Tag matches
        tags = [t.lower() for t in memory.get("tags", [])]
        for word in query_words:
            if word in tags:
                score += 15
            # Partial tag match
            for tag in tags:
                if word in tag:
                    score += 5
        
        # Title/summary matches
        title = content.get("title", "").lower() if isinstance(content, dict) else ""
        summary = content.get("summary", "").lower() if isinstance(content, dict) else ""
        
        if query_lower in title:
            score += 30
        elif any(word in title for word in query_words):
            score += 20
        
        if query_lower in summary:
            score += 25
        elif any(word in summary for word in query_words):
            score += 15
        
        # Memory type match
        memory_type = memory.get("memory_type", "").lower()
        if any(word in memory_type for word in query_words):
            score += 5
        
        # Importance boost
        importance = memory.get("importance", 0.5)
        score += 5 * importance
        
        # Recall frequency boost (more recalled = more relevant)
        recall_count = memory.get("recall_count", 0)
        score += min(10, recall_count * 2)
        
        return round(score, 2)
    
    def _get_match_highlights(
        self, 
        memory: Dict[str, Any], 
        query_words: List[str]
    ) -> List[Dict[str, str]]:
        """
        Generate match highlights showing where query matched.
        """
        highlights = []
        content = memory.get("content", {})
        
        if isinstance(content, dict):
            # Check each content field
            for key, value in content.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for word in query_words:
                        if word in value_lower:
                            # Find context around match
                            idx = value_lower.find(word)
                            start = max(0, idx - 30)
                            end = min(len(value), idx + len(word) + 30)
                            snippet = value[start:end]
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(value):
                                snippet = snippet + "..."
                            
                            highlights.append({
                                "field": key,
                                "snippet": snippet,
                                "matched_word": word
                            })
        
        # Check tags
        tags = memory.get("tags", [])
        for tag in tags:
            for word in query_words:
                if word in tag.lower():
                    highlights.append({
                        "field": "tags",
                        "snippet": tag,
                        "matched_word": word
                    })
        
        return highlights[:5]  # Limit highlights
    
    async def get_search_suggestions(
        self,
        creator_id: str,
        partial_query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get search suggestions based on partial query.
        
        Returns suggestions from:
        - Recent search queries
        - Popular tags
        - Memory titles/topics
        """
        partial_lower = partial_query.lower()
        suggestions = []
        
        # Get tags that match
        tag_pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$unwind": "$tags"},
            {"$match": {"tags": {"$regex": f"^{partial_lower}", "$options": "i"}}},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        tag_suggestions = await self.db.arris_memories.aggregate(tag_pipeline).to_list(limit)
        
        for t in tag_suggestions:
            suggestions.append({
                "type": "tag",
                "value": t["_id"],
                "frequency": t["count"]
            })
        
        # Get memory types that match
        valid_types = ["interaction", "proposal", "outcome", "pattern", "preference", "feedback", "milestone"]
        for mtype in valid_types:
            if partial_lower in mtype:
                type_count = await self.db.arris_memories.count_documents({
                    "creator_id": creator_id,
                    "memory_type": mtype
                })
                if type_count > 0:
                    suggestions.append({
                        "type": "memory_type",
                        "value": mtype,
                        "frequency": type_count
                    })
        
        # Get recent search queries
        recent_searches = await self.db.memory_search_log.find(
            {
                "creator_id": creator_id,
                "query": {"$regex": f"^{partial_lower}", "$options": "i"}
            },
            {"_id": 0, "query": 1}
        ).sort("searched_at", -1).limit(5).to_list(5)
        
        for s in recent_searches:
            if not any(sug["value"] == s["query"] for sug in suggestions):
                suggestions.append({
                    "type": "recent_search",
                    "value": s["query"],
                    "frequency": 1
                })
        
        # Sort by frequency and limit
        suggestions.sort(key=lambda x: -x.get("frequency", 0))
        
        return {
            "partial_query": partial_query,
            "suggestions": suggestions[:limit]
        }
    
    async def get_search_analytics(self, creator_id: str) -> Dict[str, Any]:
        """
        Get search analytics for a creator.
        Shows popular searches, search patterns, and memory access stats.
        """
        # Get total searches
        total_searches = await self.db.memory_search_log.count_documents({"creator_id": creator_id})
        
        # Get popular queries
        popular_pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$group": {"_id": "$query", "count": {"$sum": 1}, "avg_results": {"$avg": "$results_count"}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        popular_queries = await self.db.memory_search_log.aggregate(popular_pipeline).to_list(10)
        
        # Get average search time
        time_pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$group": {"_id": None, "avg_time": {"$avg": "$search_time_ms"}}}
        ]
        time_result = await self.db.memory_search_log.aggregate(time_pipeline).to_list(1)
        avg_search_time = time_result[0]["avg_time"] if time_result else 0
        
        # Get most searched memory types
        type_pipeline = [
            {"$match": {"creator_id": creator_id, "filters.memory_types": {"$exists": True, "$ne": None}}},
            {"$unwind": "$filters.memory_types"},
            {"$group": {"_id": "$filters.memory_types", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        popular_types = await self.db.memory_search_log.aggregate(type_pipeline).to_list(5)
        
        # Get search activity over time (last 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        activity_pipeline = [
            {"$match": {"creator_id": creator_id, "searched_at": {"$gte": thirty_days_ago}}},
            {"$project": {"day": {"$substr": ["$searched_at", 0, 10]}}},
            {"$group": {"_id": "$day", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        daily_activity = await self.db.memory_search_log.aggregate(activity_pipeline).to_list(30)
        
        return {
            "total_searches": total_searches,
            "avg_search_time_ms": round(avg_search_time, 2),
            "popular_queries": [
                {"query": q["_id"], "count": q["count"], "avg_results": round(q["avg_results"], 1)}
                for q in popular_queries
            ],
            "popular_memory_types": [
                {"type": t["_id"], "count": t["count"]}
                for t in popular_types
            ],
            "daily_activity": [
                {"date": a["_id"], "searches": a["count"]}
                for a in daily_activity
            ],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }


# Global instance (will be initialized in server startup)
enhanced_memory_palace = None
