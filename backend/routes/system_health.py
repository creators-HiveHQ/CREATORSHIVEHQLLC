"""
Creators Hive HQ - System Health Routes
=======================================
Phase 6: Data Model Finalization

Endpoints for:
- System health summary
- Data consistency verification
- Engine health aggregation
- Module health aggregation
- user_system_profiles canonical data
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service
from models_system import (
    EngineType, EngineStatus, TrackType,
    EngineHealthSummary, ModuleHealthSummary, 
    SystemHealthSummary, UserSystemProfile
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System Health"])


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


def calculate_engine_health(engine_data: dict) -> str:
    """Calculate health status for an engine"""
    status = engine_data.get("status", "inactive")
    progress = engine_data.get("progress", 0)
    blockers = engine_data.get("blockers", [])
    
    if status == "blocked" or len(blockers) > 0:
        return "blocked"
    elif status == "inactive":
        return "inactive"
    elif status == "pending":
        return "pending"
    elif progress < 25:
        return "needs_attention"
    else:
        return "good"


def calculate_module_health(module_status: str, blockers: list) -> str:
    """Calculate health status for a module"""
    if module_status == "blocked" or len(blockers) > 0:
        return "blocked"
    elif module_status == "locked":
        return "locked"
    elif module_status == "unlocked":
        return "ready"
    elif module_status == "active":
        return "good"
    else:
        return "unknown"


# ============== SYSTEM HEALTH ENDPOINT ==============

@router.get("/health")
async def get_system_health(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/system/health
    
    Returns comprehensive system health summary including:
    - Overall health status
    - Engine health (per-engine and aggregate)
    - Module health (per-module and aggregate)
    - Blockers summary
    - Data consistency checks
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
            "overall_health": "not_initialized",
            "message": "System not initialized. Complete intake form first.",
            "data_consistency": {
                "intake_completed": False,
                "track_assigned": False,
                "engines_initialized": False,
                "modules_initialized": False
            }
        }
    
    # Get engine states
    engine_record = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    engine_states = engine_record.get("engines", {}) if engine_record else {}
    
    # Calculate engine health
    engine_health = {}
    engines_active = 0
    engines_blocked = 0
    total_progress = 0
    engine_blockers = []
    
    for engine_id, engine_data in engine_states.items():
        if isinstance(engine_data, dict):
            status = engine_data.get("status", "inactive")
            progress = engine_data.get("progress", 0)
            blockers = engine_data.get("blockers", [])
            health = calculate_engine_health(engine_data)
            
            engine_health[engine_id] = {
                "engine_id": engine_id,
                "status": status,
                "health": health,
                "progress": progress,
                "inputs_received": engine_data.get("inputs_received", 0),
                "outputs_generated": engine_data.get("outputs_generated", 0),
                "blockers_count": len(blockers),
                "dependencies_met": engine_data.get("dependencies_met", False),
                "last_activity": engine_data.get("last_activity")
            }
            
            if status == "active":
                engines_active += 1
            if health == "blocked":
                engines_blocked += 1
            total_progress += progress
            engine_blockers.extend(blockers)
    
    engines_total = len(engine_states)
    engines_avg_progress = total_progress / engines_total if engines_total > 0 else 0
    
    # Get module status
    module_status_res = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0, "unlocked_modules": 1, "active_modules": 1}
    )
    
    unlocked_modules = module_status_res.get("unlocked_modules", []) if module_status_res else []
    active_modules = module_status_res.get("active_modules", []) if module_status_res else []
    
    # Calculate module health (simplified - would normally call module status endpoint)
    module_health = {}
    modules_blocked = 0
    module_blockers = []
    
    for module_id in unlocked_modules:
        is_active = module_id in active_modules
        status = "active" if is_active else "unlocked"
        health = "good" if is_active else "ready"
        
        module_health[module_id] = {
            "module_id": module_id,
            "status": status,
            "health": health,
            "priority_alignment": False,  # Would need to check against first_priority
            "blockers_count": 0,
            "is_core": module_id in ["dashboard", "profile"]
        }
    
    # Calculate overall health
    total_blockers = len(engine_blockers) + len(module_blockers)
    
    if total_blockers > 5:
        overall_health = "critical"
    elif engines_blocked > 0 or modules_blocked > 0:
        overall_health = "has_blockers"
    elif engines_avg_progress < 25:
        overall_health = "needs_attention"
    elif engines_active == 0:
        overall_health = "no_active_engines"
    else:
        overall_health = "good"
    
    # Data consistency checks
    data_consistency = {
        "intake_completed": user_state.get("intake_completed", False),
        "track_assigned": user_state.get("assigned_track") is not None,
        "engines_initialized": engines_total > 0,
        "modules_initialized": len(unlocked_modules) > 0,
        "identity_set": user_state.get("identity_type") is not None,
        "stage_set": user_state.get("stage") is not None,
        "goal_set": user_state.get("primary_goal") is not None,
        "priority_set": user_state.get("first_priority") is not None
    }
    
    all_consistent = all(data_consistency.values())
    
    # Update health fields in user_system_states
    await db.user_system_states.update_one(
        {"user_id": user_id},
        {"$set": {
            "engine_health": engine_health,
            "module_health": module_health,
            "overall_health": overall_health,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "initialized": True,
        "overall_health": overall_health,
        "data_consistent": all_consistent,
        
        "engine_summary": {
            "total": engines_total,
            "active": engines_active,
            "blocked": engines_blocked,
            "average_progress": round(engines_avg_progress, 1),
            "blockers_count": len(engine_blockers)
        },
        "engine_health": engine_health,
        
        "module_summary": {
            "total": len(unlocked_modules),
            "active": len(active_modules),
            "unlocked": len(unlocked_modules) - len(active_modules),
            "blocked": modules_blocked,
            "blockers_count": len(module_blockers)
        },
        "module_health": module_health,
        
        "blockers": {
            "total": total_blockers,
            "engine_blockers": list(set(engine_blockers)),
            "module_blockers": list(set(module_blockers))
        },
        
        "data_consistency": data_consistency,
        
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# ============== USER SYSTEM PROFILE ENDPOINT ==============

@router.get("/profile")
async def get_user_system_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/system/profile
    
    Returns the canonical user_system_profile with all required fields.
    This is the Phase 6 central data model.
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
            "message": "Profile not initialized. Complete intake form first."
        }
    
    # Get engine states
    engine_record = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    engine_states = engine_record.get("engines", {}) if engine_record else {}
    
    # Extract active engines
    active_engines = []
    for engine_id, engine_data in engine_states.items():
        if isinstance(engine_data, dict) and engine_data.get("status") == "active":
            active_engines.append(engine_id)
    
    # Get intake data for selected_engines
    intake_data = user_state.get("intake_data", {})
    selected_engines = []
    if intake_data and "system_need" in intake_data:
        selected_engines = intake_data["system_need"].get("selected_engines", [])
    
    profile = UserSystemProfile(
        user_id=user_id,
        
        # Identity
        identity_type=user_state.get("identity_type"),
        stage=user_state.get("stage"),
        primary_goal=user_state.get("primary_goal"),
        
        # Intake selections
        selected_engines=selected_engines,
        assets_already_have=user_state.get("assets_already_have", []),
        missing_elements=user_state.get("missing_elements", []),
        first_priority=user_state.get("first_priority"),
        
        # Track
        assigned_track=user_state.get("assigned_track"),
        
        # Engine state
        active_engines=active_engines,
        engine_health=user_state.get("engine_health", {}),
        
        # Module state
        unlocked_modules=user_state.get("unlocked_modules", []),
        active_modules=user_state.get("active_modules", []),
        module_health=user_state.get("module_health", {}),
        
        # System health
        overall_health=user_state.get("overall_health", "unknown"),
        total_blockers=len(user_state.get("blockers", [])),
        
        # Timestamps
        intake_completed_at=user_state.get("created_at").isoformat() if user_state.get("created_at") else None,
        last_updated=datetime.now(timezone.utc).isoformat()
    )
    
    return profile.model_dump()


# ============== DATA CONSISTENCY CHECK ==============

@router.get("/consistency")
async def check_data_consistency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/system/consistency
    
    Verifies data consistency across:
    - Intake form data
    - Engine states
    - Module states
    - Dashboard data
    
    Returns detailed consistency report.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    issues = []
    warnings = []
    
    # Check user_system_states
    user_state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user_state:
        return {
            "consistent": False,
            "issues": ["No user system state found - intake not completed"],
            "warnings": [],
            "checks_passed": 0,
            "checks_failed": 1
        }
    
    checks_passed = 0
    checks_failed = 0
    
    # Check 1: Intake completed
    if user_state.get("intake_completed"):
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append("Intake not marked as completed")
    
    # Check 2: Track assigned
    if user_state.get("assigned_track"):
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append("No track assigned")
    
    # Check 3: Identity type set
    if user_state.get("identity_type"):
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append("Identity type not set")
    
    # Check 4: First priority set
    if user_state.get("first_priority"):
        checks_passed += 1
    else:
        checks_failed += 1
        warnings.append("First priority not set")
    
    # Check 5: Engine states exist
    engine_record = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if engine_record and engine_record.get("engines"):
        checks_passed += 1
        engine_states = engine_record["engines"]
        
        # Check 6: At least one engine initialized
        if any(e.get("status") != "inactive" for e in engine_states.values() if isinstance(e, dict)):
            checks_passed += 1
        else:
            warnings.append("All engines are inactive")
    else:
        checks_failed += 1
        issues.append("No engine states found")
    
    # Check 7: Modules unlocked
    if user_state.get("unlocked_modules") and len(user_state["unlocked_modules"]) > 0:
        checks_passed += 1
    else:
        checks_failed += 1
        issues.append("No modules unlocked")
    
    # Check 8: Intake data stored
    if user_state.get("intake_data"):
        checks_passed += 1
    else:
        warnings.append("Intake data not stored in state")
    
    # Check 9: Intake record exists
    intake_record = await db.intake_records.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if intake_record:
        checks_passed += 1
        
        # Check 10: Intake record matches state
        if intake_record.get("assigned_track") == user_state.get("assigned_track"):
            checks_passed += 1
        else:
            warnings.append("Intake record track doesn't match state track")
    else:
        warnings.append("No intake record found in intake_records collection")
    
    # Check 11: Timestamps exist
    if user_state.get("created_at") and user_state.get("updated_at"):
        checks_passed += 1
    else:
        warnings.append("Missing timestamps")
    
    # Determine overall consistency
    consistent = checks_failed == 0 and len(issues) == 0
    
    return {
        "consistent": consistent,
        "overall_status": "consistent" if consistent else "inconsistent" if len(issues) > 0 else "has_warnings",
        "issues": issues,
        "warnings": warnings,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "total_checks": checks_passed + checks_failed,
        "user_id": user_id,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


# ============== SYNC HEALTH DATA ==============

@router.post("/sync-health")
async def sync_health_data(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    POST /api/system/sync-health
    
    Recalculates and syncs all health data across:
    - Engine health
    - Module health
    - Overall system health
    
    Updates user_system_states with latest health data.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Get current health
    health_response = await get_system_health(credentials)
    
    if not health_response.get("initialized"):
        return {
            "success": False,
            "message": "System not initialized"
        }
    
    # Update user_system_states with health data
    update_data = {
        "engine_health": health_response.get("engine_health", {}),
        "module_health": health_response.get("module_health", {}),
        "overall_health": health_response.get("overall_health", "unknown"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.user_system_states.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    return {
        "success": True,
        "message": "Health data synchronized",
        "overall_health": health_response.get("overall_health"),
        "engine_health_synced": len(health_response.get("engine_health", {})),
        "module_health_synced": len(health_response.get("module_health", {})),
        "updated": result.modified_count > 0,
        "synced_at": datetime.now(timezone.utc).isoformat()
    }


# ============== FULL DATA EXPORT ==============

@router.get("/export")
async def export_user_data(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/system/export
    
    Exports all user system data for verification and debugging.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Gather all data
    user_state = await db.user_system_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    engine_states = await db.user_engine_states.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    intake_record = await db.intake_records.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    arris_outputs = await db.arris_structural_outputs.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    millicent_outputs = await db.millicent_outputs.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    module_data = await db.module_data.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    return {
        "user_id": user_id,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "user_system_state": user_state,
        "engine_states": engine_states,
        "intake_record": intake_record,
        "arris_outputs": arris_outputs,
        "millicent_outputs": millicent_outputs,
        "module_data": module_data
    }
