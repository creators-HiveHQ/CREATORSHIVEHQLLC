"""
Waitlist Routes
===============
Public-facing waitlist signup endpoints for the landing page.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
import logging

from routes.dependencies import get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("/signup")
async def waitlist_signup(data: dict):
    """
    Public endpoint - Join the priority waitlist.
    Supports referral tracking.
    """
    email = data.get("email")
    referral_code = data.get("referral_code")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.add_to_waitlist(
        email=email,
        referral_code=referral_code
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to join waitlist"))
    
    return result


@router.get("/position")
async def get_waitlist_position(email: str = Query(...)):
    """Get position in the waitlist."""
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.get_position(email)
    
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Email not found in waitlist")
    
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
