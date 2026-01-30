"""
Creators Hive HQ - Intake Service
=================================
Handles the Intake Form submission and post-form logic.
This is the ignition key - nothing else activates until intake is complete.

POST-FORM LOGIC:
1. Assign user to track (Creator/Business/Hybrid)
2. Activate correct engines based on selections
3. Unlock relevant modules
4. Generate initial dashboard state
5. Initialize ARRIS + Millicent outputs
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging
import uuid

from models_system import (
    IntakeFormSubmission, IntakeFormResponse, IntakeUserIdentity,
    IntakeSystemNeed, IntakeStartingPoint, UserSystemState,
    TrackType, UserIdentityType, UserStage, EngineType, EngineStatus,
    ArrisStructuralOutput, MillicentToneOutput, DashboardState
)
from engine_service import EngineService
from millicent_service import MillicentService

logger = logging.getLogger(__name__)


# ============== MODULE DEFINITIONS ==============

MODULES = {
    # Core modules (all tracks)
    "dashboard": {
        "name": "Command Center Dashboard",
        "purpose": "Central control hub showing active items, next steps, blockers, and AI outputs",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True
    },
    "profile": {
        "name": "Profile & Identity",
        "purpose": "User identity, stage, and goal management",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [],
        "is_core": True
    },
    
    # Business Engine modules
    "business_model_canvas": {
        "name": "Business Model Canvas",
        "purpose": "Define and visualize business model components",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "inputs": ["business_model", "value_proposition"],
        "outputs": ["business_plan"]
    },
    "market_research": {
        "name": "Market Research",
        "purpose": "Analyze target market and competition",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "inputs": ["target_market"],
        "outputs": ["market_analysis"]
    },
    "financial_planning": {
        "name": "Financial Planning",
        "purpose": "Revenue streams, costs, and projections",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS, EngineType.INCOME],
        "inputs": ["revenue_streams", "cost_structure"],
        "outputs": ["financial_projections"]
    },
    "strategy_builder": {
        "name": "Strategy Builder",
        "purpose": "Build growth and execution strategy",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.BUSINESS],
        "inputs": [],
        "outputs": ["growth_strategy"]
    },
    
    # Engagement Engine modules
    "audience_builder": {
        "name": "Audience Builder",
        "purpose": "Define and understand your audience",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "inputs": ["audience_profile"],
        "outputs": ["audience_insights"]
    },
    "content_planner": {
        "name": "Content Planner",
        "purpose": "Plan and organize content strategy",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "inputs": ["content_strategy"],
        "outputs": ["content_calendar"]
    },
    "platform_optimizer": {
        "name": "Platform Optimizer",
        "purpose": "Optimize presence across platforms",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "inputs": ["platform_selection"],
        "outputs": ["engagement_plan"]
    },
    "community_manager": {
        "name": "Community Manager",
        "purpose": "Build and manage community",
        "tracks": [TrackType.CREATOR, TrackType.HYBRID],
        "engines": [EngineType.ENGAGEMENT],
        "inputs": ["engagement_goals"],
        "outputs": ["community_strategy"]
    },
    
    # Role Engine modules
    "role_definer": {
        "name": "Role Definer",
        "purpose": "Define roles and responsibilities",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "inputs": ["role_definition", "responsibilities"],
        "outputs": ["role_clarity"]
    },
    "team_builder": {
        "name": "Team Builder",
        "purpose": "Build team structure and hierarchy",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "inputs": ["skills_required"],
        "outputs": ["team_structure"]
    },
    "delegation_matrix": {
        "name": "Delegation Matrix",
        "purpose": "Define delegation and authority",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "inputs": ["authority_level"],
        "outputs": ["delegation_plan"]
    },
    "accountability_tracker": {
        "name": "Accountability Tracker",
        "purpose": "Track accountability and performance",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.ROLE],
        "inputs": ["accountability_matrix"],
        "outputs": ["performance_criteria"]
    },
    
    # Income Engine modules
    "revenue_tracker": {
        "name": "Revenue Tracker",
        "purpose": "Track and analyze income sources",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "inputs": ["income_sources"],
        "outputs": ["revenue_forecast"]
    },
    "pricing_optimizer": {
        "name": "Pricing Optimizer",
        "purpose": "Optimize pricing strategy",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "inputs": ["pricing_strategy"],
        "outputs": ["pricing_recommendations"]
    },
    "sales_funnel": {
        "name": "Sales Funnel",
        "purpose": "Build and optimize sales pipeline",
        "tracks": [TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "inputs": ["sales_pipeline"],
        "outputs": ["sales_strategy"]
    },
    "financial_dashboard": {
        "name": "Financial Dashboard",
        "purpose": "Financial overview and goals tracking",
        "tracks": [TrackType.CREATOR, TrackType.BUSINESS, TrackType.HYBRID],
        "engines": [EngineType.INCOME],
        "inputs": ["financial_goals"],
        "outputs": ["cash_flow_plan", "income_optimization"]
    }
}


# ============== TRACK ASSIGNMENT LOGIC ==============

def determine_track(identity_type: UserIdentityType) -> TrackType:
    """Determine track based on user identity type"""
    track_map = {
        UserIdentityType.CREATOR: TrackType.CREATOR,
        UserIdentityType.BUSINESS: TrackType.BUSINESS,
        UserIdentityType.HYBRID: TrackType.HYBRID
    }
    return track_map.get(identity_type, TrackType.HYBRID)


def get_selected_engines(system_need: IntakeSystemNeed) -> List[EngineType]:
    """Convert system need selections to engine types"""
    engines = []
    if system_need.business_engine:
        engines.append(EngineType.BUSINESS)
    if system_need.engagement_engine:
        engines.append(EngineType.ENGAGEMENT)
    if system_need.role_engine:
        engines.append(EngineType.ROLE)
    if system_need.income_engine:
        engines.append(EngineType.INCOME)
    return engines


def get_modules_for_track_and_engines(
    track: TrackType,
    selected_engines: List[EngineType]
) -> List[str]:
    """Get modules to unlock based on track and selected engines"""
    unlocked = []
    
    for module_id, module_def in MODULES.items():
        # Core modules always unlocked
        if module_def.get("is_core", False):
            unlocked.append(module_id)
            continue
        
        # Check track compatibility
        if track not in module_def.get("tracks", []):
            continue
        
        # Check engine requirements
        module_engines = module_def.get("engines", [])
        if not module_engines:
            unlocked.append(module_id)
        elif any(engine in selected_engines for engine in module_engines):
            unlocked.append(module_id)
    
    return unlocked


# ============== INTAKE SERVICE ==============

class IntakeService:
    """
    Handles intake form submission and post-form logic.
    This is the ignition key of the system.
    """
    
    def __init__(self, db, engine_service: EngineService, millicent_service: MillicentService, arris_service=None):
        self.db = db
        self.engine_service = engine_service
        self.millicent_service = millicent_service
        self.arris_service = arris_service
    
    async def process_intake(
        self,
        user_id: str,
        intake_data: IntakeFormSubmission
    ) -> IntakeFormResponse:
        """
        Process intake form submission and activate the system.
        
        POST-FORM LOGIC:
        1. Assign user to track
        2. Activate engines
        3. Unlock modules
        4. Generate dashboard
        5. Initialize AI outputs
        """
        
        intake_id = f"INTAKE-{str(uuid.uuid4())[:8]}"
        
        # ===== STEP 1: Assign Track =====
        assigned_track = determine_track(intake_data.user_identity.identity_type)
        logger.info(f"User {user_id} assigned to track: {assigned_track.value}")
        
        # ===== STEP 2: Activate Engines =====
        selected_engines = get_selected_engines(intake_data.system_need)
        
        if not selected_engines:
            # Default engines based on track
            if assigned_track == TrackType.CREATOR:
                selected_engines = [EngineType.ENGAGEMENT, EngineType.INCOME]
            elif assigned_track == TrackType.BUSINESS:
                selected_engines = [EngineType.BUSINESS, EngineType.ROLE, EngineType.INCOME]
            else:
                selected_engines = [EngineType.BUSINESS, EngineType.ENGAGEMENT, EngineType.INCOME]
        
        engine_states = await self.engine_service.initialize_engines_for_user(
            user_id, selected_engines
        )
        logger.info(f"Activated engines for {user_id}: {[e.value for e in selected_engines]}")
        
        # ===== STEP 3: Unlock Modules =====
        unlocked_modules = get_modules_for_track_and_engines(
            assigned_track, selected_engines
        )
        logger.info(f"Unlocked {len(unlocked_modules)} modules for {user_id}")
        
        # ===== STEP 4: Generate Initial Next Steps =====
        next_steps = self._generate_initial_next_steps(
            intake_data.user_identity,
            intake_data.starting_point,
            selected_engines,
            unlocked_modules
        )
        
        # ===== STEP 5: Initialize AI Outputs =====
        
        # Millicent tone guidance (rule-based)
        await self.millicent_service.generate_tone_guidance(
            user_id=user_id,
            context="Initial system setup",
            identity_type=intake_data.user_identity.identity_type,
            stage=intake_data.user_identity.stage
        )
        
        # ARRIS structural recommendations (using existing ARRIS service if available)
        arris_recommendations = await self._generate_arris_recommendations(
            user_id,
            intake_data,
            assigned_track,
            selected_engines
        )
        
        # ===== Store System State =====
        system_state = UserSystemState(
            user_id=user_id,
            intake_completed=True,
            intake_id=intake_id,
            intake_data=intake_data.model_dump(),
            assigned_track=assigned_track,
            identity_type=intake_data.user_identity.identity_type,
            stage=intake_data.user_identity.stage,
            primary_goal=intake_data.user_identity.primary_goal,
            what_they_have=intake_data.starting_point.what_they_have,
            what_is_missing=intake_data.starting_point.what_is_missing,
            first_accomplishment=intake_data.starting_point.first_accomplishment,
            engines={k: v.model_dump() for k, v in engine_states.items()},
            unlocked_modules=unlocked_modules,
            active_modules=["dashboard", "profile"],
            incomplete_items=self._identify_incomplete_items(intake_data, selected_engines),
            next_steps=next_steps,
            blockers=[],
            arris_recommendations=arris_recommendations,
            millicent_guidance=[
                await self.millicent_service.get_welcome_message(
                    intake_data.user_identity.identity_type,
                    intake_data.user_identity.stage
                )
            ]
        )
        
        await self.db.user_system_states.update_one(
            {"user_id": user_id},
            {"$set": system_state.model_dump()},
            upsert=True
        )
        
        # Store intake record
        await self.db.intake_records.insert_one({
            "intake_id": intake_id,
            "user_id": user_id,
            "intake_data": intake_data.model_dump(),
            "assigned_track": assigned_track.value,
            "activated_engines": [e.value for e in selected_engines],
            "unlocked_modules": unlocked_modules,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Intake completed for user {user_id}: Track={assigned_track.value}, Engines={len(selected_engines)}, Modules={len(unlocked_modules)}")
        
        return IntakeFormResponse(
            intake_id=intake_id,
            user_id=user_id,
            assigned_track=assigned_track,
            activated_engines=selected_engines,
            unlocked_modules=unlocked_modules,
            next_steps=next_steps,
            message=f"System activated. You are on the {assigned_track.value.replace('_', ' ').title()}."
        )
    
    def _generate_initial_next_steps(
        self,
        user_identity: IntakeUserIdentity,
        starting_point: IntakeStartingPoint,
        selected_engines: List[EngineType],
        unlocked_modules: List[str]
    ) -> List[str]:
        """Generate initial next steps based on intake data"""
        
        steps = []
        
        # Based on what they want to accomplish first
        first_goal = starting_point.first_accomplishment.lower()
        
        # Map goal keywords to modules
        if "audience" in first_goal or "engagement" in first_goal:
            steps.append("Start with Audience Builder to define your target audience")
        if "business" in first_goal or "plan" in first_goal:
            steps.append("Begin with Business Model Canvas to structure your business")
        if "income" in first_goal or "revenue" in first_goal or "money" in first_goal:
            steps.append("Set up Revenue Tracker to monitor income sources")
        if "team" in first_goal or "role" in first_goal:
            steps.append("Use Role Definer to clarify responsibilities")
        if "content" in first_goal:
            steps.append("Open Content Planner to organize your content strategy")
        
        # If no specific goal matched, suggest based on engines
        if not steps:
            for engine in selected_engines:
                if engine == EngineType.BUSINESS:
                    steps.append("Complete Business Model Canvas to define your business structure")
                    break
                elif engine == EngineType.ENGAGEMENT:
                    steps.append("Start with Audience Builder to understand your audience")
                    break
                elif engine == EngineType.INCOME:
                    steps.append("Set up Revenue Tracker to organize your income streams")
                    break
                elif engine == EngineType.ROLE:
                    steps.append("Define your role using Role Definer")
                    break
        
        # Add stage-appropriate steps
        if user_identity.stage == UserStage.BEGINNER:
            steps.append("Explore the Dashboard to understand your command center")
        
        # Limit to 5 steps
        return steps[:5]
    
    def _identify_incomplete_items(
        self,
        intake_data: IntakeFormSubmission,
        selected_engines: List[EngineType]
    ) -> List[str]:
        """Identify what's incomplete based on starting point"""
        
        incomplete = []
        missing = intake_data.starting_point.what_is_missing.lower()
        
        # Map missing items to modules
        if "audience" in missing:
            incomplete.append("audience_builder")
        if "content" in missing:
            incomplete.append("content_planner")
        if "business" in missing or "plan" in missing:
            incomplete.append("business_model_canvas")
        if "revenue" in missing or "income" in missing:
            incomplete.append("revenue_tracker")
        if "pricing" in missing:
            incomplete.append("pricing_optimizer")
        if "team" in missing or "role" in missing:
            incomplete.append("role_definer")
        
        return incomplete
    
    async def _generate_arris_recommendations(
        self,
        user_id: str,
        intake_data: IntakeFormSubmission,
        track: TrackType,
        engines: List[EngineType]
    ) -> List[str]:
        """Generate ARRIS structural recommendations (clarity, structure, logic)"""
        
        recommendations = []
        
        # Structure recommendation based on track
        if track == TrackType.CREATOR:
            recommendations.append(
                "STRUCTURE: Focus on audience and content before monetization. "
                "Build engagement foundation first."
            )
        elif track == TrackType.BUSINESS:
            recommendations.append(
                "STRUCTURE: Start with business model clarity, then define roles, "
                "then optimize income streams."
            )
        else:
            recommendations.append(
                "STRUCTURE: Balance creative and business activities. "
                "Alternate between engagement and strategy modules."
            )
        
        # Clarity recommendation based on stage
        if intake_data.user_identity.stage == UserStage.BEGINNER:
            recommendations.append(
                "CLARITY: Complete one module fully before moving to the next. "
                "Avoid spreading focus too thin."
            )
        elif intake_data.user_identity.stage == UserStage.INTERMEDIATE:
            recommendations.append(
                "CLARITY: You can work on 2-3 modules in parallel. "
                "Maintain clear priorities."
            )
        else:
            recommendations.append(
                "CLARITY: Optimize existing systems before adding new ones. "
                "Focus on efficiency gains."
            )
        
        # Logic recommendation based on engines
        engine_order = []
        if EngineType.BUSINESS in engines:
            engine_order.append("Business")
        if EngineType.ENGAGEMENT in engines:
            engine_order.append("Engagement")
        if EngineType.ROLE in engines:
            engine_order.append("Role")
        if EngineType.INCOME in engines:
            engine_order.append("Income")
        
        if engine_order:
            recommendations.append(
                f"LOGIC: Recommended engine sequence: {' → '.join(engine_order)}. "
                "This order respects dependencies and builds logically."
            )
        
        # Store ARRIS outputs
        for rec in recommendations:
            output = ArrisStructuralOutput(
                user_id=user_id,
                output_type="structure" if "STRUCTURE" in rec else "clarity" if "CLARITY" in rec else "logic",
                context="Intake analysis",
                recommendation=rec,
                priority="high"
            )
            await self.db.arris_structural_outputs.insert_one(output.model_dump())
        
        return recommendations
    
    async def get_system_state(self, user_id: str) -> Optional[UserSystemState]:
        """Get current system state for a user"""
        
        record = await self.db.user_system_states.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not record:
            return None
        
        return UserSystemState(**record)
    
    async def is_intake_completed(self, user_id: str) -> bool:
        """Check if user has completed intake"""
        
        state = await self.get_system_state(user_id)
        return state is not None and state.intake_completed
    
    async def recalculate_system_state(self, user_id: str) -> UserSystemState:
        """Recalculate system state based on current data"""
        
        state = await self.get_system_state(user_id)
        if not state:
            raise ValueError(f"No system state found for user {user_id}")
        
        # Recalculate engine states
        engine_states = await self.engine_service.get_all_engine_states(user_id)
        
        # Recalculate blockers
        blockers = []
        for engine_id, engine_state in engine_states.items():
            if engine_state.status == EngineStatus.BLOCKED:
                blockers.extend(engine_state.blockers)
        
        # Update state
        state.engines = {k: v.model_dump() for k, v in engine_states.items()}
        state.blockers = blockers
        state.updated_at = datetime.now(timezone.utc)
        
        await self.db.user_system_states.update_one(
            {"user_id": user_id},
            {"$set": state.model_dump()}
        )
        
        return state
    
    async def get_dashboard_state(self, user_id: str) -> DashboardState:
        """Generate dashboard state for command center view"""
        
        state = await self.get_system_state(user_id)
        if not state:
            return DashboardState(user_id=user_id)
        
        # Get engine states
        engine_states = await self.engine_service.get_all_engine_states(user_id)
        
        # Get recent ARRIS outputs
        arris_outputs = await self.db.arris_structural_outputs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Get recent Millicent outputs
        millicent_outputs = await self.db.millicent_outputs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Calculate stats
        active_engines = sum(1 for e in engine_states.values() if e.status == EngineStatus.ACTIVE)
        overall_progress = sum(e.progress for e in engine_states.values()) / max(len(engine_states), 1)
        
        return DashboardState(
            user_id=user_id,
            track=state.assigned_track,
            active_modules=[{"id": m, "name": MODULES.get(m, {}).get("name", m)} for m in state.active_modules],
            incomplete_items=[{"id": m, "name": MODULES.get(m, {}).get("name", m)} for m in state.incomplete_items],
            next_steps=[{"step": s, "priority": "normal"} for s in state.next_steps],
            blockers=[{"blocker": b, "severity": "medium"} for b in state.blockers],
            engine_status={k: v for k, v in engine_states.items()},
            arris_outputs=arris_outputs,
            millicent_outputs=millicent_outputs,
            overall_progress=overall_progress,
            engines_active=active_engines,
            modules_unlocked=len(state.unlocked_modules)
        )
