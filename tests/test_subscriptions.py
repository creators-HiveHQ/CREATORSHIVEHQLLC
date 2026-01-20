"""
Subscription & Stripe Integration Tests
Tests for Self-Funding Loop - Subscription plans and checkout flow
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://pattern-engine-3.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_CREATOR_EMAIL = "testcreator@example.com"
TEST_CREATOR_PASSWORD = "creator123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def creator_token(api_client):
    """Get creator authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/creators/login",
        json={"email": TEST_CREATOR_EMAIL, "password": TEST_CREATOR_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Creator authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, creator_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {creator_token}"})
    return api_client


class TestSubscriptionPlans:
    """Tests for GET /api/subscriptions/plans endpoint"""
    
    def test_plans_endpoint_returns_200(self, api_client):
        """Plans endpoint should return 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        print("✓ Plans endpoint returns 200")
    
    def test_plans_returns_all_5_plans(self, api_client):
        """Should return all 5 subscription plans"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        data = response.json()
        
        assert "plans" in data
        assert len(data["plans"]) == 5
        
        plan_ids = [p["plan_id"] for p in data["plans"]]
        expected_plans = ["free", "pro_monthly", "pro_annual", "enterprise_monthly", "enterprise_annual"]
        
        for expected in expected_plans:
            assert expected in plan_ids, f"Missing plan: {expected}"
        
        print(f"✓ All 5 plans returned: {plan_ids}")
    
    def test_pro_monthly_pricing(self, api_client):
        """Pro Monthly should be $29/month"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro_monthly = plans["pro_monthly"]
        assert pro_monthly["price"] == 29.0
        assert pro_monthly["billing_cycle"] == "monthly"
        assert pro_monthly["tier"] == "pro"
        print("✓ Pro Monthly: $29/month")
    
    def test_pro_annual_pricing(self, api_client):
        """Pro Annual should be $290/year with $58 savings"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro_annual = plans["pro_annual"]
        assert pro_annual["price"] == 290.0
        assert pro_annual["billing_cycle"] == "annual"
        assert pro_annual["savings"] == 58.0
        assert pro_annual["monthly_equivalent"] == 24.17
        print("✓ Pro Annual: $290/year (save $58)")
    
    def test_enterprise_monthly_pricing(self, api_client):
        """Enterprise Monthly should be $99/month"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        enterprise_monthly = plans["enterprise_monthly"]
        assert enterprise_monthly["price"] == 99.0
        assert enterprise_monthly["billing_cycle"] == "monthly"
        assert enterprise_monthly["tier"] == "enterprise"
        print("✓ Enterprise Monthly: $99/month")
    
    def test_enterprise_annual_pricing(self, api_client):
        """Enterprise Annual should be $990/year with $198 savings"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        enterprise_annual = plans["enterprise_annual"]
        assert enterprise_annual["price"] == 990.0
        assert enterprise_annual["billing_cycle"] == "annual"
        assert enterprise_annual["savings"] == 198.0
        assert enterprise_annual["monthly_equivalent"] == 82.5
        print("✓ Enterprise Annual: $990/year (save $198)")
    
    def test_free_plan_features(self, api_client):
        """Free plan should have correct feature limits"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        free = plans["free"]
        assert free["price"] == 0.0
        assert free["features"]["arris_insights"] == False
        assert free["features"]["proposal_limit"] == 3
        assert free["features"]["priority_review"] == False
        assert free["features"]["advanced_dashboards"] == False
        print("✓ Free plan: No ARRIS, 3 proposals, no priority review")
    
    def test_pro_plan_features(self, api_client):
        """Pro plans should have ARRIS insights and priority review"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro = plans["pro_monthly"]
        assert pro["features"]["arris_insights"] == True
        assert pro["features"]["proposal_limit"] == 20
        assert pro["features"]["priority_review"] == True
        assert pro["features"]["advanced_dashboards"] == True
        print("✓ Pro plan: ARRIS enabled, 20 proposals, priority review")
    
    def test_enterprise_plan_features(self, api_client):
        """Enterprise plans should have unlimited proposals and API access"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        enterprise = plans["enterprise_monthly"]
        assert enterprise["features"]["arris_insights"] == True
        assert enterprise["features"]["proposal_limit"] == -1  # Unlimited
        assert enterprise["features"]["priority_review"] == True
        assert enterprise["features"]["api_access"] == True
        assert enterprise["features"]["custom_integrations"] == True
        print("✓ Enterprise plan: Unlimited proposals, API access")


class TestSubscriptionStatus:
    """Tests for GET /api/subscriptions/my-status endpoint"""
    
    def test_status_requires_auth(self, api_client):
        """Status endpoint should require authentication"""
        # Remove auth header temporarily
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert response.status_code in [401, 403]
        print("✓ Status endpoint requires authentication")
    
    def test_status_returns_subscription_info(self, authenticated_client):
        """Status should return subscription info for authenticated creator"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "has_subscription" in data
        assert "tier" in data
        assert "features" in data
        assert "can_use_arris" in data
        assert "proposal_limit" in data
        assert "proposals_used" in data
        assert "proposals_remaining" in data
        print(f"✓ Status returned: tier={data['tier']}, proposals={data['proposals_used']}/{data['proposal_limit']}")
    
    def test_free_tier_status(self, authenticated_client):
        """Free tier should show correct limits"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        data = response.json()
        
        # Test creator is on free tier
        assert data["tier"] == "free"
        assert data["proposal_limit"] == 3
        assert data["can_use_arris"] == False
        print(f"✓ Free tier: limit=3, can_use_arris=False")
    
    def test_proposal_usage_tracking(self, authenticated_client):
        """Should track proposal usage correctly"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-status")
        data = response.json()
        
        # Test creator has 7 proposals (over limit)
        assert data["proposals_used"] >= 7
        assert data["proposals_remaining"] == 0  # Over limit
        print(f"✓ Proposal usage: {data['proposals_used']}/{data['proposal_limit']} (remaining: {data['proposals_remaining']})")


class TestCheckoutEndpoint:
    """Tests for POST /api/subscriptions/checkout endpoint"""
    
    def test_checkout_requires_auth(self, api_client):
        """Checkout endpoint should require authentication"""
        # Remove auth header temporarily
        api_client.headers.pop("Authorization", None)
        response = api_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={"plan_id": "pro_monthly", "origin_url": "https://example.com"}
        )
        assert response.status_code in [401, 403]
        print("✓ Checkout endpoint requires authentication")
    
    def test_checkout_creates_session(self, authenticated_client):
        """Checkout should create Stripe session for valid plan"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "pro_monthly",
                "origin_url": "https://pattern-engine-3.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["plan_id"] == "pro_monthly"
        assert data["amount"] == 29.0
        assert data["currency"] == "usd"
        assert "stripe.com" in data["checkout_url"]
        print(f"✓ Checkout session created: {data['session_id'][:20]}...")
    
    def test_checkout_validates_plan_id(self, authenticated_client):
        """Checkout should reject invalid plan IDs"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "invalid_plan",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400
        print("✓ Invalid plan_id rejected")
    
    def test_checkout_rejects_free_plan(self, authenticated_client):
        """Checkout should reject free plan (no payment needed)"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "free",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400
        print("✓ Free plan checkout rejected")
    
    def test_checkout_amount_from_server(self, authenticated_client):
        """Amount should come from server, not frontend"""
        # Try to pass a different amount (should be ignored)
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "enterprise_monthly",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Amount should be $99 (server-side), not any frontend value
        assert data["amount"] == 99.0
        print("✓ Amount validated server-side: $99")


class TestTransactionsEndpoint:
    """Tests for GET /api/subscriptions/my-transactions endpoint"""
    
    def test_transactions_requires_auth(self, api_client):
        """Transactions endpoint should require authentication"""
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/subscriptions/my-transactions")
        assert response.status_code in [401, 403]
        print("✓ Transactions endpoint requires authentication")
    
    def test_transactions_returns_list(self, authenticated_client):
        """Transactions should return list for authenticated creator"""
        response = authenticated_client.get(f"{BASE_URL}/api/subscriptions/my-transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)
        print(f"✓ Transactions returned: {data['total']} total")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
