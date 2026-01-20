"""
Elite Tier Service - Custom ARRIS Workflows, Brand Integrations, Adaptive Intelligence
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from models_elite import (
    CustomArrisWorkflow, WorkflowFocusArea, ArrisWorkflowConfig,
    BrandIntegration, BrandPartnershipStatus,
    EliteDashboardConfig, DashboardWidget, DashboardWidgetType,
    AdaptiveIntelligenceProfile, CreatorPattern
)

logger = logging.getLogger(__name__)


class EliteService:
    """Service for Elite tier features"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    # ============== CUSTOM ARRIS WORKFLOWS ==============
    
    async def create_workflow(self, creator_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new custom ARRIS workflow"""
        workflow = {
            "id": f"WF-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "name": workflow_data.get("name"),
            "description": workflow_data.get("description"),
            "trigger": workflow_data.get("trigger", "manual"),
            "config": workflow_data.get("config", {}),
            "is_default": workflow_data.get("is_default", False),
            "is_active": True,
            "usage_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If this is set as default, unset others
        if workflow["is_default"]:
            await self.db.arris_workflows.update_many(
                {"creator_id": creator_id, "is_default": True},
                {"$set": {"is_default": False}}
            )
        
        await self.db.arris_workflows.insert_one(workflow)
        logger.info(f"Created custom ARRIS workflow: {workflow['id']} for creator {creator_id}")
        
        return {k: v for k, v in workflow.items() if k != "_id"}
    
    async def get_workflows(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a creator"""
        workflows = await self.db.arris_workflows.find(
            {"creator_id": creator_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return workflows
    
    async def get_workflow(self, creator_id: str, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow"""
        return await self.db.arris_workflows.find_one(
            {"id": workflow_id, "creator_id": creator_id},
            {"_id": 0}
        )
    
    async def update_workflow(self, creator_id: str, workflow_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a workflow"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Handle default flag
        if updates.get("is_default"):
            await self.db.arris_workflows.update_many(
                {"creator_id": creator_id, "is_default": True},
                {"$set": {"is_default": False}}
            )
        
        result = await self.db.arris_workflows.find_one_and_update(
            {"id": workflow_id, "creator_id": creator_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def delete_workflow(self, creator_id: str, workflow_id: str) -> bool:
        """Delete a workflow"""
        result = await self.db.arris_workflows.delete_one(
            {"id": workflow_id, "creator_id": creator_id}
        )
        return result.deleted_count > 0
    
    async def run_workflow(self, creator_id: str, workflow_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Run a custom workflow on a proposal"""
        from arris_service import arris_service
        
        workflow = await self.get_workflow(creator_id, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Get adaptive profile for personalization
        adaptive_profile = await self.get_adaptive_profile(creator_id)
        
        # Build custom context from workflow config
        config = workflow.get("config", {})
        custom_context = self._build_workflow_context(config, adaptive_profile)
        
        # Run ARRIS with custom workflow
        insights = await arris_service.generate_project_insights(
            proposal,
            memory_palace_data=custom_context.get("memory_data"),
            processing_speed="fast"  # Elite always gets fast
        )
        
        # Enhance with workflow-specific analysis
        workflow_insights = await self._enhance_with_workflow(insights, config, proposal)
        
        # Increment usage count
        await self.db.arris_workflows.update_one(
            {"id": workflow_id},
            {"$inc": {"usage_count": 1}}
        )
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name"),
            "base_insights": insights,
            "workflow_enhancements": workflow_insights,
            "focus_areas": config.get("focus_areas", []),
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _build_workflow_context(self, config: Dict[str, Any], adaptive_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for workflow execution"""
        context = {
            "focus_areas": config.get("focus_areas", []),
            "analysis_depth": config.get("analysis_depth", "detailed"),
            "include_benchmarks": config.get("include_benchmarks", True),
            "custom_metrics": config.get("custom_metrics", [])
        }
        
        if adaptive_profile and config.get("include_historical_context", True):
            context["memory_data"] = {
                "success_patterns": adaptive_profile.get("success_patterns", []),
                "preferred_platforms": adaptive_profile.get("preferred_platforms", []),
                "complexity_comfort": adaptive_profile.get("complexity_comfort_level", "medium")
            }
        
        return context
    
    async def _enhance_with_workflow(self, base_insights: Dict[str, Any], config: Dict[str, Any], proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Add workflow-specific enhancements to insights"""
        enhancements = {}
        focus_areas = config.get("focus_areas", [])
        
        # Add focus-area specific insights
        if "growth_strategy" in focus_areas:
            enhancements["growth_strategy"] = {
                "recommendation": "Focus on consistent content scheduling and audience engagement",
                "key_metrics": ["subscriber_growth", "engagement_rate", "reach"],
                "priority": "high"
            }
        
        if "monetization" in focus_areas:
            enhancements["monetization"] = {
                "recommendation": "Diversify revenue streams across sponsorships and merchandise",
                "potential_revenue": self._estimate_monetization(proposal),
                "priority": "high"
            }
        
        if "brand_partnerships" in focus_areas:
            enhancements["brand_partnerships"] = {
                "recommendation": "Target brands aligned with your niche and audience demographics",
                "suggested_brands": ["Based on your content focus"],
                "outreach_timing": "optimal"
            }
        
        if "risk_assessment" in focus_areas:
            enhancements["risk_assessment"] = {
                "identified_risks": base_insights.get("risks", []),
                "mitigation_strategies": ["Regular progress reviews", "Buffer time allocation"],
                "risk_level": "moderate"
            }
        
        return enhancements
    
    def _estimate_monetization(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate monetization potential"""
        platforms = proposal.get("platforms", [])
        base_value = 1000
        
        platform_multipliers = {
            "YouTube": 2.5,
            "TikTok": 1.8,
            "Instagram": 2.0,
            "Twitter": 1.2,
            "LinkedIn": 1.5
        }
        
        multiplier = sum(platform_multipliers.get(p, 1.0) for p in platforms) / max(len(platforms), 1)
        estimated = base_value * multiplier
        
        return {
            "estimated_monthly": round(estimated, 2),
            "estimated_annual": round(estimated * 12, 2),
            "confidence": "medium"
        }
    
    # ============== BRAND INTEGRATIONS ==============
    
    async def create_brand_integration(self, creator_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand integration/partnership"""
        integration = {
            "id": f"BRAND-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "brand_name": data.get("brand_name"),
            "brand_logo_url": data.get("brand_logo_url"),
            "contact_name": data.get("contact_name"),
            "contact_email": data.get("contact_email"),
            "deal_type": data.get("deal_type", "sponsorship"),
            "status": data.get("status", "prospecting"),
            "deal_value": data.get("deal_value", 0),
            "currency": data.get("currency", "USD"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "platforms": data.get("platforms", []),
            "deliverables": data.get("deliverables", []),
            "notes": data.get("notes"),
            "arris_recommendation_score": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Generate ARRIS recommendation score
        integration["arris_recommendation_score"] = await self._calculate_brand_fit_score(creator_id, integration)
        
        await self.db.brand_integrations.insert_one(integration)
        logger.info(f"Created brand integration: {integration['id']} for creator {creator_id}")
        
        return {k: v for k, v in integration.items() if k != "_id"}
    
    async def get_brand_integrations(self, creator_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all brand integrations for a creator"""
        query = {"creator_id": creator_id}
        if status:
            query["status"] = status
        
        integrations = await self.db.brand_integrations.find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return integrations
    
    async def get_brand_integration(self, creator_id: str, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific brand integration"""
        return await self.db.brand_integrations.find_one(
            {"id": integration_id, "creator_id": creator_id},
            {"_id": 0}
        )
    
    async def update_brand_integration(self, creator_id: str, integration_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a brand integration"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.db.brand_integrations.find_one_and_update(
            {"id": integration_id, "creator_id": creator_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def delete_brand_integration(self, creator_id: str, integration_id: str) -> bool:
        """Delete a brand integration"""
        result = await self.db.brand_integrations.delete_one(
            {"id": integration_id, "creator_id": creator_id}
        )
        return result.deleted_count > 0
    
    async def get_brand_analytics(self, creator_id: str) -> Dict[str, Any]:
        """Get analytics for brand partnerships"""
        integrations = await self.get_brand_integrations(creator_id)
        
        # Calculate pipeline metrics
        pipeline_value = sum(
            i.get("deal_value", 0) 
            for i in integrations 
            if i.get("status") in ["prospecting", "outreach", "negotiating"]
        )
        
        active_value = sum(
            i.get("deal_value", 0) 
            for i in integrations 
            if i.get("status") == "active"
        )
        
        completed_value = sum(
            i.get("deal_value", 0) 
            for i in integrations 
            if i.get("status") == "completed"
        )
        
        # Status breakdown
        status_counts = {}
        for i in integrations:
            status = i.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Deal type breakdown
        deal_types = {}
        for i in integrations:
            dt = i.get("deal_type", "unknown")
            deal_types[dt] = deal_types.get(dt, 0) + 1
        
        return {
            "total_brands": len(integrations),
            "active_partnerships": status_counts.get("active", 0),
            "pipeline": {
                "total_value": pipeline_value,
                "active_value": active_value,
                "completed_value": completed_value,
                "total_lifetime_value": pipeline_value + active_value + completed_value
            },
            "status_breakdown": [
                {"status": k, "count": v} 
                for k, v in sorted(status_counts.items(), key=lambda x: -x[1])
            ],
            "deal_types": [
                {"type": k, "count": v} 
                for k, v in sorted(deal_types.items(), key=lambda x: -x[1])
            ],
            "avg_deal_value": round(
                sum(i.get("deal_value", 0) for i in integrations) / max(len(integrations), 1), 2
            )
        }
    
    async def _calculate_brand_fit_score(self, creator_id: str, integration: Dict[str, Any]) -> float:
        """Calculate how well a brand fits the creator's profile"""
        # Get creator's proposals to understand their niche
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0, "platforms": 1, "arris_insights": 1}
        ).to_list(50)
        
        score = 50.0  # Base score
        
        # Platform alignment
        creator_platforms = set()
        for p in proposals:
            creator_platforms.update(p.get("platforms", []))
        
        brand_platforms = set(integration.get("platforms", []))
        if brand_platforms:
            overlap = len(creator_platforms & brand_platforms) / len(brand_platforms)
            score += overlap * 25
        
        # Deal value assessment
        deal_value = integration.get("deal_value", 0)
        if deal_value > 5000:
            score += 15
        elif deal_value > 1000:
            score += 10
        elif deal_value > 0:
            score += 5
        
        # Historical success
        if len(proposals) > 5:
            score += 10
        
        return min(100, round(score, 1))
    
    # ============== ELITE DASHBOARD ==============
    
    async def get_dashboard_config(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get Elite dashboard configuration"""
        config = await self.db.elite_dashboards.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not config:
            # Create default config
            config = await self.create_default_dashboard(creator_id)
        
        return config
    
    async def create_default_dashboard(self, creator_id: str) -> Dict[str, Any]:
        """Create default Elite dashboard with widgets"""
        default_widgets = [
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "metric_card",
                "title": "Total Proposals",
                "position": {"x": 0, "y": 0, "w": 1, "h": 1},
                "config": {"metric": "total_proposals", "icon": "📋"},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "metric_card",
                "title": "Approval Rate",
                "position": {"x": 1, "y": 0, "w": 1, "h": 1},
                "config": {"metric": "approval_rate", "icon": "✅", "format": "percent"},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "metric_card",
                "title": "Brand Deals",
                "position": {"x": 2, "y": 0, "w": 1, "h": 1},
                "config": {"metric": "active_brands", "icon": "🤝"},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "metric_card",
                "title": "Revenue Pipeline",
                "position": {"x": 3, "y": 0, "w": 1, "h": 1},
                "config": {"metric": "pipeline_value", "icon": "💰", "format": "currency"},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "chart_line",
                "title": "Proposal Trends",
                "position": {"x": 0, "y": 1, "w": 2, "h": 2},
                "config": {"data_source": "proposal_trends", "period": "6m"},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "brand_pipeline",
                "title": "Brand Pipeline",
                "position": {"x": 2, "y": 1, "w": 2, "h": 2},
                "config": {"show_value": True, "limit": 5},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "arris_insights",
                "title": "ARRIS Intelligence",
                "position": {"x": 0, "y": 3, "w": 2, "h": 2},
                "config": {"show_predictions": True, "show_patterns": True},
                "is_visible": True
            },
            {
                "id": f"W-{uuid.uuid4().hex[:6]}",
                "widget_type": "activity_feed",
                "title": "Recent Activity",
                "position": {"x": 2, "y": 3, "w": 2, "h": 2},
                "config": {"limit": 10, "show_timestamps": True},
                "is_visible": True
            }
        ]
        
        config = {
            "id": f"DASH-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "name": "Elite Dashboard",
            "widgets": default_widgets,
            "theme": "default",
            "brand_colors": {
                "primary": "#7c3aed",
                "secondary": "#a855f7",
                "accent": "#f59e0b"
            },
            "logo_url": None,
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.elite_dashboards.insert_one(config)
        return {k: v for k, v in config.items() if k != "_id"}
    
    async def update_dashboard_config(self, creator_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update Elite dashboard configuration"""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.db.elite_dashboards.find_one_and_update(
            {"creator_id": creator_id},
            {"$set": updates},
            return_document=True
        )
        
        if result:
            return {k: v for k, v in result.items() if k != "_id"}
        return None
    
    async def get_dashboard_data(self, creator_id: str) -> Dict[str, Any]:
        """Get data for Elite dashboard widgets"""
        # Gather all metrics in parallel-ish manner
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).to_list(1000)
        
        brand_analytics = await self.get_brand_analytics(creator_id)
        adaptive_profile = await self.get_adaptive_profile(creator_id)
        workflows = await self.get_workflows(creator_id)
        
        # Calculate metrics
        total_proposals = len(proposals)
        approved = len([p for p in proposals if p.get("status") in ["approved", "in_progress", "completed"]])
        approval_rate = round((approved / total_proposals * 100), 1) if total_proposals > 0 else 0
        
        # Recent activity
        recent_activity = []
        for p in sorted(proposals, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]:
            recent_activity.append({
                "type": "proposal",
                "title": p.get("title"),
                "status": p.get("status"),
                "timestamp": p.get("updated_at")
            })
        
        return {
            "metrics": {
                "total_proposals": total_proposals,
                "approval_rate": approval_rate,
                "active_brands": brand_analytics.get("active_partnerships", 0),
                "pipeline_value": brand_analytics.get("pipeline", {}).get("total_value", 0),
                "completed_projects": len([p for p in proposals if p.get("status") == "completed"]),
                "custom_workflows": len(workflows)
            },
            "brand_analytics": brand_analytics,
            "adaptive_intelligence": {
                "learning_score": adaptive_profile.get("learning_score", 0) if adaptive_profile else 0,
                "patterns_identified": len(adaptive_profile.get("success_patterns", [])) if adaptive_profile else 0,
                "profile_exists": adaptive_profile is not None
            },
            "recent_activity": recent_activity,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ============== ADAPTIVE INTELLIGENCE ==============
    
    async def get_adaptive_profile(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Get adaptive intelligence profile for a creator"""
        return await self.db.adaptive_profiles.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
    
    async def update_adaptive_profile(self, creator_id: str) -> Dict[str, Any]:
        """Update/build adaptive intelligence profile from creator's history"""
        proposals = await self.db.proposals.find(
            {"user_id": creator_id},
            {"_id": 0}
        ).to_list(500)
        
        if not proposals:
            return {"message": "No proposals to learn from"}
        
        # Analyze patterns
        platform_counts = {}
        complexity_counts = {}
        timeline_values = []
        success_count = 0
        
        for p in proposals:
            # Platform analysis
            for platform in p.get("platforms", []):
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            # Complexity analysis
            complexity = p.get("arris_insights", {}).get("estimated_complexity", "Medium")
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            # Timeline analysis
            if p.get("timeline"):
                timeline_values.append(p["timeline"])
            
            # Success tracking
            if p.get("status") in ["approved", "completed"]:
                success_count += 1
        
        # Build patterns
        success_patterns = []
        if success_count > 3:
            success_patterns.append({
                "pattern_type": "high_approval",
                "pattern_value": f"{round(success_count/len(proposals)*100)}% success rate",
                "confidence": min(0.9, success_count / 10),
                "occurrences": success_count
            })
        
        # Determine complexity comfort
        most_common_complexity = max(complexity_counts.items(), key=lambda x: x[1])[0] if complexity_counts else "Medium"
        
        profile = {
            "id": f"ADAPT-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "preferred_platforms": [
                {"platform": k, "count": v, "percentage": round(v/len(proposals)*100, 1)}
                for k, v in sorted(platform_counts.items(), key=lambda x: -x[1])[:5]
            ],
            "common_project_types": list(set(p.get("priority", "medium") for p in proposals)),
            "typical_timeline_range": {
                "most_common": max(set(timeline_values), key=timeline_values.count) if timeline_values else "2-4 weeks"
            },
            "complexity_comfort_level": most_common_complexity.lower(),
            "success_patterns": success_patterns,
            "risk_patterns": [],
            "communication_style": "detailed" if len(proposals) > 10 else "balanced",
            "focus_areas": list(platform_counts.keys())[:3],
            "total_proposals_analyzed": len(proposals),
            "learning_score": min(100, round(len(proposals) * 5 + success_count * 10, 1)),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert profile
        await self.db.adaptive_profiles.update_one(
            {"creator_id": creator_id},
            {"$set": profile},
            upsert=True
        )
        
        logger.info(f"Updated adaptive profile for creator {creator_id}")
        return profile
    
    async def get_personalized_recommendations(self, creator_id: str) -> Dict[str, Any]:
        """Get personalized recommendations based on adaptive intelligence"""
        profile = await self.get_adaptive_profile(creator_id)
        
        if not profile:
            profile = await self.update_adaptive_profile(creator_id)
        
        recommendations = []
        
        # Platform recommendations
        if profile.get("preferred_platforms"):
            top_platform = profile["preferred_platforms"][0]["platform"]
            recommendations.append({
                "type": "platform_focus",
                "title": f"Double down on {top_platform}",
                "description": f"{top_platform} is your strongest platform. Consider creating more content there.",
                "priority": "high",
                "confidence": 0.85
            })
        
        # Complexity recommendations
        comfort = profile.get("complexity_comfort_level", "medium")
        if comfort == "low":
            recommendations.append({
                "type": "skill_growth",
                "title": "Challenge yourself with medium complexity projects",
                "description": "You've mastered low complexity projects. Time to level up!",
                "priority": "medium",
                "confidence": 0.7
            })
        
        # Success pattern recommendations
        learning_score = profile.get("learning_score", 0)
        if learning_score > 50:
            recommendations.append({
                "type": "momentum",
                "title": "You're building great momentum!",
                "description": f"Your learning score is {learning_score}. Keep up the consistent activity.",
                "priority": "info",
                "confidence": 0.9
            })
        
        return {
            "profile_summary": {
                "learning_score": profile.get("learning_score", 0),
                "total_analyzed": profile.get("total_proposals_analyzed", 0),
                "top_platforms": [p["platform"] for p in profile.get("preferred_platforms", [])[:3]],
                "comfort_level": profile.get("complexity_comfort_level", "medium")
            },
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
