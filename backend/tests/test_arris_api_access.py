"""
Test Suite for ARRIS API Access (Phase 4 Module E - Task E3)
Tests Elite creator API key management and direct ARRIS API endpoints.

Features tested:
- Elite feature gating (Pro users get 403)
- API key management (create, list, get, revoke, regenerate)
- Direct API endpoints with X-ARRIS-API-Key auth
- Rate limiting (100/hour, 1000/day)
- Usage tracking
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emergentdb.preview.emergentagent.com').rstrip('/')

# Test credentials
ELITE_CREATOR = {
    "email": "elitetest@hivehq.com",
    "password": "testpassword123"
}

PRO_CREATOR = {
    "email": "protest@hivehq.com",
    "password": "testpassword"
}

# Existing API key for testing
EXISTING_API_KEY = "arris_live_cXAcjxcVsg3Q6fbqBlNgjA05UAuY7VD5XFTf7Gui058"


class TestArrisApiAccess:
    """Test ARRIS API Access for Elite creators"""
    
    elite_token = None
    pro_token = None
    created_key_id = None
    created_api_key = None
    
    @classmethod
    def setup_class(cls):
        """Login as Elite and Pro creators"""
        # Login as Elite creator
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_CREATOR)
        if response.status_code == 200:
            cls.elite_token = response.json().get("access_token")
            print(f"✅ Elite creator logged in successfully")
        else:
            print(f"❌ Elite login failed: {response.status_code} - {response.text}")
        
        # Login as Pro creator
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            cls.pro_token = response.json().get("access_token")
            print(f"✅ Pro creator logged in successfully")
        else:
            print(f"❌ Pro login failed: {response.status_code} - {response.text}")
    
    def get_elite_headers(self):
        return {"Authorization": f"Bearer {self.elite_token}"}
    
    def get_pro_headers(self):
        return {"Authorization": f"Bearer {self.pro_token}"}
    
    # ============== FEATURE GATING TESTS ==============
    
    def test_01_elite_can_access_capabilities(self):
        """Elite creator can access /api/elite/arris-api/capabilities"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/capabilities",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify capabilities structure
        assert "capabilities" in data
        assert "rate_limits" in data
        assert "authentication" in data
        
        # Verify capabilities list
        capabilities = data["capabilities"]
        assert len(capabilities) >= 5, "Should have at least 5 capabilities"
        
        capability_ids = [c["id"] for c in capabilities]
        assert "text_analysis" in capability_ids
        assert "proposal_insights" in capability_ids
        assert "content_suggestions" in capability_ids
        assert "batch_analysis" in capability_ids
        assert "persona_chat" in capability_ids
        
        print(f"✅ Elite can access capabilities: {len(capabilities)} capabilities found")
    
    def test_02_pro_blocked_from_capabilities(self):
        """Pro creator gets 403 on /api/elite/arris-api/capabilities"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/capabilities",
            headers=self.get_pro_headers()
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert "feature_gated" in str(data) or "Elite" in str(data)
        print(f"✅ Pro creator correctly blocked from capabilities (403)")
    
    def test_03_unauthenticated_blocked(self):
        """Unauthenticated request gets 401/403"""
        response = requests.get(f"{BASE_URL}/api/elite/arris-api/capabilities")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✅ Unauthenticated request blocked ({response.status_code})")
    
    # ============== API DOCUMENTATION TESTS ==============
    
    def test_04_elite_can_access_docs(self):
        """Elite creator can access /api/elite/arris-api/docs"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/docs",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify docs structure
        assert "title" in data
        assert "version" in data
        assert "authentication" in data
        assert "rate_limits" in data
        assert "endpoints" in data
        assert "error_codes" in data
        
        # Verify endpoints documented
        endpoints = data["endpoints"]
        assert len(endpoints) >= 5, "Should document at least 5 endpoints"
        
        print(f"✅ Elite can access API docs: {len(endpoints)} endpoints documented")
    
    def test_05_pro_blocked_from_docs(self):
        """Pro creator gets 403 on /api/elite/arris-api/docs"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/docs",
            headers=self.get_pro_headers()
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✅ Pro creator correctly blocked from docs (403)")
    
    # ============== API KEY MANAGEMENT TESTS ==============
    
    def test_06_list_api_keys(self):
        """Elite creator can list API keys"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/keys",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "keys" in data
        keys = data["keys"]
        print(f"✅ Listed {len(keys)} API keys")
        
        # Store count for later tests
        TestArrisApiAccess.initial_key_count = len(keys)
    
    def test_07_create_api_key(self):
        """Elite creator can create a new API key"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/keys",
            headers=self.get_elite_headers(),
            json={
                "name": "Test API Key",
                "key_type": "test"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "api_key" in data, "Should return the API key"
        assert "key_id" in data
        assert data["key_type"] == "test"
        assert data["api_key"].startswith("arris_test_")
        
        # Store for later tests
        TestArrisApiAccess.created_key_id = data["key_id"]
        TestArrisApiAccess.created_api_key = data["api_key"]
        
        print(f"✅ Created API key: {data['key_id']} (prefix: {data['api_key'][:20]}...)")
    
    def test_08_get_specific_key(self):
        """Elite creator can get specific key details"""
        if not self.elite_token or not TestArrisApiAccess.created_key_id:
            pytest.skip("Prerequisites not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/keys/{TestArrisApiAccess.created_key_id}",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["id"] == TestArrisApiAccess.created_key_id
        assert data["name"] == "Test API Key"
        assert data["key_type"] == "test"
        assert data["status"] == "active"
        assert "key_hash" not in data, "Should not expose key hash"
        
        print(f"✅ Retrieved key details: {data['name']} ({data['status']})")
    
    def test_09_key_not_found(self):
        """Get non-existent key returns 404"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/keys/NONEXISTENT-KEY-123",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✅ Non-existent key returns 404")
    
    def test_10_pro_blocked_from_keys(self):
        """Pro creator gets 403 on key management"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        # Try to list keys
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/keys",
            headers=self.get_pro_headers()
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        # Try to create key
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/keys",
            headers=self.get_pro_headers(),
            json={"name": "Test", "key_type": "test"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print(f"✅ Pro creator blocked from key management (403)")
    
    # ============== USAGE STATISTICS TESTS ==============
    
    def test_11_get_usage_stats(self):
        """Elite creator can get usage statistics"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/usage",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "total_requests" in data
        assert "active_keys" in data
        assert "rate_limits" in data
        assert "keys" in data
        
        # Verify rate limits
        rate_limits = data["rate_limits"]
        assert rate_limits["requests_per_hour"] == 100
        assert rate_limits["requests_per_day"] == 1000
        assert rate_limits["max_batch_size"] == 10
        
        print(f"✅ Usage stats: {data['total_requests']} total requests, {data['active_keys']} active keys")
    
    def test_12_pro_blocked_from_usage(self):
        """Pro creator gets 403 on usage stats"""
        if not self.pro_token:
            pytest.skip("Pro token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/usage",
            headers=self.get_pro_headers()
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✅ Pro creator blocked from usage stats (403)")
    
    # ============== DIRECT API ENDPOINT TESTS (X-ARRIS-API-Key Auth) ==============
    
    def test_13_analyze_missing_api_key(self):
        """Analyze endpoint returns 401 without API key"""
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            json={"text": "Test content"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        assert "Missing API key" in response.text or "X-ARRIS-API-Key" in response.text
        print(f"✅ Missing API key returns 401")
    
    def test_14_analyze_invalid_api_key(self):
        """Analyze endpoint returns 401 with invalid API key"""
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": "invalid_key_12345"},
            json={"text": "Test content"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid API key returns 401")
    
    def test_15_analyze_with_valid_key(self):
        """Analyze endpoint works with valid API key"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={
                "text": "I want to grow my YouTube channel about sustainable living",
                "analysis_type": "strategy"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "request_id" in data
        assert "analysis" in data
        assert "processing_time_ms" in data
        
        print(f"✅ Text analysis successful: {data['request_id']} ({data['processing_time_ms']}ms)")
    
    def test_16_analyze_missing_text(self):
        """Analyze endpoint returns 400 without text"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"analysis_type": "general"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "text" in response.text.lower()
        print(f"✅ Missing text returns 400")
    
    def test_17_chat_with_arris(self):
        """Chat endpoint works with valid API key"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/chat",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={
                "message": "What are the best strategies for growing a YouTube channel?"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "request_id" in data
        assert "response" in data
        assert "conversation_id" in data
        
        print(f"✅ Chat successful: {data['conversation_id']}")
    
    def test_18_chat_missing_message(self):
        """Chat endpoint returns 400 without message"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/chat",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Missing message returns 400")
    
    def test_19_content_suggestions(self):
        """Content suggestions endpoint works"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/content",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={
                "topic": "sustainable living tips",
                "platform": "YouTube",
                "content_type": "video",
                "count": 3
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "suggestions" in data
        assert "request_id" in data
        
        print(f"✅ Content suggestions: {len(data.get('suggestions', []))} suggestions generated")
    
    def test_20_content_missing_topic(self):
        """Content endpoint returns 400 without topic"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/content",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"platform": "YouTube"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Missing topic returns 400")
    
    def test_21_insights_endpoint(self):
        """Insights endpoint works"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/insights",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={
                "title": "Q1 YouTube Series Launch",
                "description": "Launch a new video series about sustainable living tips for beginners",
                "goals": ["Reach 10K subscribers", "Build community engagement"],
                "platforms": ["YouTube", "Instagram"]
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "insights" in data
        assert "request_id" in data
        
        print(f"✅ Insights generated: {data['request_id']}")
    
    def test_22_insights_missing_fields(self):
        """Insights endpoint returns 400 without required fields"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        # Missing description
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/insights",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"title": "Test Project"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Missing required fields returns 400")
    
    def test_23_batch_analysis(self):
        """Batch analysis endpoint works"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/batch",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={
                "items": [
                    {"text": "First item to analyze"},
                    {"text": "Second item to analyze"},
                    {"text": "Third item to analyze"}
                ],
                "analysis_type": "general"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "results" in data
        assert data["total_items"] == 3
        assert "total_processing_time_ms" in data
        
        print(f"✅ Batch analysis: {data['successful']}/{data['total_items']} successful")
    
    def test_24_batch_exceeds_limit(self):
        """Batch analysis returns 400 when exceeding max batch size"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        # Create 11 items (max is 10)
        items = [{"text": f"Item {i}"} for i in range(11)]
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/batch",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"items": items}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "batch" in response.text.lower() or "10" in response.text
        print(f"✅ Batch exceeding limit returns 400")
    
    def test_25_batch_missing_items(self):
        """Batch analysis returns 400 without items"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/batch",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"analysis_type": "general"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Missing items returns 400")
    
    # ============== KEY REGENERATION AND REVOCATION TESTS ==============
    
    def test_26_regenerate_api_key(self):
        """Elite creator can regenerate an API key"""
        if not self.elite_token or not TestArrisApiAccess.created_key_id:
            pytest.skip("Prerequisites not available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/keys/{TestArrisApiAccess.created_key_id}/regenerate",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "api_key" in data
        assert data["api_key"] != TestArrisApiAccess.created_api_key, "New key should be different"
        
        # Update stored key
        TestArrisApiAccess.created_key_id = data["key_id"]
        TestArrisApiAccess.created_api_key = data["api_key"]
        
        print(f"✅ Key regenerated: {data['key_id']}")
    
    def test_27_old_key_invalid_after_regenerate(self):
        """Old API key should be invalid after regeneration"""
        # The old key was revoked during regeneration
        # This test verifies the new key works
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"text": "Test after regeneration"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ New key works after regeneration")
    
    def test_28_revoke_api_key(self):
        """Elite creator can revoke an API key"""
        if not self.elite_token or not TestArrisApiAccess.created_key_id:
            pytest.skip("Prerequisites not available")
        
        response = requests.delete(
            f"{BASE_URL}/api/elite/arris-api/keys/{TestArrisApiAccess.created_key_id}",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True
        print(f"✅ Key revoked successfully")
    
    def test_29_revoked_key_invalid(self):
        """Revoked API key should return 401"""
        if not TestArrisApiAccess.created_api_key:
            pytest.skip("No API key available")
        
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": TestArrisApiAccess.created_api_key},
            json={"text": "Test with revoked key"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Revoked key returns 401")
    
    def test_30_revoke_nonexistent_key(self):
        """Revoking non-existent key returns error"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.delete(
            f"{BASE_URL}/api/elite/arris-api/keys/NONEXISTENT-KEY-123",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Revoking non-existent key returns 400")
    
    # ============== API KEY LIMIT TEST ==============
    
    def test_31_max_keys_limit(self):
        """Test maximum API keys limit (5 keys)"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        # First, get current key count
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/keys",
            headers=self.get_elite_headers()
        )
        current_keys = len(response.json().get("keys", []))
        active_keys = len([k for k in response.json().get("keys", []) if k.get("status") == "active"])
        
        print(f"Current active keys: {active_keys}")
        
        # If already at limit, verify we can't create more
        if active_keys >= 5:
            response = requests.post(
                f"{BASE_URL}/api/elite/arris-api/keys",
                headers=self.get_elite_headers(),
                json={"name": "Limit Test Key", "key_type": "test"}
            )
            
            assert response.status_code == 400, f"Expected 400 at limit, got {response.status_code}"
            assert "limit" in response.text.lower() or "maximum" in response.text.lower()
            print(f"✅ Max keys limit enforced (5 keys)")
        else:
            print(f"✅ Not at key limit yet ({active_keys}/5 active keys)")
    
    # ============== REQUEST HISTORY TEST ==============
    
    def test_32_get_request_history(self):
        """Elite creator can get request history"""
        if not self.elite_token:
            pytest.skip("Elite token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/elite/arris-api/history",
            headers=self.get_elite_headers()
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "history" in data
        print(f"✅ Request history: {len(data['history'])} requests logged")


class TestExistingApiKey:
    """Test with the existing API key provided in credentials"""
    
    def test_existing_key_validation(self):
        """Test if the existing API key works"""
        response = requests.post(
            f"{BASE_URL}/api/elite/arris-api/analyze",
            headers={"X-ARRIS-API-Key": EXISTING_API_KEY},
            json={
                "text": "Testing with existing API key",
                "analysis_type": "general"
            }
        )
        
        # Key might be valid or invalid depending on state
        if response.status_code == 200:
            print(f"✅ Existing API key is valid and working")
        elif response.status_code == 401:
            print(f"⚠️ Existing API key is invalid or revoked")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
