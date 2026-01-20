"""
Feature Gating System Tests
Tests for 5-tier subscription feature gating:
- Free: 1 proposal/month, summary_only ARRIS insights
- Starter: 3 proposals/month, summary_strengths ARRIS insights
- Pro: unlimited proposals, full ARRIS insights
- Premium: unlimited proposals, full insights, fast processing
- Elite: unlimited proposals, full insights, custom workflows

Tests cover:
1. Subscription plans endpoint returns correct features
2. Subscription status endpoint returns correct limits
3. Feature access endpoint returns full feature info
4. Proposal limit enforcement for Free tier
5. ARRIS insight filtering based on tier
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://creators-db-master.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_CREATOR_EMAIL = "testcreator@example.com"
TEST_CREATOR_PASSWORD = "creator123"
FEATURE_TEST_EMAIL = "featuretest@example.com"
FEATURE_TEST_PASSWORD = "testpass123"
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="function")
def api_client():
    """Fresh requests session for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed - skipping admin tests")


@pytest.fixture(scope="module")
def creator_token():
    """Get creator authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": TEST_CREATOR_EMAIL, "password": TEST_CREATOR_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Creator authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def feature_test_token():
    """Get feature test creator authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": FEATURE_TEST_EMAIL, "password": FEATURE_TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Feature test creator authentication failed")


@pytest.fixture(scope="function")
def authenticated_client(creator_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creator_token}"
    })
    return session


class TestSubscriptionPlansFeatures:
    """Tests for GET /api/subscriptions/plans - verify 5-tier feature structure"""
    
    def test_plans_returns_8_plans_with_5_tiers(self, api_client):
        """Should return 8 plans covering 5 tiers"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        
        data = response.json()
        plans = data["plans"]
        
        # Check we have 8 plans
        assert len(plans) == 8
        
        # Check all 5 tiers are represented
        tiers = set(p["tier"] for p in plans)
        expected_tiers = {"free", "starter", "pro", "premium", "elite"}
        assert tiers == expected_tiers
        print(f"✓ All 5 tiers present: {tiers}")
    
    def test_free_tier_features(self, api_client):
        """Free tier: 1 proposal/month, summary_only ARRIS"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        free = plans["free"]
        assert free["features"]["proposals_per_month"] == 1
        assert free["features"]["arris_insights"] == "summary_only"
        assert free["features"]["dashboard_level"] == "basic"
        assert free["features"]["priority_review"] == False
        assert free["features"]["api_access"] == False
        print("✓ Free tier: 1 proposal, summary_only ARRIS, basic dashboard")
    
    def test_starter_tier_features(self, api_client):
        """Starter tier: 3 proposals/month, summary_strengths ARRIS"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        starter = plans["starter_monthly"]
        assert starter["features"]["proposals_per_month"] == 3
        assert starter["features"]["arris_insights"] == "summary_strengths"
        assert starter["features"]["dashboard_level"] == "basic"
        assert starter["features"]["priority_review"] == False
        print("✓ Starter tier: 3 proposals, summary_strengths ARRIS")
    
    def test_pro_tier_features(self, api_client):
        """Pro tier: unlimited proposals, full ARRIS insights"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro = plans["pro_monthly"]
        assert pro["features"]["proposals_per_month"] == -1  # Unlimited
        assert pro["features"]["arris_insights"] == "full"
        assert pro["features"]["dashboard_level"] == "advanced"
        assert pro["features"]["priority_review"] == True
        print("✓ Pro tier: unlimited proposals, full ARRIS, advanced dashboard, priority review")
    
    def test_premium_tier_features(self, api_client):
        """Premium tier: unlimited, full ARRIS, fast processing, API access"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        premium = plans["premium_monthly"]
        assert premium["features"]["proposals_per_month"] == -1
        assert premium["features"]["arris_insights"] == "full"
        assert premium["features"]["arris_processing_speed"] == "fast"
        assert premium["features"]["api_access"] == True
        assert premium["features"]["advanced_analytics"] == True
        print("✓ Premium tier: unlimited, full ARRIS, fast processing, API access")
    
    def test_elite_tier_features(self, api_client):
        """Elite tier: unlimited, full ARRIS, custom workflows, brand integrations"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        elite = plans["elite"]
        assert elite["features"]["proposals_per_month"] == -1
        assert elite["features"]["arris_insights"] == "full"
        assert elite["features"]["custom_arris_workflows"] == True
        assert elite["features"]["brand_integrations"] == True
        assert elite["features"]["dashboard_level"] == "custom"
        assert elite["is_custom"] == True
        print("✓ Elite tier: unlimited, full ARRIS, custom workflows, brand integrations")


class TestSubscriptionStatus:
    """Tests for GET /api/subscriptions/my-status - verify current subscription info"""
    
    def test_status_requires_auth(self, api_client):
        """Status endpoint should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert response.status_code in [401, 403]
        print("✓ Status endpoint requires authentication")
    
    def test_status_returns_tier_info(self, authenticated_client):
        """Status should return tier and feature info"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "tier" in data
        assert "plan_id" in data
        assert "features" in data
        assert "proposals_per_month" in data
        assert "proposals_used" in data
        assert "proposals_remaining" in data
        assert "can_create_proposal" in data
        assert "arris_insight_level" in data
        print(f"✓ Status returned: tier={data['tier']}, arris_level={data['arris_insight_level']}")
    
    def test_status_shows_proposal_usage(self, authenticated_client):
        """Status should show proposal usage for the month"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        data = response.json()
        
        # Verify proposal tracking fields
        assert isinstance(data["proposals_used"], int)
        assert isinstance(data["proposals_per_month"], int)
        assert "proposals_remaining" in data
        
        # For free tier, limit should be 1
        if data["tier"] == "free":
            assert data["proposals_per_month"] == 1
        
        print(f"✓ Proposal usage: {data['proposals_used']}/{data['proposals_per_month']}")


class TestFeatureAccess:
    """Tests for GET /api/subscriptions/feature-access - full feature info"""
    
    def test_feature_access_requires_auth(self, api_client):
        """Feature access endpoint should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code in [401, 403]
        print("✓ Feature access endpoint requires authentication")
    
    def test_feature_access_returns_full_info(self, authenticated_client):
        """Feature access should return complete feature info"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code == 200
        
        data = response.json()
        assert "tier" in data
        assert "plan_id" in data
        assert "features" in data
        assert "subscription_active" in data
        
        features = data["features"]
        assert "proposals_per_month" in features
        assert "proposals_used" in features
        assert "proposals_remaining" in features
        assert "can_create_proposal" in features
        assert "arris_insight_level" in features
        assert "dashboard_level" in features
        assert "priority_review" in features
        assert "api_access" in features
        
        print(f"✓ Feature access returned: tier={data['tier']}, features={len(features)} fields")


class TestCanCreateProposal:
    """Tests for GET /api/subscriptions/can-create-proposal - proposal limit check"""
    
    def test_can_create_requires_auth(self, api_client):
        """Can create proposal endpoint should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        assert response.status_code in [401, 403]
        print("✓ Can create proposal endpoint requires authentication")
    
    def test_can_create_returns_limit_info(self, authenticated_client):
        """Should return proposal limit info"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        assert response.status_code == 200
        
        data = response.json()
        assert "can_create" in data
        assert "limit" in data
        assert "used" in data
        assert "remaining" in data
        assert "upgrade_needed" in data
        assert "tier" in data
        assert "message" in data
        
        print(f"✓ Can create: {data['can_create']}, limit={data['limit']}, used={data['used']}")
    
    def test_free_tier_limit_is_1(self, authenticated_client):
        """Free tier should have limit of 1 proposal per month"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        data = response.json()
        
        if data["tier"] == "free":
            assert data["limit"] == 1
            print("✓ Free tier limit is 1 proposal/month")
        else:
            pytest.skip("Test creator is not on free tier")


class TestProposalLimitEnforcement:
    """Tests for POST /api/proposals - verify proposal limit is enforced"""
    
    def test_proposal_blocked_when_limit_reached(self, authenticated_client):
        """Proposal creation should be blocked when monthly limit reached"""
        # First check if limit is already reached
        status_response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        status = status_response.json()
        
        if status["can_create"]:
            pytest.skip("Creator can still create proposals - limit not reached")
        
        # Try to create a proposal
        response = authenticated_client.post(
            f"{BASE_URL}/api/proposals",
            json={
                "title": "Test Blocked Proposal",
                "description": "This should be blocked due to limit"
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"] == "proposal_limit_reached"
        assert "upgrade_url" in data["detail"]
        print(f"✓ Proposal blocked: {data['detail']['message']}")
    
    def test_proposal_blocked_returns_upgrade_url(self, authenticated_client):
        """Blocked proposal should return upgrade URL"""
        status_response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        status = status_response.json()
        
        if status["can_create"]:
            pytest.skip("Creator can still create proposals - limit not reached")
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/proposals",
            json={
                "title": "Test Blocked Proposal",
                "description": "This should be blocked"
            }
        )
        
        data = response.json()
        assert data["detail"]["upgrade_url"] == "/creator/subscription"
        print("✓ Blocked proposal returns upgrade URL")


class TestArrisInsightFiltering:
    """Tests for ARRIS insight filtering based on subscription tier"""
    
    def test_free_tier_gets_summary_only(self, authenticated_client):
        """Free tier should only get summary and complexity, with gated prompts"""
        # Get a submitted proposal with ARRIS insights
        response = authenticated_client.get(f"{BASE_URL}/api/creators/me/proposals?status=submitted")
        
        if response.status_code != 200:
            pytest.skip("Could not fetch proposals")
        
        proposals = response.json()
        submitted_proposals = [p for p in proposals if p.get("arris_insights")]
        
        if not submitted_proposals:
            pytest.skip("No submitted proposals with ARRIS insights found")
        
        proposal = submitted_proposals[0]
        insights = proposal.get("arris_insights", {})
        
        # Check insight level
        if insights.get("insight_level") == "summary_only":
            # Should have summary
            assert "summary" in insights
            # Should have complexity
            assert "estimated_complexity" in insights
            # Should have gated prompts
            assert "_gated" in insights
            gated = insights["_gated"]
            assert "strengths" in gated
            assert "risks" in gated
            assert "recommendations" in gated
            assert "milestones" in gated
            # Should NOT have full insights
            assert "strengths" not in insights or insights.get("strengths") is None
            assert "risks" not in insights or insights.get("risks") is None
            print("✓ Free tier gets summary_only with gated prompts")
        else:
            print(f"Note: Creator has {insights.get('insight_level')} access")
    
    def test_gated_prompts_show_upgrade_message(self, authenticated_client):
        """Gated prompts should show upgrade messages"""
        response = authenticated_client.get(f"{BASE_URL}/api/creators/me/proposals?status=submitted")
        
        if response.status_code != 200:
            pytest.skip("Could not fetch proposals")
        
        proposals = response.json()
        submitted_proposals = [p for p in proposals if p.get("arris_insights", {}).get("_gated")]
        
        if not submitted_proposals:
            pytest.skip("No proposals with gated insights found")
        
        proposal = submitted_proposals[0]
        gated = proposal["arris_insights"]["_gated"]
        
        # Check upgrade messages
        assert "Upgrade" in gated.get("strengths", "")
        assert "Upgrade" in gated.get("risks", "")
        assert "Upgrade" in gated.get("recommendations", "")
        print("✓ Gated prompts show upgrade messages")


class TestIntegrationFlow:
    """Integration tests for complete feature gating flow"""
    
    def test_free_tier_complete_flow(self, feature_test_token):
        """Test complete flow: check limit -> create proposal -> verify blocked"""
        if not feature_test_token:
            pytest.skip("Feature test token not available")
        
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {feature_test_token}"
        })
        
        # Step 1: Check current status
        status_response = session.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert status_response.status_code == 200
        status = status_response.json()
        
        print(f"Current status: tier={status['tier']}, used={status['proposals_used']}/{status['proposals_per_month']}")
        
        # Step 2: Check can create
        can_create_response = session.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        can_create = can_create_response.json()
        
        if can_create["can_create"]:
            print(f"Can create proposal: {can_create['remaining']} remaining")
        else:
            print(f"Cannot create: {can_create['message']}")
            # Verify blocked
            create_response = session.post(
                f"{BASE_URL}/api/proposals",
                json={"title": "Test", "description": "Test description"}
            )
            assert create_response.status_code == 403
            print("✓ Proposal creation correctly blocked")
        
        print("✓ Complete flow test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
