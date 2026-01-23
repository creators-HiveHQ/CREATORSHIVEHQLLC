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
    
    # ============== PROGRESS TRACKER (D3) ==============
    
    async def get_detailed_progress(self, creator_id: str) -> Dict[str, Any]:
        """
        Get detailed progress tracking for a creator with ARRIS encouragement.
        
        Returns comprehensive progress information including:
        - Overall progress percentage
        - Detailed status of each step
        - Time spent and estimated remaining
        - ARRIS encouragement message
        - Post-onboarding checklist status
        """
        # Get onboarding record
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not onboarding:
            return {
                "has_started": False,
                "message": "Onboarding not started yet",
                "next_action": "Start your creator journey"
            }
        
        # Get creator info
        creator = await self.db.creators.find_one(
            {"id": creator_id},
            {"_id": 0, "name": 1}
        )
        creator_name = creator.get("name", "Creator") if creator else "Creator"
        
        completed_steps = onboarding.get("completed_steps", [])
        current_step = onboarding.get("current_step", 1)
        step_data = onboarding.get("step_data", {})
        is_complete = onboarding.get("completed_at") is not None
        is_skipped = onboarding.get("skipped", False)
        
        # Build detailed step status
        steps_status = []
        for step in self.steps:
            step_id = step["step_id"]
            is_completed = step_id in completed_steps
            is_current = step["step_number"] == current_step and not is_complete
            has_data = step_id in step_data
            
            step_status = {
                "step_number": step["step_number"],
                "step_id": step_id,
                "title": step["title"],
                "subtitle": step["subtitle"],
                "status": "completed" if is_completed else ("current" if is_current else "pending"),
                "is_required": step["required"],
                "has_data": has_data,
                "data_summary": self._summarize_step_data(step_id, step_data.get(step_id, {}))
            }
            steps_status.append(step_status)
        
        # Calculate progress metrics
        total_required = len([s for s in self.steps if s["required"]])
        completed_count = len(completed_steps)
        progress_percentage = int((completed_count / max(total_required, 1)) * 100)
        
        # Time tracking
        started_at = onboarding.get("started_at")
        last_activity = onboarding.get("last_activity")
        completed_at = onboarding.get("completed_at")
        
        time_metrics = self._calculate_time_metrics(started_at, last_activity, completed_at, completed_count, total_required)
        
        # Generate ARRIS encouragement
        arris_message = await self._generate_progress_encouragement(
            creator_name=creator_name,
            progress_percentage=progress_percentage,
            current_step=current_step,
            is_complete=is_complete,
            is_skipped=is_skipped,
            completed_steps=completed_steps
        )
        
        # Get post-onboarding checklist if completed
        post_onboarding_checklist = None
        if is_complete:
            post_onboarding_checklist = await self._get_post_onboarding_checklist(creator_id)
        
        # Calculate next action
        next_action = self._get_next_action(current_step, is_complete, is_skipped, completed_steps)
        
        return {
            "creator_id": creator_id,
            "creator_name": creator_name,
            "has_started": True,
            "is_complete": is_complete,
            "is_skipped": is_skipped,
            "progress": {
                "percentage": progress_percentage,
                "completed_steps": completed_count,
                "total_steps": total_required,
                "current_step": current_step
            },
            "steps": steps_status,
            "time_metrics": time_metrics,
            "arris_message": arris_message,
            "next_action": next_action,
            "post_onboarding_checklist": post_onboarding_checklist,
            "rewards": onboarding.get("rewards_earned", []),
            "last_activity": last_activity
        }
    
    def _summarize_step_data(self, step_id: str, data: Dict) -> Optional[str]:
        """Generate a brief summary of step data"""
        if not data:
            return None
        
        if step_id == "profile":
            name = data.get("display_name", "")
            return f"Profile: {name}" if name else None
        elif step_id == "platforms":
            platform = data.get("primary_platform", "")
            return f"Primary: {PLATFORM_LABELS.get(platform, platform)}" if platform else None
        elif step_id == "niche":
            niche = data.get("primary_niche", "")
            return f"Niche: {NICHE_LABELS.get(niche, niche)}" if niche else None
        elif step_id == "goals":
            goal = data.get("primary_goal", "")
            return f"Goal: {GOAL_LABELS.get(goal, goal)}" if goal else None
        elif step_id == "arris_intro":
            style = data.get("arris_communication_style", "")
            return f"Style: {style.title()}" if style else None
        
        return None
    
    def _calculate_time_metrics(
        self,
        started_at: Optional[str],
        last_activity: Optional[str],
        completed_at: Optional[str],
        completed_steps: int,
        total_steps: int
    ) -> Dict[str, Any]:
        """Calculate time-related metrics"""
        now = datetime.now(timezone.utc)
        
        metrics = {
            "started_at": started_at,
            "last_activity": last_activity,
            "completed_at": completed_at,
            "time_since_start": None,
            "time_since_last_activity": None,
            "total_duration": None,
            "estimated_remaining": None
        }
        
        if started_at:
            try:
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                metrics["time_since_start"] = self._format_duration(now - start)
            except (ValueError, TypeError):
                pass
        
        if last_activity:
            try:
                last = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                metrics["time_since_last_activity"] = self._format_duration(now - last)
            except (ValueError, TypeError):
                pass
        
        if completed_at:
            try:
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                metrics["total_duration"] = self._format_duration(end - start)
            except (ValueError, TypeError):
                pass
        else:
            # Estimate remaining time
            remaining_steps = total_steps - completed_steps
            if remaining_steps > 0:
                # Assume ~2 minutes per step
                estimated_minutes = remaining_steps * 2
                metrics["estimated_remaining"] = f"~{estimated_minutes} minutes"
        
        return metrics
    
    def _format_duration(self, delta: timedelta) -> str:
        """Format a timedelta as human-readable string"""
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return "Just now"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = total_seconds // 86400
            return f"{days} day{'s' if days > 1 else ''} ago"
    
    async def _generate_progress_encouragement(
        self,
        creator_name: str,
        progress_percentage: int,
        current_step: int,
        is_complete: bool,
        is_skipped: bool,
        completed_steps: List[str]
    ) -> Dict[str, Any]:
        """Generate ARRIS encouragement message based on progress"""
        if is_complete:
            return {
                "type": "celebration",
                "icon": "🎉",
                "message": f"Congratulations, {creator_name}! You've completed your onboarding. ARRIS is now fully personalized to help you succeed.",
                "sub_message": "Check out your personalized dashboard for tailored insights."
            }
        
        if is_skipped:
            return {
                "type": "reminder",
                "icon": "📝",
                "message": f"Hey {creator_name}, you skipped onboarding earlier. Complete it anytime to unlock personalized ARRIS insights!",
                "sub_message": "It only takes a few minutes to finish."
            }
        
        if progress_percentage == 0:
            return {
                "type": "welcome",
                "icon": "👋",
                "message": f"Welcome, {creator_name}! Let's get your creator journey started.",
                "sub_message": "Just 7 quick steps to personalize your experience."
            }
        
        if progress_percentage < 30:
            return {
                "type": "early",
                "icon": "🚀",
                "message": f"Great start, {creator_name}! You're making progress.",
                "sub_message": f"{100 - progress_percentage}% to go - keep the momentum!"
            }
        
        if progress_percentage < 60:
            return {
                "type": "midway",
                "icon": "💪",
                "message": f"You're doing great, {creator_name}! Halfway there.",
                "sub_message": "The more I learn about you, the better I can help."
            }
        
        if progress_percentage < 90:
            return {
                "type": "almost",
                "icon": "⭐",
                "message": f"Almost there, {creator_name}! Just a few more steps.",
                "sub_message": "You're about to unlock your full personalized experience."
            }
        
        return {
            "type": "final",
            "icon": "🏁",
            "message": f"One last step, {creator_name}! Let's finish this together.",
            "sub_message": "Complete your setup to earn the Hive Newcomer badge!"
        }
    
    async def _get_post_onboarding_checklist(self, creator_id: str) -> Dict[str, Any]:
        """Get post-onboarding setup checklist"""
        checklist = await self.db.creator_checklist.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not checklist:
            # Initialize checklist
            checklist = {
                "id": f"CHECKLIST-{uuid.uuid4().hex[:8]}",
                "creator_id": creator_id,
                "items": [
                    {
                        "id": "first_proposal",
                        "title": "Create Your First Proposal",
                        "description": "Submit a project proposal to get feedback from ARRIS",
                        "completed": False,
                        "completed_at": None,
                        "points": 50,
                        "category": "engagement"
                    },
                    {
                        "id": "connect_socials",
                        "title": "Connect Social Accounts",
                        "description": "Link your social media for better insights",
                        "completed": False,
                        "completed_at": None,
                        "points": 30,
                        "category": "setup"
                    },
                    {
                        "id": "explore_arris",
                        "title": "Chat with ARRIS",
                        "description": "Have your first conversation with ARRIS",
                        "completed": False,
                        "completed_at": None,
                        "points": 25,
                        "category": "engagement"
                    },
                    {
                        "id": "explore_dashboard",
                        "title": "Explore Your Dashboard",
                        "description": "Check out all the features available to you",
                        "completed": False,
                        "completed_at": None,
                        "points": 15,
                        "category": "discovery"
                    },
                    {
                        "id": "set_notification_prefs",
                        "title": "Set Notification Preferences",
                        "description": "Customize how and when ARRIS reaches out",
                        "completed": False,
                        "completed_at": None,
                        "points": 20,
                        "category": "setup"
                    },
                    {
                        "id": "upgrade_tier",
                        "title": "Explore Subscription Plans",
                        "description": "Discover Premium features to accelerate your growth",
                        "completed": False,
                        "completed_at": None,
                        "points": 10,
                        "category": "discovery"
                    }
                ],
                "total_points": 150,
                "earned_points": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.creator_checklist.insert_one(checklist)
        
        # Calculate progress
        completed_items = [i for i in checklist["items"] if i["completed"]]
        earned_points = sum(i["points"] for i in completed_items)
        progress = int((len(completed_items) / len(checklist["items"])) * 100)
        
        return {
            "items": checklist["items"],
            "progress": progress,
            "completed_count": len(completed_items),
            "total_count": len(checklist["items"]),
            "earned_points": earned_points,
            "total_points": checklist["total_points"]
        }
    
    def _get_next_action(
        self,
        current_step: int,
        is_complete: bool,
        is_skipped: bool,
        completed_steps: List[str]
    ) -> Dict[str, str]:
        """Get the next recommended action for the creator"""
        if is_complete:
            return {
                "action": "explore_dashboard",
                "title": "Explore Your Dashboard",
                "description": "Your personalized dashboard is ready",
                "url": "/creator/dashboard"
            }
        
        if is_skipped:
            return {
                "action": "resume_onboarding",
                "title": "Complete Onboarding",
                "description": "Finish setting up your profile",
                "url": "/creator/onboarding"
            }
        
        current = next((s for s in self.steps if s["step_number"] == current_step), None)
        if current:
            return {
                "action": f"complete_{current['step_id']}",
                "title": current["title"],
                "description": current["subtitle"],
                "url": f"/creator/onboarding?step={current_step}"
            }
        
        return {
            "action": "start_onboarding",
            "title": "Start Onboarding",
            "description": "Begin your creator journey",
            "url": "/creator/onboarding"
        }
    
    async def update_checklist_item(
        self,
        creator_id: str,
        item_id: str,
        completed: bool = True
    ) -> Dict[str, Any]:
        """Update a post-onboarding checklist item"""
        checklist = await self.db.creator_checklist.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not checklist:
            return {"error": "Checklist not found"}
        
        # Find and update the item
        item_found = False
        points_change = 0
        
        for item in checklist["items"]:
            if item["id"] == item_id:
                item_found = True
                if completed and not item["completed"]:
                    item["completed"] = True
                    item["completed_at"] = datetime.now(timezone.utc).isoformat()
                    points_change = item["points"]
                elif not completed and item["completed"]:
                    item["completed"] = False
                    item["completed_at"] = None
                    points_change = -item["points"]
                break
        
        if not item_found:
            return {"error": "Item not found"}
        
        # Update earned points
        checklist["earned_points"] = checklist.get("earned_points", 0) + points_change
        
        # Save
        await self.db.creator_checklist.update_one(
            {"creator_id": creator_id},
            {"$set": {
                "items": checklist["items"],
                "earned_points": checklist["earned_points"]
            }}
        )
        
        # Award badge if all items completed
        completed_items = [i for i in checklist["items"] if i["completed"]]
        if len(completed_items) == len(checklist["items"]):
            await self._award_checklist_completion(creator_id, checklist)
        
        return {
            "success": True,
            "item_id": item_id,
            "completed": completed,
            "points_change": points_change,
            "total_earned": checklist["earned_points"]
        }
    
    async def _award_checklist_completion(self, creator_id: str, checklist: Dict):
        """Award badge for completing post-onboarding checklist"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Add reward to onboarding record
        reward = {
            "type": "checklist_complete",
            "name": "Setup Champion",
            "description": "Completed the post-onboarding checklist",
            "earned_at": now,
            "points": 100
        }
        
        await self.db.creator_onboarding.update_one(
            {"creator_id": creator_id},
            {"$push": {"rewards_earned": reward}}
        )
        
        # Store ARRIS memory about this achievement
        memory = {
            "id": f"MEM-CHECKLIST-{uuid.uuid4().hex[:8]}",
            "creator_id": creator_id,
            "memory_type": "milestone",
            "content": {
                "event": "checklist_complete",
                "title": "Setup Champion Badge Earned",
                "description": f"Completed all {len(checklist['items'])} post-onboarding tasks",
                "points_earned": checklist["earned_points"] + 100
            },
            "importance": 0.8,
            "tags": ["milestone", "badge", "onboarding"],
            "created_at": now
        }
        await self.db.arris_memories.insert_one(memory)
    
    async def get_progress_timeline(self, creator_id: str) -> List[Dict[str, Any]]:
        """Get timeline of onboarding progress events"""
        onboarding = await self.db.creator_onboarding.find_one(
            {"creator_id": creator_id},
            {"_id": 0}
        )
        
        if not onboarding:
            return []
        
        timeline = []
        
        # Started event
        if onboarding.get("started_at"):
            timeline.append({
                "event": "started",
                "title": "Onboarding Started",
                "description": "Began the creator journey",
                "timestamp": onboarding["started_at"],
                "icon": "🚀"
            })
        
        # Step completion events (from ARRIS insights timestamps)
        arris_insights = onboarding.get("arris_insights", {})
        step_data = onboarding.get("step_data", {})
        
        for step in self.steps:
            step_id = step["step_id"]
            if step_id in onboarding.get("completed_steps", []):
                # Use ARRIS insight timestamp if available
                insight = arris_insights.get(step_id, {})
                timestamp = insight.get("generated_at") or onboarding.get("last_activity")
                
                timeline.append({
                    "event": f"completed_{step_id}",
                    "title": f"Completed: {step['title']}",
                    "description": self._summarize_step_data(step_id, step_data.get(step_id, {})) or step["subtitle"],
                    "timestamp": timestamp,
                    "icon": "✅"
                })
        
        # Completion event
        if onboarding.get("completed_at"):
            timeline.append({
                "event": "completed",
                "title": "Onboarding Complete",
                "description": "Earned the Hive Newcomer badge",
                "timestamp": onboarding["completed_at"],
                "icon": "🎉"
            })
        
        # Rewards earned
        for reward in onboarding.get("rewards_earned", []):
            timeline.append({
                "event": "reward",
                "title": f"Badge Earned: {reward['name']}",
                "description": reward["description"],
                "timestamp": reward["earned_at"],
                "icon": "🏆",
                "points": reward["points"]
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return timeline
    
    async def get_arris_progress_insight(self, creator_id: str) -> Dict[str, Any]:
        """Get ARRIS AI-generated progress insight"""
        progress = await self.get_detailed_progress(creator_id)
        
        if not progress.get("has_started"):
            return {
                "insight": "Ready to begin your creator journey? Let's get started!",
                "recommendation": "Start onboarding to unlock personalized ARRIS assistance."
            }
        
        if progress.get("is_complete"):
            # Get personalization to provide relevant insight
            onboarding = await self.db.creator_onboarding.find_one(
                {"creator_id": creator_id},
                {"_id": 0, "personalization_profile": 1}
            )
            
            profile = onboarding.get("personalization_profile", {}) if onboarding else {}
            goal = profile.get("primary_goal", "")
            platform = profile.get("primary_platform", "")
            
            goal_label = GOAL_LABELS.get(goal, goal)
            platform_label = PLATFORM_LABELS.get(platform, platform)
            
            return {
                "insight": f"Your profile is set up for success! I'm tracking your goal to {goal_label.lower()} on {platform_label}.",
                "recommendation": "Check your dashboard for personalized growth tips based on your profile.",
                "personalization": {
                    "goal": goal_label,
                    "platform": platform_label
                }
            }
        
        # In progress
        current_step = progress["progress"]["current_step"]
        percentage = progress["progress"]["percentage"]
        
        step = next((s for s in self.steps if s["step_number"] == current_step), None)
        step_title = step["title"] if step else "Next step"
        
        return {
            "insight": f"You're {percentage}% through onboarding. Your next step: {step_title}.",
            "recommendation": "Complete your setup to unlock full ARRIS personalization.",
            "progress": {
                "percentage": percentage,
                "current_step": current_step,
                "step_title": step_title
            }
        }


# Global instance (will be initialized in server startup)
onboarding_wizard = None
