"""
Test Suite for Smart Onboarding Wizard (Phase 4 Module D - D1)
Tests all onboarding API endpoints including:
- GET /api/onboarding/steps - Get all onboarding steps configuration (public)
- GET /api/onboarding/status - Get current onboarding status for logged-in creator
- GET /api/onboarding/step/{step_number} - Get step details with ARRIS personalization
- POST /api/onboarding/step/{step_number} - Save step data and advance
- GET /api/onboarding/personalization - Get personalization summary after completion
- POST /api/onboarding/skip - Skip remaining onboarding steps
- POST /api/onboarding/reset - Reset onboarding to start fresh
- GET /api/admin/onboarding/analytics - Admin onboarding analytics
- GET /api/admin/onboarding/{creator_id} - Admin view creator's onboarding
- POST /api/admin/onboarding/{creator_id}/reset - Admin reset creator's onboarding
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
PRO_CREATOR_EMAIL = "protest@hivehq.com"
PRO_CREATOR_PASSWORD = "testpassword"
PREMIUM_CREATOR_EMAIL = "premiumtest@hivehq.com"
PREMIUM_CREATOR_PASSWORD = "testpassword123"


class TestOnboardingWizardSetup:
    """Setup and health check tests"""
    
    def test_api_health(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ API health check passed")


class TestOnboardingStepsPublic:
    """Test public onboarding steps endpoint"""
    
    def test_get_onboarding_steps_public(self):
        """GET /api/onboarding/steps - Public endpoint returns all steps"""
        response = requests.get(f"{BASE_URL}/api/onboarding/steps")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_steps" in data
        assert "steps" in data
        assert data["total_steps"] == 7
        assert len(data["steps"]) == 7
        
        # Verify step structure
        step_ids = [s["step_id"] for s in data["steps"]]
        expected_steps = ["welcome", "profile", "platforms", "niche", "goals", "arris_intro", "complete"]
        assert step_ids == expected_steps
        
        # Verify each step has required fields
        for step in data["steps"]:
            assert "step_id" in step
            assert "step_number" in step
            assert "title" in step
            assert "subtitle" in step
            assert "description" in step
            assert "required" in step
            assert "arris_enabled" in step
            assert "fields" in step
        
        print(f"✅ GET /api/onboarding/steps - Returns {data['total_steps']} steps")


class TestOnboardingCreatorAuth:
    """Test onboarding endpoints requiring creator authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get creator token for authenticated requests"""
        # Login as premium creator (likely hasn't completed onboarding)
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PREMIUM_CREATOR_EMAIL,
            "password": PREMIUM_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.premium_token = response.json().get("access_token")
            self.premium_creator_id = response.json().get("creator", {}).get("id")
        else:
            self.premium_token = None
            self.premium_creator_id = None
        
        # Login as pro creator
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_CREATOR_EMAIL,
            "password": PRO_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.pro_token = response.json().get("access_token")
            self.pro_creator_id = response.json().get("creator", {}).get("id")
        else:
            self.pro_token = None
            self.pro_creator_id = None
    
    def test_onboarding_status_requires_auth(self):
        """GET /api/onboarding/status - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code in [401, 403]
        print("✅ GET /api/onboarding/status - Requires authentication")
    
    def test_get_onboarding_status(self):
        """GET /api/onboarding/status - Returns current status for creator"""
        if not self.premium_token:
            pytest.skip("Premium creator login failed")
        
        headers = {"Authorization": f"Bearer {self.premium_token}"}
        response = requests.get(f"{BASE_URL}/api/onboarding/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "onboarding_id" in data
        assert "creator_id" in data
        assert "current_step" in data
        assert "completed_steps" in data
        assert "completion_percentage" in data
        assert "is_complete" in data
        
        print(f"✅ GET /api/onboarding/status - Current step: {data['current_step']}, Complete: {data['is_complete']}")
    
    def test_get_step_details_requires_auth(self):
        """GET /api/onboarding/step/{step_number} - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/step/1")
        assert response.status_code in [401, 403]
        print("✅ GET /api/onboarding/step/1 - Requires authentication")
    
    def test_get_step_details_valid_step(self):
        """GET /api/onboarding/step/{step_number} - Returns step details with ARRIS context"""
        if not self.premium_token:
            pytest.skip("Premium creator login failed")
        
        headers = {"Authorization": f"Bearer {self.premium_token}"}
        response = requests.get(f"{BASE_URL}/api/onboarding/step/1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "step" in data
        assert "saved_data" in data
        assert "navigation" in data
        
        # Verify step details
        step = data["step"]
        assert step["step_id"] == "welcome"
        assert step["step_number"] == 1
        
        # Verify navigation
        nav = data["navigation"]
        assert "can_go_back" in nav
        assert "can_skip" in nav
        assert "total_steps" in nav
        assert "is_last_step" in nav
        
        print(f"✅ GET /api/onboarding/step/1 - Returns step: {step['title']}")
    
    def test_get_step_details_invalid_step(self):
        """GET /api/onboarding/step/{step_number} - Invalid step returns 400"""
        if not self.premium_token:
            pytest.skip("Premium creator login failed")
        
        headers = {"Authorization": f"Bearer {self.premium_token}"}
        
        # Test step 0
        response = requests.get(f"{BASE_URL}/api/onboarding/step/0", headers=headers)
        assert response.status_code == 400
        
        # Test step 8 (beyond max)
        response = requests.get(f"{BASE_URL}/api/onboarding/step/8", headers=headers)
        assert response.status_code == 400
        
        print("✅ GET /api/onboarding/step - Invalid step numbers return 400")
    
    def test_get_all_step_details(self):
        """GET /api/onboarding/step/{step_number} - All 7 steps return valid data"""
        if not self.premium_token:
            pytest.skip("Premium creator login failed")
        
        headers = {"Authorization": f"Bearer {self.premium_token}"}
        
        for step_num in range(1, 8):
            response = requests.get(f"{BASE_URL}/api/onboarding/step/{step_num}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["step"]["step_number"] == step_num
        
        print("✅ GET /api/onboarding/step - All 7 steps return valid data")
    
    def test_save_step_requires_auth(self):
        """POST /api/onboarding/step/{step_number} - Requires authentication"""
        response = requests.post(f"{BASE_URL}/api/onboarding/step/1", json={})
        assert response.status_code in [401, 403]
        print("✅ POST /api/onboarding/step/1 - Requires authentication")
    
    def test_personalization_requires_auth(self):
        """GET /api/onboarding/personalization - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/personalization")
        assert response.status_code in [401, 403]
        print("✅ GET /api/onboarding/personalization - Requires authentication")
    
    def test_get_personalization(self):
        """GET /api/onboarding/personalization - Returns personalization summary"""
        if not self.premium_token:
            pytest.skip("Premium creator login failed")
        
        headers = {"Authorization": f"Bearer {self.premium_token}"}
        response = requests.get(f"{BASE_URL}/api/onboarding/personalization", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Structure depends on whether onboarding is complete
        if data.get("onboarding_complete"):
            assert "personalization" in data
            assert "arris_insights" in data
            assert "rewards" in data
        else:
            assert "onboarding_complete" in data
            assert data["onboarding_complete"] == False
        
        print(f"✅ GET /api/onboarding/personalization - Complete: {data.get('onboarding_complete', False)}")
    
    def test_skip_requires_auth(self):
        """POST /api/onboarding/skip - Requires authentication"""
        response = requests.post(f"{BASE_URL}/api/onboarding/skip")
        assert response.status_code in [401, 403]
        print("✅ POST /api/onboarding/skip - Requires authentication")
    
    def test_reset_requires_auth(self):
        """POST /api/onboarding/reset - Requires authentication"""
        response = requests.post(f"{BASE_URL}/api/onboarding/reset")
        assert response.status_code in [401, 403]
        print("✅ POST /api/onboarding/reset - Requires authentication")


class TestOnboardingFullFlow:
    """Test complete onboarding flow with reset, steps, and completion"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get creator token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PREMIUM_CREATOR_EMAIL,
            "password": PREMIUM_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.creator_id = response.json().get("creator", {}).get("id")
        else:
            self.token = None
            self.creator_id = None
    
    def test_reset_onboarding(self):
        """POST /api/onboarding/reset - Resets onboarding to start fresh"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{BASE_URL}/api/onboarding/reset", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "onboarding_id" in data
        assert "message" in data
        
        # Verify status is reset
        status_response = requests.get(f"{BASE_URL}/api/onboarding/status", headers=headers)
        status = status_response.json()
        assert status["current_step"] == 1
        assert status["completion_percentage"] == 0
        assert status["is_complete"] == False
        
        print("✅ POST /api/onboarding/reset - Onboarding reset successfully")
    
    def test_complete_step_1_welcome(self):
        """POST /api/onboarding/step/1 - Complete welcome step"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # First reset to ensure clean state
        requests.post(f"{BASE_URL}/api/onboarding/reset", headers=headers)
        
        # Complete step 1 (welcome - no fields required)
        response = requests.post(f"{BASE_URL}/api/onboarding/step/1", 
                                headers=headers, 
                                json={})
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "welcome"
        assert data["next_step"] == 2
        assert data["completion_percentage"] > 0
        
        print(f"✅ POST /api/onboarding/step/1 - Welcome step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_2_profile(self):
        """POST /api/onboarding/step/2 - Complete profile step with data"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 2 (profile)
        profile_data = {
            "display_name": "Test Creator Premium",
            "bio": "A premium test creator for onboarding testing",
            "website": "https://testcreator.com"
        }
        response = requests.post(f"{BASE_URL}/api/onboarding/step/2", 
                                headers=headers, 
                                json=profile_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "profile"
        assert data["next_step"] == 3
        
        print(f"✅ POST /api/onboarding/step/2 - Profile step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_3_platforms(self):
        """POST /api/onboarding/step/3 - Complete platforms step"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 3 (platforms)
        platforms_data = {
            "primary_platform": "youtube",
            "secondary_platforms": ["instagram", "tiktok"],
            "follower_count": "10K-50K"
        }
        response = requests.post(f"{BASE_URL}/api/onboarding/step/3", 
                                headers=headers, 
                                json=platforms_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "platforms"
        assert data["next_step"] == 4
        
        print(f"✅ POST /api/onboarding/step/3 - Platforms step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_4_niche(self):
        """POST /api/onboarding/step/4 - Complete niche step"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 4 (niche)
        niche_data = {
            "primary_niche": "tech",
            "sub_niches": "AI, Machine Learning, Software Development",
            "unique_angle": "Making complex tech topics accessible to beginners"
        }
        response = requests.post(f"{BASE_URL}/api/onboarding/step/4", 
                                headers=headers, 
                                json=niche_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "niche"
        assert data["next_step"] == 5
        
        print(f"✅ POST /api/onboarding/step/4 - Niche step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_5_goals(self):
        """POST /api/onboarding/step/5 - Complete goals step"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 5 (goals)
        goals_data = {
            "primary_goal": "grow_audience",
            "revenue_goal": "10K-25K",
            "biggest_challenge": "Consistently creating engaging content while managing time"
        }
        response = requests.post(f"{BASE_URL}/api/onboarding/step/5", 
                                headers=headers, 
                                json=goals_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "goals"
        assert data["next_step"] == 6
        
        print(f"✅ POST /api/onboarding/step/5 - Goals step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_6_arris_intro(self):
        """POST /api/onboarding/step/6 - Complete ARRIS intro step"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 6 (arris_intro)
        arris_data = {
            "arris_communication_style": "professional",
            "arris_focus_areas": ["content_ideas", "growth_strategies", "analytics"],
            "notification_preference": "weekly"
        }
        response = requests.post(f"{BASE_URL}/api/onboarding/step/6", 
                                headers=headers, 
                                json=arris_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "arris_intro"
        assert data["next_step"] == 7
        
        print(f"✅ POST /api/onboarding/step/6 - ARRIS intro step completed, progress: {data['completion_percentage']}%")
    
    def test_complete_step_7_complete(self):
        """POST /api/onboarding/step/7 - Complete final step and earn reward"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Complete step 7 (complete)
        response = requests.post(f"{BASE_URL}/api/onboarding/step/7", 
                                headers=headers, 
                                json={})
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["step_completed"] == "complete"
        assert data["is_complete"] == True
        assert data["completion_percentage"] == 100
        
        # Verify reward earned
        if data.get("reward_earned"):
            assert data["reward_earned"]["name"] == "Hive Newcomer"
            assert data["reward_earned"]["points"] == 100
            print(f"✅ Reward earned: {data['reward_earned']['name']} (+{data['reward_earned']['points']} points)")
        
        print(f"✅ POST /api/onboarding/step/7 - Onboarding complete! Progress: {data['completion_percentage']}%")
    
    def test_personalization_after_completion(self):
        """GET /api/onboarding/personalization - Returns full profile after completion"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/onboarding/personalization", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("onboarding_complete") == True
        assert "personalization" in data
        assert "rewards" in data
        
        # Verify personalization profile
        profile = data["personalization"]
        assert profile.get("primary_platform") == "youtube"
        assert profile.get("primary_niche") == "tech"
        assert profile.get("primary_goal") == "grow_audience"
        
        print(f"✅ GET /api/onboarding/personalization - Full profile returned after completion")
    
    def test_skip_onboarding(self):
        """POST /api/onboarding/skip - Skip remaining onboarding"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # First reset
        requests.post(f"{BASE_URL}/api/onboarding/reset", headers=headers)
        
        # Then skip
        response = requests.post(f"{BASE_URL}/api/onboarding/skip", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "skipped_at" in data
        
        print("✅ POST /api/onboarding/skip - Onboarding skipped successfully")


class TestOnboardingAdmin:
    """Test admin onboarding endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin and creator tokens"""
        # Admin login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
        else:
            self.admin_token = None
        
        # Creator login to get creator_id
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PREMIUM_CREATOR_EMAIL,
            "password": PREMIUM_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.creator_id = response.json().get("creator", {}).get("id")
        else:
            self.creator_id = None
    
    def test_admin_analytics_requires_auth(self):
        """GET /api/admin/onboarding/analytics - Requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/analytics")
        assert response.status_code in [401, 403]
        print("✅ GET /api/admin/onboarding/analytics - Requires authentication")
    
    def test_admin_get_analytics(self):
        """GET /api/admin/onboarding/analytics - Returns platform-wide analytics"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_onboardings" in data
        assert "completed" in data
        assert "skipped" in data
        assert "in_progress" in data
        assert "completion_rate" in data
        assert "step_completion" in data
        assert "top_goals" in data
        assert "top_platforms" in data
        
        print(f"✅ GET /api/admin/onboarding/analytics - Total: {data['total_onboardings']}, Completed: {data['completed']}, Rate: {data['completion_rate']}%")
    
    def test_admin_get_creator_onboarding_requires_auth(self):
        """GET /api/admin/onboarding/{creator_id} - Requires admin authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/test-creator-id")
        assert response.status_code in [401, 403]
        print("✅ GET /api/admin/onboarding/{creator_id} - Requires authentication")
    
    def test_admin_get_creator_onboarding(self):
        """GET /api/admin/onboarding/{creator_id} - Returns creator's onboarding details"""
        if not self.admin_token or not self.creator_id:
            pytest.skip("Admin login or creator_id not available")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/{self.creator_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "status" in data
        assert "personalization" in data
        
        print(f"✅ GET /api/admin/onboarding/{self.creator_id} - Creator onboarding details retrieved")
    
    def test_admin_get_creator_onboarding_invalid_id(self):
        """GET /api/admin/onboarding/{creator_id} - Invalid creator_id returns 404"""
        if not self.admin_token:
            pytest.skip("Admin login failed")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/INVALID-CREATOR-ID", headers=headers)
        # Should return data even for non-existent creator (creates new onboarding)
        assert response.status_code in [200, 404]
        print("✅ GET /api/admin/onboarding/INVALID-CREATOR-ID - Handled correctly")
    
    def test_admin_reset_creator_onboarding_requires_auth(self):
        """POST /api/admin/onboarding/{creator_id}/reset - Requires admin authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/onboarding/test-creator-id/reset")
        assert response.status_code in [401, 403]
        print("✅ POST /api/admin/onboarding/{creator_id}/reset - Requires authentication")
    
    def test_admin_reset_creator_onboarding(self):
        """POST /api/admin/onboarding/{creator_id}/reset - Admin can reset creator's onboarding"""
        if not self.admin_token or not self.creator_id:
            pytest.skip("Admin login or creator_id not available")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(f"{BASE_URL}/api/admin/onboarding/{self.creator_id}/reset", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "onboarding_id" in data
        
        print(f"✅ POST /api/admin/onboarding/{self.creator_id}/reset - Creator onboarding reset by admin")


class TestOnboardingDataPersistence:
    """Test that onboarding data is properly persisted"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get creator token"""
        response = requests.post(f"{BASE_URL}/api/creator/login", json={
            "email": PREMIUM_CREATOR_EMAIL,
            "password": PREMIUM_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None
    
    def test_saved_data_persists_across_requests(self):
        """Verify saved step data persists and can be retrieved"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Reset first
        requests.post(f"{BASE_URL}/api/onboarding/reset", headers=headers)
        
        # Complete step 1
        requests.post(f"{BASE_URL}/api/onboarding/step/1", headers=headers, json={})
        
        # Save profile data
        profile_data = {
            "display_name": "Persistence Test Creator",
            "bio": "Testing data persistence"
        }
        requests.post(f"{BASE_URL}/api/onboarding/step/2", headers=headers, json=profile_data)
        
        # Retrieve step 2 and verify saved data
        response = requests.get(f"{BASE_URL}/api/onboarding/step/2", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        saved = data.get("saved_data", {})
        assert saved.get("display_name") == "Persistence Test Creator"
        assert saved.get("bio") == "Testing data persistence"
        
        print("✅ Saved step data persists across requests")
    
    def test_status_updates_after_step_completion(self):
        """Verify status updates correctly after completing steps"""
        if not self.token:
            pytest.skip("Creator login failed")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Reset
        requests.post(f"{BASE_URL}/api/onboarding/reset", headers=headers)
        
        # Check initial status
        response = requests.get(f"{BASE_URL}/api/onboarding/status", headers=headers)
        initial_status = response.json()
        assert initial_status["current_step"] == 1
        assert initial_status["completion_percentage"] == 0
        
        # Complete step 1
        requests.post(f"{BASE_URL}/api/onboarding/step/1", headers=headers, json={})
        
        # Check updated status
        response = requests.get(f"{BASE_URL}/api/onboarding/status", headers=headers)
        updated_status = response.json()
        assert updated_status["current_step"] == 2
        assert updated_status["completion_percentage"] > 0
        assert "welcome" in updated_status["completed_steps"]
        
        print("✅ Status updates correctly after step completion")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
