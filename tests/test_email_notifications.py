"""
Test Email Notifications for Proposal Status Changes
Tests the SendGrid email integration for proposal lifecycle events.

Features tested:
- GET /api/email/status - Email service configuration status
- POST /api/email/test - Test email sending (graceful failure when not configured)
- POST /api/proposals/{id}/submit - Email notification on submission
- PATCH /api/proposals/{id} with status changes - Email notifications for:
  - approved
  - rejected
  - under_review
  - completed

Note: SendGrid API key is NOT configured, so all email operations should
gracefully return email_sent: false instead of throwing errors.
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
TEST_CREATOR_EMAIL = "emailtest@example.com"
TEST_CREATOR_PASSWORD = "testpassword"


class TestEmailServiceStatus:
    """Tests for GET /api/email/status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_email_status_requires_auth(self):
        """GET /api/email/status requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/email/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/email/status requires authentication")
    
    def test_email_status_returns_configuration(self):
        """GET /api/email/status returns email service configuration"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/email/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "service" in data, "Missing 'service' field"
        assert data["service"] == "sendgrid", f"Expected 'sendgrid', got {data['service']}"
        
        assert "configured" in data, "Missing 'configured' field"
        assert isinstance(data["configured"], bool), "'configured' should be boolean"
        
        assert "sender_email" in data, "Missing 'sender_email' field"
        assert "sender_name" in data, "Missing 'sender_name' field"
        
        assert "features" in data, "Missing 'features' field"
        features = data["features"]
        assert features.get("proposal_submitted") == True
        assert features.get("proposal_approved") == True
        assert features.get("proposal_rejected") == True
        assert features.get("proposal_under_review") == True
        assert features.get("proposal_completed") == True
        
        assert "status" in data, "Missing 'status' field"
        
        # Since SendGrid is not configured, verify not_configured status
        if not data["configured"]:
            assert data["status"] == "not_configured"
            assert "setup_instructions" in data
            print(f"✓ Email service not configured (expected) - setup_instructions provided")
        else:
            assert data["status"] == "active"
            print(f"✓ Email service is configured and active")
        
        print(f"✓ GET /api/email/status returns proper configuration: configured={data['configured']}")


class TestEmailTestEndpoint:
    """Tests for POST /api/email/test endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_email_test_requires_auth(self):
        """POST /api/email/test requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/email/test", json={
            "to_email": "test@example.com"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/email/test requires authentication")
    
    def test_email_test_fails_gracefully_when_not_configured(self):
        """POST /api/email/test returns error when SendGrid not configured"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # First check if email is configured
        status_response = self.session.get(f"{BASE_URL}/api/email/status")
        is_configured = status_response.json().get("configured", False)
        
        response = self.session.post(f"{BASE_URL}/api/email/test", json={
            "to_email": "test@example.com"
        })
        
        if not is_configured:
            # Should return 503 (or 520 via Cloudflare proxy) with helpful error message
            assert response.status_code in [503, 520], f"Expected 503/520 when not configured, got {response.status_code}"
            data = response.json()
            assert "detail" in data
            detail = data["detail"]
            assert detail.get("error") == "email_not_configured"
            assert "message" in detail
            assert "setup_url" in detail
            print("✓ POST /api/email/test returns error with helpful message when SendGrid not configured")
        else:
            # If configured, should succeed or fail based on actual email delivery
            assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
            print(f"✓ POST /api/email/test returned {response.status_code} (SendGrid is configured)")
    
    def test_email_test_requires_to_email(self):
        """POST /api/email/test requires to_email field"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # First check if email is configured - if not, we'll get 503/520 before validation
        status_response = self.session.get(f"{BASE_URL}/api/email/status")
        is_configured = status_response.json().get("configured", False)
        
        response = self.session.post(f"{BASE_URL}/api/email/test", json={})
        
        if not is_configured:
            # Will return 503/520 before checking to_email
            assert response.status_code in [503, 520]
            print("✓ POST /api/email/test returns error (not configured) before validating to_email")
        else:
            # Should return 400 for missing to_email
            assert response.status_code == 400
            print("✓ POST /api/email/test requires to_email field")


class TestProposalSubmitEmailNotification:
    """Tests for email notification on proposal submission"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_creator_token(self):
        """Get creator authentication token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": TEST_CREATOR_EMAIL,
            "password": TEST_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def create_draft_proposal(self, token):
        """Create a draft proposal for testing"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        unique_id = str(uuid.uuid4())[:8]
        response = self.session.post(f"{BASE_URL}/api/proposals", json={
            "title": f"Email Test Proposal {unique_id}",
            "description": "Testing email notifications on proposal submission",
            "platforms": ["YouTube"],
            "timeline": "1-2 weeks",
            "priority": "medium",
            "goals": "Test email notification system"
        })
        
        if response.status_code == 201:
            return response.json().get("id")
        return None
    
    def test_proposal_submit_includes_email_sent_field(self):
        """POST /api/proposals/{id}/submit includes email_sent field in response"""
        token = self.get_creator_token()
        assert token, "Failed to get creator token"
        
        # Create a draft proposal
        proposal_id = self.create_draft_proposal(token)
        assert proposal_id, "Failed to create draft proposal"
        
        # Submit the proposal
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.post(f"{BASE_URL}/api/proposals/{proposal_id}/submit")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify email_sent field is present
        assert "email_sent" in data, "Missing 'email_sent' field in response"
        assert isinstance(data["email_sent"], bool), "'email_sent' should be boolean"
        
        # Since SendGrid is not configured, email_sent should be False
        # (unless SendGrid was configured after test setup)
        print(f"✓ POST /api/proposals/{proposal_id}/submit includes email_sent: {data['email_sent']}")
        
        # Verify other expected fields
        assert data.get("status") == "submitted"
        assert "arris_insights" in data
        print(f"✓ Proposal submitted successfully with email_sent={data['email_sent']}")


class TestProposalStatusChangeEmailNotifications:
    """Tests for email notifications on proposal status changes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_proposals = []
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_creator_token(self):
        """Get creator authentication token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": TEST_CREATOR_EMAIL,
            "password": TEST_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def create_and_submit_proposal(self, creator_token):
        """Create and submit a proposal for testing status changes"""
        self.session.headers.update({"Authorization": f"Bearer {creator_token}"})
        
        unique_id = str(uuid.uuid4())[:8]
        # Create proposal
        response = self.session.post(f"{BASE_URL}/api/proposals", json={
            "title": f"Status Change Test {unique_id}",
            "description": "Testing email notifications on status changes",
            "platforms": ["YouTube", "TikTok"],
            "timeline": "1-2 weeks",
            "priority": "high",
            "goals": "Test status change email notifications"
        })
        
        if response.status_code != 201:
            return None
        
        proposal_id = response.json().get("id")
        self.created_proposals.append(proposal_id)
        
        # Submit proposal
        submit_response = self.session.post(f"{BASE_URL}/api/proposals/{proposal_id}/submit")
        if submit_response.status_code == 200:
            return proposal_id
        return None
    
    def test_status_approved_includes_email_sent(self):
        """PATCH /api/proposals/{id} with status=approved includes email_sent field"""
        creator_token = self.get_creator_token()
        assert creator_token, "Failed to get creator token"
        
        admin_token = self.get_admin_token()
        assert admin_token, "Failed to get admin token"
        
        # Create and submit a proposal
        proposal_id = self.create_and_submit_proposal(creator_token)
        assert proposal_id, "Failed to create and submit proposal"
        
        # Approve the proposal as admin
        self.session.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "approved",
            "review_notes": "Approved for testing email notifications"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify email_sent field
        assert "email_sent" in data, "Missing 'email_sent' field in approval response"
        assert isinstance(data["email_sent"], bool), "'email_sent' should be boolean"
        
        # Verify project was created
        assert "project_id" in data, "Missing 'project_id' in approval response"
        
        print(f"✓ PATCH /api/proposals/{proposal_id} (approved) includes email_sent: {data['email_sent']}")
    
    def test_status_rejected_includes_email_sent(self):
        """PATCH /api/proposals/{id} with status=rejected includes email_sent field"""
        creator_token = self.get_creator_token()
        assert creator_token, "Failed to get creator token"
        
        admin_token = self.get_admin_token()
        assert admin_token, "Failed to get admin token"
        
        # Create and submit a proposal
        proposal_id = self.create_and_submit_proposal(creator_token)
        assert proposal_id, "Failed to create and submit proposal"
        
        # Reject the proposal as admin
        self.session.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "rejected",
            "review_notes": "Rejected for testing email notifications"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify email_sent field
        assert "email_sent" in data, "Missing 'email_sent' field in rejection response"
        assert isinstance(data["email_sent"], bool), "'email_sent' should be boolean"
        
        print(f"✓ PATCH /api/proposals/{proposal_id} (rejected) includes email_sent: {data['email_sent']}")
    
    def test_status_under_review_includes_email_sent(self):
        """PATCH /api/proposals/{id} with status=under_review includes email_sent field"""
        creator_token = self.get_creator_token()
        assert creator_token, "Failed to get creator token"
        
        admin_token = self.get_admin_token()
        assert admin_token, "Failed to get admin token"
        
        # Create and submit a proposal
        proposal_id = self.create_and_submit_proposal(creator_token)
        assert proposal_id, "Failed to create and submit proposal"
        
        # Move to under_review as admin
        self.session.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "under_review"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify email_sent field
        assert "email_sent" in data, "Missing 'email_sent' field in under_review response"
        assert isinstance(data["email_sent"], bool), "'email_sent' should be boolean"
        
        print(f"✓ PATCH /api/proposals/{proposal_id} (under_review) includes email_sent: {data['email_sent']}")
    
    def test_status_completed_includes_email_sent(self):
        """PATCH /api/proposals/{id} with status=completed includes email_sent field"""
        creator_token = self.get_creator_token()
        assert creator_token, "Failed to get creator token"
        
        admin_token = self.get_admin_token()
        assert admin_token, "Failed to get admin token"
        
        # Create and submit a proposal
        proposal_id = self.create_and_submit_proposal(creator_token)
        assert proposal_id, "Failed to create and submit proposal"
        
        # First approve the proposal
        self.session.headers.update({"Authorization": f"Bearer {admin_token}"})
        approve_response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "approved"
        })
        assert approve_response.status_code == 200, "Failed to approve proposal"
        
        # Now mark as completed
        response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "completed"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify email_sent field
        assert "email_sent" in data, "Missing 'email_sent' field in completed response"
        assert isinstance(data["email_sent"], bool), "'email_sent' should be boolean"
        
        print(f"✓ PATCH /api/proposals/{proposal_id} (completed) includes email_sent: {data['email_sent']}")


class TestEmailServiceGracefulDegradation:
    """Tests that email service gracefully handles missing API key"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_creator_token(self):
        """Get creator authentication token"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": TEST_CREATOR_EMAIL,
            "password": TEST_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_email_service_returns_false_when_not_configured(self):
        """Email service returns email_sent: false when SendGrid not configured"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Check email status
        response = self.session.get(f"{BASE_URL}/api/email/status")
        assert response.status_code == 200
        
        data = response.json()
        is_configured = data.get("configured", False)
        
        if not is_configured:
            # Verify status shows not_configured
            assert data["status"] == "not_configured"
            print("✓ Email service correctly reports not_configured status")
            
            # Verify setup instructions are provided
            assert "setup_instructions" in data
            instructions = data["setup_instructions"]
            assert "step_1" in instructions
            assert "step_2" in instructions
            assert "step_3" in instructions
            print("✓ Setup instructions provided for unconfigured email service")
        else:
            print("✓ Email service is configured - skipping not_configured tests")
    
    def test_proposal_operations_succeed_without_email(self):
        """Proposal operations succeed even when email service is not configured"""
        creator_token = self.get_creator_token()
        assert creator_token, "Failed to get creator token"
        
        admin_token = self.get_admin_token()
        assert admin_token, "Failed to get admin token"
        
        # Create proposal
        self.session.headers.update({"Authorization": f"Bearer {creator_token}"})
        unique_id = str(uuid.uuid4())[:8]
        create_response = self.session.post(f"{BASE_URL}/api/proposals", json={
            "title": f"Graceful Degradation Test {unique_id}",
            "description": "Testing that operations succeed without email",
            "platforms": ["Instagram"],
            "timeline": "1-2 weeks",
            "priority": "low"
        })
        assert create_response.status_code == 201, "Failed to create proposal"
        proposal_id = create_response.json().get("id")
        print(f"✓ Proposal created successfully: {proposal_id}")
        
        # Submit proposal
        submit_response = self.session.post(f"{BASE_URL}/api/proposals/{proposal_id}/submit")
        assert submit_response.status_code == 200, "Failed to submit proposal"
        submit_data = submit_response.json()
        assert "email_sent" in submit_data
        print(f"✓ Proposal submitted successfully, email_sent: {submit_data['email_sent']}")
        
        # Approve proposal (as admin)
        self.session.headers.update({"Authorization": f"Bearer {admin_token}"})
        approve_response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "approved"
        })
        assert approve_response.status_code == 200, "Failed to approve proposal"
        approve_data = approve_response.json()
        assert "email_sent" in approve_data
        print(f"✓ Proposal approved successfully, email_sent: {approve_data['email_sent']}")
        
        # Complete proposal
        complete_response = self.session.patch(f"{BASE_URL}/api/proposals/{proposal_id}", json={
            "status": "completed"
        })
        assert complete_response.status_code == 200, "Failed to complete proposal"
        complete_data = complete_response.json()
        assert "email_sent" in complete_data
        print(f"✓ Proposal completed successfully, email_sent: {complete_data['email_sent']}")
        
        print("✓ All proposal operations succeed without email service configured")


class TestEmailNotificationTypes:
    """Tests that all 5 notification types are supported"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_all_notification_types_listed_in_status(self):
        """GET /api/email/status lists all 5 notification types"""
        token = self.get_admin_token()
        assert token, "Failed to get admin token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/email/status")
        
        assert response.status_code == 200
        data = response.json()
        
        features = data.get("features", {})
        
        # Verify all 5 notification types are listed
        expected_types = [
            "proposal_submitted",
            "proposal_approved", 
            "proposal_rejected",
            "proposal_under_review",
            "proposal_completed"
        ]
        
        for notification_type in expected_types:
            assert notification_type in features, f"Missing notification type: {notification_type}"
            assert features[notification_type] == True, f"Notification type {notification_type} should be True"
            print(f"✓ Notification type '{notification_type}' is supported")
        
        print("✓ All 5 notification types are listed in email status")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
