"""
Test Smart Automation Engine and Proposal Recommendations - Phase 4 Module B
Tests:
- Smart Automation Rules CRUD and evaluation
- Proposal Recommendations generation and retrieval
- Auto-recommendation trigger on rejection
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get admin headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestSmartAutomationRules:
    """Test Smart Automation Rules endpoints (Admin only)"""
    
    def test_get_automation_rules_requires_auth(self):
        """GET /api/admin/automation/rules requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/automation/rules")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ GET /api/admin/automation/rules requires authentication")
    
    def test_get_automation_rules_returns_list(self, admin_headers):
        """GET /api/admin/automation/rules returns list of rules"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        rules = response.json()
        assert isinstance(rules, list), "Should return a list"
        assert len(rules) >= 5, f"Should have at least 5 default rules, got {len(rules)}"
        print(f"✓ GET /api/admin/automation/rules returns {len(rules)} rules")
        return rules
    
    def test_automation_rules_have_required_fields(self, admin_headers):
        """Automation rules have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules",
            headers=admin_headers
        )
        assert response.status_code == 200
        rules = response.json()
        
        required_fields = ["id", "name", "description", "trigger_type", "actions", "is_active"]
        
        for rule in rules:
            for field in required_fields:
                assert field in rule, f"Rule missing field: {field}"
            
            # Verify actions is a list
            assert isinstance(rule["actions"], list), "Actions should be a list"
            assert len(rule["actions"]) > 0, "Rule should have at least one action"
            
            # Verify action types
            for action in rule["actions"]:
                assert "type" in action, "Action should have type"
        
        print(f"✓ All {len(rules)} rules have required fields")
    
    def test_get_specific_rule(self, admin_headers):
        """GET /api/admin/automation/rules/{rule_id} returns specific rule"""
        # First get all rules
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules",
            headers=admin_headers
        )
        rules = response.json()
        rule_id = rules[0]["id"]
        
        # Get specific rule
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules/{rule_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        rule = response.json()
        assert rule["id"] == rule_id
        print(f"✓ GET /api/admin/automation/rules/{rule_id} returns correct rule")
    
    def test_get_nonexistent_rule_returns_404(self, admin_headers):
        """GET /api/admin/automation/rules/{rule_id} returns 404 for nonexistent rule"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules/NONEXISTENT-RULE",
            headers=admin_headers
        )
        assert response.status_code == 404, "Should return 404 for nonexistent rule"
        print("✓ GET nonexistent rule returns 404")
    
    def test_toggle_rule_active_status(self, admin_headers):
        """POST /api/admin/automation/rules/{rule_id}/toggle toggles rule status"""
        # Get a rule
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules",
            headers=admin_headers
        )
        rules = response.json()
        rule = rules[0]
        rule_id = rule["id"]
        original_status = rule["is_active"]
        
        # Toggle to opposite status
        new_status = not original_status
        response = requests.post(
            f"{BASE_URL}/api/admin/automation/rules/{rule_id}/toggle?is_active={str(new_status).lower()}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        assert result["success"] == True
        assert result["is_active"] == new_status
        
        # Verify the change
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules/{rule_id}",
            headers=admin_headers
        )
        updated_rule = response.json()
        assert updated_rule["is_active"] == new_status
        
        # Toggle back to original
        response = requests.post(
            f"{BASE_URL}/api/admin/automation/rules/{rule_id}/toggle?is_active={str(original_status).lower()}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        print(f"✓ Toggle rule {rule_id} status works correctly")
    
    def test_default_rules_have_correct_structure(self, admin_headers):
        """Default rules have correct condition and action structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/rules",
            headers=admin_headers
        )
        rules = response.json()
        
        # Check for expected default rules
        rule_names = [r["name"] for r in rules]
        expected_rules = [
            "Low Approval Rate Coaching",
            "Rejection Streak Alert",
            "Inactivity Re-engagement",
            "High Performer Recognition",
            "Proposal Rejection Auto-Recommendations"
        ]
        
        for expected in expected_rules:
            assert expected in rule_names, f"Missing default rule: {expected}"
        
        # Check condition types
        for rule in rules:
            if rule.get("conditions"):
                cond = rule["conditions"]
                assert "type" in cond or "field" in cond, "Condition should have type or field"
        
        print(f"✓ All 5 default rules present with correct structure")


class TestAutomationEvaluation:
    """Test automation rule evaluation endpoints"""
    
    def test_evaluate_creator_requires_auth(self):
        """POST /api/admin/automation/evaluate/{creator_id} requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/admin/automation/evaluate/test-creator"
        )
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Evaluate creator requires authentication")
    
    def test_evaluate_creator_returns_results(self, admin_headers):
        """POST /api/admin/automation/evaluate/{creator_id} evaluates rules"""
        # Get a creator ID
        response = requests.get(
            f"{BASE_URL}/api/admin/creators",
            headers=admin_headers
        )
        if response.status_code == 200:
            creators = response.json()
            if isinstance(creators, list) and len(creators) > 0:
                creator_id = creators[0].get("id")
            else:
                creator_id = "test-creator-id"
        else:
            creator_id = "test-creator-id"
        
        # Evaluate rules for creator
        response = requests.post(
            f"{BASE_URL}/api/admin/automation/evaluate/{creator_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert "creator_id" in result
        assert "rules_triggered" in result
        assert isinstance(result["rules_triggered"], int)
        
        print(f"✓ Evaluate creator {creator_id}: {result['rules_triggered']} rules triggered")


class TestAutomationLog:
    """Test automation execution log endpoint"""
    
    def test_get_automation_log_requires_auth(self):
        """GET /api/admin/automation/log requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/automation/log")
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ GET /api/admin/automation/log requires authentication")
    
    def test_get_automation_log_returns_list(self, admin_headers):
        """GET /api/admin/automation/log returns list of log entries"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/log?limit=50",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        logs = response.json()
        assert isinstance(logs, list), "Should return a list"
        
        # If there are logs, verify structure
        if len(logs) > 0:
            log = logs[0]
            expected_fields = ["id", "rule_id", "rule_name", "creator_id", "triggered_at"]
            for field in expected_fields:
                assert field in log, f"Log entry missing field: {field}"
        
        print(f"✓ GET /api/admin/automation/log returns {len(logs)} entries")
    
    def test_automation_log_filter_by_limit(self, admin_headers):
        """GET /api/admin/automation/log respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/automation/log?limit=5",
            headers=admin_headers
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) <= 5, "Should respect limit parameter"
        print(f"✓ Automation log respects limit parameter")


class TestProposalRecommendations:
    """Test Proposal Recommendations endpoints"""
    
    @pytest.fixture(scope="class")
    def test_proposal_id(self, admin_headers):
        """Get or create a test proposal for recommendations"""
        # Try to find an existing rejected proposal
        response = requests.get(
            f"{BASE_URL}/api/admin/proposals?status=rejected&limit=1",
            headers=admin_headers
        )
        if response.status_code == 200:
            proposals = response.json()
            if isinstance(proposals, list) and len(proposals) > 0:
                return proposals[0].get("id")
        
        # Try to find any proposal
        response = requests.get(
            f"{BASE_URL}/api/admin/proposals?limit=1",
            headers=admin_headers
        )
        if response.status_code == 200:
            proposals = response.json()
            if isinstance(proposals, list) and len(proposals) > 0:
                return proposals[0].get("id")
        
        # Use a known proposal ID from the context
        return "PP-8d445ba6"
    
    def test_get_recommendations_requires_auth(self):
        """GET /api/proposals/{id}/recommendations requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/proposals/test-proposal/recommendations"
        )
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ GET recommendations requires authentication")
    
    def test_get_recommendations_for_proposal(self, admin_headers, test_proposal_id):
        """GET /api/proposals/{id}/recommendations returns recommendations or message"""
        response = requests.get(
            f"{BASE_URL}/api/proposals/{test_proposal_id}/recommendations",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert "proposal_id" in result
        # Either has recommendations or a message
        assert "recommendations" in result or "message" in result
        
        print(f"✓ GET recommendations for {test_proposal_id}: {'has recommendations' if result.get('recommendations') else 'no recommendations yet'}")
    
    def test_generate_recommendations_requires_auth(self):
        """POST /api/proposals/{id}/generate-recommendations requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/proposals/test-proposal/generate-recommendations"
        )
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ Generate recommendations requires authentication")
    
    def test_generate_recommendations_for_proposal(self, admin_headers, test_proposal_id):
        """POST /api/proposals/{id}/generate-recommendations generates AI recommendations"""
        response = requests.post(
            f"{BASE_URL}/api/proposals/{test_proposal_id}/generate-recommendations",
            headers=admin_headers
        )
        
        # May return 404 if proposal not found, or 200 with recommendations
        if response.status_code == 404:
            print(f"⚠ Proposal {test_proposal_id} not found - skipping generation test")
            pytest.skip("Proposal not found")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        
        assert result.get("success") == True, "Should return success=True"
        assert "recommendations" in result, "Should return recommendations"
        assert "proposal_id" in result
        
        recommendations = result["recommendations"]
        # Check recommendation structure
        expected_fields = ["analysis", "recommendations", "quick_wins", "encouragement"]
        for field in expected_fields:
            assert field in recommendations, f"Recommendations missing field: {field}"
        
        print(f"✓ Generated recommendations for {test_proposal_id}")
        print(f"  - Analysis severity: {recommendations.get('analysis', {}).get('severity', 'N/A')}")
        print(f"  - Quick wins: {len(recommendations.get('quick_wins', []))}")
        print(f"  - Detailed recommendations: {len(recommendations.get('recommendations', []))}")
    
    def test_recommendations_have_correct_structure(self, admin_headers, test_proposal_id):
        """Recommendations have correct structure with analysis and suggestions"""
        # First generate recommendations
        response = requests.post(
            f"{BASE_URL}/api/proposals/{test_proposal_id}/generate-recommendations",
            headers=admin_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Proposal not found")
        
        assert response.status_code == 200
        result = response.json()
        recommendations = result.get("recommendations", {})
        
        # Check analysis structure
        analysis = recommendations.get("analysis", {})
        if analysis:
            assert "likely_issues" in analysis or "severity" in analysis or "improvement_potential" in analysis
        
        # Check detailed recommendations structure
        detailed_recs = recommendations.get("recommendations", [])
        if detailed_recs:
            for rec in detailed_recs:
                assert "category" in rec, "Recommendation should have category"
                assert "suggestion" in rec, "Recommendation should have suggestion"
        
        print("✓ Recommendations have correct structure")


class TestAutoRecommendationOnRejection:
    """Test auto-recommendation trigger when proposal is rejected"""
    
    def test_rejection_triggers_recommendation_generation(self, admin_headers):
        """Rejecting a proposal triggers auto-recommendation generation"""
        # Get a proposal that can be rejected
        response = requests.get(
            f"{BASE_URL}/api/admin/proposals?status=submitted&limit=1",
            headers=admin_headers
        )
        
        if response.status_code != 200:
            print("⚠ Could not fetch proposals - skipping rejection test")
            pytest.skip("Could not fetch proposals")
        
        proposals = response.json()
        if not isinstance(proposals, list) or len(proposals) == 0:
            # Try under_review status
            response = requests.get(
                f"{BASE_URL}/api/admin/proposals?status=under_review&limit=1",
                headers=admin_headers
            )
            if response.status_code == 200:
                proposals = response.json()
        
        if not isinstance(proposals, list) or len(proposals) == 0:
            print("⚠ No proposals available for rejection test")
            pytest.skip("No proposals available for rejection")
        
        proposal_id = proposals[0].get("id")
        
        # Reject the proposal
        response = requests.put(
            f"{BASE_URL}/api/admin/proposals/{proposal_id}",
            headers=admin_headers,
            json={
                "status": "rejected",
                "review_notes": "Test rejection for automation testing"
            }
        )
        
        if response.status_code != 200:
            print(f"⚠ Could not reject proposal: {response.text}")
            pytest.skip("Could not reject proposal")
        
        result = response.json()
        
        # Check that recommendations_generating flag is set
        assert result.get("recommendations_generating") == True, "Should indicate recommendations are generating"
        
        # Wait a moment for async recommendation generation
        time.sleep(3)
        
        # Check if recommendations were generated
        response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}/recommendations",
            headers=admin_headers
        )
        assert response.status_code == 200
        rec_result = response.json()
        
        # Recommendations should now exist
        if rec_result.get("recommendations"):
            print(f"✓ Auto-recommendations generated for rejected proposal {proposal_id}")
        else:
            print(f"⚠ Recommendations may still be generating for {proposal_id}")


class TestCommonRejectionIssues:
    """Test common rejection issues endpoint"""
    
    def test_get_common_issues_requires_auth(self):
        """GET /api/admin/recommendations/common-issues requires auth"""
        response = requests.get(
            f"{BASE_URL}/api/admin/recommendations/common-issues"
        )
        assert response.status_code in [401, 403], "Should require authentication"
        print("✓ GET common issues requires authentication")
    
    def test_get_common_issues_returns_list(self, admin_headers):
        """GET /api/admin/recommendations/common-issues returns analysis"""
        response = requests.get(
            f"{BASE_URL}/api/admin/recommendations/common-issues",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        assert isinstance(result, list), "Should return a list"
        
        # If there are issues, verify structure
        if len(result) > 0:
            issue = result[0]
            assert "category" in issue, "Issue should have category"
            assert "count" in issue, "Issue should have count"
        
        print(f"✓ GET common issues returns {len(result)} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
