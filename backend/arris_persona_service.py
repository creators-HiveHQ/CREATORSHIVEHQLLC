"""
ARRIS Persona Service for Creators Hive HQ
Phase 4 Module E - Task E1: Custom ARRIS Personas

Allows Elite creators to customize ARRIS's personality, communication style,
focus areas, and response patterns. Integrates with all ARRIS interactions.

Features:
- Pre-built default personas (Professional, Friendly, Analytical, Creative, Coach)
- Custom persona creation with full customization
- Persona switching with instant effect
- Persona testing/preview
- Usage analytics per persona
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import secrets

logger = logging.getLogger(__name__)


class PersonaTone(str, Enum):
    """Communication tone options"""
    PROFESSIONAL = "professional"  # Formal, business-like
    FRIENDLY = "friendly"  # Warm, conversational
    ANALYTICAL = "analytical"  # Data-driven, precise
    CREATIVE = "creative"  # Imaginative, innovative
    MOTIVATIONAL = "motivational"  # Encouraging, energizing
    DIRECT = "direct"  # Concise, to the point
    EMPATHETIC = "empathetic"  # Understanding, supportive


class CommunicationStyle(str, Enum):
    """How ARRIS structures responses"""
    DETAILED = "detailed"  # Long, comprehensive answers
    CONCISE = "concise"  # Brief, bullet-point style
    CONVERSATIONAL = "conversational"  # Natural flow, questions back
    STRUCTURED = "structured"  # Headers, lists, organized
    STORYTELLING = "storytelling"  # Narrative-driven
    SOCRATIC = "socratic"  # Questions to guide thinking


class FocusArea(str, Enum):
    """Areas ARRIS should prioritize"""
    GROWTH = "growth"  # Audience growth strategies
    MONETIZATION = "monetization"  # Revenue optimization
    CONTENT = "content"  # Content quality and ideas
    ENGAGEMENT = "engagement"  # Community interaction
    STRATEGY = "strategy"  # Long-term planning
    PRODUCTIVITY = "productivity"  # Time management, efficiency
    CREATIVITY = "creativity"  # Ideation, innovation
    ANALYTICS = "analytics"  # Data interpretation
    BRANDING = "branding"  # Personal brand development
    NETWORKING = "networking"  # Partnerships, collaborations


class ResponseLength(str, Enum):
    """Preferred response length"""
    BRIEF = "brief"  # 1-2 sentences
    SHORT = "short"  # 1 paragraph
    MEDIUM = "medium"  # 2-3 paragraphs
    DETAILED = "detailed"  # Comprehensive, multi-section
    ADAPTIVE = "adaptive"  # Varies based on question


# Default personas available to all Elite users
DEFAULT_PERSONAS = {
    "professional": {
        "id": "PERSONA-DEFAULT-PRO",
        "name": "Professional ARRIS",
        "description": "Business-focused, data-driven advice with a formal tone. Perfect for serious strategy discussions and professional communications.",
        "tone": PersonaTone.PROFESSIONAL.value,
        "communication_style": CommunicationStyle.STRUCTURED.value,
        "response_length": ResponseLength.DETAILED.value,
        "primary_focus_areas": [FocusArea.STRATEGY.value, FocusArea.MONETIZATION.value, FocusArea.ANALYTICS.value],
        "emoji_usage": "minimal",
        "custom_greeting": "Hello! I'm here to help you achieve your business objectives.",
        "signature_phrase": "Let's make data-driven decisions together.",
        "personality_traits": ["precise", "analytical", "strategic", "reliable"],
        "avoid_topics": [],
        "is_default": True,
        "is_system": True,
        "icon": "briefcase"
    },
    "friendly": {
        "id": "PERSONA-DEFAULT-FRI",
        "name": "Friendly ARRIS",
        "description": "Warm, supportive, and encouraging. Great for daily check-ins and creative brainstorming sessions.",
        "tone": PersonaTone.FRIENDLY.value,
        "communication_style": CommunicationStyle.CONVERSATIONAL.value,
        "response_length": ResponseLength.MEDIUM.value,
        "primary_focus_areas": [FocusArea.ENGAGEMENT.value, FocusArea.CREATIVITY.value, FocusArea.CONTENT.value],
        "emoji_usage": "moderate",
        "custom_greeting": "Hey there! 👋 Great to see you! What's on your mind today?",
        "signature_phrase": "You've got this! I'm here to help.",
        "personality_traits": ["warm", "encouraging", "approachable", "positive"],
        "avoid_topics": [],
        "is_default": True,
        "is_system": True,
        "icon": "smile"
    },
    "analytical": {
        "id": "PERSONA-DEFAULT-ANA",
        "name": "Analytical ARRIS",
        "description": "Deep data analysis, metrics-focused insights, and pattern recognition. Ideal for performance reviews and optimization.",
        "tone": PersonaTone.ANALYTICAL.value,
        "communication_style": CommunicationStyle.DETAILED.value,
        "response_length": ResponseLength.DETAILED.value,
        "primary_focus_areas": [FocusArea.ANALYTICS.value, FocusArea.GROWTH.value, FocusArea.MONETIZATION.value],
        "emoji_usage": "none",
        "custom_greeting": "Ready for analysis. What data or metrics shall we examine?",
        "signature_phrase": "The numbers tell the story.",
        "personality_traits": ["precise", "thorough", "objective", "pattern-focused"],
        "avoid_topics": [],
        "is_default": True,
        "is_system": True,
        "icon": "chart-line"
    },
    "creative": {
        "id": "PERSONA-DEFAULT-CRE",
        "name": "Creative ARRIS",
        "description": "Imaginative, unconventional ideas, and out-of-the-box thinking. Perfect for content ideation and creative challenges.",
        "tone": PersonaTone.CREATIVE.value,
        "communication_style": CommunicationStyle.STORYTELLING.value,
        "response_length": ResponseLength.MEDIUM.value,
        "primary_focus_areas": [FocusArea.CREATIVITY.value, FocusArea.CONTENT.value, FocusArea.BRANDING.value],
        "emoji_usage": "frequent",
        "custom_greeting": "✨ Let's create something amazing! What shall we dream up today?",
        "signature_phrase": "Imagination is the beginning of creation.",
        "personality_traits": ["innovative", "playful", "bold", "visionary"],
        "avoid_topics": [],
        "is_default": True,
        "is_system": True,
        "icon": "lightbulb"
    },
    "coach": {
        "id": "PERSONA-DEFAULT-COA",
        "name": "Coach ARRIS",
        "description": "Motivational, accountability-focused guidance with tough love when needed. Great for goal setting and performance improvement.",
        "tone": PersonaTone.MOTIVATIONAL.value,
        "communication_style": CommunicationStyle.SOCRATIC.value,
        "response_length": ResponseLength.MEDIUM.value,
        "primary_focus_areas": [FocusArea.PRODUCTIVITY.value, FocusArea.GROWTH.value, FocusArea.STRATEGY.value],
        "emoji_usage": "moderate",
        "custom_greeting": "Let's level up! 💪 What goals are we crushing today?",
        "signature_phrase": "Success is built one decision at a time.",
        "personality_traits": ["motivating", "challenging", "supportive", "action-oriented"],
        "avoid_topics": [],
        "is_default": True,
        "is_system": True,
        "icon": "trophy"
    }
}


class ArrisPersonaService:
    """
    Manages ARRIS personas for Elite creators.
    Handles persona creation, customization, activation, and prompt generation.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ============== PERSONA MANAGEMENT ==============

    async def get_all_personas(self, creator_id: str) -> Dict[str, Any]:
        """
        Get all available personas for a creator (defaults + custom).
        """
        # Get custom personas
        custom_personas = await self.db.arris_personas.find(
            {"creator_id": creator_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)

        # Get active persona
        active_persona_id = await self._get_active_persona_id(creator_id)

        # Mark which one is active
        for persona in custom_personas:
            persona["is_active"] = persona["id"] == active_persona_id

        # Format default personas with active status
        defaults = []
        for key, persona in DEFAULT_PERSONAS.items():
            persona_copy = {**persona}
            persona_copy["is_active"] = persona_copy["id"] == active_persona_id
            defaults.append(persona_copy)

        return {
            "default_personas": defaults,
            "custom_personas": custom_personas,
            "active_persona_id": active_persona_id,
            "total_custom": len(custom_personas)
        }

    async def get_persona(self, creator_id: str, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific persona by ID."""
        # Check if it's a default persona
        for key, persona in DEFAULT_PERSONAS.items():
            if persona["id"] == persona_id:
                active_id = await self._get_active_persona_id(creator_id)
                return {**persona, "is_active": persona["id"] == active_id}

        # Check custom personas
        persona = await self.db.arris_personas.find_one(
            {"id": persona_id, "creator_id": creator_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )

        if persona:
            active_id = await self._get_active_persona_id(creator_id)
            persona["is_active"] = persona["id"] == active_id

        return persona

    async def create_persona(self, creator_id: str, persona_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new custom ARRIS persona.
        Elite creators can create unlimited custom personas.
        """
        now = datetime.now(timezone.utc)
        persona_id = f"PERSONA-{secrets.token_hex(6).upper()}"

        persona = {
            "id": persona_id,
            "creator_id": creator_id,
            "name": persona_data.get("name", "Custom ARRIS"),
            "description": persona_data.get("description", ""),
            "tone": persona_data.get("tone", PersonaTone.FRIENDLY.value),
            "communication_style": persona_data.get("communication_style", CommunicationStyle.CONVERSATIONAL.value),
            "response_length": persona_data.get("response_length", ResponseLength.MEDIUM.value),
            "primary_focus_areas": persona_data.get("primary_focus_areas", [FocusArea.CONTENT.value]),
            "emoji_usage": persona_data.get("emoji_usage", "moderate"),  # none, minimal, moderate, frequent
            "custom_greeting": persona_data.get("custom_greeting", "Hello! How can I help you today?"),
            "signature_phrase": persona_data.get("signature_phrase", ""),
            "personality_traits": persona_data.get("personality_traits", []),
            "avoid_topics": persona_data.get("avoid_topics", []),
            "custom_instructions": persona_data.get("custom_instructions", ""),
            "example_responses": persona_data.get("example_responses", []),
            "is_default": False,
            "is_system": False,
            "icon": persona_data.get("icon", "user"),
            "usage_count": 0,
            "is_deleted": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        await self.db.arris_personas.insert_one(persona)

        # Log activity
        await self._log_persona_activity(
            creator_id=creator_id,
            action="persona_created",
            persona_id=persona_id,
            details={"name": persona["name"]}
        )

        logger.info(f"Created custom ARRIS persona {persona_id} for creator {creator_id}")

        return {k: v for k, v in persona.items() if k != "_id"}

    async def update_persona(
        self,
        creator_id: str,
        persona_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a custom persona. Cannot update system personas.
        """
        # Check if it's a system persona
        for key, persona in DEFAULT_PERSONAS.items():
            if persona["id"] == persona_id:
                return None  # Cannot update system personas

        # Remove protected fields from updates
        protected_fields = ["id", "creator_id", "is_system", "created_at", "usage_count"]
        for field in protected_fields:
            updates.pop(field, None)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        result = await self.db.arris_personas.update_one(
            {"id": persona_id, "creator_id": creator_id, "is_deleted": {"$ne": True}},
            {"$set": updates}
        )

        if result.modified_count == 0:
            return None

        # Log activity
        await self._log_persona_activity(
            creator_id=creator_id,
            action="persona_updated",
            persona_id=persona_id,
            details={"updated_fields": list(updates.keys())}
        )

        return await self.get_persona(creator_id, persona_id)

    async def delete_persona(self, creator_id: str, persona_id: str) -> bool:
        """
        Soft delete a custom persona. Cannot delete system personas.
        If deleted persona was active, switches to default Professional.
        """
        # Check if it's a system persona
        for key, persona in DEFAULT_PERSONAS.items():
            if persona["id"] == persona_id:
                return False  # Cannot delete system personas

        # Check if this is the active persona
        active_id = await self._get_active_persona_id(creator_id)
        if active_id == persona_id:
            # Switch to default professional
            await self.activate_persona(creator_id, DEFAULT_PERSONAS["professional"]["id"])

        result = await self.db.arris_personas.update_one(
            {"id": persona_id, "creator_id": creator_id},
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc).isoformat()}}
        )

        if result.modified_count > 0:
            await self._log_persona_activity(
                creator_id=creator_id,
                action="persona_deleted",
                persona_id=persona_id
            )
            return True

        return False

    # ============== PERSONA ACTIVATION ==============

    async def activate_persona(self, creator_id: str, persona_id: str) -> Dict[str, Any]:
        """
        Set a persona as the active one for ARRIS interactions.
        """
        # Verify persona exists
        persona = await self.get_persona(creator_id, persona_id)
        if not persona:
            return {"success": False, "error": "Persona not found"}

        now = datetime.now(timezone.utc)

        # Update or create active persona record
        await self.db.creator_active_persona.update_one(
            {"creator_id": creator_id},
            {
                "$set": {
                    "persona_id": persona_id,
                    "persona_name": persona["name"],
                    "activated_at": now.isoformat(),
                    "updated_at": now.isoformat()
                },
                "$setOnInsert": {"creator_id": creator_id}
            },
            upsert=True
        )

        # Increment usage count if custom persona
        if not persona.get("is_system"):
            await self.db.arris_personas.update_one(
                {"id": persona_id},
                {"$inc": {"usage_count": 1}}
            )

        # Log activity
        await self._log_persona_activity(
            creator_id=creator_id,
            action="persona_activated",
            persona_id=persona_id,
            details={"persona_name": persona["name"]}
        )

        return {
            "success": True,
            "active_persona": persona,
            "message": f"Switched to {persona['name']}"
        }

    async def get_active_persona(self, creator_id: str) -> Dict[str, Any]:
        """
        Get the currently active persona for a creator.
        Returns Professional persona if none set.
        """
        persona_id = await self._get_active_persona_id(creator_id)
        persona = await self.get_persona(creator_id, persona_id)

        if not persona:
            # Fallback to Professional
            persona = {**DEFAULT_PERSONAS["professional"]}

        persona["is_active"] = True
        return persona

    async def _get_active_persona_id(self, creator_id: str) -> str:
        """Get the ID of the active persona."""
        record = await self.db.creator_active_persona.find_one(
            {"creator_id": creator_id},
            {"_id": 0, "persona_id": 1}
        )

        if record and record.get("persona_id"):
            return record["persona_id"]

        # Default to Professional
        return DEFAULT_PERSONAS["professional"]["id"]

    # ============== PROMPT GENERATION ==============

    def generate_persona_system_prompt(self, persona: Dict[str, Any]) -> str:
        """
        Generate the system prompt that shapes ARRIS's behavior based on persona.
        This is injected into all ARRIS interactions.
        """
        tone_descriptions = {
            "professional": "formal, business-oriented, and polished",
            "friendly": "warm, conversational, and approachable",
            "analytical": "precise, data-focused, and methodical",
            "creative": "imaginative, innovative, and unconventional",
            "motivational": "encouraging, energizing, and inspiring",
            "direct": "concise, straightforward, and to the point",
            "empathetic": "understanding, supportive, and compassionate"
        }

        style_instructions = {
            "detailed": "Provide comprehensive, in-depth responses with multiple perspectives and examples.",
            "concise": "Keep responses brief and focused. Use bullet points when appropriate.",
            "conversational": "Engage naturally, ask follow-up questions, and maintain a dialogue flow.",
            "structured": "Organize responses with clear headers, numbered lists, and logical sections.",
            "storytelling": "Use narratives, analogies, and relatable stories to convey points.",
            "socratic": "Guide through questions, help the creator discover insights themselves."
        }

        length_guidelines = {
            "brief": "Keep responses to 1-2 sentences maximum.",
            "short": "Limit responses to a single paragraph.",
            "medium": "Provide responses of 2-3 paragraphs.",
            "detailed": "Give comprehensive responses with multiple sections as needed.",
            "adaptive": "Adjust response length based on the complexity of the question."
        }

        emoji_rules = {
            "none": "Do not use any emojis.",
            "minimal": "Use emojis sparingly, only for key emphasis.",
            "moderate": "Include occasional emojis to add personality.",
            "frequent": "Use emojis liberally to create an expressive, lively tone."
        }

        # Build the prompt
        prompt_parts = [
            f"You are ARRIS, an AI assistant with the '{persona.get('name', 'Custom')}' persona.",
            f"Your communication tone is {tone_descriptions.get(persona.get('tone'), 'professional')}.",
            "",
            "COMMUNICATION STYLE:",
            f"- {style_instructions.get(persona.get('communication_style'), style_instructions['structured'])}",
            f"- {length_guidelines.get(persona.get('response_length'), length_guidelines['medium'])}",
            f"- {emoji_rules.get(persona.get('emoji_usage'), emoji_rules['moderate'])}",
        ]

        # Add focus areas
        focus_areas = persona.get("primary_focus_areas", [])
        if focus_areas:
            prompt_parts.append("")
            prompt_parts.append("PRIMARY FOCUS AREAS (prioritize advice in these areas):")
            for area in focus_areas:
                prompt_parts.append(f"- {area.replace('_', ' ').title()}")

        # Add personality traits
        traits = persona.get("personality_traits", [])
        if traits:
            prompt_parts.append("")
            prompt_parts.append(f"PERSONALITY TRAITS: {', '.join(traits)}")

        # Add custom greeting if different context
        greeting = persona.get("custom_greeting")
        if greeting:
            prompt_parts.append("")
            prompt_parts.append(f"GREETING STYLE: When starting conversations, use a style similar to: \"{greeting}\"")

        # Add signature phrase
        signature = persona.get("signature_phrase")
        if signature:
            prompt_parts.append(f"SIGNATURE PHRASE: Occasionally incorporate: \"{signature}\"")

        # Add topics to avoid
        avoid = persona.get("avoid_topics", [])
        if avoid:
            prompt_parts.append("")
            prompt_parts.append(f"TOPICS TO AVOID: {', '.join(avoid)}")

        # Add custom instructions
        custom = persona.get("custom_instructions")
        if custom:
            prompt_parts.append("")
            prompt_parts.append("ADDITIONAL INSTRUCTIONS:")
            prompt_parts.append(custom)

        # Add example responses
        examples = persona.get("example_responses", [])
        if examples:
            prompt_parts.append("")
            prompt_parts.append("RESPONSE STYLE EXAMPLES:")
            for i, example in enumerate(examples[:3], 1):
                prompt_parts.append(f"{i}. \"{example}\"")

        return "\n".join(prompt_parts)

    async def get_persona_prompt_for_creator(self, creator_id: str) -> str:
        """
        Get the complete persona system prompt for a creator's active persona.
        Use this when making ARRIS API calls.
        """
        persona = await self.get_active_persona(creator_id)
        return self.generate_persona_system_prompt(persona)

    # ============== PERSONA TESTING ==============

    async def test_persona(
        self,
        creator_id: str,
        persona_id: str,
        test_message: str
    ) -> Dict[str, Any]:
        """
        Test a persona with a sample message.
        Returns the system prompt that would be used and a preview response.
        Note: Actual AI response requires LLM integration.
        """
        persona = await self.get_persona(creator_id, persona_id)
        if not persona:
            return {"success": False, "error": "Persona not found"}

        system_prompt = self.generate_persona_system_prompt(persona)

        return {
            "success": True,
            "persona": persona,
            "system_prompt_preview": system_prompt,
            "test_message": test_message,
            "note": "Full AI response requires LLM integration. This shows the prompt configuration."
        }

    # ============== ANALYTICS ==============

    async def get_persona_analytics(self, creator_id: str) -> Dict[str, Any]:
        """
        Get usage analytics for personas.
        """
        # Get all custom personas with usage stats
        custom_personas = await self.db.arris_personas.find(
            {"creator_id": creator_id, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1, "usage_count": 1, "created_at": 1}
        ).to_list(50)

        # Count activations by persona
        activation_pipeline = [
            {
                "$match": {
                    "creator_id": creator_id,
                    "action": "persona_activated"
                }
            },
            {
                "$group": {
                    "_id": "$persona_id",
                    "activation_count": {"$sum": 1},
                    "last_activated": {"$max": "$timestamp"}
                }
            }
        ]
        activations = await self.db.persona_activity_log.aggregate(activation_pipeline).to_list(50)
        activation_map = {a["_id"]: a for a in activations}

        # Get current active persona
        active = await self.get_active_persona(creator_id)

        return {
            "active_persona": {
                "id": active.get("id"),
                "name": active.get("name")
            },
            "custom_personas_count": len(custom_personas),
            "custom_personas": custom_personas,
            "activation_stats": activation_map,
            "most_used_persona": max(custom_personas, key=lambda x: x.get("usage_count", 0))["name"] if custom_personas else active.get("name")
        }

    # ============== ACTIVITY LOGGING ==============

    async def _log_persona_activity(
        self,
        creator_id: str,
        action: str,
        persona_id: str = None,
        details: Dict[str, Any] = None
    ) -> None:
        """Log persona-related activity."""
        log_entry = {
            "creator_id": creator_id,
            "action": action,
            "persona_id": persona_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.persona_activity_log.insert_one(log_entry)


# Export constants for API use
AVAILABLE_TONES = [t.value for t in PersonaTone]
AVAILABLE_STYLES = [s.value for s in CommunicationStyle]
AVAILABLE_FOCUS_AREAS = [f.value for f in FocusArea]
AVAILABLE_RESPONSE_LENGTHS = [r.value for r in ResponseLength]

# Singleton instance
persona_service: Optional[ArrisPersonaService] = None
