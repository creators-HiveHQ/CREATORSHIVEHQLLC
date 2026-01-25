"""
Referral Routes
===============
Referral system endpoints for creators and admins.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/referral", tags=["Referral System"])
admin_router = APIRouter(prefix="/admin/referral", tags=["Referral Admin"])


async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import get_current_creator as auth_get_current_creator
    return await auth_get_current_creator(credentials, db)


# ============== CREATOR REFERRAL ENDPOINTS ==============

@router.post("/generate-code")
async def generate_referral_code(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Generate a unique referral code for the authenticated creator.
    Returns an existing code if one already exists.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    result = await referral_service.generate_referral_code(creator["id"])
    return result


@router.get("/my-code")
async def get_my_referral_code(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the creator's active referral code."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    code_data = await referral_service.get_referral_code(creator["id"])
    
    if not code_data:
        raise HTTPException(
            status_code=404,
            detail="No referral code found. Generate one first."
        )
    
    return code_data


@router.get("/validate/{code}")
async def validate_referral_code(code: str):
    """
    Validate a referral code (public endpoint for registration flow).
    Returns referrer info if valid.
    """
    referral_service = get_service("referral")
    result = await referral_service.validate_referral_code(code)
    return result


@router.post("/track-click/{code}")
async def track_referral_click(
    code: str,
    request: Request
):
    """Track when a referral link is clicked (public endpoint)."""
    metadata = {
        "user_agent": request.headers.get("user-agent", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    referral_service = get_service("referral")
    result = await referral_service.track_referral_click(code, metadata)
    return result


@router.get("/my-stats")
async def get_my_referral_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get comprehensive referral statistics for the authenticated creator.
    Includes tier, earnings, conversion rates, and milestone progress.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    stats = await referral_service.get_referrer_stats(creator["id"])
    return stats


@router.get("/my-referrals")
async def get_my_referrals(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get list of referrals made by the authenticated creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    referrals = await referral_service.get_creator_referrals(
        creator_id=creator["id"],
        status=status,
        limit=limit
    )
    return {"referrals": referrals, "total": len(referrals)}


@router.get("/my-commissions")
async def get_my_commissions(
    status: Optional[str] = Query(default=None, description="Filter by commission status"),
    limit: int = Query(default=50, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all commissions earned by the authenticated creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    result = await referral_service.get_creator_commissions(
        creator_id=creator["id"],
        status=status,
        limit=limit
    )
    return result


@router.get("/leaderboard")
async def get_referral_leaderboard(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get the top referrers platform-wide."""
    referral_service = get_service("referral")
    leaderboard = await referral_service.get_referral_leaderboard(limit=limit)
    return {"leaderboard": leaderboard}


@router.get("/tier-info")
async def get_referral_tier_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get information about referral tiers and commission rates."""
    from referral_service import COMMISSION_RATES, TIER_THRESHOLDS, MILESTONE_BONUSES, ReferralTier
    
    tiers = []
    for tier in ReferralTier:
        tiers.append({
            "tier": tier.value,
            "commission_rate": COMMISSION_RATES[tier],
            "min_referrals": TIER_THRESHOLDS[tier]
        })
    
    milestones = [
        {
            "threshold": threshold,
            "bonus": info["bonus"],
            "title": info["title"],
            "description": info["description"]
        }
        for threshold, info in MILESTONE_BONUSES.items()
    ]
    
    return {
        "tiers": tiers,
        "milestones": milestones
    }


@router.post("/check-qualification")
async def check_referral_qualification(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Check if the current creator's referral qualifies (based on activity criteria).
    Triggered automatically on onboarding completion or proposal creation.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    referral_service = get_service("referral")
    result = await referral_service.check_and_qualify_referral(creator["id"])
    return result


# ============== ADMIN REFERRAL ENDPOINTS ==============

@admin_router.get("/analytics")
async def get_referral_analytics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get platform-wide referral analytics (admin only)."""
    db = get_db()
    from auth import get_current_user
    
    try:
        await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_service = get_service("referral")
    analytics = await referral_service.get_referral_analytics()
    return analytics


@admin_router.get("/pending-commissions")
async def get_pending_commissions(
    limit: int = Query(default=100, le=500),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all pending commissions awaiting admin approval."""
    db = get_db()
    from auth import get_current_user
    
    try:
        await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_service = get_service("referral")
    commissions = await referral_service.get_pending_commissions(limit=limit)
    return {"commissions": commissions, "total": len(commissions)}


@admin_router.post("/commissions/{commission_id}/approve")
async def approve_commission(
    commission_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Approve a pending commission for payout (admin only)."""
    db = get_db()
    from auth import get_current_user
    
    try:
        current_user = await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_service = get_service("referral")
    result = await referral_service.approve_commission(
        commission_id=commission_id,
        admin_id=current_user["id"]
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@admin_router.post("/commissions/{commission_id}/mark-paid")
async def mark_commission_paid(
    commission_id: str,
    payout_reference: Optional[str] = Query(default=None, description="Payment reference/transaction ID"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Mark an approved commission as paid (admin only)."""
    db = get_db()
    from auth import get_current_user
    
    try:
        current_user = await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_service = get_service("referral")
    result = await referral_service.mark_commission_paid(
        commission_id=commission_id,
        admin_id=current_user["id"],
        payout_reference=payout_reference
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@admin_router.get("/leaderboard")
async def get_admin_referral_leaderboard(
    limit: int = Query(default=50, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get full referral leaderboard with detailed stats (admin only)."""
    db = get_db()
    from auth import get_current_user
    
    try:
        await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    referral_service = get_service("referral")
    leaderboard = await referral_service.get_referral_leaderboard(limit=limit)
    return {"leaderboard": leaderboard, "total": len(leaderboard)}
