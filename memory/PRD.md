# Creators Hive HQ - Master Database PRD

## Overview

Creators Hive HQ is a comprehensive database management system designed to power the Pattern Engine and Memory Palace for AI Agent ARRIS. The system implements a Zero-Human Operational Model with full data normalization based on the Master Database Excel schema.

## Architecture

### Core Principles

1. **Schema Map (Sheet 15 Index)**: Absolute source of truth for all data relationships
2. **Self-Funding Loop**: 17_Subscriptions → 06_Calculator revenue routing
3. **No-Assumption Protocol**: All relationships verified against Sheet 15 before implementation
4. **Zero-Human Operational Model**: Fully automated operations via Webhook Automations

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
| Webhooks & Automation | webhook_events, automation_rules | event_id, rule_id |

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
- **AI Insights**: GPT-powered project proposal analysis

### 3. Webhook Automations (Zero-Human Ops)

Event-driven automation system:
- **8 Default Automation Rules** covering all key workflows
- **Event Types**: creator.registered, creator.approved, proposal.submitted, proposal.approved, project.created, task.completed, revenue.recorded, arris.pattern_detected
- **Automated Actions**: log_event, update_arris_memory, create_welcome_task, create_onboarding_project, queue_for_review, create_project_tasks, initialize_project_tracking, check_project_completion, update_financial_patterns, create_insight_notification
- **Admin Dashboard**: View events, manage rules, test webhooks

### 4. Admin Dashboard

Full management interface:
- Master Dashboard with system overview
- Creators management (registration, approval workflow)
- Project Proposals with AI insights
- **Webhooks Admin** - Event monitoring & rule management
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

### Authentication
- `POST /api/auth/login` - Admin login (JWT)
- `POST /api/auth/register` - Admin registration
- `GET /api/auth/me` - Current user info
- `GET /api/auth/verify` - Token verification

### Creator Management
- `POST /api/creators/register` - Public creator registration
- `GET /api/creators` - List creators (admin)
- `PATCH /api/creators/{id}` - Update creator status (approve/reject)

### Project Proposals
- `POST /api/proposals` - Create proposal
- `POST /api/proposals/{id}/submit` - Submit for review (triggers AI insights)
- `GET /api/proposals` - List proposals
- `PATCH /api/proposals/{id}` - Update proposal status

### Webhook Automations
- `GET /api/webhooks/events` - Get webhook event log
- `GET /api/webhooks/events/{id}` - Get specific event
- `GET /api/webhooks/rules` - Get automation rules
- `PATCH /api/webhooks/rules/{id}` - Toggle rule active/inactive
- `GET /api/webhooks/stats` - Webhook statistics
- `POST /api/webhooks/test` - Trigger test webhook

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
- **AI Integration**: OpenAI via Emergent LLM Key

## Data Flow

```
User Action → Webhook Event → Automation Rules → Actions Executed
                    ↓
ARRIS Logs Usage → Pattern Engine Analyzes → Insights Generated
                    ↓
Subscription Created → Calculator Entry → Revenue Tracked
                    ↓
Dashboard Updates → Memory Palace Synthesizes
```

## Zero-Human Operational Status

- ✅ Pattern Engine: Active
- ✅ Self-Funding Loop: Active  
- ✅ Database Normalization: Complete
- ✅ Schema Index: Deployed
- ✅ ARRIS AI System: Operational
- ✅ Webhook Automations: Active (8 rules)
- ✅ Creator Registration: Live (with password auth)
- ✅ Project Proposals with AI Insights: Live
- ✅ Creator Dashboard: Live
- ✅ Creator Proposal Creation: Live

## Completed Features (January 2026)

1. **Full Database Schema** - 37+ collections based on Excel schema
2. **Admin Authentication** - JWT-based secure login for admin dashboard
3. **Creator Registration Workflow** - Public form + admin review panel with password-based auth
4. **Project Proposal System** - With ARRIS AI-generated insights
5. **Webhook Automations** - Event-driven Zero-Human Ops
6. **Creator Dashboard** - Creator-facing portal with:
   - Password-based JWT login for approved creators
   - Overview showing proposal stats & recent activity
   - My Proposals view with detailed ARRIS insights
   - Status timeline tracking (Draft → Submitted → Review → Approved → Complete)
   - Real-time progress tracking
7. **Create New Proposal Flow** - Full proposal submission from Creator Dashboard:
   - 4-step modal flow (Form → Review → ARRIS Analysis → Completion)
   - All proposal fields: title, description, goals, platforms, timeline, priority
   - ARRIS intake question for AI context
   - Real-time AI analysis with loading state
   - Auto-refresh and navigation to new proposal
8. **Stripe Subscription Integration (Self-Funding Loop)** - Full payment processing:
   - 5 Tiers: Free ($0), Starter ($9.99/mo), Pro ($29.99/mo), Premium ($99.99/mo), Elite (Custom)
   - Annual pricing with 17% discount: Starter $99.99/yr, Pro $299.99/yr, Premium $999.99/yr
   - Gated features: ARRIS insights, proposal limits (3/10/25/∞), priority review, API access
   - Elite tier: Custom pricing with "Contact Us" flow, dedicated account manager, SLA guarantee
   - Stripe Checkout integration via emergentintegrations library (test key: sk_test_emergent)
   - Calculator entry auto-creation on payment success (Self-Funding Loop)
   - Webhook events: subscription.created, revenue.recorded
   - Subscription page with 5-column plan comparison, current status banner
   - "Most Popular" badge on Pro plan

## Completed Features (January 2026 - Feature Gating Update)

9. **Feature Gating System** - Complete subscription-based feature control:
   - **FeatureGatingService** (`/app/backend/feature_gating.py`):
     - `can_create_proposal()` - enforces monthly proposal limits by tier
     - `filter_arris_insights()` - filters AI insights based on tier level
     - `get_full_feature_access()` - returns complete feature info for dashboard
     - `get_arris_insight_level()` - returns insight level (summary_only, summary_strengths, full)
   - **Proposal Limits**: Free (1/mo), Starter (3/mo), Pro+ (unlimited)
   - **ARRIS Insight Levels**:
     - Free: Summary + Complexity only (with upgrade prompts for gated features)
     - Starter: Summary + Strengths
     - Pro+: Full insights (strengths, risks, recommendations, milestones)
   - **Dashboard Levels**: Basic (Free/Starter), Advanced (Pro/Premium), Custom (Elite)
   - **Frontend Integration**:
     - Gated insights display with lock icons and upgrade prompts
     - "Unlock Full ARRIS Insights" CTA with "Upgrade Now" button
     - Proposal limit error handling with upgrade URL
   - **Testing**: 19 pytest tests covering all feature gating scenarios (100% pass rate)

10. **Advanced Dashboard for Pro Tier** - Full analytics dashboard for Pro+ users:
    - **Backend Endpoint**: `GET /api/creators/me/advanced-dashboard`
      - Feature-gated: Returns 403 for Free/Starter users with upgrade URL
      - Returns full analytics data for Pro+ users
    - **Performance Metrics**:
      - Approval rate (percentage of approved proposals)
      - Average review time (hours from submitted to reviewed)
      - Completed/In-progress proposal counts
      - Priority queue position (for priority review users)
    - **Data Visualizations**:
      - Monthly submission trends chart (last 6 months)
      - Status breakdown (approved, in_progress, completed, etc.)
      - Complexity distribution (ARRIS-analyzed: Low, Medium, High)
      - ARRIS activity timeline (recent AI interactions)
    - **Priority Review Banner**: Shows queue position for Pro+ users
    - **Frontend Features**:
      - Analytics tab with PRO badge for Free/Starter users
      - Upgrade prompt with feature preview cards
      - Full dashboard view for Pro+ users with all metrics
      - Dynamic tier badge in header (FREE/STARTER/PRO/PREMIUM/ELITE)
      - "Upgrade" vs "Manage Plan" button based on subscription
    - **Testing**: 17 pytest tests covering all advanced dashboard features (100% pass rate)

11. **Faster ARRIS Processing for Premium/Elite Users** - Priority queue processing:
    - **Backend Implementation**:
      - `ArrisPriorityQueue` class with fast_queue (Premium/Elite) and standard_queue (others)
      - `ProcessingStats` class to track processing metrics per priority level
      - `get_arris_processing_speed()` method in feature_gating service
    - **New API Endpoints**:
      - `GET /api/arris/queue-stats` - Returns queue lengths and processing statistics
      - `GET /api/arris/my-processing-speed` - Returns user's processing speed tier
    - **Processing Speed by Tier**:
      - Free/Starter/Pro: `standard` processing (standard_queue)
      - Premium/Elite: `fast` processing (fast_queue - processed first)
    - **ARRIS Insights Enhancements**:
      - `processing_time_seconds` - Actual time taken for AI analysis
      - `priority_processed` - Boolean indicating fast processing was used
      - `processing_speed` - 'standard' or 'fast'
    - **Frontend Features**:
      - "⚡ Fast ARRIS Processing" shown in Premium/Elite plan cards
      - "⚡ Fast Processing" badge in ARRIS insights for Premium users
      - Processing time displayed in insights (e.g., "7.54s")
    - **Testing**: 15 pytest tests covering all processing speed features (100% pass rate)
    - **Bug Fixed**: `filter_arris_insights` now preserves processing metadata fields

## Upcoming Tasks

- **P1**: Faster ARRIS Processing for Premium users
- **P2**: Advanced Analytics Dashboard (Premium tier - deeper analytics beyond Pro)
- **P2**: Elite Tier Features (custom ARRIS workflows, dashboards, brand integrations)
- **P2**: Advanced ARRIS Memory/Learning capabilities
- **P2**: Email notifications for proposal status changes
- **P2**: Admin revenue dashboard with subscription analytics

---

*Built following the No-Assumption Protocol with Sheet 15 Index as the source of truth.*
