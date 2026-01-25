"""
Test Suite for Module B3: Subscription Lifecycle Automation
Tests health scoring, risk detection, lifecycle stages, and retention actions.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://creatorshivehq.preview.emergentagent.com').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"

# Test creator IDs from seed data
TEST_CREATOR_IDS = [
    "CREATOR-TEST-PRO-001",
    "CREATOR-TEST-ELITE-001",
    "CREATOR-TEST-PREMIUM-001",
    "CREATOR-TEST-FREE-001",
    "CREATOR-TEST-STARTER-001"
]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture
def auth_headers(admin_token):
    """Return headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestLifecycleMetrics:
    """Tests for GET /api/admin/subscription-lifecycle/metrics"""
    
    def test_metrics_requires_auth(self):
        """Metrics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscription-lifecycle/metrics")
        assert response.status_code == 403
    
    def test_metrics_returns_correct_structure(self, auth_headers):
        """Metrics endpoint returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/metrics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_subscriptions" in data
        assert "active_subscriptions" in data
        assert "lifecycle_stages" in data
        assert "tier_distribution" in data
        assert "health_distribution" in data
        assert "churn_metrics" in data
        assert "analyzed_at" in data
        
        # Verify health distribution structure
        health = data["health_distribution"]
        assert "healthy" in health
        assert "at_risk" in health
        assert "critical" in health
        
        # Verify churn metrics structure
        churn = data["churn_metrics"]
        assert "churned_last_30d" in churn
        assert "churn_rate_30d" in churn
        assert "at_risk_count" in churn
    
    def test_metrics_has_subscriptions(self, auth_headers):
        """Metrics shows subscriptions exist"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/metrics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have some subscriptions from seed data
        assert data["total_subscriptions"] > 0
        assert data["active_subscriptions"] > 0


class TestAtRiskSubscriptions:
    """Tests for GET /api/admin/subscription-lifecycle/at-risk"""
    
    def test_at_risk_requires_auth(self):
        """At-risk endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk")
        assert response.status_code == 403
    
    def test_at_risk_returns_correct_structure(self, auth_headers):
        """At-risk endpoint returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "at_risk_subscriptions" in data
        assert "total_at_risk" in data
        assert "risk_counts" in data
        assert "threshold_applied" in data
        assert "analyzed_at" in data
        
        # Verify risk counts structure
        risk_counts = data["risk_counts"]
        assert "critical" in risk_counts
        assert "high" in risk_counts
        assert "medium" in risk_counts
        assert "low" in risk_counts
    
    def test_at_risk_threshold_filter(self, auth_headers):
        """At-risk endpoint respects threshold filter"""
        # Test with critical threshold
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=critical",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["threshold_applied"] == "critical"
        
        # Test with low threshold (should return more results)
        response_low = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response_low.status_code == 200
        data_low = response_low.json()
        assert data_low["threshold_applied"] == "low"
        
        # Low threshold should return >= critical threshold results
        assert data_low["total_at_risk"] >= data["total_at_risk"]
    
    def test_at_risk_limit_parameter(self, auth_headers):
        """At-risk endpoint respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should not exceed limit
        assert len(data["at_risk_subscriptions"]) <= 5
    
    def test_at_risk_subscription_structure(self, auth_headers):
        """At-risk subscriptions have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["at_risk_subscriptions"]:
            sub = data["at_risk_subscriptions"][0]
            assert "creator_id" in sub
            assert "tier" in sub
            assert "health_score" in sub
            assert "risk_level" in sub
            assert "lifecycle_stage" in sub
            assert "top_risk_factors" in sub
            assert "recommendations" in sub


class TestHealthAnalysis:
    """Tests for GET /api/admin/subscription-lifecycle/health/{creator_id}"""
    
    def test_health_requires_auth(self):
        """Health endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001"
        )
        assert response.status_code == 403
    
    def test_health_returns_correct_structure(self, auth_headers):
        """Health endpoint returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "creator_id" in data
        assert "subscription" in data
        assert "health_score" in data
        assert "risk_level" in data
        assert "lifecycle_stage" in data
        assert "risk_analysis" in data
        assert "recommendations" in data
        assert "last_analyzed" in data
        
        # Verify subscription structure
        sub = data["subscription"]
        assert "tier" in sub
        assert "status" in sub
        assert "plan_name" in sub
        assert "days_remaining" in sub
    
    def test_health_score_range(self, auth_headers):
        """Health score is within valid range (0-100)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert 0 <= data["health_score"] <= 100
    
    def test_risk_level_values(self, auth_headers):
        """Risk level is one of valid values"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_risk_levels = ["critical", "high", "medium", "low"]
        assert data["risk_level"] in valid_risk_levels
    
    def test_lifecycle_stage_values(self, auth_headers):
        """Lifecycle stage is one of valid values"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        valid_stages = ["onboarding", "activation", "engaged", "at_risk", "churning", "churned", "reactivated"]
        assert data["lifecycle_stage"] in valid_stages
    
    def test_risk_analysis_factors(self, auth_headers):
        """Risk analysis includes all expected factors"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        risk_analysis = data["risk_analysis"]
        expected_factors = ["inactivity", "proposal_performance", "engagement", "support_issues", "payment_health"]
        
        for factor in expected_factors:
            assert factor in risk_analysis
            assert "risk_score" in risk_analysis[factor]
            assert "status" in risk_analysis[factor]
    
    def test_health_nonexistent_creator(self, auth_headers):
        """Health endpoint returns 404 for nonexistent creator"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/NONEXISTENT-CREATOR-ID",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestRetentionAction:
    """Tests for POST /api/admin/subscription-lifecycle/retention-action"""
    
    def test_retention_action_requires_auth(self):
        """Retention action endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            json={"creator_id": "CREATOR-TEST-PRO-001", "action": "engagement_nudge"}
        )
        assert response.status_code == 403
    
    def test_retention_action_requires_creator_id(self, auth_headers):
        """Retention action requires creator_id"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={"action": "engagement_nudge"}
        )
        assert response.status_code == 400
    
    def test_retention_action_requires_action(self, auth_headers):
        """Retention action requires action field"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={"creator_id": "CREATOR-TEST-PRO-001"}
        )
        assert response.status_code == 400
    
    def test_retention_action_engagement_nudge(self, auth_headers):
        """Engagement nudge action works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-PRO-001",
                "action": "engagement_nudge",
                "custom_message": "Test engagement nudge"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "action_id" in data
        assert data["action"] == "engagement_nudge"
        assert "result" in data
    
    def test_retention_action_discount_offer(self, auth_headers):
        """Discount offer action works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-ELITE-001",
                "action": "discount_offer"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["action"] == "discount_offer"
    
    def test_retention_action_at_risk_outreach(self, auth_headers):
        """At-risk outreach action works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-PREMIUM-001",
                "action": "at_risk_outreach"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["action"] == "at_risk_outreach"


class TestRetentionHistory:
    """Tests for GET /api/admin/subscription-lifecycle/retention-history"""
    
    def test_retention_history_requires_auth(self):
        """Retention history endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscription-lifecycle/retention-history")
        assert response.status_code == 403
    
    def test_retention_history_returns_correct_structure(self, auth_headers):
        """Retention history returns expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "actions" in data
        assert "total" in data
        assert isinstance(data["actions"], list)
    
    def test_retention_history_action_structure(self, auth_headers):
        """Retention history actions have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["actions"]:
            action = data["actions"][0]
            assert "id" in action
            assert "creator_id" in action
            assert "action" in action
            assert "triggered_by" in action
            assert "created_at" in action
            assert "status" in action
    
    def test_retention_history_filter_by_creator(self, auth_headers):
        """Retention history can filter by creator_id"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-history?creator_id=CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned actions should be for the specified creator
        for action in data["actions"]:
            assert action["creator_id"] == "CREATOR-TEST-PRO-001"
    
    def test_retention_history_limit_parameter(self, auth_headers):
        """Retention history respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-history?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["actions"]) <= 5


class TestUpdateStage:
    """Tests for POST /api/admin/subscription-lifecycle/update-stage"""
    
    def test_update_stage_requires_auth(self):
        """Update stage endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            json={"creator_id": "CREATOR-TEST-PRO-001", "stage": "engaged"}
        )
        assert response.status_code == 403
    
    def test_update_stage_requires_creator_id(self, auth_headers):
        """Update stage requires creator_id"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            headers=auth_headers,
            json={"stage": "engaged"}
        )
        assert response.status_code == 400
    
    def test_update_stage_requires_stage(self, auth_headers):
        """Update stage requires stage field"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            headers=auth_headers,
            json={"creator_id": "CREATOR-TEST-PRO-001"}
        )
        assert response.status_code == 400
    
    def test_update_stage_success(self, auth_headers):
        """Update stage works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-ELITE-001",
                "stage": "engaged",
                "reason": "Manual update for testing"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["new_stage"] == "engaged"
    
    def test_update_stage_to_at_risk(self, auth_headers):
        """Can update stage to at_risk"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-PREMIUM-001",
                "stage": "at_risk",
                "reason": "Testing at_risk stage"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["new_stage"] == "at_risk"
    
    def test_update_stage_nonexistent_creator(self, auth_headers):
        """Update stage returns error for nonexistent creator"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/update-stage",
            headers=auth_headers,
            json={
                "creator_id": "NONEXISTENT-CREATOR-ID",
                "stage": "engaged"
            }
        )
        assert response.status_code == 400


class TestHealthScoreCalculation:
    """Tests for health score calculation logic"""
    
    def test_health_score_critical_threshold(self, auth_headers):
        """Health score <= 30 should be critical risk"""
        # Get all at-risk subscriptions
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for sub in data["at_risk_subscriptions"]:
            if sub["health_score"] <= 30:
                assert sub["risk_level"] == "critical"
    
    def test_health_score_high_threshold(self, auth_headers):
        """Health score 31-50 should be high risk"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for sub in data["at_risk_subscriptions"]:
            if 31 <= sub["health_score"] <= 50:
                assert sub["risk_level"] == "high"
    
    def test_health_score_medium_threshold(self, auth_headers):
        """Health score 51-70 should be medium risk"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for sub in data["at_risk_subscriptions"]:
            if 51 <= sub["health_score"] <= 70:
                assert sub["risk_level"] == "medium"
    
    def test_health_score_low_threshold(self, auth_headers):
        """Health score > 70 should be low risk"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/at-risk?threshold=low",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for sub in data["at_risk_subscriptions"]:
            if sub["health_score"] > 70:
                assert sub["risk_level"] == "low"


class TestRiskFactors:
    """Tests for risk factor analysis"""
    
    def test_inactivity_factor(self, auth_headers):
        """Inactivity risk factor is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        inactivity = data["risk_analysis"]["inactivity"]
        assert "days_inactive" in inactivity
        assert "risk_score" in inactivity
        assert "status" in inactivity
        assert inactivity["status"] in ["critical", "high", "medium", "low"]
    
    def test_proposal_performance_factor(self, auth_headers):
        """Proposal performance risk factor is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        proposal = data["risk_analysis"]["proposal_performance"]
        assert "total_proposals" in proposal
        assert "decline_rate" in proposal
        assert "risk_score" in proposal
        assert "status" in proposal
    
    def test_engagement_factor(self, auth_headers):
        """Engagement risk factor is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        engagement = data["risk_analysis"]["engagement"]
        assert "engagement_drop" in engagement
        assert "risk_score" in engagement
        assert "status" in engagement
    
    def test_support_issues_factor(self, auth_headers):
        """Support issues risk factor is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        support = data["risk_analysis"]["support_issues"]
        assert "open_tickets" in support
        assert "risk_score" in support
        assert "status" in support
    
    def test_payment_health_factor(self, auth_headers):
        """Payment health risk factor is calculated"""
        response = requests.get(
            f"{BASE_URL}/api/admin/subscription-lifecycle/health/CREATOR-TEST-PRO-001",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        payment = data["risk_analysis"]["payment_health"]
        assert "recent_failures" in payment
        assert "risk_score" in payment
        assert "status" in payment


class TestRetentionActions:
    """Tests for all retention action types"""
    
    @pytest.mark.parametrize("action", [
        "welcome_email",
        "onboarding_reminder",
        "feature_highlight",
        "engagement_nudge",
        "success_celebration",
        "at_risk_outreach",
        "discount_offer",
        "personal_call",
        "win_back_campaign"
    ])
    def test_all_retention_actions(self, auth_headers, action):
        """All retention action types work correctly"""
        response = requests.post(
            f"{BASE_URL}/api/admin/subscription-lifecycle/retention-action",
            headers=auth_headers,
            json={
                "creator_id": "CREATOR-TEST-PRO-001",
                "action": action
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["action"] == action
        assert "action_id" in data
