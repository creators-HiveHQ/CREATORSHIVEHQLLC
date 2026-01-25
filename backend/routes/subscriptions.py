"""
Subscriptions Routes
====================
Subscription management, Stripe checkout, billing, and admin subscription endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
admin_router = APIRouter(prefix="/admin/subscriptions", tags=["Subscriptions Admin"])


async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import get_current_creator as auth_get_current_creator
    return await auth_get_current_creator(credentials, db)


async def get_current_admin(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated admin."""
    from auth import get_current_user
    return await get_current_user(credentials, db)


# ============== PUBLIC SUBSCRIPTION ENDPOINTS ==============

@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans (public endpoint)"""
    from models import SUBSCRIPTION_PLANS, SubscriptionTier
    
    plans = []
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        plan_info = {
            "plan_id": plan_id,
            "name": plan["name"],
            "tier": plan["tier"].value if isinstance(plan["tier"], SubscriptionTier) else plan["tier"],
            "features": plan["features"],
            "description": plan["description"]
        }
        
        if plan_id == "free":
            plan_info["price"] = 0.0
        elif plan_id == "elite":
            plan_info["billing_cycle"] = None
            plan_info["price"] = 0
            plan_info["is_custom"] = True
        else:
            plan_info["billing_cycle"] = plan.get("billing_cycle", "monthly")
            plan_info["price"] = plan["price"]
            plan_info["monthly_equivalent"] = plan.get("monthly_equivalent")
            plan_info["savings"] = plan.get("savings")
            plan_info["is_popular"] = plan_id == "pro_monthly"
        
        plans.append(plan_info)
    
    return {"plans": plans}


@router.get("/revenue")
async def get_subscription_revenue_public():
    """Get total subscription revenue - Self-Funding Loop Report"""
    db = get_db()
    
    pipeline = [
        {"$match": {"source": {"$regex": "Subscription", "$options": "i"}}},
        {"$group": {
            "_id": None,
            "total_subscription_revenue": {"$sum": "$revenue"},
            "active_subscriptions": {"$sum": 1}
        }}
    ]
    result = await db.calculator.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "total_subscription_revenue": result[0]["total_subscription_revenue"],
            "active_subscriptions": result[0]["active_subscriptions"],
            "self_funding_status": "active"
        }
    
    return {
        "total_subscription_revenue": 0,
        "active_subscriptions": 0,
        "self_funding_status": "initializing"
    }


# ============== CREATOR SUBSCRIPTION ENDPOINTS ==============

@router.get("/me")
async def get_my_subscription(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current creator's subscription details."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    feature_access = await feature_gating.get_full_feature_access(creator_id)
    
    subscription = await db.creator_subscriptions.find_one(
        {"creator_id": creator_id, "status": "active"},
        {"_id": 0}
    )
    
    return {
        "subscription": subscription,
        "tier": feature_access.get("tier", "free"),
        "plan_id": feature_access.get("plan_id", "free"),
        "features": feature_access.get("features", {}),
        "subscription_active": feature_access.get("subscription_active", False),
        "current_period_end": feature_access.get("current_period_end"),
        "lifecycle_stage": feature_access.get("lifecycle_stage"),
        "lifecycle_updated_at": feature_access.get("lifecycle_updated_at")
    }


@router.get("/my-status")
async def get_my_subscription_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current subscription status for logged-in creator"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    feature_access = await feature_gating.get_full_feature_access(creator_id)
    
    features = feature_access.get("features", {})
    
    return {
        "has_subscription": feature_access.get("subscription_active", False),
        "tier": feature_access.get("tier", "free"),
        "plan_id": feature_access.get("plan_id", "free"),
        "current_period_end": feature_access.get("current_period_end"),
        "features": features,
        # Proposal limits
        "proposals_per_month": features.get("proposals_per_month", 1),
        "proposals_used": features.get("proposals_used", 0),
        "proposals_remaining": features.get("proposals_remaining", 1),
        "can_create_proposal": features.get("can_create_proposal", True),
        # ARRIS access
        "arris_insight_level": features.get("arris_insight_level", "summary_only"),
        "can_use_arris": features.get("arris_insight_level") != "none",
        # Dashboard
        "dashboard_level": features.get("dashboard_level", "basic"),
        "advanced_analytics": features.get("advanced_analytics", False),
        # Review & Support
        "priority_review": features.get("priority_review", False),
        "support_level": features.get("support_level", "community"),
        # API
        "api_access": features.get("api_access", False)
    }


@router.get("/me/features")
async def get_my_features(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get detailed feature access for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    feature_gating = get_service("feature_gating")
    return await feature_gating.get_full_feature_access(creator["id"])


@router.get("/feature-access")
async def get_feature_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get detailed feature access for the logged-in creator"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    feature_gating = get_service("feature_gating")
    return await feature_gating.get_full_feature_access(creator["id"])


@router.get("/can-create-proposal")
async def check_can_create_proposal(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check if creator can create a new proposal this month"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    feature_gating = get_service("feature_gating")
    return await feature_gating.can_create_proposal(creator["id"])


@router.get("/me/usage")
async def get_my_usage(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get usage statistics for the current subscription period."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    feature_access = await feature_gating.get_full_feature_access(creator_id)
    features = feature_access.get("features", {})
    
    # Get proposal count this month
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    proposals_this_month = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    # Get ARRIS interactions this month
    arris_interactions = await db.arris_activity.count_documents({
        "creator_id": creator_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    return {
        "period_start": month_start.isoformat(),
        "proposals": {
            "used": proposals_this_month,
            "limit": features.get("proposals_per_month", 1),
            "remaining": max(0, features.get("proposals_per_month", 1) - proposals_this_month)
        },
        "arris_interactions": arris_interactions,
        "tier": feature_access.get("tier", "free")
    }


@router.get("/me/billing-history")
async def get_my_billing_history(
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get billing/payment history for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    transactions = await db.payment_transactions.find(
        {"creator_id": creator["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"transactions": transactions, "total": len(transactions)}


@router.get("/my-transactions")
async def get_my_transactions(
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get payment transactions for logged-in creator"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    transactions = await db.payment_transactions.find(
        {"creator_id": creator["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"transactions": transactions, "total": len(transactions)}


# ============== STRIPE CHECKOUT ENDPOINTS ==============

@router.post("/checkout")
async def create_subscription_checkout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create Stripe checkout session for subscription"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    body = await request.json()
    plan_id = body.get("plan_id")
    origin_url = body.get("origin_url")
    
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")
    
    # Build webhook URL from request
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_service = get_service("stripe")
    
    try:
        result = await stripe_service.create_checkout_session(
            plan_id=plan_id,
            origin_url=origin_url,
            creator_id=creator["id"],
            creator_email=creator["email"],
            webhook_url=webhook_url
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of a checkout session (for polling)"""
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_service = get_service("stripe")
    
    try:
        result = await stripe_service.get_checkout_status(session_id, webhook_url)
        return result
        
    except Exception as e:
        logger.error(f"Checkout status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get checkout status")


# ============== SUBSCRIPTION UPGRADE/CANCEL ==============

@router.post("/me/upgrade")
async def upgrade_subscription(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Request subscription upgrade."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    body = await request.json()
    target_plan = body.get("plan_id")
    
    if not target_plan:
        raise HTTPException(status_code=400, detail="plan_id is required")
    
    # For now, return upgrade instructions
    # Full implementation would integrate with Stripe subscription update
    return {
        "message": "Upgrade request received",
        "current_plan": creator.get("subscription_tier", "free"),
        "target_plan": target_plan,
        "action": "Please complete checkout for the new plan",
        "checkout_url": f"/creator/subscription?upgrade={target_plan}"
    }


@router.post("/me/cancel")
async def cancel_subscription(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Request subscription cancellation."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    body = await request.json()
    reason = body.get("reason", "")
    
    # Update subscription status
    result = await db.creator_subscriptions.update_one(
        {"creator_id": creator_id, "status": "active"},
        {
            "$set": {
                "cancel_requested": True,
                "cancel_reason": reason,
                "cancel_requested_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return {
        "message": "Cancellation request received",
        "note": "Your subscription will remain active until the end of the current billing period"
    }


# ============== GENERIC SUBSCRIPTIONS CRUD ==============

@router.get("")
async def get_subscriptions(
    user_id: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get subscriptions (generic CRUD)"""
    db = get_db()
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if tier:
        query["tier"] = tier
    if status:
        query["payment_status"] = status
    
    subs = await db.subscriptions.find(query, {"_id": 0}).to_list(limit)
    return subs


@router.post("")
async def create_subscription(request: Request):
    """Create subscription - Automatically links to Calculator for Self-Funding Loop"""
    from models import Subscription, SubscriptionCreate, Calculator
    
    db = get_db()
    body = await request.json()
    
    sub = SubscriptionCreate(**body)
    sub_obj = Subscription(**sub.model_dump())
    sub_obj.subscription_id = sub_obj.id
    
    # Self-Funding Loop: Create Calculator entry for subscription revenue
    if sub_obj.monthly_cost > 0:
        calc_entry = Calculator(
            user_id=sub_obj.user_id,
            month_year=datetime.now(timezone.utc).strftime("%Y-%m"),
            revenue=sub_obj.monthly_cost,
            expenses=0.0,
            net_margin=sub_obj.monthly_cost,
            category="Income",
            source=f"Subscription: {sub_obj.plan_name}",
            subscription_id=sub_obj.id
        )
        calc_entry.calc_id = calc_entry.id
        calc_doc = calc_entry.model_dump()
        calc_doc['created_at'] = calc_doc['created_at'].isoformat()
        calc_doc['updated_at'] = calc_doc['updated_at'].isoformat()
        await db.calculator.insert_one(calc_doc)
        sub_obj.linked_calc_id = calc_entry.id
    
    doc = sub_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['start_date'] = doc['start_date'].isoformat() if doc['start_date'] else None
    doc['next_renewal'] = doc['next_renewal'].isoformat() if doc['next_renewal'] else None
    await db.subscriptions.insert_one(doc)
    
    return {
        "id": sub_obj.id, 
        "message": "Subscription created",
        "linked_calc_id": sub_obj.linked_calc_id,
        "self_funding_loop": "Revenue routed to Calculator"
    }


# ============== ADMIN SUBSCRIPTION ENDPOINTS ==============

@admin_router.get("")
async def get_all_subscriptions(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin: Get all subscriptions"""
    db = get_db()
    await get_current_admin(credentials, db)
    
    query = {}
    if status:
        query["status"] = status
    if tier:
        query["tier"] = tier
    
    subscriptions = await db.creator_subscriptions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"subscriptions": subscriptions, "total": len(subscriptions)}


@admin_router.get("/stats")
async def get_subscription_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin: Get subscription statistics."""
    db = get_db()
    await get_current_admin(credentials, db)
    
    # Count by tier
    tier_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
    ]
    tier_counts = await db.creator_subscriptions.aggregate(tier_pipeline).to_list(10)
    
    # Total active
    total_active = await db.creator_subscriptions.count_documents({"status": "active"})
    
    # Revenue stats
    revenue_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    revenue_result = await db.payment_transactions.aggregate(revenue_pipeline).to_list(1)
    
    return {
        "by_tier": {item["_id"]: item["count"] for item in tier_counts if item["_id"]},
        "total_active": total_active,
        "total_revenue": revenue_result[0]["total"] if revenue_result else 0,
        "total_transactions": revenue_result[0]["count"] if revenue_result else 0
    }


@admin_router.get("/revenue")
async def get_subscription_revenue(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin: Get subscription revenue summary"""
    db = get_db()
    await get_current_admin(credentials, db)
    
    # Total revenue from subscriptions
    revenue_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "total_transactions": {"$sum": 1}
        }}
    ]
    revenue_result = await db.payment_transactions.aggregate(revenue_pipeline).to_list(1)
    
    # Revenue by plan
    plan_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$plan_id",
            "revenue": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    plan_revenue = await db.payment_transactions.aggregate(plan_pipeline).to_list(10)
    
    # Active subscriptions by tier
    tier_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
    ]
    tier_counts = await db.creator_subscriptions.aggregate(tier_pipeline).to_list(5)
    
    # Monthly recurring revenue (MRR) estimate
    mrr_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {
            "_id": None,
            "mrr": {"$sum": "$monthly_amount"}
        }}
    ]
    mrr_result = await db.creator_subscriptions.aggregate(mrr_pipeline).to_list(1)
    
    return {
        "total_revenue": revenue_result[0]["total_revenue"] if revenue_result else 0,
        "total_transactions": revenue_result[0]["total_transactions"] if revenue_result else 0,
        "by_plan": {item["_id"]: {"revenue": item["revenue"], "count": item["count"]} for item in plan_revenue if item["_id"]},
        "active_by_tier": {item["_id"]: item["count"] for item in tier_counts if item["_id"]},
        "mrr": mrr_result[0]["mrr"] if mrr_result else 0
    }
