"""
Phase 2 Backend Tests: Engine and Module Management APIs
=========================================================
Tests for:
- GET /api/engines - List all 4 engines with display names
- GET /api/engines/{engine_id} - Get single engine with config info
- POST /api/engines/{engine_id}/progress - Update engine progress
- GET /api/engines/summary/overview - Get high-level engine summary
- GET /api/modules - List all modules with unlock status
- GET /api/modules/unlocked - List only unlocked modules
- GET /api/modules/{module_id} - Get single module details
- POST /api/modules/{module_id}/activate - Activate a module
- POST /api/modules/{module_id}/deactivate - Deactivate a module
- GET /api/modules/by-engine/{engine_id} - Get modules by engine
- GET /api/modules/by-track/{track_id} - Get modules by track
- Track assignment and module unlocking logic
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
FREE_USER = {"email": "freetest@hivehq.com", "password": "testpassword"}
PRO_USER = {"email": "protest@hivehq.com", "password": "testpassword"}
ELITE_USER = {"email": "elitetest@hivehq.com", "password": "testpassword123"}

# Engine display names mapping
ENGINE_DISPLAY_NAMES = {
    "business_engine": "Business Support",
    "engagement_engine": "Audience & Visibility Support",
    "role_engine": "Creator Identity Support",
    "income_engine": "Monetization Support"
}

# Valid engine IDs
VALID_ENGINE_IDS = ["business_engine", "engagement_engine", "role_engine", "income_engine"]

# Valid track IDs
VALID_TRACK_IDS = ["creator_track", "business_track", "hybrid_track"]


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def free_user_token(api_client):
    """Get authentication token for free tier user (has completed intake as creator)"""
    response = api_client.post(
        f"{BASE_URL}/api/creators/login",
        json=FREE_USER
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Free user authentication failed")


@pytest.fixture(scope="module")
def authenticated_client(api_client, free_user_token):
    """Session with auth header for free user"""
    api_client.headers.update({"Authorization": f"Bearer {free_user_token}"})
    return api_client


class TestEngineEndpoints:
    """Tests for /api/engines endpoints"""
    
    def test_list_engines_requires_auth(self, api_client):
        """GET /api/engines requires authentication"""
        # Remove auth header temporarily
        auth_header = api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/engines")
        # Restore auth header
        if auth_header:
            api_client.headers["Authorization"] = auth_header
        assert response.status_code == 403
    
    def test_list_engines_returns_all_four(self, authenticated_client):
        """GET /api/engines returns all 4 engines"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines")
        assert response.status_code == 200
        
        data = response.json()
        assert "engines" in data
        assert "summary" in data
        
        # Should have 4 engines
        engines = data["engines"]
        assert len(engines) == 4
        
        # Verify all engine IDs present
        engine_ids = [e["engine_id"] for e in engines]
        for expected_id in VALID_ENGINE_IDS:
            assert expected_id in engine_ids
    
    def test_list_engines_has_display_names(self, authenticated_client):
        """GET /api/engines returns correct display names (no 'Engine' word)"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines")
        assert response.status_code == 200
        
        data = response.json()
        engines = data["engines"]
        
        for engine in engines:
            engine_id = engine["engine_id"]
            expected_name = ENGINE_DISPLAY_NAMES.get(engine_id)
            assert engine["display_name"] == expected_name, f"Engine {engine_id} has wrong display name"
            # Verify 'Engine' word is not in display name
            assert "Engine" not in engine["display_name"]
    
    def test_list_engines_has_summary(self, authenticated_client):
        """GET /api/engines returns summary with status counts"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines")
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        assert "total" in summary
        assert "active" in summary
        assert "pending" in summary
        assert "blocked" in summary
        assert "inactive" in summary
        assert summary["total"] == 4
    
    def test_get_single_engine_valid(self, authenticated_client):
        """GET /api/engines/{engine_id} returns engine details"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines/engagement_engine")
        assert response.status_code == 200
        
        data = response.json()
        assert data["engine_id"] == "engagement_engine"
        assert data["display_name"] == "Audience & Visibility Support"
        assert "status" in data
        assert "progress" in data
        assert "config" in data
        
        # Verify config structure
        config = data["config"]
        assert "inputs" in config
        assert "outputs" in config
        assert "dependencies" in config
        assert "required_modules" in config
    
    def test_get_single_engine_invalid(self, authenticated_client):
        """GET /api/engines/{engine_id} returns 400 for invalid engine"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines/invalid_engine")
        assert response.status_code == 400
        assert "Invalid engine_id" in response.json().get("detail", "")
    
    def test_get_engine_summary_overview(self, authenticated_client):
        """GET /api/engines/summary/overview returns high-level summary"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines/summary/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert data["initialized"] == True
        assert "total_engines" in data
        assert "active_count" in data
        assert "blocked_count" in data
        assert "average_progress" in data
        assert "engines_by_status" in data
        
        # Verify engines_by_status structure
        by_status = data["engines_by_status"]
        assert "active" in by_status
        assert "blocked" in by_status
        assert "pending" in by_status
        assert "inactive" in by_status
    
    def test_update_engine_progress(self, authenticated_client):
        """POST /api/engines/{engine_id}/progress updates progress"""
        # Update progress for engagement_engine (which is active for free user)
        response = authenticated_client.post(
            f"{BASE_URL}/api/engines/engagement_engine/progress",
            json={"progress": 30.0, "inputs_received": 1, "outputs_generated": 0}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["engine_id"] == "engagement_engine"
        assert data["progress"] == 30.0
        
        # Verify progress persisted
        get_response = authenticated_client.get(f"{BASE_URL}/api/engines/engagement_engine")
        assert get_response.status_code == 200
        assert get_response.json()["progress"] == 30.0
    
    def test_update_engine_progress_invalid_engine(self, authenticated_client):
        """POST /api/engines/{engine_id}/progress returns 400 for invalid engine"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/engines/invalid_engine/progress",
            json={"progress": 50.0}
        )
        assert response.status_code == 400


class TestModuleEndpoints:
    """Tests for /api/modules endpoints"""
    
    def test_list_modules_requires_auth(self, api_client):
        """GET /api/modules requires authentication"""
        auth_header = api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/modules")
        if auth_header:
            api_client.headers["Authorization"] = auth_header
        assert response.status_code == 403
    
    def test_list_modules_returns_all(self, authenticated_client):
        """GET /api/modules returns all modules with unlock status"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        
        data = response.json()
        assert "modules" in data
        assert "total_modules" in data
        assert "unlocked_count" in data
        assert "active_count" in data
        assert "user_track" in data
        
        # Should have 18 total modules
        assert data["total_modules"] == 18
        
        # Verify module structure
        for module in data["modules"]:
            assert "module_id" in module
            assert "name" in module
            assert "is_unlocked" in module
            assert "is_active" in module
            assert "tracks" in module
    
    def test_list_unlocked_modules(self, authenticated_client):
        """GET /api/modules/unlocked returns only unlocked modules"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/unlocked")
        assert response.status_code == 200
        
        data = response.json()
        assert "modules" in data
        assert "unlocked_count" in data
        assert "track" in data
        
        # Free user (creator track with engagement + income engines) should have 9 modules
        assert data["unlocked_count"] == 9
        
        # Verify all returned modules are unlocked
        for module in data["modules"]:
            # All modules in this list should be unlocked (implicit)
            assert "module_id" in module
            assert "name" in module
    
    def test_get_single_module_valid(self, authenticated_client):
        """GET /api/modules/{module_id} returns module details"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/audience_builder")
        assert response.status_code == 200
        
        data = response.json()
        assert data["module_id"] == "audience_builder"
        assert data["name"] == "Audience Builder"
        assert "is_unlocked" in data
        assert "is_active" in data
        assert "tracks" in data
        assert "engines" in data
        
        # audience_builder should be unlocked for creator track with engagement engine
        assert data["is_unlocked"] == True
    
    def test_get_single_module_invalid(self, authenticated_client):
        """GET /api/modules/{module_id} returns 404 for invalid module"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/invalid_module")
        assert response.status_code == 404
    
    def test_activate_module(self, authenticated_client):
        """POST /api/modules/{module_id}/activate activates a module"""
        # First ensure module is deactivated
        authenticated_client.post(f"{BASE_URL}/api/modules/content_planner/deactivate")
        
        # Activate the module
        response = authenticated_client.post(f"{BASE_URL}/api/modules/content_planner/activate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["module_id"] == "content_planner"
        assert data["is_active"] == True
        assert "content_planner" in data["active_modules"]
        
        # Verify activation persisted
        get_response = authenticated_client.get(f"{BASE_URL}/api/modules/content_planner")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == True
    
    def test_activate_locked_module_fails(self, authenticated_client):
        """POST /api/modules/{module_id}/activate fails for locked module"""
        # business_model_canvas is not unlocked for creator track
        response = authenticated_client.post(f"{BASE_URL}/api/modules/business_model_canvas/activate")
        assert response.status_code == 403
        assert "not unlocked" in response.json().get("detail", "").lower()
    
    def test_deactivate_module(self, authenticated_client):
        """POST /api/modules/{module_id}/deactivate deactivates a module"""
        # First activate the module
        authenticated_client.post(f"{BASE_URL}/api/modules/content_planner/activate")
        
        # Deactivate the module
        response = authenticated_client.post(f"{BASE_URL}/api/modules/content_planner/deactivate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["module_id"] == "content_planner"
        assert data["is_active"] == False
        
        # Verify deactivation persisted
        get_response = authenticated_client.get(f"{BASE_URL}/api/modules/content_planner")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] == False
    
    def test_get_modules_by_engine(self, authenticated_client):
        """GET /api/modules/by-engine/{engine_id} returns modules for engine"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/by-engine/engagement_engine")
        assert response.status_code == 200
        
        data = response.json()
        assert data["engine_id"] == "engagement_engine"
        assert data["engine_name"] == "Audience & Visibility Support"
        assert "modules" in data
        assert "total" in data
        assert "unlocked" in data
        
        # Engagement engine has 4 modules
        assert data["total"] == 4
        
        # Verify module IDs
        module_ids = [m["module_id"] for m in data["modules"]]
        assert "audience_builder" in module_ids
        assert "content_planner" in module_ids
        assert "platform_optimizer" in module_ids
        assert "community_manager" in module_ids
    
    def test_get_modules_by_engine_invalid(self, authenticated_client):
        """GET /api/modules/by-engine/{engine_id} returns 400 for invalid engine"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/by-engine/invalid_engine")
        assert response.status_code == 400
    
    def test_get_modules_by_track(self, authenticated_client):
        """GET /api/modules/by-track/{track_id} returns modules for track"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/by-track/creator_track")
        assert response.status_code == 200
        
        data = response.json()
        assert data["track_id"] == "creator_track"
        assert data["track_name"] == "Creator Track"
        assert "modules" in data
        assert "total" in data
        assert "unlocked" in data
        
        # Creator track has 9 modules available
        assert data["total"] == 9
        
        # Verify core modules are included
        module_ids = [m["module_id"] for m in data["modules"]]
        assert "dashboard" in module_ids
        assert "profile" in module_ids
    
    def test_get_modules_by_track_invalid(self, authenticated_client):
        """GET /api/modules/by-track/{track_id} returns 400 for invalid track"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/by-track/invalid_track")
        assert response.status_code == 400


class TestTrackAssignment:
    """Tests for track assignment logic"""
    
    def test_creator_track_assignment(self, authenticated_client):
        """Creator identity type assigns to creator_track"""
        # Free user has identity_type=creator
        response = authenticated_client.get(f"{BASE_URL}/api/intake/system-state")
        assert response.status_code == 200
        
        data = response.json()
        assert data["identity_type"] == "creator"
        assert data["assigned_track"] == "creator_track"
    
    def test_creator_track_modules(self, authenticated_client):
        """Creator track unlocks correct modules"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules/unlocked")
        assert response.status_code == 200
        
        data = response.json()
        module_ids = [m["module_id"] for m in data["modules"]]
        
        # Core modules always unlocked
        assert "dashboard" in module_ids
        assert "profile" in module_ids
        
        # Engagement engine modules (selected by free user)
        assert "audience_builder" in module_ids
        assert "content_planner" in module_ids
        assert "platform_optimizer" in module_ids
        assert "community_manager" in module_ids
        
        # Income engine modules (selected by free user)
        assert "revenue_tracker" in module_ids
        assert "pricing_optimizer" in module_ids
        assert "financial_dashboard" in module_ids
        
        # Business engine modules should NOT be unlocked
        assert "business_model_canvas" not in module_ids
        assert "market_research" not in module_ids


class TestEngineActivation:
    """Tests for engine activation based on intake selections"""
    
    def test_selected_engines_are_active(self, authenticated_client):
        """Selected engines from intake are active or pending"""
        # Free user selected engagement_engine and income_engine
        response = authenticated_client.get(f"{BASE_URL}/api/engines")
        assert response.status_code == 200
        
        data = response.json()
        engines = {e["engine_id"]: e for e in data["engines"]}
        
        # Engagement engine should be active (no dependencies)
        assert engines["engagement_engine"]["status"] == "active"
        
        # Income engine should be pending (depends on business + engagement)
        assert engines["income_engine"]["status"] == "pending"
        
        # Business engine should be inactive (not selected)
        assert engines["business_engine"]["status"] == "inactive"
        
        # Role engine should be inactive (not selected, depends on business)
        assert engines["role_engine"]["status"] == "inactive"
    
    def test_engine_dependencies_tracked(self, authenticated_client):
        """Engine dependencies are properly tracked"""
        response = authenticated_client.get(f"{BASE_URL}/api/engines")
        assert response.status_code == 200
        
        data = response.json()
        engines = {e["engine_id"]: e for e in data["engines"]}
        
        # Engagement engine has no dependencies
        assert engines["engagement_engine"]["dependencies_met"] == True
        assert engines["engagement_engine"]["blockers"] == []
        
        # Income engine depends on business + engagement
        # Since business is not selected, dependencies not met
        assert engines["income_engine"]["dependencies_met"] == False
        assert len(engines["income_engine"]["blockers"]) > 0


class TestModuleUnlocking:
    """Tests for module unlocking based on track + engines"""
    
    def test_core_modules_always_unlocked(self, authenticated_client):
        """Core modules (dashboard, profile) are always unlocked"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        
        data = response.json()
        modules = {m["module_id"]: m for m in data["modules"]}
        
        assert modules["dashboard"]["is_unlocked"] == True
        assert modules["dashboard"]["is_core"] == True
        
        assert modules["profile"]["is_unlocked"] == True
        assert modules["profile"]["is_core"] == True
    
    def test_engine_modules_unlocked_when_engine_selected(self, authenticated_client):
        """Modules for selected engines are unlocked"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        
        data = response.json()
        modules = {m["module_id"]: m for m in data["modules"]}
        
        # Engagement engine modules should be unlocked
        assert modules["audience_builder"]["is_unlocked"] == True
        assert modules["content_planner"]["is_unlocked"] == True
        
        # Income engine modules should be unlocked
        assert modules["revenue_tracker"]["is_unlocked"] == True
        assert modules["pricing_optimizer"]["is_unlocked"] == True
    
    def test_unselected_engine_modules_locked(self, authenticated_client):
        """Modules for unselected engines are locked"""
        response = authenticated_client.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        
        data = response.json()
        modules = {m["module_id"]: m for m in data["modules"]}
        
        # Business engine modules should be locked (not selected)
        assert modules["business_model_canvas"]["is_unlocked"] == False
        assert modules["market_research"]["is_unlocked"] == False
        
        # Role engine modules should be locked (not selected)
        assert modules["role_definer"]["is_unlocked"] == False
        assert modules["team_builder"]["is_unlocked"] == False


class TestCommandCenterIntegration:
    """Tests for command center showing correct engine and module counts"""
    
    def test_command_center_engine_count(self, authenticated_client):
        """Command center shows correct engine counts"""
        response = authenticated_client.get(f"{BASE_URL}/api/command-center")
        assert response.status_code == 200
        
        data = response.json()
        assert "engines_active" in data
        assert "modules_unlocked" in data
        
        # Free user has 1 active engine (engagement) and 1 pending (income)
        # engines_active counts only ACTIVE status
        assert data["engines_active"] >= 1
    
    def test_command_center_module_count(self, authenticated_client):
        """Command center shows correct module counts"""
        response = authenticated_client.get(f"{BASE_URL}/api/command-center")
        assert response.status_code == 200
        
        data = response.json()
        
        # Free user has 9 modules unlocked
        assert data["modules_unlocked"] == 9


# Cleanup fixture to reset test state
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_state(authenticated_client):
    """Reset engine progress after tests"""
    yield
    # Reset engagement engine progress to 0
    try:
        authenticated_client.post(
            f"{BASE_URL}/api/engines/engagement_engine/progress",
            json={"progress": 0.0, "inputs_received": 0, "outputs_generated": 0}
        )
    except:
        pass
