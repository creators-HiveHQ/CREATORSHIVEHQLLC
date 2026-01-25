"""
Authentication Routes
=====================
Handles admin and creator authentication endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import logging

from routes.dependencies import security, get_db, get_service
from auth import (
    AdminUserCreate, AdminUserLogin, Token,
    create_admin_user, login_user, get_current_user,
    get_password_hash, verify_password,
    CreatorRegistration, CreatorRegistrationCreate, CreatorRegistrationResponse,
    PLATFORM_OPTIONS, NICHE_OPTIONS, ARRIS_INTAKE_QUESTIONS
)
from webhook_service import WebhookEventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
creator_auth_router = APIRouter(prefix="/creators", tags=["Creator Authentication"])


# ============== ADMIN AUTHENTICATION ==============

@router.post("/register", response_model=dict)
async def register_admin(user_data: AdminUserCreate):
    """Register a new admin user"""
    db = get_db()
    user = await create_admin_user(db, user_data)
    return {"message": "Admin user created successfully", "user": user}


@router.post("/login", response_model=Token)
async def login(credentials: AdminUserLogin):
    """Login and get access token"""
    db = get_db()
    token = await login_user(db, credentials.email, credentials.password)
    return token


@router.get("/me")
async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin user"""
    db = get_db()
    current_user = await get_current_user(credentials, db)
    return current_user


@router.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    db = get_db()
    current_user = await get_current_user(credentials, db)
    return {"valid": True, "user": current_user}


# ============== CREATOR REGISTRATION (Public Form) ==============

@creator_auth_router.get("/form-options")
async def get_creator_form_options():
    """Get options for the creator registration form (public endpoint)"""
    import random
    return {
        "platforms": PLATFORM_OPTIONS,
        "niches": NICHE_OPTIONS,
        "arris_question": random.choice(ARRIS_INTAKE_QUESTIONS)
    }


@creator_auth_router.post("/register", response_model=CreatorRegistrationResponse)
async def register_creator(registration: CreatorRegistrationCreate):
    """
    Public endpoint - Register a new creator (no auth required)
    Stores in creators collection for admin review
    Supports referral code tracking for the referral program
    """
    db = get_db()
    
    # Check if email already registered
    existing = await db.creators.find_one({"email": registration.email})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="This email is already registered. Please use a different email or contact support."
        )
    
    # Create registration record with hashed password
    registration_data = registration.model_dump()
    password = registration_data.pop("password")
    referral_code = registration_data.pop("referral_code", None)
    
    creator = CreatorRegistration(**registration_data)
    creator.hashed_password = get_password_hash(password)
    
    # Track referral if code provided
    referral_result = None
    referral_service = get_service("referral") if "referral" in str(get_service.__doc__) else None
    
    try:
        referral_service = get_service("referral")
        if referral_code and referral_service:
            creator.referred_by_code = referral_code
            referral_result = await referral_service.create_referral(
                referral_code=referral_code,
                referred_creator_id=creator.id,
                referred_email=creator.email
            )
            if referral_result.get("success"):
                creator.referral_id = referral_result.get("referral_id")
                logger.info(f"Referral tracked for creator {creator.id} via code {referral_code}")
    except HTTPException:
        pass  # Referral service not available
    
    doc = creator.model_dump()
    doc['submitted_at'] = doc['submitted_at'].isoformat()
    
    await db.creators.insert_one(doc)
    
    # Log to ARRIS usage for pattern analysis
    arris_log = {
        "id": f"ARRIS-REG-{creator.id}",
        "log_id": f"ARRIS-REG-{creator.id}",
        "user_id": creator.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_query_snippet": f"Creator Registration: {creator.name}",
        "response_type": "Registration_Intake",
        "response_id": creator.id,
        "time_taken_s": 0,
        "linked_project": None,
        "query_category": "Registration",
        "success": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.arris_usage_log.insert_one(arris_log)
    
    # WEBHOOK: Emit creator registered event
    try:
        webhook_service = get_service("webhook")
        await webhook_service.emit(
            event_type=WebhookEventType.CREATOR_REGISTERED,
            payload={
                "name": creator.name,
                "email": creator.email,
                "platforms": creator.platforms,
                "niche": creator.niche,
                "referred_by": referral_code if referral_result and referral_result.get("success") else None
            },
            source_entity="creator",
            source_id=creator.id,
            user_id=creator.id
        )
    except HTTPException:
        pass  # Webhook service not available
    
    # AUTO-APPROVAL: Process registration through auto-approval system
    response_message = "Thank you for registering! Your application is being reviewed. We'll be in touch soon."
    final_status = creator.status
    
    try:
        auto_approval_service = get_service("auto_approval")
        creator_data = await db.creators.find_one({"id": creator.id}, {"_id": 0})
        if creator_data:
            auto_approval_result = await auto_approval_service.process_registration(
                creator.id,
                auto_execute=True
            )
            
            if auto_approval_result.get("new_status") == "approved":
                response_message = "Congratulations! Your application has been automatically approved. You can now log in to your dashboard."
                final_status = "approved"
            elif auto_approval_result.get("new_status") == "rejected":
                response_message = "Thank you for your interest. Unfortunately, your application did not meet our current requirements."
                final_status = "rejected"
            elif auto_approval_result.get("new_status") == "pending_review":
                response_message = "Thank you for registering! Your application is being reviewed by our team. We'll be in touch soon."
                final_status = "pending_review"
    except (HTTPException, Exception) as e:
        logger.error(f"Auto-approval processing error: {e}")
    
    return CreatorRegistrationResponse(
        id=creator.id,
        name=creator.name,
        email=creator.email,
        status=final_status,
        message=response_message,
        submitted_at=doc['submitted_at']
    )
