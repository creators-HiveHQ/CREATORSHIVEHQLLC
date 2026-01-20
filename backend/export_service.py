"""
Export Service for Creators Hive HQ
Handles CSV/JSON export for Pro and Premium analytics
"""

import csv
import io
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExportService:
    """
    Handles data exports for Pro and Premium tier users.
    - Pro: Basic proposal and analytics export
    - Premium: Enhanced export with comparative analytics and ARRIS insights
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # ============== PROPOSAL EXPORTS ==============
    
    async def export_proposals(
        self,
        creator_id: str,
        format: str = "json",
        date_range: str = "30d",
        include_insights: bool = False
    ) -> Dict[str, Any]:
        """
        Export proposals data for a creator.
        
        Args:
            creator_id: Creator's ID
            format: 'json' or 'csv'
            date_range: '7d', '30d', '90d', '1y', or 'all'
            include_insights: Include ARRIS insights (Premium only)
        """
        time_delta = self._get_time_delta(date_range)
        start_date = datetime.now(timezone.utc) - time_delta
        
        # Exclude full insights for security
        projection = {"_id": 0}
        if not include_insights:
            projection["arris_insights_full"] = 0
        
        proposals = await self.db.proposals.find(
            {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}},
            projection
        ).sort("created_at", -1).to_list(1000)
        
        if format == "csv":
            return self._proposals_to_csv(proposals, include_insights)
        return self._proposals_to_json(proposals, date_range)
    
    def _proposals_to_csv(self, proposals: List[Dict], include_insights: bool) -> Dict[str, Any]:
        """Convert proposals to CSV format"""
        output = io.StringIO()
        
        fieldnames = [
            "id", "title", "status", "platforms", "timeline", "priority",
            "created_at", "submitted_at", "approved_at"
        ]
        
        if include_insights:
            fieldnames.extend([
                "complexity", "processing_time_seconds", "risk_level",
                "suggested_budget_min", "suggested_budget_max"
            ])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for p in proposals:
            row = {
                "id": p.get("id"),
                "title": p.get("title"),
                "status": p.get("status"),
                "platforms": ", ".join(p.get("platforms", [])),
                "timeline": p.get("timeline"),
                "priority": p.get("priority"),
                "created_at": p.get("created_at"),
                "submitted_at": p.get("submitted_at"),
                "approved_at": p.get("approved_at", "")
            }
            
            if include_insights:
                insights = p.get("arris_insights", {})
                row["complexity"] = insights.get("estimated_complexity")
                row["processing_time_seconds"] = insights.get("processing_time_seconds")
                row["risk_level"] = insights.get("risk_assessment", {}).get("level")
                budget = insights.get("suggested_budget", {})
                row["suggested_budget_min"] = budget.get("min")
                row["suggested_budget_max"] = budget.get("max")
            
            writer.writerow(row)
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"proposals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "record_count": len(proposals),
            "content_type": "text/csv"
        }
    
    def _proposals_to_json(self, proposals: List[Dict], date_range: str) -> Dict[str, Any]:
        """Convert proposals to JSON format"""
        return {
            "format": "json",
            "data": proposals,
            "filename": f"proposals_export_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "record_count": len(proposals),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "content_type": "application/json"
        }
    
    # ============== ANALYTICS EXPORTS ==============
    
    async def export_analytics(
        self,
        creator_id: str,
        format: str = "json",
        date_range: str = "30d",
        tier: str = "pro"  # "pro" or "premium"
    ) -> Dict[str, Any]:
        """
        Export analytics data for a creator.
        
        Pro tier: Basic metrics and status breakdown
        Premium tier: Enhanced with comparative analytics
        """
        time_delta = self._get_time_delta(date_range)
        start_date = datetime.now(timezone.utc) - time_delta
        
        # Get proposals for analytics
        proposals = await self.db.proposals.find(
            {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}},
            {"_id": 0}
        ).to_list(1000)
        
        # Calculate analytics
        analytics = self._calculate_analytics(proposals)
        
        if tier == "premium":
            # Add comparative analytics
            platform_proposals = await self.db.proposals.find(
                {"created_at": {"$gte": start_date.isoformat()}},
                {"_id": 0, "status": 1, "arris_insights": 1}
            ).to_list(10000)
            
            analytics["comparative"] = self._calculate_comparative_analytics(proposals, platform_proposals)
            analytics["arris_performance"] = self._calculate_arris_performance(proposals)
        
        if format == "csv":
            return self._analytics_to_csv(analytics, tier)
        return self._analytics_to_json(analytics, date_range, tier)
    
    def _calculate_analytics(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Calculate basic analytics from proposals"""
        if not proposals:
            return {
                "total_proposals": 0,
                "status_breakdown": {},
                "platform_breakdown": {},
                "priority_breakdown": {},
                "timeline_breakdown": {},
                "approval_rate": 0
            }
        
        status_count = {}
        platform_count = {}
        priority_count = {}
        timeline_count = {}
        
        for p in proposals:
            # Status
            status = p.get("status", "unknown")
            status_count[status] = status_count.get(status, 0) + 1
            
            # Platforms
            for platform in p.get("platforms", []):
                platform_count[platform] = platform_count.get(platform, 0) + 1
            
            # Priority
            priority = p.get("priority", "unknown")
            priority_count[priority] = priority_count.get(priority, 0) + 1
            
            # Timeline
            timeline = p.get("timeline", "unknown")
            timeline_count[timeline] = timeline_count.get(timeline, 0) + 1
        
        approved = status_count.get("approved", 0)
        rejected = status_count.get("rejected", 0)
        total_reviewed = approved + rejected
        
        return {
            "total_proposals": len(proposals),
            "status_breakdown": status_count,
            "platform_breakdown": platform_count,
            "priority_breakdown": priority_count,
            "timeline_breakdown": timeline_count,
            "approval_rate": round(approved / total_reviewed * 100, 1) if total_reviewed > 0 else 0
        }
    
    def _calculate_comparative_analytics(
        self, 
        user_proposals: List[Dict], 
        platform_proposals: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate comparative analytics vs platform averages"""
        user_approved = sum(1 for p in user_proposals if p.get("status") == "approved")
        user_total = len([p for p in user_proposals if p.get("status") in ["approved", "rejected"]])
        user_approval_rate = (user_approved / user_total * 100) if user_total > 0 else 0
        
        platform_approved = sum(1 for p in platform_proposals if p.get("status") == "approved")
        platform_total = len([p for p in platform_proposals if p.get("status") in ["approved", "rejected"]])
        platform_approval_rate = (platform_approved / platform_total * 100) if platform_total > 0 else 0
        
        # Average processing time
        user_times = [p.get("arris_insights", {}).get("processing_time_seconds", 0) 
                     for p in user_proposals if p.get("arris_insights")]
        user_avg_time = sum(user_times) / len(user_times) if user_times else 0
        
        platform_times = [p.get("arris_insights", {}).get("processing_time_seconds", 0) 
                         for p in platform_proposals if p.get("arris_insights")]
        platform_avg_time = sum(platform_times) / len(platform_times) if platform_times else 0
        
        return {
            "your_approval_rate": round(user_approval_rate, 1),
            "platform_avg_approval_rate": round(platform_approval_rate, 1),
            "approval_rate_vs_platform": round(user_approval_rate - platform_approval_rate, 1),
            "your_avg_processing_time": round(user_avg_time, 2),
            "platform_avg_processing_time": round(platform_avg_time, 2),
            "your_total_proposals": len(user_proposals),
            "platform_total_proposals": len(platform_proposals)
        }
    
    def _calculate_arris_performance(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Calculate ARRIS performance metrics"""
        insights_count = 0
        complexity_counts = {}
        total_time = 0
        risk_levels = {}
        
        for p in proposals:
            insights = p.get("arris_insights", {})
            if insights:
                insights_count += 1
                
                complexity = insights.get("estimated_complexity", "unknown")
                complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
                
                total_time += insights.get("processing_time_seconds", 0)
                
                risk = insights.get("risk_assessment", {}).get("level", "unknown")
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        return {
            "proposals_with_insights": insights_count,
            "complexity_distribution": complexity_counts,
            "risk_distribution": risk_levels,
            "avg_processing_time_seconds": round(total_time / insights_count, 2) if insights_count > 0 else 0
        }
    
    def _analytics_to_csv(self, analytics: Dict, tier: str) -> Dict[str, Any]:
        """Convert analytics to CSV format"""
        output = io.StringIO()
        
        # Write summary section
        output.write("=== ANALYTICS SUMMARY ===\n")
        output.write(f"Total Proposals,{analytics['total_proposals']}\n")
        output.write(f"Approval Rate,{analytics['approval_rate']}%\n")
        output.write("\n")
        
        # Status breakdown
        output.write("=== STATUS BREAKDOWN ===\n")
        output.write("Status,Count\n")
        for status, count in analytics.get("status_breakdown", {}).items():
            output.write(f"{status},{count}\n")
        output.write("\n")
        
        # Platform breakdown
        output.write("=== PLATFORM BREAKDOWN ===\n")
        output.write("Platform,Count\n")
        for platform, count in analytics.get("platform_breakdown", {}).items():
            output.write(f"{platform},{count}\n")
        output.write("\n")
        
        # Priority breakdown
        output.write("=== PRIORITY BREAKDOWN ===\n")
        output.write("Priority,Count\n")
        for priority, count in analytics.get("priority_breakdown", {}).items():
            output.write(f"{priority},{count}\n")
        
        # Premium: Comparative analytics
        if tier == "premium" and "comparative" in analytics:
            output.write("\n=== COMPARATIVE ANALYTICS ===\n")
            comp = analytics["comparative"]
            output.write(f"Your Approval Rate,{comp['your_approval_rate']}%\n")
            output.write(f"Platform Avg Approval Rate,{comp['platform_avg_approval_rate']}%\n")
            output.write(f"Difference,{comp['approval_rate_vs_platform']}%\n")
            output.write(f"Your Avg Processing Time,{comp['your_avg_processing_time']}s\n")
            output.write(f"Platform Avg Processing Time,{comp['platform_avg_processing_time']}s\n")
        
        # Premium: ARRIS performance
        if tier == "premium" and "arris_performance" in analytics:
            output.write("\n=== ARRIS PERFORMANCE ===\n")
            arris = analytics["arris_performance"]
            output.write(f"Proposals with Insights,{arris['proposals_with_insights']}\n")
            output.write(f"Avg Processing Time,{arris['avg_processing_time_seconds']}s\n")
            output.write("\nComplexity Distribution\n")
            for complexity, count in arris.get("complexity_distribution", {}).items():
                output.write(f"{complexity},{count}\n")
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"analytics_{tier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "record_count": analytics["total_proposals"],
            "content_type": "text/csv"
        }
    
    def _analytics_to_json(self, analytics: Dict, date_range: str, tier: str) -> Dict[str, Any]:
        """Convert analytics to JSON format"""
        return {
            "format": "json",
            "data": analytics,
            "filename": f"analytics_{tier}_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "record_count": analytics["total_proposals"],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tier": tier,
            "content_type": "application/json"
        }
    
    # ============== REVENUE EXPORTS (Premium Only) ==============
    
    async def export_revenue_data(
        self,
        creator_id: str,
        format: str = "json",
        date_range: str = "30d"
    ) -> Dict[str, Any]:
        """
        Export revenue/calculator data for a creator.
        Premium tier only.
        """
        time_delta = self._get_time_delta(date_range)
        start_date = (datetime.now(timezone.utc) - time_delta).strftime("%Y-%m")
        
        entries = await self.db.calculator.find(
            {"user_id": creator_id, "month_year": {"$gte": start_date}},
            {"_id": 0}
        ).sort("month_year", -1).to_list(1000)
        
        # Calculate summary
        total_revenue = sum(e.get("revenue", 0) for e in entries)
        total_expenses = sum(e.get("expenses", 0) for e in entries)
        
        summary = {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(total_revenue - total_expenses, 2),
            "transaction_count": len(entries)
        }
        
        if format == "csv":
            return self._revenue_to_csv(entries, summary)
        return self._revenue_to_json(entries, summary, date_range)
    
    def _revenue_to_csv(self, entries: List[Dict], summary: Dict) -> Dict[str, Any]:
        """Convert revenue data to CSV format"""
        output = io.StringIO()
        
        # Summary
        output.write("=== REVENUE SUMMARY ===\n")
        output.write(f"Total Revenue,${summary['total_revenue']}\n")
        output.write(f"Total Expenses,${summary['total_expenses']}\n")
        output.write(f"Net Profit,${summary['net_profit']}\n")
        output.write(f"Transaction Count,{summary['transaction_count']}\n")
        output.write("\n")
        
        # Transactions
        output.write("=== TRANSACTIONS ===\n")
        if entries:
            fieldnames = ["id", "month_year", "category", "source", "revenue", "expenses", "net_margin"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for e in entries:
                writer.writerow({
                    "id": e.get("id"),
                    "month_year": e.get("month_year"),
                    "category": e.get("category"),
                    "source": e.get("source"),
                    "revenue": e.get("revenue", 0),
                    "expenses": e.get("expenses", 0),
                    "net_margin": e.get("net_margin", 0)
                })
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"revenue_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "record_count": len(entries),
            "content_type": "text/csv"
        }
    
    def _revenue_to_json(self, entries: List[Dict], summary: Dict, date_range: str) -> Dict[str, Any]:
        """Convert revenue data to JSON format"""
        return {
            "format": "json",
            "data": {
                "summary": summary,
                "transactions": entries
            },
            "filename": f"revenue_export_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "record_count": len(entries),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "content_type": "application/json"
        }
    
    # ============== HELPERS ==============
    
    def _get_time_delta(self, date_range: str) -> timedelta:
        """Convert date range string to timedelta"""
        ranges = {
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
            "1y": timedelta(days=365),
            "all": timedelta(days=3650)
        }
        return ranges.get(date_range, timedelta(days=30))


# Singleton instance
export_service: Optional[ExportService] = None
