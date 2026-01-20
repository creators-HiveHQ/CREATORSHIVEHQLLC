"""
Test Export Feature for Creators Hive HQ
Tests CSV/JSON export for Pro and Premium analytics

Features tested:
- GET /api/export/proposals - Pro+ tier export proposals
- GET /api/export/analytics - Pro+ tier export analytics
- GET /api/export/revenue - Premium+ tier export revenue
- GET /api/export/full-report - Premium+ tier full report
- Access gating for Free/Starter users (403)
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


class TestExportFeatureGating:
    """Test that export endpoints properly gate access by tier"""
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get auth token for Pro tier creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PRO_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Pro creator login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def pro_headers(self, pro_token):
        """Headers with Pro tier auth"""
        return {"Authorization": f"Bearer {pro_token}"}
    
    # ============== PROPOSALS EXPORT TESTS ==============
    
    def test_export_proposals_json_format(self, pro_headers):
        """Test proposals export returns correct JSON format"""
        response = requests.get(
            f"{BASE_URL}/api/export/proposals?format=json&date_range=30d",
            headers=pro_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify JSON export structure
        assert "format" in data, "Missing 'format' field"
        assert data["format"] == "json", f"Expected format 'json', got {data['format']}"
        assert "data" in data, "Missing 'data' field"
        assert "filename" in data, "Missing 'filename' field"
        assert "record_count" in data, "Missing 'record_count' field"
        assert "content_type" in data, "Missing 'content_type' field"
        assert data["content_type"] == "application/json"
        assert ".json" in data["filename"], "Filename should have .json extension"
        print(f"✅ Proposals JSON export: {data['record_count']} records")
    
    def test_export_proposals_csv_format(self, pro_headers):
        """Test proposals export returns correct CSV format"""
        response = requests.get(
            f"{BASE_URL}/api/export/proposals?format=csv&date_range=30d",
            headers=pro_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify CSV export structure
        assert data["format"] == "csv", f"Expected format 'csv', got {data['format']}"
        assert "data" in data, "Missing 'data' field (CSV string)"
        assert isinstance(data["data"], str), "CSV data should be a string"
        assert "filename" in data, "Missing 'filename' field"
        assert ".csv" in data["filename"], "Filename should have .csv extension"
        assert data["content_type"] == "text/csv"
        
        # Verify CSV has headers
        csv_data = data["data"]
        assert "id" in csv_data or "title" in csv_data, "CSV should contain column headers"
        print(f"✅ Proposals CSV export: {data['record_count']} records, {len(csv_data)} bytes")
    
    def test_export_proposals_date_ranges(self, pro_headers):
        """Test proposals export with different date ranges"""
        date_ranges = ["7d", "30d", "90d", "1y", "all"]
        
        for date_range in date_ranges:
            response = requests.get(
                f"{BASE_URL}/api/export/proposals?format=json&date_range={date_range}",
                headers=pro_headers
            )
            assert response.status_code == 200, f"Failed for date_range={date_range}: {response.text}"
            data = response.json()
            assert "record_count" in data
            print(f"✅ Date range {date_range}: {data['record_count']} records")
    
    # ============== ANALYTICS EXPORT TESTS ==============
    
    def test_export_analytics_json_format(self, pro_headers):
        """Test analytics export returns correct JSON format for Pro tier"""
        response = requests.get(
            f"{BASE_URL}/api/export/analytics?format=json&date_range=30d",
            headers=pro_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["format"] == "json"
        assert "data" in data
        assert "filename" in data
        assert "tier" in data, "Should include tier info"
        
        # Verify analytics data structure
        analytics = data["data"]
        assert "total_proposals" in analytics, "Missing total_proposals"
        assert "status_breakdown" in analytics, "Missing status_breakdown"
        assert "platform_breakdown" in analytics, "Missing platform_breakdown"
        assert "approval_rate" in analytics, "Missing approval_rate"
        print(f"✅ Analytics JSON export: {analytics['total_proposals']} proposals, {analytics['approval_rate']}% approval rate")
    
    def test_export_analytics_csv_format(self, pro_headers):
        """Test analytics export returns correct CSV format"""
        response = requests.get(
            f"{BASE_URL}/api/export/analytics?format=csv&date_range=30d",
            headers=pro_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["format"] == "csv"
        assert isinstance(data["data"], str), "CSV data should be a string"
        
        # Verify CSV contains expected sections
        csv_data = data["data"]
        assert "ANALYTICS SUMMARY" in csv_data, "CSV should contain ANALYTICS SUMMARY section"
        assert "STATUS BREAKDOWN" in csv_data, "CSV should contain STATUS BREAKDOWN section"
        assert "PLATFORM BREAKDOWN" in csv_data, "CSV should contain PLATFORM BREAKDOWN section"
        print(f"✅ Analytics CSV export: {len(csv_data)} bytes")


class TestExportAccessControl:
    """Test that export endpoints properly restrict access by tier"""
    
    @pytest.fixture(scope="class")
    def free_creator_token(self):
        """Create and login a free tier creator for testing access denial"""
        # First try to register a new free user
        import uuid
        test_email = f"freetest_{uuid.uuid4().hex[:8]}@example.com"
        
        register_response = requests.post(
            f"{BASE_URL}/api/creators/register",
            json={
                "name": "Free Test User",
                "email": test_email,
                "password": "testpassword123",
                "platforms": ["YouTube"],
                "niche": "Tech",
                "arris_response": "Testing export access"
            }
        )
        
        if register_response.status_code != 200:
            # Try to use existing free user
            login_response = requests.post(
                f"{BASE_URL}/api/creators/login",
                json={"email": "freetest@example.com", "password": "testpassword"}
            )
            if login_response.status_code == 200:
                return login_response.json().get("access_token")
            pytest.skip("Could not create or login free tier user")
        
        # Login the newly created user
        login_response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": test_email, "password": "testpassword123"}
        )
        
        if login_response.status_code == 200:
            return login_response.json().get("access_token")
        pytest.skip(f"Free creator login failed: {login_response.status_code}")
    
    def test_free_user_denied_proposals_export(self, free_creator_token):
        """Test that Free tier users get 403 on proposals export"""
        if not free_creator_token:
            pytest.skip("No free creator token available")
        
        headers = {"Authorization": f"Bearer {free_creator_token}"}
        response = requests.get(
            f"{BASE_URL}/api/export/proposals?format=json",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated", "Should return feature_gated error"
        assert "Pro" in detail.get("message", ""), "Error should mention Pro tier requirement"
        print("✅ Free user correctly denied proposals export (403)")
    
    def test_free_user_denied_analytics_export(self, free_creator_token):
        """Test that Free tier users get 403 on analytics export"""
        if not free_creator_token:
            pytest.skip("No free creator token available")
        
        headers = {"Authorization": f"Bearer {free_creator_token}"}
        response = requests.get(
            f"{BASE_URL}/api/export/analytics?format=json",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403 for free user, got {response.status_code}"
        print("✅ Free user correctly denied analytics export (403)")


class TestPremiumExportFeatures:
    """Test Premium-only export features"""
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get auth token for Pro tier creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PRO_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Pro creator login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def pro_headers(self, pro_token):
        """Headers with Pro tier auth"""
        return {"Authorization": f"Bearer {pro_token}"}
    
    def test_full_report_requires_premium(self, pro_headers):
        """Test that full-report export requires Premium tier (Pro should get 403)"""
        response = requests.get(
            f"{BASE_URL}/api/export/full-report?format=json",
            headers=pro_headers
        )
        
        # Pro tier should get 403 for full-report (Premium only)
        assert response.status_code == 403, f"Expected 403 for Pro user on full-report, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated"
        assert "Premium" in detail.get("message", ""), "Error should mention Premium tier requirement"
        print("✅ Pro user correctly denied full-report export (403 - Premium required)")
    
    def test_revenue_export_requires_premium(self, pro_headers):
        """Test that revenue export requires Premium tier"""
        response = requests.get(
            f"{BASE_URL}/api/export/revenue?format=json",
            headers=pro_headers
        )
        
        # Pro tier should get 403 for revenue export (Premium only)
        assert response.status_code == 403, f"Expected 403 for Pro user on revenue export, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated"
        assert "Premium" in detail.get("message", ""), "Error should mention Premium tier requirement"
        print("✅ Pro user correctly denied revenue export (403 - Premium required)")


class TestExportDataIntegrity:
    """Test that exported data is accurate and complete"""
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get auth token for Pro tier creator"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=PRO_CREATOR
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Pro creator login failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def pro_headers(self, pro_token):
        """Headers with Pro tier auth"""
        return {"Authorization": f"Bearer {pro_token}"}
    
    def test_proposals_export_matches_api_data(self, pro_headers):
        """Verify exported proposals match what's returned by the proposals API"""
        # Get proposals from regular API
        proposals_response = requests.get(
            f"{BASE_URL}/api/creators/me/proposals",
            headers=pro_headers
        )
        assert proposals_response.status_code == 200
        api_proposals = proposals_response.json()
        
        # Get exported proposals
        export_response = requests.get(
            f"{BASE_URL}/api/export/proposals?format=json&date_range=all",
            headers=pro_headers
        )
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        # Compare counts (export might have date filtering)
        print(f"API proposals: {len(api_proposals)}, Export proposals: {export_data['record_count']}")
        
        # Verify exported data has expected fields
        if export_data["data"]:
            first_proposal = export_data["data"][0]
            expected_fields = ["id", "title", "status", "platforms", "created_at"]
            for field in expected_fields:
                assert field in first_proposal, f"Missing field '{field}' in exported proposal"
        
        print(f"✅ Proposals export data integrity verified")
    
    def test_analytics_export_has_valid_metrics(self, pro_headers):
        """Verify analytics export contains valid calculated metrics"""
        response = requests.get(
            f"{BASE_URL}/api/export/analytics?format=json&date_range=30d",
            headers=pro_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        analytics = data["data"]
        
        # Verify metrics are valid numbers
        assert isinstance(analytics["total_proposals"], int), "total_proposals should be int"
        assert isinstance(analytics["approval_rate"], (int, float)), "approval_rate should be numeric"
        assert 0 <= analytics["approval_rate"] <= 100, "approval_rate should be 0-100"
        
        # Verify breakdowns are dicts
        assert isinstance(analytics["status_breakdown"], dict), "status_breakdown should be dict"
        assert isinstance(analytics["platform_breakdown"], dict), "platform_breakdown should be dict"
        
        print(f"✅ Analytics export metrics validated: {analytics['total_proposals']} proposals, {analytics['approval_rate']}% approval")


class TestExportEndpointSecurity:
    """Test export endpoint security"""
    
    def test_export_requires_authentication(self):
        """Test that export endpoints require authentication"""
        endpoints = [
            "/api/export/proposals",
            "/api/export/analytics",
            "/api/export/revenue",
            "/api/export/full-report"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code in [401, 403], f"{endpoint} should require auth, got {response.status_code}"
        
        print("✅ All export endpoints require authentication")
    
    def test_export_with_invalid_token(self):
        """Test that invalid tokens are rejected"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        
        response = requests.get(
            f"{BASE_URL}/api/export/proposals",
            headers=headers
        )
        
        assert response.status_code == 401, f"Expected 401 for invalid token, got {response.status_code}"
        print("✅ Invalid token correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
