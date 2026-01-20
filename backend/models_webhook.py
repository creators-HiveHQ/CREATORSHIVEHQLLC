"""
Creators Hive HQ - Webhook Automation System
Zero-Human Operational Model - Event-Driven Architecture
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone
from enum import Enum
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

# ============== EVENT TYPES ==============

class WebhookEventType(str, Enum):
    # Creator Events
    CREATOR_REGISTERED = "creator.registered"
    CREATOR_APPROVED = "creator.approved"
    CREATOR_REJECTED = "creator.rejected"
    
    # Proposal Events
    PROPOSAL_CREATED = "proposal.created"
    PROPOSAL_SUBMITTED = "proposal.submitted"
    PROPOSAL_APPROVED = "proposal.approved"
    PROPOSAL_REJECTED = "proposal.rejected"
    PROPOSAL_STATUS_CHANGED = "proposal.status_changed"
    
    # Project Events
    PROJECT_CREATED = "project.created"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    PROJECT_COMPLETED = "project.completed"
    
    # Task Events
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    
    # Financial Events
    SUBSCRIPTION_CREATED = "subscription.created"
    REVENUE_RECORDED = "revenue.recorded"
    
    # ARRIS Events
    ARRIS_INSIGHTS_GENERATED = "arris.insights_generated"
    ARRIS_PATTERN_DETECTED = "arris.pattern_detected"
    
    # Elite Events
    ELITE_INQUIRY_SUBMITTED = "elite.inquiry_submitted"
    ELITE_INQUIRY_CONVERTED = "elite.inquiry_converted"
    
    # System Events
    SYSTEM_ALERT = "system.alert"
    AUDIT_LOG = "audit.log"

# ============== EVENT MODELS ==============

class WebhookEvent(BaseModel):
    """Webhook event record"""
    id: str = Field(default_factory=lambda: f"EVT-{str(uuid.uuid4())[:8]}")
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Event data
    payload: Dict[str, Any] = {}
    
    # Source information
    source_entity: str = ""  # e.g., "creator", "proposal", "project"
    source_id: str = ""  # ID of the entity that triggered the event
    user_id: Optional[str] = None  # User associated with the event
    
    # Processing status
    status: str = "pending"  # pending, processing, completed, failed
    processed_at: Optional[datetime] = None
    
    # Actions taken
    actions_triggered: List[str] = []
    action_results: Dict[str, Any] = {}
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0

class WebhookEventCreate(BaseModel):
    """Create a new webhook event"""
    event_type: str
    payload: Dict[str, Any] = {}
    source_entity: str = ""
    source_id: str = ""
    user_id: Optional[str] = None

# ============== AUTOMATION RULES ==============

class AutomationRule(BaseModel):
    """Automation rule configuration"""
    id: str = Field(default_factory=lambda: f"RULE-{str(uuid.uuid4())[:6]}")
    name: str
    description: str = ""
    
    # Trigger
    event_type: str
    conditions: Dict[str, Any] = {}  # Optional conditions to match
    
    # Actions
    actions: List[str] = []  # Action handlers to execute
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Stats
    times_triggered: int = 0
    last_triggered: Optional[datetime] = None

# ============== DEFAULT AUTOMATION RULES ==============

DEFAULT_AUTOMATION_RULES = [
    {
        "id": "RULE-001",
        "name": "New Creator Welcome",
        "description": "Log and track new creator registrations",
        "event_type": WebhookEventType.CREATOR_REGISTERED,
        "actions": ["log_event", "update_arris_memory", "create_welcome_task"],
        "is_active": True
    },
    {
        "id": "RULE-002",
        "name": "Creator Approved Onboarding",
        "description": "Trigger onboarding workflow when creator is approved",
        "event_type": WebhookEventType.CREATOR_APPROVED,
        "actions": ["log_event", "update_arris_memory", "create_onboarding_project"],
        "is_active": True
    },
    {
        "id": "RULE-003",
        "name": "Proposal Submitted Review",
        "description": "Notify and prepare for proposal review",
        "event_type": WebhookEventType.PROPOSAL_SUBMITTED,
        "actions": ["log_event", "update_arris_memory", "queue_for_review"],
        "is_active": True
    },
    {
        "id": "RULE-004",
        "name": "Proposal Approved Kickoff",
        "description": "Initialize project when proposal is approved",
        "event_type": WebhookEventType.PROPOSAL_APPROVED,
        "actions": ["log_event", "update_arris_memory", "create_project_tasks"],
        "is_active": True
    },
    {
        "id": "RULE-005",
        "name": "Project Created Setup",
        "description": "Set up project infrastructure",
        "event_type": WebhookEventType.PROJECT_CREATED,
        "actions": ["log_event", "update_arris_memory", "initialize_project_tracking"],
        "is_active": True
    },
    {
        "id": "RULE-006",
        "name": "Task Completed Progress",
        "description": "Update progress when task is completed",
        "event_type": WebhookEventType.TASK_COMPLETED,
        "actions": ["log_event", "update_arris_memory", "check_project_completion"],
        "is_active": True
    },
    {
        "id": "RULE-007",
        "name": "Revenue Tracking",
        "description": "Track revenue through Self-Funding Loop",
        "event_type": WebhookEventType.REVENUE_RECORDED,
        "actions": ["log_event", "update_arris_memory", "update_financial_patterns"],
        "is_active": True
    },
    {
        "id": "RULE-008",
        "name": "ARRIS Pattern Alert",
        "description": "Alert on significant pattern detection",
        "event_type": WebhookEventType.ARRIS_PATTERN_DETECTED,
        "actions": ["log_event", "create_insight_notification"],
        "is_active": True
    },
]

# ============== FOLLOW-UP ACTION DEFINITIONS ==============

FOLLOW_UP_ACTIONS = {
    "log_event": {
        "name": "Log Event",
        "description": "Record event in audit log"
    },
    "update_arris_memory": {
        "name": "Update ARRIS Memory",
        "description": "Update Memory Palace with new data"
    },
    "create_welcome_task": {
        "name": "Create Welcome Task",
        "description": "Create onboarding task for new creator"
    },
    "create_onboarding_project": {
        "name": "Create Onboarding Project",
        "description": "Create starter project for approved creator"
    },
    "queue_for_review": {
        "name": "Queue for Review",
        "description": "Add to admin review queue"
    },
    "create_project_tasks": {
        "name": "Create Project Tasks",
        "description": "Generate initial tasks from ARRIS milestones"
    },
    "initialize_project_tracking": {
        "name": "Initialize Tracking",
        "description": "Set up analytics and tracking for project"
    },
    "check_project_completion": {
        "name": "Check Completion",
        "description": "Evaluate if project is complete"
    },
    "update_financial_patterns": {
        "name": "Update Financial Patterns",
        "description": "Analyze revenue patterns in Calculator"
    },
    "create_insight_notification": {
        "name": "Create Notification",
        "description": "Generate notification for insights"
    },
    "send_notification": {
        "name": "Send Notification",
        "description": "Send notification to user/admin"
    },
}
