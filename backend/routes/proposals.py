"""
Proposals Routes
================
Project proposal management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import random

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["Proposals"])


# Import models - these are defined in server.py, we'll need to access them
# For now, we'll use Dict[str, Any] and handle validation in the endpoint

async def get_any_authenticated_user(credentials: HTTPAuthorizationCredentials, db):
    """Get any authenticated user (admin or creator)."""
    from auth import get_current_user, get_current_creator, decode_token
    
    token_data = decode_token(credentials.credentials)
    
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    role = getattr(token_data, 'role', 'admin')
    
    if role == "creator":
        try:
            creator = await get_current_creator(credentials, db)
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


@router.get("/form-options")
async def get_proposal_form_options():
    """Get options for the project proposal form"""
    from models_creator import PLATFORM_OPTIONS
    from models_proposal import TIMELINE_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS, ARRIS_PROJECT_QUESTIONS
    
    return {
        "platforms": PLATFORM_OPTIONS,
        "timelines": TIMELINE_OPTIONS,
        "priorities": PRIORITY_OPTIONS,
        "statuses": STATUS_OPTIONS,
        "arris_question": random.choice(ARRIS_PROJECT_QUESTIONS)
    }


@router.get("")
async def get_proposals(
    status: str = Query(default=None, description="Filter by status"),
    user_id: str = Query(default=None, description="Filter by user/creator ID"),
    limit: int = Query(default=50, le=100),
    skip: int = Query(default=0),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all proposals with optional filters (admin or own proposals for creators)"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    query = {}
    
    # Creators can only see their own proposals
    if auth_user["user_type"] == "creator":
        query["user_id"] = auth_user["user_id"]
    elif user_id:
        query["user_id"] = user_id
    
    if status:
        query["status"] = status
    
    proposals = await db.proposals.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.proposals.count_documents(query)
    
    return {
        "proposals": proposals,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/stats")
async def get_proposal_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get proposal statistics"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    query = {}
    if auth_user["user_type"] == "creator":
        query["user_id"] = auth_user["user_id"]
    
    total = await db.proposals.count_documents(query)
    
    status_counts = {}
    for status in ["draft", "submitted", "under_review", "approved", "rejected", "in_progress", "completed"]:
        status_query = {**query, "status": status}
        status_counts[status] = await db.proposals.count_documents(status_query)
    
    return {
        "total": total,
        "by_status": status_counts
    }


@router.get("/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific proposal"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Creators can only view their own proposals
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return proposal


@router.post("/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Submit a draft proposal for review"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Check ownership for creators
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if proposal.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft proposals can be submitted")
    
    # Update status
    await db.proposals.update_one(
        {"id": proposal_id},
        {
            "$set": {
                "status": "submitted",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$push": {
                "status_history": {
                    "status": "submitted",
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                    "changed_by": auth_user["user_id"]
                }
            }
        }
    )
    
    return {"success": True, "message": "Proposal submitted for review", "status": "submitted"}


@router.put("/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a proposal"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Check ownership for creators
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    data = await request.json()
    
    # Remove fields that shouldn't be updated directly
    protected_fields = ["id", "proposal_id", "user_id", "created_at"]
    for field in protected_fields:
        data.pop(field, None)
    
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.proposals.update_one(
        {"id": proposal_id},
        {"$set": data}
    )
    
    updated = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    return updated


@router.delete("/{proposal_id}")
async def delete_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a proposal (admin only or own draft)"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Creators can only delete their own drafts
    if auth_user["user_type"] == "creator":
        if proposal.get("user_id") != auth_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if proposal.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft proposals")
    
    await db.proposals.delete_one({"id": proposal_id})
    
    return {"success": True, "message": "Proposal deleted"}


@router.post("/{proposal_id}/status")
async def update_proposal_status(
    proposal_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update proposal status (admin only)"""
    db = get_db()
    from auth import get_current_user
    
    # Admin only
    try:
        admin = await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    data = await request.json()
    new_status = data.get("status")
    notes = data.get("notes", "")
    
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    valid_statuses = ["draft", "submitted", "under_review", "approved", "rejected", "in_progress", "completed", "needs_revision"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if notes:
        update_data["admin_notes"] = notes
    
    await db.proposals.update_one(
        {"id": proposal_id},
        {
            "$set": update_data,
            "$push": {
                "status_history": {
                    "status": new_status,
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                    "changed_by": admin.get("user_id", "admin"),
                    "notes": notes
                }
            }
        }
    )
    
    return {"success": True, "message": f"Status updated to {new_status}", "status": new_status}
