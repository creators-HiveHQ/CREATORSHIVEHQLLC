"""
Creators Hive HQ - Database Operations
Implements No-Assumption Protocol with full normalization
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Collection names mapping to Sheet numbers
COLLECTIONS = {
    "01_users": "users",
    "02_branding_kits": "branding_kits",
    "03_coach_kits": "coach_kits",
    "04_projects": "projects",
    "05_tasks": "tasks",
    "06_calculator": "calculator",
    "07_analytics": "analytics",
    "08_rolodex": "rolodex",
    "09_customers": "customers",
    "10_affiliates": "affiliates",
    "11_email_log": "email_log",
    "12_notepad": "notepad",
    "13_integrations": "integrations",
    "14_audit": "audit",
    "15_index": "schema_index",
    "16_lookups": "lookups",
    "17_subscriptions": "subscriptions",
    "18_support_log": "support_log",
    "19_arris_usage_log": "arris_usage_log",
    "20_arris_performance": "arris_performance",
    "21_arris_training_data": "arris_training_data",
    "22_client_contracts": "client_contracts",
    "23_terms_of_service": "terms_of_service",
    "24_privacy_policies": "privacy_policies",
    "25_vendor_agreements": "vendor_agreements",
    "26_forms_submission": "forms_submission",
    "27_intl_taxes": "intl_taxes",
    "28_product_roadmaps": "product_roadmaps",
    "29_marketing_campaigns": "marketing_campaigns",
    "31_system_health": "system_health",
    "34_dev_approaches": "dev_approaches",
    "35_funding_investment": "funding_investment",
    "36_user_activity_log": "user_activity_log",
    "37_internal_content": "internal_content",
    "patterns": "pattern_analysis",
}

# Schema Index (Sheet 15) - Source of Truth
SCHEMA_INDEX = [
    {"sheet_no": 1, "sheet_name": "Users", "category": "User_Management", "primary_key_field": "user_id"},
    {"sheet_no": 2, "sheet_name": "BrandingKits", "category": "User_Management", "primary_key_field": "kit_id"},
    {"sheet_no": 3, "sheet_name": "CoachKits", "category": "User_Management", "primary_key_field": "kit_id"},
    {"sheet_no": 4, "sheet_name": "Projects", "category": "Operations_Planning", "primary_key_field": "project_id"},
    {"sheet_no": 5, "sheet_name": "Tasks", "category": "Operations_Planning", "primary_key_field": "task_id"},
    {"sheet_no": 6, "sheet_name": "Calculator", "category": "Financials_Performance", "primary_key_field": "calc_id"},
    {"sheet_no": 7, "sheet_name": "Analytics", "category": "Financials_Performance", "primary_key_field": "metric_id"},
    {"sheet_no": 8, "sheet_name": "Rolodex", "category": "Customer_Contact", "primary_key_field": "contact_id"},
    {"sheet_no": 9, "sheet_name": "Customers", "category": "Customer_Contact", "primary_key_field": "customer_id"},
    {"sheet_no": 10, "sheet_name": "Affiliates", "category": "Customer_Contact", "primary_key_field": "affiliate_id"},
    {"sheet_no": 11, "sheet_name": "EmailLog", "category": "Customer_Contact", "primary_key_field": "email_id"},
    {"sheet_no": 12, "sheet_name": "Notepad", "category": "System_Compliance", "primary_key_field": "note_id"},
    {"sheet_no": 13, "sheet_name": "Integrations", "category": "System_Compliance", "primary_key_field": "integration_id"},
    {"sheet_no": 14, "sheet_name": "Audit", "category": "System_Compliance", "primary_key_field": "audit_id"},
    {"sheet_no": 15, "sheet_name": "Index", "category": "System_Compliance", "primary_key_field": "sheet_name"},
    {"sheet_no": 16, "sheet_name": "Lookups", "category": "System_Compliance", "primary_key_field": "standard_id"},
    {"sheet_no": 17, "sheet_name": "Subscriptions", "category": "Financials_Performance", "primary_key_field": "subscription_id"},
    {"sheet_no": 18, "sheet_name": "SupportLog", "category": "Customer_Contact", "primary_key_field": "log_id"},
    {"sheet_no": 19, "sheet_name": "ARRIS_Usage_Log", "category": "AI_System", "primary_key_field": "log_id"},
    {"sheet_no": 20, "sheet_name": "ARRIS_Performance", "category": "AI_System", "primary_key_field": "review_id"},
    {"sheet_no": 21, "sheet_name": "ARRIS_Training_Data", "category": "AI_System", "primary_key_field": "data_source_id"},
    {"sheet_no": 22, "sheet_name": "Client_Contracts", "category": "Customer_Contact", "primary_key_field": "contract_id"},
    {"sheet_no": 23, "sheet_name": "Terms_of_Service", "category": "System_Compliance", "primary_key_field": "tos_id"},
    {"sheet_no": 24, "sheet_name": "Privacy_Policies", "category": "System_Compliance", "primary_key_field": "policy_id"},
    {"sheet_no": 25, "sheet_name": "Vendor_Agreements", "category": "Customer_Contact", "primary_key_field": "vendor_id"},
    {"sheet_no": 26, "sheet_name": "Forms_Submission", "category": "System_Compliance", "primary_key_field": "submission_id"},
    {"sheet_no": 27, "sheet_name": "Intl_Taxes", "category": "System_Compliance", "primary_key_field": "compliance_id"},
    {"sheet_no": 28, "sheet_name": "Product_Roadmaps", "category": "Strategic", "primary_key_field": "roadmap_id"},
    {"sheet_no": 29, "sheet_name": "Marketing_Campaigns", "category": "Strategic", "primary_key_field": "campaign_id"},
    {"sheet_no": 31, "sheet_name": "System_Health_API_Status", "category": "System_Compliance", "primary_key_field": "system_id"},
    {"sheet_no": 34, "sheet_name": "Dev_Approaches", "category": "Strategic", "primary_key_field": "approach_id"},
    {"sheet_no": 35, "sheet_name": "Funding_Investment", "category": "Financials_Performance", "primary_key_field": "investment_id"},
    {"sheet_no": 36, "sheet_name": "User_Activity_Log", "category": "System_Compliance", "primary_key_field": "activity_id"},
    {"sheet_no": 37, "sheet_name": "Internal_Content_Library", "category": "System_Compliance", "primary_key_field": "content_id"},
]

# Lookup values from Sheet 16
LOOKUP_DATA = [
    {"standard_id": "TIER", "lookup_type": "T-PLATINUM", "value": "Platinum", "related_field": "01_Users", "description": "Highest tier", "is_active": True},
    {"standard_id": "TIER", "lookup_type": "T-GOLD", "value": "Gold", "related_field": "01_Users", "description": "Mid-tier", "is_active": True},
    {"standard_id": "TIER", "lookup_type": "T-SILVER", "value": "Silver", "related_field": "01_Users", "description": "Basic tier", "is_active": True},
    {"standard_id": "TIER", "lookup_type": "T-FREE", "value": "Free", "related_field": "01_Users", "description": "Free tier", "is_active": True},
    {"standard_id": "ROLE", "lookup_type": "R-CREATOR", "value": "Creator", "related_field": "01_Users", "description": "Content creator", "is_active": True},
    {"standard_id": "ROLE", "lookup_type": "R-COACH", "value": "Coach", "related_field": "01_Users", "description": "Business coach", "is_active": True},
    {"standard_id": "ROLE", "lookup_type": "R-STAFF", "value": "Staff", "related_field": "01_Users", "description": "Staff member", "is_active": True},
    {"standard_id": "ROLE", "lookup_type": "R-ADMIN", "value": "Admin", "related_field": "01_Users", "description": "Administrator", "is_active": True},
    {"standard_id": "STATUS", "lookup_type": "S-ACTIVE", "value": "Active", "related_field": "General", "description": "Active status", "is_active": True},
    {"standard_id": "STATUS", "lookup_type": "S-INACTIVE", "value": "Inactive", "related_field": "General", "description": "Inactive status", "is_active": True},
    {"standard_id": "STATUS", "lookup_type": "S-PENDING", "value": "Pending", "related_field": "General", "description": "Pending status", "is_active": True},
    {"standard_id": "PRIORITY", "lookup_type": "P-CRITICAL", "value": "Critical", "related_field": "04_Projects", "description": "Critical priority", "is_active": True},
    {"standard_id": "PRIORITY", "lookup_type": "P-HIGH", "value": "High", "related_field": "04_Projects", "description": "High priority", "is_active": True},
    {"standard_id": "PRIORITY", "lookup_type": "P-MEDIUM", "value": "Medium", "related_field": "04_Projects", "description": "Medium priority", "is_active": True},
    {"standard_id": "PRIORITY", "lookup_type": "P-LOW", "value": "Low", "related_field": "04_Projects", "description": "Low priority", "is_active": True},
    {"standard_id": "SEVERITY", "lookup_type": "SEV-HIGH", "value": "High", "related_field": "14_Audit", "description": "High severity", "is_active": True},
    {"standard_id": "SEVERITY", "lookup_type": "SEV-MEDIUM", "value": "Medium", "related_field": "14_Audit", "description": "Medium severity", "is_active": True},
    {"standard_id": "SEVERITY", "lookup_type": "SEV-LOW", "value": "Low", "related_field": "14_Audit", "description": "Low severity", "is_active": True},
]

def convert_excel_date(excel_date: float) -> datetime:
    """Convert Excel serial date to datetime"""
    from datetime import timedelta
    # Excel epoch is December 30, 1899
    excel_epoch = datetime(1899, 12, 30, tzinfo=timezone.utc)
    return excel_epoch + timedelta(days=excel_date)

async def create_indexes(db):
    """Create indexes for efficient querying"""
    # User ID index on all collections (universal join key)
    collections_with_user_id = [
        "users", "branding_kits", "coach_kits", "projects", "tasks",
        "calculator", "analytics", "customers", "affiliates", "email_log",
        "notepad", "integrations", "audit", "subscriptions", "arris_usage_log",
        "terms_of_service", "privacy_policies", "forms_submission", "user_activity_log"
    ]
    
    for coll_name in collections_with_user_id:
        await db[coll_name].create_index("user_id")
    
    # Time-based indexes for Pattern Engine
    await db["arris_usage_log"].create_index("timestamp")
    await db["calculator"].create_index("month_year")
    await db["analytics"].create_index("date")
    await db["user_activity_log"].create_index("timestamp")
    
    # Foreign key indexes
    await db["tasks"].create_index("project_id")
    await db["arris_performance"].create_index("log_id")
    await db["client_contracts"].create_index("customer_id")
    await db["subscriptions"].create_index("linked_calc_id")
    
    # Unique indexes
    await db["users"].create_index("email", unique=True, sparse=True)

async def seed_schema_index(db):
    """Seed the schema index (Sheet 15)"""
    collection = db["schema_index"]
    existing = await collection.count_documents({})
    if existing == 0:
        for schema in SCHEMA_INDEX:
            schema["created_at"] = datetime.now(timezone.utc).isoformat()
            schema["updated_at"] = datetime.now(timezone.utc).isoformat()
        await collection.insert_many(SCHEMA_INDEX)

async def seed_lookups(db):
    """Seed lookup values (Sheet 16)"""
    collection = db["lookups"]
    existing = await collection.count_documents({})
    if existing == 0:
        for lookup in LOOKUP_DATA:
            lookup["created_at"] = datetime.now(timezone.utc).isoformat()
            lookup["updated_at"] = datetime.now(timezone.utc).isoformat()
        await collection.insert_many(LOOKUP_DATA)
