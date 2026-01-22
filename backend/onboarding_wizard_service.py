"""
Creators Hive HQ - Smart Onboarding Wizard Service
Phase 4 Module D - D1: Smart Onboarding Wizard with ARRIS Personalization

Features:
- Multi-step guided onboarding process
- ARRIS AI personalization at each step
- Progress tracking and persistence
- Personalized recommendations
- Onboarding completion rewards
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

logger = logging.getLogger(__name__)


# ============== ONBOARDING STEPS CONFIGURATION ==============

ONBOARDING_STEPS = [
    {
        "step_id": "welcome",
        "step_number": 1,
        "title": "Welcome to Creators Hive HQ",
        "subtitle": "Let's get to know you better",
        "description": "We'll personalize your experience based on your creator journey",
        "required": True,
        "arris_enabled": True,
        "fields": []
    },
    {
        "step_id": "profile",
        "step_number": 2,
        "title": "Your Creator Profile",
        "subtitle": "Tell us about yourself",
        "description": "Help ARRIS understand your brand and style",
        "required": True,
        "arris_enabled": True,
        "fields": [
            {"name": "display_name", "type": "text", "label": "Display Name", "required": True, "placeholder": "How should we call you?"},
            {"name": "bio", "type": "textarea", "label": "Short Bio", "required": False, "placeholder": "Tell us about yourself in a few sentences...", "max_length": 500},
            {"name": "website", "type": "url", "label": "Website/Portfolio", "required": False, "placeholder": "https://"},
            {"name": "profile_image_url", "type": "url", "label": "Profile Image URL", "required": False, "placeholder": "Link to your profile image"}
        ]
    },
    {
        "step_id": "platforms",
        "step_number": 3,
        "title": "Your Platforms",
        "subtitle": "Where do you create content?",
        "description": "Select all platforms where you're active",
        "required": True,
        "arris_enabled": True,
        "fields": [
            {"name": "primary_platform", "type": "select", "label": "Primary Platform", "required": True, "options": ["youtube", "instagram", "tiktok", "twitter", "linkedin", "podcast", "blog", "newsletter", "twitch", "other"]},
            {"name": "secondary_platforms", "type": "multiselect", "label": "Other Platforms", "required": False, "options": ["youtube", "instagram", "tiktok", "twitter", "linkedin", "podcast", "blog", "newsletter", "twitch", "patreon", "courses", "other"]},
            {"name": "follower_count", "type": "select", "label": "Total Audience Size", "required": True, "options": ["0-1K", "1K-10K", "10K-50K", "50K-100K", "100K-500K", "500K-1M", "1M+"]}
        ]
    },
    {
        "step_id": "niche",
        "step_number": 4,
        "title": "Your Niche & Expertise",
        "subtitle": "What's your content about?",
        "description": "Help us understand your content focus",
        "required": True,
        "arris_enabled": True,
        "fields": [
            {"name": "primary_niche", "type": "select", "label": "Primary Niche", "required": True, "options": ["business", "tech", "finance", "health", "lifestyle", "food", "gaming", "education", "entertainment", "art", "music", "fashion", "parenting", "personal_development", "other"]},
            {"name": "sub_niches", "type": "text", "label": "Specific Topics", "required": False, "placeholder": "e.g., SaaS marketing, home workouts, vegan recipes"},
            {"name": "unique_angle", "type": "textarea", "label": "Your Unique Angle", "required": False, "placeholder": "What makes your content different?", "max_length": 300}
        ]
    },
    {
        "step_id": "goals",
        "step_number": 5,
        "title": "Your Goals",
        "subtitle": "What do you want to achieve?",
        "description": "ARRIS will help you reach these goals",
        "required": True,
        "arris_enabled": True,
        "fields": [
            {"name": "primary_goal", "type": "select", "label": "Primary Goal", "required": True, "options": ["grow_audience", "monetize", "brand_deals", "launch_product", "build_community", "improve_content", "work_life_balance", "other"]},
            {"name": "revenue_goal", "type": "select", "label": "Revenue Goal (Next 12 months)", "required": False, "options": ["not_focused", "0-1K", "1K-5K", "5K-10K", "10K-25K", "25K-50K", "50K-100K", "100K+"]},
            {"name": "biggest_challenge", "type": "textarea", "label": "Biggest Challenge", "required": True, "placeholder": "What's your #1 obstacle right now?", "max_length": 500}
        ]
    },
    {
        "step_id": "arris_intro",
        "step_number": 6,
        "title": "Meet ARRIS",
        "subtitle": "Your AI-powered creator assistant",
        "description": "ARRIS learns from your journey and provides personalized insights",
        "required": True,
        "arris_enabled": True,
        "fields": [
            {"name": "arris_communication_style", "type": "select", "label": "Preferred Communication Style", "required": True, "options": ["professional", "casual", "motivational", "direct", "detailed"]},
            {"name": "arris_focus_areas", "type": "multiselect", "label": "What should ARRIS focus on?", "required": True, "options": ["content_ideas", "growth_strategies", "monetization", "analytics", "productivity", "trends", "community"]},
            {"name": "notification_preference", "type": "select", "label": "How often should ARRIS reach out?", "required": True, "options": ["daily", "weekly", "on_demand", "important_only"]}
        ]
    },
    {
        "step_id": "complete",
        "step_number": 7,
        "title": "You're All Set!",
        "subtitle": "Welcome to the Hive",
        "description": "Your personalized dashboard is ready",
        "required": True,
        "arris_enabled": True,
        "fields": []
    }
]

GOAL_LABELS = {
    "grow_audience": "Grow My Audience",
    "monetize": "Monetize My Content",
    "brand_deals": "Land Brand Deals",
    "launch_product": "Launch a Product/Course",
    "build_community": "Build a Community",
    "improve_content": "Improve Content Quality",
    "work_life_balance": "Better Work-Life Balance",
    "other": "Other"
}

NICHE_LABELS = {
    "business": "Business & Entrepreneurship",
    "tech": "Tech & Software",
    "finance": "Finance & Investing",
    "health": "Health & Fitness",
    "lifestyle": "Lifestyle & Travel",
    "food": "Food & Cooking",
    "gaming": "Gaming",
    "education": "Education & Learning",
    "entertainment": "Entertainment",
    "art": "Art & Design",
    "music": "Music",
    "fashion": "Fashion & Beauty",
    "parenting": "Parenting & Family",
    "personal_development": "Personal Development",
    "other": "Other"
}

PLATFORM_LABELS = {
    "youtube": "YouTube",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "twitter": "Twitter/X",
    "linkedin": "LinkedIn",
    "podcast": "Podcast",
    "blog": "Blog/Website",
    "newsletter": "Newsletter",
    "twitch": "Twitch",
    "patreon": "Patreon/Membership",
    "courses": "Online Courses",
    "other": "Other"
}


class SmartOnboardingWizard:
    """
    Smart Onboarding Wizard with ARRIS AI Personalization.
    
    Features:
    - Multi-step guided onboarding
    - Progress persistence
    - ARRIS AI personalization at key steps
    - Personalized recommendations
    - Completion rewards and badges
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, llm_client=None):
        self.db = db
        self.llm_client = llm_client
        self.steps = ONBOARDING_STEPS
        
    async def get_onboarding_status(self, creator_id: str) -> Dict[str, Any]:
        """
        Get the current onboarding status for a creator.
        
        Returns:
            Current step, progress percentage, and completion status
        """
        # Get or create onboarding record
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not onboarding:
            # Initialize new onboarding
            onboarding = {
                "id": f"ONBOARD-{uuid.uuid4().hex[:10]}",
                "creator_id": creator_id,
                "current_step": 1,
                "completed_steps": [],
                "step_data": {},
                "arris_insights": {},
                "started_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "completion_percentage": 0,
                "personalization_profile": {},
                "rewards_earned": []
            }
            await self.db.creator_onboarding.insert_one(onboarding)
        
        # Calculate progress
        total_steps = len([s for s in self.steps if s["required"]])
        completed = len(onboarding.get("completed_steps", []))
        progress = int((completed / total_steps) * 100)
        
        return {
            "onboarding_id": onboarding.get("id"),
            "creator_id": creator_id,
            "current_step": onboarding.get("current_step", 1),
            "completed_steps": onboarding.get("completed_steps", []),
            "completion_percentage": progress,
            "is_complete": onboarding.get("completed_at") is not None,
            "started_at": onboarding.get("started_at"),
            "last_activity": onboarding.get("last_activity"),
            "rewards_earned": onboarding.get("rewards_earned", [])
        }
    
    async def get_step_details(self, step_number: int, creator_id: str) -> Dict[str, Any]:
        """
        Get details for a specific onboarding step with ARRIS personalization.
        
        Args:
            step_number: The step number (1-7)
            creator_id: The creator's ID
            
        Returns:
            Step details with fields and ARRIS context
        """
        # Find the step
        step = next((s for s in self.steps if s["step_number"] == step_number), None)
        if not step:
            return {"error": "Invalid step number"}
        
        # Get creator's onboarding data for context
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        # Get creator info
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0, "name": 1, "platforms": 1, "niche": 1}
        )
        
        step_data = onboarding.get("step_data", {}) if onboarding else {}
        
        # Generate ARRIS context for this step
        arris_context = None
        if step["arris_enabled"] and self.llm_client:
            arris_context = await self._generate_step_arris_context(
                step=step,
                creator=creator,
                previous_data=step_data
            )
        
        return {
            "step": step,
            "saved_data": step_data.get(step["step_id"], {}),
            "arris_context": arris_context,
            "creator_name": creator.get("name") if creator else None,
            "navigation": {
                "can_go_back": step_number > 1,
                "can_skip": not step["required"],
                "total_steps": len(self.steps),
                "is_last_step": step_number == len(self.steps)
            }
        }
    
    async def save_step_data(
        self,
        creator_id: str,
        step_number: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save data from a completed step and advance to next.
        
        Args:
            creator_id: The creator's ID
            step_number: The completed step number
            data: The data collected in this step
            
        Returns:
            Updated onboarding status with ARRIS insights
        """
        step = next((s for s in self.steps if s["step_number"] == step_number), None)
        if not step:
            return {"error": "Invalid step number"}
        
        step_id = step["step_id"]
        now = datetime.now(timezone.utc).isoformat()
        
        # Get current onboarding
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not onboarding:
            return {"error": "Onboarding not initialized"}
        
        # Update step data
        step_data = onboarding.get("step_data", {})
        step_data[step_id] = data
        
        # Add to completed steps if not already
        completed_steps = onboarding.get("completed_steps", [])
        if step_id not in completed_steps:
            completed_steps.append(step_id)
        
        # Calculate next step
        next_step = step_number + 1 if step_number < len(self.steps) else step_number
        
        # Generate ARRIS insight for this step
        arris_insight = None
        if step["arris_enabled"] and self.llm_client and step_id not in ["welcome", "complete"]:
            arris_insight = await self._generate_step_insight(
                step=step,
                data=data,
                all_data=step_data
            )
        
        # Store ARRIS insight
        arris_insights = onboarding.get("arris_insights", {})
        if arris_insight:
            arris_insights[step_id] = arris_insight
        
        # Check if onboarding is complete
        is_complete = step_id == "complete"
        completed_at = now if is_complete else None
        
        # Calculate progress
        total_steps = len([s for s in self.steps if s["required"]])
        progress = int((len(completed_steps) / total_steps) * 100)
        
        # Update personalization profile if completing
        personalization = onboarding.get("personalization_profile", {})
        if is_complete:
            personalization = await self._build_personalization_profile(step_data)
        
        # Award completion reward
        rewards = onboarding.get("rewards_earned", [])
        if is_complete and "onboarding_complete" not in [r.get("type") for r in rewards]:
            rewards.append({
                "type": "onboarding_complete",
                "name": "Hive Newcomer",
                "description": "Completed the onboarding wizard",
                "earned_at": now,
                "points": 100
            })
        
        # Update database
        await self.db.creator_onboarding.update_one(
            {"creator_id": creator_id},
            {"$set": {
                "current_step": next_step,
                "completed_steps": completed_steps,
                "step_data": step_data,
                "arris_insights": arris_insights,
                "last_activity": now,
                "completed_at": completed_at,
                "completion_percentage": progress,
                "personalization_profile": personalization,
                "rewards_earned": rewards
            }}
        )
        
        # Update creator profile with relevant data
        if step_id == "profile":
            await self._update_creator_profile(creator_id, data)
        elif step_id == "platforms":
            await self._update_creator_platforms(creator_id, data)
        elif step_id == "arris_intro":
            await self._update_arris_preferences(creator_id, data)
        
        # If complete, trigger post-onboarding setup
        if is_complete:
            await self._complete_onboarding(creator_id, step_data, personalization)
        
        return {
            "success": True,
            "step_completed": step_id,
            "next_step": next_step,
            "completion_percentage": progress,
            "is_complete": is_complete,
            "arris_insight": arris_insight,
            "reward_earned": rewards[-1] if is_complete else None
        }
    
    async def _generate_step_arris_context(
        self,
        step: Dict,
        creator: Optional[Dict],
        previous_data: Dict
    ) -> Dict[str, Any]:
        """Generate ARRIS personalized context for a step"""
        step_id = step["step_id"]
        creator_name = creator.get("name", "Creator") if creator else "Creator"
        
        # Build context based on step
        if step_id == "welcome":
            return {
                "greeting": f"Welcome to Creators Hive HQ, {creator_name}! 👋",
                "message": "I'm ARRIS, your AI-powered creator assistant. Over the next few minutes, I'll learn about you so I can provide personalized insights, growth strategies, and support for your creator journey.",
                "tips": [
                    "Take your time - there's no rush",
                    "Be honest about your challenges - it helps me help you",
                    "You can always update this info later"
                ]
            }
        
        elif step_id == "profile":
            return {
                "message": f"Let's create your creator profile, {creator_name}.",
                "why_important": "Your profile helps brands and collaborators discover you, and helps me understand your brand voice.",
                "tips": [
                    "Choose a display name that's recognizable across platforms",
                    "Your bio should capture your unique value proposition"
                ]
            }
        
        elif step_id == "platforms":
            return {
                "message": "Where does your content live?",
                "why_important": "Understanding your platform mix helps me provide platform-specific strategies and identify cross-promotion opportunities.",
                "tips": [
                    "Select your primary platform - where you focus most of your effort",
                    "Include all platforms where you post regularly"
                ]
            }
        
        elif step_id == "niche":
            platform = previous_data.get("platforms", {}).get("primary_platform", "your platforms")
            platform_label = PLATFORM_LABELS.get(platform, platform)
            return {
                "message": f"What's your content niche on {platform_label}?",
                "why_important": "Your niche determines your target audience, brand partnership opportunities, and growth strategies.",
                "tips": [
                    "Be specific - 'personal finance for millennials' is better than just 'finance'",
                    "Think about what makes your perspective unique"
                ]
            }
        
        elif step_id == "goals":
            niche = previous_data.get("niche", {}).get("primary_niche", "")
            niche_label = NICHE_LABELS.get(niche, niche)
            return {
                "message": f"What are you working towards in {niche_label}?",
                "why_important": "Your goals shape every recommendation I make. I'll track your progress and celebrate wins with you.",
                "tips": [
                    "Focus on ONE primary goal - spreading focus dilutes results",
                    "Be specific about your biggest challenge - that's where I can help most"
                ]
            }
        
        elif step_id == "arris_intro":
            goal = previous_data.get("goals", {}).get("primary_goal", "")
            goal_label = GOAL_LABELS.get(goal, goal)
            return {
                "message": f"Let's personalize how I help you {goal_label.lower()}.",
                "capabilities": [
                    "📊 Analyze your content performance patterns",
                    "💡 Generate content ideas tailored to your niche",
                    "📈 Provide growth strategies based on your platforms",
                    "🎯 Track progress towards your goals",
                    "🔔 Send timely insights when I spot opportunities"
                ],
                "tips": [
                    "Choose how you like to receive feedback",
                    "Select focus areas that matter most to you"
                ]
            }
        
        elif step_id == "complete":
            goal = previous_data.get("goals", {}).get("primary_goal", "")
            platform = previous_data.get("platforms", {}).get("primary_platform", "")
            return {
                "message": f"You're all set, {creator_name}! 🎉",
                "next_steps": [
                    "Explore your personalized dashboard",
                    "Create your first project proposal",
                    "Check out ARRIS insights in your feed"
                ],
                "first_insight": f"Based on your goal to {GOAL_LABELS.get(goal, goal).lower()}, I'll be watching for opportunities on {PLATFORM_LABELS.get(platform, platform)} and sharing relevant strategies."
            }
        
        return {"message": "Let's continue your onboarding journey."}
    
    async def _generate_step_insight(
        self,
        step: Dict,
        data: Dict,
        all_data: Dict
    ) -> Optional[Dict[str, Any]]:
        """Generate ARRIS AI insight based on step data"""
        if not self.llm_client:
            return None
        
        step_id = step["step_id"]
        
        try:
            # Build prompt based on step
            if step_id == "profile":
                prompt = f"""A creator just completed their profile:
- Display Name: {data.get('display_name', 'Not provided')}
- Bio: {data.get('bio', 'Not provided')}

Provide a brief, encouraging one-sentence observation about their brand positioning. Keep it under 50 words."""

            elif step_id == "platforms":
                primary = PLATFORM_LABELS.get(data.get('primary_platform', ''), data.get('primary_platform', ''))
                secondary = [PLATFORM_LABELS.get(p, p) for p in data.get('secondary_platforms', [])]
                audience = data.get('follower_count', '')
                
                prompt = f"""A creator shared their platform info:
- Primary Platform: {primary}
- Secondary Platforms: {', '.join(secondary) if secondary else 'None'}
- Audience Size: {audience}

Provide one specific platform-synergy tip in under 50 words."""

            elif step_id == "niche":
                niche = NICHE_LABELS.get(data.get('primary_niche', ''), data.get('primary_niche', ''))
                topics = data.get('sub_niches', '')
                angle = data.get('unique_angle', '')
                
                prompt = f"""A creator defined their niche:
- Niche: {niche}
- Specific Topics: {topics or 'Not specified'}
- Unique Angle: {angle or 'Not specified'}

Provide one observation about niche positioning or differentiation opportunity in under 50 words."""

            elif step_id == "goals":
                goal = GOAL_LABELS.get(data.get('primary_goal', ''), data.get('primary_goal', ''))
                revenue = data.get('revenue_goal', '')
                challenge = data.get('biggest_challenge', '')
                
                prompt = f"""A creator shared their goals:
- Primary Goal: {goal}
- Revenue Target: {revenue or 'Not focused on revenue'}
- Biggest Challenge: {challenge}

Provide one actionable suggestion to address their challenge in under 60 words. Be specific and encouraging."""

            elif step_id == "arris_intro":
                style = data.get('arris_communication_style', '')
                focus = data.get('arris_focus_areas', [])
                
                prompt = f"""A creator customized their AI assistant preferences:
- Communication Style: {style}
- Focus Areas: {', '.join(focus)}

Provide a brief statement about how you'll help them based on these preferences. Keep it under 40 words and match the communication style."""

            else:
                return None
            
            # Call LLM
            response = await self.llm_client.chat(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are ARRIS, a helpful AI assistant for content creators. Be concise, specific, and encouraging. Never use more than 60 words."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            insight_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "step": step_id,
                "insight": insight_text.strip(),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating ARRIS insight: {e}")
            return None
    
    async def _build_personalization_profile(self, step_data: Dict) -> Dict[str, Any]:
        """Build personalization profile from onboarding data"""
        profile_data = step_data.get("profile", {})
        platform_data = step_data.get("platforms", {})
        niche_data = step_data.get("niche", {})
        goals_data = step_data.get("goals", {})
        arris_data = step_data.get("arris_intro", {})
        
        return {
            "display_name": profile_data.get("display_name"),
            "primary_platform": platform_data.get("primary_platform"),
            "all_platforms": [platform_data.get("primary_platform")] + platform_data.get("secondary_platforms", []),
            "audience_size": platform_data.get("follower_count"),
            "primary_niche": niche_data.get("primary_niche"),
            "sub_niches": niche_data.get("sub_niches"),
            "unique_angle": niche_data.get("unique_angle"),
            "primary_goal": goals_data.get("primary_goal"),
            "revenue_goal": goals_data.get("revenue_goal"),
            "biggest_challenge": goals_data.get("biggest_challenge"),
            "arris_style": arris_data.get("arris_communication_style"),
            "arris_focus": arris_data.get("arris_focus_areas", []),
            "notification_pref": arris_data.get("notification_preference"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _update_creator_profile(self, creator_id: str, data: Dict):
        """Update creator's main profile with onboarding data"""
        update_fields = {}
        if data.get("display_name"):
            update_fields["display_name"] = data["display_name"]
        if data.get("bio"):
            update_fields["bio"] = data["bio"]
        if data.get("website"):
            update_fields["website"] = data["website"]
        if data.get("profile_image_url"):
            update_fields["profile_image_url"] = data["profile_image_url"]
        
        if update_fields:
            update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.db.creators.update_one(
                {"id": creator_id},
                {"$set": update_fields}
            )
    
    async def _update_creator_platforms(self, creator_id: str, data: Dict):
        """Update creator's platform information"""
        platforms = [data.get("primary_platform")] if data.get("primary_platform") else []
        platforms.extend(data.get("secondary_platforms", []))
        platforms = list(set(platforms))  # Remove duplicates
        
        update_fields = {
            "platforms": platforms,
            "primary_platform": data.get("primary_platform"),
            "audience_size": data.get("follower_count"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": update_fields}
        )
    
    async def _update_arris_preferences(self, creator_id: str, data: Dict):
        """Update ARRIS preferences for the creator"""
        preferences = {
            "communication_style": data.get("arris_communication_style"),
            "focus_areas": data.get("arris_focus_areas", []),
            "notification_preference": data.get("notification_preference"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.arris_preferences.update_one(
            {"creator_id": creator_id},
            {"$set": preferences},
            upsert=True
        )
    
    async def _complete_onboarding(
        self,
        creator_id: str,
        step_data: Dict,
        personalization: Dict
    ):
        """Handle post-onboarding completion tasks"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Update creator status
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "onboarding_complete": True,
                "onboarding_completed_at": now,
                "personalization_profile": personalization
            }}
        )
        
        # Store initial ARRIS memory
        initial_memory = {
            "id": f"MEM-ONBOARD-{uuid.uuid4().hex[:10]}",
            "creator_id": creator_id,
            "memory_type": "onboarding",
            "content": {
                "event": "onboarding_complete",
                "profile": personalization,
                "summary": f"Creator completed onboarding. Primary goal: {personalization.get('primary_goal')}. Primary platform: {personalization.get('primary_platform')}. Challenge: {personalization.get('biggest_challenge')}"
            },
            "importance": 0.9,
            "tags": ["onboarding", "profile", personalization.get("primary_goal", ""), personalization.get("primary_niche", "")],
            "recall_count": 0,
            "created_at": now
        }
        await self.db.arris_memories.insert_one(initial_memory)
        
        # Log completion event
        event = {
            "id": f"EVT-{uuid.uuid4().hex[:10]}",
            "type": "onboarding_complete",
            "creator_id": creator_id,
            "data": {
                "personalization": personalization,
                "duration_estimate": "5-10 minutes"
            },
            "created_at": now
        }
        await self.db.webhook_events.insert_one(event)
    
    async def get_personalization_summary(self, creator_id: str) -> Dict[str, Any]:
        """Get the personalization summary for a creator"""
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not onboarding:
            return {"error": "Onboarding not found", "onboarding_required": True}
        
        if not onboarding.get("completed_at"):
            return {
                "onboarding_complete": False,
                "completion_percentage": onboarding.get("completion_percentage", 0),
                "current_step": onboarding.get("current_step", 1)
            }
        
        profile = onboarding.get("personalization_profile", {})
        insights = onboarding.get("arris_insights", {})
        
        return {
            "onboarding_complete": True,
            "personalization": profile,
            "arris_insights": insights,
            "rewards": onboarding.get("rewards_earned", []),
            "completed_at": onboarding.get("completed_at")
        }
    
    async def skip_onboarding(self, creator_id: str) -> Dict[str, Any]:
        """Allow creator to skip remaining onboarding steps"""
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.creator_onboarding.update_one(
            {"creator_id": creator_id},
            {"$set": {
                "skipped": True,
                "skipped_at": now,
                "last_activity": now
            }}
        )
        
        # Update creator
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "onboarding_skipped": True,
                "onboarding_skipped_at": now
            }}
        )
        
        return {
            "success": True,
            "message": "Onboarding skipped. You can complete it anytime from your settings.",
            "skipped_at": now
        }
    
    async def reset_onboarding(self, creator_id: str) -> Dict[str, Any]:
        """Reset onboarding for a creator (admin or user-requested)"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Delete existing onboarding
        await self.db.creator_onboarding.delete_one({"creator_id": creator_id})
        
        # Create fresh onboarding
        onboarding = {
            "id": f"ONBOARD-{uuid.uuid4().hex[:10]}",
            "creator_id": creator_id,
            "current_step": 1,
            "completed_steps": [],
            "step_data": {},
            "arris_insights": {},
            "started_at": now,
            "last_activity": now,
            "completed_at": None,
            "completion_percentage": 0,
            "personalization_profile": {},
            "rewards_earned": [],
            "reset_count": 1
        }
        await self.db.creator_onboarding.insert_one(onboarding)
        
        # Update creator
        await self.db.creators.update_one(
            {"id": creator_id},
            {"$set": {
                "onboarding_complete": False,
                "onboarding_skipped": False
            }}
        )
        
        return {
            "success": True,
            "message": "Onboarding reset. Starting fresh!",
            "onboarding_id": onboarding["id"]
        }
    
    # ============== ADMIN FUNCTIONS ==============
    
    async def get_onboarding_analytics(self) -> Dict[str, Any]:
        """Get platform-wide onboarding analytics (admin)"""
        total = await self.db.creator_onboarding.count_documents({})
        completed = await self.db.creator_onboarding.count_documents({"completed_at": {"$ne": None}})
        skipped = await self.db.creator_onboarding.count_documents({"skipped": True})
        in_progress = total - completed - skipped
        
        # Completion rate
        completion_rate = (completed / max(total, 1)) * 100
        
        # Average completion percentage for in-progress
        pipeline = [
            {"$match": {"completed_at": None, "skipped": {"$ne": True}}},
            {"$group": {"_id": None, "avg_progress": {"$avg": "$completion_percentage"}}}
        ]
        progress_result = await self.db.creator_onboarding.aggregate(pipeline).to_list(1)
        avg_progress = progress_result[0]["avg_progress"] if progress_result else 0
        
        # Drop-off by step
        step_completion = {}
        for step in self.steps:
            count = await self.db.creator_onboarding.count_documents({
                "completed_steps": step["step_id"]
            })
            step_completion[step["step_id"]] = count
        
        # Most common goals
        goals_pipeline = [
            {"$match": {"step_data.goals.primary_goal": {"$exists": True}}},
            {"$group": {"_id": "$step_data.goals.primary_goal", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_goals = await self.db.creator_onboarding.aggregate(goals_pipeline).to_list(5)
        
        # Most common platforms
        platforms_pipeline = [
            {"$match": {"step_data.platforms.primary_platform": {"$exists": True}}},
            {"$group": {"_id": "$step_data.platforms.primary_platform", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_platforms = await self.db.creator_onboarding.aggregate(platforms_pipeline).to_list(5)
        
        return {
            "total_onboardings": total,
            "completed": completed,
            "skipped": skipped,
            "in_progress": in_progress,
            "completion_rate": round(completion_rate, 1),
            "avg_progress_incomplete": round(avg_progress, 1),
            "step_completion": step_completion,
            "top_goals": [{"goal": g["_id"], "count": g["count"]} for g in top_goals],
            "top_platforms": [{"platform": p["_id"], "count": p["count"]} for p in top_platforms],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }


# Global instance (will be initialized in server startup)
onboarding_wizard = None
