"""
Advanced Dashboard Feature Tests
Tests for Pro+ tier advanced dashboard features:
- GET /api/creators/me/advanced-dashboard endpoint
- Feature gating (403 for Free/Starter, 200 for Pro+)
- Performance metrics (approval_rate, avg_review_time)
- Trends (monthly_submissions)
- Status breakdown, complexity distribution, ARRIS activity
- Priority review status

Test credentials:
- Pro user: protest@dashboard.com / propassword123
- Free user: testcreator@example.com / creator123
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://creator-hive-3.preview.emergentagent.com').rstrip('/')

# Test credentials
PRO_USER_EMAIL = "protest@dashboard.com"
PRO_USER_PASSWORD = "propassword123"
FREE_USER_EMAIL = "testcreator@example.com"
FREE_USER_PASSWORD = "creator123"
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "adminpassword"


@pytest.fixture(scope="function")
def api_client():
    """Fresh requests session for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def pro_user_token():
    """Get Pro user authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": PRO_USER_EMAIL, "password": PRO_USER_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Pro user authentication failed")


@pytest.fixture(scope="module")
def free_user_token():
    """Get Free user authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": FREE_USER_EMAIL, "password": FREE_USER_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Free user authentication failed")


@pytest.fixture(scope="function")
def pro_client(pro_user_token):
    """Session with Pro user auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pro_user_token}"
    })
    return session


@pytest.fixture(scope="function")
def free_client(free_user_token):
    """Session with Free user auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {free_user_token}"
    })
    return session


class TestAdvancedDashboardAccess:
    """Tests for advanced dashboard access control"""
    
    def test_advanced_dashboard_requires_auth(self, api_client):
        """Advanced dashboard should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        assert response.status_code in [401, 403]
        print("✓ Advanced dashboard requires authentication")
    
    def test_free_user_gets_403(self, free_client):
        """Free tier user should get 403 with upgrade URL"""
        response = free_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "feature_gated"
        assert detail["message"] == "Advanced dashboard requires Pro plan or higher"
        assert detail["required_tier"] == "pro"
        assert detail["upgrade_url"] == "/creator/subscription"
        print("✓ Free user gets 403 with upgrade URL")
    
    def test_pro_user_gets_200(self, pro_client):
        """Pro tier user should get 200 with full dashboard data"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "dashboard_level" in data
        assert data["dashboard_level"] == "advanced"
        print("✓ Pro user gets 200 with advanced dashboard")


class TestAdvancedDashboardContent:
    """Tests for advanced dashboard content structure"""
    
    def test_dashboard_level_and_flags(self, pro_client):
        """Dashboard should include level and feature flags"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert data["dashboard_level"] in ["advanced", "custom"]
        assert "has_priority_review" in data
        assert "has_advanced_analytics" in data
        assert isinstance(data["has_priority_review"], bool)
        assert isinstance(data["has_advanced_analytics"], bool)
        print(f"✓ Dashboard level: {data['dashboard_level']}, priority_review: {data['has_priority_review']}")
    
    def test_performance_metrics(self, pro_client):
        """Dashboard should include performance metrics"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "performance" in data
        perf = data["performance"]
        
        # Required fields
        assert "total_proposals" in perf
        assert "approval_rate" in perf
        assert "avg_review_time_hours" in perf
        assert "completed" in perf
        assert "in_progress" in perf
        
        # Type checks
        assert isinstance(perf["total_proposals"], int)
        assert isinstance(perf["approval_rate"], (int, float))
        assert perf["approval_rate"] >= 0 and perf["approval_rate"] <= 100
        
        print(f"✓ Performance: {perf['total_proposals']} proposals, {perf['approval_rate']}% approval rate")
    
    def test_priority_queue_position(self, pro_client):
        """Pro users with priority review should have queue position"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        if data["has_priority_review"]:
            assert "priority_queue_position" in data["performance"]
            # Queue position can be None or an integer
            pos = data["performance"]["priority_queue_position"]
            assert pos is None or isinstance(pos, int)
            print(f"✓ Priority queue position: {pos}")
        else:
            print("Note: User doesn't have priority review")
    
    def test_monthly_trends(self, pro_client):
        """Dashboard should include monthly submission trends"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "trends" in data
        assert "monthly_submissions" in data["trends"]
        
        trends = data["trends"]["monthly_submissions"]
        assert isinstance(trends, list)
        
        if trends:
            # Check structure of trend items
            for trend in trends:
                assert "month" in trend
                assert "count" in trend
                assert isinstance(trend["count"], int)
            print(f"✓ Monthly trends: {len(trends)} months of data")
        else:
            print("Note: No monthly trend data yet")
    
    def test_status_breakdown(self, pro_client):
        """Dashboard should include status breakdown"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "status_breakdown" in data
        breakdown = data["status_breakdown"]
        assert isinstance(breakdown, list)
        
        if breakdown:
            for status in breakdown:
                assert "status" in status
                assert "count" in status
                assert "latest" in status
                assert isinstance(status["count"], int)
            print(f"✓ Status breakdown: {len(breakdown)} statuses")
        else:
            print("Note: No status breakdown data yet")
    
    def test_complexity_distribution(self, pro_client):
        """Dashboard should include complexity distribution"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "complexity_distribution" in data
        dist = data["complexity_distribution"]
        assert isinstance(dist, list)
        
        if dist:
            for item in dist:
                assert "complexity" in item
                assert "count" in item
                assert isinstance(item["count"], int)
            print(f"✓ Complexity distribution: {len(dist)} levels")
        else:
            print("Note: No complexity distribution data yet")
    
    def test_arris_activity(self, pro_client):
        """Dashboard should include ARRIS activity stats"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "arris" in data
        arris = data["arris"]
        
        assert "total_interactions" in arris
        assert "successful" in arris
        assert "recent_activity" in arris
        
        assert isinstance(arris["total_interactions"], int)
        assert isinstance(arris["successful"], int)
        assert isinstance(arris["recent_activity"], list)
        
        if arris["recent_activity"]:
            activity = arris["recent_activity"][0]
            assert "timestamp" in activity
            assert "query_category" in activity
            assert "success" in activity
        
        print(f"✓ ARRIS activity: {arris['total_interactions']} interactions, {arris['successful']} successful")
    
    def test_insights_summary(self, pro_client):
        """Dashboard should include insights summary"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert "insights" in data
        insights = data["insights"]
        
        assert "top_performing_month" in insights
        assert "most_common_complexity" in insights
        
        print(f"✓ Insights: top month={insights['top_performing_month']}, common complexity={insights['most_common_complexity']}")


class TestFeatureGatingIntegration:
    """Integration tests for feature gating with dashboard"""
    
    def test_free_user_has_basic_dashboard_level(self, free_client):
        """Free user should have basic dashboard level in feature access"""
        response = free_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["features"]["dashboard_level"] == "basic"
        assert data["features"]["priority_review"] == False
        print("✓ Free user has basic dashboard level")
    
    def test_pro_user_has_advanced_dashboard_level(self, pro_client):
        """Pro user should have advanced dashboard level in feature access"""
        response = pro_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["features"]["dashboard_level"] == "advanced"
        assert data["features"]["priority_review"] == True
        print("✓ Pro user has advanced dashboard level with priority review")
    
    def test_dashboard_level_matches_feature_access(self, pro_client):
        """Dashboard level in advanced-dashboard should match feature-access"""
        # Get feature access
        feature_response = pro_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        feature_data = feature_response.json()
        
        # Get advanced dashboard
        dashboard_response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        dashboard_data = dashboard_response.json()
        
        # Compare
        assert feature_data["features"]["dashboard_level"] == dashboard_data["dashboard_level"]
        assert feature_data["features"]["priority_review"] == dashboard_data["has_priority_review"]
        print("✓ Dashboard level matches feature access")


class TestProUserDataIntegrity:
    """Tests for Pro user data integrity in advanced dashboard"""
    
    def test_pro_user_has_proposals(self, pro_client):
        """Pro user should have proposals in the system"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert data["performance"]["total_proposals"] > 0
        print(f"✓ Pro user has {data['performance']['total_proposals']} proposals")
    
    def test_pro_user_has_arris_logs(self, pro_client):
        """Pro user should have ARRIS usage logs"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        assert data["arris"]["total_interactions"] > 0
        print(f"✓ Pro user has {data['arris']['total_interactions']} ARRIS interactions")
    
    def test_approval_rate_calculation(self, pro_client):
        """Approval rate should be calculated correctly"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/advanced-dashboard")
        data = response.json()
        
        perf = data["performance"]
        total = perf["total_proposals"]
        
        # Approval rate should be between 0 and 100
        assert 0 <= perf["approval_rate"] <= 100
        
        # If there are completed/in_progress proposals, approval rate should be > 0
        if perf["completed"] > 0 or perf["in_progress"] > 0:
            assert perf["approval_rate"] > 0
        
        print(f"✓ Approval rate: {perf['approval_rate']}% (total: {total})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
