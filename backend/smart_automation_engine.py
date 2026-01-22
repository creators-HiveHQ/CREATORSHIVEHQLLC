"""
ARRIS Smart Automation Engine - Phase 4 Module B
Advanced condition-based automation and intelligent recommendations

This module implements:
1. Smart Automation Rules - Condition-based triggers with complex criteria
2. Automated Proposal Recommendations - AI-generated improvement suggestions for rejected proposals
3. Proactive Interventions - Automated actions based on pattern detection
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

logger = logging.getLogger(__name__)


class ConditionType:
    """Types of conditions for smart automation rules"""
    THRESHOLD = "threshold"           # Numeric threshold (e.g., approval_rate < 50)
    TIME_BASED = "time_based"         # Time-based condition (e.g., no activity in 30 days)
    COUNT = "count"                   # Count-based (e.g., 3+ rejections)
    PATTERN = "pattern"               # Pattern-based (e.g., declining trend)
    COMPOSITE = "composite"           # Multiple conditions combined


class ActionType:
    """Types of actions for smart automation"""
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    NOTIFY_ADMIN = "notify_admin"
    GENERATE_RECOMMENDATION = "generate_recommendation"
    UPDATE_STATUS = "update_status"
    TRIGGER_WEBHOOK = "trigger_webhook"
    LOG_EVENT = "log_event"


class SmartAutomationEngine:
    """
    Smart Automation Engine for Condition-Based Triggers
    
    Extends the basic webhook automation with:
    - Complex condition evaluation (AND/OR logic)
    - Time-based triggers (scheduled, delayed)
    - Pattern-based triggers (from ARRIS Pattern Engine)
    - Proactive intervention workflows
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.smart_rules = []
        self.action_handlers: Dict[str, Callable] = {}
        self._setup_action_handlers()
        
    def _setup_action_handlers(self):
        """Register action handlers for smart automations"""
        self.action_handlers = {
            ActionType.SEND_EMAIL: self._action_send_email,
            ActionType.CREATE_TASK: self._action_create_task,
            ActionType.NOTIFY_ADMIN: self._action_notify_admin,
            ActionType.GENERATE_RECOMMENDATION: self._action_generate_recommendation,
            ActionType.UPDATE_STATUS: self._action_update_status,
            ActionType.LOG_EVENT: self._action_log_event,
        }
    
    async def initialize(self):
        """Load smart automation rules from database"""
        # Create default smart rules if none exist
        existing = await self.db.smart_automation_rules.count_documents({})
        
        if existing == 0:
            await self._seed_default_smart_rules()
        
        # Load active rules
        self.smart_rules = await self.db.smart_automation_rules.find(
            {"is_active": True}
        ).to_list(100)
        
        logger.info(f"Smart Automation Engine loaded {len(self.smart_rules)} active rules")
    
    async def _seed_default_smart_rules(self):
        """Seed default smart automation rules"""
        default_rules = [
            {
                "id": "SMART-RULE-001",
                "name": "Low Approval Rate Coaching",
                "description": "Send coaching email when creator approval rate drops below 50% for 30 days",
                "trigger_type": "condition",
                "conditions": {
                    "type": ConditionType.COMPOSITE,
                    "operator": "AND",
                    "rules": [
                        {"field": "approval_rate", "operator": "lt", "value": 50},
                        {"field": "total_proposals", "operator": "gte", "value": 5},
                        {"field": "days_since_last_approval", "operator": "gte", "value": 30}
                    ]
                },
                "actions": [
                    {"type": ActionType.SEND_EMAIL, "template": "coaching_low_approval"},
                    {"type": ActionType.CREATE_TASK, "task_type": "creator_coaching"},
                    {"type": ActionType.NOTIFY_ADMIN, "priority": "medium"}
                ],
                "cooldown_hours": 168,  # 7 days
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "SMART-RULE-002",
                "name": "Rejection Streak Alert",
                "description": "Alert when creator has 3+ consecutive rejections",
                "trigger_type": "condition",
                "conditions": {
                    "type": ConditionType.COUNT,
                    "field": "consecutive_rejections",
                    "operator": "gte",
                    "value": 3
                },
                "actions": [
                    {"type": ActionType.GENERATE_RECOMMENDATION, "focus": "rejection_analysis"},
                    {"type": ActionType.SEND_EMAIL, "template": "rejection_support"},
                    {"type": ActionType.LOG_EVENT, "event_type": "rejection_streak"}
                ],
                "cooldown_hours": 72,  # 3 days
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "SMART-RULE-003",
                "name": "Inactivity Re-engagement",
                "description": "Re-engage creators with no proposals in 60 days",
                "trigger_type": "time_based",
                "conditions": {
                    "type": ConditionType.TIME_BASED,
                    "field": "days_since_last_proposal",
                    "operator": "gte",
                    "value": 60
                },
                "actions": [
                    {"type": ActionType.SEND_EMAIL, "template": "reengagement"},
                    {"type": ActionType.NOTIFY_ADMIN, "priority": "low"}
                ],
                "cooldown_hours": 336,  # 14 days
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "SMART-RULE-004",
                "name": "High Performer Recognition",
                "description": "Recognize creators with 80%+ approval rate on 10+ proposals",
                "trigger_type": "condition",
                "conditions": {
                    "type": ConditionType.COMPOSITE,
                    "operator": "AND",
                    "rules": [
                        {"field": "approval_rate", "operator": "gte", "value": 80},
                        {"field": "total_proposals", "operator": "gte", "value": 10}
                    ]
                },
                "actions": [
                    {"type": ActionType.SEND_EMAIL, "template": "high_performer"},
                    {"type": ActionType.CREATE_TASK, "task_type": "feature_creator"},
                    {"type": ActionType.LOG_EVENT, "event_type": "high_performer_identified"}
                ],
                "cooldown_hours": 720,  # 30 days
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "SMART-RULE-005",
                "name": "Proposal Rejection Auto-Recommendations",
                "description": "Generate improvement recommendations when proposal is rejected",
                "trigger_type": "event",
                "event_trigger": "proposal.rejected",
                "conditions": None,
                "actions": [
                    {"type": ActionType.GENERATE_RECOMMENDATION, "focus": "proposal_improvement"},
                    {"type": ActionType.SEND_EMAIL, "template": "rejection_with_recommendations"}
                ],
                "cooldown_hours": 0,  # No cooldown - triggers on every rejection
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for rule in default_rules:
            await self.db.smart_automation_rules.insert_one(rule)
        
        logger.info(f"Seeded {len(default_rules)} default smart automation rules")
    
    # ============== CONDITION EVALUATION ==============
    
    async def evaluate_creator_conditions(self, creator_id: str) -> List[Dict[str, Any]]:
        """
        Evaluate all smart automation rules against a creator's current state.
        Returns list of triggered rules with actions to execute.
        """
        triggered_rules = []
        
        # Get creator's current metrics
        metrics = await self._get_creator_metrics(creator_id)
        
        for rule in self.smart_rules:
            if rule.get("trigger_type") != "condition" and rule.get("trigger_type") != "time_based":
                continue
            
            # Check cooldown
            if not await self._check_cooldown(rule["id"], creator_id, rule.get("cooldown_hours", 0)):
                continue
            
            # Evaluate conditions
            if self._evaluate_conditions(rule.get("conditions"), metrics):
                triggered_rules.append({
                    "rule": rule,
                    "creator_id": creator_id,
                    "metrics": metrics,
                    "triggered_at": datetime.now(timezone.utc).isoformat()
                })
        
        return triggered_rules
    
    async def _get_creator_metrics(self, creator_id: str) -> Dict[str, Any]:
        """Get current metrics for a creator"""
        now = datetime.now(timezone.utc)
        
        # Get proposals
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "status": 1, "created_at": 1, "updated_at": 1}
        ).to_list(1000)
        
        total_proposals = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]])
        rejected = len([p for p in proposals if p.get("status") == "rejected"])
        
        # Calculate approval rate
        approval_rate = (approved / total_proposals * 100) if total_proposals > 0 else 0
        
        # Get last proposal date
        last_proposal_date = None
        if proposals:
            dates = [p.get("created_at") for p in proposals if p.get("created_at")]
            if dates:
                last_proposal_date = max(dates)
        
        # Calculate days since last proposal
        days_since_last_proposal = 0
        if last_proposal_date:
            try:
                last_dt = datetime.fromisoformat(last_proposal_date.replace("Z", "+00:00"))
                days_since_last_proposal = (now - last_dt).days
            except:
                pass
        
        # Get last approval date
        approved_proposals = [p for p in proposals if p.get("status") in ["approved", "completed", "in_progress"]]
        days_since_last_approval = 999
        if approved_proposals:
            dates = [p.get("updated_at") or p.get("created_at") for p in approved_proposals if p.get("updated_at") or p.get("created_at")]
            if dates:
                try:
                    last_approval_dt = datetime.fromisoformat(max(dates).replace("Z", "+00:00"))
                    days_since_last_approval = (now - last_approval_dt).days
                except:
                    pass
        
        # Calculate consecutive rejections
        consecutive_rejections = 0
        sorted_proposals = sorted(proposals, key=lambda x: x.get("created_at", ""), reverse=True)
        for p in sorted_proposals:
            if p.get("status") == "rejected":
                consecutive_rejections += 1
            elif p.get("status") in ["approved", "completed", "in_progress"]:
                break
        
        # Get subscription tier
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0, "tier": 1}
        )
        tier = subscription.get("tier", "Free") if subscription else "Free"
        
        return {
            "creator_id": creator_id,
            "total_proposals": total_proposals,
            "approved_proposals": approved,
            "rejected_proposals": rejected,
            "approval_rate": round(approval_rate, 1),
            "days_since_last_proposal": days_since_last_proposal,
            "days_since_last_approval": days_since_last_approval,
            "consecutive_rejections": consecutive_rejections,
            "tier": tier,
            "calculated_at": now.isoformat()
        }
    
    def _evaluate_conditions(self, conditions: Optional[Dict], metrics: Dict[str, Any]) -> bool:
        """Evaluate conditions against metrics"""
        if not conditions:
            return True
        
        condition_type = conditions.get("type")
        
        if condition_type == ConditionType.COMPOSITE:
            return self._evaluate_composite(conditions, metrics)
        elif condition_type == ConditionType.THRESHOLD:
            return self._evaluate_threshold(conditions, metrics)
        elif condition_type == ConditionType.TIME_BASED:
            return self._evaluate_threshold(conditions, metrics)  # Same logic
        elif condition_type == ConditionType.COUNT:
            return self._evaluate_threshold(conditions, metrics)  # Same logic
        else:
            # Simple condition
            return self._evaluate_threshold(conditions, metrics)
        
        return False
    
    def _evaluate_composite(self, conditions: Dict, metrics: Dict[str, Any]) -> bool:
        """Evaluate composite conditions (AND/OR)"""
        operator = conditions.get("operator", "AND")
        rules = conditions.get("rules", [])
        
        if not rules:
            return True
        
        results = [self._evaluate_threshold(rule, metrics) for rule in rules]
        
        if operator == "AND":
            return all(results)
        elif operator == "OR":
            return any(results)
        
        return False
    
    def _evaluate_threshold(self, condition: Dict, metrics: Dict[str, Any]) -> bool:
        """Evaluate a single threshold condition"""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        metric_value = metrics.get(field)
        
        if metric_value is None:
            return False
        
        try:
            if operator == "lt":
                return metric_value < value
            elif operator == "lte":
                return metric_value <= value
            elif operator == "gt":
                return metric_value > value
            elif operator == "gte":
                return metric_value >= value
            elif operator == "eq":
                return metric_value == value
            elif operator == "ne":
                return metric_value != value
        except:
            return False
        
        return False
    
    async def _check_cooldown(self, rule_id: str, creator_id: str, cooldown_hours: int) -> bool:
        """Check if rule is still in cooldown period for this creator"""
        if cooldown_hours <= 0:
            return True
        
        cooldown_threshold = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
        
        # Check if this rule was triggered for this creator within cooldown period
        recent_trigger = await self.db.smart_automation_log.find_one({
            "rule_id": rule_id,
            "creator_id": creator_id,
            "triggered_at": {"$gte": cooldown_threshold.isoformat()}
        })
        
        return recent_trigger is None
    
    # ============== ACTION EXECUTION ==============
    
    async def execute_triggered_rules(self, triggered_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute actions for all triggered rules"""
        results = []
        
        for triggered in triggered_rules:
            rule = triggered["rule"]
            creator_id = triggered["creator_id"]
            metrics = triggered["metrics"]
            
            action_results = []
            
            for action in rule.get("actions", []):
                action_type = action.get("type")
                handler = self.action_handlers.get(action_type)
                
                if handler:
                    try:
                        result = await handler(creator_id, metrics, action, rule)
                        action_results.append({
                            "action": action_type,
                            "success": True,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Smart automation action failed: {action_type} - {str(e)}")
                        action_results.append({
                            "action": action_type,
                            "success": False,
                            "error": str(e)
                        })
            
            # Log the trigger
            log_entry = {
                "id": f"SMART-LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{creator_id[:8]}",
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "creator_id": creator_id,
                "metrics_snapshot": metrics,
                "actions_executed": action_results,
                "triggered_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.smart_automation_log.insert_one(log_entry)
            
            results.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "creator_id": creator_id,
                "actions_executed": len(action_results),
                "success_count": len([a for a in action_results if a["success"]])
            })
        
        return results
    
    # ============== ACTION HANDLERS ==============
    
    async def _action_send_email(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Send email action (logs for now, would integrate with email service)"""
        template = action.get("template", "generic")
        
        # Get creator email
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0, "email": 1, "name": 1}
        )
        
        if not creator:
            return {"sent": False, "reason": "Creator not found"}
        
        # Log email intent (in production, this would call email service)
        email_log = {
            "id": f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "creator_id": creator_id,
            "email": creator.get("email"),
            "template": template,
            "rule_id": rule["id"],
            "metrics": metrics,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.email_queue.insert_one(email_log)
        
        logger.info(f"Smart Automation: Email queued for {creator.get('email')} - template: {template}")
        
        return {"sent": True, "email_id": email_log["id"], "template": template}
    
    async def _action_create_task(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Create follow-up task action"""
        task_type = action.get("task_type", "follow_up")
        
        task_descriptions = {
            "creator_coaching": f"Coach creator on improving proposal quality (current approval rate: {metrics.get('approval_rate', 0)}%)",
            "feature_creator": f"Feature this high-performing creator (approval rate: {metrics.get('approval_rate', 0)}%)",
            "follow_up": f"Follow up with creator based on automation rule: {rule.get('name')}"
        }
        
        task = {
            "id": f"T-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "task_id": f"T-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "project_id": "AUTOMATION",
            "description": task_descriptions.get(task_type, task_descriptions["follow_up"]),
            "completion_status": 0,
            "assigned_to_user_id": "admin",
            "estimated_hours": 0.5,
            "metadata": {
                "creator_id": creator_id,
                "rule_id": rule["id"],
                "task_type": task_type,
                "metrics": metrics
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.tasks.insert_one(task)
        
        return {"task_id": task["id"], "task_type": task_type}
    
    async def _action_notify_admin(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Create admin notification"""
        priority = action.get("priority", "medium")
        
        notification = {
            "id": f"NOTIF-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": "admin",
            "type": "smart_automation",
            "title": f"Automation Triggered: {rule.get('name')}",
            "message": f"Creator {creator_id} triggered rule: {rule.get('description')}",
            "priority": priority,
            "metadata": {
                "creator_id": creator_id,
                "rule_id": rule["id"],
                "metrics": metrics
            },
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.notifications.insert_one(notification)
        
        return {"notification_id": notification["id"], "priority": priority}
    
    async def _action_generate_recommendation(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Generate AI-powered recommendation"""
        focus = action.get("focus", "general")
        
        # This will be called by the ProposalRecommendationService
        # For now, log the intent
        return {"recommendation_requested": True, "focus": focus, "creator_id": creator_id}
    
    async def _action_update_status(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Update creator or proposal status"""
        target = action.get("target", "creator")
        new_status = action.get("status")
        
        if target == "creator" and new_status:
            await self.db.creators.update_one(
                {"id": creator_id},
                {"$set": {"automation_status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            return {"updated": True, "target": target, "status": new_status}
        
        return {"updated": False, "reason": "Invalid target or status"}
    
    async def _action_log_event(
        self, 
        creator_id: str, 
        metrics: Dict, 
        action: Dict, 
        rule: Dict
    ) -> Dict:
        """Log event for analytics"""
        event_type = action.get("event_type", "automation_triggered")
        
        event_log = {
            "id": f"EVENT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "event_type": event_type,
            "creator_id": creator_id,
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.automation_events.insert_one(event_log)
        
        return {"logged": True, "event_id": event_log["id"]}
    
    # ============== RULE MANAGEMENT ==============
    
    async def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all smart automation rules"""
        rules = await self.db.smart_automation_rules.find({}, {"_id": 0}).to_list(100)
        return rules
    
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule"""
        return await self.db.smart_automation_rules.find_one({"id": rule_id}, {"_id": 0})
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new smart automation rule"""
        rule_data["id"] = f"SMART-RULE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        rule_data["created_at"] = datetime.now(timezone.utc).isoformat()
        rule_data["is_active"] = rule_data.get("is_active", True)
        
        await self.db.smart_automation_rules.insert_one(rule_data)
        
        # Reload rules
        await self.initialize()
        
        return rule_data
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a smart automation rule"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.db.smart_automation_rules.update_one(
            {"id": rule_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            await self.initialize()
            return True
        return False
    
    async def toggle_rule(self, rule_id: str, is_active: bool) -> bool:
        """Toggle rule active status"""
        return await self.update_rule(rule_id, {"is_active": is_active})
    
    async def get_automation_log(
        self, 
        creator_id: Optional[str] = None, 
        rule_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get automation execution log"""
        query = {}
        if creator_id:
            query["creator_id"] = creator_id
        if rule_id:
            query["rule_id"] = rule_id
        
        logs = await self.db.smart_automation_log.find(
            query, 
            {"_id": 0}
        ).sort("triggered_at", -1).to_list(limit)
        
        return logs


# Global instance (will be initialized in server startup)
smart_automation_engine = None
