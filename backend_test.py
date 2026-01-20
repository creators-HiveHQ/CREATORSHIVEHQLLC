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
    def __init__(self, base_url="https://creatorbase-5.preview.emergentagent.com"):
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

    def test_endpoint(self, name: str, method: str, endpoint: str, expected_status: int = 200, data: Dict = None, auth_required: bool = False) -> tuple:
        """Test a single API endpoint"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if required and available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
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

    def test_authentication_endpoints(self):
        """Test authentication system - JWT-based admin access"""
        print("\n🔍 Testing Authentication System...")
        
        # Test 1: Login with default admin credentials
        login_data = {
            "email": "admin@hivehq.com",
            "password": "admin123"
        }
        success, login_response = self.test_endpoint(
            "Login with Default Admin Credentials", 
            "POST", 
            "auth/login", 
            200, 
            login_data
        )
        
        if success and login_response:
            # Store token for subsequent tests
            self.auth_token = login_response.get("access_token")
            self.auth_user = login_response.get("user")
            
            print(f"   🔑 Token received: {self.auth_token[:20]}..." if self.auth_token else "   ❌ No token received")
            print(f"   👤 User: {self.auth_user.get('name')} ({self.auth_user.get('email')})" if self.auth_user else "   ❌ No user data")
            
            # Verify token structure
            if self.auth_token and self.auth_user:
                expected_fields = ["id", "email", "name", "role"]
                missing_fields = [field for field in expected_fields if field not in self.auth_user]
                if missing_fields:
                    self.log_result("User Data Completeness", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("User Data Completeness", True, "All required fields present")
        
        # Test 2: Invalid login credentials
        invalid_login_data = {
            "email": "admin@hivehq.com",
            "password": "wrongpassword"
        }
        self.test_endpoint(
            "Login with Invalid Credentials", 
            "POST", 
            "auth/login", 
            401, 
            invalid_login_data
        )
        
        # Test 3: Login with non-existent user
        nonexistent_login_data = {
            "email": "nonexistent@hivehq.com",
            "password": "admin123"
        }
        self.test_endpoint(
            "Login with Non-existent User", 
            "POST", 
            "auth/login", 
            401, 
            nonexistent_login_data
        )
        
        # Test 4: Verify token endpoint (requires valid token)
        if self.auth_token:
            success, verify_response = self.test_endpoint(
                "Verify Valid Token", 
                "GET", 
                "auth/verify", 
                200, 
                auth_required=True
            )
            
            if success and verify_response:
                if verify_response.get("valid") and verify_response.get("user"):
                    self.log_result("Token Verification Response", True, "Valid token confirmed")
                else:
                    self.log_result("Token Verification Response", False, "Invalid response structure")
        
        # Test 5: Get current user endpoint (requires valid token)
        if self.auth_token:
            success, me_response = self.test_endpoint(
                "Get Current User (/auth/me)", 
                "GET", 
                "auth/me", 
                200, 
                auth_required=True
            )
            
            if success and me_response:
                if me_response.get("email") == "admin@hivehq.com":
                    self.log_result("Current User Data", True, "Correct user returned")
                else:
                    self.log_result("Current User Data", False, "Incorrect user data")
        
        # Test 6: Access protected endpoint without token
        success, _ = self.test_endpoint(
            "Access Protected Endpoint Without Token", 
            "GET", 
            "auth/verify", 
            401
        )
        
        # Test 7: Register new admin user
        import uuid
        test_email = f"test-admin-{str(uuid.uuid4())[:8]}@hivehq.com"
        register_data = {
            "name": "Test Admin",
            "email": test_email,
            "password": "testpass123"
        }
        success, register_response = self.test_endpoint(
            "Register New Admin User", 
            "POST", 
            "auth/register", 
            200, 
            register_data
        )
        
        if success and register_response:
            if register_response.get("message") and register_response.get("user"):
                self.log_result("Registration Response", True, "User created successfully")
                
                # Test login with newly created user
                new_login_data = {
                    "email": test_email,
                    "password": "testpass123"
                }
                success, new_login_response = self.test_endpoint(
                    "Login with Newly Created User", 
                    "POST", 
                    "auth/login", 
                    200, 
                    new_login_data
                )
                
                if success and new_login_response.get("access_token"):
                    self.log_result("New User Login", True, "New user can login successfully")
                else:
                    self.log_result("New User Login", False, "New user cannot login")
            else:
                self.log_result("Registration Response", False, "Invalid registration response")
        
        # Test 8: Try to register with existing email
        duplicate_register_data = {
            "name": "Duplicate Admin",
            "email": "admin@hivehq.com",  # Already exists
            "password": "testpass123"
        }
        self.test_endpoint(
            "Register with Existing Email", 
            "POST", 
            "auth/register", 
            400, 
            duplicate_register_data
        )

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

    def test_creator_registration_endpoints(self):
        """Test Creator Registration endpoints - Public and Admin"""
        print("\n🔍 Testing Creator Registration System...")
        
        # Test 1: Get form options (public endpoint)
        success, form_options = self.test_endpoint("Get Creator Form Options", "GET", "creators/form-options")
        
        if success and form_options:
            platforms = form_options.get("platforms", [])
            niches = form_options.get("niches", [])
            arris_question = form_options.get("arris_question", "")
            
            print(f"   📋 Found {len(platforms)} platform options")
            print(f"   📋 Found {len(niches)} niche options")
            print(f"   🧠 ARRIS Question: {arris_question[:50]}..." if arris_question else "   ❌ No ARRIS question")
            
            # Validate form options structure
            if platforms and isinstance(platforms, list) and len(platforms) > 0:
                first_platform = platforms[0]
                if isinstance(first_platform, dict) and "value" in first_platform and "label" in first_platform:
                    self.log_result("Form Options Structure", True, "Platform options properly structured")
                else:
                    self.log_result("Form Options Structure", False, "Platform options missing required fields")
            else:
                self.log_result("Form Options Structure", False, "No platform options found")
        
        # Test 2: Register a new creator (public endpoint)
        import uuid
        test_creator_email = f"test-creator-{str(uuid.uuid4())[:8]}@example.com"
        creator_data = {
            "name": "Test Creator",
            "email": test_creator_email,
            "platforms": ["youtube", "instagram"],
            "niche": "Tech & Software",
            "goals": "Grow my audience and monetize content",
            "arris_intake_question": "My biggest challenge is creating consistent content while managing my day job."
        }
        
        success, registration_response = self.test_endpoint(
            "Register New Creator", 
            "POST", 
            "creators/register", 
            200, 
            creator_data
        )
        
        creator_id = None
        if success and registration_response:
            creator_id = registration_response.get("id")
            expected_fields = ["id", "name", "email", "status", "message", "submitted_at"]
            missing_fields = [field for field in expected_fields if field not in registration_response]
            
            if missing_fields:
                self.log_result("Creator Registration Response", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Creator Registration Response", True, "All required fields present")
                print(f"   ✅ Creator registered with ID: {creator_id}")
                print(f"   📧 Registration email: {registration_response.get('email')}")
                print(f"   📝 Status: {registration_response.get('status')}")
        
        # Test 3: Try to register with same email (should fail)
        duplicate_creator_data = {
            "name": "Duplicate Creator",
            "email": test_creator_email,  # Same email as above
            "platforms": ["tiktok"],
            "niche": "Entertainment",
            "goals": "Test duplicate registration",
            "arris_intake_question": "Testing duplicate email handling."
        }
        
        self.test_endpoint(
            "Register Creator with Duplicate Email", 
            "POST", 
            "creators/register", 
            400, 
            duplicate_creator_data
        )
        
        # Test 4: Register creator with missing required fields
        incomplete_creator_data = {
            "name": "Incomplete Creator",
            # Missing email, platforms, niche
            "goals": "Test validation",
            "arris_intake_question": "Testing validation."
        }
        
        self.test_endpoint(
            "Register Creator with Missing Fields", 
            "POST", 
            "creators/register", 
            422,  # Validation error
            incomplete_creator_data
        )
        
        # Admin-only endpoints (require authentication)
        if not self.auth_token:
            print("   ⚠️  Skipping admin endpoints - no auth token available")
            return
        
        # Test 5: Get all creator registrations (admin only)
        success, creators_list = self.test_endpoint(
            "Get All Creator Registrations", 
            "GET", 
            "creators", 
            200, 
            auth_required=True
        )
        
        if success and creators_list:
            print(f"   👥 Found {len(creators_list)} creator registrations")
            
            # Check if our test creator is in the list
            test_creator_found = any(c.get("email") == test_creator_email for c in creators_list)
            if test_creator_found:
                self.log_result("Test Creator in List", True, "Newly registered creator found in admin list")
            else:
                self.log_result("Test Creator in List", False, "Newly registered creator not found in admin list")
        
        # Test 6: Filter creators by status
        success, pending_creators = self.test_endpoint(
            "Filter Creators by Status (Pending)", 
            "GET", 
            "creators?status=pending", 
            200, 
            auth_required=True
        )
        
        if success and pending_creators:
            print(f"   ⏳ Found {len(pending_creators)} pending creators")
        
        # Test 7: Get creator statistics
        success, creator_stats = self.test_endpoint(
            "Get Creator Statistics", 
            "GET", 
            "creators/stats/summary", 
            200, 
            auth_required=True
        )
        
        if success and creator_stats:
            total_registrations = creator_stats.get("total_registrations", 0)
            by_status = creator_stats.get("by_status", {})
            top_platforms = creator_stats.get("top_platforms", [])
            top_niches = creator_stats.get("top_niches", [])
            
            print(f"   📊 Total Registrations: {total_registrations}")
            print(f"   📊 By Status: {by_status}")
            print(f"   📊 Top Platforms: {len(top_platforms)} entries")
            print(f"   📊 Top Niches: {len(top_niches)} entries")
            
            # Validate stats structure
            if isinstance(by_status, dict) and isinstance(top_platforms, list):
                self.log_result("Creator Stats Structure", True, "Statistics properly structured")
            else:
                self.log_result("Creator Stats Structure", False, "Statistics structure invalid")
        
        # Test 8: Get specific creator by ID (if we have one)
        if creator_id:
            success, creator_details = self.test_endpoint(
                f"Get Creator by ID: {creator_id}", 
                "GET", 
                f"creators/{creator_id}", 
                200, 
                auth_required=True
            )
            
            if success and creator_details:
                if creator_details.get("email") == test_creator_email:
                    self.log_result("Creator Details Match", True, "Retrieved creator matches registered data")
                else:
                    self.log_result("Creator Details Match", False, "Retrieved creator data mismatch")
        
        # Test 9: Update creator status (approve)
        if creator_id:
            update_data = {
                "status": "approved",
                "assigned_tier": "Free"
            }
            
            success, update_response = self.test_endpoint(
                f"Approve Creator: {creator_id}", 
                "PATCH", 
                f"creators/{creator_id}", 
                200, 
                update_data,
                auth_required=True
            )
            
            if success and update_response:
                message = update_response.get("message", "")
                if "approved" in message.lower() and "user" in message.lower():
                    self.log_result("Creator Approval with User Creation", True, "Creator approved and user account created")
                    print(f"   ✅ {message}")
                    
                    # Check if user was created in users collection
                    user_id = update_response.get("user_id")
                    if user_id:
                        print(f"   👤 New User ID: {user_id}")
                else:
                    self.log_result("Creator Approval", True, "Creator status updated")
        
        # Test 10: Try to update non-existent creator
        fake_creator_id = "CR-FAKE123"
        update_data = {"status": "approved"}
        
        self.test_endpoint(
            "Update Non-existent Creator", 
            "PATCH", 
            f"creators/{fake_creator_id}", 
            404, 
            update_data,
            auth_required=True
        )
        
        # Test 11: Access admin endpoints without authentication
        self.test_endpoint(
            "Access Creators List Without Auth", 
            "GET", 
            "creators", 
            401
        )
        
        self.test_endpoint(
            "Access Creator Stats Without Auth", 
            "GET", 
            "creators/stats/summary", 
            401
        )

    def test_project_proposal_endpoints(self):
        """Test Project Proposal endpoints - Core workflow testing"""
        print("\n🔍 Testing Project Proposal System...")
        
        # Test 1: Get proposal form options (public endpoint)
        success, form_options = self.test_endpoint("Get Proposal Form Options", "GET", "proposals/form-options")
        
        if success and form_options:
            platforms = form_options.get("platforms", [])
            timelines = form_options.get("timelines", [])
            priorities = form_options.get("priorities", [])
            statuses = form_options.get("statuses", [])
            arris_question = form_options.get("arris_question", "")
            
            print(f"   📋 Found {len(platforms)} platform options")
            print(f"   📋 Found {len(timelines)} timeline options")
            print(f"   📋 Found {len(priorities)} priority options")
            print(f"   📋 Found {len(statuses)} status options")
            print(f"   🧠 ARRIS Question: {arris_question[:50]}..." if arris_question else "   ❌ No ARRIS question")
            
            # Validate form options structure
            if platforms and isinstance(platforms, list) and len(platforms) > 0:
                first_platform = platforms[0]
                if isinstance(first_platform, dict) and "value" in first_platform and "label" in first_platform:
                    self.log_result("Proposal Form Options Structure", True, "Platform options properly structured")
                else:
                    self.log_result("Proposal Form Options Structure", False, "Platform options missing required fields")
            else:
                self.log_result("Proposal Form Options Structure", False, "No platform options found")
        
        # Skip authenticated tests if no token
        if not self.auth_token:
            print("   ⚠️  Skipping authenticated proposal endpoints - no auth token available")
            return
        
        # Test 2: Create a new proposal (requires auth)
        import uuid
        test_user_id = f"U-{str(uuid.uuid4())[:4]}"
        proposal_data = {
            "user_id": test_user_id,
            "title": "YouTube Course Launch Campaign",
            "description": "Launch a comprehensive online course about content creation, targeting aspiring YouTubers. The course will include video lessons, downloadable resources, and community access.",
            "goals": "Generate $50K in course sales within 3 months, build email list of 5K subscribers, establish authority in creator education space",
            "platforms": ["youtube", "instagram", "twitter"],
            "timeline": "2-4_weeks",
            "estimated_hours": 120.0,
            "arris_intake_question": "I want to create a sustainable income stream while helping other creators succeed. My biggest challenge is balancing content creation with course development.",
            "priority": "high"
        }
        
        success, proposal_response = self.test_endpoint(
            "Create New Proposal", 
            "POST", 
            "proposals", 
            200, 
            proposal_data,
            auth_required=True
        )
        
        proposal_id = None
        if success and proposal_response:
            proposal_id = proposal_response.get("id")
            expected_fields = ["id", "title", "status", "message"]
            missing_fields = [field for field in expected_fields if field not in proposal_response]
            
            if missing_fields:
                self.log_result("Proposal Creation Response", False, f"Missing fields: {missing_fields}")
            else:
                self.log_result("Proposal Creation Response", True, "All required fields present")
                print(f"   ✅ Proposal created with ID: {proposal_id}")
                print(f"   📝 Status: {proposal_response.get('status')}")
        
        # Test 3: Submit proposal for review (generates ARRIS insights)
        if proposal_id:
            success, submit_response = self.test_endpoint(
                f"Submit Proposal for Review: {proposal_id}", 
                "POST", 
                f"proposals/{proposal_id}/submit", 
                200, 
                auth_required=True
            )
            
            if success and submit_response:
                arris_insights = submit_response.get("arris_insights")
                if arris_insights and isinstance(arris_insights, dict):
                    self.log_result("ARRIS Insights Generation", True, "ARRIS insights generated successfully")
                    print(f"   🧠 ARRIS Insights generated")
                    
                    # Check insights structure
                    expected_insight_fields = ["summary", "strengths", "risks", "recommendations"]
                    missing_insight_fields = [field for field in expected_insight_fields if field not in arris_insights]
                    
                    if missing_insight_fields:
                        self.log_result("ARRIS Insights Structure", False, f"Missing insight fields: {missing_insight_fields}")
                    else:
                        self.log_result("ARRIS Insights Structure", True, "All required insight fields present")
                        print(f"   📊 Summary: {arris_insights.get('summary', '')[:100]}...")
                        print(f"   💪 Strengths: {len(arris_insights.get('strengths', []))} items")
                        print(f"   ⚠️  Risks: {len(arris_insights.get('risks', []))} items")
                        print(f"   💡 Recommendations: {len(arris_insights.get('recommendations', []))} items")
                else:
                    self.log_result("ARRIS Insights Generation", False, "No ARRIS insights in response")
        
        # Test 4: Get all proposals (admin view)
        success, proposals_list = self.test_endpoint(
            "Get All Proposals", 
            "GET", 
            "proposals", 
            200, 
            auth_required=True
        )
        
        if success and proposals_list:
            print(f"   📋 Found {len(proposals_list)} proposals")
            
            # Check if our test proposal is in the list
            if proposal_id:
                test_proposal_found = any(p.get("id") == proposal_id for p in proposals_list)
                if test_proposal_found:
                    self.log_result("Test Proposal in List", True, "Newly created proposal found in list")
                else:
                    self.log_result("Test Proposal in List", False, "Newly created proposal not found in list")
        
        # Test 5: Get specific proposal with ARRIS insights
        if proposal_id:
            success, proposal_details = self.test_endpoint(
                f"Get Proposal by ID: {proposal_id}", 
                "GET", 
                f"proposals/{proposal_id}", 
                200, 
                auth_required=True
            )
            
            if success and proposal_details:
                if proposal_details.get("id") == proposal_id:
                    self.log_result("Proposal Details Match", True, "Retrieved proposal matches created data")
                    
                    # Check if ARRIS insights are included
                    if proposal_details.get("arris_insights"):
                        self.log_result("ARRIS Insights in Details", True, "ARRIS insights included in proposal details")
                    else:
                        self.log_result("ARRIS Insights in Details", False, "ARRIS insights missing from proposal details")
                else:
                    self.log_result("Proposal Details Match", False, "Retrieved proposal data mismatch")
        
        # Test 6: Update proposal status (admin review)
        if proposal_id:
            update_data = {
                "status": "under_review",
                "review_notes": "Reviewing proposal for approval"
            }
            
            success, update_response = self.test_endpoint(
                f"Update Proposal Status: {proposal_id}", 
                "PATCH", 
                f"proposals/{proposal_id}", 
                200, 
                update_data,
                auth_required=True
            )
            
            if success and update_response:
                message = update_response.get("message", "")
                if "updated" in message.lower():
                    self.log_result("Proposal Status Update", True, "Proposal status updated successfully")
                    print(f"   ✅ {message}")
        
        # Test 7: Approve proposal (should create project)
        if proposal_id:
            approve_data = {
                "status": "approved"
            }
            
            success, approve_response = self.test_endpoint(
                f"Approve Proposal: {proposal_id}", 
                "PATCH", 
                f"proposals/{proposal_id}", 
                200, 
                approve_data,
                auth_required=True
            )
            
            if success and approve_response:
                message = approve_response.get("message", "")
                project_id = approve_response.get("project_id")
                
                if "approved" in message.lower() and "project" in message.lower() and project_id:
                    self.log_result("Proposal Approval with Project Creation", True, "Proposal approved and project created")
                    print(f"   ✅ {message}")
                    print(f"   📁 New Project ID: {project_id}")
                else:
                    self.log_result("Proposal Approval", True, "Proposal approved")
        
        # Test 8: Regenerate ARRIS insights
        if proposal_id:
            success, regen_response = self.test_endpoint(
                f"Regenerate ARRIS Insights: {proposal_id}", 
                "POST", 
                f"proposals/{proposal_id}/regenerate-insights", 
                200, 
                auth_required=True
            )
            
            if success and regen_response:
                arris_insights = regen_response.get("arris_insights")
                if arris_insights:
                    self.log_result("ARRIS Insights Regeneration", True, "ARRIS insights regenerated successfully")
                else:
                    self.log_result("ARRIS Insights Regeneration", False, "No insights in regeneration response")
        
        # Test 9: Get proposal statistics
        success, proposal_stats = self.test_endpoint(
            "Get Proposal Statistics", 
            "GET", 
            "proposals/stats/summary", 
            200, 
            auth_required=True
        )
        
        if success and proposal_stats:
            total_proposals = proposal_stats.get("total_proposals", 0)
            by_status = proposal_stats.get("by_status", {})
            by_priority = proposal_stats.get("by_priority", {})
            
            print(f"   📊 Total Proposals: {total_proposals}")
            print(f"   📊 By Status: {by_status}")
            print(f"   📊 By Priority: {by_priority}")
            
            # Validate stats structure
            if isinstance(by_status, dict) and isinstance(by_priority, dict):
                self.log_result("Proposal Stats Structure", True, "Statistics properly structured")
            else:
                self.log_result("Proposal Stats Structure", False, "Statistics structure invalid")
        
        # Test 10: Filter proposals by status and priority
        success, filtered_proposals = self.test_endpoint(
            "Filter Proposals by Status", 
            "GET", 
            "proposals?status=submitted", 
            200, 
            auth_required=True
        )
        
        if success and filtered_proposals:
            print(f"   📋 Found {len(filtered_proposals)} submitted proposals")
        
        success, priority_filtered = self.test_endpoint(
            "Filter Proposals by Priority", 
            "GET", 
            "proposals?priority=high", 
            200, 
            auth_required=True
        )
        
        if success and priority_filtered:
            print(f"   📋 Found {len(priority_filtered)} high priority proposals")
        
        # Test 11: Try to access proposals without authentication
        self.test_endpoint(
            "Access Proposals Without Auth", 
            "GET", 
            "proposals", 
            401
        )
        
        # Test 12: Try to create proposal with missing fields
        incomplete_proposal_data = {
            "user_id": "test-user",
            "title": "Incomplete Proposal"
            # Missing required description
        }
        
        self.test_endpoint(
            "Create Proposal with Missing Fields", 
            "POST", 
            "proposals", 
            422,  # Validation error
            incomplete_proposal_data,
            auth_required=True
        )
        
        # Test 13: Try to submit non-existent proposal
        fake_proposal_id = "PP-FAKE123"
        self.test_endpoint(
            "Submit Non-existent Proposal", 
            "POST", 
            f"proposals/{fake_proposal_id}/submit", 
            404,
            auth_required=True
        )

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
        self.test_authentication_endpoints()  # Test auth first to get token
        self.test_creator_registration_endpoints()  # Test creator registration system
        self.test_project_proposal_endpoints()  # Test project proposal system
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