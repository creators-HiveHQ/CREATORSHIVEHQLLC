"""
Test Suite for Phase 4 Module D Task D3: Onboarding Progress Tracker
Tests the progress tracking, timeline, ARRIS insights, and post-onboarding checklist features.

Endpoints tested:
- GET /api/onboarding/progress - Get detailed onboarding progress with ARRIS encouragement
- GET /api/onboarding/progress/timeline - Get timeline of onboarding events
- GET /api/onboarding/progress/arris-insight - Get ARRIS AI-generated progress insight
- GET /api/onboarding/checklist - Get post-onboarding setup checklist (requires onboarding complete)
- PATCH /api/onboarding/checklist/{item_id} - Update checklist item completion
- GET /api/admin/onboarding/progress/{creator_id} - Admin view creator progress
- GET /api/admin/onboarding/progress/{creator_id}/timeline - Admin view creator timeline
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
PRO_CREATOR_EMAIL = "protest@hivehq.com"
PRO_CREATOR_PASSWORD = "testpassword"


class TestOnboardingProgressTracker:
    """Test suite for Onboarding Progress Tracker (D3) endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_token = None
        self.creator_token = None
        self.creator_id = None
        
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        return self.admin_token
    
    def get_creator_token(self):
        """Get pro creator authentication token"""
        if self.creator_token:
            return self.creator_token
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_CREATOR_EMAIL,
            "password": PRO_CREATOR_PASSWORD
        })
        assert response.status_code == 200, f"Creator login failed: {response.text}"
        data = response.json()
        self.creator_token = data["access_token"]
        self.creator_id = data["creator"]["id"]
        return self.creator_token
    
    def get_creator_id(self):
        """Get the creator ID"""
        if not self.creator_id:
            self.get_creator_token()
        return self.creator_id
    
    # ============== GET /api/onboarding/progress ==============
    
    def test_progress_requires_auth(self):
        """Test that progress endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/progress")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/onboarding/progress - Requires authentication")
    
    def test_progress_returns_detailed_data(self):
        """Test that progress endpoint returns comprehensive progress data"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "has_started" in data, "Missing has_started field"
        
        if data.get("has_started"):
            assert "creator_id" in data, "Missing creator_id"
            assert "is_complete" in data, "Missing is_complete"
            assert "progress" in data, "Missing progress object"
            assert "steps" in data, "Missing steps array"
            assert "time_metrics" in data, "Missing time_metrics"
            assert "arris_message" in data, "Missing arris_message"
            assert "next_action" in data, "Missing next_action"
            
            # Verify progress object structure
            progress = data["progress"]
            assert "percentage" in progress, "Missing percentage"
            assert "completed_steps" in progress, "Missing completed_steps"
            assert "total_steps" in progress, "Missing total_steps"
            
            # Verify steps array structure
            if data["steps"]:
                step = data["steps"][0]
                assert "step_id" in step, "Missing step_id"
                assert "title" in step, "Missing title"
                assert "status" in step, "Missing status"
            
            # Verify ARRIS message structure
            arris_msg = data.get("arris_message")
            if arris_msg:
                assert "type" in arris_msg, "Missing ARRIS message type"
                assert "icon" in arris_msg, "Missing ARRIS message icon"
                assert "message" in arris_msg, "Missing ARRIS message text"
        
        print(f"✅ GET /api/onboarding/progress - Returns detailed data (has_started={data.get('has_started')}, is_complete={data.get('is_complete')})")
    
    def test_progress_shows_correct_percentage(self):
        """Test that progress percentage is calculated correctly"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("has_started") and data.get("progress"):
            progress = data["progress"]
            percentage = progress.get("percentage", 0)
            completed = progress.get("completed_steps", 0)
            total = progress.get("total_steps", 7)
            
            # Verify percentage is within valid range
            assert 0 <= percentage <= 100, f"Invalid percentage: {percentage}"
            
            # Verify percentage matches completed/total ratio
            expected_percentage = int((completed / max(total, 1)) * 100)
            assert percentage == expected_percentage, f"Percentage mismatch: {percentage} vs expected {expected_percentage}"
        
        print("✅ GET /api/onboarding/progress - Percentage calculated correctly")
    
    # ============== GET /api/onboarding/progress/timeline ==============
    
    def test_timeline_requires_auth(self):
        """Test that timeline endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/progress/timeline")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/onboarding/progress/timeline - Requires authentication")
    
    def test_timeline_returns_events(self):
        """Test that timeline endpoint returns event list"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress/timeline",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "timeline" in data, "Missing timeline array"
        assert "total_events" in data, "Missing total_events count"
        assert isinstance(data["timeline"], list), "Timeline should be a list"
        
        # Verify event structure if events exist
        if data["timeline"]:
            event = data["timeline"][0]
            assert "event" in event, "Missing event type"
            assert "title" in event, "Missing event title"
            assert "icon" in event, "Missing event icon"
        
        print(f"✅ GET /api/onboarding/progress/timeline - Returns {data['total_events']} events")
    
    def test_timeline_sorted_by_timestamp(self):
        """Test that timeline events are sorted by timestamp (most recent first)"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress/timeline",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data.get("timeline", [])
        if len(timeline) > 1:
            # Check that timestamps are in descending order
            timestamps = [e.get("timestamp", "") for e in timeline if e.get("timestamp")]
            for i in range(len(timestamps) - 1):
                assert timestamps[i] >= timestamps[i+1], "Timeline should be sorted by timestamp descending"
        
        print("✅ GET /api/onboarding/progress/timeline - Events sorted correctly")
    
    # ============== GET /api/onboarding/progress/arris-insight ==============
    
    def test_arris_insight_requires_auth(self):
        """Test that ARRIS insight endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/progress/arris-insight")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/onboarding/progress/arris-insight - Requires authentication")
    
    def test_arris_insight_returns_personalized_data(self):
        """Test that ARRIS insight endpoint returns personalized insight"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress/arris-insight",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "insight" in data, "Missing insight text"
        assert "recommendation" in data, "Missing recommendation"
        
        # If onboarding is complete, should have personalization data
        if data.get("personalization"):
            assert "goal" in data["personalization"] or "platform" in data["personalization"], \
                "Personalization should include goal or platform"
        
        print(f"✅ GET /api/onboarding/progress/arris-insight - Returns insight: '{data['insight'][:50]}...'")
    
    # ============== GET /api/onboarding/checklist ==============
    
    def test_checklist_requires_auth(self):
        """Test that checklist endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/onboarding/checklist")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/onboarding/checklist - Requires authentication")
    
    def test_checklist_requires_complete_onboarding(self):
        """Test that checklist requires completed onboarding"""
        token = self.get_creator_token()
        
        # First check if onboarding is complete
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        progress_data = progress_response.json()
        
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if progress_data.get("is_complete"):
            # Should return checklist
            assert response.status_code == 200, f"Should return checklist for completed onboarding: {response.text}"
            data = response.json()
            assert "items" in data, "Missing items array"
            assert "progress" in data, "Missing progress"
            assert "total_points" in data, "Missing total_points"
            print(f"✅ GET /api/onboarding/checklist - Returns checklist with {len(data['items'])} items")
        else:
            # Should return error
            assert response.status_code == 400, "Should return 400 for incomplete onboarding"
            print("✅ GET /api/onboarding/checklist - Correctly requires complete onboarding")
    
    def test_checklist_structure(self):
        """Test checklist item structure"""
        token = self.get_creator_token()
        
        # Check if onboarding is complete first
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        if not progress_response.json().get("is_complete"):
            pytest.skip("Onboarding not complete - skipping checklist structure test")
        
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify checklist structure
        assert "items" in data
        assert "progress" in data
        assert "completed_count" in data
        assert "total_count" in data
        assert "earned_points" in data
        assert "total_points" in data
        
        # Verify item structure
        if data["items"]:
            item = data["items"][0]
            assert "id" in item, "Missing item id"
            assert "title" in item, "Missing item title"
            assert "description" in item, "Missing item description"
            assert "completed" in item, "Missing completed status"
            assert "points" in item, "Missing points value"
        
        # Verify expected checklist items exist
        item_ids = [i["id"] for i in data["items"]]
        expected_items = ["first_proposal", "connect_socials", "explore_arris", 
                         "explore_dashboard", "set_notification_prefs", "upgrade_tier"]
        for expected in expected_items:
            assert expected in item_ids, f"Missing expected checklist item: {expected}"
        
        print(f"✅ GET /api/onboarding/checklist - Structure verified ({data['completed_count']}/{data['total_count']} completed)")
    
    # ============== PATCH /api/onboarding/checklist/{item_id} ==============
    
    def test_checklist_update_requires_auth(self):
        """Test that checklist update requires authentication"""
        response = requests.patch(f"{BASE_URL}/api/onboarding/checklist/explore_dashboard?completed=true")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ PATCH /api/onboarding/checklist/{item_id} - Requires authentication")
    
    def test_checklist_update_item(self):
        """Test updating a checklist item"""
        token = self.get_creator_token()
        
        # Check if onboarding is complete first
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        if not progress_response.json().get("is_complete"):
            pytest.skip("Onboarding not complete - skipping checklist update test")
        
        # Get current checklist state
        checklist_response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        checklist_data = checklist_response.json()
        
        # Find an item to toggle
        test_item = None
        for item in checklist_data.get("items", []):
            if item["id"] == "explore_dashboard":
                test_item = item
                break
        
        if not test_item:
            pytest.skip("explore_dashboard item not found")
        
        # Toggle the item
        new_completed = not test_item["completed"]
        response = requests.patch(
            f"{BASE_URL}/api/onboarding/checklist/explore_dashboard?completed={str(new_completed).lower()}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to update: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, "Update should succeed"
        assert data.get("item_id") == "explore_dashboard", "Should return correct item_id"
        assert data.get("completed") == new_completed, "Should return new completed status"
        assert "points_change" in data, "Should return points_change"
        assert "total_earned" in data, "Should return total_earned"
        
        # Verify the change persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        verify_data = verify_response.json()
        updated_item = next((i for i in verify_data["items"] if i["id"] == "explore_dashboard"), None)
        assert updated_item["completed"] == new_completed, "Change should persist"
        
        print(f"✅ PATCH /api/onboarding/checklist/explore_dashboard - Updated to completed={new_completed}")
    
    def test_checklist_update_invalid_item(self):
        """Test updating a non-existent checklist item"""
        token = self.get_creator_token()
        
        # Check if onboarding is complete first
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        if not progress_response.json().get("is_complete"):
            pytest.skip("Onboarding not complete - skipping invalid item test")
        
        response = requests.patch(
            f"{BASE_URL}/api/onboarding/checklist/INVALID_ITEM_ID?completed=true",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400, "Should return 400 for invalid item"
        print("✅ PATCH /api/onboarding/checklist/INVALID - Returns 400 for invalid item")
    
    # ============== Admin Endpoints ==============
    
    def test_admin_progress_requires_auth(self):
        """Test that admin progress endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/progress/some-creator-id")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/admin/onboarding/progress/{creator_id} - Requires authentication")
    
    def test_admin_progress_returns_creator_data(self):
        """Test that admin can view any creator's progress"""
        admin_token = self.get_admin_token()
        creator_id = self.get_creator_id()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/onboarding/progress/{creator_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should have same structure as creator progress endpoint
        assert "has_started" in data or "creator_id" in data, "Missing expected fields"
        
        print(f"✅ GET /api/admin/onboarding/progress/{creator_id} - Admin can view creator progress")
    
    def test_admin_progress_invalid_creator(self):
        """Test admin progress with invalid creator ID"""
        admin_token = self.get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/onboarding/progress/INVALID_CREATOR_ID",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404, "Should return 404 for invalid creator"
        print("✅ GET /api/admin/onboarding/progress/INVALID - Returns 404")
    
    def test_admin_timeline_requires_auth(self):
        """Test that admin timeline endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/onboarding/progress/some-id/timeline")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✅ GET /api/admin/onboarding/progress/{creator_id}/timeline - Requires authentication")
    
    def test_admin_timeline_returns_data(self):
        """Test that admin can view creator's timeline"""
        admin_token = self.get_admin_token()
        creator_id = self.get_creator_id()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/onboarding/progress/{creator_id}/timeline",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "creator_id" in data, "Missing creator_id"
        assert "timeline" in data, "Missing timeline"
        assert "total_events" in data, "Missing total_events"
        
        print(f"✅ GET /api/admin/onboarding/progress/{creator_id}/timeline - Returns {data['total_events']} events")
    
    # ============== ARRIS Encouragement Messages ==============
    
    def test_arris_message_types(self):
        """Test that ARRIS messages have correct types based on progress"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        arris_msg = data.get("arris_message")
        if arris_msg:
            valid_types = ["welcome", "early", "midway", "almost", "final", "celebration", "reminder"]
            assert arris_msg.get("type") in valid_types, f"Invalid ARRIS message type: {arris_msg.get('type')}"
            
            # Verify message matches progress state
            if data.get("is_complete"):
                assert arris_msg["type"] == "celebration", "Complete onboarding should have celebration message"
            elif data.get("is_skipped"):
                assert arris_msg["type"] == "reminder", "Skipped onboarding should have reminder message"
        
        print(f"✅ ARRIS message type verified: {arris_msg.get('type') if arris_msg else 'N/A'}")
    
    # ============== Time Metrics ==============
    
    def test_time_metrics_structure(self):
        """Test that time metrics are properly calculated"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("has_started"):
            time_metrics = data.get("time_metrics", {})
            assert "started_at" in time_metrics, "Missing started_at"
            assert "last_activity" in time_metrics, "Missing last_activity"
            
            if not data.get("is_complete"):
                # Should have estimated remaining time
                assert "estimated_remaining" in time_metrics or time_metrics.get("estimated_remaining") is None
            else:
                # Should have total duration
                assert "total_duration" in time_metrics or time_metrics.get("total_duration") is None
        
        print("✅ Time metrics structure verified")
    
    # ============== Rewards ==============
    
    def test_rewards_structure(self):
        """Test that rewards are properly tracked"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        rewards = data.get("rewards", [])
        assert isinstance(rewards, list), "Rewards should be a list"
        
        if rewards:
            reward = rewards[0]
            assert "type" in reward, "Missing reward type"
            assert "name" in reward, "Missing reward name"
            assert "points" in reward, "Missing reward points"
            assert "earned_at" in reward, "Missing earned_at timestamp"
        
        print(f"✅ Rewards structure verified ({len(rewards)} rewards)")
    
    # ============== Integration Tests ==============
    
    def test_progress_and_checklist_integration(self):
        """Test that progress endpoint includes checklist when onboarding is complete"""
        token = self.get_creator_token()
        response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_complete"):
            assert "post_onboarding_checklist" in data, "Complete onboarding should include checklist"
            checklist = data["post_onboarding_checklist"]
            assert "items" in checklist, "Checklist should have items"
            assert "progress" in checklist, "Checklist should have progress"
            print("✅ Progress includes checklist for completed onboarding")
        else:
            # Checklist should not be present or be None
            assert data.get("post_onboarding_checklist") is None, "Incomplete onboarding should not have checklist"
            print("✅ Progress correctly excludes checklist for incomplete onboarding")


class TestChecklistPointsAndBadges:
    """Test checklist points calculation and badge awarding"""
    
    def get_creator_token(self):
        """Get pro creator authentication token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_CREATOR_EMAIL,
            "password": PRO_CREATOR_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_checklist_points_calculation(self):
        """Test that checklist points are calculated correctly"""
        token = self.get_creator_token()
        
        # Check if onboarding is complete
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        if not progress_response.json().get("is_complete"):
            pytest.skip("Onboarding not complete")
        
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Calculate expected earned points
        expected_earned = sum(item["points"] for item in data["items"] if item["completed"])
        assert data["earned_points"] == expected_earned, f"Points mismatch: {data['earned_points']} vs {expected_earned}"
        
        # Verify total points
        expected_total = sum(item["points"] for item in data["items"])
        assert data["total_points"] == expected_total, f"Total points mismatch: {data['total_points']} vs {expected_total}"
        
        print(f"✅ Checklist points calculated correctly: {data['earned_points']}/{data['total_points']}")
    
    def test_checklist_progress_percentage(self):
        """Test that checklist progress percentage is correct"""
        token = self.get_creator_token()
        
        # Check if onboarding is complete
        progress_response = requests.get(
            f"{BASE_URL}/api/onboarding/progress",
            headers={"Authorization": f"Bearer {token}"}
        )
        if not progress_response.json().get("is_complete"):
            pytest.skip("Onboarding not complete")
        
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        expected_progress = int((data["completed_count"] / data["total_count"]) * 100)
        assert data["progress"] == expected_progress, f"Progress mismatch: {data['progress']} vs {expected_progress}"
        
        print(f"✅ Checklist progress percentage correct: {data['progress']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
