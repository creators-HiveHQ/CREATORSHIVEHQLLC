"""
Creators Hive HQ - Master Database API Server
Pattern Engine & Memory Palace for AI Agent ARRIS
Implements Zero-Human Operational Model

Based on Sheet 15 Index - Schema Map
Self-Funding Loop: 17_Subscriptions → 06_Calculator
"""

from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
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

# Import Stripe/subscription service
from stripe_service import StripeService
from models_subscription import (
    SUBSCRIPTION_PLANS, SubscriptionTier, BillingCycle,
    CreatorSubscription, PaymentTransaction,
    CheckoutRequest, CheckoutResponse, SubscriptionStatusResponse,
    PlanInfo, PlansResponse, FEATURE_TIERS
)

# Import feature gating service
from feature_gating import FeatureGatingService

# Import WebSocket service
from fastapi import WebSocket, WebSocketDisconnect
from websocket_service import ws_manager, notification_service, NotificationType

# Import Export service
from export_service import ExportService

# Import Elite service
from elite_service import EliteService
from models_elite import (
    WorkflowCreateRequest, WorkflowRunRequest, WorkflowFocusArea,
    BrandIntegrationCreate, BrandIntegrationUpdate, BrandPartnershipStatus,
    DashboardConfigUpdate, DashboardWidgetType
)

# Import ARRIS Memory service
from arris_memory_service import ArrisMemoryService, MemoryType, PatternCategory

# Import ARRIS Activity Feed service
from arris_activity_service import arris_activity_service

# Import ARRIS Historical Learning service
from arris_historical_service import ArrisHistoricalService

# Import ARRIS Voice service
from arris_voice_service import arris_voice_service

# Import ARRIS Pattern Engine
from arris_pattern_engine import ArrisPatternEngine

# Import Smart Automation Engine
from smart_automation_engine import SmartAutomationEngine

# Import Proposal Recommendation Service
from proposal_recommendation_service import ProposalRecommendationService

# Import Email service
from email_service import email_service, EmailDeliveryError

# Import Calculator service
from calculator_service import CalculatorService

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

# Initialize services
stripe_service = None
feature_gating = None
elite_service = None
arris_memory_service = None
arris_historical_service = None
calculator_service = None
export_service = None
pattern_engine = None
smart_automation_engine = None
proposal_recommendation_service = None

@app.on_event("startup")
async def startup_db():
    """Initialize database with indexes and seed data"""
    global stripe_service, feature_gating, elite_service, arris_memory_service, arris_historical_service, calculator_service, export_service, pattern_engine, smart_automation_engine, proposal_recommendation_service
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
    # Initialize Stripe service
    stripe_service = StripeService(db)
    # Initialize Feature Gating service
    feature_gating = FeatureGatingService(db)
    # Initialize Elite service
    elite_service = EliteService(db)
    logger.info("Elite service initialized - Custom Workflows & Brand Integrations active")
    # Initialize ARRIS Memory service
    arris_memory_service = ArrisMemoryService(db)
    logger.info("ARRIS Memory service initialized - Memory Palace & Pattern Engine active")
    
    # Initialize ARRIS Historical Learning service
    arris_historical_service = ArrisHistoricalService(db)
    logger.info("ARRIS Historical service initialized - Learning visualization active")
    
    # Initialize Calculator service
    calculator_service = CalculatorService(db)
    logger.info("Calculator service initialized - Self-Funding Loop & Financial Analytics active")
    # Initialize Export service
    export_service = ExportService(db)
    logger.info("Export service initialized - CSV/JSON analytics exports active")
    
    # Initialize ARRIS Pattern Engine
    pattern_engine = ArrisPatternEngine(db)
    logger.info("ARRIS Pattern Engine initialized - Platform-wide pattern detection active")
    
    # Initialize ARRIS Activity Feed notification callback
    async def arris_activity_notification_callback(event_type: str, creator_id: str, data: dict):
        """Callback to send ARRIS activity notifications via WebSocket"""
        if event_type == "queue_update":
            await notification_service.notify_arris_queue_update(
                creator_id=creator_id,
                proposal_id=data.get("proposal_id", ""),
                queue_position=data.get("queue_position", 0),
                estimated_wait_seconds=data.get("estimated_wait_seconds", 0),
                priority=data.get("priority", "standard")
            )
        elif event_type == "processing_started":
            await notification_service.notify_arris_processing_started(
                creator_id=creator_id,
                proposal_id=data.get("proposal_id", ""),
                proposal_title=data.get("proposal_title", ""),
                priority=data.get("priority", "standard")
            )
        elif event_type == "processing_completed":
            await notification_service.notify_arris_processing_complete(
                creator_id=creator_id,
                proposal_id=data.get("proposal_id", ""),
                proposal_title=data.get("proposal_title", ""),
                processing_time=data.get("processing_time", 0),
                priority=data.get("priority", "standard")
            )
    
    arris_activity_service.set_notification_callback(arris_activity_notification_callback)
    logger.info("ARRIS Activity Feed initialized - Real-time queue updates active")
    
    logger.info("Feature Gating service initialized")
    logger.info("Stripe service initialized - Self-Funding Loop active")
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

@api_router.get("/creators/me/advanced-dashboard")
async def get_creator_advanced_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get advanced dashboard data for Pro+ creators.
    Returns enhanced analytics, trends, and performance metrics.
    Feature-gated: Requires 'advanced' or 'custom' dashboard_level.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check dashboard level access
    dashboard_level = await feature_gating.get_dashboard_level(creator_id)
    has_priority_review = await feature_gating.has_priority_review(creator_id)
    has_advanced_analytics = await feature_gating.has_advanced_analytics(creator_id)
    
    if dashboard_level == "basic":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Advanced dashboard requires Pro plan or higher",
                "required_tier": "pro",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # ===== PERFORMANCE ANALYTICS =====
    # Calculate approval rate
    total_proposals = await db.proposals.count_documents({"user_id": creator_id})
    approved_proposals = await db.proposals.count_documents({
        "user_id": creator_id, 
        "status": {"$in": ["approved", "in_progress", "completed"]}
    })
    approval_rate = round((approved_proposals / total_proposals * 100), 1) if total_proposals > 0 else 0
    
    # Calculate average review time (submitted -> approved/rejected)
    review_pipeline = [
        {"$match": {
            "user_id": creator_id,
            "status": {"$in": ["approved", "rejected", "in_progress", "completed"]},
            "submitted_at": {"$exists": True},
            "reviewed_at": {"$exists": True}
        }},
        {"$project": {
            "review_time_hours": {
                "$divide": [
                    {"$subtract": [
                        {"$dateFromString": {"dateString": "$reviewed_at"}},
                        {"$dateFromString": {"dateString": "$submitted_at"}}
                    ]},
                    3600000  # Convert ms to hours
                ]
            }
        }},
        {"$group": {"_id": None, "avg_review_time": {"$avg": "$review_time_hours"}}}
    ]
    review_time_result = await db.proposals.aggregate(review_pipeline).to_list(1)
    avg_review_time = round(review_time_result[0]["avg_review_time"], 1) if review_time_result else None
    
    # ===== PROPOSAL TRENDS (Last 6 months) =====
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    trends_pipeline = [
        {"$match": {
            "user_id": creator_id,
            "created_at": {"$gte": six_months_ago.isoformat()}
        }},
        {"$project": {
            "month": {"$substr": ["$created_at", 0, 7]}  # YYYY-MM
        }},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    monthly_trends = await db.proposals.aggregate(trends_pipeline).to_list(12)
    
    # ===== ARRIS ACTIVITY =====
    arris_usage = await db.arris_usage_log.find(
        {"user_id": creator_id},
        {"_id": 0, "timestamp": 1, "query_category": 1, "response_type": 1, "success": 1}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    arris_stats = {
        "total_interactions": await db.arris_usage_log.count_documents({"user_id": creator_id}),
        "successful": await db.arris_usage_log.count_documents({"user_id": creator_id, "success": True}),
        "recent_activity": arris_usage
    }
    
    # ===== STATUS BREAKDOWN WITH TIMELINE =====
    status_pipeline = [
        {"$match": {"user_id": creator_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "latest": {"$max": "$updated_at"}
        }}
    ]
    status_breakdown = await db.proposals.aggregate(status_pipeline).to_list(10)
    
    # ===== PRIORITY REVIEW STATUS =====
    priority_queue_position = None
    if has_priority_review:
        # Count proposals ahead in queue (simplified - just count pending reviews)
        pending_reviews = await db.proposals.count_documents({
            "status": "submitted",
            "created_at": {"$lt": datetime.now(timezone.utc).isoformat()}
        })
        priority_queue_position = max(1, pending_reviews // 3)  # Priority gets ~3x faster
    
    # ===== COMPLEXITY DISTRIBUTION =====
    complexity_pipeline = [
        {"$match": {
            "user_id": creator_id,
            "arris_insights.estimated_complexity": {"$exists": True}
        }},
        {"$group": {"_id": "$arris_insights.estimated_complexity", "count": {"$sum": 1}}}
    ]
    complexity_dist = await db.proposals.aggregate(complexity_pipeline).to_list(5)
    
    # ===== SUCCESS METRICS =====
    completed_proposals = await db.proposals.count_documents({
        "user_id": creator_id,
        "status": "completed"
    })
    in_progress = await db.proposals.count_documents({
        "user_id": creator_id,
        "status": "in_progress"
    })
    
    return {
        "dashboard_level": dashboard_level,
        "has_priority_review": has_priority_review,
        "has_advanced_analytics": has_advanced_analytics,
        
        "performance": {
            "total_proposals": total_proposals,
            "approval_rate": approval_rate,
            "avg_review_time_hours": avg_review_time,
            "completed": completed_proposals,
            "in_progress": in_progress,
            "priority_queue_position": priority_queue_position
        },
        
        "trends": {
            "monthly_submissions": [{"month": t["_id"], "count": t["count"]} for t in monthly_trends]
        },
        
        "status_breakdown": [
            {"status": s["_id"], "count": s["count"], "latest": s["latest"]} 
            for s in status_breakdown
        ],
        
        "complexity_distribution": [
            {"complexity": c["_id"], "count": c["count"]} 
            for c in complexity_dist
        ],
        
        "arris": arris_stats,
        
        "insights": {
            "top_performing_month": max(monthly_trends, key=lambda x: x["count"])["_id"] if monthly_trends else None,
            "most_common_complexity": max(complexity_dist, key=lambda x: x["count"])["_id"] if complexity_dist else None
        }
    }

@api_router.get("/creators/me/premium-analytics")
async def get_creator_premium_analytics(
    date_range: Optional[str] = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get Premium-tier analytics with deeper insights.
    Feature-gated: Requires 'advanced_analytics' feature (Premium/Elite only).
    
    Includes:
    - Comparative analytics (vs platform averages)
    - Revenue/value tracking
    - Predictive success insights
    - Detailed ARRIS analytics with processing times
    - Weekly/daily granular trends
    - Platform performance breakdown
    - Month-over-month growth metrics
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has advanced_analytics feature
    has_advanced_analytics = await feature_gating.has_advanced_analytics(creator_id)
    
    if not has_advanced_analytics:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Premium Analytics requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription",
                "feature_highlights": [
                    "Comparative analytics vs platform averages",
                    "Revenue & value tracking",
                    "AI-powered predictive insights",
                    "Detailed ARRIS processing analytics",
                    "Granular daily/weekly trends",
                    "Export reports to CSV/JSON"
                ]
            }
        )
    
    # Parse date range
    date_ranges = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
        "all": timedelta(days=3650)  # ~10 years
    }
    time_delta = date_ranges.get(date_range, timedelta(days=30))
    start_date = datetime.now(timezone.utc) - time_delta
    
    # ===== USER'S METRICS =====
    user_proposals = await db.proposals.find(
        {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}},
        {"_id": 0}
    ).to_list(1000)
    
    user_total = len(user_proposals)
    user_approved = len([p for p in user_proposals if p.get("status") in ["approved", "in_progress", "completed"]])
    user_completed = len([p for p in user_proposals if p.get("status") == "completed"])
    user_approval_rate = round((user_approved / user_total * 100), 1) if user_total > 0 else 0
    
    # ===== PLATFORM-WIDE AVERAGES (for comparison) =====
    total_platform_proposals = await db.proposals.count_documents(
        {"created_at": {"$gte": start_date.isoformat()}}
    )
    total_platform_approved = await db.proposals.count_documents({
        "created_at": {"$gte": start_date.isoformat()},
        "status": {"$in": ["approved", "in_progress", "completed"]}
    })
    platform_approval_rate = round((total_platform_approved / total_platform_proposals * 100), 1) if total_platform_proposals > 0 else 0
    
    # Average proposals per creator (active creators in this period)
    active_creators_pipeline = [
        {"$match": {"created_at": {"$gte": start_date.isoformat()}}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "active_creators"}
    ]
    active_creators_result = await db.proposals.aggregate(active_creators_pipeline).to_list(1)
    active_creators = active_creators_result[0]["active_creators"] if active_creators_result else 1
    avg_proposals_per_creator = round(total_platform_proposals / active_creators, 1)
    
    # ===== COMPARATIVE ANALYTICS =====
    comparative = {
        "your_approval_rate": user_approval_rate,
        "platform_approval_rate": platform_approval_rate,
        "approval_rate_diff": round(user_approval_rate - platform_approval_rate, 1),
        "your_proposals": user_total,
        "avg_proposals_per_creator": avg_proposals_per_creator,
        "proposals_diff": user_total - avg_proposals_per_creator,
        "percentile_rank": min(99, max(1, int((user_approval_rate / max(1, platform_approval_rate)) * 50 + 25)))  # Simplified percentile
    }
    
    # ===== REVENUE & VALUE TRACKING =====
    # Estimate value based on proposal complexity and status
    value_map = {"Low": 500, "Medium": 1500, "High": 3500, "Very High": 7500}
    total_estimated_value = 0
    realized_value = 0
    pipeline_value = 0
    
    for p in user_proposals:
        complexity = p.get("arris_insights", {}).get("estimated_complexity", "Medium")
        value = value_map.get(complexity, 1500)
        total_estimated_value += value
        if p.get("status") == "completed":
            realized_value += value
        elif p.get("status") in ["approved", "in_progress"]:
            pipeline_value += value
    
    revenue_tracking = {
        "total_estimated_value": total_estimated_value,
        "realized_value": realized_value,
        "pipeline_value": pipeline_value,
        "pending_value": total_estimated_value - realized_value - pipeline_value,
        "realization_rate": round((realized_value / total_estimated_value * 100), 1) if total_estimated_value > 0 else 0,
        "avg_project_value": round(total_estimated_value / user_total, 2) if user_total > 0 else 0,
        "currency": "USD"
    }
    
    # ===== PREDICTIVE INSIGHTS =====
    # Based on historical patterns, predict success
    success_factors = []
    risk_factors = []
    
    if user_approval_rate > platform_approval_rate:
        success_factors.append("Above-average approval rate")
    if user_total > avg_proposals_per_creator:
        success_factors.append("High proposal volume")
    if user_completed > 0:
        success_factors.append("Track record of completed projects")
    
    recent_proposals = [p for p in user_proposals if datetime.fromisoformat(p.get("created_at", "2020-01-01").replace("Z", "+00:00")) > datetime.now(timezone.utc) - timedelta(days=7)]
    if len(recent_proposals) == 0:
        risk_factors.append("No recent activity in last 7 days")
    
    rejected = len([p for p in user_proposals if p.get("status") == "rejected"])
    if rejected > user_approved:
        risk_factors.append("More rejections than approvals")
    
    # Predicted success score (0-100)
    base_score = 50
    base_score += min(25, user_approval_rate - platform_approval_rate)  # Up to +25 for approval rate
    base_score += min(15, (user_completed * 5))  # Up to +15 for completions
    base_score -= min(20, (rejected * 3))  # Down to -20 for rejections
    predicted_success_score = max(10, min(95, int(base_score)))
    
    predictive_insights = {
        "success_score": predicted_success_score,
        "score_label": "Excellent" if predicted_success_score >= 80 else "Good" if predicted_success_score >= 60 else "Fair" if predicted_success_score >= 40 else "Needs Improvement",
        "success_factors": success_factors,
        "risk_factors": risk_factors,
        "recommendation": "Keep up the great work!" if predicted_success_score >= 70 else "Focus on proposal quality and consistency" if predicted_success_score >= 50 else "Consider reviewing rejected proposals for improvement areas"
    }
    
    # ===== DETAILED ARRIS ANALYTICS =====
    arris_logs = await db.arris_usage_log.find(
        {"user_id": creator_id, "timestamp": {"$gte": start_date.isoformat()}},
        {"_id": 0}
    ).to_list(1000)
    
    # Processing time analysis
    processing_times = []
    for p in user_proposals:
        pt = p.get("arris_insights", {}).get("processing_time_seconds")
        if pt:
            processing_times.append(pt)
    
    avg_processing_time = round(sum(processing_times) / len(processing_times), 2) if processing_times else 0
    min_processing_time = round(min(processing_times), 2) if processing_times else 0
    max_processing_time = round(max(processing_times), 2) if processing_times else 0
    
    # Category breakdown
    category_counts = {}
    for log in arris_logs:
        cat = log.get("query_category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    arris_analytics = {
        "total_interactions": len(arris_logs),
        "successful_interactions": len([l for l in arris_logs if l.get("success")]),
        "success_rate": round((len([l for l in arris_logs if l.get("success")]) / len(arris_logs) * 100), 1) if arris_logs else 0,
        "processing_times": {
            "average": avg_processing_time,
            "min": min_processing_time,
            "max": max_processing_time,
            "total_saved": round(len(processing_times) * 2, 1)  # Estimated time saved vs manual
        },
        "category_breakdown": [{"category": k, "count": v} for k, v in sorted(category_counts.items(), key=lambda x: -x[1])],
        "insights_generated": len([p for p in user_proposals if p.get("arris_insights")])
    }
    
    # ===== GRANULAR TRENDS (Daily for 30d, Weekly for 90d+) =====
    if time_delta <= timedelta(days=30):
        # Daily trends
        daily_pipeline = [
            {"$match": {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}}},
            {"$project": {"day": {"$substr": ["$created_at", 0, 10]}}},  # YYYY-MM-DD
            {"$group": {"_id": "$day", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        granular_trends = await db.proposals.aggregate(daily_pipeline).to_list(60)
        trend_granularity = "daily"
    else:
        # Weekly trends
        weekly_pipeline = [
            {"$match": {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}}},
            {"$project": {
                "week": {"$dateToString": {"format": "%Y-W%V", "date": {"$dateFromString": {"dateString": "$created_at"}}}}
            }},
            {"$group": {"_id": "$week", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        granular_trends = await db.proposals.aggregate(weekly_pipeline).to_list(52)
        trend_granularity = "weekly"
    
    # ===== PLATFORM PERFORMANCE BREAKDOWN =====
    platform_pipeline = [
        {"$match": {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}}},
        {"$unwind": {"path": "$platforms", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$platforms",
            "total": {"$sum": 1},
            "approved": {"$sum": {"$cond": [{"$in": ["$status", ["approved", "in_progress", "completed"]]}, 1, 0]}},
            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}}
        }},
        {"$project": {
            "platform": "$_id",
            "total": 1,
            "approved": 1,
            "completed": 1,
            "approval_rate": {"$round": [{"$multiply": [{"$divide": ["$approved", {"$max": ["$total", 1]}]}, 100]}, 1]}
        }}
    ]
    platform_performance = await db.proposals.aggregate(platform_pipeline).to_list(20)
    
    # ===== MONTH-OVER-MONTH GROWTH =====
    current_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_proposals = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": current_month_start.isoformat()}
    })
    last_month_proposals = await db.proposals.count_documents({
        "user_id": creator_id,
        "created_at": {"$gte": last_month_start.isoformat(), "$lt": current_month_start.isoformat()}
    })
    
    mom_growth = round(((current_month_proposals - last_month_proposals) / max(1, last_month_proposals)) * 100, 1)
    
    growth_metrics = {
        "current_month": current_month_proposals,
        "last_month": last_month_proposals,
        "mom_growth_percent": mom_growth,
        "growth_trend": "📈 Growing" if mom_growth > 10 else "📉 Declining" if mom_growth < -10 else "➡️ Stable"
    }
    
    # ===== ENGAGEMENT SCORE =====
    # Calculate overall engagement score
    engagement_factors = {
        "proposal_activity": min(100, (user_total / max(1, avg_proposals_per_creator)) * 50),
        "completion_rate": (user_completed / max(1, user_total)) * 100,
        "arris_usage": min(100, len(arris_logs) * 10),
        "recent_activity": 100 if recent_proposals else 0
    }
    engagement_score = round(sum(engagement_factors.values()) / len(engagement_factors), 1)
    
    return {
        "analytics_tier": "premium",
        "date_range": date_range,
        "period_start": start_date.isoformat(),
        "period_end": datetime.now(timezone.utc).isoformat(),
        
        "summary": {
            "total_proposals": user_total,
            "approval_rate": user_approval_rate,
            "completed_projects": user_completed,
            "engagement_score": engagement_score,
            "predicted_success": predicted_success_score
        },
        
        "comparative_analytics": comparative,
        "revenue_tracking": revenue_tracking,
        "predictive_insights": predictive_insights,
        "arris_analytics": arris_analytics,
        
        "trends": {
            "granularity": trend_granularity,
            "data": [{"period": t["_id"], "count": t["count"]} for t in granular_trends]
        },
        
        "platform_performance": [
            {
                "platform": p.get("platform") or "Unspecified",
                "total": p["total"],
                "approved": p["approved"],
                "completed": p["completed"],
                "approval_rate": p.get("approval_rate", 0)
            }
            for p in platform_performance
        ],
        
        "growth_metrics": growth_metrics,
        
        "engagement": {
            "score": engagement_score,
            "factors": engagement_factors,
            "label": "Highly Engaged" if engagement_score >= 70 else "Moderately Engaged" if engagement_score >= 40 else "Low Engagement"
        },
        
        "export_available": True,
        "export_formats": ["csv", "json"]
    }

@api_router.get("/creators/me/premium-analytics/export")
async def export_premium_analytics(
    format: str = Query(default="json", description="Export format: json or csv"),
    date_range: str = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export Premium analytics data as JSON or CSV.
    Feature-gated: Requires Premium/Elite subscription.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_advanced_analytics = await feature_gating.has_advanced_analytics(creator_id)
    if not has_advanced_analytics:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Export requires Premium plan or higher",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Get all proposals for export
    date_ranges = {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "1y": timedelta(days=365),
        "all": timedelta(days=3650)
    }
    time_delta = date_ranges.get(date_range, timedelta(days=30))
    start_date = datetime.now(timezone.utc) - time_delta
    
    proposals = await db.proposals.find(
        {"user_id": creator_id, "created_at": {"$gte": start_date.isoformat()}},
        {"_id": 0, "arris_insights_full": 0}  # Exclude full insights for security
    ).to_list(1000)
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        if proposals:
            fieldnames = ["id", "title", "status", "platforms", "timeline", "priority", 
                         "created_at", "submitted_at", "complexity", "processing_time"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for p in proposals:
                writer.writerow({
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "status": p.get("status"),
                    "platforms": ", ".join(p.get("platforms", [])),
                    "timeline": p.get("timeline"),
                    "priority": p.get("priority"),
                    "created_at": p.get("created_at"),
                    "submitted_at": p.get("submitted_at"),
                    "complexity": p.get("arris_insights", {}).get("estimated_complexity"),
                    "processing_time": p.get("arris_insights", {}).get("processing_time_seconds")
                })
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"analytics_export_{date_range}_{datetime.now().strftime('%Y%m%d')}.csv",
            "record_count": len(proposals)
        }
    else:
        return {
            "format": "json",
            "data": proposals,
            "filename": f"analytics_export_{date_range}_{datetime.now().strftime('%Y%m%d')}.json",
            "record_count": len(proposals),
            "exported_at": datetime.now(timezone.utc).isoformat()
        }

# ============== EXPORT ENDPOINTS (Pro/Premium) ==============

@api_router.get("/export/proposals")
async def export_proposals(
    format: str = Query(default="json", description="Export format: json or csv"),
    date_range: str = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export proposals data.
    Feature-gated: Requires Pro tier or higher.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check Pro tier access
    tier, _ = await feature_gating.get_creator_tier(creator_id)
    if tier.lower() not in ["pro", "premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Export requires Pro plan or higher",
                "feature": "data_export",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Premium tier gets insights included
    include_insights = tier.lower() in ["premium", "elite"]
    
    result = await export_service.export_proposals(
        creator_id=creator_id,
        format=format,
        date_range=date_range,
        include_insights=include_insights
    )
    
    return result


@api_router.get("/export/analytics")
async def export_analytics(
    format: str = Query(default="json", description="Export format: json or csv"),
    date_range: str = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export analytics data.
    Pro tier: Basic analytics
    Premium/Elite tier: Enhanced with comparative analytics
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check Pro tier access
    tier, _ = await feature_gating.get_creator_tier(creator_id)
    if tier.lower() not in ["pro", "premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Export requires Pro plan or higher",
                "feature": "analytics_export",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Determine tier level for export
    export_tier = "premium" if tier.lower() in ["premium", "elite"] else "pro"
    
    result = await export_service.export_analytics(
        creator_id=creator_id,
        format=format,
        date_range=date_range,
        tier=export_tier
    )
    
    return result


@api_router.get("/export/revenue")
async def export_revenue(
    format: str = Query(default="json", description="Export format: json or csv"),
    date_range: str = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export revenue/financial data.
    Feature-gated: Requires Premium tier or higher.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check Premium tier access
    tier, _ = await feature_gating.get_creator_tier(creator_id)
    if tier.lower() not in ["premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Revenue export requires Premium plan or higher",
                "feature": "revenue_export",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    result = await export_service.export_revenue_data(
        creator_id=creator_id,
        format=format,
        date_range=date_range
    )
    
    return result


@api_router.get("/export/full-report")
async def export_full_report(
    format: str = Query(default="json", description="Export format: json or csv"),
    date_range: str = Query(default="30d", description="Date range: 7d, 30d, 90d, 1y, all"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Export comprehensive report with all data.
    Feature-gated: Requires Premium tier or higher.
    
    Includes: Proposals, Analytics, Revenue (combined)
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check Premium tier access
    tier, _ = await feature_gating.get_creator_tier(creator_id)
    if tier.lower() not in ["premium", "elite"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Full report export requires Premium plan or higher",
                "feature": "full_report_export",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Gather all data
    proposals_data = await export_service.export_proposals(
        creator_id=creator_id,
        format="json",
        date_range=date_range,
        include_insights=True
    )
    
    analytics_data = await export_service.export_analytics(
        creator_id=creator_id,
        format="json",
        date_range=date_range,
        tier="premium"
    )
    
    revenue_data = await export_service.export_revenue_data(
        creator_id=creator_id,
        format="json",
        date_range=date_range
    )
    
    if format == "csv":
        import io
        output = io.StringIO()
        
        output.write("=" * 50 + "\n")
        output.write("CREATORS HIVE HQ - FULL ANALYTICS REPORT\n")
        output.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
        output.write(f"Date Range: {date_range}\n")
        output.write(f"Creator: {creator.get('name')} ({creator_id})\n")
        output.write("=" * 50 + "\n\n")
        
        # Add proposals section
        output.write("PROPOSALS DATA\n")
        output.write("-" * 30 + "\n")
        output.write(f"Total: {proposals_data['record_count']}\n\n")
        
        # Add analytics section
        output.write("ANALYTICS SUMMARY\n")
        output.write("-" * 30 + "\n")
        analytics = analytics_data["data"]
        output.write(f"Total Proposals: {analytics.get('total_proposals', 0)}\n")
        output.write(f"Approval Rate: {analytics.get('approval_rate', 0)}%\n")
        if "comparative" in analytics:
            output.write(f"Your vs Platform: {analytics['comparative']['approval_rate_vs_platform']}%\n")
        output.write("\n")
        
        # Add revenue section
        output.write("REVENUE SUMMARY\n")
        output.write("-" * 30 + "\n")
        revenue = revenue_data["data"]["summary"]
        output.write(f"Total Revenue: ${revenue.get('total_revenue', 0)}\n")
        output.write(f"Total Expenses: ${revenue.get('total_expenses', 0)}\n")
        output.write(f"Net Profit: ${revenue.get('net_profit', 0)}\n")
        
        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"full_report_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv"
        }
    
    return {
        "format": "json",
        "data": {
            "proposals": proposals_data["data"],
            "analytics": analytics_data["data"],
            "revenue": revenue_data["data"],
            "creator": {
                "id": creator_id,
                "name": creator.get("name"),
                "tier": tier
            }
        },
        "filename": f"full_report_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "content_type": "application/json"
    }

# ============== ELITE TIER ENDPOINTS ==============

# ----- Custom ARRIS Workflows -----

@api_router.get("/elite/workflows")
async def get_elite_workflows(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all custom ARRIS workflows for the Elite creator.
    Feature-gated: Elite tier only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Custom ARRIS Workflows require Elite plan",
                "required_tier": "elite",
                "upgrade_url": "/creator/subscription",
                "feature": "custom_arris_workflows"
            }
        )
    
    workflows = await elite_service.get_workflows(creator_id)
    return {
        "workflows": workflows,
        "total": len(workflows),
        "default_workflow": next((w for w in workflows if w.get("is_default")), None)
    }

@api_router.post("/elite/workflows")
async def create_elite_workflow(
    workflow: WorkflowCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new custom ARRIS workflow.
    Feature-gated: Elite tier only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(status_code=403, detail="Custom ARRIS Workflows require Elite plan")
    
    workflow_data = workflow.dict()
    result = await elite_service.create_workflow(creator_id, workflow_data)
    return {"message": "Workflow created", "workflow": result}

@api_router.get("/elite/workflows/{workflow_id}")
async def get_elite_workflow(
    workflow_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific custom workflow"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(status_code=403, detail="Custom ARRIS Workflows require Elite plan")
    
    workflow = await elite_service.get_workflow(creator_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow

@api_router.put("/elite/workflows/{workflow_id}")
async def update_elite_workflow(
    workflow_id: str,
    updates: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a custom workflow"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(status_code=403, detail="Custom ARRIS Workflows require Elite plan")
    
    result = await elite_service.update_workflow(creator_id, workflow_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"message": "Workflow updated", "workflow": result}

@api_router.delete("/elite/workflows/{workflow_id}")
async def delete_elite_workflow(
    workflow_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a custom workflow"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(status_code=403, detail="Custom ARRIS Workflows require Elite plan")
    
    deleted = await elite_service.delete_workflow(creator_id, workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"message": "Workflow deleted", "workflow_id": workflow_id}

@api_router.post("/elite/workflows/{workflow_id}/run")
async def run_elite_workflow(
    workflow_id: str,
    request: WorkflowRunRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Run a custom workflow on a specific proposal.
    Generates enhanced ARRIS insights based on workflow configuration.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_workflows = await feature_gating.has_custom_arris_workflows(creator_id)
    if not has_workflows:
        raise HTTPException(status_code=403, detail="Custom ARRIS Workflows require Elite plan")
    
    # Get the proposal
    proposal = await db.proposals.find_one(
        {"id": request.proposal_id, "user_id": creator_id},
        {"_id": 0}
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Run the workflow
    result = await elite_service.run_workflow(creator_id, workflow_id, proposal)
    
    return {
        "message": "Workflow executed successfully",
        "result": result
    }

# ----- Brand Integrations -----

@api_router.get("/elite/brands")
async def get_brand_integrations(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all brand integrations/partnerships.
    Feature-gated: Elite tier only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Brand Integrations require Elite plan",
                "required_tier": "elite",
                "upgrade_url": "/creator/subscription",
                "feature": "brand_integrations"
            }
        )
    
    integrations = await elite_service.get_brand_integrations(creator_id, status)
    analytics = await elite_service.get_brand_analytics(creator_id)
    
    return {
        "integrations": integrations,
        "total": len(integrations),
        "analytics": analytics
    }

@api_router.post("/elite/brands")
async def create_brand_integration(
    brand: BrandIntegrationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new brand integration"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(status_code=403, detail="Brand Integrations require Elite plan")
    
    brand_data = brand.dict()
    result = await elite_service.create_brand_integration(creator_id, brand_data)
    return {"message": "Brand integration created", "brand": result}

@api_router.get("/elite/brands/{brand_id}")
async def get_brand_integration(
    brand_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific brand integration"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(status_code=403, detail="Brand Integrations require Elite plan")
    
    integration = await elite_service.get_brand_integration(creator_id, brand_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return integration

@api_router.put("/elite/brands/{brand_id}")
async def update_brand_integration(
    brand_id: str,
    updates: BrandIntegrationUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a brand integration"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(status_code=403, detail="Brand Integrations require Elite plan")
    
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    result = await elite_service.update_brand_integration(creator_id, brand_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return {"message": "Brand integration updated", "brand": result}

@api_router.delete("/elite/brands/{brand_id}")
async def delete_brand_integration(
    brand_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a brand integration"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(status_code=403, detail="Brand Integrations require Elite plan")
    
    deleted = await elite_service.delete_brand_integration(creator_id, brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Brand integration not found")
    
    return {"message": "Brand integration deleted", "brand_id": brand_id}

@api_router.get("/elite/brands/analytics/summary")
async def get_brand_analytics_summary(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get brand partnership analytics summary"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_brands = await feature_gating.has_brand_integrations(creator_id)
    if not has_brands:
        raise HTTPException(status_code=403, detail="Brand Integrations require Elite plan")
    
    analytics = await elite_service.get_brand_analytics(creator_id)
    return analytics

# ----- Elite Dashboard -----

@api_router.get("/elite/dashboard")
async def get_elite_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get Elite dashboard configuration and data.
    Feature-gated: Elite tier only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_custom_dash = await feature_gating.has_custom_dashboard(creator_id)
    if not has_custom_dash:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Custom Dashboard requires Elite plan",
                "required_tier": "elite",
                "upgrade_url": "/creator/subscription",
                "feature": "custom_dashboard"
            }
        )
    
    config = await elite_service.get_dashboard_config(creator_id)
    data = await elite_service.get_dashboard_data(creator_id)
    
    return {
        "config": config,
        "data": data
    }

@api_router.put("/elite/dashboard")
async def update_elite_dashboard(
    updates: DashboardConfigUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update Elite dashboard configuration"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_custom_dash = await feature_gating.has_custom_dashboard(creator_id)
    if not has_custom_dash:
        raise HTTPException(status_code=403, detail="Custom Dashboard requires Elite plan")
    
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    result = await elite_service.update_dashboard_config(creator_id, update_data)
    
    return {"message": "Dashboard updated", "config": result}

# ----- Adaptive Intelligence -----

@api_router.get("/elite/adaptive-intelligence")
async def get_adaptive_intelligence(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get adaptive intelligence profile and recommendations.
    Feature-gated: Elite tier only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    is_elite = await feature_gating.is_elite_tier(creator_id)
    if not is_elite:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Adaptive Intelligence requires Elite plan",
                "required_tier": "elite",
                "upgrade_url": "/creator/subscription",
                "feature": "adaptive_intelligence"
            }
        )
    
    profile = await elite_service.get_adaptive_profile(creator_id)
    recommendations = await elite_service.get_personalized_recommendations(creator_id)
    
    return {
        "profile": profile,
        "recommendations": recommendations,
        "feature": "adaptive_intelligence"
    }

@api_router.post("/elite/adaptive-intelligence/refresh")
async def refresh_adaptive_intelligence(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh/rebuild adaptive intelligence profile from creator's history.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    is_elite = await feature_gating.is_elite_tier(creator_id)
    if not is_elite:
        raise HTTPException(status_code=403, detail="Adaptive Intelligence requires Elite plan")
    
    profile = await elite_service.update_adaptive_profile(creator_id)
    recommendations = await elite_service.get_personalized_recommendations(creator_id)
    
    return {
        "message": "Adaptive Intelligence profile refreshed",
        "profile": profile,
        "recommendations": recommendations
    }

# ----- Elite Feature Status -----

@api_router.get("/elite/status")
async def get_elite_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get Elite tier feature status for the current creator.
    Returns which Elite features are available.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
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

# ============== ARRIS MEMORY & LEARNING ENDPOINTS ==============

@api_router.get("/arris/memory/summary")
async def get_arris_memory_summary(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get a summary of ARRIS memories for the current creator.
    Available to all authenticated creators.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    summary = await arris_memory_service.get_memory_summary(creator_id)
    
    return {
        "creator_id": creator_id,
        "memory_summary": summary
    }

@api_router.get("/arris/memory/recall")
async def recall_arris_memories(
    memory_type: Optional[str] = Query(default=None, description="Filter by memory type"),
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Recall memories from the Memory Palace.
    
    Memory types: interaction, proposal, outcome, pattern, preference, feedback, milestone
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    memories = await arris_memory_service.recall_memories(
        creator_id=creator_id,
        memory_type=memory_type,
        min_importance=min_importance,
        limit=limit
    )
    
    return {
        "memories": memories,
        "count": len(memories),
        "filters_applied": {
            "memory_type": memory_type,
            "min_importance": min_importance,
            "limit": limit
        }
    }

@api_router.post("/arris/memory/store")
async def store_arris_memory(
    memory_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Store a new memory in the Memory Palace.
    
    Required fields:
    - memory_type: interaction, proposal, outcome, pattern, preference, feedback, milestone
    - content: Dict with memory content
    
    Optional:
    - importance: 0.0 to 1.0 (default 0.5)
    - tags: List of tags
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    memory_type = memory_data.get("memory_type")
    content = memory_data.get("content")
    
    if not memory_type or not content:
        raise HTTPException(status_code=400, detail="memory_type and content are required")
    
    memory = await arris_memory_service.store_memory(
        creator_id=creator_id,
        memory_type=memory_type,
        content=content,
        importance=memory_data.get("importance", 0.5),
        tags=memory_data.get("tags", [])
    )
    
    return {"message": "Memory stored", "memory": memory}

@api_router.get("/arris/patterns")
async def get_arris_patterns(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Analyze and retrieve patterns from creator's history.
    Identifies success patterns, risk factors, timing preferences, and more.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    patterns = await arris_memory_service.analyze_patterns(creator_id)
    
    return patterns

@api_router.post("/arris/patterns/analyze")
async def analyze_arris_patterns(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Force a new pattern analysis on creator's history.
    Useful after significant activity changes.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    patterns = await arris_memory_service.analyze_patterns(creator_id)
    
    return {
        "message": "Pattern analysis complete",
        "result": patterns
    }

@api_router.post("/arris/learning/record-outcome")
async def record_arris_outcome(
    outcome_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Record the outcome of a proposal to improve ARRIS predictions.
    
    Required:
    - proposal_id: The proposal ID
    - outcome: approved, rejected, completed, etc.
    
    Optional:
    - feedback: Additional feedback about the outcome
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    proposal_id = outcome_data.get("proposal_id")
    outcome = outcome_data.get("outcome")
    
    if not proposal_id or not outcome:
        raise HTTPException(status_code=400, detail="proposal_id and outcome are required")
    
    result = await arris_memory_service.record_outcome(
        creator_id=creator_id,
        proposal_id=proposal_id,
        outcome=outcome,
        feedback=outcome_data.get("feedback")
    )
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@api_router.get("/arris/learning/metrics")
async def get_arris_learning_metrics(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get ARRIS learning metrics for the current creator.
    Shows prediction accuracy and learning stage.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    return {
        "creator_id": creator_id,
        "metrics": metrics
    }

@api_router.get("/arris/context")
async def get_arris_context(
    proposal_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the rich context ARRIS uses for AI interactions.
    Shows memories, patterns, and historical data being considered.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # If proposal_id provided, get that proposal
    proposal = {}
    if proposal_id:
        proposal = await db.proposals.find_one(
            {"id": proposal_id, "user_id": creator_id},
            {"_id": 0}
        )
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
    
    context = await arris_memory_service.build_rich_context(creator_id, proposal)
    
    return {
        "context": context,
        "proposal_id": proposal_id
    }

@api_router.get("/arris/personalization")
async def get_arris_personalization(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get personalized prompt additions ARRIS uses based on learnings.
    Shows how ARRIS tailors responses to this creator.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    prompt_additions = await arris_memory_service.get_personalized_prompt_additions(creator_id)
    memory_summary = await arris_memory_service.get_memory_summary(creator_id)
    learning_metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    return {
        "creator_id": creator_id,
        "personalization": {
            "prompt_additions": prompt_additions,
            "is_personalized": len(prompt_additions) > 0
        },
        "memory_health": memory_summary.get("memory_health"),
        "learning_stage": learning_metrics.get("learning_stage"),
        "accuracy_rate": learning_metrics.get("accuracy_rate")
    }

@api_router.get("/arris/memory-palace/status")
async def get_memory_palace_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get comprehensive Memory Palace status.
    Shows overall health, memory counts, pattern summary, and learning progress.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get all relevant data
    memory_summary = await arris_memory_service.get_memory_summary(creator_id)
    learning_metrics = await arris_memory_service.get_learning_metrics(creator_id)
    
    # Get pattern count
    patterns = await arris_memory_service.recall_memories(
        creator_id=creator_id,
        memory_type=MemoryType.PATTERN,
        limit=100
    )
    
    return {
        "memory_palace": {
            "status": "active",
            "health": memory_summary.get("memory_health"),
            "total_memories": memory_summary.get("total_memories", 0),
            "by_type": memory_summary.get("by_type", {})
        },
        "pattern_engine": {
            "patterns_identified": len(patterns),
            "pattern_categories": list(set(
                p.get("content", {}).get("category") 
                for p in patterns 
                if p.get("content", {}).get("category")
            ))
        },
        "learning_system": {
            "stage": learning_metrics.get("learning_stage"),
            "accuracy_rate": learning_metrics.get("accuracy_rate"),
            "total_predictions": learning_metrics.get("total_predictions", 0)
        },
        "features": {
            "memory_storage": True,
            "pattern_recognition": True,
            "outcome_learning": True,
            "personalization": True,
            "context_building": True
        }
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
    
    # Check monthly proposal limit for creators
    if auth_user["user_type"] == "creator":
        limit_check = await feature_gating.can_create_proposal(auth_user["user_id"])
        if not limit_check["can_create"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "proposal_limit_reached",
                    "message": limit_check.get("message", "Monthly proposal limit reached"),
                    "limit": limit_check["limit"],
                    "used": limit_check["used"],
                    "upgrade_url": "/creator/subscription"
                }
            )
    
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
    
    # Get processing speed for the creator (Premium/Elite get fast processing)
    creator_id = proposal.get("user_id")
    processing_speed = "standard"
    if creator_id and auth_user["user_type"] == "creator":
        processing_speed = await feature_gating.get_arris_processing_speed(creator_id)
    
    # Generate ARRIS insights with priority processing for Premium/Elite users
    arris_insights_full = await arris_service.generate_project_insights(
        proposal, 
        memory_palace_data,
        processing_speed=processing_speed
    )
    
    # Filter insights based on creator's subscription tier
    if creator_id and auth_user["user_type"] == "creator":
        arris_insights = await feature_gating.filter_arris_insights(creator_id, arris_insights_full)
    else:
        # Admins get full insights
        arris_insights = arris_insights_full
    
    # Store full insights in database (for when user upgrades)
    # But only return filtered insights
    update_data = {
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "arris_insights_full": arris_insights_full,  # Store full for future upgrade access
        "arris_insights": arris_insights,  # Filtered based on tier
        "arris_insights_generated_at": datetime.now(timezone.utc).isoformat(),
        "arris_processing_speed": processing_speed,  # Track processing speed used
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
    
    # EMAIL: Send submission confirmation
    creator_email = proposal.get("creator_email")
    creator_name = proposal.get("creator_name", "Creator")
    if not creator_email:
        creator = await db.creators.find_one(
            {"id": proposal.get("user_id")},
            {"_id": 0, "email": 1, "name": 1}
        )
        if creator:
            creator_email = creator.get("email")
            creator_name = creator.get("name", creator_name)
    
    if creator_email and email_service.is_configured():
        try:
            await email_service.send_proposal_submitted_notification(
                creator_email=creator_email,
                creator_name=creator_name,
                proposal_title=proposal.get("title", "Untitled Proposal"),
                proposal_id=proposal_id
            )
            logger.info(f"Submission email sent to {creator_email} for proposal {proposal_id}")
        except Exception as e:
            logger.error(f"Failed to send submission email: {str(e)}")
    
    # WEBSOCKET: Real-time notifications
    await notification_service.notify_proposal_submitted(
        proposal_id=proposal_id,
        proposal_title=proposal.get("title", "Untitled Proposal"),
        creator_id=proposal.get("user_id"),
        creator_name=creator_name
    )
    
    # WEBSOCKET: Notify ARRIS insights are ready
    await notification_service.notify_arris_insights_ready(
        proposal_id=proposal_id,
        creator_id=proposal.get("user_id"),
        insights_summary=arris_insights.get("summary", "")[:200]
    )
    
    return {
        "id": proposal_id,
        "status": "submitted",
        "message": "Proposal submitted for review. ARRIS has generated insights.",
        "arris_insights": arris_insights,
        "email_sent": creator_email and email_service.is_configured()
    }

@api_router.post("/proposals/{proposal_id}/regenerate-insights")
async def regenerate_insights(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Regenerate ARRIS insights for a proposal with priority processing for Premium/Elite"""
    auth_user = await get_any_authenticated_user(credentials)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get processing speed for the user
    processing_speed = "standard"
    if auth_user["user_type"] == "creator":
        processing_speed = await feature_gating.get_arris_processing_speed(auth_user["user_id"])
    
    # Regenerate insights with priority processing
    arris_insights = await arris_service.generate_project_insights(
        proposal, 
        None,
        processing_speed=processing_speed
    )
    
    await db.proposals.update_one(
        {"id": proposal_id},
        {"$set": {
            "arris_insights": arris_insights,
            "arris_insights_generated_at": datetime.now(timezone.utc).isoformat(),
            "arris_processing_speed": processing_speed,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Insights regenerated", 
        "arris_insights": arris_insights,
        "processing_speed": processing_speed,
        "priority_processed": processing_speed == "fast"
    }

@api_router.get("/arris/queue-stats")
async def get_arris_queue_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get ARRIS processing queue statistics.
    Shows queue lengths, processing stats, and average times.
    """
    await get_any_authenticated_user(credentials)
    
    queue_stats = arris_service.get_queue_stats()
    
    return {
        "queue": {
            "fast_queue": queue_stats["fast_queue_length"],
            "standard_queue": queue_stats["standard_queue_length"],
            "currently_processing": queue_stats["currently_processing"]
        },
        "processing_stats": queue_stats["processing_stats"],
        "message": "Premium/Elite users are processed in the fast queue with priority"
    }

@api_router.get("/arris/my-processing-speed")
async def get_my_arris_processing_speed(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the current creator's ARRIS processing speed tier.
    Returns 'fast' for Premium/Elite, 'standard' for others.
    """
    auth_user = await get_any_authenticated_user(credentials)
    
    if auth_user["user_type"] != "creator":
        return {
            "processing_speed": "standard",
            "tier": "admin",
            "message": "Admin users use standard processing"
        }
    
    processing_speed = await feature_gating.get_arris_processing_speed(auth_user["user_id"])
    tier_info = await feature_gating.get_creator_tier(auth_user["user_id"])
    tier = tier_info[0].value if hasattr(tier_info[0], 'value') else tier_info[0]
    
    return {
        "processing_speed": processing_speed,
        "tier": tier,
        "is_fast": processing_speed == "fast",
        "benefits": {
            "fast": ["Priority queue processing", "Reduced wait time", "Dedicated processing slots"],
            "standard": ["Standard queue processing", "Fair queue ordering"]
        }.get(processing_speed, []),
        "message": f"Your ARRIS processing speed: {processing_speed.upper()}" + 
                  (" - Premium/Elite benefit active! 🚀" if processing_speed == "fast" else " - Upgrade to Premium for faster processing")
    }

# ============== ARRIS ACTIVITY FEED (Premium/Elite) ==============

@api_router.get("/arris/activity-feed")
async def get_arris_activity_feed(
    limit: int = Query(default=20, le=50),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get real-time ARRIS activity feed.
    Feature-gated: Premium/Elite users see full feed with their queue position.
    Pro and below see limited feed without personal queue data.
    """
    auth_user = await get_any_authenticated_user(credentials)
    
    # Check tier for feature access
    has_premium = False
    if auth_user["user_type"] == "creator":
        has_premium = await feature_gating.has_advanced_analytics(auth_user["user_id"])
    
    # Get activity feed data
    live_status = await arris_activity_service.get_live_status()
    
    # Get user's queue items if Premium
    my_queue_items = []
    if has_premium and auth_user["user_type"] == "creator":
        my_queue_items = await arris_activity_service.get_creator_queue_items(auth_user["user_id"])
    
    return {
        "has_premium_access": has_premium,
        "live_status": live_status,
        "my_queue_items": my_queue_items,
        "feature_highlights": [
            "Real-time queue position updates",
            "Processing time estimates",
            "Live activity feed"
        ] if not has_premium else None
    }


@api_router.get("/arris/my-queue-position")
async def get_my_arris_queue_position(
    proposal_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the current creator's position in the ARRIS queue.
    Feature-gated: Premium/Elite only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Real-time queue position requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Get all queue items for this creator
    queue_items = await arris_activity_service.get_creator_queue_items(creator_id)
    
    # If specific proposal requested, get that position
    if proposal_id:
        position = await arris_activity_service.get_queue_position(creator_id, proposal_id)
        return {
            "proposal_id": proposal_id,
            "position": position,
            "all_items": queue_items
        }
    
    # Return all queue items
    queue_stats = await arris_activity_service.get_queue_stats()
    
    return {
        "queue_items": queue_items,
        "total_in_queue": len(queue_items),
        "queue_stats": queue_stats
    }


@api_router.get("/arris/live-stats")
async def get_arris_live_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get live ARRIS processing statistics.
    Available to all authenticated users.
    """
    await get_any_authenticated_user(credentials)
    
    queue_stats = await arris_activity_service.get_queue_stats()
    
    return {
        "fast_queue": queue_stats["fast_queue_length"],
        "standard_queue": queue_stats["standard_queue_length"],
        "total_queued": queue_stats["total_queue_length"],
        "currently_processing": queue_stats["currently_processing"],
        "total_processed_today": queue_stats["total_processed"],
        "avg_processing_time": {
            "fast": queue_stats["avg_fast_time"],
            "standard": queue_stats["avg_standard_time"]
        },
        "estimated_wait": {
            "fast_queue": queue_stats["estimated_wait_fast"],
            "standard_queue": queue_stats["estimated_wait_standard"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@api_router.get("/arris/recent-activity")
async def get_arris_recent_activity(
    limit: int = Query(default=10, le=30),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get recent ARRIS processing activity (anonymized).
    Available to all authenticated users.
    """
    await get_any_authenticated_user(credentials)
    
    activity = await arris_activity_service.get_activity_feed(limit=limit, include_anonymous=True)
    
    return {
        "activity": activity,
        "count": len(activity)
    }


# ============== ARRIS HISTORICAL LEARNING (Premium/Elite) ==============

@api_router.get("/arris/learning-timeline")
async def get_arris_learning_timeline(
    date_range: str = Query(default="all", regex="^(7d|30d|90d|1y|all)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get ARRIS learning timeline for the creator.
    Shows memory accumulation, pattern discoveries, and accuracy improvements over time.
    Feature-gated: Premium/Elite only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "ARRIS Learning Timeline requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    timeline = await arris_historical_service.get_learning_timeline(creator_id, date_range)
    return timeline


@api_router.get("/arris/learning-comparison")
async def get_arris_learning_comparison(
    period1: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    period2: str = Query(default="prev_30d", regex="^(prev_7d|prev_30d|prev_90d)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Compare ARRIS learning between two time periods.
    Shows growth and improvement over time.
    Feature-gated: Premium/Elite only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "ARRIS Learning Comparison requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    comparison = await arris_historical_service.get_comparative_analysis(
        creator_id, period1, period2
    )
    return comparison


@api_router.get("/arris/learning-snapshot")
async def get_arris_learning_snapshot(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a snapshot of current ARRIS learning state.
    Shows memory summary, active patterns, and learning health.
    Available to all creators but Premium gets enhanced data.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    
    snapshot = await arris_historical_service.get_learning_snapshot(creator_id)
    
    # Add premium flag
    snapshot["is_premium"] = has_premium
    
    # If not premium, limit some data
    if not has_premium:
        snapshot["active_patterns"] = snapshot.get("active_patterns", [])[:3]
        snapshot["recent_activity"] = snapshot.get("recent_activity", [])[:5]
        snapshot["upgrade_prompt"] = {
            "message": "Upgrade to Premium for full learning insights",
            "features": ["Complete pattern history", "Detailed growth metrics", "Historical comparisons"]
        }
    
    return snapshot


@api_router.get("/arris/growth-chart")
async def get_arris_growth_chart(
    metric: str = Query(default="memories", regex="^(memories|patterns|accuracy|interactions)$"),
    granularity: str = Query(default="daily", regex="^(daily|weekly|monthly)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get chart data for visualizing ARRIS learning growth.
    Feature-gated: Premium/Elite only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "ARRIS Growth Charts require Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    chart_data = await arris_historical_service.get_growth_chart_data(
        creator_id, metric, granularity
    )
    return chart_data


@api_router.get("/arris/milestones")
async def get_arris_milestones(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get ARRIS learning milestones for the creator.
    Shows achievements and learning journey highlights.
    Available to all creators.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    timeline = await arris_historical_service.get_learning_timeline(creator_id, "all")
    
    return {
        "milestones": timeline.get("milestones", []),
        "creator_id": creator_id
    }


# ============== ARRIS VOICE INTERACTION ENDPOINTS ==============

@api_router.get("/arris/voice/status")
async def get_voice_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get ARRIS voice interaction service status and available voices.
    Feature-gated: Premium/Elite only.
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        return {
            "enabled": False,
            "message": "Voice interaction requires Premium plan or higher",
            "upgrade_url": "/creator/subscription"
        }
    
    voices = arris_voice_service.get_available_voices()
    return {
        "enabled": True,
        "voices": voices["voices"],
        "default_voice": voices["default"],
        "models": voices["models"],
        "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
        "max_audio_size_mb": 25
    }


@api_router.post("/arris/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Query(default="en", description="Language code (ISO-639-1)"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Transcribe audio to text using ARRIS voice service.
    Feature-gated: Premium/Elite only.
    
    Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
    Max file size: 25 MB
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Voice interaction requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/mp3", "audio/mp4", "audio/wav", 
                     "audio/webm", "audio/m4a", "audio/x-m4a", "video/webm"]
    if audio.content_type and audio.content_type not in allowed_types:
        # Also check by extension
        ext = audio.filename.split('.')[-1].lower() if audio.filename else ""
        allowed_exts = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Allowed: {', '.join(allowed_exts)}"
            )
    
    # Read audio data
    audio_data = await audio.read()
    
    # Check file size (25 MB limit)
    if len(audio_data) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Audio file too large. Maximum size is 25 MB."
        )
    
    # Transcribe
    result = await arris_voice_service.transcribe_audio(
        audio_data=audio_data,
        filename=audio.filename or "audio.webm",
        language=language
    )
    
    # Log usage
    await db.arris_usage_log.insert_one({
        "id": f"ARRIS-VOICE-{creator_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_query_snippet": f"Voice transcription: {result.get('text', '')[:100]}..." if result.get('text') else "Voice transcription failed",
        "response_type": "voice_transcription",
        "query_category": "Voice",
        "success": result.get("success", False),
        "processing_time_s": result.get("processing_time_seconds", 0)
    })
    
    return result


@api_router.post("/arris/voice/speak")
async def generate_speech(
    text: str = Query(..., description="Text to convert to speech", max_length=4096),
    voice: Optional[str] = Query(default="nova", description="Voice to use"),
    speed: float = Query(default=1.0, ge=0.25, le=4.0, description="Speech speed"),
    format: str = Query(default="mp3", description="Output format"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Convert text to speech using ARRIS voice service.
    Feature-gated: Premium/Elite only.
    
    Available voices: alloy, ash, coral, echo, fable, nova (default), onyx, sage, shimmer
    Speed: 0.25 to 4.0 (default: 1.0)
    Formats: mp3, opus, aac, flac, wav, pcm
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Voice interaction requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Validate voice
    valid_voices = ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]
    if voice not in valid_voices:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid voice. Choose from: {', '.join(valid_voices)}"
        )
    
    # Validate format
    valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Choose from: {', '.join(valid_formats)}"
        )
    
    # Generate speech
    result = await arris_voice_service.generate_speech(
        text=text,
        voice=voice,
        speed=speed,
        output_format=format
    )
    
    return result


@api_router.post("/arris/voice/query")
async def voice_query(
    audio: UploadFile = File(...),
    respond_with_voice: bool = Query(default=True, description="Generate audio response"),
    voice: Optional[str] = Query(default="nova", description="Voice for response"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Complete voice interaction: transcribe query → ARRIS processes → voice response.
    Feature-gated: Premium/Elite only.
    
    This endpoint handles the full voice conversation flow:
    1. Transcribes your audio question using Whisper
    2. Sends the question to ARRIS AI for processing
    3. Returns both text and audio response
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Check if user has Premium access
    has_premium = await feature_gating.has_advanced_analytics(creator_id)
    if not has_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_gated",
                "message": "Voice interaction requires Premium plan or higher",
                "required_tier": "premium",
                "upgrade_url": "/creator/subscription"
            }
        )
    
    # Read audio data
    audio_data = await audio.read()
    
    # Check file size
    if len(audio_data) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Audio file too large. Maximum size is 25 MB."
        )
    
    # Build creator context
    creator_context = {
        "name": creator.get("name", "Creator"),
        "platforms": creator.get("platforms", []),
        "niche": creator.get("niche", "Content Creation")
    }
    
    # Process voice query
    result = await arris_voice_service.voice_query(
        audio_data=audio_data,
        filename=audio.filename or "audio.webm",
        creator_context=creator_context,
        respond_with_voice=respond_with_voice,
        voice=voice
    )
    
    # Log usage
    transcription_text = result.get("transcription", {}).get("text", "")
    arris_response_text = result.get("arris_response", {}).get("text", "")
    
    await db.arris_usage_log.insert_one({
        "id": f"ARRIS-VOICE-QUERY-{creator_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_query_snippet": f"Voice query: {transcription_text[:100]}..." if transcription_text else "Voice query",
        "response_type": "voice_conversation",
        "response_snippet": arris_response_text[:200] if arris_response_text else "",
        "query_category": "Voice",
        "success": result.get("arris_response", {}).get("success", False),
        "processing_time_s": result.get("total_processing_time", 0)
    })
    
    # Notify via WebSocket
    await notification_service.notify_arris_insights_ready(
        creator_id=creator_id,
        proposal_id="voice-query",
        proposal_title="Voice Conversation",
        insight_type="voice"
    )
    
    return result


@api_router.get("/arris/voice/voices")
async def get_available_voices(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get list of available TTS voices.
    Available to all authenticated users (for preview).
    """
    await get_current_creator(credentials, db)
    return arris_voice_service.get_available_voices()


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
    
    # Get updated proposal for webhook data and email notifications
    updated_proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    # Get creator info for email notifications
    creator_email = updated_proposal.get("creator_email")
    creator_name = updated_proposal.get("creator_name", "Creator")
    proposal_title = updated_proposal.get("title", "Untitled Proposal")
    
    # If creator email not in proposal, try to fetch from creators collection
    if not creator_email:
        creator = await db.creators.find_one(
            {"id": updated_proposal.get("user_id")},
            {"_id": 0, "email": 1, "name": 1}
        )
        if creator:
            creator_email = creator.get("email")
            creator_name = creator.get("name", creator_name)
    
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
        
        # EMAIL: Send approval notification
        if creator_email and email_service.is_configured():
            try:
                await email_service.send_proposal_approved_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id,
                    project_id=update_data["assigned_project_id"],
                    review_notes=update.review_notes
                )
                logger.info(f"Approval email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send approval email: {str(e)}")
        
        # WEBSOCKET: Real-time notification
        await notification_service.notify_proposal_approved(
            proposal_id=proposal_id,
            proposal_title=proposal_title,
            project_id=update_data["assigned_project_id"],
            creator_id=updated_proposal.get("user_id")
        )
        
        return {
            "message": "Proposal approved and project created",
            "project_id": update_data["assigned_project_id"],
            "email_sent": creator_email and email_service.is_configured()
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
        
        # EMAIL: Send rejection notification
        if creator_email and email_service.is_configured():
            try:
                await email_service.send_proposal_rejected_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id,
                    rejection_reason=update.review_notes
                )
                logger.info(f"Rejection email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send rejection email: {str(e)}")
        
        # WEBSOCKET: Real-time notification
        await notification_service.notify_proposal_rejected(
            proposal_id=proposal_id,
            proposal_title=proposal_title,
            creator_id=updated_proposal.get("user_id"),
            reason=update.review_notes
        )
        
        return {
            "message": "Proposal rejected",
            "email_sent": creator_email and email_service.is_configured()
        }
    
    if update.status == "under_review":
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
        
        # EMAIL: Send under review notification
        if creator_email and email_service.is_configured():
            try:
                await email_service.send_proposal_under_review_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id
                )
                logger.info(f"Under review email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send under review email: {str(e)}")
        
        # WEBSOCKET: Real-time notification
        await notification_service.notify_proposal_under_review(
            proposal_id=proposal_id,
            proposal_title=proposal_title,
            creator_id=updated_proposal.get("user_id")
        )
        
        return {
            "message": "Proposal moved to under review",
            "email_sent": creator_email and email_service.is_configured()
        }
    
    if update.status == "completed":
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
        
        # EMAIL: Send completion notification
        if creator_email and email_service.is_configured():
            try:
                await email_service.send_proposal_completed_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id,
                    project_id=updated_proposal.get("assigned_project_id", "N/A")
                )
                logger.info(f"Completion email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send completion email: {str(e)}")
        
        return {
            "message": "Proposal marked as completed",
            "email_sent": creator_email and email_service.is_configured()
        }
    
    if update.status and update.status not in ["approved", "rejected", "under_review", "completed"]:
        # WEBHOOK: Emit status changed event for other statuses
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

# ============== EMAIL SERVICE ==============

@api_router.get("/email/status")
async def get_email_service_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get email service status and configuration (admin only).
    Returns whether SendGrid is configured and operational.
    """
    await get_current_user(credentials, db)
    
    return {
        "service": "sendgrid",
        "configured": email_service.is_configured(),
        "sender_email": email_service.sender_email,
        "sender_name": email_service.sender_name,
        "features": {
            "proposal_submitted": True,
            "proposal_approved": True,
            "proposal_rejected": True,
            "proposal_under_review": True,
            "proposal_completed": True
        },
        "status": "active" if email_service.is_configured() else "not_configured",
        "setup_instructions": None if email_service.is_configured() else {
            "step_1": "Create a SendGrid account at https://sendgrid.com",
            "step_2": "Generate an API key at https://app.sendgrid.com/settings/api_keys",
            "step_3": "Add SENDGRID_API_KEY to your backend/.env file",
            "step_4": "Optionally set SENDER_EMAIL for a verified sender"
        }
    }

@api_router.post("/email/test")
async def send_test_email(
    email_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Send a test email to verify SendGrid configuration (admin only).
    
    Request body:
    - to_email: Recipient email address
    """
    await get_current_user(credentials, db)
    
    if not email_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "email_not_configured",
                "message": "SendGrid API key not configured",
                "setup_url": "https://app.sendgrid.com/settings/api_keys"
            }
        )
    
    to_email = email_data.get("to_email")
    if not to_email:
        raise HTTPException(status_code=400, detail="to_email is required")
    
    try:
        content = f"""
<h2 style="color: #6366f1;">🐝 Test Email from Creators Hive HQ</h2>
<p>This is a test email to verify your SendGrid configuration is working correctly.</p>
<p><strong>Timestamp:</strong> {datetime.now(timezone.utc).isoformat()}</p>
<p style="color: #22c55e;">✅ Your email notifications are configured and working!</p>
"""
        success = await email_service.send_email(
            to_email=to_email,
            subject="🐝 Test Email - Creators Hive HQ",
            html_content=email_service._get_base_template(content)
        )
        
        if success:
            return {
                "message": "Test email sent successfully",
                "to": to_email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except EmailDeliveryError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Test email error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")

@api_router.post("/elite/contact")
async def submit_elite_inquiry(
    inquiry: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Submit an Elite plan inquiry from an authenticated creator.
    Sends notification to sales team and confirmation to creator.
    
    Request body:
    - message: str (required) - Inquiry message
    - company_name: str (optional) - Creator's company name
    - team_size: str (optional) - Team size (solo, 2-5, 6-20, 21-50, 50+)
    """
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    creator_email = creator["email"]
    creator_name = creator.get("name", "Creator")
    
    message = inquiry.get("message")
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    company_name = inquiry.get("company_name")
    team_size = inquiry.get("team_size")
    
    # Store inquiry in database
    inquiry_doc = {
        "id": f"EI-{str(uuid.uuid4())[:8]}",
        "creator_id": creator_id,
        "creator_email": creator_email,
        "creator_name": creator_name,
        "company_name": company_name,
        "team_size": team_size,
        "message": message.strip(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.elite_inquiries.insert_one(inquiry_doc)
    
    # Send emails
    sales_email_sent = False
    confirmation_email_sent = False
    
    if email_service.is_configured():
        try:
            # Send to sales team
            sales_email_sent = await email_service.send_elite_inquiry_to_sales(
                creator_name=creator_name,
                creator_email=creator_email,
                company_name=company_name,
                team_size=team_size,
                message=message.strip(),
                creator_id=creator_id
            )
            logger.info(f"Elite inquiry email sent to sales for creator {creator_id}")
        except Exception as e:
            logger.error(f"Failed to send Elite inquiry to sales: {str(e)}")
        
        try:
            # Send confirmation to creator
            confirmation_email_sent = await email_service.send_elite_inquiry_confirmation(
                creator_email=creator_email,
                creator_name=creator_name
            )
            logger.info(f"Elite inquiry confirmation sent to {creator_email}")
        except Exception as e:
            logger.error(f"Failed to send Elite inquiry confirmation: {str(e)}")
    
    # Emit webhook event
    await webhook_service.emit(
        event_type=WebhookEventType.ELITE_INQUIRY_SUBMITTED,
        payload={
            "inquiry_id": inquiry_doc["id"],
            "creator_name": creator_name,
            "creator_email": creator_email,
            "company_name": company_name,
            "team_size": team_size
        },
        source_entity="elite_inquiry",
        source_id=inquiry_doc["id"],
        user_id=creator_id
    )
    
    # WEBSOCKET: Real-time notification to admins
    await notification_service.notify_elite_inquiry_received(
        inquiry_id=inquiry_doc["id"],
        creator_name=creator_name,
        creator_email=creator_email,
        company_name=company_name
    )
    
    return {
        "message": "Thank you for your interest in Elite! Our team will be in touch within 24 hours.",
        "inquiry_id": inquiry_doc["id"],
        "sales_email_sent": sales_email_sent,
        "confirmation_email_sent": confirmation_email_sent
    }

@api_router.get("/elite/inquiries")
async def get_elite_inquiries(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all Elite plan inquiries (admin only).
    """
    await get_current_user(credentials, db)
    
    query = {}
    if status:
        query["status"] = status
    
    inquiries = await db.elite_inquiries.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Get stats
    total = await db.elite_inquiries.count_documents({})
    pending = await db.elite_inquiries.count_documents({"status": "pending"})
    contacted = await db.elite_inquiries.count_documents({"status": "contacted"})
    converted = await db.elite_inquiries.count_documents({"status": "converted"})
    
    return {
        "inquiries": inquiries,
        "stats": {
            "total": total,
            "pending": pending,
            "contacted": contacted,
            "converted": converted
        }
    }

@api_router.patch("/elite/inquiries/{inquiry_id}")
async def update_elite_inquiry(
    inquiry_id: str,
    update: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update an Elite inquiry status (admin only).
    
    Status options: pending, contacted, converted, declined
    """
    await get_current_user(credentials, db)
    
    allowed_statuses = ["pending", "contacted", "converted", "declined"]
    new_status = update.get("status")
    notes = update.get("notes")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if new_status:
        if new_status not in allowed_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {allowed_statuses}")
        update_data["status"] = new_status
    
    if notes:
        update_data["notes"] = notes
    
    result = await db.elite_inquiries.update_one(
        {"id": inquiry_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    
    return {"message": "Inquiry updated", "inquiry_id": inquiry_id}

# ============== SUBSCRIPTION & STRIPE (Self-Funding Loop) ==============

@api_router.get("/subscriptions/plans")
async def get_subscription_plans():
    """Get available subscription plans (public endpoint)"""
    plans = []
    
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        if plan_id == "free":
            plans.append(PlanInfo(
                plan_id=plan_id,
                name=plan["name"],
                tier=plan["tier"].value if isinstance(plan["tier"], SubscriptionTier) else plan["tier"],
                price=0.0,
                features=plan["features"],
                description=plan["description"]
            ))
        elif plan_id == "elite":
            # Elite is custom pricing
            plans.append(PlanInfo(
                plan_id=plan_id,
                name=plan["name"],
                tier=plan["tier"].value if isinstance(plan["tier"], SubscriptionTier) else plan["tier"],
                billing_cycle=None,
                price=0,
                features=plan["features"],
                description=plan["description"],
                is_custom=True
            ))
        else:
            plans.append(PlanInfo(
                plan_id=plan_id,
                name=plan["name"],
                tier=plan["tier"].value if isinstance(plan["tier"], SubscriptionTier) else plan["tier"],
                billing_cycle=plan.get("billing_cycle", "monthly"),
                price=plan["price"],
                monthly_equivalent=plan.get("monthly_equivalent"),
                savings=plan.get("savings"),
                features=plan["features"],
                description=plan["description"],
                is_popular=plan_id == "pro_monthly"
            ))
    
    return PlansResponse(plans=plans)

@api_router.get("/subscriptions/my-status")
async def get_my_subscription_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current subscription status for logged-in creator"""
    creator = await get_current_creator(credentials, db)
    creator_id = creator["id"]
    
    # Get full feature access using feature gating service
    feature_access = await feature_gating.get_full_feature_access(creator_id)
    
    features = feature_access.get("features", {})
    
    return {
        "has_subscription": feature_access.get("subscription_active", False),
        "tier": feature_access.get("tier", "free"),
        "plan_id": feature_access.get("plan_id", "free"),
        "current_period_end": feature_access.get("current_period_end"),
        "features": features,
        # Proposal limits
        "proposals_per_month": features.get("proposals_per_month", 1),
        "proposals_used": features.get("proposals_used", 0),
        "proposals_remaining": features.get("proposals_remaining", 1),
        "can_create_proposal": features.get("can_create_proposal", True),
        # ARRIS access
        "arris_insight_level": features.get("arris_insight_level", "summary_only"),
        "can_use_arris": features.get("arris_insight_level") != "none",
        # Dashboard
        "dashboard_level": features.get("dashboard_level", "basic"),
        "advanced_analytics": features.get("advanced_analytics", False),
        # Review & Support
        "priority_review": features.get("priority_review", False),
        "support_level": features.get("support_level", "community"),
        # API
        "api_access": features.get("api_access", False)
    }

@api_router.get("/subscriptions/feature-access")
async def get_feature_access(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get detailed feature access for the logged-in creator"""
    creator = await get_current_creator(credentials, db)
    return await feature_gating.get_full_feature_access(creator["id"])

@api_router.get("/subscriptions/can-create-proposal")
async def check_can_create_proposal(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Check if creator can create a new proposal this month"""
    creator = await get_current_creator(credentials, db)
    return await feature_gating.can_create_proposal(creator["id"])

@api_router.post("/subscriptions/checkout", response_model=CheckoutResponse)
async def create_subscription_checkout(
    request: CheckoutRequest,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create Stripe checkout session for subscription"""
    creator = await get_current_creator(credentials, db)
    
    # Build webhook URL from request
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    try:
        result = await stripe_service.create_checkout_session(
            plan_id=request.plan_id,
            origin_url=request.origin_url,
            creator_id=creator["id"],
            creator_email=creator["email"],
            webhook_url=webhook_url
        )
        
        return CheckoutResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@api_router.get("/subscriptions/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of a checkout session (for polling)"""
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    try:
        result = await stripe_service.get_checkout_status(session_id, webhook_url)
        
        # If payment completed, trigger webhook event
        if result.get("payment_status") == "paid":
            metadata = result.get("metadata", {})
            await webhook_service.emit(
                event_type=WebhookEventType.SUBSCRIPTION_CREATED,
                payload={
                    "plan_id": metadata.get("plan_id"),
                    "tier": metadata.get("tier"),
                    "amount": result.get("amount"),
                    "session_id": session_id
                },
                source_entity="subscription",
                source_id=session_id,
                user_id=metadata.get("creator_id")
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Checkout status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get checkout status")

@api_router.get("/subscriptions/my-transactions")
async def get_my_transactions(
    limit: int = Query(default=20, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get payment transactions for logged-in creator"""
    creator = await get_current_creator(credentials, db)
    
    transactions = await db.payment_transactions.find(
        {"creator_id": creator["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"transactions": transactions, "total": len(transactions)}

# Stripe Webhook endpoint (public - called by Stripe)
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    try:
        result = await stripe_service.handle_webhook(body, signature, webhook_url)
        
        # If payment succeeded, trigger revenue webhook
        if result.get("event_type") == "checkout.session.completed" and result.get("payment_status") == "paid":
            # Get transaction details
            transaction = await db.payment_transactions.find_one(
                {"stripe_session_id": result.get("session_id")},
                {"_id": 0}
            )
            
            if transaction:
                # Emit subscription created event
                await webhook_service.emit(
                    event_type=WebhookEventType.SUBSCRIPTION_CREATED,
                    payload={
                        "plan_id": transaction.get("plan_id"),
                        "amount": transaction.get("amount"),
                        "billing_cycle": transaction.get("billing_cycle")
                    },
                    source_entity="subscription",
                    source_id=result.get("session_id"),
                    user_id=transaction.get("creator_id")
                )
                
                # Emit revenue recorded event
                await webhook_service.emit(
                    event_type=WebhookEventType.REVENUE_RECORDED,
                    payload={
                        "amount": transaction.get("amount"),
                        "source": "stripe_subscription",
                        "plan_id": transaction.get("plan_id")
                    },
                    source_entity="payment",
                    source_id=result.get("session_id"),
                    user_id=transaction.get("creator_id")
                )
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Admin endpoints for subscription management
@api_router.get("/admin/subscriptions")
async def get_all_subscriptions(
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin: Get all subscriptions"""
    await get_current_user(credentials, db)
    
    query = {}
    if status:
        query["status"] = status
    if tier:
        query["tier"] = tier
    
    subscriptions = await db.creator_subscriptions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"subscriptions": subscriptions, "total": len(subscriptions)}

@api_router.get("/admin/subscriptions/revenue")
async def get_subscription_revenue(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Admin: Get subscription revenue summary"""
    await get_current_user(credentials, db)
    
    # Total revenue from subscriptions
    revenue_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "total_transactions": {"$sum": 1}
        }}
    ]
    revenue_result = await db.payment_transactions.aggregate(revenue_pipeline).to_list(1)
    
    # Revenue by plan
    plan_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$plan_id",
            "revenue": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    plan_revenue = await db.payment_transactions.aggregate(plan_pipeline).to_list(10)
    
    # Active subscriptions by tier
    tier_pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$tier", "count": {"$sum": 1}}}
    ]
    tier_counts = await db.creator_subscriptions.aggregate(tier_pipeline).to_list(5)
    
    return {
        "total_revenue": revenue_result[0]["total_revenue"] if revenue_result else 0,
        "total_transactions": revenue_result[0]["total_transactions"] if revenue_result else 0,
        "by_plan": {item["_id"]: {"revenue": item["revenue"], "count": item["count"]} for item in plan_revenue},
        "active_by_tier": {item["_id"]: item["count"] for item in tier_counts}
    }

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

# ============== 06_CALCULATOR - ADVANCED FINANCIAL ANALYTICS ==============

@api_router.get("/calculator/metrics/mrr")
async def get_mrr(
    user_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get Monthly Recurring Revenue (MRR) with growth metrics.
    MRR = Sum of all active subscription revenue per month.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_mrr(user_id)

@api_router.get("/calculator/metrics/arr")
async def get_arr(
    user_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get Annual Recurring Revenue (ARR).
    ARR = MRR × 12
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_arr(user_id)

@api_router.get("/calculator/metrics/churn")
async def get_churn_rate(
    user_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Calculate subscription churn rate (last 30 days).
    Churn Rate = (Lost Subscribers / Total Subscribers at Start) × 100
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_churn_rate(user_id)

@api_router.get("/calculator/metrics/ltv")
async def get_ltv(
    user_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Calculate Customer Lifetime Value (LTV).
    LTV = ARPU × Average Customer Lifetime
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_ltv(user_id)

@api_router.get("/calculator/metrics/all")
async def get_all_key_metrics(
    user_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all key financial metrics in one call: MRR, ARR, Churn, LTV.
    """
    await get_current_user(credentials, db)
    
    mrr = await calculator_service.get_mrr(user_id)
    arr = await calculator_service.get_arr(user_id)
    churn = await calculator_service.get_churn_rate(user_id)
    ltv = await calculator_service.get_ltv(user_id)
    
    return {
        "mrr": mrr,
        "arr": arr,
        "churn": churn,
        "ltv": ltv,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/calculator/revenue/breakdown")
async def get_revenue_breakdown(
    user_id: Optional[str] = None,
    months_back: int = Query(default=6, ge=1, le=24),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed revenue breakdown by source/category over time.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_revenue_breakdown(user_id, months_back=months_back)

@api_router.get("/calculator/revenue/trends")
async def get_revenue_trends(
    user_id: Optional[str] = None,
    months_back: int = Query(default=12, ge=3, le=36),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analyze revenue trends over time with growth rates.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_revenue_trends(user_id, months_back=months_back)

@api_router.get("/calculator/expenses/breakdown")
async def get_expense_breakdown(
    user_id: Optional[str] = None,
    months_back: int = Query(default=6, ge=1, le=24),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed expense breakdown by category over time.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_expense_breakdown(user_id, months_back=months_back)

@api_router.get("/calculator/profit/analysis")
async def get_profit_analysis(
    user_id: Optional[str] = None,
    months_back: int = Query(default=6, ge=1, le=24),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Comprehensive profit analysis including margins and health indicators.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_profit_analysis(user_id, months_back=months_back)

@api_router.get("/calculator/forecast")
async def get_revenue_forecast(
    user_id: Optional[str] = None,
    months_ahead: int = Query(default=3, ge=1, le=12),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Forecast future revenue based on historical patterns.
    """
    await get_current_user(credentials, db)
    return await calculator_service.forecast_revenue(user_id, months_ahead=months_ahead)

@api_router.get("/calculator/self-funding-loop")
async def get_self_funding_loop_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get comprehensive status of the Self-Funding Loop.
    Shows how subscription revenue flows through the Calculator.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_self_funding_loop_status()

@api_router.get("/calculator/creator/{creator_id}/summary")
async def get_creator_financial_summary(
    creator_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get comprehensive financial summary for a specific creator.
    Includes subscription status, revenue, expenses, and profit analysis.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_creator_financial_summary(creator_id)

@api_router.get("/calculator/dashboard")
async def get_financial_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get comprehensive platform-wide financial dashboard.
    Includes MRR, ARR, Churn, LTV, Self-Funding Loop status, profit analysis, and forecasts.
    """
    await get_current_user(credentials, db)
    return await calculator_service.get_platform_financial_dashboard()

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


# ============== ADMIN PATTERN ENGINE DASHBOARD (Phase 4) ==============

@api_router.get("/admin/patterns/overview")
async def get_admin_pattern_overview(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get platform-wide pattern overview for admin dashboard.
    Admin-only endpoint.
    """
    # Verify admin access
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.get_platform_overview()


@api_router.get("/admin/patterns/detect")
async def detect_platform_patterns(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Run comprehensive pattern detection across the platform.
    Returns categorized patterns with confidence scores and recommendations.
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.detect_all_patterns()


@api_router.get("/admin/patterns/cohorts")
async def get_cohort_analysis(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analyze creators by cohort (registration month, tier, engagement level).
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.get_cohort_analysis()


@api_router.get("/admin/patterns/rankings")
async def get_creator_rankings(
    sort_by: str = Query(default="approval_rate", description="approval_rate, total_proposals, approved_proposals"),
    limit: int = Query(default=20, le=100),
    tier: Optional[str] = Query(default=None, description="Filter by tier"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get ranked list of creators by performance metrics.
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.get_creator_ranking(
        sort_by=sort_by,
        limit=limit,
        tier_filter=tier
    )


@api_router.get("/admin/patterns/revenue")
async def get_revenue_analysis(
    period_days: int = Query(default=90, le=365, description="Analysis period in days"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analyze revenue patterns from subscriptions and Calculator entries.
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.get_revenue_analysis(period_days=period_days)


@api_router.get("/admin/patterns/insights")
async def get_actionable_insights(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate actionable insights for admin based on detected patterns.
    Returns prioritized list of insights with recommendations.
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    return await pattern_engine.get_actionable_insights()


@api_router.get("/admin/patterns/churn-risk")
async def get_churn_risk_creators(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get list of creators at risk of churning.
    Admin-only endpoint.
    """
    current_user = await get_current_user(credentials, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    patterns = await pattern_engine.detect_all_patterns()
    return {
        "at_risk_creators": patterns.get("churn_patterns", []),
        "total_at_risk": len(patterns.get("churn_patterns", [])),
        "high_risk_count": len([p for p in patterns.get("churn_patterns", []) if p.get("risk_level") == "high"]),
        "medium_risk_count": len([p for p in patterns.get("churn_patterns", []) if p.get("risk_level") == "medium"]),
        "detected_at": patterns.get("detected_at")
    }


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

# ============== WEBSOCKET API ENDPOINTS ==============

@api_router.get("/ws/stats")
async def get_websocket_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get WebSocket connection statistics (admin only)"""
    await get_current_user(credentials, db)
    return ws_manager.get_connection_stats()


@api_router.post("/ws/broadcast")
async def broadcast_notification(
    notification: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Broadcast a notification to specified targets (admin only).
    
    Request body:
    - type: Notification type (e.g., "system_alert")
    - message: Notification message
    - target: "all", "admins", or creator_id for specific creator
    - severity: "info", "warning", "error" (for system alerts)
    """
    await get_current_user(credentials, db)
    
    notification_type = notification.get("type", "system_alert")
    message = notification.get("message", "")
    target = notification.get("target", "all")
    data = notification.get("data", {})
    data["message"] = message
    
    try:
        notif_type = NotificationType(notification_type)
    except ValueError:
        notif_type = NotificationType.SYSTEM_ALERT
    
    if target == "all":
        await ws_manager.broadcast_all(notif_type, data)
    elif target == "admins":
        await ws_manager.broadcast_to_admins(notif_type, data)
    else:
        # Assume target is a creator_id
        await ws_manager.broadcast_to_creator(target, notif_type, data)
    
    return {
        "message": "Notification broadcasted",
        "target": target,
        "type": notification_type,
        "connections": ws_manager.get_connection_stats()
    }

# Include the router
app.include_router(api_router)

# ============== WEBSOCKET ENDPOINTS ==============

@app.websocket("/ws/notifications/{user_type}/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_type: str,
    user_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time notifications.
    
    URL: /ws/notifications/{user_type}/{user_id}
    - user_type: "admin" or "creator"
    - user_id: The user's ID
    - token: Authentication token (optional query param)
    
    Messages sent to client:
    {
        "type": "notification_type",
        "data": {...},
        "timestamp": "ISO timestamp"
    }
    """
    # Validate user type
    if user_type not in ["admin", "creator"]:
        await websocket.close(code=4000, reason="Invalid user type")
        return
    
    # Get user name for logging
    user_name = None
    if user_type == "admin":
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "name": 1})
        if user:
            user_name = user.get("name")
    else:
        creator = await db.creators.find_one({"id": user_id}, {"_id": 0, "name": 1})
        if creator:
            user_name = creator.get("name")
    
    await ws_manager.connect(websocket, user_id, user_type, user_name)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_text("pong")
            
            # Handle acknowledgment messages
            elif data.startswith("ack:"):
                # Client acknowledging receipt of notification
                pass
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
