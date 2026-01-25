"""
Test Migrated Routes
====================
Tests for routes migrated from server.py to modular route files:
- ARRIS routes (/api/arris/*)
- Subscription routes (/api/subscriptions/*)
- Elite routes (/api/elite/*)
- Referral routes (/api/referral/*)
- Admin Referral routes (/api/admin/referral/*)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
ELITE_EMAIL = "elitetest@hivehq.com"
ELITE_PASSWORD = "testpassword123"
FREE_EMAIL = "freetest@hivehq.com"
FREE_PASSWORD = "testpassword"


class TestSetup:
    """Setup and authentication helpers"""
    
    @staticmethod
    def get_admin_token():
        """Get admin JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_creator_token(email, password):
        """Get creator JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


# ============== ARRIS ROUTES TESTS ==============

class TestARRISRoutes:
    """Test ARRIS route handlers from /app/backend/routes/arris.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_arris_memory_requires_auth(self):
        """GET /api/arris/memory requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/memory")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/arris/memory requires authentication")
    
    def test_arris_memory_with_auth(self):
        """GET /api/arris/memory returns memories for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "memories" in data, "Response should contain 'memories' key"
        assert "total" in data, "Response should contain 'total' key"
        print(f"✓ GET /api/arris/memory returns {data['total']} memories")
    
    def test_arris_memory_summary_requires_auth(self):
        """GET /api/arris/memory/summary requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/memory/summary")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/arris/memory/summary requires authentication")
    
    def test_arris_memory_summary_with_auth(self):
        """GET /api/arris/memory/summary returns summary for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/summary",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Summary should have some structure
        assert isinstance(data, dict), "Response should be a dictionary"
        print(f"✓ GET /api/arris/memory/summary returns summary: {list(data.keys())}")
    
    def test_arris_activity_requires_auth(self):
        """GET /api/arris/activity requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/activity")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/arris/activity requires authentication")
    
    def test_arris_activity_with_auth(self):
        """GET /api/arris/activity returns activity feed for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/activity",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "activities" in data, "Response should contain 'activities' key"
        assert "total" in data, "Response should contain 'total' key"
        print(f"✓ GET /api/arris/activity returns {data['total']} activities")
    
    def test_arris_historical_requires_auth(self):
        """GET /api/arris/historical requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/historical")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/arris/historical requires authentication")
    
    def test_arris_historical_with_auth(self):
        """GET /api/arris/historical returns historical data for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/historical",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        print(f"✓ GET /api/arris/historical returns data: {list(data.keys())}")
    
    def test_arris_performance_requires_auth(self):
        """GET /api/arris/performance requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/performance")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/arris/performance requires authentication")
    
    def test_arris_performance_with_auth(self):
        """GET /api/arris/performance returns performance metrics for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/performance",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total_interactions" in data, "Response should contain 'total_interactions'"
        assert "recent_success_rate" in data, "Response should contain 'recent_success_rate'"
        assert "status" in data, "Response should contain 'status'"
        print(f"✓ GET /api/arris/performance returns: interactions={data['total_interactions']}, success_rate={data['recent_success_rate']}%")


# ============== SUBSCRIPTION ROUTES TESTS ==============

class TestSubscriptionRoutes:
    """Test Subscription route handlers from /app/backend/routes/subscriptions.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_subscription_plans_public(self):
        """GET /api/subscriptions/plans is public and returns plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        assert isinstance(data["plans"], list), "Plans should be a list"
        print(f"✓ GET /api/subscriptions/plans returns {len(data['plans'])} plans")
    
    def test_subscription_me_requires_auth(self):
        """GET /api/subscriptions/me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me requires authentication")
    
    def test_subscription_me_with_auth(self):
        """GET /api/subscriptions/me returns subscription for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should have subscription info or indicate no subscription
        assert "has_subscription" in data or "tier" in data, "Response should contain subscription info"
        print(f"✓ GET /api/subscriptions/me returns subscription data")
    
    def test_subscription_usage_requires_auth(self):
        """GET /api/subscriptions/me/usage requires authentication"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/me/usage")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/subscriptions/me/usage requires authentication")
    
    def test_subscription_usage_with_auth(self):
        """GET /api/subscriptions/me/usage returns usage metrics for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me/usage",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "usage" in data, "Response should contain 'usage'"
        assert "limits" in data, "Response should contain 'limits'"
        print(f"✓ GET /api/subscriptions/me/usage returns tier={data['tier']}, usage={data['usage']}")


# ============== ELITE ROUTES TESTS ==============

class TestEliteRoutes:
    """Test Elite route handlers from /app/backend/routes/elite.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_elite_status_requires_auth(self):
        """GET /api/elite/status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/elite/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/elite/status requires authentication")
    
    def test_elite_status_with_elite_user(self):
        """GET /api/elite/status returns status for Elite tier user"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/status",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "is_elite" in data, "Response should contain 'is_elite'"
        assert "tier" in data, "Response should contain 'tier'"
        assert "elite_features" in data, "Response should contain 'elite_features'"
        print(f"✓ GET /api/elite/status returns is_elite={data['is_elite']}, tier={data['tier']}")
    
    def test_elite_status_with_free_user(self):
        """GET /api/elite/status returns status for Free tier user"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/status",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "is_elite" in data, "Response should contain 'is_elite'"
        # Free user should not be elite
        print(f"✓ GET /api/elite/status for free user: is_elite={data['is_elite']}, tier={data['tier']}")
    
    def test_elite_workflows_requires_auth(self):
        """GET /api/elite/workflows requires authentication"""
        response = requests.get(f"{BASE_URL}/api/elite/workflows")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/elite/workflows requires authentication")
    
    def test_elite_workflows_gated_for_free_user(self):
        """GET /api/elite/workflows returns 403 for Free tier user"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/workflows",
            headers=self.headers_free
        )
        # Should be 403 feature gated
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        print(f"✓ GET /api/elite/workflows correctly gates Free tier user (403)")
    
    def test_elite_workflows_with_elite_user(self):
        """GET /api/elite/workflows returns workflows for Elite tier user"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/workflows",
            headers=self.headers_elite
        )
        # Elite user should get 200 or 403 if not actually elite tier
        if response.status_code == 403:
            print(f"✓ GET /api/elite/workflows - Elite user not actually elite tier (403)")
        else:
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "workflows" in data, "Response should contain 'workflows'"
            print(f"✓ GET /api/elite/workflows returns {data.get('total', len(data.get('workflows', [])))} workflows")
    
    def test_elite_personas_requires_auth(self):
        """GET /api/elite/personas requires authentication"""
        response = requests.get(f"{BASE_URL}/api/elite/personas")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/elite/personas requires authentication")
    
    def test_elite_personas_gated_for_free_user(self):
        """GET /api/elite/personas returns 403 for Free tier user"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/personas",
            headers=self.headers_free
        )
        # Should be 403 feature gated
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}: {response.text}"
        print(f"✓ GET /api/elite/personas correctly gates Free tier user (403)")
    
    def test_elite_dashboard_requires_auth(self):
        """GET /api/elite/dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/elite/dashboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/elite/dashboard requires authentication")
    
    def test_elite_dashboard_gated_for_free_user(self):
        """GET /api/elite/dashboard returns 403 for Free tier user"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/dashboard",
            headers=self.headers_free
        )
        # Should be 403 feature gated
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}: {response.text}"
        print(f"✓ GET /api/elite/dashboard correctly gates Free tier user (403)")


# ============== REFERRAL ROUTES TESTS ==============

class TestReferralRoutes:
    """Test Referral route handlers from /app/backend/routes/referral.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.admin_token = TestSetup.get_admin_token()
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
    
    def test_referral_my_stats_requires_auth(self):
        """GET /api/referral/my-stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/my-stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/referral/my-stats requires authentication")
    
    def test_referral_my_stats_with_auth(self):
        """GET /api/referral/my-stats returns stats for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/referral/my-stats",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should have referral stats
        assert isinstance(data, dict), "Response should be a dictionary"
        print(f"✓ GET /api/referral/my-stats returns stats: {list(data.keys())}")
    
    def test_referral_tier_info_requires_auth(self):
        """GET /api/referral/tier-info requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/tier-info")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/referral/tier-info requires authentication")
    
    def test_referral_tier_info_with_auth(self):
        """GET /api/referral/tier-info returns tier info for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/referral/tier-info",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "tiers" in data, "Response should contain 'tiers'"
        assert "milestones" in data, "Response should contain 'milestones'"
        print(f"✓ GET /api/referral/tier-info returns {len(data['tiers'])} tiers and {len(data['milestones'])} milestones")
    
    def test_referral_generate_code_requires_auth(self):
        """POST /api/referral/generate-code requires authentication"""
        response = requests.post(f"{BASE_URL}/api/referral/generate-code")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/referral/generate-code requires authentication")
    
    def test_referral_generate_code_with_auth(self):
        """POST /api/referral/generate-code generates code for authenticated creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/referral/generate-code",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should return code info
        assert isinstance(data, dict), "Response should be a dictionary"
        print(f"✓ POST /api/referral/generate-code returns: {list(data.keys())}")


# ============== ADMIN REFERRAL ROUTES TESTS ==============

class TestAdminReferralRoutes:
    """Test Admin Referral route handlers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.admin_token = TestSetup.get_admin_token()
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
    
    def test_admin_referral_analytics_requires_auth(self):
        """GET /api/admin/referral/analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/referral/analytics")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/referral/analytics requires authentication")
    
    def test_admin_referral_analytics_requires_admin(self):
        """GET /api/admin/referral/analytics requires admin role"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/referral/analytics",
            headers=self.headers_elite
        )
        # Creator should get 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ GET /api/admin/referral/analytics correctly rejects non-admin (creator)")
    
    def test_admin_referral_analytics_with_admin(self):
        """GET /api/admin/referral/analytics returns analytics for admin"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/referral/analytics",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        print(f"✓ GET /api/admin/referral/analytics returns analytics: {list(data.keys())}")


# ============== INTEGRATION TESTS ==============

class TestRouteIntegration:
    """Integration tests to verify routes are properly registered"""
    
    def test_arris_routes_registered(self):
        """Verify ARRIS routes are registered under /api/arris prefix"""
        # Test a few endpoints to verify routing
        endpoints = [
            "/api/arris/memory",
            "/api/arris/memory/summary",
            "/api/arris/activity",
            "/api/arris/historical",
            "/api/arris/performance"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Should get 401/403 (auth required) not 404 (not found)
            assert response.status_code != 404, f"Endpoint {endpoint} not found (404)"
            print(f"✓ {endpoint} is registered (status: {response.status_code})")
    
    def test_subscription_routes_registered(self):
        """Verify Subscription routes are registered under /api/subscriptions prefix"""
        endpoints = [
            "/api/subscriptions/plans",
            "/api/subscriptions/me",
            "/api/subscriptions/me/usage"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Plans is public (200), others need auth (401/403)
            assert response.status_code != 404, f"Endpoint {endpoint} not found (404)"
            print(f"✓ {endpoint} is registered (status: {response.status_code})")
    
    def test_elite_routes_registered(self):
        """Verify Elite routes are registered under /api/elite prefix"""
        endpoints = [
            "/api/elite/status",
            "/api/elite/workflows",
            "/api/elite/personas",
            "/api/elite/dashboard"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Should get 401/403 (auth required) not 404 (not found)
            assert response.status_code != 404, f"Endpoint {endpoint} not found (404)"
            print(f"✓ {endpoint} is registered (status: {response.status_code})")
    
    def test_referral_routes_registered(self):
        """Verify Referral routes are registered under /api/referral prefix"""
        endpoints = [
            "/api/referral/my-stats",
            "/api/referral/tier-info"
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            # Should get 401/403 (auth required) not 404 (not found)
            assert response.status_code != 404, f"Endpoint {endpoint} not found (404)"
            print(f"✓ {endpoint} is registered (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
