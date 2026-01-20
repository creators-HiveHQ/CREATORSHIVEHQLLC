"""
Test Elite Contact Us Flow
Tests the Elite plan inquiry submission, admin management, and webhook events.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
CREATOR_EMAIL = "emailtest@example.com"
CREATOR_PASSWORD = "testpassword"


class TestEliteContactFlow:
    """Test Elite Contact Us flow - submission, admin view, status updates"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.creator_token = None
        self.test_inquiry_id = None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.admin_token = response.json().get("access_token")
            return self.admin_token
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    def get_creator_token(self):
        """Get creator authentication token"""
        if self.creator_token:
            return self.creator_token
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": CREATOR_EMAIL,
            "password": CREATOR_PASSWORD
        })
        if response.status_code == 200:
            self.creator_token = response.json().get("access_token")
            return self.creator_token
        pytest.skip(f"Creator login failed: {response.status_code}")
    
    # ============== POST /api/elite/contact Tests ==============
    
    def test_elite_contact_requires_auth(self):
        """Test that elite contact endpoint requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/elite/contact", json={
            "message": "Test inquiry"
        })
        assert response.status_code == 403 or response.status_code == 401, \
            f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/elite/contact requires authentication")
    
    def test_elite_contact_requires_message(self):
        """Test that message field is required"""
        token = self.get_creator_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with empty message
        response = self.session.post(f"{BASE_URL}/api/elite/contact", 
            json={"message": ""},
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400 for empty message, got {response.status_code}"
        
        # Test with no message field
        response = self.session.post(f"{BASE_URL}/api/elite/contact", 
            json={"company_name": "Test Co"},
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400 for missing message, got {response.status_code}"
        print("✓ POST /api/elite/contact requires message field")
    
    def test_elite_contact_submit_success(self):
        """Test successful Elite inquiry submission"""
        token = self.get_creator_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        inquiry_data = {
            "message": "TEST_INQUIRY: I'm interested in the Elite plan for my content team.",
            "company_name": "TEST_Creator Studios",
            "team_size": "6-20"
        }
        
        response = self.session.post(f"{BASE_URL}/api/elite/contact", 
            json=inquiry_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "inquiry_id" in data, "Response should contain inquiry_id"
        assert data["inquiry_id"].startswith("EI-"), "Inquiry ID should start with EI-"
        assert "message" in data, "Response should contain success message"
        assert "sales_email_sent" in data, "Response should indicate if sales email was sent"
        assert "confirmation_email_sent" in data, "Response should indicate if confirmation email was sent"
        
        # Store inquiry ID for later tests
        self.__class__.test_inquiry_id = data["inquiry_id"]
        
        print(f"✓ POST /api/elite/contact successful - Inquiry ID: {data['inquiry_id']}")
        print(f"  - Sales email sent: {data['sales_email_sent']}")
        print(f"  - Confirmation email sent: {data['confirmation_email_sent']}")
    
    def test_elite_contact_minimal_data(self):
        """Test Elite inquiry with only required message field"""
        token = self.get_creator_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.post(f"{BASE_URL}/api/elite/contact", 
            json={"message": "TEST_MINIMAL: Just interested in Elite features."},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "inquiry_id" in data
        print("✓ POST /api/elite/contact works with minimal data (message only)")
    
    # ============== GET /api/elite/inquiries Tests (Admin) ==============
    
    def test_elite_inquiries_requires_admin(self):
        """Test that getting inquiries requires admin authentication"""
        # Test without auth
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        # Test with creator token (should fail - admin only)
        creator_token = self.get_creator_token()
        headers = {"Authorization": f"Bearer {creator_token}"}
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries", headers=headers)
        assert response.status_code in [401, 403], f"Creator should not access admin endpoint, got {response.status_code}"
        
        print("✓ GET /api/elite/inquiries requires admin authentication")
    
    def test_elite_inquiries_admin_access(self):
        """Test admin can view all Elite inquiries"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "inquiries" in data, "Response should contain inquiries list"
        assert "stats" in data, "Response should contain stats"
        assert isinstance(data["inquiries"], list), "Inquiries should be a list"
        
        # Verify stats structure
        stats = data["stats"]
        assert "total" in stats, "Stats should contain total"
        assert "pending" in stats, "Stats should contain pending count"
        assert "contacted" in stats, "Stats should contain contacted count"
        assert "converted" in stats, "Stats should contain converted count"
        
        print(f"✓ GET /api/elite/inquiries returns {len(data['inquiries'])} inquiries")
        print(f"  - Stats: Total={stats['total']}, Pending={stats['pending']}, Contacted={stats['contacted']}, Converted={stats['converted']}")
    
    def test_elite_inquiries_filter_by_status(self):
        """Test filtering inquiries by status"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries?status=pending", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # All returned inquiries should have pending status
        for inquiry in data["inquiries"]:
            assert inquiry.get("status") == "pending", f"Expected pending status, got {inquiry.get('status')}"
        
        print(f"✓ GET /api/elite/inquiries?status=pending filters correctly ({len(data['inquiries'])} pending)")
    
    def test_elite_inquiry_structure(self):
        """Test that inquiry documents have correct structure"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        if len(data["inquiries"]) > 0:
            inquiry = data["inquiries"][0]
            
            # Verify required fields
            required_fields = ["id", "creator_id", "creator_email", "creator_name", "message", "status", "created_at"]
            for field in required_fields:
                assert field in inquiry, f"Inquiry should contain {field}"
            
            # Verify ID format
            assert inquiry["id"].startswith("EI-"), "Inquiry ID should start with EI-"
            
            # Verify status is valid
            valid_statuses = ["pending", "contacted", "converted", "declined"]
            assert inquiry["status"] in valid_statuses, f"Invalid status: {inquiry['status']}"
            
            print("✓ Elite inquiry document has correct structure")
            print(f"  - Fields: {list(inquiry.keys())}")
        else:
            print("⚠ No inquiries found to verify structure")
    
    # ============== PATCH /api/elite/inquiries/{id} Tests (Admin) ==============
    
    def test_elite_inquiry_update_requires_admin(self):
        """Test that updating inquiry requires admin authentication"""
        response = self.session.patch(f"{BASE_URL}/api/elite/inquiries/EI-test123", 
            json={"status": "contacted"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ PATCH /api/elite/inquiries/{id} requires admin authentication")
    
    def test_elite_inquiry_update_status(self):
        """Test admin can update inquiry status"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # First get an inquiry to update
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        if len(data["inquiries"]) == 0:
            pytest.skip("No inquiries available to update")
        
        # Find a test inquiry or use the first one
        inquiry_id = None
        for inq in data["inquiries"]:
            if "TEST_" in inq.get("message", "") or "TEST_" in inq.get("company_name", ""):
                inquiry_id = inq["id"]
                break
        
        if not inquiry_id:
            inquiry_id = data["inquiries"][0]["id"]
        
        # Update status to contacted
        response = self.session.patch(f"{BASE_URL}/api/elite/inquiries/{inquiry_id}", 
            json={"status": "contacted", "notes": "TEST: Contacted via email"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        update_data = response.json()
        assert "message" in update_data, "Response should contain success message"
        assert update_data.get("inquiry_id") == inquiry_id, "Response should contain inquiry_id"
        
        print(f"✓ PATCH /api/elite/inquiries/{inquiry_id} updated status to 'contacted'")
    
    def test_elite_inquiry_update_invalid_status(self):
        """Test that invalid status is rejected"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get an inquiry ID
        response = self.session.get(f"{BASE_URL}/api/elite/inquiries", headers=headers)
        if response.status_code != 200 or len(response.json().get("inquiries", [])) == 0:
            pytest.skip("No inquiries available")
        
        inquiry_id = response.json()["inquiries"][0]["id"]
        
        # Try invalid status
        response = self.session.patch(f"{BASE_URL}/api/elite/inquiries/{inquiry_id}", 
            json={"status": "invalid_status"},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid status, got {response.status_code}"
        print("✓ PATCH /api/elite/inquiries/{id} rejects invalid status")
    
    def test_elite_inquiry_update_not_found(self):
        """Test updating non-existent inquiry returns 404"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.patch(f"{BASE_URL}/api/elite/inquiries/EI-nonexistent123", 
            json={"status": "contacted"},
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PATCH /api/elite/inquiries/{id} returns 404 for non-existent inquiry")
    
    # ============== Webhook Event Test ==============
    
    def test_elite_inquiry_webhook_event(self):
        """Test that webhook event is emitted for Elite inquiry"""
        token = self.get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check webhook events for elite inquiry
        response = self.session.get(f"{BASE_URL}/api/webhooks/events?event_type=elite_inquiry_submitted", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            # Look for recent elite inquiry events
            elite_events = [e for e in events if e.get("event_type") == "elite_inquiry_submitted"]
            
            if len(elite_events) > 0:
                print(f"✓ Webhook events found for elite_inquiry_submitted: {len(elite_events)} events")
                # Verify event structure
                event = elite_events[0]
                assert "payload" in event, "Event should have payload"
                payload = event.get("payload", {})
                assert "inquiry_id" in payload or "creator_email" in payload, "Payload should contain inquiry details"
            else:
                print("⚠ No elite_inquiry_submitted webhook events found (may be expected if no recent submissions)")
        else:
            print(f"⚠ Could not verify webhook events: {response.status_code}")


class TestEliteContactDataPersistence:
    """Test that Elite inquiries are properly persisted in database"""
    
    def test_inquiry_persisted_after_creation(self):
        """Test that created inquiry can be retrieved"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as creator
        response = session.post(f"{BASE_URL}/api/creators/login", json={
            "email": CREATOR_EMAIL,
            "password": CREATOR_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Creator login failed")
        
        creator_token = response.json().get("access_token")
        
        # Create inquiry
        unique_message = f"TEST_PERSIST_{int(time.time())}: Testing data persistence"
        response = session.post(f"{BASE_URL}/api/elite/contact", 
            json={"message": unique_message, "company_name": "Persistence Test Co"},
            headers={"Authorization": f"Bearer {creator_token}"}
        )
        
        assert response.status_code == 200
        inquiry_id = response.json().get("inquiry_id")
        
        # Login as admin and verify inquiry exists
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = response.json().get("access_token")
        
        # Get inquiries and find our test inquiry
        response = session.get(f"{BASE_URL}/api/elite/inquiries", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        inquiries = response.json().get("inquiries", [])
        
        found = False
        for inq in inquiries:
            if inq.get("id") == inquiry_id:
                found = True
                assert inq.get("message") == unique_message, "Message should match"
                assert inq.get("company_name") == "Persistence Test Co", "Company name should match"
                assert inq.get("status") == "pending", "Initial status should be pending"
                break
        
        assert found, f"Created inquiry {inquiry_id} should be retrievable"
        print(f"✓ Inquiry {inquiry_id} persisted and retrieved successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
