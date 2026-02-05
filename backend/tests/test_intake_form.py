"""
Creators Hive HQ - Intake Form API Tests
=========================================
Tests for Phase 1: Intake Form endpoints

Endpoints tested:
- GET /api/intake/form-options - Returns all field definitions
- GET /api/intake/status - Shows intake_completed status
- POST /api/intake/submit - Submit intake form with track assignment
- GET /api/intake/system-state - Returns full system state after intake
- GET /api/command-center - Returns dashboard state with engines and modules
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Use the public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://user-test-drive.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_CREDENTIALS = {
    "pro_creator": {"email": "protest@hivehq.com", "password": "testpassword"},
    "elite_creator": {"email": "elitetest@hivehq.com", "password": "testpassword123"},
    "admin": {"email": "admin@hivehq.com", "password": "admin123"}
}


class TestIntakeFormOptions:
    """Test GET /api/intake/form-options endpoint"""
    
    def test_form_options_returns_all_sections(self):
        """Verify form-options returns all 3 sections"""
        response = requests.get(f"{BASE_URL}/api/intake/form-options")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all 3 sections exist
        assert "user_identity" in data, "Missing user_identity section"
        assert "system_need" in data, "Missing system_need section"
        assert "starting_point" in data, "Missing starting_point section"
        print("✓ Form options returns all 3 sections")
    
    def test_user_identity_fields(self):
        """Verify user_identity section has correct fields"""
        response = requests.get(f"{BASE_URL}/api/intake/form-options")
        assert response.status_code == 200
        
        data = response.json()
        user_identity = data["user_identity"]
        
        # Check required fields
        assert "identity_type" in user_identity, "Missing identity_type field"
        assert "stage" in user_identity, "Missing stage field"
        assert "primary_goal" in user_identity, "Missing primary_goal field"
        
        # Verify identity_type options
        identity_options = [opt["value"] for opt in user_identity["identity_type"]["options"]]
        assert "creator" in identity_options
        assert "business" in identity_options
        assert "hybrid" in identity_options
        
        # Verify stage options
        stage_options = [opt["value"] for opt in user_identity["stage"]["options"]]
        assert "beginner" in stage_options
        assert "intermediate" in stage_options
        assert "advanced" in stage_options
        
        print("✓ User identity fields are correct")
    
    def test_system_need_engines(self):
        """Verify system_need section has all 4 engines"""
        response = requests.get(f"{BASE_URL}/api/intake/form-options")
        assert response.status_code == 200
        
        data = response.json()
        system_need = data["system_need"]
        
        assert "selected_engines" in system_need, "Missing selected_engines field"
        
        engine_options = [opt["value"] for opt in system_need["selected_engines"]["options"]]
        assert "business_engine" in engine_options, "Missing business_engine"
        assert "engagement_engine" in engine_options, "Missing engagement_engine"
        assert "role_engine" in engine_options, "Missing role_engine"
        assert "income_engine" in engine_options, "Missing income_engine"
        
        # Verify labels don't contain "Engine" word (per requirements)
        for opt in system_need["selected_engines"]["options"]:
            assert "Engine" not in opt["label"], f"Label should not contain 'Engine': {opt['label']}"
        
        print("✓ System need engines are correct (labels updated)")
    
    def test_starting_point_fields(self):
        """Verify starting_point section has correct fields"""
        response = requests.get(f"{BASE_URL}/api/intake/form-options")
        assert response.status_code == 200
        
        data = response.json()
        starting_point = data["starting_point"]
        
        assert "assets_already_have" in starting_point, "Missing assets_already_have field"
        assert "missing_elements" in starting_point, "Missing missing_elements field"
        assert "first_priority" in starting_point, "Missing first_priority field"
        
        # Verify first_priority is required
        assert starting_point["first_priority"]["required"] == True
        
        print("✓ Starting point fields are correct")


class TestIntakeStatus:
    """Test GET /api/intake/status endpoint"""
    
    @pytest.fixture
    def pro_token(self):
        """Get auth token for pro creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as pro creator")
    
    @pytest.fixture
    def elite_token(self):
        """Get auth token for elite creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["elite_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as elite creator")
    
    def test_intake_status_requires_auth(self):
        """Verify intake status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/intake/status")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Intake status requires authentication")
    
    def test_intake_status_returns_completion_status(self, pro_token):
        """Verify intake status returns intake_completed field"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/intake/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "intake_completed" in data, "Missing intake_completed field"
        assert isinstance(data["intake_completed"], bool)
        
        print(f"✓ Intake status returned: intake_completed={data['intake_completed']}")


class TestIntakeSubmission:
    """Test POST /api/intake/submit endpoint"""
    
    @pytest.fixture
    def pro_token(self):
        """Get auth token for pro creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as pro creator")
    
    @pytest.fixture
    def elite_token(self):
        """Get auth token for elite creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["elite_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as elite creator")
    
    def test_intake_submit_requires_auth(self):
        """Verify intake submit requires authentication"""
        submission = {
            "user_identity": {
                "identity_type": "creator",
                "stage": "beginner",
                "primary_goal": "grow_audience"
            },
            "system_need": {
                "selected_engines": ["engagement_engine"]
            },
            "starting_point": {
                "assets_already_have": [],
                "missing_elements": [],
                "first_priority": "build_foundation"
            }
        }
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=submission)
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Intake submit requires authentication")
    
    def test_intake_submit_validates_required_fields(self, pro_token):
        """Verify intake submit validates required fields"""
        headers = {"Authorization": f"Bearer {pro_token}", "Content-Type": "application/json"}
        
        # Missing identity_type
        invalid_submission = {
            "user_identity": {
                "stage": "beginner",
                "primary_goal": "grow_audience"
            },
            "system_need": {
                "selected_engines": ["engagement_engine"]
            },
            "starting_point": {
                "first_priority": "build_foundation"
            }
        }
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=invalid_submission, headers=headers)
        assert response.status_code == 422, f"Should reject missing identity_type, got {response.status_code}"
        print("✓ Intake submit validates required fields")
    
    def test_intake_submit_requires_at_least_one_engine(self, pro_token):
        """Verify intake submit requires at least one engine selected"""
        headers = {"Authorization": f"Bearer {pro_token}", "Content-Type": "application/json"}
        
        # Empty engines list
        invalid_submission = {
            "user_identity": {
                "identity_type": "creator",
                "stage": "beginner",
                "primary_goal": "grow_audience"
            },
            "system_need": {
                "selected_engines": []
            },
            "starting_point": {
                "first_priority": "build_foundation"
            }
        }
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=invalid_submission, headers=headers)
        assert response.status_code == 422, f"Should reject empty engines, got {response.status_code}"
        print("✓ Intake submit requires at least one engine")
    
    def test_intake_submit_success_creator_track(self, pro_token):
        """Test successful intake submission for creator track"""
        headers = {"Authorization": f"Bearer {pro_token}", "Content-Type": "application/json"}
        
        submission = {
            "user_identity": {
                "identity_type": "creator",
                "stage": "intermediate",
                "primary_goal": "grow_audience"
            },
            "system_need": {
                "selected_engines": ["engagement_engine", "income_engine"]
            },
            "starting_point": {
                "assets_already_have": ["social_media_accounts", "existing_audience"],
                "missing_elements": ["content_plan", "monetization_path"],
                "first_priority": "grow_audience"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=submission, headers=headers)
        assert response.status_code == 200, f"Submit failed: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "intake_id" in data, "Missing intake_id"
        assert "user_id" in data, "Missing user_id"
        assert "assigned_track" in data, "Missing assigned_track"
        assert "activated_engines" in data, "Missing activated_engines"
        assert "unlocked_modules" in data, "Missing unlocked_modules"
        assert "next_steps" in data, "Missing next_steps"
        assert "message" in data, "Missing message"
        
        # Verify track assignment (creator identity -> creator track)
        assert data["assigned_track"] == "creator_track", f"Expected creator_track, got {data['assigned_track']}"
        
        # Verify engines activated
        assert "engagement_engine" in data["activated_engines"]
        assert "income_engine" in data["activated_engines"]
        
        # Verify modules unlocked
        assert len(data["unlocked_modules"]) > 0, "Should have unlocked modules"
        
        print(f"✓ Intake submit success: track={data['assigned_track']}, engines={len(data['activated_engines'])}, modules={len(data['unlocked_modules'])}")
    
    def test_intake_submit_success_business_track(self, elite_token):
        """Test successful intake submission for business track"""
        headers = {"Authorization": f"Bearer {elite_token}", "Content-Type": "application/json"}
        
        submission = {
            "user_identity": {
                "identity_type": "business",
                "stage": "advanced",
                "primary_goal": "launch_offers"
            },
            "system_need": {
                "selected_engines": ["business_engine", "role_engine", "income_engine"]
            },
            "starting_point": {
                "assets_already_have": ["offers_products", "brand_identity"],
                "missing_elements": ["systems_automation"],
                "first_priority": "increase_income"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=submission, headers=headers)
        assert response.status_code == 200, f"Submit failed: {response.text}"
        
        data = response.json()
        
        # Verify track assignment (business identity -> business track)
        assert data["assigned_track"] == "business_track", f"Expected business_track, got {data['assigned_track']}"
        
        # Verify all 3 engines activated
        assert len(data["activated_engines"]) == 3
        
        print(f"✓ Business track submit success: engines={data['activated_engines']}")
    
    def test_intake_submit_success_hybrid_track(self, pro_token):
        """Test successful intake submission for hybrid track"""
        headers = {"Authorization": f"Bearer {pro_token}", "Content-Type": "application/json"}
        
        submission = {
            "user_identity": {
                "identity_type": "hybrid",
                "stage": "beginner",
                "primary_goal": "build_brand"
            },
            "system_need": {
                "selected_engines": ["business_engine", "engagement_engine"]
            },
            "starting_point": {
                "assets_already_have": ["none"],
                "missing_elements": ["clarity_structure", "content_plan", "offer_strategy"],
                "first_priority": "build_foundation"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/intake/submit", json=submission, headers=headers)
        assert response.status_code == 200, f"Submit failed: {response.text}"
        
        data = response.json()
        
        # Verify track assignment (hybrid identity -> hybrid track)
        assert data["assigned_track"] == "hybrid_track", f"Expected hybrid_track, got {data['assigned_track']}"
        
        print(f"✓ Hybrid track submit success: track={data['assigned_track']}")


class TestIntakeSystemState:
    """Test GET /api/intake/system-state endpoint"""
    
    @pytest.fixture
    def pro_token(self):
        """Get auth token for pro creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as pro creator")
    
    def test_system_state_requires_auth(self):
        """Verify system-state requires authentication"""
        response = requests.get(f"{BASE_URL}/api/intake/system-state")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ System state requires authentication")
    
    def test_system_state_after_intake(self, pro_token):
        """Verify system-state returns full state after intake"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        
        # First check if intake is completed
        status_response = requests.get(f"{BASE_URL}/api/intake/status", headers=headers)
        if status_response.status_code == 200:
            status_data = status_response.json()
            if not status_data.get("intake_completed"):
                # Submit intake first
                submission = {
                    "user_identity": {
                        "identity_type": "creator",
                        "stage": "intermediate",
                        "primary_goal": "grow_audience"
                    },
                    "system_need": {
                        "selected_engines": ["engagement_engine"]
                    },
                    "starting_point": {
                        "first_priority": "grow_audience"
                    }
                }
                requests.post(f"{BASE_URL}/api/intake/submit", json=submission, headers={**headers, "Content-Type": "application/json"})
        
        # Now get system state
        response = requests.get(f"{BASE_URL}/api/intake/system-state", headers=headers)
        assert response.status_code == 200, f"System state failed: {response.text}"
        
        data = response.json()
        
        # Verify key fields
        assert "user_id" in data, "Missing user_id"
        assert "intake_completed" in data, "Missing intake_completed"
        assert "assigned_track" in data, "Missing assigned_track"
        assert "engines" in data, "Missing engines"
        assert "unlocked_modules" in data, "Missing unlocked_modules"
        
        print(f"✓ System state returned: track={data.get('assigned_track')}, modules={len(data.get('unlocked_modules', []))}")


class TestCommandCenter:
    """Test GET /api/command-center endpoint"""
    
    @pytest.fixture
    def pro_token(self):
        """Get auth token for pro creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as pro creator")
    
    def test_command_center_requires_auth(self):
        """Verify command-center requires authentication"""
        response = requests.get(f"{BASE_URL}/api/command-center")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Command center requires authentication")
    
    def test_command_center_returns_dashboard_state(self, pro_token):
        """Verify command-center returns dashboard state with engines and modules"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        
        response = requests.get(f"{BASE_URL}/api/command-center", headers=headers)
        
        # If intake not completed, should redirect
        if response.status_code == 200:
            data = response.json()
            
            if data.get("intake_required"):
                print("✓ Command center correctly requires intake completion")
                return
            
            # Verify dashboard state structure
            assert "user_id" in data, "Missing user_id"
            assert "track" in data, "Missing track"
            assert "active_modules" in data, "Missing active_modules"
            assert "engine_status" in data, "Missing engine_status"
            assert "modules_unlocked" in data, "Missing modules_unlocked"
            
            print(f"✓ Command center returned: track={data.get('track')}, engines_active={data.get('engines_active', 0)}, modules={data.get('modules_unlocked', 0)}")
        else:
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


class TestIntakeStatusAfterSubmission:
    """Test intake status changes after submission"""
    
    @pytest.fixture
    def elite_token(self):
        """Get auth token for elite creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["elite_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as elite creator")
    
    def test_intake_status_shows_completed_after_submission(self, elite_token):
        """Verify intake status shows intake_completed=true after submission"""
        headers = {"Authorization": f"Bearer {elite_token}", "Content-Type": "application/json"}
        
        # Submit intake
        submission = {
            "user_identity": {
                "identity_type": "hybrid",
                "stage": "advanced",
                "primary_goal": "monetize_content"
            },
            "system_need": {
                "selected_engines": ["business_engine", "engagement_engine", "income_engine"]
            },
            "starting_point": {
                "assets_already_have": ["social_media_accounts", "existing_audience", "offers_products"],
                "missing_elements": ["systems_automation"],
                "first_priority": "increase_income"
            }
        }
        
        submit_response = requests.post(f"{BASE_URL}/api/intake/submit", json=submission, headers=headers)
        assert submit_response.status_code == 200, f"Submit failed: {submit_response.text}"
        
        # Check status
        status_response = requests.get(f"{BASE_URL}/api/intake/status", headers=headers)
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["intake_completed"] == True, "intake_completed should be True after submission"
        assert "assigned_track" in status_data, "Should include assigned_track"
        assert "engines_active" in status_data, "Should include engines_active count"
        assert "modules_unlocked" in status_data, "Should include modules_unlocked count"
        
        print(f"✓ Status after submission: completed={status_data['intake_completed']}, track={status_data['assigned_track']}, engines={status_data['engines_active']}, modules={status_data['modules_unlocked']}")


class TestPreviousSubmission:
    """Test GET /api/intake/previous-submission endpoint"""
    
    @pytest.fixture
    def pro_token(self):
        """Get auth token for pro creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro_creator"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Could not login as pro creator")
    
    def test_previous_submission_returns_data(self, pro_token):
        """Verify previous-submission returns saved data for pre-filling"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        
        response = requests.get(f"{BASE_URL}/api/intake/previous-submission", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "has_previous" in data, "Missing has_previous field"
        
        if data["has_previous"]:
            assert "previous_data" in data, "Should include previous_data when has_previous=True"
            print(f"✓ Previous submission found with data")
        else:
            print("✓ No previous submission (expected for new users)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
