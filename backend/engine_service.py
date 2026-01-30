"""
Creators Hive HQ - Engine Service
=================================
Manages the four core engines: Business, Engagement, Role, Income.
Each engine has inputs, outputs, rules, and dependencies.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

from models_system import (
    EngineType, EngineStatus, EngineState, EngineConfig,
    TrackType, UserIdentityType, UserStage
)

logger = logging.getLogger(__name__)


# ============== ENGINE CONFIGURATIONS ==============

ENGINE_CONFIGS: Dict[EngineType, EngineConfig] = {
    EngineType.BUSINESS: EngineConfig(
        engine_type=EngineType.BUSINESS,
        inputs=[
            "business_model",
            "target_market",
            "value_proposition",
            "revenue_streams",
            "cost_structure"
        ],
        outputs=[
            "business_plan",
            "market_analysis",
            "financial_projections",
            "growth_strategy",
            "risk_assessment"
        ],
        rules=[
            "Requires at least 3 inputs to activate",
            "Must define target market before revenue streams",
            "Financial projections require cost structure",
            "Growth strategy unlocks after business plan"
        ],
        dependencies=[],  # Business engine has no dependencies
        required_modules=[
            "business_model_canvas",
            "market_research",
            "financial_planning",
            "strategy_builder"
        ]
    ),
    
    EngineType.ENGAGEMENT: EngineConfig(
        engine_type=EngineType.ENGAGEMENT,
        inputs=[
            "audience_profile",
            "content_strategy",
            "platform_selection",
            "engagement_goals",
            "communication_style"
        ],
        outputs=[
            "engagement_plan",
            "content_calendar",
            "audience_insights",
            "growth_metrics",
            "community_strategy"
        ],
        rules=[
            "Requires audience profile first",
            "Platform selection enables content strategy",
            "Engagement goals drive metrics tracking",
            "Communication style informs content tone"
        ],
        dependencies=[],  # Can operate independently
        required_modules=[
            "audience_builder",
            "content_planner",
            "platform_optimizer",
            "community_manager"
        ]
    ),
    
    EngineType.ROLE: EngineConfig(
        engine_type=EngineType.ROLE,
        inputs=[
            "role_definition",
            "responsibilities",
            "skills_required",
            "authority_level",
            "accountability_matrix"
        ],
        outputs=[
            "role_clarity",
            "task_assignments",
            "delegation_plan",
            "team_structure",
            "performance_criteria"
        ],
        rules=[
            "Role definition is the foundation",
            "Responsibilities must align with authority",
            "Skills gap triggers training recommendations",
            "Accountability requires clear metrics"
        ],
        dependencies=[EngineType.BUSINESS],  # Roles need business context
        required_modules=[
            "role_definer",
            "team_builder",
            "delegation_matrix",
            "accountability_tracker"
        ]
    ),
    
    EngineType.INCOME: EngineConfig(
        engine_type=EngineType.INCOME,
        inputs=[
            "income_sources",
            "pricing_strategy",
            "sales_pipeline",
            "payment_systems",
            "financial_goals"
        ],
        outputs=[
            "revenue_forecast",
            "pricing_recommendations",
            "sales_strategy",
            "cash_flow_plan",
            "income_optimization"
        ],
        rules=[
            "Income sources must be validated",
            "Pricing requires market validation",
            "Sales pipeline needs audience data",
            "Financial goals drive all outputs"
        ],
        dependencies=[EngineType.BUSINESS, EngineType.ENGAGEMENT],
        required_modules=[
            "revenue_tracker",
            "pricing_optimizer",
            "sales_funnel",
            "financial_dashboard"
        ]
    )
}


# ============== ENGINE SERVICE ==============

class EngineService:
    """Manages the four core engines"""
    
    def __init__(self, db):
        self.db = db
        self.configs = ENGINE_CONFIGS
    
    async def initialize_engines_for_user(
        self,
        user_id: str,
        selected_engines: List[EngineType]
    ) -> Dict[str, EngineState]:
        """Initialize engines for a user based on their intake selections"""
        engine_states = {}
        
        for engine_type in EngineType:
            is_selected = engine_type in selected_engines
            
            # Check dependencies
            config = self.configs[engine_type]
            dependencies_met = all(
                dep in selected_engines for dep in config.dependencies
            )
            
            # Determine initial status
            if is_selected and dependencies_met:
                status = EngineStatus.ACTIVE
            elif is_selected and not dependencies_met:
                status = EngineStatus.PENDING
            else:
                status = EngineStatus.INACTIVE
            
            engine_states[engine_type.value] = EngineState(
                engine_type=engine_type,
                status=status,
                progress=0.0,
                inputs_received=0,
                outputs_generated=0,
                blockers=[] if dependencies_met else [
                    f"Requires {dep.value} to be active" for dep in config.dependencies
                    if dep not in selected_engines
                ],
                dependencies_met=dependencies_met,
                last_activity=datetime.now(timezone.utc).isoformat()
            )
        
        # Store in database
        await self.db.user_engine_states.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "engines": {k: v.model_dump() for k, v in engine_states.items()},
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        logger.info(f"Initialized engines for user {user_id}: {[e.value for e in selected_engines]}")
        return engine_states
    
    async def get_engine_state(self, user_id: str, engine_type: EngineType) -> Optional[EngineState]:
        """Get current state of a specific engine for a user"""
        record = await self.db.user_engine_states.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not record or "engines" not in record:
            return None
        
        engine_data = record["engines"].get(engine_type.value)
        if engine_data:
            return EngineState(**engine_data)
        return None
    
    async def get_all_engine_states(self, user_id: str) -> Dict[str, EngineState]:
        """Get all engine states for a user"""
        record = await self.db.user_engine_states.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not record or "engines" not in record:
            return {}
        
        return {
            k: EngineState(**v) for k, v in record["engines"].items()
        }
    
    async def update_engine_progress(
        self,
        user_id: str,
        engine_type: EngineType,
        progress: float,
        inputs_received: int = 0,
        outputs_generated: int = 0
    ) -> EngineState:
        """Update progress for an engine"""
        engine_state = await self.get_engine_state(user_id, engine_type)
        
        if not engine_state:
            raise ValueError(f"Engine {engine_type.value} not initialized for user {user_id}")
        
        engine_state.progress = min(100.0, max(0.0, progress))
        engine_state.inputs_received += inputs_received
        engine_state.outputs_generated += outputs_generated
        engine_state.last_activity = datetime.now(timezone.utc).isoformat()
        
        await self.db.user_engine_states.update_one(
            {"user_id": user_id},
            {"$set": {
                f"engines.{engine_type.value}": engine_state.model_dump(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return engine_state
    
    async def add_engine_blocker(
        self,
        user_id: str,
        engine_type: EngineType,
        blocker: str
    ) -> EngineState:
        """Add a blocker to an engine"""
        engine_state = await self.get_engine_state(user_id, engine_type)
        
        if not engine_state:
            raise ValueError(f"Engine {engine_type.value} not initialized for user {user_id}")
        
        if blocker not in engine_state.blockers:
            engine_state.blockers.append(blocker)
            engine_state.status = EngineStatus.BLOCKED
        
        await self.db.user_engine_states.update_one(
            {"user_id": user_id},
            {"$set": {
                f"engines.{engine_type.value}": engine_state.model_dump(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return engine_state
    
    async def remove_engine_blocker(
        self,
        user_id: str,
        engine_type: EngineType,
        blocker: str
    ) -> EngineState:
        """Remove a blocker from an engine"""
        engine_state = await self.get_engine_state(user_id, engine_type)
        
        if not engine_state:
            raise ValueError(f"Engine {engine_type.value} not initialized for user {user_id}")
        
        if blocker in engine_state.blockers:
            engine_state.blockers.remove(blocker)
        
        # Update status if no more blockers
        if not engine_state.blockers and engine_state.status == EngineStatus.BLOCKED:
            engine_state.status = EngineStatus.ACTIVE if engine_state.dependencies_met else EngineStatus.PENDING
        
        await self.db.user_engine_states.update_one(
            {"user_id": user_id},
            {"$set": {
                f"engines.{engine_type.value}": engine_state.model_dump(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return engine_state
    
    async def process_engine_input(
        self,
        user_id: str,
        engine_type: EngineType,
        input_type: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an input for an engine and generate outputs"""
        config = self.configs[engine_type]
        engine_state = await self.get_engine_state(user_id, engine_type)
        
        if not engine_state:
            raise ValueError(f"Engine {engine_type.value} not initialized")
        
        if engine_state.status not in [EngineStatus.ACTIVE, EngineStatus.PENDING]:
            raise ValueError(f"Engine {engine_type.value} is not active")
        
        if input_type not in config.inputs:
            raise ValueError(f"Invalid input type {input_type} for engine {engine_type.value}")
        
        # Store the input
        await self.db.engine_inputs.insert_one({
            "user_id": user_id,
            "engine_type": engine_type.value,
            "input_type": input_type,
            "input_data": input_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Update progress
        total_inputs = len(config.inputs)
        received = await self.db.engine_inputs.count_documents({
            "user_id": user_id,
            "engine_type": engine_type.value
        })
        progress = min(100.0, (received / total_inputs) * 100)
        
        await self.update_engine_progress(
            user_id, engine_type, progress, inputs_received=1
        )
        
        return {
            "success": True,
            "engine": engine_type.value,
            "input_type": input_type,
            "progress": progress,
            "inputs_received": received,
            "total_inputs": total_inputs
        }
    
    async def generate_engine_output(
        self,
        user_id: str,
        engine_type: EngineType,
        output_type: str
    ) -> Dict[str, Any]:
        """Generate an output from an engine based on collected inputs"""
        config = self.configs[engine_type]
        
        if output_type not in config.outputs:
            raise ValueError(f"Invalid output type {output_type} for engine {engine_type.value}")
        
        # Get all inputs for this engine
        inputs = await self.db.engine_inputs.find({
            "user_id": user_id,
            "engine_type": engine_type.value
        }, {"_id": 0}).to_list(100)
        
        # Generate output based on inputs (rule-based, not LLM)
        output_data = self._generate_rule_based_output(
            engine_type, output_type, inputs
        )
        
        # Store the output
        output_record = {
            "user_id": user_id,
            "engine_type": engine_type.value,
            "output_type": output_type,
            "output_data": output_data,
            "inputs_used": len(inputs),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.engine_outputs.insert_one(output_record)
        
        # Update engine state
        await self.update_engine_progress(
            user_id, engine_type, 
            progress=0,  # Don't change progress
            outputs_generated=1
        )
        
        return output_data
    
    def _generate_rule_based_output(
        self,
        engine_type: EngineType,
        output_type: str,
        inputs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate rule-based output (no LLM)"""
        input_map = {inp["input_type"]: inp["input_data"] for inp in inputs}
        
        # Business Engine outputs
        if engine_type == EngineType.BUSINESS:
            if output_type == "business_plan":
                return {
                    "title": "Business Plan Summary",
                    "sections": [
                        {"name": "Business Model", "status": "complete" if "business_model" in input_map else "pending"},
                        {"name": "Target Market", "status": "complete" if "target_market" in input_map else "pending"},
                        {"name": "Value Proposition", "status": "complete" if "value_proposition" in input_map else "pending"},
                        {"name": "Revenue Streams", "status": "complete" if "revenue_streams" in input_map else "pending"},
                        {"name": "Cost Structure", "status": "complete" if "cost_structure" in input_map else "pending"}
                    ],
                    "completion": len(input_map) / 5 * 100
                }
            elif output_type == "market_analysis":
                return {
                    "title": "Market Analysis",
                    "target_market": input_map.get("target_market", {}),
                    "insights": ["Define your target market to generate insights"],
                    "recommendations": ["Complete market research module"]
                }
        
        # Engagement Engine outputs
        elif engine_type == EngineType.ENGAGEMENT:
            if output_type == "engagement_plan":
                return {
                    "title": "Engagement Plan",
                    "audience": input_map.get("audience_profile", {}),
                    "platforms": input_map.get("platform_selection", []),
                    "content_strategy": input_map.get("content_strategy", {}),
                    "next_actions": ["Define audience profile", "Select platforms", "Create content strategy"]
                }
            elif output_type == "content_calendar":
                return {
                    "title": "Content Calendar",
                    "frequency": "To be determined based on strategy",
                    "platforms": input_map.get("platform_selection", []),
                    "content_types": []
                }
        
        # Role Engine outputs
        elif engine_type == EngineType.ROLE:
            if output_type == "role_clarity":
                return {
                    "title": "Role Clarity Report",
                    "defined_roles": input_map.get("role_definition", []),
                    "responsibilities": input_map.get("responsibilities", []),
                    "gaps": ["Complete role definition module"],
                    "recommendations": []
                }
            elif output_type == "team_structure":
                return {
                    "title": "Team Structure",
                    "roles": input_map.get("role_definition", []),
                    "hierarchy": "To be defined",
                    "accountability": input_map.get("accountability_matrix", {})
                }
        
        # Income Engine outputs
        elif engine_type == EngineType.INCOME:
            if output_type == "revenue_forecast":
                return {
                    "title": "Revenue Forecast",
                    "sources": input_map.get("income_sources", []),
                    "projections": "Requires pricing and pipeline data",
                    "goals": input_map.get("financial_goals", {})
                }
            elif output_type == "pricing_recommendations":
                return {
                    "title": "Pricing Recommendations",
                    "current_pricing": input_map.get("pricing_strategy", {}),
                    "market_rates": "Complete market analysis first",
                    "recommendations": []
                }
        
        # Default output
        return {
            "title": f"{output_type.replace('_', ' ').title()}",
            "engine": engine_type.value,
            "status": "generated",
            "inputs_used": len(inputs),
            "data": {}
        }
    
    def get_engine_config(self, engine_type: EngineType) -> EngineConfig:
        """Get configuration for an engine"""
        return self.configs[engine_type]
    
    def get_all_engine_configs(self) -> Dict[EngineType, EngineConfig]:
        """Get all engine configurations"""
        return self.configs
    
    def get_required_modules_for_engines(
        self,
        selected_engines: List[EngineType]
    ) -> List[str]:
        """Get list of modules required for selected engines"""
        modules = set()
        for engine_type in selected_engines:
            config = self.configs[engine_type]
            modules.update(config.required_modules)
        return list(modules)
