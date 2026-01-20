"""
Test Calculator Service - Central Revenue Hub
Tests all financial analytics endpoints:
- MRR/ARR metrics
- Churn rate
- LTV (Customer Lifetime Value)
- Revenue breakdown/trends
- Expense analysis
- Profit analysis
- Revenue forecasting
- Self-Funding Loop status
- Creator-specific financial summary
- Platform financial dashboard
"""

import pytest
import requests
import os
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
TEST_CREATOR_ID = "CR-43a0c31e"
TEST_CREATOR_EMAIL = "emailtest@example.com"
TEST_CREATOR_PASSWORD = "testpassword"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestCalculatorMetricsMRR:
    """Test MRR (Monthly Recurring Revenue) endpoint"""
    
    def test_mrr_requires_auth(self):
        """MRR endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/metrics/mrr")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ MRR endpoint requires authentication")
    
    def test_mrr_returns_valid_structure(self, admin_headers):
        """MRR endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/mrr",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Validate required fields
        assert "mrr" in data, "Missing 'mrr' field"
        assert "mrr_previous" in data, "Missing 'mrr_previous' field"
        assert "mrr_growth_percent" in data, "Missing 'mrr_growth_percent' field"
        assert "active_subscriptions" in data, "Missing 'active_subscriptions' field"
        assert "avg_revenue_per_subscription" in data, "Missing 'avg_revenue_per_subscription' field"
        assert "month" in data, "Missing 'month' field"
        
        # Validate data types
        assert isinstance(data["mrr"], (int, float)), "MRR should be numeric"
        assert isinstance(data["mrr_growth_percent"], (int, float)), "Growth percent should be numeric"
        assert isinstance(data["active_subscriptions"], int), "Active subscriptions should be integer"
        
        print(f"✓ MRR endpoint returns valid structure: MRR=${data['mrr']}, Growth={data['mrr_growth_percent']}%")
    
    def test_mrr_with_user_filter(self, admin_headers):
        """MRR endpoint accepts user_id filter"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/mrr",
            params={"user_id": TEST_CREATOR_ID},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "mrr" in data
        print(f"✓ MRR with user filter works: MRR=${data['mrr']}")


class TestCalculatorMetricsARR:
    """Test ARR (Annual Recurring Revenue) endpoint"""
    
    def test_arr_requires_auth(self):
        """ARR endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/metrics/arr")
        assert response.status_code in [401, 403]
        print("✓ ARR endpoint requires authentication")
    
    def test_arr_returns_valid_structure(self, admin_headers):
        """ARR endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/arr",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "arr" in data, "Missing 'arr' field"
        assert "arr_previous" in data, "Missing 'arr_previous' field"
        assert "arr_growth_percent" in data, "Missing 'arr_growth_percent' field"
        assert "based_on_mrr" in data, "Missing 'based_on_mrr' field"
        assert "projected_year_end" in data, "Missing 'projected_year_end' field"
        
        # ARR should be MRR * 12
        assert isinstance(data["arr"], (int, float))
        print(f"✓ ARR endpoint returns valid structure: ARR=${data['arr']}")


class TestCalculatorMetricsChurn:
    """Test Churn Rate endpoint"""
    
    def test_churn_requires_auth(self):
        """Churn endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/metrics/churn")
        assert response.status_code in [401, 403]
        print("✓ Churn endpoint requires authentication")
    
    def test_churn_returns_valid_structure(self, admin_headers):
        """Churn endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/churn",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "churn_rate_percent" in data, "Missing 'churn_rate_percent' field"
        assert "retention_rate_percent" in data, "Missing 'retention_rate_percent' field"
        assert "churned_subscriptions" in data, "Missing 'churned_subscriptions' field"
        assert "total_at_period_start" in data, "Missing 'total_at_period_start' field"
        assert "period" in data, "Missing 'period' field"
        assert "health_indicator" in data, "Missing 'health_indicator' field"
        
        # Validate health indicator values
        valid_health = ["excellent", "good", "concerning", "critical"]
        assert data["health_indicator"] in valid_health, f"Invalid health indicator: {data['health_indicator']}"
        
        print(f"✓ Churn endpoint returns valid structure: Churn={data['churn_rate_percent']}%, Health={data['health_indicator']}")


class TestCalculatorMetricsLTV:
    """Test LTV (Customer Lifetime Value) endpoint"""
    
    def test_ltv_requires_auth(self):
        """LTV endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/metrics/ltv")
        assert response.status_code in [401, 403]
        print("✓ LTV endpoint requires authentication")
    
    def test_ltv_returns_valid_structure(self, admin_headers):
        """LTV endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/ltv",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "ltv" in data, "Missing 'ltv' field"
        assert "arpu" in data, "Missing 'arpu' field"
        assert "avg_lifetime_months" in data, "Missing 'avg_lifetime_months' field"
        assert "monthly_churn_rate" in data, "Missing 'monthly_churn_rate' field"
        assert "health_indicator" in data, "Missing 'health_indicator' field"
        
        # Validate health indicator values
        valid_health = ["excellent", "good", "fair", "needs_improvement"]
        assert data["health_indicator"] in valid_health, f"Invalid health indicator: {data['health_indicator']}"
        
        print(f"✓ LTV endpoint returns valid structure: LTV=${data['ltv']}, ARPU=${data['arpu']}")


class TestCalculatorMetricsAll:
    """Test All Metrics endpoint"""
    
    def test_all_metrics_requires_auth(self):
        """All metrics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/metrics/all")
        assert response.status_code in [401, 403]
        print("✓ All metrics endpoint requires authentication")
    
    def test_all_metrics_returns_valid_structure(self, admin_headers):
        """All metrics endpoint returns all key metrics"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/all",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "mrr" in data, "Missing 'mrr' field"
        assert "arr" in data, "Missing 'arr' field"
        assert "churn" in data, "Missing 'churn' field"
        assert "ltv" in data, "Missing 'ltv' field"
        assert "generated_at" in data, "Missing 'generated_at' field"
        
        # Validate nested structures
        assert "mrr" in data["mrr"], "MRR object missing 'mrr' value"
        assert "arr" in data["arr"], "ARR object missing 'arr' value"
        assert "churn_rate_percent" in data["churn"], "Churn object missing 'churn_rate_percent'"
        assert "ltv" in data["ltv"], "LTV object missing 'ltv' value"
        
        print(f"✓ All metrics endpoint returns complete data: MRR=${data['mrr']['mrr']}, ARR=${data['arr']['arr']}")


class TestCalculatorRevenueBreakdown:
    """Test Revenue Breakdown endpoint"""
    
    def test_revenue_breakdown_requires_auth(self):
        """Revenue breakdown endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/revenue/breakdown")
        assert response.status_code in [401, 403]
        print("✓ Revenue breakdown endpoint requires authentication")
    
    def test_revenue_breakdown_returns_valid_structure(self, admin_headers):
        """Revenue breakdown endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/revenue/breakdown",
            params={"months_back": 6},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_revenue" in data, "Missing 'total_revenue' field"
        assert "by_month" in data, "Missing 'by_month' field"
        assert "by_source" in data, "Missing 'by_source' field"
        assert "source_percentages" in data, "Missing 'source_percentages' field"
        assert "period_analyzed" in data, "Missing 'period_analyzed' field"
        assert "avg_monthly_revenue" in data, "Missing 'avg_monthly_revenue' field"
        
        print(f"✓ Revenue breakdown returns valid structure: Total=${data['total_revenue']}")
    
    def test_revenue_breakdown_months_back_param(self, admin_headers):
        """Revenue breakdown accepts months_back parameter"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/revenue/breakdown",
            params={"months_back": 3},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "Last 3 months" in data["period_analyzed"]
        print("✓ Revenue breakdown accepts months_back parameter")


class TestCalculatorRevenueTrends:
    """Test Revenue Trends endpoint"""
    
    def test_revenue_trends_requires_auth(self):
        """Revenue trends endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/revenue/trends")
        assert response.status_code in [401, 403]
        print("✓ Revenue trends endpoint requires authentication")
    
    def test_revenue_trends_returns_valid_structure(self, admin_headers):
        """Revenue trends endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/revenue/trends",
            params={"months_back": 12},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Check for either trend data or insufficient_data response
        assert "trend" in data or "monthly_data" in data, "Missing trend data"
        
        if data.get("trend") != "insufficient_data":
            assert "trend_strength" in data, "Missing 'trend_strength' field"
            assert "avg_monthly_growth_percent" in data, "Missing 'avg_monthly_growth_percent' field"
            assert "monthly_data" in data, "Missing 'monthly_data' field"
            print(f"✓ Revenue trends returns valid structure: Trend={data['trend']}, Strength={data.get('trend_strength')}")
        else:
            print(f"✓ Revenue trends returns insufficient_data (expected with limited data)")


class TestCalculatorExpenseBreakdown:
    """Test Expense Breakdown endpoint"""
    
    def test_expense_breakdown_requires_auth(self):
        """Expense breakdown endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/expenses/breakdown")
        assert response.status_code in [401, 403]
        print("✓ Expense breakdown endpoint requires authentication")
    
    def test_expense_breakdown_returns_valid_structure(self, admin_headers):
        """Expense breakdown endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/expenses/breakdown",
            params={"months_back": 6},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_expenses" in data, "Missing 'total_expenses' field"
        assert "by_month" in data, "Missing 'by_month' field"
        assert "by_category" in data, "Missing 'by_category' field"
        assert "avg_monthly_expenses" in data, "Missing 'avg_monthly_expenses' field"
        assert "period" in data, "Missing 'period' field"
        
        print(f"✓ Expense breakdown returns valid structure: Total=${data['total_expenses']}")


class TestCalculatorProfitAnalysis:
    """Test Profit Analysis endpoint"""
    
    def test_profit_analysis_requires_auth(self):
        """Profit analysis endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/profit/analysis")
        assert response.status_code in [401, 403]
        print("✓ Profit analysis endpoint requires authentication")
    
    def test_profit_analysis_returns_valid_structure(self, admin_headers):
        """Profit analysis endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/profit/analysis",
            params={"months_back": 3},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_revenue" in data, "Missing 'total_revenue' field"
        assert "total_expenses" in data, "Missing 'total_expenses' field"
        assert "net_profit" in data, "Missing 'net_profit' field"
        assert "profit_margin_percent" in data, "Missing 'profit_margin_percent' field"
        assert "monthly_breakdown" in data, "Missing 'monthly_breakdown' field"
        assert "health_indicator" in data, "Missing 'health_indicator' field"
        assert "expense_to_revenue_ratio" in data, "Missing 'expense_to_revenue_ratio' field"
        
        # Validate health indicator values
        valid_health = ["excellent", "healthy", "moderate", "low", "loss"]
        assert data["health_indicator"] in valid_health, f"Invalid health indicator: {data['health_indicator']}"
        
        print(f"✓ Profit analysis returns valid structure: Net Profit=${data['net_profit']}, Margin={data['profit_margin_percent']}%")


class TestCalculatorForecast:
    """Test Revenue Forecast endpoint"""
    
    def test_forecast_requires_auth(self):
        """Forecast endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/forecast")
        assert response.status_code in [401, 403]
        print("✓ Forecast endpoint requires authentication")
    
    def test_forecast_returns_valid_structure(self, admin_headers):
        """Forecast endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/forecast",
            params={"months_ahead": 3},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check for either forecasts or error (insufficient data)
        if "error" in data:
            assert "Insufficient historical data" in data["error"]
            print(f"✓ Forecast returns insufficient data message (expected with limited data)")
        else:
            assert "forecasts" in data, "Missing 'forecasts' field"
            assert "base_amount" in data, "Missing 'base_amount' field"
            assert "growth_rate_used" in data, "Missing 'growth_rate_used' field"
            assert "methodology" in data, "Missing 'methodology' field"
            
            # Validate forecast structure
            if data["forecasts"]:
                forecast = data["forecasts"][0]
                assert "month" in forecast, "Forecast missing 'month'"
                assert "predicted_revenue" in forecast, "Forecast missing 'predicted_revenue'"
                assert "confidence" in forecast, "Forecast missing 'confidence'"
            
            print(f"✓ Forecast returns valid structure: {len(data['forecasts'])} months forecasted")


class TestCalculatorSelfFundingLoop:
    """Test Self-Funding Loop Status endpoint"""
    
    def test_self_funding_loop_requires_auth(self):
        """Self-funding loop endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/self-funding-loop")
        assert response.status_code in [401, 403]
        print("✓ Self-funding loop endpoint requires authentication")
    
    def test_self_funding_loop_returns_valid_structure(self, admin_headers):
        """Self-funding loop endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/self-funding-loop",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Missing 'status' field"
        assert "subscription_revenue" in data, "Missing 'subscription_revenue' field"
        assert "other_revenue" in data, "Missing 'other_revenue' field"
        assert "total_platform_revenue" in data, "Missing 'total_platform_revenue' field"
        assert "active_subscriptions" in data, "Missing 'active_subscriptions' field"
        assert "loop_health" in data, "Missing 'loop_health' field"
        assert "description" in data, "Missing 'description' field"
        
        # Validate subscription_revenue structure
        sub_rev = data["subscription_revenue"]
        assert "total" in sub_rev, "subscription_revenue missing 'total'"
        assert "transactions" in sub_rev, "subscription_revenue missing 'transactions'"
        assert "percentage_of_total" in sub_rev, "subscription_revenue missing 'percentage_of_total'"
        
        # Validate loop_health values
        valid_health = ["optimal", "healthy", "diversified"]
        assert data["loop_health"] in valid_health, f"Invalid loop_health: {data['loop_health']}"
        
        print(f"✓ Self-funding loop returns valid structure: Status={data['status']}, Health={data['loop_health']}")


class TestCalculatorCreatorSummary:
    """Test Creator Financial Summary endpoint"""
    
    def test_creator_summary_requires_auth(self):
        """Creator summary endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/creator/{TEST_CREATOR_ID}/summary")
        assert response.status_code in [401, 403]
        print("✓ Creator summary endpoint requires authentication")
    
    def test_creator_summary_returns_valid_structure(self, admin_headers):
        """Creator summary endpoint returns valid data structure"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/creator/{TEST_CREATOR_ID}/summary",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check for error (creator not found) or valid data
        if "error" in data:
            print(f"✓ Creator summary returns error for non-existent creator: {data['error']}")
        else:
            assert "creator" in data, "Missing 'creator' field"
            assert "subscription" in data, "Missing 'subscription' field"
            assert "financials" in data, "Missing 'financials' field"
            assert "trends" in data, "Missing 'trends' field"
            assert "health_score" in data, "Missing 'health_score' field"
            
            # Validate creator structure
            creator = data["creator"]
            assert "id" in creator, "creator missing 'id'"
            
            # Validate financials structure
            financials = data["financials"]
            assert "mrr_contribution" in financials, "financials missing 'mrr_contribution'"
            assert "total_revenue" in financials, "financials missing 'total_revenue'"
            assert "net_profit" in financials, "financials missing 'net_profit'"
            
            print(f"✓ Creator summary returns valid structure for creator {data['creator']['id']}")
    
    def test_creator_summary_nonexistent_creator(self, admin_headers):
        """Creator summary returns error for non-existent creator"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/creator/NONEXISTENT-ID/summary",
            headers=admin_headers
        )
        assert response.status_code == 200  # Returns 200 with error in body
        data = response.json()
        assert "error" in data, "Expected error for non-existent creator"
        assert data["error"] == "Creator not found"
        print("✓ Creator summary returns proper error for non-existent creator")


class TestCalculatorDashboard:
    """Test Platform Financial Dashboard endpoint"""
    
    def test_dashboard_requires_auth(self):
        """Dashboard endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/calculator/dashboard")
        assert response.status_code in [401, 403]
        print("✓ Dashboard endpoint requires authentication")
    
    def test_dashboard_returns_valid_structure(self, admin_headers):
        """Dashboard endpoint returns comprehensive financial data"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/dashboard",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "key_metrics" in data, "Missing 'key_metrics' field"
        assert "self_funding_loop" in data, "Missing 'self_funding_loop' field"
        assert "profit_analysis" in data, "Missing 'profit_analysis' field"
        assert "revenue_forecast" in data, "Missing 'revenue_forecast' field"
        assert "generated_at" in data, "Missing 'generated_at' field"
        assert "report_type" in data, "Missing 'report_type' field"
        
        # Validate key_metrics structure
        key_metrics = data["key_metrics"]
        assert "mrr" in key_metrics, "key_metrics missing 'mrr'"
        assert "arr" in key_metrics, "key_metrics missing 'arr'"
        assert "churn" in key_metrics, "key_metrics missing 'churn'"
        assert "ltv" in key_metrics, "key_metrics missing 'ltv'"
        
        # Validate report_type
        assert data["report_type"] == "platform_financial_dashboard"
        
        print(f"✓ Dashboard returns comprehensive financial data")
        print(f"  - MRR: ${key_metrics['mrr']['mrr']}")
        print(f"  - ARR: ${key_metrics['arr']['arr']}")
        print(f"  - Churn: {key_metrics['churn']['churn_rate_percent']}%")
        print(f"  - LTV: ${key_metrics['ltv']['ltv']}")


class TestCalculatorDataIntegrity:
    """Test data integrity and calculations"""
    
    def test_arr_equals_mrr_times_12(self, admin_headers):
        """ARR should equal MRR * 12"""
        # Get MRR
        mrr_response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/mrr",
            headers=admin_headers
        )
        mrr_data = mrr_response.json()
        
        # Get ARR
        arr_response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/arr",
            headers=admin_headers
        )
        arr_data = arr_response.json()
        
        # Validate ARR = MRR * 12
        expected_arr = mrr_data["mrr"] * 12
        assert abs(arr_data["arr"] - expected_arr) < 0.01, f"ARR ({arr_data['arr']}) should equal MRR*12 ({expected_arr})"
        print(f"✓ ARR calculation verified: ${arr_data['arr']} = ${mrr_data['mrr']} * 12")
    
    def test_retention_plus_churn_equals_100(self, admin_headers):
        """Retention rate + Churn rate should equal 100%"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/metrics/churn",
            headers=admin_headers
        )
        data = response.json()
        
        total = data["churn_rate_percent"] + data["retention_rate_percent"]
        assert abs(total - 100) < 0.01, f"Churn + Retention should equal 100%, got {total}"
        print(f"✓ Churn + Retention = 100% verified: {data['churn_rate_percent']}% + {data['retention_rate_percent']}% = {total}%")
    
    def test_profit_equals_revenue_minus_expenses(self, admin_headers):
        """Net profit should equal revenue minus expenses"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/profit/analysis",
            params={"months_back": 3},
            headers=admin_headers
        )
        data = response.json()
        
        expected_profit = data["total_revenue"] - data["total_expenses"]
        assert abs(data["net_profit"] - expected_profit) < 0.01, f"Net profit calculation mismatch"
        print(f"✓ Profit calculation verified: ${data['net_profit']} = ${data['total_revenue']} - ${data['total_expenses']}")


class TestCalculatorSeedData:
    """Test that seed data exists for calculator"""
    
    def test_seed_data_exists(self, admin_headers):
        """Verify calculator has seed data"""
        response = requests.get(
            f"{BASE_URL}/api/calculator",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have some entries
        assert len(data) > 0, "Calculator should have seed data"
        print(f"✓ Calculator has {len(data)} entries")
    
    def test_subscription_revenue_exists(self, admin_headers):
        """Verify subscription revenue data exists"""
        response = requests.get(
            f"{BASE_URL}/api/calculator/self-funding-loop",
            headers=admin_headers
        )
        data = response.json()
        
        # Check subscription revenue
        sub_rev = data["subscription_revenue"]
        print(f"✓ Subscription revenue: ${sub_rev['total']} from {sub_rev['transactions']} transactions")
        print(f"  - Percentage of total: {sub_rev['percentage_of_total']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
