"""
ARRIS Voice Interaction Feature Tests
Tests for voice endpoints: status, speak, transcribe, query, voices
Feature-gated to Premium/Elite tiers
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PREMIUM_USER = {"email": "premiumtest@hivehq.com", "password": "testpassword123"}
PRO_USER = {"email": "protest@hivehq.com", "password": "testpassword"}


class TestArrisVoiceFeature:
    """Test ARRIS Voice Interaction endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_token(self, email, password):
        """Get authentication token for a user"""
        response = self.session.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_auth_headers(self, token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    # ============== Voice Status Endpoint Tests ==============
    
    def test_voice_status_requires_auth(self):
        """Test that voice status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/voice/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Voice status requires authentication")
    
    def test_voice_status_premium_user_enabled(self):
        """Test that Premium user gets enabled=true for voice status"""
        token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Premium user login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/voice/status",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("enabled") == True, f"Expected enabled=True for Premium user, got {data}"
        assert "voices" in data, "Expected voices list in response"
        assert "default_voice" in data, "Expected default_voice in response"
        print(f"✅ Premium user voice status: enabled={data.get('enabled')}, voices={len(data.get('voices', []))}")
    
    def test_voice_status_pro_user_disabled(self):
        """Test that Pro user gets enabled=false for voice status"""
        token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Pro user login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/voice/status",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("enabled") == False, f"Expected enabled=False for Pro user, got {data}"
        assert "upgrade_url" in data, "Expected upgrade_url in response for non-Premium user"
        print(f"✅ Pro user voice status: enabled={data.get('enabled')}, message={data.get('message')}")
    
    # ============== Voice Speak (TTS) Endpoint Tests ==============
    
    def test_voice_speak_requires_auth(self):
        """Test that speak endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/arris/voice/speak?text=Hello")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Voice speak requires authentication")
    
    def test_voice_speak_pro_user_forbidden(self):
        """Test that Pro user gets 403 on speak endpoint"""
        token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Pro user login failed")
        
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/speak?text=Hello%20world",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 403, f"Expected 403 for Pro user, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated", f"Expected feature_gated error, got {detail}"
        print(f"✅ Pro user correctly blocked from speak endpoint: {detail.get('message')}")
    
    def test_voice_speak_premium_user_success(self):
        """Test that Premium user can use speak endpoint"""
        token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Premium user login failed")
        
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/speak?text=Hello%20from%20ARRIS&voice=nova&speed=1.0&format=mp3",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert "audio_base64" in data, "Expected audio_base64 in response"
        assert data.get("audio_format") == "mp3", f"Expected mp3 format, got {data.get('audio_format')}"
        assert data.get("voice") == "nova", f"Expected nova voice, got {data.get('voice')}"
        
        # Verify base64 is valid
        try:
            audio_bytes = base64.b64decode(data["audio_base64"])
            assert len(audio_bytes) > 0, "Audio data should not be empty"
            print(f"✅ Premium user TTS success: {len(audio_bytes)} bytes, format={data.get('audio_format')}, voice={data.get('voice')}")
        except Exception as e:
            pytest.fail(f"Invalid base64 audio data: {e}")
    
    def test_voice_speak_invalid_voice(self):
        """Test that invalid voice returns 400"""
        token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Premium user login failed")
        
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/speak?text=Hello&voice=invalid_voice",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 400, f"Expected 400 for invalid voice, got {response.status_code}"
        print("✅ Invalid voice correctly rejected with 400")
    
    def test_voice_speak_invalid_format(self):
        """Test that invalid format returns 400"""
        token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Premium user login failed")
        
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/speak?text=Hello&format=invalid_format",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 400, f"Expected 400 for invalid format, got {response.status_code}"
        print("✅ Invalid format correctly rejected with 400")
    
    # ============== Voice Transcribe (STT) Endpoint Tests ==============
    
    def test_voice_transcribe_requires_auth(self):
        """Test that transcribe endpoint requires authentication"""
        # Create a minimal audio file for testing
        files = {"audio": ("test.webm", b"fake audio data", "audio/webm")}
        response = requests.post(f"{BASE_URL}/api/arris/voice/transcribe", files=files)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Voice transcribe requires authentication")
    
    def test_voice_transcribe_pro_user_forbidden(self):
        """Test that Pro user gets 403 on transcribe endpoint"""
        token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Pro user login failed")
        
        files = {"audio": ("test.webm", b"fake audio data", "audio/webm")}
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/transcribe",
            headers=self.get_auth_headers(token),
            files=files
        )
        assert response.status_code == 403, f"Expected 403 for Pro user, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated", f"Expected feature_gated error, got {detail}"
        print(f"✅ Pro user correctly blocked from transcribe endpoint: {detail.get('message')}")
    
    # ============== Voice Query Endpoint Tests ==============
    
    def test_voice_query_requires_auth(self):
        """Test that voice query endpoint requires authentication"""
        files = {"audio": ("test.webm", b"fake audio data", "audio/webm")}
        response = requests.post(f"{BASE_URL}/api/arris/voice/query", files=files)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Voice query requires authentication")
    
    def test_voice_query_pro_user_forbidden(self):
        """Test that Pro user gets 403 on voice query endpoint"""
        token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Pro user login failed")
        
        files = {"audio": ("test.webm", b"fake audio data", "audio/webm")}
        response = requests.post(
            f"{BASE_URL}/api/arris/voice/query",
            headers=self.get_auth_headers(token),
            files=files
        )
        assert response.status_code == 403, f"Expected 403 for Pro user, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "feature_gated", f"Expected feature_gated error, got {detail}"
        print(f"✅ Pro user correctly blocked from voice query endpoint: {detail.get('message')}")
    
    # ============== Voice Voices Endpoint Tests ==============
    
    def test_voices_list_requires_auth(self):
        """Test that voices list endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/voice/voices")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Voices list requires authentication")
    
    def test_voices_list_available_to_all_authenticated(self):
        """Test that voices list is available to all authenticated users (for preview)"""
        # Test with Pro user (should work)
        token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not token:
            pytest.skip("Pro user login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/voice/voices",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "voices" in data, "Expected voices list in response"
        assert "default" in data, "Expected default voice in response"
        assert len(data["voices"]) > 0, "Expected at least one voice"
        
        # Verify voice structure
        voice = data["voices"][0]
        assert "id" in voice, "Voice should have id"
        assert "name" in voice, "Voice should have name"
        assert "description" in voice, "Voice should have description"
        
        print(f"✅ Voices list available to Pro user: {len(data['voices'])} voices, default={data['default']}")
    
    def test_voices_list_premium_user(self):
        """Test that Premium user can also access voices list"""
        token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not token:
            pytest.skip("Premium user login failed")
        
        response = requests.get(
            f"{BASE_URL}/api/arris/voice/voices",
            headers=self.get_auth_headers(token)
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "voices" in data, "Expected voices list in response"
        
        # Verify expected voices are present
        voice_ids = [v["id"] for v in data["voices"]]
        expected_voices = ["nova", "alloy", "echo", "fable", "shimmer"]
        for expected in expected_voices:
            assert expected in voice_ids, f"Expected voice '{expected}' in list"
        
        print(f"✅ Premium user voices list: {voice_ids}")


class TestArrisVoiceFeatureGating:
    """Test feature gating for different user tiers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        
    def get_token(self, email, password):
        """Get authentication token for a user"""
        response = self.session.post(
            f"{BASE_URL}/api/creators/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_auth_headers(self, token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_feature_gating_consistency(self):
        """Test that feature gating is consistent across all voice endpoints"""
        pro_token = self.get_token(PRO_USER["email"], PRO_USER["password"])
        if not pro_token:
            pytest.skip("Pro user login failed")
        
        headers = self.get_auth_headers(pro_token)
        
        # All these endpoints should return 403 for Pro user
        endpoints_to_test = [
            ("POST", "/api/arris/voice/speak?text=Hello"),
            ("POST", "/api/arris/voice/transcribe"),
            ("POST", "/api/arris/voice/query"),
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "POST" and "transcribe" in endpoint or "query" in endpoint:
                files = {"audio": ("test.webm", b"fake audio data", "audio/webm")}
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, files=files)
            else:
                response = requests.request(method, f"{BASE_URL}{endpoint}", headers=headers)
            
            assert response.status_code == 403, f"Expected 403 for {method} {endpoint}, got {response.status_code}"
            
            data = response.json()
            detail = data.get("detail", {})
            assert detail.get("error") == "feature_gated", f"Expected feature_gated for {endpoint}"
            assert "premium" in detail.get("required_tier", "").lower(), f"Expected premium tier requirement for {endpoint}"
        
        print("✅ Feature gating consistent across all voice endpoints for Pro user")
    
    def test_premium_user_has_full_access(self):
        """Test that Premium user has access to all voice endpoints"""
        premium_token = self.get_token(PREMIUM_USER["email"], PREMIUM_USER["password"])
        if not premium_token:
            pytest.skip("Premium user login failed")
        
        headers = self.get_auth_headers(premium_token)
        
        # Status should return enabled=True
        status_response = requests.get(f"{BASE_URL}/api/arris/voice/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json().get("enabled") == True
        
        # Speak should work
        speak_response = requests.post(
            f"{BASE_URL}/api/arris/voice/speak?text=Test",
            headers=headers
        )
        assert speak_response.status_code == 200
        assert speak_response.json().get("success") == True
        
        # Voices should work
        voices_response = requests.get(f"{BASE_URL}/api/arris/voice/voices", headers=headers)
        assert voices_response.status_code == 200
        assert "voices" in voices_response.json()
        
        print("✅ Premium user has full access to voice endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
