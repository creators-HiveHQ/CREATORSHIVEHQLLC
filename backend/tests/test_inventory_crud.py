"""
Inventory CRUD API Tests - Expression Phase
============================================
Tests for inventory endpoints: GET, POST, PUT, DELETE
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://engine-dashboard-1.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "elitetest@hivehq.com"
TEST_PASSWORD = "testpassword123"


class TestInventoryAPI:
    """Test inventory CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_items = []  # Track items for cleanup
    
    def teardown_method(self):
        """Cleanup created test items"""
        for item in self.created_items:
            try:
                requests.delete(
                    f"{BASE_URL}/api/inventory/{item['category']}/{item['id']}",
                    headers=self.headers
                )
            except:
                pass
    
    # ============== GET Tests ==============
    
    def test_get_inventory_returns_all_categories(self):
        """GET /api/inventory returns all 5 categories"""
        response = requests.get(f"{BASE_URL}/api/inventory", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all categories exist
        assert "assets" in data
        assert "offers" in data
        assert "content" in data
        assert "workflows" in data
        assert "tasks" in data
        assert "total_count" in data
        
        # Verify categories are lists
        assert isinstance(data["assets"], list)
        assert isinstance(data["offers"], list)
        assert isinstance(data["content"], list)
        assert isinstance(data["workflows"], list)
        assert isinstance(data["tasks"], list)
    
    def test_get_inventory_requires_auth(self):
        """GET /api/inventory requires authentication"""
        response = requests.get(f"{BASE_URL}/api/inventory")
        assert response.status_code in [401, 403]
    
    def test_get_category_items(self):
        """GET /api/inventory/{category} returns items for specific category"""
        response = requests.get(f"{BASE_URL}/api/inventory/assets", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "category" in data
        assert data["category"] == "assets"
        assert "items" in data
        assert "count" in data
        assert isinstance(data["items"], list)
    
    def test_get_invalid_category_returns_400(self):
        """GET /api/inventory/{invalid} returns 400"""
        response = requests.get(f"{BASE_URL}/api/inventory/invalid_category", headers=self.headers)
        assert response.status_code == 400
    
    # ============== POST Tests ==============
    
    def test_create_asset_item(self):
        """POST /api/inventory creates new asset"""
        item_data = {
            "name": f"TEST_Asset_{uuid.uuid4().hex[:8]}",
            "description": "Test asset created by automation",
            "category": "assets",
            "status": "draft",
            "tags": ["test", "automation"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == item_data["name"]
        assert data["description"] == item_data["description"]
        assert data["category"] == "assets"
        assert data["status"] == "draft"
        assert "created_at" in data
        assert "updated_at" in data
        
        # Track for cleanup
        self.created_items.append({"id": data["id"], "category": "assets"})
    
    def test_create_offer_item(self):
        """POST /api/inventory creates new offer"""
        item_data = {
            "name": f"TEST_Offer_{uuid.uuid4().hex[:8]}",
            "description": "Test offer",
            "category": "offers",
            "status": "active"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "offers"
        assert data["status"] == "active"
        
        self.created_items.append({"id": data["id"], "category": "offers"})
    
    def test_create_content_item(self):
        """POST /api/inventory creates new content"""
        item_data = {
            "name": f"TEST_Content_{uuid.uuid4().hex[:8]}",
            "description": "Test content",
            "category": "content",
            "status": "published"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "content"
        
        self.created_items.append({"id": data["id"], "category": "content"})
    
    def test_create_workflow_item(self):
        """POST /api/inventory creates new workflow"""
        item_data = {
            "name": f"TEST_Workflow_{uuid.uuid4().hex[:8]}",
            "description": "Test workflow",
            "category": "workflows",
            "status": "active"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "workflows"
        
        self.created_items.append({"id": data["id"], "category": "workflows"})
    
    def test_create_task_item(self):
        """POST /api/inventory creates new task"""
        item_data = {
            "name": f"TEST_Task_{uuid.uuid4().hex[:8]}",
            "description": "Test task",
            "category": "tasks",
            "status": "pending"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "tasks"
        
        self.created_items.append({"id": data["id"], "category": "tasks"})
    
    def test_create_item_requires_name(self):
        """POST /api/inventory requires name field"""
        item_data = {
            "description": "Missing name",
            "category": "assets"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_item_requires_valid_category(self):
        """POST /api/inventory requires valid category"""
        item_data = {
            "name": "Test Item",
            "category": "invalid_category"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=item_data,
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error
    
    # ============== PUT Tests ==============
    
    def test_update_item(self):
        """PUT /api/inventory/{category}/{id} updates item"""
        # First create an item
        create_data = {
            "name": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "description": "Original description",
            "category": "assets",
            "status": "draft"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=create_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        self.created_items.append({"id": item_id, "category": "assets"})
        
        # Update the item
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "status": "active"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            json=update_data,
            headers=self.headers
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["status"] == "active"
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            headers=self.headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Updated Name"
    
    def test_update_nonexistent_item_returns_404(self):
        """PUT /api/inventory/{category}/{id} returns 404 for nonexistent item"""
        update_data = {"name": "Test"}
        
        response = requests.put(
            f"{BASE_URL}/api/inventory/assets/nonexistent-id",
            json=update_data,
            headers=self.headers
        )
        
        assert response.status_code == 404
    
    # ============== DELETE Tests ==============
    
    def test_delete_item(self):
        """DELETE /api/inventory/{category}/{id} removes item"""
        # First create an item
        create_data = {
            "name": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "category": "assets"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=create_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        
        # Delete the item
        delete_response = requests.delete(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] == True
        assert data["deleted_id"] == item_id
        
        # Verify item is gone
        get_response = requests.get(
            f"{BASE_URL}/api/inventory/assets/{item_id}",
            headers=self.headers
        )
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_item_returns_404(self):
        """DELETE /api/inventory/{category}/{id} returns 404 for nonexistent item"""
        response = requests.delete(
            f"{BASE_URL}/api/inventory/assets/nonexistent-id",
            headers=self.headers
        )
        
        assert response.status_code == 404
    
    # ============== Stats Tests ==============
    
    def test_get_inventory_stats(self):
        """GET /api/inventory/stats/summary returns statistics"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/stats/summary",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "categories" in data
        assert "total_items" in data
        assert "total_active" in data


class TestSystemProfile:
    """Test system profile endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_system_profile(self):
        """GET /api/system/profile returns user system profile"""
        response = requests.get(
            f"{BASE_URL}/api/system/profile",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify profile structure
        assert "user_id" in data
        assert "active_engines" in data
        assert "unlocked_modules" in data
        assert "assigned_track" in data
    
    def test_system_profile_requires_auth(self):
        """GET /api/system/profile requires authentication"""
        response = requests.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
