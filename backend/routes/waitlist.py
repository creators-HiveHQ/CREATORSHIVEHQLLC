"""
Waitlist Routes
===============
Public-facing waitlist signup endpoints for the landing page.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from routes.dependencies import get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("/signup")
async def waitlist_signup(signup_data: Dict[str, Any]):
    """
    Public endpoint - Sign up for the priority waitlist.
    No authentication required.
    """
    waitlist_service = get_service("waitlist")
    
    email = signup_data.get("email", "").strip()
    name = signup_data.get("name", "").strip()
    creator_type = signup_data.get("creator_type", "").strip()
    niche = signup_data.get("niche", "").strip()
    referral_code = signup_data.get("referral_code")
    source = signup_data.get("source", "landing_page")
    
    if not email or not name or not creator_type:
        raise HTTPException(status_code=400, detail="Email, name, and creator type are required")
    
    result = await waitlist_service.signup(
        email=email,
        name=name,
        creator_type=creator_type,
        niche=niche,
        referral_code=referral_code,
        source=source
    )
    
    return result


@router.get("/position")
async def get_waitlist_position(email: str = Query(..., description="Email address")):
    """
    Public endpoint - Get current waitlist position by email.
    """
    waitlist_service = get_service("waitlist")
    
    result = await waitlist_service.get_position(email)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/stats")
async def get_public_waitlist_stats():
    """
    Public endpoint - Get basic waitlist statistics for landing page.
    Only returns non-sensitive aggregate data.
    """
    db = get_db()
    total = await db.waitlist.count_documents({})
    return {"total": total}


@router.get("/leaderboard")
async def get_public_leaderboard(limit: int = Query(default=10, le=20)):
    """
    Public endpoint - Get top referrers leaderboard.
    Names are partially masked for privacy.
    """
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.get_leaderboard(limit=limit)
    return result


@router.post("/verify")
async def verify_waitlist_email(data: dict):
    """Verify email address for waitlist entry."""
    email = data.get("email")
    code = data.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and verification code are required")
    
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.verify_email(email=email, code=code)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Verification failed"))
    
    return result


@router.get("/referral/{code}")
async def get_referral_info(code: str):
    """Get referral information by code."""
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.get_referral_info(code)
    
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Referral code not found")
    
    return result
