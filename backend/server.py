"""
Creators Hive HQ - Master Database API Server
Pattern Engine & Memory Palace for AI Agent ARRIS
Implements Zero-Human Operational Model

Based on Sheet 15 Index - Schema Map
Self-Funding Loop: 17_Subscriptions → 06_Calculator
"""

from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'creators_hive_hq')]

# Create the main app
app = FastAPI(
    title="Creators Hive HQ",
    description="Master Database - Pattern Engine & Memory Palace for AI Agent ARRIS",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import models
from models import (
    User, UserCreate, BrandingKit, BrandingKitCreate,
    CoachKit, CoachKitCreate, Project, ProjectCreate,
    Task, TaskCreate, Calculator, CalculatorCreate,
    Analytics, AnalyticsCreate, Rolodex, RolodexCreate,
    Customer, CustomerCreate, Affiliate, AffiliateCreate,
    EmailLog, EmailLogCreate, Notepad, NotepadCreate,
    Integration, IntegrationCreate, Audit, AuditCreate,
    Lookup, LookupCreate, Subscription, SubscriptionCreate
)

from models_extended import (
    ArrisUsageLog, ArrisUsageLogCreate,
    ArrisPerformance, ArrisPerformanceCreate,
    ArrisTrainingData, ArrisTrainingDataCreate,
    ClientContract, ClientContractCreate,
    TermsOfService, TermsOfServiceCreate,
    PrivacyPolicy, PrivacyPolicyCreate,
    VendorAgreement, VendorAgreementCreate,
    FormSubmission, FormSubmissionCreate,
    IntlTax, IntlTaxCreate,
    ProductRoadmap, ProductRoadmapCreate,
    MarketingCampaign, MarketingCampaignCreate,
    SystemHealth, SystemHealthCreate,
    DevApproach, DevApproachCreate,
    FundingInvestment, FundingInvestmentCreate,
    UserActivityLog, UserActivityLogCreate,
    InternalContent, InternalContentCreate,
    PatternAnalysis, PatternAnalysisCreate,
    SupportLog, SupportLogCreate
)

# Import creator registration models
from models_creator import (
    CreatorRegistration, CreatorRegistrationCreate,
    CreatorRegistrationUpdate, CreatorRegistrationResponse,
    CreatorLogin, CreatorToken,
    PLATFORM_OPTIONS, NICHE_OPTIONS, ARRIS_INTAKE_QUESTIONS
)

# Import project proposal models
from models_proposal import (
    ProjectProposal, ProjectProposalCreate, ProjectProposalUpdate,
    ProjectProposalResponse, TIMELINE_OPTIONS, PRIORITY_OPTIONS,
    STATUS_OPTIONS, ARRIS_PROJECT_QUESTIONS
)

# Import ARRIS AI service
from arris_service import arris_service

# Import webhook service
from webhook_service import webhook_service
from models_webhook import (
    WebhookEvent, WebhookEventCreate, WebhookEventType,
    AutomationRule, DEFAULT_AUTOMATION_RULES, FOLLOW_UP_ACTIONS
)

from database import create_indexes, seed_schema_index, seed_lookups, SCHEMA_INDEX
from seed_data import seed_all_data

# Import authentication
from auth import (
    AdminUserCreate, AdminUserLogin, Token,
    get_current_user, create_admin_user, login_user,
    seed_default_admin, security, get_password_hash,
    login_creator, get_current_creator, decode_token
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== AUTH HELPERS ==============

async def get_any_authenticated_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates token and returns user info for either admin or creator.
    Returns dict with user_type, user_id, email, and full user/creator data.
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    role = getattr(token_data, 'role', 'admin')  # Default to admin for backward compatibility
    
    if role == "creator":
        creator = await db.creators.find_one({"email": token_data.email}, {"_id": 0, "hashed_password": 0})
        if not creator:
            raise HTTPException(status_code=401, detail="Creator not found")
        return {
            "user_type": "creator",
            "user_id": creator["id"],
            "email": creator["email"],
            "name": creator["name"],
            "data": creator
        }
    else:
        admin = await db.admin_users.find_one({"email": token_data.email}, {"_id": 0, "hashed_password": 0})
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        return {
            "user_type": "admin",
            "user_id": admin["id"],
            "email": admin["email"],
            "name": admin["name"],
            "data": admin
        }

# ============== STARTUP ==============

@app.on_event("startup")
async def startup_db():
    """Initialize database with indexes and seed data"""
    logger.info("Initializing Creators Hive HQ Database...")
    await create_indexes(db)
    await seed_schema_index(db)
    await seed_lookups(db)
    seeded = await seed_all_data(db)
    if seeded:
        logger.info(f"Seeded collections: {seeded}")
    # Seed default admin user
    admin_seeded = await seed_default_admin(db)
    if admin_seeded:
        logger.info("Default admin user created: admin@hivehq.com / admin123")
    # Initialize webhook service
    await webhook_service.initialize(db)
    logger.info("Database ready - Zero-Human Operational Model active")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# ============== ROOT & HEALTH ==============

@api_router.get("/")
async def root():
    return {
        "name": "Creators Hive HQ",
        "version": "1.0.0",
        "status": "operational",
        "model": "Zero-Human Operational",
        "engine": "ARRIS Pattern Engine Active"
    }

@api_router.get("/health")
async def health_check():
    """System health check"""
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")

# ============== AUTHENTICATION ==============

@api_router.post("/auth/register", response_model=dict)
async def register_admin(user_data: AdminUserCreate):
    """Register a new admin user"""
    user = await create_admin_user(db, user_data)
    return {"message": "Admin user created successfully", "user": user}

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: AdminUserLogin):
    """Login and get access token"""
    token = await login_user(db, credentials.email, credentials.password)
    return token

@api_router.get("/auth/me")
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin user"""
    current_user = await get_current_user(credentials, db)
    return current_user

@api_router.get("/auth/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if token is valid"""
    current_user = await get_current_user(credentials, db)
    return {"valid": True, "user": current_user}

# ============== CREATOR REGISTRATION (Public Form) ==============

@api_router.get("/creators/form-options")
async def get_creator_form_options():
    """Get options for the creator registration form (public endpoint)"""
    import random
    return {
        "platforms": PLATFORM_OPTIONS,
        "niches": NICHE_OPTIONS,
        "arris_question": random.choice(ARRIS_INTAKE_QUESTIONS)
    }

@api_router.post("/creators/register", response_model=CreatorRegistrationResponse)
async def register_creator(registration: CreatorRegistrationCreate):
    """
    Public endpoint - Register a new creator (no auth required)
    Stores in creators collection for admin review
    """
    # Check if email already registered
    existing = await db.creators.find_one({"email": registration.email})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="This email is already registered. Please use a different email or contact support."
        )
    
    # Create registration record with hashed password
    registration_data = registration.model_dump()
    password = registration_data.pop("password")  # Remove plain password
    
    creator = CreatorRegistration(**registration_data)
    creator.hashed_password = get_password_hash(password)  # Store hashed password
    
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
    await webhook_service.emit(
        event_type=WebhookEventType.CREATOR_REGISTERED,
        payload={
            "name": creator.name,
            "email": creator.email,
            "platforms": creator.platforms,
            "niche": creator.niche
        },
        source_entity="creator",
        source_id=creator.id,
        user_id=creator.id
    )
    
    return CreatorRegistrationResponse(
        id=creator.id,
        name=creator.name,
        email=creator.email,
        status=creator.status,
        message="Thank you for registering! Your application is being reviewed. We'll be in touch soon.",
        submitted_at=doc['submitted_at']
    )

# ============== CREATOR AUTHENTICATION ==============

@api_router.post("/creators/login", response_model=CreatorToken)
async def creator_login(credentials: CreatorLogin):
    """
    Creator login endpoint - returns JWT token
    Only approved/active creators can login
    """
    token = await login_creator(db, credentials.email, credentials.password)
    return token

@api_router.get("/creators/me")
async def get_current_creator_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current logged-in creator's profile"""
    creator = await get_current_creator(credentials, db)
    return creator

@api_router.get("/creators/me/proposals")
async def get_my_proposals(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all proposals for the current logged-in creator"""
    creator = await get_current_creator(credentials, db)
    
    query = {"user_id": creator["id"]}
    if status:
        query["status"] = status
    
    proposals = await db.proposals.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return proposals

@api_router.get("/creators/me/dashboard")
async def get_creator_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get dashboard data for the current logged-in creator"""
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
    
    # Get project counts (if any projects created from approved proposals)
    project_count = await db.projects.count_documents({"user_id": creator_id})
    
    # Get tasks if any
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

@api_router.get("/creators")
async def get_creators(
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all creator registrations (admin only)"""
    await get_current_user(credentials, db)
    
    query = {}
    if status:
        query["status"] = status
    
    creators = await db.creators.find(query, {"_id": 0}).sort("submitted_at", -1).to_list(limit)
    return creators

@api_router.get("/creators/{creator_id}")
async def get_creator(
    creator_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific creator registration (admin only)"""
    await get_current_user(credentials, db)
    
    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0})
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    return creator

@api_router.patch("/creators/{creator_id}")
async def update_creator(
    creator_id: str,
    update: CreatorRegistrationUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update creator registration status (admin only)"""
    current_user = await get_current_user(credentials, db)
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    update_data["reviewed_by"] = current_user.get("id", "admin")
    
    result = await db.creators.update_one(
        {"id": creator_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    # If approved, create a user account
    if update.status == "approved":
        creator = await db.creators.find_one({"id": creator_id})
        if creator and not creator.get("assigned_user_id"):
            # Create user in 01_Users
            new_user_id = f"U-{str(uuid.uuid4())[:4]}"
            new_user = {
                "id": new_user_id,
                "user_id": new_user_id,
                "name": creator["name"],
                "email": creator["email"],
                "role": "Creator",
                "business_type": creator.get("niche", ""),
                "tier": update.assigned_tier or "Free",
                "account_status": "Active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(new_user)
            
            # Link user to creator registration
            await db.creators.update_one(
                {"id": creator_id},
                {"$set": {"assigned_user_id": new_user_id, "status": "active"}}
            )
            
            # WEBHOOK: Emit creator approved event
            await webhook_service.emit(
                event_type=WebhookEventType.CREATOR_APPROVED,
                payload={
                    "name": creator["name"],
                    "email": creator["email"],
                    "user_id": new_user_id,
                    "tier": update.assigned_tier or "Free"
                },
                source_entity="creator",
                source_id=creator_id,
                user_id=new_user_id
            )
            
            return {"message": "Creator approved and user account created", "user_id": new_user_id}
    
    # WEBHOOK: Emit creator rejected if rejected
    if update.status == "rejected":
        creator = await db.creators.find_one({"id": creator_id})
        if creator:
            await webhook_service.emit(
                event_type=WebhookEventType.CREATOR_REJECTED,
                payload={
                    "name": creator.get("name"),
                    "email": creator.get("email"),
                    "reason": update.notes or "Not specified"
                },
                source_entity="creator",
                source_id=creator_id,
                user_id=creator_id
            )
    
    return {"message": "Creator updated successfully"}

@api_router.get("/creators/stats/summary")
async def get_creator_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get creator registration statistics (admin only)"""
    await get_current_user(credentials, db)
    
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_counts = await db.creators.aggregate(pipeline).to_list(10)
    
    # Platform popularity
    platform_pipeline = [
        {"$unwind": "$platforms"},
        {"$group": {"_id": "$platforms", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    platform_stats = await db.creators.aggregate(platform_pipeline).to_list(10)
    
    # Niche distribution
    niche_pipeline = [
        {"$match": {"niche": {"$ne": ""}}},
        {"$group": {"_id": "$niche", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    niche_stats = await db.creators.aggregate(niche_pipeline).to_list(10)
    
    total = await db.creators.count_documents({})
    
    return {
        "total_registrations": total,
        "by_status": {item["_id"]: item["count"] for item in status_counts},
        "top_platforms": platform_stats,
        "top_niches": niche_stats
    }

# ============== PROJECT PROPOSALS ==============

@api_router.get("/proposals/form-options")
async def get_proposal_form_options():
    """Get options for the project proposal form"""
    import random
    return {
        "platforms": PLATFORM_OPTIONS,
        "timelines": TIMELINE_OPTIONS,
        "priorities": PRIORITY_OPTIONS,
        "statuses": STATUS_OPTIONS,
        "arris_question": random.choice(ARRIS_PROJECT_QUESTIONS)
    }

@api_router.post("/proposals", response_model=ProjectProposalResponse)
async def create_proposal(
    proposal: ProjectProposalCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new project proposal (authenticated users - admin or creator)"""
    auth_user = await get_any_authenticated_user(credentials)
    
    # For creators, auto-fill the user_id if not provided
    if auth_user["user_type"] == "creator" and not proposal.user_id:
        proposal.user_id = auth_user["user_id"]
    
    # Get user/creator info for display
    user_info = await db.users.find_one({"id": proposal.user_id}, {"_id": 0})
    creator_info = await db.creators.find_one({"id": proposal.user_id}, {"_id": 0})
    
    # Create proposal
    proposal_obj = ProjectProposal(**proposal.model_dump())
    if user_info:
        proposal_obj.creator_name = user_info.get("name", "")
        proposal_obj.creator_email = user_info.get("email", "")
    elif creator_info:
        proposal_obj.creator_name = creator_info.get("name", "")
        proposal_obj.creator_email = creator_info.get("email", "")
    
    doc = proposal_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.proposals.insert_one(doc)
    
    # WEBHOOK: Emit proposal created event
    await webhook_service.emit(
        event_type=WebhookEventType.PROPOSAL_CREATED,
        payload={
            "title": proposal_obj.title,
            "description": proposal_obj.description[:200] if proposal_obj.description else "",
            "priority": proposal_obj.priority
        },
        source_entity="proposal",
        source_id=proposal_obj.id,
        user_id=proposal.user_id
    )
    
    return ProjectProposalResponse(
        id=proposal_obj.id,
        title=proposal_obj.title,
        status=proposal_obj.status,
        message="Proposal created as draft. Submit when ready for review."
    )

@api_router.post("/proposals/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Submit a proposal for review and generate ARRIS insights"""
    auth_user = await get_any_authenticated_user(credentials)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Verify ownership for creators
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only submit your own proposals")
    
    if proposal.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Only draft proposals can be submitted")
    
    # Get Memory Palace data for context
    memory_palace_data = None
    if proposal.get("user_id"):
        # Fetch user patterns
        user_id = proposal["user_id"]
        activity = {
            "projects": await db.projects.count_documents({"user_id": user_id}),
            "tasks_completed": await db.tasks.count_documents({"assigned_to_user_id": user_id, "completion_status": 1}),
            "arris_queries": await db.arris_usage_log.count_documents({"user_id": user_id}),
        }
        
        # Financial data
        income_entries = await db.calculator.find({"user_id": user_id, "category": "Income"}).to_list(100)
        total_revenue = sum(e.get("revenue", 0) for e in income_entries)
        expense_entries = await db.calculator.find({"user_id": user_id, "category": "Expense"}).to_list(100)
        total_expenses = sum(e.get("expenses", 0) for e in expense_entries)
        
        memory_palace_data = {
            "activity": activity,
            "financials": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": total_revenue - total_expenses
            }
        }
    
    # Generate ARRIS insights
    arris_insights = await arris_service.generate_project_insights(proposal, memory_palace_data)
    
    # Update proposal
    update_data = {
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "arris_insights": arris_insights,
        "arris_insights_generated_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.proposals.update_one({"id": proposal_id}, {"$set": update_data})
    
    # Log to ARRIS usage
    arris_log = {
        "id": f"ARRIS-PROP-{proposal_id}",
        "log_id": f"ARRIS-PROP-{proposal_id}",
        "user_id": proposal.get("user_id", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_query_snippet": f"Project Proposal Analysis: {proposal.get('title', '')}",
        "response_type": "Proposal_Analysis",
        "response_id": proposal_id,
        "time_taken_s": 0,
        "linked_project": None,
        "query_category": "Proposal",
        "success": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.arris_usage_log.insert_one(arris_log)
    
    # WEBHOOK: Emit proposal submitted event
    await webhook_service.emit(
        event_type=WebhookEventType.PROPOSAL_SUBMITTED,
        payload={
            "title": proposal.get("title"),
            "priority": proposal.get("priority"),
            "has_arris_insights": True,
            "complexity": arris_insights.get("estimated_complexity", "Unknown")
        },
        source_entity="proposal",
        source_id=proposal_id,
        user_id=proposal.get("user_id")
    )
    
    # WEBHOOK: Emit ARRIS insights generated event
    await webhook_service.emit(
        event_type=WebhookEventType.ARRIS_INSIGHTS_GENERATED,
        payload={
            "proposal_id": proposal_id,
            "insights_summary": arris_insights.get("summary", "")[:200],
            "complexity": arris_insights.get("estimated_complexity")
        },
        source_entity="arris",
        source_id=proposal_id,
        user_id=proposal.get("user_id")
    )
    
    return {
        "id": proposal_id,
        "status": "submitted",
        "message": "Proposal submitted for review. ARRIS has generated insights.",
        "arris_insights": arris_insights
    }

@api_router.post("/proposals/{proposal_id}/regenerate-insights")
async def regenerate_insights(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Regenerate ARRIS insights for a proposal"""
    await get_current_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Regenerate insights
    arris_insights = await arris_service.generate_project_insights(proposal, None)
    
    await db.proposals.update_one(
        {"id": proposal_id},
        {"$set": {
            "arris_insights": arris_insights,
            "arris_insights_generated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Insights regenerated", "arris_insights": arris_insights}

@api_router.get("/proposals")
async def get_proposals(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all proposals (admin) or user's proposals"""
    await get_current_user(credentials, db)
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    proposals = await db.proposals.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return proposals

@api_router.get("/proposals/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific proposal with ARRIS insights"""
    await get_current_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@api_router.patch("/proposals/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    update: ProjectProposalUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a proposal (admin review)"""
    current_user = await get_current_user(credentials, db)
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Handle status changes
    if update.status:
        if update.status == "under_review":
            update_data["reviewed_by"] = current_user.get("id", "admin")
        elif update.status == "approved":
            update_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            update_data["reviewed_by"] = current_user.get("id", "admin")
            
            # Create project in 04_Projects
            proposal = await db.proposals.find_one({"id": proposal_id})
            if proposal and not proposal.get("assigned_project_id"):
                new_project_id = f"P-{str(uuid.uuid4())[:4]}"
                new_project = {
                    "id": new_project_id,
                    "project_id": new_project_id,
                    "title": proposal["title"],
                    "platform": ", ".join(proposal.get("platforms", [])),
                    "status": "Planning",
                    "user_id": proposal["user_id"],
                    "priority_level": proposal.get("priority", "Medium").capitalize(),
                    "start_date": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.projects.insert_one(new_project)
                update_data["assigned_project_id"] = new_project_id
                update_data["status"] = "in_progress"
        elif update.status == "rejected":
            update_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            update_data["reviewed_by"] = current_user.get("id", "admin")
    
    result = await db.proposals.update_one({"id": proposal_id}, {"$set": update_data})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get updated proposal for webhook data
    updated_proposal = await db.proposals.find_one({"id": proposal_id})
    
    if update.status == "approved" and update_data.get("assigned_project_id"):
        # WEBHOOK: Emit proposal approved event
        await webhook_service.emit(
            event_type=WebhookEventType.PROPOSAL_APPROVED,
            payload={
                "title": updated_proposal.get("title"),
                "project_id": update_data["assigned_project_id"],
                "proposal_id": proposal_id,
                "milestones": updated_proposal.get("arris_insights", {}).get("suggested_milestones", [])
            },
            source_entity="proposal",
            source_id=proposal_id,
            user_id=updated_proposal.get("user_id")
        )
        
        # WEBHOOK: Emit project created event
        await webhook_service.emit(
            event_type=WebhookEventType.PROJECT_CREATED,
            payload={
                "title": updated_proposal.get("title"),
                "platforms": updated_proposal.get("platforms", []),
                "priority": updated_proposal.get("priority"),
                "from_proposal": proposal_id
            },
            source_entity="project",
            source_id=update_data["assigned_project_id"],
            user_id=updated_proposal.get("user_id")
        )
        
        return {
            "message": "Proposal approved and project created",
            "project_id": update_data["assigned_project_id"]
        }
    
    if update.status == "rejected":
        # WEBHOOK: Emit proposal rejected event
        await webhook_service.emit(
            event_type=WebhookEventType.PROPOSAL_REJECTED,
            payload={
                "title": updated_proposal.get("title"),
                "reason": update.review_notes or "Not specified"
            },
            source_entity="proposal",
            source_id=proposal_id,
            user_id=updated_proposal.get("user_id")
        )
    
    if update.status and update.status not in ["approved", "rejected"]:
        # WEBHOOK: Emit status changed event
        await webhook_service.emit(
            event_type=WebhookEventType.PROPOSAL_STATUS_CHANGED,
            payload={
                "title": updated_proposal.get("title"),
                "new_status": update.status,
                "previous_status": updated_proposal.get("status")
            },
            source_entity="proposal",
            source_id=proposal_id,
            user_id=updated_proposal.get("user_id")
        )
    
    return {"message": "Proposal updated successfully"}

@api_router.get("/proposals/stats/summary")
async def get_proposal_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get proposal statistics"""
    await get_current_user(credentials, db)
    
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    status_counts = await db.proposals.aggregate(pipeline).to_list(10)
    
    priority_pipeline = [
        {"$group": {
            "_id": "$priority",
            "count": {"$sum": 1}
        }}
    ]
    priority_counts = await db.proposals.aggregate(priority_pipeline).to_list(10)
    
    total = await db.proposals.count_documents({})
    
    return {
        "total_proposals": total,
        "by_status": {item["_id"]: item["count"] for item in status_counts},
        "by_priority": {item["_id"]: item["count"] for item in priority_counts}
    }

# ============== WEBHOOK AUTOMATIONS ==============

@api_router.get("/webhooks/events")
async def get_webhook_events(
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get webhook events log (admin only)"""
    await get_current_user(credentials, db)
    
    query = {}
    if event_type:
        query["event_type"] = event_type
    if status:
        query["status"] = status
    
    events = await db.webhook_events.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return events

@api_router.get("/webhooks/events/{event_id}")
async def get_webhook_event(
    event_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific webhook event"""
    await get_current_user(credentials, db)
    
    event = await db.webhook_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@api_router.get("/webhooks/rules")
async def get_automation_rules(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all automation rules"""
    await get_current_user(credentials, db)
    
    rules = await db.automation_rules.find({}, {"_id": 0}).to_list(100)
    return rules

@api_router.patch("/webhooks/rules/{rule_id}")
async def update_automation_rule(
    rule_id: str,
    is_active: bool,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Enable/disable an automation rule"""
    await get_current_user(credentials, db)
    
    result = await db.automation_rules.update_one(
        {"id": rule_id},
        {"$set": {"is_active": is_active}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Reload rules in webhook service
    await webhook_service._load_automation_rules()
    
    return {"message": f"Rule {'enabled' if is_active else 'disabled'}", "rule_id": rule_id}

@api_router.get("/webhooks/stats")
async def get_webhook_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get webhook statistics"""
    await get_current_user(credentials, db)
    
    # Event counts by type
    type_pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    type_counts = await db.webhook_events.aggregate(type_pipeline).to_list(50)
    
    # Event counts by status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.webhook_events.aggregate(status_pipeline).to_list(10)
    
    # Recent events (last 24 hours)
    from datetime import timedelta
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_count = await db.webhook_events.count_documents({
        "timestamp": {"$gte": yesterday.isoformat()}
    })
    
    # Active rules
    active_rules = await db.automation_rules.count_documents({"is_active": True})
    total_rules = await db.automation_rules.count_documents({})
    
    total_events = await db.webhook_events.count_documents({})
    
    return {
        "total_events": total_events,
        "events_last_24h": recent_count,
        "by_type": {item["_id"]: item["count"] for item in type_counts},
        "by_status": {item["_id"]: item["count"] for item in status_counts},
        "automation_rules": {
            "total": total_rules,
            "active": active_rules
        }
    }

@api_router.post("/webhooks/test")
async def test_webhook(
    event_type: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Test webhook by emitting a test event"""
    current_user = await get_current_user(credentials, db)
    
    event = await webhook_service.emit(
        event_type=event_type,
        payload={"test": True, "triggered_by": current_user.get("email")},
        source_entity="test",
        source_id=f"TEST-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        user_id=current_user.get("id")
    )
    
    return {"message": "Test event emitted", "event_id": event.id if event else None}

# ============== SCHEMA INDEX (Sheet 15) ==============

@api_router.get("/schema")
async def get_schema_index():
    """Get the complete schema index (Sheet 15) - Source of Truth"""
    schemas = await db.schema_index.find({}, {"_id": 0}).to_list(100)
    return {"schema_index": schemas, "total": len(schemas)}

@api_router.get("/schema/{sheet_name}")
async def get_schema_by_name(sheet_name: str):
    """Get schema details for a specific sheet"""
    schema = await db.schema_index.find_one({"sheet_name": {"$regex": sheet_name, "$options": "i"}}, {"_id": 0})
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found for: {sheet_name}")
    return schema

# ============== 01_USERS ==============

@api_router.get("/users", response_model=List[Dict])
async def get_users(
    role: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get all users with optional filters"""
    query = {}
    if role:
        query["role"] = role
    if tier:
        query["tier"] = tier
    if status:
        query["account_status"] = status
    users = await db.users.find(query, {"_id": 0}).to_list(limit)
    return users

@api_router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID with related data"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch related data (following Sheet 15 relationships)
    related = {
        "branding_kit": await db.branding_kits.find_one({"user_id": user_id}, {"_id": 0}),
        "coach_kit": await db.coach_kits.find_one({"user_id": user_id}, {"_id": 0}),
        "subscription": await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0}),
        "projects_count": await db.projects.count_documents({"user_id": user_id}),
        "total_revenue": 0.0
    }
    
    # Calculate total revenue from Calculator
    calc_entries = await db.calculator.find({"user_id": user_id, "category": "Income"}).to_list(100)
    related["total_revenue"] = sum(entry.get("revenue", 0) for entry in calc_entries)
    
    return {"user": user, "related": related}

@api_router.post("/users", response_model=Dict)
async def create_user(user: UserCreate):
    """Create a new user"""
    user_obj = User(**user.model_dump())
    user_obj.user_id = user_obj.id
    doc = user_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.users.insert_one(doc)
    return {"id": user_obj.id, "message": "User created", "user": doc}

# ============== 04_PROJECTS ==============

@api_router.get("/projects")
async def get_projects(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get all projects with optional filters"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    if priority:
        query["priority_level"] = priority
    projects = await db.projects.find(query, {"_id": 0}).to_list(limit)
    return projects

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get project with tasks"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(100)
    return {"project": project, "tasks": tasks}

@api_router.post("/projects")
async def create_project(project: ProjectCreate):
    """Create a new project"""
    project_obj = Project(**project.model_dump())
    project_obj.project_id = project_obj.id
    project_obj.start_date = datetime.now(timezone.utc)
    doc = project_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['start_date'] = doc['start_date'].isoformat() if doc['start_date'] else None
    await db.projects.insert_one(doc)
    return {"id": project_obj.id, "message": "Project created"}

# ============== 05_TASKS ==============

@api_router.get("/tasks")
async def get_tasks(
    project_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    status: Optional[int] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get tasks with optional filters"""
    query = {}
    if project_id:
        query["project_id"] = project_id
    if assigned_to:
        query["assigned_to_user_id"] = assigned_to
    if status is not None:
        query["completion_status"] = status
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(limit)
    return tasks

@api_router.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new task"""
    task_obj = Task(**task.model_dump())
    task_obj.task_id = task_obj.id
    doc = task_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.tasks.insert_one(doc)
    return {"id": task_obj.id, "message": "Task created"}

@api_router.patch("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark task as complete"""
    result = await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"completion_status": 1, "date_completed": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task completed", "task_id": task_id}

# ============== 06_CALCULATOR (Revenue Hub) ==============

@api_router.get("/calculator")
async def get_calculator_entries(
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    month_year: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get calculator/revenue entries"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if category:
        query["category"] = category
    if month_year:
        query["month_year"] = month_year
    entries = await db.calculator.find(query, {"_id": 0}).to_list(limit)
    return entries

@api_router.get("/calculator/summary")
async def get_revenue_summary(user_id: Optional[str] = None):
    """Get revenue summary - Self-Funding Loop analytics"""
    match_stage = {}
    if user_id:
        match_stage["user_id"] = user_id
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": "$revenue"},
            "expenses": {"$sum": "$expenses"},
            "net_margin": {"$sum": "$net_margin"},
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.calculator.aggregate(pipeline).to_list(10)
    
    total_revenue = sum(r["total"] for r in results if r["_id"] == "Income")
    total_expenses = sum(r["expenses"] for r in results)
    
    return {
        "summary": results,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": total_revenue - total_expenses,
        "self_funding_loop": "Active"
    }

@api_router.post("/calculator")
async def create_calculator_entry(entry: CalculatorCreate):
    """Create revenue/expense entry - All money flows through here"""
    calc_obj = Calculator(**entry.model_dump())
    calc_obj.calc_id = calc_obj.id
    calc_obj.net_margin = calc_obj.revenue - calc_obj.expenses
    doc = calc_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.calculator.insert_one(doc)
    return {"id": calc_obj.id, "message": "Calculator entry created", "net_margin": calc_obj.net_margin}

# ============== 17_SUBSCRIPTIONS (Self-Funding Loop) ==============

@api_router.get("/subscriptions")
async def get_subscriptions(
    user_id: Optional[str] = None,
    tier: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get subscriptions"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if tier:
        query["tier"] = tier
    if status:
        query["payment_status"] = status
    subs = await db.subscriptions.find(query, {"_id": 0}).to_list(limit)
    return subs

@api_router.post("/subscriptions")
async def create_subscription(sub: SubscriptionCreate):
    """Create subscription - Automatically links to Calculator for Self-Funding Loop"""
    sub_obj = Subscription(**sub.model_dump())
    sub_obj.subscription_id = sub_obj.id
    
    # Self-Funding Loop: Create Calculator entry for subscription revenue
    if sub_obj.monthly_cost > 0:
        calc_entry = Calculator(
            user_id=sub_obj.user_id,
            month_year=datetime.now(timezone.utc).strftime("%Y-%m"),
            revenue=sub_obj.monthly_cost,
            expenses=0.0,
            net_margin=sub_obj.monthly_cost,
            category="Income",
            source=f"Subscription: {sub_obj.plan_name}",
            subscription_id=sub_obj.id
        )
        calc_entry.calc_id = calc_entry.id
        calc_doc = calc_entry.model_dump()
        calc_doc['created_at'] = calc_doc['created_at'].isoformat()
        calc_doc['updated_at'] = calc_doc['updated_at'].isoformat()
        await db.calculator.insert_one(calc_doc)
        sub_obj.linked_calc_id = calc_entry.id
    
    doc = sub_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['start_date'] = doc['start_date'].isoformat() if doc['start_date'] else None
    doc['next_renewal'] = doc['next_renewal'].isoformat() if doc['next_renewal'] else None
    await db.subscriptions.insert_one(doc)
    
    return {
        "id": sub_obj.id, 
        "message": "Subscription created",
        "linked_calc_id": sub_obj.linked_calc_id,
        "self_funding_loop": "Revenue routed to Calculator"
    }

@api_router.get("/subscriptions/revenue")
async def get_subscription_revenue():
    """Get total subscription revenue - Self-Funding Loop Report"""
    pipeline = [
        {"$match": {"source": {"$regex": "Subscription", "$options": "i"}}},
        {"$group": {
            "_id": None,
            "total_subscription_revenue": {"$sum": "$revenue"},
            "active_subscriptions": {"$sum": 1}
        }}
    ]
    result = await db.calculator.aggregate(pipeline).to_list(1)
    
    if result:
        return {
            "total_subscription_revenue": result[0]["total_subscription_revenue"],
            "active_subscriptions": result[0]["active_subscriptions"],
            "self_funding_loop": "Active - All subscription revenue flows through Calculator"
        }
    return {"total_subscription_revenue": 0, "active_subscriptions": 0, "self_funding_loop": "Active"}

# ============== ARRIS PATTERN ENGINE (19-21) ==============

@api_router.get("/arris/usage")
async def get_arris_usage(
    user_id: Optional[str] = None,
    response_type: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get ARRIS usage logs"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if response_type:
        query["response_type"] = response_type
    logs = await db.arris_usage_log.find(query, {"_id": 0}).to_list(limit)
    return logs

@api_router.post("/arris/usage")
async def log_arris_usage(log: ArrisUsageLogCreate):
    """Log ARRIS usage - Pattern Engine captures all interactions"""
    log_obj = ArrisUsageLog(**log.model_dump())
    log_obj.log_id = log_obj.id
    doc = log_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.arris_usage_log.insert_one(doc)
    return {"id": log_obj.id, "message": "ARRIS usage logged"}

@api_router.get("/arris/performance")
async def get_arris_performance(limit: int = Query(default=100, le=1000)):
    """Get ARRIS performance reviews"""
    reviews = await db.arris_performance.find({}, {"_id": 0}).to_list(limit)
    return reviews

@api_router.get("/arris/training")
async def get_arris_training_data(limit: int = Query(default=100, le=1000)):
    """Get ARRIS training data sources"""
    data = await db.arris_training_data.find({}, {"_id": 0}).to_list(limit)
    return data

# ============== PATTERN ENGINE - Core Analytics ==============

@api_router.get("/patterns/analyze")
async def analyze_patterns(
    pattern_type: str = Query(default="usage", description="usage, revenue, engagement"),
    user_id: Optional[str] = None,
    days: int = Query(default=30, description="Analysis period in days")
):
    """
    ARRIS Pattern Engine - Reads patterns over time, not single events
    Implements Memory Palace concept for temporal analysis
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    patterns = {
        "pattern_type": pattern_type,
        "time_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "user_id": user_id,
        "insights": [],
        "recommendations": []
    }
    
    if pattern_type == "usage":
        # Analyze ARRIS usage patterns
        match_query = {}
        if user_id:
            match_query["user_id"] = user_id
        
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$response_type",
                "count": {"$sum": 1},
                "avg_time": {"$avg": "$time_taken_s"},
                "success_rate": {"$avg": {"$cond": ["$success", 1, 0]}}
            }},
            {"$sort": {"count": -1}}
        ]
        
        usage_patterns = await db.arris_usage_log.aggregate(pipeline).to_list(10)
        patterns["data"] = usage_patterns
        
        # Generate insights
        if usage_patterns:
            top_usage = usage_patterns[0]
            patterns["insights"].append(f"Most common query type: {top_usage['_id']} ({top_usage['count']} queries)")
            if top_usage.get("avg_time", 0) > 2:
                patterns["recommendations"].append("Consider optimizing response time for common queries")
    
    elif pattern_type == "revenue":
        # Analyze revenue patterns from Calculator
        match_query = {"category": "Income"}
        if user_id:
            match_query["user_id"] = user_id
        
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$source",
                "total_revenue": {"$sum": "$revenue"},
                "entries": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        
        revenue_patterns = await db.calculator.aggregate(pipeline).to_list(10)
        patterns["data"] = revenue_patterns
        
        # Generate insights
        if revenue_patterns:
            top_source = revenue_patterns[0]
            patterns["insights"].append(f"Top revenue source: {top_source['_id']} (${top_source['total_revenue']:,.2f})")
            patterns["recommendations"].append(f"Focus on scaling {top_source['_id']} revenue stream")
    
    elif pattern_type == "engagement":
        # Analyze engagement from Analytics
        match_query = {}
        if user_id:
            match_query["user_id"] = user_id
        
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$platform",
                "total_views": {"$sum": "$platform_views"},
                "avg_engagement": {"$avg": "$engagement_score"},
                "avg_conversion": {"$avg": "$conversion_rate"}
            }},
            {"$sort": {"total_views": -1}}
        ]
        
        engagement_patterns = await db.analytics.aggregate(pipeline).to_list(10)
        patterns["data"] = engagement_patterns
        
        if engagement_patterns:
            top_platform = engagement_patterns[0]
            patterns["insights"].append(f"Top platform: {top_platform['_id']} ({top_platform['total_views']:,} views)")
    
    return patterns

@api_router.get("/patterns/memory-palace")
async def get_memory_palace(user_id: Optional[str] = None):
    """
    Memory Palace - Comprehensive view of all patterns for a user
    ARRIS reads patterns over time across all data sources
    """
    memory = {
        "user_id": user_id or "global",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sections": {}
    }
    
    base_query = {"user_id": user_id} if user_id else {}
    
    # User Profile
    if user_id:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        memory["sections"]["profile"] = user
    
    # Activity Summary
    memory["sections"]["activity"] = {
        "projects": await db.projects.count_documents(base_query),
        "tasks_completed": await db.tasks.count_documents({**base_query, "completion_status": 1}),
        "arris_queries": await db.arris_usage_log.count_documents(base_query),
    }
    
    # Financial Summary (from Calculator - Revenue Hub)
    calc_query = {"category": "Income", **base_query} if user_id else {"category": "Income"}
    income_entries = await db.calculator.find(calc_query).to_list(100)
    total_income = sum(e.get("revenue", 0) for e in income_entries)
    
    expense_query = {"category": "Expense", **base_query} if user_id else {"category": "Expense"}
    expense_entries = await db.calculator.find(expense_query).to_list(100)
    total_expenses = sum(e.get("expenses", 0) for e in expense_entries)
    
    memory["sections"]["financials"] = {
        "total_revenue": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "self_funding_loop_status": "Active"
    }
    
    # Recent Patterns
    memory["sections"]["recent_patterns"] = {
        "usage": await analyze_patterns("usage", user_id, 7),
        "revenue": await analyze_patterns("revenue", user_id, 30),
    }
    
    return memory

# ============== LOOKUPS (Sheet 16) ==============

@api_router.get("/lookups")
async def get_lookups(standard_id: Optional[str] = None):
    """Get lookup values"""
    query = {}
    if standard_id:
        query["standard_id"] = standard_id
    lookups = await db.lookups.find(query, {"_id": 0}).to_list(100)
    return lookups

# ============== ANALYTICS (Sheet 07) ==============

@api_router.get("/analytics")
async def get_analytics(
    user_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get analytics data"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if platform:
        query["platform"] = platform
    data = await db.analytics.find(query, {"_id": 0}).to_list(limit)
    return data

@api_router.post("/analytics")
async def create_analytics(entry: AnalyticsCreate):
    """Create analytics entry"""
    analytics_obj = Analytics(**entry.model_dump())
    analytics_obj.metric_id = analytics_obj.id
    doc = analytics_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['date'] = doc['date'].isoformat()
    await db.analytics.insert_one(doc)
    return {"id": analytics_obj.id, "message": "Analytics entry created"}

# ============== CUSTOMERS (Sheet 09) ==============

@api_router.get("/customers")
async def get_customers(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get customers"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    customers = await db.customers.find(query, {"_id": 0}).to_list(limit)
    return customers

@api_router.post("/customers")
async def create_customer(customer: CustomerCreate):
    """Create customer"""
    cust_obj = Customer(**customer.model_dump())
    cust_obj.customer_id = cust_obj.id
    doc = cust_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.customers.insert_one(doc)
    return {"id": cust_obj.id, "message": "Customer created"}

# ============== AFFILIATES (Sheet 10) ==============

@api_router.get("/affiliates")
async def get_affiliates(
    user_id: Optional[str] = None,
    payout_status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get affiliates"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if payout_status:
        query["payout_status"] = payout_status
    affiliates = await db.affiliates.find(query, {"_id": 0}).to_list(limit)
    return affiliates

# ============== ROLODEX (Sheet 08) ==============

@api_router.get("/rolodex")
async def get_rolodex(
    relationship_type: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get contacts from Rolodex"""
    query = {}
    if relationship_type:
        query["relationship_type"] = relationship_type
    contacts = await db.rolodex.find(query, {"_id": 0}).to_list(limit)
    return contacts

@api_router.post("/rolodex")
async def create_contact(contact: RolodexCreate):
    """Create contact"""
    contact_obj = Rolodex(**contact.model_dump())
    contact_obj.contact_id = contact_obj.id
    doc = contact_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.rolodex.insert_one(doc)
    return {"id": contact_obj.id, "message": "Contact created"}

# ============== INTEGRATIONS (Sheet 13) ==============

@api_router.get("/integrations")
async def get_integrations(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get integrations"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["connection_status"] = status
    integrations = await db.integrations.find(query, {"_id": 0}).to_list(limit)
    return integrations

# ============== MARKETING CAMPAIGNS (Sheet 29) ==============

@api_router.get("/campaigns")
async def get_campaigns(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get marketing campaigns"""
    query = {}
    if status:
        query["status"] = status
    if channel:
        query["channel"] = channel
    campaigns = await db.marketing_campaigns.find(query, {"_id": 0}).to_list(limit)
    return campaigns

@api_router.post("/campaigns")
async def create_campaign(campaign: MarketingCampaignCreate):
    """Create marketing campaign"""
    camp_obj = MarketingCampaign(**campaign.model_dump())
    camp_obj.campaign_id = camp_obj.id
    doc = camp_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.marketing_campaigns.insert_one(doc)
    return {"id": camp_obj.id, "message": "Campaign created"}

# ============== DEV APPROACHES (Sheet 34) ==============

@api_router.get("/dev-approaches")
async def get_dev_approaches():
    """Get development approaches"""
    approaches = await db.dev_approaches.find({}, {"_id": 0}).to_list(20)
    return approaches

# ============== BRANDING KITS (Sheet 02) ==============

@api_router.get("/branding-kits")
async def get_branding_kits(user_id: Optional[str] = None, limit: int = Query(default=100, le=1000)):
    """Get branding kits"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    kits = await db.branding_kits.find(query, {"_id": 0}).to_list(limit)
    return kits

# ============== COACH KITS (Sheet 03) ==============

@api_router.get("/coach-kits")
async def get_coach_kits(user_id: Optional[str] = None, limit: int = Query(default=100, le=1000)):
    """Get coach kits"""
    query = {}
    if user_id:
        query["user_id"] = user_id
    kits = await db.coach_kits.find(query, {"_id": 0}).to_list(limit)
    return kits

# ============== DASHBOARD AGGREGATION ==============

@api_router.get("/dashboard")
async def get_dashboard():
    """Master dashboard - Zero-Human Operational Model overview"""
    dashboard = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_status": "Zero-Human Operational Model Active",
        "pattern_engine": "ARRIS Active",
        "self_funding_loop": "Active",
        "stats": {}
    }
    
    # Collection counts
    collections = [
        "users", "projects", "tasks", "calculator", "subscriptions",
        "customers", "affiliates", "arris_usage_log", "analytics",
        "integrations", "marketing_campaigns"
    ]
    
    for coll in collections:
        dashboard["stats"][coll] = await db[coll].count_documents({})
    
    # Revenue summary
    income = await db.calculator.aggregate([
        {"$match": {"category": "Income"}},
        {"$group": {"_id": None, "total": {"$sum": "$revenue"}}}
    ]).to_list(1)
    
    expenses = await db.calculator.aggregate([
        {"$match": {}},
        {"$group": {"_id": None, "total": {"$sum": "$expenses"}}}
    ]).to_list(1)
    
    dashboard["financials"] = {
        "total_revenue": income[0]["total"] if income else 0,
        "total_expenses": expenses[0]["total"] if expenses else 0,
        "net_profit": (income[0]["total"] if income else 0) - (expenses[0]["total"] if expenses else 0)
    }
    
    # ARRIS stats
    arris_stats = await db.arris_usage_log.aggregate([
        {"$group": {
            "_id": None,
            "total_queries": {"$sum": 1},
            "avg_response_time": {"$avg": "$time_taken_s"}
        }}
    ]).to_list(1)
    
    dashboard["arris"] = arris_stats[0] if arris_stats else {"total_queries": 0, "avg_response_time": 0}
    
    return dashboard

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
