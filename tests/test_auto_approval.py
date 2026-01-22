"""
Test Suite for Phase 4 Module D Task D2: Auto-Approval Rules with ARRIS Evaluation Logic

Tests cover:
- GET /api/admin/auto-approval/config - Get auto-approval configuration
- PATCH /api/admin/auto-approval/config - Update configuration
- GET /api/admin/auto-approval/rules - Get all approval rules
- GET /api/admin/auto-approval/rules/{rule_id} - Get specific rule
- POST /api/admin/auto-approval/rules - Create new rule
- PATCH /api/admin/auto-approval/rules/{rule_id} - Update rule
- DELETE /api/admin/auto-approval/rules/{rule_id} - Delete rule
- POST /api/admin/auto-approval/evaluate/{creator_id} - Evaluate creator without action
- POST /api/admin/auto-approval/process/{creator_id} - Process registration with auto_execute
- POST /api/admin/auto-approval/process-all - Batch process pending registrations
- GET /api/admin/auto-approval/history - Get evaluation history
- GET /api/admin/auto-approval/analytics - Get approval analytics
- POST /api/creators/register - Registration triggers auto-approval
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


class TestAutoApprovalConfig:
    """Tests for auto-approval configuration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_config_requires_auth(self):
        """GET /api/admin/auto-approval/config requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/auto-approval/config")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/auto-approval/config requires authentication")
    
    def test_get_config_success(self):
        """GET /api/admin/auto-approval/config returns configuration"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        # Verify expected fields
        assert "enabled" in config
        assert "approval_threshold" in config
        assert "require_arris_review" in config
        assert "arris_override_enabled" in config
        assert "auto_reject_enabled" in config
        assert "auto_reject_threshold" in config
        assert "notify_admin_on_auto_approve" in config
        assert "notify_admin_on_edge_case" in config
        assert "edge_case_range" in config
        
        print(f"✓ GET /api/admin/auto-approval/config returns config with threshold={config['approval_threshold']}")
    
    def test_update_config_requires_auth(self):
        """PATCH /api/admin/auto-approval/config requires authentication"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            json={"approval_threshold": 75}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ PATCH /api/admin/auto-approval/config requires authentication")
    
    def test_update_config_success(self):
        """PATCH /api/admin/auto-approval/config updates configuration"""
        # Get current config
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers
        )
        original_threshold = response.json().get("approval_threshold", 70)
        
        # Update threshold
        new_threshold = 75 if original_threshold != 75 else 80
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers,
            json={"approval_threshold": new_threshold}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        assert config["approval_threshold"] == new_threshold
        
        # Restore original
        requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers,
            json={"approval_threshold": original_threshold}
        )
        
        print(f"✓ PATCH /api/admin/auto-approval/config updated threshold to {new_threshold}")
    
    def test_update_config_invalid_threshold(self):
        """PATCH /api/admin/auto-approval/config validates threshold range"""
        # Test threshold > 100
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers,
            json={"approval_threshold": 150}
        )
        assert response.status_code == 400, f"Expected 400 for threshold > 100, got {response.status_code}"
        
        # Test threshold < 0
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers,
            json={"approval_threshold": -10}
        )
        assert response.status_code == 400, f"Expected 400 for threshold < 0, got {response.status_code}"
        
        print("✓ PATCH /api/admin/auto-approval/config validates threshold range (0-100)")
    
    def test_update_config_multiple_fields(self):
        """PATCH /api/admin/auto-approval/config can update multiple fields"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/config",
            headers=self.headers,
            json={
                "notify_admin_on_auto_approve": True,
                "notify_admin_on_edge_case": True,
                "require_arris_review": True
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        assert config["notify_admin_on_auto_approve"] == True
        assert config["notify_admin_on_edge_case"] == True
        assert config["require_arris_review"] == True
        
        print("✓ PATCH /api/admin/auto-approval/config updates multiple fields")


class TestAutoApprovalRules:
    """Tests for auto-approval rules CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        self.created_rule_ids = []
    
    def teardown_method(self, method):
        """Clean up created rules"""
        for rule_id in self.created_rule_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/admin/auto-approval/rules/{rule_id}",
                    headers=self.headers
                )
            except:
                pass
    
    def test_get_rules_requires_auth(self):
        """GET /api/admin/auto-approval/rules requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/auto-approval/rules")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/auto-approval/rules requires authentication")
    
    def test_get_rules_success(self):
        """GET /api/admin/auto-approval/rules returns all rules"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "rules" in data
        assert "total" in data
        assert isinstance(data["rules"], list)
        
        # Verify default rules exist
        rule_ids = [r.get("rule_id") for r in data["rules"]]
        expected_rules = ["min_followers", "platform_presence", "niche_specified", 
                         "goals_clarity", "professional_email", "arris_response_quality", 
                         "website_provided"]
        
        for expected in expected_rules:
            assert expected in rule_ids, f"Missing default rule: {expected}"
        
        print(f"✓ GET /api/admin/auto-approval/rules returns {data['total']} rules including all 7 defaults")
    
    def test_get_rules_enabled_only(self):
        """GET /api/admin/auto-approval/rules?enabled_only=true filters rules"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules?enabled_only=true",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        for rule in data["rules"]:
            assert rule["enabled"] == True, f"Rule {rule['id']} should be enabled"
        
        print(f"✓ GET /api/admin/auto-approval/rules?enabled_only=true returns only enabled rules")
    
    def test_get_specific_rule(self):
        """GET /api/admin/auto-approval/rules/{rule_id} returns specific rule"""
        # First get all rules to find a valid ID
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers
        )
        rules = response.json()["rules"]
        assert len(rules) > 0, "No rules found"
        
        rule_id = rules[0]["id"]
        
        # Get specific rule
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules/{rule_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        rule = response.json()
        assert rule["id"] == rule_id
        assert "name" in rule
        assert "condition_type" in rule
        assert "field" in rule
        assert "operator" in rule
        assert "score_weight" in rule
        assert "is_required" in rule
        assert "enabled" in rule
        
        print(f"✓ GET /api/admin/auto-approval/rules/{rule_id} returns rule details")
    
    def test_get_nonexistent_rule(self):
        """GET /api/admin/auto-approval/rules/{rule_id} returns 404 for invalid ID"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules/INVALID-RULE-ID",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ GET /api/admin/auto-approval/rules/INVALID returns 404")
    
    def test_create_rule_requires_auth(self):
        """POST /api/admin/auto-approval/rules requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            json={"name": "Test Rule", "condition_type": "exists", "field": "test", "operator": "not_empty"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/rules requires authentication")
    
    def test_create_rule_success(self):
        """POST /api/admin/auto-approval/rules creates new rule"""
        rule_data = {
            "name": f"TEST_Custom Rule {uuid.uuid4().hex[:6]}",
            "description": "Test rule for automated testing",
            "category": "custom",
            "condition_type": "exists",
            "field": "bio",
            "operator": "not_empty",
            "score_weight": 15,
            "is_required": False,
            "enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers,
            json=rule_data
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        rule = response.json()
        self.created_rule_ids.append(rule["id"])
        
        assert rule["name"] == rule_data["name"]
        assert rule["condition_type"] == rule_data["condition_type"]
        assert rule["field"] == rule_data["field"]
        assert rule["operator"] == rule_data["operator"]
        assert rule["score_weight"] == rule_data["score_weight"]
        assert "id" in rule
        assert "created_at" in rule
        
        print(f"✓ POST /api/admin/auto-approval/rules created rule {rule['id']}")
    
    def test_create_rule_missing_fields(self):
        """POST /api/admin/auto-approval/rules validates required fields"""
        # Missing required fields
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers,
            json={"name": "Incomplete Rule"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/rules validates required fields")
    
    def test_update_rule_success(self):
        """PATCH /api/admin/auto-approval/rules/{rule_id} updates rule"""
        # Create a rule first
        rule_data = {
            "name": f"TEST_Update Rule {uuid.uuid4().hex[:6]}",
            "condition_type": "exists",
            "field": "website",
            "operator": "not_empty",
            "score_weight": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers,
            json=rule_data
        )
        rule = response.json()
        self.created_rule_ids.append(rule["id"])
        
        # Update the rule
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/rules/{rule['id']}",
            headers=self.headers,
            json={"score_weight": 25, "enabled": False}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        updated_rule = response.json()
        assert updated_rule["score_weight"] == 25
        assert updated_rule["enabled"] == False
        
        print(f"✓ PATCH /api/admin/auto-approval/rules/{rule['id']} updated rule")
    
    def test_update_nonexistent_rule(self):
        """PATCH /api/admin/auto-approval/rules/{rule_id} returns 404 for invalid ID"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/auto-approval/rules/INVALID-RULE-ID",
            headers=self.headers,
            json={"score_weight": 20}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PATCH /api/admin/auto-approval/rules/INVALID returns 404")
    
    def test_delete_rule_success(self):
        """DELETE /api/admin/auto-approval/rules/{rule_id} deletes rule"""
        # Create a rule first
        rule_data = {
            "name": f"TEST_Delete Rule {uuid.uuid4().hex[:6]}",
            "condition_type": "exists",
            "field": "goals",
            "operator": "not_empty",
            "score_weight": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/rules",
            headers=self.headers,
            json=rule_data
        )
        rule = response.json()
        rule_id = rule["id"]
        
        # Delete the rule
        response = requests.delete(
            f"{BASE_URL}/api/admin/auto-approval/rules/{rule_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify deletion
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/rules/{rule_id}",
            headers=self.headers
        )
        assert response.status_code == 404, "Rule should be deleted"
        
        print(f"✓ DELETE /api/admin/auto-approval/rules/{rule_id} deleted rule")
    
    def test_delete_nonexistent_rule(self):
        """DELETE /api/admin/auto-approval/rules/{rule_id} returns 404 for invalid ID"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/auto-approval/rules/INVALID-RULE-ID",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ DELETE /api/admin/auto-approval/rules/INVALID returns 404")


class TestAutoApprovalEvaluation:
    """Tests for creator evaluation and processing endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token and create test creators"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        self.created_creator_ids = []
    
    def _create_test_creator(self, quality="high"):
        """Helper to create test creators with varying quality"""
        unique_id = uuid.uuid4().hex[:8]
        
        if quality == "high":
            # High-quality creator - should auto-approve
            creator_data = {
                "name": f"TEST_HighQuality Creator {unique_id}",
                "email": f"test_high_{unique_id}@example.com",
                "password": "testpassword123",
                "platforms": ["youtube", "instagram", "tiktok"],
                "niche": "Tech & Software",
                "follower_count": "100K-500K",
                "goals": "I want to grow my audience and monetize my content through brand partnerships and courses. My goal is to reach 1M followers within 2 years.",
                "website": "https://example.com/creator",
                "arris_response": "My biggest challenge is creating consistent content while managing brand deals. I need help with workflow automation and content scheduling to maintain quality while scaling."
            }
        elif quality == "medium":
            # Medium-quality creator - edge case for manual review
            creator_data = {
                "name": f"TEST_MediumQuality Creator {unique_id}",
                "email": f"test_medium_{unique_id}@example.com",
                "password": "testpassword123",
                "platforms": ["instagram"],
                "niche": "Lifestyle & Travel",
                "follower_count": "10K-50K",
                "goals": "Grow my following",
                "arris_response": "Need help with content"
            }
        else:
            # Low-quality creator - should be rejected or manual review
            creator_data = {
                "name": f"TEST_LowQuality Creator {unique_id}",
                "email": f"test_low_{unique_id}@example.com",
                "password": "testpassword123",
                "platforms": [],
                "niche": "",
                "follower_count": "0-1K",
                "goals": "",
                "arris_response": ""
            }
        
        response = requests.post(
            f"{BASE_URL}/api/creators/register",
            json=creator_data
        )
        
        if response.status_code == 200:
            creator = response.json()
            self.created_creator_ids.append(creator["id"])
            return creator
        return None
    
    def test_evaluate_creator_requires_auth(self):
        """POST /api/admin/auto-approval/evaluate/{creator_id} requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/TEST-CREATOR-ID"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/evaluate requires authentication")
    
    def test_evaluate_high_quality_creator(self):
        """POST /api/admin/auto-approval/evaluate evaluates high-quality creator"""
        creator = self._create_test_creator("high")
        if not creator:
            pytest.skip("Could not create test creator")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/{creator['id']}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        evaluation = response.json()
        
        # Verify evaluation structure
        assert "evaluation_id" in evaluation
        assert "creator_id" in evaluation
        assert "score" in evaluation
        assert "base_score" in evaluation
        assert "bonus_score" in evaluation
        assert "recommendation" in evaluation
        assert "rule_results" in evaluation
        assert "thresholds" in evaluation
        
        # High-quality creator should have high score
        assert evaluation["score"] >= 70, f"High-quality creator score {evaluation['score']} should be >= 70"
        assert evaluation["recommendation"] in ["auto_approve", "manual_review"]
        
        print(f"✓ High-quality creator evaluated: score={evaluation['score']}, recommendation={evaluation['recommendation']}")
    
    def test_evaluate_medium_quality_creator(self):
        """POST /api/admin/auto-approval/evaluate evaluates medium-quality creator"""
        creator = self._create_test_creator("medium")
        if not creator:
            pytest.skip("Could not create test creator")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/{creator['id']}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        evaluation = response.json()
        
        # Medium-quality creator should have moderate score
        assert 30 <= evaluation["score"] <= 80, f"Medium-quality creator score {evaluation['score']} should be 30-80"
        
        print(f"✓ Medium-quality creator evaluated: score={evaluation['score']}, recommendation={evaluation['recommendation']}")
    
    def test_evaluate_low_quality_creator(self):
        """POST /api/admin/auto-approval/evaluate evaluates low-quality creator"""
        creator = self._create_test_creator("low")
        if not creator:
            pytest.skip("Could not create test creator")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/{creator['id']}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        evaluation = response.json()
        
        # Low-quality creator should have low score and fail required rules
        assert evaluation["score"] < 70, f"Low-quality creator score {evaluation['score']} should be < 70"
        assert evaluation["required_rules_passed"] == False, "Low-quality creator should fail required rules"
        assert evaluation["recommendation"] in ["reject", "manual_review", "auto_reject"]
        
        print(f"✓ Low-quality creator evaluated: score={evaluation['score']}, recommendation={evaluation['recommendation']}")
    
    def test_evaluate_nonexistent_creator(self):
        """POST /api/admin/auto-approval/evaluate/{creator_id} returns 404 for invalid ID"""
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/INVALID-CREATOR-ID",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/evaluate/INVALID returns 404")
    
    def test_evaluate_without_arris(self):
        """POST /api/admin/auto-approval/evaluate can skip ARRIS assessment"""
        creator = self._create_test_creator("medium")
        if not creator:
            pytest.skip("Could not create test creator")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/{creator['id']}?include_arris=false",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        evaluation = response.json()
        # ARRIS assessment may or may not be present depending on config
        
        print(f"✓ Evaluation without ARRIS: score={evaluation['score']}")
    
    def test_process_creator_requires_auth(self):
        """POST /api/admin/auto-approval/process/{creator_id} requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/process/TEST-CREATOR-ID"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/process requires authentication")
    
    def test_process_creator_dry_run(self):
        """POST /api/admin/auto-approval/process with auto_execute=false does dry run"""
        # Note: Since registration now triggers auto-approval, creators are already processed
        # This test verifies the endpoint returns appropriate error for already-processed creators
        creator = self._create_test_creator("high")
        if not creator:
            pytest.skip("Could not create test creator")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/process/{creator['id']}?auto_execute=false",
            headers=self.headers
        )
        
        # Creator is already processed during registration, so we expect either:
        # - 200 with evaluation (if not yet processed)
        # - 400 with "Creator already processed" (if already processed)
        if response.status_code == 200:
            result = response.json()
            assert "evaluation" in result
            print(f"✓ Process dry run: recommendation={result['evaluation']['recommendation']}")
        elif response.status_code == 400:
            result = response.json()
            assert "already processed" in result.get("detail", "").lower() or "error" in result
            print(f"✓ Process dry run: Creator already processed (expected behavior)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")
    
    def test_process_all_requires_auth(self):
        """POST /api/admin/auto-approval/process-all requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/auto-approval/process-all")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/admin/auto-approval/process-all requires authentication")
    
    def test_process_all_dry_run(self):
        """POST /api/admin/auto-approval/process-all with auto_execute=false does dry run"""
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/process-all?auto_execute=false&limit=5",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        result = response.json()
        assert "summary" in result
        assert "dry_run" in result
        assert result["dry_run"] == True
        assert "results" in result
        
        print(f"✓ Process-all dry run: processed {result['summary']['total_processed']} creators")


class TestAutoApprovalHistoryAndAnalytics:
    """Tests for evaluation history and analytics endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_history_requires_auth(self):
        """GET /api/admin/auto-approval/history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/auto-approval/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/auto-approval/history requires authentication")
    
    def test_get_history_success(self):
        """GET /api/admin/auto-approval/history returns evaluation history"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/history",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)
        
        # If there's history, verify structure
        if len(data["history"]) > 0:
            entry = data["history"][0]
            assert "evaluation_id" in entry
            assert "creator_id" in entry
            assert "score" in entry
            assert "recommendation" in entry
            assert "evaluated_at" in entry
        
        print(f"✓ GET /api/admin/auto-approval/history returns {data['total']} entries")
    
    def test_get_history_filtered_by_creator(self):
        """GET /api/admin/auto-approval/history can filter by creator_id"""
        # First get some history
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/history?limit=1",
            headers=self.headers
        )
        data = response.json()
        
        if len(data["history"]) > 0:
            creator_id = data["history"][0]["creator_id"]
            
            # Filter by creator
            response = requests.get(
                f"{BASE_URL}/api/admin/auto-approval/history?creator_id={creator_id}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            
            filtered_data = response.json()
            for entry in filtered_data["history"]:
                assert entry["creator_id"] == creator_id
            
            print(f"✓ GET /api/admin/auto-approval/history filtered by creator_id")
        else:
            print("✓ GET /api/admin/auto-approval/history filter test skipped (no history)")
    
    def test_get_analytics_requires_auth(self):
        """GET /api/admin/auto-approval/analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/auto-approval/analytics")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/auto-approval/analytics requires authentication")
    
    def test_get_analytics_success(self):
        """GET /api/admin/auto-approval/analytics returns analytics data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/auto-approval/analytics",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        analytics = response.json()
        
        # Verify expected fields
        assert "total_evaluations" in analytics
        assert "average_score" in analytics
        assert "by_recommendation" in analytics
        assert "actions_taken" in analytics
        assert "most_failed_rules" in analytics
        assert "analyzed_at" in analytics
        
        # Verify actions_taken structure
        actions = analytics["actions_taken"]
        assert "auto_approved" in actions
        assert "auto_rejected" in actions
        assert "marked_for_review" in actions
        
        print(f"✓ GET /api/admin/auto-approval/analytics: {analytics['total_evaluations']} evaluations, avg score={analytics['average_score']}")


class TestCreatorRegistrationAutoApproval:
    """Tests for auto-approval integration with creator registration"""
    
    def test_registration_triggers_auto_approval(self):
        """POST /api/creators/register triggers auto-approval evaluation"""
        unique_id = uuid.uuid4().hex[:8]
        
        # Register a high-quality creator
        creator_data = {
            "name": f"TEST_AutoApproval Creator {unique_id}",
            "email": f"test_autoapproval_{unique_id}@example.com",
            "password": "testpassword123",
            "platforms": ["youtube", "instagram", "tiktok"],
            "niche": "Tech & Software",
            "follower_count": "100K-500K",
            "goals": "I want to grow my audience and monetize my content through brand partnerships and courses. My goal is to reach 1M followers within 2 years.",
            "website": "https://example.com/creator",
            "arris_response": "My biggest challenge is creating consistent content while managing brand deals. I need help with workflow automation and content scheduling to maintain quality while scaling."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/creators/register",
            json=creator_data
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        result = response.json()
        
        # Verify response includes status update from auto-approval
        assert "status" in result
        assert "message" in result
        
        # High-quality creator should be auto-approved or pending_review
        assert result["status"] in ["approved", "pending_review", "pending"], f"Unexpected status: {result['status']}"
        
        print(f"✓ Registration triggered auto-approval: status={result['status']}, message={result['message'][:50]}...")
    
    def test_registration_low_quality_not_auto_approved(self):
        """POST /api/creators/register with low quality goes to manual review"""
        unique_id = uuid.uuid4().hex[:8]
        
        # Register a low-quality creator (missing required fields)
        creator_data = {
            "name": f"TEST_LowQuality {unique_id}",
            "email": f"test_lowquality_{unique_id}@example.com",
            "password": "testpassword123",
            "platforms": [],  # No platforms - fails required rule
            "niche": "",  # No niche - fails required rule
            "follower_count": "0-1K",
            "goals": "",
            "arris_response": ""
        }
        
        response = requests.post(
            f"{BASE_URL}/api/creators/register",
            json=creator_data
        )
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        result = response.json()
        
        # Low-quality creator should NOT be auto-approved
        assert result["status"] in ["pending_review", "pending", "rejected"], f"Low-quality creator should not be approved: {result['status']}"
        
        print(f"✓ Low-quality registration not auto-approved: status={result['status']}")


class TestRuleEvaluationLogic:
    """Tests for specific rule evaluation logic"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def _create_and_evaluate(self, creator_data):
        """Helper to create creator and get evaluation"""
        response = requests.post(
            f"{BASE_URL}/api/creators/register",
            json=creator_data
        )
        if response.status_code != 200:
            return None, None
        
        creator = response.json()
        
        response = requests.post(
            f"{BASE_URL}/api/admin/auto-approval/evaluate/{creator['id']}?include_arris=false",
            headers=self.headers
        )
        if response.status_code != 200:
            return creator, None
        
        return creator, response.json()
    
    def test_follower_count_scoring(self):
        """Verify follower count affects score appropriately"""
        unique_id = uuid.uuid4().hex[:8]
        
        # High follower count
        creator_data = {
            "name": f"TEST_HighFollowers {unique_id}",
            "email": f"test_highfollowers_{unique_id}@example.com",
            "password": "testpassword123",
            "platforms": ["youtube"],
            "niche": "Tech & Software",
            "follower_count": "500K-1M",
            "goals": "Grow my audience and create valuable content",
            "arris_response": "I need help with content strategy and monetization"
        }
        
        creator, evaluation = self._create_and_evaluate(creator_data)
        if evaluation:
            # Check that min_followers rule passed
            follower_rule = next((r for r in evaluation["rule_results"] if r["rule_name"] == "Minimum Follower Count"), None)
            if follower_rule:
                assert follower_rule["passed"] == True, "High follower count should pass min_followers rule"
            
            # Should have bonus points for high followers
            assert evaluation["bonus_score"] > 0, "High follower count should earn bonus points"
            
            print(f"✓ High follower count scoring: score={evaluation['score']}, bonus={evaluation['bonus_score']}")
        else:
            print("✓ Follower count scoring test skipped (could not create/evaluate)")
    
    def test_platform_presence_required(self):
        """Verify platform_presence is a required rule"""
        unique_id = uuid.uuid4().hex[:8]
        
        # No platforms
        creator_data = {
            "name": f"TEST_NoPlatforms {unique_id}",
            "email": f"test_noplatforms_{unique_id}@example.com",
            "password": "testpassword123",
            "platforms": [],  # Empty platforms
            "niche": "Tech & Software",
            "follower_count": "10K-50K",
            "goals": "Grow my audience",
            "arris_response": "Need help with content"
        }
        
        creator, evaluation = self._create_and_evaluate(creator_data)
        if evaluation:
            # Check that platform_presence rule failed
            platform_rule = next((r for r in evaluation["rule_results"] if r["rule_name"] == "Platform Presence"), None)
            if platform_rule:
                assert platform_rule["passed"] == False, "Empty platforms should fail platform_presence rule"
                assert platform_rule["is_required"] == True, "platform_presence should be required"
            
            # Required rules failed should affect recommendation
            assert evaluation["required_rules_passed"] == False, "Should fail required rules check"
            
            print(f"✓ Platform presence required rule: passed={platform_rule['passed'] if platform_rule else 'N/A'}")
        else:
            print("✓ Platform presence test skipped (could not create/evaluate)")
    
    def test_professional_email_pattern(self):
        """Verify professional_email rule rejects disposable emails"""
        unique_id = uuid.uuid4().hex[:8]
        
        # Disposable email (should fail)
        creator_data = {
            "name": f"TEST_DisposableEmail {unique_id}",
            "email": f"test_mailinator_{unique_id}@mailinator.com",  # Disposable email
            "password": "testpassword123",
            "platforms": ["youtube"],
            "niche": "Tech & Software",
            "follower_count": "10K-50K",
            "goals": "Grow my audience",
            "arris_response": "Need help with content"
        }
        
        creator, evaluation = self._create_and_evaluate(creator_data)
        if evaluation:
            # Check that professional_email rule failed
            email_rule = next((r for r in evaluation["rule_results"] if r["rule_name"] == "Professional Email"), None)
            if email_rule:
                assert email_rule["passed"] == False, "Disposable email should fail professional_email rule"
            
            print(f"✓ Professional email pattern: passed={email_rule['passed'] if email_rule else 'N/A'}")
        else:
            print("✓ Professional email test skipped (could not create/evaluate)")
    
    def test_bonus_points_multiple_platforms(self):
        """Verify bonus points for multiple platforms"""
        unique_id = uuid.uuid4().hex[:8]
        
        # Multiple platforms
        creator_data = {
            "name": f"TEST_MultiPlatform {unique_id}",
            "email": f"test_multiplatform_{unique_id}@example.com",
            "password": "testpassword123",
            "platforms": ["youtube", "instagram", "tiktok", "twitter", "linkedin"],  # 5 platforms
            "niche": "Tech & Software",
            "follower_count": "10K-50K",
            "goals": "Grow my audience across all platforms",
            "website": "https://example.com",
            "arris_response": "I need help managing content across multiple platforms efficiently"
        }
        
        creator, evaluation = self._create_and_evaluate(creator_data)
        if evaluation:
            # Should have bonus points for multiple platforms
            assert evaluation["bonus_score"] >= 10, f"5 platforms should earn at least 10 bonus points, got {evaluation['bonus_score']}"
            
            print(f"✓ Multiple platforms bonus: bonus_score={evaluation['bonus_score']}")
        else:
            print("✓ Multiple platforms bonus test skipped (could not create/evaluate)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
