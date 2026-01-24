"""
Scheduled ARRIS Reports Service for Creators Hive HQ
Phase 4 Module E - Task E2: Scheduled ARRIS Reports

Provides Elite creators with automated daily/weekly AI-generated summaries:
- Activity summaries (proposals, content, engagement)
- Key metrics and trends
- ARRIS usage statistics
- AI-powered insights and recommendations
- Pattern highlights from Pattern Engine

Features:
- Customizable report schedules (daily, weekly, or both)
- Topic selection for report focus
- Email delivery via SendGrid
- Report history and on-demand generation
- Report preview before sending
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import secrets
import json

logger = logging.getLogger(__name__)


class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BOTH = "both"
    NONE = "none"


class ReportTopic(str, Enum):
    ACTIVITY_SUMMARY = "activity_summary"
    METRICS_OVERVIEW = "metrics_overview"
    ARRIS_USAGE = "arris_usage"
    PATTERN_INSIGHTS = "pattern_insights"
    RECOMMENDATIONS = "recommendations"
    UPCOMING_TASKS = "upcoming_tasks"
    FINANCIAL_SUMMARY = "financial_summary"
    ENGAGEMENT_TRENDS = "engagement_trends"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"


# Default report configuration
DEFAULT_REPORT_CONFIG = {
    "frequency": ReportFrequency.WEEKLY.value,
    "daily_time": "08:00",  # UTC
    "weekly_day": "monday",  # Day of week
    "weekly_time": "09:00",  # UTC
    "topics": [
        ReportTopic.ACTIVITY_SUMMARY.value,
        ReportTopic.METRICS_OVERVIEW.value,
        ReportTopic.RECOMMENDATIONS.value,
    ],
    "include_charts": True,
    "email_format": "html",  # html or text
}


class ScheduledReportsService:
    """
    Manages scheduled ARRIS reports for Elite creators.
    Generates AI-powered summaries and delivers via email.
    """

    def __init__(self, db: AsyncIOMotorDatabase, llm_client=None, email_service=None):
        self.db = db
        self.llm_client = llm_client  # ARRIS service for AI summaries
        self.email_service = email_service

    # ============== REPORT SETTINGS ==============

    async def get_report_settings(self, creator_id: str) -> Dict[str, Any]:
        """Get creator's report preferences."""
        settings = await self.db.report_settings.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )

        if not settings:
            # Return defaults
            return {
                "creator_id": creator_id,
                "enabled": False,
                **DEFAULT_REPORT_CONFIG,
                "created_at": None,
                "updated_at": None
            }

        return settings

    async def update_report_settings(
        self,
        creator_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update report preferences."""
        now = datetime.now(timezone.utc)

        # Validate frequency
        if "frequency" in settings:
            if settings["frequency"] not in [f.value for f in ReportFrequency]:
                settings["frequency"] = ReportFrequency.WEEKLY.value

        # Validate topics
        if "topics" in settings:
            valid_topics = [t.value for t in ReportTopic]
            settings["topics"] = [t for t in settings["topics"] if t in valid_topics]

        # Validate weekly day
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if settings.get("weekly_day") and settings["weekly_day"].lower() not in valid_days:
            settings["weekly_day"] = "monday"

        update_data = {
            **settings,
            "creator_id": creator_id,
            "updated_at": now.isoformat()
        }

        await self.db.report_settings.update_one(
            {"creator_id": creator_id},
            {
                "$set": update_data,
                "$setOnInsert": {"created_at": now.isoformat()}
            },
            upsert=True
        )

        # Log the update
        await self._log_report_activity(
            creator_id=creator_id,
            action="settings_updated",
            details={"topics": settings.get("topics"), "frequency": settings.get("frequency")}
        )

        return await self.get_report_settings(creator_id)

    # ============== REPORT GENERATION ==============

    async def generate_report(
        self,
        creator_id: str,
        report_type: str = "weekly",
        send_email: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an AI-powered report for a creator.
        Can be triggered on-demand or by scheduler.
        """
        now = datetime.now(timezone.utc)
        report_id = f"RPT-{secrets.token_hex(6).upper()}"

        # Get creator info
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0, "name": 1, "email": 1, "tier": 1}
        )

        if not creator:
            return {"success": False, "error": "Creator not found"}

        # Get report settings
        settings = await self.get_report_settings(creator_id)
        topics = settings.get("topics", DEFAULT_REPORT_CONFIG["topics"])

        # Determine date range
        if report_type == "daily":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_label = "Yesterday"
        else:  # weekly
            start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_label = "This Week"

        # Create report record
        report_doc = {
            "id": report_id,
            "creator_id": creator_id,
            "creator_name": creator.get("name"),
            "creator_email": creator.get("email"),
            "report_type": report_type,
            "period_label": period_label,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "topics": topics,
            "status": ReportStatus.GENERATING.value,
            "sections": {},
            "ai_summary": None,
            "created_at": now.isoformat(),
            "sent_at": None,
            "error": None
        }

        await self.db.arris_reports.insert_one(report_doc)

        try:
            # Generate each section based on topics
            sections = {}

            if ReportTopic.ACTIVITY_SUMMARY.value in topics:
                sections["activity_summary"] = await self._generate_activity_summary(
                    creator_id, start_date, end_date
                )

            if ReportTopic.METRICS_OVERVIEW.value in topics:
                sections["metrics_overview"] = await self._generate_metrics_overview(
                    creator_id, start_date, end_date
                )

            if ReportTopic.ARRIS_USAGE.value in topics:
                sections["arris_usage"] = await self._generate_arris_usage(
                    creator_id, start_date, end_date
                )

            if ReportTopic.PATTERN_INSIGHTS.value in topics:
                sections["pattern_insights"] = await self._generate_pattern_insights(
                    creator_id, start_date, end_date
                )

            if ReportTopic.RECOMMENDATIONS.value in topics:
                sections["recommendations"] = await self._generate_recommendations(
                    creator_id, sections
                )

            if ReportTopic.UPCOMING_TASKS.value in topics:
                sections["upcoming_tasks"] = await self._generate_upcoming_tasks(creator_id)

            if ReportTopic.FINANCIAL_SUMMARY.value in topics:
                sections["financial_summary"] = await self._generate_financial_summary(
                    creator_id, start_date, end_date
                )

            if ReportTopic.ENGAGEMENT_TRENDS.value in topics:
                sections["engagement_trends"] = await self._generate_engagement_trends(
                    creator_id, start_date, end_date
                )

            # Generate AI executive summary
            ai_summary = await self._generate_ai_summary(creator, sections, period_label)

            # Update report with generated content
            await self.db.arris_reports.update_one(
                {"id": report_id},
                {
                    "$set": {
                        "sections": sections,
                        "ai_summary": ai_summary,
                        "status": ReportStatus.READY.value
                    }
                }
            )

            # Send email if requested
            if send_email and self.email_service:
                await self._send_report_email(report_id)

            # Log success
            await self._log_report_activity(
                creator_id=creator_id,
                action="report_generated",
                details={"report_id": report_id, "type": report_type}
            )

            return {
                "success": True,
                "report_id": report_id,
                "status": ReportStatus.READY.value,
                "sections_generated": list(sections.keys())
            }

        except Exception as e:
            logger.error(f"Report generation error for {creator_id}: {e}")

            await self.db.arris_reports.update_one(
                {"id": report_id},
                {
                    "$set": {
                        "status": ReportStatus.FAILED.value,
                        "error": str(e)
                    }
                }
            )

            return {"success": False, "error": str(e), "report_id": report_id}

    async def _generate_activity_summary(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate activity summary section."""
        # Count proposals
        proposals_count = await self.db.project_proposals.count_documents({
            "creator_id": creator_id,
            "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
        })

        # Count approved proposals
        approved_count = await self.db.project_proposals.count_documents({
            "creator_id": creator_id,
            "status": "approved",
            "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
        })

        # Count completed tasks
        tasks_completed = await self.db.tasks.count_documents({
            "assigned_to": creator_id,
            "status": "completed",
            "completed_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
        })

        # Memory entries
        memories_created = await self.db.arris_memory_palace.count_documents({
            "creator_id": creator_id,
            "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
        })

        return {
            "title": "Activity Summary",
            "proposals_created": proposals_count,
            "proposals_approved": approved_count,
            "tasks_completed": tasks_completed,
            "memories_created": memories_created,
            "highlight": f"You created {proposals_count} proposals and completed {tasks_completed} tasks this period."
        }

    async def _generate_metrics_overview(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate metrics overview section."""
        # Get calculator entries for the period
        pipeline = [
            {
                "$match": {
                    "user_id": creator_id,
                    "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$revenue"},
                    "total_expenses": {"$sum": "$expenses"},
                    "entry_count": {"$sum": 1}
                }
            }
        ]

        results = await self.db.calculator.aggregate(pipeline).to_list(1)
        metrics = results[0] if results else {"total_revenue": 0, "total_expenses": 0, "entry_count": 0}

        net_margin = metrics.get("total_revenue", 0) - metrics.get("total_expenses", 0)

        return {
            "title": "Metrics Overview",
            "revenue": round(metrics.get("total_revenue", 0), 2),
            "expenses": round(metrics.get("total_expenses", 0), 2),
            "net_margin": round(net_margin, 2),
            "transactions": metrics.get("entry_count", 0),
            "highlight": f"Net margin: ${net_margin:,.2f} from {metrics.get('entry_count', 0)} transactions."
        }

    async def _generate_arris_usage(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate ARRIS usage statistics."""
        # Count ARRIS interactions
        usage_count = await self.db.arris_usage_log.count_documents({
            "user_id": creator_id,
            "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
        })

        # Get category breakdown
        category_pipeline = [
            {
                "$match": {
                    "user_id": creator_id,
                    "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": "$query_category",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]

        categories = await self.db.arris_usage_log.aggregate(category_pipeline).to_list(5)
        top_category = categories[0]["_id"] if categories else "N/A"

        return {
            "title": "ARRIS Usage",
            "total_interactions": usage_count,
            "top_categories": [{"category": c["_id"], "count": c["count"]} for c in categories],
            "most_used": top_category,
            "highlight": f"You had {usage_count} ARRIS interactions. Most common: {top_category}."
        }

    async def _generate_pattern_insights(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate pattern insights from Pattern Engine."""
        # Get recent patterns
        patterns = await self.db.creator_patterns.find(
            {
                "creator_id": creator_id,
                "detected_at": {"$gte": start_date.isoformat()}
            },
            {"_id": 0}
        ).sort("confidence", -1).to_list(5)

        insights = []
        for p in patterns:
            insights.append({
                "type": p.get("pattern_type", "general"),
                "description": p.get("description", "Pattern detected"),
                "confidence": p.get("confidence", 0),
                "recommendation": p.get("recommendation", "")
            })

        return {
            "title": "Pattern Insights",
            "patterns_detected": len(patterns),
            "insights": insights,
            "highlight": f"{len(patterns)} patterns detected in your activity." if patterns else "No significant patterns detected this period."
        }

    async def _generate_recommendations(
        self,
        creator_id: str,
        other_sections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered recommendations based on data."""
        recommendations = []

        # Activity-based recommendations
        activity = other_sections.get("activity_summary", {})
        if activity.get("proposals_created", 0) == 0:
            recommendations.append({
                "priority": "high",
                "category": "growth",
                "title": "Create New Proposals",
                "description": "You haven't created any proposals this period. Consider brainstorming new project ideas."
            })

        # Metrics-based recommendations
        metrics = other_sections.get("metrics_overview", {})
        if metrics.get("net_margin", 0) < 0:
            recommendations.append({
                "priority": "high",
                "category": "financial",
                "title": "Review Expenses",
                "description": "Your net margin is negative. Review your expenses to improve profitability."
            })

        # ARRIS usage recommendations
        arris = other_sections.get("arris_usage", {})
        if arris.get("total_interactions", 0) < 5:
            recommendations.append({
                "priority": "medium",
                "category": "productivity",
                "title": "Use ARRIS More",
                "description": "Leverage ARRIS more frequently to get AI-powered insights and assistance."
            })

        # Default recommendation if none
        if not recommendations:
            recommendations.append({
                "priority": "low",
                "category": "general",
                "title": "Keep Up the Good Work",
                "description": "Your activity looks healthy. Keep building momentum!"
            })

        return {
            "title": "Recommendations",
            "count": len(recommendations),
            "items": recommendations,
            "highlight": f"{len(recommendations)} recommendations for your review."
        }

    async def _generate_upcoming_tasks(self, creator_id: str) -> Dict[str, Any]:
        """Generate upcoming tasks section."""
        now = datetime.now(timezone.utc)
        next_week = now + timedelta(days=7)

        tasks = await self.db.tasks.find(
            {
                "assigned_to": creator_id,
                "status": {"$in": ["pending", "in_progress"]},
                "due_date": {"$lte": next_week.isoformat()}
            },
            {"_id": 0, "title": 1, "due_date": 1, "priority": 1, "status": 1}
        ).sort("due_date", 1).to_list(10)

        return {
            "title": "Upcoming Tasks",
            "count": len(tasks),
            "tasks": tasks,
            "highlight": f"{len(tasks)} tasks due in the next 7 days." if tasks else "No upcoming tasks due."
        }

    async def _generate_financial_summary(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate financial summary section."""
        # Revenue by category
        category_pipeline = [
            {
                "$match": {
                    "user_id": creator_id,
                    "created_at": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "revenue": {"$sum": "$revenue"},
                    "expenses": {"$sum": "$expenses"}
                }
            },
            {"$sort": {"revenue": -1}}
        ]

        by_category = await self.db.calculator.aggregate(category_pipeline).to_list(10)

        total_revenue = sum(c.get("revenue", 0) for c in by_category)
        total_expenses = sum(c.get("expenses", 0) for c in by_category)

        return {
            "title": "Financial Summary",
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_profit": round(total_revenue - total_expenses, 2),
            "by_category": [
                {"category": c["_id"], "revenue": round(c.get("revenue", 0), 2)}
                for c in by_category if c["_id"]
            ],
            "highlight": f"Total revenue: ${total_revenue:,.2f}, Net profit: ${total_revenue - total_expenses:,.2f}"
        }

    async def _generate_engagement_trends(
        self,
        creator_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate engagement trends section."""
        # Daily activity counts
        daily_pipeline = [
            {
                "$match": {
                    "user_id": creator_id,
                    "timestamp": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": {"$substr": ["$timestamp", 0, 10]},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        daily_activity = await self.db.arris_usage_log.aggregate(daily_pipeline).to_list(30)

        # Calculate trend
        if len(daily_activity) >= 2:
            first_half = sum(d["count"] for d in daily_activity[:len(daily_activity)//2])
            second_half = sum(d["count"] for d in daily_activity[len(daily_activity)//2:])
            trend = "increasing" if second_half > first_half else "decreasing" if second_half < first_half else "stable"
        else:
            trend = "insufficient data"

        return {
            "title": "Engagement Trends",
            "daily_data": [{"date": d["_id"], "interactions": d["count"]} for d in daily_activity],
            "trend": trend,
            "peak_day": max(daily_activity, key=lambda x: x["count"])["_id"] if daily_activity else "N/A",
            "highlight": f"Engagement trend: {trend}."
        }

    async def _generate_ai_summary(
        self,
        creator: Dict[str, Any],
        sections: Dict[str, Any],
        period_label: str
    ) -> str:
        """Generate AI executive summary using ARRIS."""
        if not self.llm_client:
            # Fallback to template-based summary
            return self._generate_template_summary(creator, sections, period_label)

        try:
            # Build context for AI
            context = f"""
            Generate a brief, encouraging executive summary for {creator.get('name', 'Creator')}'s {period_label} report.
            
            Key metrics:
            - Activity: {sections.get('activity_summary', {}).get('highlight', 'No data')}
            - Metrics: {sections.get('metrics_overview', {}).get('highlight', 'No data')}
            - ARRIS Usage: {sections.get('arris_usage', {}).get('highlight', 'No data')}
            
            Keep it concise (2-3 sentences), professional yet friendly, and end with encouragement.
            """

            response = await self.llm_client.generate_response(
                prompt=context,
                max_tokens=200
            )
            return response.get("content", self._generate_template_summary(creator, sections, period_label))

        except Exception as e:
            logger.error(f"AI summary generation error: {e}")
            return self._generate_template_summary(creator, sections, period_label)

    def _generate_template_summary(
        self,
        creator: Dict[str, Any],
        sections: Dict[str, Any],
        period_label: str
    ) -> str:
        """Generate template-based summary as fallback."""
        name = creator.get("name", "Creator")
        activity = sections.get("activity_summary", {})
        metrics = sections.get("metrics_overview", {})

        proposals = activity.get("proposals_created", 0)
        tasks = activity.get("tasks_completed", 0)
        revenue = metrics.get("revenue", 0)

        return f"""Hi {name}! Here's your {period_label.lower()} summary: You created {proposals} proposal(s) and completed {tasks} task(s), with ${revenue:,.2f} in revenue tracked. Keep building your creator empire – every step counts toward your goals!"""

    # ============== EMAIL DELIVERY ==============

    async def _send_report_email(self, report_id: str) -> bool:
        """Send report via email."""
        report = await self.db.arris_reports.find_one(
            {"id": report_id},
            {"_id": 0}
        )

        if not report:
            return False

        if not self.email_service:
            logger.warning("Email service not configured, skipping email delivery")
            return False

        try:
            # Build email content
            html_content = self._build_email_html(report)

            # Send via email service
            await self.email_service.send_email(
                to_email=report["creator_email"],
                subject=f"Your ARRIS {report['report_type'].title()} Report - {report['period_label']}",
                html_content=html_content
            )

            # Update report status
            await self.db.arris_reports.update_one(
                {"id": report_id},
                {
                    "$set": {
                        "status": ReportStatus.SENT.value,
                        "sent_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )

            await self._log_report_activity(
                creator_id=report["creator_id"],
                action="report_sent",
                details={"report_id": report_id, "email": report["creator_email"]}
            )

            return True

        except Exception as e:
            logger.error(f"Email delivery error for report {report_id}: {e}")
            await self.db.arris_reports.update_one(
                {"id": report_id},
                {"$set": {"error": f"Email delivery failed: {str(e)}"}}
            )
            return False

    def _build_email_html(self, report: Dict[str, Any]) -> str:
        """Build HTML email content for report."""
        sections_html = ""

        for key, section in report.get("sections", {}).items():
            if isinstance(section, dict):
                sections_html += f"""
                <div style="margin-bottom: 24px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
                    <h3 style="color: #6b46c1; margin: 0 0 12px 0;">{section.get('title', key.replace('_', ' ').title())}</h3>
                    <p style="color: #4a5568; margin: 0;">{section.get('highlight', '')}</p>
                </div>
                """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ARRIS Report</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #ffffff;">
            <div style="text-align: center; margin-bottom: 32px;">
                <h1 style="color: #6b46c1; margin: 0;">Creators Hive HQ</h1>
                <p style="color: #718096; margin: 8px 0 0 0;">Your ARRIS {report.get('report_type', 'Weekly').title()} Report</p>
            </div>
            
            <div style="background: linear-gradient(135deg, #6b46c1 0%, #805ad5 100%); color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                <h2 style="margin: 0 0 8px 0;">Hi {report.get('creator_name', 'Creator')}! 👋</h2>
                <p style="margin: 0; opacity: 0.9;">{report.get('period_label', 'This Period')} Summary</p>
            </div>
            
            <div style="background: #faf5ff; padding: 16px; border-radius: 8px; margin-bottom: 24px; border-left: 4px solid #6b46c1;">
                <p style="margin: 0; color: #553c9a; font-style: italic;">
                    {report.get('ai_summary', 'Your activity summary is ready!')}
                </p>
            </div>
            
            {sections_html}
            
            <div style="text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid #e2e8f0;">
                <p style="color: #718096; font-size: 14px; margin: 0;">
                    Powered by ARRIS • Creators Hive HQ
                </p>
                <p style="color: #a0aec0; font-size: 12px; margin: 8px 0 0 0;">
                    Manage your report preferences in your Elite dashboard
                </p>
            </div>
        </body>
        </html>
        """

    # ============== REPORT HISTORY ==============

    async def get_report_history(
        self,
        creator_id: str,
        limit: int = 20,
        report_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get creator's report history."""
        query = {"creator_id": creator_id}
        if report_type:
            query["report_type"] = report_type

        reports = await self.db.arris_reports.find(
            query,
            {"_id": 0, "sections": 0}  # Exclude large sections for list view
        ).sort("created_at", -1).to_list(limit)

        return reports

    async def get_report(self, creator_id: str, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific report."""
        report = await self.db.arris_reports.find_one(
            {"id": report_id, "creator_id": creator_id},
            {"_id": 0}
        )
        return report

    async def delete_report(self, creator_id: str, report_id: str) -> bool:
        """Delete a report."""
        result = await self.db.arris_reports.delete_one(
            {"id": report_id, "creator_id": creator_id}
        )
        return result.deleted_count > 0

    # ============== SCHEDULER SUPPORT ==============

    async def get_creators_for_daily_reports(self) -> List[Dict[str, Any]]:
        """Get creators who should receive daily reports now."""
        current_hour = datetime.now(timezone.utc).strftime("%H:00")

        creators = await self.db.report_settings.find(
            {
                "enabled": True,
                "frequency": {"$in": [ReportFrequency.DAILY.value, ReportFrequency.BOTH.value]},
                "daily_time": current_hour
            },
            {"_id": 0, "creator_id": 1}
        ).to_list(1000)

        return creators

    async def get_creators_for_weekly_reports(self) -> List[Dict[str, Any]]:
        """Get creators who should receive weekly reports now."""
        current_day = datetime.now(timezone.utc).strftime("%A").lower()
        current_hour = datetime.now(timezone.utc).strftime("%H:00")

        creators = await self.db.report_settings.find(
            {
                "enabled": True,
                "frequency": {"$in": [ReportFrequency.WEEKLY.value, ReportFrequency.BOTH.value]},
                "weekly_day": current_day,
                "weekly_time": current_hour
            },
            {"_id": 0, "creator_id": 1}
        ).to_list(1000)

        return creators

    # ============== ACTIVITY LOGGING ==============

    async def _log_report_activity(
        self,
        creator_id: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Log report-related activity."""
        log_entry = {
            "creator_id": creator_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.report_activity_log.insert_one(log_entry)


# Export constants
AVAILABLE_TOPICS = [t.value for t in ReportTopic]
AVAILABLE_FREQUENCIES = [f.value for f in ReportFrequency]

# Singleton instance
scheduled_reports_service: Optional[ScheduledReportsService] = None
