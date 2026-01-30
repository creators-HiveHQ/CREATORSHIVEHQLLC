"""
Creators Hive HQ - Module Routes
================================
API endpoints for managing user modules.
Modules are unlocked based on track and selected engines.

Phase 2 of the system restoration.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service
from models_system import TrackType, EngineType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["Modules"])


# ============== MODULE DEFINITIONS ==============

MODULE_REGISTRY = {
    # Core modules (all tracks)
    "dashboard": {
        "name": "Command Center Dashboard",
        "description": "Central control hub showing active items, next steps, blockers, and AI outputs",
        "purpose": "Monitor and control your system",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True,
        "icon": "layout-dashboard",
        "color": "slate"
    },
    "profile": {
        "name": "Profile & Identity",
        "description": "User identity, stage, and goal management",
        "purpose": "Define who you are and what you're building",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True,
        "icon": "user-circle",
        "color": "blue"
    },
    
    # Business Engine modules
    "business_model_canvas": {
        "name": "Business Model Canvas",
        "description": "Define and visualize your business model components",
        "purpose": "Clarify your value proposition and business structure",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "grid-3x3",
        "color": "blue"
    },
    "market_research": {
        "name": "Market Research",
        "description": "Analyze your target market and competition",
        "purpose": "Understand your market landscape",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "search",
        "color": "blue"
    },
    "financial_planning": {
        "name": "Financial Planning",
        "description": "Revenue streams, costs, and projections",
        "purpose": "Plan your financial future",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS, EngineType.INCOME],
        "is_core": False,
        "icon": "calculator",
        "color": "blue"
    },
    "strategy_builder": {
        "name": "Strategy Builder",
        "description": "Build your growth and execution strategy",
        "purpose": "Create a roadmap to your goals",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "route",
        "color": "blue"
    },
    
    # Engagement Engine modules
    "audience_builder": {
        "name": "Audience Builder",
        "description": "Define and understand your audience",
        "purpose": "Know who you're creating for",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "users",
        "color": "purple"
    },
    "content_planner": {
        "name": "Content Planner",
        "description": "Plan and organize your content strategy",
        "purpose": "Stay consistent and strategic with content",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "calendar",
        "color": "purple"
    },
    "platform_optimizer": {
        "name": "Platform Optimizer",
        "description": "Optimize your presence across platforms",
        "purpose": "Maximize reach and engagement",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "share-2",
        "color": "purple"
    },
    "community_manager": {
        "name": "Community Manager",
        "description": "Build and manage your community",
        "purpose": "Foster meaningful connections",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "heart",
        "color": "purple"
    },
    
    # Role Engine modules
    "role_definer": {
        "name": "Role Definer",
        "description": "Define roles and responsibilities",
        "purpose": "Clarify who does what",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "badge",
        "color": "amber"
    },
    "team_builder": {
        "name": "Team Builder",
        "description": "Build team structure and hierarchy",
        "purpose": "Organize your team effectively",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "users-round",
        "color": "amber"
    },
    "delegation_matrix": {
        "name": "Delegation Matrix",
        "description": "Define delegation and authority levels",
        "purpose": "Empower your team to act",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "network",
        "color": "amber"
    },
    "accountability_tracker": {
        "name": "Accountability Tracker",
        "description": "Track accountability and performance",
        "purpose": "Ensure follow-through and results",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "check-circle",
        "color": "amber"
    },
    
    # Income Engine modules
    "revenue_tracker": {
        "name": "Revenue Tracker",
        "description": "Track and analyze income sources",
        "purpose": "Understand where money comes from",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "trending-up",
        "color": "emerald"
    },
    "pricing_optimizer": {
        "name": "Pricing Optimizer",
        "description": "Optimize your pricing strategy",
        "purpose": "Price for maximum value",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "tag",
        "color": "emerald"
    },
    "sales_funnel": {
        "name": "Sales Funnel",
        "description": "Build and optimize your sales pipeline",
        "purpose": "Convert interest into sales",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "filter",
        "color": "emerald"
    },
    "financial_dashboard": {
        "name": "Financial Dashboard",
        "description": "Financial overview and goals tracking",
        "purpose": "See your financial big picture",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "bar-chart-3",
        "color": "emerald"
    }
}


# ============== HELPERS ==============

async def get_current_user_or_creator(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated user (admin or creator)"""
    from auth import decode_token
    
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = getattr(token_data, 'user_id', None) or getattr(token_data, 'sub', None)
    role = getattr(token_data, 'role', 'admin')
    
    if role == "creator":
        creator = await db.creators.find_one({"id": user_id}, {"_id": 0})
        if creator:
            return {"user_id": user_id, "role": "creator", "user": creator}
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user:
        return {"user_id": user_id, "role": "admin", "user": user}
    
    user = await db.users.find_one({"email": user_id}, {"_id": 0})
    if user:
        return {"user_id": user.get("id", user_id), "role": "admin", "user": user}
    
    raise HTTPException(status_code=401, detail="User not found")


def get_engine_display_name(engine: EngineType) -> str:
    """Get display name for engine (without 'Engine' word)"""
    names = {
        EngineType.BUSINESS: "Business Support",
        EngineType.ENGAGEMENT: "Audience & Visibility Support",
        EngineType.ROLE: "Creator Identity Support",
        EngineType.INCOME: "Monetization Support"
    }
    return names.get(engine, engine.value)


# ============== LIST ALL MODULES ==============

@router.get("")
async def list_all_modules(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all modules with their unlock status for the current user.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Get user's system state
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    unlocked_modules = state.get("unlocked_modules", []) if state else []
    active_modules = state.get("active_modules", []) if state else []
    user_track = state.get("assigned_track") if state else None
    
    # Format modules
    modules = []
    for module_id, module_def in MODULE_REGISTRY.items():
        is_unlocked = module_id in unlocked_modules
        is_active = module_id in active_modules
        
        modules.append({
            "module_id": module_id,
            "name": module_def["name"],
            "description": module_def["description"],
            "purpose": module_def["purpose"],
            "is_core": module_def.get("is_core", False),
            "is_unlocked": is_unlocked,
            "is_active": is_active,
            "icon": module_def.get("icon", "circle"),
            "color": module_def.get("color", "slate"),
            "tracks": [t.value for t in module_def.get("tracks", [])],
            "engines": [get_engine_display_name(e) for e in module_def.get("engines", [])]
        })
    
    return {
        "user_track": user_track,
        "total_modules": len(modules),
        "unlocked_count": len(unlocked_modules),
        "active_count": len(active_modules),
        "modules": modules
    }


# ============== GET USER'S UNLOCKED MODULES ==============

@router.get("/unlocked")
async def get_unlocked_modules(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get only the modules unlocked for the current user."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1, "active_modules": 1, "assigned_track": 1}
    )
    
    if not state:
        return {
            "message": "No modules unlocked. Complete intake form first.",
            "modules": []
        }
    
    unlocked_modules = state.get("unlocked_modules", [])
    active_modules = state.get("active_modules", [])
    
    modules = []
    for module_id in unlocked_modules:
        module_def = MODULE_REGISTRY.get(module_id, {})
        modules.append({
            "module_id": module_id,
            "name": module_def.get("name", module_id),
            "description": module_def.get("description", ""),
            "purpose": module_def.get("purpose", ""),
            "is_active": module_id in active_modules,
            "icon": module_def.get("icon", "circle"),
            "color": module_def.get("color", "slate")
        })
    
    return {
        "track": state.get("assigned_track"),
        "unlocked_count": len(modules),
        "modules": modules
    }


# ============== GET SINGLE MODULE ==============

@router.get("/{module_id}")
async def get_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed information about a specific module."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    if module_id not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found")
    
    module_def = MODULE_REGISTRY[module_id]
    
    # Check if unlocked
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1, "active_modules": 1}
    )
    
    is_unlocked = module_id in state.get("unlocked_modules", []) if state else False
    is_active = module_id in state.get("active_modules", []) if state else False
    
    # Get module data if any
    module_data = await db.module_data.find_one(
        {"user_id": user_id, "module_id": module_id},
        {"_id": 0}
    )
    
    return {
        "module_id": module_id,
        "name": module_def["name"],
        "description": module_def["description"],
        "purpose": module_def["purpose"],
        "is_core": module_def.get("is_core", False),
        "is_unlocked": is_unlocked,
        "is_active": is_active,
        "icon": module_def.get("icon", "circle"),
        "color": module_def.get("color", "slate"),
        "tracks": [t.value for t in module_def.get("tracks", [])],
        "engines": [get_engine_display_name(e) for e in module_def.get("engines", [])],
        "data": module_data.get("data") if module_data else None
    }


# ============== ACTIVATE MODULE ==============

@router.post("/{module_id}/activate")
async def activate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Activate a module (add to active list)."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    if module_id not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found")
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not state:
        raise HTTPException(status_code=404, detail="Please complete intake first")
    
    if module_id not in state.get("unlocked_modules", []):
        raise HTTPException(status_code=403, detail=f"Module {module_id} is not unlocked")
    
    active_modules = state.get("active_modules", [])
    if module_id not in active_modules:
        active_modules.append(module_id)
        await db.user_system_states.update_one(
            {"user_id": user_id},
            {"$set": {
                "active_modules": active_modules,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return {
        "success": True,
        "module_id": module_id,
        "is_active": True,
        "active_modules": active_modules
    }


# ============== DEACTIVATE MODULE ==============

@router.post("/{module_id}/deactivate")
async def deactivate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Deactivate a module (remove from active list)."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    result = await db.user_system_states.update_one(
        {"user_id": user_id},
        {
            "$pull": {"active_modules": module_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "success": True,
        "module_id": module_id,
        "is_active": False,
        "removed": result.modified_count > 0
    }


# ============== SAVE MODULE DATA ==============

class ModuleDataRequest(BaseModel):
    """Request to save module data"""
    data: Dict[str, Any]


@router.post("/{module_id}/data")
async def save_module_data(
    module_id: str,
    request: ModuleDataRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Save data for a module."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    if module_id not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Check if module is unlocked
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1}
    )
    
    if not state or module_id not in state.get("unlocked_modules", []):
        raise HTTPException(status_code=403, detail="Module not unlocked")
    
    await db.module_data.update_one(
        {"user_id": user_id, "module_id": module_id},
        {"$set": {
            "user_id": user_id,
            "module_id": module_id,
            "data": request.data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Also record this as an engine input if module is connected to engines
    module_def = MODULE_REGISTRY[module_id]
    for engine_type in module_def.get("engines", []):
        await db.engine_inputs.insert_one({
            "user_id": user_id,
            "engine_id": engine_type.value,
            "input_type": "module_data",
            "input_data": {"module_id": module_id, "data_keys": list(request.data.keys())},
            "source_module": module_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "success": True,
        "module_id": module_id,
        "saved_at": datetime.now(timezone.utc).isoformat()
    }


# ============== GET MODULES BY ENGINE ==============

@router.get("/by-engine/{engine_id}")
async def get_modules_by_engine(
    engine_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all modules connected to a specific engine."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1, "active_modules": 1}
    )
    
    unlocked = state.get("unlocked_modules", []) if state else []
    active = state.get("active_modules", []) if state else []
    
    modules = []
    for module_id, module_def in MODULE_REGISTRY.items():
        if engine_type in module_def.get("engines", []):
            modules.append({
                "module_id": module_id,
                "name": module_def["name"],
                "description": module_def["description"],
                "is_unlocked": module_id in unlocked,
                "is_active": module_id in active,
                "icon": module_def.get("icon", "circle"),
                "color": module_def.get("color", "slate")
            })
    
    return {
        "engine_id": engine_id,
        "engine_name": get_engine_display_name(engine_type),
        "modules": modules,
        "total": len(modules),
        "unlocked": len([m for m in modules if m["is_unlocked"]])
    }


# ============== GET MODULES BY TRACK ==============

@router.get("/by-track/{track_id}")
async def get_modules_by_track(
    track_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all modules available for a specific track."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        track_type = TrackType(track_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid track_id")
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1, "active_modules": 1}
    )
    
    unlocked = state.get("unlocked_modules", []) if state else []
    active = state.get("active_modules", []) if state else []
    
    modules = []
    for module_id, module_def in MODULE_REGISTRY.items():
        if track_type in module_def.get("tracks", []):
            modules.append({
                "module_id": module_id,
                "name": module_def["name"],
                "description": module_def["description"],
                "is_core": module_def.get("is_core", False),
                "is_unlocked": module_id in unlocked,
                "is_active": module_id in active,
                "icon": module_def.get("icon", "circle"),
                "color": module_def.get("color", "slate"),
                "engines": [get_engine_display_name(e) for e in module_def.get("engines", [])]
            })
    
    return {
        "track_id": track_id,
        "track_name": track_type.value.replace("_", " ").title(),
        "modules": modules,
        "total": len(modules),
        "unlocked": len([m for m in modules if m["is_unlocked"]])
    }
