"""
Production Webhook Handlers
===========================
Enhanced webhook handling for Stripe subscription lifecycle and SendGrid email events.
Includes signature verification, idempotency, and creator tier updates.
"""

from fastapi import APIRouter, HTTPException, Request, Header
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import logging
import hashlib
import hmac
import os

from routes.dependencies import get_db, get_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


# ============== IDEMPOTENCY HELPER ==============

async def check_event_processed(event_id: str, event_type: str) -> bool:
    """Check if a webhook event has already been processed (idempotency)."""
    db = get_db()
    existing = await db.webhook_events.find_one({"event_id": event_id})
    return existing is not None


async def mark_event_processed(event_id: str, event_type: str, result: Dict[str, Any]):
    """Mark a webhook event as processed."""
    db = get_db()
    await db.webhook_events.insert_one({
        "event_id": event_id,
        "event_type": event_type,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "result": result
    })


# ============== STRIPE WEBHOOK HANDLER ==============

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for subscription lifecycle management.
    
    Handles:
    - checkout.session.completed: New subscription created
    - customer.subscription.updated: Plan change, renewal
    - customer.subscription.deleted: Cancellation
    - invoice.paid: Successful renewal payment
    - invoice.payment_failed: Failed payment
    """
    from models_webhook import WebhookEventType
    
    db = get_db()
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_service = get_service("stripe")
    webhook_service = get_service("webhook")
    referral_service = get_service("referral")
    notification_service = get_service("notification")
    email_service = get_service("email")
    
    try:
        # Handle webhook through stripe service
        result = await stripe_service.handle_webhook(body, signature, webhook_url)
        
        event_type = result.get("event_type")
        session_id = result.get("session_id")
        payment_status = result.get("payment_status")
        
        # Check idempotency
        event_id = f"{event_type}:{session_id}"
        if await check_event_processed(event_id, event_type):
            logger.info(f"Webhook event {event_id} already processed, skipping")
            return {"received": True, "already_processed": True}
        
        # Get transaction details
        transaction = await db.payment_transactions.find_one(
            {"stripe_session_id": session_id},
            {"_id": 0}
        )
        
        # ============== CHECKOUT COMPLETED (NEW SUBSCRIPTION) ==============
        if event_type == "checkout.session.completed" and payment_status == "paid":
            if transaction:
                creator_id = transaction.get("creator_id")
                plan_id = transaction.get("plan_id")
                amount = transaction.get("amount", 0)
                
                # Emit internal webhooks
                if webhook_service:
                    # Subscription created event
                    await webhook_service.emit(
                        event_type=WebhookEventType.SUBSCRIPTION_CREATED,
                        payload={
                            "plan_id": plan_id,
                            "amount": amount,
                            "billing_cycle": transaction.get("billing_cycle")
                        },
                        source_entity="subscription",
                        source_id=session_id,
                        user_id=creator_id
                    )
                    
                    # Revenue recorded event
                    await webhook_service.emit(
                        event_type=WebhookEventType.REVENUE_RECORDED,
                        payload={
                            "amount": amount,
                            "source": "stripe_subscription",
                            "plan_id": plan_id
                        },
                        source_entity="payment",
                        source_id=session_id,
                        user_id=creator_id
                    )
                
                # Process referral conversion
                if referral_service and creator_id:
                    try:
                        conversion_result = await referral_service.convert_referral(
                            referred_creator_id=creator_id,
                            subscription_amount=amount,
                            plan_id=plan_id
                        )
                        if conversion_result.get("converted"):
                            logger.info(f"Referral converted for creator {creator_id}: commission ${conversion_result.get('commission_amount')}")
                    except Exception as e:
                        logger.error(f"Referral conversion error: {e}")
                
                # Send welcome email
                if email_service and email_service.is_configured():
                    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0, "email": 1, "name": 1})
                    if creator:
                        try:
                            await email_service.send_subscription_welcome(
                                creator_email=creator.get("email"),
                                creator_name=creator.get("name", "Creator"),
                                plan_id=plan_id
                            )
                        except Exception as e:
                            logger.error(f"Failed to send welcome email: {e}")
                
                # Real-time notification
                if notification_service:
                    await notification_service.notify_subscription_activated(
                        creator_id=creator_id,
                        plan_id=plan_id
                    )
                
                logger.info(f"Processed checkout.session.completed for creator {creator_id}, plan {plan_id}")
        
        # ============== SUBSCRIPTION UPDATED (PLAN CHANGE) ==============
        elif event_type == "customer.subscription.updated":
            metadata = result.get("metadata", {})
            creator_id = metadata.get("creator_id")
            
            if creator_id:
                # Get new subscription status
                new_status = result.get("subscription_status", "active")
                new_plan = metadata.get("plan_id")
                
                if new_status == "active" and new_plan:
                    # Update creator's tier
                    from models_subscription import SUBSCRIPTION_PLANS
                    plan = SUBSCRIPTION_PLANS.get(new_plan, {})
                    new_tier = plan.get("tier", "free")
                    if hasattr(new_tier, 'value'):
                        new_tier = new_tier.value
                    
                    await db.creators.update_one(
                        {"id": creator_id},
                        {"$set": {"assigned_tier": new_tier}}
                    )
                    
                    await db.creator_subscriptions.update_one(
                        {"creator_id": creator_id},
                        {"$set": {
                            "plan_id": new_plan,
                            "tier": new_tier,
                            "status": "active",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    logger.info(f"Updated subscription for creator {creator_id} to plan {new_plan}")
        
        # ============== SUBSCRIPTION DELETED (CANCELLATION) ==============
        elif event_type == "customer.subscription.deleted":
            metadata = result.get("metadata", {})
            creator_id = metadata.get("creator_id")
            
            if creator_id:
                # Downgrade to free tier
                await db.creators.update_one(
                    {"id": creator_id},
                    {"$set": {"assigned_tier": "free"}}
                )
                
                await db.creator_subscriptions.update_one(
                    {"creator_id": creator_id},
                    {"$set": {
                        "status": "cancelled",
                        "tier": "free",
                        "cancelled_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Emit cancellation event
                if webhook_service:
                    await webhook_service.emit(
                        event_type=WebhookEventType.SUBSCRIPTION_CANCELLED,
                        payload={"creator_id": creator_id, "reason": "subscription_deleted"},
                        source_entity="subscription",
                        source_id=session_id,
                        user_id=creator_id
                    )
                
                # Send cancellation email
                if email_service and email_service.is_configured():
                    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0, "email": 1, "name": 1})
                    if creator:
                        try:
                            await email_service.send_subscription_cancelled(
                                creator_email=creator.get("email"),
                                creator_name=creator.get("name", "Creator")
                            )
                        except Exception as e:
                            logger.error(f"Failed to send cancellation email: {e}")
                
                logger.info(f"Cancelled subscription for creator {creator_id}")
        
        # ============== INVOICE PAID (RENEWAL) ==============
        elif event_type == "invoice.paid":
            metadata = result.get("metadata", {})
            creator_id = metadata.get("creator_id")
            amount = result.get("amount_paid", 0)
            
            if creator_id and amount:
                # Record renewal payment
                await db.creator_subscriptions.update_one(
                    {"creator_id": creator_id},
                    {
                        "$inc": {"total_paid": amount / 100, "payment_count": 1},
                        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                    }
                )
                
                # Emit revenue event
                if webhook_service:
                    await webhook_service.emit(
                        event_type=WebhookEventType.REVENUE_RECORDED,
                        payload={"amount": amount / 100, "source": "stripe_renewal"},
                        source_entity="payment",
                        source_id=session_id,
                        user_id=creator_id
                    )
                
                logger.info(f"Processed renewal payment for creator {creator_id}: ${amount / 100}")
        
        # ============== INVOICE PAYMENT FAILED ==============
        elif event_type == "invoice.payment_failed":
            metadata = result.get("metadata", {})
            creator_id = metadata.get("creator_id")
            
            if creator_id:
                # Log failed payment
                await db.payment_failures.insert_one({
                    "creator_id": creator_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Emit payment failed event
                if webhook_service:
                    await webhook_service.emit(
                        event_type=WebhookEventType.PAYMENT_FAILED,
                        payload={"creator_id": creator_id, "session_id": session_id},
                        source_entity="payment",
                        source_id=session_id,
                        user_id=creator_id
                    )
                
                # Send payment failed email
                if email_service and email_service.is_configured():
                    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0, "email": 1, "name": 1})
                    if creator:
                        try:
                            await email_service.send_payment_failed_notification(
                                creator_email=creator.get("email"),
                                creator_name=creator.get("name", "Creator")
                            )
                        except Exception as e:
                            logger.error(f"Failed to send payment failed email: {e}")
                
                logger.info(f"Logged payment failure for creator {creator_id}")
        
        # Mark event as processed
        await mark_event_processed(event_id, event_type, {"success": True})
        
        return {"received": True, "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============== SENDGRID WEBHOOK HANDLER ==============

@router.post("/sendgrid")
async def sendgrid_webhook(
    request: Request,
    x_twilio_email_event_webhook_signature: Optional[str] = Header(None),
    x_twilio_email_event_webhook_timestamp: Optional[str] = Header(None)
):
    """
    Handle SendGrid webhook events for email tracking.
    
    Handles:
    - delivered: Email successfully delivered
    - open: Email opened
    - click: Link clicked in email
    - bounce: Email bounced
    - dropped: Email dropped
    - spam_report: Marked as spam
    - unsubscribe: User unsubscribed
    """
    db = get_db()
    
    try:
        events = await request.json()
        
        # SendGrid sends array of events
        if not isinstance(events, list):
            events = [events]
        
        processed_count = 0
        
        for event in events:
            event_type = event.get("event")
            email = event.get("email")
            sg_message_id = event.get("sg_message_id", "")
            timestamp = event.get("timestamp")
            
            # Check idempotency
            event_id = f"sendgrid:{sg_message_id}:{event_type}:{timestamp}"
            if await check_event_processed(event_id, f"sendgrid_{event_type}"):
                continue
            
            # Store email event
            email_event = {
                "event_id": event_id,
                "event_type": event_type,
                "email": email,
                "sg_message_id": sg_message_id,
                "timestamp": timestamp,
                "raw_event": event,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.email_events.insert_one(email_event)
            
            # Handle specific events
            if event_type == "bounce":
                # Mark email as bounced
                await db.creators.update_one(
                    {"email": email},
                    {"$set": {"email_status": "bounced", "email_bounced_at": datetime.now(timezone.utc).isoformat()}}
                )
                logger.warning(f"Email bounced for {email}")
                
            elif event_type == "spam_report":
                # Mark as spam reporter
                await db.creators.update_one(
                    {"email": email},
                    {"$set": {"email_status": "spam_reported", "spam_reported_at": datetime.now(timezone.utc).isoformat()}}
                )
                logger.warning(f"Spam report from {email}")
                
            elif event_type == "unsubscribe":
                # Update subscription preferences
                await db.creators.update_one(
                    {"email": email},
                    {"$set": {"email_unsubscribed": True, "unsubscribed_at": datetime.now(timezone.utc).isoformat()}}
                )
                logger.info(f"Unsubscribe from {email}")
            
            # Mark event as processed
            await mark_event_processed(event_id, f"sendgrid_{event_type}", {"success": True})
            processed_count += 1
        
        return {"received": True, "processed": processed_count}
        
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============== INTERNAL WEBHOOK TRIGGER ==============

@router.post("/internal/subscription-lifecycle")
async def internal_subscription_lifecycle(
    request: Request
):
    """
    Internal endpoint for subscription lifecycle events.
    Called by cron jobs or internal services to check/update subscriptions.
    """
    from models_webhook import WebhookEventType
    
    db = get_db()
    webhook_service = get_service("webhook")
    email_service = get_service("email")
    
    try:
        data = await request.json()
        action = data.get("action")
        
        if action == "check_expiring":
            # Find subscriptions expiring in next 7 days
            seven_days = datetime.now(timezone.utc) + timedelta(days=7)
            
            expiring = await db.creator_subscriptions.find({
                "status": "active",
                "current_period_end": {"$lte": seven_days.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            for sub in expiring:
                creator_id = sub.get("creator_id")
                
                # Emit expiring event
                if webhook_service:
                    await webhook_service.emit(
                        event_type=WebhookEventType.SUBSCRIPTION_EXPIRING,
                        payload={
                            "creator_id": creator_id,
                            "expires_at": sub.get("current_period_end"),
                            "plan_id": sub.get("plan_id")
                        },
                        source_entity="subscription",
                        source_id=sub.get("id"),
                        user_id=creator_id
                    )
                
                # Send reminder email
                if email_service and email_service.is_configured():
                    creator = await db.creators.find_one({"id": creator_id}, {"_id": 0, "email": 1, "name": 1})
                    if creator:
                        try:
                            await email_service.send_subscription_expiring_reminder(
                                creator_email=creator.get("email"),
                                creator_name=creator.get("name", "Creator"),
                                expires_at=sub.get("current_period_end")
                            )
                        except Exception as e:
                            logger.error(f"Failed to send expiring reminder: {e}")
            
            return {"checked": len(expiring), "action": "check_expiring"}
        
        elif action == "expire_overdue":
            # Find and expire overdue subscriptions
            now = datetime.now(timezone.utc)
            
            overdue = await db.creator_subscriptions.find({
                "status": "active",
                "current_period_end": {"$lt": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            expired_count = 0
            for sub in overdue:
                creator_id = sub.get("creator_id")
                
                # Downgrade to free
                await db.creators.update_one(
                    {"id": creator_id},
                    {"$set": {"assigned_tier": "free"}}
                )
                
                await db.creator_subscriptions.update_one(
                    {"creator_id": creator_id},
                    {"$set": {
                        "status": "expired",
                        "tier": "free",
                        "expired_at": now.isoformat(),
                        "updated_at": now.isoformat()
                    }}
                )
                
                expired_count += 1
                logger.info(f"Expired subscription for creator {creator_id}")
            
            return {"expired": expired_count, "action": "expire_overdue"}
        
        return {"error": "Unknown action"}
        
    except Exception as e:
        logger.error(f"Internal webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
