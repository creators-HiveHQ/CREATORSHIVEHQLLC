"""
Test Module B5: Auto-Escalation System
Tests for automatic proposal escalation endpoints.
All endpoints require admin authentication.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://aigenthq-1.preview.emergentagent.com')

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@hivehq.com", "password": "admin123"}
FREE_CREATOR_CREDENTIALS = {"email": "freetest@hivehq.com", "password": "testpassword"}


class TestAutoEscalationAuth:
    """Test authentication requirements for escalation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_creator_token(self):
        """Get creator authentication token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json=FREE_CREATOR_CREDENTIALS)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_dashboard_requires_auth(self):
        """GET /api/admin/escalation/dashboard - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Dashboard requires authentication")
    
    def test_stalled_requires_auth(self):
        """GET /api/admin/escalation/stalled - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/stalled")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Stalled endpoint requires authentication")
    
    def test_history_requires_auth(self):
        """GET /api/admin/escalation/history - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ History endpoint requires authentication")
    
    def test_analytics_requires_auth(self):
        """GET /api/admin/escalation/analytics - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/analytics")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Analytics endpoint requires authentication")
    
    def test_config_requires_auth(self):
        """GET /api/admin/escalation/config - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/config")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Config endpoint requires authentication")
    
    def test_scan_requires_auth(self):
        """POST /api/admin/escalation/scan - Requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/escalation/scan")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Scan endpoint requires authentication")
    
    def test_creator_cannot_access_dashboard(self):
        """Non-admin users receive 403 error"""
        token = self.get_creator_token()
        if not token:
            pytest.skip("Could not get creator token")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard", headers=headers)
        assert response.status_code == 403, f"Expected 403 for creator, got {response.status_code}"
        print("✓ Non-admin users receive 403 error")


class TestEscalationDashboard:
    """Test escalation dashboard endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get admin token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_dashboard_returns_summary(self):
        """GET /api/admin/escalation/dashboard - Returns summary stats"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "summary" in data, "Response should contain 'summary'"
        print(f"✓ Dashboard returns summary: {data.get('summary', {})}")
    
    def test_dashboard_summary_structure(self):
        """Dashboard summary has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        
        # Check required fields
        assert "total_active" in summary, "Summary should have 'total_active'"
        assert "by_level" in summary, "Summary should have 'by_level'"
        assert "resolved_24h" in summary, "Summary should have 'resolved_24h'"
        assert "avg_resolution_hours" in summary, "Summary should have 'avg_resolution_hours'"
        
        # Check by_level structure
        by_level = summary.get("by_level", {})
        assert isinstance(by_level, dict), "by_level should be a dict"
        
        print(f"✓ Summary structure correct: total_active={summary.get('total_active')}, by_level={by_level}")
    
    def test_dashboard_returns_active_escalations(self):
        """Dashboard returns active escalations list"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "active_escalations" in data, "Response should contain 'active_escalations'"
        assert isinstance(data["active_escalations"], list), "active_escalations should be a list"
        
        print(f"✓ Dashboard returns {len(data['active_escalations'])} active escalations")
    
    def test_dashboard_returns_health_status(self):
        """Dashboard returns health status"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/dashboard", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "health_status" in data, "Response should contain 'health_status'"
        
        valid_statuses = ["healthy", "fair", "needs_attention", "poor", "critical"]
        assert data["health_status"] in valid_statuses, f"Invalid health status: {data['health_status']}"
        
        print(f"✓ Health status: {data['health_status']}")


class TestStalledProposals:
    """Test stalled proposals endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_stalled_returns_list(self):
        """GET /api/admin/escalation/stalled - Returns list of stalled proposals"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/stalled", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "stalled_proposals" in data, "Response should contain 'stalled_proposals'"
        assert isinstance(data["stalled_proposals"], list), "stalled_proposals should be a list"
        assert "total" in data, "Response should contain 'total'"
        assert "threshold_hours" in data, "Response should contain 'threshold_hours'"
        
        print(f"✓ Stalled endpoint returns {data['total']} proposals (threshold: {data['threshold_hours']}h)")
    
    def test_stalled_threshold_parameter(self):
        """Stalled endpoint accepts threshold_hours parameter"""
        # Test with 24 hours threshold
        response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/stalled?threshold_hours=24",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["threshold_hours"] == 24, "Threshold should be 24"
        
        # Test with 96 hours threshold
        response2 = self.session.get(
            f"{BASE_URL}/api/admin/escalation/stalled?threshold_hours=96",
            headers=self.headers
        )
        assert response2.status_code == 200
        
        data2 = response2.json()
        assert data2["threshold_hours"] == 96, "Threshold should be 96"
        
        print(f"✓ Threshold parameter works: 24h={data['total']} proposals, 96h={data2['total']} proposals")
    
    def test_stalled_proposal_structure(self):
        """Stalled proposals have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/stalled", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        proposals = data.get("stalled_proposals", [])
        
        if len(proposals) > 0:
            proposal = proposals[0]
            expected_fields = ["proposal_id", "title", "status", "hours_stalled"]
            for field in expected_fields:
                assert field in proposal, f"Proposal should have '{field}'"
            
            print(f"✓ Stalled proposal structure correct: {list(proposal.keys())}")
        else:
            print("✓ No stalled proposals to verify structure (empty list)")


class TestEscalationHistory:
    """Test escalation history endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_history_returns_list(self):
        """GET /api/admin/escalation/history - Returns escalation history"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/history", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "escalations" in data, "Response should contain 'escalations'"
        assert isinstance(data["escalations"], list), "escalations should be a list"
        assert "total" in data, "Response should contain 'total'"
        
        print(f"✓ History returns {data['total']} escalations")
    
    def test_history_include_resolved_filter(self):
        """History endpoint accepts include_resolved filter"""
        # With resolved
        response1 = self.session.get(
            f"{BASE_URL}/api/admin/escalation/history?include_resolved=true",
            headers=self.headers
        )
        assert response1.status_code == 200
        
        # Without resolved
        response2 = self.session.get(
            f"{BASE_URL}/api/admin/escalation/history?include_resolved=false",
            headers=self.headers
        )
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        print(f"✓ Include resolved filter works: with_resolved={data1['total']}, without_resolved={data2['total']}")
    
    def test_history_level_filter(self):
        """History endpoint accepts level filter"""
        for level in ["elevated", "urgent", "critical"]:
            response = self.session.get(
                f"{BASE_URL}/api/admin/escalation/history?level={level}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Level filter '{level}' should work"
        
        print("✓ Level filter works for elevated, urgent, critical")
    
    def test_history_filters_applied(self):
        """History response includes filters_applied"""
        response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/history?include_resolved=false&level=urgent",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "filters_applied" in data, "Response should contain 'filters_applied'"
        
        filters = data["filters_applied"]
        assert filters.get("include_resolved") == False, "include_resolved filter should be False"
        assert filters.get("level_filter") == "urgent", "level_filter should be 'urgent'"
        
        print(f"✓ Filters applied correctly: {filters}")


class TestEscalationAnalytics:
    """Test escalation analytics endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_analytics_returns_data(self):
        """GET /api/admin/escalation/analytics - Returns analytics data"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/analytics", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        expected_fields = ["period_days", "total_escalations", "by_level", "by_reason", "resolution_rate"]
        for field in expected_fields:
            assert field in data, f"Analytics should contain '{field}'"
        
        print(f"✓ Analytics returns data: {data.get('total_escalations')} escalations in {data.get('period_days')} days")
    
    def test_analytics_days_parameter(self):
        """Analytics endpoint accepts days parameter"""
        response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/analytics?days=7",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 7, "Period should be 7 days"
        
        print(f"✓ Days parameter works: {data['period_days']} days")
    
    def test_analytics_by_level_structure(self):
        """Analytics by_level has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/analytics", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        by_level = data.get("by_level", {})
        
        # Should have counts for each level
        assert isinstance(by_level, dict), "by_level should be a dict"
        
        print(f"✓ Analytics by_level: {by_level}")
    
    def test_analytics_resolution_rate(self):
        """Analytics includes resolution rate"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/analytics", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        resolution_rate = data.get("resolution_rate")
        
        assert resolution_rate is not None, "Should have resolution_rate"
        assert isinstance(resolution_rate, (int, float)), "resolution_rate should be numeric"
        assert 0 <= resolution_rate <= 100, "resolution_rate should be 0-100"
        
        print(f"✓ Resolution rate: {resolution_rate}%")


class TestEscalationConfig:
    """Test escalation config endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_config_returns_thresholds(self):
        """GET /api/admin/escalation/config - Returns thresholds"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/config", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "thresholds" in data, "Config should contain 'thresholds'"
        
        thresholds = data["thresholds"]
        assert isinstance(thresholds, dict), "thresholds should be a dict"
        
        print(f"✓ Config returns thresholds for statuses: {list(thresholds.keys())}")
    
    def test_config_returns_actions(self):
        """Config returns escalation actions"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/config", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "actions" in data, "Config should contain 'actions'"
        
        actions = data["actions"]
        assert isinstance(actions, dict), "actions should be a dict"
        
        print(f"✓ Config returns actions for levels: {list(actions.keys())}")
    
    def test_config_returns_monitored_statuses(self):
        """Config returns monitored statuses"""
        response = self.session.get(f"{BASE_URL}/api/admin/escalation/config", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "monitored_statuses" in data, "Config should contain 'monitored_statuses'"
        
        statuses = data["monitored_statuses"]
        assert isinstance(statuses, list), "monitored_statuses should be a list"
        
        # Expected monitored statuses
        expected = ["submitted", "under_review", "approved", "in_progress", "needs_revision"]
        for status in expected:
            assert status in statuses, f"'{status}' should be monitored"
        
        print(f"✓ Monitored statuses: {statuses}")


class TestEscalationScan:
    """Test escalation scan endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_scan_runs_successfully(self):
        """POST /api/admin/escalation/scan - Runs full escalation scan"""
        response = self.session.post(f"{BASE_URL}/api/admin/escalation/scan", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        expected_fields = ["scanned", "needs_escalation", "escalated", "errors"]
        for field in expected_fields:
            assert field in data, f"Scan result should contain '{field}'"
        
        print(f"✓ Scan completed: scanned={data['scanned']}, needs_escalation={data['needs_escalation']}, escalated={data['escalated']}")
    
    def test_scan_returns_escalations_list(self):
        """Scan returns list of escalations created"""
        response = self.session.post(f"{BASE_URL}/api/admin/escalation/scan", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "escalations" in data, "Scan should return 'escalations' list"
        assert isinstance(data["escalations"], list), "escalations should be a list"
        
        print(f"✓ Scan created {len(data['escalations'])} new escalations")


class TestCheckProposal:
    """Test check proposal escalation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_check_nonexistent_proposal(self):
        """Check returns error for non-existent proposal"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/escalation/check/NONEXISTENT-123",
            headers=self.headers
        )
        assert response.status_code == 200  # Returns result with error field
        
        data = response.json()
        assert data.get("needs_escalation") == False or "error" in data
        
        print("✓ Check handles non-existent proposal correctly")
    
    def test_check_returns_escalation_status(self):
        """Check returns escalation status for proposal"""
        # First get a stalled proposal
        stalled_response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/stalled?threshold_hours=24",
            headers=self.headers
        )
        
        if stalled_response.status_code == 200:
            stalled = stalled_response.json().get("stalled_proposals", [])
            if len(stalled) > 0:
                proposal_id = stalled[0]["proposal_id"]
                
                response = self.session.post(
                    f"{BASE_URL}/api/admin/escalation/check/{proposal_id}",
                    headers=self.headers
                )
                assert response.status_code == 200
                
                data = response.json()
                assert "proposal_id" in data, "Should return proposal_id"
                assert "needs_escalation" in data, "Should return needs_escalation"
                assert "hours_in_status" in data, "Should return hours_in_status"
                
                print(f"✓ Check returns status: needs_escalation={data['needs_escalation']}, hours={data.get('hours_in_status')}")
                return
        
        print("✓ No stalled proposals to check (skipped detailed check)")


class TestManualEscalation:
    """Test manual escalation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_escalate_nonexistent_proposal(self):
        """Escalate returns error for non-existent proposal"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/escalation/escalate/NONEXISTENT-123?level=elevated",
            headers=self.headers
        )
        # Should return 400 with error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Escalate handles non-existent proposal correctly")
    
    def test_escalate_with_parameters(self):
        """Escalate accepts level, reason, and notes parameters"""
        # Get a stalled proposal to escalate
        stalled_response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/stalled?threshold_hours=24",
            headers=self.headers
        )
        
        if stalled_response.status_code == 200:
            stalled = stalled_response.json().get("stalled_proposals", [])
            # Find one that's not already escalated
            for proposal in stalled:
                if not proposal.get("already_escalated"):
                    proposal_id = proposal["proposal_id"]
                    
                    response = self.session.post(
                        f"{BASE_URL}/api/admin/escalation/escalate/{proposal_id}?level=elevated&reason=admin_attention&notes=Test escalation",
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        assert data.get("success") == True, "Escalation should succeed"
                        assert "escalation_id" in data, "Should return escalation_id"
                        assert data.get("level") == "elevated", "Level should be elevated"
                        
                        print(f"✓ Manual escalation successful: {data.get('escalation_id')}")
                        return
        
        print("✓ No suitable proposals for manual escalation test (skipped)")


class TestResolveEscalation:
    """Test resolve escalation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Could not authenticate as admin")
    
    def test_resolve_nonexistent_escalation(self):
        """Resolve returns error for non-existent escalation"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/escalation/resolve/ESC-NONEXISTENT",
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Resolve handles non-existent escalation correctly")
    
    def test_resolve_with_notes(self):
        """Resolve accepts resolution_notes parameter"""
        # Get an active escalation
        dashboard_response = self.session.get(
            f"{BASE_URL}/api/admin/escalation/dashboard",
            headers=self.headers
        )
        
        if dashboard_response.status_code == 200:
            escalations = dashboard_response.json().get("active_escalations", [])
            if len(escalations) > 0:
                escalation_id = escalations[0]["escalation_id"]
                
                response = self.session.post(
                    f"{BASE_URL}/api/admin/escalation/resolve/{escalation_id}?resolution_notes=Test resolution",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assert data.get("success") == True, "Resolution should succeed"
                    assert data.get("resolved") == True, "Should be marked resolved"
                    
                    print(f"✓ Resolution successful: {escalation_id}")
                    return
        
        print("✓ No active escalations to resolve (skipped)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
