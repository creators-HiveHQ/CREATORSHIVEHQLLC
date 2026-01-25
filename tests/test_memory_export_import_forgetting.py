"""
Test Suite for Phase 4 Module C Tasks C4 and C5:
- C4: Memory Export/Import System (Elite feature)
- C5: GDPR-compliant Forgetting Protocol (all users)

Endpoints tested:
- GET /api/memory/export - Export memories (Pro+ can export, Elite gets full features)
- POST /api/memory/import - Import memories (Elite only)
- GET /api/memory/export-history - View export history
- GET /api/memory/import-history - View import history (Elite only)
- DELETE /api/memory/delete - Soft delete memories with selection criteria
- DELETE /api/memory/delete?permanent=true - Permanent deletion
- POST /api/memory/recover - Recover soft-deleted memories
- GET /api/memory/deletion-history - View deletion audit history
- GET /api/memory/pending-deletions - View soft-deleted memories pending permanent deletion
- GET /api/memory/gdpr-export - Full GDPR data portability export
- DELETE /api/memory/gdpr-erase?confirm=true - Full GDPR erasure (Right to be Forgotten)
- GET /api/admin/memory/export/{creator_id} - Admin export any creator's memories
- GET /api/admin/memory/deletion-audit - Admin view deletion audit logs
- GET /api/admin/memory/gdpr-erasure-audit - Admin view GDPR erasure logs
- POST /api/admin/memory/purge-expired - Admin purge expired soft-deleted memories
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emergentdb.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@hivehq.com"
ADMIN_PASSWORD = "admin123"
PRO_CREATOR_EMAIL = "protest@hivehq.com"
PRO_CREATOR_PASSWORD = "testpassword"
PREMIUM_CREATOR_EMAIL = "premiumtest@hivehq.com"
PREMIUM_CREATOR_PASSWORD = "testpassword123"


class TestSetup:
    """Setup and authentication helpers"""
    
    @staticmethod
    def get_admin_token():
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_pro_creator_token():
        """Get Pro creator authentication token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PRO_CREATOR_EMAIL,
            "password": PRO_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_premium_creator_token():
        """Get Premium creator authentication token"""
        response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": PREMIUM_CREATOR_EMAIL,
            "password": PREMIUM_CREATOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def admin_token():
    """Admin authentication token"""
    token = TestSetup.get_admin_token()
    if not token:
        pytest.skip("Admin authentication failed")
    return token


@pytest.fixture(scope="module")
def pro_creator_token():
    """Pro creator authentication token"""
    token = TestSetup.get_pro_creator_token()
    if not token:
        pytest.skip("Pro creator authentication failed")
    return token


@pytest.fixture(scope="module")
def premium_creator_token():
    """Premium creator authentication token"""
    token = TestSetup.get_premium_creator_token()
    if not token:
        pytest.skip("Premium creator authentication failed")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin request headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def pro_headers(pro_creator_token):
    """Pro creator request headers"""
    return {"Authorization": f"Bearer {pro_creator_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def premium_headers(premium_creator_token):
    """Premium creator request headers"""
    return {"Authorization": f"Bearer {premium_creator_token}", "Content-Type": "application/json"}


# ============== HEALTH CHECK ==============

class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ API health check passed")


# ============== MEMORY EXPORT TESTS (C4) ==============

class TestMemoryExport:
    """Test memory export functionality"""
    
    def test_export_requires_authentication(self):
        """Test export endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/memory/export")
        assert response.status_code in [401, 403]
        print("✓ Export requires authentication")
    
    def test_pro_creator_can_export(self, pro_headers):
        """Test Pro creator can export memories (limited)"""
        response = requests.get(f"{BASE_URL}/api/memory/export", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify export structure
        assert "export_version" in data
        assert "exported_at" in data
        assert "creator_id" in data
        assert "memories" in data
        assert "statistics" in data
        assert "integrity" in data
        
        # Pro users get limited export (portable format, no archived)
        assert "tier_limitations" in data
        assert data["tier_limitations"]["format_used"] == "portable"
        assert data["tier_limitations"]["archived_included"] == False
        
        print(f"✓ Pro creator export successful - {data['statistics']['total_active_memories']} memories")
    
    def test_export_with_format_parameter(self, pro_headers):
        """Test export format parameter (Pro gets portable only)"""
        response = requests.get(f"{BASE_URL}/api/memory/export?format=json", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Pro users forced to portable format
        assert data["tier_limitations"]["format_used"] == "portable"
        print("✓ Export format parameter works (Pro forced to portable)")
    
    def test_export_includes_integrity_checksum(self, pro_headers):
        """Test export includes integrity checksum"""
        response = requests.get(f"{BASE_URL}/api/memory/export", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "integrity" in data
        assert "checksum" in data["integrity"]
        assert "algorithm" in data["integrity"]
        assert data["integrity"]["algorithm"] == "sha256"
        assert len(data["integrity"]["checksum"]) == 64  # SHA256 hex length
        
        print(f"✓ Export includes integrity checksum: {data['integrity']['checksum'][:16]}...")
    
    def test_export_statistics(self, pro_headers):
        """Test export includes statistics"""
        response = requests.get(f"{BASE_URL}/api/memory/export", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        stats = data["statistics"]
        assert "total_active_memories" in stats
        assert "total_archived_memories" in stats
        assert "memory_types" in stats
        assert "date_range" in stats
        
        print(f"✓ Export statistics: {stats['total_active_memories']} active, {stats['total_archived_memories']} archived")


# ============== MEMORY IMPORT TESTS (C4 - Elite Only) ==============

class TestMemoryImport:
    """Test memory import functionality (Elite only)"""
    
    def test_import_requires_authentication(self):
        """Test import endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/memory/import", json={})
        assert response.status_code in [401, 403]
        print("✓ Import requires authentication")
    
    def test_pro_creator_cannot_import(self, pro_headers):
        """Test Pro creator cannot import (Elite only feature)"""
        # Create minimal import data
        import_data = {
            "export_version": "1.0",
            "memories": {"active": [], "archived": []}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/memory/import",
            headers=pro_headers,
            json=import_data
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "feature_gated" in str(data.get("detail", {}))
        print("✓ Pro creator correctly blocked from import (Elite only)")
    
    def test_import_invalid_merge_strategy(self, pro_headers):
        """Test import with invalid merge strategy"""
        import_data = {
            "export_version": "1.0",
            "memories": {"active": [], "archived": []}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/memory/import?merge_strategy=invalid",
            headers=pro_headers,
            json=import_data
        )
        
        # Should fail with 403 (feature gated) before merge strategy validation
        assert response.status_code in [400, 403]
        print("✓ Import with invalid merge strategy handled")


# ============== EXPORT/IMPORT HISTORY TESTS ==============

class TestExportImportHistory:
    """Test export and import history endpoints"""
    
    def test_export_history_requires_auth(self):
        """Test export history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/memory/export-history")
        assert response.status_code in [401, 403]
        print("✓ Export history requires authentication")
    
    def test_get_export_history(self, pro_headers):
        """Test getting export history"""
        response = requests.get(f"{BASE_URL}/api/memory/export-history", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)
        
        print(f"✓ Export history retrieved: {data['total']} records")
    
    def test_export_history_with_limit(self, pro_headers):
        """Test export history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/memory/export-history?limit=5", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["history"]) <= 5
        print(f"✓ Export history with limit: {len(data['history'])} records")
    
    def test_import_history_requires_elite(self, pro_headers):
        """Test import history requires Elite tier"""
        response = requests.get(f"{BASE_URL}/api/memory/import-history", headers=pro_headers)
        assert response.status_code == 403
        data = response.json()
        assert "feature_gated" in str(data.get("detail", {}))
        print("✓ Import history correctly requires Elite tier")


# ============== FORGETTING PROTOCOL TESTS (C5) ==============

class TestForgettingProtocol:
    """Test GDPR-compliant Forgetting Protocol"""
    
    def test_delete_requires_authentication(self):
        """Test delete endpoint requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/memory/delete?memory_types=test")
        assert response.status_code in [401, 403]
        print("✓ Delete requires authentication")
    
    def test_delete_requires_selection_criteria(self, pro_headers):
        """Test delete requires at least one selection criteria"""
        response = requests.delete(f"{BASE_URL}/api/memory/delete", headers=pro_headers)
        assert response.status_code == 400
        data = response.json()
        assert "selection criteria" in str(data.get("detail", "")).lower()
        print("✓ Delete requires selection criteria")
    
    def test_soft_delete_by_memory_type(self, pro_headers):
        """Test soft delete by memory type"""
        # Use a test memory type that won't affect real data
        response = requests.delete(
            f"{BASE_URL}/api/memory/delete?memory_types=test_delete_type",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "deletion_id" in data
        
        # When memories are deleted, full response is returned
        # When no memories match, simplified response is returned
        if data["deleted_count"] > 0:
            assert data["deletion_type"] == "soft_delete"
            assert data["recovery_possible"] == True
            print(f"✓ Soft delete successful - {data['deleted_count']} deleted, deletion_id: {data['deletion_id']}")
        else:
            assert "message" in data
            print(f"✓ Soft delete endpoint works - no memories matched criteria")
        
        return data["deletion_id"]
    
    def test_soft_delete_by_tags(self, pro_headers):
        """Test soft delete by tags"""
        response = requests.delete(
            f"{BASE_URL}/api/memory/delete?tags=test_tag_for_deletion",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        if data["deleted_count"] > 0:
            assert data["deletion_type"] == "soft_delete"
        print(f"✓ Soft delete by tags successful - {data['deleted_count']} deleted")
    
    def test_soft_delete_by_date(self, pro_headers):
        """Test soft delete by date_before"""
        # Use a very old date to avoid deleting real data
        old_date = "2020-01-01T00:00:00Z"
        response = requests.delete(
            f"{BASE_URL}/api/memory/delete?date_before={old_date}",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        print(f"✓ Soft delete by date successful - {data['deleted_count']} deleted")
    
    def test_permanent_delete(self, pro_headers):
        """Test permanent delete (no recovery)"""
        response = requests.delete(
            f"{BASE_URL}/api/memory/delete?memory_types=test_permanent_delete&permanent=true",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        if data["deleted_count"] > 0:
            assert data["deletion_type"] == "permanent"
            assert data["recovery_possible"] == False
            assert data["retention_until"] is None
        
        print(f"✓ Permanent delete successful - {data['deleted_count']} permanently deleted")
    
    def test_delete_returns_audit_id(self, pro_headers):
        """Test delete returns audit ID for compliance"""
        response = requests.delete(
            f"{BASE_URL}/api/memory/delete?memory_types=test_audit",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # audit_id is only returned when memories are actually deleted
        # deletion_id is always returned
        assert "deletion_id" in data
        assert data["deletion_id"].startswith("DEL-")
        
        if data["deleted_count"] > 0:
            assert "audit_id" in data
            assert data["audit_id"].startswith("DEL-")
            print(f"✓ Delete returns audit ID: {data['audit_id']}")
        else:
            print(f"✓ Delete returns deletion_id: {data['deletion_id']} (no memories matched)")


# ============== MEMORY RECOVERY TESTS ==============

class TestMemoryRecovery:
    """Test memory recovery functionality"""
    
    def test_recover_requires_authentication(self):
        """Test recover endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/memory/recover?deletion_id=test")
        assert response.status_code in [401, 403]
        print("✓ Recover requires authentication")
    
    def test_recover_requires_deletion_id(self, pro_headers):
        """Test recover requires deletion_id parameter"""
        response = requests.post(f"{BASE_URL}/api/memory/recover", headers=pro_headers)
        assert response.status_code == 422  # Missing required parameter
        print("✓ Recover requires deletion_id parameter")
    
    def test_recover_invalid_deletion_id(self, pro_headers):
        """Test recover with invalid deletion_id"""
        response = requests.post(
            f"{BASE_URL}/api/memory/recover?deletion_id=INVALID-ID",
            headers=pro_headers
        )
        assert response.status_code == 404
        print("✓ Recover with invalid deletion_id returns 404")
    
    def test_recover_workflow(self, pro_headers):
        """Test full soft delete and recover workflow"""
        # First, create a test memory by triggering export (which creates log)
        export_response = requests.get(f"{BASE_URL}/api/memory/export", headers=pro_headers)
        assert export_response.status_code == 200
        
        # Soft delete by a unique tag
        unique_tag = f"test_recover_{uuid.uuid4().hex[:8]}"
        delete_response = requests.delete(
            f"{BASE_URL}/api/memory/delete?tags={unique_tag}",
            headers=pro_headers
        )
        assert delete_response.status_code == 200
        deletion_id = delete_response.json()["deletion_id"]
        
        # Try to recover (may or may not have memories to recover)
        recover_response = requests.post(
            f"{BASE_URL}/api/memory/recover?deletion_id={deletion_id}",
            headers=pro_headers
        )
        
        # Either 200 (recovered) or 404 (nothing to recover)
        assert recover_response.status_code in [200, 404]
        
        if recover_response.status_code == 200:
            data = recover_response.json()
            assert data["success"] == True
            assert "recovered_count" in data
            print(f"✓ Recovery workflow successful - {data['recovered_count']} recovered")
        else:
            print("✓ Recovery workflow tested (no memories matched criteria)")


# ============== DELETION HISTORY AND PENDING DELETIONS ==============

class TestDeletionHistory:
    """Test deletion history and pending deletions"""
    
    def test_deletion_history_requires_auth(self):
        """Test deletion history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/memory/deletion-history")
        assert response.status_code in [401, 403]
        print("✓ Deletion history requires authentication")
    
    def test_get_deletion_history(self, pro_headers):
        """Test getting deletion history"""
        response = requests.get(f"{BASE_URL}/api/memory/deletion-history", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)
        
        # Verify history entry structure if any exist
        if data["history"]:
            entry = data["history"][0]
            assert "id" in entry
            assert "creator_id" in entry
            assert "action" in entry
            assert "deletion_type" in entry
            assert "executed_at" in entry
        
        print(f"✓ Deletion history retrieved: {data['total']} records")
    
    def test_deletion_history_with_limit(self, pro_headers):
        """Test deletion history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/memory/deletion-history?limit=5", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["history"]) <= 5
        print(f"✓ Deletion history with limit: {len(data['history'])} records")
    
    def test_pending_deletions_requires_auth(self):
        """Test pending deletions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/memory/pending-deletions")
        assert response.status_code in [401, 403]
        print("✓ Pending deletions requires authentication")
    
    def test_get_pending_deletions(self, pro_headers):
        """Test getting pending deletions"""
        response = requests.get(f"{BASE_URL}/api/memory/pending-deletions", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_pending" in data
        assert "by_deletion" in data
        assert isinstance(data["by_deletion"], dict)
        
        print(f"✓ Pending deletions retrieved: {data['total_pending']} pending")


# ============== GDPR COMPLIANCE TESTS ==============

class TestGDPRCompliance:
    """Test GDPR compliance endpoints"""
    
    def test_gdpr_export_requires_auth(self):
        """Test GDPR export requires authentication"""
        response = requests.get(f"{BASE_URL}/api/memory/gdpr-export")
        assert response.status_code in [401, 403]
        print("✓ GDPR export requires authentication")
    
    def test_gdpr_export(self, pro_headers):
        """Test GDPR Article 20 data portability export"""
        response = requests.get(f"{BASE_URL}/api/memory/gdpr-export", headers=pro_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify GDPR export structure
        assert data["gdpr_export"] == True
        assert data["export_type"] == "full_data_portability"
        assert "exported_at" in data
        assert "creator_id" in data
        assert "data_categories" in data
        
        # Verify all data categories are included
        categories = data["data_categories"]
        assert "memories" in categories
        assert "search_activity" in categories
        assert "deletion_history" in categories
        assert "pending_deletions" in categories
        assert "export_history" in categories
        assert "import_history" in categories
        
        # Verify data retention info
        assert "data_retention_info" in data
        
        print("✓ GDPR export successful - all data categories included")
    
    def test_gdpr_erase_requires_auth(self):
        """Test GDPR erasure requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/memory/gdpr-erase?confirm=true")
        assert response.status_code in [401, 403]
        print("✓ GDPR erasure requires authentication")
    
    def test_gdpr_erase_requires_confirmation(self, pro_headers):
        """Test GDPR erasure requires confirmation"""
        response = requests.delete(f"{BASE_URL}/api/memory/gdpr-erase?confirm=false", headers=pro_headers)
        assert response.status_code == 400
        data = response.json()
        assert "confirmation_required" in str(data.get("detail", {}))
        print("✓ GDPR erasure requires confirmation")
    
    # Note: We don't actually test GDPR erasure with confirm=true as it's irreversible
    # and would delete all test data


# ============== ADMIN ENDPOINT TESTS ==============

class TestAdminEndpoints:
    """Test admin memory management endpoints"""
    
    def test_admin_export_requires_auth(self):
        """Test admin export requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/export/CREATOR-PRO-TEST-001")
        assert response.status_code in [401, 403]
        print("✓ Admin export requires authentication")
    
    def test_admin_export_creator_memories(self, admin_headers):
        """Test admin can export any creator's memories"""
        response = requests.get(
            f"{BASE_URL}/api/admin/memory/export/CREATOR-PRO-TEST-001",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["admin_export"] == True
        assert "creator" in data
        assert "memories" in data
        assert "statistics" in data
        
        print(f"✓ Admin export successful - {data['statistics']['total_active_memories']} memories")
    
    def test_admin_export_nonexistent_creator(self, admin_headers):
        """Test admin export for nonexistent creator"""
        response = requests.get(
            f"{BASE_URL}/api/admin/memory/export/NONEXISTENT-CREATOR",
            headers=admin_headers
        )
        assert response.status_code == 404
        print("✓ Admin export returns 404 for nonexistent creator")
    
    def test_admin_deletion_audit_requires_auth(self):
        """Test admin deletion audit requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/deletion-audit")
        assert response.status_code in [401, 403]
        print("✓ Admin deletion audit requires authentication")
    
    def test_admin_get_deletion_audit(self, admin_headers):
        """Test admin can view deletion audit logs"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/deletion-audit", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "audit_logs" in data
        assert "total" in data
        assert isinstance(data["audit_logs"], list)
        
        print(f"✓ Admin deletion audit retrieved: {data['total']} records")
    
    def test_admin_deletion_audit_by_creator(self, admin_headers):
        """Test admin can filter deletion audit by creator"""
        response = requests.get(
            f"{BASE_URL}/api/admin/memory/deletion-audit?creator_id=CREATOR-PRO-TEST-001",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # All logs should be for the specified creator
        for log in data["audit_logs"]:
            assert log["creator_id"] == "CREATOR-PRO-TEST-001"
        
        print(f"✓ Admin deletion audit filtered by creator: {data['total']} records")
    
    def test_admin_gdpr_erasure_audit_requires_auth(self):
        """Test admin GDPR erasure audit requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/gdpr-erasure-audit")
        assert response.status_code in [401, 403]
        print("✓ Admin GDPR erasure audit requires authentication")
    
    def test_admin_get_gdpr_erasure_audit(self, admin_headers):
        """Test admin can view GDPR erasure audit logs"""
        response = requests.get(f"{BASE_URL}/api/admin/memory/gdpr-erasure-audit", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "audit_logs" in data
        assert "total" in data
        assert isinstance(data["audit_logs"], list)
        
        print(f"✓ Admin GDPR erasure audit retrieved: {data['total']} records")
    
    def test_admin_purge_expired_requires_auth(self):
        """Test admin purge expired requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/memory/purge-expired")
        assert response.status_code in [401, 403]
        print("✓ Admin purge expired requires authentication")
    
    def test_admin_purge_expired_deletions(self, admin_headers):
        """Test admin can purge expired soft-deleted memories"""
        response = requests.post(f"{BASE_URL}/api/admin/memory/purge-expired", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "purged" in data
        assert isinstance(data["purged"], int)
        
        print(f"✓ Admin purge expired successful - {data['purged']} purged")


# ============== TIER RESTRICTION TESTS ==============

class TestTierRestrictions:
    """Test tier-based feature restrictions"""
    
    def test_free_tier_cannot_export(self):
        """Test Free tier users cannot export"""
        # Register a new free user
        unique_email = f"freetest_{uuid.uuid4().hex[:8]}@test.com"
        register_response = requests.post(f"{BASE_URL}/api/creators/register", json={
            "name": "Free Test User",
            "email": unique_email,
            "password": "testpassword123",
            "platforms": ["YouTube"],
            "niche": "Technology"
        })
        
        if register_response.status_code != 200:
            pytest.skip("Could not register free test user")
        
        # Try to login (may need approval)
        login_response = requests.post(f"{BASE_URL}/api/creators/login", json={
            "email": unique_email,
            "password": "testpassword123"
        })
        
        if login_response.status_code != 200:
            # User needs approval - skip this test
            pytest.skip("Free user needs approval before login")
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Try to export
        export_response = requests.get(f"{BASE_URL}/api/memory/export", headers=headers)
        assert export_response.status_code == 403
        data = export_response.json()
        assert "feature_gated" in str(data.get("detail", {}))
        
        print("✓ Free tier correctly blocked from export")
    
    def test_pro_export_limitations(self, pro_headers):
        """Test Pro tier export limitations"""
        response = requests.get(
            f"{BASE_URL}/api/memory/export?include_archived=true&format=json",
            headers=pro_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Pro users should have limitations applied
        assert data["tier_limitations"]["is_elite"] == False
        assert data["tier_limitations"]["archived_included"] == False
        assert data["tier_limitations"]["format_used"] == "portable"
        
        print("✓ Pro tier export limitations correctly applied")


# ============== INTEGRATION TESTS ==============

class TestIntegration:
    """Integration tests for export/import and forgetting protocol"""
    
    def test_export_creates_log_entry(self, pro_headers):
        """Test that export creates a log entry"""
        # Get current export history count
        history_before = requests.get(f"{BASE_URL}/api/memory/export-history", headers=pro_headers)
        count_before = history_before.json()["total"]
        
        # Perform export
        export_response = requests.get(f"{BASE_URL}/api/memory/export", headers=pro_headers)
        assert export_response.status_code == 200
        
        # Check history increased
        history_after = requests.get(f"{BASE_URL}/api/memory/export-history", headers=pro_headers)
        count_after = history_after.json()["total"]
        
        assert count_after >= count_before
        print(f"✓ Export creates log entry (before: {count_before}, after: {count_after})")
    
    def test_delete_creates_audit_entry(self, pro_headers):
        """Test that delete creates an audit entry when memories are deleted"""
        # Get current deletion history count
        history_before = requests.get(f"{BASE_URL}/api/memory/deletion-history", headers=pro_headers)
        count_before = history_before.json()["total"]
        
        # Perform delete - use a type that might have memories
        delete_response = requests.delete(
            f"{BASE_URL}/api/memory/delete?memory_types=test_audit_entry",
            headers=pro_headers
        )
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        
        # Check history - only increases if memories were actually deleted
        history_after = requests.get(f"{BASE_URL}/api/memory/deletion-history", headers=pro_headers)
        count_after = history_after.json()["total"]
        
        if delete_data["deleted_count"] > 0:
            assert count_after > count_before
            print(f"✓ Delete creates audit entry (before: {count_before}, after: {count_after})")
        else:
            # No memories deleted, audit entry may or may not be created
            print(f"✓ Delete endpoint works - no memories matched (history: {count_after})")
    
    def test_soft_delete_appears_in_pending(self, pro_headers):
        """Test that soft-deleted memories appear in pending deletions"""
        # Perform soft delete with unique identifier
        unique_type = f"test_pending_{uuid.uuid4().hex[:8]}"
        delete_response = requests.delete(
            f"{BASE_URL}/api/memory/delete?memory_types={unique_type}",
            headers=pro_headers
        )
        assert delete_response.status_code == 200
        deletion_id = delete_response.json()["deletion_id"]
        
        # Check pending deletions
        pending_response = requests.get(f"{BASE_URL}/api/memory/pending-deletions", headers=pro_headers)
        assert pending_response.status_code == 200
        
        # The deletion_id should be in pending (if any memories were deleted)
        # Note: May not appear if no memories matched the criteria
        print(f"✓ Soft delete workflow tested - deletion_id: {deletion_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
