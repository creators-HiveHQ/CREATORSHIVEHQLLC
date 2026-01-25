"""
Admin Routes
============
Admin-only endpoints for system management.
Includes: Escalation, Lifecycle, Waitlist management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service, verify_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== AUTO-ESCALATION ENDPOINTS ==============

@router.get("/escalation/dashboard")
async def get_escalation_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get escalation dashboard with summary stats and active escalations.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.get_escalation_dashboard()
    return result


@router.get("/escalation/stalled")
async def get_stalled_proposals(
    threshold_hours: int = Query(default=48, description="Minimum hours to consider stalled"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all proposals that are stalled and nearing escalation.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.get_stalled_proposals(threshold_hours=threshold_hours)
    return result


@router.get("/escalation/history")
async def get_escalation_history(
    limit: int = Query(default=50, le=100),
    include_resolved: bool = Query(default=True),
    level: str = Query(default=None, description="Filter by level: elevated, urgent, critical"),
    proposal_id: str = Query(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get escalation history with optional filters.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.get_escalation_history(
        limit=limit,
        include_resolved=include_resolved,
        level_filter=level,
        proposal_id=proposal_id
    )
    return result


@router.get("/escalation/analytics")
async def get_escalation_analytics(
    days: int = Query(default=30, le=90),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get escalation analytics and performance metrics.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.get_escalation_analytics(days=days)
    return result


@router.post("/escalation/check/{proposal_id}")
async def check_proposal_escalation(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Check if a specific proposal needs escalation.
    Returns escalation status and recommended actions.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.check_proposal(proposal_id)
    return result


@router.post("/escalation/escalate/{proposal_id}")
async def escalate_proposal(
    proposal_id: str,
    level: str = Query(default=None, description="Escalation level: elevated, urgent, critical"),
    reason: str = Query(default=None, description="Reason for escalation"),
    notes: str = Query(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Manually escalate a proposal.
    Admin only endpoint.
    """
    admin = await verify_admin(credentials)
    admin_id = admin.get("user_id", "admin")
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.escalate_proposal(
        proposal_id=proposal_id,
        level=level,
        reason=reason,
        notes=notes,
        escalated_by=admin_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Escalation failed"))
    
    return result


@router.post("/escalation/resolve/{escalation_id}")
async def resolve_escalation(
    escalation_id: str,
    resolution_notes: str = Query(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Resolve an escalation.
    Admin only endpoint.
    """
    admin = await verify_admin(credentials)
    admin_id = admin.get("user_id", "admin")
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.resolve_escalation(
        escalation_id=escalation_id,
        resolved_by=admin_id,
        resolution_notes=resolution_notes
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Resolution failed"))
    
    return result


@router.post("/escalation/scan")
async def run_escalation_scan(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Manually trigger a full escalation scan.
    Scans all proposals for escalation needs and auto-escalates as needed.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.scan_all_proposals()
    return result


@router.get("/escalation/config")
async def get_escalation_config(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current escalation configuration including thresholds.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    result = await auto_escalation_service.get_config()
    return result


@router.put("/escalation/config")
async def update_escalation_config(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update escalation configuration including thresholds.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    auto_escalation_service = get_service("auto_escalation")
    data = await request.json()
    result = await auto_escalation_service.update_config(data)
    return result


# ============== SUBSCRIPTION LIFECYCLE ENDPOINTS ==============

@router.get("/lifecycle/stats")
async def get_lifecycle_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get subscription lifecycle statistics.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    subscription_lifecycle_service = get_service("subscription_lifecycle")
    result = await subscription_lifecycle_service.get_lifecycle_stats()
    return result


@router.get("/lifecycle/at-risk")
async def get_at_risk_subscriptions(
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get subscriptions at risk of churning.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    subscription_lifecycle_service = get_service("subscription_lifecycle")
    result = await subscription_lifecycle_service.get_at_risk_subscriptions(limit=limit)
    return result


@router.get("/lifecycle/transitions")
async def get_lifecycle_transitions(
    days: int = Query(default=30),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get recent lifecycle stage transitions.
    Admin only endpoint.
    """
    await verify_admin(credentials)
    
    subscription_lifecycle_service = get_service("subscription_lifecycle")
    result = await subscription_lifecycle_service.get_recent_transitions(days=days)
    return result


@router.post("/lifecycle/{creator_id}/stage")
async def update_lifecycle_stage(
    creator_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a creator's lifecycle stage.
    Admin only endpoint.
    """
    admin = await verify_admin(credentials)
    admin_id = admin.get("user_id", "admin")
    
    data = await request.json()
    new_stage = data.get("stage")
    reason = data.get("reason", "Admin manual update")
    
    if not creator_id or not new_stage:
        raise HTTPException(status_code=400, detail="creator_id and stage are required")
    
    subscription_lifecycle_service = get_service("subscription_lifecycle")
    result = await subscription_lifecycle_service.update_lifecycle_stage(
        creator_id=creator_id,
        new_stage=new_stage,
        reason=reason,
        triggered_by=admin_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Update failed"))
    
    return result


# ============== WAITLIST MANAGEMENT ==============

@router.get("/waitlist/stats")
async def get_waitlist_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get waitlist statistics for admin dashboard."""
    await verify_admin(credentials)
    
    waitlist_service = get_service("waitlist")
    stats = await waitlist_service.get_waitlist_stats()
    return stats


@router.get("/waitlist/entries")
async def get_waitlist_entries(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    verified_only: bool = Query(default=False),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get paginated waitlist entries for admin dashboard."""
    await verify_admin(credentials)
    
    waitlist_service = get_service("waitlist")
    entries = await waitlist_service.get_all_entries(
        limit=limit,
        offset=offset,
        verified_only=verified_only
    )
    return entries


@router.post("/waitlist/invite/{email}")
async def invite_from_waitlist(
    email: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send invitation to a waitlist entry."""
    await verify_admin(credentials)
    
    waitlist_service = get_service("waitlist")
    result = await waitlist_service.send_invitation(email)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invitation failed"))
    
    return result


@router.delete("/waitlist/{email}")
async def remove_from_waitlist(
    email: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Remove an entry from the waitlist."""
    await verify_admin(credentials)
    
    db = get_db()
    result = await db.waitlist_entries.delete_one({"email": email})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return {"success": True, "message": f"Removed {email} from waitlist"}
