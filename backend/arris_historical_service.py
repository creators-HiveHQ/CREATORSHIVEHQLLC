"""
ARRIS Historical Learning Visualization Service
Provides historical comparison data for ARRIS learning progression over time

Features:
- Memory growth over time
- Pattern detection timeline
- Learning accuracy progression
- Milestone achievements
- Comparative analytics across time periods
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict

logger = logging.getLogger(__name__)


class ArrisHistoricalService:
    """
    Service for providing historical visualization data for ARRIS learning.
    Shows how ARRIS has learned about a creator over time.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_learning_timeline(
        self,
        creator_id: str,
        date_range: str = "all"
    ) -> Dict[str, Any]:
        """
        Get a timeline of ARRIS learning progression.
        Shows memory accumulation, pattern discoveries, and accuracy improvements.
        """
        # Calculate date filter
        start_date = self._get_start_date(date_range)
        
        # Get memories over time
        memory_timeline = await self._get_memory_timeline(creator_id, start_date)
        
        # Get pattern discoveries over time
        pattern_timeline = await self._get_pattern_timeline(creator_id, start_date)
        
        # Get learning metrics progression
        learning_progression = await self._get_learning_progression(creator_id, start_date)
        
        # Get milestones
        milestones = await self._get_milestones(creator_id)
        
        return {
            "creator_id": creator_id,
            "date_range": date_range,
            "memory_timeline": memory_timeline,
            "pattern_timeline": pattern_timeline,
            "learning_progression": learning_progression,
            "milestones": milestones,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_comparative_analysis(
        self,
        creator_id: str,
        period1: str = "30d",
        period2: str = "prev_30d"
    ) -> Dict[str, Any]:
        """
        Compare ARRIS learning between two time periods.
        Shows growth and improvement over time.
        """
        # Calculate date ranges
        now = datetime.now(timezone.utc)
        
        if period1 == "30d":
            period1_start = now - timedelta(days=30)
            period1_end = now
        elif period1 == "7d":
            period1_start = now - timedelta(days=7)
            period1_end = now
        elif period1 == "90d":
            period1_start = now - timedelta(days=90)
            period1_end = now
        else:
            period1_start = now - timedelta(days=30)
            period1_end = now
        
        if period2 == "prev_30d":
            period2_start = period1_start - timedelta(days=30)
            period2_end = period1_start
        elif period2 == "prev_7d":
            period2_start = period1_start - timedelta(days=7)
            period2_end = period1_start
        elif period2 == "prev_90d":
            period2_start = period1_start - timedelta(days=90)
            period2_end = period1_start
        else:
            period2_start = period1_start - timedelta(days=30)
            period2_end = period1_start
        
        # Get stats for both periods
        period1_stats = await self._get_period_stats(creator_id, period1_start, period1_end)
        period2_stats = await self._get_period_stats(creator_id, period2_start, period2_end)
        
        # Calculate comparisons
        comparisons = self._calculate_comparisons(period1_stats, period2_stats)
        
        return {
            "creator_id": creator_id,
            "current_period": {
                "label": period1,
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "stats": period1_stats
            },
            "previous_period": {
                "label": period2,
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "stats": period2_stats
            },
            "comparisons": comparisons,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_learning_snapshot(self, creator_id: str) -> Dict[str, Any]:
        """
        Get a snapshot of current ARRIS learning state for a creator.
        Shows current understanding, strengths, and growth indicators.
        """
        # Get memory summary
        memory_summary = await self._get_memory_summary(creator_id)
        
        # Get active patterns
        active_patterns = await self._get_active_patterns(creator_id)
        
        # Get learning metrics
        learning_metrics = await self._get_current_learning_metrics(creator_id)
        
        # Get recent activity
        recent_activity = await self._get_recent_learning_activity(creator_id)
        
        # Calculate learning health score
        health_score = self._calculate_learning_health(
            memory_summary, active_patterns, learning_metrics
        )
        
        return {
            "creator_id": creator_id,
            "memory_summary": memory_summary,
            "active_patterns": active_patterns,
            "learning_metrics": learning_metrics,
            "recent_activity": recent_activity,
            "health_score": health_score,
            "snapshot_time": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_growth_chart_data(
        self,
        creator_id: str,
        metric: str = "memories",
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get chart data for visualizing ARRIS learning growth.
        
        Args:
            creator_id: Creator's ID
            metric: What to chart - memories, patterns, accuracy, interactions
            granularity: daily, weekly, monthly
        """
        # Determine time window based on granularity
        if granularity == "daily":
            days = 30
            date_format = "%Y-%m-%d"
        elif granularity == "weekly":
            days = 90
            date_format = "%Y-W%W"
        else:  # monthly
            days = 365
            date_format = "%Y-%m"
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get data points based on metric
        if metric == "memories":
            data_points = await self._get_memory_growth_data(
                creator_id, start_date, date_format
            )
        elif metric == "patterns":
            data_points = await self._get_pattern_growth_data(
                creator_id, start_date, date_format
            )
        elif metric == "accuracy":
            data_points = await self._get_accuracy_growth_data(
                creator_id, start_date, date_format
            )
        elif metric == "interactions":
            data_points = await self._get_interaction_growth_data(
                creator_id, start_date, date_format
            )
        else:
            data_points = []
        
        return {
            "creator_id": creator_id,
            "metric": metric,
            "granularity": granularity,
            "data_points": data_points,
            "total_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ============== PRIVATE METHODS ==============
    
    def _get_start_date(self, date_range: str) -> Optional[datetime]:
        """Convert date range string to start date"""
        now = datetime.now(timezone.utc)
        
        if date_range == "7d":
            return now - timedelta(days=7)
        elif date_range == "30d":
            return now - timedelta(days=30)
        elif date_range == "90d":
            return now - timedelta(days=90)
        elif date_range == "1y":
            return now - timedelta(days=365)
        else:  # all
            return None
    
    async def _get_memory_timeline(
        self,
        creator_id: str,
        start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get memory accumulation over time"""
        query = {"creator_id": creator_id}
        if start_date:
            query["created_at"] = {"$gte": start_date.isoformat()}
        
        pipeline = [
            {"$match": query},
            {"$project": {
                "date": {"$substr": ["$created_at", 0, 10]},
                "memory_type": 1,
                "importance": 1
            }},
            {"$group": {
                "_id": {"date": "$date", "type": "$memory_type"},
                "count": {"$sum": 1},
                "avg_importance": {"$avg": "$importance"}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        results = await self.db.arris_memories.aggregate(pipeline).to_list(500)
        
        # Transform to timeline format
        timeline = []
        date_groups = defaultdict(lambda: {"types": {}, "total": 0})
        
        for r in results:
            date = r["_id"]["date"]
            mtype = r["_id"]["type"]
            date_groups[date]["types"][mtype] = {
                "count": r["count"],
                "avg_importance": round(r["avg_importance"], 2)
            }
            date_groups[date]["total"] += r["count"]
        
        for date in sorted(date_groups.keys()):
            timeline.append({
                "date": date,
                "total_memories": date_groups[date]["total"],
                "by_type": date_groups[date]["types"]
            })
        
        return timeline
    
    async def _get_pattern_timeline(
        self,
        creator_id: str,
        start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get pattern discoveries over time"""
        query = {
            "creator_id": creator_id,
            "memory_type": "pattern"
        }
        if start_date:
            query["created_at"] = {"$gte": start_date.isoformat()}
        
        patterns = await self.db.arris_memories.find(
            query,
            {"_id": 0, "created_at": 1, "content": 1, "importance": 1}
        ).sort("created_at", 1).to_list(100)
        
        timeline = []
        for p in patterns:
            content = p.get("content", {})
            timeline.append({
                "date": p.get("created_at", "")[:10],
                "category": content.get("category"),
                "title": content.get("title"),
                "confidence": content.get("confidence"),
                "importance": p.get("importance")
            })
        
        return timeline
    
    async def _get_learning_progression(
        self,
        creator_id: str,
        start_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get learning accuracy progression over time"""
        # Get outcome memories to track prediction accuracy
        query = {
            "creator_id": creator_id,
            "memory_type": "outcome"
        }
        if start_date:
            query["created_at"] = {"$gte": start_date.isoformat()}
        
        outcomes = await self.db.arris_memories.find(
            query,
            {"_id": 0, "created_at": 1, "content": 1}
        ).sort("created_at", 1).to_list(100)
        
        # Calculate cumulative accuracy
        progression = []
        total = 0
        accurate = 0
        
        for o in outcomes:
            total += 1
            content = o.get("content", {})
            if content.get("prediction_accurate", False):
                accurate += 1
            
            accuracy_rate = (accurate / total) * 100 if total > 0 else 0
            
            progression.append({
                "date": o.get("created_at", "")[:10],
                "cumulative_predictions": total,
                "cumulative_accurate": accurate,
                "accuracy_rate": round(accuracy_rate, 1),
                "outcome": content.get("outcome")
            })
        
        return progression
    
    async def _get_milestones(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get ARRIS learning milestones for a creator"""
        milestones = []
        
        # Check for first memory
        first_memory = await self.db.arris_memories.find_one(
            {"creator_id": creator_id},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", 1)]
        )
        if first_memory:
            milestones.append({
                "type": "first_memory",
                "title": "First Memory Created",
                "description": "ARRIS started learning about you",
                "date": first_memory.get("created_at", "")[:10],
                "icon": "🧠"
            })
        
        # Check for first pattern
        first_pattern = await self.db.arris_memories.find_one(
            {"creator_id": creator_id, "memory_type": "pattern"},
            {"_id": 0, "created_at": 1, "content": 1},
            sort=[("created_at", 1)]
        )
        if first_pattern:
            milestones.append({
                "type": "first_pattern",
                "title": "First Pattern Detected",
                "description": first_pattern.get("content", {}).get("title", "Pattern identified"),
                "date": first_pattern.get("created_at", "")[:10],
                "icon": "🔮"
            })
        
        # Check memory count milestones
        memory_count = await self.db.arris_memories.count_documents({"creator_id": creator_id})
        
        milestone_thresholds = [
            (10, "10 Memories", "Building understanding", "📚"),
            (25, "25 Memories", "Growing knowledge base", "📖"),
            (50, "50 Memories", "Deep understanding achieved", "🎓"),
            (100, "100 Memories", "Expert level knowledge", "🏆")
        ]
        
        for threshold, title, desc, icon in milestone_thresholds:
            if memory_count >= threshold:
                # Find when this milestone was reached
                skip_count = threshold - 1
                milestone_memory = await self.db.arris_memories.find_one(
                    {"creator_id": creator_id},
                    {"_id": 0, "created_at": 1},
                    sort=[("created_at", 1)],
                    skip=skip_count
                )
                if milestone_memory:
                    milestones.append({
                        "type": f"memories_{threshold}",
                        "title": title,
                        "description": desc,
                        "date": milestone_memory.get("created_at", "")[:10],
                        "icon": icon
                    })
        
        # Check for high accuracy milestone
        learning_metrics = await self.db.arris_learning_metrics.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        if learning_metrics:
            total = learning_metrics.get("total_predictions", 0)
            accurate = learning_metrics.get("accurate_predictions", 0)
            if total >= 10:
                accuracy = (accurate / total) * 100
                if accuracy >= 80:
                    milestones.append({
                        "type": "high_accuracy",
                        "title": "High Accuracy Achieved",
                        "description": f"ARRIS predictions are {int(accuracy)}% accurate",
                        "date": learning_metrics.get("last_updated", "")[:10],
                        "icon": "🎯"
                    })
        
        # Sort milestones by date
        milestones.sort(key=lambda x: x.get("date", ""))
        
        return milestones
    
    async def _get_period_stats(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get statistics for a specific time period"""
        date_query = {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
        
        # Memory stats
        memory_count = await self.db.arris_memories.count_documents({
            "creator_id": creator_id,
            "created_at": date_query
        })
        
        # Pattern stats
        pattern_count = await self.db.arris_memories.count_documents({
            "creator_id": creator_id,
            "memory_type": "pattern",
            "created_at": date_query
        })
        
        # Outcome/prediction stats
        outcomes = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": "outcome",
            "created_at": date_query
        }, {"_id": 0, "content": 1}).to_list(100)
        
        accurate_predictions = len([o for o in outcomes if o.get("content", {}).get("prediction_accurate")])
        total_predictions = len(outcomes)
        accuracy_rate = (accurate_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # Interaction stats
        interactions = await self.db.arris_memories.count_documents({
            "creator_id": creator_id,
            "memory_type": "interaction",
            "created_at": date_query
        })
        
        # Calculate avg importance
        pipeline = [
            {"$match": {"creator_id": creator_id, "created_at": date_query}},
            {"$group": {"_id": None, "avg_importance": {"$avg": "$importance"}}}
        ]
        avg_result = await self.db.arris_memories.aggregate(pipeline).to_list(1)
        avg_importance = avg_result[0]["avg_importance"] if avg_result else 0
        
        return {
            "memories_created": memory_count,
            "patterns_discovered": pattern_count,
            "predictions_made": total_predictions,
            "prediction_accuracy": round(accuracy_rate, 1),
            "interactions": interactions,
            "avg_importance": round(avg_importance, 2) if avg_importance else 0
        }
    
    def _calculate_comparisons(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between two periods"""
        def calc_change(curr, prev):
            if prev == 0:
                return 100 if curr > 0 else 0
            return round(((curr - prev) / prev) * 100, 1)
        
        return {
            "memories_change": calc_change(
                current.get("memories_created", 0),
                previous.get("memories_created", 0)
            ),
            "patterns_change": calc_change(
                current.get("patterns_discovered", 0),
                previous.get("patterns_discovered", 0)
            ),
            "accuracy_change": round(
                current.get("prediction_accuracy", 0) - previous.get("prediction_accuracy", 0),
                1
            ),
            "interactions_change": calc_change(
                current.get("interactions", 0),
                previous.get("interactions", 0)
            ),
            "importance_change": round(
                current.get("avg_importance", 0) - previous.get("avg_importance", 0),
                2
            ),
            "overall_trend": self._determine_trend(current, previous)
        }
    
    def _determine_trend(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> str:
        """Determine overall learning trend"""
        positive_indicators = 0
        
        if current.get("memories_created", 0) > previous.get("memories_created", 0):
            positive_indicators += 1
        if current.get("patterns_discovered", 0) > previous.get("patterns_discovered", 0):
            positive_indicators += 1
        if current.get("prediction_accuracy", 0) > previous.get("prediction_accuracy", 0):
            positive_indicators += 2  # Accuracy is more important
        
        if positive_indicators >= 3:
            return "improving"
        elif positive_indicators >= 1:
            return "stable"
        else:
            return "needs_attention"
    
    async def _get_memory_summary(self, creator_id: str) -> Dict[str, Any]:
        """Get summary of all memories"""
        pipeline = [
            {"$match": {"creator_id": creator_id}},
            {"$group": {
                "_id": "$memory_type",
                "count": {"$sum": 1},
                "avg_importance": {"$avg": "$importance"},
                "latest": {"$max": "$created_at"}
            }}
        ]
        
        type_stats = await self.db.arris_memories.aggregate(pipeline).to_list(20)
        total_count = sum(s["count"] for s in type_stats)
        
        return {
            "total_memories": total_count,
            "by_type": {
                s["_id"]: {
                    "count": s["count"],
                    "avg_importance": round(s["avg_importance"], 2),
                    "latest": s["latest"][:10] if s.get("latest") else None
                }
                for s in type_stats
            }
        }
    
    async def _get_active_patterns(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get currently active patterns"""
        patterns = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": "pattern",
            "importance": {"$gte": 0.5}
        }, {"_id": 0, "content": 1, "importance": 1, "created_at": 1}).sort(
            "importance", -1
        ).limit(10).to_list(10)
        
        return [
            {
                "category": p.get("content", {}).get("category"),
                "title": p.get("content", {}).get("title"),
                "description": p.get("content", {}).get("description"),
                "confidence": p.get("content", {}).get("confidence"),
                "recommendation": p.get("content", {}).get("recommendation"),
                "importance": p.get("importance"),
                "discovered": p.get("created_at", "")[:10]
            }
            for p in patterns
        ]
    
    async def _get_current_learning_metrics(self, creator_id: str) -> Dict[str, Any]:
        """Get current learning metrics"""
        metrics = await self.db.arris_learning_metrics.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not metrics:
            return {
                "total_predictions": 0,
                "accurate_predictions": 0,
                "accuracy_rate": 0,
                "learning_stage": "initializing",
                "stage_description": "ARRIS is just starting to learn about you"
            }
        
        total = metrics.get("total_predictions", 0)
        accurate = metrics.get("accurate_predictions", 0)
        accuracy = (accurate / total * 100) if total > 0 else 0
        
        # Determine stage
        if total < 5:
            stage = "initializing"
            stage_desc = "ARRIS is collecting initial data"
        elif total < 15:
            stage = "learning"
            stage_desc = "ARRIS is identifying your patterns"
        elif total < 30:
            stage = "developing"
            stage_desc = "ARRIS is refining its understanding"
        elif accuracy >= 80:
            stage = "expert"
            stage_desc = "ARRIS has deep knowledge of your preferences"
        elif accuracy >= 60:
            stage = "proficient"
            stage_desc = "ARRIS understands most of your patterns"
        else:
            stage = "calibrating"
            stage_desc = "ARRIS is adjusting to your unique style"
        
        return {
            "total_predictions": total,
            "accurate_predictions": accurate,
            "accuracy_rate": round(accuracy, 1),
            "learning_stage": stage,
            "stage_description": stage_desc,
            "last_updated": metrics.get("last_updated")
        }
    
    async def _get_recent_learning_activity(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get recent learning activity"""
        recent = await self.db.arris_memories.find(
            {"creator_id": creator_id},
            {"_id": 0, "memory_type": 1, "content": 1, "created_at": 1, "importance": 1}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        activity = []
        for r in recent:
            content = r.get("content", {})
            activity.append({
                "type": r.get("memory_type"),
                "summary": self._summarize_activity(r.get("memory_type"), content),
                "importance": r.get("importance"),
                "date": r.get("created_at", "")[:10],
                "time": r.get("created_at", "")[11:19] if len(r.get("created_at", "")) > 19 else ""
            })
        
        return activity
    
    def _summarize_activity(self, memory_type: str, content: Dict) -> str:
        """Summarize a learning activity"""
        if memory_type == "pattern":
            return f"Pattern discovered: {content.get('title', 'New pattern')}"
        elif memory_type == "outcome":
            return f"Outcome recorded: {content.get('proposal_title', 'Proposal')} - {content.get('outcome', 'result')}"
        elif memory_type == "interaction":
            return f"ARRIS interaction: {content.get('topic', 'Analysis performed')}"
        elif memory_type == "proposal":
            return f"Proposal analyzed: {content.get('title', 'New proposal')}"
        elif memory_type == "feedback":
            return "Feedback recorded"
        else:
            return f"Learning event: {memory_type}"
    
    def _calculate_learning_health(
        self,
        memory_summary: Dict,
        active_patterns: List,
        learning_metrics: Dict
    ) -> Dict[str, Any]:
        """Calculate overall learning health score"""
        total_memories = memory_summary.get("total_memories", 0)
        pattern_count = len(active_patterns)
        accuracy = learning_metrics.get("accuracy_rate", 0)
        
        # Calculate score components
        memory_score = min(40, total_memories * 2)  # Max 40 points
        pattern_score = min(30, pattern_count * 6)  # Max 30 points
        accuracy_score = accuracy * 0.3  # Max 30 points
        
        total_score = memory_score + pattern_score + accuracy_score
        
        # Determine health status
        if total_score >= 80:
            status = "excellent"
            message = "ARRIS has developed deep understanding of your patterns"
            recommendation = "Continue engaging - your personalization is optimal"
        elif total_score >= 60:
            status = "good"
            message = "ARRIS is learning effectively about you"
            recommendation = "Submit more proposals to enhance pattern recognition"
        elif total_score >= 40:
            status = "developing"
            message = "ARRIS is building its understanding"
            recommendation = "Regular engagement will improve predictions"
        elif total_score >= 20:
            status = "early"
            message = "ARRIS is in early learning stages"
            recommendation = "Submit proposals and provide feedback to accelerate learning"
        else:
            status = "new"
            message = "ARRIS is just getting started"
            recommendation = "Submit your first proposals to begin the learning journey"
        
        return {
            "score": round(total_score),
            "status": status,
            "message": message,
            "recommendation": recommendation,
            "breakdown": {
                "memory_score": round(memory_score),
                "pattern_score": round(pattern_score),
                "accuracy_score": round(accuracy_score)
            }
        }
    
    async def _get_memory_growth_data(
        self,
        creator_id: str,
        start_date: datetime,
        date_format: str
    ) -> List[Dict[str, Any]]:
        """Get memory growth chart data"""
        pipeline = [
            {"$match": {
                "creator_id": creator_id,
                "created_at": {"$gte": start_date.isoformat()}
            }},
            {"$project": {
                "date_key": {"$substr": ["$created_at", 0, 10 if "W" not in date_format else 7]},
                "memory_type": 1
            }},
            {"$group": {
                "_id": "$date_key",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.arris_memories.aggregate(pipeline).to_list(500)
        
        # Calculate cumulative
        cumulative = 0
        data_points = []
        for r in results:
            cumulative += r["count"]
            data_points.append({
                "date": r["_id"],
                "daily": r["count"],
                "cumulative": cumulative
            })
        
        return data_points
    
    async def _get_pattern_growth_data(
        self,
        creator_id: str,
        start_date: datetime,
        date_format: str
    ) -> List[Dict[str, Any]]:
        """Get pattern discovery growth chart data"""
        pipeline = [
            {"$match": {
                "creator_id": creator_id,
                "memory_type": "pattern",
                "created_at": {"$gte": start_date.isoformat()}
            }},
            {"$project": {
                "date_key": {"$substr": ["$created_at", 0, 10]},
                "category": "$content.category"
            }},
            {"$group": {
                "_id": {"date": "$date_key", "category": "$category"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        results = await self.db.arris_memories.aggregate(pipeline).to_list(500)
        
        # Group by date
        date_groups = defaultdict(lambda: {"total": 0, "by_category": {}})
        cumulative = 0
        
        for r in results:
            date = r["_id"]["date"]
            category = r["_id"]["category"]
            date_groups[date]["by_category"][category] = r["count"]
            date_groups[date]["total"] += r["count"]
        
        data_points = []
        for date in sorted(date_groups.keys()):
            cumulative += date_groups[date]["total"]
            data_points.append({
                "date": date,
                "daily": date_groups[date]["total"],
                "cumulative": cumulative,
                "by_category": date_groups[date]["by_category"]
            })
        
        return data_points
    
    async def _get_accuracy_growth_data(
        self,
        creator_id: str,
        start_date: datetime,
        date_format: str
    ) -> List[Dict[str, Any]]:
        """Get prediction accuracy growth chart data"""
        outcomes = await self.db.arris_memories.find({
            "creator_id": creator_id,
            "memory_type": "outcome",
            "created_at": {"$gte": start_date.isoformat()}
        }, {"_id": 0, "created_at": 1, "content": 1}).sort("created_at", 1).to_list(500)
        
        cumulative_total = 0
        cumulative_accurate = 0
        data_points = []
        
        for o in outcomes:
            cumulative_total += 1
            if o.get("content", {}).get("prediction_accurate"):
                cumulative_accurate += 1
            
            accuracy = (cumulative_accurate / cumulative_total) * 100
            
            data_points.append({
                "date": o.get("created_at", "")[:10],
                "predictions": cumulative_total,
                "accurate": cumulative_accurate,
                "accuracy_rate": round(accuracy, 1)
            })
        
        return data_points
    
    async def _get_interaction_growth_data(
        self,
        creator_id: str,
        start_date: datetime,
        date_format: str
    ) -> List[Dict[str, Any]]:
        """Get interaction growth chart data"""
        pipeline = [
            {"$match": {
                "creator_id": creator_id,
                "memory_type": "interaction",
                "created_at": {"$gte": start_date.isoformat()}
            }},
            {"$project": {
                "date_key": {"$substr": ["$created_at", 0, 10]}
            }},
            {"$group": {
                "_id": "$date_key",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.db.arris_memories.aggregate(pipeline).to_list(500)
        
        cumulative = 0
        data_points = []
        for r in results:
            cumulative += r["count"]
            data_points.append({
                "date": r["_id"],
                "daily": r["count"],
                "cumulative": cumulative
            })
        
        return data_points


# Global instance placeholder
arris_historical_service = None
