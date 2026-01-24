"""
Seed Test Creators Script
=========================
Creates reliable test creators for each subscription tier.
Run this script to set up test accounts for development and testing.

Usage:
    python seed_test_creators.py

This script is IDEMPOTENT - safe to run multiple times.
Existing users will be updated, not duplicated.

Test Accounts Created:
    - freetest@hivehq.com / testpassword (Free tier)
    - startertest@hivehq.com / testpassword (Starter tier)  
    - protest@hivehq.com / testpassword (Pro tier)
    - premiumtest@hivehq.com / testpassword (Premium tier)
    - elitetest@hivehq.com / testpassword123 (Elite tier)
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment
load_dotenv(Path(__file__).parent / '.env')

# Import password hashing from auth module
from auth import pwd_context

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'creators_hive_hq')


# Test creator definitions - one for each tier
TEST_CREATORS = [
    {
        "id": "CREATOR-TEST-FREE-001",
        "email": "freetest@hivehq.com",
        "password": "testpassword",
        "name": "Free Tier Test Creator",
        "tier": "free",
        "platforms": ["YouTube", "Instagram"],
        "niche": "Tech Reviews",
        "business_description": "Test creator account for Free tier testing",
        "status": "approved"
    },
    {
        "id": "CREATOR-TEST-STARTER-001",
        "email": "startertest@hivehq.com",
        "password": "testpassword",
        "name": "Starter Tier Test Creator",
        "tier": "starter",
        "platforms": ["TikTok", "Instagram"],
        "niche": "Lifestyle",
        "business_description": "Test creator account for Starter tier testing",
        "status": "approved"
    },
    {
        "id": "CREATOR-TEST-PRO-001",
        "email": "protest@hivehq.com",
        "password": "testpassword",
        "name": "Pro Tier Test Creator",
        "tier": "pro",
        "platforms": ["YouTube", "TikTok", "Instagram"],
        "niche": "Gaming",
        "business_description": "Test creator account for Pro tier testing",
        "status": "approved"
    },
    {
        "id": "CREATOR-TEST-PREMIUM-001",
        "email": "premiumtest@hivehq.com",
        "password": "testpassword",
        "name": "Premium Tier Test Creator",
        "tier": "premium",
        "platforms": ["YouTube", "Twitch", "Twitter"],
        "niche": "Entertainment",
        "business_description": "Test creator account for Premium tier testing",
        "status": "approved"
    },
    {
        "id": "CREATOR-TEST-ELITE-001",
        "email": "elitetest@hivehq.com",
        "password": "testpassword123",
        "name": "Elite Tier Test Creator",
        "tier": "elite",
        "platforms": ["YouTube", "Instagram", "TikTok", "Twitter", "LinkedIn"],
        "niche": "Business & Entrepreneurship",
        "business_description": "Test creator account for Elite tier testing with all features",
        "status": "approved"
    }
]

# Subscription plan details for each tier
SUBSCRIPTION_PLANS = {
    "free": {
        "plan_id": "free",
        "plan_name": "Free",
        "monthly_price": 0,
        "billing_cycle": "monthly",
        "features": ["basic_dashboard", "1_proposal_per_month"]
    },
    "starter": {
        "plan_id": "starter_monthly",
        "plan_name": "Starter",
        "monthly_price": 9.99,
        "billing_cycle": "monthly",
        "features": ["basic_dashboard", "3_proposals_per_month", "email_support"]
    },
    "pro": {
        "plan_id": "pro_monthly",
        "plan_name": "Pro",
        "monthly_price": 29.99,
        "billing_cycle": "monthly",
        "features": ["advanced_dashboard", "unlimited_proposals", "priority_support", "arris_full_insights"]
    },
    "premium": {
        "plan_id": "premium_monthly",
        "plan_name": "Premium",
        "monthly_price": 99.99,
        "billing_cycle": "monthly",
        "features": ["advanced_dashboard", "unlimited_proposals", "priority_review", "arris_full_insights", "voice_interaction", "activity_feed", "learning_history"]
    },
    "elite": {
        "plan_id": "elite_monthly",
        "plan_name": "Elite",
        "monthly_price": 199.99,
        "billing_cycle": "monthly",
        "features": ["custom_dashboard", "unlimited_proposals", "priority_review", "arris_full_insights", "voice_interaction", "activity_feed", "learning_history", "api_access", "custom_personas", "multi_brand", "scheduled_reports", "dedicated_support"]
    }
}


def hash_password(password: str) -> str:
    """Hash password using the same method as auth.py"""
    return pwd_context.hash(password)


async def seed_test_creators():
    """
    Create or update test creators for each subscription tier.
    This function is idempotent - safe to run multiple times.
    """
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 60)
    print("SEED TEST CREATORS SCRIPT")
    print("=" * 60)
    print(f"Database: {db_name}")
    print(f"Creating/updating {len(TEST_CREATORS)} test creators...")
    print()
    
    results = {
        "created": [],
        "updated": [],
        "errors": []
    }
    
    now = datetime.now(timezone.utc)
    
    for creator_def in TEST_CREATORS:
        try:
            email = creator_def["email"]
            tier = creator_def["tier"]
            
            # Check if creator already exists
            existing = await db.creators.find_one({"email": email})
            
            # Prepare creator document
            creator_doc = {
                "id": creator_def["id"],
                "email": email,
                "name": creator_def["name"],
                "hashed_password": hash_password(creator_def["password"]),
                "platforms": creator_def["platforms"],
                "niche": creator_def["niche"],
                "business_description": creator_def["business_description"],
                "status": creator_def["status"],
                "assigned_tier": tier.capitalize() if tier != "free" else "Free",
                "submitted_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "arris_intake_response": f"Test account for {tier} tier testing",
                "admin_notes": f"Auto-generated test account for {tier} tier",
                "is_test_account": True
            }
            
            if existing:
                # Update existing creator
                await db.creators.update_one(
                    {"email": email},
                    {"$set": creator_doc}
                )
                results["updated"].append(email)
                print(f"  ✓ Updated: {email} ({tier})")
            else:
                # Create new creator
                creator_doc["created_at"] = now.isoformat()
                await db.creators.insert_one(creator_doc)
                results["created"].append(email)
                print(f"  ✓ Created: {email} ({tier})")
            
            # Create or update subscription
            plan = SUBSCRIPTION_PLANS[tier]
            subscription_doc = {
                "id": f"SUB-TEST-{tier.upper()}-001",
                "creator_id": creator_def["id"],
                "email": email,
                "tier": tier,
                "plan_id": plan["plan_id"],
                "plan_name": plan["plan_name"],
                "monthly_price": plan["monthly_price"],
                "billing_cycle": plan["billing_cycle"],
                "status": "active",
                "features": plan["features"],
                "current_period_start": now.isoformat(),
                "current_period_end": (now + timedelta(days=30)).isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "is_test_subscription": True,
                "stripe_subscription_id": f"sub_test_{tier}",
                "stripe_customer_id": f"cus_test_{tier}"
            }
            
            # Upsert subscription
            await db.creator_subscriptions.update_one(
                {"creator_id": creator_def["id"]},
                {"$set": subscription_doc},
                upsert=True
            )
            
        except Exception as e:
            results["errors"].append(f"{email}: {str(e)}")
            print(f"  ✗ Error: {email} - {str(e)}")
    
    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Created: {len(results['created'])}")
    print(f"Updated: {len(results['updated'])}")
    print(f"Errors:  {len(results['errors'])}")
    print()
    
    if results["errors"]:
        print("ERRORS:")
        for err in results["errors"]:
            print(f"  - {err}")
        print()
    
    print("TEST ACCOUNTS:")
    print("-" * 60)
    print(f"{'Email':<35} {'Password':<20} {'Tier'}")
    print("-" * 60)
    for creator in TEST_CREATORS:
        print(f"{creator['email']:<35} {creator['password']:<20} {creator['tier'].capitalize()}")
    print("-" * 60)
    print()
    print("Login URL: /creator/login")
    print()
    
    # Verify creators can be found
    print("VERIFICATION:")
    for creator in TEST_CREATORS:
        found = await db.creators.find_one({"email": creator["email"]})
        if found:
            # Verify password works
            if pwd_context.verify(creator["password"], found["hashed_password"]):
                print(f"  ✓ {creator['email']} - Password verified")
            else:
                print(f"  ✗ {creator['email']} - Password verification FAILED")
        else:
            print(f"  ✗ {creator['email']} - Creator not found in database")
    
    print()
    print("Seed script completed!")
    
    client.close()
    return results


async def cleanup_test_creators():
    """
    Remove all test creators and their subscriptions.
    Use this to clean up test data.
    """
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Cleaning up test creators...")
    
    # Delete test creators
    result = await db.creators.delete_many({"is_test_account": True})
    print(f"  Deleted {result.deleted_count} test creators")
    
    # Delete test subscriptions
    result = await db.creator_subscriptions.delete_many({"is_test_subscription": True})
    print(f"  Deleted {result.deleted_count} test subscriptions")
    
    print("Cleanup completed!")
    
    client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed test creators for each subscription tier")
    parser.add_argument("--cleanup", action="store_true", help="Remove all test creators instead of creating them")
    args = parser.parse_args()
    
    if args.cleanup:
        asyncio.run(cleanup_test_creators())
    else:
        asyncio.run(seed_test_creators())
