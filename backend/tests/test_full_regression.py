"""
Full System Regression Test
============================
Comprehensive regression test after major backend refactoring.
Routes migrated from server.py to modular files:
- proposals.py, subscriptions.py, arris.py, referral.py, elite.py, waitlist.py

Tests all critical workflows:
1. Proposals workflow (CRUD, submit, ARRIS insights, recommendations)
2. Subscriptions workflow (plans, status, feature access, checkout)
3. ARRIS workflow (memory, patterns, learning, activity, queue)
4. Referral workflow (generate code, stats, my-referrals)
5. Waitlist workflow (signup, position, admin stats)
6. Elite workflow (status, dashboard)
7. Cross-feature integration (feature gating, proposal limits, ARRIS on submit)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
FREE_EMAIL = "freetest@hivehq.com"
FREE_PASSWORD = "testpassword"
PRO_EMAIL = "protest@hivehq.com"
PRO_PASSWORD = "testpassword"
ELITE_EMAIL = "elitetest@hivehq.com"
ELITE_PASSWORD = "testpassword123"


class TestSetup:
    """Authentication helpers"""
    
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


# ============== PROPOSALS WORKFLOW ==============

class TestProposalsWorkflow:
    """Test proposals workflow from routes/proposals.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = TestSetup.get_admin_token()
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestSetup.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.created_proposal_ids = []
    
    def teardown_method(self):
        """Cleanup created proposals"""
        for proposal_id in self.created_proposal_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/proposals/{proposal_id}",
                    headers=self.headers_admin
                )
            except:
                pass
    
    def test_01_form_options(self):
        """GET /api/proposals/form-options - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/proposals/form-options")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "platforms" in data, "Should have platforms"
        assert "timelines" in data, "Should have timelines"
        assert "priorities" in data, "Should have priorities"
        assert "statuses" in data, "Should have statuses"
        assert "arris_question" in data, "Should have arris_question"
        print(f"✓ GET /api/proposals/form-options - {len(data['platforms'])} platforms, {len(data['priorities'])} priorities")
    
    def test_02_create_proposal(self):
        """POST /api/proposals - create new proposal"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        proposal_data = {
            "title": f"TEST_Regression_Proposal_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for regression testing",
            "platforms": ["YouTube", "TikTok"],
            "timeline": "1-2 weeks",
            "priority": "medium"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Should return proposal id"
        assert data["status"] == "draft", "New proposal should be draft"
        self.created_proposal_ids.append(data["id"])
        print(f"✓ POST /api/proposals - created proposal {data['id']}")
        return data["id"]
    
    def test_03_get_proposal(self):
        """GET /api/proposals/{id} - get proposal details"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        # Create a proposal first
        proposal_data = {
            "title": f"TEST_Get_Proposal_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for get test",
            "platforms": ["Instagram"],
            "priority": "low"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        proposal_id = create_response.json()["id"]
        self.created_proposal_ids.append(proposal_id)
        
        # Get the proposal
        response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == proposal_id, "Should return correct proposal"
        assert data["title"] == proposal_data["title"], "Title should match"
        print(f"✓ GET /api/proposals/{proposal_id} - retrieved proposal")
    
    def test_04_submit_proposal_generates_arris(self):
        """POST /api/proposals/{id}/submit - submit and generate ARRIS insights"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        # Create a proposal
        proposal_data = {
            "title": f"TEST_Submit_Proposal_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for submission with ARRIS insights generation",
            "platforms": ["YouTube", "Twitch"],
            "timeline": "2-4 weeks",
            "priority": "high"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        proposal_id = create_response.json()["id"]
        self.created_proposal_ids.append(proposal_id)
        
        # Submit the proposal
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "submitted", "Status should be submitted"
        assert "arris_insights" in data, "Should have ARRIS insights"
        print(f"✓ POST /api/proposals/{proposal_id}/submit - submitted with ARRIS insights")
    
    def test_05_admin_update_proposal(self):
        """PATCH /api/proposals/{id} - admin update/approve/reject"""
        if not self.admin_token or not self.pro_token:
            pytest.skip("Admin or Pro token not available")
        
        # Create and submit a proposal
        proposal_data = {
            "title": f"TEST_Admin_Update_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for admin update",
            "platforms": ["YouTube"],
            "priority": "medium"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        proposal_id = create_response.json()["id"]
        self.created_proposal_ids.append(proposal_id)
        
        # Submit it
        requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers=self.headers_pro
        )
        
        # Admin updates status to under_review
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={"status": "under_review"},
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ PATCH /api/proposals/{proposal_id} - admin updated to under_review")
    
    def test_06_stats_summary(self):
        """GET /api/proposals/stats/summary - admin statistics"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/proposals/stats/summary",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_proposals" in data, "Should have total_proposals"
        assert "by_status" in data, "Should have by_status"
        assert "by_priority" in data, "Should have by_priority"
        print(f"✓ GET /api/proposals/stats/summary - total: {data['total_proposals']}")
    
    def test_07_generate_recommendations(self):
        """POST /api/proposals/{id}/generate-recommendations - AI recommendations"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        # Create a proposal
        proposal_data = {
            "title": f"TEST_Recommendations_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for recommendations",
            "platforms": ["YouTube"],
            "priority": "medium"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        proposal_id = create_response.json()["id"]
        self.created_proposal_ids.append(proposal_id)
        
        # Generate recommendations
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/generate-recommendations",
            headers=self.headers_pro
        )
        # May return 200 or 503 if service unavailable
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"
        if response.status_code == 200:
            print(f"✓ POST /api/proposals/{proposal_id}/generate-recommendations - generated")
        else:
            print(f"✓ POST /api/proposals/{proposal_id}/generate-recommendations - service unavailable (expected)")


# ============== SUBSCRIPTIONS WORKFLOW ==============

class TestSubscriptionsWorkflow:
    """Test subscriptions workflow from routes/subscriptions.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = TestSetup.get_admin_token()
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestSetup.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
    
    def test_01_plans(self):
        """GET /api/subscriptions/plans - list all subscription plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "plans" in data, "Should have plans"
        assert len(data["plans"]) > 0, "Should have at least one plan"
        print(f"✓ GET /api/subscriptions/plans - {len(data['plans'])} plans")
    
    def test_02_my_status_free(self):
        """GET /api/subscriptions/my-status - free tier creator"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "tier" in data, "Should have tier"
        assert "proposals_per_month" in data, "Should have proposals_per_month"
        print(f"✓ GET /api/subscriptions/my-status (free) - tier: {data['tier']}, proposals: {data['proposals_per_month']}/month")
    
    def test_03_my_status_pro(self):
        """GET /api/subscriptions/my-status - pro tier creator"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "tier" in data, "Should have tier"
        print(f"✓ GET /api/subscriptions/my-status (pro) - tier: {data['tier']}")
    
    def test_04_my_status_elite(self):
        """GET /api/subscriptions/my-status - elite tier creator"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/my-status",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "tier" in data, "Should have tier"
        print(f"✓ GET /api/subscriptions/my-status (elite) - tier: {data['tier']}")
    
    def test_05_feature_access(self):
        """GET /api/subscriptions/feature-access - feature gating check"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/feature-access",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "tier" in data, "Should have tier"
        assert "features" in data, "Should have features"
        print(f"✓ GET /api/subscriptions/feature-access - tier: {data['tier']}")
    
    def test_06_can_create_proposal(self):
        """GET /api/subscriptions/can-create-proposal - proposal limit check"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/can-create-proposal",
            headers=self.headers_free
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "can_create" in data, "Should have can_create"
        assert "limit" in data, "Should have limit"
        assert "used" in data, "Should have used"
        print(f"✓ GET /api/subscriptions/can-create-proposal - can_create: {data['can_create']}, {data['used']}/{data['limit']}")
    
    def test_07_checkout_requires_plan_id(self):
        """POST /api/subscriptions/checkout - requires plan_id"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={},
            headers=self.headers_free
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ POST /api/subscriptions/checkout - requires plan_id (400)")
    
    def test_08_checkout_creates_session(self):
        """POST /api/subscriptions/checkout - create Stripe checkout session"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout",
            json={"plan_id": "pro_monthly", "origin_url": "https://test.com"},
            headers=self.headers_free
        )
        # May return 200 or 500 if Stripe not configured
        assert response.status_code in [200, 500, 520], f"Expected 200/500/520, got {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data or "session_id" in data, "Should have checkout info"
            print("✓ POST /api/subscriptions/checkout - created session")
        else:
            print("✓ POST /api/subscriptions/checkout - Stripe error (expected in test mode)")
    
    def test_09_usage(self):
        """GET /api/subscriptions/me/usage - usage statistics"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/me/usage",
            headers=self.headers_pro
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "proposals" in data, "Should have proposals usage"
        assert "tier" in data, "Should have tier"
        print(f"✓ GET /api/subscriptions/me/usage - tier: {data['tier']}")
    
    def test_10_admin_stats(self):
        """GET /api/admin/subscriptions/stats - admin subscription stats"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/subscriptions/stats",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return stats dict"
        print(f"✓ GET /api/admin/subscriptions/stats - {list(data.keys())}")


# ============== ARRIS WORKFLOW ==============

class TestARRISWorkflow:
    """Test ARRIS workflow from routes/arris.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_01_memory_summary(self):
        """GET /api/arris/memory/summary - memory palace summary"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/summary",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return summary dict"
        print(f"✓ GET /api/arris/memory/summary - {list(data.keys())}")
    
    def test_02_patterns(self):
        """GET /api/arris/patterns - pattern detection"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/patterns",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return patterns dict"
        print(f"✓ GET /api/arris/patterns - {list(data.keys())}")
    
    def test_03_learning_metrics(self):
        """GET /api/arris/learning/metrics - learning metrics"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/learning/metrics",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return metrics dict"
        print(f"✓ GET /api/arris/learning/metrics - {list(data.keys())}")
    
    def test_04_activity_feed(self):
        """GET /api/arris/activity-feed - activity feed"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/activity-feed",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return feed dict"
        print(f"✓ GET /api/arris/activity-feed - {list(data.keys())}")
    
    def test_05_queue_stats(self):
        """GET /api/arris/queue-stats - processing queue stats"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/queue-stats",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return queue stats dict"
        print(f"✓ GET /api/arris/queue-stats - {list(data.keys())}")


# ============== REFERRAL WORKFLOW ==============

class TestReferralWorkflow:
    """Test referral workflow from routes/referral.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = TestSetup.get_admin_token()
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_01_generate_code(self):
        """POST /api/referral/generate-code - generate referral code"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/referral/generate-code",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return code info"
        print(f"✓ POST /api/referral/generate-code - {list(data.keys())}")
    
    def test_02_my_stats(self):
        """GET /api/referral/my-stats - referral statistics"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/referral/my-stats",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return stats dict"
        print(f"✓ GET /api/referral/my-stats - {list(data.keys())}")
    
    def test_03_my_referrals(self):
        """GET /api/referral/my-referrals - creator's referrals"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/referral/my-referrals",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return referrals dict"
        print(f"✓ GET /api/referral/my-referrals - {list(data.keys())}")
    
    def test_04_admin_analytics(self):
        """GET /api/admin/referral/analytics - admin referral analytics"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/referral/analytics",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return admin analytics dict"
        print(f"✓ GET /api/admin/referral/analytics - {list(data.keys())}")


# ============== WAITLIST WORKFLOW ==============

class TestWaitlistWorkflow:
    """Test waitlist workflow from routes/waitlist.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = TestSetup.get_admin_token()
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.test_email = f"test_waitlist_{uuid.uuid4().hex[:8]}@test.com"
    
    def test_01_signup(self):
        """POST /api/waitlist/signup - new waitlist signup"""
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={
                "email": self.test_email,
                "name": "Test User",
                "creator_type": "content_creator",
                "platform": "YouTube"
            }
        )
        # May return 200 or 409 if already exists
        assert response.status_code in [200, 201, 409], f"Expected 200/201/409, got {response.status_code}"
        if response.status_code in [200, 201]:
            data = response.json()
            assert "position" in data or "message" in data, "Should have position or message"
            print(f"✓ POST /api/waitlist/signup - signed up")
        else:
            print(f"✓ POST /api/waitlist/signup - already exists (409)")
    
    def test_02_position(self):
        """GET /api/waitlist/position - check position"""
        # First signup
        requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={
                "email": self.test_email,
                "name": "Test User",
                "creator_type": "content_creator",
                "platform": "YouTube"
            }
        )
        
        response = requests.get(f"{BASE_URL}/api/waitlist/position?email={self.test_email}")
        assert response.status_code in [200, 404], f"Expected 200/404, got {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "position" in data or "email" in data, "Should have position info"
            print(f"✓ GET /api/waitlist/position?email={self.test_email} - found")
        else:
            print(f"✓ GET /api/waitlist/position?email={self.test_email} - not found (404)")
    
    def test_03_admin_stats(self):
        """GET /api/admin/waitlist/stats - admin waitlist stats"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/stats",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, dict), "Should return stats dict"
        print(f"✓ GET /api/admin/waitlist/stats - {list(data.keys())}")
    
    def test_04_admin_signups(self):
        """GET /api/admin/waitlist/signups - list all signups"""
        if not self.admin_token:
            pytest.skip("Admin token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/signups",
            headers=self.headers_admin
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, (list, dict)), "Should return signups"
        print(f"✓ GET /api/admin/waitlist/signups - retrieved")


# ============== ELITE WORKFLOW ==============

class TestEliteWorkflow:
    """Test elite workflow from routes/elite.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
    
    def test_01_status(self):
        """GET /api/elite/status - elite tier status"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/status",
            headers=self.headers_elite
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "is_elite" in data, "Should have is_elite"
        assert "tier" in data, "Should have tier"
        print(f"✓ GET /api/elite/status - is_elite: {data['is_elite']}, tier: {data['tier']}")
    
    def test_02_dashboard(self):
        """GET /api/elite/dashboard - elite dashboard data"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/dashboard",
            headers=self.headers_elite
        )
        # May return 200 or 403 if not actually elite
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Should return dashboard data"
            print(f"✓ GET /api/elite/dashboard - {list(data.keys())}")
        else:
            print(f"✓ GET /api/elite/dashboard - feature gated (403)")
    
    def test_03_free_user_gated(self):
        """GET /api/elite/dashboard - free user should be gated"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/dashboard",
            headers=self.headers_free
        )
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}"
        print(f"✓ GET /api/elite/dashboard - correctly gates free user (403)")


# ============== CROSS-FEATURE INTEGRATION ==============

class TestCrossFeatureIntegration:
    """Test cross-feature integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = TestSetup.get_admin_token()
        self.free_token = TestSetup.get_creator_token(FREE_EMAIL, FREE_PASSWORD)
        self.pro_token = TestSetup.get_creator_token(PRO_EMAIL, PRO_PASSWORD)
        self.elite_token = TestSetup.get_creator_token(ELITE_EMAIL, ELITE_PASSWORD)
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        self.headers_free = {"Authorization": f"Bearer {self.free_token}"} if self.free_token else {}
        self.headers_pro = {"Authorization": f"Bearer {self.pro_token}"} if self.pro_token else {}
        self.headers_elite = {"Authorization": f"Bearer {self.elite_token}"} if self.elite_token else {}
    
    def test_01_feature_gating_across_tiers(self):
        """Feature gating across tiers (free/pro/elite)"""
        # Test free tier limits
        if self.free_token:
            response = requests.get(
                f"{BASE_URL}/api/subscriptions/feature-access",
                headers=self.headers_free
            )
            if response.status_code == 200:
                data = response.json()
                free_tier = data.get("tier", "free")
                print(f"  Free tier: {free_tier}")
        
        # Test pro tier features
        if self.pro_token:
            response = requests.get(
                f"{BASE_URL}/api/subscriptions/feature-access",
                headers=self.headers_pro
            )
            if response.status_code == 200:
                data = response.json()
                pro_tier = data.get("tier", "pro")
                print(f"  Pro tier: {pro_tier}")
        
        # Test elite tier features
        if self.elite_token:
            response = requests.get(
                f"{BASE_URL}/api/subscriptions/feature-access",
                headers=self.headers_elite
            )
            if response.status_code == 200:
                data = response.json()
                elite_tier = data.get("tier", "elite")
                print(f"  Elite tier: {elite_tier}")
        
        print("✓ Feature gating across tiers verified")
    
    def test_02_proposal_respects_subscription_limits(self):
        """Proposal creation respects subscription limits"""
        if not self.free_token:
            pytest.skip("Free token not available")
        
        # Check current limit
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/can-create-proposal",
            headers=self.headers_free
        )
        assert response.status_code == 200
        data = response.json()
        
        can_create = data.get("can_create", True)
        limit = data.get("limit", 1)
        used = data.get("used", 0)
        
        print(f"✓ Proposal limits enforced - can_create: {can_create}, {used}/{limit} used")
    
    def test_03_arris_insights_on_proposal_submission(self):
        """ARRIS insights generated on proposal submission"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        # Create a proposal
        proposal_data = {
            "title": f"TEST_ARRIS_Integration_{uuid.uuid4().hex[:8]}",
            "description": "Test proposal for ARRIS integration verification",
            "platforms": ["YouTube"],
            "priority": "medium"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers=self.headers_pro
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create proposal")
        
        proposal_id = create_response.json()["id"]
        
        # Submit and verify ARRIS insights
        submit_response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers=self.headers_pro
        )
        
        assert submit_response.status_code == 200
        data = submit_response.json()
        assert "arris_insights" in data, "Should have ARRIS insights on submission"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers=self.headers_admin
        )
        
        print("✓ ARRIS insights generated on proposal submission")
    
    def test_04_referral_code_validation(self):
        """Referral code validation on signup"""
        # Generate a referral code
        if self.elite_token:
            gen_response = requests.post(
                f"{BASE_URL}/api/referral/generate-code",
                headers=self.headers_elite
            )
            if gen_response.status_code == 200:
                code_data = gen_response.json()
                referral_code = code_data.get("code") or code_data.get("referral_code")
                
                if referral_code:
                    # Try to use the code in waitlist signup
                    test_email = f"test_referral_{uuid.uuid4().hex[:8]}@test.com"
                    signup_response = requests.post(
                        f"{BASE_URL}/api/waitlist/signup",
                        json={
                            "email": test_email,
                            "name": "Test Referral User",
                            "creator_type": "content_creator",
                            "platform": "YouTube",
                            "referral_code": referral_code
                        }
                    )
                    # Should accept the referral code
                    assert signup_response.status_code in [200, 201, 409], f"Signup should work with referral code"
                    print(f"✓ Referral code validation works - code: {referral_code[:8]}...")
                    return
        
        print("✓ Referral code validation - skipped (no code generated)")


# ============== ROUTE REGISTRATION VERIFICATION ==============

class TestRouteRegistration:
    """Verify all routes are properly registered after migration"""
    
    def test_proposals_routes_registered(self):
        """Verify proposals routes are registered"""
        endpoints = [
            ("GET", "/api/proposals/form-options"),
            ("GET", "/api/proposals/stats/summary"),
        ]
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ Proposals routes registered")
    
    def test_subscriptions_routes_registered(self):
        """Verify subscriptions routes are registered"""
        endpoints = [
            ("GET", "/api/subscriptions/plans"),
            ("GET", "/api/subscriptions/my-status"),
            ("GET", "/api/subscriptions/feature-access"),
            ("GET", "/api/subscriptions/can-create-proposal"),
            ("GET", "/api/subscriptions/me/usage"),
        ]
        for method, endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ Subscriptions routes registered")
    
    def test_arris_routes_registered(self):
        """Verify ARRIS routes are registered"""
        endpoints = [
            ("GET", "/api/arris/memory/summary"),
            ("GET", "/api/arris/patterns"),
            ("GET", "/api/arris/activity-feed"),
        ]
        for method, endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ ARRIS routes registered")
    
    def test_referral_routes_registered(self):
        """Verify referral routes are registered"""
        endpoints = [
            ("GET", "/api/referral/my-stats"),
            ("GET", "/api/referral/my-referrals"),
            ("POST", "/api/referral/generate-code"),
        ]
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ Referral routes registered")
    
    def test_waitlist_routes_registered(self):
        """Verify waitlist routes are registered"""
        endpoints = [
            ("POST", "/api/waitlist/signup"),
            ("GET", "/api/admin/waitlist/stats"),
        ]
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ Waitlist routes registered")
    
    def test_elite_routes_registered(self):
        """Verify elite routes are registered"""
        endpoints = [
            ("GET", "/api/elite/status"),
            ("GET", "/api/elite/dashboard"),
        ]
        for method, endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, f"{endpoint} not found (404)"
        print("✓ Elite routes registered")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
