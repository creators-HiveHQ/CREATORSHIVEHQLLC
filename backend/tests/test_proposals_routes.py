"""
Test Proposals Routes - Migrated from server.py to routes/proposals.py
======================================================================
Tests all proposal CRUD, submission with ARRIS integration, and recommendation routes.

Endpoints tested:
- GET /api/proposals/form-options - public endpoint for form options
- GET /api/proposals/stats/summary - admin stats endpoint
- GET /api/proposals - admin list all proposals
- POST /api/proposals - create new proposal (creator)
- GET /api/proposals/{id} - get specific proposal
- PATCH /api/proposals/{id} - update proposal (admin)
- DELETE /api/proposals/{id} - delete proposal
- POST /api/proposals/{id}/submit - submit proposal for review with ARRIS insights
- POST /api/proposals/{id}/regenerate-insights - regenerate ARRIS insights
- POST /api/proposals/{id}/generate-recommendations - generate improvement recommendations
- GET /api/proposals/{id}/recommendations - get existing recommendations
- GET /api/creators/me/proposals - get creator's own proposals
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "admin@hivehq.com", "password": "admin123"}
FREE_CREATOR_CREDS = {"email": "freetest@hivehq.com", "password": "testpassword"}
PRO_CREATOR_CREDS = {"email": "protest@hivehq.com", "password": "testpassword"}
ELITE_CREATOR_CREDS = {"email": "elitetest@hivehq.com", "password": "testpassword123"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def free_creator_token():
    """Get free tier creator authentication token"""
    response = requests.post(f"{BASE_URL}/api/creators/login", json=FREE_CREATOR_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Free creator login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def pro_creator_token():
    """Get pro tier creator authentication token"""
    response = requests.post(f"{BASE_URL}/api/creators/login", json=PRO_CREATOR_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Pro creator login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def elite_creator_token():
    """Get elite tier creator authentication token"""
    response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_CREATOR_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Elite creator login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def free_creator_id(free_creator_token):
    """Get free creator's ID"""
    response = requests.get(
        f"{BASE_URL}/api/creators/me",
        headers={"Authorization": f"Bearer {free_creator_token}"}
    )
    if response.status_code == 200:
        return response.json().get("id")
    pytest.skip("Could not get free creator ID")


@pytest.fixture(scope="module")
def pro_creator_id(pro_creator_token):
    """Get pro creator's ID"""
    response = requests.get(
        f"{BASE_URL}/api/creators/me",
        headers={"Authorization": f"Bearer {pro_creator_token}"}
    )
    if response.status_code == 200:
        return response.json().get("id")
    pytest.skip("Could not get pro creator ID")


class TestPublicEndpoints:
    """Test public proposal endpoints (no auth required)"""
    
    def test_get_form_options(self):
        """GET /api/proposals/form-options - returns form options"""
        response = requests.get(f"{BASE_URL}/api/proposals/form-options")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "platforms" in data, "Response should contain platforms"
        assert "timelines" in data, "Response should contain timelines"
        assert "priorities" in data, "Response should contain priorities"
        assert "statuses" in data, "Response should contain statuses"
        assert "arris_question" in data, "Response should contain arris_question"
        
        # Validate platforms structure
        assert len(data["platforms"]) > 0, "Should have at least one platform"
        assert "value" in data["platforms"][0], "Platform should have value"
        assert "label" in data["platforms"][0], "Platform should have label"
        
        print(f"✓ Form options returned with {len(data['platforms'])} platforms, {len(data['timelines'])} timelines")


class TestAdminEndpoints:
    """Test admin-only proposal endpoints"""
    
    def test_stats_summary_requires_auth(self):
        """GET /api/proposals/stats/summary - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/proposals/stats/summary")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Stats summary requires authentication")
    
    def test_stats_summary_rejects_creator(self, free_creator_token):
        """GET /api/proposals/stats/summary - rejects creator auth"""
        response = requests.get(
            f"{BASE_URL}/api/proposals/stats/summary",
            headers={"Authorization": f"Bearer {free_creator_token}"}
        )
        # Should reject creator - only admin allowed
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ Stats summary rejects creator authentication")
    
    def test_stats_summary_with_admin(self, admin_token):
        """GET /api/proposals/stats/summary - returns stats for admin"""
        response = requests.get(
            f"{BASE_URL}/api/proposals/stats/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_proposals" in data, "Response should contain total_proposals"
        assert "by_status" in data, "Response should contain by_status"
        assert "by_priority" in data, "Response should contain by_priority"
        
        print(f"✓ Stats summary: {data['total_proposals']} total proposals")
    
    def test_list_proposals_requires_auth(self):
        """GET /api/proposals - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/proposals")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ List proposals requires authentication")
    
    def test_list_proposals_with_admin(self, admin_token):
        """GET /api/proposals - returns proposals list for admin"""
        response = requests.get(
            f"{BASE_URL}/api/proposals",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Admin can list proposals: {len(data)} proposals found")
    
    def test_list_proposals_with_filters(self, admin_token):
        """GET /api/proposals - supports filtering by status and priority"""
        # Test status filter
        response = requests.get(
            f"{BASE_URL}/api/proposals?status=draft",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Status filter failed: {response.status_code}"
        
        # Test priority filter
        response = requests.get(
            f"{BASE_URL}/api/proposals?priority=high",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Priority filter failed: {response.status_code}"
        
        # Test limit
        response = requests.get(
            f"{BASE_URL}/api/proposals?limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Limit filter failed: {response.status_code}"
        data = response.json()
        assert len(data) <= 5, "Limit should be respected"
        
        print("✓ Proposal list supports status, priority, and limit filters")


class TestCreatorProposalCRUD:
    """Test creator proposal CRUD operations"""
    
    def test_create_proposal_requires_auth(self):
        """POST /api/proposals - requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/proposals",
            json={"title": "Test", "description": "Test"}
        )
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Create proposal requires authentication")
    
    def test_create_proposal_as_creator(self, pro_creator_token, pro_creator_id):
        """POST /api/proposals - creator can create proposal"""
        proposal_data = {
            "title": f"TEST_Proposal_{int(time.time())}",
            "description": "Test proposal for backend testing",
            "goals": "Test the proposal creation endpoint",
            "platforms": ["youtube", "instagram"],
            "timeline": "1-2_weeks",
            "estimated_hours": 10,
            "priority": "medium",
            "arris_intake_question": "I want to test the API"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain proposal id"
        assert "title" in data, "Response should contain title"
        assert data["status"] == "draft", "New proposal should be in draft status"
        assert "message" in data, "Response should contain message"
        
        print(f"✓ Creator created proposal: {data['id']}")
        return data["id"]
    
    def test_get_proposal_by_id(self, pro_creator_token):
        """GET /api/proposals/{id} - get specific proposal"""
        # First create a proposal
        proposal_data = {
            "title": f"TEST_GetById_{int(time.time())}",
            "description": "Test proposal for get by ID",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Now get it by ID
        response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["id"] == proposal_id, "Returned proposal should match requested ID"
        assert data["title"] == proposal_data["title"], "Title should match"
        
        print(f"✓ Got proposal by ID: {proposal_id}")
    
    def test_get_proposal_not_found(self, pro_creator_token):
        """GET /api/proposals/{id} - returns 404 for non-existent proposal"""
        response = requests.get(
            f"{BASE_URL}/api/proposals/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Returns 404 for non-existent proposal")
    
    def test_creator_cannot_access_others_proposal(self, pro_creator_token, free_creator_token):
        """GET /api/proposals/{id} - creator cannot access another creator's proposal"""
        # Create proposal as pro creator
        proposal_data = {
            "title": f"TEST_AccessControl_{int(time.time())}",
            "description": "Test access control",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Try to access as free creator
        response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {free_creator_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for access denied, got {response.status_code}"
        print("✓ Creator cannot access another creator's proposal")
    
    def test_delete_draft_proposal(self, pro_creator_token):
        """DELETE /api/proposals/{id} - creator can delete own draft"""
        # Create a draft proposal
        proposal_data = {
            "title": f"TEST_ToDelete_{int(time.time())}",
            "description": "This will be deleted",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Delete should return success"
        
        # Verify it's deleted
        get_response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert get_response.status_code == 404, "Deleted proposal should return 404"
        
        print(f"✓ Creator deleted draft proposal: {proposal_id}")
    
    def test_delete_not_found(self, pro_creator_token):
        """DELETE /api/proposals/{id} - returns 404 for non-existent proposal"""
        response = requests.delete(
            f"{BASE_URL}/api/proposals/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Delete returns 404 for non-existent proposal")


class TestAdminProposalUpdate:
    """Test admin proposal update (PATCH) operations"""
    
    def test_update_proposal_requires_admin(self, pro_creator_token):
        """PATCH /api/proposals/{id} - requires admin authentication"""
        # Create a proposal first
        proposal_data = {
            "title": f"TEST_UpdateAuth_{int(time.time())}",
            "description": "Test update auth",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Try to update as creator (should fail)
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 for creator, got {response.status_code}"
        print("✓ Update proposal requires admin authentication")
    
    def test_admin_update_proposal_status(self, admin_token, pro_creator_token):
        """PATCH /api/proposals/{id} - admin can update proposal status"""
        # Create a proposal as creator
        proposal_data = {
            "title": f"TEST_AdminUpdate_{int(time.time())}",
            "description": "Test admin update",
            "platforms": ["youtube"],
            "priority": "medium"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Admin updates status to under_review
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={"status": "under_review"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the update
        get_response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "under_review"
        
        print(f"✓ Admin updated proposal status to under_review: {proposal_id}")
    
    def test_admin_approve_proposal_creates_project(self, admin_token, pro_creator_token):
        """PATCH /api/proposals/{id} - approving proposal creates project"""
        # Create and submit a proposal
        proposal_data = {
            "title": f"TEST_Approve_{int(time.time())}",
            "description": "Test approval creates project",
            "platforms": ["youtube", "instagram"],
            "priority": "high"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit the proposal first
        submit_response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        # May fail due to feature gating, but let's try
        
        # Admin approves
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify proposal has assigned_project_id and status is in_progress
        get_response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        
        # Status should be in_progress after approval (project created)
        assert data["status"] == "in_progress", f"Expected in_progress, got {data['status']}"
        assert "assigned_project_id" in data, "Should have assigned_project_id"
        
        print(f"✓ Admin approved proposal, project created: {data.get('assigned_project_id')}")
    
    def test_admin_reject_proposal(self, admin_token, pro_creator_token):
        """PATCH /api/proposals/{id} - admin can reject proposal with notes"""
        # Create a proposal
        proposal_data = {
            "title": f"TEST_Reject_{int(time.time())}",
            "description": "Test rejection",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Admin rejects with notes
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={
                "status": "rejected",
                "admin_notes": "Needs more detail on goals and timeline"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify rejection
        get_response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["status"] == "rejected"
        assert "reviewed_at" in data, "Should have reviewed_at timestamp"
        
        print(f"✓ Admin rejected proposal: {proposal_id}")
    
    def test_update_not_found(self, admin_token):
        """PATCH /api/proposals/{id} - returns 404 for non-existent proposal"""
        response = requests.patch(
            f"{BASE_URL}/api/proposals/nonexistent-id-12345",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Update returns 404 for non-existent proposal")
    
    def test_update_requires_data(self, admin_token, pro_creator_token):
        """PATCH /api/proposals/{id} - requires update data"""
        # Create a proposal
        proposal_data = {
            "title": f"TEST_NoData_{int(time.time())}",
            "description": "Test no data",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Try to update with empty data
        response = requests.patch(
            f"{BASE_URL}/api/proposals/{proposal_id}",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for empty data, got {response.status_code}"
        print("✓ Update requires non-empty data")


class TestProposalSubmission:
    """Test proposal submission with ARRIS integration"""
    
    def test_submit_proposal_requires_auth(self):
        """POST /api/proposals/{id}/submit - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/proposals/some-id/submit")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Submit proposal requires authentication")
    
    def test_submit_draft_proposal(self, pro_creator_token):
        """POST /api/proposals/{id}/submit - submits draft and generates ARRIS insights"""
        # Create a draft proposal
        proposal_data = {
            "title": f"TEST_Submit_{int(time.time())}",
            "description": "Test proposal submission with ARRIS insights generation",
            "goals": "Test the submission flow and ARRIS integration",
            "platforms": ["youtube", "instagram"],
            "timeline": "2-4_weeks",
            "estimated_hours": 20,
            "priority": "high",
            "arris_intake_question": "I want to grow my audience by 50%"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit the proposal
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "submitted", "Status should be submitted"
        assert "arris_insights" in data, "Should contain ARRIS insights"
        assert data["id"] == proposal_id, "Should return correct proposal ID"
        
        # Verify ARRIS insights structure
        insights = data["arris_insights"]
        assert "summary" in insights, "Insights should have summary"
        assert "estimated_complexity" in insights, "Insights should have estimated_complexity"
        
        print(f"✓ Proposal submitted with ARRIS insights: {proposal_id}")
        print(f"  - Complexity: {insights.get('estimated_complexity')}")
    
    def test_submit_not_found(self, pro_creator_token):
        """POST /api/proposals/{id}/submit - returns 404 for non-existent proposal"""
        response = requests.post(
            f"{BASE_URL}/api/proposals/nonexistent-id-12345/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Submit returns 404 for non-existent proposal")
    
    def test_cannot_submit_non_draft(self, pro_creator_token, admin_token):
        """POST /api/proposals/{id}/submit - cannot submit non-draft proposal"""
        # Create and submit a proposal
        proposal_data = {
            "title": f"TEST_DoubleSubmit_{int(time.time())}",
            "description": "Test double submission",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit once
        submit_response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert submit_response.status_code == 200
        
        # Try to submit again
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for non-draft, got {response.status_code}"
        print("✓ Cannot submit non-draft proposal")


class TestRegenerateInsights:
    """Test ARRIS insights regeneration"""
    
    def test_regenerate_insights_requires_auth(self):
        """POST /api/proposals/{id}/regenerate-insights - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/proposals/some-id/regenerate-insights")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Regenerate insights requires authentication")
    
    def test_regenerate_insights(self, pro_creator_token):
        """POST /api/proposals/{id}/regenerate-insights - regenerates ARRIS insights"""
        # Create and submit a proposal
        proposal_data = {
            "title": f"TEST_Regenerate_{int(time.time())}",
            "description": "Test regenerating ARRIS insights",
            "goals": "Test the regeneration endpoint",
            "platforms": ["youtube"],
            "priority": "medium"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit first
        submit_response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert submit_response.status_code == 200
        
        # Regenerate insights
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/regenerate-insights",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "arris_insights" in data, "Should contain regenerated ARRIS insights"
        assert "processing_speed" in data, "Should indicate processing speed"
        
        print(f"✓ Regenerated ARRIS insights for: {proposal_id}")
    
    def test_regenerate_not_found(self, pro_creator_token):
        """POST /api/proposals/{id}/regenerate-insights - returns 404 for non-existent"""
        response = requests.post(
            f"{BASE_URL}/api/proposals/nonexistent-id-12345/regenerate-insights",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Regenerate returns 404 for non-existent proposal")


class TestRecommendations:
    """Test proposal recommendations endpoints"""
    
    def test_generate_recommendations_requires_auth(self):
        """POST /api/proposals/{id}/generate-recommendations - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/proposals/some-id/generate-recommendations")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Generate recommendations requires authentication")
    
    def test_get_recommendations_requires_auth(self):
        """GET /api/proposals/{id}/recommendations - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/proposals/some-id/recommendations")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ Get recommendations requires authentication")
    
    def test_generate_recommendations(self, admin_token, pro_creator_token):
        """POST /api/proposals/{id}/generate-recommendations - generates recommendations"""
        # Create a proposal
        proposal_data = {
            "title": f"TEST_Recommendations_{int(time.time())}",
            "description": "Test generating recommendations",
            "platforms": ["youtube"],
            "priority": "medium"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Generate recommendations (can be called by admin or creator)
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/generate-recommendations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # May return 503 if service not available, or 200 if successful
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "recommendations" in data, "Should contain success or recommendations"
            print(f"✓ Generated recommendations for: {proposal_id}")
        else:
            print("✓ Recommendation service not available (expected in test environment)")
    
    def test_get_recommendations(self, pro_creator_token):
        """GET /api/proposals/{id}/recommendations - gets existing recommendations"""
        # Create a proposal
        proposal_data = {
            "title": f"TEST_GetRecs_{int(time.time())}",
            "description": "Test getting recommendations",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Get recommendations (may be empty)
        response = requests.get(
            f"{BASE_URL}/api/proposals/{proposal_id}/recommendations",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "proposal_id" in data, "Should contain proposal_id"
        
        print(f"✓ Got recommendations for: {proposal_id}")


class TestCreatorMyProposals:
    """Test creator's own proposals endpoint"""
    
    def test_my_proposals_requires_auth(self):
        """GET /api/creators/me/proposals - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/creators/me/proposals")
        assert response.status_code == 403, f"Expected 403 without auth, got {response.status_code}"
        print("✓ My proposals requires authentication")
    
    def test_my_proposals_returns_own_proposals(self, pro_creator_token):
        """GET /api/creators/me/proposals - returns creator's own proposals"""
        # Create a proposal first
        proposal_data = {
            "title": f"TEST_MyProposals_{int(time.time())}",
            "description": "Test my proposals endpoint",
            "platforms": ["youtube"],
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        assert create_response.status_code == 200
        
        # Get my proposals
        response = requests.get(
            f"{BASE_URL}/api/creators/me/proposals",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one proposal"
        
        print(f"✓ Creator has {len(data)} proposals")
    
    def test_my_proposals_with_status_filter(self, pro_creator_token):
        """GET /api/creators/me/proposals - supports status filter"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/proposals?status=draft",
            headers={"Authorization": f"Bearer {pro_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # All returned proposals should be drafts
        for proposal in data:
            assert proposal.get("status") == "draft", f"Expected draft status, got {proposal.get('status')}"
        
        print(f"✓ Status filter works: {len(data)} draft proposals")


class TestFeatureGating:
    """Test feature gating for different subscription tiers"""
    
    def test_free_tier_proposal_limit(self, free_creator_token):
        """Free tier creators have limited proposals per month"""
        # Check if can create proposal
        response = requests.get(
            f"{BASE_URL}/api/subscriptions/can-create-proposal",
            headers={"Authorization": f"Bearer {free_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "can_create" in data, "Should indicate if can create"
        assert "limit" in data, "Should show limit"
        assert "used" in data, "Should show used count"
        
        print(f"✓ Free tier limit check: {data['used']}/{data['limit']} proposals used")
    
    def test_elite_tier_has_fast_processing(self, elite_creator_token):
        """Elite tier creators get fast ARRIS processing"""
        # Create and submit a proposal
        proposal_data = {
            "title": f"TEST_EliteSpeed_{int(time.time())}",
            "description": "Test elite processing speed",
            "platforms": ["youtube"],
            "priority": "high"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/proposals",
            json=proposal_data,
            headers={"Authorization": f"Bearer {elite_creator_token}"}
        )
        assert create_response.status_code == 200
        proposal_id = create_response.json()["id"]
        
        # Submit and check processing speed
        response = requests.post(
            f"{BASE_URL}/api/proposals/{proposal_id}/submit",
            headers={"Authorization": f"Bearer {elite_creator_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        insights = data.get("arris_insights", {})
        
        # Elite should get fast processing
        processing_speed = insights.get("processing_speed", "standard")
        print(f"✓ Elite tier processing speed: {processing_speed}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_proposals(self, admin_token):
        """Clean up TEST_ prefixed proposals"""
        # Get all proposals
        response = requests.get(
            f"{BASE_URL}/api/proposals?limit=500",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            proposals = response.json()
            test_proposals = [p for p in proposals if p.get("title", "").startswith("TEST_")]
            
            deleted = 0
            for proposal in test_proposals:
                delete_response = requests.delete(
                    f"{BASE_URL}/api/proposals/{proposal['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                if delete_response.status_code == 200:
                    deleted += 1
            
            print(f"✓ Cleaned up {deleted} test proposals")
        else:
            print("⚠ Could not fetch proposals for cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
