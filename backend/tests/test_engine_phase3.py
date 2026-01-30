"""
Creators Hive HQ - Phase 3 Engine Restoration Tests
====================================================
Tests for the new engine endpoints:
- GET /api/engines/status - Comprehensive status of all engines
- GET /api/engines/{engine_id}/details - Full engine configuration

Test credentials:
- freetest@hivehq.com / testpassword (creator track, engagement+income engines)
- protest@hivehq.com / testpassword (pro tier)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
FREE_USER = {"email": "freetest@hivehq.com", "password": "testpassword"}
PRO_USER = {"email": "protest@hivehq.com", "password": "testpassword"}

# Engine IDs
ENGINE_IDS = ["business_engine", "engagement_engine", "role_engine", "income_engine"]

# Expected display names (using 'Support' instead of 'Engine')
ENGINE_DISPLAY_NAMES = {
    "business_engine": "Business Support",
    "engagement_engine": "Audience & Visibility Support",
    "role_engine": "Creator Identity Support",
    "income_engine": "Monetization Support"
}


class TestSetup:
    """Setup and authentication helpers"""
    
    @staticmethod
    def get_creator_token(email, password):
        """Get authentication token for creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            # Try both 'access_token' and 'token' keys
            return data.get("access_token") or data.get("token")
        return None


@pytest.fixture(scope="module")
def free_user_token():
    """Get token for free tier creator"""
    token = TestSetup.get_creator_token(FREE_USER["email"], FREE_USER["password"])
    if not token:
        pytest.skip("Could not authenticate free tier user")
    return token


@pytest.fixture(scope="module")
def pro_user_token():
    """Get token for pro tier creator"""
    token = TestSetup.get_creator_token(PRO_USER["email"], PRO_USER["password"])
    if not token:
        pytest.skip("Could not authenticate pro tier user")
    return token


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ============== GET /api/engines/status TESTS ==============

class TestEnginesStatus:
    """Tests for GET /api/engines/status endpoint"""
    
    def test_engines_status_requires_auth(self, api_client):
        """GET /api/engines/status - Requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/engines/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/engines/status requires authentication")
    
    def test_engines_status_returns_initialized(self, api_client, free_user_token):
        """GET /api/engines/status - Returns initialized=True for user with engines"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify initialized flag
        assert "initialized" in data, "Response should contain 'initialized' field"
        assert data["initialized"] == True, "Engines should be initialized for test user"
        print("✓ GET /api/engines/status returns initialized=True")
    
    def test_engines_status_returns_overall_health(self, api_client, free_user_token):
        """GET /api/engines/status - Returns overall_health indicator"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify overall_health field
        assert "overall_health" in data, "Response should contain 'overall_health' field"
        valid_health_values = ["good", "has_blockers", "no_active_engines", "low_progress"]
        assert data["overall_health"] in valid_health_values, f"Invalid overall_health: {data['overall_health']}"
        print(f"✓ GET /api/engines/status returns overall_health: {data['overall_health']}")
    
    def test_engines_status_returns_summary(self, api_client, free_user_token):
        """GET /api/engines/status - Returns summary with active/pending/blocked/inactive counts"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "summary" in data, "Response should contain 'summary' field"
        summary = data["summary"]
        
        required_fields = ["total", "active", "pending", "blocked", "inactive", "average_progress"]
        for field in required_fields:
            assert field in summary, f"Summary should contain '{field}' field"
        
        # Verify counts are integers
        assert isinstance(summary["total"], int), "total should be integer"
        assert isinstance(summary["active"], int), "active should be integer"
        assert isinstance(summary["pending"], int), "pending should be integer"
        assert isinstance(summary["blocked"], int), "blocked should be integer"
        assert isinstance(summary["inactive"], int), "inactive should be integer"
        
        # Verify total equals sum of statuses
        total_statuses = summary["active"] + summary["pending"] + summary["blocked"] + summary["inactive"]
        assert summary["total"] == total_statuses, f"Total ({summary['total']}) should equal sum of statuses ({total_statuses})"
        
        print(f"✓ GET /api/engines/status returns summary: {summary}")
    
    def test_engines_status_returns_engines_list(self, api_client, free_user_token):
        """GET /api/engines/status - Returns list of engines with required fields"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify engines list
        assert "engines" in data, "Response should contain 'engines' field"
        engines = data["engines"]
        assert isinstance(engines, list), "engines should be a list"
        assert len(engines) == 4, f"Should have 4 engines, got {len(engines)}"
        
        # Verify each engine has required fields
        required_fields = [
            "engine_id", "display_name", "description", "status", "health",
            "warnings", "progress", "inputs", "outputs", "blockers",
            "dependencies", "last_activity"
        ]
        
        for engine in engines:
            for field in required_fields:
                assert field in engine, f"Engine should contain '{field}' field"
        
        print(f"✓ GET /api/engines/status returns {len(engines)} engines with all required fields")
    
    def test_engines_status_health_and_warnings(self, api_client, free_user_token):
        """GET /api/engines/status - Each engine has health status and warnings"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_health_values = ["good", "pending", "blocked", "needs_attention", "inactive"]
        
        for engine in data["engines"]:
            # Verify health field
            assert "health" in engine, f"Engine {engine['engine_id']} should have 'health' field"
            assert engine["health"] in valid_health_values, f"Invalid health value: {engine['health']}"
            
            # Verify warnings is a list
            assert "warnings" in engine, f"Engine {engine['engine_id']} should have 'warnings' field"
            assert isinstance(engine["warnings"], list), "warnings should be a list"
            
            print(f"  - {engine['engine_id']}: health={engine['health']}, warnings={engine['warnings']}")
        
        print("✓ All engines have valid health status and warnings")
    
    def test_engines_status_display_names(self, api_client, free_user_token):
        """GET /api/engines/status - Display names use 'Support' instead of 'Engine'"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for engine in data["engines"]:
            engine_id = engine["engine_id"]
            expected_name = ENGINE_DISPLAY_NAMES.get(engine_id)
            if expected_name:
                assert engine["display_name"] == expected_name, \
                    f"Expected display_name '{expected_name}', got '{engine['display_name']}'"
                print(f"  - {engine_id}: {engine['display_name']} ✓")
        
        print("✓ All engine display names use 'Support' naming convention")
    
    def test_engines_status_inputs_outputs_structure(self, api_client, free_user_token):
        """GET /api/engines/status - Inputs and outputs have correct structure"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for engine in data["engines"]:
            # Verify inputs structure
            assert "inputs" in engine
            inputs = engine["inputs"]
            assert "received" in inputs, "inputs should have 'received' count"
            assert "required" in inputs, "inputs should have 'required' list"
            assert "total_types" in inputs, "inputs should have 'total_types' count"
            
            # Verify outputs structure
            assert "outputs" in engine
            outputs = engine["outputs"]
            assert "generated" in outputs, "outputs should have 'generated' count"
            assert "available" in outputs, "outputs should have 'available' list"
            
            print(f"  - {engine['engine_id']}: inputs={inputs['received']}/{inputs['total_types']}, outputs={outputs['generated']}")
        
        print("✓ All engines have correct inputs/outputs structure")
    
    def test_engines_status_dependencies_structure(self, api_client, free_user_token):
        """GET /api/engines/status - Dependencies have required and met fields"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/status",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for engine in data["engines"]:
            assert "dependencies" in engine
            deps = engine["dependencies"]
            assert "required" in deps, "dependencies should have 'required' list"
            assert "met" in deps, "dependencies should have 'met' boolean"
            assert isinstance(deps["required"], list), "required should be a list"
            assert isinstance(deps["met"], bool), "met should be a boolean"
            
            print(f"  - {engine['engine_id']}: deps_required={deps['required']}, deps_met={deps['met']}")
        
        print("✓ All engines have correct dependencies structure")


# ============== GET /api/engines/{engine_id}/details TESTS ==============

class TestEngineDetails:
    """Tests for GET /api/engines/{engine_id}/details endpoint"""
    
    def test_engine_details_requires_auth(self, api_client):
        """GET /api/engines/{engine_id}/details - Requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/engines/engagement_engine/details")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/engines/{engine_id}/details requires authentication")
    
    def test_engine_details_invalid_engine_id(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns 400 for invalid engine_id"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/invalid_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ GET /api/engines/invalid_engine/details returns 400")
    
    def test_engine_details_returns_full_config(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns full engine configuration"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify top-level fields
        required_fields = [
            "engine_id", "display_name", "description", "state", "health",
            "inputs", "outputs", "rules", "dependencies", "modules"
        ]
        for field in required_fields:
            assert field in data, f"Response should contain '{field}' field"
        
        assert data["engine_id"] == "engagement_engine"
        assert data["display_name"] == "Audience & Visibility Support"
        print("✓ GET /api/engines/engagement_engine/details returns full configuration")
    
    def test_engine_details_inputs_completion(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns inputs completion status"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify inputs structure
        assert "inputs" in data
        inputs = data["inputs"]
        assert "required" in inputs, "inputs should have 'required' list"
        assert "completion" in inputs, "inputs should have 'completion' list"
        assert "recent" in inputs, "inputs should have 'recent' list"
        
        # Verify completion items have correct structure
        if inputs["completion"]:
            for item in inputs["completion"]:
                assert "input_type" in item, "completion item should have 'input_type'"
                assert "received" in item, "completion item should have 'received' boolean"
                assert "label" in item, "completion item should have 'label'"
        
        print(f"✓ Engine details returns inputs completion: {len(inputs['completion'])} input types")
    
    def test_engine_details_outputs_availability(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns outputs availability"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify outputs structure
        assert "outputs" in data
        outputs = data["outputs"]
        assert "available" in outputs, "outputs should have 'available' list"
        assert "availability" in outputs, "outputs should have 'availability' list"
        assert "recent" in outputs, "outputs should have 'recent' list"
        
        # Verify availability items have correct structure
        if outputs["availability"]:
            for item in outputs["availability"]:
                assert "output_type" in item, "availability item should have 'output_type'"
                assert "generated" in item, "availability item should have 'generated' boolean"
                assert "label" in item, "availability item should have 'label'"
        
        print(f"✓ Engine details returns outputs availability: {len(outputs['availability'])} output types")
    
    def test_engine_details_rules_with_status(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns rules with status"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify rules structure
        assert "rules" in data
        rules = data["rules"]
        assert "definitions" in rules, "rules should have 'definitions' list"
        assert "status" in rules, "rules should have 'status' list"
        
        # Verify rule status items have correct structure
        if rules["status"]:
            for item in rules["status"]:
                assert "rule" in item, "rule status item should have 'rule'"
                assert "status" in item, "rule status item should have 'status'"
                assert item["status"] in ["met", "pending"], f"Invalid rule status: {item['status']}"
        
        print(f"✓ Engine details returns rules with status: {len(rules['status'])} rules")
    
    def test_engine_details_dependencies_display_names(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns dependencies with display names"""
        # Test income_engine which has dependencies
        response = api_client.get(
            f"{BASE_URL}/api/engines/income_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify dependencies structure
        assert "dependencies" in data
        deps = data["dependencies"]
        assert "required" in deps, "dependencies should have 'required' list"
        assert "met" in deps, "dependencies should have 'met' boolean"
        assert "display_names" in deps, "dependencies should have 'display_names' list"
        
        # Income engine depends on business_engine and engagement_engine
        assert len(deps["required"]) >= 1, "income_engine should have dependencies"
        assert len(deps["display_names"]) == len(deps["required"]), \
            "display_names count should match required count"
        
        print(f"✓ Engine details returns dependencies with display names: {deps['display_names']}")
    
    def test_engine_details_connected_modules(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns connected modules"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify modules structure
        assert "modules" in data
        modules = data["modules"]
        assert "required" in modules, "modules should have 'required' list"
        assert "count" in modules, "modules should have 'count'"
        
        # Engagement engine should have 4 modules
        expected_modules = ["audience_builder", "content_planner", "platform_optimizer", "community_manager"]
        assert modules["count"] == len(expected_modules), \
            f"Expected {len(expected_modules)} modules, got {modules['count']}"
        
        for module in expected_modules:
            assert module in modules["required"], f"Module '{module}' should be in required modules"
        
        print(f"✓ Engine details returns connected modules: {modules['required']}")
    
    def test_engine_details_state_structure(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns state with all fields"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify state structure
        assert "state" in data
        state = data["state"]
        required_state_fields = [
            "status", "progress", "inputs_received", "outputs_generated",
            "blockers", "dependencies_met", "last_activity"
        ]
        for field in required_state_fields:
            assert field in state, f"state should have '{field}' field"
        
        # Verify status is valid
        valid_statuses = ["active", "pending", "blocked", "inactive"]
        assert state["status"] in valid_statuses, f"Invalid status: {state['status']}"
        
        print(f"✓ Engine details returns state: status={state['status']}, progress={state['progress']}")
    
    def test_engine_details_health_structure(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Returns health with status, notes, indicators"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify health structure
        assert "health" in data
        health = data["health"]
        assert "status" in health, "health should have 'status'"
        assert "notes" in health, "health should have 'notes' list"
        assert "indicators" in health, "health should have 'indicators' list"
        
        valid_health_statuses = ["good", "pending", "blocked", "needs_attention", "inactive"]
        assert health["status"] in valid_health_statuses, f"Invalid health status: {health['status']}"
        
        print(f"✓ Engine details returns health: status={health['status']}, notes={health['notes']}")
    
    def test_all_engines_details(self, api_client, free_user_token):
        """GET /api/engines/{engine_id}/details - Works for all 4 engines"""
        for engine_id in ENGINE_IDS:
            response = api_client.get(
                f"{BASE_URL}/api/engines/{engine_id}/details",
                headers={"Authorization": f"Bearer {free_user_token}"}
            )
            assert response.status_code == 200, f"Failed for {engine_id}: {response.status_code}"
            data = response.json()
            assert data["engine_id"] == engine_id
            assert data["display_name"] == ENGINE_DISPLAY_NAMES[engine_id]
            print(f"  - {engine_id}: {data['display_name']} ✓")
        
        print("✓ All 4 engines return valid details")


# ============== ENGINE DEPENDENCIES TESTS ==============

class TestEngineDependencies:
    """Tests for engine dependency enforcement"""
    
    def test_role_engine_depends_on_business(self, api_client, free_user_token):
        """Role engine depends on business_engine"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/role_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Role engine should depend on business_engine
        deps = data["dependencies"]
        assert "business_engine" in deps["required"], \
            "role_engine should depend on business_engine"
        
        print(f"✓ role_engine depends on: {deps['required']}")
    
    def test_income_engine_dependencies(self, api_client, free_user_token):
        """Income engine depends on business_engine and engagement_engine"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/income_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Income engine should depend on business_engine and engagement_engine
        deps = data["dependencies"]
        assert "business_engine" in deps["required"], \
            "income_engine should depend on business_engine"
        assert "engagement_engine" in deps["required"], \
            "income_engine should depend on engagement_engine"
        
        print(f"✓ income_engine depends on: {deps['required']}")
    
    def test_business_engine_no_dependencies(self, api_client, free_user_token):
        """Business engine has no dependencies"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/business_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        deps = data["dependencies"]
        assert len(deps["required"]) == 0, \
            f"business_engine should have no dependencies, got: {deps['required']}"
        
        print("✓ business_engine has no dependencies")
    
    def test_engagement_engine_no_dependencies(self, api_client, free_user_token):
        """Engagement engine has no dependencies"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        deps = data["dependencies"]
        assert len(deps["required"]) == 0, \
            f"engagement_engine should have no dependencies, got: {deps['required']}"
        
        print("✓ engagement_engine has no dependencies")


# ============== ENGINE PROGRESS UPDATE TESTS ==============

class TestEngineProgressUpdate:
    """Tests for engine progress updates"""
    
    def test_update_engine_progress(self, api_client, free_user_token):
        """POST /api/engines/{engine_id}/progress - Updates progress correctly"""
        # Update progress for engagement_engine
        response = api_client.post(
            f"{BASE_URL}/api/engines/engagement_engine/progress",
            headers={"Authorization": f"Bearer {free_user_token}"},
            json={"progress": 50.0, "inputs_received": 1, "outputs_generated": 0}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert data["engine_id"] == "engagement_engine"
        assert data["progress"] == 50.0
        
        print(f"✓ Engine progress updated: {data}")
    
    def test_verify_progress_persisted(self, api_client, free_user_token):
        """Verify progress update is persisted"""
        # First update progress
        api_client.post(
            f"{BASE_URL}/api/engines/engagement_engine/progress",
            headers={"Authorization": f"Bearer {free_user_token}"},
            json={"progress": 35.0}
        )
        
        # Then verify via details endpoint
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Progress should be updated
        assert data["state"]["progress"] == 35.0, \
            f"Expected progress 35.0, got {data['state']['progress']}"
        
        print("✓ Progress update persisted correctly")


# ============== ENGINE SERVICE TESTS ==============

class TestEngineService:
    """Tests for engine service functionality"""
    
    def test_engine_inputs_structure(self, api_client, free_user_token):
        """Engine service processes inputs correctly - verify input structure"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected inputs for engagement engine
        expected_inputs = [
            "audience_profile", "content_strategy", "platform_selection",
            "engagement_goals", "communication_style"
        ]
        
        actual_inputs = data["inputs"]["required"]
        for inp in expected_inputs:
            assert inp in actual_inputs, f"Expected input '{inp}' not found"
        
        print(f"✓ Engagement engine has correct inputs: {actual_inputs}")
    
    def test_engine_outputs_structure(self, api_client, free_user_token):
        """Engine service generates outputs based on rules - verify output structure"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected outputs for engagement engine
        expected_outputs = [
            "engagement_plan", "content_calendar", "audience_insights",
            "growth_metrics", "community_strategy"
        ]
        
        actual_outputs = data["outputs"]["available"]
        for out in expected_outputs:
            assert out in actual_outputs, f"Expected output '{out}' not found"
        
        print(f"✓ Engagement engine has correct outputs: {actual_outputs}")
    
    def test_engine_rules_structure(self, api_client, free_user_token):
        """Engine has rules defined"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify rules exist
        rules = data["rules"]
        assert len(rules["definitions"]) > 0, "Engine should have rules defined"
        assert len(rules["status"]) > 0, "Engine should have rule status"
        
        print(f"✓ Engagement engine has {len(rules['definitions'])} rules defined")


# ============== FREE USER STATE VERIFICATION ==============

class TestFreeUserEngineState:
    """Tests to verify free user's engine state (engagement+income selected)"""
    
    def test_free_user_engagement_engine_active(self, api_client, free_user_token):
        """Free user's engagement_engine should be active"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/engagement_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Engagement engine should be active (no dependencies)
        assert data["state"]["status"] == "active", \
            f"Expected engagement_engine to be active, got {data['state']['status']}"
        
        print("✓ Free user's engagement_engine is active")
    
    def test_free_user_income_engine_pending(self, api_client, free_user_token):
        """Free user's income_engine should be pending (missing business_engine dependency)"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/income_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Income engine should be pending (depends on business_engine which is not selected)
        # Note: Status could be pending or have blockers
        assert data["state"]["status"] in ["pending", "blocked"], \
            f"Expected income_engine to be pending/blocked, got {data['state']['status']}"
        
        # Dependencies should not be met
        assert data["dependencies"]["met"] == False, \
            "income_engine dependencies should not be met for free user"
        
        print(f"✓ Free user's income_engine is {data['state']['status']} (deps not met)")
    
    def test_free_user_business_engine_inactive(self, api_client, free_user_token):
        """Free user's business_engine should be inactive (not selected)"""
        response = api_client.get(
            f"{BASE_URL}/api/engines/business_engine/details",
            headers={"Authorization": f"Bearer {free_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Business engine should be inactive (not selected by free user)
        assert data["state"]["status"] == "inactive", \
            f"Expected business_engine to be inactive, got {data['state']['status']}"
        
        print("✓ Free user's business_engine is inactive")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
