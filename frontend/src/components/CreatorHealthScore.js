/**
 * Creator Health Score Component (Module B4)
 * Personal health score dashboard for Pro+ creators.
 * Shows overall score, component breakdown, achievements, and recommendations.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Status colors
const STATUS_COLORS = {
  excellent: { bg: "bg-green-100", text: "text-green-700", ring: "#22c55e" },
  good: { bg: "bg-blue-100", text: "text-blue-700", ring: "#3b82f6" },
  fair: { bg: "bg-amber-100", text: "text-amber-700", ring: "#f59e0b" },
  needs_attention: { bg: "bg-orange-100", text: "text-orange-700", ring: "#f97316" },
  critical: { bg: "bg-red-100", text: "text-red-700", ring: "#ef4444" },
};

// Component colors
const COMPONENT_COLORS = {
  engagement: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", bar: "bg-blue-500" },
  proposal_success: { bg: "bg-green-50", border: "border-green-200", text: "text-green-700", bar: "bg-green-500" },
  consistency: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700", bar: "bg-purple-500" },
  arris_utilization: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", bar: "bg-amber-500" },
  profile_completeness: { bg: "bg-pink-50", border: "border-pink-200", text: "text-pink-700", bar: "bg-pink-500" },
};

/**
 * Health Score Ring Component
 */
const HealthScoreRing = ({ score, status, size = "lg" }) => {
  const sizeConfig = {
    lg: { radius: 80, stroke: 12, text: "text-5xl" },
    md: { radius: 60, stroke: 10, text: "text-3xl" },
    sm: { radius: 40, stroke: 6, text: "text-xl" },
  };
  
  const config = sizeConfig[size];
  const circumference = 2 * Math.PI * config.radius;
  const progress = (score / 100) * circumference;
  const color = STATUS_COLORS[status?.name]?.ring || "#6b7280";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={config.radius * 2 + config.stroke * 2} height={config.radius * 2 + config.stroke * 2}>
        <circle
          cx={config.radius + config.stroke}
          cy={config.radius + config.stroke}
          r={config.radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={config.stroke}
        />
        <circle
          cx={config.radius + config.stroke}
          cy={config.radius + config.stroke}
          r={config.radius}
          fill="none"
          stroke={color}
          strokeWidth={config.stroke}
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          transform={`rotate(-90 ${config.radius + config.stroke} ${config.radius + config.stroke})`}
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold ${config.text}`}>{score}</span>
        <span className="text-sm text-slate-500">Health Score</span>
      </div>
    </div>
  );
};

/**
 * Component Score Card
 */
const ComponentCard = ({ component, data, onClick }) => {
  const colors = COMPONENT_COLORS[component] || COMPONENT_COLORS.engagement;
  
  return (
    <Card
      className={`${colors.bg} ${colors.border} border cursor-pointer hover:shadow-md transition-all`}
      onClick={() => onClick(component)}
      data-testid={`component-${component}`}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">{data.icon}</span>
            <span className={`font-medium ${colors.text}`}>{data.label}</span>
          </div>
          <span className={`text-2xl font-bold ${colors.text}`}>{data.score}</span>
        </div>
        <Progress value={data.score} className={`h-2 ${colors.bar}`} />
        <p className="text-xs text-slate-500 mt-2">{data.description}</p>
      </CardContent>
    </Card>
  );
};

/**
 * Achievement Badge
 */
const AchievementBadge = ({ achievement }) => {
  return (
    <div
      className="flex flex-col items-center p-3 bg-gradient-to-br from-amber-50 to-yellow-50 rounded-lg border border-amber-200 hover:shadow-md transition-all"
      data-testid={`achievement-${achievement.label.replace(/\s+/g, "-").toLowerCase()}`}
    >
      <span className="text-3xl mb-1">{achievement.icon}</span>
      <span className="text-sm font-medium text-amber-800">{achievement.label}</span>
      <span className="text-xs text-amber-600 text-center">{achievement.description}</span>
    </div>
  );
};

/**
 * Recommendation Card
 */
const RecommendationCard = ({ recommendation }) => {
  const impactColors = {
    high: "bg-red-100 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-blue-100 text-blue-700",
  };

  return (
    <Card className="hover:shadow-md transition-all" data-testid={`recommendation-${recommendation.component}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💡</span>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-slate-800">{recommendation.title}</h4>
              <Badge className={impactColors[recommendation.impact]}>
                {recommendation.impact} impact
              </Badge>
            </div>
            <p className="text-sm text-slate-600">{recommendation.action}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Component Details Modal
 */
const ComponentDetailsModal = ({ component, data, details, isOpen, onClose }) => {
  if (!component || !data) return null;
  
  const colors = COMPONENT_COLORS[component] || COMPONENT_COLORS.engagement;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>{data.icon}</span>
            <span>{data.label}</span>
          </DialogTitle>
          <DialogDescription>{data.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Score */}
          <div className={`p-4 rounded-lg ${colors.bg} ${colors.border} border text-center`}>
            <span className={`text-4xl font-bold ${colors.text}`}>{data.score}</span>
            <p className="text-sm text-slate-600">out of 100</p>
          </div>

          {/* Metrics */}
          {data.metrics && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Key Metrics</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.metrics).map(([key, value]) => (
                  <div key={key} className="bg-slate-50 p-2 rounded">
                    <p className="text-xs text-slate-500">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm font-medium">
                      {typeof value === "number" && value < 1 && value > 0
                        ? `${(value * 100).toFixed(0)}%`
                        : Array.isArray(value)
                        ? value.join(", ") || "None"
                        : String(value ?? "N/A")}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Details tip */}
          {details?.tip && (
            <div className="bg-purple-50 border border-purple-200 p-3 rounded-lg">
              <p className="text-sm text-purple-700">💡 {details.tip}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Main Creator Health Score Component
 */
export const CreatorHealthScore = ({ token, onUpgrade }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [tier, setTier] = useState(null);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [componentDetails, setComponentDetails] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchHealthScore = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = getAuthHeaders();

      const response = await axios.get(`${API}/creators/me/health-score`, { headers });

      if (response.data.access_denied) {
        setAccessDenied(true);
        setTier(response.data.tier);
        return;
      }

      setHealthData(response.data);
      setTier(response.data.tier);
      setAccessDenied(false);
    } catch (err) {
      console.error("Error fetching health score:", err);
      if (err.response?.status === 403) {
        setAccessDenied(true);
      } else {
        setError("Failed to load health score");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (token) {
      fetchHealthScore();
    }
  }, [token, fetchHealthScore]);

  const handleComponentClick = async (component) => {
    setSelectedComponent(component);
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/creators/me/health-score/component/${component}`, { headers });
      setComponentDetails(response.data.details);
    } catch (err) {
      console.error("Error fetching component details:", err);
    }
  };

  // Access denied - show upgrade prompt
  if (accessDenied) {
    return (
      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200" data-testid="health-score-upgrade">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6">
            <span className="text-5xl">💪</span>
          </div>
          <h2 className="text-2xl font-bold text-green-800 mb-3">Creator Health Score</h2>
          <p className="text-green-600 max-w-md mx-auto mb-6">
            Upgrade to Pro to unlock your personal health score dashboard. Track your engagement,
            proposal success, consistency, and get personalized recommendations to improve.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🎯</span>
              <p className="text-xs text-slate-600 mt-2">Engagement</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">📋</span>
              <p className="text-xs text-slate-600 mt-2">Success Rate</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">📈</span>
              <p className="text-xs text-slate-600 mt-2">Consistency</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🧠</span>
              <p className="text-xs text-slate-600 mt-2">ARRIS Usage</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🏆</span>
              <p className="text-xs text-slate-600 mt-2">Achievements</p>
            </div>
          </div>
          <Button
            onClick={onUpgrade}
            className="bg-green-600 hover:bg-green-700"
            data-testid="upgrade-to-pro-health"
          >
            ⚡ Upgrade to Pro
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Loading state
  if (loading) {
    return (
      <Card data-testid="health-score-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Calculating your health score...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200" data-testid="health-score-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchHealthScore} className="mt-4">Retry</Button>
        </CardContent>
      </Card>
    );
  }

  if (!healthData) return null;

  const { overall_score, status, components, trend, achievements, recommendations } = healthData;
  const statusStyle = STATUS_COLORS[status?.name] || STATUS_COLORS.fair;

  return (
    <div className="space-y-6" data-testid="creator-health-score">
      {/* Component Details Modal */}
      {selectedComponent && (
        <ComponentDetailsModal
          component={selectedComponent}
          data={components[selectedComponent]}
          details={componentDetails}
          isOpen={!!selectedComponent}
          onClose={() => { setSelectedComponent(null); setComponentDetails(null); }}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            💪 Health Score
            <Badge className="bg-purple-100 text-purple-700">{tier?.toUpperCase()}</Badge>
          </h2>
          <p className="text-sm text-slate-600">Your personal creator health dashboard</p>
        </div>
        <Button variant="outline" onClick={fetchHealthScore} data-testid="refresh-health">
          🔄 Refresh
        </Button>
      </div>

      {/* Main Score Card */}
      <Card className={`${statusStyle.bg} border-2`} style={{ borderColor: statusStyle.ring }}>
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Score Ring */}
            <div className="flex-shrink-0">
              <HealthScoreRing score={overall_score} status={status} size="lg" />
            </div>

            {/* Status and Trend */}
            <div className="flex-1 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                <span className="text-3xl">{status?.emoji}</span>
                <span className={`text-2xl font-bold ${statusStyle.text}`}>{status?.label}</span>
              </div>
              
              {/* Trend indicator */}
              <div className="flex items-center justify-center md:justify-start gap-2">
                {trend?.direction === "up" && (
                  <Badge className="bg-green-500 text-white">↑ +{trend.change} from last week</Badge>
                )}
                {trend?.direction === "down" && (
                  <Badge className="bg-red-500 text-white">↓ {trend.change} from last week</Badge>
                )}
                {trend?.direction === "stable" && (
                  <Badge className="bg-slate-400 text-white">→ Stable</Badge>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{achievements?.length || 0}</p>
                <p className="text-xs text-slate-600">Achievements</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{recommendations?.length || 0}</p>
                <p className="text-xs text-slate-600">Actions</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-overview">📊 Overview</TabsTrigger>
          <TabsTrigger value="achievements" data-testid="tab-achievements">🏆 Achievements ({achievements?.length || 0})</TabsTrigger>
          <TabsTrigger value="recommendations" data-testid="tab-recommendations">💡 Actions ({recommendations?.length || 0})</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(components || {}).map(([key, data]) => (
              <ComponentCard
                key={key}
                component={key}
                data={data}
                onClick={handleComponentClick}
              />
            ))}
          </div>
        </TabsContent>

        {/* Achievements Tab */}
        <TabsContent value="achievements" className="mt-4">
          {achievements && achievements.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {achievements.map((achievement, i) => (
                <AchievementBadge key={i} achievement={achievement} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">🎯</span>
                <p className="text-slate-600 mt-2">
                  No achievements yet. Submit proposals and use ARRIS to earn badges!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="mt-4">
          {recommendations && recommendations.length > 0 ? (
            <div className="space-y-4">
              {recommendations.map((rec, i) => (
                <RecommendationCard key={i} recommendation={rec} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">✨</span>
                <p className="text-slate-600 mt-2">
                  Great job! No recommendations right now. Keep up the excellent work!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CreatorHealthScore;
