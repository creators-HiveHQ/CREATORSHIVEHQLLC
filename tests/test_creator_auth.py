"""
Creator Authentication API Tests
Tests for Creators Hive HQ Creator Dashboard - Password-based Login with JWT
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCreatorRegistration:
    """Test creator registration with password field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_get_form_options(self):
        """Test GET /api/creators/form-options returns platforms, niches, and ARRIS question"""
        response = self.session.get(f"{BASE_URL}/api/creators/form-options")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "platforms" in data, "Response should have platforms"
        assert "niches" in data, "Response should have niches"
        assert "arris_question" in data, "Response should have arris_question"
        
        # Verify platforms structure
        assert len(data["platforms"]) > 0, "Should have platform options"
        platform = data["platforms"][0]
        assert "value" in platform, "Platform should have value"
        assert "label" in platform, "Platform should have label"
        assert "icon" in platform, "Platform should have icon"
        
        print(f"✓ Form options retrieved: {len(data['platforms'])} platforms, {len(data['niches'])} niches")
    
    def test_register_creator_with_password(self):
        """Test POST /api/creators/register stores hashed password"""
        test_email = f"test_reg_{uuid.uuid4().hex[:8]}@example.com"
        
        response = self.session.post(f"{BASE_URL}/api/creators/register", json={
            "name": "Test Registration Creator",
            "email": test_email,
            "password": "testpass123",
            "platforms": ["youtube", "instagram"],
            "niche": "Tech & Software",
            "goals": "Testing registration",
            "arris_intake_question": "Testing the flow"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should have id"
        assert "name" in data, "Response should have name"
        assert "email" in data, "Response should have email"
        assert "status" in data, "Response should have status"
        assert data["status"] == "pending", f"Status should be pending, got {data['status']}"
        assert "message" in data, "Response should have message"
        
        # Verify password is NOT returned in response
        assert "password" not in data, "Password should not be in response"
        assert "hashed_password" not in data, "Hashed password should not be in response"
        
        print(f"✓ Creator registered: {data['id']} with status {data['status']}")
        return data
    
    def test_register_duplicate_email_fails(self):
        """Test that registering with existing email fails"""
        response = self.session.post(f"{BASE_URL}/api/creators/register", json={
            "name": "Duplicate Test",
            "email": "testcreator@example.com",  # Already exists
            "password": "testpass123",
            "platforms": ["youtube"],
            "niche": "Tech & Software"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should have detail"
        assert "already registered" in data["detail"].lower(), f"Error should mention already registered: {data['detail']}"
        
        print("✓ Duplicate email registration correctly rejected")


class TestCreatorLogin:
    """Test creator login endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_login_approved_creator_returns_jwt(self):
        """Test POST /api/creators/login returns JWT token for approved creators"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "testcreator@example.com",
            "password": "creator123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should have access_token"
        assert "token_type" in data, "Response should have token_type"
        assert data["token_type"] == "bearer", f"Token type should be bearer, got {data['token_type']}"
        assert "expires_in" in data, "Response should have expires_in"
        assert "creator" in data, "Response should have creator info"
        
        # Verify creator info
        creator = data["creator"]
        assert "id" in creator, "Creator should have id"
        assert "email" in creator, "Creator should have email"
        assert "name" in creator, "Creator should have name"
        assert "status" in creator, "Creator should have status"
        assert creator["status"] in ["approved", "active"], f"Creator status should be approved/active, got {creator['status']}"
        
        print(f"✓ Creator login successful: {creator['name']} ({creator['status']})")
        return data
    
    def test_login_pending_creator_fails_with_403(self):
        """Test that pending creators cannot login"""
        # First register a new creator (will be pending)
        test_email = f"pending_{uuid.uuid4().hex[:8]}@example.com"
        
        reg_response = self.session.post(f"{BASE_URL}/api/creators/register", json={
            "name": "Pending Test Creator",
            "email": test_email,
            "password": "testpass123",
            "platforms": ["youtube"],
            "niche": "Tech & Software"
        })
        
        assert reg_response.status_code == 200, "Registration should succeed"
        
        # Try to login
        login_response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": test_email,
            "password": "testpass123"
        })
        
        assert login_response.status_code == 403, f"Expected 403, got {login_response.status_code}"
        
        data = login_response.json()
        assert "detail" in data, "Response should have detail"
        assert "pending" in data["detail"].lower(), f"Error should mention pending: {data['detail']}"
        
        print("✓ Pending creator login correctly rejected with 403")
    
    def test_login_wrong_password_fails(self):
        """Test that wrong password fails"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "testcreator@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("✓ Wrong password correctly rejected with 401")
    
    def test_login_nonexistent_email_fails(self):
        """Test that nonexistent email fails"""
        response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "nonexistent@example.com",
            "password": "anypassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("✓ Nonexistent email correctly rejected with 401")


class TestCreatorMeEndpoints:
    """Test creator /me endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get creator token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get creator token
        login_response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "testcreator@example.com",
            "password": "creator123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
            self.creator_id = login_response.json()["creator"]["id"]
        else:
            pytest.skip("Creator authentication failed - skipping authenticated tests")
    
    def test_get_creator_profile(self):
        """Test GET /api/creators/me returns creator profile"""
        response = self.session.get(f"{BASE_URL}/api/creators/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "id" in data, "Response should have id"
        assert "name" in data, "Response should have name"
        assert "email" in data, "Response should have email"
        assert "platforms" in data, "Response should have platforms"
        assert "niche" in data, "Response should have niche"
        assert "status" in data, "Response should have status"
        
        # Verify password is NOT returned
        assert "password" not in data, "Password should not be in response"
        assert "hashed_password" not in data, "Hashed password should not be in response"
        
        print(f"✓ Creator profile retrieved: {data['name']} ({data['email']})")
    
    def test_get_creator_dashboard(self):
        """Test GET /api/creators/me/dashboard returns proposal stats and recent proposals"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/dashboard")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify creator info
        assert "creator" in data, "Response should have creator"
        creator = data["creator"]
        assert "id" in creator, "Creator should have id"
        assert "name" in creator, "Creator should have name"
        assert "tier" in creator, "Creator should have tier"
        
        # Verify proposals stats
        assert "proposals" in data, "Response should have proposals"
        proposals = data["proposals"]
        assert "total" in proposals, "Proposals should have total"
        assert "by_status" in proposals, "Proposals should have by_status"
        assert "recent" in proposals, "Proposals should have recent"
        
        # Verify projects stats
        assert "projects" in data, "Response should have projects"
        assert "total" in data["projects"], "Projects should have total"
        
        # Verify tasks stats
        assert "tasks" in data, "Response should have tasks"
        
        print(f"✓ Dashboard retrieved: {proposals['total']} proposals, {data['projects']['total']} projects")
        
        # Verify recent proposals have ARRIS insights
        if len(proposals["recent"]) > 0:
            recent = proposals["recent"][0]
            assert "id" in recent, "Recent proposal should have id"
            assert "title" in recent, "Recent proposal should have title"
            assert "status" in recent, "Recent proposal should have status"
            if recent.get("arris_insights"):
                print(f"  - Recent proposal has ARRIS insights: {recent['title']}")
    
    def test_get_creator_proposals(self):
        """Test GET /api/creators/me/proposals returns all creator's proposals"""
        response = self.session.get(f"{BASE_URL}/api/creators/me/proposals")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify all proposals belong to this creator
        for proposal in data:
            assert proposal.get("user_id") == self.creator_id, f"Proposal should belong to creator {self.creator_id}"
            assert "id" in proposal, "Proposal should have id"
            assert "title" in proposal, "Proposal should have title"
            assert "status" in proposal, "Proposal should have status"
        
        print(f"✓ Creator proposals retrieved: {len(data)} proposals")
        
        # Check for ARRIS insights in submitted proposals
        for proposal in data:
            if proposal.get("status") in ["submitted", "under_review", "approved", "in_progress"]:
                if proposal.get("arris_insights"):
                    insights = proposal["arris_insights"]
                    assert "summary" in insights, "ARRIS insights should have summary"
                    assert "strengths" in insights, "ARRIS insights should have strengths"
                    assert "risks" in insights, "ARRIS insights should have risks"
                    assert "recommendations" in insights, "ARRIS insights should have recommendations"
                    print(f"  - Proposal {proposal['id']} has ARRIS insights")
    
    def test_me_endpoint_without_auth_fails(self):
        """Test that /me endpoints require authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        
        response = no_auth_session.get(f"{BASE_URL}/api/creators/me")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        print("✓ /me endpoint correctly requires authentication")


class TestCreatorProposalCreation:
    """Test proposal creation with creator token"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get creator token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get creator token
        login_response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "testcreator@example.com",
            "password": "creator123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
            self.creator_id = login_response.json()["creator"]["id"]
        else:
            pytest.skip("Creator authentication failed")
    
    def test_create_proposal_auto_fills_user_id(self):
        """Test POST /api/proposals with creator token auto-fills user_id"""
        response = self.session.post(f"{BASE_URL}/api/proposals", json={
            "title": f"Test Proposal {uuid.uuid4().hex[:8]}",
            "description": "Testing proposal creation with creator token",
            "platforms": ["youtube"],
            "timeline": "1 month",
            "priority": "medium"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should have id"
        assert "title" in data, "Response should have title"
        assert "status" in data, "Response should have status"
        assert data["status"] == "draft", f"Status should be draft, got {data['status']}"
        
        proposal_id = data["id"]
        
        # Verify the proposal was created with correct user_id
        proposals_response = self.session.get(f"{BASE_URL}/api/creators/me/proposals")
        proposals = proposals_response.json()
        
        created_proposal = next((p for p in proposals if p["id"] == proposal_id), None)
        assert created_proposal is not None, "Created proposal should be in creator's proposals"
        assert created_proposal["user_id"] == self.creator_id, f"Proposal user_id should be {self.creator_id}"
        
        print(f"✓ Proposal created with auto-filled user_id: {proposal_id}")
        return proposal_id
    
    def test_submit_proposal_with_creator_token(self):
        """Test POST /api/proposals/{id}/submit with creator token and ownership validation"""
        # First create a proposal
        create_response = self.session.post(f"{BASE_URL}/api/proposals", json={
            "title": f"Submit Test {uuid.uuid4().hex[:8]}",
            "description": "Testing proposal submission",
            "platforms": ["instagram"],
            "timeline": "2 weeks",
            "priority": "low"
        })
        
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit the proposal
        submit_response = self.session.post(f"{BASE_URL}/api/proposals/{proposal_id}/submit")
        
        assert submit_response.status_code == 200, f"Expected 200, got {submit_response.status_code}: {submit_response.text}"
        
        data = submit_response.json()
        assert data["status"] == "submitted", f"Status should be submitted, got {data['status']}"
        assert "arris_insights" in data, "Response should have arris_insights"
        
        # Verify ARRIS insights structure
        insights = data["arris_insights"]
        assert "summary" in insights, "ARRIS insights should have summary"
        assert "strengths" in insights, "ARRIS insights should have strengths"
        assert "risks" in insights, "ARRIS insights should have risks"
        assert "recommendations" in insights, "ARRIS insights should have recommendations"
        assert "suggested_milestones" in insights, "ARRIS insights should have suggested_milestones"
        
        print(f"✓ Proposal submitted with ARRIS insights: {proposal_id}")
        print(f"  - Summary: {insights['summary'][:100]}...")
    
    def test_cannot_submit_other_creators_proposal(self):
        """Test that creator cannot submit another creator's proposal"""
        # Get admin token to create a proposal for different user
        admin_session = requests.Session()
        admin_session.headers.update({"Content-Type": "application/json"})
        
        admin_login = admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hivehq.com",
            "password": "admin123"
        })
        
        if admin_login.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_login.json()["access_token"]
        admin_session.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Create proposal with different user_id
        create_response = admin_session.post(f"{BASE_URL}/api/proposals", json={
            "title": "Other User Proposal",
            "description": "This belongs to a different user",
            "user_id": "U-different",
            "platforms": ["youtube"],
            "priority": "low"
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test proposal")
        
        other_proposal_id = create_response.json()["id"]
        
        # Try to submit with creator token (should fail)
        submit_response = self.session.post(f"{BASE_URL}/api/proposals/{other_proposal_id}/submit")
        
        assert submit_response.status_code == 403, f"Expected 403, got {submit_response.status_code}"
        
        print("✓ Creator correctly cannot submit other creator's proposal")


class TestARRISInsightsDisplay:
    """Test ARRIS insights in proposal detail"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get creator token
        login_response = self.session.post(f"{BASE_URL}/api/creators/login", json={
            "email": "testcreator@example.com",
            "password": "creator123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Creator authentication failed")
    
    def test_arris_insights_structure(self):
        """Test that ARRIS insights have correct structure (summary, strengths, risks, recommendations, milestones)"""
        # Get proposals with ARRIS insights
        response = self.session.get(f"{BASE_URL}/api/creators/me/proposals")
        
        assert response.status_code == 200
        
        proposals = response.json()
        
        # Find a submitted proposal with insights
        submitted_proposals = [p for p in proposals if p.get("arris_insights")]
        
        if len(submitted_proposals) == 0:
            pytest.skip("No proposals with ARRIS insights found")
        
        proposal = submitted_proposals[0]
        insights = proposal["arris_insights"]
        
        # Verify all required fields
        required_fields = ["summary", "strengths", "risks", "recommendations", "suggested_milestones"]
        for field in required_fields:
            assert field in insights, f"ARRIS insights should have {field}"
        
        # Verify types
        assert isinstance(insights["summary"], str), "Summary should be string"
        assert isinstance(insights["strengths"], list), "Strengths should be list"
        assert isinstance(insights["risks"], list), "Risks should be list"
        assert isinstance(insights["recommendations"], list), "Recommendations should be list"
        assert isinstance(insights["suggested_milestones"], list), "Milestones should be list"
        
        # Verify content
        assert len(insights["summary"]) > 0, "Summary should not be empty"
        assert len(insights["strengths"]) > 0, "Strengths should not be empty"
        assert len(insights["risks"]) > 0, "Risks should not be empty"
        assert len(insights["recommendations"]) > 0, "Recommendations should not be empty"
        
        print(f"✓ ARRIS insights structure verified for proposal {proposal['id']}")
        print(f"  - Summary length: {len(insights['summary'])} chars")
        print(f"  - Strengths: {len(insights['strengths'])} items")
        print(f"  - Risks: {len(insights['risks'])} items")
        print(f"  - Recommendations: {len(insights['recommendations'])} items")
        print(f"  - Milestones: {len(insights['suggested_milestones'])} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
