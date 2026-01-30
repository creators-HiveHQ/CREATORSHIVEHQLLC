"""
Creators Hive HQ - Millicent Service
====================================
Rule-based tone, resonance, and communication guidance.
Millicent does NOT use LLM - all guidance is rule-based.

ROLE SEPARATION:
- ARRIS = structure, clarity, logic
- Millicent = tone, resonance, communication
- Neither handles intake or engines
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

from models_system import (
    MillicentToneOutput, TrackType, UserIdentityType, 
    UserStage, EngineType
)

logger = logging.getLogger(__name__)


# ============== TONE RULES ==============

TONE_RULES = {
    # By identity type
    UserIdentityType.CREATOR: {
        "default_tone": "friendly",
        "communication_style": "creative and encouraging",
        "key_phrases": [
            "Your creative vision",
            "Express your unique voice",
            "Build your audience",
            "Share your story"
        ],
        "avoid_phrases": [
            "Corporate strategy",
            "Stakeholder alignment",
            "ROI optimization"
        ]
    },
    UserIdentityType.BUSINESS: {
        "default_tone": "professional",
        "communication_style": "direct and results-focused",
        "key_phrases": [
            "Strategic objectives",
            "Market positioning",
            "Revenue growth",
            "Operational efficiency"
        ],
        "avoid_phrases": [
            "Vibes",
            "Creative journey",
            "Personal expression"
        ]
    },
    UserIdentityType.HYBRID: {
        "default_tone": "balanced",
        "communication_style": "adaptable and strategic",
        "key_phrases": [
            "Creative business",
            "Brand building",
            "Sustainable growth",
            "Authentic engagement"
        ],
        "avoid_phrases": []
    }
}

# By stage
STAGE_TONE_MODIFIERS = {
    UserStage.BEGINNER: {
        "complexity": "simple",
        "guidance_level": "high",
        "encouragement": True,
        "jargon_level": "minimal",
        "tone_modifier": "supportive and educational"
    },
    UserStage.INTERMEDIATE: {
        "complexity": "moderate",
        "guidance_level": "medium",
        "encouragement": True,
        "jargon_level": "some",
        "tone_modifier": "collaborative and growth-focused"
    },
    UserStage.ADVANCED: {
        "complexity": "detailed",
        "guidance_level": "low",
        "encouragement": False,
        "jargon_level": "full",
        "tone_modifier": "peer-level and strategic"
    }
}

# By engine context
ENGINE_TONE_CONTEXT = {
    EngineType.BUSINESS: {
        "tone": "professional",
        "focus": "strategy and planning",
        "keywords": ["plan", "strategy", "market", "growth", "revenue"]
    },
    EngineType.ENGAGEMENT: {
        "tone": "friendly",
        "focus": "connection and community",
        "keywords": ["audience", "engage", "connect", "share", "community"]
    },
    EngineType.ROLE: {
        "tone": "authoritative",
        "focus": "clarity and responsibility",
        "keywords": ["role", "responsibility", "team", "delegate", "accountability"]
    },
    EngineType.INCOME: {
        "tone": "empowering",
        "focus": "financial confidence",
        "keywords": ["income", "revenue", "pricing", "value", "profit"]
    }
}

# Communication templates
COMMUNICATION_TEMPLATES = {
    "welcome": {
        UserIdentityType.CREATOR: "Welcome to your creative command center. Let's build something amazing together.",
        UserIdentityType.BUSINESS: "Welcome to your business control hub. Let's drive results.",
        UserIdentityType.HYBRID: "Welcome to your hybrid workspace. Let's blend creativity with strategy."
    },
    "next_step": {
        UserIdentityType.CREATOR: "Your next creative milestone: {action}",
        UserIdentityType.BUSINESS: "Your next strategic priority: {action}",
        UserIdentityType.HYBRID: "Your next focus area: {action}"
    },
    "blocker": {
        UserIdentityType.CREATOR: "Something needs your attention before you can continue: {blocker}",
        UserIdentityType.BUSINESS: "Action required to proceed: {blocker}",
        UserIdentityType.HYBRID: "Let's address this first: {blocker}"
    },
    "encouragement": {
        UserStage.BEGINNER: "You're making great progress! Every step forward matters.",
        UserStage.INTERMEDIATE: "You're building momentum. Keep pushing forward.",
        UserStage.ADVANCED: "Solid progress. On track for your goals."
    }
}


# ============== MILLICENT SERVICE ==============

class MillicentService:
    """
    Rule-based tone, resonance, and communication guidance.
    Does NOT use LLM - all outputs are rule-based.
    """
    
    def __init__(self, db):
        self.db = db
    
    async def generate_tone_guidance(
        self,
        user_id: str,
        context: str,
        identity_type: UserIdentityType,
        stage: UserStage,
        related_engine: Optional[EngineType] = None,
        related_module: Optional[str] = None
    ) -> MillicentToneOutput:
        """Generate tone guidance based on user identity and context"""
        
        # Get base tone rules
        identity_rules = TONE_RULES.get(identity_type, TONE_RULES[UserIdentityType.HYBRID])
        stage_modifiers = STAGE_TONE_MODIFIERS.get(stage, STAGE_TONE_MODIFIERS[UserStage.INTERMEDIATE])
        
        # Determine tone style
        tone_style = identity_rules["default_tone"]
        if related_engine:
            engine_context = ENGINE_TONE_CONTEXT.get(related_engine, {})
            tone_style = engine_context.get("tone", tone_style)
        
        # Build guidance
        guidance_parts = []
        
        # Communication style
        guidance_parts.append(f"Use a {identity_rules['communication_style']} approach.")
        
        # Stage-appropriate complexity
        guidance_parts.append(f"Keep explanations {stage_modifiers['complexity']}.")
        
        # Tone modifier
        guidance_parts.append(f"Maintain a {stage_modifiers['tone_modifier']} tone.")
        
        # Key phrases to use
        if identity_rules["key_phrases"]:
            guidance_parts.append(f"Incorporate phrases like: {', '.join(identity_rules['key_phrases'][:3])}")
        
        # Phrases to avoid
        if identity_rules["avoid_phrases"]:
            guidance_parts.append(f"Avoid terminology like: {', '.join(identity_rules['avoid_phrases'][:2])}")
        
        # Engine-specific focus
        if related_engine:
            engine_ctx = ENGINE_TONE_CONTEXT.get(related_engine, {})
            guidance_parts.append(f"Focus on {engine_ctx.get('focus', 'the task at hand')}.")
        
        # Encouragement for beginners
        if stage_modifiers["encouragement"]:
            guidance_parts.append("Include encouragement and positive reinforcement.")
        
        guidance = " ".join(guidance_parts)
        
        # Create output
        output = MillicentToneOutput(
            user_id=user_id,
            output_type="tone",
            context=context,
            guidance=guidance,
            tone_style=tone_style,
            related_module=related_module
        )
        
        # Store in database
        await self.db.millicent_outputs.insert_one(output.model_dump())
        
        return output
    
    async def generate_resonance_guidance(
        self,
        user_id: str,
        message: str,
        identity_type: UserIdentityType,
        stage: UserStage
    ) -> MillicentToneOutput:
        """
        Generate resonance guidance - ensuring messages resonate with the user.
        Rule-based analysis of message alignment with user identity.
        """
        
        identity_rules = TONE_RULES.get(identity_type, TONE_RULES[UserIdentityType.HYBRID])
        
        # Check for alignment issues
        issues = []
        recommendations = []
        
        # Check for avoid phrases
        message_lower = message.lower()
        for phrase in identity_rules.get("avoid_phrases", []):
            if phrase.lower() in message_lower:
                issues.append(f"Contains '{phrase}' which may not resonate with {identity_type.value} users")
                recommendations.append(f"Consider replacing '{phrase}' with more appropriate terminology")
        
        # Check for key phrases presence
        key_phrase_count = sum(1 for phrase in identity_rules.get("key_phrases", []) 
                               if phrase.lower() in message_lower)
        if key_phrase_count == 0:
            recommendations.append(f"Consider incorporating key phrases for {identity_type.value} users")
        
        # Build guidance
        if issues:
            guidance = f"Resonance issues detected: {'; '.join(issues)}. Recommendations: {'; '.join(recommendations)}"
        else:
            guidance = f"Message aligns well with {identity_type.value} user expectations. Tone and terminology are appropriate."
        
        output = MillicentToneOutput(
            user_id=user_id,
            output_type="resonance",
            context=f"Message review: {message[:100]}...",
            guidance=guidance,
            tone_style=identity_rules["default_tone"]
        )
        
        await self.db.millicent_outputs.insert_one(output.model_dump())
        
        return output
    
    async def generate_communication_guidance(
        self,
        user_id: str,
        communication_type: str,
        identity_type: UserIdentityType,
        stage: UserStage,
        context_data: Dict[str, Any] = None
    ) -> MillicentToneOutput:
        """
        Generate communication-specific guidance.
        Templates + rules for specific communication types.
        """
        
        context_data = context_data or {}
        
        # Get appropriate template
        template = COMMUNICATION_TEMPLATES.get(communication_type, {})
        
        if identity_type in template:
            base_message = template[identity_type]
        elif stage in template:
            base_message = template[stage]
        else:
            base_message = f"Proceed with {communication_type}"
        
        # Format with context data
        try:
            formatted_message = base_message.format(**context_data)
        except KeyError:
            formatted_message = base_message
        
        # Add stage-appropriate guidance
        stage_modifiers = STAGE_TONE_MODIFIERS.get(stage, STAGE_TONE_MODIFIERS[UserStage.INTERMEDIATE])
        
        guidance = f"{formatted_message} [Delivery: {stage_modifiers['tone_modifier']}]"
        
        output = MillicentToneOutput(
            user_id=user_id,
            output_type="communication",
            context=communication_type,
            guidance=guidance,
            tone_style=TONE_RULES.get(identity_type, TONE_RULES[UserIdentityType.HYBRID])["default_tone"]
        )
        
        await self.db.millicent_outputs.insert_one(output.model_dump())
        
        return output
    
    async def get_welcome_message(
        self,
        identity_type: UserIdentityType,
        stage: UserStage,
        user_name: str = "there"
    ) -> str:
        """Get personalized welcome message"""
        
        base_welcome = COMMUNICATION_TEMPLATES["welcome"].get(
            identity_type, 
            "Welcome to Creators Hive HQ."
        )
        
        stage_mod = STAGE_TONE_MODIFIERS.get(stage, STAGE_TONE_MODIFIERS[UserStage.INTERMEDIATE])
        
        if stage == UserStage.BEGINNER:
            return f"Hi {user_name}! {base_welcome} We're here to guide you every step of the way."
        elif stage == UserStage.INTERMEDIATE:
            return f"Welcome back, {user_name}. {base_welcome}"
        else:
            return f"{user_name}, {base_welcome}"
    
    async def get_next_step_message(
        self,
        identity_type: UserIdentityType,
        action: str
    ) -> str:
        """Get next step message formatted for user identity"""
        
        template = COMMUNICATION_TEMPLATES["next_step"].get(
            identity_type,
            "Your next step: {action}"
        )
        
        return template.format(action=action)
    
    async def get_blocker_message(
        self,
        identity_type: UserIdentityType,
        blocker: str
    ) -> str:
        """Get blocker message formatted for user identity"""
        
        template = COMMUNICATION_TEMPLATES["blocker"].get(
            identity_type,
            "Blocker: {blocker}"
        )
        
        return template.format(blocker=blocker)
    
    async def get_encouragement(
        self,
        stage: UserStage
    ) -> Optional[str]:
        """Get encouragement message based on stage"""
        
        if not STAGE_TONE_MODIFIERS.get(stage, {}).get("encouragement", False):
            return None
        
        return COMMUNICATION_TEMPLATES["encouragement"].get(
            stage,
            "Keep going!"
        )
    
    async def get_recent_outputs(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[MillicentToneOutput]:
        """Get recent Millicent outputs for a user"""
        
        outputs = await self.db.millicent_outputs.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return [MillicentToneOutput(**o) for o in outputs]
