"""
Test ARRIS Historical Learning Visualization Feature
Tests the historical comparison visualization for ARRIS learning over time.

Endpoints tested:
- GET /api/arris/learning-snapshot - Available to all creators (limited for non-Premium)
- GET /api/arris/learning-timeline - Premium/Elite only
- GET /api/arris/learning-comparison - Premium/Elite only
- GET /api/arris/growth-chart - Premium/Elite only
- GET /api/arris/milestones - Available to all creators
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PRO_CREATOR = {
    "email": "protest@example.com",
    "password": "testpassword"
}

PREMIUM_CREATOR = {
    "email": "premium@example.com",
    "password": "testpassword"
}


class TestArrisHistoricalLearning:
    """Test ARRIS Historical Learning endpoints"""
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get Pro creator token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PRO_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Pro creator login failed")
    
    @pytest.fixture(scope="class")
    def premium_token(self):
        """Get Premium creator token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PREMIUM_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Premium creator login failed")
    
    # ============== LEARNING SNAPSHOT TESTS ==============
    
    def test_learning_snapshot_requires_auth(self):
        """Test that learning-snapshot requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_learning_snapshot_pro_user(self, pro_token):
        """Test learning-snapshot returns data for Pro users with limited patterns"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "creator_id" in data
        assert "memory_summary" in data
        assert "active_patterns" in data
        assert "learning_metrics" in data
        assert "health_score" in data
        assert "is_premium" in data
        
        # Pro users should have is_premium=False
        assert data["is_premium"] == False
        
        # Pro users should have upgrade_prompt
        assert "upgrade_prompt" in data
        assert "message" in data["upgrade_prompt"]
        assert "features" in data["upgrade_prompt"]
        
        # Pro users should have limited patterns (max 3)
        assert len(data.get("active_patterns", [])) <= 3
    
    def test_learning_snapshot_premium_user(self, premium_token):
        """Test learning-snapshot returns full data for Premium users"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "creator_id" in data
        assert "memory_summary" in data
        assert "active_patterns" in data
        assert "learning_metrics" in data
        assert "health_score" in data
        assert "is_premium" in data
        
        # Premium users should have is_premium=True
        assert data["is_premium"] == True
        
        # Premium users should NOT have upgrade_prompt
        assert "upgrade_prompt" not in data
    
    def test_learning_snapshot_health_score_structure(self, premium_token):
        """Test health_score has correct structure"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        health_score = data.get("health_score", {})
        
        # Verify health score structure
        assert "score" in health_score
        assert "status" in health_score
        assert "message" in health_score
        assert "recommendation" in health_score
        assert "breakdown" in health_score
        
        # Verify breakdown structure
        breakdown = health_score.get("breakdown", {})
        assert "memory_score" in breakdown
        assert "pattern_score" in breakdown
        assert "accuracy_score" in breakdown
    
    def test_learning_snapshot_learning_metrics_structure(self, premium_token):
        """Test learning_metrics has correct structure"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        metrics = data.get("learning_metrics", {})
        
        # Verify learning metrics structure
        assert "total_predictions" in metrics
        assert "accurate_predictions" in metrics
        assert "accuracy_rate" in metrics
        assert "learning_stage" in metrics
        assert "stage_description" in metrics
    
    def test_learning_snapshot_memory_summary_structure(self, premium_token):
        """Test memory_summary has correct structure"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-snapshot", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        memory_summary = data.get("memory_summary", {})
        
        # Verify memory summary structure
        assert "total_memories" in memory_summary
        assert "by_type" in memory_summary
    
    # ============== LEARNING TIMELINE TESTS ==============
    
    def test_learning_timeline_requires_auth(self):
        """Test that learning-timeline requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/learning-timeline")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_learning_timeline_pro_user_forbidden(self, pro_token):
        """Test learning-timeline returns 403 for Pro users (Premium only)"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-timeline", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail.get("error") == "feature_gated"
        assert "premium" in detail.get("required_tier", "").lower()
    
    def test_learning_timeline_premium_user(self, premium_token):
        """Test learning-timeline returns data for Premium users"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-timeline", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "creator_id" in data
        assert "date_range" in data
        assert "memory_timeline" in data
        assert "pattern_timeline" in data
        assert "learning_progression" in data
        assert "milestones" in data
        assert "generated_at" in data
    
    def test_learning_timeline_date_range_param(self, premium_token):
        """Test learning-timeline respects date_range parameter"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        for date_range in ["7d", "30d", "90d", "1y", "all"]:
            response = requests.get(
                f"{BASE_URL}/api/arris/learning-timeline?date_range={date_range}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed for date_range={date_range}"
            data = response.json()
            assert data.get("date_range") == date_range
    
    # ============== LEARNING COMPARISON TESTS ==============
    
    def test_learning_comparison_requires_auth(self):
        """Test that learning-comparison requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/learning-comparison")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_learning_comparison_pro_user_forbidden(self, pro_token):
        """Test learning-comparison returns 403 for Pro users (Premium only)"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-comparison", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail.get("error") == "feature_gated"
        assert "premium" in detail.get("required_tier", "").lower()
    
    def test_learning_comparison_premium_user(self, premium_token):
        """Test learning-comparison returns data for Premium users"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning-comparison", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "creator_id" in data
        assert "current_period" in data
        assert "previous_period" in data
        assert "comparisons" in data
        assert "generated_at" in data
        
        # Verify current_period structure
        current = data.get("current_period", {})
        assert "label" in current
        assert "start" in current
        assert "end" in current
        assert "stats" in current
        
        # Verify previous_period structure
        previous = data.get("previous_period", {})
        assert "label" in previous
        assert "start" in previous
        assert "end" in previous
        assert "stats" in previous
        
        # Verify comparisons structure
        comparisons = data.get("comparisons", {})
        assert "memories_change" in comparisons
        assert "patterns_change" in comparisons
        assert "accuracy_change" in comparisons
        assert "interactions_change" in comparisons
        assert "overall_trend" in comparisons
    
    def test_learning_comparison_period_params(self, premium_token):
        """Test learning-comparison respects period parameters"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/arris/learning-comparison?period1=7d&period2=prev_7d",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("current_period", {}).get("label") == "7d"
        assert data.get("previous_period", {}).get("label") == "prev_7d"
    
    # ============== GROWTH CHART TESTS ==============
    
    def test_growth_chart_requires_auth(self):
        """Test that growth-chart requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/growth-chart")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_growth_chart_pro_user_forbidden(self, pro_token):
        """Test growth-chart returns 403 for Pro users (Premium only)"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/growth-chart", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail.get("error") == "feature_gated"
        assert "premium" in detail.get("required_tier", "").lower()
    
    def test_growth_chart_premium_user(self, premium_token):
        """Test growth-chart returns data for Premium users"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/growth-chart", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "creator_id" in data
        assert "metric" in data
        assert "granularity" in data
        assert "data_points" in data
        assert "total_days" in data
        assert "generated_at" in data
    
    def test_growth_chart_metric_params(self, premium_token):
        """Test growth-chart respects metric parameter"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        for metric in ["memories", "patterns", "accuracy", "interactions"]:
            response = requests.get(
                f"{BASE_URL}/api/arris/growth-chart?metric={metric}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed for metric={metric}"
            data = response.json()
            assert data.get("metric") == metric
    
    def test_growth_chart_granularity_params(self, premium_token):
        """Test growth-chart respects granularity parameter"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        for granularity in ["daily", "weekly", "monthly"]:
            response = requests.get(
                f"{BASE_URL}/api/arris/growth-chart?granularity={granularity}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed for granularity={granularity}"
            data = response.json()
            assert data.get("granularity") == granularity
    
    # ============== MILESTONES TESTS ==============
    
    def test_milestones_requires_auth(self):
        """Test that milestones requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/milestones")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_milestones_pro_user(self, pro_token):
        """Test milestones returns data for Pro users (available to all)"""
        headers = {"Authorization": f"Bearer {pro_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/milestones", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "milestones" in data
        assert "creator_id" in data
        assert isinstance(data["milestones"], list)
    
    def test_milestones_premium_user(self, premium_token):
        """Test milestones returns data for Premium users"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/milestones", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "milestones" in data
        assert "creator_id" in data
        assert isinstance(data["milestones"], list)
        
        # Premium user should have seeded milestones
        milestones = data["milestones"]
        if len(milestones) > 0:
            # Verify milestone structure
            milestone = milestones[0]
            assert "type" in milestone
            assert "title" in milestone
            assert "description" in milestone
            assert "date" in milestone
            assert "icon" in milestone


class TestArrisHistoricalLearningDataIntegrity:
    """Test data integrity for ARRIS Historical Learning"""
    
    @pytest.fixture(scope="class")
    def premium_token(self):
        """Get Premium creator token"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PREMIUM_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Premium creator login failed")
    
    def test_snapshot_and_milestones_consistency(self, premium_token):
        """Test that snapshot and milestones return consistent data"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        # Get snapshot
        snapshot_response = requests.get(
            f"{BASE_URL}/api/arris/learning-snapshot",
            headers=headers
        )
        assert snapshot_response.status_code == 200
        snapshot = snapshot_response.json()
        
        # Get milestones
        milestones_response = requests.get(
            f"{BASE_URL}/api/arris/milestones",
            headers=headers
        )
        assert milestones_response.status_code == 200
        milestones = milestones_response.json()
        
        # Both should have same creator_id
        assert snapshot.get("creator_id") == milestones.get("creator_id")
    
    def test_timeline_and_comparison_consistency(self, premium_token):
        """Test that timeline and comparison return consistent data"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        # Get timeline
        timeline_response = requests.get(
            f"{BASE_URL}/api/arris/learning-timeline?date_range=30d",
            headers=headers
        )
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()
        
        # Get comparison
        comparison_response = requests.get(
            f"{BASE_URL}/api/arris/learning-comparison?period1=30d&period2=prev_30d",
            headers=headers
        )
        assert comparison_response.status_code == 200
        comparison = comparison_response.json()
        
        # Both should have same creator_id
        assert timeline.get("creator_id") == comparison.get("creator_id")
    
    def test_health_score_calculation(self, premium_token):
        """Test that health score is calculated correctly"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/arris/learning-snapshot",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        health_score = data.get("health_score", {})
        breakdown = health_score.get("breakdown", {})
        
        # Score should be sum of breakdown components
        expected_score = (
            breakdown.get("memory_score", 0) +
            breakdown.get("pattern_score", 0) +
            breakdown.get("accuracy_score", 0)
        )
        
        # Allow for rounding differences
        assert abs(health_score.get("score", 0) - expected_score) <= 1
        
        # Score should be between 0 and 100
        assert 0 <= health_score.get("score", 0) <= 100
        
        # Status should be valid
        valid_statuses = ["new", "early", "developing", "good", "excellent"]
        assert health_score.get("status") in valid_statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
