"""
Creators Hive HQ - Intake Routes
================================
API endpoints for the Intake Form and system state management.
This replaces the existing onboarding wizard.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service
from models_system import (
    IntakeFormSubmission, IntakeFormResponse,
    UserSystemState, DashboardState, EngineStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intake", tags=["Intake"])
dashboard_router = APIRouter(prefix="/command-center", tags=["Command Center"])


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
    
    # Try email lookup
    user = await db.users.find_one({"email": user_id}, {"_id": 0})
    if user:
        return {"user_id": user.get("id", user_id), "role": "admin", "user": user}
    
    raise HTTPException(status_code=401, detail="User not found")


# ============== INTAKE FORM OPTIONS ==============

@router.get("/form-options")
async def get_intake_form_options():
    """
    Get all options for the intake form.
    
    Returns the exact field definitions for the single-page intake form:
    - CATEGORY 1: User Identity (identity_type, stage, primary_goal)
    - CATEGORY 2: System Need (selected_engines - multi-select)
    - CATEGORY 3: Starting Point (assets_already_have, missing_elements, first_priority)
    """
    
    return {
        "user_identity": {
            "identity_type": {
                "label": "I am a...",
                "required": True,
                "type": "radio",
                "options": [
                    {"value": "creator", "label": "Creator", "description": "Content creators, artists, influencers"},
                    {"value": "business", "label": "Business", "description": "Entrepreneurs, business owners, consultants"},
                    {"value": "hybrid", "label": "Hybrid", "description": "Creative business owners, creator-entrepreneurs"}
                ]
            },
            "stage": {
                "label": "My current stage is...",
                "required": True,
                "type": "radio",
                "options": [
                    {"value": "beginner", "label": "Beginner", "description": "Just starting out, learning the basics"},
                    {"value": "intermediate", "label": "Intermediate", "description": "Some experience, growing steadily"},
                    {"value": "advanced", "label": "Advanced", "description": "Established, optimizing and scaling"}
                ]
            },
            "primary_goal": {
                "label": "My primary goal is...",
                "required": True,
                "type": "radio",
                "options": [
                    {"value": "grow_audience", "label": "Grow audience"},
                    {"value": "build_brand", "label": "Build brand"},
                    {"value": "monetize_content", "label": "Monetize content"},
                    {"value": "launch_offers", "label": "Launch offers"},
                    {"value": "improve_consistency", "label": "Improve consistency"},
                    {"value": "other", "label": "Other", "has_text_input": True}
                ]
            }
        },
        "system_need": {
            "selected_engines": {
                "label": "Select the engines you need",
                "required": True,
                "type": "checkbox",
                "min_selections": 1,
                "options": [
                    {
                        "value": "business_engine",
                        "label": "Business Engine",
                        "description": "Business planning, strategy, market analysis",
                        "best_for": ["Business", "Hybrid"]
                    },
                    {
                        "value": "engagement_engine",
                        "label": "Engagement Engine",
                        "description": "Audience building, content strategy, community",
                        "best_for": ["Creator", "Hybrid"]
                    },
                    {
                        "value": "role_engine",
                        "label": "Role Engine",
                        "description": "Role definition, team building, delegation",
                        "best_for": ["Business", "Hybrid"]
                    },
                    {
                        "value": "income_engine",
                        "label": "Income Engine",
                        "description": "Revenue tracking, pricing, sales optimization",
                        "best_for": ["Creator", "Business", "Hybrid"]
                    }
                ]
            }
        },
        "starting_point": {
            "assets_already_have": {
                "label": "What do you already have?",
                "required": False,
                "type": "checkbox",
                "options": [
                    {"value": "social_media_accounts", "label": "Social media accounts"},
                    {"value": "existing_audience", "label": "Existing audience"},
                    {"value": "offers_products", "label": "Offers/products"},
                    {"value": "brand_identity", "label": "Brand identity"},
                    {"value": "content_system", "label": "Content system"},
                    {"value": "none", "label": "None"}
                ]
            },
            "missing_elements": {
                "label": "What is missing?",
                "required": False,
                "type": "checkbox",
                "options": [
                    {"value": "clarity_structure", "label": "Clarity/structure"},
                    {"value": "content_plan", "label": "Content plan"},
                    {"value": "offer_strategy", "label": "Offer strategy"},
                    {"value": "brand_voice", "label": "Brand voice"},
                    {"value": "monetization_path", "label": "Monetization path"},
                    {"value": "systems_automation", "label": "Systems/automation"}
                ]
            },
            "first_priority": {
                "label": "What is your first priority?",
                "required": True,
                "type": "radio",
                "options": [
                    {"value": "build_foundation", "label": "Build foundation"},
                    {"value": "fix_gaps", "label": "Fix gaps"},
                    {"value": "grow_audience", "label": "Grow audience"},
                    {"value": "launch_offer", "label": "Launch offer"},
                    {"value": "increase_income", "label": "Increase income"},
                    {"value": "improve_consistency", "label": "Improve consistency"}
                ]
            }
        }
    }


# ============== INTAKE FORM SUBMISSION ==============

@router.post("/submit", response_model=IntakeFormResponse)
async def submit_intake_form(
    submission: IntakeFormSubmission,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Submit the intake form and activate the system.
    
    This is the ignition key - nothing else activates until this is complete.
    
    Post-form logic:
    1. Assigns user to track (Creator/Business/Hybrid)
    2. Activates selected engines
    3. Unlocks relevant modules
    4. Generates dashboard with initial state
    5. Initializes ARRIS + Millicent outputs
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        raise HTTPException(status_code=503, detail="Intake service not available")
    
    # Check if already completed
    if await intake_service.is_intake_completed(user_id):
        # Allow re-submission to update
        logger.info(f"User {user_id} re-submitting intake form")
    
    try:
        response = await intake_service.process_intake(user_id, submission)
        return response
    except Exception as e:
        logger.error(f"Intake submission failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process intake: {str(e)}")


@router.get("/status")
async def get_intake_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Check if user has completed intake and get current status"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        return {"intake_completed": False, "message": "Intake service not available"}
    
    completed = await intake_service.is_intake_completed(user_id)
    
    if not completed:
        return {
            "intake_completed": False,
            "message": "Please complete the intake form to activate the system",
            "redirect_to": "/intake"
        }
    
    state = await intake_service.get_system_state(user_id)
    
    # Count active engines
    engines_active = 0
    if state and state.engines:
        for engine_data in state.engines.values():
            if isinstance(engine_data, dict):
                if engine_data.get("status") == "active":
                    engines_active += 1
            elif hasattr(engine_data, 'status'):
                if engine_data.status == EngineStatus.ACTIVE or engine_data.status == "active":
                    engines_active += 1
    
    return {
        "intake_completed": True,
        "intake_id": state.intake_id if state else None,
        "assigned_track": state.assigned_track.value if state and state.assigned_track else None,
        "engines_active": engines_active,
        "modules_unlocked": len(state.unlocked_modules) if state else 0
    }


@router.get("/previous-submission")
async def get_previous_submission(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get previous intake submission data for pre-filling the form"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        return {"has_previous": False}
    
    state = await intake_service.get_system_state(user_id)
    
    if not state or not state.intake_data:
        return {"has_previous": False}
    
    return {
        "has_previous": True,
        "previous_data": state.intake_data,
        "submitted_at": state.created_at.isoformat() if state.created_at else None
    }


# ============== SYSTEM STATE ==============

@router.get("/system-state")
async def get_system_state(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current system state for the user"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        raise HTTPException(status_code=503, detail="Intake service not available")
    
    state = await intake_service.get_system_state(user_id)
    
    if not state:
        raise HTTPException(
            status_code=404, 
            detail="No system state found. Please complete intake form first."
        )
    
    return state.model_dump()


@router.post("/recalculate")
async def recalculate_system_state(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Recalculate system state based on current data"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        raise HTTPException(status_code=503, detail="Intake service not available")
    
    try:
        state = await intake_service.recalculate_system_state(user_id)
        return {"success": True, "state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== COMMAND CENTER DASHBOARD ==============

@dashboard_router.get("")
async def get_command_center(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get command center dashboard state.
    
    Returns:
    - What's active (modules currently in use)
    - What's incomplete (modules that need attention)
    - What's next (recommended next steps)
    - What's blocked (blockers preventing progress)
    - Engine activity (status of all engines)
    - ARRIS outputs (structure, clarity, logic recommendations)
    - Millicent outputs (tone, resonance, communication guidance)
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    intake_service = get_service("intake")
    if not intake_service:
        raise HTTPException(status_code=503, detail="Intake service not available")
    
    # Check intake completion
    if not await intake_service.is_intake_completed(user_id):
        return {
            "intake_required": True,
            "message": "Please complete the intake form to access the command center",
            "redirect_to": "/intake"
        }
    
    dashboard_state = await intake_service.get_dashboard_state(user_id)
    
    return dashboard_state.model_dump()


@dashboard_router.get("/active")
async def get_active_modules(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get list of currently active modules"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "active_modules": 1, "unlocked_modules": 1}
    )
    
    if not state:
        return {"active_modules": [], "unlocked_modules": []}
    
    return {
        "active_modules": state.get("active_modules", []),
        "unlocked_modules": state.get("unlocked_modules", [])
    }


@dashboard_router.get("/blockers")
async def get_blockers(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get list of current blockers"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "blockers": 1}
    )
    
    # Also get engine blockers
    engine_state = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "engines": 1}
    )
    
    blockers = state.get("blockers", []) if state else []
    
    if engine_state and "engines" in engine_state:
        for engine_id, engine_data in engine_state["engines"].items():
            if engine_data.get("blockers"):
                for blocker in engine_data["blockers"]:
                    blockers.append({
                        "engine": engine_id,
                        "blocker": blocker
                    })
    
    return {"blockers": blockers}


@dashboard_router.get("/next-steps")
async def get_next_steps(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get recommended next steps"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "next_steps": 1}
    )
    
    return {"next_steps": state.get("next_steps", []) if state else []}


@dashboard_router.get("/engines")
async def get_engine_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of all engines"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engines = await engine_service.get_all_engine_states(user_id)
    
    return {
        "engines": {k: v.model_dump() for k, v in engines.items()},
        "active_count": sum(1 for e in engines.values() if e.status == EngineStatus.ACTIVE),
        "total_progress": sum(e.progress for e in engines.values()) / max(len(engines), 1)
    }


@dashboard_router.get("/ai-outputs")
async def get_ai_outputs(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get recent ARRIS and Millicent outputs"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Get ARRIS outputs (structure, clarity, logic)
    arris_outputs = await db.arris_structural_outputs.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get Millicent outputs (tone, resonance, communication)
    millicent_outputs = await db.millicent_outputs.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "arris": {
            "role": "structure, clarity, logic",
            "outputs": arris_outputs
        },
        "millicent": {
            "role": "tone, resonance, communication",
            "outputs": millicent_outputs
        }
    }


# ============== MODULE ACTIVATION ==============

@router.post("/activate-module/{module_id}")
async def activate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Activate a module for the user"""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
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
            {"$set": {"active_modules": active_modules, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"success": True, "module_id": module_id, "active_modules": active_modules}


@router.post("/deactivate-module/{module_id}")
async def deactivate_module(
    module_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Deactivate a module for the user"""
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
    
    return {"success": True, "module_id": module_id, "removed": result.modified_count > 0}
