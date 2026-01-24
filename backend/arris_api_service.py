"""
ARRIS API Access Service for Creators Hive HQ
Phase 4 Module E - Task E3: ARRIS API Access

Provides Elite creators with direct API access to ARRIS capabilities:
- API key generation and management
- Direct text analysis and insights
- Batch processing
- Usage tracking and rate limiting
- Webhook integration for async results

Features:
- Secure API key with prefix (arris_live_, arris_test_)
- Rate limiting: 1000 requests/day, 100 requests/hour
- Usage analytics and quota tracking
- Multiple API keys per creator
- Key rotation and revocation
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import secrets
import hashlib
import json

logger = logging.getLogger(__name__)


class ApiKeyType(str, Enum):
    LIVE = "live"
    TEST = "test"


class ApiKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Rate limits for Elite API access
RATE_LIMITS = {
    "requests_per_hour": 100,
    "requests_per_day": 1000,
    "max_batch_size": 10,
    "max_text_length": 50000,  # characters
    "max_concurrent_requests": 5,
}

# Available API capabilities
API_CAPABILITIES = [
    {
        "id": "text_analysis",
        "name": "Text Analysis",
        "description": "Analyze any text content for insights, sentiment, and recommendations",
        "endpoint": "/api/elite/arris-api/analyze",
        "method": "POST"
    },
    {
        "id": "proposal_insights",
        "name": "Proposal Insights",
        "description": "Get AI-powered insights for project proposals",
        "endpoint": "/api/elite/arris-api/insights",
        "method": "POST"
    },
    {
        "id": "content_suggestions",
        "name": "Content Suggestions",
        "description": "Generate content ideas and suggestions based on your niche",
        "endpoint": "/api/elite/arris-api/content",
        "method": "POST"
    },
    {
        "id": "batch_analysis",
        "name": "Batch Analysis",
        "description": "Process multiple texts in a single request",
        "endpoint": "/api/elite/arris-api/batch",
        "method": "POST"
    },
    {
        "id": "persona_chat",
        "name": "Persona Chat",
        "description": "Chat with ARRIS using your custom persona settings",
        "endpoint": "/api/elite/arris-api/chat",
        "method": "POST"
    }
]


class ArrisApiService:
    """
    Manages ARRIS API access for Elite creators.
    Provides API key management, rate limiting, and direct AI access.
    """

    def __init__(self, db: AsyncIOMotorDatabase, arris_service=None, persona_service=None):
        self.db = db
        self.arris_service = arris_service
        self.persona_service = persona_service

    # ============== API KEY MANAGEMENT ==============

    async def generate_api_key(
        self,
        creator_id: str,
        key_type: str = ApiKeyType.LIVE.value,
        name: str = "Default API Key",
        expires_in_days: int = 365
    ) -> Dict[str, Any]:
        """
        Generate a new API key for the creator.
        Returns the full key only once - it's hashed for storage.
        """
        # Check existing keys count (max 5 active keys)
        active_keys = await self.db.arris_api_keys.count_documents({
            "creator_id": creator_id,
            "status": ApiKeyStatus.ACTIVE.value
        })
        
        if active_keys >= 5:
            return {
                "success": False,
                "error": "Maximum API keys limit reached (5). Please revoke an existing key."
            }

        # Generate secure API key
        prefix = f"arris_{key_type}_"
        raw_key = secrets.token_urlsafe(32)
        full_key = f"{prefix}{raw_key}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:20]  # Store prefix for identification
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expires_in_days)
        
        key_doc = {
            "id": f"APIKEY-{secrets.token_hex(6).upper()}",
            "creator_id": creator_id,
            "name": name,
            "key_type": key_type,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "status": ApiKeyStatus.ACTIVE.value,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_used_at": None,
            "usage_count": 0,
            "daily_usage": 0,
            "hourly_usage": 0,
            "last_usage_reset": now.isoformat()
        }
        
        await self.db.arris_api_keys.insert_one(key_doc)
        
        # Log key creation
        await self._log_api_activity(
            creator_id=creator_id,
            action="key_created",
            details={"key_id": key_doc["id"], "key_type": key_type}
        )
        
        logger.info(f"Generated API key {key_doc['id']} for creator {creator_id}")
        
        return {
            "success": True,
            "key_id": key_doc["id"],
            "api_key": full_key,  # Only returned once!
            "key_type": key_type,
            "name": name,
            "expires_at": expires_at.isoformat(),
            "warning": "Save this API key securely. It will not be shown again."
        }

    async def list_api_keys(self, creator_id: str) -> List[Dict[str, Any]]:
        """List all API keys for a creator (without the actual key values)."""
        keys = await self.db.arris_api_keys.find(
            {"creator_id": creator_id},
            {"_id": 0, "key_hash": 0}  # Exclude hash for security
        ).sort("created_at", -1).to_list(10)
        
        return keys

    async def get_api_key(self, creator_id: str, key_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific API key."""
        key = await self.db.arris_api_keys.find_one(
            {"id": key_id, "creator_id": creator_id},
            {"_id": 0, "key_hash": 0}
        )
        return key

    async def revoke_api_key(self, creator_id: str, key_id: str) -> Dict[str, Any]:
        """Revoke an API key."""
        result = await self.db.arris_api_keys.update_one(
            {"id": key_id, "creator_id": creator_id, "status": ApiKeyStatus.ACTIVE.value},
            {
                "$set": {
                    "status": ApiKeyStatus.REVOKED.value,
                    "revoked_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            await self._log_api_activity(
                creator_id=creator_id,
                action="key_revoked",
                details={"key_id": key_id}
            )
            return {"success": True, "message": "API key revoked successfully"}
        
        return {"success": False, "error": "API key not found or already revoked"}

    async def regenerate_api_key(self, creator_id: str, key_id: str) -> Dict[str, Any]:
        """Regenerate an API key (revoke old, create new with same name)."""
        # Get existing key details
        existing = await self.db.arris_api_keys.find_one(
            {"id": key_id, "creator_id": creator_id}
        )
        
        if not existing:
            return {"success": False, "error": "API key not found"}
        
        # Revoke the old key
        await self.revoke_api_key(creator_id, key_id)
        
        # Generate new key with same name and type
        return await self.generate_api_key(
            creator_id=creator_id,
            key_type=existing.get("key_type", ApiKeyType.LIVE.value),
            name=existing.get("name", "Regenerated Key")
        )

    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate an API key and return creator info if valid.
        Also checks rate limits.
        """
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find the key
        key_doc = await self.db.arris_api_keys.find_one(
            {"key_hash": key_hash},
            {"_id": 0}
        )
        
        if not key_doc:
            return {"valid": False, "error": "Invalid API key"}
        
        # Check status
        if key_doc.get("status") != ApiKeyStatus.ACTIVE.value:
            return {"valid": False, "error": f"API key is {key_doc.get('status')}"}
        
        # Check expiration
        expires_at = datetime.fromisoformat(key_doc["expires_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            # Mark as expired
            await self.db.arris_api_keys.update_one(
                {"id": key_doc["id"]},
                {"$set": {"status": ApiKeyStatus.EXPIRED.value}}
            )
            return {"valid": False, "error": "API key has expired"}
        
        # Check rate limits
        rate_check = await self._check_rate_limits(key_doc)
        if not rate_check["allowed"]:
            return {
                "valid": False,
                "error": rate_check["error"],
                "rate_limited": True,
                "retry_after": rate_check.get("retry_after")
            }
        
        return {
            "valid": True,
            "creator_id": key_doc["creator_id"],
            "key_id": key_doc["id"],
            "key_type": key_doc["key_type"],
            "rate_limits": {
                "hourly_remaining": RATE_LIMITS["requests_per_hour"] - key_doc.get("hourly_usage", 0),
                "daily_remaining": RATE_LIMITS["requests_per_day"] - key_doc.get("daily_usage", 0)
            }
        }

    async def _check_rate_limits(self, key_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        now = datetime.now(timezone.utc)
        last_reset = datetime.fromisoformat(
            key_doc.get("last_usage_reset", now.isoformat()).replace('Z', '+00:00')
        )
        
        # Reset counters if needed
        hours_since_reset = (now - last_reset).total_seconds() / 3600
        
        if hours_since_reset >= 24:
            # Reset both daily and hourly
            await self.db.arris_api_keys.update_one(
                {"id": key_doc["id"]},
                {
                    "$set": {
                        "daily_usage": 0,
                        "hourly_usage": 0,
                        "last_usage_reset": now.isoformat()
                    }
                }
            )
            return {"allowed": True}
        elif hours_since_reset >= 1:
            # Reset hourly only
            await self.db.arris_api_keys.update_one(
                {"id": key_doc["id"]},
                {"$set": {"hourly_usage": 0}}
            )
            key_doc["hourly_usage"] = 0
        
        # Check limits
        hourly_usage = key_doc.get("hourly_usage", 0)
        daily_usage = key_doc.get("daily_usage", 0)
        
        if hourly_usage >= RATE_LIMITS["requests_per_hour"]:
            return {
                "allowed": False,
                "error": f"Hourly rate limit exceeded ({RATE_LIMITS['requests_per_hour']} requests/hour)",
                "retry_after": 3600 - int((now - last_reset).total_seconds() % 3600)
            }
        
        if daily_usage >= RATE_LIMITS["requests_per_day"]:
            return {
                "allowed": False,
                "error": f"Daily rate limit exceeded ({RATE_LIMITS['requests_per_day']} requests/day)",
                "retry_after": 86400 - int((now - last_reset).total_seconds())
            }
        
        return {"allowed": True}

    async def _increment_usage(self, key_id: str):
        """Increment usage counters for an API key."""
        await self.db.arris_api_keys.update_one(
            {"id": key_id},
            {
                "$inc": {"usage_count": 1, "daily_usage": 1, "hourly_usage": 1},
                "$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}
            }
        )

    # ============== API CAPABILITIES ==============

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get available API capabilities and documentation."""
        return {
            "capabilities": API_CAPABILITIES,
            "rate_limits": RATE_LIMITS,
            "authentication": {
                "type": "Bearer Token",
                "header": "X-ARRIS-API-Key",
                "example": "X-ARRIS-API-Key: arris_live_xxxxx"
            },
            "documentation_url": "/api/elite/arris-api/docs"
        }

    async def get_api_docs(self) -> Dict[str, Any]:
        """Get full API documentation."""
        return {
            "title": "ARRIS API for Elite Creators",
            "version": "1.0.0",
            "description": "Direct programmatic access to ARRIS AI capabilities",
            "authentication": {
                "type": "API Key",
                "header": "X-ARRIS-API-Key",
                "description": "Include your API key in the X-ARRIS-API-Key header",
                "example": "curl -H 'X-ARRIS-API-Key: arris_live_xxxxx' https://api.hivehq.com/api/elite/arris-api/analyze"
            },
            "rate_limits": {
                "requests_per_hour": RATE_LIMITS["requests_per_hour"],
                "requests_per_day": RATE_LIMITS["requests_per_day"],
                "max_batch_size": RATE_LIMITS["max_batch_size"],
                "max_text_length": RATE_LIMITS["max_text_length"]
            },
            "endpoints": [
                {
                    "path": "/api/elite/arris-api/analyze",
                    "method": "POST",
                    "description": "Analyze text content for insights",
                    "request_body": {
                        "text": "string (required) - Text to analyze",
                        "analysis_type": "string (optional) - 'general', 'sentiment', 'content_ideas', 'strategy'",
                        "context": "object (optional) - Additional context for analysis"
                    },
                    "response": {
                        "request_id": "string - Unique request identifier",
                        "analysis": "object - Analysis results",
                        "processing_time_ms": "number - Processing time in milliseconds"
                    }
                },
                {
                    "path": "/api/elite/arris-api/insights",
                    "method": "POST",
                    "description": "Get AI-powered insights for proposals",
                    "request_body": {
                        "title": "string (required) - Proposal title",
                        "description": "string (required) - Proposal description",
                        "goals": "array (optional) - Project goals",
                        "platforms": "array (optional) - Target platforms"
                    },
                    "response": {
                        "request_id": "string",
                        "insights": "object - ARRIS insights",
                        "processing_time_ms": "number"
                    }
                },
                {
                    "path": "/api/elite/arris-api/content",
                    "method": "POST",
                    "description": "Generate content suggestions",
                    "request_body": {
                        "topic": "string (required) - Content topic",
                        "platform": "string (optional) - Target platform",
                        "content_type": "string (optional) - 'video', 'post', 'article', 'story'",
                        "count": "number (optional) - Number of suggestions (1-10)"
                    },
                    "response": {
                        "request_id": "string",
                        "suggestions": "array - Content suggestions",
                        "processing_time_ms": "number"
                    }
                },
                {
                    "path": "/api/elite/arris-api/chat",
                    "method": "POST",
                    "description": "Chat with ARRIS using your persona",
                    "request_body": {
                        "message": "string (required) - Your message",
                        "conversation_id": "string (optional) - Continue existing conversation",
                        "persona_id": "string (optional) - Use specific persona"
                    },
                    "response": {
                        "request_id": "string",
                        "response": "string - ARRIS response",
                        "conversation_id": "string - Conversation identifier",
                        "processing_time_ms": "number"
                    }
                },
                {
                    "path": "/api/elite/arris-api/batch",
                    "method": "POST",
                    "description": "Process multiple items in batch",
                    "request_body": {
                        "items": "array (required) - Array of analysis requests",
                        "analysis_type": "string (optional) - Type for all items"
                    },
                    "response": {
                        "request_id": "string",
                        "results": "array - Results for each item",
                        "total_processing_time_ms": "number"
                    }
                }
            ],
            "error_codes": {
                "400": "Bad Request - Invalid input",
                "401": "Unauthorized - Invalid or missing API key",
                "403": "Forbidden - API key doesn't have access",
                "429": "Too Many Requests - Rate limit exceeded",
                "500": "Internal Server Error"
            },
            "examples": {
                "analyze_text": {
                    "request": {
                        "text": "I want to create a YouTube channel about sustainable living",
                        "analysis_type": "strategy"
                    },
                    "response": {
                        "request_id": "REQ-ABC123",
                        "analysis": {
                            "summary": "Strong niche with growing interest...",
                            "opportunities": ["..."],
                            "recommendations": ["..."]
                        },
                        "processing_time_ms": 1234
                    }
                }
            }
        }

    # ============== API REQUEST PROCESSING ==============

    async def analyze_text(
        self,
        creator_id: str,
        key_id: str,
        text: str,
        analysis_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze text content using ARRIS."""
        import time
        start_time = time.time()
        request_id = f"REQ-{secrets.token_hex(6).upper()}"
        
        # Validate text length
        if len(text) > RATE_LIMITS["max_text_length"]:
            return {
                "success": False,
                "error": f"Text exceeds maximum length ({RATE_LIMITS['max_text_length']} characters)"
            }
        
        # Increment usage
        await self._increment_usage(key_id)
        
        try:
            # Get active persona for the creator
            persona_prompt = ""
            if self.persona_service:
                active_persona = await self.persona_service.get_active_persona(creator_id)
                if active_persona:
                    persona_prompt = self.persona_service.generate_persona_system_prompt(active_persona)
            
            # Build analysis prompt based on type
            analysis_prompts = {
                "general": "Provide a comprehensive analysis of this text, including key themes, insights, and actionable recommendations.",
                "sentiment": "Analyze the sentiment and emotional tone of this text. Identify positive, negative, and neutral aspects.",
                "content_ideas": "Based on this text, generate creative content ideas and angles that could be explored.",
                "strategy": "Provide strategic analysis including opportunities, challenges, and recommended next steps."
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
            
            # Use ARRIS service for analysis
            if self.arris_service:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                system_prompt = f"""You are ARRIS, an AI assistant for Creators Hive HQ.
{persona_prompt}

Your task: {prompt}

Provide your analysis in a structured JSON format with these fields:
- summary: Brief overview (2-3 sentences)
- key_points: Array of main points
- insights: Array of deeper insights
- recommendations: Array of actionable recommendations
- confidence_score: 0-100 indicating analysis confidence"""
                
                chat = LlmChat(
                    api_key=self.arris_service.api_key,
                    session_id=f"arris-api-{request_id}",
                    system_message=system_prompt
                ).with_model("openai", "gpt-4o")
                
                user_message = UserMessage(text=f"Analyze this text:\n\n{text}\n\nContext: {json.dumps(context or {})}")
                response = await chat.send_async(message=user_message)
                
                # Parse response
                try:
                    analysis = json.loads(response.content)
                except json.JSONDecodeError:
                    analysis = {
                        "summary": response.content[:500],
                        "raw_response": response.content
                    }
            else:
                # Fallback analysis
                analysis = self._generate_fallback_analysis(text, analysis_type)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Log the request
            await self._log_api_request(
                creator_id=creator_id,
                key_id=key_id,
                request_id=request_id,
                endpoint="analyze",
                status=RequestStatus.COMPLETED.value,
                processing_time_ms=processing_time
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "analysis_type": analysis_type,
                "analysis": analysis,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Analysis error for {creator_id}: {e}")
            await self._log_api_request(
                creator_id=creator_id,
                key_id=key_id,
                request_id=request_id,
                endpoint="analyze",
                status=RequestStatus.FAILED.value,
                error=str(e)
            )
            return {"success": False, "error": str(e), "request_id": request_id}

    async def generate_insights(
        self,
        creator_id: str,
        key_id: str,
        title: str,
        description: str,
        goals: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate proposal insights using ARRIS."""
        import time
        start_time = time.time()
        request_id = f"REQ-{secrets.token_hex(6).upper()}"
        
        await self._increment_usage(key_id)
        
        try:
            # Build proposal object
            proposal = {
                "id": request_id,
                "title": title,
                "description": description,
                "goals": goals or [],
                "platforms": platforms or []
            }
            
            # Use ARRIS service
            if self.arris_service:
                insights = await self.arris_service.generate_project_insights(
                    proposal=proposal,
                    processing_speed="fast"  # Elite users get fast processing
                )
            else:
                insights = self._generate_fallback_insights(proposal)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            await self._log_api_request(
                creator_id=creator_id,
                key_id=key_id,
                request_id=request_id,
                endpoint="insights",
                status=RequestStatus.COMPLETED.value,
                processing_time_ms=processing_time
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "insights": insights,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Insights error for {creator_id}: {e}")
            return {"success": False, "error": str(e), "request_id": request_id}

    async def generate_content_suggestions(
        self,
        creator_id: str,
        key_id: str,
        topic: str,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        count: int = 5
    ) -> Dict[str, Any]:
        """Generate content suggestions."""
        import time
        start_time = time.time()
        request_id = f"REQ-{secrets.token_hex(6).upper()}"
        
        await self._increment_usage(key_id)
        
        try:
            count = min(max(1, count), 10)  # Clamp between 1-10
            
            if self.arris_service:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                prompt = f"""Generate {count} creative content suggestions for:
Topic: {topic}
Platform: {platform or 'any'}
Content Type: {content_type or 'any'}

Return as JSON array with each suggestion having:
- title: Catchy title
- description: Brief description
- hook: Attention-grabbing hook
- key_points: Array of main points to cover
- estimated_engagement: 'high', 'medium', or 'low'
- best_time_to_post: Suggested posting time"""
                
                chat = LlmChat(
                    api_key=self.arris_service.api_key,
                    session_id=f"arris-content-{request_id}",
                    system_message="You are ARRIS, a creative content strategist. Generate engaging content ideas."
                ).with_model("openai", "gpt-4o")
                
                user_message = UserMessage(text=prompt)
                response = await chat.send_async(message=user_message)
                
                try:
                    suggestions = json.loads(response.content)
                except json.JSONDecodeError:
                    suggestions = [{"raw_response": response.content}]
            else:
                suggestions = self._generate_fallback_content(topic, count)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            await self._log_api_request(
                creator_id=creator_id,
                key_id=key_id,
                request_id=request_id,
                endpoint="content",
                status=RequestStatus.COMPLETED.value,
                processing_time_ms=processing_time
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "topic": topic,
                "suggestions": suggestions,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Content suggestions error for {creator_id}: {e}")
            return {"success": False, "error": str(e), "request_id": request_id}

    async def chat_with_arris(
        self,
        creator_id: str,
        key_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        persona_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Chat with ARRIS using creator's persona."""
        import time
        start_time = time.time()
        request_id = f"REQ-{secrets.token_hex(6).upper()}"
        
        if not conversation_id:
            conversation_id = f"CONV-{secrets.token_hex(6).upper()}"
        
        await self._increment_usage(key_id)
        
        try:
            # Get persona
            persona_prompt = ""
            if self.persona_service:
                if persona_id:
                    persona = await self.persona_service.get_persona(creator_id, persona_id)
                else:
                    persona = await self.persona_service.get_active_persona(creator_id)
                
                if persona:
                    persona_prompt = self.persona_service.generate_persona_system_prompt(persona)
            
            # Get conversation history
            history = await self.db.arris_api_conversations.find(
                {"conversation_id": conversation_id, "creator_id": creator_id}
            ).sort("created_at", 1).to_list(20)
            
            # Build conversation context
            history_text = "\n".join([
                f"User: {h['user_message']}\nARRIS: {h['arris_response']}"
                for h in history[-5:]  # Last 5 exchanges
            ])
            
            if self.arris_service:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                system_prompt = f"""You are ARRIS, an AI assistant for Creators Hive HQ.
{persona_prompt}

You're having a conversation with a creator. Be helpful, encouraging, and provide actionable advice.
{f'Previous conversation: {history_text}' if history_text else ''}"""
                
                chat = LlmChat(
                    api_key=self.arris_service.api_key,
                    session_id=f"arris-chat-{conversation_id}",
                    system_message=system_prompt
                ).with_model("openai", "gpt-4o")
                
                user_message = UserMessage(text=message)
                response = await chat.send_async(message=user_message)
                
                arris_response = response.content
            else:
                arris_response = f"Thank you for your message about '{message[:50]}...'. As ARRIS, I'm here to help you succeed as a creator. How can I assist you further?"
            
            # Store conversation
            await self.db.arris_api_conversations.insert_one({
                "conversation_id": conversation_id,
                "creator_id": creator_id,
                "user_message": message,
                "arris_response": arris_response,
                "persona_id": persona_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            processing_time = int((time.time() - start_time) * 1000)
            
            await self._log_api_request(
                creator_id=creator_id,
                key_id=key_id,
                request_id=request_id,
                endpoint="chat",
                status=RequestStatus.COMPLETED.value,
                processing_time_ms=processing_time
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "conversation_id": conversation_id,
                "response": arris_response,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Chat error for {creator_id}: {e}")
            return {"success": False, "error": str(e), "request_id": request_id}

    async def batch_analyze(
        self,
        creator_id: str,
        key_id: str,
        items: List[Dict[str, Any]],
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Process multiple items in batch."""
        import time
        start_time = time.time()
        request_id = f"BATCH-{secrets.token_hex(6).upper()}"
        
        # Validate batch size
        if len(items) > RATE_LIMITS["max_batch_size"]:
            return {
                "success": False,
                "error": f"Batch size exceeds maximum ({RATE_LIMITS['max_batch_size']} items)"
            }
        
        results = []
        for idx, item in enumerate(items):
            text = item.get("text", "")
            item_type = item.get("analysis_type", analysis_type)
            
            result = await self.analyze_text(
                creator_id=creator_id,
                key_id=key_id,
                text=text,
                analysis_type=item_type,
                context=item.get("context")
            )
            
            results.append({
                "index": idx,
                "success": result.get("success"),
                "analysis": result.get("analysis") if result.get("success") else None,
                "error": result.get("error") if not result.get("success") else None
            })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "request_id": request_id,
            "total_items": len(items),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results,
            "total_processing_time_ms": processing_time
        }

    # ============== USAGE & ANALYTICS ==============

    async def get_usage_stats(self, creator_id: str, days: int = 30) -> Dict[str, Any]:
        """Get API usage statistics for a creator."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all keys
        keys = await self.list_api_keys(creator_id)
        
        # Get request logs
        pipeline = [
            {
                "$match": {
                    "creator_id": creator_id,
                    "created_at": {"$gte": start_date.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$substr": ["$created_at", 0, 10]},
                        "endpoint": "$endpoint"
                    },
                    "count": {"$sum": 1},
                    "avg_time": {"$avg": "$processing_time_ms"}
                }
            },
            {"$sort": {"_id.date": 1}}
        ]
        
        daily_stats = await self.db.arris_api_requests.aggregate(pipeline).to_list(100)
        
        # Get totals by endpoint
        endpoint_pipeline = [
            {"$match": {"creator_id": creator_id}},
            {
                "$group": {
                    "_id": "$endpoint",
                    "total_requests": {"$sum": 1},
                    "avg_processing_time": {"$avg": "$processing_time_ms"},
                    "success_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            }
        ]
        
        endpoint_stats = await self.db.arris_api_requests.aggregate(endpoint_pipeline).to_list(10)
        
        # Calculate totals
        total_requests = sum(k.get("usage_count", 0) for k in keys)
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "active_keys": len([k for k in keys if k.get("status") == "active"]),
            "rate_limits": RATE_LIMITS,
            "daily_breakdown": [
                {
                    "date": s["_id"]["date"],
                    "endpoint": s["_id"]["endpoint"],
                    "requests": s["count"],
                    "avg_time_ms": round(s["avg_time"], 2) if s["avg_time"] else 0
                }
                for s in daily_stats
            ],
            "by_endpoint": [
                {
                    "endpoint": s["_id"],
                    "total_requests": s["total_requests"],
                    "success_rate": round(s["success_count"] / max(1, s["total_requests"]) * 100, 1),
                    "avg_time_ms": round(s["avg_processing_time"], 2) if s["avg_processing_time"] else 0
                }
                for s in endpoint_stats
            ],
            "keys": keys
        }

    async def get_request_history(
        self,
        creator_id: str,
        limit: int = 50,
        endpoint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent API request history."""
        query = {"creator_id": creator_id}
        if endpoint:
            query["endpoint"] = endpoint
        
        requests = await self.db.arris_api_requests.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(limit)
        
        return requests

    # ============== HELPER METHODS ==============

    def _generate_fallback_analysis(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """Generate fallback analysis when ARRIS is unavailable."""
        word_count = len(text.split())
        
        return {
            "summary": f"Analysis of {word_count} words of content.",
            "key_points": [
                "Text content received for analysis",
                f"Analysis type: {analysis_type}",
                "AI service temporarily unavailable for full analysis"
            ],
            "insights": ["Please try again later for full AI-powered insights"],
            "recommendations": ["Consider breaking content into smaller sections for better analysis"],
            "confidence_score": 50,
            "note": "Fallback analysis - AI service unavailable"
        }

    def _generate_fallback_insights(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback insights when ARRIS is unavailable."""
        return {
            "summary": f"Project proposal: {proposal.get('title', 'Untitled')}",
            "strengths": ["Proposal submitted successfully"],
            "risks": ["Full AI analysis temporarily unavailable"],
            "recommendations": ["Try again later for complete insights"],
            "estimated_complexity": "Medium",
            "note": "Fallback insights - AI service unavailable"
        }

    def _generate_fallback_content(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """Generate fallback content suggestions."""
        return [
            {
                "title": f"Content Idea {i+1} for {topic}",
                "description": f"A content piece exploring {topic}",
                "hook": f"Have you ever wondered about {topic}?",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "estimated_engagement": "medium",
                "best_time_to_post": "9:00 AM",
                "note": "Fallback suggestion - AI service unavailable"
            }
            for i in range(count)
        ]

    async def _log_api_activity(
        self,
        creator_id: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Log API activity."""
        log_entry = {
            "creator_id": creator_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.arris_api_activity_log.insert_one(log_entry)

    async def _log_api_request(
        self,
        creator_id: str,
        key_id: str,
        request_id: str,
        endpoint: str,
        status: str,
        processing_time_ms: int = 0,
        error: str = None
    ) -> None:
        """Log an API request."""
        log_entry = {
            "request_id": request_id,
            "creator_id": creator_id,
            "key_id": key_id,
            "endpoint": endpoint,
            "status": status,
            "processing_time_ms": processing_time_ms,
            "error": error,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.arris_api_requests.insert_one(log_entry)


# Export constants
AVAILABLE_CAPABILITIES = API_CAPABILITIES

# Singleton instance
arris_api_service: Optional[ArrisApiService] = None
