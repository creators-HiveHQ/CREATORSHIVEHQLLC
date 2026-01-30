/**
 * Creators Hive HQ - Intake Form
 * ==============================
 * The ignition key of the system. Nothing else activates until this is complete.
 * 
 * Collects:
 * 1. USER IDENTITY - Creator/Business/Hybrid, Stage, Primary goal
 * 2. SYSTEM NEED - Which engines they require
 * 3. STARTING POINT - What they have, what's missing, first accomplishment
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Briefcase, Users, Zap, DollarSign, 
  ArrowRight, ArrowLeft, CheckCircle2, Sparkles,
  Target, Layers, UserCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== STEP COMPONENTS ==============

const StepIndicator = ({ currentStep, totalSteps }) => (
  <div className="flex items-center justify-center mb-8">
    {[1, 2, 3].map((step) => (
      <div key={step} className="flex items-center">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
            step < currentStep
              ? "bg-emerald-500 text-white"
              : step === currentStep
              ? "bg-slate-900 text-white"
              : "bg-slate-200 text-slate-500"
          }`}
        >
          {step < currentStep ? <CheckCircle2 className="w-5 h-5" /> : step}
        </div>
        {step < totalSteps && (
          <div
            className={`w-16 h-1 mx-2 rounded ${
              step < currentStep ? "bg-emerald-500" : "bg-slate-200"
            }`}
          />
        )}
      </div>
    ))}
  </div>
);

// Step 1: User Identity
const UserIdentityStep = ({ data, onChange }) => {
  const identityTypes = [
    {
      value: "creator",
      label: "Creator",
      description: "Content creators, artists, influencers",
      icon: UserCircle
    },
    {
      value: "business",
      label: "Business",
      description: "Entrepreneurs, business owners, consultants",
      icon: Briefcase
    },
    {
      value: "hybrid",
      label: "Hybrid",
      description: "Creative business owners, creator-entrepreneurs",
      icon: Layers
    }
  ];

  const stages = [
    { value: "beginner", label: "Beginner", description: "Just starting out" },
    { value: "intermediate", label: "Intermediate", description: "Growing steadily" },
    { value: "advanced", label: "Advanced", description: "Optimizing and scaling" }
  ];

  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Who Are You?</h2>
        <p className="text-slate-600">Help us understand your identity to personalize your experience</p>
      </div>

      {/* Identity Type */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">I am a...</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {identityTypes.map((type) => {
            const Icon = type.icon;
            const isSelected = data.identity_type === type.value;
            return (
              <div
                key={type.value}
                onClick={() => onChange({ ...data, identity_type: type.value })}
                className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                  isSelected
                    ? "border-slate-900 bg-slate-50"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <Icon className={`w-8 h-8 mb-3 ${isSelected ? "text-slate-900" : "text-slate-400"}`} />
                <h3 className="font-semibold text-slate-900">{type.label}</h3>
                <p className="text-sm text-slate-500 mt-1">{type.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stage */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">My current stage is...</Label>
        <RadioGroup
          value={data.stage}
          onValueChange={(value) => onChange({ ...data, stage: value })}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {stages.map((stage) => (
            <div key={stage.value} className="flex items-center space-x-2">
              <RadioGroupItem value={stage.value} id={stage.value} />
              <Label htmlFor={stage.value} className="flex flex-col cursor-pointer">
                <span className="font-medium">{stage.label}</span>
                <span className="text-sm text-slate-500">{stage.description}</span>
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Primary Goal */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">My primary goal is...</Label>
        <Textarea
          value={data.primary_goal}
          onChange={(e) => onChange({ ...data, primary_goal: e.target.value })}
          placeholder="Describe your main objective in 1-2 sentences..."
          className="min-h-[100px]"
        />
      </div>
    </div>
  );
};

// Step 2: System Need (Engines)
const SystemNeedStep = ({ data, onChange }) => {
  const engines = [
    {
      id: "business_engine",
      name: "Business Engine",
      description: "Business planning, strategy, market analysis",
      icon: Briefcase,
      bestFor: ["Business", "Hybrid"],
      color: "bg-blue-500"
    },
    {
      id: "engagement_engine",
      name: "Engagement Engine",
      description: "Audience building, content strategy, community",
      icon: Users,
      bestFor: ["Creator", "Hybrid"],
      color: "bg-purple-500"
    },
    {
      id: "role_engine",
      name: "Role Engine",
      description: "Role definition, team building, delegation",
      icon: Target,
      bestFor: ["Business", "Hybrid"],
      color: "bg-amber-500"
    },
    {
      id: "income_engine",
      name: "Income Engine",
      description: "Revenue tracking, pricing, sales optimization",
      icon: DollarSign,
      bestFor: ["Creator", "Business", "Hybrid"],
      color: "bg-emerald-500"
    }
  ];

  const toggleEngine = (engineId) => {
    onChange({ ...data, [engineId]: !data[engineId] });
  };

  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">What Do You Need?</h2>
        <p className="text-slate-600">Select the engines that match your goals</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {engines.map((engine) => {
          const Icon = engine.icon;
          const isSelected = data[engine.id];
          return (
            <div
              key={engine.id}
              onClick={() => toggleEngine(engine.id)}
              className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                isSelected
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className={`p-3 rounded-lg ${engine.color} bg-opacity-10`}>
                  <Icon className={`w-6 h-6 ${engine.color.replace('bg-', 'text-')}`} />
                </div>
                <Checkbox checked={isSelected} className="mt-1" />
              </div>
              <h3 className="font-semibold text-slate-900 mt-4">{engine.name}</h3>
              <p className="text-sm text-slate-500 mt-1">{engine.description}</p>
              <div className="flex flex-wrap gap-1 mt-3">
                {engine.bestFor.map((type) => (
                  <Badge key={type} variant="secondary" className="text-xs">
                    {type}
                  </Badge>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {!data.business_engine && !data.engagement_engine && !data.role_engine && !data.income_engine && (
        <p className="text-center text-slate-500 text-sm">
          Select at least one engine, or we'll recommend engines based on your identity
        </p>
      )}
    </div>
  );
};

// Step 3: Starting Point
const StartingPointStep = ({ data, onChange }) => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Where Are You Starting?</h2>
        <p className="text-slate-600">Tell us what you have and what you need</p>
      </div>

      {/* What they have */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">What do you already have?</Label>
        <Textarea
          value={data.what_they_have}
          onChange={(e) => onChange({ ...data, what_they_have: e.target.value })}
          placeholder="Describe your existing assets, audience, systems, or experience..."
          className="min-h-[100px]"
        />
        <div className="flex flex-wrap gap-2">
          {["Existing audience", "Business plan", "Revenue streams", "Team", "Content library"].map((suggestion) => (
            <Badge
              key={suggestion}
              variant="outline"
              className="cursor-pointer hover:bg-slate-100"
              onClick={() => {
                const current = data.what_they_have;
                const newValue = current ? `${current}, ${suggestion.toLowerCase()}` : suggestion;
                onChange({ ...data, what_they_have: newValue });
              }}
            >
              + {suggestion}
            </Badge>
          ))}
        </div>
      </div>

      {/* What's missing */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">What is missing?</Label>
        <Textarea
          value={data.what_is_missing}
          onChange={(e) => onChange({ ...data, what_is_missing: e.target.value })}
          placeholder="Describe what gaps you need to fill..."
          className="min-h-[100px]"
        />
        <div className="flex flex-wrap gap-2">
          {["Clear strategy", "Audience growth", "Income diversification", "Role clarity", "Content system"].map((suggestion) => (
            <Badge
              key={suggestion}
              variant="outline"
              className="cursor-pointer hover:bg-slate-100"
              onClick={() => {
                const current = data.what_is_missing;
                const newValue = current ? `${current}, ${suggestion.toLowerCase()}` : suggestion;
                onChange({ ...data, what_is_missing: newValue });
              }}
            >
              + {suggestion}
            </Badge>
          ))}
        </div>
      </div>

      {/* First accomplishment */}
      <div className="space-y-4">
        <Label className="text-base font-semibold">What do you want to accomplish first?</Label>
        <Textarea
          value={data.first_accomplishment}
          onChange={(e) => onChange({ ...data, first_accomplishment: e.target.value })}
          placeholder="Describe your immediate priority..."
          className="min-h-[80px]"
        />
      </div>
    </div>
  );
};

// ============== MAIN INTAKE FORM ==============

export default function IntakeForm({ token, onComplete }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [previousData, setPreviousData] = useState(null);

  // Form state
  const [userIdentity, setUserIdentity] = useState({
    identity_type: "",
    stage: "",
    primary_goal: ""
  });

  const [systemNeed, setSystemNeed] = useState({
    business_engine: false,
    engagement_engine: false,
    role_engine: false,
    income_engine: false
  });

  const [startingPoint, setStartingPoint] = useState({
    what_they_have: "",
    what_is_missing: "",
    first_accomplishment: ""
  });

  const headers = { Authorization: `Bearer ${token}` };

  // Check for previous submission
  useEffect(() => {
    const checkPrevious = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/intake/previous-submission`, { headers });
        const data = await res.json();
        if (data.has_previous && data.previous_data) {
          setPreviousData(data.previous_data);
        }
      } catch (err) {
        console.error("Failed to check previous submission:", err);
      }
    };
    if (token) checkPrevious();
  }, [token]);

  // Load previous data
  const loadPreviousData = useCallback(() => {
    if (previousData) {
      if (previousData.user_identity) {
        setUserIdentity(previousData.user_identity);
      }
      if (previousData.system_need) {
        setSystemNeed(previousData.system_need);
      }
      if (previousData.starting_point) {
        setStartingPoint(previousData.starting_point);
      }
    }
  }, [previousData]);

  // Validate current step
  const isStepValid = () => {
    if (currentStep === 1) {
      return userIdentity.identity_type && userIdentity.stage && userIdentity.primary_goal.length >= 5;
    }
    if (currentStep === 2) {
      return true; // Engines are optional
    }
    if (currentStep === 3) {
      return (
        startingPoint.what_they_have.length >= 5 &&
        startingPoint.what_is_missing.length >= 5 &&
        startingPoint.first_accomplishment.length >= 5
      );
    }
    return false;
  };

  // Submit form
  const submitForm = async () => {
    setLoading(true);
    setError(null);

    try {
      const submission = {
        user_identity: userIdentity,
        system_need: systemNeed,
        starting_point: startingPoint
      };

      const res = await fetch(`${BACKEND_URL}/api/intake/submit`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(submission)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to submit intake form");
      }

      const result = await res.json();
      
      if (onComplete) {
        onComplete(result);
      }
    } catch (err) {
      setError(err.message);
      console.error("Intake submission failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-full mb-4">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-medium">System Activation</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">Intake Form</h1>
          <p className="text-slate-600 mt-2">
            This is your ignition key. Complete this to activate your personalized system.
          </p>
        </div>

        {/* Previous data notice */}
        {previousData && currentStep === 1 && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-amber-800 text-sm">
              You have a previous submission. 
              <button
                onClick={loadPreviousData}
                className="ml-2 underline font-medium"
              >
                Load previous data
              </button>
            </p>
          </div>
        )}

        {/* Step Indicator */}
        <StepIndicator currentStep={currentStep} totalSteps={3} />

        {/* Form Card */}
        <Card className="shadow-lg border-0">
          <CardContent className="p-8">
            {/* Step Content */}
            {currentStep === 1 && (
              <UserIdentityStep data={userIdentity} onChange={setUserIdentity} />
            )}
            {currentStep === 2 && (
              <SystemNeedStep data={systemNeed} onChange={setSystemNeed} />
            )}
            {currentStep === 3 && (
              <StartingPointStep data={startingPoint} onChange={setStartingPoint} />
            )}

            {/* Error */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => setCurrentStep((s) => s - 1)}
                disabled={currentStep === 1}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>

              {currentStep < 3 ? (
                <Button
                  onClick={() => setCurrentStep((s) => s + 1)}
                  disabled={!isStepValid()}
                  className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800"
                >
                  Continue
                  <ArrowRight className="w-4 h-4" />
                </Button>
              ) : (
                <Button
                  onClick={submitForm}
                  disabled={!isStepValid() || loading}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Activating...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Activate System
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Step Labels */}
        <div className="flex justify-center gap-8 mt-6 text-sm text-slate-500">
          <span className={currentStep === 1 ? "text-slate-900 font-medium" : ""}>
            1. Identity
          </span>
          <span className={currentStep === 2 ? "text-slate-900 font-medium" : ""}>
            2. Engines
          </span>
          <span className={currentStep === 3 ? "text-slate-900 font-medium" : ""}>
            3. Starting Point
          </span>
        </div>
      </div>
    </div>
  );
}
