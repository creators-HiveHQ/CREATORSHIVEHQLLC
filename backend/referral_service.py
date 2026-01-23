"""
Referral Service for Creators Hive HQ
Phase 4 Module D - Task D4: Referral System

Implements:
- Referral code generation and management
- Referral tracking and attribution
- Commission calculation integrated with Calculator service
- Multi-tier referral rewards
- Referral analytics and leaderboards
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import hashlib
import secrets
import string

logger = logging.getLogger(__name__)


class ReferralStatus(str, Enum):
    PENDING = "pending"  # Referred user registered but not yet qualified
    QUALIFIED = "qualified"  # Referred user met qualification criteria
    CONVERTED = "converted"  # Referred user subscribed (commission earned)
    EXPIRED = "expired"  # Referral window expired
    INVALID = "invalid"  # Referral invalidated (fraud, etc.)


class CommissionStatus(str, Enum):
    PENDING = "pending"  # Awaiting payout
    APPROVED = "approved"  # Approved for payout
    PAID = "paid"  # Commission paid out
    CANCELLED = "cancelled"  # Commission cancelled


class ReferralTier(str, Enum):
    BRONZE = "bronze"  # 0-4 successful referrals
    SILVER = "silver"  # 5-14 successful referrals
    GOLD = "gold"  # 15-29 successful referrals
    PLATINUM = "platinum"  # 30+ successful referrals


# Tier-based commission rates (percentage of first payment)
COMMISSION_RATES = {
    ReferralTier.BRONZE: 0.10,  # 10%
    ReferralTier.SILVER: 0.15,  # 15%
    ReferralTier.GOLD: 0.20,  # 20%
    ReferralTier.PLATINUM: 0.25,  # 25%
}

# Tier thresholds (minimum successful referrals)
TIER_THRESHOLDS = {
    ReferralTier.BRONZE: 0,
    ReferralTier.SILVER: 5,
    ReferralTier.GOLD: 15,
    ReferralTier.PLATINUM: 30,
}

# Bonus rewards for milestone achievements
MILESTONE_BONUSES = {
    5: {"bonus": 25.00, "title": "First Five", "description": "Earned for your first 5 successful referrals"},
    10: {"bonus": 50.00, "title": "Double Digits", "description": "Reached 10 successful referrals"},
    25: {"bonus": 100.00, "title": "Quarter Century", "description": "Achieved 25 successful referrals"},
    50: {"bonus": 250.00, "title": "Half Century", "description": "Impressive! 50 successful referrals"},
    100: {"bonus": 500.00, "title": "Centurion", "description": "Legendary status with 100 referrals"},
}

# Referral qualification criteria
QUALIFICATION_CRITERIA = {
    "min_days_active": 7,  # Days since registration
    "min_proposals": 1,  # Minimum proposals created
    "require_onboarding_complete": True,  # Must complete onboarding
}


class ReferralService:
    """
    Comprehensive Referral System integrated with Calculator Service.
    Handles referral tracking, commission calculation, and payouts.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ============== REFERRAL CODE MANAGEMENT ==============

    async def generate_referral_code(self, creator_id: str) -> Dict[str, Any]:
        """
        Generate a unique referral code for a creator.
        Code format: HIVE-{creator_short_id}-{random_suffix}
        """
        # Check if creator already has a code
        existing = await self.db.referral_codes.find_one(
            {"creator_id": creator_id, "is_active": True},
            {"_id": 0}
        )
        if existing:
            return {
                "code": existing["code"],
                "created_at": existing["created_at"],
                "referral_url": self._build_referral_url(existing["code"]),
                "is_new": False
            }

        # Generate unique code
        short_id = creator_id[-6:].upper()
        suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        code = f"HIVE-{short_id}-{suffix}"

        # Ensure uniqueness
        while await self.db.referral_codes.find_one({"code": code}):
            suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            code = f"HIVE-{short_id}-{suffix}"

        now = datetime.now(timezone.utc)
        referral_code_doc = {
            "code": code,
            "creator_id": creator_id,
            "is_active": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "total_clicks": 0,
            "total_registrations": 0,
            "total_conversions": 0
        }

        await self.db.referral_codes.insert_one(referral_code_doc)

        # Log the activity
        await self._log_referral_activity(
            creator_id=creator_id,
            action="code_generated",
            details={"code": code}
        )

        return {
            "code": code,
            "created_at": now.isoformat(),
            "referral_url": self._build_referral_url(code),
            "is_new": True
        }

    async def get_referral_code(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get creator's active referral code."""
        code_doc = await self.db.referral_codes.find_one(
            {"creator_id": creator_id, "is_active": True},
            {"_id": 0}
        )
        if not code_doc:
            return None

        return {
            **code_doc,
            "referral_url": self._build_referral_url(code_doc["code"])
        }

    async def validate_referral_code(self, code: str) -> Dict[str, Any]:
        """Validate a referral code and return referrer info."""
        code_doc = await self.db.referral_codes.find_one(
            {"code": code.upper(), "is_active": True},
            {"_id": 0}
        )

        if not code_doc:
            return {"valid": False, "error": "Invalid or inactive referral code"}

        # Get referrer info
        referrer = await self.db.creators.find_one(
            {"id": code_doc["creator_id"]},
            {"_id": 0, "id": 1, "name": 1}
        )

        return {
            "valid": True,
            "code": code_doc["code"],
            "referrer_id": code_doc["creator_id"],
            "referrer_name": referrer.get("name", "A Creator") if referrer else "A Creator"
        }

    def _build_referral_url(self, code: str) -> str:
        """Build the full referral URL."""
        # This would use the actual frontend URL in production
        return f"/creator/register?ref={code}"

    # ============== REFERRAL TRACKING ==============

    async def track_referral_click(self, code: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track when someone clicks a referral link."""
        code_doc = await self.db.referral_codes.find_one({"code": code.upper()})
        if not code_doc:
            return {"tracked": False, "error": "Invalid code"}

        now = datetime.now(timezone.utc)

        # Update click count
        await self.db.referral_codes.update_one(
            {"code": code.upper()},
            {
                "$inc": {"total_clicks": 1},
                "$set": {"updated_at": now.isoformat()}
            }
        )

        # Log click event
        click_event = {
            "code": code.upper(),
            "referrer_id": code_doc["creator_id"],
            "event_type": "click",
            "timestamp": now.isoformat(),
            "metadata": metadata or {}
        }
        await self.db.referral_events.insert_one(click_event)

        return {"tracked": True}

    async def create_referral(
        self,
        referral_code: str,
        referred_creator_id: str,
        referred_email: str
    ) -> Dict[str, Any]:
        """
        Create a referral record when a new creator registers with a referral code.
        """
        # Validate the code
        validation = await self.validate_referral_code(referral_code)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        referrer_id = validation["referrer_id"]

        # Prevent self-referral
        if referrer_id == referred_creator_id:
            return {"success": False, "error": "Cannot refer yourself"}

        # Check for existing referral
        existing = await self.db.referrals.find_one({
            "referred_creator_id": referred_creator_id
        })
        if existing:
            return {"success": False, "error": "Creator already has a referrer"}

        now = datetime.now(timezone.utc)
        referral_id = f"REF-{secrets.token_hex(6).upper()}"

        referral_doc = {
            "id": referral_id,
            "referrer_id": referrer_id,
            "referred_creator_id": referred_creator_id,
            "referred_email": referred_email,
            "referral_code": referral_code.upper(),
            "status": ReferralStatus.PENDING.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "qualified_at": None,
            "converted_at": None,
            "conversion_value": 0.0,
            "commission_earned": 0.0,
            "commission_status": None,
            "expires_at": (now + timedelta(days=30)).isoformat()  # 30-day attribution window
        }

        await self.db.referrals.insert_one(referral_doc)

        # Update referral code stats
        await self.db.referral_codes.update_one(
            {"code": referral_code.upper()},
            {
                "$inc": {"total_registrations": 1},
                "$set": {"updated_at": now.isoformat()}
            }
        )

        # Log activity
        await self._log_referral_activity(
            creator_id=referrer_id,
            action="new_referral",
            details={
                "referral_id": referral_id,
                "referred_id": referred_creator_id
            }
        )

        return {
            "success": True,
            "referral_id": referral_id,
            "referrer_id": referrer_id,
            "message": "Referral tracked successfully"
        }

    async def check_and_qualify_referral(self, referred_creator_id: str) -> Dict[str, Any]:
        """
        Check if a referred creator meets qualification criteria.
        Called periodically or on certain events (onboarding complete, first proposal, etc.)
        """
        referral = await self.db.referrals.find_one(
            {"referred_creator_id": referred_creator_id, "status": ReferralStatus.PENDING.value},
            {"_id": 0}
        )

        if not referral:
            return {"qualified": False, "reason": "No pending referral found"}

        # Check expiration
        if referral.get("expires_at"):
            expires_at = datetime.fromisoformat(referral["expires_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expires_at:
                await self.db.referrals.update_one(
                    {"id": referral["id"]},
                    {"$set": {"status": ReferralStatus.EXPIRED.value}}
                )
                return {"qualified": False, "reason": "Referral expired"}

        # Get referred creator details
        creator = await self.db.creators.find_one(
            {"id": referred_creator_id},
            {"_id": 0}
        )

        if not creator:
            return {"qualified": False, "reason": "Creator not found"}

        # Check criteria
        criteria_met = {
            "days_active": False,
            "proposals_created": False,
            "onboarding_complete": False
        }

        # Days active check
        created_at = creator.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            days_active = (datetime.now(timezone.utc) - created_at).days
            criteria_met["days_active"] = days_active >= QUALIFICATION_CRITERIA["min_days_active"]

        # Proposals check
        proposal_count = await self.db.project_proposals.count_documents(
            {"creator_id": referred_creator_id}
        )
        criteria_met["proposals_created"] = proposal_count >= QUALIFICATION_CRITERIA["min_proposals"]

        # Onboarding check
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": referred_creator_id},
            {"_id": 0}
        )
        onboarding_complete = onboarding.get("is_complete", False) if onboarding else False
        criteria_met["onboarding_complete"] = not QUALIFICATION_CRITERIA["require_onboarding_complete"] or onboarding_complete

        # All criteria must be met
        all_met = all(criteria_met.values())

        if all_met:
            now = datetime.now(timezone.utc)
            await self.db.referrals.update_one(
                {"id": referral["id"]},
                {
                    "$set": {
                        "status": ReferralStatus.QUALIFIED.value,
                        "qualified_at": now.isoformat(),
                        "updated_at": now.isoformat()
                    }
                }
            )

            # Log activity
            await self._log_referral_activity(
                creator_id=referral["referrer_id"],
                action="referral_qualified",
                details={"referral_id": referral["id"], "referred_id": referred_creator_id}
            )

        return {
            "qualified": all_met,
            "criteria_status": criteria_met,
            "referral_id": referral["id"]
        }

    async def convert_referral(
        self,
        referred_creator_id: str,
        subscription_amount: float,
        plan_id: str
    ) -> Dict[str, Any]:
        """
        Convert a referral when the referred user subscribes.
        Calculates and awards commission to the referrer.
        Integrated with Calculator service.
        """
        # Find pending or qualified referral
        referral = await self.db.referrals.find_one(
            {
                "referred_creator_id": referred_creator_id,
                "status": {"$in": [ReferralStatus.PENDING.value, ReferralStatus.QUALIFIED.value]}
            },
            {"_id": 0}
        )

        if not referral:
            return {"converted": False, "reason": "No active referral found"}

        referrer_id = referral["referrer_id"]
        now = datetime.now(timezone.utc)

        # Get referrer's tier
        tier = await self._get_referrer_tier(referrer_id)
        commission_rate = COMMISSION_RATES[tier]
        commission_amount = round(subscription_amount * commission_rate, 2)

        # Update referral
        await self.db.referrals.update_one(
            {"id": referral["id"]},
            {
                "$set": {
                    "status": ReferralStatus.CONVERTED.value,
                    "converted_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "conversion_value": subscription_amount,
                    "commission_earned": commission_amount,
                    "commission_status": CommissionStatus.PENDING.value,
                    "subscription_plan": plan_id,
                    "commission_rate": commission_rate,
                    "referrer_tier": tier.value
                }
            }
        )

        # Update referral code stats
        await self.db.referral_codes.update_one(
            {"code": referral["referral_code"]},
            {
                "$inc": {"total_conversions": 1},
                "$set": {"updated_at": now.isoformat()}
            }
        )

        # Create commission record
        commission_id = f"COM-{secrets.token_hex(6).upper()}"
        commission_doc = {
            "id": commission_id,
            "referral_id": referral["id"],
            "referrer_id": referrer_id,
            "referred_id": referred_creator_id,
            "amount": commission_amount,
            "conversion_value": subscription_amount,
            "commission_rate": commission_rate,
            "tier": tier.value,
            "status": CommissionStatus.PENDING.value,
            "created_at": now.isoformat(),
            "approved_at": None,
            "paid_at": None
        }
        await self.db.referral_commissions.insert_one(commission_doc)

        # Record in Calculator (Self-Funding Loop)
        await self._record_commission_in_calculator(
            referrer_id=referrer_id,
            commission_amount=commission_amount,
            referral_id=referral["id"]
        )

        # Check for milestone achievements
        milestones = await self._check_milestones(referrer_id)

        # Log activity
        await self._log_referral_activity(
            creator_id=referrer_id,
            action="referral_converted",
            details={
                "referral_id": referral["id"],
                "commission": commission_amount,
                "subscription_amount": subscription_amount
            }
        )

        return {
            "converted": True,
            "referral_id": referral["id"],
            "commission_id": commission_id,
            "commission_amount": commission_amount,
            "commission_rate": commission_rate,
            "referrer_tier": tier.value,
            "milestones_achieved": milestones
        }

    # ============== COMMISSION MANAGEMENT ==============

    async def _record_commission_in_calculator(
        self,
        referrer_id: str,
        commission_amount: float,
        referral_id: str
    ) -> None:
        """Record referral commission in the Calculator for Self-Funding Loop."""
        now = datetime.now(timezone.utc)
        month_year = now.strftime("%Y-%m")

        calc_entry = {
            "id": f"CALC-REF-{secrets.token_hex(4).upper()}",
            "user_id": referrer_id,
            "category": "Affiliate",  # Uses existing affiliate category
            "source": "Referral Commission",
            "revenue": commission_amount,
            "expenses": 0,
            "net_margin": commission_amount,
            "month_year": month_year,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "notes": f"Referral commission from {referral_id}",
            "linked_referral_id": referral_id
        }

        await self.db.calculator.insert_one(calc_entry)
        logger.info(f"Recorded referral commission ${commission_amount} for creator {referrer_id}")

    async def get_creator_commissions(
        self,
        creator_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get all commissions for a creator."""
        query = {"referrer_id": creator_id}
        if status:
            query["status"] = status

        commissions = await self.db.referral_commissions.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(limit)

        # Calculate totals
        total_earned = sum(c.get("amount", 0) for c in commissions)
        total_pending = sum(c.get("amount", 0) for c in commissions if c.get("status") == CommissionStatus.PENDING.value)
        total_paid = sum(c.get("amount", 0) for c in commissions if c.get("status") == CommissionStatus.PAID.value)

        return {
            "commissions": commissions,
            "summary": {
                "total_earned": round(total_earned, 2),
                "total_pending": round(total_pending, 2),
                "total_paid": round(total_paid, 2),
                "commission_count": len(commissions)
            }
        }

    async def approve_commission(
        self,
        commission_id: str,
        admin_id: str
    ) -> Dict[str, Any]:
        """Admin approves a commission for payout."""
        now = datetime.now(timezone.utc)

        result = await self.db.referral_commissions.update_one(
            {"id": commission_id, "status": CommissionStatus.PENDING.value},
            {
                "$set": {
                    "status": CommissionStatus.APPROVED.value,
                    "approved_at": now.isoformat(),
                    "approved_by": admin_id
                }
            }
        )

        if result.modified_count == 0:
            return {"success": False, "error": "Commission not found or not pending"}

        return {"success": True, "commission_id": commission_id, "status": "approved"}

    async def mark_commission_paid(
        self,
        commission_id: str,
        admin_id: str,
        payout_reference: str = None
    ) -> Dict[str, Any]:
        """Admin marks a commission as paid."""
        now = datetime.now(timezone.utc)

        result = await self.db.referral_commissions.update_one(
            {"id": commission_id, "status": CommissionStatus.APPROVED.value},
            {
                "$set": {
                    "status": CommissionStatus.PAID.value,
                    "paid_at": now.isoformat(),
                    "paid_by": admin_id,
                    "payout_reference": payout_reference
                }
            }
        )

        if result.modified_count == 0:
            return {"success": False, "error": "Commission not found or not approved"}

        # Update the referral record
        commission = await self.db.referral_commissions.find_one({"id": commission_id}, {"_id": 0})
        if commission:
            await self.db.referrals.update_one(
                {"id": commission["referral_id"]},
                {"$set": {"commission_status": CommissionStatus.PAID.value}}
            )

        return {"success": True, "commission_id": commission_id, "status": "paid"}

    # ============== REFERRER TIERS & MILESTONES ==============

    async def _get_referrer_tier(self, creator_id: str) -> ReferralTier:
        """Determine a referrer's tier based on successful referrals."""
        successful_count = await self.db.referrals.count_documents({
            "referrer_id": creator_id,
            "status": ReferralStatus.CONVERTED.value
        })

        if successful_count >= TIER_THRESHOLDS[ReferralTier.PLATINUM]:
            return ReferralTier.PLATINUM
        elif successful_count >= TIER_THRESHOLDS[ReferralTier.GOLD]:
            return ReferralTier.GOLD
        elif successful_count >= TIER_THRESHOLDS[ReferralTier.SILVER]:
            return ReferralTier.SILVER
        return ReferralTier.BRONZE

    async def get_referrer_stats(self, creator_id: str) -> Dict[str, Any]:
        """Get comprehensive referral statistics for a creator."""
        # Get referral code
        code_doc = await self.db.referral_codes.find_one(
            {"creator_id": creator_id, "is_active": True},
            {"_id": 0}
        )

        # Count referrals by status
        pipeline = [
            {"$match": {"referrer_id": creator_id}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        status_counts = {doc["_id"]: doc["count"] for doc in await self.db.referrals.aggregate(pipeline).to_list(10)}

        total_referrals = sum(status_counts.values())
        converted = status_counts.get(ReferralStatus.CONVERTED.value, 0)
        pending = status_counts.get(ReferralStatus.PENDING.value, 0)
        qualified = status_counts.get(ReferralStatus.QUALIFIED.value, 0)

        # Get tier
        tier = await self._get_referrer_tier(creator_id)
        commission_rate = COMMISSION_RATES[tier]

        # Get next tier info
        next_tier_info = self._get_next_tier_info(tier, converted)

        # Get earnings
        earnings_result = await self.db.referral_commissions.aggregate([
            {"$match": {"referrer_id": creator_id}},
            {"$group": {
                "_id": "$status",
                "total": {"$sum": "$amount"}
            }}
        ]).to_list(10)
        earnings_by_status = {doc["_id"]: doc["total"] for doc in earnings_result}

        total_earnings = sum(earnings_by_status.values())
        pending_earnings = earnings_by_status.get(CommissionStatus.PENDING.value, 0)
        paid_earnings = earnings_by_status.get(CommissionStatus.PAID.value, 0)

        # Get milestones
        achieved_milestones = await self.db.referral_milestones.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).to_list(100)

        return {
            "referral_code": code_doc.get("code") if code_doc else None,
            "referral_url": self._build_referral_url(code_doc["code"]) if code_doc else None,
            "tier": tier.value,
            "commission_rate": commission_rate,
            "next_tier": next_tier_info,
            "stats": {
                "total_clicks": code_doc.get("total_clicks", 0) if code_doc else 0,
                "total_referrals": total_referrals,
                "pending": pending,
                "qualified": qualified,
                "converted": converted,
                "conversion_rate": round(converted / total_referrals * 100, 1) if total_referrals > 0 else 0
            },
            "earnings": {
                "total": round(total_earnings, 2),
                "pending": round(pending_earnings, 2),
                "paid": round(paid_earnings, 2)
            },
            "milestones": {
                "achieved": [m["milestone_id"] for m in achieved_milestones],
                "total_bonus_earned": sum(m.get("bonus_amount", 0) for m in achieved_milestones)
            }
        }

    def _get_next_tier_info(self, current_tier: ReferralTier, current_conversions: int) -> Dict[str, Any]:
        """Get info about the next tier and progress toward it."""
        tier_order = [ReferralTier.BRONZE, ReferralTier.SILVER, ReferralTier.GOLD, ReferralTier.PLATINUM]
        current_index = tier_order.index(current_tier)

        if current_index >= len(tier_order) - 1:
            return {
                "tier": None,
                "referrals_needed": 0,
                "commission_rate": COMMISSION_RATES[current_tier],
                "message": "You've reached the highest tier!"
            }

        next_tier = tier_order[current_index + 1]
        referrals_needed = TIER_THRESHOLDS[next_tier] - current_conversions

        return {
            "tier": next_tier.value,
            "referrals_needed": max(0, referrals_needed),
            "commission_rate": COMMISSION_RATES[next_tier],
            "progress_percent": round(current_conversions / TIER_THRESHOLDS[next_tier] * 100, 1) if TIER_THRESHOLDS[next_tier] > 0 else 100
        }

    async def _check_milestones(self, creator_id: str) -> List[Dict[str, Any]]:
        """Check and award milestone bonuses."""
        successful_count = await self.db.referrals.count_documents({
            "referrer_id": creator_id,
            "status": ReferralStatus.CONVERTED.value
        })

        achieved = []
        now = datetime.now(timezone.utc)

        for threshold, milestone in MILESTONE_BONUSES.items():
            if successful_count >= threshold:
                # Check if already achieved
                existing = await self.db.referral_milestones.find_one({
                    "creator_id": creator_id,
                    "milestone_id": f"MILESTONE_{threshold}"
                })

                if not existing:
                    milestone_doc = {
                        "creator_id": creator_id,
                        "milestone_id": f"MILESTONE_{threshold}",
                        "threshold": threshold,
                        "title": milestone["title"],
                        "description": milestone["description"],
                        "bonus_amount": milestone["bonus"],
                        "achieved_at": now.isoformat()
                    }
                    await self.db.referral_milestones.insert_one(milestone_doc)

                    # Record bonus in Calculator
                    await self._record_commission_in_calculator(
                        referrer_id=creator_id,
                        commission_amount=milestone["bonus"],
                        referral_id=f"MILESTONE_{threshold}"
                    )

                    achieved.append({
                        "milestone": milestone["title"],
                        "bonus": milestone["bonus"]
                    })

                    # Log activity
                    await self._log_referral_activity(
                        creator_id=creator_id,
                        action="milestone_achieved",
                        details=milestone_doc
                    )

        return achieved

    # ============== REFERRAL LISTS & HISTORY ==============

    async def get_creator_referrals(
        self,
        creator_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all referrals made by a creator."""
        query = {"referrer_id": creator_id}
        if status:
            query["status"] = status

        referrals = await self.db.referrals.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(limit)

        # Enrich with referred creator info
        for ref in referrals:
            creator = await self.db.creators.find_one(
                {"id": ref["referred_creator_id"]},
                {"_id": 0, "name": 1}
            )
            ref["referred_name"] = creator.get("name", "Unknown") if creator else "Unknown"

        return referrals

    async def get_referral_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the top referrers platform-wide."""
        pipeline = [
            {"$match": {"status": ReferralStatus.CONVERTED.value}},
            {"$group": {
                "_id": "$referrer_id",
                "total_referrals": {"$sum": 1},
                "total_earnings": {"$sum": "$commission_earned"}
            }},
            {"$sort": {"total_referrals": -1}},
            {"$limit": limit}
        ]

        results = await self.db.referrals.aggregate(pipeline).to_list(limit)

        leaderboard = []
        for i, result in enumerate(results):
            creator = await self.db.creators.find_one(
                {"id": result["_id"]},
                {"_id": 0, "name": 1}
            )
            tier = await self._get_referrer_tier(result["_id"])

            leaderboard.append({
                "rank": i + 1,
                "creator_id": result["_id"],
                "name": creator.get("name", "Unknown") if creator else "Unknown",
                "total_referrals": result["total_referrals"],
                "total_earnings": round(result["total_earnings"], 2),
                "tier": tier.value
            })

        return leaderboard

    # ============== ADMIN FUNCTIONS ==============

    async def get_referral_analytics(self) -> Dict[str, Any]:
        """Get platform-wide referral analytics (admin only)."""
        # Total referrals by status
        status_pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$conversion_value"},
                "total_commission": {"$sum": "$commission_earned"}
            }}
        ]
        status_results = await self.db.referrals.aggregate(status_pipeline).to_list(10)
        by_status = {r["_id"]: {"count": r["count"], "value": r["total_value"], "commission": r["total_commission"]} for r in status_results}

        # Active referrers count
        active_referrers = await self.db.referral_codes.count_documents({"is_active": True})

        # Monthly trends
        monthly_pipeline = [
            {"$match": {"status": ReferralStatus.CONVERTED.value}},
            {"$group": {
                "_id": {"$substr": ["$converted_at", 0, 7]},
                "conversions": {"$sum": 1},
                "revenue": {"$sum": "$commission_earned"}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 6}
        ]
        monthly_data = await self.db.referrals.aggregate(monthly_pipeline).to_list(6)

        # Commission stats
        commission_pipeline = [
            {"$group": {
                "_id": "$status",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }}
        ]
        commission_results = await self.db.referral_commissions.aggregate(commission_pipeline).to_list(10)
        commissions_by_status = {r["_id"]: {"total": r["total"], "count": r["count"]} for r in commission_results}

        total_referrals = sum(s["count"] for s in by_status.values())
        total_conversions = by_status.get(ReferralStatus.CONVERTED.value, {}).get("count", 0)

        return {
            "summary": {
                "total_referrals": total_referrals,
                "total_conversions": total_conversions,
                "conversion_rate": round(total_conversions / total_referrals * 100, 1) if total_referrals > 0 else 0,
                "active_referrers": active_referrers,
                "total_commission_paid": commissions_by_status.get(CommissionStatus.PAID.value, {}).get("total", 0),
                "total_commission_pending": commissions_by_status.get(CommissionStatus.PENDING.value, {}).get("total", 0)
            },
            "by_status": by_status,
            "monthly_trends": monthly_data,
            "commissions": commissions_by_status
        }

    async def get_pending_commissions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pending commissions for admin review."""
        commissions = await self.db.referral_commissions.find(
            {"status": CommissionStatus.PENDING.value},
            {"_id": 0}
        ).sort("created_at", 1).to_list(limit)

        # Enrich with creator names
        for comm in commissions:
            referrer = await self.db.creators.find_one({"id": comm["referrer_id"]}, {"_id": 0, "name": 1, "email": 1})
            comm["referrer_name"] = referrer.get("name") if referrer else "Unknown"
            comm["referrer_email"] = referrer.get("email") if referrer else "Unknown"

        return commissions

    # ============== ACTIVITY LOGGING ==============

    async def _log_referral_activity(
        self,
        creator_id: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Log referral-related activity."""
        log_entry = {
            "creator_id": creator_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.referral_activity_log.insert_one(log_entry)


# Singleton instance
referral_service: Optional[ReferralService] = None
