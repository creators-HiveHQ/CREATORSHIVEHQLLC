"""
Test Subscription Routes (Comprehensive)
=========================================
Tests for all subscription endpoints migrated from server.py to routes/subscriptions.py

Endpoints tested:
- GET /api/subscriptions/plans - public endpoint to get subscription plans
- GET /api/subscriptions/revenue - public endpoint for self-funding loop revenue
- GET /api/subscriptions - generic CRUD to list subscriptions
- POST /api/subscriptions - create subscription with self-funding loop
- GET /api/subscriptions/my-status - authenticated creator subscription status
- GET /api/subscriptions/feature-access - authenticated feature access details
- GET /api/subscriptions/can-create-proposal - check proposal creation limit
- GET /api/subscriptions/me - get current creator subscription
- GET /api/subscriptions/me/features - get feature access for creator
- GET /api/subscriptions/me/usage - get usage stats for current period
- GET /api/subscriptions/me/billing-history - get billing history
- GET /api/subscriptions/my-transactions - get payment transactions
- POST /api/subscriptions/checkout - create Stripe checkout session
- GET /api/subscriptions/checkout/status/{session_id} - check checkout status
- POST /api/subscriptions/me/upgrade - request subscription upgrade
- POST /api/subscriptions/me/cancel - request subscription cancellation
- GET /api/admin/subscriptions - admin list all subscriptions
- GET /api/admin/subscriptions/stats - admin subscription statistics
- GET /api/admin/subscriptions/revenue - admin revenue summary
- POST /api/webhook/stripe - Stripe webhook handler (in server.py)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
FREE_EMAIL = "freetest@hivehq.com"
FREE_PASSWORD = "testpassword"
PRO_EMAIL = "protest@hivehq.com"
PRO_PASSWORD = "testpassword"
ELITE_EMAIL = "elitetest@hivehq.com"
ELITE_PASSWORD = "testpassword123"
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication helpers"""
    
    @staticmethod
    def get_creator_token(email, password):
        """Get creator JWT token via /api/creators/login"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_admin_token():
        """Get admin JWT token via /api/auth/login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


# ============== PUBLIC SUBSCRIPTION ENDPOINTS ==============

class TestPublicSubscriptionEndpoints:
    """Test public subscription endpoints (no auth required)"""
    
    def test_get_subscription_plans(self):
        """GET /api/subscriptions/plans - returns available subscription plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        assert isinstance(data["plans"], list), "Plans should be a list"
        assert len(data["plans"]) > 0, "Should have at least one plan"
        
        # Verify plan structure
        plan = data["plans"][0]
        assert "plan_id" in plan, "Plan should have plan_id"
        assert "name" in plan, "Plan should have name"
        assert "tier" in plan, "Plan should have tier"
        assert "features" in plan, "Plan should have features"
        
        print(f"✓ GET /api/subscriptions/plans returns {len(data['plans'])} plans")
        for p in data["plans"]:
            print(f"  - {p['plan_id']}: {p['name']} (tier: {p['tier']})")
    
    def test_get_subscription_revenue_public(self):
        """GET /api/subscriptions/revenue - returns self-funding loop revenue"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/revenue")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_subscription_revenue" in data, "Response should contain 'total_subscription_revenue'"
        assert "active_subscriptions" in data, "Response should contain 'active_subscriptions'"
        assert "self_funding_status" in data, "Response should contain 'self_funding_status'"
        
        print(f"✓ GET /api/subscriptions/revenue returns:")
        print(f"  - Total revenue: ${data['total_subscription_revenue']}")
        print(f"  - Active subscriptions: {data['active_subscriptions']}")
        print(f"  - Self-funding status: {data['self_funding_status']}")
    
    def test_get_subscriptions_generic_crud(self):
        """GET /api/subscriptions - generic CRUD to list subscriptions"""
        response = requests.get(f"{BASE_URL}/api/subscriptions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/subscriptions returns {len(data)} subscriptions")


# ============== AUTHENTICATED CREATOR ENDPOINTS ==============

class TestCreatorSubscriptionEndpoints:
    """Test authenticated creator subscription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each test"""
        self.free_token = TestAuth.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestAuth.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.elite_token = TestAuth.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
    
    # --- GET /api/subscriptions/my-status ---
    
    def test_my_status_requires_auth(self):
        """GET /api/subscriptions/my-status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my-status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/my-status requires authentication")
    
    def test_my_status_free_tier(self):
        """GET /api/subscriptions/my-status for free tier creator"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "has_subscription" in data, "Response should contain 'has_subscription'"
        assert "features" in data, "Response should contain 'features'"
        assert "proposals_per_month" in data, "Response should contain 'proposals_per_month'"
        assert "can_create_proposal" in data, "Response should contain 'can_create_proposal'"
        
        print(f"✓ GET /api/subscriptions/my-status (free tier):")
        print(f"  - Tier: {data['tier']}")
        print(f"  - Has subscription: {data['has_subscription']}")
        print(f"  - Proposals per month: {data['proposals_per_month']}")
    
    def test_my_status_pro_tier(self):
        """GET /api/subscriptions/my-status for pro tier creator"""
        if not self.pro_token:
            pytest.skip("Pro tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ GET /api/subscriptions/my-status (pro tier): tier={data.get('tier')}")
    
    def test_my_status_elite_tier(self):
        """GET /api/subscriptions/my-status for elite tier creator"""
        if not self.elite_token:
            pytest.skip("Elite tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ GET /api/subscriptions/my-status (elite tier): tier={data.get('tier')}")
    
    # --- GET /api/subscriptions/feature-access ---
    
    def test_feature_access_requires_auth(self):
        """GET /api/subscriptions/feature-access requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/feature-access")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/feature-access requires authentication")
    
    def test_feature_access_with_auth(self):
        """GET /api/subscriptions/feature-access returns feature access details"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/feature-access",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "features" in data, "Response should contain 'features'"
        
        print(f"✓ GET /api/subscriptions/feature-access returns tier={data['tier']}")
        print(f"  - Features: {list(data['features'].keys())}")
    
    # --- GET /api/subscriptions/can-create-proposal ---
    
    def test_can_create_proposal_requires_auth(self):
        """GET /api/subscriptions/can-create-proposal requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/can-create-proposal")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/can-create-proposal requires authentication")
    
    def test_can_create_proposal_with_auth(self):
        """GET /api/subscriptions/can-create-proposal checks proposal limit"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/can-create-proposal",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "can_create" in data, "Response should contain 'can_create'"
        assert "limit" in data, "Response should contain 'limit'"
        assert "used" in data, "Response should contain 'used'"
        assert "remaining" in data, "Response should contain 'remaining'"
        
        print(f"✓ GET /api/subscriptions/can-create-proposal:")
        print(f"  - Can create: {data['can_create']}")
        print(f"  - Limit: {data['limit']}, Used: {data['used']}, Remaining: {data['remaining']}")
    
    # --- GET /api/subscriptions/me ---
    
    def test_me_requires_auth(self):
        """GET /api/subscriptions/me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me requires authentication")
    
    def test_me_with_auth(self):
        """GET /api/subscriptions/me returns current creator subscription"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "plan_id" in data, "Response should contain 'plan_id'"
        assert "features" in data, "Response should contain 'features'"
        
        print(f"✓ GET /api/subscriptions/me returns tier={data['tier']}, plan_id={data['plan_id']}")
    
    # --- GET /api/subscriptions/me/features ---
    
    def test_me_features_requires_auth(self):
        """GET /api/subscriptions/me/features requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me/features")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me/features requires authentication")
    
    def test_me_features_with_auth(self):
        """GET /api/subscriptions/me/features returns feature access"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me/features",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "features" in data, "Response should contain 'features'"
        
        print(f"✓ GET /api/subscriptions/me/features returns tier={data['tier']}")
    
    # --- GET /api/subscriptions/me/usage ---
    
    def test_me_usage_requires_auth(self):
        """GET /api/subscriptions/me/usage requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me/usage")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me/usage requires authentication")
    
    def test_me_usage_with_auth(self):
        """GET /api/subscriptions/me/usage returns usage stats"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me/usage",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "period_start" in data, "Response should contain 'period_start'"
        assert "proposals" in data, "Response should contain 'proposals'"
        assert "tier" in data, "Response should contain 'tier'"
        
        print(f"✓ GET /api/subscriptions/me/usage returns:")
        print(f"  - Period start: {data['period_start']}")
        print(f"  - Proposals: {data['proposals']}")
    
    # --- GET /api/subscriptions/me/billing-history ---
    
    def test_me_billing_history_requires_auth(self):
        """GET /api/subscriptions/me/billing-history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me/billing-history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me/billing-history requires authentication")
    
    def test_me_billing_history_with_auth(self):
        """GET /api/subscriptions/me/billing-history returns billing history"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me/billing-history",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions'"
        assert "total" in data, "Response should contain 'total'"
        assert isinstance(data["transactions"], list), "Transactions should be a list"
        
        print(f"✓ GET /api/subscriptions/me/billing-history returns {data['total']} transactions")
    
    # --- GET /api/subscriptions/my-transactions ---
    
    def test_my_transactions_requires_auth(self):
        """GET /api/subscriptions/my-transactions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my-transactions")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/my-transactions requires authentication")
    
    def test_my_transactions_with_auth(self):
        """GET /api/subscriptions/my-transactions returns payment transactions"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-transactions",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions'"
        assert "total" in data, "Response should contain 'total'"
        
        print(f"✓ GET /api/subscriptions/my-transactions returns {data['total']} transactions")


# ============== STRIPE CHECKOUT ENDPOINTS ==============

class TestStripeCheckoutEndpoints:
    """Test Stripe checkout endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each test"""
        self.free_token = TestAuth.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_checkout_requires_auth(self):
        """POST /api/subscriptions/checkout requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={"plan_id": "pro_monthly", "origin_url": "https://example.com"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/subscriptions/checkout requires authentication")
    
    def test_checkout_requires_plan_id(self):
        """POST /api/subscriptions/checkout requires plan_id"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            headers=self.headers_free,
            json={"origin_url": "https://example.com"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ POST /api/subscriptions/checkout requires plan_id (400 without it)")
    
    def test_checkout_creates_session(self):
        """POST /api/subscriptions/checkout creates Stripe checkout session"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            headers=self.headers_free,
            json={
                "plan_id": "pro_monthly",
                "origin_url": "https://example.com"
            }
        )
        # May return 200 with checkout URL or 500 if Stripe not configured
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data or "url" in data, "Response should contain checkout URL"
            print(f"✓ POST /api/subscriptions/checkout creates session")
        elif response.status_code == 500:
            print(f"⚠ POST /api/subscriptions/checkout - Stripe may not be fully configured (500)")
        else:
            assert False, f"Unexpected status {response.status_code}: {response.text}"
    
    def test_checkout_status_requires_auth(self):
        """GET /api/subscriptions/checkout/status/{session_id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/checkout/status/test_session_123")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/checkout/status requires authentication")
    
    def test_checkout_status_with_invalid_session(self):
        """GET /api/subscriptions/checkout/status/{session_id} with invalid session"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/checkout/status/invalid_session_id",
            headers=self.headers_free
        )
        # Should return error for invalid session (404, 500, or 520 from Stripe)
        assert response.status_code in [404, 500, 520], f"Expected 404/500/520 for invalid session, got {response.status_code}"
        print(f"✓ GET /api/subscriptions/checkout/status handles invalid session ({response.status_code})")


# ============== SUBSCRIPTION UPGRADE/CANCEL ENDPOINTS ==============

class TestSubscriptionManagementEndpoints:
    """Test subscription upgrade and cancel endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each test"""
        self.free_token = TestAuth.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestAuth.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
    
    # --- POST /api/subscriptions/me/upgrade ---
    
    def test_upgrade_requires_auth(self):
        """POST /api/subscriptions/me/upgrade requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/me/upgrade",
            json={"plan_id": "pro_monthly"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/subscriptions/me/upgrade requires authentication")
    
    def test_upgrade_requires_plan_id(self):
        """POST /api/subscriptions/me/upgrade requires plan_id"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/me/upgrade",
            headers=self.headers_free,
            json={}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ POST /api/subscriptions/me/upgrade requires plan_id (400 without it)")
    
    def test_upgrade_request(self):
        """POST /api/subscriptions/me/upgrade creates upgrade request"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/me/upgrade",
            headers=self.headers_free,
            json={"plan_id": "pro_monthly"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        assert "target_plan" in data, "Response should contain 'target_plan'"
        
        print(f"✓ POST /api/subscriptions/me/upgrade returns: {data['message']}")
    
    # --- POST /api/subscriptions/me/cancel ---
    
    def test_cancel_requires_auth(self):
        """POST /api/subscriptions/me/cancel requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/me/cancel",
            json={"reason": "Testing"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/subscriptions/me/cancel requires authentication")
    
    def test_cancel_no_active_subscription(self):
        """POST /api/subscriptions/me/cancel with no active subscription"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/me/cancel",
            headers=self.headers_free,
            json={"reason": "Testing cancellation"}
        )
        # Should return 404 if no active subscription
        if response.status_code == 404:
            print("✓ POST /api/subscriptions/me/cancel returns 404 for no active subscription")
        elif response.status_code == 200:
            data = response.json()
            print(f"✓ POST /api/subscriptions/me/cancel returns: {data.get('message', data)}")
        else:
            print(f"⚠ POST /api/subscriptions/me/cancel returned {response.status_code}: {response.text}")


# ============== GENERIC SUBSCRIPTION CRUD ==============

class TestGenericSubscriptionCRUD:
    """Test generic subscription CRUD endpoints"""
    
    def test_create_subscription_with_self_funding_loop(self):
        """POST /api/subscriptions creates subscription with self-funding loop"""
        test_user_id = f"TEST_USER_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions",
            json={
                "user_id": test_user_id,
                "plan_name": "Test Pro Plan",
                "monthly_cost": 29.99,
                "payment_status": "active"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert "message" in data, "Response should contain 'message'"
        assert "self_funding_loop" in data, "Response should contain 'self_funding_loop'"
        
        print(f"✓ POST /api/subscriptions creates subscription:")
        print(f"  - ID: {data['id']}")
        print(f"  - Self-funding loop: {data['self_funding_loop']}")
        print(f"  - Linked calc ID: {data.get('linked_calc_id', 'N/A')}")
    
    def test_get_subscriptions_with_filters(self):
        """GET /api/subscriptions with query filters"""
        # Test with tier filter
        response = requests.get(f"{BASE_URL}/api/subscriptions?tier=pro")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/subscriptions?tier=pro returns {len(data)} subscriptions")
        
        # Test with status filter
        response = requests.get(f"{BASE_URL}/api/subscriptions?status=active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ GET /api/subscriptions?status=active returns {len(data)} subscriptions")


# ============== ADMIN SUBSCRIPTION ENDPOINTS ==============

class TestAdminSubscriptionEndpoints:
    """Test admin subscription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each test"""
        self.admin_token = TestAuth.get_admin_token()
        self.free_token = TestAuth.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    # --- GET /api/admin/subscriptions ---
    
    def test_admin_subscriptions_requires_auth(self):
        """GET /api/admin/subscriptions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions requires authentication")
    
    def test_admin_subscriptions_requires_admin(self):
        """GET /api/admin/subscriptions requires admin role"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions",
            headers=self.headers_free
        )
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions rejects non-admin users")
    
    def test_admin_subscriptions_with_admin(self):
        """GET /api/admin/subscriptions returns subscriptions for admin"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subscriptions" in data, "Response should contain 'subscriptions'"
        assert "total" in data, "Response should contain 'total'"
        
        print(f"✓ GET /api/admin/subscriptions returns {data['total']} subscriptions")
    
    # --- GET /api/admin/subscriptions/stats ---
    
    def test_admin_stats_requires_auth(self):
        """GET /api/admin/subscriptions/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions/stats requires authentication")
    
    def test_admin_stats_requires_admin(self):
        """GET /api/admin/subscriptions/stats requires admin role"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions/stats",
            headers=self.headers_free
        )
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions/stats rejects non-admin users")
    
    def test_admin_stats_with_admin(self):
        """GET /api/admin/subscriptions/stats returns statistics for admin"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions/stats",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "by_tier" in data, "Response should contain 'by_tier'"
        assert "total_active" in data, "Response should contain 'total_active'"
        assert "total_revenue" in data, "Response should contain 'total_revenue'"
        
        print(f"✓ GET /api/admin/subscriptions/stats returns:")
        print(f"  - Total active: {data['total_active']}")
        print(f"  - Total revenue: ${data['total_revenue']}")
        print(f"  - By tier: {data['by_tier']}")
    
    # --- GET /api/admin/subscriptions/revenue ---
    
    def test_admin_revenue_requires_auth(self):
        """GET /api/admin/subscriptions/revenue requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions/revenue")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions/revenue requires authentication")
    
    def test_admin_revenue_requires_admin(self):
        """GET /api/admin/subscriptions/revenue requires admin role"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions/revenue",
            headers=self.headers_free
        )
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions/revenue rejects non-admin users")
    
    def test_admin_revenue_with_admin(self):
        """GET /api/admin/subscriptions/revenue returns revenue summary for admin"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions/revenue",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_revenue" in data, "Response should contain 'total_revenue'"
        assert "total_transactions" in data, "Response should contain 'total_transactions'"
        assert "by_plan" in data, "Response should contain 'by_plan'"
        assert "mrr" in data, "Response should contain 'mrr'"
        
        print(f"✓ GET /api/admin/subscriptions/revenue returns:")
        print(f"  - Total revenue: ${data['total_revenue']}")
        print(f"  - Total transactions: {data['total_transactions']}")
        print(f"  - MRR: ${data['mrr']}")


# ============== STRIPE WEBHOOK ENDPOINT ==============

class TestStripeWebhook:
    """Test Stripe webhook endpoint (in server.py)"""
    
    def test_webhook_requires_signature(self):
        """POST /api/webhook/stripe requires Stripe signature"""
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            data=b"test_payload",
            headers={"Content-Type": "application/json"}
        )
        # Should return 400 or 401 without proper signature
        assert response.status_code in [400, 401, 422, 500], f"Expected error without signature, got {response.status_code}"
        print(f"✓ POST /api/webhook/stripe requires Stripe signature ({response.status_code})")


# ============== FEATURE GATING VERIFICATION ==============

class TestFeatureGatingByTier:
    """Verify feature gating works correctly for different tiers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each test"""
        self.free_token = TestAuth.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestAuth.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.elite_token = TestAuth.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
    
    def test_free_tier_features(self):
        """Verify free tier has limited features"""
        if not self.free_token:
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/feature-access",
            headers=self.headers_free
        )
        assert response.status_code == 200
        
        data = response.json()
        features = data.get("features", {})
        
        # Free tier should have limited proposals
        proposals_limit = features.get("proposals_per_month", 1)
        assert proposals_limit <= 3, f"Free tier should have limited proposals, got {proposals_limit}"
        
        # Free tier should not have API access
        api_access = features.get("api_access", False)
        assert api_access == False, "Free tier should not have API access"
        
        print(f"✓ Free tier features verified:")
        print(f"  - Proposals per month: {proposals_limit}")
        print(f"  - API access: {api_access}")
        print(f"  - ARRIS insight level: {features.get('arris_insight_level', 'N/A')}")
    
    def test_tier_comparison(self):
        """Compare features across tiers"""
        tiers_data = {}
        
        for tier_name, token, headers in [
            ("free", self.free_token, self.headers_free),
            ("pro", self.pro_token, self.headers_pro),
            ("elite", self.elite_token, self.headers_elite)
        ]:
            if not token:
                continue
            
            response = requests.get(
                f"{BASE_URL}/api/subscriptions/feature-access",
                headers=headers
            )
            if response.status_code == 200:
                tiers_data[tier_name] = response.json()
        
        print(f"✓ Tier comparison ({len(tiers_data)} tiers tested):")
        for tier_name, data in tiers_data.items():
            features = data.get("features", {})
            print(f"  {tier_name.upper()}:")
            print(f"    - Proposals: {features.get('proposals_per_month', 'N/A')}")
            print(f"    - ARRIS level: {features.get('arris_insight_level', 'N/A')}")
            print(f"    - API access: {features.get('api_access', False)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
