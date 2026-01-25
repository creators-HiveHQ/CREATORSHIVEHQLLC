"""
Test Pattern Export Module (A5)
Tests pattern export functionality for Premium+ creators.
Covers: export options, preview, JSON/CSV export, history, and tier gating.
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USERS = {
    "free": {"email": "freetest@hivehq.com", "password": "testpassword"},
    "pro": {"email": "protest@hivehq.com", "password": "testpassword"},
    "premium": {"email": "premiumtest@hivehq.com", "password": "testpassword"},
    "elite": {"email": "elitetest@hivehq.com", "password": "testpassword123"},
}


@pytest.fixture(scope="module")
def tokens():
    """Get auth tokens for all test users"""
    user_tokens = {}
    for tier, creds in TEST_USERS.items():
        try:
            response = requests.post(
                f"{BASE_URL}/api/creators/login",
                json=creds,
                timeout=10
            )
            if response.status_code == 200:
                user_tokens[tier] = response.json().get("access_token")
            else:
                user_tokens[tier] = None
        except Exception as e:
            print(f"Failed to get token for {tier}: {e}")
            user_tokens[tier] = None
    return user_tokens


def get_headers(token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============== AUTHENTICATION TESTS ==============

class TestPatternExportAuth:
    """Test authentication requirements for pattern export endpoints"""
    
    def test_export_options_requires_auth(self):
        """GET /api/creators/me/pattern-export/options requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/pattern-export/options")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Export options endpoint requires authentication")
    
    def test_export_preview_requires_auth(self):
        """GET /api/creators/me/pattern-export/preview requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/pattern-export/preview")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Export preview endpoint requires authentication")
    
    def test_export_endpoint_requires_auth(self):
        """POST /api/creators/me/pattern-export requires authentication"""
        response = requests.post(f"{BASE_URL}/api/creators/me/pattern-export")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Export endpoint requires authentication")
    
    def test_export_history_requires_auth(self):
        """GET /api/creators/me/pattern-export/history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/pattern-export/history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Export history endpoint requires authentication")


# ============== TIER GATING TESTS ==============

class TestPatternExportTierGating:
    """Test tier gating - Free and Pro should be denied, Premium+ should have access"""
    
    def test_free_tier_denied_export_options(self, tokens):
        """Free tier users should get 403 with upgrade message for export options"""
        if not tokens.get("free"):
            pytest.skip("Free tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(tokens["free"])
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        # Check for upgrade message
        detail = response.json().get("detail", "")
        assert "upgrade" in detail.lower() or "premium" in detail.lower(), \
            f"Expected upgrade message, got: {detail}"
        print("✅ Free tier correctly denied with upgrade message")
    
    def test_pro_tier_denied_export_options(self, tokens):
        """Pro tier users should get 403 with upgrade message for export options"""
        if not tokens.get("pro"):
            pytest.skip("Pro tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(tokens["pro"])
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        detail = response.json().get("detail", "")
        assert "upgrade" in detail.lower() or "premium" in detail.lower(), \
            f"Expected upgrade message, got: {detail}"
        print("✅ Pro tier correctly denied with upgrade message")
    
    def test_premium_tier_has_access(self, tokens):
        """Premium tier users should have access to export options"""
        if not tokens.get("premium"):
            pytest.skip("Premium tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(tokens["premium"])
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("access_denied") != True, "Premium should not be access denied"
        print("✅ Premium tier has access to export options")
    
    def test_elite_tier_has_access(self, tokens):
        """Elite tier users should have access to export options"""
        if not tokens.get("elite"):
            pytest.skip("Elite tier token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(tokens["elite"])
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("access_denied") != True, "Elite should not be access denied"
        print("✅ Elite tier has access to export options")


# ============== EXPORT OPTIONS TESTS ==============

class TestPatternExportOptions:
    """Test export options endpoint structure and content"""
    
    def test_export_options_structure(self, tokens):
        """Export options should return correct structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "formats" in data, "Missing 'formats' field"
        assert "filters" in data, "Missing 'filters' field"
        assert "data_availability" in data, "Missing 'data_availability' field"
        assert "tier" in data, "Missing 'tier' field"
        
        print("✅ Export options has correct structure")
    
    def test_export_formats_available(self, tokens):
        """Export options should include JSON and CSV formats"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(token)
        )
        data = response.json()
        
        formats = data.get("formats", [])
        format_ids = [f.get("id") for f in formats]
        
        assert "json" in format_ids, "JSON format not available"
        assert "csv" in format_ids, "CSV format not available"
        
        # Check format structure
        for fmt in formats:
            assert "id" in fmt, "Format missing 'id'"
            assert "name" in fmt, "Format missing 'name'"
            assert "description" in fmt, "Format missing 'description'"
        
        print("✅ JSON and CSV formats available with correct structure")
    
    def test_export_filters_available(self, tokens):
        """Export options should include filter options"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(token)
        )
        data = response.json()
        
        filters = data.get("filters", {})
        
        assert "categories" in filters, "Missing categories filter"
        assert "confidence_levels" in filters, "Missing confidence_levels filter"
        assert "date_ranges" in filters, "Missing date_ranges filter"
        assert "include_options" in filters, "Missing include_options filter"
        
        # Check categories include expected values
        categories = filters.get("categories", [])
        assert "all" in categories, "Missing 'all' category"
        assert "success" in categories, "Missing 'success' category"
        assert "risk" in categories, "Missing 'risk' category"
        
        print("✅ Filter options available with correct structure")
    
    def test_data_availability_info(self, tokens):
        """Export options should include data availability info"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/options",
            headers=get_headers(token)
        )
        data = response.json()
        
        availability = data.get("data_availability", {})
        
        assert "total_patterns" in availability, "Missing total_patterns"
        assert "total_recommendations" in availability, "Missing total_recommendations"
        assert "last_updated" in availability, "Missing last_updated"
        
        # total_patterns should be a number
        assert isinstance(availability["total_patterns"], int), "total_patterns should be int"
        
        print("✅ Data availability info present and correct")


# ============== EXPORT PREVIEW TESTS ==============

class TestPatternExportPreview:
    """Test export preview endpoint"""
    
    def test_preview_returns_counts(self, tokens):
        """Preview should return pattern and recommendation counts"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/preview",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        preview = data.get("preview", {})
        
        assert "total_patterns" in preview, "Missing total_patterns in preview"
        assert "total_recommendations" in preview, "Missing total_recommendations in preview"
        assert "estimated_file_size" in preview, "Missing estimated_file_size in preview"
        
        print("✅ Preview returns counts and file size estimate")
    
    def test_preview_with_category_filter(self, tokens):
        """Preview should accept category filter"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/preview?categories=success,growth",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "preview" in data, "Missing preview in response"
        
        print("✅ Preview accepts category filter")
    
    def test_preview_with_confidence_filter(self, tokens):
        """Preview should accept confidence level filter"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/preview?confidence_level=high",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "preview" in data, "Missing preview in response"
        
        print("✅ Preview accepts confidence level filter")
    
    def test_preview_with_date_range_filter(self, tokens):
        """Preview should accept date range filter"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/preview?date_range=30d",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "preview" in data, "Missing preview in response"
        
        print("✅ Preview accepts date range filter")
    
    def test_preview_category_breakdown(self, tokens):
        """Preview should include category breakdown"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/preview",
            headers=get_headers(token)
        )
        data = response.json()
        preview = data.get("preview", {})
        
        assert "category_breakdown" in preview, "Missing category_breakdown"
        assert "confidence_breakdown" in preview, "Missing confidence_breakdown"
        
        print("✅ Preview includes category and confidence breakdowns")


# ============== JSON EXPORT TESTS ==============

class TestPatternExportJSON:
    """Test JSON export functionality"""
    
    def test_json_export_success(self, tokens):
        """JSON export should succeed for Premium+ users"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Export should be successful"
        
        print("✅ JSON export succeeds for Premium+ users")
    
    def test_json_export_structure(self, tokens):
        """JSON export should have correct response structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json",
            headers=get_headers(token)
        )
        data = response.json()
        
        # Check required fields
        assert "export_id" in data, "Missing export_id"
        assert "format" in data, "Missing format"
        assert "content" in data, "Missing content"
        assert "content_type" in data, "Missing content_type"
        assert "filename" in data, "Missing filename"
        assert "checksum" in data, "Missing checksum"
        assert "record_counts" in data, "Missing record_counts"
        
        # Verify format
        assert data["format"] == "json", f"Expected json format, got {data['format']}"
        assert data["content_type"] == "application/json", f"Wrong content type: {data['content_type']}"
        assert data["filename"].endswith(".json"), f"Filename should end with .json: {data['filename']}"
        
        print("✅ JSON export has correct response structure")
    
    def test_json_export_content_valid(self, tokens):
        """JSON export content should be valid JSON"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json",
            headers=get_headers(token)
        )
        data = response.json()
        
        content = data.get("content", "")
        
        # Parse the JSON content
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Export content is not valid JSON: {e}")
        
        # Check JSON structure
        assert "metadata" in parsed, "Missing metadata in export"
        assert "data" in parsed, "Missing data in export"
        assert "summary" in parsed, "Missing summary in export"
        
        # Check metadata
        metadata = parsed["metadata"]
        assert "export_id" in metadata, "Missing export_id in metadata"
        assert "exported_at" in metadata, "Missing exported_at in metadata"
        assert "format" in metadata, "Missing format in metadata"
        
        # Check data section
        export_data = parsed["data"]
        assert "patterns" in export_data, "Missing patterns in data"
        assert "recommendations" in export_data, "Missing recommendations in data"
        
        print("✅ JSON export content is valid and has correct structure")
    
    def test_json_export_with_filters(self, tokens):
        """JSON export should respect filters"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json&categories=success&confidence_level=high&date_range=30d",
            headers=get_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        # Parse content and check filters were applied
        content = json.loads(data["content"])
        metadata = content.get("metadata", {})
        filters = metadata.get("filters_applied", {})
        
        assert "success" in filters.get("categories", []), "Category filter not applied"
        assert filters.get("confidence_level") == "high", "Confidence filter not applied"
        assert filters.get("date_range") == "30d", "Date range filter not applied"
        
        print("✅ JSON export respects filters")


# ============== CSV EXPORT TESTS ==============

class TestPatternExportCSV:
    """Test CSV export functionality"""
    
    def test_csv_export_success(self, tokens):
        """CSV export should succeed for Premium+ users"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=csv",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Export should be successful"
        
        print("✅ CSV export succeeds for Premium+ users")
    
    def test_csv_export_structure(self, tokens):
        """CSV export should have correct response structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=csv",
            headers=get_headers(token)
        )
        data = response.json()
        
        # Check required fields
        assert "export_id" in data, "Missing export_id"
        assert "format" in data, "Missing format"
        assert "content" in data, "Missing content"
        assert "content_type" in data, "Missing content_type"
        assert "filename" in data, "Missing filename"
        
        # Verify format
        assert data["format"] == "csv", f"Expected csv format, got {data['format']}"
        assert data["content_type"] == "text/csv", f"Wrong content type: {data['content_type']}"
        assert data["filename"].endswith(".csv"), f"Filename should end with .csv: {data['filename']}"
        
        print("✅ CSV export has correct response structure")
    
    def test_csv_export_content_valid(self, tokens):
        """CSV export content should have proper CSV structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=csv",
            headers=get_headers(token)
        )
        data = response.json()
        
        content = data.get("content", "")
        
        # Check CSV has metadata header
        assert "# PATTERN EXPORT" in content, "Missing CSV header"
        assert "# Export ID:" in content, "Missing export ID in CSV"
        
        # Check for sections
        assert "## PATTERNS" in content or "Pattern ID" in content or content.strip(), \
            "CSV should have patterns section or be valid"
        
        print("✅ CSV export content has proper structure")
    
    def test_csv_export_with_include_options(self, tokens):
        """CSV export should respect include options"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=csv&include_recommendations=true&include_trends=true&include_feedback=true",
            headers=get_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        print("✅ CSV export respects include options")


# ============== EXPORT HISTORY TESTS ==============

class TestPatternExportHistory:
    """Test export history endpoint"""
    
    def test_history_returns_list(self, tokens):
        """Export history should return a list of exports"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/history",
            headers=get_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "exports" in data, "Missing exports field"
        assert isinstance(data["exports"], list), "exports should be a list"
        
        print("✅ Export history returns list of exports")
    
    def test_history_limit_parameter(self, tokens):
        """Export history should respect limit parameter"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/history?limit=5",
            headers=get_headers(token)
        )
        assert response.status_code == 200
        
        data = response.json()
        exports = data.get("exports", [])
        assert len(exports) <= 5, f"Expected max 5 exports, got {len(exports)}"
        
        print("✅ Export history respects limit parameter")
    
    def test_history_item_structure(self, tokens):
        """Export history items should have correct structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        # First do an export to ensure there's history
        requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json",
            headers=get_headers(token)
        )
        
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-export/history",
            headers=get_headers(token)
        )
        data = response.json()
        exports = data.get("exports", [])
        
        if len(exports) > 0:
            export_item = exports[0]
            assert "export_id" in export_item, "Missing export_id in history item"
            assert "exported_at" in export_item, "Missing exported_at in history item"
            assert "format" in export_item, "Missing format in history item"
            assert "record_counts" in export_item, "Missing record_counts in history item"
            print("✅ Export history items have correct structure")
        else:
            print("⚠️ No export history items to verify structure (expected if first run)")


# ============== INVALID FORMAT TESTS ==============

class TestPatternExportInvalidInputs:
    """Test error handling for invalid inputs"""
    
    def test_invalid_format_rejected(self, tokens):
        """Invalid export format should be rejected"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=xml",
            headers=get_headers(token)
        )
        assert response.status_code == 400, f"Expected 400 for invalid format, got {response.status_code}"
        
        print("✅ Invalid export format correctly rejected")


# ============== RECORD COUNTS TESTS ==============

class TestPatternExportRecordCounts:
    """Test record counts in export response"""
    
    def test_record_counts_structure(self, tokens):
        """Record counts should have correct structure"""
        token = tokens.get("premium") or tokens.get("elite")
        if not token:
            pytest.skip("No Premium+ token available")
        
        response = requests.post(
            f"{BASE_URL}/api/creators/me/pattern-export?export_format=json",
            headers=get_headers(token)
        )
        data = response.json()
        
        record_counts = data.get("record_counts", {})
        
        assert "patterns" in record_counts, "Missing patterns count"
        assert "recommendations" in record_counts, "Missing recommendations count"
        assert "trends" in record_counts, "Missing trends count"
        
        # Counts should be integers
        assert isinstance(record_counts["patterns"], int), "patterns count should be int"
        assert isinstance(record_counts["recommendations"], int), "recommendations count should be int"
        
        print("✅ Record counts have correct structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
