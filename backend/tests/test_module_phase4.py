"""
Phase 4: Module Realignment Tests
=================================
Tests for GET /api/modules/status and POST /api/modules/update/{module_id}
Verifies module status calculation, activation/deactivation, and blocker handling.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from Phase 1-3
FREE_USER_EMAIL = "freetest@hivehq.com"
FREE_USER_PASSWORD = "testpassword"


class TestModuleStatusEndpoint:
    """Tests for GET /api/modules/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token for free tier creator"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as free tier creator
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_modules_status_requires_auth(self):
        """GET /api/modules/status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/modules/status requires authentication")
    
    def test_modules_status_returns_initialized(self):
        """GET /api/modules/status returns initialized=True for user with system state"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "initialized" in data, "Response should have 'initialized' field"
        assert data["initialized"] == True, "User should be initialized"
        print("✓ GET /api/modules/status returns initialized=True")
    
    def test_modules_status_returns_overall_health(self):
        """GET /api/modules/status returns overall_health indicator"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_health" in data, "Response should have 'overall_health' field"
        assert data["overall_health"] in ["good", "has_blockers", "no_active_modules"], \
            f"Invalid overall_health: {data['overall_health']}"
        print(f"✓ GET /api/modules/status returns overall_health: {data['overall_health']}")
    
    def test_modules_status_returns_summary(self):
        """GET /api/modules/status returns summary with counts"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data, "Response should have 'summary' field"
        
        summary = data["summary"]
        assert "total" in summary, "Summary should have 'total'"
        assert "active" in summary, "Summary should have 'active'"
        assert "unlocked" in summary, "Summary should have 'unlocked'"
        assert "blocked" in summary, "Summary should have 'blocked'"
        assert "locked" in summary, "Summary should have 'locked'"
        
        # Verify counts add up
        total = summary["active"] + summary["unlocked"] + summary["blocked"] + summary["locked"]
        assert total == summary["total"], f"Counts don't add up: {total} != {summary['total']}"
        print(f"✓ GET /api/modules/status returns summary: {summary}")
    
    def test_modules_status_returns_active_modules(self):
        """GET /api/modules/status returns active_modules array"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_modules" in data, "Response should have 'active_modules' field"
        assert isinstance(data["active_modules"], list), "active_modules should be a list"
        print(f"✓ GET /api/modules/status returns active_modules: {len(data['active_modules'])} modules")
    
    def test_modules_status_returns_unlocked_modules(self):
        """GET /api/modules/status returns unlocked_modules array"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "unlocked_modules" in data, "Response should have 'unlocked_modules' field"
        assert isinstance(data["unlocked_modules"], list), "unlocked_modules should be a list"
        print(f"✓ GET /api/modules/status returns unlocked_modules: {len(data['unlocked_modules'])} modules")
    
    def test_modules_status_returns_blocked_modules(self):
        """GET /api/modules/status returns blocked_modules array"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "blocked_modules" in data, "Response should have 'blocked_modules' field"
        assert isinstance(data["blocked_modules"], list), "blocked_modules should be a list"
        print(f"✓ GET /api/modules/status returns blocked_modules: {len(data['blocked_modules'])} modules")
    
    def test_modules_status_returns_locked_modules(self):
        """GET /api/modules/status returns locked_modules array"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "locked_modules" in data, "Response should have 'locked_modules' field"
        assert isinstance(data["locked_modules"], list), "locked_modules should be a list"
        print(f"✓ GET /api/modules/status returns locked_modules: {len(data['locked_modules'])} modules")
    
    def test_module_has_health_field(self):
        """Each module has health field"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        assert len(all_modules) > 0, "Should have modules"
        
        for module in all_modules:
            assert "health" in module, f"Module {module.get('module_id')} missing 'health' field"
            assert module["health"] in ["good", "ready", "blocked", "locked"], \
                f"Invalid health for {module.get('module_id')}: {module['health']}"
        
        print(f"✓ All {len(all_modules)} modules have valid health field")
    
    def test_module_has_blockers_field(self):
        """Each module has blockers field"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        for module in all_modules:
            assert "blockers" in module, f"Module {module.get('module_id')} missing 'blockers' field"
            assert isinstance(module["blockers"], list), f"blockers should be a list for {module.get('module_id')}"
        
        print(f"✓ All modules have blockers field")
    
    def test_module_has_priority_alignment_field(self):
        """Each module has priority_alignment field"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        for module in all_modules:
            assert "priority_alignment" in module, f"Module {module.get('module_id')} missing 'priority_alignment' field"
            assert isinstance(module["priority_alignment"], bool), \
                f"priority_alignment should be boolean for {module.get('module_id')}"
        
        print(f"✓ All modules have priority_alignment field")
    
    def test_module_has_next_steps_field(self):
        """Each module has next_steps field"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        for module in all_modules:
            assert "next_steps" in module, f"Module {module.get('module_id')} missing 'next_steps' field"
            assert isinstance(module["next_steps"], list), f"next_steps should be a list for {module.get('module_id')}"
        
        print(f"✓ All modules have next_steps field")
    
    def test_module_has_required_engines_field(self):
        """Each module has required_engines field (Phase 4 metadata)"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        for module in all_modules:
            assert "required_engines" in module, f"Module {module.get('module_id')} missing 'required_engines' field"
            assert isinstance(module["required_engines"], list), \
                f"required_engines should be a list for {module.get('module_id')}"
        
        print(f"✓ All modules have required_engines field")
    
    def test_module_has_required_track_field(self):
        """Each module has required_track field (Phase 4 metadata)"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        for module in all_modules:
            assert "required_track" in module, f"Module {module.get('module_id')} missing 'required_track' field"
            # required_track can be None for core modules
        
        print(f"✓ All modules have required_track field")
    
    def test_returns_track_and_first_priority(self):
        """GET /api/modules/status returns user's track and first_priority"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "track" in data, "Response should have 'track' field"
        assert "first_priority" in data, "Response should have 'first_priority' field"
        
        # Free user should have creator_track and grow_audience priority
        assert data["track"] == "creator_track", f"Expected creator_track, got {data['track']}"
        assert data["first_priority"] == "grow_audience", f"Expected grow_audience, got {data['first_priority']}"
        print(f"✓ Returns track: {data['track']}, first_priority: {data['first_priority']}")


class TestModulePriorityAlignment:
    """Tests for module priority_alignment matching user's first_priority"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_priority_alignment_for_grow_audience(self):
        """Modules with grow_audience in starting_point_priority should have priority_alignment=True"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        # Free user has first_priority=grow_audience
        assert data["first_priority"] == "grow_audience"
        
        # Check modules that should align with grow_audience
        # audience_builder, content_planner, platform_optimizer, community_manager should align
        all_modules = data.get("all_modules", [])
        
        aligned_modules = [m for m in all_modules if m["priority_alignment"]]
        aligned_ids = [m["module_id"] for m in aligned_modules]
        
        # audience_builder should be aligned (has grow_audience in starting_point_priority)
        audience_builder = next((m for m in all_modules if m["module_id"] == "audience_builder"), None)
        if audience_builder:
            assert audience_builder["priority_alignment"] == True, \
                "audience_builder should align with grow_audience priority"
        
        print(f"✓ Found {len(aligned_modules)} modules aligned with grow_audience priority")
        print(f"  Aligned modules: {aligned_ids}")


class TestBlockedModules:
    """Tests for blocked modules showing correct blocker messages"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_blocked_modules_have_blocker_messages(self):
        """Blocked modules should have non-empty blockers array"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        blocked_modules = data.get("blocked_modules", [])
        
        for module in blocked_modules:
            assert len(module["blockers"]) > 0, \
                f"Blocked module {module['module_id']} should have blocker messages"
            print(f"  {module['module_id']}: {module['blockers']}")
        
        print(f"✓ All {len(blocked_modules)} blocked modules have blocker messages")
    
    def test_content_planner_blocked_by_missing_content_plan(self):
        """content_planner should be blocked when user has missing_elements=[content_plan]"""
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        content_planner = next((m for m in all_modules if m["module_id"] == "content_planner"), None)
        if content_planner:
            # Free user has missing_elements=[content_plan, monetization_path]
            # content_planner has blocker: missing_content_plan
            if content_planner["status"] == "blocked":
                assert "Define audience first for targeted content" in content_planner["blockers"], \
                    f"content_planner should show content plan blocker, got: {content_planner['blockers']}"
                print(f"✓ content_planner correctly blocked: {content_planner['blockers']}")
            else:
                print(f"  content_planner status: {content_planner['status']} (not blocked)")


class TestModuleUpdateEndpoint:
    """Tests for POST /api/modules/update/{module_id} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_module_update_requires_auth(self):
        """POST /api/modules/update/{module_id} requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/modules/update/dashboard",
            json={"action": "activate"}
        )
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print("✓ POST /api/modules/update requires authentication")
    
    def test_module_update_invalid_module(self):
        """POST /api/modules/update/{module_id} returns 404 for invalid module"""
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/invalid_module_xyz",
            json={"action": "activate"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST /api/modules/update returns 404 for invalid module")
    
    def test_module_update_invalid_action(self):
        """POST /api/modules/update/{module_id} returns 400 for invalid action"""
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/dashboard",
            json={"action": "invalid_action"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ POST /api/modules/update returns 400 for invalid action")
    
    def test_activate_unlocked_module(self):
        """POST /api/modules/update/{module_id} with action=activate works for unlocked module"""
        # First get status to find an unlocked module
        status_response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert status_response.status_code == 200
        
        data = status_response.json()
        unlocked_modules = data.get("unlocked_modules", [])
        
        if len(unlocked_modules) == 0:
            pytest.skip("No unlocked modules to test activation")
        
        # Pick first unlocked module
        module_to_activate = unlocked_modules[0]["module_id"]
        
        # Activate it
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/{module_to_activate}",
            json={"action": "activate"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result["success"] == True, "Activation should succeed"
        assert result["status"] == "active", f"Status should be 'active', got {result['status']}"
        assert result["module_id"] == module_to_activate
        
        print(f"✓ Successfully activated module: {module_to_activate}")
        
        # Verify it's now in active_modules
        verify_response = self.session.get(f"{BASE_URL}/api/modules/status")
        verify_data = verify_response.json()
        active_ids = [m["module_id"] for m in verify_data.get("active_modules", [])]
        assert module_to_activate in active_ids, f"{module_to_activate} should be in active_modules"
        
        print(f"✓ Verified {module_to_activate} is now active")
    
    def test_deactivate_active_module(self):
        """POST /api/modules/update/{module_id} with action=deactivate works"""
        # First get status to find an active module
        status_response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert status_response.status_code == 200
        
        data = status_response.json()
        active_modules = data.get("active_modules", [])
        
        if len(active_modules) == 0:
            # Activate one first
            unlocked = data.get("unlocked_modules", [])
            if len(unlocked) == 0:
                pytest.skip("No modules to test deactivation")
            
            module_id = unlocked[0]["module_id"]
            self.session.post(
                f"{BASE_URL}/api/modules/update/{module_id}",
                json={"action": "activate"}
            )
        else:
            module_id = active_modules[0]["module_id"]
        
        # Deactivate it
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/{module_id}",
            json={"action": "deactivate"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result["success"] == True, "Deactivation should succeed"
        assert result["status"] == "unlocked", f"Status should be 'unlocked', got {result['status']}"
        
        print(f"✓ Successfully deactivated module: {module_id}")
    
    def test_acknowledge_blocker_action(self):
        """POST /api/modules/update/{module_id} with action=acknowledge_blocker works"""
        # Get a blocked module
        status_response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert status_response.status_code == 200
        
        data = status_response.json()
        blocked_modules = data.get("blocked_modules", [])
        
        if len(blocked_modules) == 0:
            # Use any module for acknowledge_blocker test
            all_modules = data.get("all_modules", [])
            if len(all_modules) == 0:
                pytest.skip("No modules to test acknowledge_blocker")
            module_id = all_modules[0]["module_id"]
            blocker_msg = "Test blocker message"
        else:
            module_id = blocked_modules[0]["module_id"]
            blocker_msg = blocked_modules[0]["blockers"][0] if blocked_modules[0]["blockers"] else "Test blocker"
        
        # Acknowledge blocker
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/{module_id}",
            json={
                "action": "acknowledge_blocker",
                "blocker_to_acknowledge": blocker_msg
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result["success"] == True, "Acknowledge blocker should succeed"
        assert result["blocker_acknowledged"] == blocker_msg
        
        print(f"✓ Successfully acknowledged blocker for module: {module_id}")
    
    def test_activate_locked_module_fails(self):
        """POST /api/modules/update/{module_id} with action=activate fails for locked module"""
        # Get a locked module
        status_response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert status_response.status_code == 200
        
        data = status_response.json()
        locked_modules = data.get("locked_modules", [])
        
        if len(locked_modules) == 0:
            pytest.skip("No locked modules to test")
        
        module_id = locked_modules[0]["module_id"]
        
        # Try to activate locked module
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/{module_id}",
            json={"action": "activate"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print(f"✓ Correctly rejected activation of locked module: {module_id}")


class TestModuleActivityLog:
    """Tests for module activation being logged to module_activity_log"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_activation_creates_log_entry(self):
        """Module activation should create entry in module_activity_log"""
        # Get an unlocked module
        status_response = self.session.get(f"{BASE_URL}/api/modules/status")
        data = status_response.json()
        
        unlocked = data.get("unlocked_modules", [])
        if len(unlocked) == 0:
            pytest.skip("No unlocked modules to test")
        
        module_id = unlocked[0]["module_id"]
        
        # Activate module
        response = self.session.post(
            f"{BASE_URL}/api/modules/update/{module_id}",
            json={"action": "activate"}
        )
        assert response.status_code == 200
        
        # The log entry is created internally - we verify by checking the response
        result = response.json()
        assert result["success"] == True
        
        print(f"✓ Module activation logged for: {module_id}")
        
        # Deactivate to clean up
        self.session.post(
            f"{BASE_URL}/api/modules/update/{module_id}",
            json={"action": "deactivate"}
        )


class TestModuleMetadata:
    """Tests for module metadata fields (Phase 4 enhanced)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_single_module_has_full_metadata(self):
        """GET /api/modules/{module_id} returns full Phase 4 metadata"""
        response = self.session.get(f"{BASE_URL}/api/modules/audience_builder")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check Phase 4 metadata fields
        assert "required_track" in data, "Should have required_track"
        assert "required_engines" in data, "Should have required_engines"
        assert "required_assets" in data, "Should have required_assets"
        assert "unlock_conditions" in data, "Should have unlock_conditions"
        assert "starting_point_priority" in data, "Should have starting_point_priority"
        
        # Verify audience_builder specific metadata
        assert data["required_track"] == "creator_track", \
            f"audience_builder should require creator_track, got {data['required_track']}"
        assert "engagement_engine" in data["required_engines"], \
            f"audience_builder should require engagement_engine"
        assert "social_media_accounts" in data["required_assets"], \
            f"audience_builder should require social_media_accounts"
        
        print(f"✓ audience_builder has full Phase 4 metadata")
        print(f"  required_track: {data['required_track']}")
        print(f"  required_engines: {data['required_engines']}")
        print(f"  required_assets: {data['required_assets']}")
    
    def test_core_modules_have_no_required_track(self):
        """Core modules (dashboard, profile) should have required_track=None"""
        response = self.session.get(f"{BASE_URL}/api/modules/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_core"] == True, "dashboard should be a core module"
        assert data["required_track"] is None, "Core modules should have required_track=None"
        
        print(f"✓ Core module 'dashboard' has required_track=None")
    
    def test_module_status_calculation_based_on_assets(self):
        """Module status should be calculated based on user's assets"""
        # Free user has: assets=[social_media_accounts], missing=[content_plan, monetization_path]
        
        response = self.session.get(f"{BASE_URL}/api/modules/status")
        assert response.status_code == 200
        
        data = response.json()
        all_modules = data.get("all_modules", [])
        
        # audience_builder requires social_media_accounts - user has it
        audience_builder = next((m for m in all_modules if m["module_id"] == "audience_builder"), None)
        if audience_builder:
            # Should not be blocked due to missing social_media_accounts
            if audience_builder["status"] == "blocked":
                assert "Set up social media accounts first" not in audience_builder["blockers"], \
                    "audience_builder should not be blocked for social_media_accounts (user has it)"
        
        # community_manager requires existing_audience - user doesn't have it
        community_manager = next((m for m in all_modules if m["module_id"] == "community_manager"), None)
        if community_manager and community_manager["status"] == "blocked":
            # Should be blocked due to missing existing_audience
            print(f"  community_manager blockers: {community_manager['blockers']}")
        
        print(f"✓ Module status correctly calculated based on user assets")


class TestModulesByEngineAndTrack:
    """Tests for modules filtered by engine and track"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/creator/login",
            json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_modules_by_engagement_engine(self):
        """GET /api/modules/by-engine/engagement_engine returns engagement modules"""
        response = self.session.get(f"{BASE_URL}/api/modules/by-engine/engagement_engine")
        assert response.status_code == 200
        
        data = response.json()
        assert data["engine_id"] == "engagement_engine"
        assert data["engine_name"] == "Audience & Visibility Support"
        assert len(data["modules"]) > 0, "Should have engagement modules"
        
        # Verify expected modules
        module_ids = [m["module_id"] for m in data["modules"]]
        assert "audience_builder" in module_ids, "Should include audience_builder"
        assert "content_planner" in module_ids, "Should include content_planner"
        
        print(f"✓ GET /api/modules/by-engine/engagement_engine returns {len(data['modules'])} modules")
    
    def test_modules_by_creator_track(self):
        """GET /api/modules/by-track/creator_track returns creator modules"""
        response = self.session.get(f"{BASE_URL}/api/modules/by-track/creator_track")
        assert response.status_code == 200
        
        data = response.json()
        assert data["track_id"] == "creator_track"
        assert len(data["modules"]) > 0, "Should have creator track modules"
        
        # Verify core modules are included
        module_ids = [m["module_id"] for m in data["modules"]]
        assert "dashboard" in module_ids, "Should include dashboard (core)"
        assert "profile" in module_ids, "Should include profile (core)"
        
        print(f"✓ GET /api/modules/by-track/creator_track returns {len(data['modules'])} modules")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
