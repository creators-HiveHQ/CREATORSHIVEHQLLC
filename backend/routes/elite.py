"""
Elite Routes
=============
Elite tier feature endpoints including:
- Custom ARRIS Workflows
- Brand Integrations
- Elite Dashboard
- Adaptive Intelligence
- ARRIS Personas
- Scheduled Reports
- ARRIS API Access
- Multi-Brand Management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/elite", tags=["Elite Features"])


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


async def check_elite_access(creator_id: str) -> Dict[str, Any]:
    """Check if creator has Elite tier access."""
    feature_gating = get_service("feature_gating")
    access = await feature_gating.get_full_feature_access(creator_id)
    
    if not access.get("features", {}).get("custom_arris_workflows"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "This feature requires Elite plan",
                "required_tier": "elite",
                "upgrade_url": "/creator/subscription"
            }
        )
    return access


# ============== ELITE STATUS ==============

@router.get("/status")
async def get_elite_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get Elite tier feature status for the current creator.
    Returns which Elite features are available.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    feature_gating = get_service("feature_gating")
    tier, features = await feature_gating.get_creator_tier(creator_id)
    is_elite = await feature_gating.is_elite_tier(creator_id)
    
    return {
        "is_elite": is_elite,
        "tier": tier.value if hasattr(tier, 'value') else tier,
        "elite_features": {
            "custom_arris_workflows": features.get("custom_arris_workflows", False),
            "brand_integrations": features.get("brand_integrations", False),
            "custom_dashboard": features.get("dashboard_level") == "custom",
            "adaptive_intelligence": is_elite,
            "high_touch_onboarding": features.get("high_touch_onboarding", False),
            "dedicated_support": features.get("support_level") == "dedicated"
        },
        "upgrade_url": "/creator/subscription" if not is_elite else None,
        "contact_sales": "sales@hivehq.com" if not is_elite else None
    }


# ============== CUSTOM ARRIS WORKFLOWS ==============

@router.get("/workflows")
async def get_elite_workflows(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all custom ARRIS workflows for the Elite creator.
    Feature-gated: Elite tier only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    workflows = await elite_service.get_workflows(creator_id)
    return {
        "workflows": workflows,
        "total": len(workflows),
        "default_workflow": next((w for w in workflows if w.get("is_default")), None)
    }


@router.post("/workflows")
async def create_elite_workflow(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new custom ARRIS workflow.
    Feature-gated: Elite tier only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    workflow_data = await request.json()
    elite_service = get_service("elite")
    result = await elite_service.create_workflow(creator_id, workflow_data)
    return {"message": "Workflow created", "workflow": result}


@router.get("/workflows/{workflow_id}")
async def get_elite_workflow(
    workflow_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific custom workflow"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    workflow = await elite_service.get_workflow(creator_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow


@router.put("/workflows/{workflow_id}")
async def update_elite_workflow(
    workflow_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a custom workflow"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    updates = await request.json()
    elite_service = get_service("elite")
    result = await elite_service.update_workflow(creator_id, workflow_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"message": "Workflow updated", "workflow": result}


@router.delete("/workflows/{workflow_id}")
async def delete_elite_workflow(
    workflow_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a custom workflow"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    deleted = await elite_service.delete_workflow(creator_id, workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"message": "Workflow deleted", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/run")
async def run_elite_workflow(
    workflow_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Run a custom workflow on a specific proposal.
    Generates enhanced ARRIS insights based on workflow configuration.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    data = await request.json()
    proposal_id = data.get("proposal_id")
    
    # Get the proposal
    proposal = await db.proposals.find_one(
        {"id": proposal_id, "user_id": creator_id},
        {"_id": 0}
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    elite_service = get_service("elite")
    result = await elite_service.run_workflow(creator_id, workflow_id, proposal)
    
    return {
        "message": "Workflow executed successfully",
        "result": result
    }


# ============== BRAND INTEGRATIONS ==============

@router.get("/brands")
async def get_brand_integrations(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all brand integrations/partnerships.
    Feature-gated: Elite tier only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    integrations = await elite_service.get_brand_integrations(creator_id, status)
    analytics = await elite_service.get_brand_analytics(creator_id)
    
    return {
        "integrations": integrations,
        "total": len(integrations),
        "analytics": analytics
    }


@router.post("/brands")
async def create_brand_integration(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new brand integration"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    brand_data = await request.json()
    elite_service = get_service("elite")
    result = await elite_service.create_brand_integration(creator_id, brand_data)
    return {"message": "Brand integration created", "brand": result}


@router.get("/brands/{brand_id}")
async def get_brand_integration(
    brand_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific brand integration"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    integration = await elite_service.get_brand_integration(creator_id, brand_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return integration


@router.put("/brands/{brand_id}")
async def update_brand_integration(
    brand_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a brand integration"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    updates = await request.json()
    update_data = {k: v for k, v in updates.items() if v is not None}
    
    elite_service = get_service("elite")
    result = await elite_service.update_brand_integration(creator_id, brand_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return {"message": "Brand integration updated", "brand": result}


@router.delete("/brands/{brand_id}")
async def delete_brand_integration(
    brand_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a brand integration"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    deleted = await elite_service.delete_brand_integration(creator_id, brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return {"message": "Brand integration deleted", "brand_id": brand_id}


@router.get("/brands/analytics/summary")
async def get_brand_analytics_summary(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get brand partnership analytics summary"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    analytics = await elite_service.get_brand_analytics(creator_id)
    return analytics


# ============== ELITE DASHBOARD ==============

@router.get("/dashboard")
async def get_elite_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get Elite dashboard configuration and data.
    Feature-gated: Elite tier only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    config = await elite_service.get_dashboard_config(creator_id)
    data = await elite_service.get_dashboard_data(creator_id)
    
    return {
        "config": config,
        "data": data
    }


@router.put("/dashboard")
async def update_elite_dashboard(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update Elite dashboard configuration"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    updates = await request.json()
    update_data = {k: v for k, v in updates.items() if v is not None}
    
    elite_service = get_service("elite")
    result = await elite_service.update_dashboard_config(creator_id, update_data)
    
    return {"message": "Dashboard updated", "config": result}


# ============== ADAPTIVE INTELLIGENCE ==============

@router.get("/adaptive-intelligence")
async def get_adaptive_intelligence(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get adaptive intelligence profile and recommendations.
    Feature-gated: Elite tier only.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    profile = await elite_service.get_adaptive_profile(creator_id)
    recommendations = await elite_service.get_personalized_recommendations(creator_id)
    
    return {
        "profile": profile,
        "recommendations": recommendations,
        "feature": "adaptive_intelligence"
    }


@router.post("/adaptive-intelligence/refresh")
async def refresh_adaptive_intelligence(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh/rebuild adaptive intelligence profile from creator's history.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    await check_elite_access(creator_id)
    
    elite_service = get_service("elite")
    profile = await elite_service.update_adaptive_profile(creator_id)
    recommendations = await elite_service.get_personalized_recommendations(creator_id)
    
    return {
        "message": "Adaptive Intelligence profile refreshed",
        "profile": profile,
        "recommendations": recommendations
    }


# ============== ARRIS PERSONAS ==============

@router.get("/personas")
async def get_all_personas(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all available ARRIS personas (default + custom) for an Elite creator.
    Includes which persona is currently active.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_service = get_service("persona")
    result = await persona_service.get_all_personas(creator["id"])
    return result


@router.get("/personas/options")
async def get_persona_options(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get available options for creating/customizing personas.
    Returns available tones, styles, focus areas, etc.
    """
    db = get_db()
    _creator = await get_current_creator(credentials, db)
    
    from arris_persona_service import (
        AVAILABLE_TONES, AVAILABLE_STYLES, AVAILABLE_FOCUS_AREAS, AVAILABLE_RESPONSE_LENGTHS
    )
    
    return {
        "tones": AVAILABLE_TONES,
        "communication_styles": AVAILABLE_STYLES,
        "focus_areas": AVAILABLE_FOCUS_AREAS,
        "response_lengths": AVAILABLE_RESPONSE_LENGTHS,
        "emoji_options": ["none", "minimal", "moderate", "frequent"],
        "icon_options": ["user", "briefcase", "smile", "chart-line", "lightbulb", "trophy", "star", "rocket", "heart", "brain"]
    }


@router.get("/personas/active")
async def get_active_persona(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the currently active ARRIS persona for the creator.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    persona_service = get_service("persona")
    persona = await persona_service.get_active_persona(creator["id"])
    return persona


@router.get("/personas/{persona_id}")
async def get_persona(
    persona_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get details of a specific persona.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    persona_service = get_service("persona")
    persona = await persona_service.get_persona(creator["id"], persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return persona


@router.post("/personas")
async def create_persona(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new custom ARRIS persona.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_data = await request.json()
    
    # Validate name
    if not persona_data.get("name"):
        raise HTTPException(status_code=400, detail="Persona name is required")
    
    if len(persona_data.get("name", "")) > 50:
        raise HTTPException(status_code=400, detail="Persona name must be 50 characters or less")
    
    persona_service = get_service("persona")
    result = await persona_service.create_persona(creator["id"], persona_data)
    return result


@router.patch("/personas/{persona_id}")
async def update_persona(
    persona_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a custom persona. System personas cannot be modified.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    updates = await request.json()
    persona_service = get_service("persona")
    result = await persona_service.update_persona(creator["id"], persona_id, updates)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Persona not found or cannot be modified (system personas are read-only)"
        )
    
    return result


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a custom persona. System personas cannot be deleted.
    If the deleted persona was active, switches to Professional.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_service = get_service("persona")
    success = await persona_service.delete_persona(creator["id"], persona_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Persona not found or cannot be deleted (system personas are protected)"
        )
    
    return {"success": True, "message": "Persona deleted successfully"}


@router.post("/personas/{persona_id}/activate")
async def activate_persona(
    persona_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Set a persona as the active one for all ARRIS interactions.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_service = get_service("persona")
    result = await persona_service.activate_persona(creator["id"], persona_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Activation failed"))
    
    return result


@router.post("/personas/{persona_id}/test")
async def test_persona(
    persona_id: str,
    test_message: str = Query(..., description="Test message to preview persona response style"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Test a persona with a sample message.
    Returns the system prompt configuration and preview.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_service = get_service("persona")
    result = await persona_service.test_persona(creator["id"], persona_id, test_message)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Persona not found"))
    
    return result


@router.get("/personas/analytics/summary")
async def get_persona_analytics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get usage analytics for the creator's personas.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    persona_service = get_service("persona")
    analytics = await persona_service.get_persona_analytics(creator["id"])
    return analytics


# ============== SCHEDULED REPORTS ==============

@router.get("/reports/settings")
async def get_report_settings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the creator's scheduled report preferences.
    Returns default settings if none configured.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    scheduled_reports_service = get_service("scheduled_reports")
    settings = await scheduled_reports_service.get_report_settings(creator["id"])
    return settings


@router.put("/reports/settings")
async def update_report_settings(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update scheduled report preferences.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    settings = await request.json()
    scheduled_reports_service = get_service("scheduled_reports")
    result = await scheduled_reports_service.update_report_settings(creator["id"], settings)
    return result


@router.get("/reports/topics")
async def get_report_topics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get available report topics and frequencies."""
    from scheduled_reports_service import AVAILABLE_TOPICS, AVAILABLE_FREQUENCIES
    
    return {
        "topics": [
            {"id": t, "label": t.replace("_", " ").title()}
            for t in AVAILABLE_TOPICS
        ],
        "frequencies": AVAILABLE_FREQUENCIES,
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "times": [f"{h:02d}:00" for h in range(24)]
    }


@router.post("/reports/generate")
async def generate_report(
    report_type: str = Query(default="weekly", description="daily or weekly"),
    send_email: bool = Query(default=False, description="Send report via email"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate a report on-demand.
    Useful for previewing reports or getting immediate summaries.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    if report_type not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="report_type must be 'daily' or 'weekly'")
    
    scheduled_reports_service = get_service("scheduled_reports")
    result = await scheduled_reports_service.generate_report(
        creator_id=creator["id"],
        report_type=report_type,
        send_email=send_email
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Report generation failed"))
    
    return result


@router.get("/reports/history")
async def get_report_history(
    limit: int = Query(default=20, le=50),
    report_type: Optional[str] = Query(default=None, description="Filter by daily or weekly"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get the creator's report history."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    scheduled_reports_service = get_service("scheduled_reports")
    reports = await scheduled_reports_service.get_report_history(
        creator_id=creator["id"],
        limit=limit,
        report_type=report_type
    )
    
    return {"reports": reports, "total": len(reports)}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific report with full content."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    scheduled_reports_service = get_service("scheduled_reports")
    report = await scheduled_reports_service.get_report(creator["id"], report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a report from history."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    scheduled_reports_service = get_service("scheduled_reports")
    success = await scheduled_reports_service.delete_report(creator["id"], report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"success": True, "message": "Report deleted"}


@router.post("/reports/{report_id}/send")
async def send_report(
    report_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send a generated report via email."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    scheduled_reports_service = get_service("scheduled_reports")
    report = await scheduled_reports_service.get_report(creator["id"], report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    success = await scheduled_reports_service._send_report_email(report_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email. Check email configuration.")
    
    return {"success": True, "message": "Report sent to email"}


# ============== ARRIS API ACCESS ==============

@router.get("/arris-api/capabilities")
async def get_api_capabilities(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get available ARRIS API capabilities and documentation.
    Elite feature - provides programmatic access to ARRIS.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    caps = await arris_api_service.get_capabilities()
    return caps


@router.get("/arris-api/docs")
async def get_api_docs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get full API documentation."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    docs = await arris_api_service.get_api_docs()
    return docs


@router.get("/arris-api/keys")
async def list_api_keys(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List all API keys for the creator."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    keys = await arris_api_service.list_api_keys(creator["id"])
    return {"keys": keys}


@router.post("/arris-api/keys")
async def create_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new API key."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    data = await request.json()
    arris_api_service = get_service("arris_api")
    result = await arris_api_service.generate_api_key(
        creator_id=creator["id"],
        key_type=data.get("key_type", "live"),
        name=data.get("name", "API Key")
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/arris-api/keys/{key_id}")
async def get_api_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get details for a specific API key."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    key = await arris_api_service.get_api_key(creator["id"], key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return key


@router.delete("/arris-api/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Revoke an API key."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    result = await arris_api_service.revoke_api_key(creator["id"], key_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/arris-api/keys/{key_id}/regenerate")
async def regenerate_api_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Regenerate an API key."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    result = await arris_api_service.regenerate_api_key(creator["id"], key_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/arris-api/usage")
async def get_api_usage(
    days: int = Query(default=30, le=90, description="Days of history"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get API usage statistics."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    stats = await arris_api_service.get_usage_stats(creator["id"], days)
    return stats


@router.get("/arris-api/history")
async def get_api_history(
    limit: int = Query(default=50, le=200),
    endpoint: Optional[str] = Query(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get API request history."""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    
    await check_elite_access(creator["id"])
    
    arris_api_service = get_service("arris_api")
    history = await arris_api_service.get_request_history(creator["id"], limit, endpoint)
    return {"history": history}
