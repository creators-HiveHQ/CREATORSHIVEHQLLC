"""
ARRIS Activity Feed Service for Creators Hive HQ
Real-time activity tracking and queue position updates for Premium users

Features:
- Track active processing requests
- Broadcast queue position updates
- Maintain activity history
- Provide activity feed data
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
import logging
import uuid

logger = logging.getLogger(__name__)


class ArrisActivityItem:
    """Represents a single activity item in the feed"""
    
    def __init__(
        self,
        activity_type: str,
        creator_id: str,
        creator_name: str,
        proposal_id: Optional[str] = None,
        proposal_title: Optional[str] = None,
        priority: str = "standard",
        status: str = "queued",
        processing_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = f"activity_{uuid.uuid4().hex[:12]}"
        self.activity_type = activity_type
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.proposal_id = proposal_id
        self.proposal_title = proposal_title
        self.priority = priority
        self.status = status
        self.processing_time = processing_time
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "proposal_id": self.proposal_id,
            "proposal_title": self.proposal_title,
            "priority": self.priority,
            "status": self.status,
            "processing_time": self.processing_time,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ArrisQueueItem:
    """Represents an item in the ARRIS processing queue"""
    
    def __init__(
        self,
        request_id: str,
        creator_id: str,
        creator_name: str,
        proposal_id: str,
        proposal_title: str,
        priority: str,
        tier: str
    ):
        self.request_id = request_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.proposal_id = proposal_id
        self.proposal_title = proposal_title
        self.priority = priority
        self.tier = tier
        self.status = "queued"  # queued, processing, completed, failed
        self.queue_position = 0
        self.enqueued_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "proposal_id": self.proposal_id,
            "proposal_title": self.proposal_title,
            "priority": self.priority,
            "tier": self.tier,
            "status": self.status,
            "queue_position": self.queue_position,
            "enqueued_at": self.enqueued_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time": self.processing_time
        }


class ArrisActivityFeedService:
    """
    Service for managing ARRIS activity feed and queue tracking.
    Provides real-time updates for Premium/Elite users.
    """
    
    def __init__(self, max_history: int = 50):
        # Queue tracking
        self.fast_queue: List[ArrisQueueItem] = []  # Premium/Elite
        self.standard_queue: List[ArrisQueueItem] = []  # Free/Starter/Pro
        self.processing: Dict[str, ArrisQueueItem] = {}  # request_id -> item
        
        # Activity history (recent activities)
        self.activity_history: deque = deque(maxlen=max_history)
        
        # Statistics
        self.total_processed = 0
        self.total_fast_processed = 0
        self.total_standard_processed = 0
        self.avg_fast_time = 0.0
        self.avg_standard_time = 0.0
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        # Notification callback (set by server)
        self._notification_callback = None
    
    def set_notification_callback(self, callback):
        """Set callback for sending notifications"""
        self._notification_callback = callback
    
    async def enqueue_request(
        self,
        request_id: str,
        creator_id: str,
        creator_name: str,
        proposal_id: str,
        proposal_title: str,
        priority: str,
        tier: str
    ) -> ArrisQueueItem:
        """Add a request to the appropriate queue"""
        async with self.lock:
            item = ArrisQueueItem(
                request_id=request_id,
                creator_id=creator_id,
                creator_name=creator_name,
                proposal_id=proposal_id,
                proposal_title=proposal_title,
                priority=priority,
                tier=tier
            )
            
            if priority == "fast":
                self.fast_queue.append(item)
                item.queue_position = len(self.fast_queue)
            else:
                self.standard_queue.append(item)
                # Standard queue position includes fast queue
                item.queue_position = len(self.fast_queue) + len(self.standard_queue)
            
            # Create activity item
            activity = ArrisActivityItem(
                activity_type="request_queued",
                creator_id=creator_id,
                creator_name=creator_name,
                proposal_id=proposal_id,
                proposal_title=proposal_title,
                priority=priority,
                status="queued"
            )
            self.activity_history.appendleft(activity)
            
            # Update all queue positions
            await self._update_queue_positions()
            
            logger.info(f"ARRIS Activity: Enqueued {request_id} at position {item.queue_position} ({priority})")
            
            return item
    
    async def start_processing(self, request_id: str) -> Optional[ArrisQueueItem]:
        """Mark a request as started processing"""
        async with self.lock:
            item = None
            
            # Find in fast queue first
            for i, q_item in enumerate(self.fast_queue):
                if q_item.request_id == request_id:
                    item = self.fast_queue.pop(i)
                    break
            
            # If not found, check standard queue
            if not item:
                for i, q_item in enumerate(self.standard_queue):
                    if q_item.request_id == request_id:
                        item = self.standard_queue.pop(i)
                        break
            
            if item:
                item.status = "processing"
                item.started_at = datetime.now(timezone.utc)
                self.processing[request_id] = item
                
                # Create activity item
                activity = ArrisActivityItem(
                    activity_type="processing_started",
                    creator_id=item.creator_id,
                    creator_name=item.creator_name,
                    proposal_id=item.proposal_id,
                    proposal_title=item.proposal_title,
                    priority=item.priority,
                    status="processing"
                )
                self.activity_history.appendleft(activity)
                
                # Update queue positions for remaining items
                await self._update_queue_positions()
                
                # Send notification
                if self._notification_callback:
                    await self._notification_callback(
                        "processing_started",
                        item.creator_id,
                        item.to_dict()
                    )
                
                logger.info(f"ARRIS Activity: Started processing {request_id}")
            
            return item
    
    async def complete_processing(
        self,
        request_id: str,
        processing_time: float,
        success: bool = True
    ) -> Optional[ArrisQueueItem]:
        """Mark a request as completed"""
        async with self.lock:
            item = self.processing.pop(request_id, None)
            
            if item:
                item.status = "completed" if success else "failed"
                item.completed_at = datetime.now(timezone.utc)
                item.processing_time = processing_time
                
                # Update statistics
                self.total_processed += 1
                if item.priority == "fast":
                    self.total_fast_processed += 1
                    self.avg_fast_time = (
                        (self.avg_fast_time * (self.total_fast_processed - 1) + processing_time) 
                        / self.total_fast_processed
                    )
                else:
                    self.total_standard_processed += 1
                    self.avg_standard_time = (
                        (self.avg_standard_time * (self.total_standard_processed - 1) + processing_time)
                        / self.total_standard_processed
                    )
                
                # Create activity item
                activity = ArrisActivityItem(
                    activity_type="processing_completed" if success else "processing_failed",
                    creator_id=item.creator_id,
                    creator_name=item.creator_name,
                    proposal_id=item.proposal_id,
                    proposal_title=item.proposal_title,
                    priority=item.priority,
                    status="completed" if success else "failed",
                    processing_time=processing_time
                )
                self.activity_history.appendleft(activity)
                
                # Send notification
                if self._notification_callback:
                    await self._notification_callback(
                        "processing_completed",
                        item.creator_id,
                        {
                            **item.to_dict(),
                            "success": success
                        }
                    )
                
                logger.info(f"ARRIS Activity: Completed {request_id} in {processing_time:.2f}s")
            
            return item
    
    async def _update_queue_positions(self):
        """Update queue positions for all items and notify users"""
        # Calculate estimated wait times
        avg_time = self.avg_fast_time if self.avg_fast_time > 0 else 5.0
        
        # Update fast queue positions
        for i, item in enumerate(self.fast_queue):
            old_position = item.queue_position
            item.queue_position = i + 1
            estimated_wait = int(item.queue_position * avg_time)
            
            # Notify if position changed
            if self._notification_callback and old_position != item.queue_position:
                await self._notification_callback(
                    "queue_update",
                    item.creator_id,
                    {
                        "proposal_id": item.proposal_id,
                        "queue_position": item.queue_position,
                        "estimated_wait_seconds": estimated_wait,
                        "priority": item.priority
                    }
                )
        
        # Update standard queue positions (after fast queue)
        fast_queue_len = len(self.fast_queue)
        for i, item in enumerate(self.standard_queue):
            old_position = item.queue_position
            item.queue_position = fast_queue_len + i + 1
            estimated_wait = int(item.queue_position * avg_time)
            
            # Notify if position changed
            if self._notification_callback and old_position != item.queue_position:
                await self._notification_callback(
                    "queue_update",
                    item.creator_id,
                    {
                        "proposal_id": item.proposal_id,
                        "queue_position": item.queue_position,
                        "estimated_wait_seconds": estimated_wait,
                        "priority": item.priority
                    }
                )
    
    async def get_queue_position(self, creator_id: str, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get queue position for a specific creator's proposal"""
        async with self.lock:
            # Check if currently processing
            for item in self.processing.values():
                if item.creator_id == creator_id and item.proposal_id == proposal_id:
                    return {
                        "status": "processing",
                        "queue_position": 0,
                        "estimated_wait_seconds": 0,
                        "priority": item.priority,
                        "started_at": item.started_at.isoformat() if item.started_at else None
                    }
            
            # Check fast queue
            for item in self.fast_queue:
                if item.creator_id == creator_id and item.proposal_id == proposal_id:
                    avg_time = self.avg_fast_time if self.avg_fast_time > 0 else 5.0
                    return {
                        "status": "queued",
                        "queue_position": item.queue_position,
                        "estimated_wait_seconds": int(item.queue_position * avg_time),
                        "priority": item.priority,
                        "enqueued_at": item.enqueued_at.isoformat()
                    }
            
            # Check standard queue
            for item in self.standard_queue:
                if item.creator_id == creator_id and item.proposal_id == proposal_id:
                    avg_time = self.avg_standard_time if self.avg_standard_time > 0 else 5.0
                    return {
                        "status": "queued",
                        "queue_position": item.queue_position,
                        "estimated_wait_seconds": int(item.queue_position * avg_time),
                        "priority": item.priority,
                        "enqueued_at": item.enqueued_at.isoformat()
                    }
            
            return None
    
    async def get_creator_queue_items(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get all queue items for a specific creator"""
        async with self.lock:
            items = []
            
            # Check processing
            for item in self.processing.values():
                if item.creator_id == creator_id:
                    items.append(item.to_dict())
            
            # Check fast queue
            for item in self.fast_queue:
                if item.creator_id == creator_id:
                    items.append(item.to_dict())
            
            # Check standard queue
            for item in self.standard_queue:
                if item.creator_id == creator_id:
                    items.append(item.to_dict())
            
            return items
    
    async def get_activity_feed(
        self,
        limit: int = 20,
        include_anonymous: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recent activity feed items"""
        async with self.lock:
            activities = []
            for activity in list(self.activity_history)[:limit]:
                activity_dict = activity.to_dict()
                if not include_anonymous:
                    # Anonymize creator info for privacy
                    activity_dict["creator_name"] = activity_dict["creator_name"][:2] + "***"
                    activity_dict["creator_id"] = "***"
                activities.append(activity_dict)
            return activities
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        async with self.lock:
            return self._get_queue_stats_internal()
    
    def _get_queue_stats_internal(self) -> Dict[str, Any]:
        """Internal method to get queue stats (call with lock held)"""
        avg_time = max(self.avg_fast_time, self.avg_standard_time, 5.0)
        
        return {
            "fast_queue_length": len(self.fast_queue),
            "standard_queue_length": len(self.standard_queue),
            "total_queue_length": len(self.fast_queue) + len(self.standard_queue),
            "currently_processing": len(self.processing),
            "total_processed": self.total_processed,
            "avg_fast_time": round(self.avg_fast_time, 2),
            "avg_standard_time": round(self.avg_standard_time, 2),
            "estimated_wait_fast": int(len(self.fast_queue) * avg_time),
            "estimated_wait_standard": int((len(self.fast_queue) + len(self.standard_queue)) * avg_time)
        }
    
    async def get_live_status(self) -> Dict[str, Any]:
        """Get live status for activity feed display"""
        async with self.lock:
            processing_items = [item.to_dict() for item in self.processing.values()]
            
            # Get next few items in queue (anonymized)
            next_in_queue = []
            for item in (self.fast_queue[:3] + self.standard_queue[:2]):
                item_dict = item.to_dict()
                item_dict["creator_name"] = item_dict["creator_name"][:2] + "***"
                item_dict["creator_id"] = "***"
                next_in_queue.append(item_dict)
            
            # Get queue stats without re-acquiring lock
            queue_stats = self._get_queue_stats_internal()
            
            # Get activity feed without re-acquiring lock
            activities = []
            for activity in list(self.activity_history)[:10]:
                activity_dict = activity.to_dict()
                # Anonymize creator info for privacy
                activity_dict["creator_name"] = activity_dict["creator_name"][:2] + "***"
                activity_dict["creator_id"] = "***"
                activities.append(activity_dict)
            
            return {
                "currently_processing": processing_items,
                "next_in_queue": next_in_queue,
                "queue_stats": queue_stats,
                "recent_activity": activities,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Global instance
arris_activity_service = ArrisActivityFeedService()
