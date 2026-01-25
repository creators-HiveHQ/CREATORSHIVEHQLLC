"""
Route Dependencies Module
=========================
Shared dependencies, utilities, and helpers for route handlers.
This module is imported by all route modules to access shared resources.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional

# Security scheme
security = HTTPBearer()

# These will be set by the main server during startup
db = None
feature_gating = None
notification_service = None
ws_manager = None

# Service references (set during initialization)
services = {
    "stripe": None,
    "elite": None,
    "arris_memory": None,
    "arris_historical": None,
    "calculator": None,
    "export": None,
    "pattern_engine": None,
    "smart_automation": None,
    "proposal_recommendation": None,
    "enhanced_memory_palace": None,
    "onboarding_wizard": None,
    "auto_approval": None,
    "referral": None,
    "persona": None,
    "scheduled_reports": None,
    "arris_api": None,
    "multi_brand": None,
    "waitlist": None,
    "creator_pattern_insights": None,
    "predictive_alerts": None,
    "subscription_lifecycle": None,
    "creator_health_score": None,
    "pattern_export": None,
    "auto_escalation": None,
    "webhook": None,
    "email": None,
}


def init_dependencies(
    database,
    feature_gating_service,
    notification_svc,
    websocket_manager,
    **service_kwargs
):
    """
    Initialize shared dependencies for route modules.
    Called by main server during startup.
    """
    global db, feature_gating, notification_service, ws_manager
    
    db = database
    feature_gating = feature_gating_service
    notification_service = notification_svc
    ws_manager = websocket_manager
    
    # Set service references
    for key, value in service_kwargs.items():
        if key in services:
            services[key] = value


def get_db():
    """Get database reference."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db


def get_service(name: str):
    """Get a service by name."""
    service = services.get(name)
    if service is None:
        raise HTTPException(status_code=503, detail=f"Service '{name}' not available")
    return service


async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify admin authentication and return admin user."""
    from auth import get_current_user
    try:
        admin = await get_current_user(credentials, get_db())
        return admin
    except Exception:
        raise HTTPException(status_code=403, detail="Admin access required")


async def verify_creator(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify creator authentication and return creator data."""
    from auth import get_current_creator
    return await get_current_creator(credentials, get_db())
