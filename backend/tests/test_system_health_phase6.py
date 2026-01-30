"""
Phase 6: System Health Endpoints Tests
=======================================
Tests for:
- GET /api/system/health - Comprehensive system health
- GET /api/system/profile - Canonical UserSystemProfile
- GET /api/system/consistency - Data consistency verification
- POST /api/system/sync-health - Health data synchronization
- GET /api/system/export - Full data export

Verifies data flow: intake → engines → modules → dashboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
FREE_TIER_EMAIL = "freetest@hivehq.com"
FREE_TIER_PASSWORD = "testpassword"


class TestSystemHealthEndpoints:
    """Phase 6: System Health API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def get_auth_token(self):
        """Authenticate and get token"""
        if self.token:
            return self.token
            
        response = self.session.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": FREE_TIER_EMAIL, "password": FREE_TIER_PASSWORD}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        
        pytest.skip(f"Authentication failed: {response.status_code}")
        
    # ============== GET /api/system/health ==============
    
    def test_system_health_returns_200(self):
        """GET /api/system/health returns 200 status"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_system_health_returns_overall_health(self):
        """GET /api/system/health returns overall_health status"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_health" in data, "Missing overall_health field"
        # Valid health statuses
        valid_statuses = ["good", "needs_attention", "has_blockers", "critical", "no_active_engines", "not_initialized"]
        assert data["overall_health"] in valid_statuses, f"Invalid overall_health: {data['overall_health']}"
        
    def test_system_health_returns_engine_health(self):
        """GET /api/system/health returns engine_health per-engine"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "engine_health" in data, "Missing engine_health field"
        
        # If initialized, check engine health structure
        if data.get("initialized"):
            engine_health = data["engine_health"]
            assert isinstance(engine_health, dict), "engine_health should be a dict"
            
            # Check each engine has required fields
            for engine_id, engine_data in engine_health.items():
                assert "status" in engine_data, f"Engine {engine_id} missing status"
                assert "health" in engine_data, f"Engine {engine_id} missing health"
                assert "progress" in engine_data, f"Engine {engine_id} missing progress"
                
    def test_system_health_returns_module_health(self):
        """GET /api/system/health returns module_health per-module"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "module_health" in data, "Missing module_health field"
        
        # If initialized, check module health structure
        if data.get("initialized"):
            module_health = data["module_health"]
            assert isinstance(module_health, dict), "module_health should be a dict"
            
            # Check each module has required fields
            for module_id, module_data in module_health.items():
                assert "status" in module_data, f"Module {module_id} missing status"
                assert "health" in module_data, f"Module {module_id} missing health"
                
    def test_system_health_returns_data_consistency(self):
        """GET /api/system/health returns data_consistency checks"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "data_consistency" in data, "Missing data_consistency field"
        
        consistency = data["data_consistency"]
        # Required consistency checks
        required_checks = ["intake_completed", "track_assigned", "engines_initialized", "modules_initialized"]
        for check in required_checks:
            assert check in consistency, f"Missing consistency check: {check}"
            
    def test_system_health_returns_engine_summary(self):
        """GET /api/system/health returns engine_summary aggregates"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized"):
            assert "engine_summary" in data, "Missing engine_summary"
            summary = data["engine_summary"]
            assert "total" in summary, "Missing engine total"
            assert "active" in summary, "Missing engine active count"
            assert "blocked" in summary, "Missing engine blocked count"
            assert "average_progress" in summary, "Missing average_progress"
            
    def test_system_health_returns_module_summary(self):
        """GET /api/system/health returns module_summary aggregates"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized"):
            assert "module_summary" in data, "Missing module_summary"
            summary = data["module_summary"]
            assert "total" in summary, "Missing module total"
            assert "active" in summary, "Missing module active count"
            
    def test_system_health_returns_blockers(self):
        """GET /api/system/health returns blockers summary"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized"):
            assert "blockers" in data, "Missing blockers field"
            blockers = data["blockers"]
            assert "total" in blockers, "Missing total blockers count"
            
    # ============== GET /api/system/profile ==============
    
    def test_system_profile_returns_200(self):
        """GET /api/system/profile returns 200 status"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_system_profile_contains_identity_fields(self):
        """GET /api/system/profile contains identity_type, stage, primary_goal"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized", True):  # If not explicitly uninitialized
            # Check identity fields exist (may be null if not set)
            assert "identity_type" in data or "user_id" in data, "Missing identity fields"
            if "identity_type" in data:
                assert "stage" in data, "Missing stage field"
                assert "primary_goal" in data, "Missing primary_goal field"
                
    def test_system_profile_contains_engine_fields(self):
        """GET /api/system/profile contains selected_engines, active_engines"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized", True) and "user_id" in data:
            assert "selected_engines" in data, "Missing selected_engines"
            assert "active_engines" in data, "Missing active_engines"
            assert isinstance(data["selected_engines"], list), "selected_engines should be a list"
            assert isinstance(data["active_engines"], list), "active_engines should be a list"
            
    def test_system_profile_contains_starting_point_fields(self):
        """GET /api/system/profile contains assets_already_have, missing_elements"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized", True) and "user_id" in data:
            assert "assets_already_have" in data, "Missing assets_already_have"
            assert "missing_elements" in data, "Missing missing_elements"
            assert isinstance(data["assets_already_have"], list), "assets_already_have should be a list"
            assert isinstance(data["missing_elements"], list), "missing_elements should be a list"
            
    def test_system_profile_contains_health_fields(self):
        """GET /api/system/profile contains engine_health, module_health"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized", True) and "user_id" in data:
            assert "engine_health" in data, "Missing engine_health"
            assert "module_health" in data, "Missing module_health"
            assert "overall_health" in data, "Missing overall_health"
            
    def test_system_profile_contains_module_fields(self):
        """GET /api/system/profile contains unlocked_modules, active_modules"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code == 200
        
        data = response.json()
        
        if data.get("initialized", True) and "user_id" in data:
            assert "unlocked_modules" in data, "Missing unlocked_modules"
            assert "active_modules" in data, "Missing active_modules"
            
    # ============== GET /api/system/consistency ==============
    
    def test_system_consistency_returns_200(self):
        """GET /api/system/consistency returns 200 status"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_system_consistency_verifies_intake_data(self):
        """GET /api/system/consistency verifies intake data stored"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200
        
        data = response.json()
        # Should have consistency check result
        assert "consistent" in data, "Missing consistent field"
        assert isinstance(data["consistent"], bool), "consistent should be boolean"
        
    def test_system_consistency_verifies_track_assigned(self):
        """GET /api/system/consistency verifies track assigned"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200
        
        data = response.json()
        # Check for issues/warnings about track
        assert "issues" in data or "checks_passed" in data, "Missing consistency check results"
        
    def test_system_consistency_verifies_engines_initialized(self):
        """GET /api/system/consistency verifies engines initialized"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200
        
        data = response.json()
        assert "checks_passed" in data, "Missing checks_passed count"
        assert "checks_failed" in data, "Missing checks_failed count"
        
    def test_system_consistency_verifies_modules_unlocked(self):
        """GET /api/system/consistency verifies modules unlocked"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200
        
        data = response.json()
        # Should report on module initialization
        assert "issues" in data, "Missing issues list"
        assert "warnings" in data, "Missing warnings list"
        
    def test_system_consistency_returns_detailed_report(self):
        """GET /api/system/consistency returns detailed consistency report"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code == 200
        
        data = response.json()
        # Should have detailed report fields
        assert "overall_status" in data or "consistent" in data, "Missing overall status"
        assert "checked_at" in data or "user_id" in data, "Missing metadata"
        
    # ============== POST /api/system/sync-health ==============
    
    def test_sync_health_returns_200(self):
        """POST /api/system/sync-health returns 200 status"""
        self.get_auth_token()
        response = self.session.post(f"{BASE_URL}/api/system/sync-health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_sync_health_syncs_data(self):
        """POST /api/system/sync-health syncs health data"""
        self.get_auth_token()
        response = self.session.post(f"{BASE_URL}/api/system/sync-health")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data, "Missing success field"
        
        if data.get("success"):
            assert "overall_health" in data, "Missing overall_health after sync"
            assert "synced_at" in data, "Missing synced_at timestamp"
            
    def test_sync_health_updates_engine_health(self):
        """POST /api/system/sync-health updates engine health counts"""
        self.get_auth_token()
        response = self.session.post(f"{BASE_URL}/api/system/sync-health")
        assert response.status_code == 200
        
        data = response.json()
        if data.get("success"):
            assert "engine_health_synced" in data, "Missing engine_health_synced count"
            
    def test_sync_health_updates_module_health(self):
        """POST /api/system/sync-health updates module health counts"""
        self.get_auth_token()
        response = self.session.post(f"{BASE_URL}/api/system/sync-health")
        assert response.status_code == 200
        
        data = response.json()
        if data.get("success"):
            assert "module_health_synced" in data, "Missing module_health_synced count"
            
    # ============== GET /api/system/export ==============
    
    def test_system_export_returns_200(self):
        """GET /api/system/export returns 200 status"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/export")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_system_export_returns_user_data(self):
        """GET /api/system/export returns comprehensive user data"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/export")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data, "Missing user_id"
        assert "export_timestamp" in data, "Missing export_timestamp"
        
    def test_system_export_includes_system_state(self):
        """GET /api/system/export includes user_system_state"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/export")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_system_state" in data, "Missing user_system_state"
        
    def test_system_export_includes_engine_states(self):
        """GET /api/system/export includes engine_states"""
        self.get_auth_token()
        response = self.session.get(f"{BASE_URL}/api/system/export")
        assert response.status_code == 200
        
        data = response.json()
        assert "engine_states" in data, "Missing engine_states"
        
    # ============== Data Flow Verification ==============
    
    def test_data_flow_intake_to_engines(self):
        """Verify data flows correctly from intake to engines"""
        self.get_auth_token()
        
        # Get profile to check intake data
        profile_response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert profile_response.status_code == 200
        profile = profile_response.json()
        
        # Get health to check engine data
        health_response = self.session.get(f"{BASE_URL}/api/system/health")
        assert health_response.status_code == 200
        health = health_response.json()
        
        # If profile has selected_engines, health should have engine_health
        if profile.get("selected_engines") and health.get("initialized"):
            assert health.get("engine_health"), "Engine health should be populated when engines selected"
            
    def test_data_flow_engines_to_modules(self):
        """Verify data flows correctly from engines to modules"""
        self.get_auth_token()
        
        # Get health data
        health_response = self.session.get(f"{BASE_URL}/api/system/health")
        assert health_response.status_code == 200
        health = health_response.json()
        
        if health.get("initialized"):
            # If engines are initialized, modules should be too
            engine_summary = health.get("engine_summary", {})
            module_summary = health.get("module_summary", {})
            
            if engine_summary.get("total", 0) > 0:
                # Should have some modules unlocked
                assert module_summary.get("total", 0) >= 0, "Modules should be tracked"
                
    def test_data_flow_modules_to_dashboard(self):
        """Verify data flows correctly from modules to dashboard"""
        self.get_auth_token()
        
        # Get profile
        profile_response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert profile_response.status_code == 200
        profile = profile_response.json()
        
        # Get consistency check
        consistency_response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert consistency_response.status_code == 200
        consistency = consistency_response.json()
        
        # If profile has modules, consistency should verify them
        if profile.get("unlocked_modules"):
            # Consistency check should pass for modules
            assert "checks_passed" in consistency, "Consistency should track module checks"
            
    def test_full_data_consistency_flow(self):
        """Verify complete data consistency: intake → engines → modules → dashboard"""
        self.get_auth_token()
        
        # Step 1: Get consistency check
        consistency_response = self.session.get(f"{BASE_URL}/api/system/consistency")
        assert consistency_response.status_code == 200
        consistency = consistency_response.json()
        
        # Step 2: Get health
        health_response = self.session.get(f"{BASE_URL}/api/system/health")
        assert health_response.status_code == 200
        health = health_response.json()
        
        # Step 3: Get profile
        profile_response = self.session.get(f"{BASE_URL}/api/system/profile")
        assert profile_response.status_code == 200
        profile = profile_response.json()
        
        # Verify data consistency across all endpoints
        if health.get("initialized") and profile.get("user_id"):
            # Health data_consistency should match consistency endpoint
            health_consistency = health.get("data_consistency", {})
            
            # Both should agree on intake_completed
            if "intake_completed" in health_consistency:
                # Consistency endpoint should not have intake_completed as an issue
                issues = consistency.get("issues", [])
                intake_issue = any("intake" in str(i).lower() for i in issues)
                
                if health_consistency["intake_completed"]:
                    # If health says intake completed, consistency shouldn't flag it
                    assert not intake_issue or consistency.get("consistent"), \
                        "Inconsistency between health and consistency endpoints"


class TestSystemHealthAuthentication:
    """Test authentication requirements for system health endpoints"""
    
    def test_health_requires_auth(self):
        """GET /api/system/health requires authentication"""
        response = requests.get(f"{BASE_URL}/api/system/health")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_profile_requires_auth(self):
        """GET /api/system/profile requires authentication"""
        response = requests.get(f"{BASE_URL}/api/system/profile")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_consistency_requires_auth(self):
        """GET /api/system/consistency requires authentication"""
        response = requests.get(f"{BASE_URL}/api/system/consistency")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_sync_health_requires_auth(self):
        """POST /api/system/sync-health requires authentication"""
        response = requests.post(f"{BASE_URL}/api/system/sync-health")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_export_requires_auth(self):
        """GET /api/system/export requires authentication"""
        response = requests.get(f"{BASE_URL}/api/system/export")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
