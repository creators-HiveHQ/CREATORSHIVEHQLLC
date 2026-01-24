"""
Test suite for Landing Page and Priority Waitlist System
Features tested:
- Public waitlist signup with form validation
- Referral code generation and tracking
- Priority score increases when referred (+5 bonus)
- Position tracking in queue
- Admin waitlist management dashboard
"""

import pytest
import requests
import os
import time
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://creatorshivehq.preview.emergentagent.com')

# Admin credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"


def generate_random_email():
    """Generate a unique test email"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_waitlist_{random_str}@example.com"


def generate_random_name():
    """Generate a random test name"""
    first_names = ["Test", "Demo", "Sample", "Example", "Mock"]
    last_names = ["User", "Creator", "Person", "Account", "Tester"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


class TestPublicWaitlistEndpoints:
    """Test public waitlist endpoints (no auth required)"""
    
    def test_get_waitlist_stats(self):
        """GET /api/waitlist/stats - public stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/waitlist/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)
        print(f"✓ Waitlist stats: {data['total']} total signups")
    
    def test_get_creator_types(self):
        """GET /api/waitlist/creator-types - get available creator types"""
        response = requests.get(f"{BASE_URL}/api/waitlist/creator-types")
        assert response.status_code == 200
        data = response.json()
        assert "creator_types" in data
        assert len(data["creator_types"]) == 11  # 11 creator types defined
        
        # Verify structure
        for ct in data["creator_types"]:
            assert "id" in ct
            assert "name" in ct
            assert "icon" in ct
        
        print(f"✓ Creator types: {len(data['creator_types'])} types available")
    
    def test_waitlist_signup_success(self):
        """POST /api/waitlist/signup - create new waitlist entry"""
        email = generate_random_email()
        name = generate_random_name()
        
        payload = {
            "email": email,
            "name": name,
            "creator_type": "youtuber",
            "niche": "Tech Reviews"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "id" in data
        assert "position" in data
        assert "referral_code" in data
        assert "priority_score" in data
        assert data["priority_score"] == 10  # Base signup points
        
        print(f"✓ Signup successful: position #{data['position']}, referral code: {data['referral_code']}")
        
        # Store for cleanup
        return data
    
    def test_waitlist_signup_validation_missing_email(self):
        """POST /api/waitlist/signup - validation: email required"""
        payload = {
            "name": "Test User",
            "creator_type": "youtuber"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json=payload
        )
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]
        print("✓ Validation: missing email rejected")
    
    def test_waitlist_signup_validation_missing_name(self):
        """POST /api/waitlist/signup - validation: name required"""
        payload = {
            "email": generate_random_email(),
            "creator_type": "youtuber"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json=payload
        )
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]
        print("✓ Validation: missing name rejected")
    
    def test_waitlist_signup_validation_missing_creator_type(self):
        """POST /api/waitlist/signup - validation: creator_type required"""
        payload = {
            "email": generate_random_email(),
            "name": "Test User"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json=payload
        )
        
        # Should fail validation
        assert response.status_code in [400, 422, 500]
        print("✓ Validation: missing creator_type rejected")
    
    def test_waitlist_signup_duplicate_email(self):
        """POST /api/waitlist/signup - duplicate email rejected"""
        email = generate_random_email()
        name = generate_random_name()
        
        # First signup
        payload = {
            "email": email,
            "name": name,
            "creator_type": "youtuber"
        }
        
        response1 = requests.post(f"{BASE_URL}/api/waitlist/signup", json=payload)
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = requests.post(f"{BASE_URL}/api/waitlist/signup", json=payload)
        assert response2.status_code == 200
        data = response2.json()
        assert data["success"] == False
        assert "already on the waitlist" in data["error"].lower()
        
        print("✓ Duplicate email rejected with appropriate message")
    
    def test_get_position_by_email(self):
        """GET /api/waitlist/position?email= - get position by email"""
        # First create a signup
        email = generate_random_email()
        name = generate_random_name()
        
        signup_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": email, "name": name, "creator_type": "podcaster"}
        )
        assert signup_response.status_code == 200
        
        # Now get position
        response = requests.get(f"{BASE_URL}/api/waitlist/position?email={email}")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "name" in data
        assert "original_position" in data
        assert "current_position" in data
        assert "referral_code" in data
        assert "priority_score" in data
        assert "status" in data
        
        print(f"✓ Position retrieved: #{data['current_position']}, score: {data['priority_score']}")
    
    def test_get_position_invalid_email(self):
        """GET /api/waitlist/position - invalid email returns error"""
        response = requests.get(f"{BASE_URL}/api/waitlist/position?email=nonexistent@example.com")
        # API returns 404 for not found emails
        assert response.status_code in [200, 404]
        data = response.json()
        # Either "error" key or "detail" key for error message
        assert "error" in data or "detail" in data
        print("✓ Invalid email returns error message")
    
    def test_get_leaderboard(self):
        """GET /api/waitlist/leaderboard - get top referrers"""
        response = requests.get(f"{BASE_URL}/api/waitlist/leaderboard?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        print(f"✓ Leaderboard: {len(data['leaderboard'])} entries")


class TestReferralSystem:
    """Test referral code generation and tracking"""
    
    def test_referral_code_generated_on_signup(self):
        """Verify referral code is generated on signup"""
        email = generate_random_email()
        name = generate_random_name()
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": email, "name": name, "creator_type": "blogger"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert len(data["referral_code"]) > 0
        
        # Referral code should contain part of name
        name_part = name.split()[0].upper()[:6]
        assert name_part in data["referral_code"]
        
        print(f"✓ Referral code generated: {data['referral_code']}")
    
    def test_signup_with_referral_code_bonus(self):
        """Verify +5 priority bonus when signing up with referral code"""
        # First create a referrer
        referrer_email = generate_random_email()
        referrer_name = generate_random_name()
        
        referrer_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": referrer_email, "name": referrer_name, "creator_type": "streamer"}
        )
        assert referrer_response.status_code == 200
        referrer_data = referrer_response.json()
        referral_code = referrer_data["referral_code"]
        
        # Now signup with referral code
        referred_email = generate_random_email()
        referred_name = generate_random_name()
        
        referred_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={
                "email": referred_email,
                "name": referred_name,
                "creator_type": "musician",
                "referral_code": referral_code
            }
        )
        
        assert referred_response.status_code == 200
        referred_data = referred_response.json()
        
        # Should have base 10 + 5 bonus = 15 points
        assert referred_data["priority_score"] == 15
        
        print(f"✓ Referred signup has priority score: {referred_data['priority_score']} (10 base + 5 bonus)")
    
    def test_referrer_gets_points_when_referred(self):
        """Verify referrer gets +25 points when someone uses their code"""
        # Create referrer
        referrer_email = generate_random_email()
        referrer_name = generate_random_name()
        
        referrer_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": referrer_email, "name": referrer_name, "creator_type": "artist"}
        )
        assert referrer_response.status_code == 200
        referrer_data = referrer_response.json()
        referral_code = referrer_data["referral_code"]
        initial_score = referrer_data["priority_score"]  # Should be 10
        
        # Someone signs up with referral code
        referred_email = generate_random_email()
        referred_name = generate_random_name()
        
        requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={
                "email": referred_email,
                "name": referred_name,
                "creator_type": "educator",
                "referral_code": referral_code
            }
        )
        
        # Check referrer's updated score
        position_response = requests.get(f"{BASE_URL}/api/waitlist/position?email={referrer_email}")
        assert position_response.status_code == 200
        updated_data = position_response.json()
        
        # Referrer should have 10 (base) + 25 (referral bonus) = 35
        assert updated_data["priority_score"] == initial_score + 25
        assert updated_data["referral_count"] == 1
        
        print(f"✓ Referrer score updated: {initial_score} -> {updated_data['priority_score']} (+25 for referral)")
    
    def test_get_referral_stats(self):
        """GET /api/waitlist/referral-stats - get referral statistics"""
        # Create a user first
        email = generate_random_email()
        name = generate_random_name()
        
        requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": email, "name": name, "creator_type": "business"}
        )
        
        response = requests.get(f"{BASE_URL}/api/waitlist/referral-stats?email={email}")
        assert response.status_code == 200
        data = response.json()
        
        assert "referral_code" in data
        assert "referral_count" in data
        assert "priority_score" in data
        assert "referrals" in data
        
        print(f"✓ Referral stats retrieved: {data['referral_count']} referrals")


class TestAdminWaitlistEndpoints:
    """Test admin waitlist management endpoints (auth required)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token before each test"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_waitlist_stats(self):
        """GET /api/admin/waitlist/stats - comprehensive stats (admin auth required)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/stats",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify comprehensive stats structure
        assert "total" in data
        assert "pending" in data
        assert "invited" in data
        assert "converted" in data
        assert "by_creator_type" in data
        assert "by_source" in data
        assert "daily_signups" in data
        assert "top_referrers" in data
        assert "conversion_rate" in data
        
        print(f"✓ Admin stats: {data['total']} total, {data['pending']} pending, {data['invited']} invited")
    
    def test_admin_waitlist_stats_unauthorized(self):
        """GET /api/admin/waitlist/stats - requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/waitlist/stats")
        assert response.status_code in [401, 403]
        print("✓ Admin stats requires authentication")
    
    def test_admin_get_signups(self):
        """GET /api/admin/waitlist/signups - list signups with filtering"""
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/signups",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "signups" in data
        assert "total" in data
        assert isinstance(data["signups"], list)
        
        if len(data["signups"]) > 0:
            signup = data["signups"][0]
            assert "id" in signup
            assert "email" in signup
            assert "name" in signup
            assert "creator_type" in signup
            assert "status" in signup
            assert "priority_score" in signup
        
        print(f"✓ Admin signups: {len(data['signups'])} returned, {data['total']} total")
    
    def test_admin_get_signups_with_filters(self):
        """GET /api/admin/waitlist/signups - with status and creator_type filters"""
        # Test status filter
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/signups?status=pending",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Test creator_type filter
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/signups?creator_type=youtuber",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Test pagination
        response = requests.get(
            f"{BASE_URL}/api/admin/waitlist/signups?skip=0&limit=5",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["signups"]) <= 5
        
        print("✓ Admin signups filtering works correctly")
    
    def test_admin_get_signups_unauthorized(self):
        """GET /api/admin/waitlist/signups - requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/waitlist/signups")
        assert response.status_code in [401, 403]
        print("✓ Admin signups requires authentication")
    
    def test_admin_invite_users(self):
        """POST /api/admin/waitlist/invite - send invitations"""
        # First create a test signup
        email = generate_random_email()
        name = generate_random_name()
        
        signup_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": email, "name": name, "creator_type": "tiktoker"}
        )
        assert signup_response.status_code == 200
        signup_id = signup_response.json()["id"]
        
        # Now invite
        response = requests.post(
            f"{BASE_URL}/api/admin/waitlist/invite",
            headers=self.headers,
            json={"signup_ids": [signup_id]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["invited"] == 1
        
        print(f"✓ Admin invite: {data['invited']} user(s) invited")
    
    def test_admin_invite_unauthorized(self):
        """POST /api/admin/waitlist/invite - requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/admin/waitlist/invite",
            json={"signup_ids": ["test-id"]}
        )
        assert response.status_code in [401, 403]
        print("✓ Admin invite requires authentication")
    
    def test_admin_delete_signup(self):
        """DELETE /api/admin/waitlist/{signup_id} - delete signup"""
        # First create a test signup
        email = generate_random_email()
        name = generate_random_name()
        
        signup_response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json={"email": email, "name": name, "creator_type": "instagrammer"}
        )
        assert signup_response.status_code == 200
        signup_id = signup_response.json()["id"]
        
        # Now delete
        response = requests.delete(
            f"{BASE_URL}/api/admin/waitlist/{signup_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Verify deleted - API returns 404 for not found
        position_response = requests.get(f"{BASE_URL}/api/waitlist/position?email={email}")
        assert position_response.status_code == 404 or "error" in position_response.json() or "detail" in position_response.json()
        
        print(f"✓ Admin delete: signup {signup_id} deleted successfully")
    
    def test_admin_delete_unauthorized(self):
        """DELETE /api/admin/waitlist/{signup_id} - requires auth"""
        response = requests.delete(f"{BASE_URL}/api/admin/waitlist/test-id")
        assert response.status_code in [401, 403]
        print("✓ Admin delete requires authentication")
    
    def test_admin_delete_nonexistent(self):
        """DELETE /api/admin/waitlist/{signup_id} - nonexistent signup"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/waitlist/NONEXISTENT-ID",
            headers=self.headers
        )
        
        # API returns 404 for nonexistent signup
        assert response.status_code in [200, 404]
        data = response.json()
        if response.status_code == 200:
            assert data["success"] == False
        else:
            assert "detail" in data or "error" in data
        
        print("✓ Admin delete nonexistent returns error")


class TestInvalidEmailFormat:
    """Test email validation"""
    
    def test_invalid_email_format(self):
        """POST /api/waitlist/signup - invalid email format rejected"""
        payload = {
            "email": "not-an-email",
            "name": "Test User",
            "creator_type": "youtuber"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/waitlist/signup",
            json=payload
        )
        
        # Should fail validation
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == False
            assert "invalid" in data.get("error", "").lower()
        else:
            assert response.status_code in [400, 422]
        
        print("✓ Invalid email format rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
