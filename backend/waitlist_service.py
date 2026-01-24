"""
Waitlist Service for Creators Hive HQ
Landing Page Waitlist with Priority Referral System

Features:
- Email + name + creator type collection
- Referral code generation for priority access
- Referral tracking and leaderboard
- Position tracking in queue
- SendGrid email notifications
- Admin management dashboard
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import secrets
import hashlib
import re

logger = logging.getLogger(__name__)


class WaitlistStatus(str, Enum):
    PENDING = "pending"
    INVITED = "invited"
    CONVERTED = "converted"
    UNSUBSCRIBED = "unsubscribed"


class CreatorType(str, Enum):
    YOUTUBER = "youtuber"
    INSTAGRAMMER = "instagrammer"
    TIKTOKER = "tiktoker"
    PODCASTER = "podcaster"
    BLOGGER = "blogger"
    STREAMER = "streamer"
    MUSICIAN = "musician"
    ARTIST = "artist"
    EDUCATOR = "educator"
    BUSINESS = "business"
    OTHER = "other"


# Points for referral priority
REFERRAL_POINTS = {
    "signup": 10,           # Points for signing up
    "referral_signup": 25,  # Points when someone uses your referral
    "referral_invited": 50, # Points when your referral gets invited
    "social_share": 5,      # Points for social sharing
}

# Creator type display names
CREATOR_TYPES = [
    {"id": "youtuber", "name": "YouTuber", "icon": "🎬"},
    {"id": "instagrammer", "name": "Instagram Creator", "icon": "📸"},
    {"id": "tiktoker", "name": "TikToker", "icon": "🎵"},
    {"id": "podcaster", "name": "Podcaster", "icon": "🎙️"},
    {"id": "blogger", "name": "Blogger/Writer", "icon": "✍️"},
    {"id": "streamer", "name": "Streamer", "icon": "🎮"},
    {"id": "musician", "name": "Musician", "icon": "🎸"},
    {"id": "artist", "name": "Visual Artist", "icon": "🎨"},
    {"id": "educator", "name": "Educator/Coach", "icon": "📚"},
    {"id": "business", "name": "Business Owner", "icon": "💼"},
    {"id": "other", "name": "Other", "icon": "✨"},
]


class WaitlistService:
    """
    Manages the waitlist with priority referral system.
    """

    def __init__(self, db: AsyncIOMotorDatabase, email_service=None):
        self.db = db
        self.email_service = email_service

    # ============== WAITLIST SIGNUP ==============

    async def signup(
        self,
        email: str,
        name: str,
        creator_type: str,
        niche: str = "",
        referral_code: Optional[str] = None,
        source: str = "landing_page"
    ) -> Dict[str, Any]:
        """
        Sign up for the waitlist with optional referral code.
        """
        # Validate email
        email = email.lower().strip()
        if not self._validate_email(email):
            return {"success": False, "error": "Invalid email address"}

        # Check if already on waitlist
        existing = await self.db.waitlist.find_one({"email": email})
        if existing:
            return {
                "success": False,
                "error": "You're already on the waitlist!",
                "position": existing.get("position"),
                "referral_code": existing.get("referral_code")
            }

        # Validate referral code if provided
        referred_by = None
        if referral_code:
            referrer = await self.db.waitlist.find_one({"referral_code": referral_code})
            if referrer:
                referred_by = referrer.get("id")
                # Award points to referrer
                await self._award_points(referrer["id"], REFERRAL_POINTS["referral_signup"])

        # Get current position (count + 1)
        count = await self.db.waitlist.count_documents({})
        position = count + 1

        # Generate unique referral code
        referral_code_new = await self._generate_referral_code(name)

        # Calculate initial priority score
        priority_score = REFERRAL_POINTS["signup"]
        if referred_by:
            priority_score += 5  # Bonus for being referred

        now = datetime.now(timezone.utc)
        signup_id = f"WL-{secrets.token_hex(6).upper()}"

        signup_data = {
            "id": signup_id,
            "email": email,
            "name": name,
            "creator_type": creator_type,
            "niche": niche,
            "status": WaitlistStatus.PENDING.value,
            "position": position,
            "referral_code": referral_code_new,
            "referred_by": referred_by,
            "referral_count": 0,
            "priority_score": priority_score,
            "source": source,
            "social_shares": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "invited_at": None,
            "converted_at": None
        }

        await self.db.waitlist.insert_one(signup_data)

        # Send confirmation email
        await self._send_confirmation_email(email, name, position, referral_code_new)

        # Log signup
        await self._log_activity(signup_id, "signup", {"source": source, "referred_by": referred_by})

        logger.info(f"New waitlist signup: {email} at position {position}")

        return {
            "success": True,
            "id": signup_id,
            "position": position,
            "referral_code": referral_code_new,
            "priority_score": priority_score,
            "message": f"You're #{position} on the waitlist! Share your referral link to move up."
        }

    async def get_signup_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get waitlist signup by email."""
        return await self.db.waitlist.find_one(
            {"email": email.lower().strip()},
            {"_id": 0}
        )

    async def get_signup_by_referral_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get waitlist signup by referral code."""
        return await self.db.waitlist.find_one(
            {"referral_code": code},
            {"_id": 0}
        )

    async def get_position(self, email: str) -> Dict[str, Any]:
        """Get current position and stats for a signup."""
        signup = await self.get_signup_by_email(email)
        if not signup:
            return {"error": "Email not found on waitlist"}

        # Calculate actual position based on priority score
        higher_priority = await self.db.waitlist.count_documents({
            "priority_score": {"$gt": signup["priority_score"]},
            "status": WaitlistStatus.PENDING.value
        })

        actual_position = higher_priority + 1
        total_waitlist = await self.db.waitlist.count_documents({"status": WaitlistStatus.PENDING.value})

        return {
            "id": signup["id"],
            "email": signup["email"],
            "name": signup["name"],
            "original_position": signup["position"],
            "current_position": actual_position,
            "total_waitlist": total_waitlist,
            "referral_code": signup["referral_code"],
            "referral_count": signup["referral_count"],
            "priority_score": signup["priority_score"],
            "status": signup["status"]
        }

    # ============== REFERRAL SYSTEM ==============

    async def track_social_share(self, email: str, platform: str) -> Dict[str, Any]:
        """Track when user shares on social media."""
        signup = await self.get_signup_by_email(email)
        if not signup:
            return {"success": False, "error": "Email not found"}

        # Check if already shared on this platform
        if platform in signup.get("social_shares", []):
            return {"success": False, "error": f"Already tracked share on {platform}"}

        # Award points
        await self._award_points(signup["id"], REFERRAL_POINTS["social_share"])

        # Track the share
        await self.db.waitlist.update_one(
            {"id": signup["id"]},
            {
                "$push": {"social_shares": platform},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )

        return {"success": True, "points_earned": REFERRAL_POINTS["social_share"]}

    async def get_referral_stats(self, email: str) -> Dict[str, Any]:
        """Get referral statistics for a signup."""
        signup = await self.get_signup_by_email(email)
        if not signup:
            return {"error": "Email not found"}

        # Get referrals
        referrals = await self.db.waitlist.find(
            {"referred_by": signup["id"]},
            {"_id": 0, "email": 1, "name": 1, "status": 1, "created_at": 1}
        ).to_list(100)

        return {
            "referral_code": signup["referral_code"],
            "referral_count": len(referrals),
            "priority_score": signup["priority_score"],
            "referrals": [
                {
                    "name": r["name"],
                    "status": r["status"],
                    "joined": r["created_at"]
                }
                for r in referrals
            ]
        }

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top referrers leaderboard."""
        pipeline = [
            {"$match": {"status": WaitlistStatus.PENDING.value}},
            {"$sort": {"priority_score": -1, "referral_count": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0,
                "name": 1,
                "referral_count": 1,
                "priority_score": 1,
                "creator_type": 1
            }}
        ]

        leaders = await self.db.waitlist.aggregate(pipeline).to_list(limit)

        return [
            {
                "rank": idx + 1,
                "name": self._mask_name(l["name"]),
                "referrals": l["referral_count"],
                "score": l["priority_score"],
                "creator_type": l["creator_type"]
            }
            for idx, l in enumerate(leaders)
        ]

    # ============== ADMIN FUNCTIONS ==============

    async def get_all_signups(
        self,
        status: Optional[str] = None,
        creator_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> Dict[str, Any]:
        """Get all waitlist signups with filtering."""
        query = {}
        if status:
            query["status"] = status
        if creator_type:
            query["creator_type"] = creator_type

        total = await self.db.waitlist.count_documents(query)

        signups = await self.db.waitlist.find(
            query,
            {"_id": 0}
        ).sort(sort_by, sort_order).skip(skip).limit(limit).to_list(limit)

        return {
            "signups": signups,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def get_waitlist_stats(self) -> Dict[str, Any]:
        """Get waitlist statistics for admin dashboard."""
        total = await self.db.waitlist.count_documents({})
        pending = await self.db.waitlist.count_documents({"status": WaitlistStatus.PENDING.value})
        invited = await self.db.waitlist.count_documents({"status": WaitlistStatus.INVITED.value})
        converted = await self.db.waitlist.count_documents({"status": WaitlistStatus.CONVERTED.value})

        # Get signups by creator type
        type_pipeline = [
            {"$group": {"_id": "$creator_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_type = await self.db.waitlist.aggregate(type_pipeline).to_list(20)

        # Get signups by source
        source_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_source = await self.db.waitlist.aggregate(source_pipeline).to_list(10)

        # Get daily signups (last 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        daily_pipeline = [
            {"$match": {"created_at": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_signups = await self.db.waitlist.aggregate(daily_pipeline).to_list(30)

        # Top referrers
        top_referrers = await self.db.waitlist.find(
            {"referral_count": {"$gt": 0}},
            {"_id": 0, "name": 1, "email": 1, "referral_count": 1, "priority_score": 1}
        ).sort("referral_count", -1).limit(10).to_list(10)

        return {
            "total": total,
            "pending": pending,
            "invited": invited,
            "converted": converted,
            "by_creator_type": [{"type": t["_id"], "count": t["count"]} for t in by_type],
            "by_source": [{"source": s["_id"], "count": s["count"]} for s in by_source],
            "daily_signups": [{"date": d["_id"], "count": d["count"]} for d in daily_signups],
            "top_referrers": top_referrers,
            "conversion_rate": round((converted / max(1, invited)) * 100, 1) if invited > 0 else 0
        }

    async def invite_users(self, signup_ids: List[str]) -> Dict[str, Any]:
        """Send invitations to selected users."""
        invited_count = 0
        errors = []

        for signup_id in signup_ids:
            signup = await self.db.waitlist.find_one({"id": signup_id})
            if not signup:
                errors.append(f"{signup_id}: Not found")
                continue

            if signup["status"] != WaitlistStatus.PENDING.value:
                errors.append(f"{signup_id}: Already {signup['status']}")
                continue

            # Update status
            await self.db.waitlist.update_one(
                {"id": signup_id},
                {
                    "$set": {
                        "status": WaitlistStatus.INVITED.value,
                        "invited_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )

            # Award points to referrer
            if signup.get("referred_by"):
                await self._award_points(signup["referred_by"], REFERRAL_POINTS["referral_invited"])

            # Send invitation email
            await self._send_invitation_email(signup["email"], signup["name"])

            await self._log_activity(signup_id, "invited", {})
            invited_count += 1

        return {
            "success": True,
            "invited": invited_count,
            "errors": errors if errors else None
        }

    async def mark_converted(self, email: str) -> Dict[str, Any]:
        """Mark a waitlist signup as converted (signed up for real account)."""
        signup = await self.get_signup_by_email(email)
        if not signup:
            return {"success": False, "error": "Email not found"}

        await self.db.waitlist.update_one(
            {"id": signup["id"]},
            {
                "$set": {
                    "status": WaitlistStatus.CONVERTED.value,
                    "converted_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        await self._log_activity(signup["id"], "converted", {})

        return {"success": True}

    async def delete_signup(self, signup_id: str) -> Dict[str, Any]:
        """Delete a waitlist signup."""
        result = await self.db.waitlist.delete_one({"id": signup_id})
        if result.deleted_count > 0:
            return {"success": True}
        return {"success": False, "error": "Signup not found"}

    async def export_waitlist(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export waitlist data."""
        query = {}
        if status:
            query["status"] = status

        signups = await self.db.waitlist.find(
            query,
            {"_id": 0}
        ).sort("priority_score", -1).to_list(10000)

        return signups

    # ============== HELPER METHODS ==============

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    async def _generate_referral_code(self, name: str) -> str:
        """Generate unique referral code."""
        # Use first part of name + random suffix
        name_part = re.sub(r'[^a-zA-Z]', '', name.split()[0] if name else 'USER')[:6].upper()
        suffix = secrets.token_hex(3).upper()
        code = f"{name_part}{suffix}"

        # Ensure unique
        while await self.db.waitlist.find_one({"referral_code": code}):
            suffix = secrets.token_hex(3).upper()
            code = f"{name_part}{suffix}"

        return code

    async def _award_points(self, signup_id: str, points: int) -> None:
        """Award priority points to a signup."""
        await self.db.waitlist.update_one(
            {"id": signup_id},
            {
                "$inc": {"priority_score": points, "referral_count": 1 if points == REFERRAL_POINTS["referral_signup"] else 0},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )

    def _mask_name(self, name: str) -> str:
        """Mask name for privacy (e.g., "John Doe" -> "John D.")"""
        parts = name.split()
        if len(parts) > 1:
            return f"{parts[0]} {parts[1][0]}."
        return name

    async def _send_confirmation_email(
        self,
        email: str,
        name: str,
        position: int,
        referral_code: str
    ) -> None:
        """Send waitlist confirmation email."""
        if not self.email_service:
            logger.info(f"Email service not configured, skipping confirmation email to {email}")
            return

        try:
            referral_link = f"https://creatorshivehq.com?ref={referral_code}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f23; color: #fff; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #7C3AED, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .card {{ background: linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(167, 139, 250, 0.1)); border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 16px; padding: 30px; margin-bottom: 20px; }}
                    .position {{ font-size: 48px; font-weight: bold; color: #7C3AED; text-align: center; }}
                    .referral-box {{ background: rgba(0,0,0,0.3); border-radius: 8px; padding: 15px; text-align: center; margin-top: 20px; }}
                    .referral-code {{ font-size: 24px; font-weight: bold; color: #A78BFA; letter-spacing: 2px; }}
                    .btn {{ display: inline-block; background: linear-gradient(135deg, #7C3AED, #A78BFA); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }}
                    .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">Creators Hive HQ</div>
                        <p style="color: #A78BFA;">Powered by ARRIS AI</p>
                    </div>
                    
                    <div class="card">
                        <h2 style="text-align: center; margin-bottom: 20px;">Welcome to the Waitlist, {name}! 🎉</h2>
                        <p style="text-align: center; color: #ccc;">You're officially on the list! Here's your position:</p>
                        <div class="position">#{position}</div>
                        <p style="text-align: center; color: #ccc; margin-top: 20px;">
                            Want to move up? Share your unique referral link and earn priority access!
                        </p>
                        
                        <div class="referral-box">
                            <p style="color: #888; margin-bottom: 10px;">Your Referral Code</p>
                            <div class="referral-code">{referral_code}</div>
                            <p style="margin-top: 15px;">
                                <a href="{referral_link}" class="btn">Share & Move Up</a>
                            </p>
                        </div>
                    </div>
                    
                    <div class="card" style="padding: 20px;">
                        <h3 style="margin-bottom: 15px;">🚀 How to Move Up the List</h3>
                        <ul style="color: #ccc; line-height: 1.8;">
                            <li>Each friend who joins using your link = +25 priority points</li>
                            <li>Share on social media = +5 points per platform</li>
                            <li>When your referrals get invited = +50 bonus points</li>
                        </ul>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 Creators Hive HQ. All rights reserved.</p>
                        <p>You received this email because you signed up for our waitlist.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            await self.email_service.send_email(
                to_email=email,
                subject=f"You're #{position} on the Creators Hive HQ Waitlist! 🎉",
                html_content=html_content
            )
            logger.info(f"Confirmation email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

    async def _send_invitation_email(self, email: str, name: str) -> None:
        """Send invitation email when user is invited."""
        if not self.email_service:
            return

        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f23; color: #fff; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #7C3AED, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .card {{ background: linear-gradient(135deg, rgba(124, 58, 237, 0.2), rgba(167, 139, 250, 0.1)); border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 16px; padding: 30px; text-align: center; }}
                    .btn {{ display: inline-block; background: linear-gradient(135deg, #7C3AED, #A78BFA); color: white; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 18px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">Creators Hive HQ</div>
                    </div>
                    
                    <div class="card">
                        <h1 style="margin-bottom: 20px;">🎉 You're In, {name}!</h1>
                        <p style="color: #ccc; font-size: 18px; margin-bottom: 30px;">
                            Your wait is over! You've been selected to join Creators Hive HQ.
                        </p>
                        <a href="https://creatorshivehq.com/creator/register" class="btn">
                            Create Your Account →
                        </a>
                        <p style="color: #888; margin-top: 20px; font-size: 14px;">
                            This invitation expires in 7 days.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            await self.email_service.send_email(
                to_email=email,
                subject="🎉 You're Invited to Creators Hive HQ!",
                html_content=html_content
            )
            logger.info(f"Invitation email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}")

    async def _log_activity(
        self,
        signup_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Log waitlist activity."""
        log_entry = {
            "signup_id": signup_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.waitlist_activity_log.insert_one(log_entry)


# Export constants
AVAILABLE_CREATOR_TYPES = CREATOR_TYPES

# Singleton instance
waitlist_service: Optional[WaitlistService] = None
