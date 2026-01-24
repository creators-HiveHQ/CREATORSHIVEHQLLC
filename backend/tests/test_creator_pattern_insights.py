"""
Test Creator Pattern Insights (Module A3)
=========================================
Tests for personalized pattern analysis for Pro+ creators.
Feature-gated: Pro, Premium, Elite have access; Free and Starter see access_denied.

Endpoints tested:
- GET /api/creators/me/pattern-insights
- GET /api/creators/me/pattern-recommendations
- GET /api/creators/me/pattern-trends
- GET /api/creators/me/pattern-detail/{pattern_id}
- POST /api/creators/me/pattern-feedback
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for each tier
TEST_CREDENTIALS = {
    "free": {"email": "freetest@hivehq.com", "password": "testpassword"},
    "starter": {"email": "startertest@hivehq.com", "password": "testpassword"},
    "pro": {"email": "protest@hivehq.com", "password": "testpassword"},
    "premium": {"email": "premiumtest@hivehq.com", "password": "testpassword"},
    "elite": {"email": "elitetest@hivehq.com", "password": "testpassword123"},
}


class TestCreatorPatternInsightsAccess:
    """Test feature gating - Pro+ have access, Free/Starter see access_denied"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup tokens for each tier"""
        self.tokens = {}
        for tier, creds in TEST_CREDENTIALS.items():
            response = requests.post(
                f"{BASE_URL}/api/creators/login",
                json=creds
            )
            if response.status_code == 200:
                self.tokens[tier] = response.json().get("access_token")
            else:
                print(f"Warning: Could not login {tier} user: {response.status_code}")
    
    def test_free_user_pattern_insights_access_denied(self):
        """Free tier should see access_denied=true"""
        if "free" not in self.tokens:
            pytest.skip("Free user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.tokens['free']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == True
        assert data.get("tier") == "free"
        assert "upgrade_message" in data
        assert data.get("patterns") == []
        print(f"✓ Free user sees access_denied=true, tier={data.get('tier')}")
    
    def test_starter_user_pattern_insights_access_denied(self):
        """Starter tier should see access_denied=true"""
        if "starter" not in self.tokens:
            pytest.skip("Starter user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.tokens['starter']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == True
        assert data.get("tier") == "starter"
        assert "upgrade_message" in data
        print(f"✓ Starter user sees access_denied=true, tier={data.get('tier')}")
    
    def test_pro_user_pattern_insights_has_access(self):
        """Pro tier should have access (access_denied=false)"""
        if "pro" not in self.tokens:
            pytest.skip("Pro user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.tokens['pro']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == False
        assert data.get("tier") == "pro"
        assert "patterns" in data
        assert "summary" in data
        print(f"✓ Pro user has access, tier={data.get('tier')}, patterns={len(data.get('patterns', []))}")
    
    def test_premium_user_pattern_insights_has_access(self):
        """Premium tier should have access"""
        if "premium" not in self.tokens:
            pytest.skip("Premium user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.tokens['premium']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == False
        assert data.get("tier") == "premium"
        print(f"✓ Premium user has access, tier={data.get('tier')}")
    
    def test_elite_user_pattern_insights_has_access(self):
        """Elite tier should have access"""
        if "elite" not in self.tokens:
            pytest.skip("Elite user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.tokens['elite']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == False
        assert data.get("tier") == "elite"
        print(f"✓ Elite user has access, tier={data.get('tier')}")


class TestPatternInsightsEndpoint:
    """Test GET /api/creators/me/pattern-insights endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Pro user token for testing"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Pro user")
    
    def test_pattern_insights_returns_correct_structure(self):
        """Pattern insights should return patterns, summary, tier, access_denied"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "patterns" in data
        assert "summary" in data
        assert "tier" in data
        assert "access_denied" in data
        
        # Patterns should be a list
        assert isinstance(data["patterns"], list)
        
        # Summary should have expected fields
        summary = data.get("summary", {})
        assert "total_patterns" in summary
        assert "high_confidence" in summary
        assert "categories" in summary
        assert "last_updated" in summary
        
        print(f"✓ Pattern insights structure valid: {len(data['patterns'])} patterns, summary has {len(summary)} fields")
    
    def test_pattern_insights_with_limit_parameter(self):
        """Test limit parameter works"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights?limit=5",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("patterns", [])) <= 5
        print(f"✓ Limit parameter works: returned {len(data.get('patterns', []))} patterns (limit=5)")
    
    def test_pattern_insights_requires_auth(self):
        """Pattern insights should require authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/pattern-insights")
        
        assert response.status_code in [401, 403]
        print("✓ Pattern insights requires authentication")


class TestPatternRecommendationsEndpoint:
    """Test GET /api/creators/me/pattern-recommendations endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Pro user token for testing"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Pro user")
    
    def test_recommendations_returns_correct_structure(self):
        """Recommendations should return recommendations list and access_denied"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-recommendations",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommendations" in data
        assert "access_denied" in data
        assert isinstance(data["recommendations"], list)
        
        print(f"✓ Recommendations structure valid: {len(data['recommendations'])} recommendations")
    
    def test_recommendations_access_denied_for_free_user(self):
        """Free user should see access_denied for recommendations"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["free"]
        )
        if response.status_code != 200:
            pytest.skip("Could not login Free user")
        
        free_token = response.json().get("access_token")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-recommendations",
            headers={"Authorization": f"Bearer {free_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == True
        print("✓ Free user sees access_denied for recommendations")


class TestPatternTrendsEndpoint:
    """Test GET /api/creators/me/pattern-trends endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Pro user token for testing"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Pro user")
    
    def test_trends_returns_correct_structure(self):
        """Trends should return trends dict and period_days"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-trends",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trends" in data
        assert "period_days" in data
        assert "access_denied" in data
        
        print(f"✓ Trends structure valid: period_days={data.get('period_days')}")
    
    def test_trends_with_days_parameter(self):
        """Test days parameter works"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-trends?days=60",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("period_days") == 60
        print("✓ Days parameter works: period_days=60")
    
    def test_trends_access_denied_for_starter_user(self):
        """Starter user should see access_denied for trends"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["starter"]
        )
        if response.status_code != 200:
            pytest.skip("Could not login Starter user")
        
        starter_token = response.json().get("access_token")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-trends",
            headers={"Authorization": f"Bearer {starter_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("access_denied") == True
        print("✓ Starter user sees access_denied for trends")


class TestPatternDetailEndpoint:
    """Test GET /api/creators/me/pattern-detail/{pattern_id} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Pro user token for testing"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Pro user")
    
    def test_pattern_detail_not_found(self):
        """Non-existent pattern should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-detail/PAT-NONEXISTENT",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 404
        print("✓ Non-existent pattern returns 404")
    
    def test_pattern_detail_requires_auth(self):
        """Pattern detail should require authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/pattern-detail/PAT-TEST")
        
        assert response.status_code in [401, 403]
        print("✓ Pattern detail requires authentication")


class TestPatternFeedbackEndpoint:
    """Test POST /api/creators/me/pattern-feedback endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Pro user token for testing"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["pro"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Pro user")
    
    def test_feedback_requires_pattern_id(self):
        """Feedback should require pattern_id"""
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-feedback",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"is_helpful": True}
        )
        
        assert response.status_code == 400
        assert "pattern_id" in response.json().get("detail", "").lower()
        print("✓ Feedback requires pattern_id")
    
    def test_feedback_submission_success(self):
        """Valid feedback should be saved successfully"""
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-feedback",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "pattern_id": "PAT-TEST-001",
                "is_helpful": True,
                "feedback_text": "This pattern was very helpful!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "feedback_id" in data
        print(f"✓ Feedback saved successfully: {data.get('feedback_id')}")
    
    def test_feedback_not_helpful(self):
        """Feedback with is_helpful=false should work"""
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-feedback",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "pattern_id": "PAT-TEST-002",
                "is_helpful": False,
                "feedback_text": "Not relevant to my situation"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Negative feedback saved successfully")
    
    def test_feedback_requires_auth(self):
        """Feedback should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-feedback",
            json={"pattern_id": "PAT-TEST", "is_helpful": True}
        )
        
        assert response.status_code in [401, 403]
        print("✓ Feedback requires authentication")


class TestPatternCategories:
    """Test that patterns have correct category structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get Elite user token (most likely to have patterns)"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=TEST_CREDENTIALS["elite"]
        )
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            pytest.skip("Could not login Elite user")
    
    def test_pattern_categories_are_valid(self):
        """Patterns should have valid categories"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-insights",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        valid_categories = ["success", "risk", "timing", "growth", "engagement", "platform", "content"]
        
        for pattern in data.get("patterns", []):
            category = pattern.get("category")
            if category:
                assert category in valid_categories, f"Invalid category: {category}"
        
        print(f"✓ All pattern categories are valid")


class TestAllTiersLogin:
    """Verify all test users can login successfully"""
    
    def test_all_tiers_can_login(self):
        """All test tier users should be able to login"""
        for tier, creds in TEST_CREDENTIALS.items():
            response = requests.post(
                f"{BASE_URL}/api/creators/login",
                json=creds
            )
            
            assert response.status_code == 200, f"{tier} user login failed: {response.status_code}"
            data = response.json()
            assert "access_token" in data
            assert "creator" in data
            print(f"✓ {tier.capitalize()} user login successful: {creds['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
