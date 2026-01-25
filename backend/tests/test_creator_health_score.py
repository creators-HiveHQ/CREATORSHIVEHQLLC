"""
Test Creator Health Score (Module B4)
=====================================
Tests for the Creator Health Score feature which provides:
- Overall health score (0-100) for Pro+ creators
- 5 component scores (engagement, proposal_success, consistency, arris_utilization, profile_completeness)
- Status levels (excellent/good/fair/needs_attention/critical)
- Achievements and recommendations
- Historical trend tracking
- Leaderboard with masked names
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
FREE_CREATOR = {"email": "freetest@hivehq.com", "password": "testpassword"}
PRO_CREATOR = {"email": "protest@hivehq.com", "password": "testpassword"}
ELITE_CREATOR = {"email": "elitetest@hivehq.com", "password": "testpassword123"}


class TestCreatorHealthScoreAuth:
    """Test authentication and feature gating for health score endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_creator_token(self, email, password):
        """Helper to get creator auth token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_health_score_requires_auth(self):
        """Health score endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Health score endpoint requires authentication")
    
    def test_health_history_requires_auth(self):
        """Health history endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Health history endpoint requires authentication")
    
    def test_component_details_requires_auth(self):
        """Component details endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/engagement")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Component details endpoint requires authentication")
    
    def test_leaderboard_requires_auth(self):
        """Leaderboard endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/creators/health-leaderboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Leaderboard endpoint requires authentication")


class TestFreeCreatorHealthScore:
    """Test health score access for Free tier creators (should be denied)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as free creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=FREE_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Could not login as free creator: {response.status_code}")
    
    def test_free_creator_health_score_access_denied(self):
        """Free tier creator should get access_denied=true for health score"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("access_denied") == True, "Expected access_denied=true for free creator"
        assert "upgrade_message" in data, "Expected upgrade_message in response"
        assert data.get("tier") in ["free", "starter"], f"Expected free/starter tier, got {data.get('tier')}"
        print(f"✅ Free creator gets access_denied=true, tier={data.get('tier')}")
        print(f"   Upgrade message: {data.get('upgrade_message')}")
    
    def test_free_creator_health_history_access_denied(self):
        """Free tier creator should get access_denied=true for health history"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("access_denied") == True, "Expected access_denied=true for free creator"
        print("✅ Free creator gets access_denied=true for health history")
    
    def test_free_creator_component_details_access_denied(self):
        """Free tier creator should get access_denied=true for component details"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/engagement")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("access_denied") == True, "Expected access_denied=true for free creator"
        print("✅ Free creator gets access_denied=true for component details")


class TestProCreatorHealthScore:
    """Test health score access for Pro tier creators (should have full access)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as pro creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Could not login as pro creator: {response.status_code}")
    
    def test_pro_creator_health_score_access(self):
        """Pro tier creator should have access to health score"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("access_denied") == False, "Expected access_denied=false for pro creator"
        print(f"✅ Pro creator has access to health score, tier={data.get('tier')}")
    
    def test_pro_creator_health_score_structure(self):
        """Pro creator health score should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "overall_score" in data, "Missing overall_score"
        assert "status" in data, "Missing status"
        assert "components" in data, "Missing components"
        assert "trend" in data, "Missing trend"
        assert "achievements" in data, "Missing achievements"
        assert "recommendations" in data, "Missing recommendations"
        assert "calculated_at" in data, "Missing calculated_at"
        
        print(f"✅ Health score structure is correct")
        print(f"   Overall score: {data.get('overall_score')}")
        print(f"   Status: {data.get('status', {}).get('name')}")
    
    def test_pro_creator_overall_score_range(self):
        """Overall score should be between 0 and 100"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        score = data.get("overall_score")
        
        assert isinstance(score, int), f"Score should be int, got {type(score)}"
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
        print(f"✅ Overall score is valid: {score}")
    
    def test_pro_creator_status_levels(self):
        """Status should be one of the valid levels"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        status = data.get("status", {})
        
        valid_statuses = ["excellent", "good", "fair", "needs_attention", "critical"]
        assert status.get("name") in valid_statuses, f"Invalid status: {status.get('name')}"
        assert "label" in status, "Missing status label"
        assert "color" in status, "Missing status color"
        assert "emoji" in status, "Missing status emoji"
        
        print(f"✅ Status is valid: {status.get('name')} ({status.get('label')})")
    
    def test_pro_creator_five_components(self):
        """Health score should have 5 components with correct weights"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        components = data.get("components", {})
        
        expected_components = [
            "engagement",
            "proposal_success",
            "consistency",
            "arris_utilization",
            "profile_completeness"
        ]
        
        for comp in expected_components:
            assert comp in components, f"Missing component: {comp}"
            comp_data = components[comp]
            assert "score" in comp_data, f"Missing score for {comp}"
            assert "weight" in comp_data, f"Missing weight for {comp}"
            assert "label" in comp_data, f"Missing label for {comp}"
            assert "metrics" in comp_data, f"Missing metrics for {comp}"
            
            # Verify score is 0-100
            assert 0 <= comp_data["score"] <= 100, f"Invalid score for {comp}: {comp_data['score']}"
            
            print(f"   {comp}: score={comp_data['score']}, weight={comp_data['weight']}%")
        
        # Verify weights sum to 100
        total_weight = sum(components[c]["weight"] for c in expected_components)
        assert total_weight == 100, f"Weights should sum to 100, got {total_weight}"
        
        print(f"✅ All 5 components present with correct weights (total: {total_weight}%)")
    
    def test_pro_creator_component_scores_valid(self):
        """Each component score should be between 0 and 100"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        components = data.get("components", {})
        
        for name, comp in components.items():
            score = comp.get("score")
            assert isinstance(score, int), f"{name} score should be int"
            assert 0 <= score <= 100, f"{name} score should be 0-100, got {score}"
        
        print("✅ All component scores are valid (0-100)")
    
    def test_pro_creator_achievements_structure(self):
        """Achievements should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        achievements = data.get("achievements", [])
        
        assert isinstance(achievements, list), "Achievements should be a list"
        
        for achievement in achievements:
            assert "label" in achievement, "Achievement missing label"
            assert "description" in achievement, "Achievement missing description"
            assert "icon" in achievement, "Achievement missing icon"
            assert "earned" in achievement, "Achievement missing earned flag"
        
        print(f"✅ Achievements structure is correct ({len(achievements)} earned)")
    
    def test_pro_creator_recommendations_structure(self):
        """Recommendations should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data.get("recommendations", [])
        
        assert isinstance(recommendations, list), "Recommendations should be a list"
        
        for rec in recommendations:
            assert "component" in rec, "Recommendation missing component"
            assert "title" in rec, "Recommendation missing title"
            assert "action" in rec, "Recommendation missing action"
            assert "impact" in rec, "Recommendation missing impact"
            assert rec["impact"] in ["high", "medium", "low"], f"Invalid impact: {rec['impact']}"
        
        print(f"✅ Recommendations structure is correct ({len(recommendations)} recommendations)")
    
    def test_pro_creator_trend_structure(self):
        """Trend should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        trend = data.get("trend", {})
        
        assert "direction" in trend, "Trend missing direction"
        assert trend["direction"] in ["up", "down", "stable"], f"Invalid direction: {trend['direction']}"
        assert "change" in trend, "Trend missing change"
        
        print(f"✅ Trend structure is correct: {trend['direction']} ({trend['change']})")


class TestHealthScoreHistory:
    """Test health score history endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as pro creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Could not login as pro creator: {response.status_code}")
    
    def test_health_history_default(self):
        """Health history should return data for default 30 days"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("access_denied") == False, "Expected access for pro creator"
        assert "history" in data, "Missing history field"
        assert "days" in data, "Missing days field"
        assert data["days"] == 30, f"Expected 30 days, got {data['days']}"
        
        print(f"✅ Health history returns data for 30 days ({len(data['history'])} records)")
    
    def test_health_history_custom_days(self):
        """Health history should accept custom days parameter"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/history?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert data["days"] == 7, f"Expected 7 days, got {data['days']}"
        
        print(f"✅ Health history accepts custom days parameter")
    
    def test_health_history_max_days(self):
        """Health history should cap at 90 days"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/history?days=100")
        # Should either cap at 90 or return validation error
        assert response.status_code in [200, 422], f"Expected 200 or 422, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data["days"] <= 90, f"Days should be capped at 90, got {data['days']}"
        
        print("✅ Health history respects max days limit")


class TestHealthScoreComponents:
    """Test health score component details endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as pro creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Could not login as pro creator: {response.status_code}")
    
    def test_engagement_component_details(self):
        """Engagement component should return detailed breakdown"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/engagement")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("access_denied") == False
        assert data.get("component") == "engagement"
        assert "label" in data
        assert "description" in data
        assert "weight" in data
        assert "details" in data
        
        print(f"✅ Engagement component details: weight={data['weight']}%")
    
    def test_proposal_success_component_details(self):
        """Proposal success component should return detailed breakdown"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/proposal_success")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("component") == "proposal_success"
        assert data.get("weight") == 25
        
        print(f"✅ Proposal success component details: weight={data['weight']}%")
    
    def test_consistency_component_details(self):
        """Consistency component should return detailed breakdown"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/consistency")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("component") == "consistency"
        assert data.get("weight") == 20
        
        print(f"✅ Consistency component details: weight={data['weight']}%")
    
    def test_arris_utilization_component_details(self):
        """ARRIS utilization component should return detailed breakdown"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/arris_utilization")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("component") == "arris_utilization"
        assert data.get("weight") == 15
        
        print(f"✅ ARRIS utilization component details: weight={data['weight']}%")
    
    def test_profile_completeness_component_details(self):
        """Profile completeness component should return detailed breakdown"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/profile_completeness")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("component") == "profile_completeness"
        assert data.get("weight") == 15
        
        print(f"✅ Profile completeness component details: weight={data['weight']}%")
    
    def test_invalid_component_returns_error(self):
        """Invalid component should return error"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score/component/invalid_component")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✅ Invalid component returns 400 error")


class TestHealthLeaderboard:
    """Test health score leaderboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as pro creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Could not login as pro creator: {response.status_code}")
    
    def test_leaderboard_returns_data(self):
        """Leaderboard should return top creators"""
        response = self.session.get(f"{BASE_URL}/api/creators/health-leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "leaderboard" in data, "Missing leaderboard field"
        assert "date" in data, "Missing date field"
        
        print(f"✅ Leaderboard returns data ({len(data['leaderboard'])} entries)")
    
    def test_leaderboard_names_masked(self):
        """Leaderboard names should be partially masked for privacy"""
        response = self.session.get(f"{BASE_URL}/api/creators/health-leaderboard")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data.get("leaderboard", [])
        
        for entry in leaderboard:
            name = entry.get("name", "")
            # Names should contain *** for masking
            assert "***" in name, f"Name should be masked: {name}"
            assert "rank" in entry, "Missing rank"
            assert "score" in entry, "Missing score"
            assert "status" in entry, "Missing status"
        
        print("✅ Leaderboard names are properly masked")
    
    def test_leaderboard_limit_parameter(self):
        """Leaderboard should respect limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/creators/health-leaderboard?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        leaderboard = data.get("leaderboard", [])
        assert len(leaderboard) <= 5, f"Expected max 5 entries, got {len(leaderboard)}"
        
        print(f"✅ Leaderboard respects limit parameter ({len(leaderboard)} entries)")


class TestEliteCreatorHealthScore:
    """Test health score access for Elite tier creators"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as elite creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=ELITE_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Could not login as elite creator: {response.status_code}")
    
    def test_elite_creator_health_score_access(self):
        """Elite tier creator should have access to health score"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("access_denied") == False, "Expected access for elite creator"
        assert data.get("tier") == "elite", f"Expected elite tier, got {data.get('tier')}"
        
        print(f"✅ Elite creator has access to health score")
        print(f"   Overall score: {data.get('overall_score')}")
        print(f"   Status: {data.get('status', {}).get('name')}")


class TestStatusThresholds:
    """Test that status levels are assigned correctly based on score thresholds"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as pro creator
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Could not login as pro creator: {response.status_code}")
    
    def test_status_matches_score(self):
        """Status should match score according to thresholds"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/health-score")
        assert response.status_code == 200
        
        data = response.json()
        score = data.get("overall_score")
        status_name = data.get("status", {}).get("name")
        
        # Verify status matches score thresholds
        # excellent: >=85, good: >=70, fair: >=50, needs_attention: >=30, critical: <30
        if score >= 85:
            expected = "excellent"
        elif score >= 70:
            expected = "good"
        elif score >= 50:
            expected = "fair"
        elif score >= 30:
            expected = "needs_attention"
        else:
            expected = "critical"
        
        assert status_name == expected, f"Score {score} should have status '{expected}', got '{status_name}'"
        print(f"✅ Status '{status_name}' correctly matches score {score}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
