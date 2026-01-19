"""
Creators Hive HQ - Backend API Testing
Tests all endpoints for the Master Database system
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

class CreatorsHiveAPITester:
    def __init__(self, base_url="https://hive-matrix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.results = {}
        self.auth_token = None
        self.auth_user = None

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
            self.failed_tests.append({"test": test_name, "error": details})
        
        self.results[test_name] = {"success": success, "details": details}

    def test_endpoint(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict = None) -> tuple:
        """Test a single API endpoint"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    self.log_result(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except json.JSONDecodeError:
                    self.log_result(name, False, f"Invalid JSON response, Status: {response.status_code}")
                    return False, {}
            else:
                self.log_result(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, {}

        except requests.exceptions.RequestException as e:
            self.log_result(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_health_and_root(self):
        """Test basic health and root endpoints"""
        print("\n🔍 Testing Health & Root Endpoints...")
        
        # Test root endpoint
        self.test_endpoint("Root API", "GET", "")
        
        # Test health check
        self.test_endpoint("Health Check", "GET", "health")

    def test_schema_endpoints(self):
        """Test schema index endpoints (Sheet 15)"""
        print("\n🔍 Testing Schema Index (Sheet 15)...")
        
        # Get complete schema index
        success, schema_data = self.test_endpoint("Get Schema Index", "GET", "schema")
        
        if success and schema_data.get("schema_index"):
            print(f"   📊 Found {len(schema_data['schema_index'])} schema entries")
            
            # Test getting specific schema
            first_schema = schema_data["schema_index"][0]
            sheet_name = first_schema.get("sheet_name", "Users")
            self.test_endpoint(f"Get Schema by Name: {sheet_name}", "GET", f"schema/{sheet_name}")

    def test_users_endpoints(self):
        """Test users endpoints (01_Users)"""
        print("\n🔍 Testing Users (01_Users)...")
        
        # Get all users
        success, users_data = self.test_endpoint("Get All Users", "GET", "users")
        
        if success and users_data:
            print(f"   👥 Found {len(users_data)} users")
            
            # Test filters
            self.test_endpoint("Filter Users by Role", "GET", "users?role=Creator")
            self.test_endpoint("Filter Users by Tier", "GET", "users?tier=Platinum")
            
            # Test getting specific user if users exist
            if users_data and len(users_data) > 0:
                user_id = users_data[0].get("id")
                if user_id:
                    self.test_endpoint(f"Get User by ID: {user_id}", "GET", f"users/{user_id}")

    def test_projects_endpoints(self):
        """Test projects endpoints (04_Projects)"""
        print("\n🔍 Testing Projects (04_Projects)...")
        
        # Get all projects
        success, projects_data = self.test_endpoint("Get All Projects", "GET", "projects")
        
        if success and projects_data:
            print(f"   📁 Found {len(projects_data)} projects")
            
            # Test filters
            self.test_endpoint("Filter Projects by Status", "GET", "projects?status=In_Progress")
            
            # Test getting specific project
            if projects_data and len(projects_data) > 0:
                project_id = projects_data[0].get("id")
                if project_id:
                    self.test_endpoint(f"Get Project by ID: {project_id}", "GET", f"projects/{project_id}")

    def test_calculator_endpoints(self):
        """Test calculator endpoints (06_Calculator) - Revenue Hub"""
        print("\n🔍 Testing Calculator (06_Calculator) - Revenue Hub...")
        
        # Get calculator entries
        success, calc_data = self.test_endpoint("Get Calculator Entries", "GET", "calculator")
        
        if success and calc_data:
            print(f"   💰 Found {len(calc_data)} calculator entries")
        
        # Test revenue summary - Critical for Self-Funding Loop
        success, summary_data = self.test_endpoint("Get Revenue Summary", "GET", "calculator/summary")
        
        if success and summary_data:
            print(f"   💰 Total Revenue: ${summary_data.get('total_revenue', 0):,}")
            print(f"   💰 Self-Funding Loop: {summary_data.get('self_funding_loop', 'Unknown')}")

    def test_subscriptions_endpoints(self):
        """Test subscriptions endpoints (17_Subscriptions) - Self-Funding Loop"""
        print("\n🔍 Testing Subscriptions (17_Subscriptions) - Self-Funding Loop...")
        
        # Get all subscriptions
        success, subs_data = self.test_endpoint("Get All Subscriptions", "GET", "subscriptions")
        
        if success and subs_data:
            print(f"   💳 Found {len(subs_data)} subscriptions")
            
            # Check for linked_calc_id (Self-Funding Loop connection)
            linked_count = sum(1 for sub in subs_data if sub.get("linked_calc_id"))
            print(f"   🔗 {linked_count} subscriptions linked to Calculator")
        
        # Test subscription revenue summary
        success, revenue_data = self.test_endpoint("Get Subscription Revenue", "GET", "subscriptions/revenue")
        
        if success and revenue_data:
            print(f"   💰 Subscription Revenue: ${revenue_data.get('total_subscription_revenue', 0):,}")
            print(f"   🔄 Self-Funding Loop: {revenue_data.get('self_funding_loop', 'Unknown')}")

    def test_arris_endpoints(self):
        """Test ARRIS Pattern Engine endpoints (19-21)"""
        print("\n🔍 Testing ARRIS Pattern Engine (19-21)...")
        
        # Test ARRIS usage logs
        success, usage_data = self.test_endpoint("Get ARRIS Usage Logs", "GET", "arris/usage")
        
        if success and usage_data:
            print(f"   🧠 Found {len(usage_data)} ARRIS usage logs")
        
        # Test ARRIS performance reviews
        success, perf_data = self.test_endpoint("Get ARRIS Performance", "GET", "arris/performance")
        
        if success and perf_data:
            print(f"   📊 Found {len(perf_data)} performance reviews")
        
        # Test ARRIS training data
        success, train_data = self.test_endpoint("Get ARRIS Training Data", "GET", "arris/training")
        
        if success and train_data:
            print(f"   📚 Found {len(train_data)} training data sources")

    def test_patterns_endpoints(self):
        """Test Pattern Engine endpoints"""
        print("\n🔍 Testing Pattern Engine...")
        
        # Test pattern analysis for different types
        pattern_types = ["usage", "revenue", "engagement"]
        
        for pattern_type in pattern_types:
            success, pattern_data = self.test_endpoint(
                f"Analyze {pattern_type.title()} Patterns", 
                "GET", 
                f"patterns/analyze?pattern_type={pattern_type}&days=30"
            )
            
            if success and pattern_data:
                insights_count = len(pattern_data.get("insights", []))
                recommendations_count = len(pattern_data.get("recommendations", []))
                print(f"   🔮 {pattern_type.title()}: {insights_count} insights, {recommendations_count} recommendations")
        
        # Test Memory Palace
        success, memory_data = self.test_endpoint("Get Memory Palace", "GET", "patterns/memory-palace")
        
        if success and memory_data:
            sections = memory_data.get("sections", {})
            print(f"   🏰 Memory Palace: {len(sections)} sections")

    def test_dashboard_endpoint(self):
        """Test dashboard aggregation endpoint"""
        print("\n🔍 Testing Dashboard Aggregation...")
        
        success, dashboard_data = self.test_endpoint("Get Dashboard", "GET", "dashboard")
        
        if success and dashboard_data:
            stats = dashboard_data.get("stats", {})
            financials = dashboard_data.get("financials", {})
            arris = dashboard_data.get("arris", {})
            
            print(f"   📊 Users: {stats.get('users', 0)}")
            print(f"   📊 Projects: {stats.get('projects', 0)}")
            print(f"   💰 Total Revenue: ${financials.get('total_revenue', 0):,}")
            print(f"   🧠 ARRIS Queries: {arris.get('total_queries', 0)}")
            print(f"   🔄 System Status: {dashboard_data.get('system_status', 'Unknown')}")

    def test_additional_endpoints(self):
        """Test additional endpoints"""
        print("\n🔍 Testing Additional Endpoints...")
        
        # Test lookups
        self.test_endpoint("Get Lookups", "GET", "lookups")
        
        # Test analytics
        self.test_endpoint("Get Analytics", "GET", "analytics")
        
        # Test customers
        self.test_endpoint("Get Customers", "GET", "customers")
        
        # Test affiliates
        self.test_endpoint("Get Affiliates", "GET", "affiliates")
        
        # Test rolodex
        self.test_endpoint("Get Rolodex", "GET", "rolodex")
        
        # Test integrations
        self.test_endpoint("Get Integrations", "GET", "integrations")
        
        # Test marketing campaigns
        self.test_endpoint("Get Marketing Campaigns", "GET", "campaigns")
        
        # Test dev approaches
        self.test_endpoint("Get Dev Approaches", "GET", "dev-approaches")
        
        # Test branding kits
        self.test_endpoint("Get Branding Kits", "GET", "branding-kits")
        
        # Test coach kits
        self.test_endpoint("Get Coach Kits", "GET", "coach-kits")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Creators Hive HQ API Testing...")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Run all test suites
        self.test_health_and_root()
        self.test_schema_endpoints()
        self.test_users_endpoints()
        self.test_projects_endpoints()
        self.test_calculator_endpoints()
        self.test_subscriptions_endpoints()
        self.test_arris_endpoints()
        self.test_patterns_endpoints()
        self.test_dashboard_endpoint()
        self.test_additional_endpoints()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {len(self.failed_tests)}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"   - {failure['test']}: {failure['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CreatorsHiveAPITester()
    success = tester.run_all_tests()
    
    # Save results to file
    results_file = "/app/test_reports/backend_api_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "failed_tests": tester.failed_tests,
            "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
            "detailed_results": tester.results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())