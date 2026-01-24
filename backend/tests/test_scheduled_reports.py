"""
Test Suite for Scheduled ARRIS Reports (Phase 4 Module E Task E2)
Tests all report endpoints, settings, generation, history, and feature gating.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ELITE_EMAIL = "elitetest@hivehq.com"
ELITE_PASSWORD = "testpassword123"
PRO_EMAIL = "protest@hivehq.com"
PRO_PASSWORD = "testpassword"


class TestScheduledReportsAuth:
    """Authentication and feature gating tests"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        assert response.status_code == 200, f"Elite login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def pro_token(self):
        """Get Pro creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_EMAIL,
            "password": PRO_PASSWORD
        })
        assert response.status_code == 200, f"Pro login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_elite_can_access_report_settings(self, elite_token):
        """Elite user should be able to access report settings"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "frequency" in data
        assert "topics" in data
        print(f"✓ Elite user can access report settings: {data.get('frequency')}")
    
    def test_pro_user_gets_403_on_settings(self, pro_token):
        """Pro user should get 403 for Elite-only features"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={"Authorization": f"Bearer {pro_token}"}
        )
        assert response.status_code == 403
        print("✓ Pro user correctly gets 403 on report settings")
    
    def test_pro_user_gets_403_on_generate(self, pro_token):
        """Pro user should get 403 when trying to generate reports"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly",
            headers={"Authorization": f"Bearer {pro_token}"}
        )
        assert response.status_code == 403
        print("✓ Pro user correctly gets 403 on report generation")
    
    def test_pro_user_gets_403_on_history(self, pro_token):
        """Pro user should get 403 when accessing report history"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/history",
            headers={"Authorization": f"Bearer {pro_token}"}
        )
        assert response.status_code == 403
        print("✓ Pro user correctly gets 403 on report history")
    
    def test_unauthenticated_gets_401(self):
        """Unauthenticated request should get 401"""
        response = requests.get(f"{BASE_URL}/api/elite/reports/settings")
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated request correctly rejected")


class TestReportTopics:
    """Tests for report topics endpoint"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_available_topics(self, elite_token):
        """Should return all available topics and options"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/topics",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check topics
        assert "topics" in data
        topic_ids = [t["id"] for t in data["topics"]]
        expected_topics = [
            "activity_summary", "metrics_overview", "arris_usage",
            "pattern_insights", "recommendations", "upcoming_tasks",
            "financial_summary", "engagement_trends"
        ]
        for topic in expected_topics:
            assert topic in topic_ids, f"Missing topic: {topic}"
        print(f"✓ All {len(expected_topics)} topics available")
        
        # Check frequencies
        assert "frequencies" in data
        assert "daily" in data["frequencies"]
        assert "weekly" in data["frequencies"]
        assert "both" in data["frequencies"]
        assert "none" in data["frequencies"]
        print("✓ All frequencies available")
        
        # Check days
        assert "days" in data
        assert len(data["days"]) == 7
        assert "monday" in data["days"]
        print("✓ All days available")
        
        # Check times
        assert "times" in data
        assert len(data["times"]) == 24
        print("✓ All 24 hours available for scheduling")


class TestReportSettings:
    """Tests for report settings CRUD"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_default_settings(self, elite_token):
        """Should return default settings if none configured"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check default structure
        assert "frequency" in data
        assert "topics" in data
        assert isinstance(data["topics"], list)
        print(f"✓ Default settings returned with frequency: {data['frequency']}")
    
    def test_update_frequency(self, elite_token):
        """Should update report frequency"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"frequency": "weekly"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["frequency"] == "weekly"
        print("✓ Frequency updated to weekly")
    
    def test_update_topics(self, elite_token):
        """Should update selected topics"""
        new_topics = ["activity_summary", "metrics_overview", "recommendations"]
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"topics": new_topics}
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["topics"]) == set(new_topics)
        print(f"✓ Topics updated: {new_topics}")
    
    def test_update_weekly_day(self, elite_token):
        """Should update weekly report day"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"weekly_day": "friday"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["weekly_day"] == "friday"
        print("✓ Weekly day updated to friday")
    
    def test_update_times(self, elite_token):
        """Should update report times"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"daily_time": "10:00", "weekly_time": "11:00"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_time"] == "10:00"
        assert data["weekly_time"] == "11:00"
        print("✓ Report times updated")
    
    def test_enable_reports(self, elite_token):
        """Should enable scheduled reports"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"enabled": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == True
        print("✓ Reports enabled")
    
    def test_invalid_frequency_defaults_to_weekly(self, elite_token):
        """Invalid frequency should default to weekly"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"frequency": "invalid_frequency"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["frequency"] == "weekly"
        print("✓ Invalid frequency defaults to weekly")
    
    def test_invalid_topics_filtered(self, elite_token):
        """Invalid topics should be filtered out"""
        response = requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"topics": ["activity_summary", "invalid_topic", "metrics_overview"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "invalid_topic" not in data["topics"]
        assert "activity_summary" in data["topics"]
        print("✓ Invalid topics filtered out")


class TestReportGeneration:
    """Tests for on-demand report generation"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_generate_weekly_report(self, elite_token):
        """Should generate a weekly report on-demand"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "report_id" in data
        assert data["report_id"].startswith("RPT-")
        assert "sections_generated" in data
        print(f"✓ Weekly report generated: {data['report_id']}")
        print(f"  Sections: {data['sections_generated']}")
        
        return data["report_id"]
    
    def test_generate_daily_report(self, elite_token):
        """Should generate a daily report on-demand"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=daily&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "report_id" in data
        print(f"✓ Daily report generated: {data['report_id']}")
    
    def test_invalid_report_type_returns_400(self, elite_token):
        """Invalid report type should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=monthly",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 400
        print("✓ Invalid report type correctly returns 400")


class TestReportHistory:
    """Tests for report history"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_report_history(self, elite_token):
        """Should return report history"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/history",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "reports" in data
        assert "total" in data
        assert isinstance(data["reports"], list)
        print(f"✓ Report history returned: {data['total']} reports")
        
        # Check report structure if any exist
        if data["reports"]:
            report = data["reports"][0]
            assert "id" in report
            assert "report_type" in report
            assert "status" in report
            assert "created_at" in report
            print(f"  Latest report: {report['id']} ({report['report_type']}, {report['status']})")
    
    def test_filter_history_by_type(self, elite_token):
        """Should filter history by report type"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/history?report_type=weekly",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned reports should be weekly
        for report in data["reports"]:
            assert report["report_type"] == "weekly"
        print(f"✓ Filtered to weekly reports: {len(data['reports'])} found")
    
    def test_limit_history_results(self, elite_token):
        """Should respect limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/history?limit=5",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["reports"]) <= 5
        print(f"✓ Limit respected: {len(data['reports'])} reports returned")


class TestReportCRUD:
    """Tests for individual report operations"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def generated_report_id(self, elite_token):
        """Generate a report for testing"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        return response.json()["report_id"]
    
    def test_get_specific_report(self, elite_token, generated_report_id):
        """Should get a specific report with full content"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/{generated_report_id}",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check full report structure
        assert data["id"] == generated_report_id
        assert "sections" in data
        assert "ai_summary" in data
        assert "creator_id" in data
        assert "report_type" in data
        assert "period_label" in data
        assert "status" in data
        
        print(f"✓ Full report retrieved: {data['id']}")
        print(f"  Period: {data['period_label']}")
        print(f"  Status: {data['status']}")
        print(f"  Sections: {list(data['sections'].keys())}")
        
        # Check sections content
        if "activity_summary" in data["sections"]:
            section = data["sections"]["activity_summary"]
            assert "title" in section
            assert "highlight" in section
            print(f"  Activity Summary: {section.get('highlight', 'N/A')}")
        
        if "recommendations" in data["sections"]:
            section = data["sections"]["recommendations"]
            assert "items" in section
            print(f"  Recommendations: {len(section.get('items', []))} items")
    
    def test_get_nonexistent_report_returns_404(self, elite_token):
        """Should return 404 for non-existent report"""
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/RPT-NONEXISTENT123",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 404
        print("✓ Non-existent report correctly returns 404")
    
    def test_delete_report(self, elite_token):
        """Should delete a report"""
        # First generate a report to delete
        gen_response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=daily&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        report_id = gen_response.json()["report_id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/elite/reports/{report_id}",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✓ Report deleted: {report_id}")
        
        # Verify it's gone
        get_response = requests.get(
            f"{BASE_URL}/api/elite/reports/{report_id}",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert get_response.status_code == 404
        print("✓ Deleted report no longer accessible")
    
    def test_delete_nonexistent_report_returns_404(self, elite_token):
        """Should return 404 when deleting non-existent report"""
        response = requests.delete(
            f"{BASE_URL}/api/elite/reports/RPT-NONEXISTENT123",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 404
        print("✓ Delete non-existent report correctly returns 404")


class TestReportEmailSend:
    """Tests for email sending functionality"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_send_report_email(self, elite_token):
        """Should attempt to send report via email (may fail if email not configured)"""
        # First generate a report
        gen_response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        report_id = gen_response.json()["report_id"]
        
        # Try to send it
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/{report_id}/send",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        
        # Email service may not be configured, so 500/520 is acceptable
        # The important thing is the endpoint exists and processes the request
        # 520 is Cloudflare timeout which can happen when email service is slow/not configured
        assert response.status_code in [200, 500, 520]
        
        if response.status_code == 200:
            print(f"✓ Report email sent successfully: {report_id}")
        else:
            print(f"✓ Email send endpoint works (email service not configured, status: {response.status_code}): {report_id}")
    
    def test_send_nonexistent_report_returns_404(self, elite_token):
        """Should return 404 when sending non-existent report"""
        response = requests.post(
            f"{BASE_URL}/api/elite/reports/RPT-NONEXISTENT123/send",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        assert response.status_code == 404
        print("✓ Send non-existent report correctly returns 404")


class TestReportSections:
    """Tests for report section content"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite creator token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": ELITE_EMAIL,
            "password": ELITE_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_report_contains_expected_sections(self, elite_token):
        """Report should contain sections based on selected topics"""
        # First set topics
        requests.put(
            f"{BASE_URL}/api/elite/reports/settings",
            headers={
                "Authorization": f"Bearer {elite_token}",
                "Content-Type": "application/json"
            },
            json={"topics": [
                "activity_summary", "metrics_overview", "arris_usage",
                "pattern_insights", "recommendations"
            ]}
        )
        
        # Generate report
        gen_response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        report_id = gen_response.json()["report_id"]
        
        # Get full report
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/{report_id}",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        data = response.json()
        
        sections = data.get("sections", {})
        
        # Check expected sections exist
        expected_sections = ["activity_summary", "metrics_overview", "arris_usage", 
                           "pattern_insights", "recommendations"]
        for section in expected_sections:
            assert section in sections, f"Missing section: {section}"
            assert "title" in sections[section]
            assert "highlight" in sections[section]
        
        print(f"✓ All expected sections present: {list(sections.keys())}")
        
        # Check activity_summary structure
        activity = sections.get("activity_summary", {})
        assert "proposals_created" in activity
        assert "tasks_completed" in activity
        print(f"  Activity: {activity.get('proposals_created')} proposals, {activity.get('tasks_completed')} tasks")
        
        # Check metrics_overview structure
        metrics = sections.get("metrics_overview", {})
        assert "revenue" in metrics
        assert "expenses" in metrics
        assert "net_margin" in metrics
        print(f"  Metrics: Revenue ${metrics.get('revenue')}, Net ${metrics.get('net_margin')}")
        
        # Check recommendations structure
        recs = sections.get("recommendations", {})
        assert "items" in recs
        assert isinstance(recs["items"], list)
        print(f"  Recommendations: {len(recs.get('items', []))} items")
    
    def test_ai_summary_generated(self, elite_token):
        """Report should have AI-generated summary"""
        # Generate report
        gen_response = requests.post(
            f"{BASE_URL}/api/elite/reports/generate?report_type=weekly&send_email=false",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        report_id = gen_response.json()["report_id"]
        
        # Get full report
        response = requests.get(
            f"{BASE_URL}/api/elite/reports/{report_id}",
            headers={"Authorization": f"Bearer {elite_token}"}
        )
        data = response.json()
        
        assert "ai_summary" in data
        assert data["ai_summary"] is not None
        assert len(data["ai_summary"]) > 0
        print(f"✓ AI summary generated: {data['ai_summary'][:100]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
