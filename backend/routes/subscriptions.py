"""
Subscriptions Routes
====================
Subscription management and Stripe integration endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import get_current_creator as auth_get_current_creator
    return await auth_get_current_creator(credentials, db)


# ============== PUBLIC SUBSCRIPTION ENDPOINTS ==============

@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans (public)."""
    from subscription_service import SUBSCRIPTION_PLANS
    
    plans = []
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        plans.append({
            "id": plan_id,
            **plan_data,
            "features_summary": plan_data.get("features", {})
        })
    
    return {"plans": plans}


@router.get("/revenue")
async def get_subscription_revenue_public():
    """Get total subscription revenue - Self-Funding Loop Report (public stats)."""
    db = get_db()
    
    # Calculate total revenue from completed payments
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await db.subscription_payments.aggregate(pipeline).to_list(1)
    total_revenue = result[0]["total"] if result else 0
    
    # Count active subscriptions
    active_count = await db.creator_subscriptions.count_documents({"status": "active"})
    
    return {
        "total_revenue": total_revenue,
        "active_subscriptions": active_count,
        "self_funding_loop": "Active"
    }


# ============== CREATOR SUBSCRIPTION ENDPOINTS ==============

@router.get("/me")
async def get_my_subscription(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current creator's subscription details."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    subscription = await db.creator_subscriptions.find_one(
        {"creator_id": creator_id},
        {"_id": 0}
    )
    
    if not subscription:
        return {
            "has_subscription": False,
            "tier": "free",
            "message": "No active subscription"
        }
    
    return {
        "has_subscription": True,
        **subscription
    }


@router.get("/me/features")
async def get_my_features(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get features available for the creator's current tier."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating") if "feature_gating" in str(get_service.__doc__) else None
    
    try:
        feature_gating_svc = get_service("feature_gating")
        tier, features = await feature_gating_svc.get_creator_tier(creator_id)
        
        return {
            "tier": tier.value if hasattr(tier, 'value') else tier,
            "features": features
        }
    except HTTPException:
        return {
            "tier": "free",
            "features": {}
        }


@router.post("/me/upgrade")
async def request_upgrade(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Request a subscription upgrade."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    target_plan = data.get("plan_id")
    payment_method = data.get("payment_method_id")
    
    if not target_plan:
        raise HTTPException(status_code=400, detail="Plan ID is required")
    
    stripe_service = get_service("stripe")
    result = await stripe_service.create_subscription(
        creator_id=creator_id,
        plan_id=target_plan,
        payment_method_id=payment_method
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Upgrade failed"))
    
    return result


@router.post("/me/cancel")
async def cancel_subscription(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel current subscription."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    reason = data.get("reason", "Not specified")
    
    stripe_service = get_service("stripe")
    result = await stripe_service.cancel_subscription(
        creator_id=creator_id,
        reason=reason
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cancellation failed"))
    
    return result


@router.get("/me/billing-history")
async def get_billing_history(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get billing/payment history for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    payments = await db.subscription_payments.find(
        {"creator_id": creator_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"payments": payments, "total": len(payments)}


@router.get("/me/usage")
async def get_subscription_usage(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current usage metrics against subscription limits."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get current month's proposal count
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    proposals_this_month = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    # Get ARRIS queries
    arris_queries = await db.arris_usage_log.count_documents({
        "user_id": creator_id,
        "timestamp": {"$gte": month_start.isoformat()}
    })
    
    # Get tier limits
    try:
        feature_gating = get_service("feature_gating")
        tier, features = await feature_gating.get_creator_tier(creator_id)
        tier_value = tier.value if hasattr(tier, 'value') else tier
    except HTTPException:
        tier_value = "free"
        features = {}
    
    # Default limits by tier
    limits = {
        "free": {"proposals": 3, "arris_queries": 50},
        "starter": {"proposals": 10, "arris_queries": 200},
        "pro": {"proposals": 50, "arris_queries": 1000},
        "premium": {"proposals": 200, "arris_queries": 5000},
        "elite": {"proposals": -1, "arris_queries": -1}  # -1 = unlimited
    }
    
    tier_limits = limits.get(tier_value, limits["free"])
    
    return {
        "tier": tier_value,
        "usage": {
            "proposals": proposals_this_month,
            "arris_queries": arris_queries
        },
        "limits": tier_limits,
        "period": "monthly",
        "period_start": month_start.isoformat()
    }


# ============== ADMIN SUBSCRIPTION ENDPOINTS ==============

@router.get("/admin/stats")
async def get_admin_subscription_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get subscription statistics for admin dashboard."""
    db = get_db()
    from auth import get_current_user
    
    # Admin only
    try:
        await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Count by tier
    tier_counts = {}
    for tier in ["free", "starter", "pro", "premium", "elite"]:
        count = await db.creator_subscriptions.count_documents({"plan_id": {"$regex": tier}})
        tier_counts[tier] = count
    
    # Total revenue
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.subscription_payments.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Monthly recurring revenue (MRR)
    mrr_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": None, "mrr": {"$sum": "$monthly_amount"}}}
    ]
    mrr_result = await db.creator_subscriptions.aggregate(mrr_pipeline).to_list(1)
    mrr = mrr_result[0]["mrr"] if mrr_result else 0
    
    return {
        "by_tier": tier_counts,
        "total_revenue": total_revenue,
        "mrr": mrr,
        "active_subscriptions": sum(tier_counts.values())
    }


@router.get("/admin/revenue")
async def get_admin_revenue_details(
    days: int = Query(default=30, le=90),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed revenue breakdown for admin."""
    db = get_db()
    from auth import get_current_user
    
    # Admin only
    try:
        await get_current_user(credentials, db)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Daily revenue
    pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": cutoff.isoformat()}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily = await db.subscription_payments.aggregate(pipeline).to_list(days)
    
    # By plan
    plan_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": cutoff.isoformat()}}},
        {"$group": {"_id": "$plan_id", "amount": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"amount": -1}}
    ]
    by_plan = await db.subscription_payments.aggregate(plan_pipeline).to_list(10)
    
    return {
        "period_days": days,
        "daily_revenue": daily,
        "by_plan": by_plan
    }
