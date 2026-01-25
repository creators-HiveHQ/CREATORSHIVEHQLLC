"""
ARRIS Routes
============
ARRIS AI endpoints for memory, patterns, learning, activity, and historical data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/arris", tags=["ARRIS"])


async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import get_current_creator as auth_get_current_creator
    return await auth_get_current_creator(credentials, db)


async def get_any_authenticated_user(credentials: HTTPAuthorizationCredentials):
    """Get any authenticated user (admin or creator)."""
    from auth import get_current_user, get_current_creator as auth_get_creator, decode_token
    
    db = get_db()
    token_data = decode_token(credentials.credentials)
    
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    role = getattr(token_data, 'role', 'admin')
    
    if role == "creator":
        try:
            creator = await auth_get_creator(credentials, db)
            return {"user_type": "creator", "user_id": creator["id"], "user": creator}
        except Exception:
            pass
    
    # Try admin
    try:
        admin = await get_current_user(credentials, db)
        if admin:
            return {"user_type": "admin", "user_id": admin.get("user_id", admin.get("id")), "user": admin}
    except Exception:
        pass
    
    raise HTTPException(status_code=401, detail="Could not validate credentials")


# ============== ARRIS MEMORY ENDPOINTS ==============

@router.get("/memory")
async def get_arris_memory(
    memory_type: Optional[str] = Query(default=None, description="Filter by memory type"),
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Recall memories from the Memory Palace.
    Memory types: interaction, proposal, outcome, pattern, preference, feedback, milestone
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    memories = await arris_memory_service.recall_memories(
        creator_id=creator_id,
        memory_type=memory_type,
        min_importance=min_importance,
        limit=limit
    )
    
    return {
        "memories": memories,
        "count": len(memories),
        "filters_applied": {
            "memory_type": memory_type,
            "min_importance": min_importance,
            "limit": limit
        }
    }


@router.get("/memory/summary")
async def get_arris_memory_summary(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get a summary of ARRIS memories for the current creator.
    Available to all authenticated creators.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    summary = await arris_memory_service.get_memory_summary(creator_id)
    
    return {
        "creator_id": creator_id,
        "memory_summary": summary
    }


@router.post("/memory")
async def store_arris_memory(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Store a new memory in the Memory Palace.
    
    Required fields:
    - memory_type: interaction, proposal, outcome, pattern, preference, feedback, milestone
    - content: Dict with memory content
    
    Optional:
    - importance: 0.0 to 1.0 (default 0.5)
    - tags: List of tags
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    memory_data = await request.json()
    memory_type = memory_data.get("memory_type") or memory_data.get("type")
    content = memory_data.get("content")
    
    if not memory_type or not content:
        raise HTTPException(status_code=400, detail="memory_type and content are required")
    
    arris_memory_service = get_service("arris_memory")
    memory = await arris_memory_service.store_memory(
        creator_id=creator_id,
        memory_type=memory_type,
        content=content,
        importance=memory_data.get("importance", 0.5),
        tags=memory_data.get("tags", []),
        context=memory_data.get("context", {})
    )
    
    return {"message": "Memory stored", "memory": memory}


@router.delete("/memory/{memory_id}")
async def delete_arris_memory(
    memory_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a specific memory entry."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    result = await db.arris_memory.delete_one({
        "id": memory_id,
        "creator_id": creator_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    
    return {"success": True, "message": "Memory entry deleted"}


# ============== ARRIS PATTERNS ENDPOINTS ==============

@router.get("/patterns")
async def get_arris_patterns(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Analyze and retrieve patterns from creator's history.
    Identifies success patterns, risk factors, timing preferences, and more.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    patterns = await arris_memory_service.analyze_patterns(creator_id)
    
    return patterns


@router.post("/patterns/analyze")
async def analyze_arris_patterns(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Force a new pattern analysis on creator's history.
    Useful after significant activity changes.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    patterns = await arris_memory_service.analyze_patterns(creator_id)
    
    return {
        "message": "Pattern analysis complete",
        "result": patterns
    }


# ============== ARRIS LEARNING ENDPOINTS ==============

@router.post("/learning/record-outcome")
async def record_arris_outcome(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Record the outcome of a proposal to improve ARRIS predictions.
    
    Required:
    - proposal_id: The proposal ID
    - outcome: approved, rejected, completed, etc.
    
    Optional:
    - feedback: Additional feedback about the outcome
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    outcome_data = await request.json()
    proposal_id = outcome_data.get("proposal_id")
    outcome = outcome_data.get("outcome")
    
    if not proposal_id or not outcome:
        raise HTTPException(status_code=400, detail="proposal_id and outcome are required")
    
    arris_memory_service = get_service("arris_memory")
    result = await arris_memory_service.record_outcome(
        creator_id=creator_id,
        proposal_id=proposal_id,
        outcome=outcome,
        feedback=outcome_data.get("feedback")
    )
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/learning/metrics")
async def get_arris_learning_metrics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get ARRIS learning metrics for the current creator.
    Shows prediction accuracy and learning stage.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    return {
        "creator_id": creator_id,
        "metrics": metrics
    }


# ============== ARRIS CONTEXT & PERSONALIZATION ==============

@router.get("/context")
async def get_arris_context(
    proposal_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the rich context ARRIS uses for AI interactions.
    Shows memories, patterns, and historical data being considered.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # If proposal_id provided, get that proposal
    proposal = {}
    if proposal_id:
        proposal = await db.proposals.find_one(
            {"id": proposal_id, "user_id": creator_id},
            {"_id": 0}
        )
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
    
    arris_memory_service = get_service("arris_memory")
    context = await arris_memory_service.build_rich_context(creator_id, proposal)
    
    return {
        "context": context,
        "proposal_id": proposal_id
    }


@router.get("/personalization")
async def get_arris_personalization(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get personalized prompt additions ARRIS uses based on learnings.
    Shows how ARRIS tailors responses to this creator.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    prompt_additions = await arris_memory_service.get_personalized_prompt_additions(creator_id)
    memory_summary = await arris_memory_service.get_memory_summary(creator_id)
    learning_metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    return {
        "creator_id": creator_id,
        "personalization": {
            "prompt_additions": prompt_additions,
            "is_personalized": len(prompt_additions) > 0
        },
        "memory_health": memory_summary.get("memory_health"),
        "learning_stage": learning_metrics.get("learning_stage"),
        "accuracy_rate": learning_metrics.get("accuracy_rate")
    }


@router.get("/memory-palace/status")
async def get_memory_palace_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get comprehensive Memory Palace status.
    Shows overall health, memory counts, pattern summary, and learning progress.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    
    # Get all relevant data
    memory_summary = await arris_memory_service.get_memory_summary(creator_id)
    learning_metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    # Get pattern count
    patterns = await arris_memory_service.recall_memories(
        creator_id=creator_id,
        memory_type="pattern",
        limit=100
    )
    
    return {
        "memory_palace": {
            "status": "active",
            "health": memory_summary.get("memory_health"),
            "total_memories": memory_summary.get("total_memories", 0),
            "by_type": memory_summary.get("by_type", {})
        },
        "pattern_engine": {
            "patterns_identified": len(patterns),
            "pattern_categories": list(set(
                p.get("content", {}).get("category") 
                for p in patterns 
                if p.get("content", {}).get("category")
            ))
        },
        "learning_system": {
            "stage": learning_metrics.get("learning_stage"),
            "accuracy_rate": learning_metrics.get("accuracy_rate"),
            "total_predictions": learning_metrics.get("total_predictions", 0)
        },
        "features": {
            "memory_storage": True,
            "pattern_recognition": True,
            "outcome_learning": True,
            "personalization": True,
            "context_building": True
        }
    }


# ============== ARRIS ACTIVITY FEED (Premium/Elite) ==============

@router.get("/activity")
async def get_arris_activity(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS activity for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    # Get activity from arris_activity collection
    activities = await db.arris_activity.find(
        {"creator_id": creator["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return {"activities": activities, "total": len(activities)}


@router.get("/activity/stats")
async def get_arris_activity_stats(
    days: int = Query(default=30, le=90),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS activity statistics."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Count interactions
    total_interactions = await db.arris_activity.count_documents({
        "creator_id": creator_id,
        "created_at": {"$gte": cutoff_date.isoformat()}
    })
    
    # Count by type
    pipeline = [
        {"$match": {"creator_id": creator_id}},
        {"$group": {"_id": "$activity_type", "count": {"$sum": 1}}}
    ]
    by_type_cursor = db.arris_activity.aggregate(pipeline)
    by_type = {doc["_id"]: doc["count"] async for doc in by_type_cursor}
    
    return {
        "total_interactions": total_interactions,
        "period_days": days,
        "by_type": by_type,
        "avg_per_day": round(total_interactions / days, 2) if days > 0 else 0
    }


@router.get("/activity-feed")
async def get_arris_activity_feed(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get real-time ARRIS activity feed.
    Feature-gated: Premium/Elite users see full feed with their queue position.
    Pro and below see limited feed without personal queue data.
    """
    auth_user = await get_any_authenticated_user(credentials)
    
    feature_gating = get_service("feature_gating")
    
    # Check tier for feature access
    has_premium = False
    if auth_user["user_type"] == "creator":
        has_premium = await feature_gating.has_advanced_analytics(auth_user["user_id"])
    
    # Get activity feed data
    arris_activity_service = get_service("arris_activity")
    if arris_activity_service:
        live_status = await arris_activity_service.get_live_status()
        
        # Get user's queue items if Premium
        my_queue_items = []
        if has_premium and auth_user["user_type"] == "creator":
            my_queue_items = await arris_activity_service.get_creator_queue_items(auth_user["user_id"])
        
        return {
            "has_premium_access": has_premium,
            "live_status": live_status,
            "my_queue_items": my_queue_items,
            "feature_highlights": [
                "Real-time queue position updates",
                "Processing time estimates",
                "Live activity feed"
            ] if not has_premium else None
        }
    
    return {
        "has_premium_access": has_premium,
        "live_status": {"status": "active"},
        "my_queue_items": [],
        "feature_highlights": None
    }


@router.get("/my-queue-position")
async def get_my_arris_queue_position(
    proposal_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the current creator's position in the ARRIS queue.
    Feature-gated: Premium/Elite only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Real-time queue position requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    arris_activity_service = get_service("arris_activity")
    
    # Get all queue items for this creator
    queue_items = await arris_activity_service.get_creator_queue_items(creator_id)
    
    # If specific proposal requested, get that position
    if proposal_id:
        position = await arris_activity_service.get_queue_position(creator_id, proposal_id)
        return {
            "proposal_id": proposal_id,
            "position": position,
            "all_items": queue_items
        }
    
    # Return all queue items
    queue_stats = await arris_activity_service.get_queue_stats()
    
    return {
        "queue_items": queue_items,
        "total_in_queue": len(queue_items),
        "queue_stats": queue_stats
    }


@router.get("/live-stats")
async def get_arris_live_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get live ARRIS processing statistics.
    Available to all authenticated users.
    """
    await get_any_authenticated_user(credentials)
    
    arris_activity_service = get_service("arris_activity")
    queue_stats = await arris_activity_service.get_queue_stats()
    
    return {
        "fast_queue": queue_stats["fast_queue_length"],
        "standard_queue": queue_stats["standard_queue_length"],
        "total_queued": queue_stats["total_queue_length"],
        "currently_processing": queue_stats["currently_processing"],
        "total_processed_today": queue_stats["total_processed"],
        "avg_processing_time": {
            "fast": queue_stats["avg_fast_time"],
            "standard": queue_stats["avg_standard_time"]
        },
        "estimated_wait": {
            "fast_queue": queue_stats["estimated_wait_fast"],
            "standard_queue": queue_stats["estimated_wait_standard"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/recent-activity")
async def get_arris_recent_activity(
    limit: int = Query(default=10, le=30),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get recent ARRIS processing activity (anonymized).
    Available to all authenticated users.
    """
    await get_any_authenticated_user(credentials)
    
    arris_activity_service = get_service("arris_activity")
    activity = await arris_activity_service.get_activity_feed(limit=limit, include_anonymous=True)
    
    return {
        "activity": activity,
        "count": len(activity)
    }


# ============== ARRIS HISTORICAL LEARNING (Premium/Elite) ==============

@router.get("/historical")
async def get_arris_historical(
    date_range: str = Query(default="all", description="Date range: 7d, 30d, 90d, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get historical learning data for ARRIS."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_historical_service = get_service("arris_historical")
    history = await arris_historical_service.get_learning_timeline(creator_id, date_range=date_range)
    
    return history


@router.get("/historical/patterns")
async def get_arris_historical_patterns(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detected patterns from historical data."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_historical_service = get_service("arris_historical")
    snapshot = await arris_historical_service.get_learning_snapshot(creator_id)
    
    return {
        "patterns": snapshot.get("active_patterns", []),
        "learning_metrics": snapshot.get("current_metrics", {}),
        "recent_activity": snapshot.get("recent_activity", [])
    }


@router.get("/learning-timeline")
async def get_arris_learning_timeline(
    date_range: str = Query(default="all", regex="^(7d|30d|90d|1y|all)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get ARRIS learning timeline for the creator.
    Shows memory accumulation, pattern discoveries, and accuracy improvements over time.
    Feature-gated: Premium/Elite only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "ARRIS Learning Timeline requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    arris_historical_service = get_service("arris_historical")
    timeline = await arris_historical_service.get_learning_timeline(creator_id, date_range)
    return timeline


@router.get("/learning-comparison")
async def get_arris_learning_comparison(
    period1: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    period2: str = Query(default="prev_30d", regex="^(prev_7d|prev_30d|prev_90d)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Compare ARRIS learning between two time periods.
    Shows growth and improvement over time.
    Feature-gated: Premium/Elite only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "ARRIS Learning Comparison requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    arris_historical_service = get_service("arris_historical")
    comparison = await arris_historical_service.get_comparative_analysis(
        creator_id, period1, period2
    )
    return comparison


@router.get("/learning-snapshot")
async def get_arris_learning_snapshot(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a snapshot of current ARRIS learning state.
    Shows memory summary, active patterns, and learning health.
    Available to all creators but Premium gets enhanced data.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    
    arris_historical_service = get_service("arris_historical")
    snapshot = await arris_historical_service.get_learning_snapshot(creator_id)
    
    # Add premium flag
    snapshot["is_premium"] = has_premium
    
    # If not premium, limit some data
    if not has_premium:
        snapshot["active_patterns"] = snapshot.get("active_patterns", [])[:3]
        snapshot["recent_activity"] = snapshot.get("recent_activity", [])[:5]
        snapshot["upgrade_prompt"] = {
            "message": "Upgrade to Premium for full learning insights",
            "features": ["Complete pattern history", "Detailed growth metrics", "Historical comparisons"]
        }
    
    return snapshot


# ============== ARRIS CHAT ==============

@router.post("/chat")
async def arris_chat(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Chat with ARRIS AI assistant."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    data = await request.json()
    message = data.get("message")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # This would integrate with the actual ARRIS chat service
    # For now, return a placeholder response
    return {
        "response": f"ARRIS received your message: {message[:100]}...",
        "creator_id": creator["id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============== ARRIS PERFORMANCE & TRAINING ==============

@router.get("/performance")
async def get_arris_performance(
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS performance reviews."""
    db = get_db()
    reviews = await db.arris_performance.find({}, {"_id": 0}).to_list(limit)
    return {"reviews": reviews, "total": len(reviews)}


@router.get("/training-status")
async def get_arris_training_status(
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS training data sources and status."""
    db = get_db()
    data = await db.arris_training_data.find({}, {"_id": 0}).to_list(limit)
    return {"training_data": data, "total": len(data)}
