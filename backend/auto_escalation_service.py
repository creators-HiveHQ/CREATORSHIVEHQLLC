"""
Auto-Escalation Service (Module B5)
===================================
Automatically escalates stalled proposals for admin review.
Monitors proposal status, tracks time in each stage, and escalates
when thresholds are exceeded.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

logger = logging.getLogger(__name__)


# Escalation levels
class EscalationLevel:
    STANDARD = "standard"           # Normal review queue
    ELEVATED = "elevated"           # Needs attention soon
    URGENT = "urgent"               # Requires immediate attention
    CRITICAL = "critical"           # Overdue, executive attention


# Escalation reasons
class EscalationReason:
    REVIEW_TIMEOUT = "review_timeout"           # Pending review too long
    APPROVAL_STALLED = "approval_stalled"       # Approved but not started
    IN_PROGRESS_STALLED = "in_progress_stalled" # In progress but no activity
    FEEDBACK_PENDING = "feedback_pending"       # Waiting for creator feedback
    ADMIN_ATTENTION = "admin_attention"         # Manually flagged
    PATTERN_DETECTED = "pattern_detected"       # ARRIS detected an issue
    HIGH_VALUE = "high_value"                   # High-value proposal needs attention


# Default escalation thresholds (in hours)
DEFAULT_THRESHOLDS = {
    "submitted": {
        EscalationLevel.ELEVATED: 48,    # 2 days
        EscalationLevel.URGENT: 96,      # 4 days
        EscalationLevel.CRITICAL: 168    # 7 days
    },
    "under_review": {
        EscalationLevel.ELEVATED: 72,    # 3 days
        EscalationLevel.URGENT: 120,     # 5 days
        EscalationLevel.CRITICAL: 168    # 7 days
    },
    "approved": {
        EscalationLevel.ELEVATED: 168,   # 7 days (not started project)
        EscalationLevel.URGENT: 336,     # 14 days
        EscalationLevel.CRITICAL: 504    # 21 days
    },
    "in_progress": {
        EscalationLevel.ELEVATED: 336,   # 14 days no activity
        EscalationLevel.URGENT: 504,     # 21 days
        EscalationLevel.CRITICAL: 720    # 30 days
    },
    "needs_revision": {
        EscalationLevel.ELEVATED: 120,   # 5 days
        EscalationLevel.URGENT: 168,     # 7 days
        EscalationLevel.CRITICAL: 336    # 14 days
    }
}


# Actions for each escalation level
ESCALATION_ACTIONS = {
    EscalationLevel.ELEVATED: {
        "notify_admin": True,
        "notify_creator": False,
        "priority_boost": 1,
        "dashboard_highlight": "yellow"
    },
    EscalationLevel.URGENT: {
        "notify_admin": True,
        "notify_creator": True,
        "priority_boost": 2,
        "dashboard_highlight": "orange",
        "create_task": True
    },
    EscalationLevel.CRITICAL: {
        "notify_admin": True,
        "notify_creator": True,
        "priority_boost": 3,
        "dashboard_highlight": "red",
        "create_task": True,
        "executive_alert": True
    }
}


class AutoEscalationService:
    """
    Service for automatically escalating stalled proposals.
    Monitors proposal status duration and triggers escalation actions.
    """
    
    def __init__(
        self,
        db,
        ws_manager=None,
        notification_service=None,
        email_service=None
    ):
        self.db = db
        self.ws_manager = ws_manager
        self.notification_service = notification_service
        self.email_service = email_service
        self.thresholds = DEFAULT_THRESHOLDS.copy()
    
    async def initialize(self):
        """Initialize the service and load custom thresholds."""
        # Load custom thresholds from database if they exist
        config = await self.db.escalation_config.find_one({"type": "thresholds"})
        if config:
            self.thresholds.update(config.get("thresholds", {}))
            logger.info("Loaded custom escalation thresholds from database")
        
        # Ensure indexes
        await self.db.escalation_log.create_index([("proposal_id", 1)])
        await self.db.escalation_log.create_index([("created_at", -1)])
        await self.db.escalation_log.create_index([("level", 1)])
        await self.db.escalation_log.create_index([("resolved", 1)])
        
        logger.info("Auto-Escalation Service initialized")
    
    async def get_config(self) -> Dict[str, Any]:
        """Get current escalation configuration."""
        return {
            "thresholds": self.thresholds,
            "actions": ESCALATION_ACTIONS,
            "monitored_statuses": list(self.thresholds.keys())
        }
    
    async def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update escalation configuration."""
        if "thresholds" in updates:
            self.thresholds.update(updates["thresholds"])
            
            # Persist to database
            await self.db.escalation_config.update_one(
                {"type": "thresholds"},
                {"$set": {
                    "thresholds": self.thresholds,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        return await self.get_config()
    
    async def check_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Check a single proposal for escalation needs.
        Returns escalation status and recommended actions.
        """
        proposal = await self.db.proposals.find_one(
            {"proposal_id": proposal_id},
            {"_id": 0}
        )
        
        if not proposal:
            return {"error": "Proposal not found", "needs_escalation": False}
        
        status = proposal.get("status", "draft")
        
        # Skip statuses that don't need monitoring
        if status not in self.thresholds:
            return {
                "proposal_id": proposal_id,
                "status": status,
                "needs_escalation": False,
                "reason": "Status not monitored"
            }
        
        # Calculate time in current status
        status_history = proposal.get("status_history", [])
        last_status_change = proposal.get("updated_at") or proposal.get("created_at")
        
        if status_history:
            # Find the most recent status change
            for entry in reversed(status_history):
                if entry.get("status") == status:
                    last_status_change = entry.get("changed_at", last_status_change)
                    break
        
        # Parse the timestamp
        if isinstance(last_status_change, str):
            last_change_dt = datetime.fromisoformat(last_status_change.replace("Z", "+00:00"))
        else:
            last_change_dt = last_status_change
        
        now = datetime.now(timezone.utc)
        hours_in_status = (now - last_change_dt).total_seconds() / 3600
        
        # Determine escalation level
        status_thresholds = self.thresholds.get(status, {})
        escalation_level = None
        
        # Check from highest to lowest level
        for level in [EscalationLevel.CRITICAL, EscalationLevel.URGENT, EscalationLevel.ELEVATED]:
            threshold = status_thresholds.get(level)
            if threshold and hours_in_status >= threshold:
                escalation_level = level
                break
        
        if not escalation_level:
            return {
                "proposal_id": proposal_id,
                "status": status,
                "hours_in_status": round(hours_in_status, 1),
                "needs_escalation": False,
                "next_escalation": self._get_next_escalation(status, hours_in_status)
            }
        
        # Check if already escalated to this level
        existing = await self.db.escalation_log.find_one({
            "proposal_id": proposal_id,
            "level": escalation_level,
            "resolved": False
        })
        
        return {
            "proposal_id": proposal_id,
            "status": status,
            "hours_in_status": round(hours_in_status, 1),
            "needs_escalation": existing is None,
            "escalation_level": escalation_level,
            "already_escalated": existing is not None,
            "existing_escalation_id": existing.get("escalation_id") if existing else None,
            "actions": ESCALATION_ACTIONS.get(escalation_level, {}),
            "creator_id": proposal.get("user_id"),
            "proposal_title": proposal.get("title")
        }
    
    async def escalate_proposal(
        self,
        proposal_id: str,
        level: str = None,
        reason: str = None,
        notes: str = None,
        escalated_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Escalate a proposal to a specific level.
        If level is not provided, it will be auto-determined.
        """
        # Check proposal status
        check_result = await self.check_proposal(proposal_id)
        
        if check_result.get("error"):
            return {"success": False, "error": check_result["error"]}
        
        # Use provided level or auto-determined level
        escalation_level = level or check_result.get("escalation_level", EscalationLevel.ELEVATED)
        
        if not escalation_level:
            return {
                "success": False,
                "error": "No escalation needed",
                "details": check_result
            }
        
        # Create escalation record
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        escalation_record = {
            "escalation_id": escalation_id,
            "proposal_id": proposal_id,
            "proposal_title": check_result.get("proposal_title"),
            "creator_id": check_result.get("creator_id"),
            "status": check_result.get("status"),
            "level": escalation_level,
            "reason": reason or EscalationReason.REVIEW_TIMEOUT,
            "notes": notes,
            "hours_in_status": check_result.get("hours_in_status"),
            "escalated_by": escalated_by,
            "actions_taken": [],
            "resolved": False,
            "resolved_at": None,
            "resolved_by": None,
            "resolution_notes": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.escalation_log.insert_one(escalation_record)
        
        # Execute escalation actions
        actions = ESCALATION_ACTIONS.get(escalation_level, {})
        actions_taken = []
        
        if actions.get("notify_admin") and self.notification_service:
            await self._notify_admin(escalation_record)
            actions_taken.append("admin_notified")
        
        if actions.get("notify_creator") and self.notification_service:
            await self._notify_creator(escalation_record)
            actions_taken.append("creator_notified")
        
        if actions.get("create_task"):
            await self._create_escalation_task(escalation_record)
            actions_taken.append("task_created")
        
        if actions.get("priority_boost"):
            await self._boost_priority(proposal_id, actions["priority_boost"])
            actions_taken.append(f"priority_boosted_by_{actions['priority_boost']}")
        
        # Update escalation record with actions taken
        await self.db.escalation_log.update_one(
            {"escalation_id": escalation_id},
            {"$set": {"actions_taken": actions_taken}}
        )
        
        # Create webhook event
        await self._create_webhook_event(escalation_record)
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "level": escalation_level,
            "proposal_id": proposal_id,
            "actions_taken": actions_taken
        }
    
    async def resolve_escalation(
        self,
        escalation_id: str,
        resolved_by: str,
        resolution_notes: str = None
    ) -> Dict[str, Any]:
        """Resolve an escalation."""
        result = await self.db.escalation_log.update_one(
            {"escalation_id": escalation_id, "resolved": False},
            {"$set": {
                "resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes
            }}
        )
        
        if result.modified_count == 0:
            return {"success": False, "error": "Escalation not found or already resolved"}
        
        return {"success": True, "escalation_id": escalation_id, "resolved": True}
    
    async def scan_all_proposals(self) -> Dict[str, Any]:
        """
        Scan all proposals for escalation needs.
        This should be run periodically (e.g., hourly via cron).
        """
        results = {
            "scanned": 0,
            "needs_escalation": 0,
            "escalated": 0,
            "errors": [],
            "escalations": []
        }
        
        # Find all proposals in monitored statuses
        proposals = await self.db.proposals.find(
            {"status": {"$in": list(self.thresholds.keys())}},
            {"proposal_id": 1, "_id": 0}
        ).to_list(1000)
        
        results["scanned"] = len(proposals)
        
        for proposal in proposals:
            proposal_id = proposal.get("proposal_id")
            if not proposal_id:
                continue
            
            try:
                check = await self.check_proposal(proposal_id)
                
                if check.get("needs_escalation"):
                    results["needs_escalation"] += 1
                    
                    # Auto-escalate
                    escalation = await self.escalate_proposal(
                        proposal_id=proposal_id,
                        reason=EscalationReason.REVIEW_TIMEOUT
                    )
                    
                    if escalation.get("success"):
                        results["escalated"] += 1
                        results["escalations"].append(escalation)
                        
            except Exception as e:
                logger.error(f"Error checking proposal {proposal_id}: {e}")
                results["errors"].append({"proposal_id": proposal_id, "error": str(e)})
        
        # Log scan results
        await self.db.escalation_scan_log.insert_one({
            "scan_id": f"SCAN-{uuid.uuid4().hex[:8].upper()}",
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "results": results
        })
        
        return results
    
    async def get_escalation_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data for escalation management."""
        now = datetime.now(timezone.utc)
        
        # Count by level
        level_counts = {}
        for level in [EscalationLevel.CRITICAL, EscalationLevel.URGENT, EscalationLevel.ELEVATED]:
            count = await self.db.escalation_log.count_documents({
                "level": level,
                "resolved": False
            })
            level_counts[level] = count
        
        # Total active escalations
        total_active = sum(level_counts.values())
        
        # Resolved in last 24 hours
        yesterday = now - timedelta(hours=24)
        resolved_24h = await self.db.escalation_log.count_documents({
            "resolved": True,
            "resolved_at": {"$gte": yesterday.isoformat()}
        })
        
        # Average time to resolution (last 7 days)
        week_ago = now - timedelta(days=7)
        resolved_week = await self.db.escalation_log.find({
            "resolved": True,
            "resolved_at": {"$gte": week_ago.isoformat()}
        }).to_list(100)
        
        avg_resolution_hours = 0
        if resolved_week:
            resolution_times = []
            for esc in resolved_week:
                try:
                    created = datetime.fromisoformat(esc["created_at"].replace("Z", "+00:00"))
                    resolved = datetime.fromisoformat(esc["resolved_at"].replace("Z", "+00:00"))
                    hours = (resolved - created).total_seconds() / 3600
                    resolution_times.append(hours)
                except:
                    pass
            if resolution_times:
                avg_resolution_hours = sum(resolution_times) / len(resolution_times)
        
        # Get recent escalations
        recent = await self.db.escalation_log.find(
            {"resolved": False},
            {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        return {
            "summary": {
                "total_active": total_active,
                "by_level": level_counts,
                "resolved_24h": resolved_24h,
                "avg_resolution_hours": round(avg_resolution_hours, 1)
            },
            "active_escalations": recent,
            "health_status": self._calculate_health_status(level_counts)
        }
    
    async def get_escalation_history(
        self,
        limit: int = 50,
        include_resolved: bool = True,
        level_filter: str = None,
        proposal_id: str = None
    ) -> Dict[str, Any]:
        """Get escalation history with filters."""
        query = {}
        
        if not include_resolved:
            query["resolved"] = False
        
        if level_filter:
            query["level"] = level_filter
        
        if proposal_id:
            query["proposal_id"] = proposal_id
        
        escalations = await self.db.escalation_log.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "escalations": escalations,
            "total": len(escalations),
            "filters_applied": {
                "include_resolved": include_resolved,
                "level_filter": level_filter,
                "proposal_id": proposal_id
            }
        }
    
    async def get_stalled_proposals(self, threshold_hours: int = 48) -> Dict[str, Any]:
        """
        Get all proposals that are stalled (nearing escalation).
        Useful for proactive admin monitoring.
        """
        stalled = []
        
        proposals = await self.db.proposals.find(
            {"status": {"$in": list(self.thresholds.keys())}},
            {"_id": 0}
        ).to_list(1000)
        
        for proposal in proposals:
            # Support both 'id' and 'proposal_id' field names
            proposal_id = proposal.get("proposal_id") or proposal.get("id")
            check = await self.check_proposal(proposal_id)
            
            if check.get("hours_in_status", 0) >= threshold_hours:
                stalled.append({
                    "proposal_id": proposal_id,
                    "title": proposal.get("title"),
                    "status": proposal.get("status"),
                    "creator_id": proposal.get("user_id"),
                    "hours_stalled": check.get("hours_in_status"),
                    "escalation_level": check.get("escalation_level"),
                    "already_escalated": check.get("already_escalated", False)
                })
        
        # Sort by hours stalled (most urgent first)
        stalled.sort(key=lambda x: x.get("hours_stalled", 0), reverse=True)
        
        return {
            "stalled_proposals": stalled,
            "total": len(stalled),
            "threshold_hours": threshold_hours
        }
    
    async def get_escalation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics for escalation performance."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total escalations in period
        total = await self.db.escalation_log.count_documents({
            "created_at": {"$gte": cutoff.isoformat()}
        })
        
        # By level
        by_level = {}
        for level in [EscalationLevel.ELEVATED, EscalationLevel.URGENT, EscalationLevel.CRITICAL]:
            count = await self.db.escalation_log.count_documents({
                "level": level,
                "created_at": {"$gte": cutoff.isoformat()}
            })
            by_level[level] = count
        
        # By reason
        reason_pipeline = [
            {"$match": {"created_at": {"$gte": cutoff.isoformat()}}},
            {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        reason_stats = await self.db.escalation_log.aggregate(reason_pipeline).to_list(10)
        by_reason = {r["_id"]: r["count"] for r in reason_stats if r["_id"]}
        
        # Resolution rate
        resolved = await self.db.escalation_log.count_documents({
            "created_at": {"$gte": cutoff.isoformat()},
            "resolved": True
        })
        resolution_rate = (resolved / total * 100) if total > 0 else 0
        
        # Average time to escalation by status
        time_to_escalation = {}
        for status in self.thresholds.keys():
            pipeline = [
                {"$match": {
                    "status": status,
                    "created_at": {"$gte": cutoff.isoformat()}
                }},
                {"$group": {
                    "_id": None,
                    "avg_hours": {"$avg": "$hours_in_status"}
                }}
            ]
            result = await self.db.escalation_log.aggregate(pipeline).to_list(1)
            if result:
                time_to_escalation[status] = round(result[0].get("avg_hours", 0), 1)
        
        return {
            "period_days": days,
            "total_escalations": total,
            "by_level": by_level,
            "by_reason": by_reason,
            "resolution_rate": round(resolution_rate, 1),
            "resolved_count": resolved,
            "avg_time_to_escalation_by_status": time_to_escalation
        }
    
    # ============== PRIVATE HELPER METHODS ==============
    
    def _get_next_escalation(self, status: str, current_hours: float) -> Optional[Dict[str, Any]]:
        """Get info about when the next escalation will occur."""
        status_thresholds = self.thresholds.get(status, {})
        
        for level in [EscalationLevel.ELEVATED, EscalationLevel.URGENT, EscalationLevel.CRITICAL]:
            threshold = status_thresholds.get(level)
            if threshold and current_hours < threshold:
                return {
                    "level": level,
                    "hours_until": round(threshold - current_hours, 1),
                    "threshold_hours": threshold
                }
        
        return None
    
    def _calculate_health_status(self, level_counts: Dict[str, int]) -> str:
        """Calculate overall escalation health status."""
        critical = level_counts.get(EscalationLevel.CRITICAL, 0)
        urgent = level_counts.get(EscalationLevel.URGENT, 0)
        elevated = level_counts.get(EscalationLevel.ELEVATED, 0)
        
        if critical > 0:
            return "critical"
        elif urgent >= 3:
            return "poor"
        elif urgent > 0 or elevated >= 5:
            return "needs_attention"
        elif elevated > 0:
            return "fair"
        else:
            return "healthy"
    
    async def _notify_admin(self, escalation: Dict[str, Any]):
        """Send admin notification for escalation."""
        if not self.notification_service:
            logger.warning("Notification service not available for admin escalation alert")
            return
        
        try:
            await self.notification_service.broadcast_to_admins({
                "type": "escalation.created",
                "escalation_id": escalation.get("escalation_id"),
                "proposal_id": escalation.get("proposal_id"),
                "proposal_title": escalation.get("proposal_title"),
                "level": escalation.get("level"),
                "reason": escalation.get("reason"),
                "hours_in_status": escalation.get("hours_in_status"),
                "message": f"Proposal '{escalation.get('proposal_title')}' escalated to {escalation.get('level')} level",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to notify admins about escalation: {e}")
    
    async def _notify_creator(self, escalation: Dict[str, Any]):
        """Send creator notification about their escalated proposal."""
        if not self.notification_service:
            return
        
        creator_id = escalation.get("creator_id")
        if not creator_id:
            return
        
        try:
            await self.notification_service.send_to_user(
                user_id=creator_id,
                user_type="creator",
                notification={
                    "type": "proposal.escalated",
                    "proposal_id": escalation.get("proposal_id"),
                    "proposal_title": escalation.get("proposal_title"),
                    "level": escalation.get("level"),
                    "message": f"Your proposal '{escalation.get('proposal_title')}' needs attention",
                    "action_required": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to notify creator about escalation: {e}")
    
    async def _create_escalation_task(self, escalation: Dict[str, Any]):
        """Create a task for the escalated proposal."""
        task = {
            "task_id": f"TASK-ESC-{uuid.uuid4().hex[:6].upper()}",
            "title": f"Review Escalated Proposal: {escalation.get('proposal_title', 'Unknown')}",
            "description": f"Proposal has been in '{escalation.get('status')}' status for {escalation.get('hours_in_status')} hours. Escalation level: {escalation.get('level')}",
            "type": "escalation_review",
            "priority": "high" if escalation.get("level") == EscalationLevel.CRITICAL else "medium",
            "status": "pending",
            "related_proposal_id": escalation.get("proposal_id"),
            "related_escalation_id": escalation.get("escalation_id"),
            "assigned_to": None,  # Admin assignment needed
            "created_at": datetime.now(timezone.utc).isoformat(),
            "due_date": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
        
        await self.db.tasks.insert_one(task)
        logger.info(f"Created escalation task {task['task_id']} for proposal {escalation.get('proposal_id')}")
    
    async def _boost_priority(self, proposal_id: str, boost_amount: int):
        """Boost the priority of an escalated proposal."""
        # Update proposal with priority boost
        await self.db.proposals.update_one(
            {"proposal_id": proposal_id},
            {
                "$set": {"escalation_priority_boost": boost_amount},
                "$push": {
                    "status_history": {
                        "action": "priority_boosted",
                        "boost_amount": boost_amount,
                        "changed_at": datetime.now(timezone.utc).isoformat(),
                        "changed_by": "auto_escalation"
                    }
                }
            }
        )
    
    async def _create_webhook_event(self, escalation: Dict[str, Any]):
        """Create a webhook event for the escalation."""
        event = {
            "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "event_type": "proposal.escalated",
            "payload": {
                "escalation_id": escalation.get("escalation_id"),
                "proposal_id": escalation.get("proposal_id"),
                "creator_id": escalation.get("creator_id"),
                "level": escalation.get("level"),
                "reason": escalation.get("reason"),
                "status": escalation.get("status")
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "processed": False
        }
        
        await self.db.webhook_events.insert_one(event)
