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




# ============== FILE UPLOAD ==============

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    "application/pdf",
    "video/mp4", "video/webm",
    "audio/mpeg", "audio/wav",
    "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", 
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class UploadResponse(BaseModel):
    """File upload response"""
    id: str
    name: str
    type: str
    size: str
    url: str
    created_at: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    item_id: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Upload a file attachment to an inventory item"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    # Validate file type
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{file.content_type}' not allowed")
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    file_id = f"file-{str(uuid.uuid4())[:8]}"
    stored_filename = f"{user_id}_{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Create attachment record
    now = datetime.now(timezone.utc).isoformat()
    attachment = {
        "id": file_id,
        "name": file.filename,
        "type": file.content_type,
        "size": f"{len(content) / 1024:.1f} KB" if len(content) < 1024 * 1024 else f"{len(content) / (1024 * 1024):.1f} MB",
        "url": f"/api/inventory/files/{stored_filename}",
        "created_at": now
    }
    
    # Update item's attachments
    inventory = await get_user_inventory(db, user_id)
    items = inventory.get(category, [])
    
    for item in items:
        if item.get("id") == item_id:
            if "metadata" not in item:
                item["metadata"] = {}
            if "attachments" not in item["metadata"]:
                item["metadata"]["attachments"] = []
            item["metadata"]["attachments"].append(attachment)
            item["updated_at"] = now
            break
    
    inventory[category] = items
    await save_user_inventory(db, user_id, inventory)
    
    logger.info(f"Uploaded file {file_id} for item {item_id}")
    
    return UploadResponse(**attachment)


@router.delete("/attachment/{category}/{item_id}/{attachment_id}")
async def delete_attachment(
    category: str,
    item_id: str,
    attachment_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    """Delete a file attachment from an inventory item"""
    # Validate token
    token_data = verify_token(credentials.credentials)
    user_id = token_data.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find the item
    profile = await db.user_system_profiles.find_one({"user_id": user_id})
    if not profile or "inventory" not in profile:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    items = profile["inventory"].get(category, [])
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Find and remove attachment from metadata
    attachments = item.get("metadata", {}).get("attachments", [])
    attachment = next((a for a in attachments if a.get("id") == attachment_id), None)
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file from storage
    if attachment.get("url"):
        filename = attachment["url"].split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
    
    # Remove attachment from item metadata
    new_attachments = [a for a in attachments if a.get("id") != attachment_id]
    
    # Update the database
    await db.user_system_profiles.update_one(
        {"user_id": user_id, f"inventory.{category}.id": item_id},
        {
            "$set": {
                f"inventory.{category}.$.metadata.attachments": new_attachments,
                f"inventory.{category}.$.updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "success": True,
        "deleted_id": attachment_id,
        "message": f"Attachment '{attachment.get('name', attachment_id)}' deleted successfully"
    }


@router.get("/files/{filename}")
async def get_file(filename: str):
    """Serve an uploaded file"""
    from fastapi.responses import FileResponse
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)


# ============== WORKFLOW TRIGGERS ==============

class WorkflowTrigger(BaseModel):
    """Workflow trigger model"""
    id: str
    type: str  # manual, scheduled, task_completed, engine_activated, webhook, condition
    name: Optional[str] = None
    enabled: bool = True
    schedule: Optional[str] = None
    cron: Optional[str] = None
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    engine: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: str
    updated_at: str


class TriggerExecutionRequest(BaseModel):
    """Trigger execution request"""
    trigger_id: str
    payload: Dict[str, Any] = {}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Manually execute a workflow"""
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    # Get workflow
    inventory = await get_user_inventory(db, user_id)
    workflows = inventory.get("workflows", [])
    
    workflow = None
    for w in workflows:
        if w.get("id") == workflow_id:
            workflow = w
            break
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Log execution
    now = datetime.now(timezone.utc).isoformat()
    execution = {
        "id": f"exec-{str(uuid.uuid4())[:8]}",
        "workflow_id": workflow_id,
        "trigger_type": "manual",
        "status": "completed",
        "started_at": now,
        "completed_at": now
    }
    
    # Update workflow with execution history
    if "metadata" not in workflow:
        workflow["metadata"] = {}
    if "executions" not in workflow["metadata"]:
        workflow["metadata"]["executions"] = []
    workflow["metadata"]["executions"].append(execution)
    workflow["metadata"]["last_executed"] = now
    workflow["updated_at"] = now
    
    # Save
    for i, w in enumerate(workflows):
        if w.get("id") == workflow_id:
            workflows[i] = workflow
            break
    
    inventory["workflows"] = workflows
    await save_user_inventory(db, user_id, inventory)
    
    logger.info(f"Executed workflow {workflow_id} for user {user_id}")
    
    return {
        "success": True,
        "execution_id": execution["id"],
        "workflow_id": workflow_id,
        "status": "completed"
    }


@router.post("/workflows/trigger/{trigger_id}")
async def trigger_workflow_webhook(
    trigger_id: str,
    payload: Dict[str, Any] = {}
):
    """
    Webhook endpoint to trigger a workflow.
    This is a public endpoint for external integrations.
    """
    db = get_db()
    
    # Find workflow with this trigger
    # Note: In production, you'd want to store trigger->workflow mapping more efficiently
    # For now, we search through all user profiles
    profiles = await db.user_system_profiles.find({}).to_list(100)
    
    for profile in profiles:
        inventory = profile.get("inventory", {})
        workflows = inventory.get("workflows", [])
        
        for workflow in workflows:
            triggers = workflow.get("metadata", {}).get("triggers", [])
            for trigger in triggers:
                if trigger.get("id") == trigger_id and trigger.get("enabled"):
                    # Found the trigger - execute workflow
                    now = datetime.now(timezone.utc).isoformat()
                    execution = {
                        "id": f"exec-{str(uuid.uuid4())[:8]}",
                        "workflow_id": workflow["id"],
                        "trigger_type": "webhook",
                        "trigger_id": trigger_id,
                        "payload": payload,
                        "status": "completed",
                        "started_at": now,
                        "completed_at": now
                    }
                    
                    # Update workflow
                    if "metadata" not in workflow:
                        workflow["metadata"] = {}
                    if "executions" not in workflow["metadata"]:
                        workflow["metadata"]["executions"] = []
                    workflow["metadata"]["executions"].append(execution)
                    workflow["metadata"]["last_executed"] = now
                    
                    # Save back to database
                    await db.user_system_profiles.update_one(
                        {"_id": profile["_id"]},
                        {"$set": {"inventory": inventory}}
                    )
                    
                    logger.info(f"Webhook triggered workflow {workflow['id']} via trigger {trigger_id}")
                    
                    return {
                        "success": True,
                        "execution_id": execution["id"],
                        "workflow_id": workflow["id"],
                        "trigger_id": trigger_id
                    }
    
    raise HTTPException(status_code=404, detail="Trigger not found or disabled")


@router.post("/tasks/{task_id}/complete")
async def mark_task_complete(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Mark a task as complete and trigger any associated workflows.
    """
    db = get_db()
    creator = await get_current_creator(credentials, db)
    user_id = creator["id"]
    
    inventory = await get_user_inventory(db, user_id)
    tasks = inventory.get("tasks", [])
    workflows = inventory.get("workflows", [])
    
    # Find and update task
    task_found = False
    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "completed"
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            if "metadata" not in task:
                task["metadata"] = {}
            task["metadata"]["completed_at"] = task["updated_at"]
            task_found = True
            break
    
    if not task_found:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check for workflows triggered by this task completion
    triggered_workflows = []
    now = datetime.now(timezone.utc).isoformat()
    
    for workflow in workflows:
        triggers = workflow.get("metadata", {}).get("triggers", [])
        for trigger in triggers:
            if (trigger.get("type") == "task_completed" and 
                trigger.get("task_id") == task_id and 
                trigger.get("enabled")):
                # Trigger this workflow
                execution = {
                    "id": f"exec-{str(uuid.uuid4())[:8]}",
                    "workflow_id": workflow["id"],
                    "trigger_type": "task_completed",
                    "trigger_id": trigger["id"],
                    "task_id": task_id,
                    "status": "completed",
                    "started_at": now,
                    "completed_at": now
                }
                
                if "metadata" not in workflow:
                    workflow["metadata"] = {}
                if "executions" not in workflow["metadata"]:
                    workflow["metadata"]["executions"] = []
                workflow["metadata"]["executions"].append(execution)
                workflow["metadata"]["last_executed"] = now
                
                triggered_workflows.append({
                    "workflow_id": workflow["id"],
                    "workflow_name": workflow.get("name"),
                    "execution_id": execution["id"]
                })
    
    # Save changes
    inventory["tasks"] = tasks
    inventory["workflows"] = workflows
    await save_user_inventory(db, user_id, inventory)
    
    logger.info(f"Completed task {task_id}, triggered {len(triggered_workflows)} workflows")
    
    return {
        "success": True,
        "task_id": task_id,
        "triggered_workflows": triggered_workflows
    }
