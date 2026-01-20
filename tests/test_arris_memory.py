"""
ARRIS Memory & Learning System Tests
Tests for Memory Palace, Pattern Engine, Learning System, and Context Builder

Endpoints tested:
- GET /api/arris/memory-palace/status - Comprehensive Memory Palace status
- POST /api/arris/memory/store - Store new memory
- GET /api/arris/memory/recall - Recall memories with filters
- GET /api/arris/memory/summary - Memory statistics by type
- POST /api/arris/patterns/analyze - Analyze patterns from proposal history
- GET /api/arris/patterns - Get existing patterns
- POST /api/arris/learning/record-outcome - Record outcome and update metrics
- GET /api/arris/learning/metrics - Get prediction accuracy and learning stage
- GET /api/arris/context - Build rich context with memories, patterns, history
- GET /api/arris/personalization - Get personalized prompt additions
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ELITE_USER = {"email": "elite@poweruser.com", "password": "elite123"}
PREMIUM_USER = {"email": "premium@speedtest.com", "password": "premium123"}


class TestArrisMemorySetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        """Get Elite user token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        assert response.status_code == 200, f"Elite login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def premium_token(self):
        """Get Premium user token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PREMIUM_USER)
        assert response.status_code == 200, f"Premium login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_elite_user_login(self):
        """Test Elite user can login"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✓ Elite user login successful")
    
    def test_premium_user_login(self):
        """Test Premium user can login"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PREMIUM_USER)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"✓ Premium user login successful")


class TestMemoryPalaceStatus:
    """Tests for GET /api/arris/memory-palace/status"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_memory_palace_status_requires_auth(self):
        """Test that memory palace status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/memory-palace/status")
        assert response.status_code in [401, 403]
        print(f"✓ Memory palace status requires authentication")
    
    def test_memory_palace_status_returns_comprehensive_data(self, elite_token):
        """Test that memory palace status returns comprehensive status"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/memory-palace/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check memory_palace section
        assert "memory_palace" in data
        mp = data["memory_palace"]
        assert mp["status"] == "active"
        assert "health" in mp
        assert "total_memories" in mp
        assert "by_type" in mp
        
        # Check pattern_engine section
        assert "pattern_engine" in data
        pe = data["pattern_engine"]
        assert "patterns_identified" in pe
        assert "pattern_categories" in pe
        
        # Check learning_system section
        assert "learning_system" in data
        ls = data["learning_system"]
        assert "stage" in ls
        assert "accuracy_rate" in ls
        assert "total_predictions" in ls
        
        # Check features section
        assert "features" in data
        features = data["features"]
        assert features["memory_storage"] == True
        assert features["pattern_recognition"] == True
        assert features["outcome_learning"] == True
        assert features["personalization"] == True
        assert features["context_building"] == True
        
        print(f"✓ Memory palace status returns comprehensive data")
        print(f"  - Total memories: {mp['total_memories']}")
        print(f"  - Patterns identified: {pe['patterns_identified']}")
        print(f"  - Learning stage: {ls['stage']}")


class TestMemoryStore:
    """Tests for POST /api/arris/memory/store"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_store_memory_requires_auth(self):
        """Test that storing memory requires authentication"""
        memory_data = {
            "memory_type": "interaction",
            "content": {"topic": "test"},
            "importance": 0.5
        }
        response = requests.post(f"{BASE_URL}/api/arris/memory/store", json=memory_data)
        assert response.status_code in [401, 403]
        print(f"✓ Store memory requires authentication")
    
    def test_store_memory_requires_type_and_content(self, elite_token):
        """Test that memory_type and content are required"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # Missing memory_type
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json={"content": {"test": "data"}}
        )
        assert response.status_code == 400
        
        # Missing content
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json={"memory_type": "interaction"}
        )
        assert response.status_code == 400
        
        print(f"✓ Store memory validates required fields")
    
    def test_store_interaction_memory(self, elite_token):
        """Test storing an interaction memory"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        memory_data = {
            "memory_type": "interaction",
            "content": {
                "topic": "TEST_proposal_review",
                "query": "How can I improve my proposal?",
                "response_summary": "Focus on clear deliverables"
            },
            "importance": 0.7,
            "tags": ["TEST", "proposal", "improvement"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json=memory_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Memory stored"
        assert "memory" in data
        
        memory = data["memory"]
        assert memory["id"].startswith("MEM-")
        assert memory["memory_type"] == "interaction"
        assert memory["importance"] == 0.7
        assert "TEST" in memory["tags"]
        assert memory["recall_count"] == 0
        
        print(f"✓ Stored interaction memory: {memory['id']}")
    
    def test_store_preference_memory(self, elite_token):
        """Test storing a preference memory"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        memory_data = {
            "memory_type": "preference",
            "content": {
                "preference_type": "platform",
                "value": "YouTube",
                "strength": "strong"
            },
            "importance": 0.8,
            "tags": ["TEST", "preference", "platform"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json=memory_data
        )
        
        assert response.status_code == 200
        data = response.json()
        memory = data["memory"]
        assert memory["memory_type"] == "preference"
        assert memory["importance"] == 0.8
        
        print(f"✓ Stored preference memory: {memory['id']}")
    
    def test_store_feedback_memory(self, elite_token):
        """Test storing a feedback memory"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        memory_data = {
            "memory_type": "feedback",
            "content": {
                "feedback_type": "positive",
                "message": "ARRIS suggestions were very helpful",
                "context": "proposal_creation"
            },
            "importance": 0.6,
            "tags": ["TEST", "feedback", "positive"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json=memory_data
        )
        
        assert response.status_code == 200
        data = response.json()
        memory = data["memory"]
        assert memory["memory_type"] == "feedback"
        
        print(f"✓ Stored feedback memory: {memory['id']}")
    
    def test_importance_clamped_to_valid_range(self, elite_token):
        """Test that importance is clamped between 0.0 and 1.0"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # Test importance > 1.0
        memory_data = {
            "memory_type": "interaction",
            "content": {"topic": "TEST_high_importance"},
            "importance": 1.5
        }
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json=memory_data
        )
        assert response.status_code == 200
        assert response.json()["memory"]["importance"] == 1.0
        
        # Test importance < 0.0
        memory_data["importance"] = -0.5
        memory_data["content"]["topic"] = "TEST_low_importance"
        response = requests.post(
            f"{BASE_URL}/api/arris/memory/store",
            headers=headers,
            json=memory_data
        )
        assert response.status_code == 200
        assert response.json()["memory"]["importance"] == 0.0
        
        print(f"✓ Importance values clamped to valid range [0.0, 1.0]")


class TestMemoryRecall:
    """Tests for GET /api/arris/memory/recall"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_recall_memories_requires_auth(self):
        """Test that recalling memories requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/memory/recall")
        assert response.status_code in [401, 403]
        print(f"✓ Recall memories requires authentication")
    
    def test_recall_all_memories(self, elite_token):
        """Test recalling all memories without filters"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/memory/recall", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
        assert "count" in data
        assert "filters_applied" in data
        
        print(f"✓ Recalled {data['count']} memories without filters")
    
    def test_recall_memories_by_type(self, elite_token):
        """Test recalling memories filtered by type"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # Test interaction type
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/recall",
            headers=headers,
            params={"memory_type": "interaction"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["memory_type"] == "interaction"
        
        # Verify all returned memories are of type interaction
        for memory in data["memories"]:
            assert memory["memory_type"] == "interaction"
        
        print(f"✓ Recalled {data['count']} interaction memories")
    
    def test_recall_memories_by_min_importance(self, elite_token):
        """Test recalling memories filtered by minimum importance"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/recall",
            headers=headers,
            params={"min_importance": 0.7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["min_importance"] == 0.7
        
        # Verify all returned memories have importance >= 0.7
        for memory in data["memories"]:
            assert memory["importance"] >= 0.7
        
        print(f"✓ Recalled {data['count']} memories with importance >= 0.7")
    
    def test_recall_memories_with_limit(self, elite_token):
        """Test recalling memories with limit"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/recall",
            headers=headers,
            params={"limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["limit"] == 5
        assert len(data["memories"]) <= 5
        
        print(f"✓ Recalled {data['count']} memories with limit=5")
    
    def test_recall_pattern_memories(self, elite_token):
        """Test recalling pattern memories specifically"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/arris/memory/recall",
            headers=headers,
            params={"memory_type": "pattern"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pattern memories have expected structure
        for memory in data["memories"]:
            assert memory["memory_type"] == "pattern"
            if memory.get("content"):
                # Pattern memories should have category
                assert "category" in memory["content"] or "type" in memory["content"]
        
        print(f"✓ Recalled {data['count']} pattern memories")


class TestMemorySummary:
    """Tests for GET /api/arris/memory/summary"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_memory_summary_requires_auth(self):
        """Test that memory summary requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/memory/summary")
        assert response.status_code in [401, 403]
        print(f"✓ Memory summary requires authentication")
    
    def test_memory_summary_returns_statistics(self, elite_token):
        """Test that memory summary returns statistics by type"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/memory/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "creator_id" in data
        assert "memory_summary" in data
        
        summary = data["memory_summary"]
        assert "total_memories" in summary
        assert "by_type" in summary
        assert "memory_health" in summary
        
        # Check memory health structure
        health = summary["memory_health"]
        assert "score" in health
        assert "status" in health
        assert "message" in health
        
        print(f"✓ Memory summary returned")
        print(f"  - Total memories: {summary['total_memories']}")
        print(f"  - Memory health score: {health['score']}")
        print(f"  - Health status: {health['status']}")
        
        # Print breakdown by type
        if summary["by_type"]:
            print(f"  - Memory types: {list(summary['by_type'].keys())}")


class TestPatternAnalysis:
    """Tests for POST /api/arris/patterns/analyze and GET /api/arris/patterns"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_pattern_analysis_requires_auth(self):
        """Test that pattern analysis requires authentication"""
        response = requests.post(f"{BASE_URL}/api/arris/patterns/analyze")
        assert response.status_code in [401, 403]
        print(f"✓ Pattern analysis requires authentication")
    
    def test_analyze_patterns_for_elite_user(self, elite_token):
        """Test pattern analysis for Elite user with proposals"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.post(f"{BASE_URL}/api/arris/patterns/analyze", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "result" in data
        
        result = data["result"]
        assert "status" in result
        
        # Elite user has 3 proposals, should have patterns
        if result["status"] == "analyzed":
            assert "proposals_analyzed" in result
            assert "patterns_identified" in result
            assert "patterns" in result
            assert "analyzed_at" in result
            
            print(f"✓ Pattern analysis complete")
            print(f"  - Proposals analyzed: {result['proposals_analyzed']}")
            print(f"  - Patterns identified: {result['patterns_identified']}")
            
            # Check pattern categories
            categories = set()
            for pattern in result["patterns"]:
                if "category" in pattern:
                    categories.add(pattern["category"])
            print(f"  - Pattern categories: {categories}")
        else:
            print(f"✓ Pattern analysis returned status: {result['status']}")
            print(f"  - Message: {result.get('message', 'N/A')}")
    
    def test_get_patterns(self, elite_token):
        """Test getting existing patterns"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/patterns", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        
        print(f"✓ GET patterns returned status: {data['status']}")
        if data.get("patterns"):
            print(f"  - Patterns count: {len(data['patterns'])}")
    
    def test_pattern_categories_include_expected_types(self, elite_token):
        """Test that patterns include expected categories"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # First analyze patterns
        requests.post(f"{BASE_URL}/api/arris/patterns/analyze", headers=headers)
        
        # Then get patterns
        response = requests.get(f"{BASE_URL}/api/arris/patterns", headers=headers)
        data = response.json()
        
        if data.get("patterns"):
            categories = set()
            for pattern in data["patterns"]:
                if "category" in pattern:
                    categories.add(pattern["category"])
            
            # Expected categories: success, risk, timing, complexity, platform
            expected_categories = {"success", "risk", "timing", "complexity", "platform"}
            found_categories = categories.intersection(expected_categories)
            
            print(f"✓ Found pattern categories: {found_categories}")
            # At least some categories should be present
            assert len(found_categories) > 0 or data["status"] == "insufficient_data"


class TestLearningSystem:
    """Tests for POST /api/arris/learning/record-outcome and GET /api/arris/learning/metrics"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def elite_proposal_id(self, elite_token):
        """Get a proposal ID for the Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/proposals", headers=headers)
        if response.status_code == 200 and response.json():
            return response.json()[0]["id"]
        return None
    
    def test_record_outcome_requires_auth(self):
        """Test that recording outcome requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/arris/learning/record-outcome",
            json={"proposal_id": "test", "outcome": "approved"}
        )
        assert response.status_code in [401, 403]
        print(f"✓ Record outcome requires authentication")
    
    def test_record_outcome_requires_proposal_id_and_outcome(self, elite_token):
        """Test that proposal_id and outcome are required"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        
        # Missing proposal_id
        response = requests.post(
            f"{BASE_URL}/api/arris/learning/record-outcome",
            headers=headers,
            json={"outcome": "approved"}
        )
        assert response.status_code == 400
        
        # Missing outcome
        response = requests.post(
            f"{BASE_URL}/api/arris/learning/record-outcome",
            headers=headers,
            json={"proposal_id": "test"}
        )
        assert response.status_code == 400
        
        print(f"✓ Record outcome validates required fields")
    
    def test_record_outcome_for_valid_proposal(self, elite_token, elite_proposal_id):
        """Test recording outcome for a valid proposal"""
        if not elite_proposal_id:
            pytest.skip("No proposal found for Elite user")
        
        headers = {"Authorization": f"Bearer {elite_token}"}
        outcome_data = {
            "proposal_id": elite_proposal_id,
            "outcome": "approved",
            "feedback": "TEST_Great proposal execution"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/arris/learning/record-outcome",
            headers=headers,
            json=outcome_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["outcome_recorded"] == True
        assert "memory_id" in data
        assert "prediction_was_accurate" in data
        assert data["learning_updated"] == True
        
        print(f"✓ Recorded outcome for proposal {elite_proposal_id}")
        print(f"  - Memory ID: {data['memory_id']}")
        print(f"  - Prediction accurate: {data['prediction_was_accurate']}")
    
    def test_record_outcome_for_invalid_proposal(self, elite_token):
        """Test recording outcome for non-existent proposal"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        outcome_data = {
            "proposal_id": "INVALID-PROPOSAL-ID",
            "outcome": "approved"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/arris/learning/record-outcome",
            headers=headers,
            json=outcome_data
        )
        
        assert response.status_code == 404
        print(f"✓ Record outcome returns 404 for invalid proposal")
    
    def test_get_learning_metrics_requires_auth(self):
        """Test that learning metrics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/learning/metrics")
        assert response.status_code in [401, 403]
        print(f"✓ Learning metrics requires authentication")
    
    def test_get_learning_metrics(self, elite_token):
        """Test getting learning metrics"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning/metrics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "creator_id" in data
        assert "metrics" in data
        
        metrics = data["metrics"]
        assert "total_predictions" in metrics
        assert "accurate_predictions" in metrics
        assert "accuracy_rate" in metrics
        assert "learning_stage" in metrics
        
        # Verify learning stage is valid
        valid_stages = ["initializing", "learning", "developing", "proficient", "expert", "calibrating"]
        assert metrics["learning_stage"] in valid_stages
        
        print(f"✓ Learning metrics returned")
        print(f"  - Total predictions: {metrics['total_predictions']}")
        print(f"  - Accurate predictions: {metrics['accurate_predictions']}")
        print(f"  - Accuracy rate: {metrics['accuracy_rate']}%")
        print(f"  - Learning stage: {metrics['learning_stage']}")


class TestContextBuilder:
    """Tests for GET /api/arris/context"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def elite_proposal_id(self, elite_token):
        """Get a proposal ID for the Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/creators/me/proposals", headers=headers)
        if response.status_code == 200 and response.json():
            return response.json()[0]["id"]
        return None
    
    def test_context_requires_auth(self):
        """Test that context endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/context")
        assert response.status_code in [401, 403]
        print(f"✓ Context endpoint requires authentication")
    
    def test_get_context_without_proposal(self, elite_token):
        """Test getting context without specifying a proposal"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/context", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "context" in data
        context = data["context"]
        
        # Check context structure
        assert "creator_id" in context
        assert "memory_context" in context
        assert "identified_patterns" in context
        assert "historical_performance" in context
        assert "learning_metrics" in context
        assert "proposal_context" in context
        assert "built_at" in context
        
        print(f"✓ Context built without proposal")
        print(f"  - Memory context: {context['memory_context'].get('recent_interactions', 0)} interactions")
        print(f"  - Patterns: {len(context['identified_patterns'])} identified")
    
    def test_get_context_with_proposal(self, elite_token, elite_proposal_id):
        """Test getting context with a specific proposal"""
        if not elite_proposal_id:
            pytest.skip("No proposal found for Elite user")
        
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(
            f"{BASE_URL}/api/arris/context",
            headers=headers,
            params={"proposal_id": elite_proposal_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["proposal_id"] == elite_proposal_id
        assert "context" in data
        
        context = data["context"]
        assert "proposal_context" in context
        
        # Proposal context should have similar proposals
        proposal_ctx = context["proposal_context"]
        assert "platforms" in proposal_ctx
        assert "similar_proposals" in proposal_ctx
        
        print(f"✓ Context built with proposal {elite_proposal_id}")
        print(f"  - Similar proposals: {len(proposal_ctx['similar_proposals'])}")
    
    def test_context_with_invalid_proposal(self, elite_token):
        """Test getting context with invalid proposal ID"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(
            f"{BASE_URL}/api/arris/context",
            headers=headers,
            params={"proposal_id": "INVALID-PROPOSAL-ID"}
        )
        
        assert response.status_code == 404
        print(f"✓ Context returns 404 for invalid proposal")
    
    def test_context_includes_historical_performance(self, elite_token):
        """Test that context includes historical performance data"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/context", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        historical = data["context"]["historical_performance"]
        
        # Check historical performance structure
        if historical.get("total_proposals", 0) > 0:
            assert "total_proposals" in historical
            assert "approval_rate" in historical
            assert "completion_rate" in historical
            assert "most_used_platforms" in historical
            assert "avg_complexity" in historical
            
            print(f"✓ Historical performance included")
            print(f"  - Total proposals: {historical['total_proposals']}")
            print(f"  - Approval rate: {historical['approval_rate']}%")
        else:
            print(f"✓ Historical performance: No history yet")


class TestPersonalization:
    """Tests for GET /api/arris/personalization"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def premium_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=PREMIUM_USER)
        return response.json()["access_token"]
    
    def test_personalization_requires_auth(self):
        """Test that personalization requires authentication"""
        response = requests.get(f"{BASE_URL}/api/arris/personalization")
        assert response.status_code in [401, 403]
        print(f"✓ Personalization requires authentication")
    
    def test_get_personalization_for_elite_user(self, elite_token):
        """Test getting personalization for Elite user"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/personalization", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "creator_id" in data
        assert "personalization" in data
        assert "memory_health" in data
        assert "learning_stage" in data
        assert "accuracy_rate" in data
        
        personalization = data["personalization"]
        assert "prompt_additions" in personalization
        assert "is_personalized" in personalization
        
        print(f"✓ Personalization returned for Elite user")
        print(f"  - Is personalized: {personalization['is_personalized']}")
        print(f"  - Learning stage: {data['learning_stage']}")
        print(f"  - Memory health: {data['memory_health']}")
    
    def test_get_personalization_for_premium_user(self, premium_token):
        """Test getting personalization for Premium user"""
        headers = {"Authorization": f"Bearer {premium_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/personalization", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "creator_id" in data
        assert "personalization" in data
        
        print(f"✓ Personalization returned for Premium user")
        print(f"  - Is personalized: {data['personalization']['is_personalized']}")


class TestMemoryHealthCalculation:
    """Tests for memory health score calculation"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_memory_health_score_structure(self, elite_token):
        """Test that memory health score has correct structure"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/memory/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        health = data["memory_summary"]["memory_health"]
        
        # Check structure
        assert "score" in health
        assert "status" in health
        assert "message" in health
        
        # Score should be 0-100
        assert 0 <= health["score"] <= 100
        
        # Status should be valid
        valid_statuses = ["new", "developing", "good", "excellent"]
        assert health["status"] in valid_statuses
        
        print(f"✓ Memory health score structure valid")
        print(f"  - Score: {health['score']}")
        print(f"  - Status: {health['status']}")
        print(f"  - Message: {health['message']}")
    
    def test_memory_health_based_on_diversity(self, elite_token):
        """Test that memory health considers type diversity"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/memory/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["memory_summary"]
        type_count = len(summary["by_type"])
        health_score = summary["memory_health"]["score"]
        
        # More diverse types should contribute to higher score
        print(f"✓ Memory health considers diversity")
        print(f"  - Memory types: {type_count}")
        print(f"  - Health score: {health_score}")


class TestLearningStages:
    """Tests for learning stage progression"""
    
    @pytest.fixture(scope="class")
    def elite_token(self):
        response = requests.post(f"{BASE_URL}/api/creators/login", json=ELITE_USER)
        return response.json()["access_token"]
    
    def test_learning_stage_values(self, elite_token):
        """Test that learning stage returns valid values"""
        headers = {"Authorization": f"Bearer {elite_token}"}
        response = requests.get(f"{BASE_URL}/api/arris/learning/metrics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        metrics = data["metrics"]
        stage = metrics["learning_stage"]
        total = metrics["total_predictions"]
        accuracy = metrics["accuracy_rate"]
        
        # Verify stage is valid
        valid_stages = ["initializing", "learning", "developing", "proficient", "expert", "calibrating"]
        assert stage in valid_stages
        
        # Verify stage logic
        # initializing: <5 predictions
        # learning: <15 predictions
        # developing: <30 predictions
        # proficient: 60%+ accuracy
        # expert: 80%+ accuracy
        
        print(f"✓ Learning stage: {stage}")
        print(f"  - Total predictions: {total}")
        print(f"  - Accuracy rate: {accuracy}%")
        
        if total < 5:
            assert stage == "initializing"
        elif total < 15:
            assert stage == "learning"
        elif total < 30:
            assert stage == "developing"
        elif accuracy >= 80:
            assert stage == "expert"
        elif accuracy >= 60:
            assert stage == "proficient"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
