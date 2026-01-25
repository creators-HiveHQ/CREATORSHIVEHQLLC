"""
Proposals Routes
================
Project proposal management endpoints with ARRIS integration, 
feature gating, webhooks, and email notifications.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging
import random
import uuid

from routes.dependencies import security, get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["Proposals"])


async def get_any_authenticated_user(credentials: HTTPAuthorizationCredentials, db):
    """Get any authenticated user (admin or creator)."""
    from auth import get_current_user, get_current_creator, decode_token
    
    token_data = decode_token(credentials.credentials)
    
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    role = getattr(token_data, 'role', 'admin')
    
    if role == "creator":
        try:
            creator = await get_current_creator(credentials, db)
            return {"user_type": "creator", "user_id": creator["id"], "user": creator}
        except Exception:
            pass
    
    # Try admin
    try:
        admin = await get_current_user(credentials, db)
        if admin:
            return {"user_type": "admin", "user_id": admin.get("user_id", admin.get("id")), "user": admin}
    except Exception:
        pass
    
    raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_admin(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated admin."""
    from auth import get_current_user
    return await get_current_user(credentials, db)


async def get_current_creator_user(credentials: HTTPAuthorizationCredentials, db):
    """Get current authenticated creator."""
    from auth import get_current_creator
    return await get_current_creator(credentials, db)


# ============== PUBLIC/FORM OPTIONS ==============

@router.get("/form-options")
async def get_proposal_form_options():
    """Get options for the project proposal form"""
    from models_creator import PLATFORM_OPTIONS
    from models_proposal import TIMELINE_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS, ARRIS_PROJECT_QUESTIONS
    
    return {
        "platforms": PLATFORM_OPTIONS,
        "timelines": TIMELINE_OPTIONS,
        "priorities": PRIORITY_OPTIONS,
        "statuses": STATUS_OPTIONS,
        "arris_question": random.choice(ARRIS_PROJECT_QUESTIONS)
    }


# ============== PROPOSAL CRUD ==============

@router.get("/stats/summary")
async def get_proposal_stats_summary(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get proposal statistics (admin)"""
    db = get_db()
    await get_current_admin(credentials, db)
    
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
        "by_status": {item["_id"]: item["count"] for item in status_counts if item["_id"]},
        "by_priority": {item["_id"]: item["count"] for item in priority_counts if item["_id"]}
    }


@router.get("")
async def get_proposals(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all proposals with optional filters (admin)"""
    db = get_db()
    await get_current_admin(credentials, db)
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    
    proposals = await db.proposals.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return proposals


@router.post("")
async def create_proposal(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new project proposal (authenticated users - admin or creator)"""
    from models_proposal import ProjectProposal, ProjectProposalCreate, ProjectProposalResponse
    from models_webhook import WebhookEventType
    
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    body = await request.json()
    proposal = ProjectProposalCreate(**body)
    
    # For creators, auto-fill the user_id if not provided
    if auth_user["user_type"] == "creator" and not proposal.user_id:
        proposal.user_id = auth_user["user_id"]
    
    # Check monthly proposal limit for creators
    if auth_user["user_type"] == "creator":
        feature_gating = get_service("feature_gating")
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
    webhook_service = get_service("webhook")
    if webhook_service:
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
    
    return {
        "id": proposal_obj.id,
        "title": proposal_obj.title,
        "status": proposal_obj.status,
        "message": "Proposal created as draft. Submit when ready for review."
    }


@router.get("/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific proposal with ARRIS insights"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Creators can only view their own proposals
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return proposal


@router.patch("/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a proposal (admin review)"""
    from models_webhook import WebhookEventType
    
    db = get_db()
    current_user = await get_current_admin(credentials, db)
    
    body = await request.json()
    update_data = {k: v for k, v in body.items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    new_status = update_data.get("status")
    
    # Handle status changes
    if new_status:
        if new_status == "under_review":
            update_data["reviewed_by"] = current_user.get("id", "admin")
        elif new_status == "approved":
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
        elif new_status == "rejected":
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
    
    webhook_service = get_service("webhook")
    email_service = get_service("email")
    notification_service = get_service("notification")
    
    if new_status == "approved" and update_data.get("assigned_project_id"):
        # WEBHOOK: Emit proposal approved event
        if webhook_service:
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
                    "project_id": update_data["assigned_project_id"],
                    "proposal_id": proposal_id
                },
                source_entity="project",
                source_id=update_data["assigned_project_id"],
                user_id=updated_proposal.get("user_id")
            )
        
        # EMAIL: Send approval notification
        if creator_email and email_service and email_service.is_configured():
            try:
                await email_service.send_proposal_approved_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id,
                    project_id=update_data["assigned_project_id"]
                )
                logger.info(f"Approval email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send approval email: {str(e)}")
        
        # WEBSOCKET: Real-time notification
        if notification_service:
            await notification_service.notify_proposal_approved(
                proposal_id=proposal_id,
                proposal_title=proposal_title,
                project_id=update_data["assigned_project_id"],
                creator_id=updated_proposal.get("user_id")
            )
    
    elif new_status == "rejected":
        # WEBHOOK: Emit proposal rejected event
        if webhook_service:
            await webhook_service.emit(
                event_type=WebhookEventType.PROPOSAL_REJECTED,
                payload={
                    "title": updated_proposal.get("title"),
                    "proposal_id": proposal_id,
                    "rejection_notes": update_data.get("admin_notes", "")
                },
                source_entity="proposal",
                source_id=proposal_id,
                user_id=updated_proposal.get("user_id")
            )
        
        # EMAIL: Send rejection notification
        if creator_email and email_service and email_service.is_configured():
            try:
                await email_service.send_proposal_rejected_notification(
                    creator_email=creator_email,
                    creator_name=creator_name,
                    proposal_title=proposal_title,
                    proposal_id=proposal_id,
                    rejection_reason=update_data.get("admin_notes", "No specific reason provided")
                )
                logger.info(f"Rejection email sent to {creator_email} for proposal {proposal_id}")
            except Exception as e:
                logger.error(f"Failed to send rejection email: {str(e)}")
        
        # WEBSOCKET: Real-time notification
        if notification_service:
            await notification_service.notify_proposal_rejected(
                proposal_id=proposal_id,
                proposal_title=proposal_title,
                creator_id=updated_proposal.get("user_id")
            )
    
    return {"message": "Proposal updated successfully"}


@router.delete("/{proposal_id}")
async def delete_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a proposal (admin only or own draft)"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Creators can only delete their own drafts
    if auth_user["user_type"] == "creator":
        if proposal.get("user_id") != auth_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if proposal.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Can only delete draft proposals")
    
    await db.proposals.delete_one({"id": proposal_id})
    
    return {"success": True, "message": "Proposal deleted"}


# ============== PROPOSAL SUBMISSION WITH ARRIS ==============

@router.post("/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Submit a proposal for review and generate ARRIS insights"""
    from models_webhook import WebhookEventType
    
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Verify ownership for creators
    if auth_user["user_type"] == "creator" and proposal.get("user_id") != auth_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only submit your own proposals")
    
    if proposal.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Only draft proposals can be submitted")
    
    # Get services
    feature_gating = get_service("feature_gating")
    arris_service = get_service("arris")
    webhook_service = get_service("webhook")
    email_service = get_service("email")
    notification_service = get_service("notification")
    
    # Get Memory Palace data for context
    memory_palace_data = None
    if proposal.get("user_id"):
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
    if creator_id and auth_user["user_type"] == "creator" and feature_gating:
        processing_speed = await feature_gating.get_arris_processing_speed(creator_id)
    
    # Generate ARRIS insights with priority processing for Premium/Elite users
    arris_insights_full = {}
    if arris_service:
        arris_insights_full = await arris_service.generate_project_insights(
            proposal, 
            memory_palace_data,
            processing_speed=processing_speed
        )
    
    # Filter insights based on creator's subscription tier
    if creator_id and auth_user["user_type"] == "creator" and feature_gating:
        arris_insights = await feature_gating.filter_arris_insights(creator_id, arris_insights_full)
    else:
        # Admins get full insights
        arris_insights = arris_insights_full
    
    # Store full insights in database (for when user upgrades)
    update_data = {
        "status": "submitted",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "arris_insights_full": arris_insights_full,
        "arris_insights": arris_insights,
        "arris_insights_generated_at": datetime.now(timezone.utc).isoformat(),
        "arris_processing_speed": processing_speed,
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
    if webhook_service:
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
    
    email_sent = False
    if creator_email and email_service and email_service.is_configured():
        try:
            await email_service.send_proposal_submitted_notification(
                creator_email=creator_email,
                creator_name=creator_name,
                proposal_title=proposal.get("title", "Untitled Proposal"),
                proposal_id=proposal_id
            )
            logger.info(f"Submission email sent to {creator_email} for proposal {proposal_id}")
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send submission email: {str(e)}")
    
    # WEBSOCKET: Real-time notifications
    if notification_service:
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
        "email_sent": email_sent
    }


@router.post("/{proposal_id}/regenerate-insights")
async def regenerate_insights(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Regenerate ARRIS insights for a proposal with priority processing for Premium/Elite"""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal = await db.proposals.find_one({"id": proposal_id}, {"_id": 0})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    feature_gating = get_service("feature_gating")
    arris_service = get_service("arris")
    
    # Get processing speed for the user
    processing_speed = "standard"
    if auth_user["user_type"] == "creator" and feature_gating:
        processing_speed = await feature_gating.get_arris_processing_speed(auth_user["user_id"])
    
    # Regenerate insights with priority processing
    arris_insights = {}
    if arris_service:
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
        "id": proposal_id,
        "message": "ARRIS insights regenerated",
        "arris_insights": arris_insights,
        "processing_speed": processing_speed
    }


# ============== PROPOSAL RECOMMENDATIONS ==============

@router.post("/{proposal_id}/generate-recommendations")
async def generate_proposal_recommendations(
    proposal_id: str,
    rejection_reason: Optional[str] = Query(default=None, description="Admin's rejection reason"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Generate AI-powered improvement recommendations for a proposal.
    Can be called by admin after rejection or by creator.
    """
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal_recommendation_service = get_service("proposal_recommendation")
    if not proposal_recommendation_service:
        raise HTTPException(status_code=503, detail="Recommendation service not available")
    
    # Generate recommendations
    result = await proposal_recommendation_service.generate_rejection_recommendations(
        proposal_id=proposal_id,
        rejection_reason=rejection_reason
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Failed to generate recommendations"))
    
    return result


@router.get("/{proposal_id}/recommendations")
async def get_proposal_recommendations(
    proposal_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get existing recommendations for a proposal."""
    db = get_db()
    auth_user = await get_any_authenticated_user(credentials, db)
    
    proposal_recommendation_service = get_service("proposal_recommendation")
    if not proposal_recommendation_service:
        return {
            "proposal_id": proposal_id,
            "recommendations": None,
            "message": "Recommendation service not available"
        }
    
    recommendations = await proposal_recommendation_service.get_recommendations_for_proposal(proposal_id)
    
    if not recommendations:
        return {
            "proposal_id": proposal_id,
            "recommendations": None,
            "message": "No recommendations available for this proposal"
        }
    
    return recommendations
