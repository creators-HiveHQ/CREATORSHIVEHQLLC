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

from database import create_indexes, seed_schema_index, seed_lookups, SCHEMA_INDEX
from seed_data import seed_all_data

# Import authentication
from auth import (
    AdminUserCreate, AdminUserLogin, Token,
    get_current_user, create_admin_user, login_user,
    seed_default_admin, security
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
