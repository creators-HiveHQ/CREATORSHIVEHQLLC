"""
Subscription & Stripe Integration Tests
Tests for Self-Funding Loop - Updated 5-tier subscription plans
Tiers: Free ($0), Starter ($9.99), Pro ($29.99), Premium ($99.99), Elite (Custom)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://creators-db-master.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_CREATOR_EMAIL = "testcreator@example.com"
TEST_CREATOR_PASSWORD = "creator123"


@pytest.fixture(scope="function")
def api_client():
    """Fresh requests session for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


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


@pytest.fixture(scope="function")
def authenticated_client(creator_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creator_token}"
    })
    return session


class TestSubscriptionPlans:
    """Tests for GET /api/subscriptions/plans endpoint - 5 tiers with 8 plans"""
    
    def test_plans_endpoint_returns_200(self, api_client):
        """Plans endpoint should return 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        print("✓ Plans endpoint returns 200")
    
    def test_plans_returns_all_8_plans(self, api_client):
        """Should return all 8 subscription plans (5 tiers with monthly/annual variants)"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        data = response.json()
        
        assert "plans" in data
        assert len(data["plans"]) == 8
        
        plan_ids = [p["plan_id"] for p in data["plans"]]
        expected_plans = [
            "free", 
            "starter_monthly", "starter_annual",
            "pro_monthly", "pro_annual",
            "premium_monthly", "premium_annual",
            "elite"
        ]
        
        for expected in expected_plans:
            assert expected in plan_ids, f"Missing plan: {expected}"
        
        print(f"✓ All 8 plans returned: {plan_ids}")
    
    # ============== FREE TIER TESTS ==============
    
    def test_free_plan_pricing(self, api_client):
        """Free plan should be $0"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        free = plans["free"]
        assert free["price"] == 0.0
        assert free["tier"] == "free"
        print("✓ Free plan: $0")
    
    def test_free_plan_features(self, api_client):
        """Free plan: 3 proposals, no ARRIS insights"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        free = plans["free"]
        assert free["features"]["arris_insights"] == False
        assert free["features"]["proposal_limit"] == 3
        assert free["features"]["priority_review"] == False
        assert free["features"]["advanced_dashboards"] == False
        assert free["features"]["support_level"] == "community"
        print("✓ Free plan: No ARRIS, 3 proposals, community support")
    
    # ============== STARTER TIER TESTS ==============
    
    def test_starter_monthly_pricing(self, api_client):
        """Starter Monthly should be $9.99/month"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        starter_monthly = plans["starter_monthly"]
        assert starter_monthly["price"] == 9.99
        assert starter_monthly["billing_cycle"] == "monthly"
        assert starter_monthly["tier"] == "starter"
        print("✓ Starter Monthly: $9.99/month")
    
    def test_starter_annual_pricing(self, api_client):
        """Starter Annual should be $99.99/year with $19.89 savings"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        starter_annual = plans["starter_annual"]
        assert starter_annual["price"] == 99.99
        assert starter_annual["billing_cycle"] == "annual"
        assert starter_annual["savings"] == 19.89
        assert starter_annual["monthly_equivalent"] == 8.33
        print("✓ Starter Annual: $99.99/year (save $19.89)")
    
    def test_starter_plan_features(self, api_client):
        """Starter plan: 10 proposals, ARRIS insights enabled"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        starter = plans["starter_monthly"]
        assert starter["features"]["arris_insights"] == True
        assert starter["features"]["proposal_limit"] == 10
        assert starter["features"]["priority_review"] == False
        assert starter["features"]["advanced_dashboards"] == False
        assert starter["features"]["support_level"] == "email"
        print("✓ Starter plan: ARRIS enabled, 10 proposals, email support")
    
    # ============== PRO TIER TESTS ==============
    
    def test_pro_monthly_pricing(self, api_client):
        """Pro Monthly should be $29.99/month"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro_monthly = plans["pro_monthly"]
        assert pro_monthly["price"] == 29.99
        assert pro_monthly["billing_cycle"] == "monthly"
        assert pro_monthly["tier"] == "pro"
        print("✓ Pro Monthly: $29.99/month")
    
    def test_pro_annual_pricing(self, api_client):
        """Pro Annual should be $299.99/year with $59.89 savings"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro_annual = plans["pro_annual"]
        assert pro_annual["price"] == 299.99
        assert pro_annual["billing_cycle"] == "annual"
        assert pro_annual["savings"] == 59.89
        assert pro_annual["monthly_equivalent"] == 25.0
        print("✓ Pro Annual: $299.99/year (save $59.89)")
    
    def test_pro_plan_features(self, api_client):
        """Pro plan: 25 proposals, priority review, advanced dashboards"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro = plans["pro_monthly"]
        assert pro["features"]["arris_insights"] == True
        assert pro["features"]["proposal_limit"] == 25
        assert pro["features"]["priority_review"] == True
        assert pro["features"]["advanced_dashboards"] == True
        assert pro["features"]["support_level"] == "priority"
        print("✓ Pro plan: ARRIS, 25 proposals, priority review, advanced dashboards")
    
    def test_pro_is_most_popular(self, api_client):
        """Pro Monthly should have 'Most Popular' badge"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        pro_monthly = plans["pro_monthly"]
        assert pro_monthly["is_popular"] == True
        print("✓ Pro Monthly has 'Most Popular' badge")
    
    # ============== PREMIUM TIER TESTS ==============
    
    def test_premium_monthly_pricing(self, api_client):
        """Premium Monthly should be $99.99/month"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        premium_monthly = plans["premium_monthly"]
        assert premium_monthly["price"] == 99.99
        assert premium_monthly["billing_cycle"] == "monthly"
        assert premium_monthly["tier"] == "premium"
        print("✓ Premium Monthly: $99.99/month")
    
    def test_premium_annual_pricing(self, api_client):
        """Premium Annual should be $999.99/year with $199.89 savings"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        premium_annual = plans["premium_annual"]
        assert premium_annual["price"] == 999.99
        assert premium_annual["billing_cycle"] == "annual"
        assert premium_annual["savings"] == 199.89
        assert premium_annual["monthly_equivalent"] == 83.33
        print("✓ Premium Annual: $999.99/year (save $199.89)")
    
    def test_premium_plan_features(self, api_client):
        """Premium plan: unlimited proposals, API access"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        premium = plans["premium_monthly"]
        assert premium["features"]["arris_insights"] == True
        assert premium["features"]["proposal_limit"] == -1  # Unlimited
        assert premium["features"]["priority_review"] == True
        assert premium["features"]["advanced_dashboards"] == True
        assert premium["features"]["api_access"] == True
        assert premium["features"]["custom_integrations"] == True
        print("✓ Premium plan: Unlimited proposals, API access")
    
    # ============== ELITE TIER TESTS ==============
    
    def test_elite_plan_is_custom(self, api_client):
        """Elite plan should have is_custom=true"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        elite = plans["elite"]
        assert elite["is_custom"] == True
        assert elite["tier"] == "elite"
        print("✓ Elite plan: is_custom=true")
    
    def test_elite_plan_features(self, api_client):
        """Elite plan: dedicated support, account manager"""
        response = api_client.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = {p["plan_id"]: p for p in response.json()["plans"]}
        
        elite = plans["elite"]
        assert elite["features"]["arris_insights"] == True
        assert elite["features"]["proposal_limit"] == -1  # Unlimited
        assert elite["features"]["support_level"] == "dedicated"
        assert elite["features"]["dedicated_account_manager"] == True
        assert elite["features"]["custom_training"] == True
        assert elite["features"]["sla_guarantee"] == True
        print("✓ Elite plan: Dedicated support, account manager, SLA guarantee")


class TestSubscriptionStatus:
    """Tests for GET /api/subscriptions/my-status endpoint"""
    
    def test_status_requires_auth(self, api_client):
        """Status endpoint should require authentication"""
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


class TestCheckoutEndpoint:
    """Tests for POST /api/subscriptions/checkout endpoint"""
    
    def test_checkout_requires_auth(self, api_client):
        """Checkout endpoint should require authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={"plan_id": "pro_monthly", "origin_url": "https://example.com"}
        )
        assert response.status_code in [401, 403]
        print("✓ Checkout endpoint requires authentication")
    
    def test_checkout_creates_session_starter(self, authenticated_client):
        """Checkout should create Stripe session for Starter plan"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "starter_monthly",
                "origin_url": "https://creators-db-master.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "checkout_url" in data
        assert data["plan_id"] == "starter_monthly"
        assert data["amount"] == 9.99
        print(f"✓ Starter checkout: ${data['amount']}")
    
    def test_checkout_creates_session_pro(self, authenticated_client):
        """Checkout should create Stripe session for Pro plan"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "pro_monthly",
                "origin_url": "https://creators-db-master.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan_id"] == "pro_monthly"
        assert data["amount"] == 29.99
        print(f"✓ Pro checkout: ${data['amount']}")
    
    def test_checkout_creates_session_premium(self, authenticated_client):
        """Checkout should create Stripe session for Premium plan"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "premium_monthly",
                "origin_url": "https://creators-db-master.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan_id"] == "premium_monthly"
        assert data["amount"] == 99.99
        print(f"✓ Premium checkout: ${data['amount']}")
    
    def test_checkout_rejects_elite_plan(self, authenticated_client):
        """Elite plan checkout should be rejected (contact us only)"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "plan_id": "elite",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400
        assert "contact" in response.json().get("detail", "").lower()
        print("✓ Elite plan checkout rejected with 'contact us' message")
    
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


class TestTransactionsEndpoint:
    """Tests for GET /api/subscriptions/my-transactions endpoint"""
    
    def test_transactions_requires_auth(self, api_client):
        """Transactions endpoint should require authentication"""
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
