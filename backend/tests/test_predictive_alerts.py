"""
Test Module A4: Predictive Alerts
=================================
Tests for WebSocket notifications and predictive alerts for Pro+ creators.
Feature-gated: Pro, Premium, Elite have access; Free and Starter see upgrade prompt.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USERS = {
    "free": {"email": "freetest@hivehq.com", "password": "testpassword"},
    "starter": {"email": "startertest@hivehq.com", "password": "testpassword"},
    "pro": {"email": "protest@hivehq.com", "password": "testpassword"},
    "premium": {"email": "premiumtest@hivehq.com", "password": "testpassword"},
    "elite": {"email": "elitetest@hivehq.com", "password": "testpassword123"},
}


class TestPredictiveAlertsAuth:
    """Test authentication requirements for predictive alerts endpoints"""
    
    def test_predictive_alerts_requires_auth(self):
        """GET /api/creators/me/predictive-alerts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/creators/me/predictive-alerts requires authentication")
    
    def test_trigger_alerts_requires_auth(self):
        """POST /api/creators/me/trigger-alerts requires authentication"""
        response = requests.post(f"{BASE_URL}/api/creators/me/trigger-alerts")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/creators/me/trigger-alerts requires authentication")
    
    def test_alert_preferences_requires_auth(self):
        """GET /api/creators/me/alert-preferences requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/alert-preferences")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/creators/me/alert-preferences requires authentication")
    
    def test_mark_alert_read_requires_auth(self):
        """POST /api/creators/me/alerts/{alert_id}/read requires authentication"""
        response = requests.post(f"{BASE_URL}/api/creators/me/alerts/TEST-ALERT-123/read")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/creators/me/alerts/{alert_id}/read requires authentication")
    
    def test_dismiss_alert_requires_auth(self):
        """POST /api/creators/me/alerts/{alert_id}/dismiss requires authentication"""
        response = requests.post(f"{BASE_URL}/api/creators/me/alerts/TEST-ALERT-123/dismiss")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/creators/me/alerts/{alert_id}/dismiss requires authentication")


class TestPredictiveAlertsFeatureGating:
    """Test feature gating - Pro+ have access, Free/Starter see access_denied"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login all test users and store tokens"""
        self.tokens = {}
        for tier, creds in TEST_USERS.items():
            response = requests.post(f"{BASE_URL}/api/creators/login", json=creds)
            if response.status_code == 200:
                self.tokens[tier] = response.json().get("access_token")
            else:
                print(f"Warning: Could not login {tier} user: {response.status_code}")
    
    def test_free_user_access_denied(self):
        """Free user should see access_denied=true"""
        if "free" not in self.tokens:
            pytest.skip("Free user token not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['free']}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("access_denied") == True, f"Expected access_denied=true, got {data}"
        assert data.get("tier") == "free", f"Expected tier=free, got {data.get('tier')}"
        assert "upgrade_message" in data, "Expected upgrade_message in response"
        print(f"✓ Free user sees access_denied=true, tier=free")
    
    def test_starter_user_access_denied(self):
        """Starter user should see access_denied=true"""
        if "starter" not in self.tokens:
            pytest.skip("Starter user token not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['starter']}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("access_denied") == True, f"Expected access_denied=true, got {data}"
        assert data.get("tier") == "starter", f"Expected tier=starter, got {data.get('tier')}"
        print(f"✓ Starter user sees access_denied=true, tier=starter")
    
    def test_pro_user_has_access(self):
        """Pro user should have access (access_denied=false)"""
        if "pro" not in self.tokens:
            pytest.skip("Pro user token not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['pro']}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("access_denied") == False, f"Expected access_denied=false, got {data}"
        assert data.get("tier") == "pro", f"Expected tier=pro, got {data.get('tier')}"
        assert "alerts" in data, "Expected alerts array in response"
        assert "priority_counts" in data, "Expected priority_counts in response"
        print(f"✓ Pro user has access (access_denied=false), tier=pro")
    
    def test_premium_user_has_access(self):
        """Premium user should have access"""
        if "premium" not in self.tokens:
            pytest.skip("Premium user token not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['premium']}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("access_denied") == False, f"Expected access_denied=false, got {data}"
        assert data.get("tier") == "premium", f"Expected tier=premium, got {data.get('tier')}"
        print(f"✓ Premium user has access, tier=premium")
    
    def test_elite_user_has_access(self):
        """Elite user should have access"""
        if "elite" not in self.tokens:
            pytest.skip("Elite user token not available")
        
        headers = {"Authorization": f"Bearer {self.tokens['elite']}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("access_denied") == False, f"Expected access_denied=false, got {data}"
        assert data.get("tier") == "elite", f"Expected tier=elite, got {data.get('tier')}"
        print(f"✓ Elite user has access, tier=elite")


class TestPredictiveAlertsEndpoints:
    """Test predictive alerts endpoints functionality for Pro+ users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login Pro user for testing"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=TEST_USERS["pro"])
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not login Pro user")
    
    def test_get_predictive_alerts_structure(self):
        """GET /api/creators/me/predictive-alerts returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "alerts" in data, "Missing 'alerts' field"
        assert "access_denied" in data, "Missing 'access_denied' field"
        assert "tier" in data, "Missing 'tier' field"
        assert "priority_counts" in data, "Missing 'priority_counts' field"
        assert "total" in data, "Missing 'total' field"
        assert "unread" in data, "Missing 'unread' field"
        
        # Check priority_counts structure
        priority_counts = data.get("priority_counts", {})
        assert "urgent" in priority_counts, "Missing 'urgent' in priority_counts"
        assert "high" in priority_counts, "Missing 'high' in priority_counts"
        assert "medium" in priority_counts, "Missing 'medium' in priority_counts"
        assert "low" in priority_counts, "Missing 'low' in priority_counts"
        
        print(f"✓ GET /api/creators/me/predictive-alerts returns correct structure")
        print(f"  - alerts: {len(data['alerts'])} items")
        print(f"  - priority_counts: {priority_counts}")
    
    def test_get_predictive_alerts_limit_param(self):
        """GET /api/creators/me/predictive-alerts respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/predictive-alerts?limit=5", 
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("alerts", [])) <= 5, "Limit parameter not respected"
        print(f"✓ Limit parameter works correctly")
    
    def test_trigger_alerts_for_pro_user(self):
        """POST /api/creators/me/trigger-alerts works for Pro user"""
        response = requests.post(f"{BASE_URL}/api/creators/me/trigger-alerts", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check response structure
        assert "success" in data, "Missing 'success' field"
        assert "alerts_generated" in data, "Missing 'alerts_generated' field"
        assert "notifications_sent" in data, "Missing 'notifications_sent' field"
        
        print(f"✓ POST /api/creators/me/trigger-alerts works for Pro user")
        print(f"  - success: {data.get('success')}")
        print(f"  - alerts_generated: {data.get('alerts_generated')}")
    
    def test_trigger_alerts_access_denied_for_free(self):
        """POST /api/creators/me/trigger-alerts returns access_denied for Free user"""
        # Login as free user
        response = requests.post(f"{BASE_URL}/api/creators/login", json=TEST_USERS["free"])
        if response.status_code != 200:
            pytest.skip("Could not login Free user")
        
        free_token = response.json().get("access_token")
        free_headers = {"Authorization": f"Bearer {free_token}"}
        
        response = requests.post(f"{BASE_URL}/api/creators/me/trigger-alerts", headers=free_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == False, f"Expected success=false for Free user"
        assert data.get("reason") == "access_denied", f"Expected reason=access_denied"
        print(f"✓ POST /api/creators/me/trigger-alerts returns access_denied for Free user")
    
    def test_get_alert_preferences(self):
        """GET /api/creators/me/alert-preferences returns preferences"""
        response = requests.get(f"{BASE_URL}/api/creators/me/alert-preferences", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check default preferences structure
        assert "enabled" in data, "Missing 'enabled' field"
        assert "categories" in data, "Missing 'categories' field"
        assert "priorities" in data, "Missing 'priorities' field"
        assert "quiet_hours" in data, "Missing 'quiet_hours' field"
        assert "channels" in data, "Missing 'channels' field"
        
        # Check categories
        categories = data.get("categories", {})
        expected_categories = ["timing", "performance", "risk", "platform", "arris"]
        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"
        
        # Check priorities
        priorities = data.get("priorities", {})
        expected_priorities = ["urgent", "high", "medium", "low"]
        for pri in expected_priorities:
            assert pri in priorities, f"Missing priority: {pri}"
        
        print(f"✓ GET /api/creators/me/alert-preferences returns correct structure")
        print(f"  - enabled: {data.get('enabled')}")
        print(f"  - categories: {list(categories.keys())}")
    
    def test_update_alert_preferences(self):
        """PUT /api/creators/me/alert-preferences updates preferences"""
        new_prefs = {
            "enabled": True,
            "categories": {
                "timing": True,
                "performance": True,
                "risk": True,
                "platform": False,  # Disable platform alerts
                "arris": True
            },
            "priorities": {
                "urgent": True,
                "high": True,
                "medium": True,
                "low": False  # Disable low priority
            },
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00"
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/creators/me/alert-preferences",
            headers=self.headers,
            json=new_prefs
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=true"
        assert "preferences" in data, "Missing 'preferences' in response"
        
        # Verify preferences were saved
        saved_prefs = data.get("preferences", {})
        assert saved_prefs.get("categories", {}).get("platform") == False, "Platform category not updated"
        assert saved_prefs.get("priorities", {}).get("low") == False, "Low priority not updated"
        assert saved_prefs.get("quiet_hours", {}).get("enabled") == True, "Quiet hours not updated"
        
        print(f"✓ PUT /api/creators/me/alert-preferences updates preferences successfully")
    
    def test_mark_alert_read(self):
        """POST /api/creators/me/alerts/{alert_id}/read marks alert as read"""
        # First, get alerts to find an alert_id
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=self.headers)
        data = response.json()
        alerts = data.get("alerts", [])
        
        if not alerts:
            # Trigger alerts first
            requests.post(f"{BASE_URL}/api/creators/me/trigger-alerts", headers=self.headers)
            response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=self.headers)
            data = response.json()
            alerts = data.get("alerts", [])
        
        if not alerts:
            # Test with a fake alert_id - should return success=false
            response = requests.post(
                f"{BASE_URL}/api/creators/me/alerts/FAKE-ALERT-123/read",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") == False, "Expected success=false for non-existent alert"
            print(f"✓ POST /api/creators/me/alerts/{{alert_id}}/read returns success=false for non-existent alert")
            return
        
        # Mark first alert as read
        alert_id = alerts[0].get("alert_id")
        response = requests.post(
            f"{BASE_URL}/api/creators/me/alerts/{alert_id}/read",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "success" in data, "Missing 'success' field"
        print(f"✓ POST /api/creators/me/alerts/{{alert_id}}/read works correctly")
    
    def test_dismiss_alert(self):
        """POST /api/creators/me/alerts/{alert_id}/dismiss dismisses alert"""
        # First, get alerts to find an alert_id
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=self.headers)
        data = response.json()
        alerts = data.get("alerts", [])
        
        if not alerts:
            # Test with a fake alert_id - should return success=false
            response = requests.post(
                f"{BASE_URL}/api/creators/me/alerts/FAKE-ALERT-456/dismiss",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") == False, "Expected success=false for non-existent alert"
            print(f"✓ POST /api/creators/me/alerts/{{alert_id}}/dismiss returns success=false for non-existent alert")
            return
        
        # Dismiss last alert (to not interfere with read test)
        alert_id = alerts[-1].get("alert_id")
        response = requests.post(
            f"{BASE_URL}/api/creators/me/alerts/{alert_id}/dismiss",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "success" in data, "Missing 'success' field"
        print(f"✓ POST /api/creators/me/alerts/{{alert_id}}/dismiss works correctly")


class TestAlertStructure:
    """Test alert object structure when alerts exist"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login Pro user for testing"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=TEST_USERS["pro"])
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not login Pro user")
    
    def test_alert_object_structure(self):
        """Verify alert object has all required fields"""
        # Trigger alerts first
        requests.post(f"{BASE_URL}/api/creators/me/trigger-alerts", headers=self.headers)
        
        response = requests.get(f"{BASE_URL}/api/creators/me/predictive-alerts", headers=self.headers)
        data = response.json()
        alerts = data.get("alerts", [])
        
        if not alerts:
            print("⚠ No alerts generated (test user has no proposals) - skipping structure check")
            pytest.skip("No alerts to verify structure")
        
        alert = alerts[0]
        
        # Check required fields
        required_fields = [
            "alert_id", "alert_type", "title", "message", "icon",
            "priority", "category", "actionable", "created_at"
        ]
        
        for field in required_fields:
            assert field in alert, f"Missing required field: {field}"
        
        # Check priority is valid
        valid_priorities = ["urgent", "high", "medium", "low"]
        assert alert.get("priority") in valid_priorities, f"Invalid priority: {alert.get('priority')}"
        
        # Check category is valid
        valid_categories = ["timing", "performance", "risk", "platform", "arris", "general"]
        assert alert.get("category") in valid_categories, f"Invalid category: {alert.get('category')}"
        
        print(f"✓ Alert object has correct structure")
        print(f"  - alert_type: {alert.get('alert_type')}")
        print(f"  - priority: {alert.get('priority')}")
        print(f"  - category: {alert.get('category')}")


class TestAllUsersCanLogin:
    """Verify all test users can login successfully"""
    
    def test_all_users_login(self):
        """All tier users can login successfully"""
        for tier, creds in TEST_USERS.items():
            response = requests.post(f"{BASE_URL}/api/creators/login", json=creds)
            assert response.status_code == 200, f"{tier} user login failed: {response.status_code} - {response.text}"
            data = response.json()
            assert "access_token" in data, f"{tier} user missing access_token"
            print(f"✓ {tier.capitalize()} user login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
