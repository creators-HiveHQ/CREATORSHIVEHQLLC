/**
 * Creators Hive HQ - Intake Form
 * ==============================
 * The ignition key of the system. Nothing else activates until this is complete.
 * 
 * SINGLE-PAGE FORM with three sections:
 * 1. USER IDENTITY - identity_type, stage, primary_goal
 * 2. SYSTEM NEED - selected_engines (multi-select, required)
 * 3. STARTING POINT - assets_already_have, missing_elements, first_priority
 * 
 * Submit button: "Activate My System"
 * POST to /api/intake
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Briefcase, Users, Target, DollarSign, 
  Zap, UserCircle, Layers, CheckCircle2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== OPTION DEFINITIONS ==============

const IDENTITY_OPTIONS = [
  { value: "creator", label: "Creator", description: "Content creators, artists, influencers", icon: UserCircle },
  { value: "business", label: "Business", description: "Entrepreneurs, business owners, consultants", icon: Briefcase },
  { value: "hybrid", label: "Hybrid", description: "Creative business owners, creator-entrepreneurs", icon: Layers }
];

const STAGE_OPTIONS = [
  { value: "beginner", label: "Beginner", description: "Just starting out, learning the basics" },
  { value: "intermediate", label: "Intermediate", description: "Some experience, growing steadily" },
  { value: "advanced", label: "Advanced", description: "Established, optimizing and scaling" }
];

const PRIMARY_GOAL_OPTIONS = [
  { value: "grow_audience", label: "Grow audience" },
  { value: "build_brand", label: "Build brand" },
  { value: "monetize_content", label: "Monetize content" },
  { value: "launch_offers", label: "Launch offers" },
  { value: "improve_consistency", label: "Improve consistency" },
  { value: "other", label: "Other (specify below)" }
];

const ENGINE_OPTIONS = [
  { value: "business_engine", label: "Business Engine", description: "Business planning, strategy, market analysis", icon: Briefcase, color: "bg-blue-500" },
  { value: "engagement_engine", label: "Engagement Engine", description: "Audience building, content strategy, community", icon: Users, color: "bg-purple-500" },
  { value: "role_engine", label: "Role Engine", description: "Role definition, team building, delegation", icon: Target, color: "bg-amber-500" },
  { value: "income_engine", label: "Income Engine", description: "Revenue tracking, pricing, sales optimization", icon: DollarSign, color: "bg-emerald-500" }
];

const ASSETS_OPTIONS = [
  { value: "social_media_accounts", label: "Social media accounts" },
  { value: "existing_audience", label: "Existing audience" },
  { value: "offers_products", label: "Offers/products" },
  { value: "brand_identity", label: "Brand identity" },
  { value: "content_system", label: "Content system" },
  { value: "none", label: "None" }
];

const MISSING_OPTIONS = [
  { value: "clarity_structure", label: "Clarity/structure" },
  { value: "content_plan", label: "Content plan" },
  { value: "offer_strategy", label: "Offer strategy" },
  { value: "brand_voice", label: "Brand voice" },
  { value: "monetization_path", label: "Monetization path" },
  { value: "systems_automation", label: "Systems/automation" }
];

const PRIORITY_OPTIONS = [
  { value: "build_foundation", label: "Build foundation" },
  { value: "fix_gaps", label: "Fix gaps" },
  { value: "grow_audience", label: "Grow audience" },
  { value: "launch_offer", label: "Launch offer" },
  { value: "increase_income", label: "Increase income" },
  { value: "improve_consistency", label: "Improve consistency" }
];

// ============== MAIN INTAKE FORM ==============

export default function IntakeForm({ token, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state - User Identity
  const [identityType, setIdentityType] = useState("");
  const [stage, setStage] = useState("");
  const [primaryGoal, setPrimaryGoal] = useState("");
  const [primaryGoalOther, setPrimaryGoalOther] = useState("");

  // Form state - System Need
  const [selectedEngines, setSelectedEngines] = useState([]);

  // Form state - Starting Point
  const [assetsAlreadyHave, setAssetsAlreadyHave] = useState([]);
  const [missingElements, setMissingElements] = useState([]);
  const [firstPriority, setFirstPriority] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  // Load previous submission if exists
  useEffect(() => {
    const checkPrevious = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/intake/previous-submission`, { headers });
        const data = await res.json();
        if (data.has_previous && data.previous_data) {
          const prev = data.previous_data;
          // Load user identity
          if (prev.user_identity) {
            setIdentityType(prev.user_identity.identity_type || "");
            setStage(prev.user_identity.stage || "");
            setPrimaryGoal(prev.user_identity.primary_goal || "");
            setPrimaryGoalOther(prev.user_identity.primary_goal_other || "");
          }
          // Load system need
          if (prev.system_need?.selected_engines) {
            setSelectedEngines(prev.system_need.selected_engines);
          }
          // Load starting point
          if (prev.starting_point) {
            setAssetsAlreadyHave(prev.starting_point.assets_already_have || []);
            setMissingElements(prev.starting_point.missing_elements || []);
            setFirstPriority(prev.starting_point.first_priority || "");
          }
        }
      } catch (err) {
        console.error("Failed to check previous submission:", err);
      }
    };
    if (token) checkPrevious();
  }, [token]);

  // Toggle engine selection
  const toggleEngine = (engineValue) => {
    setSelectedEngines(prev => 
      prev.includes(engineValue) 
        ? prev.filter(e => e !== engineValue)
        : [...prev, engineValue]
    );
  };

  // Toggle multi-select option
  const toggleOption = (value, currentArray, setter) => {
    if (value === "none") {
      setter(currentArray.includes("none") ? [] : ["none"]);
    } else {
      const filtered = currentArray.filter(v => v !== "none");
      setter(
        filtered.includes(value)
          ? filtered.filter(v => v !== value)
          : [...filtered, value]
      );
    }
  };

  // Validate form
  const isFormValid = () => {
    // Required: identity_type, stage, primary_goal, at least 1 engine, first_priority
    if (!identityType) return false;
    if (!stage) return false;
    if (!primaryGoal) return false;
    if (primaryGoal === "other" && !primaryGoalOther.trim()) return false;
    if (selectedEngines.length === 0) return false;
    if (!firstPriority) return false;
    return true;
  };

  // Submit form
  const submitForm = async () => {
    if (!isFormValid()) {
      setError("Please complete all required fields.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const submission = {
        user_identity: {
          identity_type: identityType,
          stage: stage,
          primary_goal: primaryGoal,
          primary_goal_other: primaryGoal === "other" ? primaryGoalOther : null
        },
        system_need: {
          selected_engines: selectedEngines
        },
        starting_point: {
          assets_already_have: assetsAlreadyHave.filter(a => a !== "none"),
          missing_elements: missingElements,
          first_priority: firstPriority
        }
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
      setSuccess(result);
      
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

  // Success view
  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <Card className="border-0 shadow-lg">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">System Activated!</h2>
              <p className="text-slate-600 mb-6">{success.message}</p>
              
              <div className="bg-slate-50 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm text-slate-600 mb-2">
                  <strong>Track:</strong> {success.assigned_track?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <p className="text-sm text-slate-600 mb-2">
                  <strong>Engines Active:</strong> {success.activated_engines?.length || 0}
                </p>
                <p className="text-sm text-slate-600">
                  <strong>Modules Unlocked:</strong> {success.unlocked_modules?.length || 0}
                </p>
              </div>

              {success.next_steps?.length > 0 && (
                <div className="text-left mb-6">
                  <h3 className="font-semibold text-slate-900 mb-2">Next Steps:</h3>
                  <ul className="space-y-1">
                    {success.next_steps.map((step, idx) => (
                      <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <Button 
                onClick={() => window.location.href = "/creator/dashboard"}
                className="bg-slate-900 hover:bg-slate-800"
              >
                Go to Command Center
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-full mb-4">
            <Zap className="w-4 h-4" />
            <span className="text-sm font-medium">System Activation</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900">Intake Form</h1>
          <p className="text-slate-600 mt-2">
            This is your ignition key. Complete this to activate your personalized system.
          </p>
        </div>

        {/* Single Page Form */}
        <Card className="border-0 shadow-lg">
          <CardContent className="p-8 space-y-10">
            
            {/* ============== SECTION 1: USER IDENTITY ============== */}
            <section>
              <CardHeader className="px-0 pt-0">
                <CardTitle className="text-xl text-slate-900 flex items-center gap-2">
                  <UserCircle className="w-5 h-5" />
                  User Identity
                </CardTitle>
              </CardHeader>

              {/* Identity Type */}
              <div className="space-y-4 mb-6">
                <Label className="text-base font-semibold">
                  I am a... <span className="text-red-500">*</span>
                </Label>
                <RadioGroup
                  value={identityType}
                  onValueChange={setIdentityType}
                  className="grid grid-cols-1 md:grid-cols-3 gap-4"
                >
                  {IDENTITY_OPTIONS.map((opt) => {
                    const Icon = opt.icon;
                    const isSelected = identityType === opt.value;
                    return (
                      <label
                        key={opt.value}
                        className={`relative flex flex-col p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected 
                            ? "border-slate-900 bg-slate-50" 
                            : "border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <RadioGroupItem value={opt.value} className="sr-only" />
                        <Icon className={`w-6 h-6 mb-2 ${isSelected ? "text-slate-900" : "text-slate-400"}`} />
                        <span className="font-medium text-slate-900">{opt.label}</span>
                        <span className="text-xs text-slate-500 mt-1">{opt.description}</span>
                        {isSelected && (
                          <CheckCircle2 className="absolute top-2 right-2 w-4 h-4 text-emerald-500" />
                        )}
                      </label>
                    );
                  })}
                </RadioGroup>
              </div>

              {/* Stage */}
              <div className="space-y-4 mb-6">
                <Label className="text-base font-semibold">
                  My current stage is... <span className="text-red-500">*</span>
                </Label>
                <RadioGroup
                  value={stage}
                  onValueChange={setStage}
                  className="space-y-2"
                >
                  {STAGE_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                        stage === opt.value
                          ? "border-slate-900 bg-slate-50"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <RadioGroupItem value={opt.value} />
                      <div>
                        <span className="font-medium text-slate-900">{opt.label}</span>
                        <span className="text-sm text-slate-500 ml-2">- {opt.description}</span>
                      </div>
                    </label>
                  ))}
                </RadioGroup>
              </div>

              {/* Primary Goal */}
              <div className="space-y-4">
                <Label className="text-base font-semibold">
                  My primary goal is... <span className="text-red-500">*</span>
                </Label>
                <RadioGroup
                  value={primaryGoal}
                  onValueChange={setPrimaryGoal}
                  className="grid grid-cols-2 md:grid-cols-3 gap-3"
                >
                  {PRIMARY_GOAL_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                        primaryGoal === opt.value
                          ? "border-slate-900 bg-slate-50"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <RadioGroupItem value={opt.value} />
                      <span className="text-sm text-slate-700">{opt.label}</span>
                    </label>
                  ))}
                </RadioGroup>
                {primaryGoal === "other" && (
                  <Input
                    type="text"
                    placeholder="Please specify your goal..."
                    value={primaryGoalOther}
                    onChange={(e) => setPrimaryGoalOther(e.target.value)}
                    className="mt-2"
                  />
                )}
              </div>
            </section>

            {/* Divider */}
            <hr className="border-slate-200" />

            {/* ============== SECTION 2: SYSTEM NEED ============== */}
            <section>
              <CardHeader className="px-0 pt-0">
                <CardTitle className="text-xl text-slate-900 flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  System Need
                </CardTitle>
              </CardHeader>

              <div className="space-y-4">
                <Label className="text-base font-semibold">
                  Select the engines you need <span className="text-red-500">*</span>
                  <span className="text-sm font-normal text-slate-500 ml-2">(select at least one)</span>
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ENGINE_OPTIONS.map((engine) => {
                    const Icon = engine.icon;
                    const isSelected = selectedEngines.includes(engine.value);
                    return (
                      <div
                        key={engine.value}
                        onClick={() => toggleEngine(engine.value)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          isSelected
                            ? "border-slate-900 bg-slate-50"
                            : "border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className={`p-2 rounded-lg ${engine.color} bg-opacity-10`}>
                            <Icon className={`w-5 h-5 ${engine.color.replace('bg-', 'text-')}`} />
                          </div>
                          <Checkbox checked={isSelected} className="mt-1" />
                        </div>
                        <h4 className="font-semibold text-slate-900 mt-3">{engine.label}</h4>
                        <p className="text-sm text-slate-500 mt-1">{engine.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Divider */}
            <hr className="border-slate-200" />

            {/* ============== SECTION 3: STARTING POINT ============== */}
            <section>
              <CardHeader className="px-0 pt-0">
                <CardTitle className="text-xl text-slate-900 flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Starting Point
                </CardTitle>
              </CardHeader>

              {/* Assets Already Have */}
              <div className="space-y-4 mb-6">
                <Label className="text-base font-semibold">What do you already have?</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {ASSETS_OPTIONS.map((opt) => {
                    const isSelected = assetsAlreadyHave.includes(opt.value);
                    return (
                      <label
                        key={opt.value}
                        className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? "border-slate-900 bg-slate-50"
                            : "border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleOption(opt.value, assetsAlreadyHave, setAssetsAlreadyHave)}
                        />
                        <span className="text-sm text-slate-700">{opt.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Missing Elements */}
              <div className="space-y-4 mb-6">
                <Label className="text-base font-semibold">What is missing?</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {MISSING_OPTIONS.map((opt) => {
                    const isSelected = missingElements.includes(opt.value);
                    return (
                      <label
                        key={opt.value}
                        className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? "border-slate-900 bg-slate-50"
                            : "border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleOption(opt.value, missingElements, setMissingElements)}
                        />
                        <span className="text-sm text-slate-700">{opt.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* First Priority */}
              <div className="space-y-4">
                <Label className="text-base font-semibold">
                  What is your first priority? <span className="text-red-500">*</span>
                </Label>
                <RadioGroup
                  value={firstPriority}
                  onValueChange={setFirstPriority}
                  className="grid grid-cols-2 md:grid-cols-3 gap-3"
                >
                  {PRIORITY_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                        firstPriority === opt.value
                          ? "border-slate-900 bg-slate-50"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <RadioGroupItem value={opt.value} />
                      <span className="text-sm text-slate-700">{opt.label}</span>
                    </label>
                  ))}
                </RadioGroup>
              </div>
            </section>

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-6 border-t border-slate-200">
              <Button
                onClick={submitForm}
                disabled={!isFormValid() || loading}
                className="w-full py-6 text-lg bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300"
                data-testid="activate-system-btn"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Activating...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 mr-2" />
                    Activate My System
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
