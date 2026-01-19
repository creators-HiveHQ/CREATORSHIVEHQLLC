"""
Creators Hive HQ - Seed Data from Master Database Excel
Sample data as extracted from the uploaded file
"""

from datetime import datetime, timezone, timedelta
import uuid

def get_date_from_excel(excel_date: float) -> str:
    """Convert Excel serial date to ISO string"""
    excel_epoch = datetime(1899, 12, 30, tzinfo=timezone.utc)
    dt = excel_epoch + timedelta(days=excel_date)
    return dt.isoformat()

# Sample Users (01_Users)
USERS = [
    {"id": "U-1001", "user_id": "U-1001", "name": "Alex Smith", "email": "alex.smith@example.com", "role": "Creator", "business_type": "Video Production", "tier": "Platinum", "account_status": "Active"},
    {"id": "U-1002", "user_id": "U-1002", "name": "Blake Jensen", "email": "blake.jensen@example.com", "role": "Coach", "business_type": "E-Commerce", "tier": "Gold", "account_status": "Active"},
    {"id": "U-1003", "user_id": "U-1003", "name": "Carla Diaz", "email": "carla.diaz@example.com", "role": "Staff", "business_type": "Social Media", "tier": "Silver", "account_status": "Inactive"},
    {"id": "U-1004", "user_id": "U-1004", "name": "Derek Ng", "email": "derek.ng@example.com", "role": "Creator", "business_type": "App Development", "tier": "Gold", "account_status": "Active"},
    {"id": "U-1005", "user_id": "U-1005", "name": "Eva Chen", "email": "eva.chen@example.com", "role": "Coach", "business_type": "Consulting", "tier": "Silver", "account_status": "Active"},
    {"id": "U-1006", "user_id": "U-1006", "name": "Frank White", "email": "frank.white@example.com", "role": "Staff", "business_type": "Marketing", "tier": "Free", "account_status": "Active"},
]

# Branding Kits (02_BrandingKits)
BRANDING_KITS = [
    {"id": "BK-001", "kit_id": "BK-001", "user_id": "U-1001", "logo_url": "https://example.com/logo1.png", "primary_color": "#007bff", "secondary_color": "#6c757d", "font_family": "Roboto", "default_template": "Video_Overlay"},
    {"id": "BK-002", "kit_id": "BK-002", "user_id": "U-1002", "logo_url": "https://example.com/logo2.png", "primary_color": "#28a745", "secondary_color": "#e9ecef", "font_family": "Montserrat", "default_template": "Ebook_Cover"},
    {"id": "BK-003", "kit_id": "BK-003", "user_id": "U-1003", "logo_url": "https://example.com/logo3.png", "primary_color": "#ffc107", "secondary_color": "#343a40", "font_family": "Open_Sans", "default_template": "Presentation_Deck"},
]

# Coach Kits (03_CoachKits)
COACH_KITS = [
    {"id": "CK-001", "kit_id": "CK-001", "user_id": "U-1002", "template_name": "Lead_Generation_Funnel", "enabled_modules": "Sales_CRM_Email", "target_niche": "Digital_Coaching", "access_level": "Admin", "is_premium": True},
    {"id": "CK-002", "kit_id": "CK-002", "user_id": "U-1005", "template_name": "Business_Starter_Pack", "enabled_modules": "Planning_Finance", "target_niche": "Small_Business", "access_level": "User", "is_premium": False},
    {"id": "CK-003", "kit_id": "CK-003", "user_id": "U-1001", "template_name": "Video_Production_Pipeline", "enabled_modules": "Production_Marketing", "target_niche": "YouTube_Creators", "access_level": "User", "is_premium": True},
]

# Projects (04_Projects)
PROJECTS = [
    {"id": "P-2001", "project_id": "P-2001", "title": "Ebook_Launch_Campaign", "platform": "ConvertKit", "status": "In_Progress", "user_id": "U-1002", "priority_level": "High"},
    {"id": "P-2002", "project_id": "P-2002", "title": "Q4_Video_Series", "platform": "YouTube", "status": "Completed", "user_id": "U-1001", "priority_level": "Medium"},
    {"id": "P-2003", "project_id": "P-2003", "title": "New_App_Feature_Development", "platform": "AppSheet", "status": "Planning", "user_id": "U-1004", "priority_level": "Critical"},
    {"id": "P-2004", "project_id": "P-2004", "title": "Coaching_Program_V2", "platform": "Teachable", "status": "In_Progress", "user_id": "U-1005", "priority_level": "High"},
]

# Tasks (05_Tasks)
TASKS = [
    {"id": "T-3001", "task_id": "T-3001", "project_id": "P-2001", "description": "Draft_Ebook_Chapter_3", "completion_status": 0, "assigned_to_user_id": "U-1002", "estimated_hours": 8.0},
    {"id": "T-3002", "task_id": "T-3002", "project_id": "P-2002", "description": "Final_Video_SEO_Optimization", "completion_status": 1, "assigned_to_user_id": "U-1001", "estimated_hours": 2.0},
    {"id": "T-3003", "task_id": "T-3003", "project_id": "P-2003", "description": "Define_database_schema", "completion_status": 0, "assigned_to_user_id": "U-1004", "estimated_hours": 4.0},
    {"id": "T-3004", "task_id": "T-3004", "project_id": "P-2004", "description": "Create_Module_Outline", "completion_status": 0, "assigned_to_user_id": "U-1005", "estimated_hours": 3.0},
]

# Calculator / Revenue (06_Calculator)
CALCULATOR = [
    {"id": "C-4001", "calc_id": "C-4001", "user_id": "U-1001", "month_year": "2025-11", "revenue": 5200.0, "expenses": 1100.0, "net_margin": 4100.0, "category": "Income", "source": "YouTube Ads"},
    {"id": "C-4002", "calc_id": "C-4002", "user_id": "U-1002", "month_year": "2025-11", "revenue": 8500.0, "expenses": 2500.0, "net_margin": 6000.0, "category": "Income", "source": "Ebook Sales"},
    {"id": "C-4003", "calc_id": "C-4003", "user_id": "U-1001", "month_year": "2025-11", "revenue": 0.0, "expenses": 300.0, "net_margin": -300.0, "category": "Expense", "source": "Software Subscriptions"},
    {"id": "C-4004", "calc_id": "C-4004", "user_id": "U-1004", "month_year": "2025-11", "revenue": 1200.0, "expenses": 50.0, "net_margin": 1150.0, "category": "Income", "source": "App Revenue"},
    {"id": "C-4005", "calc_id": "C-4005", "user_id": "U-1005", "month_year": "2025-11", "revenue": 3000.0, "expenses": 200.0, "net_margin": 2800.0, "category": "Income", "source": "Coaching Sessions"},
]

# Analytics (07_Analytics)
ANALYTICS = [
    {"id": "A-5001", "metric_id": "A-5001", "user_id": "U-1001", "platform_views": 55000, "revenue": 1200.0, "engagement_score": 7.8, "platform": "YouTube", "conversion_rate": 0.025},
    {"id": "A-5002", "metric_id": "A-5002", "user_id": "U-1002", "platform_views": 12000, "revenue": 800.0, "engagement_score": 9.1, "platform": "Instagram", "conversion_rate": 0.041},
    {"id": "A-5003", "metric_id": "A-5003", "user_id": "U-1004", "platform_views": 2500, "revenue": 50.0, "engagement_score": 6.5, "platform": "Website", "conversion_rate": 0.018},
]

# Subscriptions (17_Subscriptions) - Links to Calculator for Self-Funding Loop
SUBSCRIPTIONS = [
    {"id": "SUB-1301", "subscription_id": "SUB-1301", "user_id": "U-1001", "plan_name": "Pro_Video_Plan", "tier": "Platinum", "monthly_cost": 99.99, "payment_status": "Active", "linked_calc_id": "C-4001"},
    {"id": "SUB-1302", "subscription_id": "SUB-1302", "user_id": "U-1002", "plan_name": "Coach_Sell", "tier": "Gold", "monthly_cost": 49.99, "payment_status": "Active", "linked_calc_id": "C-4002"},
    {"id": "SUB-1303", "subscription_id": "SUB-1303", "user_id": "U-1004", "plan_name": "App_Starter_Tier", "tier": "Free", "monthly_cost": 0.0, "payment_status": "Active", "linked_calc_id": None},
    {"id": "SUB-1304", "subscription_id": "SUB-1304", "user_id": "U-1005", "plan_name": "Coach_Basic", "tier": "Silver", "monthly_cost": 29.99, "payment_status": "Active", "linked_calc_id": "C-4005"},
]

# Rolodex (08_Rolodex)
ROLODEX = [
    {"id": "R-6001", "contact_id": "R-6001", "contact_name": "Jane Doe", "email": "jane.doe@mediaco.com", "phone": "(555) 123-4567", "notes": "Potential Podcast Guest", "company": "Media Co.", "relationship_type": "Partner"},
    {"id": "R-6002", "contact_id": "R-6002", "contact_name": "John Smith", "email": "john.smith@startup.com", "phone": "(555) 987-6543", "notes": "Lead for coaching services", "company": "Startup LLC", "relationship_type": "Prospect"},
    {"id": "R-6003", "contact_id": "R-6003", "contact_name": "Acme Printing", "email": "contact@acme.com", "phone": "(555) 111-2222", "notes": "Vendor contact", "company": "Acme Inc.", "relationship_type": "Service_Provider"},
]

# Customers (09_Customers)
CUSTOMERS = [
    {"id": "CUS-7001", "customer_id": "CUS-7001", "user_id": "U-1002", "name": "Mike Johnson", "email": "mike.johnson@email.com", "purchase_history": "Course_A, Ebook_B", "status": "Active", "total_spend": 599.0},
    {"id": "CUS-7002", "customer_id": "CUS-7002", "user_id": "U-1001", "name": "Lisa Ray", "email": "lisa.ray@email.com", "purchase_history": "Premium_Templates", "status": "Active", "total_spend": 49.0},
    {"id": "CUS-7003", "customer_id": "CUS-7003", "user_id": "U-1005", "name": "Kevin Lee", "email": "kevin.lee@email.com", "purchase_history": "1-Hour Consultation", "status": "Lapsed", "total_spend": 150.0},
]

# Affiliates (10_Affiliates)
AFFILIATES = [
    {"id": "AFF-8001", "affiliate_id": "AFF-8001", "user_id": "U-1006", "program_name": "HiveHQ_Referral_Tier_1", "commission_rate": 0.15, "earnings": 450.0, "payout_status": "Pending", "referral_url": "https://hivehq.com/ref/u1006"},
    {"id": "AFF-8002", "affiliate_id": "AFF-8002", "user_id": "U-1002", "program_name": "Partner_Network_Basic", "commission_rate": 0.10, "earnings": 1200.0, "payout_status": "Paid", "referral_url": "https://hivehq.com/ref/u1002"},
    {"id": "AFF-8003", "affiliate_id": "AFF-8003", "user_id": "U-1001", "program_name": "HiveHQ_Referral_Tier_2", "commission_rate": 0.20, "earnings": 150.0, "payout_status": "Pending", "referral_url": "https://hivehq.com/ref/u1001"},
]

# ARRIS Usage Log (19_ARRIS_Usage_Log)
ARRIS_USAGE = [
    {"id": "ARRIS-2001", "log_id": "ARRIS-2001", "user_id": "U-1002", "user_query_snippet": "Draft marketing email", "response_type": "Content_Gen", "response_id": "E-9007", "time_taken_s": 2.5, "linked_project": "P-2001", "query_category": "Content", "success": True},
    {"id": "ARRIS-2002", "log_id": "ARRIS-2002", "user_id": "U-1005", "user_query_snippet": "Summarize Q4 revenue", "response_type": "Data_Analysis", "response_id": "C-4007", "time_taken_s": 1.1, "linked_project": "P-2004", "query_category": "Analytics", "success": True},
    {"id": "ARRIS-2003", "log_id": "ARRIS-2003", "user_id": "U-1001", "user_query_snippet": "Find top 3 affiliates", "response_type": "Search_Lookup", "response_id": "AFF-8002", "time_taken_s": 0.8, "linked_project": None, "query_category": "Search", "success": True},
    {"id": "ARRIS-2004", "log_id": "ARRIS-2004", "user_id": "U-1004", "user_query_snippet": "Generate app feature list", "response_type": "Content_Gen", "response_id": "P-2003-FEAT", "time_taken_s": 3.2, "linked_project": "P-2003", "query_category": "Content", "success": True},
]

# ARRIS Performance (20_ARRIS_Performance)
ARRIS_PERFORMANCE = [
    {"id": "AR-R-001", "review_id": "AR-R-001", "log_id": "ARRIS-2001", "quality_score": 9.5, "error_count": 0, "human_reviewer_id": "U-1003", "feedback_tags": "Excellent, Tone", "final_verdict": "Approved"},
    {"id": "AR-R-002", "review_id": "AR-R-002", "log_id": "ARRIS-2002", "quality_score": 8.0, "error_count": 1, "human_reviewer_id": "U-1006", "feedback_tags": "Minor_Data_Error", "final_verdict": "Needs_Correction"},
    {"id": "AR-R-003", "review_id": "AR-R-003", "log_id": "ARRIS-2003", "quality_score": 10.0, "error_count": 0, "human_reviewer_id": "U-1003", "feedback_tags": "Perfect, Fast", "final_verdict": "Approved"},
]

# ARRIS Training Data (21_ARRIS_Training_Data)
ARRIS_TRAINING = [
    {"id": "DS-3001", "data_source_id": "DS-3001", "source_type": "Internal_Docs", "source_url": "https://drive.google.com/doc1", "content_summary": "Platform TOS v1.2", "version": 1.2, "compliance_status": "Approved", "reviewer_id": "U-1003"},
    {"id": "DS-3002", "data_source_id": "DS-3002", "source_type": "External_Article", "source_url": "https://linkedin.com/article1", "content_summary": "Top 5 Marketing Funnels", "version": 1.0, "compliance_status": "Approved", "reviewer_id": "U-1006"},
    {"id": "DS-3003", "data_source_id": "DS-3003", "source_type": "Customer_Feedback", "source_url": "#slack-channel", "content_summary": "Ebook Launch Feedback", "version": 1.0, "compliance_status": "Pending_Review", "reviewer_id": "U-1003"},
]

# Integrations (13_Integrations)
INTEGRATIONS = [
    {"id": "I-1101", "integration_id": "I-1101", "connected_platform": "Mailchimp", "type": "Email_Marketing", "user_id": "U-1002", "connection_status": "Active", "api_key_status": "Valid", "scope_of_access": "Send_Receive_Lists"},
    {"id": "I-1102", "integration_id": "I-1102", "connected_platform": "Stripe", "type": "Payment_Gateway", "user_id": "U-1005", "connection_status": "Active", "api_key_status": "Valid", "scope_of_access": "Read_Transactions"},
    {"id": "I-1103", "integration_id": "I-1103", "connected_platform": "Google_Analytics", "type": "Analytics", "user_id": "U-1001", "connection_status": "Active", "api_key_status": "Valid", "scope_of_access": "Read_Data"},
]

# Dev Approaches (34_Dev_Approaches)
DEV_APPROACHES = [
    {"id": "DEV-001", "approach_id": "DEV-001", "approach_name": "Agile", "key_characteristic": "Iterative_Sprints", "focus_goal": "Customer_Value", "speed_flexibility": "High_Adaptable", "risk_level": "Medium"},
    {"id": "DEV-002", "approach_id": "DEV-002", "approach_name": "Waterfall", "key_characteristic": "Sequential_Phases", "focus_goal": "Documentation", "speed_flexibility": "Low_Rigid", "risk_level": "Medium"},
    {"id": "DEV-003", "approach_id": "DEV-003", "approach_name": "Lean_Startup", "key_characteristic": "Build_Measure_Learn", "focus_goal": "Validation_Efficiency", "speed_flexibility": "Very_High", "risk_level": "Low"},
    {"id": "DEV-004", "approach_id": "DEV-004", "approach_name": "Stage-Gate", "key_characteristic": "Decision_Checkpoints", "focus_goal": "Risk_Mitigation", "speed_flexibility": "Medium_Controlled", "risk_level": "Low"},
]

# Marketing Campaigns (29_Marketing_Campaigns)
MARKETING_CAMPAIGNS = [
    {"id": "MC-7001", "campaign_id": "MC-7001", "campaign_name": "Ebook_Launch", "channel": "Email_Social", "goal": "New_Signups", "budget": 5000.0, "status": "In_Progress"},
    {"id": "MC-7002", "campaign_id": "MC-7002", "campaign_name": "Q4_Video_Promo", "channel": "YouTube_Paid_Ads", "goal": "Views_Leads", "budget": 1500.0, "status": "Active"},
    {"id": "MC-7003", "campaign_id": "MC-7003", "campaign_name": "Founders_Stories", "channel": "Instagram_Blog", "goal": "Brand_Buzz", "budget": 500.0, "status": "Planning"},
]

async def seed_all_data(db):
    """Seed all sample data from Master Database"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Helper to add timestamps
    def add_timestamps(items):
        for item in items:
            item["created_at"] = now
            item["updated_at"] = now
        return items
    
    # Seed each collection
    collections_data = [
        ("users", USERS),
        ("branding_kits", BRANDING_KITS),
        ("coach_kits", COACH_KITS),
        ("projects", PROJECTS),
        ("tasks", TASKS),
        ("calculator", CALCULATOR),
        ("analytics", ANALYTICS),
        ("subscriptions", SUBSCRIPTIONS),
        ("rolodex", ROLODEX),
        ("customers", CUSTOMERS),
        ("affiliates", AFFILIATES),
        ("arris_usage_log", ARRIS_USAGE),
        ("arris_performance", ARRIS_PERFORMANCE),
        ("arris_training_data", ARRIS_TRAINING),
        ("integrations", INTEGRATIONS),
        ("dev_approaches", DEV_APPROACHES),
        ("marketing_campaigns", MARKETING_CAMPAIGNS),
    ]
    
    seeded = {}
    for coll_name, data in collections_data:
        existing = await db[coll_name].count_documents({})
        if existing == 0:
            await db[coll_name].insert_many(add_timestamps(data.copy()))
            seeded[coll_name] = len(data)
    
    return seeded
