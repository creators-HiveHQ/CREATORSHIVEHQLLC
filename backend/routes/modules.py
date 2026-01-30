"""
Creators Hive HQ - Module Routes
================================
API endpoints for managing user modules.
Modules are reconnected to the restored system architecture.

Phase 4 of the system restoration - Module Realignment.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum
import logging

from routes.dependencies import security, get_db, get_service
from models_system import TrackType, EngineType, EngineStatus, AssetsAlreadyHave, MissingElements, FirstPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["Modules"])


# ============== MODULE STATUS ENUM ==============

class ModuleStatus(str, Enum):
    ACTIVE = "active"
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    BLOCKED = "blocked"


# ============== MODULE DEFINITIONS (Phase 4 Enhanced) ==============

MODULE_REGISTRY = {
    # ============== CORE MODULES (all tracks) ==============
    "dashboard": {
        "name": "Command Center Dashboard",
        "description": "Central control hub showing active items, next steps, blockers, and AI outputs",
        "purpose": "Monitor and control your system",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True,
        "icon": "layout-dashboard",
        "color": "slate",
        # Phase 4 metadata
        "required_track": None,  # Available to all
        "required_engines": [],
        "required_assets": [],
        "unlock_conditions": [],
        "blockers_when": [],
        "next_steps_after": ["Complete profile setup", "Review engine status"],
        "starting_point_priority": []  # Always accessible
    },
    "profile": {
        "name": "Profile & Identity",
        "description": "User identity, stage, and goal management",
        "purpose": "Define who you are and what you're building",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True,
        "icon": "user-circle",
        "color": "blue",
        "required_track": None,
        "required_engines": [],
        "required_assets": [],
        "unlock_conditions": [],
        "blockers_when": [],
        "next_steps_after": ["Define your primary goal", "Select your support areas"],
        "starting_point_priority": [FirstPriority.BUILD_FOUNDATION]
    },
    
    # ============== BUSINESS ENGINE MODULES ==============
    "business_model_canvas": {
        "name": "Business Model Canvas",
        "description": "Define and visualize your business model components",
        "purpose": "Clarify your value proposition and business structure",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "grid-3x3",
        "color": "blue",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.BUSINESS],
        "required_assets": [],
        "unlock_conditions": ["Business Support active"],
        "blockers_when": [
            {"condition": "missing_clarity_structure", "message": "Complete clarity/structure assessment first"}
        ],
        "next_steps_after": ["Define target market", "Build financial projections"],
        "starting_point_priority": [FirstPriority.BUILD_FOUNDATION, FirstPriority.LAUNCH_OFFER]
    },
    "market_research": {
        "name": "Market Research",
        "description": "Analyze your target market and competition",
        "purpose": "Understand your market landscape",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "search",
        "color": "blue",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.BUSINESS],
        "required_assets": [],
        "unlock_conditions": ["Business Support active"],
        "blockers_when": [],
        "next_steps_after": ["Validate business model", "Identify competitors"],
        "starting_point_priority": [FirstPriority.BUILD_FOUNDATION]
    },
    "financial_planning": {
        "name": "Financial Planning",
        "description": "Revenue streams, costs, and projections",
        "purpose": "Plan your financial future",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS, EngineType.INCOME],
        "is_core": False,
        "icon": "calculator",
        "color": "blue",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.BUSINESS],
        "required_assets": [AssetsAlreadyHave.OFFERS_PRODUCTS],
        "unlock_conditions": ["Business Support active", "Income Support recommended"],
        "blockers_when": [
            {"condition": "no_offers", "message": "Define offers/products first"}
        ],
        "next_steps_after": ["Set pricing strategy", "Track revenue"],
        "starting_point_priority": [FirstPriority.INCREASE_INCOME, FirstPriority.LAUNCH_OFFER]
    },
    "strategy_builder": {
        "name": "Strategy Builder",
        "description": "Build your growth and execution strategy",
        "purpose": "Create a roadmap to your goals",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "is_core": False,
        "icon": "route",
        "color": "blue",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.BUSINESS],
        "required_assets": [],
        "unlock_conditions": ["Business Support active"],
        "blockers_when": [
            {"condition": "no_business_model", "message": "Complete Business Model Canvas first"}
        ],
        "next_steps_after": ["Execute strategy phases", "Review progress"],
        "starting_point_priority": [FirstPriority.BUILD_FOUNDATION, FirstPriority.FIX_GAPS]
    },
    
    # ============== ENGAGEMENT ENGINE MODULES ==============
    "audience_builder": {
        "name": "Audience Builder",
        "description": "Define and understand your audience",
        "purpose": "Know who you're creating for",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "users",
        "color": "purple",
        "required_track": TrackType.CREATOR,
        "required_engines": [EngineType.ENGAGEMENT],
        "required_assets": [AssetsAlreadyHave.SOCIAL_MEDIA_ACCOUNTS],
        "unlock_conditions": ["Audience & Visibility Support active"],
        "blockers_when": [],
        "next_steps_after": ["Create content plan", "Optimize platforms"],
        "starting_point_priority": [FirstPriority.GROW_AUDIENCE, FirstPriority.BUILD_FOUNDATION]
    },
    "content_planner": {
        "name": "Content Planner",
        "description": "Plan and organize your content strategy",
        "purpose": "Stay consistent and strategic with content",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "calendar",
        "color": "purple",
        "required_track": TrackType.CREATOR,
        "required_engines": [EngineType.ENGAGEMENT],
        "required_assets": [],
        "unlock_conditions": ["Audience & Visibility Support active"],
        "blockers_when": [
            {"condition": "missing_content_plan", "message": "Define audience first for targeted content"}
        ],
        "next_steps_after": ["Schedule content", "Track engagement"],
        "starting_point_priority": [FirstPriority.IMPROVE_CONSISTENCY, FirstPriority.GROW_AUDIENCE]
    },
    "platform_optimizer": {
        "name": "Platform Optimizer",
        "description": "Optimize your presence across platforms",
        "purpose": "Maximize reach and engagement",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "share-2",
        "color": "purple",
        "required_track": TrackType.CREATOR,
        "required_engines": [EngineType.ENGAGEMENT],
        "required_assets": [AssetsAlreadyHave.SOCIAL_MEDIA_ACCOUNTS],
        "unlock_conditions": ["Audience & Visibility Support active"],
        "blockers_when": [
            {"condition": "no_social_accounts", "message": "Set up social media accounts first"}
        ],
        "next_steps_after": ["A/B test content", "Analyze platform performance"],
        "starting_point_priority": [FirstPriority.GROW_AUDIENCE]
    },
    "community_manager": {
        "name": "Community Manager",
        "description": "Build and manage your community",
        "purpose": "Foster meaningful connections",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "is_core": False,
        "icon": "heart",
        "color": "purple",
        "required_track": TrackType.CREATOR,
        "required_engines": [EngineType.ENGAGEMENT],
        "required_assets": [AssetsAlreadyHave.EXISTING_AUDIENCE],
        "unlock_conditions": ["Audience & Visibility Support active", "Some audience exists"],
        "blockers_when": [
            {"condition": "no_audience", "message": "Build initial audience first"}
        ],
        "next_steps_after": ["Engage with community", "Create community events"],
        "starting_point_priority": [FirstPriority.GROW_AUDIENCE]
    },
    
    # ============== ROLE ENGINE MODULES ==============
    "role_definer": {
        "name": "Role Definer",
        "description": "Define roles and responsibilities",
        "purpose": "Clarify who does what",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "badge",
        "color": "amber",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.ROLE],
        "required_assets": [],
        "unlock_conditions": ["Creator Identity Support active", "Business Support active (dependency)"],
        "blockers_when": [
            {"condition": "business_engine_inactive", "message": "Activate Business Support first (dependency)"}
        ],
        "next_steps_after": ["Build team structure", "Set accountability"],
        "starting_point_priority": [FirstPriority.BUILD_FOUNDATION, FirstPriority.FIX_GAPS]
    },
    "team_builder": {
        "name": "Team Builder",
        "description": "Build team structure and hierarchy",
        "purpose": "Organize your team effectively",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "users-round",
        "color": "amber",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.ROLE],
        "required_assets": [],
        "unlock_conditions": ["Creator Identity Support active"],
        "blockers_when": [
            {"condition": "no_roles_defined", "message": "Define roles first"}
        ],
        "next_steps_after": ["Hire team members", "Set up workflows"],
        "starting_point_priority": [FirstPriority.FIX_GAPS]
    },
    "delegation_matrix": {
        "name": "Delegation Matrix",
        "description": "Define delegation and authority levels",
        "purpose": "Empower your team to act",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "network",
        "color": "amber",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.ROLE],
        "required_assets": [],
        "unlock_conditions": ["Creator Identity Support active"],
        "blockers_when": [
            {"condition": "no_team", "message": "Build team structure first"}
        ],
        "next_steps_after": ["Document processes", "Train team on delegation"],
        "starting_point_priority": [FirstPriority.FIX_GAPS]
    },
    "accountability_tracker": {
        "name": "Accountability Tracker",
        "description": "Track accountability and performance",
        "purpose": "Ensure follow-through and results",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "is_core": False,
        "icon": "check-circle",
        "color": "amber",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.ROLE],
        "required_assets": [],
        "unlock_conditions": ["Creator Identity Support active"],
        "blockers_when": [
            {"condition": "no_delegation", "message": "Set up delegation matrix first"}
        ],
        "next_steps_after": ["Review performance", "Adjust accountability"],
        "starting_point_priority": [FirstPriority.IMPROVE_CONSISTENCY]
    },
    
    # ============== INCOME ENGINE MODULES ==============
    "revenue_tracker": {
        "name": "Revenue Tracker",
        "description": "Track and analyze income sources",
        "purpose": "Understand where money comes from",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "trending-up",
        "color": "emerald",
        "required_track": None,  # All tracks
        "required_engines": [EngineType.INCOME],
        "required_assets": [AssetsAlreadyHave.OFFERS_PRODUCTS],
        "unlock_conditions": ["Monetization Support active"],
        "blockers_when": [
            {"condition": "no_income_sources", "message": "Set up offers/products first"}
        ],
        "next_steps_after": ["Optimize pricing", "Identify growth opportunities"],
        "starting_point_priority": [FirstPriority.INCREASE_INCOME]
    },
    "pricing_optimizer": {
        "name": "Pricing Optimizer",
        "description": "Optimize your pricing strategy",
        "purpose": "Price for maximum value",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "tag",
        "color": "emerald",
        "required_track": None,
        "required_engines": [EngineType.INCOME],
        "required_assets": [AssetsAlreadyHave.OFFERS_PRODUCTS],
        "unlock_conditions": ["Monetization Support active"],
        "blockers_when": [
            {"condition": "missing_offer_strategy", "message": "Define offer strategy first"}
        ],
        "next_steps_after": ["Test pricing", "Analyze conversion rates"],
        "starting_point_priority": [FirstPriority.INCREASE_INCOME, FirstPriority.LAUNCH_OFFER]
    },
    "sales_funnel": {
        "name": "Sales Funnel",
        "description": "Build and optimize your sales pipeline",
        "purpose": "Convert interest into sales",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "filter",
        "color": "emerald",
        "required_track": TrackType.BUSINESS,
        "required_engines": [EngineType.INCOME],
        "required_assets": [AssetsAlreadyHave.OFFERS_PRODUCTS, AssetsAlreadyHave.EXISTING_AUDIENCE],
        "unlock_conditions": ["Monetization Support active", "Offers defined"],
        "blockers_when": [
            {"condition": "no_audience", "message": "Build audience first"},
            {"condition": "no_offers", "message": "Create offers first"}
        ],
        "next_steps_after": ["Optimize conversion", "Scale funnel"],
        "starting_point_priority": [FirstPriority.LAUNCH_OFFER, FirstPriority.INCREASE_INCOME]
    },
    "financial_dashboard": {
        "name": "Financial Dashboard",
        "description": "Financial overview and goals tracking",
        "purpose": "See your financial big picture",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "is_core": False,
        "icon": "bar-chart-3",
        "color": "emerald",
        "required_track": None,
        "required_engines": [EngineType.INCOME],
        "required_assets": [],
        "unlock_conditions": ["Monetization Support active"],
        "blockers_when": [],
        "next_steps_after": ["Set financial goals", "Review projections"],
        "starting_point_priority": [FirstPriority.INCREASE_INCOME]
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


def calculate_module_status(
    module_id: str,
    module_def: dict,
    user_state: dict,
    engine_states: dict
) -> dict:
    """Calculate module status based on user state and engine states"""
    
    unlocked_modules = user_state.get("unlocked_modules", [])
    active_modules = user_state.get("active_modules", [])
    assets = user_state.get("assets_already_have", [])
    missing = user_state.get("missing_elements", [])
    first_priority = user_state.get("first_priority", "")
    
    # Determine base status
    if module_id in active_modules:
        status = ModuleStatus.ACTIVE
    elif module_id in unlocked_modules:
        status = ModuleStatus.UNLOCKED
    else:
        status = ModuleStatus.LOCKED
    
    # Check for blockers
    blockers = []
    blocker_conditions = module_def.get("blockers_when", [])
    
    for blocker_def in blocker_conditions:
        condition = blocker_def.get("condition", "")
        message = blocker_def.get("message", "")
        
        # Check various blocking conditions
        if condition == "no_audience" and AssetsAlreadyHave.EXISTING_AUDIENCE.value not in assets:
            blockers.append(message)
        elif condition == "no_offers" and AssetsAlreadyHave.OFFERS_PRODUCTS.value not in assets:
            blockers.append(message)
        elif condition == "no_social_accounts" and AssetsAlreadyHave.SOCIAL_MEDIA_ACCOUNTS.value not in assets:
            blockers.append(message)
        elif condition == "missing_clarity_structure" and MissingElements.CLARITY_STRUCTURE.value in missing:
            blockers.append(message)
        elif condition == "missing_content_plan" and MissingElements.CONTENT_PLAN.value in missing:
            blockers.append(message)
        elif condition == "missing_offer_strategy" and MissingElements.OFFER_STRATEGY.value in missing:
            blockers.append(message)
        elif condition == "business_engine_inactive":
            business_state = engine_states.get(EngineType.BUSINESS.value)
            if business_state and business_state.get("status") != "active":
                blockers.append(message)
    
    if blockers and status != ModuleStatus.LOCKED:
        status = ModuleStatus.BLOCKED
    
    # Calculate health
    health = "good"
    health_notes = []
    
    if status == ModuleStatus.BLOCKED:
        health = "blocked"
        health_notes.extend(blockers)
    elif status == ModuleStatus.LOCKED:
        health = "locked"
        health_notes.append("Module not unlocked - missing requirements")
    elif status == ModuleStatus.UNLOCKED:
        health = "ready"
        health_notes.append("Module ready to activate")
    
    # Calculate priority alignment
    priority_alignment = False
    module_priorities = module_def.get("starting_point_priority", [])
    if first_priority:
        try:
            user_priority = FirstPriority(first_priority)
            priority_alignment = user_priority in module_priorities
        except ValueError:
            pass
    
    # Get next steps
    next_steps = module_def.get("next_steps_after", []) if status == ModuleStatus.ACTIVE else []
    
    return {
        "status": status.value,
        "health": health,
        "health_notes": health_notes,
        "blockers": blockers,
        "priority_alignment": priority_alignment,
        "next_steps": next_steps
    }


# ============== MODULE STATUS ENDPOINT (Phase 4) ==============

@router.get("/status")
async def get_modules_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/modules/status
    
    Returns comprehensive module status including:
    - active_modules
    - unlocked_modules (ready but not active)
    - locked_modules
    - blocked_modules
    - module_health for each
    - dependencies
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Get user system state
    user_state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user_state:
        return {
            "initialized": False,
            "message": "System not initialized. Complete intake form first.",
            "redirect_to": "/intake"
        }
    
    # Get engine states
    engine_record = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    engine_states = engine_record.get("engines", {}) if engine_record else {}
    
    # Categorize modules
    active_modules = []
    unlocked_modules = []
    locked_modules = []
    blocked_modules = []
    
    module_details = []
    
    for module_id, module_def in MODULE_REGISTRY.items():
        status_info = calculate_module_status(
            module_id, module_def, user_state, engine_states
        )
        
        module_info = {
            "module_id": module_id,
            "name": module_def["name"],
            "description": module_def["description"],
            "purpose": module_def["purpose"],
            "is_core": module_def.get("is_core", False),
            "icon": module_def.get("icon", "circle"),
            "color": module_def.get("color", "slate"),
            "status": status_info["status"],
            "health": status_info["health"],
            "health_notes": status_info["health_notes"],
            "blockers": status_info["blockers"],
            "priority_alignment": status_info["priority_alignment"],
            "next_steps": status_info["next_steps"],
            "required_engines": [get_engine_display_name(e) for e in module_def.get("engines", [])],
            "required_track": module_def.get("required_track").value if module_def.get("required_track") else None
        }
        
        module_details.append(module_info)
        
        # Categorize
        if status_info["status"] == ModuleStatus.ACTIVE.value:
            active_modules.append(module_info)
        elif status_info["status"] == ModuleStatus.BLOCKED.value:
            blocked_modules.append(module_info)
        elif status_info["status"] == ModuleStatus.UNLOCKED.value:
            unlocked_modules.append(module_info)
        else:
            locked_modules.append(module_info)
    
    # Calculate overall health
    overall_health = "good"
    if len(blocked_modules) > 0:
        overall_health = "has_blockers"
    elif len(active_modules) == 0:
        overall_health = "no_active_modules"
    
    return {
        "initialized": True,
        "overall_health": overall_health,
        "track": user_state.get("assigned_track"),
        "first_priority": user_state.get("first_priority"),
        "summary": {
            "total": len(MODULE_REGISTRY),
            "active": len(active_modules),
            "unlocked": len(unlocked_modules),
            "blocked": len(blocked_modules),
            "locked": len(locked_modules)
        },
        "active_modules": active_modules,
        "unlocked_modules": unlocked_modules,
        "blocked_modules": blocked_modules,
        "locked_modules": locked_modules,
        "all_modules": module_details
    }


# ============== MODULE UPDATE ENDPOINT (Phase 4) ==============

class ModuleUpdateRequest(BaseModel):
    """Request to update module status"""
    action: str  # "activate", "deactivate", "acknowledge_blocker"
    blocker_to_acknowledge: Optional[str] = None


@router.post("/update/{module_id}")
async def update_module_status(
    module_id: str,
    request: ModuleUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /api/modules/update/{module_id}
    
    Update module status (activate/deactivate only, no rebuild).
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    if module_id not in MODULE_REGISTRY:
        raise HTTPException(status_code=404, detail="Module not found")
    
    module_def = MODULE_REGISTRY[module_id]
    
    # Get user state
    user_state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user_state:
        raise HTTPException(status_code=404, detail="Please complete intake first")
    
    unlocked_modules = user_state.get("unlocked_modules", [])
    active_modules = user_state.get("active_modules", [])
    
    if request.action == "activate":
        if module_id not in unlocked_modules:
            raise HTTPException(status_code=403, detail=f"Module {module_id} is not unlocked")
        
        if module_id not in active_modules:
            active_modules.append(module_id)
            await db.user_system_states.update_one(
                {"user_id": user_id},
                {"$set": {
                    "active_modules": active_modules,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Log module activation
            await db.module_activity_log.insert_one({
                "user_id": user_id,
                "module_id": module_id,
                "action": "activated",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return {
            "success": True,
            "module_id": module_id,
            "status": "active",
            "message": f"{module_def['name']} activated"
        }
    
    elif request.action == "deactivate":
        if module_id in active_modules:
            active_modules.remove(module_id)
            await db.user_system_states.update_one(
                {"user_id": user_id},
                {"$set": {
                    "active_modules": active_modules,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            await db.module_activity_log.insert_one({
                "user_id": user_id,
                "module_id": module_id,
                "action": "deactivated",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return {
            "success": True,
            "module_id": module_id,
            "status": "unlocked",
            "message": f"{module_def['name']} deactivated"
        }
    
    elif request.action == "acknowledge_blocker":
        # Store acknowledged blocker
        await db.acknowledged_blockers.update_one(
            {"user_id": user_id, "module_id": module_id},
            {"$addToSet": {"blockers": request.blocker_to_acknowledge}},
            upsert=True
        )
        
        return {
            "success": True,
            "module_id": module_id,
            "blocker_acknowledged": request.blocker_to_acknowledge
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use: activate, deactivate, acknowledge_blocker")


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
    
    # Get user state
    user_state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    is_unlocked = module_id in user_state.get("unlocked_modules", []) if user_state else False
    is_active = module_id in user_state.get("active_modules", []) if user_state else False
    
    # Get engine states for status calculation
    engine_record = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    engine_states = engine_record.get("engines", {}) if engine_record else {}
    
    # Calculate status
    status_info = calculate_module_status(
        module_id, module_def, user_state or {}, engine_states
    )
    
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
        "status": status_info["status"],
        "health": status_info["health"],
        "health_notes": status_info["health_notes"],
        "blockers": status_info["blockers"],
        "priority_alignment": status_info["priority_alignment"],
        "next_steps": status_info["next_steps"],
        "icon": module_def.get("icon", "circle"),
        "color": module_def.get("color", "slate"),
        "tracks": [t.value for t in module_def.get("tracks", [])],
        "engines": [get_engine_display_name(e) for e in module_def.get("engines", [])],
        "required_track": module_def.get("required_track").value if module_def.get("required_track") else None,
        "required_engines": [e.value for e in module_def.get("required_engines", [])],
        "required_assets": [a.value for a in module_def.get("required_assets", [])],
        "unlock_conditions": module_def.get("unlock_conditions", []),
        "starting_point_priority": [p.value for p in module_def.get("starting_point_priority", [])],
        "data": module_data.get("data") if module_data else None
    }


# ============== ACTIVATE/DEACTIVATE MODULE (Legacy endpoints) ==============

@router.post("/{module_id}/activate")
async def activate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Activate a module (add to active list)."""
    request = ModuleUpdateRequest(action="activate")
    return await update_module_status(module_id, request, credentials)


@router.post("/{module_id}/deactivate")
async def deactivate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Deactivate a module (remove from active list)."""
    request = ModuleUpdateRequest(action="deactivate")
    return await update_module_status(module_id, request, credentials)


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
