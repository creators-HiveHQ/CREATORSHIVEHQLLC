"""
Test ARRIS Activity Feed Feature
Tests for real-time activity tracking and queue position updates for Premium users

Endpoints tested:
- GET /api/arris/activity-feed - Main activity feed (Premium gets full access)
- GET /api/arris/my-queue-position - Queue position for Premium users (403 for non-Premium)
- GET /api/arris/live-stats - Queue statistics (all authenticated users)
- GET /api/arris/recent-activity - Anonymized activity list (all authenticated users)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://aigenthq-1.preview.emergentagent.com')

# Test credentials
PRO_CREATOR = {
    "email": "protest@example.com",
    "password": "testpassword"
}

PREMIUM_CREATOR = {
    "email": "premium@example.com",
    "password": "testpassword"
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def pro_token(api_client):
    """Get Pro tier creator token"""
    response = api_client.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Pro creator login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def premium_token(api_client):
    """Get Premium tier creator token"""
    response = api_client.post(f"{BASE_URL}/api/creators/login", json=PREMIUM_CREATOR)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Premium creator login failed: {response.status_code} - {response.text}")


class TestArrisActivityFeedEndpoint:
    """Tests for GET /api/arris/activity-feed"""
    
    def test_activity_feed_requires_auth(self, api_client):
        """Activity feed should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/arris/activity-feed")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_activity_feed_pro_user_limited_access(self, api_client, pro_token):
        """Pro user should get activity feed but with has_premium_access=false"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/activity-feed", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Pro user should NOT have premium access
        assert "has_premium_access" in data, "Response should include has_premium_access field"
        assert data["has_premium_access"] == False, "Pro user should have has_premium_access=false"
        
        # Should still have live_status
        assert "live_status" in data, "Response should include live_status"
        
        # Pro user should NOT have my_queue_items (or empty)
        assert data.get("my_queue_items", []) == [], "Pro user should not have my_queue_items"
        
        # Should have feature_highlights for upgrade prompt
        assert "feature_highlights" in data, "Pro user should see feature_highlights"
    
    def test_activity_feed_premium_user_full_access(self, api_client, premium_token):
        """Premium user should get full activity feed with has_premium_access=true"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/activity-feed", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Premium user should have premium access
        assert "has_premium_access" in data, "Response should include has_premium_access field"
        assert data["has_premium_access"] == True, "Premium user should have has_premium_access=true"
        
        # Should have live_status with queue_stats
        assert "live_status" in data, "Response should include live_status"
        live_status = data["live_status"]
        assert "queue_stats" in live_status, "live_status should include queue_stats"
        assert "recent_activity" in live_status, "live_status should include recent_activity"
        
        # Premium user should have my_queue_items (even if empty)
        assert "my_queue_items" in data, "Premium user should have my_queue_items field"
        
        # Should NOT have feature_highlights (already premium)
        assert data.get("feature_highlights") is None, "Premium user should not see feature_highlights"
    
    def test_activity_feed_live_status_structure(self, api_client, premium_token):
        """Verify live_status has correct structure"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/activity-feed", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        live_status = data["live_status"]
        
        # Check queue_stats structure
        queue_stats = live_status.get("queue_stats", {})
        expected_fields = [
            "fast_queue_length",
            "standard_queue_length",
            "total_queue_length",
            "currently_processing",
            "total_processed",
            "avg_fast_time",
            "avg_standard_time"
        ]
        for field in expected_fields:
            assert field in queue_stats, f"queue_stats should include {field}"
        
        # Check timestamp
        assert "timestamp" in live_status, "live_status should include timestamp"


class TestArrisMyQueuePositionEndpoint:
    """Tests for GET /api/arris/my-queue-position"""
    
    def test_queue_position_requires_auth(self, api_client):
        """Queue position should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/arris/my-queue-position")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_queue_position_pro_user_forbidden(self, api_client, pro_token):
        """Pro user should get 403 for queue position endpoint"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/my-queue-position", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        data = response.json()
        detail = data.get("detail", {})
        
        # Check error structure
        assert detail.get("error") == "feature_gated", "Should return feature_gated error"
        assert "premium" in detail.get("required_tier", "").lower(), "Should indicate Premium required"
        assert "upgrade_url" in detail, "Should include upgrade_url"
    
    def test_queue_position_premium_user_allowed(self, api_client, premium_token):
        """Premium user should be able to access queue position"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/my-queue-position", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have queue_items and queue_stats
        assert "queue_items" in data, "Response should include queue_items"
        assert "queue_stats" in data, "Response should include queue_stats"
        assert "total_in_queue" in data, "Response should include total_in_queue"


class TestArrisLiveStatsEndpoint:
    """Tests for GET /api/arris/live-stats"""
    
    def test_live_stats_requires_auth(self, api_client):
        """Live stats should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/arris/live-stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_live_stats_pro_user_allowed(self, api_client, pro_token):
        """Pro user should be able to access live stats"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/live-stats", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check response structure
        expected_fields = [
            "fast_queue",
            "standard_queue",
            "total_queued",
            "currently_processing",
            "total_processed_today",
            "avg_processing_time",
            "estimated_wait",
            "timestamp"
        ]
        for field in expected_fields:
            assert field in data, f"Response should include {field}"
        
        # Check nested structures
        assert "fast" in data["avg_processing_time"], "avg_processing_time should include fast"
        assert "standard" in data["avg_processing_time"], "avg_processing_time should include standard"
        assert "fast_queue" in data["estimated_wait"], "estimated_wait should include fast_queue"
        assert "standard_queue" in data["estimated_wait"], "estimated_wait should include standard_queue"
    
    def test_live_stats_premium_user_allowed(self, api_client, premium_token):
        """Premium user should be able to access live stats"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/live-stats", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify numeric values
        assert isinstance(data["fast_queue"], int), "fast_queue should be integer"
        assert isinstance(data["standard_queue"], int), "standard_queue should be integer"
        assert isinstance(data["total_queued"], int), "total_queued should be integer"
        assert isinstance(data["currently_processing"], int), "currently_processing should be integer"


class TestArrisRecentActivityEndpoint:
    """Tests for GET /api/arris/recent-activity"""
    
    def test_recent_activity_requires_auth(self, api_client):
        """Recent activity should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_recent_activity_pro_user_allowed(self, api_client, pro_token):
        """Pro user should be able to access recent activity"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "activity" in data, "Response should include activity"
        assert "count" in data, "Response should include count"
        assert isinstance(data["activity"], list), "activity should be a list"
    
    def test_recent_activity_premium_user_allowed(self, api_client, premium_token):
        """Premium user should be able to access recent activity"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "activity" in data, "Response should include activity"
        assert "count" in data, "Response should include count"
    
    def test_recent_activity_limit_parameter(self, api_client, pro_token):
        """Test limit parameter for recent activity"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        
        # Test with limit=5
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity?limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 5, "Count should respect limit parameter"
        
        # Test with limit=30 (max)
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity?limit=30", headers=headers)
        assert response.status_code == 200


class TestArrisActivityFeedDataIntegrity:
    """Tests for data integrity and anonymization"""
    
    def test_activity_feed_anonymizes_creator_data(self, api_client, premium_token):
        """Activity feed should anonymize creator data for privacy"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/activity-feed", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check recent_activity for anonymization
        recent_activity = data.get("live_status", {}).get("recent_activity", [])
        for activity in recent_activity:
            # Creator names should be anonymized (e.g., "Jo***")
            creator_name = activity.get("creator_name", "")
            if creator_name:
                assert "***" in creator_name or len(creator_name) <= 5, \
                    f"Creator name should be anonymized: {creator_name}"
            
            # Creator IDs should be anonymized
            creator_id = activity.get("creator_id", "")
            if creator_id:
                assert creator_id == "***" or creator_id.startswith("***"), \
                    f"Creator ID should be anonymized: {creator_id}"
    
    def test_recent_activity_anonymizes_data(self, api_client, pro_token):
        """Recent activity endpoint should return anonymized data"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = api_client.get(f"{BASE_URL}/api/arris/recent-activity", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Activity items should have expected structure
        for activity in data.get("activity", []):
            expected_fields = ["id", "activity_type", "status", "created_at"]
            for field in expected_fields:
                assert field in activity, f"Activity should include {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
