"""
Routes Package - Modular API Route Organization
================================================
This package contains modularized route handlers for the Creators Hive HQ API.

Route Modules:
- auth.py: Authentication routes (Admin & Creator login/register)
- creator.py: Creator-facing endpoints (Pattern Insights, Alerts, Health Score)
- admin.py: Admin dashboard endpoints (Escalation, Lifecycle, Waitlist)
- proposals.py: Project proposal management
- arris.py: ARRIS AI endpoints (Memory, Voice, Activity)
- subscriptions.py: Subscription & Stripe endpoints
- elite.py: Elite tier features (Personas, Reports, Multi-brand)
"""

from fastapi import APIRouter

# Create a router for each module
auth_router = APIRouter(tags=["Authentication"])
creator_router = APIRouter(tags=["Creator"])
admin_router = APIRouter(tags=["Admin"])
proposals_router = APIRouter(tags=["Proposals"])
arris_router = APIRouter(tags=["ARRIS"])
subscriptions_router = APIRouter(tags=["Subscriptions"])
elite_router = APIRouter(tags=["Elite"])
