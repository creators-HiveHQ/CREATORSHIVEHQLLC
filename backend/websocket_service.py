"""
WebSocket Notification Service for Creators Hive HQ
Real-time notifications for admins and creators

Features:
- Connection management for multiple clients
- User-specific notifications
- Broadcast to all connections
- Notification types: proposal updates, ARRIS insights, system alerts, elite inquiries
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    # Proposal notifications
    PROPOSAL_SUBMITTED = "proposal_submitted"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_UNDER_REVIEW = "proposal_under_review"
    
    # ARRIS notifications
    ARRIS_INSIGHTS_READY = "arris_insights_ready"
    ARRIS_MEMORY_UPDATED = "arris_memory_updated"
    ARRIS_PATTERN_DETECTED = "arris_pattern_detected"
    ARRIS_QUEUE_UPDATE = "arris_queue_update"           # New: Queue position updates
    ARRIS_PROCESSING_STARTED = "arris_processing_started"  # New: Processing started
    ARRIS_PROCESSING_COMPLETE = "arris_processing_complete"  # New: Processing complete
    ARRIS_ACTIVITY_UPDATE = "arris_activity_update"     # New: Activity feed updates
    
    # Subscription notifications
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # Elite notifications
    ELITE_INQUIRY_RECEIVED = "elite_inquiry_received"
    ELITE_INQUIRY_UPDATED = "elite_inquiry_updated"
    
    # System notifications
    SYSTEM_ALERT = "system_alert"
    WELCOME = "welcome"
    
    # Revenue notifications
    REVENUE_MILESTONE = "revenue_milestone"


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.
    Supports user-specific connections and broadcast messaging.
    """
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # All connections (for broadcast)
        self.all_connections: Set[WebSocket] = set()
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Admin connections
        self.admin_connections: Set[WebSocket] = set()
        # Creator connections
        self.creator_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        user_type: str = "admin",  # "admin" or "creator"
        user_name: Optional[str] = None
    ):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.all_connections.add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "user_type": user_type,
            "user_name": user_name,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Track by type
        if user_type == "admin":
            self.admin_connections.add(websocket)
        else:
            if user_id not in self.creator_connections:
                self.creator_connections[user_id] = set()
            self.creator_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: {user_type} {user_id} ({user_name})")
        
        # Send welcome notification
        await self.send_personal_notification(
            websocket,
            NotificationType.WELCOME,
            {
                "message": f"Welcome to Creators Hive HQ, {user_name or user_id}!",
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        # Get metadata before removing
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        user_type = metadata.get("user_type")
        
        # Remove from active connections
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from all connections
        self.all_connections.discard(websocket)
        
        # Remove from type-specific sets
        if user_type == "admin":
            self.admin_connections.discard(websocket)
        elif user_id and user_id in self.creator_connections:
            self.creator_connections[user_id].discard(websocket)
            if not self.creator_connections[user_id]:
                del self.creator_connections[user_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected: {user_type} {user_id}")
    
    async def send_personal_notification(
        self,
        websocket: WebSocket,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ):
        """Send notification to a specific WebSocket connection"""
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def send_to_user(
        self,
        user_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ):
        """Send notification to all connections of a specific user"""
        if user_id not in self.active_connections:
            return
        
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_admins(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ):
        """Broadcast notification to all admin connections"""
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.admin_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to admin: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_creator(
        self,
        creator_id: str,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ):
        """Broadcast notification to a specific creator's connections"""
        if creator_id not in self.creator_connections:
            return
        
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.creator_connections[creator_id].copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to creator {creator_id}: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_all(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ):
        """Broadcast notification to all connections"""
        message = {
            "type": notification_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        disconnected = []
        for connection in self.all_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self.all_connections),
            "admin_connections": len(self.admin_connections),
            "creator_connections": sum(len(conns) for conns in self.creator_connections.values()),
            "unique_creators": len(self.creator_connections),
            "unique_users": len(self.active_connections)
        }


# Global connection manager instance
ws_manager = ConnectionManager()


class NotificationService:
    """
    Service for sending real-time notifications.
    Integrates with existing events to push notifications.
    """
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    # ============== PROPOSAL NOTIFICATIONS ==============
    
    async def notify_proposal_submitted(
        self,
        proposal_id: str,
        proposal_title: str,
        creator_id: str,
        creator_name: str
    ):
        """Notify when a proposal is submitted"""
        # Notify admins
        await self.manager.broadcast_to_admins(
            NotificationType.PROPOSAL_SUBMITTED,
            {
                "proposal_id": proposal_id,
                "title": proposal_title,
                "creator_id": creator_id,
                "creator_name": creator_name,
                "message": f"New proposal submitted by {creator_name}: {proposal_title}"
            }
        )
        
        # Notify creator
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.PROPOSAL_SUBMITTED,
            {
                "proposal_id": proposal_id,
                "title": proposal_title,
                "message": f"Your proposal '{proposal_title}' has been submitted for review"
            }
        )
    
    async def notify_proposal_approved(
        self,
        proposal_id: str,
        proposal_title: str,
        project_id: str,
        creator_id: str
    ):
        """Notify when a proposal is approved"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.PROPOSAL_APPROVED,
            {
                "proposal_id": proposal_id,
                "title": proposal_title,
                "project_id": project_id,
                "message": f"🎉 Great news! Your proposal '{proposal_title}' has been approved!"
            }
        )
    
    async def notify_proposal_rejected(
        self,
        proposal_id: str,
        proposal_title: str,
        creator_id: str,
        reason: Optional[str] = None
    ):
        """Notify when a proposal is rejected"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.PROPOSAL_REJECTED,
            {
                "proposal_id": proposal_id,
                "title": proposal_title,
                "reason": reason,
                "message": f"Update on your proposal '{proposal_title}'"
            }
        )
    
    async def notify_proposal_under_review(
        self,
        proposal_id: str,
        proposal_title: str,
        creator_id: str
    ):
        """Notify when a proposal moves to under review"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.PROPOSAL_UNDER_REVIEW,
            {
                "proposal_id": proposal_id,
                "title": proposal_title,
                "message": f"Your proposal '{proposal_title}' is now under review"
            }
        )
    
    # ============== ARRIS NOTIFICATIONS ==============
    
    async def notify_arris_insights_ready(
        self,
        proposal_id: str,
        creator_id: str,
        insights_summary: str
    ):
        """Notify when ARRIS insights are ready"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.ARRIS_INSIGHTS_READY,
            {
                "proposal_id": proposal_id,
                "summary": insights_summary,
                "message": "🧠 ARRIS has generated insights for your proposal"
            }
        )
    
    async def notify_arris_pattern_detected(
        self,
        creator_id: str,
        pattern_type: str,
        pattern_description: str
    ):
        """Notify when ARRIS detects a new pattern"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.ARRIS_PATTERN_DETECTED,
            {
                "pattern_type": pattern_type,
                "description": pattern_description,
                "message": f"🔮 ARRIS detected a new pattern: {pattern_type}"
            }
        )
    
    # ============== SUBSCRIPTION NOTIFICATIONS ==============
    
    async def notify_subscription_created(
        self,
        creator_id: str,
        plan_name: str,
        tier: str
    ):
        """Notify when a subscription is created"""
        await self.manager.broadcast_to_creator(
            creator_id,
            NotificationType.SUBSCRIPTION_CREATED,
            {
                "plan_name": plan_name,
                "tier": tier,
                "message": f"✨ Welcome to {plan_name}! Your subscription is now active."
            }
        )
        
        # Also notify admins
        await self.manager.broadcast_to_admins(
            NotificationType.SUBSCRIPTION_CREATED,
            {
                "creator_id": creator_id,
                "plan_name": plan_name,
                "tier": tier,
                "message": f"New {tier} subscription created"
            }
        )
    
    # ============== ELITE NOTIFICATIONS ==============
    
    async def notify_elite_inquiry_received(
        self,
        inquiry_id: str,
        creator_name: str,
        creator_email: str,
        company_name: Optional[str] = None
    ):
        """Notify admins when an Elite inquiry is received"""
        await self.manager.broadcast_to_admins(
            NotificationType.ELITE_INQUIRY_RECEIVED,
            {
                "inquiry_id": inquiry_id,
                "creator_name": creator_name,
                "creator_email": creator_email,
                "company_name": company_name,
                "message": f"🌟 New Elite inquiry from {creator_name}"
            }
        )
    
    # ============== SYSTEM NOTIFICATIONS ==============
    
    async def notify_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info"  # info, warning, error
    ):
        """Broadcast system alert to all admins"""
        await self.manager.broadcast_to_admins(
            NotificationType.SYSTEM_ALERT,
            {
                "alert_type": alert_type,
                "message": message,
                "severity": severity
            }
        )
    
    async def notify_revenue_milestone(
        self,
        milestone: str,
        amount: float
    ):
        """Notify admins about revenue milestones"""
        await self.manager.broadcast_to_admins(
            NotificationType.REVENUE_MILESTONE,
            {
                "milestone": milestone,
                "amount": amount,
                "message": f"💰 Revenue milestone reached: {milestone}!"
            }
        )


# Global notification service instance
notification_service = NotificationService(ws_manager)
