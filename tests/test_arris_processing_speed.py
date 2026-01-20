"""
Test ARRIS Processing Speed Feature
Tests for Faster ARRIS Processing for Premium/Elite users

Features tested:
1. GET /api/arris/queue-stats - Queue lengths and processing statistics
2. GET /api/arris/my-processing-speed - Returns 'standard' for Free/Starter/Pro, 'fast' for Premium/Elite
3. feature_gating.get_arris_processing_speed() returns correct speed by tier
4. ARRIS insights include processing_time_seconds and priority_processed fields
5. Submit proposal as Premium user - verify fast processing flag in response
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PRO_USER = {"email": "protest@dashboard.com", "password": "propassword123"}
PREMIUM_USER = {"email": "premium@speedtest.com", "password": "premium123"}
FREE_USER = {"email": "testcreator@example.com", "password": "creator123"}
ADMIN_USER = {"email": "admin@hivehq.com", "password": "admin123"}


class TestARRISQueueStats:
    """Test ARRIS queue statistics endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
        
    def get_creator_token(self, email, password):
        """Get creator authentication token"""
        response = requests.post(
            f"{self.base_url}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": ADMIN_USER["email"], "password": ADMIN_USER["password"]}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_queue_stats_requires_auth(self):
        """Test that queue stats endpoint requires authentication"""
        response = requests.get(f"{self.base_url}/api/arris/queue-stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Queue stats requires authentication")
    
    def test_queue_stats_returns_data(self):
        """Test that queue stats returns proper structure"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        response = requests.get(
            f"{self.base_url}/api/arris/queue-stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify queue structure
        assert "queue" in data, "Response should contain 'queue' key"
        queue = data["queue"]
        assert "fast_queue" in queue, "Queue should have 'fast_queue'"
        assert "standard_queue" in queue, "Queue should have 'standard_queue'"
        assert "currently_processing" in queue, "Queue should have 'currently_processing'"
        
        # Verify processing_stats structure
        assert "processing_stats" in data, "Response should contain 'processing_stats'"
        stats = data["processing_stats"]
        assert "total_requests" in stats, "Stats should have 'total_requests'"
        assert "standard_requests" in stats, "Stats should have 'standard_requests'"
        assert "fast_requests" in stats, "Stats should have 'fast_requests'"
        assert "avg_processing_time" in stats, "Stats should have 'avg_processing_time'"
        
        print(f"✓ Queue stats returned: fast_queue={queue['fast_queue']}, standard_queue={queue['standard_queue']}")
        print(f"✓ Processing stats: total={stats['total_requests']}, fast={stats['fast_requests']}, standard={stats['standard_requests']}")


class TestMyProcessingSpeed:
    """Test my-processing-speed endpoint for different tiers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
        
    def get_creator_token(self, email, password):
        """Get creator authentication token"""
        response = requests.post(
            f"{self.base_url}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_processing_speed_requires_auth(self):
        """Test that processing speed endpoint requires authentication"""
        response = requests.get(f"{self.base_url}/api/arris/my-processing-speed")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Processing speed endpoint requires authentication")
    
    def test_pro_user_gets_standard_speed(self):
        """Test that Pro user gets 'standard' processing speed"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        response = requests.get(
            f"{self.base_url}/api/arris/my-processing-speed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "processing_speed" in data, "Response should contain 'processing_speed'"
        assert data["processing_speed"] == "standard", f"Pro user should have 'standard' speed, got '{data['processing_speed']}'"
        assert data.get("is_fast") == False, "Pro user should have is_fast=False"
        
        print(f"✓ Pro user ({PRO_USER['email']}) has processing_speed='standard'")
        print(f"  Tier: {data.get('tier')}, is_fast: {data.get('is_fast')}")
    
    def test_premium_user_gets_fast_speed(self):
        """Test that Premium user gets 'fast' processing speed"""
        token = self.get_creator_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Premium user - may need to create test user")
        
        response = requests.get(
            f"{self.base_url}/api/arris/my-processing-speed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "processing_speed" in data, "Response should contain 'processing_speed'"
        assert data["processing_speed"] == "fast", f"Premium user should have 'fast' speed, got '{data['processing_speed']}'"
        assert data.get("is_fast") == True, "Premium user should have is_fast=True"
        
        print(f"✓ Premium user ({PREMIUM_USER['email']}) has processing_speed='fast'")
        print(f"  Tier: {data.get('tier')}, is_fast: {data.get('is_fast')}")
    
    def test_free_user_gets_standard_speed(self):
        """Test that Free user gets 'standard' processing speed"""
        token = self.get_creator_token(FREE_USER["email"], FREE_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Free user")
        
        response = requests.get(
            f"{self.base_url}/api/arris/my-processing-speed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "processing_speed" in data, "Response should contain 'processing_speed'"
        assert data["processing_speed"] == "standard", f"Free user should have 'standard' speed, got '{data['processing_speed']}'"
        
        print(f"✓ Free user ({FREE_USER['email']}) has processing_speed='standard'")
    
    def test_processing_speed_response_structure(self):
        """Test that processing speed response has all expected fields"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        response = requests.get(
            f"{self.base_url}/api/arris/my-processing-speed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields
        expected_fields = ["processing_speed", "tier", "is_fast", "benefits", "message"]
        for field in expected_fields:
            assert field in data, f"Response should contain '{field}'"
        
        # Check benefits structure
        assert isinstance(data["benefits"], list), "Benefits should be a list"
        
        print(f"✓ Processing speed response has all expected fields: {expected_fields}")


class TestFeatureGatingProcessingSpeed:
    """Test feature gating for ARRIS processing speed"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
        
    def get_creator_token(self, email, password):
        """Get creator authentication token"""
        response = requests.post(
            f"{self.base_url}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_feature_access_includes_processing_speed(self):
        """Test that feature-access endpoint includes arris_processing_speed"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        response = requests.get(
            f"{self.base_url}/api/subscriptions/feature-access",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "features" in data, "Response should contain 'features'"
        features = data["features"]
        assert "arris_processing_speed" in features, "Features should include 'arris_processing_speed'"
        
        print(f"✓ Feature access includes arris_processing_speed: {features['arris_processing_speed']}")
    
    def test_pro_tier_has_standard_in_features(self):
        """Test that Pro tier has 'standard' processing speed in features"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        response = requests.get(
            f"{self.base_url}/api/subscriptions/feature-access",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        speed = data.get("features", {}).get("arris_processing_speed")
        assert speed == "standard", f"Pro tier should have 'standard' speed in features, got '{speed}'"
        
        print(f"✓ Pro tier feature-access shows arris_processing_speed='standard'")
    
    def test_premium_tier_has_fast_in_features(self):
        """Test that Premium tier has 'fast' processing speed in features"""
        token = self.get_creator_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Premium user")
        
        response = requests.get(
            f"{self.base_url}/api/subscriptions/feature-access",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        speed = data.get("features", {}).get("arris_processing_speed")
        assert speed == "fast", f"Premium tier should have 'fast' speed in features, got '{speed}'"
        
        print(f"✓ Premium tier feature-access shows arris_processing_speed='fast'")


class TestARRISInsightsProcessingFields:
    """Test that ARRIS insights include processing_time_seconds and priority_processed"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
        
    def get_creator_token(self, email, password):
        """Get creator authentication token"""
        response = requests.post(
            f"{self.base_url}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_submit_proposal_includes_processing_fields(self):
        """Test that submitting a proposal returns processing fields in ARRIS insights"""
        token = self.get_creator_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Pro user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a draft proposal
        proposal_data = {
            "title": f"TEST_ARRIS_Speed_Test_{int(time.time())}",
            "description": "Testing ARRIS processing speed fields in insights response",
            "goals": "Verify processing_time_seconds and priority_processed fields",
            "platforms": ["YouTube"],
            "timeline": "1_week",
            "priority": "medium"
        }
        
        create_response = requests.post(
            f"{self.base_url}/api/proposals",
            json=proposal_data,
            headers=headers
        )
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create proposal: {create_response.text}")
        
        proposal_id = create_response.json().get("id")
        print(f"  Created proposal: {proposal_id}")
        
        # Submit the proposal for ARRIS analysis
        submit_response = requests.post(
            f"{self.base_url}/api/proposals/{proposal_id}/submit",
            headers=headers
        )
        
        assert submit_response.status_code == 200, f"Expected 200, got {submit_response.status_code}: {submit_response.text}"
        data = submit_response.json()
        
        # Check ARRIS insights
        assert "arris_insights" in data, "Response should contain 'arris_insights'"
        insights = data["arris_insights"]
        
        # Verify processing fields exist
        assert "processing_time_seconds" in insights, "ARRIS insights should include 'processing_time_seconds'"
        assert "priority_processed" in insights, "ARRIS insights should include 'priority_processed'"
        
        # For Pro user, priority_processed should be False (standard processing)
        assert insights["priority_processed"] == False, f"Pro user should have priority_processed=False, got {insights['priority_processed']}"
        
        print(f"✓ ARRIS insights include processing fields:")
        print(f"  processing_time_seconds: {insights['processing_time_seconds']}")
        print(f"  priority_processed: {insights['priority_processed']}")
    
    def test_premium_user_proposal_has_priority_processed_true(self):
        """Test that Premium user's proposal has priority_processed=True"""
        token = self.get_creator_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Could not authenticate Premium user")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a draft proposal
        proposal_data = {
            "title": f"TEST_Premium_Speed_Test_{int(time.time())}",
            "description": "Testing Premium user fast ARRIS processing",
            "goals": "Verify priority_processed=True for Premium users",
            "platforms": ["Instagram"],
            "timeline": "2_weeks",
            "priority": "high"
        }
        
        create_response = requests.post(
            f"{self.base_url}/api/proposals",
            json=proposal_data,
            headers=headers
        )
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create proposal: {create_response.text}")
        
        proposal_id = create_response.json().get("id")
        print(f"  Created Premium proposal: {proposal_id}")
        
        # Submit the proposal for ARRIS analysis
        submit_response = requests.post(
            f"{self.base_url}/api/proposals/{proposal_id}/submit",
            headers=headers
        )
        
        assert submit_response.status_code == 200, f"Expected 200, got {submit_response.status_code}: {submit_response.text}"
        data = submit_response.json()
        
        # Check ARRIS insights
        assert "arris_insights" in data, "Response should contain 'arris_insights'"
        insights = data["arris_insights"]
        
        # For Premium user, priority_processed should be True (fast processing)
        assert insights.get("priority_processed") == True, f"Premium user should have priority_processed=True, got {insights.get('priority_processed')}"
        
        print(f"✓ Premium user ARRIS insights:")
        print(f"  processing_time_seconds: {insights.get('processing_time_seconds')}")
        print(f"  priority_processed: {insights.get('priority_processed')} (FAST)")


class TestSubscriptionPlansShowFastProcessing:
    """Test that subscription plans endpoint shows Fast ARRIS Processing for Premium/Elite"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.base_url = BASE_URL
    
    def test_plans_endpoint_returns_processing_speed(self):
        """Test that plans endpoint includes arris_processing_speed in features"""
        response = requests.get(f"{self.base_url}/api/subscriptions/plans")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "plans" in data, "Response should contain 'plans'"
        plans = data["plans"]
        
        # Check each plan for arris_processing_speed
        for plan in plans:
            features = plan.get("features", {})
            assert "arris_processing_speed" in features, f"Plan {plan['plan_id']} should have arris_processing_speed"
            
            # Verify correct speed for each tier
            tier = plan.get("tier", "")
            speed = features.get("arris_processing_speed")
            
            if tier in ["premium", "elite"]:
                assert speed == "fast", f"{tier} tier should have 'fast' speed, got '{speed}'"
                print(f"✓ {plan['name']} ({tier}): arris_processing_speed='fast'")
            else:
                assert speed == "standard", f"{tier} tier should have 'standard' speed, got '{speed}'"
                print(f"✓ {plan['name']} ({tier}): arris_processing_speed='standard'")
    
    def test_premium_plan_has_fast_processing_feature(self):
        """Test that Premium plan specifically shows fast processing"""
        response = requests.get(f"{self.base_url}/api/subscriptions/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find Premium monthly plan
        premium_plan = None
        for plan in data.get("plans", []):
            if plan.get("tier") == "premium":
                premium_plan = plan
                break
        
        assert premium_plan is not None, "Premium plan should exist"
        
        features = premium_plan.get("features", {})
        assert features.get("arris_processing_speed") == "fast", "Premium plan should have fast processing"
        
        print(f"✓ Premium plan features include arris_processing_speed='fast'")
    
    def test_elite_plan_has_fast_processing_feature(self):
        """Test that Elite plan shows fast processing"""
        response = requests.get(f"{self.base_url}/api/subscriptions/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        # Find Elite plan
        elite_plan = None
        for plan in data.get("plans", []):
            if plan.get("tier") == "elite":
                elite_plan = plan
                break
        
        assert elite_plan is not None, "Elite plan should exist"
        
        features = elite_plan.get("features", {})
        assert features.get("arris_processing_speed") == "fast", "Elite plan should have fast processing"
        
        print(f"✓ Elite plan features include arris_processing_speed='fast'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
