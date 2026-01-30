"""
Creators Hive HQ - Engine Routes
================================
API endpoints for managing the four core engines:
- Business Engine (Business Support)
- Engagement Engine (Audience & Visibility Support)
- Role Engine (Creator Identity Support)
- Income Engine (Monetization Support)

Phase 2 of the system restoration.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service
from models_system import EngineType, EngineStatus, EngineState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/engines", tags=["Engines"])


# ============== REQUEST MODELS ==============

class UpdateProgressRequest(BaseModel):
    """Request to update engine progress"""
    progress: float
    inputs_received: Optional[int] = 0
    outputs_generated: Optional[int] = 0


class AddBlockerRequest(BaseModel):
    """Request to add a blocker to an engine"""
    blocker: str


class EngineInputRequest(BaseModel):
    """Request to record an input to an engine"""
    input_type: str
    input_data: dict
    source_module: Optional[str] = None


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


# ============== ENGINE DISPLAY LABELS ==============

ENGINE_DISPLAY_NAMES = {
    EngineType.BUSINESS: "Business Support",
    EngineType.ENGAGEMENT: "Audience & Visibility Support",
    EngineType.ROLE: "Creator Identity Support",
    EngineType.INCOME: "Monetization Support"
}

ENGINE_DESCRIPTIONS = {
    EngineType.BUSINESS: "Business planning, strategy, and market analysis",
    EngineType.ENGAGEMENT: "Audience building, content strategy, and community",
    EngineType.ROLE: "Role definition, team building, and delegation",
    EngineType.INCOME: "Revenue tracking, pricing, and sales optimization"
}

ENGINE_INDICATORS = {
    EngineType.BUSINESS: {
        "health_metrics": ["business_clarity", "strategy_defined", "market_analyzed"],
        "warning_thresholds": {"inputs_required": 3, "stale_days": 14}
    },
    EngineType.ENGAGEMENT: {
        "health_metrics": ["audience_defined", "content_planned", "platforms_active"],
        "warning_thresholds": {"inputs_required": 2, "stale_days": 7}
    },
    EngineType.ROLE: {
        "health_metrics": ["roles_defined", "delegation_clear", "accountability_set"],
        "warning_thresholds": {"inputs_required": 2, "stale_days": 21}
    },
    EngineType.INCOME: {
        "health_metrics": ["revenue_tracked", "pricing_set", "funnel_active"],
        "warning_thresholds": {"inputs_required": 2, "stale_days": 7}
    }
}


# ============== STATUS ENDPOINT (Phase 3) ==============

@router.get("/status")
async def get_engines_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/engines/status
    
    Returns comprehensive status of all engines including:
    - Current status (active/pending/blocked/inactive)
    - Progress percentage
    - Input/output counts
    - Blockers
    - Health indicators
    - Dependencies status
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engines = await engine_service.get_all_engine_states(user_id)
    
    if not engines:
        return {
            "initialized": False,
            "message": "Engines not initialized. Complete intake form first.",
            "redirect_to": "/intake"
        }
    
    # Build detailed status for each engine
    engine_statuses = []
    overall_health = "good"
    total_progress = 0
    active_count = 0
    blocked_count = 0
    
    for engine_id, engine_state in engines.items():
        try:
            engine_type = EngineType(engine_id)
        except ValueError:
            continue
        
        config = engine_service.configs.get(engine_type)
        indicators = ENGINE_INDICATORS.get(engine_type, {})
        
        # Calculate health status
        health = "good"
        warnings = []
        
        if engine_state.status == EngineStatus.BLOCKED:
            health = "blocked"
            blocked_count += 1
        elif engine_state.status == EngineStatus.PENDING:
            health = "pending"
            warnings.append("Waiting for dependencies")
        elif engine_state.status == EngineStatus.ACTIVE:
            active_count += 1
            if engine_state.progress < 25:
                health = "needs_attention"
                warnings.append("Low progress - add more inputs")
            elif engine_state.inputs_received < indicators.get("warning_thresholds", {}).get("inputs_required", 0):
                health = "needs_attention"
                warnings.append("Insufficient inputs received")
        
        total_progress += engine_state.progress
        
        # Get recent activity
        last_input = await db.engine_inputs.find_one(
            {"user_id": user_id, "engine_id": engine_id},
            {"_id": 0, "created_at": 1}
        )
        last_output = await db.engine_outputs.find_one(
            {"user_id": user_id, "engine_id": engine_id},
            {"_id": 0, "created_at": 1}
        )
        
        engine_statuses.append({
            "engine_id": engine_id,
            "display_name": ENGINE_DISPLAY_NAMES.get(engine_type, engine_id),
            "description": ENGINE_DESCRIPTIONS.get(engine_type, ""),
            "status": engine_state.status.value,
            "health": health,
            "warnings": warnings,
            "progress": engine_state.progress,
            "inputs": {
                "received": engine_state.inputs_received,
                "required": config.inputs if config else [],
                "total_types": len(config.inputs) if config else 0
            },
            "outputs": {
                "generated": engine_state.outputs_generated,
                "available": config.outputs if config else []
            },
            "blockers": engine_state.blockers,
            "dependencies": {
                "required": [d.value for d in config.dependencies] if config else [],
                "met": engine_state.dependencies_met
            },
            "last_input_at": last_input.get("created_at") if last_input else None,
            "last_output_at": last_output.get("created_at") if last_output else None,
            "last_activity": engine_state.last_activity
        })
    
    # Determine overall health
    if blocked_count > 0:
        overall_health = "has_blockers"
    elif active_count == 0:
        overall_health = "no_active_engines"
    elif total_progress / len(engines) < 25:
        overall_health = "low_progress"
    
    return {
        "initialized": True,
        "overall_health": overall_health,
        "summary": {
            "total": len(engine_statuses),
            "active": active_count,
            "blocked": blocked_count,
            "pending": len([e for e in engine_statuses if e["status"] == "pending"]),
            "inactive": len([e for e in engine_statuses if e["status"] == "inactive"]),
            "average_progress": round(total_progress / len(engines), 1) if engines else 0
        },
        "engines": engine_statuses
    }


# ============== LIST ALL ENGINES ==============

@router.get("")
async def list_engines(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all engine states for the current user.
    
    Returns engine status, progress, blockers, and metadata for all 4 engines.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engines = await engine_service.get_all_engine_states(user_id)
    
    if not engines:
        return {
            "message": "No engines initialized. Please complete the intake form first.",
            "engines": [],
            "summary": {
                "total": 0,
                "active": 0,
                "pending": 0,
                "blocked": 0,
                "inactive": 0
            }
        }
    
    # Format response with display names
    formatted_engines = []
    status_counts = {"active": 0, "pending": 0, "blocked": 0, "inactive": 0}
    
    for engine_id, engine_state in engines.items():
        try:
            engine_type = EngineType(engine_id)
        except ValueError:
            continue
        
        status_counts[engine_state.status.value] = status_counts.get(engine_state.status.value, 0) + 1
        
        formatted_engines.append({
            "engine_id": engine_id,
            "display_name": ENGINE_DISPLAY_NAMES.get(engine_type, engine_id),
            "description": ENGINE_DESCRIPTIONS.get(engine_type, ""),
            "status": engine_state.status.value,
            "progress": engine_state.progress,
            "inputs_received": engine_state.inputs_received,
            "outputs_generated": engine_state.outputs_generated,
            "blockers": engine_state.blockers,
            "dependencies_met": engine_state.dependencies_met,
            "last_activity": engine_state.last_activity
        })
    
    return {
        "engines": formatted_engines,
        "summary": {
            "total": len(formatted_engines),
            **status_counts
        }
    }


# ============== GET SINGLE ENGINE ==============

@router.get("/{engine_id}")
async def get_engine(
    engine_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed state of a specific engine.
    
    Valid engine_ids: business_engine, engagement_engine, role_engine, income_engine
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    # Validate engine type
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid engine_id. Must be one of: {[e.value for e in EngineType]}"
        )
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engine_state = await engine_service.get_engine_state(user_id, engine_type)
    
    if not engine_state:
        raise HTTPException(
            status_code=404,
            detail="Engine not initialized. Please complete the intake form first."
        )
    
    # Get engine config for additional info
    config = engine_service.configs.get(engine_type)
    
    return {
        "engine_id": engine_id,
        "display_name": ENGINE_DISPLAY_NAMES.get(engine_type, engine_id),
        "description": ENGINE_DESCRIPTIONS.get(engine_type, ""),
        "status": engine_state.status.value,
        "progress": engine_state.progress,
        "inputs_received": engine_state.inputs_received,
        "outputs_generated": engine_state.outputs_generated,
        "blockers": engine_state.blockers,
        "dependencies_met": engine_state.dependencies_met,
        "last_activity": engine_state.last_activity,
        "config": {
            "inputs": config.inputs if config else [],
            "outputs": config.outputs if config else [],
            "dependencies": [d.value for d in config.dependencies] if config else [],
            "required_modules": config.required_modules if config else []
        }
    }


# ============== GET ENGINE DETAILS (Phase 3) ==============

@router.get("/{engine_id}/details")
async def get_engine_details(
    engine_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    GET /api/engines/{engine_name}/details
    
    Returns comprehensive details for a specific engine including:
    - Full configuration (inputs, outputs, rules, dependencies)
    - Current state and progress
    - Recent inputs and outputs
    - Health indicators
    - Connected modules
    - Rule enforcement status
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid engine_id. Must be one of: {[e.value for e in EngineType]}"
        )
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engine_state = await engine_service.get_engine_state(user_id, engine_type)
    
    if not engine_state:
        raise HTTPException(
            status_code=404,
            detail="Engine not initialized. Please complete the intake form first."
        )
    
    config = engine_service.configs.get(engine_type)
    indicators = ENGINE_INDICATORS.get(engine_type, {})
    
    # Get recent inputs
    recent_inputs = await db.engine_inputs.find(
        {"user_id": user_id, "engine_id": engine_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get recent outputs
    recent_outputs = await db.engine_outputs.find(
        {"user_id": user_id, "engine_id": engine_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Calculate input completion
    received_input_types = set()
    for inp in recent_inputs:
        received_input_types.add(inp.get("input_type"))
    
    input_completion = []
    if config:
        for input_type in config.inputs:
            input_completion.append({
                "input_type": input_type,
                "received": input_type in received_input_types,
                "label": input_type.replace("_", " ").title()
            })
    
    # Calculate output availability
    generated_output_types = set()
    for out in recent_outputs:
        generated_output_types.add(out.get("output_type"))
    
    output_availability = []
    if config:
        for output_type in config.outputs:
            output_availability.append({
                "output_type": output_type,
                "generated": output_type in generated_output_types,
                "label": output_type.replace("_", " ").title()
            })
    
    # Health assessment
    health = "good"
    health_notes = []
    
    if engine_state.status == EngineStatus.BLOCKED:
        health = "blocked"
        health_notes.append(f"Engine blocked: {', '.join(engine_state.blockers)}")
    elif engine_state.status == EngineStatus.PENDING:
        health = "pending"
        health_notes.append("Waiting for dependency engines to activate")
    elif engine_state.status == EngineStatus.INACTIVE:
        health = "inactive"
        health_notes.append("Engine not selected during intake")
    else:
        if engine_state.progress < 25:
            health = "needs_attention"
            health_notes.append("Progress is low - provide more inputs")
        if len(received_input_types) < 2:
            health_notes.append("Insufficient input diversity")
    
    # Rule status
    rule_status = []
    if config:
        for rule in config.rules:
            # Simple rule evaluation (can be enhanced)
            met = engine_state.progress >= 25 or engine_state.inputs_received >= 2
            rule_status.append({
                "rule": rule,
                "status": "met" if met else "pending"
            })
    
    return {
        "engine_id": engine_id,
        "display_name": ENGINE_DISPLAY_NAMES.get(engine_type, engine_id),
        "description": ENGINE_DESCRIPTIONS.get(engine_type, ""),
        
        "state": {
            "status": engine_state.status.value,
            "progress": engine_state.progress,
            "inputs_received": engine_state.inputs_received,
            "outputs_generated": engine_state.outputs_generated,
            "blockers": engine_state.blockers,
            "dependencies_met": engine_state.dependencies_met,
            "last_activity": engine_state.last_activity
        },
        
        "health": {
            "status": health,
            "notes": health_notes,
            "indicators": indicators.get("health_metrics", [])
        },
        
        "inputs": {
            "required": config.inputs if config else [],
            "completion": input_completion,
            "recent": recent_inputs[:5]
        },
        
        "outputs": {
            "available": config.outputs if config else [],
            "availability": output_availability,
            "recent": recent_outputs[:5]
        },
        
        "rules": {
            "definitions": config.rules if config else [],
            "status": rule_status
        },
        
        "dependencies": {
            "required": [d.value for d in config.dependencies] if config else [],
            "met": engine_state.dependencies_met,
            "display_names": [ENGINE_DISPLAY_NAMES.get(d, d.value) for d in config.dependencies] if config else []
        },
        
        "modules": {
            "required": config.required_modules if config else [],
            "count": len(config.required_modules) if config else 0
        }
    }


# ============== UPDATE ENGINE PROGRESS ==============

@router.post("/{engine_id}/progress")
async def update_engine_progress(
    engine_id: str,
    request: UpdateProgressRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update progress for an engine.
    
    Progress is 0-100. Can also track inputs received and outputs generated.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    try:
        engine_state = await engine_service.update_engine_progress(
            user_id,
            engine_type,
            request.progress,
            request.inputs_received or 0,
            request.outputs_generated or 0
        )
        
        return {
            "success": True,
            "engine_id": engine_id,
            "progress": engine_state.progress,
            "inputs_received": engine_state.inputs_received,
            "outputs_generated": engine_state.outputs_generated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== ADD BLOCKER ==============

@router.post("/{engine_id}/blockers")
async def add_engine_blocker(
    engine_id: str,
    request: AddBlockerRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Add a blocker to an engine. Engine status will change to BLOCKED."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    try:
        engine_state = await engine_service.add_engine_blocker(
            user_id, engine_type, request.blocker
        )
        
        return {
            "success": True,
            "engine_id": engine_id,
            "status": engine_state.status.value,
            "blockers": engine_state.blockers
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== REMOVE BLOCKER ==============

@router.delete("/{engine_id}/blockers")
async def remove_engine_blocker(
    engine_id: str,
    blocker: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Remove a blocker from an engine. Status may change back to ACTIVE."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    try:
        engine_state = await engine_service.remove_engine_blocker(
            user_id, engine_type, blocker
        )
        
        return {
            "success": True,
            "engine_id": engine_id,
            "status": engine_state.status.value,
            "blockers": engine_state.blockers
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== RECORD ENGINE INPUT ==============

@router.post("/{engine_id}/inputs")
async def record_engine_input(
    engine_id: str,
    request: EngineInputRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Record an input to an engine from a module.
    
    This tracks data flowing into the engine and updates progress.
    """
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    # Record the input
    input_record = {
        "user_id": user_id,
        "engine_id": engine_id,
        "input_type": request.input_type,
        "input_data": request.input_data,
        "source_module": request.source_module,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.engine_inputs.insert_one(input_record)
    
    # Update engine state
    try:
        engine_state = await engine_service.update_engine_progress(
            user_id,
            engine_type,
            progress=None,  # Don't change progress
            inputs_received=1
        )
        
        return {
            "success": True,
            "engine_id": engine_id,
            "input_type": request.input_type,
            "inputs_received": engine_state.inputs_received
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== GET ENGINE OUTPUTS ==============

@router.get("/{engine_id}/outputs")
async def get_engine_outputs(
    engine_id: str,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get recent outputs generated by an engine."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    try:
        engine_type = EngineType(engine_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid engine_id")
    
    outputs = await db.engine_outputs.find(
        {"user_id": user_id, "engine_id": engine_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "engine_id": engine_id,
        "display_name": ENGINE_DISPLAY_NAMES.get(engine_type, engine_id),
        "outputs": outputs,
        "count": len(outputs)
    }


# ============== ENGINE SUMMARY ==============

@router.get("/summary/overview")
async def get_engines_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a high-level summary of all engine states."""
    db = get_db()
    auth_user = await get_current_user_or_creator(credentials, db)
    user_id = auth_user["user_id"]
    
    engine_service = get_service("engine")
    if not engine_service:
        raise HTTPException(status_code=503, detail="Engine service not available")
    
    engines = await engine_service.get_all_engine_states(user_id)
    
    if not engines:
        return {
            "initialized": False,
            "message": "Engines not initialized. Complete intake form first."
        }
    
    # Calculate overall stats
    total_progress = sum(e.progress for e in engines.values())
    avg_progress = total_progress / len(engines) if engines else 0
    
    active_engines = [e for e in engines.values() if e.status == EngineStatus.ACTIVE]
    blocked_engines = [e for e in engines.values() if e.status == EngineStatus.BLOCKED]
    
    all_blockers = []
    for engine_state in engines.values():
        all_blockers.extend(engine_state.blockers)
    
    return {
        "initialized": True,
        "total_engines": len(engines),
        "active_count": len(active_engines),
        "blocked_count": len(blocked_engines),
        "average_progress": round(avg_progress, 1),
        "total_inputs": sum(e.inputs_received for e in engines.values()),
        "total_outputs": sum(e.outputs_generated for e in engines.values()),
        "all_blockers": list(set(all_blockers)),
        "engines_by_status": {
            "active": [e.engine_type.value for e in active_engines],
            "blocked": [e.engine_type.value for e in blocked_engines],
            "pending": [e.engine_type.value for e in engines.values() if e.status == EngineStatus.PENDING],
            "inactive": [e.engine_type.value for e in engines.values() if e.status == EngineStatus.INACTIVE]
        }
    }
