"""
ARRIS Routes
============
ARRIS AI endpoints for memory, voice, activity, and historical learning.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging
import uuid

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/arris", tags=["ARRIS"])


async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    import jwt
    token = credentials.credentials
    try:
        payload = jwt.decode(token, "secret-key-change-in-production", algorithms=["HS256"])
        creator_id = payload.get("user_id")
        
        if not creator_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        creator = await db.creators.find_one({"id": creator_id}, {"_id": 0})
        if not creator:
            raise HTTPException(status_code=401, detail="Creator not found")
        
        return creator
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============== ARRIS MEMORY ENDPOINTS ==============

@router.get("/memory")
async def get_arris_memory(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS memory entries for the authenticated creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    memory = await arris_memory_service.get_creator_memory(creator_id)
    
    return memory


@router.post("/memory")
async def add_arris_memory(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Add a memory entry for ARRIS."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    memory_type = data.get("type", "preference")
    content = data.get("content")
    context = data.get("context")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    arris_memory_service = get_service("arris_memory")
    result = await arris_memory_service.add_memory(
        creator_id=creator_id,
        memory_type=memory_type,
        content=content,
        context=context
    )
    
    return result


@router.delete("/memory/{memory_id}")
async def delete_arris_memory(
    memory_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a specific memory entry."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    result = await arris_memory_service.delete_memory(creator_id, memory_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Memory entry not found")
    
    return result


@router.get("/memory/summary")
async def get_arris_memory_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a summary of ARRIS memory for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_memory_service = get_service("arris_memory")
    summary = await arris_memory_service.get_memory_summary(creator_id)
    
    return summary


# ============== ARRIS ACTIVITY FEED ==============

@router.get("/activity")
async def get_arris_activity(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS activity feed for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    activities = await db.arris_usage_log.find(
        {"user_id": creator_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
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
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Count interactions
    total = await db.arris_usage_log.count_documents({
        "user_id": creator_id,
        "timestamp": {"$gte": cutoff.isoformat()}
    })
    
    # Count by category
    pipeline = [
        {"$match": {"user_id": creator_id, "timestamp": {"$gte": cutoff.isoformat()}}},
        {"$group": {"_id": "$query_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_category = await db.arris_usage_log.aggregate(pipeline).to_list(20)
    
    return {
        "total_interactions": total,
        "period_days": days,
        "by_category": {item["_id"]: item["count"] for item in by_category if item["_id"]}
    }


# ============== ARRIS HISTORICAL LEARNING ==============

@router.get("/historical")
async def get_arris_historical(
    limit: int = Query(default=10, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get historical learning data for ARRIS."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    arris_historical_service = get_service("arris_historical")
    history = await arris_historical_service.get_creator_history(creator_id, limit=limit)
    
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
    patterns = await arris_historical_service.get_patterns(creator_id)
    
    return patterns


# ============== ARRIS CHAT/QUERY ==============

@router.post("/chat")
async def arris_chat(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send a message to ARRIS and get a response."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    message = data.get("message")
    context = data.get("context", {})
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Log the interaction
    log_entry = {
        "id": f"ARRIS-CHAT-{uuid.uuid4().hex[:8].upper()}",
        "log_id": f"ARRIS-CHAT-{uuid.uuid4().hex[:8].upper()}",
        "user_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_query_snippet": message[:100],
        "response_type": "Chat",
        "query_category": "General",
        "success": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.arris_usage_log.insert_one(log_entry)
    
    # Generate response (this would typically call an LLM service)
    response = {
        "message": f"I understand you're asking about: {message[:50]}... Let me help you with that.",
        "suggestions": [
            "Would you like me to analyze your recent proposals?",
            "I can help you optimize your content strategy.",
            "Let me know if you need help with a specific project."
        ],
        "context_used": bool(context)
    }
    
    return response


# ============== ARRIS PERFORMANCE ==============

@router.get("/performance")
async def get_arris_performance(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS performance metrics for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get interaction counts
    total_interactions = await db.arris_usage_log.count_documents({"user_id": creator_id})
    
    # Get recent success rate
    recent = await db.arris_usage_log.find(
        {"user_id": creator_id},
        {"_id": 0, "success": 1}
    ).sort("timestamp", -1).limit(100).to_list(100)
    
    successful = len([r for r in recent if r.get("success", True)])
    success_rate = (successful / len(recent) * 100) if recent else 100
    
    return {
        "total_interactions": total_interactions,
        "recent_success_rate": round(success_rate, 1),
        "status": "operational"
    }


@router.get("/training-status")
async def get_arris_training_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get ARRIS training/learning status."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get memory count
    memory_count = await db.arris_memory.count_documents({"creator_id": creator_id})
    
    # Get interaction count
    interaction_count = await db.arris_usage_log.count_documents({"user_id": creator_id})
    
    # Calculate training level
    if interaction_count < 10:
        level = "learning"
        progress = min(interaction_count * 10, 100)
    elif interaction_count < 50:
        level = "adapting"
        progress = min((interaction_count - 10) * 2.5, 100)
    else:
        level = "optimized"
        progress = 100
    
    return {
        "level": level,
        "progress": progress,
        "memory_entries": memory_count,
        "total_interactions": interaction_count,
        "personalization_score": min(memory_count * 5 + interaction_count, 100)
    }
