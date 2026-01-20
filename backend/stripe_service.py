"""
Creators Hive HQ - Stripe Service
Self-Funding Loop - Payment processing and subscription management
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionRequest, 
    CheckoutSessionResponse,
    CheckoutStatusResponse
)

from models_subscription import (
    SUBSCRIPTION_PLANS,
    SubscriptionTier,
    BillingCycle,
    CreatorSubscription,
    PaymentTransaction
)

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe payments and subscriptions"""
    
    def __init__(self, db):
        self.db = db
        self.api_key = os.environ.get("STRIPE_API_KEY")
        if not self.api_key:
            logger.warning("STRIPE_API_KEY not set - Stripe features disabled")
        self.stripe_checkout = None
        
    def _init_checkout(self, webhook_url: str):
        """Initialize Stripe checkout with webhook URL"""
        if not self.api_key:
            raise ValueError("Stripe API key not configured")
        self.stripe_checkout = StripeCheckout(
            api_key=self.api_key,
            webhook_url=webhook_url
        )
        
    async def create_checkout_session(
        self,
        plan_id: str,
        origin_url: str,
        creator_id: str,
        creator_email: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for a subscription plan.
        Amount is determined server-side only (never from frontend).
        """
        # Validate plan exists
        if plan_id not in SUBSCRIPTION_PLANS:
            raise ValueError(f"Invalid plan ID: {plan_id}")
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # Free plan doesn't need checkout
        if plan_id == "free":
            raise ValueError("Free plan doesn't require payment")
        
        # Get price from server-side definition (SECURITY: never from frontend)
        amount = plan["price"]
        
        # Initialize checkout with webhook
        self._init_checkout(webhook_url)
        
        # Build success and cancel URLs from frontend origin
        success_url = f"{origin_url}/creator/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/creator/subscription/cancel"
        
        # Prepare metadata
        metadata = {
            "creator_id": creator_id,
            "creator_email": creator_email,
            "plan_id": plan_id,
            "tier": plan["tier"].value if isinstance(plan["tier"], SubscriptionTier) else plan["tier"],
            "billing_cycle": plan.get("billing_cycle", "one_time"),
            "source": "creators_hive_hq"
        }
        
        # Create checkout request
        checkout_request = CheckoutSessionRequest(
            amount=float(amount),
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        try:
            # Create Stripe session
            session: CheckoutSessionResponse = await self.stripe_checkout.create_checkout_session(checkout_request)
            
            # Create payment transaction record BEFORE redirect
            transaction = PaymentTransaction(
                creator_id=creator_id,
                creator_email=creator_email,
                stripe_session_id=session.session_id,
                amount=amount,
                currency="usd",
                plan_id=plan_id,
                billing_cycle=plan.get("billing_cycle", "one_time"),
                status="pending",
                payment_status="initiated",
                metadata=metadata
            )
            
            tx_doc = transaction.model_dump()
            tx_doc["created_at"] = tx_doc["created_at"].isoformat()
            tx_doc["updated_at"] = tx_doc["updated_at"].isoformat()
            
            await self.db.payment_transactions.insert_one(tx_doc)
            
            logger.info(f"Created checkout session {session.session_id} for creator {creator_id}, plan {plan_id}")
            
            return {
                "checkout_url": session.url,
                "session_id": session.session_id,
                "plan_id": plan_id,
                "amount": amount,
                "currency": "usd"
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
    
    async def get_checkout_status(self, session_id: str, webhook_url: str) -> Dict[str, Any]:
        """Get the status of a checkout session and update transaction"""
        self._init_checkout(webhook_url)
        
        try:
            status: CheckoutStatusResponse = await self.stripe_checkout.get_checkout_status(session_id)
            
            # Get existing transaction
            transaction = await self.db.payment_transactions.find_one(
                {"stripe_session_id": session_id},
                {"_id": 0}
            )
            
            if transaction:
                # Determine new status
                new_status = "pending"
                if status.payment_status == "paid":
                    new_status = "completed"
                elif status.status == "expired":
                    new_status = "failed"
                
                # Update transaction (only if not already completed to prevent duplicates)
                if transaction.get("status") != "completed":
                    await self.db.payment_transactions.update_one(
                        {"stripe_session_id": session_id},
                        {
                            "$set": {
                                "status": new_status,
                                "payment_status": status.payment_status,
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                                "completed_at": datetime.now(timezone.utc).isoformat() if new_status == "completed" else None
                            }
                        }
                    )
                    
                    # If payment successful and not already processed, activate subscription
                    if new_status == "completed" and transaction.get("status") != "completed":
                        await self._activate_subscription(transaction)
            
            return {
                "session_id": session_id,
                "status": status.status,
                "payment_status": status.payment_status,
                "amount": status.amount_total / 100,  # Convert from cents
                "currency": status.currency,
                "metadata": status.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get checkout status: {e}")
            raise
    
    async def handle_webhook(self, body: bytes, signature: str, webhook_url: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        self._init_checkout(webhook_url)
        
        try:
            webhook_response = await self.stripe_checkout.handle_webhook(body, signature)
            
            event_type = webhook_response.event_type
            session_id = webhook_response.session_id
            payment_status = webhook_response.payment_status
            metadata = webhook_response.metadata
            
            logger.info(f"Webhook received: {event_type} for session {session_id}")
            
            # Get transaction
            transaction = await self.db.payment_transactions.find_one(
                {"stripe_session_id": session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("status") != "completed":
                if event_type == "checkout.session.completed" and payment_status == "paid":
                    # Update transaction
                    await self.db.payment_transactions.update_one(
                        {"stripe_session_id": session_id},
                        {
                            "$set": {
                                "status": "completed",
                                "payment_status": "paid",
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                                "completed_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    
                    # Activate subscription
                    await self._activate_subscription(transaction)
                    
                elif event_type == "checkout.session.expired":
                    await self.db.payment_transactions.update_one(
                        {"stripe_session_id": session_id},
                        {
                            "$set": {
                                "status": "failed",
                                "payment_status": "expired",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
            
            return {
                "event_type": event_type,
                "session_id": session_id,
                "payment_status": payment_status,
                "processed": True
            }
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise
    
    async def _activate_subscription(self, transaction: Dict[str, Any]):
        """Activate subscription after successful payment"""
        creator_id = transaction.get("creator_id")
        creator_email = transaction.get("creator_email")
        plan_id = transaction.get("plan_id")
        amount = transaction.get("amount", 0)
        
        if not creator_id or not plan_id:
            logger.error("Missing creator_id or plan_id in transaction")
            return
        
        plan = SUBSCRIPTION_PLANS.get(plan_id, {})
        tier = plan.get("tier", SubscriptionTier.FREE)
        billing_cycle = plan.get("billing_cycle", BillingCycle.MONTHLY)
        
        # Calculate period end
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        if billing_cycle == BillingCycle.ANNUAL or billing_cycle == "annual":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        # Check if subscription exists
        existing_sub = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if existing_sub:
            # Update existing subscription
            await self.db.creator_subscriptions.update_one(
                {"creator_id": creator_id},
                {
                    "$set": {
                        "plan_id": plan_id,
                        "tier": tier.value if isinstance(tier, SubscriptionTier) else tier,
                        "billing_cycle": billing_cycle.value if isinstance(billing_cycle, BillingCycle) else billing_cycle,
                        "status": "active",
                        "current_period_start": now.isoformat(),
                        "current_period_end": period_end.isoformat(),
                        "updated_at": now.isoformat()
                    },
                    "$inc": {
                        "total_paid": amount,
                        "payment_count": 1
                    }
                }
            )
            subscription_id = existing_sub.get("id")
        else:
            # Create new subscription
            subscription = CreatorSubscription(
                creator_id=creator_id,
                creator_email=creator_email,
                plan_id=plan_id,
                tier=tier,
                billing_cycle=billing_cycle,
                status="active",
                current_period_start=now,
                current_period_end=period_end,
                total_paid=amount,
                payment_count=1
            )
            
            sub_doc = subscription.model_dump()
            sub_doc["created_at"] = sub_doc["created_at"].isoformat()
            sub_doc["updated_at"] = sub_doc["updated_at"].isoformat()
            sub_doc["current_period_start"] = sub_doc["current_period_start"].isoformat()
            sub_doc["current_period_end"] = sub_doc["current_period_end"].isoformat()
            sub_doc["tier"] = sub_doc["tier"].value if isinstance(sub_doc["tier"], SubscriptionTier) else sub_doc["tier"]
            sub_doc["billing_cycle"] = sub_doc["billing_cycle"].value if isinstance(sub_doc["billing_cycle"], BillingCycle) else sub_doc["billing_cycle"]
            
            await self.db.creator_subscriptions.insert_one(sub_doc)
            subscription_id = subscription.id
        
        # Update creator's assigned tier
        await self.db.creators.update_one(
            {"id": creator_id},
            {
                "$set": {
                    "assigned_tier": tier.value if isinstance(tier, SubscriptionTier) else tier,
                    "subscription_id": subscription_id
                }
            }
        )
        
        # Create Calculator entry (Self-Funding Loop)
        calculator_entry = {
            "id": f"CALC-SUB-{transaction.get('id', 'unknown')}",
            "calc_id": f"CALC-SUB-{transaction.get('id', 'unknown')}",
            "user_id": creator_id,
            "category": "Income",
            "sub_category": "Subscription",
            "description": f"Subscription payment - {plan.get('name', plan_id)}",
            "revenue": amount,
            "expenses": 0,
            "net_margin": amount,
            "source": "stripe",
            "source_transaction_id": transaction.get("stripe_session_id"),
            "notes": f"Plan: {plan_id}, Billing: {billing_cycle}",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.calculator.insert_one(calculator_entry)
        
        logger.info(f"Activated subscription {subscription_id} for creator {creator_id}, plan {plan_id}")
        logger.info(f"Created Calculator entry {calculator_entry['id']} for revenue ${amount}")
        
        # Return data for webhook event
        return {
            "subscription_id": subscription_id,
            "creator_id": creator_id,
            "plan_id": plan_id,
            "amount": amount,
            "calculator_entry_id": calculator_entry["id"]
        }
    
    async def get_creator_subscription(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get current subscription for a creator"""
        subscription = await self.db.creator_subscriptions.find_one(
            {"creator_id": creator_id, "status": "active"},
            {"_id": 0}
        )
        return subscription
    
    async def get_subscription_features(self, creator_id: str) -> Dict[str, Any]:
        """Get features available for a creator based on their subscription"""
        subscription = await self.get_creator_subscription(creator_id)
        
        if not subscription:
            # Default to free tier
            plan = SUBSCRIPTION_PLANS["free"]
            return {
                "tier": "free",
                "plan_id": "free",
                "features": plan["features"],
                "has_subscription": False
            }
        
        plan_id = subscription.get("plan_id", "free")
        plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
        
        return {
            "tier": subscription.get("tier", "free"),
            "plan_id": plan_id,
            "features": plan["features"],
            "has_subscription": True,
            "current_period_end": subscription.get("current_period_end"),
            "status": subscription.get("status")
        }
    
    async def check_feature_access(self, creator_id: str, feature: str) -> bool:
        """Check if a creator has access to a specific feature"""
        features_data = await self.get_subscription_features(creator_id)
        features = features_data.get("features", {})
        return features.get(feature, False)
    
    async def check_proposal_limit(self, creator_id: str) -> Dict[str, Any]:
        """Check if creator can create more proposals"""
        features_data = await self.get_subscription_features(creator_id)
        limit = features_data.get("features", {}).get("proposal_limit", 3)
        
        # Count existing proposals
        proposal_count = await self.db.proposals.count_documents({"user_id": creator_id})
        
        if limit == -1:  # Unlimited
            return {
                "can_create": True,
                "limit": -1,
                "used": proposal_count,
                "remaining": -1
            }
        
        return {
            "can_create": proposal_count < limit,
            "limit": limit,
            "used": proposal_count,
            "remaining": max(0, limit - proposal_count)
        }
