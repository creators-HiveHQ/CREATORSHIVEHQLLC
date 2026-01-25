/**
 * Creator Pattern Insights Component (Module A3)
 * Displays personalized pattern cards for Pro+ creators.
 * Shows success patterns, risk patterns, timing insights, and actionable recommendations.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Category colors and icons
const CATEGORY_STYLES = {
  success: { bg: "bg-green-50", border: "border-green-200", text: "text-green-700", icon: "✅" },
  risk: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", icon: "⚠️" },
  timing: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", icon: "⏰" },
  growth: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700", icon: "📈" },
  engagement: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", icon: "🎯" },
  platform: { bg: "bg-indigo-50", border: "border-indigo-200", text: "text-indigo-700", icon: "📱" },
  content: { bg: "bg-pink-50", border: "border-pink-200", text: "text-pink-700", icon: "📝" },
};

// Confidence badge styles
const CONFIDENCE_STYLES = {
  high: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-slate-600",
};

/**
 * Pattern Card Component
 */
const PatternCard = ({ pattern, onViewDetails, onFeedback }) => {
  const style = CATEGORY_STYLES[pattern.category] || CATEGORY_STYLES.success;
  const confidenceStyle = CONFIDENCE_STYLES[pattern.confidence_level] || CONFIDENCE_STYLES.medium;

  return (
    <Card
      className={`${style.bg} ${style.border} border cursor-pointer hover:shadow-md transition-all`}
      onClick={() => onViewDetails(pattern)}
      data-testid={`pattern-card-${pattern.pattern_id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <span className="text-2xl">{style.icon}</span>
            <div className="flex-1 min-w-0">
              <h4 className={`font-semibold ${style.text}`}>{pattern.title}</h4>
              <p className="text-sm text-slate-600 mt-1 line-clamp-2">{pattern.description}</p>
              
              {/* Action indicator */}
              {pattern.actionable && (
                <div className="flex items-center gap-1 mt-2">
                  <Badge variant="outline" className="text-xs bg-white">
                    💡 Actionable
                  </Badge>
                </div>
              )}
            </div>
          </div>
          
          {/* Confidence badge */}
          <Badge className={`${confidenceStyle} text-xs shrink-0`}>
            {Math.round(pattern.confidence * 100)}%
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Recommendation Card Component
 */
const RecommendationCard = ({ recommendation }) => {
  const style = CATEGORY_STYLES[recommendation.category] || CATEGORY_STYLES.success;
  
  const impactColors = {
    high: "bg-green-500",
    medium: "bg-amber-500",
    low: "bg-slate-400",
  };
  
  const effortColors = {
    low: "bg-green-500",
    medium: "bg-amber-500",
    high: "bg-red-500",
  };

  return (
    <Card className="hover:shadow-md transition-all" data-testid={`recommendation-${recommendation.id}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <span className="text-xl">{style.icon}</span>
          <div className="flex-1">
            <h4 className="font-semibold text-slate-800">{recommendation.title}</h4>
            <p className="text-sm text-slate-600 mt-1">{recommendation.action}</p>
            
            {/* Impact and Effort indicators */}
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Impact:</span>
                <div className="flex gap-0.5">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        i <= (recommendation.impact === "high" ? 3 : recommendation.impact === "medium" ? 2 : 1)
                          ? impactColors[recommendation.impact]
                          : "bg-slate-200"
                      }`}
                    />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Effort:</span>
                <div className="flex gap-0.5">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        i <= (recommendation.effort === "high" ? 3 : recommendation.effort === "medium" ? 2 : 1)
                          ? effortColors[recommendation.effort]
                          : "bg-slate-200"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Pattern Detail Modal
 */
const PatternDetailModal = ({ pattern, isOpen, onClose, onFeedback }) => {
  const [feedbackSent, setFeedbackSent] = useState(false);
  
  if (!pattern) return null;
  
  const style = CATEGORY_STYLES[pattern.category] || CATEGORY_STYLES.success;

  const handleFeedback = async (isHelpful) => {
    await onFeedback(pattern.pattern_id, isHelpful);
    setFeedbackSent(true);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>{style.icon}</span>
            <span>{pattern.title}</span>
          </DialogTitle>
          <DialogDescription>
            Pattern discovered based on your activity
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          {/* Description */}
          <div className={`p-4 rounded-lg ${style.bg} ${style.border} border`}>
            <p className={`${style.text}`}>{pattern.description}</p>
          </div>
          
          {/* Confidence */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">Confidence Level</span>
            <div className="flex items-center gap-2">
              <Progress value={pattern.confidence * 100} className="w-24 h-2" />
              <Badge className={CONFIDENCE_STYLES[pattern.confidence_level]}>
                {pattern.confidence_label}
              </Badge>
            </div>
          </div>
          
          {/* Data Points */}
          {pattern.data && Object.keys(pattern.data).length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Supporting Data</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(pattern.data).map(([key, value]) => (
                  <div key={key} className="bg-slate-50 p-2 rounded">
                    <p className="text-xs text-slate-500">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm font-medium">
                      {typeof value === "number" && value < 1 && value > 0
                        ? `${(value * 100).toFixed(0)}%`
                        : String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Recommended Action */}
          {pattern.recommended_action && (
            <div className="bg-purple-50 border border-purple-200 p-4 rounded-lg">
              <p className="text-sm font-medium text-purple-700 mb-1">💡 Recommended Action</p>
              <p className="text-sm text-purple-600">{pattern.recommended_action}</p>
            </div>
          )}
          
          {/* Feedback */}
          {!feedbackSent ? (
            <div className="border-t pt-4">
              <p className="text-sm text-slate-600 mb-3">Was this insight helpful?</p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleFeedback(true)}
                  className="flex-1"
                >
                  👍 Yes, helpful
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleFeedback(false)}
                  className="flex-1"
                >
                  👎 Not helpful
                </Button>
              </div>
            </div>
          ) : (
            <div className="border-t pt-4 text-center">
              <p className="text-sm text-green-600">✓ Thanks for your feedback!</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Main Creator Pattern Insights Component
 */
export const CreatorPatternInsights = ({ token, onUpgrade }) => {
  const [patterns, setPatterns] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [selectedPattern, setSelectedPattern] = useState(null);
  const [activeTab, setActiveTab] = useState("patterns");
  const [tier, setTier] = useState(null);

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchPatterns = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = getAuthHeaders();
      
      const [patternsRes, recsRes] = await Promise.all([
        axios.get(`${API}/creators/me/pattern-insights`, { headers }),
        axios.get(`${API}/creators/me/pattern-recommendations`, { headers }).catch(() => ({ data: { recommendations: [] } }))
      ]);
      
      if (patternsRes.data.access_denied) {
        setAccessDenied(true);
        setTier(patternsRes.data.tier);
        return;
      }
      
      setPatterns(patternsRes.data.patterns || []);
      setSummary(patternsRes.data.summary || null);
      setTier(patternsRes.data.tier);
      setRecommendations(recsRes.data.recommendations || []);
      setAccessDenied(false);
    } catch (err) {
      console.error("Error fetching patterns:", err);
      if (err.response?.status === 403) {
        setAccessDenied(true);
      } else {
        setError("Failed to load pattern insights");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (token) {
      fetchPatterns();
    }
  }, [token, fetchPatterns]);

  const handleFeedback = async (patternId, isHelpful) => {
    try {
      const headers = getAuthHeaders();
      await axios.post(
        `${API}/creators/me/pattern-feedback`,
        { pattern_id: patternId, is_helpful: isHelpful },
        { headers }
      );
    } catch (err) {
      console.error("Error sending feedback:", err);
    }
  };

  // Access denied - show upgrade prompt
  if (accessDenied) {
    return (
      <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200" data-testid="pattern-insights-upgrade">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6">
            <span className="text-4xl">🔮</span>
          </div>
          <h2 className="text-2xl font-bold text-purple-800 mb-3">Pattern Insights</h2>
          <p className="text-purple-600 max-w-md mx-auto mb-6">
            Unlock personalized pattern analysis with Pro tier. Discover what makes your proposals successful,
            identify timing patterns, and get actionable recommendations.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">✅</span>
              <p className="text-xs text-slate-600 mt-2">Success Patterns</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">⚠️</span>
              <p className="text-xs text-slate-600 mt-2">Risk Detection</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">⏰</span>
              <p className="text-xs text-slate-600 mt-2">Timing Insights</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">💡</span>
              <p className="text-xs text-slate-600 mt-2">Recommendations</p>
            </div>
          </div>
          <Button
            onClick={onUpgrade}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="upgrade-to-pro-patterns"
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
      <Card data-testid="pattern-insights-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Analyzing your patterns...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200" data-testid="pattern-insights-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchPatterns} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="creator-pattern-insights">
      {/* Pattern Detail Modal */}
      <PatternDetailModal
        pattern={selectedPattern}
        isOpen={!!selectedPattern}
        onClose={() => setSelectedPattern(null)}
        onFeedback={handleFeedback}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            🔮 Pattern Insights
            <Badge className="bg-purple-100 text-purple-700">{tier?.toUpperCase()}</Badge>
          </h2>
          <p className="text-sm text-slate-600">Personalized patterns based on your activity</p>
        </div>
        <Button variant="outline" onClick={fetchPatterns} size="sm" data-testid="refresh-patterns">
          🔄 Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-purple-50 border-purple-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-700">{summary.total_patterns}</p>
              <p className="text-sm text-purple-600">Total Patterns</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-700">{summary.high_confidence}</p>
              <p className="text-sm text-green-600">High Confidence</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-700">{summary.categories?.length || 0}</p>
              <p className="text-sm text-blue-600">Categories</p>
            </CardContent>
          </Card>
          <Card className="bg-amber-50 border-amber-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-amber-700">{recommendations.length}</p>
              <p className="text-sm text-amber-600">Actions</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="patterns" data-testid="tab-patterns">
            🔮 Patterns ({patterns.length})
          </TabsTrigger>
          <TabsTrigger value="recommendations" data-testid="tab-recommendations">
            💡 Recommendations ({recommendations.length})
          </TabsTrigger>
        </TabsList>

        {/* Patterns Tab */}
        <TabsContent value="patterns" className="mt-4">
          {patterns.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {patterns.map((pattern) => (
                <PatternCard
                  key={pattern.pattern_id}
                  pattern={pattern}
                  onViewDetails={setSelectedPattern}
                  onFeedback={handleFeedback}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">📊</span>
                <p className="text-slate-600 mt-2">
                  No patterns discovered yet. Submit more proposals to generate insights!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="mt-4">
          {recommendations.length > 0 ? (
            <div className="space-y-4">
              {recommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">💡</span>
                <p className="text-slate-600 mt-2">
                  No actionable recommendations right now. Keep submitting proposals!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Last Updated */}
      {summary?.last_updated && (
        <p className="text-xs text-slate-400 text-center">
          Last updated: {new Date(summary.last_updated).toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default CreatorPatternInsights;
