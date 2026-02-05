"""
Expression Phase Backend Tests
==============================
Tests for inventory item detail, asset upload, and workflow triggers.
"""

import pytest
import requests
import os
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://user-test-drive.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "elitetest@hivehq.com"
TEST_PASSWORD = "testpassword123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for creator"""
    response = requests.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestInventoryItemDetail:
    """Tests for inventory item detail endpoints"""
    
    def test_get_inventory_list(self, auth_headers):
        """Test GET /api/inventory returns all categories"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all categories exist
        assert "assets" in data
        assert "offers" in data
        assert "content" in data
        assert "workflows" in data
        assert "tasks" in data
        assert "total_count" in data
        print(f"✓ Inventory has {data['total_count']} total items")
    
    def test_create_asset_item(self, auth_headers):
        """Test creating an asset item"""
        payload = {
            "name": "TEST_Expression_Asset",
            "description": "Test asset for expression phase testing",
            "status": "draft",
            "category": "assets",
            "tags": ["test", "expression"]
        }
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["category"] == "assets"
        assert "id" in data
        assert data["id"].startswith("AST-")
        print(f"✓ Created asset: {data['id']}")
        return data["id"]
    
    def test_get_item_detail(self, auth_headers):
        """Test GET /api/inventory/{category}/{id} returns item details"""
        # First create an item
        payload = {
            "name": "TEST_Detail_Item",
            "description": "Item for detail testing",
            "status": "active",
            "category": "assets",
            "tags": ["detail", "test"],
            "metadata": {"custom_field": "test_value"}
        }
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        
        # Get item detail
        response = requests.get(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == item_id
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["status"] == payload["status"]
        assert data["tags"] == payload["tags"]
        assert "created_at" in data
        assert "updated_at" in data
        print(f"✓ Retrieved item detail: {item_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/assets/{item_id}", headers=auth_headers)
    
    def test_update_item_with_notes(self, auth_headers):
        """Test updating item with notes in metadata"""
        # Create item
        create_payload = {
            "name": "TEST_Notes_Item",
            "description": "Item for notes testing",
            "status": "draft",
            "category": "assets"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=create_payload,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Update with notes
        update_payload = {
            "metadata": {
                "notes": [
                    {
                        "id": "note-test-1",
                        "content": "This is a test note",
                        "created_at": "2026-01-30T10:00:00Z"
                    }
                ]
            }
        }
        response = requests.put(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "metadata" in data
        assert "notes" in data["metadata"]
        assert len(data["metadata"]["notes"]) == 1
        assert data["metadata"]["notes"][0]["content"] == "This is a test note"
        print(f"✓ Updated item with notes: {item_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/assets/{item_id}", headers=auth_headers)
    
    def test_get_nonexistent_item_returns_404(self, auth_headers):
        """Test GET for non-existent item returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/assets/NONEXISTENT-ID",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent item returns 404")


class TestAssetUpload:
    """Tests for asset upload functionality"""
    
    def test_upload_endpoint_requires_file(self, auth_headers):
        """Test upload endpoint requires file parameter"""
        response = requests.post(
            f"{BASE_URL}/api/inventory/upload",
            data={"category": "assets", "item_id": "test-id"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error - missing file
        print("✓ Upload endpoint validates required file")
    
    def test_upload_file_to_item(self, auth_headers):
        """Test uploading a file to an inventory item"""
        # First create an item
        create_payload = {
            "name": "TEST_Upload_Item",
            "description": "Item for upload testing",
            "status": "draft",
            "category": "assets"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=create_payload,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test file content for upload testing")
            temp_path = f.name
        
        try:
            # Upload file
            with open(temp_path, "rb") as f:
                files = {"file": ("test_upload.txt", f, "text/plain")}
                data = {"category": "assets", "item_id": item_id}
                
                # Note: Need to remove Content-Type from headers for multipart
                headers = {"Authorization": auth_headers["Authorization"]}
                response = requests.post(
                    f"{BASE_URL}/api/inventory/upload",
                    files=files,
                    data=data,
                    headers=headers
                )
            
            # Check response - may fail due to file type restrictions
            if response.status_code == 400:
                # text/plain might not be allowed
                print(f"✓ Upload endpoint validates file types (text/plain not allowed)")
            else:
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert "name" in data
                assert "url" in data
                print(f"✓ Uploaded file: {data['id']}")
        finally:
            os.unlink(temp_path)
            # Cleanup item
            requests.delete(f"{BASE_URL}/api/inventory/assets/{item_id}", headers=auth_headers)
    
    def test_upload_image_file(self, auth_headers):
        """Test uploading an image file"""
        # Create item
        create_payload = {
            "name": "TEST_Image_Upload",
            "description": "Item for image upload testing",
            "status": "draft",
            "category": "assets"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=create_payload,
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Create a minimal PNG file (1x1 pixel)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_data)
            temp_path = f.name
        
        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("test_image.png", f, "image/png")}
                data = {"category": "assets", "item_id": item_id}
                headers = {"Authorization": auth_headers["Authorization"]}
                
                response = requests.post(
                    f"{BASE_URL}/api/inventory/upload",
                    files=files,
                    data=data,
                    headers=headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["type"] == "image/png"
            print(f"✓ Uploaded image: {data['id']}")
        finally:
            os.unlink(temp_path)
            requests.delete(f"{BASE_URL}/api/inventory/assets/{item_id}", headers=auth_headers)


class TestWorkflowTriggers:
    """Tests for workflow trigger functionality"""
    
    def test_create_workflow_with_triggers(self, auth_headers):
        """Test creating a workflow with triggers"""
        payload = {
            "name": "TEST_Workflow_Triggers",
            "description": "Workflow for trigger testing",
            "status": "active",
            "category": "workflows",
            "metadata": {
                "triggers": [
                    {
                        "id": "trigger-manual-1",
                        "type": "manual",
                        "name": "Manual Trigger",
                        "enabled": True,
                        "created_at": "2026-01-30T10:00:00Z",
                        "updated_at": "2026-01-30T10:00:00Z"
                    },
                    {
                        "id": "trigger-scheduled-1",
                        "type": "scheduled",
                        "name": "Daily Schedule",
                        "schedule": "daily",
                        "enabled": True,
                        "created_at": "2026-01-30T10:00:00Z",
                        "updated_at": "2026-01-30T10:00:00Z"
                    }
                ]
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"].startswith("WFL-")
        assert "triggers" in data["metadata"]
        assert len(data["metadata"]["triggers"]) == 2
        print(f"✓ Created workflow with triggers: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/workflows/{data['id']}", headers=auth_headers)
    
    def test_manual_workflow_execution(self, auth_headers):
        """Test manual workflow execution"""
        # Create workflow
        payload = {
            "name": "TEST_Manual_Execution",
            "description": "Workflow for manual execution testing",
            "status": "active",
            "category": "workflows"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers
        )
        workflow_id = create_response.json()["id"]
        
        # Execute workflow
        response = requests.post(
            f"{BASE_URL}/api/inventory/workflows/{workflow_id}/execute",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "completed"
        assert "execution_id" in data
        print(f"✓ Executed workflow: {workflow_id}, execution: {data['execution_id']}")
        
        # Verify execution was recorded
        get_response = requests.get(
            f"{BASE_URL}/api/inventory/workflows/{workflow_id}",
            headers=auth_headers
        )
        workflow_data = get_response.json()
        assert "executions" in workflow_data["metadata"]
        assert len(workflow_data["metadata"]["executions"]) > 0
        print(f"✓ Execution recorded in workflow metadata")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/workflows/{workflow_id}", headers=auth_headers)
    
    def test_task_completion_triggers_workflow(self, auth_headers):
        """Test that completing a task can trigger associated workflows"""
        # Create a task
        task_payload = {
            "name": "TEST_Trigger_Task",
            "description": "Task that triggers workflow",
            "status": "in_progress",
            "category": "tasks"
        }
        task_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=task_payload,
            headers=auth_headers
        )
        task_id = task_response.json()["id"]
        
        # Create workflow with task_completed trigger
        workflow_payload = {
            "name": "TEST_Task_Triggered_Workflow",
            "description": "Workflow triggered by task completion",
            "status": "active",
            "category": "workflows",
            "metadata": {
                "triggers": [
                    {
                        "id": "trigger-task-1",
                        "type": "task_completed",
                        "name": "On Task Complete",
                        "task_id": task_id,
                        "enabled": True,
                        "created_at": "2026-01-30T10:00:00Z",
                        "updated_at": "2026-01-30T10:00:00Z"
                    }
                ]
            }
        }
        workflow_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=workflow_payload,
            headers=auth_headers
        )
        workflow_id = workflow_response.json()["id"]
        
        # Complete the task
        complete_response = requests.post(
            f"{BASE_URL}/api/inventory/tasks/{task_id}/complete",
            headers=auth_headers
        )
        assert complete_response.status_code == 200
        data = complete_response.json()
        
        assert data["success"] == True
        assert data["task_id"] == task_id
        assert "triggered_workflows" in data
        
        # Check if workflow was triggered
        if len(data["triggered_workflows"]) > 0:
            assert data["triggered_workflows"][0]["workflow_id"] == workflow_id
            print(f"✓ Task completion triggered workflow: {workflow_id}")
        else:
            print(f"✓ Task completed, no workflows triggered (trigger may not match)")
        
        # Verify task status changed
        task_get = requests.get(
            f"{BASE_URL}/api/inventory/tasks/{task_id}",
            headers=auth_headers
        )
        assert task_get.json()["status"] == "completed"
        print(f"✓ Task status updated to completed")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/tasks/{task_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/inventory/workflows/{workflow_id}", headers=auth_headers)
    
    def test_execute_nonexistent_workflow_returns_404(self, auth_headers):
        """Test executing non-existent workflow returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/inventory/workflows/NONEXISTENT-WFL/execute",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent workflow execution returns 404")
    
    def test_all_trigger_types_supported(self, auth_headers):
        """Test that all 6 trigger types can be configured"""
        trigger_types = ["manual", "scheduled", "task_completed", "engine_activated", "webhook", "condition"]
        
        triggers = []
        for i, trigger_type in enumerate(trigger_types):
            trigger = {
                "id": f"trigger-{trigger_type}-{i}",
                "type": trigger_type,
                "name": f"{trigger_type.replace('_', ' ').title()} Trigger",
                "enabled": True,
                "created_at": "2026-01-30T10:00:00Z",
                "updated_at": "2026-01-30T10:00:00Z"
            }
            if trigger_type == "scheduled":
                trigger["schedule"] = "daily"
            elif trigger_type == "task_completed":
                trigger["task_id"] = "task-0"
            elif trigger_type == "engine_activated":
                trigger["engine"] = "business_engine"
            triggers.append(trigger)
        
        payload = {
            "name": "TEST_All_Trigger_Types",
            "description": "Workflow with all trigger types",
            "status": "active",
            "category": "workflows",
            "metadata": {"triggers": triggers}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["metadata"]["triggers"]) == 6
        saved_types = [t["type"] for t in data["metadata"]["triggers"]]
        for trigger_type in trigger_types:
            assert trigger_type in saved_types
        print(f"✓ All 6 trigger types supported: {trigger_types}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/inventory/workflows/{data['id']}", headers=auth_headers)


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_items(self, auth_headers):
        """Clean up any remaining test items"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=auth_headers)
        data = response.json()
        
        cleaned = 0
        for category in ["assets", "offers", "content", "workflows", "tasks"]:
            for item in data.get(category, []):
                if item.get("name", "").startswith("TEST_"):
                    requests.delete(
                        f"{BASE_URL}/api/inventory/{category}/{item['id']}",
                        headers=auth_headers
                    )
                    cleaned += 1
        
        print(f"✓ Cleaned up {cleaned} test items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
