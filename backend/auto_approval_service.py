"""
Creators Hive HQ - Auto-Approval Rules Service
Phase 4 Module D - D2: Auto-Approval Rules with ARRIS Evaluation Logic

Features:
- Define criteria for automatic creator approval
- ARRIS AI evaluation of creator applications
- Rule-based scoring system
- Automatic approval workflow
- Audit trail for compliance
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import json
import re

logger = logging.getLogger(__name__)


# ============== DEFAULT APPROVAL RULES ==============

DEFAULT_APPROVAL_RULES = [
    {
        "rule_id": "min_followers",
        "name": "Minimum Follower Count",
        "description": "Require minimum audience size",
        "category": "audience",
        "condition_type": "threshold",
        "field": "follower_count",
        "operator": ">=",
        "value": "1K-10K",
        "score_weight": 20,
        "is_required": False,
        "enabled": True
    },
    {
        "rule_id": "platform_presence",
        "name": "Platform Presence",
        "description": "Creator has at least one recognized platform",
        "category": "platforms",
        "condition_type": "exists",
        "field": "platforms",
        "operator": "not_empty",
        "value": None,
        "score_weight": 15,
        "is_required": True,
        "enabled": True
    },
    {
        "rule_id": "niche_specified",
        "name": "Niche Specified",
        "description": "Creator has specified their content niche",
        "category": "profile",
        "condition_type": "exists",
        "field": "niche",
        "operator": "not_empty",
        "value": None,
        "score_weight": 10,
        "is_required": True,
        "enabled": True
    },
    {
        "rule_id": "goals_clarity",
        "name": "Clear Goals",
        "description": "Creator has described their goals",
        "category": "profile",
        "condition_type": "length",
        "field": "goals",
        "operator": ">=",
        "value": 20,
        "score_weight": 15,
        "is_required": False,
        "enabled": True
    },
    {
        "rule_id": "professional_email",
        "name": "Professional Email",
        "description": "Email appears professional (not disposable)",
        "category": "trust",
        "condition_type": "pattern",
        "field": "email",
        "operator": "not_matches",
        "value": r"(tempmail|throwaway|guerrilla|10minute|mailinator)",
        "score_weight": 10,
        "is_required": True,
        "enabled": True
    },
    {
        "rule_id": "arris_response_quality",
        "name": "Quality ARRIS Response",
        "description": "Meaningful response to ARRIS intake question",
        "category": "engagement",
        "condition_type": "length",
        "field": "arris_response",
        "operator": ">=",
        "value": 50,
        "score_weight": 20,
        "is_required": False,
        "enabled": True
    },
    {
        "rule_id": "website_provided",
        "name": "Website/Portfolio Provided",
        "description": "Creator has provided a website or portfolio link",
        "category": "credibility",
        "condition_type": "exists",
        "field": "website",
        "operator": "not_empty",
        "value": None,
        "score_weight": 10,
        "is_required": False,
        "enabled": True
    }
]

# Follower count score mapping
FOLLOWER_SCORE_MAP = {
    "0-1K": 5,
    "1K-10K": 15,
    "10K-50K": 25,
    "50K-100K": 35,
    "100K-500K": 45,
    "500K-1M": 55,
    "1M+": 65
}

# Platform score mapping (more platforms = higher credibility)
PLATFORM_SCORE_MAP = {
    1: 10,
    2: 18,
    3: 25,
    4: 30,
    5: 35
}


class AutoApprovalService:
    """
    Auto-Approval Rules Service with ARRIS Evaluation Logic.
    
    Features:
    - Rule-based creator evaluation
    - Scoring system with configurable weights
    - ARRIS AI assessment for edge cases
    - Automatic approval workflow
    - Admin rule management
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_client=None):
        self.db = db
        self.llm_client = llm_client
        self.approval_threshold = 70  # Default: 70% score to auto-approve
        
    async def initialize(self):
        """Initialize default rules if not present"""
        existing_rules = await self.db.auto_approval_rules.count_documents({})
        if existing_rules == 0:
            for rule in DEFAULT_APPROVAL_RULES:
                rule["id"] = f"RULE-{uuid.uuid4().hex[:8]}"
                rule["created_at"] = datetime.now(timezone.utc).isoformat()
                rule["updated_at"] = datetime.now(timezone.utc).isoformat()
                await self.db.auto_approval_rules.insert_one(rule)
            logger.info(f"Initialized {len(DEFAULT_APPROVAL_RULES)} default auto-approval rules")
    
    async def get_approval_config(self) -> Dict[str, Any]:
        """Get current auto-approval configuration"""
        config = await self.db.auto_approval_config.find_one(
            {"config_type": "approval"},
            {"_id": 0}
        )
        
        if not config:
            # Create default config
            config = {
                "config_type": "approval",
                "enabled": True,
                "approval_threshold": 70,
                "require_arris_review": True,
                "arris_override_enabled": True,
                "auto_reject_enabled": False,
                "auto_reject_threshold": 30,
                "notify_admin_on_auto_approve": True,
                "notify_admin_on_edge_case": True,
                "edge_case_range": [50, 70],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.auto_approval_config.insert_one(config)
        
        return config
    
    async def update_approval_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update auto-approval configuration"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.db.auto_approval_config.update_one(
            {"config_type": "approval"},
            {"$set": updates},
            upsert=True
        )
        
        return await self.get_approval_config()
    
    async def get_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get all auto-approval rules"""
        query = {}
        if enabled_only:
            query["enabled"] = True
        
        rules = await self.db.auto_approval_rules.find(
            query,
            {"_id": 0}
        ).sort("score_weight", -1).to_list(100)
        
        return rules
    
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule by ID"""
        return await self.db.auto_approval_rules.find_one(
            {"id": rule_id},
            {"_id": 0}
        )
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new approval rule"""
        rule = {
            "id": f"RULE-{uuid.uuid4().hex[:8]}",
            "rule_id": rule_data.get("rule_id", f"custom_{uuid.uuid4().hex[:6]}"),
            "name": rule_data["name"],
            "description": rule_data.get("description", ""),
            "category": rule_data.get("category", "custom"),
            "condition_type": rule_data["condition_type"],
            "field": rule_data["field"],
            "operator": rule_data["operator"],
            "value": rule_data.get("value"),
            "score_weight": rule_data.get("score_weight", 10),
            "is_required": rule_data.get("is_required", False),
            "enabled": rule_data.get("enabled", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.auto_approval_rules.insert_one(rule)
        return rule
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing rule"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Don't allow updating system fields
        updates.pop("id", None)
        updates.pop("created_at", None)
        
        result = await self.db.auto_approval_rules.update_one(
            {"id": rule_id},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_rule(rule_id)
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        result = await self.db.auto_approval_rules.delete_one({"id": rule_id})
        return result.deleted_count > 0
    
    async def evaluate_creator(
        self,
        creator_data: Dict[str, Any],
        include_arris_assessment: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a creator application against all enabled rules.
        
        Args:
            creator_data: The creator's registration data
            include_arris_assessment: Whether to include ARRIS AI assessment
        
        Returns:
            Evaluation result with score, rule results, and recommendation
        """
        evaluation_start = datetime.now(timezone.utc)
        evaluation_id = f"EVAL-{uuid.uuid4().hex[:10]}"
        
        # Get enabled rules
        rules = await self.get_rules(enabled_only=True)
        
        # Get configuration
        config = await self.get_approval_config()
        
        # Evaluate each rule
        rule_results = []
        total_weight = 0
        earned_score = 0
        required_passed = True
        
        for rule in rules:
            result = self._evaluate_rule(rule, creator_data)
            rule_results.append(result)
            
            total_weight += rule["score_weight"]
            if result["passed"]:
                earned_score += rule["score_weight"]
            
            # Check required rules
            if rule["is_required"] and not result["passed"]:
                required_passed = False
        
        # Calculate percentage score
        percentage_score = (earned_score / max(total_weight, 1)) * 100
        
        # Add bonus points for exceptional applications
        bonus_score = self._calculate_bonus_score(creator_data)
        final_score = min(100, percentage_score + bonus_score)
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            final_score,
            required_passed,
            config
        )
        
        # Get ARRIS AI assessment for edge cases or when requested
        arris_assessment = None
        if include_arris_assessment and config.get("require_arris_review"):
            is_edge_case = config["edge_case_range"][0] <= final_score <= config["edge_case_range"][1]
            if is_edge_case or recommendation == "manual_review":
                arris_assessment = await self._get_arris_assessment(
                    creator_data,
                    final_score,
                    rule_results
                )
                
                # ARRIS can override recommendation in edge cases
                if arris_assessment and config.get("arris_override_enabled"):
                    if arris_assessment.get("override_recommendation"):
                        recommendation = arris_assessment["override_recommendation"]
        
        evaluation_result = {
            "evaluation_id": evaluation_id,
            "creator_id": creator_data.get("id"),
            "creator_name": creator_data.get("name"),
            "creator_email": creator_data.get("email"),
            "score": round(final_score, 1),
            "base_score": round(percentage_score, 1),
            "bonus_score": round(bonus_score, 1),
            "earned_points": earned_score,
            "total_points": total_weight,
            "required_rules_passed": required_passed,
            "recommendation": recommendation,
            "rule_results": rule_results,
            "arris_assessment": arris_assessment,
            "thresholds": {
                "approval": config.get("approval_threshold", 70),
                "rejection": config.get("auto_reject_threshold", 30),
                "edge_case": config.get("edge_case_range", [50, 70])
            },
            "evaluated_at": evaluation_start.isoformat(),
            "evaluation_time_ms": (datetime.now(timezone.utc) - evaluation_start).total_seconds() * 1000
        }
        
        # Log evaluation
        await self.db.creator_evaluations.insert_one({
            **evaluation_result,
            "config_snapshot": config
        })
        
        return evaluation_result
    
    def _evaluate_rule(self, rule: Dict, creator_data: Dict) -> Dict[str, Any]:
        """Evaluate a single rule against creator data"""
        field = rule["field"]
        operator = rule["operator"]
        expected_value = rule["value"]
        condition_type = rule["condition_type"]
        
        # Get field value from creator data
        actual_value = creator_data.get(field)
        
        passed = False
        reason = ""
        
        try:
            if condition_type == "exists":
                if operator == "not_empty":
                    if isinstance(actual_value, list):
                        passed = len(actual_value) > 0
                    elif isinstance(actual_value, str):
                        passed = len(actual_value.strip()) > 0
                    else:
                        passed = actual_value is not None
                    reason = f"Field '{field}' is {'present' if passed else 'empty'}"
                elif operator == "empty":
                    passed = actual_value is None or (isinstance(actual_value, (str, list)) and len(actual_value) == 0)
                    reason = f"Field '{field}' is {'empty' if passed else 'present'}"
            
            elif condition_type == "threshold":
                if field == "follower_count":
                    # Special handling for follower count ranges
                    actual_score = FOLLOWER_SCORE_MAP.get(actual_value, 0)
                    threshold_score = FOLLOWER_SCORE_MAP.get(expected_value, 0)
                    passed = actual_score >= threshold_score
                    reason = f"Follower count '{actual_value}' {'meets' if passed else 'below'} threshold '{expected_value}'"
                else:
                    # Numeric comparison
                    if actual_value is not None:
                        if operator == ">=":
                            passed = float(actual_value) >= float(expected_value)
                        elif operator == ">":
                            passed = float(actual_value) > float(expected_value)
                        elif operator == "<=":
                            passed = float(actual_value) <= float(expected_value)
                        elif operator == "<":
                            passed = float(actual_value) < float(expected_value)
                        elif operator == "==":
                            passed = float(actual_value) == float(expected_value)
                    reason = f"Value {actual_value} {operator} {expected_value} = {passed}"
            
            elif condition_type == "length":
                if actual_value is not None:
                    actual_length = len(str(actual_value))
                    if operator == ">=":
                        passed = actual_length >= int(expected_value)
                    elif operator == ">":
                        passed = actual_length > int(expected_value)
                    elif operator == "<=":
                        passed = actual_length <= int(expected_value)
                    elif operator == "<":
                        passed = actual_length < int(expected_value)
                    reason = f"Length {actual_length} {operator} {expected_value} = {passed}"
                else:
                    passed = False
                    reason = f"Field '{field}' is empty"
            
            elif condition_type == "pattern":
                if actual_value is not None:
                    if operator == "matches":
                        passed = bool(re.search(expected_value, str(actual_value), re.IGNORECASE))
                    elif operator == "not_matches":
                        passed = not bool(re.search(expected_value, str(actual_value), re.IGNORECASE))
                    reason = f"Pattern {'matched' if (operator == 'matches') == passed else 'not matched'}"
                else:
                    passed = operator == "not_matches"
                    reason = f"Field '{field}' is empty"
            
            elif condition_type == "contains":
                if actual_value is not None:
                    if isinstance(actual_value, list):
                        passed = expected_value in actual_value
                    else:
                        passed = expected_value in str(actual_value)
                    reason = f"Value {'contains' if passed else 'does not contain'} '{expected_value}'"
                else:
                    passed = False
                    reason = f"Field '{field}' is empty"
            
            elif condition_type == "in_list":
                if actual_value is not None:
                    allowed_values = expected_value if isinstance(expected_value, list) else [expected_value]
                    passed = actual_value in allowed_values
                    reason = f"Value '{actual_value}' {'in' if passed else 'not in'} allowed list"
                else:
                    passed = False
                    reason = f"Field '{field}' is empty"
        
        except Exception as e:
            passed = False
            reason = f"Evaluation error: {str(e)}"
        
        return {
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "category": rule["category"],
            "field": field,
            "passed": passed,
            "reason": reason,
            "is_required": rule["is_required"],
            "score_weight": rule["score_weight"],
            "points_earned": rule["score_weight"] if passed else 0
        }
    
    def _calculate_bonus_score(self, creator_data: Dict) -> float:
        """Calculate bonus points for exceptional applications"""
        bonus = 0.0
        
        # Bonus for multiple platforms
        platforms = creator_data.get("platforms", [])
        if len(platforms) >= 3:
            bonus += 5
        if len(platforms) >= 5:
            bonus += 5
        
        # Bonus for high follower count
        follower_count = creator_data.get("follower_count", "0-1K")
        if follower_count in ["100K-500K", "500K-1M", "1M+"]:
            bonus += 10
        
        # Bonus for complete profile
        fields_filled = sum(1 for f in ["bio", "website", "goals", "arris_response"] 
                          if creator_data.get(f) and len(str(creator_data.get(f))) > 10)
        if fields_filled >= 3:
            bonus += 5
        
        # Bonus for detailed ARRIS response
        arris_response = creator_data.get("arris_response", "")
        if len(arris_response) >= 200:
            bonus += 5
        
        return bonus
    
    def _determine_recommendation(
        self,
        score: float,
        required_passed: bool,
        config: Dict
    ) -> str:
        """Determine approval recommendation based on score and rules"""
        approval_threshold = config.get("approval_threshold", 70)
        rejection_threshold = config.get("auto_reject_threshold", 30)
        auto_reject_enabled = config.get("auto_reject_enabled", False)
        
        # Required rules must pass
        if not required_passed:
            return "reject" if auto_reject_enabled else "manual_review"
        
        # Score-based recommendation
        if score >= approval_threshold:
            return "auto_approve"
        elif auto_reject_enabled and score < rejection_threshold:
            return "auto_reject"
        else:
            return "manual_review"
    
    async def _get_arris_assessment(
        self,
        creator_data: Dict,
        score: float,
        rule_results: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """Get ARRIS AI assessment for edge cases"""
        if not self.llm_client:
            return None
        
        try:
            # Build context for ARRIS
            failed_rules = [r for r in rule_results if not r["passed"]]
            passed_rules = [r for r in rule_results if r["passed"]]
            
            prompt = f"""Evaluate this creator application for Creators Hive HQ:

**Creator Profile:**
- Name: {creator_data.get('name', 'Unknown')}
- Email: {creator_data.get('email', 'Not provided')}
- Platforms: {', '.join(creator_data.get('platforms', [])) or 'None specified'}
- Niche: {creator_data.get('niche', 'Not specified')}
- Follower Count: {creator_data.get('follower_count', 'Not specified')}
- Goals: {creator_data.get('goals', 'Not provided')[:200] if creator_data.get('goals') else 'Not provided'}
- ARRIS Response: {creator_data.get('arris_response', 'Not provided')[:300] if creator_data.get('arris_response') else 'Not provided'}
- Website: {creator_data.get('website', 'Not provided')}

**Current Score:** {score:.1f}/100

**Passed Rules:** {', '.join([r['rule_name'] for r in passed_rules]) or 'None'}
**Failed Rules:** {', '.join([r['rule_name'] for r in failed_rules]) or 'None'}

As ARRIS, provide a brief assessment (max 100 words) covering:
1. Quality of the application
2. Potential as a creator
3. Any red flags or concerns
4. Recommendation: APPROVE, REJECT, or NEEDS_REVIEW

Format your response as:
ASSESSMENT: [Your assessment]
RECOMMENDATION: [APPROVE/REJECT/NEEDS_REVIEW]
CONFIDENCE: [HIGH/MEDIUM/LOW]"""

            response = await self.llm_client.chat(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are ARRIS, an AI assistant evaluating creator applications. Be concise and objective. Focus on quality signals and potential."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            response_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse response
            assessment = ""
            recommendation = "NEEDS_REVIEW"
            confidence = "MEDIUM"
            
            for line in response_text.split("\n"):
                if line.startswith("ASSESSMENT:"):
                    assessment = line.replace("ASSESSMENT:", "").strip()
                elif line.startswith("RECOMMENDATION:"):
                    rec = line.replace("RECOMMENDATION:", "").strip().upper()
                    if rec in ["APPROVE", "REJECT", "NEEDS_REVIEW"]:
                        recommendation = rec
                elif line.startswith("CONFIDENCE:"):
                    conf = line.replace("CONFIDENCE:", "").strip().upper()
                    if conf in ["HIGH", "MEDIUM", "LOW"]:
                        confidence = conf
            
            # Map recommendation to system values
            override_map = {
                "APPROVE": "auto_approve",
                "REJECT": "auto_reject",
                "NEEDS_REVIEW": "manual_review"
            }
            
            return {
                "assessment": assessment or response_text[:300],
                "recommendation": recommendation,
                "override_recommendation": override_map.get(recommendation, "manual_review") if confidence == "HIGH" else None,
                "confidence": confidence,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"ARRIS assessment error: {e}")
            return None
    
    async def process_registration(
        self,
        creator_id: str,
        auto_execute: bool = True
    ) -> Dict[str, Any]:
        """
        Process a creator registration through auto-approval.
        
        Args:
            creator_id: The creator's ID
            auto_execute: If True, automatically approve/reject based on result
        
        Returns:
            Processing result with evaluation and action taken
        """
        # Get creator data
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0}
        )
        
        if not creator:
            return {"error": "Creator not found"}
        
        # Check if already processed
        if creator.get("status") not in ["pending", None]:
            return {
                "error": "Creator already processed",
                "current_status": creator.get("status")
            }
        
        # Get config
        config = await self.get_approval_config()
        
        if not config.get("enabled"):
            return {
                "skipped": True,
                "reason": "Auto-approval is disabled",
                "recommendation": "manual_review"
            }
        
        # Evaluate creator
        evaluation = await self.evaluate_creator(creator)
        
        action_taken = None
        new_status = None
        
        if auto_execute:
            if evaluation["recommendation"] == "auto_approve":
                # Auto-approve the creator
                action_taken = await self._execute_approval(creator_id, evaluation)
                new_status = "approved"
                
            elif evaluation["recommendation"] == "auto_reject" and config.get("auto_reject_enabled"):
                # Auto-reject the creator
                action_taken = await self._execute_rejection(creator_id, evaluation)
                new_status = "rejected"
                
            else:
                # Mark for manual review
                action_taken = await self._mark_for_review(creator_id, evaluation)
                new_status = "pending_review"
        
        # Notify admin if configured
        if config.get("notify_admin_on_auto_approve") and new_status == "approved":
            await self._notify_admin(creator, evaluation, "auto_approved")
        elif config.get("notify_admin_on_edge_case") and evaluation["recommendation"] == "manual_review":
            await self._notify_admin(creator, evaluation, "needs_review")
        
        return {
            "creator_id": creator_id,
            "evaluation": evaluation,
            "auto_executed": auto_execute,
            "action_taken": action_taken,
            "new_status": new_status
        }
    
    async def _execute_approval(self, creator_id: str, evaluation: Dict) -> Dict:
        """Execute automatic approval"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Get creator data
        creator = await self.db.creators.find_one({"id": creator_id})
        
        # Create user account
        new_user_id = f"U-{uuid.uuid4().hex[:8]}"
        new_user = {
            "id": new_user_id,
            "user_id": new_user_id,
            "name": creator["name"],
            "email": creator["email"],
            "role": "Creator",
            "business_type": creator.get("niche", ""),
            "tier": "Free",  # Start with free tier
            "account_status": "Active",
            "created_at": now,
            "updated_at": now
        }
        await self.db.users.insert_one(new_user)
        
        # Update creator status
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "status": "approved",
                "assigned_user_id": new_user_id,
                "approved_at": now,
                "approved_by": "auto_approval_system",
                "approval_evaluation_id": evaluation["evaluation_id"],
                "approval_score": evaluation["score"]
            }}
        )
        
        # Log the action
        await self.db.auto_approval_log.insert_one({
            "id": f"APPROVAL-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "user_id": new_user_id,
            "action": "auto_approve",
            "score": evaluation["score"],
            "evaluation_id": evaluation["evaluation_id"],
            "executed_at": now
        })
        
        return {
            "action": "approved",
            "user_id": new_user_id,
            "executed_at": now
        }
    
    async def _execute_rejection(self, creator_id: str, evaluation: Dict) -> Dict:
        """Execute automatic rejection"""
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "status": "rejected",
                "rejected_at": now,
                "rejected_by": "auto_approval_system",
                "rejection_reason": "Did not meet minimum requirements",
                "approval_evaluation_id": evaluation["evaluation_id"],
                "approval_score": evaluation["score"]
            }}
        )
        
        await self.db.auto_approval_log.insert_one({
            "id": f"REJECTION-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "action": "auto_reject",
            "score": evaluation["score"],
            "evaluation_id": evaluation["evaluation_id"],
            "executed_at": now
        })
        
        return {
            "action": "rejected",
            "executed_at": now
        }
    
    async def _mark_for_review(self, creator_id: str, evaluation: Dict) -> Dict:
        """Mark creator for manual review"""
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "status": "pending_review",
                "review_requested_at": now,
                "approval_evaluation_id": evaluation["evaluation_id"],
                "approval_score": evaluation["score"],
                "needs_manual_review": True
            }}
        )
        
        await self.db.auto_approval_log.insert_one({
            "id": f"REVIEW-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "action": "marked_for_review",
            "score": evaluation["score"],
            "evaluation_id": evaluation["evaluation_id"],
            "reason": "Edge case or failed required rules",
            "executed_at": now
        })
        
        return {
            "action": "marked_for_review",
            "executed_at": now
        }
    
    async def _notify_admin(self, creator: Dict, evaluation: Dict, notification_type: str):
        """Notify admin about auto-approval action"""
        notification = {
            "id": f"NOTIF-{uuid.uuid4().hex[:8]}",
            "type": f"auto_approval_{notification_type}",
            "title": f"Auto-Approval: {creator.get('name', 'Unknown')}",
            "message": f"Creator {creator.get('name')} was {notification_type}. Score: {evaluation['score']:.1f}/100",
            "creator_id": creator.get("id"),
            "evaluation_id": evaluation["evaluation_id"],
            "score": evaluation["score"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False
        }
        
        await self.db.admin_notifications.insert_one(notification)
    
    async def get_evaluation_history(
        self,
        creator_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get evaluation history"""
        query = {}
        if creator_id:
            query["creator_id"] = creator_id
        
        history = await self.db.creator_evaluations.find(
            query,
            {"_id": 0}
        ).sort("evaluated_at", -1).to_list(limit)
        
        return history
    
    async def get_approval_analytics(self) -> Dict[str, Any]:
        """Get auto-approval analytics"""
        # Total evaluations
        total = await self.db.creator_evaluations.count_documents({})
        
        # By recommendation
        rec_pipeline = [
            {"$group": {"_id": "$recommendation", "count": {"$sum": 1}}}
        ]
        by_recommendation = await self.db.creator_evaluations.aggregate(rec_pipeline).to_list(10)
        
        # Average score
        score_pipeline = [
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ]
        avg_result = await self.db.creator_evaluations.aggregate(score_pipeline).to_list(1)
        avg_score = avg_result[0]["avg_score"] if avg_result else 0
        
        # Auto-approval log stats
        approved_count = await self.db.auto_approval_log.count_documents({"action": "auto_approve"})
        rejected_count = await self.db.auto_approval_log.count_documents({"action": "auto_reject"})
        review_count = await self.db.auto_approval_log.count_documents({"action": "marked_for_review"})
        
        # Most failed rules
        failed_pipeline = [
            {"$unwind": "$rule_results"},
            {"$match": {"rule_results.passed": False}},
            {"$group": {"_id": "$rule_results.rule_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        most_failed = await self.db.creator_evaluations.aggregate(failed_pipeline).to_list(5)
        
        return {
            "total_evaluations": total,
            "average_score": round(avg_score, 1),
            "by_recommendation": {r["_id"]: r["count"] for r in by_recommendation},
            "actions_taken": {
                "auto_approved": approved_count,
                "auto_rejected": rejected_count,
                "marked_for_review": review_count
            },
            "most_failed_rules": [{"rule": r["_id"], "failures": r["count"]} for r in most_failed],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }


# Global instance
auto_approval_service = None
