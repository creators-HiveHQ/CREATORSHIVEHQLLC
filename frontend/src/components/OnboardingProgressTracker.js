import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  Sparkles, 
  Trophy, 
  ArrowRight, 
  ChevronRight,
  Gift,
  Target,
  Loader2,
  RefreshCw
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Step icons mapping
const STEP_ICONS = {
  welcome: "👋",
  profile: "👤",
  platforms: "🌐",
  niche: "🎯",
  goals: "🚀",
  arris_intro: "⚡",
  complete: "🎉"
};

export const OnboardingProgressTracker = ({ token, onResumeOnboarding, compact = false }) => {
  const [progress, setProgress] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingItem, setUpdatingItem] = useState(null);

  const fetchProgress = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/onboarding/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProgress(response.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load progress");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchTimeline = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/onboarding/progress/timeline`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTimeline(response.data.timeline || []);
    } catch (err) {
      console.error("Failed to load timeline:", err);
    }
  }, [token]);

  useEffect(() => {
    fetchProgress();
    fetchTimeline();
  }, [fetchProgress, fetchTimeline]);

  const handleChecklistUpdate = async (itemId, completed) => {
    setUpdatingItem(itemId);
    try {
      await axios.patch(
        `${API}/onboarding/checklist/${itemId}?completed=${completed}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchProgress();
    } catch (err) {
      console.error("Failed to update checklist:", err);
    } finally {
      setUpdatingItem(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8" data-testid="progress-loading">
        <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50" data-testid="progress-error">
        <CardContent className="p-4 text-center text-red-600">
          <p>{error}</p>
          <Button variant="outline" size="sm" onClick={fetchProgress} className="mt-2">
            <RefreshCw className="w-4 h-4 mr-2" /> Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!progress?.has_started) {
    return (
      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white" data-testid="progress-not-started">
        <CardContent className="p-6 text-center">
          <div className="text-4xl mb-4">🚀</div>
          <h3 className="text-lg font-semibold text-purple-900 mb-2">Ready to Begin?</h3>
          <p className="text-purple-600 mb-4">Start your onboarding to unlock personalized ARRIS assistance.</p>
          <Button onClick={onResumeOnboarding} className="bg-purple-600 hover:bg-purple-700">
            Start Onboarding <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Compact view for dashboard widget
  if (compact) {
    return <CompactProgress progress={progress} onResume={onResumeOnboarding} />;
  }

  return (
    <div className="space-y-6" data-testid="onboarding-progress-tracker">
      {/* Main Progress Card */}
      <Card className="border-purple-200" data-testid="progress-main-card">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl text-purple-900">Onboarding Progress</CardTitle>
              <CardDescription>Your journey to personalized ARRIS assistance</CardDescription>
            </div>
            {progress.is_complete ? (
              <Badge className="bg-green-100 text-green-700 border-green-200">
                <CheckCircle2 className="w-4 h-4 mr-1" /> Complete
              </Badge>
            ) : progress.is_skipped ? (
              <Badge className="bg-yellow-100 text-yellow-700 border-yellow-200">
                <Clock className="w-4 h-4 mr-1" /> Skipped
              </Badge>
            ) : (
              <Badge className="bg-purple-100 text-purple-700 border-purple-200">
                <Target className="w-4 h-4 mr-1" /> In Progress
              </Badge>
            )}
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-slate-600">
                {progress.progress.completed_steps} of {progress.progress.total_steps} steps completed
              </span>
              <span className="text-sm font-semibold text-purple-600">
                {progress.progress.percentage}%
              </span>
            </div>
            <Progress value={progress.progress.percentage} className="h-3" />
          </div>

          {/* ARRIS Message */}
          {progress.arris_message && (
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-100" data-testid="arris-message">
              <div className="flex items-start gap-3">
                <span className="text-2xl">{progress.arris_message.icon}</span>
                <div>
                  <p className="font-medium text-purple-900">{progress.arris_message.message}</p>
                  <p className="text-sm text-purple-600 mt-1">{progress.arris_message.sub_message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Steps Status */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-700 mb-3">Steps</h4>
            <div className="grid gap-2">
              {progress.steps.map((step) => (
                <StepItem key={step.step_id} step={step} />
              ))}
            </div>
          </div>

          {/* Time Metrics */}
          {progress.time_metrics && (
            <div className="flex flex-wrap gap-4 text-sm text-slate-500 pt-2 border-t">
              {progress.time_metrics.time_since_start && (
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>Started {progress.time_metrics.time_since_start}</span>
                </div>
              )}
              {progress.time_metrics.estimated_remaining && !progress.is_complete && (
                <div className="flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  <span>{progress.time_metrics.estimated_remaining} remaining</span>
                </div>
              )}
              {progress.time_metrics.total_duration && progress.is_complete && (
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span>Completed in {progress.time_metrics.total_duration}</span>
                </div>
              )}
            </div>
          )}

          {/* Action Button */}
          {!progress.is_complete && (
            <Button 
              onClick={onResumeOnboarding} 
              className="w-full bg-purple-600 hover:bg-purple-700"
              data-testid="resume-onboarding-btn"
            >
              {progress.is_skipped ? "Complete Onboarding" : "Continue Onboarding"}
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Rewards Section */}
      {progress.rewards && progress.rewards.length > 0 && (
        <Card className="border-yellow-200 bg-gradient-to-br from-yellow-50 to-white" data-testid="rewards-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2 text-yellow-800">
              <Trophy className="w-5 h-5" /> Rewards Earned
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {progress.rewards.map((reward, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white rounded-lg border border-yellow-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                      <Gift className="w-5 h-5 text-yellow-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{reward.name}</p>
                      <p className="text-sm text-slate-500">{reward.description}</p>
                    </div>
                  </div>
                  <Badge className="bg-yellow-100 text-yellow-700">+{reward.points} pts</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Post-Onboarding Checklist */}
      {progress.is_complete && progress.post_onboarding_checklist && (
        <Card className="border-blue-200" data-testid="checklist-card">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2 text-blue-800">
                <Target className="w-5 h-5" /> Setup Checklist
              </CardTitle>
              <Badge className="bg-blue-100 text-blue-700">
                {progress.post_onboarding_checklist.earned_points}/{progress.post_onboarding_checklist.total_points} pts
              </Badge>
            </div>
            <CardDescription>
              Complete these tasks to maximize your experience
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Progress 
                value={progress.post_onboarding_checklist.progress} 
                className="h-2"
              />
              <p className="text-xs text-slate-500 mt-1 text-right">
                {progress.post_onboarding_checklist.completed_count}/{progress.post_onboarding_checklist.total_count} completed
              </p>
            </div>
            <div className="space-y-2">
              {progress.post_onboarding_checklist.items.map((item) => (
                <ChecklistItem 
                  key={item.id} 
                  item={item} 
                  onUpdate={handleChecklistUpdate}
                  updating={updatingItem === item.id}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <Card data-testid="timeline-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {timeline.slice(0, 5).map((event, idx) => (
                <TimelineItem key={idx} event={event} isLast={idx === Math.min(timeline.length - 1, 4)} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Step Item Component
const StepItem = ({ step }) => {
  const getStatusStyles = () => {
    switch (step.status) {
      case "completed":
        return "bg-green-50 border-green-200 text-green-700";
      case "current":
        return "bg-purple-50 border-purple-300 text-purple-700 ring-2 ring-purple-200";
      default:
        return "bg-slate-50 border-slate-200 text-slate-500";
    }
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${getStatusStyles()}`}>
      <span className="text-xl">{STEP_ICONS[step.step_id] || "📋"}</span>
      <div className="flex-1">
        <p className="font-medium text-sm">{step.title}</p>
        {step.data_summary && (
          <p className="text-xs opacity-75">{step.data_summary}</p>
        )}
      </div>
      {step.status === "completed" ? (
        <CheckCircle2 className="w-5 h-5 text-green-500" />
      ) : step.status === "current" ? (
        <ArrowRight className="w-5 h-5 text-purple-500" />
      ) : (
        <Circle className="w-5 h-5 text-slate-300" />
      )}
    </div>
  );
};

// Checklist Item Component
const ChecklistItem = ({ item, onUpdate, updating }) => {
  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${item.completed ? "bg-green-50 border-green-200" : "bg-white border-slate-200"}`}>
      <Checkbox 
        checked={item.completed}
        onCheckedChange={(checked) => onUpdate(item.id, checked)}
        disabled={updating}
        className="h-5 w-5"
        data-testid={`checklist-item-${item.id}`}
      />
      <div className="flex-1">
        <p className={`font-medium text-sm ${item.completed ? "text-green-700 line-through" : "text-slate-700"}`}>
          {item.title}
        </p>
        <p className="text-xs text-slate-500">{item.description}</p>
      </div>
      <Badge variant="outline" className={item.completed ? "bg-green-100 text-green-600" : "bg-slate-100"}>
        {updating ? <Loader2 className="w-3 h-3 animate-spin" /> : `+${item.points}`}
      </Badge>
    </div>
  );
};

// Timeline Item Component
const TimelineItem = ({ event, isLast }) => {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-lg">
          {event.icon}
        </div>
        {!isLast && <div className="w-0.5 h-full bg-slate-200 mt-1"></div>}
      </div>
      <div className="flex-1 pb-4">
        <p className="font-medium text-sm text-slate-900">{event.title}</p>
        <p className="text-xs text-slate-500">{event.description}</p>
        {event.timestamp && (
          <p className="text-xs text-slate-400 mt-1">
            {new Date(event.timestamp).toLocaleDateString()}
          </p>
        )}
      </div>
    </div>
  );
};

// Compact Progress Widget
const CompactProgress = ({ progress, onResume }) => {
  if (progress.is_complete) {
    return (
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200" data-testid="compact-progress-complete">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-green-800">Onboarding Complete</p>
            <p className="text-sm text-green-600">ARRIS is fully personalized</p>
          </div>
          {progress.rewards?.length > 0 && (
            <Badge className="bg-yellow-100 text-yellow-700">
              <Trophy className="w-3 h-3 mr-1" /> {progress.rewards.length} badge{progress.rewards.length > 1 ? "s" : ""}
            </Badge>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200" data-testid="compact-progress-inprogress">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-purple-600" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <p className="font-medium text-purple-800">Setup Progress</p>
            <span className="text-sm font-semibold text-purple-600">{progress.progress.percentage}%</span>
          </div>
          <Progress value={progress.progress.percentage} className="h-2" />
        </div>
        <Button size="sm" onClick={onResume} className="bg-purple-600 hover:bg-purple-700">
          Continue
        </Button>
      </div>
    </div>
  );
};

export default OnboardingProgressTracker;
