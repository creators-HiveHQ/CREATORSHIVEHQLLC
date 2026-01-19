"""
Creators Hive HQ - Webhook Service
Zero-Human Operational Model - Event Processing & Automation
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
import uuid

from models_webhook import (
    WebhookEvent, WebhookEventCreate, WebhookEventType,
    AutomationRule, DEFAULT_AUTOMATION_RULES, FOLLOW_UP_ACTIONS
)

logger = logging.getLogger(__name__)

class WebhookService:
    """
    Webhook Automation Service for Zero-Human Ops
    Processes events and triggers automated actions
    """
    
    def __init__(self, db=None):
        self.db = db
        self.automation_rules: Dict[str, AutomationRule] = {}
        self.action_handlers: Dict[str, Callable] = {}
        self._initialized = False
    
    async def initialize(self, db):
        """Initialize the webhook service with database"""
        self.db = db
        await self._load_automation_rules()
        self._register_default_handlers()
        self._initialized = True
        logger.info("Webhook Service initialized - Zero-Human Ops active")
    
    async def _load_automation_rules(self):
        """Load automation rules from database or defaults"""
        # Check if rules exist in DB
        existing = await self.db.automation_rules.count_documents({})
        
        if existing == 0:
            # Seed default rules
            for rule_data in DEFAULT_AUTOMATION_RULES:
                rule_data["created_at"] = datetime.now(timezone.utc).isoformat()
                await self.db.automation_rules.insert_one(rule_data)
            logger.info(f"Seeded {len(DEFAULT_AUTOMATION_RULES)} default automation rules")
        
        # Load rules into memory
        rules = await self.db.automation_rules.find({"is_active": True}).to_list(100)
        for rule in rules:
            self.automation_rules[rule["event_type"]] = rule
        
        logger.info(f"Loaded {len(self.automation_rules)} active automation rules")
    
    def _register_default_handlers(self):
        """Register default action handlers"""
        self.action_handlers = {
            "log_event": self._handle_log_event,
            "update_arris_memory": self._handle_update_arris_memory,
            "create_welcome_task": self._handle_create_welcome_task,
            "create_onboarding_project": self._handle_create_onboarding_project,
            "queue_for_review": self._handle_queue_for_review,
            "create_project_tasks": self._handle_create_project_tasks,
            "initialize_project_tracking": self._handle_initialize_tracking,
            "check_project_completion": self._handle_check_completion,
            "update_financial_patterns": self._handle_update_financial_patterns,
            "create_insight_notification": self._handle_create_notification,
            "send_notification": self._handle_send_notification,
        }
    
    # ============== EVENT EMISSION ==============
    
    async def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source_entity: str = "",
        source_id: str = "",
        user_id: Optional[str] = None
    ) -> WebhookEvent:
        """
        Emit a webhook event and process it
        This is the main entry point for triggering automations
        """
        if not self._initialized:
            logger.warning("Webhook service not initialized, skipping event")
            return None
        
        # Create event record
        event = WebhookEvent(
            event_type=event_type,
            payload=payload,
            source_entity=source_entity,
            source_id=source_id,
            user_id=user_id,
            status="pending"
        )
        
        # Store event
        event_doc = event.model_dump()
        event_doc['timestamp'] = event_doc['timestamp'].isoformat()
        await self.db.webhook_events.insert_one(event_doc)
        
        logger.info(f"Webhook event emitted: {event_type} ({event.id})")
        
        # Process event asynchronously
        asyncio.create_task(self._process_event(event))
        
        return event
    
    async def _process_event(self, event: WebhookEvent):
        """Process a webhook event through automation rules"""
        try:
            # Update status to processing
            await self.db.webhook_events.update_one(
                {"id": event.id},
                {"$set": {"status": "processing"}}
            )
            
            # Find matching automation rule
            rule = self.automation_rules.get(event.event_type)
            
            if not rule:
                logger.debug(f"No automation rule for event type: {event.event_type}")
                await self.db.webhook_events.update_one(
                    {"id": event.id},
                    {"$set": {"status": "completed", "processed_at": datetime.now(timezone.utc).isoformat()}}
                )
                return
            
            # Execute actions
            actions_triggered = []
            action_results = {}
            
            for action_name in rule.get("actions", []):
                handler = self.action_handlers.get(action_name)
                if handler:
                    try:
                        result = await handler(event)
                        actions_triggered.append(action_name)
                        action_results[action_name] = {"success": True, "result": result}
                        logger.info(f"Action executed: {action_name} for event {event.id}")
                    except Exception as e:
                        action_results[action_name] = {"success": False, "error": str(e)}
                        logger.error(f"Action failed: {action_name} - {str(e)}")
            
            # Update event with results
            await self.db.webhook_events.update_one(
                {"id": event.id},
                {"$set": {
                    "status": "completed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "actions_triggered": actions_triggered,
                    "action_results": action_results
                }}
            )
            
            # Update rule stats
            await self.db.automation_rules.update_one(
                {"id": rule["id"]},
                {"$inc": {"times_triggered": 1}, "$set": {"last_triggered": datetime.now(timezone.utc).isoformat()}}
            )
            
            logger.info(f"Event processed: {event.id} - {len(actions_triggered)} actions executed")
            
        except Exception as e:
            logger.error(f"Event processing failed: {event.id} - {str(e)}")
            await self.db.webhook_events.update_one(
                {"id": event.id},
                {"$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    
    # ============== ACTION HANDLERS ==============
    
    async def _handle_log_event(self, event: WebhookEvent) -> Dict:
        """Log event to audit trail"""
        audit_entry = {
            "id": f"AUD-{str(uuid.uuid4())[:6]}",
            "audit_id": f"AUD-{str(uuid.uuid4())[:6]}",
            "user_id": event.user_id or "system",
            "violation_type": f"EVENT:{event.event_type}",
            "severity": "Low",
            "resolution_status": "Logged",
            "date_of_incident": datetime.now(timezone.utc).isoformat(),
            "auditor_system": "Webhook_Automation",
            "remediation_steps": f"Automated event: {event.event_type}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.audit.insert_one(audit_entry)
        return {"audit_id": audit_entry["id"]}
    
    async def _handle_update_arris_memory(self, event: WebhookEvent) -> Dict:
        """Update ARRIS Memory Palace with event data"""
        # Create ARRIS usage log for pattern tracking
        arris_log = {
            "id": f"ARRIS-WH-{event.id}",
            "log_id": f"ARRIS-WH-{event.id}",
            "user_id": event.user_id or "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_query_snippet": f"Webhook: {event.event_type}",
            "response_type": "Automation_Event",
            "response_id": event.source_id,
            "time_taken_s": 0,
            "linked_project": event.payload.get("project_id"),
            "query_category": "Automation",
            "success": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.arris_usage_log.insert_one(arris_log)
        
        # Update user activity log
        activity_log = {
            "id": f"ACT-{str(uuid.uuid4())[:6]}",
            "activity_id": f"ACT-{str(uuid.uuid4())[:6]}",
            "user_id": event.user_id or "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": event.event_type,
            "feature_name": "Webhook_Automation",
            "session_id": event.id,
            "details": str(event.payload)[:500],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.user_activity_log.insert_one(activity_log)
        
        return {"arris_log_id": arris_log["id"], "activity_log_id": activity_log["id"]}
    
    async def _handle_create_welcome_task(self, event: WebhookEvent) -> Dict:
        """Create a welcome/onboarding task for new creator"""
        creator_id = event.source_id
        creator_name = event.payload.get("name", "New Creator")
        
        task = {
            "id": f"T-WEL-{str(uuid.uuid4())[:4]}",
            "task_id": f"T-WEL-{str(uuid.uuid4())[:4]}",
            "project_id": "ONBOARDING",
            "description": f"Welcome {creator_name} - Complete profile setup and platform review",
            "due_date": None,
            "completion_status": 0,
            "assigned_to_user_id": creator_id,
            "estimated_hours": 1.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.tasks.insert_one(task)
        return {"task_id": task["id"]}
    
    async def _handle_create_onboarding_project(self, event: WebhookEvent) -> Dict:
        """Create onboarding project for approved creator"""
        user_id = event.payload.get("user_id") or event.source_id
        creator_name = event.payload.get("name", "Creator")
        
        project = {
            "id": f"P-ONB-{str(uuid.uuid4())[:4]}",
            "project_id": f"P-ONB-{str(uuid.uuid4())[:4]}",
            "title": f"{creator_name} Onboarding Journey",
            "platform": "HiveHQ",
            "status": "In_Progress",
            "user_id": user_id,
            "priority_level": "High",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.projects.insert_one(project)
        
        # Create onboarding tasks
        onboarding_tasks = [
            "Complete profile information",
            "Connect primary platform accounts",
            "Review ARRIS capabilities",
            "Submit first project proposal"
        ]
        
        for i, task_desc in enumerate(onboarding_tasks):
            task = {
                "id": f"T-{project['id']}-{i+1}",
                "task_id": f"T-{project['id']}-{i+1}",
                "project_id": project["id"],
                "description": task_desc,
                "completion_status": 0,
                "assigned_to_user_id": user_id,
                "estimated_hours": 0.5,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.tasks.insert_one(task)
        
        return {"project_id": project["id"], "tasks_created": len(onboarding_tasks)}
    
    async def _handle_queue_for_review(self, event: WebhookEvent) -> Dict:
        """Add item to review queue"""
        # Create a support log entry for tracking
        support_entry = {
            "id": f"SR-{str(uuid.uuid4())[:6]}",
            "log_id": f"SR-{str(uuid.uuid4())[:6]}",
            "user_id": event.user_id or "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issue_summary": f"Review Required: {event.event_type} - {event.source_id}",
            "category": "Review_Queue",
            "status": "New",
            "assigned_to": None,
            "resolution": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.support_log.insert_one(support_entry)
        return {"queue_entry_id": support_entry["id"]}
    
    async def _handle_create_project_tasks(self, event: WebhookEvent) -> Dict:
        """Create tasks from ARRIS suggested milestones"""
        project_id = event.payload.get("project_id")
        user_id = event.user_id
        milestones = event.payload.get("milestones", [])
        
        if not milestones:
            # Get milestones from proposal if available
            proposal_id = event.payload.get("proposal_id")
            if proposal_id:
                proposal = await self.db.proposals.find_one({"id": proposal_id})
                if proposal and proposal.get("arris_insights"):
                    milestones = proposal["arris_insights"].get("suggested_milestones", [])
        
        tasks_created = []
        for i, milestone in enumerate(milestones[:5]):  # Max 5 initial tasks
            task = {
                "id": f"T-{str(uuid.uuid4())[:6]}",
                "task_id": f"T-{str(uuid.uuid4())[:6]}",
                "project_id": project_id,
                "description": milestone,
                "completion_status": 0,
                "assigned_to_user_id": user_id,
                "estimated_hours": 4.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.tasks.insert_one(task)
            tasks_created.append(task["id"])
        
        return {"tasks_created": tasks_created}
    
    async def _handle_initialize_tracking(self, event: WebhookEvent) -> Dict:
        """Initialize analytics tracking for new project"""
        project_id = event.source_id
        user_id = event.user_id
        
        # Create initial analytics entry
        analytics = {
            "id": f"A-{str(uuid.uuid4())[:6]}",
            "metric_id": f"A-{str(uuid.uuid4())[:6]}",
            "user_id": user_id,
            "platform_views": 0,
            "revenue": 0.0,
            "engagement_score": 0.0,
            "date": datetime.now(timezone.utc).isoformat(),
            "platform": "HiveHQ",
            "conversion_rate": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.analytics.insert_one(analytics)
        return {"analytics_id": analytics["id"]}
    
    async def _handle_check_completion(self, event: WebhookEvent) -> Dict:
        """Check if project is complete after task completion"""
        project_id = event.payload.get("project_id")
        
        if not project_id:
            return {"checked": False, "reason": "No project_id"}
        
        # Count total and completed tasks
        total_tasks = await self.db.tasks.count_documents({"project_id": project_id})
        completed_tasks = await self.db.tasks.count_documents({
            "project_id": project_id,
            "completion_status": 1
        })
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # If all tasks complete, mark project as completed
        if total_tasks > 0 and completed_tasks == total_tasks:
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {"status": "Completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Emit project completed event
            await self.emit(
                event_type=WebhookEventType.PROJECT_COMPLETED,
                payload={"project_id": project_id, "completion_rate": 100},
                source_entity="project",
                source_id=project_id,
                user_id=event.user_id
            )
            
            return {"project_completed": True, "completion_rate": 100}
        
        return {"project_completed": False, "completion_rate": completion_rate}
    
    async def _handle_update_financial_patterns(self, event: WebhookEvent) -> Dict:
        """Update financial patterns in Calculator"""
        user_id = event.user_id
        
        # This would trigger pattern analysis on financial data
        # For now, just log that financial update was processed
        return {"patterns_updated": True, "user_id": user_id}
    
    async def _handle_create_notification(self, event: WebhookEvent) -> Dict:
        """Create a notification for the event"""
        notification = {
            "id": f"NOTIF-{str(uuid.uuid4())[:6]}",
            "user_id": event.user_id or "admin",
            "type": event.event_type,
            "title": f"Event: {event.event_type.replace('.', ' ').replace('_', ' ').title()}",
            "message": str(event.payload.get("message", f"Event triggered: {event.source_id}")),
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.notifications.insert_one(notification)
        return {"notification_id": notification["id"]}
    
    async def _handle_send_notification(self, event: WebhookEvent) -> Dict:
        """Send notification (placeholder for email/push)"""
        # In production, this would integrate with email/SMS service
        logger.info(f"Notification would be sent for event: {event.id}")
        return {"notification_sent": True, "method": "log_only"}

# Global webhook service instance
webhook_service = WebhookService()
