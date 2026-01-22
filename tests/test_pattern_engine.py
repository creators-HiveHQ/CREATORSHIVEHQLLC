"""
Test Suite for ARRIS Pattern Engine Dashboard - Phase 4 Module A
Tests platform-wide pattern detection and admin analytics endpoints

Endpoints tested:
- GET /api/admin/patterns/overview - Platform overview with health indicators
- GET /api/admin/patterns/detect - Comprehensive pattern detection
- GET /api/admin/patterns/cohorts - Cohort analysis by tier, month, engagement
- GET /api/admin/patterns/rankings - Creator rankings with filters
- GET /api/admin/patterns/revenue - Revenue analysis with MRR/ARR
- GET /api/admin/patterns/insights - Actionable insights
- GET /api/admin/patterns/churn-risk - At-risk creators
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


class TestPatternEngineAuth:
    """Test authentication requirements for Pattern Engine endpoints"""
    
    def test_overview_requires_auth(self):
        """GET /api/admin/patterns/overview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/overview")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Overview endpoint requires authentication")
    
    def test_detect_requires_auth(self):
        """GET /api/admin/patterns/detect requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/detect")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Detect endpoint requires authentication")
    
    def test_cohorts_requires_auth(self):
        """GET /api/admin/patterns/cohorts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/cohorts")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Cohorts endpoint requires authentication")
    
    def test_rankings_requires_auth(self):
        """GET /api/admin/patterns/rankings requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Rankings endpoint requires authentication")
    
    def test_revenue_requires_auth(self):
        """GET /api/admin/patterns/revenue requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/revenue")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Revenue endpoint requires authentication")
    
    def test_insights_requires_auth(self):
        """GET /api/admin/patterns/insights requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/insights")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Insights endpoint requires authentication")
    
    def test_churn_risk_requires_auth(self):
        """GET /api/admin/patterns/churn-risk requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/patterns/churn-risk")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Churn-risk endpoint requires authentication")


@pytest.fixture(scope="class")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✓ Admin login successful")
        return token
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


class TestPatternEngineOverview:
    """Test GET /api/admin/patterns/overview endpoint"""
    
    def test_overview_returns_200(self, admin_token):
        """Overview endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/overview", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Overview returns 200")
    
    def test_overview_has_snapshot(self, admin_token):
        """Overview contains snapshot with total_creators, total_proposals, active_subscriptions"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/overview", headers=headers)
        data = response.json()
        
        assert "snapshot" in data, "Missing 'snapshot' in response"
        snapshot = data["snapshot"]
        assert "total_creators" in snapshot, "Missing 'total_creators' in snapshot"
        assert "total_proposals" in snapshot, "Missing 'total_proposals' in snapshot"
        assert "active_subscriptions" in snapshot, "Missing 'active_subscriptions' in snapshot"
        assert "timestamp" in snapshot, "Missing 'timestamp' in snapshot"
        print(f"✓ Snapshot: {snapshot['total_creators']} creators, {snapshot['total_proposals']} proposals, {snapshot['active_subscriptions']} subscriptions")
    
    def test_overview_has_activity_30d(self, admin_token):
        """Overview contains 30-day activity metrics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/overview", headers=headers)
        data = response.json()
        
        assert "activity_30d" in data, "Missing 'activity_30d' in response"
        activity = data["activity_30d"]
        assert "new_proposals" in activity, "Missing 'new_proposals'"
        assert "new_registrations" in activity, "Missing 'new_registrations'"
        assert "proposal_growth_pct" in activity, "Missing 'proposal_growth_pct'"
        assert "registration_growth_pct" in activity, "Missing 'registration_growth_pct'"
        print(f"✓ 30-day activity: {activity['new_proposals']} new proposals, {activity['new_registrations']} new registrations")
    
    def test_overview_has_health_indicators(self, admin_token):
        """Overview contains health indicators with overall, engagement, success, revenue scores"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/overview", headers=headers)
        data = response.json()
        
        assert "health_indicators" in data, "Missing 'health_indicators' in response"
        health = data["health_indicators"]
        assert "overall" in health, "Missing 'overall' score"
        assert "engagement" in health, "Missing 'engagement' score"
        assert "success" in health, "Missing 'success' score"
        assert "revenue" in health, "Missing 'revenue' score"
        assert "status" in health, "Missing 'status'"
        assert health["status"] in ["excellent", "good", "fair", "needs_attention"], f"Invalid status: {health['status']}"
        print(f"✓ Health indicators: overall={health['overall']}, status={health['status']}")


class TestPatternEngineDetect:
    """Test GET /api/admin/patterns/detect endpoint"""
    
    def test_detect_returns_200(self, admin_token):
        """Detect endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/detect", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Detect returns 200")
    
    def test_detect_has_pattern_categories(self, admin_token):
        """Detect returns all pattern categories"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/detect", headers=headers)
        data = response.json()
        
        expected_categories = ["success_patterns", "risk_patterns", "churn_patterns", 
                              "revenue_patterns", "engagement_patterns"]
        for category in expected_categories:
            assert category in data, f"Missing '{category}' in response"
            assert isinstance(data[category], list), f"'{category}' should be a list"
        
        assert "detected_at" in data, "Missing 'detected_at' timestamp"
        assert "total_patterns" in data, "Missing 'total_patterns' count"
        print(f"✓ Pattern detection: {data['total_patterns']} total patterns detected")
    
    def test_detect_pattern_structure(self, admin_token):
        """Patterns have proper structure with title, description, confidence"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/detect", headers=headers)
        data = response.json()
        
        # Check structure of any non-empty pattern list
        for category in ["success_patterns", "risk_patterns", "revenue_patterns"]:
            if data.get(category):
                pattern = data[category][0]
                assert "title" in pattern, f"Pattern missing 'title'"
                assert "description" in pattern, f"Pattern missing 'description'"
                assert "confidence" in pattern, f"Pattern missing 'confidence'"
                assert 0 <= pattern["confidence"] <= 1, f"Confidence should be 0-1"
                print(f"✓ Pattern structure valid: {pattern['title'][:50]}...")
                break


class TestPatternEngineCohorts:
    """Test GET /api/admin/patterns/cohorts endpoint"""
    
    def test_cohorts_returns_200(self, admin_token):
        """Cohorts endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/cohorts", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Cohorts returns 200")
    
    def test_cohorts_has_tier_analysis(self, admin_token):
        """Cohorts contains tier-based analysis"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/cohorts", headers=headers)
        data = response.json()
        
        assert "by_tier" in data, "Missing 'by_tier' in response"
        by_tier = data["by_tier"]
        
        # Check tier data structure
        for tier, tier_data in by_tier.items():
            assert "count" in tier_data, f"Tier '{tier}' missing 'count'"
            assert "total_proposals" in tier_data, f"Tier '{tier}' missing 'total_proposals'"
            assert "avg_proposals_per_creator" in tier_data, f"Tier '{tier}' missing 'avg_proposals_per_creator'"
        
        print(f"✓ Tier cohorts: {len(by_tier)} tiers analyzed")
    
    def test_cohorts_has_engagement_levels(self, admin_token):
        """Cohorts contains engagement level analysis"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/cohorts", headers=headers)
        data = response.json()
        
        assert "by_engagement" in data, "Missing 'by_engagement' in response"
        engagement = data["by_engagement"]
        
        expected_levels = ["highly_engaged", "moderately_engaged", "low_engaged", "inactive"]
        for level in expected_levels:
            assert level in engagement, f"Missing engagement level '{level}'"
            assert "count" in engagement[level], f"Level '{level}' missing 'count'"
            assert "criteria" in engagement[level], f"Level '{level}' missing 'criteria'"
        
        print(f"✓ Engagement cohorts: {sum(e['count'] for e in engagement.values())} total creators")
    
    def test_cohorts_has_monthly_retention(self, admin_token):
        """Cohorts contains monthly registration cohort retention"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/cohorts", headers=headers)
        data = response.json()
        
        assert "by_registration_month" in data, "Missing 'by_registration_month' in response"
        monthly = data["by_registration_month"]
        assert isinstance(monthly, list), "'by_registration_month' should be a list"
        
        if monthly:
            month_data = monthly[0]
            assert "month" in month_data, "Monthly data missing 'month'"
            assert "count" in month_data, "Monthly data missing 'count'"
            assert "retained" in month_data, "Monthly data missing 'retained'"
            assert "retention_rate" in month_data, "Monthly data missing 'retention_rate'"
        
        print(f"✓ Monthly cohorts: {len(monthly)} months analyzed")


class TestPatternEngineRankings:
    """Test GET /api/admin/patterns/rankings endpoint"""
    
    def test_rankings_returns_200(self, admin_token):
        """Rankings endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Rankings returns 200")
    
    def test_rankings_returns_list(self, admin_token):
        """Rankings returns a list of creators"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings", headers=headers)
        data = response.json()
        
        assert isinstance(data, list), "Rankings should return a list"
        print(f"✓ Rankings: {len(data)} creators returned")
    
    def test_rankings_creator_structure(self, admin_token):
        """Rankings contain proper creator data structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings", headers=headers)
        data = response.json()
        
        if data:
            creator = data[0]
            required_fields = ["creator_id", "name", "email", "tier", 
                             "total_proposals", "approved_proposals", "approval_rate"]
            for field in required_fields:
                assert field in creator, f"Creator missing '{field}'"
            
            assert isinstance(creator["approval_rate"], (int, float)), "approval_rate should be numeric"
            print(f"✓ Top creator: {creator['name']} with {creator['approval_rate']}% approval rate")
    
    def test_rankings_sort_by_approval_rate(self, admin_token):
        """Rankings can be sorted by approval_rate"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings?sort_by=approval_rate", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        if len(data) >= 2:
            # First should have higher or equal approval rate
            assert data[0]["approval_rate"] >= data[1]["approval_rate"], "Not sorted by approval_rate"
        print("✓ Rankings sorted by approval_rate")
    
    def test_rankings_sort_by_total_proposals(self, admin_token):
        """Rankings can be sorted by total_proposals"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings?sort_by=total_proposals", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        if len(data) >= 2:
            assert data[0]["total_proposals"] >= data[1]["total_proposals"], "Not sorted by total_proposals"
        print("✓ Rankings sorted by total_proposals")
    
    def test_rankings_tier_filter(self, admin_token):
        """Rankings can be filtered by tier"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings?tier=Pro", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        # All returned creators should be Pro tier (if any)
        for creator in data:
            assert creator["tier"].lower() == "pro", f"Expected Pro tier, got {creator['tier']}"
        print(f"✓ Rankings filtered by tier: {len(data)} Pro creators")
    
    def test_rankings_limit(self, admin_token):
        """Rankings respects limit parameter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/rankings?limit=5", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert len(data) <= 5, f"Expected max 5 results, got {len(data)}"
        print(f"✓ Rankings limit: {len(data)} results (max 5)")


class TestPatternEngineRevenue:
    """Test GET /api/admin/patterns/revenue endpoint"""
    
    def test_revenue_returns_200(self, admin_token):
        """Revenue endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/revenue", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Revenue returns 200")
    
    def test_revenue_has_summary(self, admin_token):
        """Revenue contains summary with MRR, ARR, profit metrics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/revenue", headers=headers)
        data = response.json()
        
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        
        required_fields = ["total_revenue", "total_expenses", "net_profit", 
                          "profit_margin", "mrr", "arr", "active_subscriptions"]
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}'"
        
        print(f"✓ Revenue summary: MRR=${summary['mrr']}, ARR=${summary['arr']}")
    
    def test_revenue_has_monthly_trend(self, admin_token):
        """Revenue contains monthly trend data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/revenue", headers=headers)
        data = response.json()
        
        assert "monthly_trend" in data, "Missing 'monthly_trend' in response"
        monthly = data["monthly_trend"]
        assert isinstance(monthly, list), "'monthly_trend' should be a list"
        
        if monthly:
            month_data = monthly[0]
            assert "month" in month_data, "Monthly data missing 'month'"
            assert "revenue" in month_data, "Monthly data missing 'revenue'"
        
        print(f"✓ Monthly trend: {len(monthly)} months of data")
    
    def test_revenue_period_parameter(self, admin_token):
        """Revenue accepts period_days parameter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/revenue?period_days=30", headers=headers)
        data = response.json()
        
        assert response.status_code == 200
        assert "period_days" in data, "Missing 'period_days' in response"
        assert data["period_days"] == 30, f"Expected period_days=30, got {data['period_days']}"
        print("✓ Revenue period parameter works")


class TestPatternEngineInsights:
    """Test GET /api/admin/patterns/insights endpoint"""
    
    def test_insights_returns_200(self, admin_token):
        """Insights endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/insights", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Insights returns 200")
    
    def test_insights_returns_list(self, admin_token):
        """Insights returns a list of actionable insights"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/insights", headers=headers)
        data = response.json()
        
        assert isinstance(data, list), "Insights should return a list"
        print(f"✓ Insights: {len(data)} actionable insights")
    
    def test_insights_structure(self, admin_token):
        """Insights have proper structure with id, type, priority, title, description"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/insights", headers=headers)
        data = response.json()
        
        if data:
            insight = data[0]
            required_fields = ["id", "type", "priority", "title", "description"]
            for field in required_fields:
                assert field in insight, f"Insight missing '{field}'"
            
            assert insight["type"] in ["warning", "success", "opportunity"], f"Invalid type: {insight['type']}"
            assert insight["priority"] in ["high", "medium", "low"], f"Invalid priority: {insight['priority']}"
            print(f"✓ Insight structure valid: [{insight['priority']}] {insight['title'][:50]}...")


class TestPatternEngineChurnRisk:
    """Test GET /api/admin/patterns/churn-risk endpoint"""
    
    def test_churn_risk_returns_200(self, admin_token):
        """Churn-risk endpoint returns 200 with valid admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/churn-risk", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Churn-risk returns 200")
    
    def test_churn_risk_has_counts(self, admin_token):
        """Churn-risk contains risk counts"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/churn-risk", headers=headers)
        data = response.json()
        
        assert "total_at_risk" in data, "Missing 'total_at_risk'"
        assert "high_risk_count" in data, "Missing 'high_risk_count'"
        assert "medium_risk_count" in data, "Missing 'medium_risk_count'"
        assert "detected_at" in data, "Missing 'detected_at'"
        
        print(f"✓ Churn risk: {data['total_at_risk']} at risk ({data['high_risk_count']} high, {data['medium_risk_count']} medium)")
    
    def test_churn_risk_has_creators_list(self, admin_token):
        """Churn-risk contains list of at-risk creators"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/patterns/churn-risk", headers=headers)
        data = response.json()
        
        assert "at_risk_creators" in data, "Missing 'at_risk_creators'"
        assert isinstance(data["at_risk_creators"], list), "'at_risk_creators' should be a list"
        
        if data["at_risk_creators"]:
            creator = data["at_risk_creators"][0]
            required_fields = ["creator_id", "creator_name", "risk_score", "risk_level", "risk_factors"]
            for field in required_fields:
                assert field in creator, f"At-risk creator missing '{field}'"
            
            assert creator["risk_level"] in ["high", "medium"], f"Invalid risk_level: {creator['risk_level']}"
            assert isinstance(creator["risk_factors"], list), "'risk_factors' should be a list"
            print(f"✓ At-risk creator: {creator['creator_name']} (score: {creator['risk_score']}, level: {creator['risk_level']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
