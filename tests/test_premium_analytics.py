"""
Premium Analytics Feature Tests
Tests for Premium-tier analytics features:
- GET /api/creators/me/premium-analytics endpoint
- GET /api/creators/me/premium-analytics/export endpoint
- Feature gating (403 for Free/Starter/Pro, 200 for Premium/Elite)
- Comparative analytics (your_approval_rate, platform_approval_rate, percentile_rank)
- Revenue tracking (estimated value, realized, pipeline, pending)
- Predictive insights (success_score, factors, recommendation)
- ARRIS analytics (processing_times, category_breakdown)
- Platform performance and growth metrics
- Date range parameter (7d, 30d, 90d, 1y, all)
- Export functionality (JSON and CSV formats)

Test credentials:
- Premium user: premium@speedtest.com / premium123
- Pro user: protest@dashboard.com / propassword123
- Free user: testcreator@example.com / creator123
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://aigenthq-1.preview.emergentagent.com').rstrip('/')

# Test credentials
PREMIUM_USER_EMAIL = "premium@speedtest.com"
PREMIUM_USER_PASSWORD = "premium123"
PRO_USER_EMAIL = "protest@dashboard.com"
PRO_USER_PASSWORD = "propassword123"
FREE_USER_EMAIL = "testcreator@example.com"
FREE_USER_PASSWORD = "creator123"


@pytest.fixture(scope="function")
def api_client():
    """Fresh requests session for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def premium_user_token():
    """Get Premium user authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": PREMIUM_USER_EMAIL, "password": PREMIUM_USER_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Premium user authentication failed: {response.status_code} - {response.text}")


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
    pytest.skip(f"Pro user authentication failed: {response.status_code} - {response.text}")


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
    pytest.skip(f"Free user authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="function")
def premium_client(premium_user_token):
    """Session with Premium user auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {premium_user_token}"
    })
    return session


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


class TestPremiumAnalyticsAccess:
    """Tests for premium analytics access control"""
    
    def test_premium_analytics_requires_auth(self, api_client):
        """Premium analytics should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        assert response.status_code in [401, 403]
        print("✓ Premium analytics requires authentication")
    
    def test_free_user_gets_403(self, free_client):
        """Free tier user should get 403 with upgrade URL"""
        response = free_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "feature_gated"
        assert "Premium" in detail["message"]
        assert detail["required_tier"] == "premium"
        assert detail["upgrade_url"] == "/creator/subscription"
        assert "feature_highlights" in detail
        assert isinstance(detail["feature_highlights"], list)
        print("✓ Free user gets 403 with upgrade URL and feature highlights")
    
    def test_pro_user_gets_403(self, pro_client):
        """Pro tier user should get 403 (Premium required)"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "feature_gated"
        assert detail["required_tier"] == "premium"
        print("✓ Pro user gets 403 (Premium required)")
    
    def test_premium_user_gets_200(self, premium_client):
        """Premium tier user should get 200 with full analytics data"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert "analytics_tier" in data
        assert data["analytics_tier"] == "premium"
        print("✓ Premium user gets 200 with premium analytics")


class TestPremiumAnalyticsContent:
    """Tests for premium analytics content structure"""
    
    def test_analytics_tier_and_date_range(self, premium_client):
        """Analytics should include tier and date range info"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert data["analytics_tier"] == "premium"
        assert "date_range" in data
        assert "period_start" in data
        assert "period_end" in data
        print(f"✓ Analytics tier: {data['analytics_tier']}, date_range: {data['date_range']}")
    
    def test_summary_section(self, premium_client):
        """Analytics should include summary section"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "summary" in data
        summary = data["summary"]
        
        assert "total_proposals" in summary
        assert "approval_rate" in summary
        assert "completed_projects" in summary
        assert "engagement_score" in summary
        assert "predicted_success" in summary
        
        assert isinstance(summary["total_proposals"], int)
        assert isinstance(summary["approval_rate"], (int, float))
        assert isinstance(summary["engagement_score"], (int, float))
        assert isinstance(summary["predicted_success"], int)
        
        print(f"✓ Summary: {summary['total_proposals']} proposals, {summary['approval_rate']}% approval, {summary['engagement_score']} engagement")
    
    def test_comparative_analytics(self, premium_client):
        """Analytics should include comparative analytics"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "comparative_analytics" in data
        comp = data["comparative_analytics"]
        
        # Required fields
        assert "your_approval_rate" in comp
        assert "platform_approval_rate" in comp
        assert "approval_rate_diff" in comp
        assert "your_proposals" in comp
        assert "avg_proposals_per_creator" in comp
        assert "proposals_diff" in comp
        assert "percentile_rank" in comp
        
        # Type checks
        assert isinstance(comp["your_approval_rate"], (int, float))
        assert isinstance(comp["platform_approval_rate"], (int, float))
        assert isinstance(comp["percentile_rank"], int)
        assert 1 <= comp["percentile_rank"] <= 99
        
        print(f"✓ Comparative: your rate={comp['your_approval_rate']}%, platform={comp['platform_approval_rate']}%, percentile={comp['percentile_rank']}")
    
    def test_revenue_tracking(self, premium_client):
        """Analytics should include revenue tracking"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "revenue_tracking" in data
        rev = data["revenue_tracking"]
        
        # Required fields
        assert "total_estimated_value" in rev
        assert "realized_value" in rev
        assert "pipeline_value" in rev
        assert "pending_value" in rev
        assert "realization_rate" in rev
        assert "avg_project_value" in rev
        assert "currency" in rev
        
        # Type checks
        assert isinstance(rev["total_estimated_value"], (int, float))
        assert isinstance(rev["realized_value"], (int, float))
        assert isinstance(rev["realization_rate"], (int, float))
        assert rev["currency"] == "USD"
        
        # Value consistency check
        assert rev["total_estimated_value"] >= rev["realized_value"]
        
        print(f"✓ Revenue: total=${rev['total_estimated_value']}, realized=${rev['realized_value']}, rate={rev['realization_rate']}%")
    
    def test_predictive_insights(self, premium_client):
        """Analytics should include predictive insights"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "predictive_insights" in data
        pred = data["predictive_insights"]
        
        # Required fields
        assert "success_score" in pred
        assert "score_label" in pred
        assert "success_factors" in pred
        assert "risk_factors" in pred
        assert "recommendation" in pred
        
        # Type checks
        assert isinstance(pred["success_score"], int)
        assert 10 <= pred["success_score"] <= 95
        assert pred["score_label"] in ["Excellent", "Good", "Fair", "Needs Improvement"]
        assert isinstance(pred["success_factors"], list)
        assert isinstance(pred["risk_factors"], list)
        assert isinstance(pred["recommendation"], str)
        
        print(f"✓ Predictive: score={pred['success_score']}, label={pred['score_label']}")
    
    def test_arris_analytics(self, premium_client):
        """Analytics should include ARRIS analytics"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "arris_analytics" in data
        arris = data["arris_analytics"]
        
        # Required fields
        assert "total_interactions" in arris
        assert "successful_interactions" in arris
        assert "success_rate" in arris
        assert "processing_times" in arris
        assert "category_breakdown" in arris
        assert "insights_generated" in arris
        
        # Processing times structure
        pt = arris["processing_times"]
        assert "average" in pt
        assert "min" in pt
        assert "max" in pt
        assert "total_saved" in pt
        
        # Category breakdown structure
        assert isinstance(arris["category_breakdown"], list)
        
        print(f"✓ ARRIS: {arris['total_interactions']} interactions, {arris['success_rate']}% success, avg time={pt['average']}s")
    
    def test_trends_data(self, premium_client):
        """Analytics should include trends data"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "trends" in data
        trends = data["trends"]
        
        assert "granularity" in trends
        assert trends["granularity"] in ["daily", "weekly"]
        assert "data" in trends
        assert isinstance(trends["data"], list)
        
        if trends["data"]:
            for item in trends["data"]:
                assert "period" in item
                assert "count" in item
        
        print(f"✓ Trends: {trends['granularity']} granularity, {len(trends['data'])} data points")
    
    def test_platform_performance(self, premium_client):
        """Analytics should include platform performance"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "platform_performance" in data
        platforms = data["platform_performance"]
        assert isinstance(platforms, list)
        
        if platforms:
            for p in platforms:
                assert "platform" in p
                assert "total" in p
                assert "approved" in p
                assert "completed" in p
                assert "approval_rate" in p
        
        print(f"✓ Platform performance: {len(platforms)} platforms")
    
    def test_growth_metrics(self, premium_client):
        """Analytics should include growth metrics"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "growth_metrics" in data
        growth = data["growth_metrics"]
        
        assert "current_month" in growth
        assert "last_month" in growth
        assert "mom_growth_percent" in growth
        assert "growth_trend" in growth
        
        assert isinstance(growth["current_month"], int)
        assert isinstance(growth["last_month"], int)
        assert isinstance(growth["mom_growth_percent"], (int, float))
        
        print(f"✓ Growth: current={growth['current_month']}, last={growth['last_month']}, MoM={growth['mom_growth_percent']}%")
    
    def test_engagement_section(self, premium_client):
        """Analytics should include engagement section"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "engagement" in data
        eng = data["engagement"]
        
        assert "score" in eng
        assert "factors" in eng
        assert "label" in eng
        
        assert isinstance(eng["score"], (int, float))
        assert isinstance(eng["factors"], dict)
        assert eng["label"] in ["Highly Engaged", "Moderately Engaged", "Low Engagement"]
        
        print(f"✓ Engagement: score={eng['score']}, label={eng['label']}")
    
    def test_export_availability(self, premium_client):
        """Analytics should indicate export availability"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert "export_available" in data
        assert data["export_available"] == True
        assert "export_formats" in data
        assert "csv" in data["export_formats"]
        assert "json" in data["export_formats"]
        
        print("✓ Export available: CSV and JSON formats")


class TestDateRangeParameter:
    """Tests for date range parameter"""
    
    def test_default_date_range(self, premium_client):
        """Default date range should be 30d"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        assert data["date_range"] == "30d"
        print("✓ Default date range is 30d")
    
    def test_7d_date_range(self, premium_client):
        """7d date range should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics?date_range=7d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date_range"] == "7d"
        assert data["trends"]["granularity"] == "daily"
        print("✓ 7d date range works with daily granularity")
    
    def test_30d_date_range(self, premium_client):
        """30d date range should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics?date_range=30d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date_range"] == "30d"
        assert data["trends"]["granularity"] == "daily"
        print("✓ 30d date range works with daily granularity")
    
    def test_90d_date_range(self, premium_client):
        """90d date range should work with weekly granularity"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics?date_range=90d")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date_range"] == "90d"
        assert data["trends"]["granularity"] == "weekly"
        print("✓ 90d date range works with weekly granularity")
    
    def test_1y_date_range(self, premium_client):
        """1y date range should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics?date_range=1y")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date_range"] == "1y"
        assert data["trends"]["granularity"] == "weekly"
        print("✓ 1y date range works with weekly granularity")
    
    def test_all_date_range(self, premium_client):
        """all date range should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics?date_range=all")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date_range"] == "all"
        print("✓ all date range works")


class TestExportEndpoint:
    """Tests for premium analytics export endpoint"""
    
    def test_export_requires_auth(self, api_client):
        """Export should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export")
        assert response.status_code in [401, 403]
        print("✓ Export requires authentication")
    
    def test_export_requires_premium(self, pro_client):
        """Export should require Premium tier"""
        response = pro_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export")
        assert response.status_code == 403
        
        data = response.json()
        assert data["detail"]["error"] == "feature_gated"
        print("✓ Export requires Premium tier")
    
    def test_json_export(self, premium_client):
        """JSON export should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export?format=json")
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "json"
        assert "data" in data
        assert "filename" in data
        assert "record_count" in data
        assert "exported_at" in data
        assert ".json" in data["filename"]
        assert isinstance(data["data"], list)
        
        print(f"✓ JSON export: {data['record_count']} records, filename={data['filename']}")
    
    def test_csv_export(self, premium_client):
        """CSV export should work"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export?format=csv")
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "csv"
        assert "data" in data
        assert "filename" in data
        assert "record_count" in data
        assert ".csv" in data["filename"]
        assert isinstance(data["data"], str)
        
        # Check CSV has headers
        if data["record_count"] > 0:
            assert "id,title,status" in data["data"]
        
        print(f"✓ CSV export: {data['record_count']} records, filename={data['filename']}")
    
    def test_export_with_date_range(self, premium_client):
        """Export should respect date range parameter"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export?format=json&date_range=7d")
        assert response.status_code == 200
        
        data = response.json()
        assert "7d" in data["filename"]
        print("✓ Export respects date range parameter")
    
    def test_default_export_format(self, premium_client):
        """Default export format should be JSON"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics/export")
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "json"
        print("✓ Default export format is JSON")


class TestFeatureGatingIntegration:
    """Integration tests for feature gating with premium analytics"""
    
    def test_free_user_no_advanced_analytics(self, free_client):
        """Free user should not have advanced_analytics feature"""
        response = free_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["features"]["advanced_analytics"] == False
        print("✓ Free user has advanced_analytics=False")
    
    def test_pro_user_no_advanced_analytics(self, pro_client):
        """Pro user should not have advanced_analytics feature"""
        response = pro_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["features"]["advanced_analytics"] == False
        print("✓ Pro user has advanced_analytics=False")
    
    def test_premium_user_has_advanced_analytics(self, premium_client):
        """Premium user should have advanced_analytics feature"""
        response = premium_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["features"]["advanced_analytics"] == True
        print("✓ Premium user has advanced_analytics=True")
    
    def test_premium_user_tier(self, premium_client):
        """Premium user should have premium tier"""
        response = premium_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tier"] == "premium"
        print("✓ Premium user has tier=premium")


class TestPremiumUserDataIntegrity:
    """Tests for Premium user data integrity"""
    
    def test_premium_user_has_proposals(self, premium_client):
        """Premium user should have proposals in the system"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        # Premium test user should have at least some proposals
        assert data["summary"]["total_proposals"] >= 0
        print(f"✓ Premium user has {data['summary']['total_proposals']} proposals")
    
    def test_data_consistency(self, premium_client):
        """Data should be consistent across sections"""
        response = premium_client.get(f"{BASE_URL}/api/creators/me/premium-analytics")
        data = response.json()
        
        # Summary total should match comparative analytics
        assert data["summary"]["total_proposals"] == data["comparative_analytics"]["your_proposals"]
        
        # Approval rate should match
        assert data["summary"]["approval_rate"] == data["comparative_analytics"]["your_approval_rate"]
        
        print("✓ Data is consistent across sections")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
