# Creators Hive HQ - Master Database PRD

## Overview

Creators Hive HQ is a comprehensive database management system designed to power the Pattern Engine and Memory Palace for AI Agent ARRIS. The system implements a Zero-Human Operational Model with full data normalization based on the Master Database Excel schema.

## Architecture

### Core Principles

1. **Schema Map (Sheet 15 Index)**: Absolute source of truth for all data relationships
2. **Self-Funding Loop**: 17_Subscriptions → 06_Calculator revenue routing
3. **No-Assumption Protocol**: All relationships verified against Sheet 15 before implementation
4. **Zero-Human Operational Model**: Fully automated operations

### Database Collections (37+)

| Category | Sheets | Primary Keys |
|----------|--------|--------------|
| User Management | 01_Users, 02_BrandingKits, 03_CoachKits | user_id, kit_id |
| Operations & Planning | 04_Projects, 05_Tasks | project_id, task_id |
| Financials & Performance | 06_Calculator, 07_Analytics, 17_Subscriptions, 35_Funding_Investment | calc_id, metric_id, subscription_id |
| Customer & Contact | 08_Rolodex, 09_Customers, 10_Affiliates, 11_EmailLog, 18_SupportLog, 22_Client_Contracts, 25_Vendor_Agreements | contact_id, customer_id, affiliate_id |
| AI System (ARRIS) | 19_ARRIS_Usage_Log, 20_ARRIS_Performance, 21_ARRIS_Training_Data | log_id, review_id, data_source_id |
| System & Compliance | 12_Notepad, 13_Integrations, 14_Audit, 15_Index, 16_Lookups, 23_TOS, 24_Privacy, 26_Forms, 27_Intl_Taxes, 31_System_Health | Various |
| Strategic | 28_Product_Roadmaps, 29_Marketing_Campaigns, 34_Dev_Approaches, 36_User_Activity_Log, 37_Internal_Content | Various |

## Key Features

### 1. Self-Funding Loop

All revenue flows through the Calculator (Sheet 06):
- Subscriptions automatically create Calculator entries
- Revenue tracked by source, category, and user
- Net margin calculated automatically
- Never bypass Calculator for money-related operations

### 2. ARRIS Pattern Engine

AI Agent capabilities:
- **Usage Log (19)**: Tracks all queries, response types, and performance
- **Performance (20)**: Quality scores, error counts, human reviews
- **Training Data (21)**: Data sources with compliance status
- **Pattern Analysis**: Temporal analysis over time ranges
- **Memory Palace**: Comprehensive view across all data sources

### 3. Admin Dashboard

Full management interface:
- Master Dashboard with system overview
- Users management with role/tier filtering
- Projects and Tasks tracking
- Calculator (Revenue Hub) with financial summary
- Subscriptions with Self-Funding Loop indicators
- ARRIS Engine with tabbed views
- Pattern Analysis with insights
- Schema Index reference

## API Endpoints

### Core Endpoints
- `GET /api/` - System status
- `GET /api/health` - Health check
- `GET /api/dashboard` - Master dashboard data
- `GET /api/schema` - Schema index (Sheet 15)

### Data Management
- `GET/POST /api/users` - User CRUD
- `GET/POST /api/projects` - Project management
- `GET/POST /api/tasks` - Task management
- `GET/POST /api/calculator` - Revenue entries
- `GET/POST /api/subscriptions` - Subscription management

### ARRIS Pattern Engine
- `GET /api/arris/usage` - Usage logs
- `GET /api/arris/performance` - Performance reviews
- `GET /api/arris/training` - Training data
- `GET /api/patterns/analyze` - Pattern analysis
- `GET /api/patterns/memory-palace` - Memory Palace overview

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Frontend**: React with Tailwind CSS
- **UI Components**: Radix UI / shadcn

## Data Flow

```
User Action → ARRIS Logs Usage → Pattern Engine Analyzes
                    ↓
Subscription Created → Calculator Entry → Revenue Tracked
                    ↓
Dashboard Updates → Memory Palace Synthesizes → Insights Generated
```

## Zero-Human Operational Status

- ✅ Pattern Engine: Active
- ✅ Self-Funding Loop: Active  
- ✅ Database Normalization: Complete
- ✅ Schema Index: Deployed
- ✅ ARRIS AI System: Operational

---

*Built following the No-Assumption Protocol with Sheet 15 Index as the source of truth.*
