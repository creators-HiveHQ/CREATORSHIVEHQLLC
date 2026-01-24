"""
Multi-Brand Management Service for Creators Hive HQ
Phase 4 Module E - Task E4: Multi-Brand Management

Allows Elite creators to manage multiple brand profiles under one account:
- Create and manage multiple brands (up to 5 for Elite)
- Each brand has its own identity, colors, settings
- Switch between brands for different content contexts
- Brand-specific analytics and metrics
- Separate ARRIS personas per brand
- Brand isolation for projects and proposals

Features:
- Brand profile CRUD operations
- Active brand switching
- Brand-specific settings
- Cross-brand analytics dashboard
- Brand templates and presets
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import secrets

logger = logging.getLogger(__name__)


class BrandStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class BrandCategory(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    INFLUENCER = "influencer"
    AGENCY = "agency"
    PRODUCT = "product"
    SERVICE = "service"


# Brand limits by tier (using lowercase tier values)
BRAND_LIMITS = {
    "free": 1,
    "starter": 1,
    "pro": 2,
    "premium": 3,
    "elite": 5
}

# Default brand templates
BRAND_TEMPLATES = [
    {
        "id": "personal_brand",
        "name": "Personal Brand",
        "description": "For individual creators building their personal brand",
        "category": "personal",
        "default_colors": {"primary": "#7C3AED", "secondary": "#A78BFA", "accent": "#DDD6FE"},
        "suggested_platforms": ["youtube", "instagram", "tiktok", "twitter"],
        "icon": "👤"
    },
    {
        "id": "business_brand",
        "name": "Business Brand",
        "description": "For businesses and companies",
        "category": "business",
        "default_colors": {"primary": "#2563EB", "secondary": "#60A5FA", "accent": "#BFDBFE"},
        "suggested_platforms": ["linkedin", "twitter", "youtube"],
        "icon": "🏢"
    },
    {
        "id": "influencer_brand",
        "name": "Influencer Brand",
        "description": "For social media influencers",
        "category": "influencer",
        "default_colors": {"primary": "#EC4899", "secondary": "#F472B6", "accent": "#FBCFE8"},
        "suggested_platforms": ["instagram", "tiktok", "youtube", "snapchat"],
        "icon": "⭐"
    },
    {
        "id": "product_brand",
        "name": "Product Brand",
        "description": "For specific products or product lines",
        "category": "product",
        "default_colors": {"primary": "#10B981", "secondary": "#34D399", "accent": "#A7F3D0"},
        "suggested_platforms": ["instagram", "pinterest", "youtube"],
        "icon": "📦"
    },
    {
        "id": "service_brand",
        "name": "Service Brand",
        "description": "For service-based businesses",
        "category": "service",
        "default_colors": {"primary": "#F59E0B", "secondary": "#FBBF24", "accent": "#FDE68A"},
        "suggested_platforms": ["linkedin", "twitter", "youtube"],
        "icon": "🛠️"
    }
]


class MultiBrandService:
    """
    Manages multiple brand profiles for Elite creators.
    Enables brand switching, brand-specific settings, and cross-brand analytics.
    """

    def __init__(self, db: AsyncIOMotorDatabase, feature_gating=None):
        self.db = db
        self.feature_gating = feature_gating

    # ============== BRAND MANAGEMENT ==============

    async def create_brand(
        self,
        creator_id: str,
        name: str,
        description: str = "",
        category: str = BrandCategory.PERSONAL.value,
        template_id: Optional[str] = None,
        colors: Optional[Dict[str, str]] = None,
        logo_url: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new brand profile for a creator.
        Elite users can have up to 5 brands.
        """
        # Check brand limit
        existing_brands = await self.get_brands(creator_id)
        active_count = len([b for b in existing_brands if b.get("status") != BrandStatus.ARCHIVED.value])
        
        # Get creator's tier limit
        tier_limit = await self._get_brand_limit(creator_id)
        
        if active_count >= tier_limit:
            return {
                "success": False,
                "error": f"Brand limit reached ({tier_limit} brands for your tier). Upgrade to add more brands.",
                "current_count": active_count,
                "limit": tier_limit
            }

        # Check for duplicate name
        existing_name = await self.db.creator_brands.find_one({
            "creator_id": creator_id,
            "name": {"$regex": f"^{name}$", "$options": "i"},
            "status": {"$ne": BrandStatus.ARCHIVED.value}
        })
        
        if existing_name:
            return {
                "success": False,
                "error": f"A brand named '{name}' already exists"
            }

        # Get template defaults if specified
        template = None
        if template_id:
            template = next((t for t in BRAND_TEMPLATES if t["id"] == template_id), None)

        # Build brand profile
        now = datetime.now(timezone.utc)
        brand_id = f"BRAND-{secrets.token_hex(6).upper()}"
        
        # Use template defaults if not specified
        if template:
            if not colors:
                colors = template.get("default_colors", {})
            # Use template category if category wasn't explicitly specified (still default)
            if category == BrandCategory.PERSONAL.value and template.get("category"):
                category = template.get("category")
            if not platforms:
                platforms = template.get("suggested_platforms", [])
        
        if not colors:
            colors = {"primary": "#7C3AED", "secondary": "#A78BFA", "accent": "#DDD6FE"}

        brand = {
            "id": brand_id,
            "creator_id": creator_id,
            "name": name,
            "description": description,
            "category": category,
            "template_id": template_id,
            "status": BrandStatus.ACTIVE.value,
            
            # Branding
            "colors": colors,
            "logo_url": logo_url or "",
            "cover_image_url": "",
            "favicon_url": "",
            
            # Identity
            "tagline": "",
            "mission": "",
            "voice_tone": "professional",  # professional, casual, friendly, authoritative
            "target_audience": "",
            
            # Platforms
            "platforms": platforms or (template.get("suggested_platforms", []) if template else []),
            "social_links": {},
            
            # Settings
            "settings": settings or {
                "default_for_proposals": False,
                "show_in_portfolio": True,
                "enable_arris_persona": True,
                "notification_preferences": {
                    "email": True,
                    "in_app": True
                }
            },
            
            # ARRIS Integration
            "arris_persona_id": None,  # Can link to custom ARRIS persona
            "arris_context": "",  # Brand-specific context for ARRIS
            
            # Metrics
            "metrics": {
                "total_proposals": 0,
                "total_projects": 0,
                "total_revenue": 0,
                "total_arris_interactions": 0
            },
            
            # Metadata
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_active_at": now.isoformat()
        }

        await self.db.creator_brands.insert_one(brand)
        
        # If this is the first brand, set it as active
        if active_count == 0:
            await self._set_active_brand(creator_id, brand_id)

        # Log brand creation
        await self._log_brand_activity(
            creator_id=creator_id,
            brand_id=brand_id,
            action="brand_created",
            details={"name": name, "category": category}
        )

        logger.info(f"Created brand {brand_id} ({name}) for creator {creator_id}")

        # Remove _id for response
        brand.pop("_id", None)
        
        return {
            "success": True,
            "brand": brand,
            "message": f"Brand '{name}' created successfully"
        }

    async def get_brands(
        self,
        creator_id: str,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all brands for a creator."""
        query = {"creator_id": creator_id}
        
        if not include_archived:
            query["status"] = {"$ne": BrandStatus.ARCHIVED.value}

        brands = await self.db.creator_brands.find(
            query,
            {"_id": 0}
        ).sort("created_at", 1).to_list(10)

        return brands

    async def get_brand(self, creator_id: str, brand_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific brand."""
        brand = await self.db.creator_brands.find_one(
            {"id": brand_id, "creator_id": creator_id},
            {"_id": 0}
        )
        return brand

    async def update_brand(
        self,
        creator_id: str,
        brand_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a brand profile."""
        # Validate brand exists
        brand = await self.get_brand(creator_id, brand_id)
        if not brand:
            return {"success": False, "error": "Brand not found"}

        # Fields that can be updated
        allowed_fields = [
            "name", "description", "category", "tagline", "mission",
            "voice_tone", "target_audience", "colors", "logo_url",
            "cover_image_url", "favicon_url", "platforms", "social_links",
            "settings", "arris_persona_id", "arris_context"
        ]

        # Filter updates
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return {"success": False, "error": "No valid fields to update"}

        # Check for duplicate name if name is being updated
        if "name" in filtered_updates:
            existing = await self.db.creator_brands.find_one({
                "creator_id": creator_id,
                "id": {"$ne": brand_id},
                "name": {"$regex": f"^{filtered_updates['name']}$", "$options": "i"},
                "status": {"$ne": BrandStatus.ARCHIVED.value}
            })
            if existing:
                return {"success": False, "error": f"A brand named '{filtered_updates['name']}' already exists"}

        filtered_updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        result = await self.db.creator_brands.update_one(
            {"id": brand_id, "creator_id": creator_id},
            {"$set": filtered_updates}
        )

        if result.modified_count > 0:
            await self._log_brand_activity(
                creator_id=creator_id,
                brand_id=brand_id,
                action="brand_updated",
                details={"updated_fields": list(filtered_updates.keys())}
            )
            
            updated_brand = await self.get_brand(creator_id, brand_id)
            return {"success": True, "brand": updated_brand}

        return {"success": False, "error": "No changes made"}

    async def update_brand_status(
        self,
        creator_id: str,
        brand_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update brand status (active, paused, archived)."""
        if status not in [s.value for s in BrandStatus]:
            return {"success": False, "error": f"Invalid status: {status}"}

        brand = await self.get_brand(creator_id, brand_id)
        if not brand:
            return {"success": False, "error": "Brand not found"}

        # Can't archive the only active brand
        if status == BrandStatus.ARCHIVED.value:
            active_brands = await self.db.creator_brands.count_documents({
                "creator_id": creator_id,
                "status": BrandStatus.ACTIVE.value
            })
            if active_brands <= 1 and brand.get("status") == BrandStatus.ACTIVE.value:
                return {"success": False, "error": "Cannot archive your only active brand"}

        await self.db.creator_brands.update_one(
            {"id": brand_id, "creator_id": creator_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        await self._log_brand_activity(
            creator_id=creator_id,
            brand_id=brand_id,
            action="status_changed",
            details={"new_status": status}
        )

        return {"success": True, "message": f"Brand status updated to {status}"}

    async def delete_brand(self, creator_id: str, brand_id: str) -> Dict[str, Any]:
        """
        Soft delete a brand (archive it).
        Brands are never fully deleted to preserve historical data.
        """
        return await self.update_brand_status(creator_id, brand_id, BrandStatus.ARCHIVED.value)

    # ============== ACTIVE BRAND SWITCHING ==============

    async def get_active_brand(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get the currently active brand for a creator."""
        # Check creator's active brand setting
        creator_settings = await self.db.creator_brand_settings.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        active_brand_id = creator_settings.get("active_brand_id") if creator_settings else None
        
        if active_brand_id:
            brand = await self.get_brand(creator_id, active_brand_id)
            if brand and brand.get("status") == BrandStatus.ACTIVE.value:
                return brand
        
        # Fall back to first active brand
        brands = await self.get_brands(creator_id)
        active_brands = [b for b in brands if b.get("status") == BrandStatus.ACTIVE.value]
        
        if active_brands:
            # Set this as active and return
            await self._set_active_brand(creator_id, active_brands[0]["id"])
            return active_brands[0]
        
        return None

    async def switch_brand(self, creator_id: str, brand_id: str) -> Dict[str, Any]:
        """Switch the active brand for a creator."""
        brand = await self.get_brand(creator_id, brand_id)
        
        if not brand:
            return {"success": False, "error": "Brand not found"}
        
        if brand.get("status") != BrandStatus.ACTIVE.value:
            return {"success": False, "error": "Cannot switch to a non-active brand"}

        await self._set_active_brand(creator_id, brand_id)

        # Update last active timestamp
        await self.db.creator_brands.update_one(
            {"id": brand_id, "creator_id": creator_id},
            {"$set": {"last_active_at": datetime.now(timezone.utc).isoformat()}}
        )

        await self._log_brand_activity(
            creator_id=creator_id,
            brand_id=brand_id,
            action="brand_switched",
            details={}
        )

        return {
            "success": True,
            "brand": brand,
            "message": f"Switched to brand '{brand['name']}'"
        }

    async def _set_active_brand(self, creator_id: str, brand_id: str) -> None:
        """Set the active brand in creator settings."""
        await self.db.creator_brand_settings.update_one(
            {"creator_id": creator_id},
            {
                "$set": {
                    "active_brand_id": brand_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$setOnInsert": {"creator_id": creator_id}
            },
            upsert=True
        )

    # ============== BRAND TEMPLATES ==============

    async def get_brand_templates(self) -> List[Dict[str, Any]]:
        """Get available brand templates."""
        return BRAND_TEMPLATES

    async def create_brand_from_template(
        self,
        creator_id: str,
        template_id: str,
        name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a brand from a template with optional customizations."""
        template = next((t for t in BRAND_TEMPLATES if t["id"] == template_id), None)
        
        if not template:
            return {"success": False, "error": f"Template '{template_id}' not found"}

        return await self.create_brand(
            creator_id=creator_id,
            name=name,
            description=customizations.get("description", template.get("description", "")),
            category=template.get("category", BrandCategory.PERSONAL.value),
            template_id=template_id,
            colors=customizations.get("colors") if customizations else None,
            logo_url=customizations.get("logo_url") if customizations else None,
            platforms=customizations.get("platforms") if customizations else None,
            settings=customizations.get("settings") if customizations else None
        )

    # ============== BRAND ANALYTICS ==============

    async def get_brand_analytics(self, creator_id: str, brand_id: str) -> Dict[str, Any]:
        """Get analytics for a specific brand."""
        brand = await self.get_brand(creator_id, brand_id)
        if not brand:
            return {"error": "Brand not found"}

        # Get proposals for this brand
        proposals = await self.db.project_proposals.count_documents({
            "creator_id": creator_id,
            "brand_id": brand_id
        })

        # Get projects for this brand
        projects = await self.db.projects.count_documents({
            "creator_id": creator_id,
            "brand_id": brand_id
        })

        # Get revenue from calculator entries
        revenue_pipeline = [
            {"$match": {"creator_id": creator_id, "brand_id": brand_id, "type": "income"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        revenue_result = await self.db.calculator_entries.aggregate(revenue_pipeline).to_list(1)
        total_revenue = revenue_result[0]["total"] if revenue_result else 0

        # Get ARRIS interactions for this brand
        arris_interactions = await self.db.arris_api_requests.count_documents({
            "creator_id": creator_id,
            "brand_id": brand_id
        })

        # Activity over time (last 30 days)
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        activity_pipeline = [
            {
                "$match": {
                    "creator_id": creator_id,
                    "brand_id": brand_id,
                    "timestamp": {"$gte": thirty_days_ago}
                }
            },
            {
                "$group": {
                    "_id": {"$substr": ["$timestamp", 0, 10]},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        activity = await self.db.brand_activity_log.aggregate(activity_pipeline).to_list(30)

        return {
            "brand_id": brand_id,
            "brand_name": brand.get("name"),
            "metrics": {
                "total_proposals": proposals,
                "total_projects": projects,
                "total_revenue": total_revenue,
                "total_arris_interactions": arris_interactions
            },
            "activity_30d": [{"date": a["_id"], "count": a["count"]} for a in activity],
            "status": brand.get("status"),
            "created_at": brand.get("created_at"),
            "last_active_at": brand.get("last_active_at")
        }

    async def get_cross_brand_analytics(self, creator_id: str) -> Dict[str, Any]:
        """Get aggregated analytics across all brands."""
        brands = await self.get_brands(creator_id)
        
        if not brands:
            return {"error": "No brands found"}

        brand_analytics = []
        totals = {
            "total_proposals": 0,
            "total_projects": 0,
            "total_revenue": 0,
            "total_arris_interactions": 0
        }

        for brand in brands:
            analytics = await self.get_brand_analytics(creator_id, brand["id"])
            
            if "error" not in analytics:
                brand_analytics.append({
                    "brand_id": brand["id"],
                    "brand_name": brand["name"],
                    "status": brand["status"],
                    "metrics": analytics.get("metrics", {})
                })
                
                metrics = analytics.get("metrics", {})
                totals["total_proposals"] += metrics.get("total_proposals", 0)
                totals["total_projects"] += metrics.get("total_projects", 0)
                totals["total_revenue"] += metrics.get("total_revenue", 0)
                totals["total_arris_interactions"] += metrics.get("total_arris_interactions", 0)

        return {
            "creator_id": creator_id,
            "total_brands": len(brands),
            "active_brands": len([b for b in brands if b.get("status") == BrandStatus.ACTIVE.value]),
            "brand_limit": await self._get_brand_limit(creator_id),
            "aggregated_metrics": totals,
            "brands": brand_analytics
        }

    # ============== BRAND CONTEXT FOR ARRIS ==============

    async def get_brand_arris_context(self, creator_id: str, brand_id: str) -> Dict[str, Any]:
        """Get brand-specific context for ARRIS interactions."""
        brand = await self.get_brand(creator_id, brand_id)
        
        if not brand:
            return {}

        return {
            "brand_name": brand.get("name"),
            "brand_description": brand.get("description"),
            "category": brand.get("category"),
            "tagline": brand.get("tagline"),
            "mission": brand.get("mission"),
            "voice_tone": brand.get("voice_tone"),
            "target_audience": brand.get("target_audience"),
            "platforms": brand.get("platforms", []),
            "custom_context": brand.get("arris_context", ""),
            "persona_id": brand.get("arris_persona_id")
        }

    async def set_brand_arris_persona(
        self,
        creator_id: str,
        brand_id: str,
        persona_id: str
    ) -> Dict[str, Any]:
        """Link a custom ARRIS persona to a brand."""
        brand = await self.get_brand(creator_id, brand_id)
        if not brand:
            return {"success": False, "error": "Brand not found"}

        await self.db.creator_brands.update_one(
            {"id": brand_id, "creator_id": creator_id},
            {
                "$set": {
                    "arris_persona_id": persona_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )

        return {"success": True, "message": "ARRIS persona linked to brand"}

    # ============== HELPER METHODS ==============

    async def _get_brand_limit(self, creator_id: str) -> int:
        """Get the brand limit for a creator based on their tier."""
        if self.feature_gating:
            access = await self.feature_gating.get_full_feature_access(creator_id)
            tier = access.get("tier", "Free")
            return BRAND_LIMITS.get(tier, 1)
        return 1

    async def _log_brand_activity(
        self,
        creator_id: str,
        brand_id: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Log brand-related activity."""
        log_entry = {
            "creator_id": creator_id,
            "brand_id": brand_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.brand_activity_log.insert_one(log_entry)

    async def increment_brand_metric(
        self,
        creator_id: str,
        brand_id: str,
        metric: str,
        amount: int = 1
    ) -> None:
        """Increment a brand metric (proposals, projects, revenue, etc.)."""
        await self.db.creator_brands.update_one(
            {"id": brand_id, "creator_id": creator_id},
            {"$inc": {f"metrics.{metric}": amount}}
        )


# Export constants
AVAILABLE_TEMPLATES = BRAND_TEMPLATES
AVAILABLE_CATEGORIES = [c.value for c in BrandCategory]

# Singleton instance
multi_brand_service: Optional[MultiBrandService] = None
