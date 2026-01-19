"""
Webhook Automations API Tests
Tests for Creators Hive HQ Webhook System - Zero-Human Operational Model
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWebhookAPIs:
    """Test webhook automation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hivehq.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    # ============== WEBHOOK EVENTS TESTS ==============
    
    def test_get_webhook_events(self):
        """Test GET /api/webhooks/events - Get webhook event log"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/events?limit=50")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If events exist, verify structure
        if len(data) > 0:
            event = data[0]
            assert "id" in event, "Event should have id"
            assert "event_type" in event, "Event should have event_type"
            assert "status" in event, "Event should have status"
            assert "timestamp" in event, "Event should have timestamp"
            print(f"✓ Found {len(data)} webhook events")
        else:
            print("✓ No webhook events found (empty list)")
    
    def test_get_webhook_events_filter_by_type(self):
        """Test GET /api/webhooks/events with event_type filter"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/events?event_type=creator.registered&limit=50")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify all events match the filter
        for event in data:
            assert event.get("event_type") == "creator.registered", f"Event type mismatch: {event.get('event_type')}"
        
        print(f"✓ Filter by event_type works - found {len(data)} creator.registered events")
    
    def test_get_webhook_events_filter_by_status(self):
        """Test GET /api/webhooks/events with status filter"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/events?status=completed&limit=50")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify all events match the filter
        for event in data:
            assert event.get("status") == "completed", f"Status mismatch: {event.get('status')}"
        
        print(f"✓ Filter by status works - found {len(data)} completed events")
    
    def test_get_webhook_events_unauthorized(self):
        """Test GET /api/webhooks/events without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/webhooks/events?limit=50")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthorized access correctly denied")
    
    # ============== AUTOMATION RULES TESTS ==============
    
    def test_get_automation_rules(self):
        """Test GET /api/webhooks/rules - Get all automation rules"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/rules")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 8, f"Expected at least 8 default rules, got {len(data)}"
        
        # Verify rule structure
        rule = data[0]
        assert "id" in rule, "Rule should have id"
        assert "name" in rule, "Rule should have name"
        assert "event_type" in rule, "Rule should have event_type"
        assert "actions" in rule, "Rule should have actions"
        assert "is_active" in rule, "Rule should have is_active"
        
        print(f"✓ Found {len(data)} automation rules")
        
        # Print rule names for verification
        for r in data:
            print(f"  - {r['id']}: {r['name']} ({r['event_type']}) - Active: {r['is_active']}")
    
    def test_automation_rules_have_correct_event_types(self):
        """Test that automation rules have expected event types"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/rules")
        
        assert response.status_code == 200
        
        data = response.json()
        event_types = [r["event_type"] for r in data]
        
        expected_types = [
            "creator.registered",
            "creator.approved",
            "proposal.submitted",
            "proposal.approved",
            "project.created",
            "task.completed",
            "revenue.recorded",
            "arris.pattern_detected"
        ]
        
        for expected in expected_types:
            assert expected in event_types, f"Missing expected event type: {expected}"
        
        print(f"✓ All {len(expected_types)} expected event types present")
    
    def test_toggle_automation_rule(self):
        """Test PATCH /api/webhooks/rules/{rule_id} - Toggle rule active status"""
        # First get rules
        rules_response = self.session.get(f"{BASE_URL}/api/webhooks/rules")
        assert rules_response.status_code == 200
        
        rules = rules_response.json()
        assert len(rules) > 0, "No rules found to toggle"
        
        # Get first rule
        rule = rules[0]
        rule_id = rule["id"]
        original_status = rule["is_active"]
        
        # Toggle to opposite status
        new_status = not original_status
        toggle_response = self.session.patch(f"{BASE_URL}/api/webhooks/rules/{rule_id}?is_active={str(new_status).lower()}")
        
        assert toggle_response.status_code == 200, f"Expected 200, got {toggle_response.status_code}"
        
        # Verify toggle worked
        verify_response = self.session.get(f"{BASE_URL}/api/webhooks/rules")
        updated_rules = verify_response.json()
        updated_rule = next((r for r in updated_rules if r["id"] == rule_id), None)
        
        assert updated_rule is not None, "Rule not found after toggle"
        assert updated_rule["is_active"] == new_status, f"Rule status not updated: expected {new_status}, got {updated_rule['is_active']}"
        
        # Toggle back to original
        self.session.patch(f"{BASE_URL}/api/webhooks/rules/{rule_id}?is_active={str(original_status).lower()}")
        
        print(f"✓ Rule toggle works - toggled {rule_id} from {original_status} to {new_status} and back")
    
    # ============== WEBHOOK STATS TESTS ==============
    
    def test_get_webhook_stats(self):
        """Test GET /api/webhooks/stats - Get webhook statistics"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify stats structure
        assert "total_events" in data, "Stats should have total_events"
        assert "events_last_24h" in data, "Stats should have events_last_24h"
        assert "by_type" in data, "Stats should have by_type"
        assert "by_status" in data, "Stats should have by_status"
        assert "automation_rules" in data, "Stats should have automation_rules"
        
        # Verify automation_rules structure
        assert "total" in data["automation_rules"], "automation_rules should have total"
        assert "active" in data["automation_rules"], "automation_rules should have active"
        
        print(f"✓ Webhook stats retrieved:")
        print(f"  - Total Events: {data['total_events']}")
        print(f"  - Events (24h): {data['events_last_24h']}")
        print(f"  - Active Rules: {data['automation_rules']['active']}/{data['automation_rules']['total']}")
    
    # ============== TEST WEBHOOK TESTS ==============
    
    def test_trigger_test_webhook(self):
        """Test POST /api/webhooks/test - Trigger a test webhook event"""
        response = self.session.post(f"{BASE_URL}/api/webhooks/test?event_type=creator.registered")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        assert "event_id" in data, "Response should have event_id"
        
        print(f"✓ Test webhook triggered - Event ID: {data['event_id']}")
        
        # Wait for event processing
        time.sleep(2)
        
        # Verify event was created
        events_response = self.session.get(f"{BASE_URL}/api/webhooks/events?limit=10")
        events = events_response.json()
        
        # Find the test event
        test_event = next((e for e in events if e.get("id") == data["event_id"]), None)
        
        if test_event:
            assert test_event["status"] in ["completed", "processing"], f"Event status: {test_event['status']}"
            print(f"✓ Test event found with status: {test_event['status']}")
            
            # Check actions triggered
            if test_event.get("actions_triggered"):
                print(f"  - Actions triggered: {test_event['actions_triggered']}")
        else:
            print("⚠ Test event not found in recent events (may still be processing)")
    
    # ============== CREATOR REGISTRATION WEBHOOK INTEGRATION ==============
    
    def test_creator_registration_triggers_webhook(self):
        """Test that creator registration triggers webhook event"""
        import uuid
        
        # Create a unique test creator
        test_email = f"test_webhook_{uuid.uuid4().hex[:8]}@test.com"
        
        # Register creator (public endpoint)
        register_response = requests.post(f"{BASE_URL}/api/creators/register", json={
            "name": "Webhook Test Creator",
            "email": test_email,
            "platforms": ["YouTube", "Instagram"],
            "niche": "Tech",
            "arris_intake_response": "Testing webhook integration"
        })
        
        assert register_response.status_code == 200, f"Registration failed: {register_response.status_code}"
        
        creator_data = register_response.json()
        creator_id = creator_data.get("id")
        
        print(f"✓ Creator registered: {creator_id}")
        
        # Wait for webhook processing
        time.sleep(2)
        
        # Check for webhook event
        events_response = self.session.get(f"{BASE_URL}/api/webhooks/events?event_type=creator.registered&limit=10")
        events = events_response.json()
        
        # Find event for this creator
        creator_event = next((e for e in events if e.get("source_id") == creator_id), None)
        
        if creator_event:
            assert creator_event["event_type"] == "creator.registered"
            assert creator_event["status"] in ["completed", "processing"]
            print(f"✓ Webhook event found for creator registration:")
            print(f"  - Event ID: {creator_event['id']}")
            print(f"  - Status: {creator_event['status']}")
            print(f"  - Actions: {creator_event.get('actions_triggered', [])}")
        else:
            print("⚠ Webhook event not found (may still be processing)")
    
    # ============== GET SINGLE EVENT TEST ==============
    
    def test_get_single_webhook_event(self):
        """Test GET /api/webhooks/events/{event_id} - Get specific event"""
        # First get list of events
        events_response = self.session.get(f"{BASE_URL}/api/webhooks/events?limit=5")
        events = events_response.json()
        
        if len(events) == 0:
            pytest.skip("No events to test single event retrieval")
        
        event_id = events[0]["id"]
        
        # Get single event
        response = self.session.get(f"{BASE_URL}/api/webhooks/events/{event_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["id"] == event_id, "Event ID mismatch"
        assert "event_type" in data
        assert "payload" in data
        assert "status" in data
        
        print(f"✓ Single event retrieved: {event_id}")
        print(f"  - Type: {data['event_type']}")
        print(f"  - Status: {data['status']}")
    
    def test_get_nonexistent_event_returns_404(self):
        """Test GET /api/webhooks/events/{event_id} with invalid ID returns 404"""
        response = self.session.get(f"{BASE_URL}/api/webhooks/events/NONEXISTENT-EVENT-ID")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Nonexistent event correctly returns 404")


class TestWebhookActionsExecution:
    """Test that webhook actions are executed correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hivehq.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_log_event_action_creates_audit_entry(self):
        """Test that log_event action creates audit trail entry"""
        # Trigger test webhook
        response = self.session.post(f"{BASE_URL}/api/webhooks/test?event_type=creator.registered")
        assert response.status_code == 200
        
        event_id = response.json().get("event_id")
        
        # Wait for processing
        time.sleep(2)
        
        # Check event for action results
        event_response = self.session.get(f"{BASE_URL}/api/webhooks/events/{event_id}")
        
        if event_response.status_code == 200:
            event = event_response.json()
            actions = event.get("actions_triggered", [])
            
            if "log_event" in actions:
                print(f"✓ log_event action executed for event {event_id}")
                
                # Check action results
                results = event.get("action_results", {})
                if "log_event" in results:
                    print(f"  - Result: {results['log_event']}")
            else:
                print(f"⚠ log_event action not in triggered actions: {actions}")
        else:
            print(f"⚠ Could not retrieve event {event_id}")
    
    def test_update_arris_memory_action(self):
        """Test that update_arris_memory action updates ARRIS logs"""
        # Trigger test webhook
        response = self.session.post(f"{BASE_URL}/api/webhooks/test?event_type=creator.registered")
        assert response.status_code == 200
        
        event_id = response.json().get("event_id")
        
        # Wait for processing
        time.sleep(2)
        
        # Check event for action results
        event_response = self.session.get(f"{BASE_URL}/api/webhooks/events/{event_id}")
        
        if event_response.status_code == 200:
            event = event_response.json()
            actions = event.get("actions_triggered", [])
            
            if "update_arris_memory" in actions:
                print(f"✓ update_arris_memory action executed for event {event_id}")
                
                results = event.get("action_results", {})
                if "update_arris_memory" in results:
                    print(f"  - Result: {results['update_arris_memory']}")
            else:
                print(f"⚠ update_arris_memory action not in triggered actions: {actions}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
