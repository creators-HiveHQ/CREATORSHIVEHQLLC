import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronRight, ChevronLeft, Sparkles, CheckCircle2, User, Globe, Target, Zap, Award, Loader2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Platform options with icons
const PLATFORM_OPTIONS = {
  youtube: { label: "YouTube", icon: "📺" },
  instagram: { label: "Instagram", icon: "📸" },
  tiktok: { label: "TikTok", icon: "🎵" },
  twitter: { label: "Twitter/X", icon: "🐦" },
  linkedin: { label: "LinkedIn", icon: "💼" },
  podcast: { label: "Podcast", icon: "🎙️" },
  blog: { label: "Blog/Website", icon: "📝" },
  newsletter: { label: "Newsletter", icon: "📧" },
  twitch: { label: "Twitch", icon: "🎮" },
  patreon: { label: "Patreon", icon: "💰" },
  courses: { label: "Online Courses", icon: "🎓" },
  other: { label: "Other", icon: "➕" }
};

// Niche options
const NICHE_OPTIONS = {
  business: "Business & Entrepreneurship",
  tech: "Tech & Software",
  finance: "Finance & Investing",
  health: "Health & Fitness",
  lifestyle: "Lifestyle & Travel",
  food: "Food & Cooking",
  gaming: "Gaming",
  education: "Education & Learning",
  entertainment: "Entertainment",
  art: "Art & Design",
  music: "Music",
  fashion: "Fashion & Beauty",
  parenting: "Parenting & Family",
  personal_development: "Personal Development",
  other: "Other"
};

// Goal options
const GOAL_OPTIONS = {
  grow_audience: "Grow My Audience",
  monetize: "Monetize My Content",
  brand_deals: "Land Brand Deals",
  launch_product: "Launch a Product/Course",
  build_community: "Build a Community",
  improve_content: "Improve Content Quality",
  work_life_balance: "Better Work-Life Balance",
  other: "Other"
};

// Communication style options
const STYLE_OPTIONS = {
  professional: "Professional & Polished",
  casual: "Casual & Friendly",
  motivational: "Motivational & Encouraging",
  direct: "Direct & To-the-point",
  detailed: "Detailed & Analytical"
};

// ARRIS focus area options
const FOCUS_OPTIONS = {
  content_ideas: "Content Ideas",
  growth_strategies: "Growth Strategies",
  monetization: "Monetization Tips",
  analytics: "Analytics & Insights",
  productivity: "Productivity",
  trends: "Trends & News",
  community: "Community Building"
};

// Step icons
const STEP_ICONS = {
  welcome: <Sparkles className="w-6 h-6" />,
  profile: <User className="w-6 h-6" />,
  platforms: <Globe className="w-6 h-6" />,
  niche: <Target className="w-6 h-6" />,
  goals: <Target className="w-6 h-6" />,
  arris_intro: <Zap className="w-6 h-6" />,
  complete: <Award className="w-6 h-6" />
};

export const SmartOnboardingWizard = ({ token, onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [stepData, setStepData] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [completionPercentage, setCompletionPercentage] = useState(0);
  const [error, setError] = useState("");
  const [arrisInsight, setArrisInsight] = useState(null);
  const [rewardEarned, setRewardEarned] = useState(null);

  // Fetch step details
  const fetchStepDetails = useCallback(async (stepNumber) => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`${API}/onboarding/step/${stepNumber}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStepData(response.data);
      // Pre-fill form with saved data
      if (response.data.saved_data) {
        setFormData(response.data.saved_data);
      } else {
        setFormData({});
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load step");
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Fetch initial status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API}/onboarding/status`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setCurrentStep(response.data.current_step);
        setCompletionPercentage(response.data.completion_percentage);
        if (response.data.is_complete) {
          onComplete?.();
        } else {
          fetchStepDetails(response.data.current_step);
        }
      } catch (err) {
        setError("Failed to load onboarding status");
        setLoading(false);
      }
    };
    fetchStatus();
  }, [token, fetchStepDetails, onComplete]);

  // Handle step completion
  const handleCompleteStep = async () => {
    setSaving(true);
    setError("");
    setArrisInsight(null);
    
    try {
      const response = await axios.post(
        `${API}/onboarding/step/${currentStep}`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setCompletionPercentage(response.data.completion_percentage);
      
      if (response.data.arris_insight) {
        setArrisInsight(response.data.arris_insight);
      }
      
      if (response.data.reward_earned) {
        setRewardEarned(response.data.reward_earned);
      }
      
      if (response.data.is_complete) {
        // Show completion for a moment before callback
        setTimeout(() => {
          onComplete?.();
        }, 2000);
      } else {
        setCurrentStep(response.data.next_step);
        fetchStepDetails(response.data.next_step);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save step");
    } finally {
      setSaving(false);
    }
  };

  // Handle going back
  const handleBack = () => {
    if (currentStep > 1) {
      const prevStep = currentStep - 1;
      setCurrentStep(prevStep);
      fetchStepDetails(prevStep);
      setArrisInsight(null);
    }
  };

  // Handle skip
  const handleSkip = async () => {
    try {
      await axios.post(
        `${API}/onboarding/skip`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      onSkip?.();
    } catch (err) {
      setError("Failed to skip onboarding");
    }
  };

  // Handle input change
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle multiselect toggle
  const handleMultiSelectToggle = (field, value) => {
    setFormData(prev => {
      const current = prev[field] || [];
      if (current.includes(value)) {
        return { ...prev, [field]: current.filter(v => v !== value) };
      } else {
        return { ...prev, [field]: [...current, value] };
      }
    });
  };

  // Render step content based on step_id
  const renderStepContent = () => {
    if (!stepData?.step) return null;
    
    const { step, arris_context } = stepData;
    
    switch (step.step_id) {
      case "welcome":
        return <WelcomeStep arrisContext={arris_context} />;
      case "profile":
        return <ProfileStep formData={formData} onChange={handleInputChange} arrisContext={arris_context} />;
      case "platforms":
        return <PlatformsStep formData={formData} onChange={handleInputChange} onMultiToggle={handleMultiSelectToggle} arrisContext={arris_context} />;
      case "niche":
        return <NicheStep formData={formData} onChange={handleInputChange} arrisContext={arris_context} />;
      case "goals":
        return <GoalsStep formData={formData} onChange={handleInputChange} arrisContext={arris_context} />;
      case "arris_intro":
        return <ArrisIntroStep formData={formData} onChange={handleInputChange} onMultiToggle={handleMultiSelectToggle} arrisContext={arris_context} />;
      case "complete":
        return <CompleteStep arrisContext={arris_context} rewardEarned={rewardEarned} />;
      default:
        return null;
    }
  };

  if (loading && !stepData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center" data-testid="onboarding-loading">
        <div className="text-center text-white">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading your journey...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4" data-testid="onboarding-wizard">
      <div className="w-full max-w-2xl">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-purple-300">Step {currentStep} of 7</span>
            <span className="text-sm text-purple-300">{completionPercentage}% complete</span>
          </div>
          <Progress value={completionPercentage} className="h-2 bg-purple-900" />
          
          {/* Step indicators */}
          <div className="flex justify-between mt-4">
            {[1, 2, 3, 4, 5, 6, 7].map(step => (
              <div
                key={step}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  step < currentStep
                    ? "bg-green-500 text-white"
                    : step === currentStep
                    ? "bg-purple-500 text-white ring-2 ring-purple-300"
                    : "bg-slate-700 text-slate-400"
                }`}
              >
                {step < currentStep ? <CheckCircle2 className="w-5 h-5" /> : step}
              </div>
            ))}
          </div>
        </div>

        {/* Main Card */}
        <Card className="border-purple-500/20 bg-slate-900/90 backdrop-blur" data-testid="onboarding-step-card">
          <CardHeader className="text-center pb-4">
            {stepData?.step && (
              <>
                <div className="mx-auto mb-4 w-14 h-14 bg-purple-500/20 rounded-full flex items-center justify-center text-purple-400">
                  {STEP_ICONS[stepData.step.step_id]}
                </div>
                <CardTitle className="text-2xl text-white" data-testid="step-title">
                  {stepData.step.title}
                </CardTitle>
                <CardDescription className="text-purple-300">
                  {stepData.step.subtitle}
                </CardDescription>
              </>
            )}
          </CardHeader>
          
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm" data-testid="error-message">
                {error}
              </div>
            )}
            
            {arrisInsight && (
              <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg" data-testid="arris-insight">
                <div className="flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-purple-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-purple-300 mb-1">ARRIS Insight</p>
                    <p className="text-sm text-slate-300">{arrisInsight.insight}</p>
                  </div>
                </div>
              </div>
            )}
            
            {renderStepContent()}
            
            {/* Navigation buttons */}
            <div className="flex justify-between pt-4">
              <div>
                {currentStep > 1 && stepData?.step?.step_id !== "complete" && (
                  <Button
                    variant="ghost"
                    onClick={handleBack}
                    className="text-slate-400 hover:text-white"
                    data-testid="back-button"
                  >
                    <ChevronLeft className="w-4 h-4 mr-2" />
                    Back
                  </Button>
                )}
              </div>
              
              <div className="flex gap-2">
                {currentStep === 1 && (
                  <Button
                    variant="ghost"
                    onClick={handleSkip}
                    className="text-slate-400 hover:text-white"
                    data-testid="skip-button"
                  >
                    Skip for now
                  </Button>
                )}
                
                {stepData?.step?.step_id !== "complete" && (
                  <Button
                    onClick={handleCompleteStep}
                    disabled={saving}
                    className="bg-purple-600 hover:bg-purple-700"
                    data-testid="continue-button"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : null}
                    {currentStep === 6 ? "Complete Setup" : "Continue"}
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Step Components

const WelcomeStep = ({ arrisContext }) => (
  <div className="text-center space-y-4" data-testid="welcome-step">
    <div className="text-5xl mb-4">👋</div>
    <p className="text-lg text-white">{arrisContext?.greeting}</p>
    <p className="text-slate-300">{arrisContext?.message}</p>
    
    {arrisContext?.tips && (
      <div className="bg-slate-800/50 rounded-lg p-4 mt-6">
        <p className="text-sm font-medium text-purple-300 mb-3">Before we start:</p>
        <ul className="space-y-2 text-sm text-slate-300 text-left">
          {arrisContext.tips.map((tip, i) => (
            <li key={i} className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              {tip}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const ProfileStep = ({ formData, onChange, arrisContext }) => (
  <div className="space-y-4" data-testid="profile-step">
    {arrisContext?.why_important && (
      <p className="text-sm text-slate-400 mb-4">{arrisContext.why_important}</p>
    )}
    
    <div>
      <Label htmlFor="display_name" className="text-slate-200">Display Name *</Label>
      <Input
        id="display_name"
        value={formData.display_name || ""}
        onChange={(e) => onChange("display_name", e.target.value)}
        placeholder="How should we call you?"
        className="bg-slate-800 border-slate-700 text-white mt-1"
        data-testid="display-name-input"
      />
    </div>
    
    <div>
      <Label htmlFor="bio" className="text-slate-200">Short Bio</Label>
      <Textarea
        id="bio"
        value={formData.bio || ""}
        onChange={(e) => onChange("bio", e.target.value)}
        placeholder="Tell us about yourself in a few sentences..."
        className="bg-slate-800 border-slate-700 text-white mt-1 h-24"
        maxLength={500}
        data-testid="bio-input"
      />
      <p className="text-xs text-slate-500 mt-1">{(formData.bio || "").length}/500</p>
    </div>
    
    <div>
      <Label htmlFor="website" className="text-slate-200">Website/Portfolio</Label>
      <Input
        id="website"
        type="url"
        value={formData.website || ""}
        onChange={(e) => onChange("website", e.target.value)}
        placeholder="https://"
        className="bg-slate-800 border-slate-700 text-white mt-1"
        data-testid="website-input"
      />
    </div>
  </div>
);

const PlatformsStep = ({ formData, onChange, onMultiToggle, arrisContext }) => (
  <div className="space-y-6" data-testid="platforms-step">
    {arrisContext?.why_important && (
      <p className="text-sm text-slate-400 mb-4">{arrisContext.why_important}</p>
    )}
    
    <div>
      <Label className="text-slate-200 mb-3 block">Primary Platform *</Label>
      <Select
        value={formData.primary_platform || ""}
        onValueChange={(value) => onChange("primary_platform", value)}
      >
        <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="primary-platform-select">
          <SelectValue placeholder="Select your main platform" />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700">
          {Object.entries(PLATFORM_OPTIONS).map(([key, { label, icon }]) => (
            <SelectItem key={key} value={key} className="text-white hover:bg-slate-700">
              {icon} {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
    
    <div>
      <Label className="text-slate-200 mb-3 block">Other Platforms</Label>
      <div className="grid grid-cols-3 gap-2">
        {Object.entries(PLATFORM_OPTIONS).map(([key, { label, icon }]) => (
          <div
            key={key}
            onClick={() => onMultiToggle("secondary_platforms", key)}
            className={`p-2 rounded-lg border cursor-pointer transition-all text-center text-sm ${
              (formData.secondary_platforms || []).includes(key)
                ? "bg-purple-500/20 border-purple-500 text-purple-300"
                : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
            }`}
            data-testid={`platform-${key}`}
          >
            <span className="text-lg">{icon}</span>
            <p className="mt-1">{label}</p>
          </div>
        ))}
      </div>
    </div>
    
    <div>
      <Label className="text-slate-200 mb-3 block">Total Audience Size *</Label>
      <Select
        value={formData.follower_count || ""}
        onValueChange={(value) => onChange("follower_count", value)}
      >
        <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="follower-count-select">
          <SelectValue placeholder="Select audience size" />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700">
          {["0-1K", "1K-10K", "10K-50K", "50K-100K", "100K-500K", "500K-1M", "1M+"].map(size => (
            <SelectItem key={size} value={size} className="text-white hover:bg-slate-700">
              {size} followers
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  </div>
);

const NicheStep = ({ formData, onChange, arrisContext }) => (
  <div className="space-y-4" data-testid="niche-step">
    {arrisContext?.why_important && (
      <p className="text-sm text-slate-400 mb-4">{arrisContext.why_important}</p>
    )}
    
    <div>
      <Label className="text-slate-200 mb-3 block">Primary Niche *</Label>
      <Select
        value={formData.primary_niche || ""}
        onValueChange={(value) => onChange("primary_niche", value)}
      >
        <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="niche-select">
          <SelectValue placeholder="Select your niche" />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700">
          {Object.entries(NICHE_OPTIONS).map(([key, label]) => (
            <SelectItem key={key} value={key} className="text-white hover:bg-slate-700">
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
    
    <div>
      <Label htmlFor="sub_niches" className="text-slate-200">Specific Topics</Label>
      <Input
        id="sub_niches"
        value={formData.sub_niches || ""}
        onChange={(e) => onChange("sub_niches", e.target.value)}
        placeholder="e.g., SaaS marketing, home workouts, vegan recipes"
        className="bg-slate-800 border-slate-700 text-white mt-1"
        data-testid="sub-niches-input"
      />
    </div>
    
    <div>
      <Label htmlFor="unique_angle" className="text-slate-200">Your Unique Angle</Label>
      <Textarea
        id="unique_angle"
        value={formData.unique_angle || ""}
        onChange={(e) => onChange("unique_angle", e.target.value)}
        placeholder="What makes your content different?"
        className="bg-slate-800 border-slate-700 text-white mt-1 h-20"
        maxLength={300}
        data-testid="unique-angle-input"
      />
      <p className="text-xs text-slate-500 mt-1">{(formData.unique_angle || "").length}/300</p>
    </div>
  </div>
);

const GoalsStep = ({ formData, onChange, arrisContext }) => (
  <div className="space-y-4" data-testid="goals-step">
    {arrisContext?.why_important && (
      <p className="text-sm text-slate-400 mb-4">{arrisContext.why_important}</p>
    )}
    
    <div>
      <Label className="text-slate-200 mb-3 block">Primary Goal *</Label>
      <div className="grid grid-cols-2 gap-2">
        {Object.entries(GOAL_OPTIONS).map(([key, label]) => (
          <div
            key={key}
            onClick={() => onChange("primary_goal", key)}
            className={`p-3 rounded-lg border cursor-pointer transition-all text-sm ${
              formData.primary_goal === key
                ? "bg-purple-500/20 border-purple-500 text-purple-300"
                : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
            }`}
            data-testid={`goal-${key}`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
    
    <div>
      <Label className="text-slate-200 mb-3 block">Revenue Goal (Next 12 months)</Label>
      <Select
        value={formData.revenue_goal || ""}
        onValueChange={(value) => onChange("revenue_goal", value)}
      >
        <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="revenue-goal-select">
          <SelectValue placeholder="Select revenue target" />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700">
          {["not_focused", "0-1K", "1K-5K", "5K-10K", "10K-25K", "25K-50K", "50K-100K", "100K+"].map(goal => (
            <SelectItem key={goal} value={goal} className="text-white hover:bg-slate-700">
              {goal === "not_focused" ? "Not focused on revenue" : `$${goal}/month`}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
    
    <div>
      <Label htmlFor="biggest_challenge" className="text-slate-200">Biggest Challenge *</Label>
      <Textarea
        id="biggest_challenge"
        value={formData.biggest_challenge || ""}
        onChange={(e) => onChange("biggest_challenge", e.target.value)}
        placeholder="What's your #1 obstacle right now?"
        className="bg-slate-800 border-slate-700 text-white mt-1 h-24"
        maxLength={500}
        data-testid="challenge-input"
      />
      <p className="text-xs text-slate-500 mt-1">{(formData.biggest_challenge || "").length}/500</p>
    </div>
  </div>
);

const ArrisIntroStep = ({ formData, onChange, onMultiToggle, arrisContext }) => (
  <div className="space-y-6" data-testid="arris-intro-step">
    {arrisContext?.capabilities && (
      <div className="bg-slate-800/50 rounded-lg p-4 mb-4">
        <p className="text-sm font-medium text-purple-300 mb-3">What ARRIS can do for you:</p>
        <ul className="space-y-2 text-sm text-slate-300">
          {arrisContext.capabilities.map((cap, i) => (
            <li key={i}>{cap}</li>
          ))}
        </ul>
      </div>
    )}
    
    <div>
      <Label className="text-slate-200 mb-3 block">Preferred Communication Style *</Label>
      <div className="grid grid-cols-1 gap-2">
        {Object.entries(STYLE_OPTIONS).map(([key, label]) => (
          <div
            key={key}
            onClick={() => onChange("arris_communication_style", key)}
            className={`p-3 rounded-lg border cursor-pointer transition-all text-sm ${
              formData.arris_communication_style === key
                ? "bg-purple-500/20 border-purple-500 text-purple-300"
                : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
            }`}
            data-testid={`style-${key}`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
    
    <div>
      <Label className="text-slate-200 mb-3 block">What should ARRIS focus on? *</Label>
      <div className="grid grid-cols-2 gap-2">
        {Object.entries(FOCUS_OPTIONS).map(([key, label]) => (
          <div
            key={key}
            onClick={() => onMultiToggle("arris_focus_areas", key)}
            className={`p-2 rounded-lg border cursor-pointer transition-all text-sm text-center ${
              (formData.arris_focus_areas || []).includes(key)
                ? "bg-purple-500/20 border-purple-500 text-purple-300"
                : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600"
            }`}
            data-testid={`focus-${key}`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
    
    <div>
      <Label className="text-slate-200 mb-3 block">How often should ARRIS reach out? *</Label>
      <Select
        value={formData.notification_preference || ""}
        onValueChange={(value) => onChange("notification_preference", value)}
      >
        <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="notification-pref-select">
          <SelectValue placeholder="Select notification frequency" />
        </SelectTrigger>
        <SelectContent className="bg-slate-800 border-slate-700">
          <SelectItem value="daily" className="text-white hover:bg-slate-700">Daily check-ins</SelectItem>
          <SelectItem value="weekly" className="text-white hover:bg-slate-700">Weekly summaries</SelectItem>
          <SelectItem value="on_demand" className="text-white hover:bg-slate-700">Only when I ask</SelectItem>
          <SelectItem value="important_only" className="text-white hover:bg-slate-700">Important updates only</SelectItem>
        </SelectContent>
      </Select>
    </div>
  </div>
);

const CompleteStep = ({ arrisContext, rewardEarned }) => (
  <div className="text-center space-y-6" data-testid="complete-step">
    <div className="text-6xl mb-4">🎉</div>
    <p className="text-lg text-white">{arrisContext?.message}</p>
    
    {rewardEarned && (
      <div className="bg-gradient-to-r from-yellow-500/20 to-purple-500/20 border border-yellow-500/30 rounded-lg p-4" data-testid="reward-earned">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Award className="w-6 h-6 text-yellow-400" />
          <span className="font-semibold text-yellow-400">{rewardEarned.name}</span>
        </div>
        <p className="text-sm text-slate-300">{rewardEarned.description}</p>
        <Badge className="mt-2 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
          +{rewardEarned.points} points
        </Badge>
      </div>
    )}
    
    {arrisContext?.next_steps && (
      <div className="bg-slate-800/50 rounded-lg p-4 text-left">
        <p className="text-sm font-medium text-purple-300 mb-3">What&apos;s next:</p>
        <ul className="space-y-2 text-sm text-slate-300">
          {arrisContext.next_steps.map((step, i) => (
            <li key={i} className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-purple-400" />
              {step}
            </li>
          ))}
        </ul>
      </div>
    )}
    
    {arrisContext?.first_insight && (
      <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
        <div className="flex items-start gap-3 text-left">
          <Sparkles className="w-5 h-5 text-purple-400 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-purple-300 mb-1">Your First ARRIS Insight</p>
            <p className="text-sm text-slate-300">{arrisContext.first_insight}</p>
          </div>
        </div>
      </div>
    )}
  </div>
);

export default SmartOnboardingWizard;
