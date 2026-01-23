"""
Test Suite for ARRIS Persona System (Phase 4 Module E - Task E1)
Tests Custom ARRIS Personas for Elite creators

Features tested:
- GET /api/elite/personas - Get all personas (default + custom)
- GET /api/elite/personas/options - Get customization options
- GET /api/elite/personas/active - Get active persona
- GET /api/elite/personas/{id} - Get specific persona
- POST /api/elite/personas - Create custom persona
- PATCH /api/elite/personas/{id} - Update custom persona
- DELETE /api/elite/personas/{id} - Delete custom persona
- POST /api/elite/personas/{id}/activate - Activate persona
- POST /api/elite/personas/{id}/test - Test persona
- GET /api/elite/personas/analytics/summary - Get analytics
- Feature gating (403 for non-Elite users)
- Default personas protection (cannot delete/modify)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ELITE_CREATOR = {"email": "elitetest@hivehq.com", "password": "testpassword123"}
PRO_CREATOR = {"email": "protest@hivehq.com", "password": "testpassword"}
ADMIN_USER = {"email": "admin@hivehq.com", "password": "admin123"}

# Default persona IDs
DEFAULT_PERSONA_IDS = [
    "PERSONA-DEFAULT-PRO",  # Professional
    "PERSONA-DEFAULT-FRI",  # Friendly
    "PERSONA-DEFAULT-ANA",  # Analytical
    "PERSONA-DEFAULT-CRE",  # Creative
    "PERSONA-DEFAULT-COA",  # Coach
]


class TestSetup:
    """Setup and helper methods for tests"""
    
    @staticmethod
    def get_elite_token():
        """Get authentication token for Elite creator"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_CREATOR)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_pro_token():
        """Get authentication token for Pro creator"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_admin_token():
        """Get authentication token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


class TestFeatureGating:
    """Test that ARRIS Personas are properly gated to Elite users"""
    
    def test_elite_user_can_access_personas(self):
        """Elite user should be able to access personas endpoint"""
        token = TestSetup.get_elite_token()
        assert token is not None, "Failed to get Elite token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "default_personas" in data
        assert "custom_personas" in data
        print(f"✓ Elite user can access personas - {len(data['default_personas'])} default, {len(data['custom_personas'])} custom")
    
    def test_pro_user_gets_403(self):
        """Pro user should get 403 Forbidden for personas endpoint"""
        token = TestSetup.get_pro_token()
        assert token is not None, "Failed to get Pro token"
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Pro user correctly gets 403 for personas endpoint")
    
    def test_unauthenticated_gets_401(self):
        """Unauthenticated request should get 401"""
        response = requests.get(f"{BASE_URL}/api/elite/personas")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")


class TestGetAllPersonas:
    """Test GET /api/elite/personas endpoint"""
    
    def test_returns_default_personas(self):
        """Should return all 5 default personas"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        default_personas = data.get("default_personas", [])
        
        assert len(default_personas) == 5, f"Expected 5 default personas, got {len(default_personas)}"
        
        # Verify all default persona IDs are present
        persona_ids = [p["id"] for p in default_personas]
        for expected_id in DEFAULT_PERSONA_IDS:
            assert expected_id in persona_ids, f"Missing default persona: {expected_id}"
        
        print(f"✓ All 5 default personas returned: {[p['name'] for p in default_personas]}")
    
    def test_default_personas_have_required_fields(self):
        """Default personas should have all required fields"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        data = response.json()
        
        required_fields = [
            "id", "name", "description", "tone", "communication_style",
            "response_length", "primary_focus_areas", "emoji_usage",
            "custom_greeting", "signature_phrase", "personality_traits",
            "is_default", "is_system", "icon"
        ]
        
        for persona in data["default_personas"]:
            for field in required_fields:
                assert field in persona, f"Missing field '{field}' in persona {persona.get('name')}"
            assert persona["is_default"] == True
            assert persona["is_system"] == True
        
        print("✓ All default personas have required fields")
    
    def test_returns_active_persona_id(self):
        """Should return the active persona ID"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        data = response.json()
        
        assert "active_persona_id" in data
        assert data["active_persona_id"] is not None
        print(f"✓ Active persona ID returned: {data['active_persona_id']}")


class TestGetPersonaOptions:
    """Test GET /api/elite/personas/options endpoint"""
    
    def test_returns_all_options(self):
        """Should return all customization options"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas/options", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all option categories are present
        assert "tones" in data
        assert "communication_styles" in data
        assert "focus_areas" in data
        assert "response_lengths" in data
        assert "emoji_options" in data
        assert "icon_options" in data
        
        # Verify expected values
        expected_tones = ["professional", "friendly", "analytical", "creative", "motivational", "direct", "empathetic"]
        for tone in expected_tones:
            assert tone in data["tones"], f"Missing tone: {tone}"
        
        expected_styles = ["detailed", "concise", "conversational", "structured", "storytelling", "socratic"]
        for style in expected_styles:
            assert style in data["communication_styles"], f"Missing style: {style}"
        
        print(f"✓ Options returned - {len(data['tones'])} tones, {len(data['focus_areas'])} focus areas")


class TestGetActivePersona:
    """Test GET /api/elite/personas/active endpoint"""
    
    def test_returns_active_persona(self):
        """Should return the currently active persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas/active", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "is_active" in data
        assert data["is_active"] == True
        
        print(f"✓ Active persona: {data['name']} ({data['id']})")


class TestGetSpecificPersona:
    """Test GET /api/elite/personas/{id} endpoint"""
    
    def test_get_default_persona_by_id(self):
        """Should return a specific default persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get Professional persona
        response = requests.get(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "PERSONA-DEFAULT-PRO"
        assert data["name"] == "Professional ARRIS"
        assert data["tone"] == "professional"
        
        print(f"✓ Retrieved default persona: {data['name']}")
    
    def test_get_nonexistent_persona_returns_404(self):
        """Should return 404 for non-existent persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas/PERSONA-NONEXISTENT", headers=headers)
        assert response.status_code == 404
        
        print("✓ Non-existent persona returns 404")


class TestCreatePersona:
    """Test POST /api/elite/personas endpoint"""
    
    created_persona_id = None
    
    def test_create_custom_persona(self):
        """Should create a new custom persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        persona_data = {
            "name": "TEST Growth Expert",
            "description": "Focused on audience growth and engagement strategies",
            "tone": "motivational",
            "communication_style": "structured",
            "response_length": "detailed",
            "primary_focus_areas": ["growth", "engagement", "content"],
            "emoji_usage": "moderate",
            "custom_greeting": "Ready to grow your audience! What's our focus today?",
            "signature_phrase": "Growth is a journey, not a destination.",
            "personality_traits": ["encouraging", "strategic", "data-informed"],
            "icon": "rocket"
        }
        
        response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=persona_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST Growth Expert"
        assert data["tone"] == "motivational"
        assert data["is_default"] == False
        assert data["is_system"] == False
        
        TestCreatePersona.created_persona_id = data["id"]
        print(f"✓ Created custom persona: {data['name']} ({data['id']})")
    
    def test_create_persona_requires_name(self):
        """Should fail if name is not provided"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        persona_data = {
            "description": "No name provided",
            "tone": "friendly"
        }
        
        response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=persona_data)
        assert response.status_code == 400
        
        print("✓ Create persona without name returns 400")
    
    def test_create_persona_name_max_length(self):
        """Should fail if name exceeds 50 characters"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        persona_data = {
            "name": "A" * 51,  # 51 characters
            "tone": "friendly"
        }
        
        response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=persona_data)
        assert response.status_code == 400
        
        print("✓ Create persona with name > 50 chars returns 400")
    
    def test_pro_user_cannot_create_persona(self):
        """Pro user should get 403 when trying to create persona"""
        token = TestSetup.get_pro_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        persona_data = {
            "name": "Should Fail",
            "tone": "friendly"
        }
        
        response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=persona_data)
        assert response.status_code == 403
        
        print("✓ Pro user cannot create persona (403)")


class TestUpdatePersona:
    """Test PATCH /api/elite/personas/{id} endpoint"""
    
    def test_update_custom_persona(self):
        """Should update a custom persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # First create a persona to update
        create_data = {
            "name": "TEST Update Target",
            "tone": "friendly"
        }
        create_response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=create_data)
        assert create_response.status_code == 200
        persona_id = create_response.json()["id"]
        
        # Update the persona
        update_data = {
            "name": "TEST Updated Name",
            "tone": "analytical",
            "description": "Updated description"
        }
        
        response = requests.patch(f"{BASE_URL}/api/elite/personas/{persona_id}", headers=headers, json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST Updated Name"
        assert data["tone"] == "analytical"
        assert data["description"] == "Updated description"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/elite/personas/{persona_id}", headers=headers)
        
        print(f"✓ Updated custom persona successfully")
    
    def test_cannot_update_default_persona(self):
        """Should not be able to update default/system personas"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        update_data = {
            "name": "Hacked Professional"
        }
        
        response = requests.patch(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO", headers=headers, json=update_data)
        assert response.status_code == 400
        
        print("✓ Cannot update default persona (400)")


class TestDeletePersona:
    """Test DELETE /api/elite/personas/{id} endpoint"""
    
    def test_delete_custom_persona(self):
        """Should delete a custom persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # First create a persona to delete
        create_data = {
            "name": "TEST Delete Target",
            "tone": "friendly"
        }
        create_response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=create_data)
        assert create_response.status_code == 200
        persona_id = create_response.json()["id"]
        
        # Delete the persona
        response = requests.delete(f"{BASE_URL}/api/elite/personas/{persona_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/elite/personas/{persona_id}", headers=headers)
        assert get_response.status_code == 404
        
        print(f"✓ Deleted custom persona successfully")
    
    def test_cannot_delete_default_persona(self):
        """Should not be able to delete default/system personas"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.delete(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO", headers=headers)
        assert response.status_code == 400
        
        print("✓ Cannot delete default persona (400)")


class TestActivatePersona:
    """Test POST /api/elite/personas/{id}/activate endpoint"""
    
    def test_activate_default_persona(self):
        """Should activate a default persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Activate Friendly persona
        response = requests.post(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-FRI/activate", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["active_persona"]["id"] == "PERSONA-DEFAULT-FRI"
        assert data["active_persona"]["name"] == "Friendly ARRIS"
        
        print(f"✓ Activated default persona: {data['active_persona']['name']}")
    
    def test_activate_custom_persona(self):
        """Should activate a custom persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Create a custom persona
        create_data = {
            "name": "TEST Activate Target",
            "tone": "creative"
        }
        create_response = requests.post(f"{BASE_URL}/api/elite/personas", headers=headers, json=create_data)
        assert create_response.status_code == 200
        persona_id = create_response.json()["id"]
        
        # Activate it
        response = requests.post(f"{BASE_URL}/api/elite/personas/{persona_id}/activate", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["active_persona"]["id"] == persona_id
        
        # Verify it's active
        active_response = requests.get(f"{BASE_URL}/api/elite/personas/active", headers=headers)
        assert active_response.json()["id"] == persona_id
        
        # Cleanup - switch back to default and delete
        requests.post(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO/activate", headers=headers)
        requests.delete(f"{BASE_URL}/api/elite/personas/{persona_id}", headers=headers)
        
        print(f"✓ Activated custom persona successfully")
    
    def test_activate_nonexistent_persona_fails(self):
        """Should fail when activating non-existent persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/elite/personas/PERSONA-NONEXISTENT/activate", headers=headers)
        assert response.status_code == 400
        
        print("✓ Activating non-existent persona returns 400")


class TestTestPersona:
    """Test POST /api/elite/personas/{id}/test endpoint"""
    
    def test_test_persona_returns_system_prompt(self):
        """Should return system prompt preview for persona"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        test_message = "How can I grow my YouTube channel?"
        response = requests.post(
            f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO/test?test_message={test_message}",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "persona" in data
        assert "system_prompt_preview" in data
        assert "test_message" in data
        assert data["test_message"] == test_message
        
        # Verify system prompt contains persona characteristics
        prompt = data["system_prompt_preview"]
        assert "Professional ARRIS" in prompt
        assert "professional" in prompt.lower()
        
        print(f"✓ Test persona returns system prompt preview ({len(prompt)} chars)")
    
    def test_test_persona_requires_message(self):
        """Should require test_message parameter"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO/test", headers=headers)
        assert response.status_code == 422  # Validation error
        
        print("✓ Test persona requires message parameter")


class TestPersonaAnalytics:
    """Test GET /api/elite/personas/analytics/summary endpoint"""
    
    def test_get_analytics_summary(self):
        """Should return persona usage analytics"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/elite/personas/analytics/summary", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "active_persona" in data
        assert "custom_personas_count" in data
        assert "custom_personas" in data
        
        print(f"✓ Analytics summary returned - {data['custom_personas_count']} custom personas")


class TestSystemPromptGeneration:
    """Test that system prompts are generated correctly"""
    
    def test_professional_persona_prompt(self):
        """Professional persona should generate appropriate prompt"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO/test?test_message=test",
            headers=headers
        )
        data = response.json()
        prompt = data["system_prompt_preview"]
        
        # Check for professional characteristics
        assert "formal" in prompt.lower() or "business" in prompt.lower()
        assert "strategy" in prompt.lower() or "monetization" in prompt.lower()
        
        print("✓ Professional persona generates appropriate prompt")
    
    def test_creative_persona_prompt(self):
        """Creative persona should generate appropriate prompt"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-CRE/test?test_message=test",
            headers=headers
        )
        data = response.json()
        prompt = data["system_prompt_preview"]
        
        # Check for creative characteristics
        assert "creative" in prompt.lower() or "imaginative" in prompt.lower()
        assert "emoji" in prompt.lower()  # Creative uses frequent emojis
        
        print("✓ Creative persona generates appropriate prompt")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_personas(self):
        """Clean up any TEST_ prefixed personas"""
        token = TestSetup.get_elite_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all personas
        response = requests.get(f"{BASE_URL}/api/elite/personas", headers=headers)
        if response.status_code == 200:
            data = response.json()
            for persona in data.get("custom_personas", []):
                if persona["name"].startswith("TEST"):
                    requests.delete(f"{BASE_URL}/api/elite/personas/{persona['id']}", headers=headers)
                    print(f"  Cleaned up: {persona['name']}")
        
        # Reset to Professional persona
        requests.post(f"{BASE_URL}/api/elite/personas/PERSONA-DEFAULT-PRO/activate", headers=headers)
        
        print("✓ Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
