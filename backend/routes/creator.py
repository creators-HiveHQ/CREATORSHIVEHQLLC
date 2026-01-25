"""
Creator Routes
==============
Creator-facing endpoints.
Includes: Pattern Insights, Alerts, Health Score, Pattern Export.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service, verify_creator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creators/me", tags=["Creator"])


# ============== HELPER: Get current creator ==============

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


# ============== PATTERN INSIGHTS ENDPOINTS (Pro+) ==============

@router.get("/pattern-insights")
async def get_pattern_insights(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get pattern insights for the authenticated creator.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_pattern_insights_service = get_service("creator_pattern_insights")
    result = await creator_pattern_insights_service.get_creator_patterns(creator_id)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.get("/pattern-recommendations")
async def get_pattern_recommendations(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get personalized pattern-based recommendations.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_pattern_insights_service = get_service("creator_pattern_insights")
    result = await creator_pattern_insights_service.get_pattern_recommendations(creator_id)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.post("/pattern-feedback/{pattern_id}")
async def submit_pattern_feedback(
    pattern_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Submit feedback on a pattern insight.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    
    creator_pattern_insights_service = get_service("creator_pattern_insights")
    result = await creator_pattern_insights_service.save_pattern_feedback(
        creator_id=creator_id,
        pattern_id=pattern_id,
        feedback=data
    )
    return result


# ============== PATTERN EXPORT ENDPOINTS (Premium+) ==============

@router.get("/pattern-export/options")
async def get_pattern_export_options(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get available export options for the authenticated creator.
    Returns formats, filters, and data availability info.
    Feature-gated: Requires Premium tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    pattern_export_service = get_service("pattern_export")
    result = await pattern_export_service.get_export_options(creator_id)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.get("/pattern-export/preview")
async def get_pattern_export_preview(
    categories: str = Query(default=None, description="Comma-separated categories to filter"),
    confidence_level: str = Query(default="all"),
    date_range: str = Query(default="all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a preview of what would be exported based on filters.
    Shows counts and sample data without generating the full export.
    Feature-gated: Requires Premium tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Parse categories
    category_list = categories.split(",") if categories else None
    
    pattern_export_service = get_service("pattern_export")
    result = await pattern_export_service.get_export_preview(
        creator_id=creator_id,
        categories=category_list,
        confidence_level=confidence_level,
        date_range=date_range
    )
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.post("/pattern-export")
async def export_patterns(
    export_format: str = Query(default="json", description="Export format: json or csv"),
    categories: str = Query(default=None, description="Comma-separated categories to filter"),
    confidence_level: str = Query(default="all"),
    date_range: str = Query(default="all"),
    include_recommendations: bool = Query(default=True),
    include_trends: bool = Query(default=True),
    include_feedback: bool = Query(default=False),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export pattern analysis data in JSON or CSV format.
    Feature-gated: Requires Premium tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Parse categories
    category_list = categories.split(",") if categories else None
    
    pattern_export_service = get_service("pattern_export")
    result = await pattern_export_service.export_patterns(
        creator_id=creator_id,
        export_format=export_format,
        categories=category_list,
        confidence_level=confidence_level,
        date_range=date_range,
        include_recommendations=include_recommendations,
        include_trends=include_trends,
        include_feedback=include_feedback
    )
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Export failed"))
    
    return result


@router.get("/pattern-export/history")
async def get_pattern_export_history(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get pattern export history for the authenticated creator.
    Shows previous exports with metadata.
    Feature-gated: Requires Premium tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    pattern_export_service = get_service("pattern_export")
    result = await pattern_export_service.get_export_history(creator_id, limit=limit)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


# ============== PREDICTIVE ALERTS ENDPOINTS (Pro+) ==============

@router.get("/alerts")
async def get_creator_alerts(
    limit: int = Query(default=20, le=100),
    priority: str = Query(default=None, description="Filter by priority: urgent, high, medium, low"),
    unread_only: bool = Query(default=False),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get predictive alerts for the authenticated creator.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    predictive_alerts_service = get_service("predictive_alerts")
    result = await predictive_alerts_service.get_creator_alerts(
        creator_id=creator_id,
        limit=limit,
        priority=priority,
        unread_only=unread_only
    )
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403,
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Mark an alert as read.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    predictive_alerts_service = get_service("predictive_alerts")
    result = await predictive_alerts_service.mark_alert_read(
        creator_id=creator_id,
        alert_id=alert_id
    )
    
    if result.get("access_denied"):
        raise HTTPException(status_code=403, detail=result.get("upgrade_message"))
    
    return result


@router.post("/alerts/{alert_id}/action")
async def take_alert_action(
    alert_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Record an action taken on an alert.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    data = await request.json()
    action = data.get("action", "acknowledged")
    
    predictive_alerts_service = get_service("predictive_alerts")
    result = await predictive_alerts_service.record_alert_action(
        creator_id=creator_id,
        alert_id=alert_id,
        action=action
    )
    
    if result.get("access_denied"):
        raise HTTPException(status_code=403, detail=result.get("upgrade_message"))
    
    return result


# ============== CREATOR HEALTH SCORE ENDPOINTS (Pro+) ==============

@router.get("/health-score")
async def get_health_score(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the creator's health score dashboard.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_health_score_service = get_service("creator_health_score")
    result = await creator_health_score_service.get_health_score(creator_id)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.get("/health-score/history")
async def get_health_score_history(
    days: int = Query(default=30, le=90),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get historical health scores.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_health_score_service = get_service("creator_health_score")
    result = await creator_health_score_service.get_health_history(
        creator_id=creator_id,
        days=days
    )
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result


@router.get("/health-score/actions")
async def get_health_actions(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get recommended actions to improve health score.
    Feature-gated: Requires Pro tier or higher.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    creator_health_score_service = get_service("creator_health_score")
    result = await creator_health_score_service.get_improvement_actions(creator_id)
    
    if result.get("access_denied"):
        raise HTTPException(
            status_code=403, 
            detail=result.get("upgrade_message"),
            headers={"X-Upgrade-URL": result.get("upgrade_url", "/creator/subscription")}
        )
    
    return result
