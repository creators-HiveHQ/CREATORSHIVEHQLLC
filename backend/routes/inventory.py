"""
Inventory Routes - Expression Phase
====================================
CRUD endpoints for user inventory items (assets, offers, content, workflows, tasks).
Stores data in user_system_profiles collection.
Includes file upload and workflow trigger functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
import os
import base64

from routes.dependencies import security, get_db
from auth import get_current_creator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ============== MODELS ==============

class InventoryItemBase(BaseModel):
    """Base inventory item model"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="draft")  # draft, active, inactive, archived, pending, in_progress, completed, published
    type: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class InventoryItemCreate(InventoryItemBase):
    """Create inventory item request"""
    category: str = Field(..., pattern="^(assets|offers|content|workflows|tasks)$")


class InventoryItemUpdate(BaseModel):
    """Update inventory item request"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class InventoryItem(InventoryItemBase):
    """Full inventory item with ID and timestamps"""
    id: str
    category: str
    created_at: str
    updated_at: str


class InventoryResponse(BaseModel):
    """Inventory list response"""
    assets: List[InventoryItem] = []
    offers: List[InventoryItem] = []
    content: List[InventoryItem] = []
    workflows: List[InventoryItem] = []
    tasks: List[InventoryItem] = []
    total_count: int = 0


# ============== HELPER FUNCTIONS ==============

def generate_item_id(category: str) -> str:
    """Generate unique item ID with category prefix"""
    prefixes = {
        "assets": "AST",
        "offers": "OFR",
        "content": "CNT",
        "workflows": "WFL",
        "tasks": "TSK"
    }
    prefix = prefixes.get(category, "ITM")
    return f"{prefix}-{str(uuid.uuid4())[:8]}"


async def get_user_inventory(db, user_id: str) -> Dict[str, List[Dict]]:
    """Get user's inventory from database"""
    profile = await db.user_system_profiles.find_one(
        {"user_id": user_id},
        {"_id": 0, "inventory": 1}
    )
    
    if not profile or "inventory" not in profile:
        return {
            "assets": [],
            "offers": [],
            "content": [],
            "workflows": [],
            "tasks": []
        }
    
    return profile.get("inventory", {})


async def save_user_inventory(db, user_id: str, inventory: Dict[str, List[Dict]]) -> bool:
    """Save user's inventory to database"""
    result = await db.user_system_profiles.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "inventory": inventory,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    return result.modified_count > 0 or result.upserted_id is not None


# ============== ROUTES ==============

@router.get("", response_model=InventoryResponse)
async def get_inventory(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get all inventory items for the current user.
    Returns items organized by category.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    
    # Count total items
    total = sum(len(items) for items in inventory.values())
    
    return InventoryResponse(
        assets=inventory.get("assets", []),
        offers=inventory.get("offers", []),
        content=inventory.get("content", []),
        workflows=inventory.get("workflows", []),
        tasks=inventory.get("tasks", []),
        total_count=total
    )


@router.get("/stats/summary")
async def get_inventory_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get inventory statistics summary"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    
    stats = {}
    for category, items in inventory.items():
        active_count = len([i for i in items if i.get("status") in ["active", "published", "in_progress"]])
        stats[category] = {
            "total": len(items),
            "active": active_count,
            "draft": len([i for i in items if i.get("status") == "draft"]),
            "completed": len([i for i in items if i.get("status") == "completed"])
        }
    
    return {
        "user_id": user_id,
        "categories": stats,
        "total_items": sum(s["total"] for s in stats.values()),
        "total_active": sum(s["active"] for s in stats.values())
    }


@router.get("/{category}")
async def get_category_items(
    category: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all items in a specific category"""
    if category not in ["assets", "offers", "content", "workflows", "tasks"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    items = inventory.get(category, [])
    
    return {
        "category": category,
        "items": items,
        "count": len(items)
    }


@router.post("", response_model=InventoryItem)
async def create_inventory_item(
    item: InventoryItemCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new inventory item"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    # Get current inventory
    inventory = await get_user_inventory(db, user_id)
    
    # Create new item
    now = datetime.now(timezone.utc).isoformat()
    new_item = {
        "id": generate_item_id(item.category),
        "name": item.name,
        "description": item.description,
        "status": item.status,
        "type": item.type,
        "tags": item.tags,
        "metadata": item.metadata,
        "category": item.category,
        "created_at": now,
        "updated_at": now
    }
    
    # Add to category
    if item.category not in inventory:
        inventory[item.category] = []
    inventory[item.category].append(new_item)
    
    # Save
    await save_user_inventory(db, user_id, inventory)
    
    logger.info(f"Created inventory item {new_item['id']} for user {user_id}")
    
    return InventoryItem(**new_item)


@router.get("/{category}/{item_id}")
async def get_inventory_item(
    category: str,
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get a specific inventory item by ID"""
    if category not in ["assets", "offers", "content", "workflows", "tasks"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    items = inventory.get(category, [])
    
    # Find item
    for item in items:
        if item.get("id") == item_id:
            return item
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.put("/{category}/{item_id}", response_model=InventoryItem)
async def update_inventory_item(
    category: str,
    item_id: str,
    update: InventoryItemUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update an existing inventory item"""
    if category not in ["assets", "offers", "content", "workflows", "tasks"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    items = inventory.get(category, [])
    
    # Find and update item
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            # Update fields
            update_data = update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    item[key] = value
            item["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            items[i] = item
            inventory[category] = items
            
            await save_user_inventory(db, user_id, inventory)
            
            logger.info(f"Updated inventory item {item_id} for user {user_id}")
            
            return InventoryItem(**item)
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{category}/{item_id}")
async def delete_inventory_item(
    category: str,
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete an inventory item"""
    if category not in ["assets", "offers", "content", "workflows", "tasks"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    items = inventory.get(category, [])
    
    # Find and remove item
    original_count = len(items)
    items = [item for item in items if item.get("id") != item_id]
    
    if len(items) == original_count:
        raise HTTPException(status_code=404, detail="Item not found")
    
    inventory[category] = items
    await save_user_inventory(db, user_id, inventory)
    
    logger.info(f"Deleted inventory item {item_id} for user {user_id}")
    
    return {"success": True, "deleted_id": item_id}


@router.post("/{category}/{item_id}/status")
async def update_item_status(
    category: str,
    item_id: str,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Quick status update for an inventory item"""
    valid_statuses = ["draft", "active", "inactive", "archived", "pending", "in_progress", "completed", "published"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update = InventoryItemUpdate(status=status)
    return await update_inventory_item(category, item_id, update, credentials)

