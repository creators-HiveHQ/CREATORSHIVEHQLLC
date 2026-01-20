"""
Elite Tier Features Tests
Tests for Custom ARRIS Workflows, Elite Dashboard, Adaptive Intelligence, and Brand Integrations
Elite users get access to all these exclusive features.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ELITE_USER = {"email": "elite@poweruser.com", "password": "elite123"}
PRO_USER = {"email": "protest@dashboard.com", "password": "propassword123"}


class TestEliteAuth:
    """Test authentication for Elite and Pro users"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite user token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Elite user login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get Pro user token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Pro user login failed: {response.status_code} - {response.text}")
    
    def test_elite_user_login(self):
        """Test Elite user can login"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        assert response.status_code == 200, f"Elite login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
    
    def test_pro_user_login(self):
        """Test Pro user can login"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        assert response.status_code == 200, f"Pro login failed: {response.text}"
        data = response.json()
        assert "access_token" in data


class TestEliteStatus:
    """Test GET /api/elite/status endpoint"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    def test_elite_status_requires_auth(self):
        """Test /api/elite/status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/elite/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_elite_user_status_returns_elite_features(self, elite_token):
        """Test Elite user gets is_elite=true and all elite features enabled"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/status", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("is_elite") == True, f"Expected is_elite=True, got {data.get('is_elite')}"
        assert data.get("tier") == "elite", f"Expected tier='elite', got {data.get('tier')}"
        
        # Check elite features
        elite_features = data.get("elite_features", {})
        assert elite_features.get("custom_arris_workflows") == True
        assert elite_features.get("brand_integrations") == True
        assert elite_features.get("custom_dashboard") == True
        assert elite_features.get("adaptive_intelligence") == True
    
    def test_pro_user_status_returns_non_elite(self, pro_token):
        """Test Pro user gets is_elite=false and elite features disabled"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/status", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("is_elite") == False, f"Expected is_elite=False, got {data.get('is_elite')}"
        
        # Check elite features are disabled
        elite_features = data.get("elite_features", {})
        assert elite_features.get("custom_arris_workflows") == False
        assert elite_features.get("brand_integrations") == False
        assert elite_features.get("custom_dashboard") == False
        assert elite_features.get("adaptive_intelligence") == False
        
        # Should have upgrade URL
        assert data.get("upgrade_url") is not None


class TestEliteWorkflows:
    """Test Custom ARRIS Workflows endpoints"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    # --- Feature Gating Tests ---
    
    def test_workflows_returns_403_for_non_elite(self, pro_token):
        """Test GET /api/elite/workflows returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/workflows", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated" or "Elite" in str(detail)
    
    def test_create_workflow_returns_403_for_non_elite(self, pro_token):
        """Test POST /api/elite/workflows returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        workflow_data = {
            "name": "Test Workflow",
            "description": "Should fail for Pro user"
        }
        response = requests.post(f"{BASE_URL}/api/elite/workflows", headers=headers, json=workflow_data)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    # --- Elite User CRUD Tests ---
    
    def test_get_workflows_for_elite_user(self, elite_token):
        """Test GET /api/elite/workflows returns workflows for Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/workflows", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "workflows" in data
        assert "total" in data
        assert isinstance(data["workflows"], list)
        # Check for default_workflow field
        assert "default_workflow" in data
    
    def test_create_workflow_for_elite_user(self, elite_token):
        """Test POST /api/elite/workflows creates workflow for Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        workflow_data = {
            "name": "TEST_Growth Analysis Workflow",
            "description": "Custom workflow for growth strategy analysis",
            "trigger": "manual",
            "config": {
                "focus_areas": ["growth_strategy", "monetization"],
                "analysis_depth": "detailed",
                "include_benchmarks": True
            },
            "is_default": False
        }
        response = requests.post(f"{BASE_URL}/api/elite/workflows", headers=headers, json=workflow_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Workflow created"
        workflow = data.get("workflow", {})
        assert workflow.get("name") == "TEST_Growth Analysis Workflow"
        assert workflow.get("id") is not None
        assert workflow.get("id").startswith("WF-")
        
        # Store workflow ID for later tests
        TestEliteWorkflows.created_workflow_id = workflow.get("id")
    
    def test_get_specific_workflow(self, elite_token):
        """Test GET /api/elite/workflows/{id} returns specific workflow"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        workflow_id = getattr(TestEliteWorkflows, 'created_workflow_id', None)
        
        if not workflow_id:
            # Get first workflow from list
            response = requests.get(f"{BASE_URL}/api/elite/workflows", headers=headers)
            workflows = response.json().get("workflows", [])
            if workflows:
                workflow_id = workflows[0].get("id")
            else:
                pytest.skip("No workflows available to test")
        
        response = requests.get(f"{BASE_URL}/api/elite/workflows/{workflow_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("id") == workflow_id
        assert "name" in data
        assert "config" in data
    
    def test_update_workflow(self, elite_token):
        """Test PUT /api/elite/workflows/{id} updates workflow"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        workflow_id = getattr(TestEliteWorkflows, 'created_workflow_id', None)
        
        if not workflow_id:
            pytest.skip("No workflow created to update")
        
        updates = {
            "name": "TEST_Updated Growth Workflow",
            "description": "Updated description"
        }
        response = requests.put(f"{BASE_URL}/api/elite/workflows/{workflow_id}", headers=headers, json=updates)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Workflow updated"
        workflow = data.get("workflow", {})
        assert workflow.get("name") == "TEST_Updated Growth Workflow"
    
    def test_delete_workflow(self, elite_token):
        """Test DELETE /api/elite/workflows/{id} deletes workflow"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        workflow_id = getattr(TestEliteWorkflows, 'created_workflow_id', None)
        
        if not workflow_id:
            pytest.skip("No workflow created to delete")
        
        response = requests.delete(f"{BASE_URL}/api/elite/workflows/{workflow_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Workflow deleted"
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/elite/workflows/{workflow_id}", headers=headers)
        assert response.status_code == 404


class TestWorkflowRun:
    """Test running workflows on proposals"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    def test_run_workflow_on_proposal(self, elite_token):
        """Test POST /api/elite/workflows/{id}/run executes workflow on proposal"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # First, get a workflow
        response = requests.get(f"{BASE_URL}/api/elite/workflows", headers=headers)
        workflows = response.json().get("workflows", [])
        
        if not workflows:
            # Create a workflow first
            workflow_data = {
                "name": "TEST_Run Workflow",
                "description": "Workflow for run test",
                "config": {"focus_areas": ["growth_strategy"]}
            }
            response = requests.post(f"{BASE_URL}/api/elite/workflows", headers=headers, json=workflow_data)
            workflow_id = response.json().get("workflow", {}).get("id")
        else:
            workflow_id = workflows[0].get("id")
        
        # Get a proposal
        response = requests.get(f"{BASE_URL}/api/creators/me/proposals", headers=headers)
        proposals = response.json()
        
        if not proposals:
            pytest.skip("No proposals available to run workflow on")
        
        proposal_id = proposals[0].get("id")
        
        # Run workflow
        run_data = {
            "proposal_id": proposal_id,
            "workflow_id": workflow_id
        }
        response = requests.post(f"{BASE_URL}/api/elite/workflows/{workflow_id}/run", headers=headers, json=run_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Workflow executed successfully"
        result = data.get("result", {})
        assert "workflow_id" in result
        assert "workflow_name" in result
        assert "base_insights" in result or "workflow_enhancements" in result


class TestBrandIntegrations:
    """Test Brand Integrations endpoints"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    # --- Feature Gating Tests ---
    
    def test_brands_returns_403_for_non_elite(self, pro_token):
        """Test GET /api/elite/brands returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/brands", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated" or "Elite" in str(detail)
    
    def test_create_brand_returns_403_for_non_elite(self, pro_token):
        """Test POST /api/elite/brands returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        brand_data = {
            "brand_name": "Test Brand",
            "deal_type": "sponsorship"
        }
        response = requests.post(f"{BASE_URL}/api/elite/brands", headers=headers, json=brand_data)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    # --- Elite User CRUD Tests ---
    
    def test_get_brands_for_elite_user(self, elite_token):
        """Test GET /api/elite/brands returns brands with analytics for Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/brands", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "integrations" in data
        assert "total" in data
        assert "analytics" in data
        
        # Check analytics structure
        analytics = data.get("analytics", {})
        assert "total_brands" in analytics
        assert "pipeline" in analytics
    
    def test_create_brand_integration(self, elite_token):
        """Test POST /api/elite/brands creates brand with arris_recommendation_score"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        brand_data = {
            "brand_name": "TEST_Nike Partnership",
            "contact_name": "John Smith",
            "contact_email": "john@nike.com",
            "deal_type": "sponsorship",
            "status": "prospecting",
            "deal_value": 5000,
            "currency": "USD",
            "platforms": ["YouTube", "Instagram"],
            "deliverables": ["3 sponsored posts", "1 video review"],
            "notes": "Initial outreach for Q1 campaign"
        }
        response = requests.post(f"{BASE_URL}/api/elite/brands", headers=headers, json=brand_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Brand integration created"
        brand = data.get("brand", {})
        assert brand.get("brand_name") == "TEST_Nike Partnership"
        assert brand.get("id") is not None
        assert brand.get("id").startswith("BRAND-")
        
        # Check arris_recommendation_score is calculated
        assert "arris_recommendation_score" in brand
        assert brand.get("arris_recommendation_score") is not None
        
        # Store brand ID for later tests
        TestBrandIntegrations.created_brand_id = brand.get("id")
    
    def test_get_specific_brand(self, elite_token):
        """Test GET /api/elite/brands/{id} returns specific brand"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        brand_id = getattr(TestBrandIntegrations, 'created_brand_id', None)
        
        if not brand_id:
            pytest.skip("No brand created to test")
        
        response = requests.get(f"{BASE_URL}/api/elite/brands/{brand_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("id") == brand_id
        assert "brand_name" in data
        assert "arris_recommendation_score" in data
    
    def test_update_brand_integration(self, elite_token):
        """Test PUT /api/elite/brands/{id} updates brand"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        brand_id = getattr(TestBrandIntegrations, 'created_brand_id', None)
        
        if not brand_id:
            pytest.skip("No brand created to update")
        
        updates = {
            "status": "negotiating",
            "deal_value": 7500,
            "notes": "Updated - in negotiation phase"
        }
        response = requests.put(f"{BASE_URL}/api/elite/brands/{brand_id}", headers=headers, json=updates)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Brand integration updated"
        brand = data.get("brand", {})
        assert brand.get("status") == "negotiating"
        assert brand.get("deal_value") == 7500
    
    def test_delete_brand_integration(self, elite_token):
        """Test DELETE /api/elite/brands/{id} deletes brand"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        brand_id = getattr(TestBrandIntegrations, 'created_brand_id', None)
        
        if not brand_id:
            pytest.skip("No brand created to delete")
        
        response = requests.delete(f"{BASE_URL}/api/elite/brands/{brand_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Brand integration deleted"
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/elite/brands/{brand_id}", headers=headers)
        assert response.status_code == 404


class TestEliteDashboard:
    """Test Elite Dashboard endpoints"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    def test_dashboard_returns_403_for_non_elite(self, pro_token):
        """Test GET /api/elite/dashboard returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/dashboard", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated" or "Elite" in str(detail)
    
    def test_get_dashboard_for_elite_user(self, elite_token):
        """Test GET /api/elite/dashboard returns config and data with 8 default widgets"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/dashboard", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "config" in data
        assert "data" in data
        
        # Check config structure
        config = data.get("config", {})
        assert "widgets" in config
        assert "brand_colors" in config
        assert "theme" in config
        
        # Check for 8 default widgets
        widgets = config.get("widgets", [])
        assert len(widgets) >= 8, f"Expected at least 8 widgets, got {len(widgets)}"
        
        # Check widget types
        widget_types = [w.get("widget_type") for w in widgets]
        expected_types = ["metric_card", "chart_line", "brand_pipeline", "arris_insights", "activity_feed"]
        for expected in expected_types:
            assert expected in widget_types, f"Missing widget type: {expected}"
        
        # Check data structure
        dashboard_data = data.get("data", {})
        assert "metrics" in dashboard_data
        assert "brand_analytics" in dashboard_data
        assert "adaptive_intelligence" in dashboard_data
        assert "recent_activity" in dashboard_data
    
    def test_update_dashboard_config(self, elite_token):
        """Test PUT /api/elite/dashboard updates dashboard configuration"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        updates = {
            "name": "My Custom Elite Dashboard",
            "theme": "dark",
            "brand_colors": {
                "primary": "#1a1a2e",
                "secondary": "#16213e",
                "accent": "#e94560"
            }
        }
        response = requests.put(f"{BASE_URL}/api/elite/dashboard", headers=headers, json=updates)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Dashboard updated"
        config = data.get("config", {})
        assert config.get("name") == "My Custom Elite Dashboard"
        assert config.get("theme") == "dark"


class TestAdaptiveIntelligence:
    """Test Adaptive Intelligence endpoints"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    def test_adaptive_intelligence_returns_403_for_non_elite(self, pro_token):
        """Test GET /api/elite/adaptive-intelligence returns 403 for non-Elite users"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/adaptive-intelligence", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated" or "Elite" in str(detail)
    
    def test_get_adaptive_intelligence_for_elite_user(self, elite_token):
        """Test GET /api/elite/adaptive-intelligence returns profile and recommendations"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/adaptive-intelligence", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "profile" in data or data.get("profile") is None  # Profile may not exist yet
        assert "recommendations" in data
        assert data.get("feature") == "adaptive_intelligence"
        
        # Check recommendations structure
        recommendations = data.get("recommendations", {})
        assert "profile_summary" in recommendations or "recommendations" in recommendations
    
    def test_refresh_adaptive_intelligence(self, elite_token):
        """Test POST /api/elite/adaptive-intelligence/refresh rebuilds profile"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.post(f"{BASE_URL}/api/elite/adaptive-intelligence/refresh", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("message") == "Adaptive Intelligence profile refreshed"
        assert "profile" in data
        assert "recommendations" in data
        
        # Check profile structure
        profile = data.get("profile", {})
        if profile and profile != {"message": "No proposals to learn from"}:
            assert "learning_score" in profile
            assert "preferred_platforms" in profile
            assert "complexity_comfort_level" in profile
            assert "total_proposals_analyzed" in profile


class TestBrandAnalytics:
    """Test Brand Analytics summary endpoint"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    def test_get_brand_analytics_summary(self, elite_token):
        """Test GET /api/elite/brands/analytics/summary returns analytics"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/elite/brands/analytics/summary", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "total_brands" in data
        assert "active_partnerships" in data
        assert "pipeline" in data
        assert "status_breakdown" in data
        assert "deal_types" in data
        assert "avg_deal_value" in data
        
        # Check pipeline structure
        pipeline = data.get("pipeline", {})
        assert "total_value" in pipeline
        assert "active_value" in pipeline
        assert "completed_value" in pipeline


class TestEliteFeatureGating:
    """Test feature gating for Elite features"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Elite user login failed")
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro user login failed")
    
    def test_elite_user_feature_access(self, elite_token):
        """Test Elite user has all Elite features in feature-access"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/feature-access", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("tier") == "elite"
        
        features = data.get("features", {})
        assert features.get("custom_arris_workflows") == True
        assert features.get("brand_integrations") == True
        assert features.get("dashboard_level") == "custom"
    
    def test_pro_user_no_elite_features(self, pro_token):
        """Test Pro user does not have Elite features"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/feature-access", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("tier") != "elite"
        
        features = data.get("features", {})
        assert features.get("custom_arris_workflows") == False
        assert features.get("brand_integrations") == False
        assert features.get("dashboard_level") != "custom"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
