"""
Test Suite for Multi-Brand Management Feature (Phase 4 Module E - Task E4)
Tests Elite creator multi-brand management functionality:
- Brand CRUD operations (create, read, update, delete/archive)
- Brand switching
- Brand templates
- Cross-brand analytics
- ARRIS persona linking
- Feature gating (Elite only)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ELITE_EMAIL = "elitetest@hivehq.com"
ELITE_PASSWORD = "testpassword123"
PRO_EMAIL = "protest@hivehq.com"
PRO_PASSWORD = "testpassword"


class TestMultiBrandFeatureGating:
    """Test that multi-brand endpoints are restricted to Elite tier only"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_elite_token(self):
        """Get Elite creator auth token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Elite login failed: {response.status_code}")
    
    def get_pro_token(self):
        """Get Pro creator auth token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_EMAIL,
            "password": PRO_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Pro login failed: {response.status_code}")
    
    def test_elite_can_access_multi_brand_templates(self):
        """Elite user can access brand templates"""
        token = self.get_elite_token()
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/templates",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 5, f"Expected 5 templates, got {len(data['templates'])}"
        print(f"✓ Elite user can access templates: {len(data['templates'])} templates returned")
    
    def test_pro_blocked_from_multi_brand_templates(self):
        """Pro user should be blocked from multi-brand endpoints"""
        token = self.get_pro_token()
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/templates",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Pro user correctly blocked from templates endpoint (403)")
    
    def test_pro_blocked_from_list_brands(self):
        """Pro user should be blocked from listing brands"""
        token = self.get_pro_token()
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Pro user correctly blocked from list brands endpoint (403)")
    
    def test_pro_blocked_from_create_brand(self):
        """Pro user should be blocked from creating brands"""
        token = self.get_pro_token()
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Brand", "category": "personal"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Pro user correctly blocked from create brand endpoint (403)")
    
    def test_pro_blocked_from_analytics(self):
        """Pro user should be blocked from cross-brand analytics"""
        token = self.get_pro_token()
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/analytics",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Pro user correctly blocked from analytics endpoint (403)")
    
    def test_unauthenticated_blocked(self):
        """Unauthenticated requests should be blocked"""
        response = self.session.get(f"{BASE_URL}/api/elite/multi-brand/templates")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated request correctly blocked")


class TestBrandTemplates:
    """Test brand templates functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
    
    def test_get_templates_returns_5_templates(self):
        """GET /api/elite/multi-brand/templates returns 5 templates"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/templates",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) == 5, f"Expected 5 templates, got {len(templates)}"
        
        # Verify template structure
        expected_ids = ["personal_brand", "business_brand", "influencer_brand", "product_brand", "service_brand"]
        template_ids = [t["id"] for t in templates]
        for expected_id in expected_ids:
            assert expected_id in template_ids, f"Missing template: {expected_id}"
        
        # Verify template fields
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "category" in template
            assert "default_colors" in template
            assert "suggested_platforms" in template
            assert "icon" in template
        
        print(f"✓ Templates endpoint returns 5 templates with correct structure")
        print(f"  Template IDs: {template_ids}")


class TestBrandCRUD:
    """Test brand CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
        
        self.created_brand_ids = []
    
    def teardown_method(self):
        """Cleanup created test brands"""
        for brand_id in self.created_brand_ids:
            try:
                self.session.delete(
                    f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
                    headers=self.headers
                )
            except:
                pass
    
    def test_list_brands(self):
        """GET /api/elite/multi-brand - List brands with limit"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "brands" in data
        assert "limit" in data
        assert data["limit"] == 5, f"Expected limit 5 for Elite, got {data['limit']}"
        
        print(f"✓ List brands returns {len(data['brands'])} brands with limit {data['limit']}")
        
        # Verify existing brands (Tech Reviews Pro and Gaming Zone)
        brand_names = [b["name"] for b in data["brands"]]
        print(f"  Existing brands: {brand_names}")
    
    def test_get_active_brand(self):
        """GET /api/elite/multi-brand/active - Get currently active brand"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/active",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # May or may not have an active brand
        if data.get("brand"):
            brand = data["brand"]
            assert "id" in brand
            assert "name" in brand
            assert "status" in brand
            print(f"✓ Active brand: {brand['name']} (ID: {brand['id']})")
        else:
            print("✓ No active brand set (expected for new users)")
    
    def test_create_brand(self):
        """POST /api/elite/multi-brand - Create new brand"""
        brand_data = {
            "name": "TEST_New Test Brand",
            "description": "A test brand for automated testing",
            "category": "business",
            "colors": {"primary": "#FF5733", "secondary": "#33FF57", "accent": "#3357FF"},
            "tagline": "Testing is believing",
            "voice_tone": "professional",
            "platforms": ["youtube", "twitter"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json=brand_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert "brand" in data
        
        brand = data["brand"]
        self.created_brand_ids.append(brand["id"])
        
        # Verify brand data
        assert brand["name"] == brand_data["name"]
        assert brand["description"] == brand_data["description"]
        assert brand["category"] == brand_data["category"]
        assert brand["status"] == "active"
        assert "id" in brand
        assert brand["id"].startswith("BRAND-")
        
        print(f"✓ Created brand: {brand['name']} (ID: {brand['id']})")
        
        # Verify persistence with GET
        get_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand['id']}",
            headers=self.headers
        )
        assert get_response.status_code == 200
        fetched_brand = get_response.json()
        assert fetched_brand["name"] == brand_data["name"]
        print(f"✓ Brand persisted and retrievable via GET")
    
    def test_create_brand_from_template(self):
        """POST /api/elite/multi-brand - Create brand using template"""
        brand_data = {
            "name": "TEST_Template Brand",
            "description": "Created from influencer template",
            "template_id": "influencer_brand"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json=brand_data
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("success"):
            brand = data["brand"]
            self.created_brand_ids.append(brand["id"])
            
            # Template should set category and colors
            assert brand["category"] == "influencer"
            assert brand["template_id"] == "influencer_brand"
            print(f"✓ Created brand from template: {brand['name']}")
        else:
            # May fail if brand limit reached
            print(f"⚠ Brand creation failed (may be at limit): {data.get('error')}")
    
    def test_get_specific_brand(self):
        """GET /api/elite/multi-brand/{brand_id} - Get specific brand"""
        # First list brands to get an ID
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands available to test")
        
        brand_id = brands[0]["id"]
        
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        brand = response.json()
        
        assert brand["id"] == brand_id
        assert "name" in brand
        assert "status" in brand
        assert "category" in brand
        
        print(f"✓ Retrieved brand: {brand['name']} (ID: {brand_id})")
    
    def test_get_nonexistent_brand_returns_404(self):
        """GET /api/elite/multi-brand/{brand_id} - Returns 404 for non-existent brand"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/BRAND-NONEXISTENT123",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent brand returns 404")
    
    def test_update_brand(self):
        """PUT /api/elite/multi-brand/{brand_id} - Update brand"""
        # Create a brand first
        create_response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json={"name": "TEST_Update Brand", "category": "personal"}
        )
        
        if create_response.status_code != 200 or not create_response.json().get("success"):
            pytest.skip("Could not create brand for update test")
        
        brand_id = create_response.json()["brand"]["id"]
        self.created_brand_ids.append(brand_id)
        
        # Update the brand
        update_data = {
            "name": "TEST_Updated Brand Name",
            "description": "Updated description",
            "tagline": "New tagline",
            "voice_tone": "casual"
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data["brand"]["name"] == update_data["name"]
        assert data["brand"]["description"] == update_data["description"]
        
        print(f"✓ Updated brand: {data['brand']['name']}")
        
        # Verify persistence
        get_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers
        )
        fetched = get_response.json()
        assert fetched["name"] == update_data["name"]
        assert fetched["tagline"] == update_data["tagline"]
        print("✓ Update persisted correctly")
    
    def test_delete_brand_archives_it(self):
        """DELETE /api/elite/multi-brand/{brand_id} - Archives brand (soft delete)"""
        # Create a brand first
        create_response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json={"name": "TEST_Delete Brand", "category": "personal"}
        )
        
        if create_response.status_code != 200 or not create_response.json().get("success"):
            pytest.skip("Could not create brand for delete test")
        
        brand_id = create_response.json()["brand"]["id"]
        
        # Delete (archive) the brand
        response = self.session.delete(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        print(f"✓ Brand archived successfully")
        
        # Verify it's archived (not in default list)
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        brand_ids = [b["id"] for b in brands]
        assert brand_id not in brand_ids, "Archived brand should not appear in default list"
        
        # But should appear with include_archived=true
        list_archived = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand?include_archived=true",
            headers=self.headers
        )
        all_brands = list_archived.json().get("brands", [])
        archived_brand = next((b for b in all_brands if b["id"] == brand_id), None)
        if archived_brand:
            assert archived_brand["status"] == "archived"
            print("✓ Archived brand has status 'archived'")


class TestBrandSwitching:
    """Test brand switching functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
    
    def test_switch_brand(self):
        """POST /api/elite/multi-brand/{brand_id}/switch - Switch active brand"""
        # Get list of brands
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        active_brands = [b for b in brands if b["status"] == "active"]
        
        if len(active_brands) < 2:
            pytest.skip("Need at least 2 active brands to test switching")
        
        # Get current active brand
        active_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/active",
            headers=self.headers
        )
        current_active = active_response.json().get("brand")
        
        # Find a different brand to switch to
        target_brand = next((b for b in active_brands if b["id"] != current_active.get("id")), None)
        if not target_brand:
            pytest.skip("No different brand to switch to")
        
        # Switch to the target brand
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand/{target_brand['id']}/switch",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data["brand"]["id"] == target_brand["id"]
        
        print(f"✓ Switched to brand: {data['brand']['name']}")
        
        # Verify active brand changed
        verify_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/active",
            headers=self.headers
        )
        new_active = verify_response.json().get("brand")
        assert new_active["id"] == target_brand["id"]
        print("✓ Active brand verified after switch")
    
    def test_switch_to_nonexistent_brand_fails(self):
        """POST /api/elite/multi-brand/{brand_id}/switch - Fails for non-existent brand"""
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand/BRAND-NONEXISTENT/switch",
            headers=self.headers
        )
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("✓ Switch to non-existent brand correctly fails")


class TestBrandStatus:
    """Test brand status changes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
        
        self.created_brand_ids = []
    
    def teardown_method(self):
        """Cleanup created test brands"""
        for brand_id in self.created_brand_ids:
            try:
                self.session.delete(
                    f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
                    headers=self.headers
                )
            except:
                pass
    
    def test_change_brand_status_to_paused(self):
        """PATCH /api/elite/multi-brand/{brand_id}/status - Change to paused"""
        # Create a brand
        create_response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json={"name": "TEST_Status Brand", "category": "personal"}
        )
        
        if create_response.status_code != 200 or not create_response.json().get("success"):
            pytest.skip("Could not create brand for status test")
        
        brand_id = create_response.json()["brand"]["id"]
        self.created_brand_ids.append(brand_id)
        
        # Change status to paused
        response = self.session.patch(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}/status",
            headers=self.headers,
            json={"status": "paused"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        print("✓ Brand status changed to paused")
        
        # Verify status
        get_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers
        )
        brand = get_response.json()
        assert brand["status"] == "paused"
        print("✓ Status change persisted")
    
    def test_invalid_status_rejected(self):
        """PATCH /api/elite/multi-brand/{brand_id}/status - Invalid status rejected"""
        # Get a brand
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands available")
        
        brand_id = brands[0]["id"]
        
        response = self.session.patch(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}/status",
            headers=self.headers,
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid status correctly rejected")


class TestBrandAnalytics:
    """Test brand analytics functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
    
    def test_cross_brand_analytics(self):
        """GET /api/elite/multi-brand/analytics - Cross-brand analytics"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/analytics",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "total_brands" in data
        assert "active_brands" in data
        assert "brand_limit" in data
        assert "aggregated_metrics" in data
        assert "brands" in data
        
        # Verify aggregated metrics
        metrics = data["aggregated_metrics"]
        assert "total_proposals" in metrics
        assert "total_projects" in metrics
        assert "total_revenue" in metrics
        assert "total_arris_interactions" in metrics
        
        print(f"✓ Cross-brand analytics returned")
        print(f"  Total brands: {data['total_brands']}, Active: {data['active_brands']}, Limit: {data['brand_limit']}")
        print(f"  Aggregated metrics: {metrics}")
    
    def test_single_brand_analytics(self):
        """GET /api/elite/multi-brand/{brand_id}/analytics - Single brand analytics"""
        # Get a brand
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands available")
        
        brand_id = brands[0]["id"]
        
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}/analytics",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "brand_id" in data
        assert "brand_name" in data
        assert "metrics" in data
        assert "status" in data
        
        metrics = data["metrics"]
        assert "total_proposals" in metrics
        assert "total_projects" in metrics
        assert "total_revenue" in metrics
        
        print(f"✓ Single brand analytics for: {data['brand_name']}")
        print(f"  Metrics: {metrics}")


class TestArrisPersonaLinking:
    """Test ARRIS persona linking to brands"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
    
    def test_link_arris_persona_to_brand(self):
        """POST /api/elite/multi-brand/{brand_id}/arris-persona - Link persona"""
        # Get a brand
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands available")
        
        brand_id = brands[0]["id"]
        
        # Get available personas
        personas_response = self.session.get(
            f"{BASE_URL}/api/elite/personas",
            headers=self.headers
        )
        
        if personas_response.status_code != 200:
            pytest.skip("Could not get personas")
        
        personas = personas_response.json().get("personas", [])
        if not personas:
            pytest.skip("No personas available")
        
        persona_id = personas[0]["id"]
        
        # Link persona to brand
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}/arris-persona",
            headers=self.headers,
            json={"persona_id": persona_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        print(f"✓ Linked persona {persona_id} to brand {brand_id}")
        
        # Verify the link
        brand_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}",
            headers=self.headers
        )
        brand = brand_response.json()
        assert brand.get("arris_persona_id") == persona_id
        print("✓ Persona link persisted")
    
    def test_get_brand_arris_context(self):
        """GET /api/elite/multi-brand/{brand_id}/arris-context - Get ARRIS context"""
        # Get a brand
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands available")
        
        brand_id = brands[0]["id"]
        
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand/{brand_id}/arris-context",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify context structure
        assert "brand_name" in data
        assert "category" in data
        assert "voice_tone" in data
        
        print(f"✓ ARRIS context for brand: {data.get('brand_name')}")


class TestBrandLimits:
    """Test brand limits by tier"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get Elite token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Elite login failed")
    
    def test_elite_has_5_brand_limit(self):
        """Elite tier should have 5 brand limit"""
        response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 5, f"Expected limit 5 for Elite, got {data['limit']}"
        print(f"✓ Elite tier has correct brand limit: {data['limit']}")
    
    def test_duplicate_brand_name_rejected(self):
        """Creating brand with duplicate name should fail"""
        # Get existing brand name
        list_response = self.session.get(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers
        )
        brands = list_response.json().get("brands", [])
        
        if not brands:
            pytest.skip("No brands to test duplicate")
        
        existing_name = brands[0]["name"]
        
        # Try to create with same name
        response = self.session.post(
            f"{BASE_URL}/api/elite/multi-brand",
            headers=self.headers,
            json={"name": existing_name, "category": "personal"}
        )
        
        # Should fail with error about duplicate
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == False, "Should not allow duplicate brand name"
            assert "already exists" in data.get("error", "").lower()
        
        print("✓ Duplicate brand name correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
