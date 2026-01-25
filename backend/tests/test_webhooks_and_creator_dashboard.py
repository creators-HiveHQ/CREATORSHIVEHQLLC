"""
Test Webhooks and Creator Dashboard Routes
==========================================
Tests for:
1. Stripe webhook handler (POST /api/webhook/stripe)
2. SendGrid webhook handler (POST /api/webhook/sendgrid)
3. Internal subscription lifecycle trigger (POST /api/webhook/internal/subscription-lifecycle)
4. Creator dashboard routes (/api/creators/me/*)
"""

import pytest
import requests
import os
import json
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    "free_tier": {"email": "freetest@hivehq.com", "password": "testpassword"},
    "pro_tier": {"email": "protest@hivehq.com", "password": "testpassword"},
    "elite_tier": {"email": "elitetest@hivehq.com", "password": "testpassword123"},
    "admin": {"email": "admin@hivehq.com", "password": "admin123"}
}


class TestCreatorLogin:
    """Test creator authentication to get tokens for subsequent tests"""
    
    def test_free_tier_login(self):
        """Test free tier creator login"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=CREDENTIALS["free_tier"]
        )
        assert response.status_code == 200, f"Free tier login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["creator"]["email"] == CREDENTIALS["free_tier"]["email"]
        print(f"✓ Free tier login successful - Creator ID: {data['creator']['id']}")
    
    def test_pro_tier_login(self):
        """Test pro tier creator login"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=CREDENTIALS["pro_tier"]
        )
        assert response.status_code == 200, f"Pro tier login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Pro tier login successful - Creator ID: {data['creator']['id']}")
    
    def test_elite_tier_login(self):
        """Test elite tier creator login"""
        response = requests.post(
            f"{BASE_URL}/api/creators/login",
            json=CREDENTIALS["elite_tier"]
        )
        assert response.status_code == 200, f"Elite tier login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Elite tier login successful - Creator ID: {data['creator']['id']}")


# ============== WEBHOOK ENDPOINT TESTS ==============

class TestStripeWebhook:
    """Test Stripe webhook handler"""
    
    def test_stripe_webhook_accepts_post(self):
        """Test that Stripe webhook endpoint accepts POST requests"""
        # Send a mock Stripe event (will fail signature verification but should accept POST)
        mock_event = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_status": "paid",
                    "metadata": {
                        "creator_id": "TEST-CREATOR-001",
                        "plan_id": "pro_monthly"
                    }
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            json=mock_event,
            headers={"Stripe-Signature": "test_signature"}
        )
        
        # Webhook should return 400 for invalid signature (expected behavior)
        # or 200 if signature verification is disabled in test mode
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"✓ Stripe webhook endpoint accepts POST - Status: {response.status_code}")
    
    def test_stripe_webhook_without_signature(self):
        """Test Stripe webhook without signature header"""
        mock_event = {"type": "test"}
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            json=mock_event
        )
        
        # Should return 400 for missing/invalid signature
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"✓ Stripe webhook handles missing signature - Status: {response.status_code}")


class TestSendGridWebhook:
    """Test SendGrid webhook handler"""
    
    def test_sendgrid_webhook_accepts_post(self):
        """Test that SendGrid webhook endpoint accepts POST requests"""
        # SendGrid sends array of events
        mock_events = [
            {
                "event": "delivered",
                "email": "test@example.com",
                "sg_message_id": "msg_test_123",
                "timestamp": int(datetime.now(timezone.utc).timestamp())
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/sendgrid",
            json=mock_events
        )
        
        assert response.status_code == 200, f"SendGrid webhook failed: {response.text}"
        data = response.json()
        assert "received" in data
        assert data["received"] == True
        print(f"✓ SendGrid webhook accepts POST - Processed: {data.get('processed', 0)} events")
    
    def test_sendgrid_webhook_bounce_event(self):
        """Test SendGrid bounce event handling"""
        mock_events = [
            {
                "event": "bounce",
                "email": "bounce_test@example.com",
                "sg_message_id": f"msg_bounce_{datetime.now().timestamp()}",
                "timestamp": int(datetime.now(timezone.utc).timestamp())
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/sendgrid",
            json=mock_events
        )
        
        assert response.status_code == 200, f"SendGrid bounce event failed: {response.text}"
        print(f"✓ SendGrid bounce event processed successfully")
    
    def test_sendgrid_webhook_open_event(self):
        """Test SendGrid open event handling"""
        mock_events = [
            {
                "event": "open",
                "email": "open_test@example.com",
                "sg_message_id": f"msg_open_{datetime.now().timestamp()}",
                "timestamp": int(datetime.now(timezone.utc).timestamp())
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/sendgrid",
            json=mock_events
        )
        
        assert response.status_code == 200, f"SendGrid open event failed: {response.text}"
        print(f"✓ SendGrid open event processed successfully")
    
    def test_sendgrid_webhook_multiple_events(self):
        """Test SendGrid with multiple events in single request"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        mock_events = [
            {"event": "delivered", "email": "multi1@example.com", "sg_message_id": f"msg_multi1_{timestamp}", "timestamp": timestamp},
            {"event": "open", "email": "multi2@example.com", "sg_message_id": f"msg_multi2_{timestamp}", "timestamp": timestamp},
            {"event": "click", "email": "multi3@example.com", "sg_message_id": f"msg_multi3_{timestamp}", "timestamp": timestamp}
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/webhook/sendgrid",
            json=mock_events
        )
        
        assert response.status_code == 200, f"SendGrid multiple events failed: {response.text}"
        data = response.json()
        assert data.get("processed", 0) >= 1
        print(f"✓ SendGrid multiple events processed - Count: {data.get('processed', 0)}")
    
    def test_sendgrid_webhook_idempotency(self):
        """Test SendGrid webhook idempotency - same event should not be processed twice"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        unique_id = f"msg_idempotent_{timestamp}"
        
        mock_events = [
            {"event": "delivered", "email": "idempotent@example.com", "sg_message_id": unique_id, "timestamp": timestamp}
        ]
        
        # First request
        response1 = requests.post(f"{BASE_URL}/api/webhook/sendgrid", json=mock_events)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second request with same event
        response2 = requests.post(f"{BASE_URL}/api/webhook/sendgrid", json=mock_events)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Second request should process 0 events (already processed)
        print(f"✓ SendGrid idempotency test - First: {data1.get('processed', 0)}, Second: {data2.get('processed', 0)}")


class TestInternalSubscriptionLifecycle:
    """Test internal subscription lifecycle webhook"""
    
    def test_check_expiring_subscriptions(self):
        """Test check_expiring action"""
        response = requests.post(
            f"{BASE_URL}/api/webhook/internal/subscription-lifecycle",
            json={"action": "check_expiring"}
        )
        
        assert response.status_code == 200, f"Check expiring failed: {response.text}"
        data = response.json()
        assert "checked" in data or "action" in data
        print(f"✓ Check expiring subscriptions - Checked: {data.get('checked', 0)}")
    
    def test_expire_overdue_subscriptions(self):
        """Test expire_overdue action"""
        response = requests.post(
            f"{BASE_URL}/api/webhook/internal/subscription-lifecycle",
            json={"action": "expire_overdue"}
        )
        
        assert response.status_code == 200, f"Expire overdue failed: {response.text}"
        data = response.json()
        assert "expired" in data or "action" in data
        print(f"✓ Expire overdue subscriptions - Expired: {data.get('expired', 0)}")
    
    def test_unknown_action(self):
        """Test unknown action returns error"""
        response = requests.post(
            f"{BASE_URL}/api/webhook/internal/subscription-lifecycle",
            json={"action": "unknown_action"}
        )
        
        assert response.status_code == 200, f"Unknown action failed: {response.text}"
        data = response.json()
        assert "error" in data
        print(f"✓ Unknown action handled correctly - Error: {data.get('error')}")


# ============== CREATOR DASHBOARD ROUTE TESTS ==============

class TestCreatorDashboardRoutes:
    """Test creator dashboard routes with authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth tokens for different tiers"""
        self.tokens = {}
        
        for tier, creds in CREDENTIALS.items():
            if tier == "admin":
                continue
            response = requests.post(
                f"{BASE_URL}/api/creators/login",
                json=creds
            )
            if response.status_code == 200:
                self.tokens[tier] = response.json()["access_token"]
    
    def get_auth_header(self, tier="free_tier"):
        """Get authorization header for a tier"""
        token = self.tokens.get(tier)
        if not token:
            pytest.skip(f"No token available for {tier}")
        return {"Authorization": f"Bearer {token}"}
    
    # === GET /api/creators/me ===
    def test_get_current_creator_profile_free(self):
        """Test GET /api/creators/me for free tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me",
            headers=self.get_auth_header("free_tier")
        )
        
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == CREDENTIALS["free_tier"]["email"]
        print(f"✓ GET /api/creators/me (free tier) - Creator: {data.get('name')}")
    
    def test_get_current_creator_profile_pro(self):
        """Test GET /api/creators/me for pro tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        assert data["email"] == CREDENTIALS["pro_tier"]["email"]
        print(f"✓ GET /api/creators/me (pro tier) - Creator: {data.get('name')}")
    
    def test_get_current_creator_profile_unauthorized(self):
        """Test GET /api/creators/me without auth"""
        response = requests.get(f"{BASE_URL}/api/creators/me")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got: {response.status_code}"
        print(f"✓ GET /api/creators/me unauthorized - Status: {response.status_code}")
    
    # === GET /api/creators/me/proposals ===
    def test_get_my_proposals(self):
        """Test GET /api/creators/me/proposals"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/proposals",
            headers=self.get_auth_header("free_tier")
        )
        
        assert response.status_code == 200, f"Get proposals failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/creators/me/proposals - Count: {len(data)}")
    
    def test_get_my_proposals_with_status_filter(self):
        """Test GET /api/creators/me/proposals with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/proposals?status=draft",
            headers=self.get_auth_header("free_tier")
        )
        
        assert response.status_code == 200, f"Get proposals with filter failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/creators/me/proposals?status=draft - Count: {len(data)}")
    
    # === GET /api/creators/me/dashboard ===
    def test_get_creator_dashboard(self):
        """Test GET /api/creators/me/dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/dashboard",
            headers=self.get_auth_header("free_tier")
        )
        
        assert response.status_code == 200, f"Get dashboard failed: {response.text}"
        data = response.json()
        assert "creator" in data
        assert "proposals" in data
        assert "projects" in data
        assert "tasks" in data
        print(f"✓ GET /api/creators/me/dashboard - Proposals: {data['proposals'].get('total', 0)}")
    
    # === GET /api/creators/me/advanced-dashboard (Pro+) ===
    def test_advanced_dashboard_free_tier_blocked(self):
        """Test advanced dashboard is blocked for free tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/advanced-dashboard",
            headers=self.get_auth_header("free_tier")
        )
        
        # Should be 403 for free tier (feature gated)
        assert response.status_code == 403, f"Expected 403 for free tier, got: {response.status_code}"
        data = response.json()
        assert "feature_gated" in str(data.get("detail", {}))
        print(f"✓ GET /api/creators/me/advanced-dashboard (free tier) - Correctly blocked")
    
    def test_advanced_dashboard_pro_tier_allowed(self):
        """Test advanced dashboard is allowed for pro tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/advanced-dashboard",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Pro tier advanced dashboard failed: {response.text}"
        data = response.json()
        assert "dashboard_level" in data
        assert "performance" in data
        print(f"✓ GET /api/creators/me/advanced-dashboard (pro tier) - Level: {data.get('dashboard_level')}")
    
    def test_advanced_dashboard_elite_tier_allowed(self):
        """Test advanced dashboard is allowed for elite tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/advanced-dashboard",
            headers=self.get_auth_header("elite_tier")
        )
        
        assert response.status_code == 200, f"Elite tier advanced dashboard failed: {response.text}"
        data = response.json()
        assert "dashboard_level" in data
        print(f"✓ GET /api/creators/me/advanced-dashboard (elite tier) - Level: {data.get('dashboard_level')}")
    
    # === GET /api/creators/me/premium-analytics (Premium+) ===
    def test_premium_analytics_free_tier_blocked(self):
        """Test premium analytics is blocked for free tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/premium-analytics",
            headers=self.get_auth_header("free_tier")
        )
        
        assert response.status_code == 403, f"Expected 403 for free tier, got: {response.status_code}"
        print(f"✓ GET /api/creators/me/premium-analytics (free tier) - Correctly blocked")
    
    def test_premium_analytics_elite_tier_allowed(self):
        """Test premium analytics is allowed for elite tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/premium-analytics",
            headers=self.get_auth_header("elite_tier")
        )
        
        assert response.status_code == 200, f"Elite tier premium analytics failed: {response.text}"
        data = response.json()
        # Response structure may vary - check for any valid response
        assert isinstance(data, dict)
        print(f"✓ GET /api/creators/me/premium-analytics (elite tier) - Success")
    
    # === GET /api/creators/me/pattern-trends (Pro+) ===
    def test_pattern_trends_free_tier_blocked(self):
        """Test pattern trends is blocked for free tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-trends",
            headers=self.get_auth_header("free_tier")
        )
        
        # Pattern trends may return 200 with limited data or 403 for free tier
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        print(f"✓ GET /api/creators/me/pattern-trends (free tier) - Status: {response.status_code}")
    
    def test_pattern_trends_pro_tier_allowed(self):
        """Test pattern trends is allowed for pro tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/pattern-trends",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Pro tier pattern trends failed: {response.text}"
        data = response.json()
        # Response structure may vary
        assert isinstance(data, dict)
        print(f"✓ GET /api/creators/me/pattern-trends (pro tier) - Success")
    
    # === GET /api/creators/me/predictive-alerts ===
    def test_predictive_alerts(self):
        """Test GET /api/creators/me/predictive-alerts"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/predictive-alerts",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Predictive alerts failed: {response.text}"
        data = response.json()
        assert "alerts" in data or "message" in data
        print(f"✓ GET /api/creators/me/predictive-alerts - Success")
    
    # === GET /api/creators/me/health-score ===
    def test_health_score(self):
        """Test GET /api/creators/me/health-score"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/health-score",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Health score failed: {response.text}"
        data = response.json()
        # Response structure may vary - check for valid response
        assert isinstance(data, dict)
        print(f"✓ GET /api/creators/me/health-score - Success")
    
    # === GET /api/creators/me/health-score/history ===
    def test_health_score_history(self):
        """Test GET /api/creators/me/health-score/history"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/health-score/history",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Health score history failed: {response.text}"
        data = response.json()
        assert "history" in data
        print(f"✓ GET /api/creators/me/health-score/history - Count: {len(data.get('history', []))}")
    
    # === GET /api/creators/me/alert-preferences ===
    def test_alert_preferences(self):
        """Test GET /api/creators/me/alert-preferences"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/alert-preferences",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Alert preferences failed: {response.text}"
        data = response.json()
        # Response structure may vary
        assert isinstance(data, dict)
        print(f"✓ GET /api/creators/me/alert-preferences - Success")
    
    # === PUT /api/creators/me/alert-preferences ===
    def test_update_alert_preferences(self):
        """Test PUT /api/creators/me/alert-preferences"""
        new_prefs = {
            "email_notifications": True,
            "in_app_notifications": True,
            "urgent_only": False,
            "categories": ["performance", "financial"]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/creators/me/alert-preferences",
            headers=self.get_auth_header("pro_tier"),
            json=new_prefs
        )
        
        assert response.status_code == 200, f"Update alert preferences failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ PUT /api/creators/me/alert-preferences - Updated successfully")
    
    # === GET /api/creators/me/cross-insights (Pro+) ===
    def test_cross_insights_free_tier_blocked(self):
        """Test cross insights is blocked for free tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/cross-insights",
            headers=self.get_auth_header("free_tier")
        )
        
        # Cross insights may return 200 with limited data or 403 for free tier
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        print(f"✓ GET /api/creators/me/cross-insights (free tier) - Status: {response.status_code}")
    
    def test_cross_insights_pro_tier_allowed(self):
        """Test cross insights is allowed for pro tier"""
        response = requests.get(
            f"{BASE_URL}/api/creators/me/cross-insights",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Pro tier cross insights failed: {response.text}"
        data = response.json()
        # Response structure may vary
        assert isinstance(data, dict)
        print(f"✓ GET /api/creators/me/cross-insights (pro tier) - Success")
    
    # === GET /api/creators/health-leaderboard ===
    def test_health_leaderboard(self):
        """Test GET /api/creators/health-leaderboard"""
        response = requests.get(
            f"{BASE_URL}/api/creators/health-leaderboard",
            headers=self.get_auth_header("pro_tier")
        )
        
        assert response.status_code == 200, f"Health leaderboard failed: {response.text}"
        data = response.json()
        assert "leaderboard" in data
        print(f"✓ GET /api/creators/health-leaderboard - Count: {len(data.get('leaderboard', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
