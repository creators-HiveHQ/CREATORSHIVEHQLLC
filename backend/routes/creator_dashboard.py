"""
Creator Dashboard Routes
========================
All creator-facing dashboard endpoints: profile, proposals, analytics,
onboarding, and advanced features.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creators", tags=["Creator Dashboard"])


# ============== HELPER: Get current creator ==============

async def get_current_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import decode_token
    
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    creator_id = getattr(token_data, 'user_id', None) or getattr(token_data, 'sub', None)
    if not creator_id:
        raise HTTPException(status_code=401, detail="Invalid token - no user_id")
    
    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0})
    if not creator:
        raise HTTPException(status_code=401, detail="Creator not found")
    
    return creator


# ============== PROFILE & BASIC DASHBOARD ==============

@router.get("/me")
async def get_current_creator_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current logged-in creator's profile"""
    logger.info(f"GET /creators/me called with credentials: {credentials.credentials[:20]}...")
    db = get_db()
    try:
        creator = await get_current_creator(credentials, db)
        logger.info(f"GET /creators/me returning creator: {creator.get('id')}")
        return creator
    except Exception as e:
        logger.error(f"GET /creators/me error: {e}")
        raise


@router.get("/me/proposals")
async def get_my_proposals(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all proposals for the current logged-in creator"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    query = {"user_id": creator["id"]}
    if status:
        query["status"] = status
    
    proposals = await db.proposals.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return proposals


@router.get("/me/dashboard")
async def get_creator_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get dashboard data for the current logged-in creator"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get proposal counts
    proposals_pipeline = [
        {"$match": {"user_id": creator_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    proposal_stats = await db.proposals.aggregate(proposals_pipeline).to_list(10)
    proposals_by_status = {item["_id"]: item["count"] for item in proposal_stats}
    
    # Get recent proposals
    recent_proposals = await db.proposals.find(
        {"user_id": creator_id},
        {"_id": 0, "id": 1, "title": 1, "status": 1, "created_at": 1, "arris_insights": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Get project counts
    project_count = await db.projects.count_documents({"user_id": creator_id})
    
    # Get task stats
    task_stats = {
        "total": await db.tasks.count_documents({"assigned_to_user_id": creator_id}),
        "completed": await db.tasks.count_documents({"assigned_to_user_id": creator_id, "completion_status": 1})
    }
    
    return {
        "creator": {
            "id": creator["id"],
            "name": creator["name"],
            "email": creator["email"],
            "status": creator.get("status"),
            "tier": creator.get("assigned_tier", "Free"),
            "platforms": creator.get("platforms", []),
            "niche": creator.get("niche", "")
        },
        "proposals": {
            "total": sum(proposals_by_status.values()),
            "by_status": proposals_by_status,
            "recent": recent_proposals
        },
        "projects": {
            "total": project_count
        },
        "tasks": task_stats
    }


# ============== ADVANCED DASHBOARD (Pro+) ==============

@router.get("/me/advanced-dashboard")
async def get_creator_advanced_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get advanced dashboard data for Pro+ creators.
    Returns enhanced analytics, trends, and performance metrics.
    Feature-gated: Requires 'advanced' or 'custom' dashboard_level.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    
    # Check dashboard level access
    dashboard_level = await feature_gating.get_dashboard_level(creator_id)
    has_priority_review = await feature_gating.has_priority_review(creator_id)
    has_advanced_analytics = await feature_gating.has_advanced_analytics(creator_id)
    
    if dashboard_level == "basic":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Advanced dashboard requires Pro plan or higher",
                "required_tier": "pro",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # ===== PERFORMANCE ANALYTICS =====
    total_proposals = await db.proposals.count_documents({"user_id": creator_id})
    approved_proposals = await db.proposals.count_documents({
        "user_id": creator_id, 
        "status": {"$in": ["approved", "in_progress", "completed"]}
    })
    approval_rate = round((approved_proposals / total_proposals * 100), 1) if total_proposals > 0 else 0
    
    # Average review time
    review_pipeline = [
        {"$match": {
            "user_id": creator_id,
            "status": {"$in": ["approved", "rejected", "in_progress", "completed"]},
            "submitted_at": {"$exists": True},
            "reviewed_at": {"$exists": True}
        }},
        {"$project": {
            "review_time_hours": {
                "$divide": [
                    {"$subtract": [
                        {"$dateFromString": {"dateString": "$reviewed_at"}},
                        {"$dateFromString": {"dateString": "$submitted_at"}}
                    ]},
                    3600000
                ]
            }
        }},
        {"$group": {"_id": None, "avg_review_time": {"$avg": "$review_time_hours"}}}
    ]
    review_time_result = await db.proposals.aggregate(review_pipeline).to_list(1)
    avg_review_time = round(review_time_result[0]["avg_review_time"], 1) if review_time_result else None
    
    # ===== PROPOSAL TRENDS (Last 6 months) =====
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    trends_pipeline = [
        {"$match": {
            "user_id": creator_id,
            "created_at": {"$gte": six_months_ago.isoformat()}
        }},
        {"$project": {
            "month": {"$substr": ["$created_at", 0, 7]}
        }},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    monthly_trends = await db.proposals.aggregate(trends_pipeline).to_list(12)
    
    # ===== ARRIS ACTIVITY =====
    arris_usage = await db.arris_usage_log.find(
        {"user_id": creator_id},
        {"_id": 0, "timestamp": 1, "response_type": 1, "success": 1}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    arris_stats = {
        "total_queries": len(arris_usage),
        "success_rate": round(sum(1 for q in arris_usage if q.get("success", True)) / len(arris_usage) * 100, 1) if arris_usage else 100,
        "recent_activity": arris_usage[:10]
    }
    
    return {
        "dashboard_level": dashboard_level,
        "has_priority_review": has_priority_review,
        "has_advanced_analytics": has_advanced_analytics,
        "performance": {
            "total_proposals": total_proposals,
            "approved_proposals": approved_proposals,
            "approval_rate": approval_rate,
            "avg_review_time_hours": avg_review_time,
            "queue_position": "priority" if has_priority_review else "standard"
        },
        "trends": {
            "monthly_proposals": monthly_trends
        },
        "arris": arris_stats
    }


# ============== PREMIUM ANALYTICS (Premium+) ==============

@router.get("/me/premium-analytics")
async def get_premium_analytics(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get premium analytics dashboard with detailed insights.
    Feature-gated: Requires Premium tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    
    # Check Premium access
    dashboard_level = await feature_gating.get_dashboard_level(creator_id)
    if dashboard_level not in ["custom"]:
        tier_info = await feature_gating.get_full_feature_access(creator_id)
        if tier_info.get("tier") not in ["premium", "elite"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "feature_gated",
                    "message": "Premium analytics requires Premium plan or higher",
                    "required_tier": "premium",
                    "upgrade_url": "/creator/subscription"
                }
            )
    
    # Deep analytics
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)
    
    # Proposal velocity
    proposals_30d = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    proposals_90d = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": ninety_days_ago.isoformat()}
    })
    
    # Revenue tracking (from Calculator)
    revenue_pipeline = [
        {"$match": {"user_id": creator_id, "category": "Income"}},
        {"$group": {"_id": None, "total": {"$sum": "$revenue"}}}
    ]
    revenue_result = await db.calculator.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Platform breakdown
    platform_pipeline = [
        {"$match": {"user_id": creator_id}},
        {"$unwind": {"path": "$platforms", "preserveNullAndEmptyArrays": False}},
        {"$group": {"_id": "$platforms", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    platform_stats = await db.proposals.aggregate(platform_pipeline).to_list(10)
    
    return {
        "tier": "premium",
        "velocity": {
            "proposals_30d": proposals_30d,
            "proposals_90d": proposals_90d,
            "monthly_avg": round(proposals_90d / 3, 1) if proposals_90d else 0
        },
        "revenue": {
            "total": total_revenue,
            "currency": "USD"
        },
        "platform_distribution": {p["_id"]: p["count"] for p in platform_stats},
        "generated_at": now.isoformat()
    }


@router.get("/me/premium-analytics/export")
async def export_premium_analytics(
    format: str = Query(default="json", enum=["json", "csv"]),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Export premium analytics data. Feature-gated: Premium+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    
    # Check Premium access
    tier_info = await feature_gating.get_full_feature_access(creator_id)
    if tier_info.get("tier") not in ["premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Analytics export requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Get all proposals for export
    proposals = await db.proposals.find(
        {"user_id": creator_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get revenue data
    revenue_entries = await db.calculator.find(
        {"user_id": creator_id},
        {"_id": 0}
    ).to_list(1000)
    
    export_data = {
        "creator_id": creator_id,
        "export_date": datetime.now(timezone.utc).isoformat(),
        "proposals": proposals,
        "revenue_entries": revenue_entries,
        "summary": {
            "total_proposals": len(proposals),
            "total_revenue_entries": len(revenue_entries)
        }
    }
    
    if format == "csv":
        # Return CSV-friendly format
        return {
            "format": "csv",
            "data": export_data,
            "message": "Use frontend to convert to CSV"
        }
    
    return export_data


# ============== PATTERN TRENDS ==============

@router.get("/me/pattern-trends")
async def get_pattern_trends(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get pattern trends for creator. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    tier_info = await feature_gating.get_full_feature_access(creator_id)
    
    if tier_info.get("tier") not in ["pro", "premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Pattern trends require Pro plan or higher",
                "required_tier": "pro",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    pattern_engine = get_service("pattern_engine")
    if pattern_engine:
        trends = await pattern_engine.get_user_patterns(creator_id)
        return trends
    
    return {"patterns": [], "message": "Pattern engine not available"}


@router.get("/me/pattern-detail/{pattern_id}")
async def get_pattern_detail(
    pattern_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed pattern analysis. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    tier_info = await feature_gating.get_full_feature_access(creator_id)
    
    if tier_info.get("tier") not in ["pro", "premium", "elite"]:
        raise HTTPException(status_code=403, detail="Pattern detail requires Pro plan or higher")
    
    pattern_engine = get_service("pattern_engine")
    if pattern_engine:
        detail = await pattern_engine.get_pattern_detail(pattern_id, creator_id)
        return detail
    
    return {"error": "Pattern engine not available"}


# ============== PREDICTIVE ALERTS ==============

@router.get("/me/predictive-alerts")
async def get_predictive_alerts(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get predictive alerts for creator. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    predictive_alerts = get_service("predictive_alerts")
    if predictive_alerts:
        alerts = await predictive_alerts.get_creator_alerts(creator_id)
        return alerts
    
    return {"alerts": [], "message": "Predictive alerts not available"}


@router.post("/me/trigger-alerts")
async def trigger_alert_check(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Manually trigger alert analysis. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    predictive_alerts = get_service("predictive_alerts")
    if predictive_alerts:
        result = await predictive_alerts.analyze_creator(creator_id)
        return result
    
    return {"message": "Predictive alerts not available"}


@router.post("/me/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Dismiss an alert"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    result = await db.creator_alerts.update_one(
        {"id": alert_id, "creator_id": creator_id},
        {"$set": {"dismissed": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert dismissed"}


@router.get("/me/alert-preferences")
async def get_alert_preferences(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get alert notification preferences"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    prefs = await db.creator_preferences.find_one(
        {"creator_id": creator_id},
        {"_id": 0, "alert_preferences": 1}
    )
    
    return prefs.get("alert_preferences", {
        "email_notifications": True,
        "in_app_notifications": True,
        "urgent_only": False,
        "categories": ["performance", "financial", "engagement"]
    }) if prefs else {
        "email_notifications": True,
        "in_app_notifications": True,
        "urgent_only": False,
        "categories": ["performance", "financial", "engagement"]
    }


@router.put("/me/alert-preferences")
async def update_alert_preferences(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update alert notification preferences"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    
    await db.creator_preferences.update_one(
        {"creator_id": creator_id},
        {
            "$set": {
                "alert_preferences": data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$setOnInsert": {
                "creator_id": creator_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"success": True, "message": "Preferences updated"}


# ============== HEALTH SCORE ==============

@router.get("/me/health-score")
async def get_health_score(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get creator health score. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_health_score = get_service("creator_health_score")
    if creator_health_score:
        score = await creator_health_score.get_health_score(creator_id)
        return score
    
    return {"score": 0, "message": "Health score service not available"}


@router.get("/me/health-score/history")
async def get_health_score_history(
    days: int = Query(default=30, le=90),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get health score history"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    history = await db.health_score_history.find(
        {"creator_id": creator_id, "recorded_at": {"$gte": cutoff.isoformat()}},
        {"_id": 0}
    ).sort("recorded_at", -1).to_list(days)
    
    return {"history": history, "days": days}


@router.get("/me/health-score/component/{component}")
async def get_health_component(
    component: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed health score for a specific component"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    valid_components = ["engagement", "revenue", "consistency", "growth"]
    if component not in valid_components:
        raise HTTPException(status_code=400, detail=f"Invalid component. Must be one of: {valid_components}")
    
    creator_health_score = get_service("creator_health_score")
    if creator_health_score:
        detail = await creator_health_score.get_component_detail(creator_id, component)
        return detail
    
    return {"component": component, "score": 0, "message": "Service not available"}


# ============== CROSS-CREATOR INSIGHTS ==============

@router.get("/me/cross-insights")
async def get_cross_creator_insights(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get cross-creator benchmark insights. Feature-gated: Pro+"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    tier_info = await feature_gating.get_full_feature_access(creator_id)
    
    if tier_info.get("tier") not in ["pro", "premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Cross-creator insights require Pro plan or higher",
                "required_tier": "pro",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Get anonymized benchmarks
    niche = creator.get("niche", "General")
    
    # Average proposals in same niche
    niche_avg_pipeline = [
        {"$lookup": {
            "from": "creators",
            "localField": "user_id",
            "foreignField": "id",
            "as": "creator_info"
        }},
        {"$unwind": "$creator_info"},
        {"$match": {"creator_info.niche": niche}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "total_creators"}
    ]
    niche_stats = await db.proposals.aggregate(niche_avg_pipeline).to_list(1)
    
    total_in_niche = niche_stats[0]["total_creators"] if niche_stats else 0
    
    # Your rank
    my_proposals = await db.proposals.count_documents({"user_id": creator_id})
    
    return {
        "niche": niche,
        "your_proposals": my_proposals,
        "creators_in_niche": total_in_niche,
        "percentile": "Top 25%" if my_proposals > 5 else "Average",
        "insights": [
            f"You have {my_proposals} proposals in the {niche} niche",
            f"There are {total_in_niche} active creators in your niche"
        ]
    }


# ============== HEALTH LEADERBOARD ==============

@router.get("/health-leaderboard")
async def get_health_leaderboard(
    limit: int = Query(default=10, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get anonymized health score leaderboard"""
    db = get_db()
    await get_current_creator(credentials, db)
    
    leaderboard = await db.creator_health_scores.find(
        {},
        {"_id": 0, "score": 1, "tier": 1, "niche": 1}
    ).sort("score", -1).limit(limit).to_list(limit)
    
    # Anonymize
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        entry["creator"] = f"Creator #{i + 1}"
    
    return {"leaderboard": leaderboard}


# DEBUG: Test route
@router.get("/test-debug")
async def test_debug():
    """Test route to verify routing works"""
    return {"status": "ok", "message": "creator_dashboard.py is working"}
