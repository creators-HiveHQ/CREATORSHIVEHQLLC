/**
 * Cross-Creator Insights Component - Phase 4 Module C
 * Displays "Creators like you..." insights from similar creators
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Users, TrendingUp, AlertTriangle, Target, Clock, 
  BarChart3, Sparkles, RefreshCw, ChevronRight, Award
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const INSIGHT_ICONS = {
  success_pattern: <TrendingUp className="w-5 h-5 text-green-500" />,
  common_mistake: <AlertTriangle className="w-5 h-5 text-amber-500" />,
  timing_insight: <Clock className="w-5 h-5 text-blue-500" />,
  platform_trend: <BarChart3 className="w-5 h-5 text-purple-500" />,
  niche_benchmark: <Award className="w-5 h-5 text-indigo-500" />
};

const INSIGHT_COLORS = {
  success_pattern: "border-green-200 bg-green-50",
  common_mistake: "border-amber-200 bg-amber-50",
  timing_insight: "border-blue-200 bg-blue-50",
  platform_trend: "border-purple-200 bg-purple-50",
  niche_benchmark: "border-indigo-200 bg-indigo-50"
};

export function CrossCreatorInsights({ token, creatorTier, onUpgrade }) {
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);

  // Check if user has Premium access
  const hasPremiumAccess = ["premium", "elite"].includes(creatorTier?.toLowerCase());

  useEffect(() => {
    if (token && hasPremiumAccess) {
      fetchInsights();
    } else {
      setLoading(false);
    }
  }, [token, hasPremiumAccess]);

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API}/creators/me/cross-insights?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setInsights(data.insights || []);
        setMetadata({
          similarCreators: data.similar_creators_found,
          generatedAt: data.generated_at
        });
      } else {
        setError("Failed to load insights");
      }
    } catch (err) {
      setError("Failed to load insights");
      console.error("Cross-creator insights error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Non-Premium upgrade prompt
  if (!hasPremiumAccess) {
    return (
      <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200" data-testid="insights-upgrade-prompt">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
            <Users className="w-10 h-10 text-indigo-600" />
          </div>
          <h2 className="text-2xl font-bold text-indigo-800 mb-3">Cross-Creator Insights</h2>
          <p className="text-indigo-600 max-w-md mx-auto mb-6">
            Learn from creators like you! Get anonymous insights about what successful 
            similar creators do differently.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <TrendingUp className="w-6 h-6 mx-auto text-green-500" />
              <p className="text-xs text-slate-600 mt-2">Success Patterns</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <AlertTriangle className="w-6 h-6 mx-auto text-amber-500" />
              <p className="text-xs text-slate-600 mt-2">Mistakes to Avoid</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <BarChart3 className="w-6 h-6 mx-auto text-purple-500" />
              <p className="text-xs text-slate-600 mt-2">Platform Trends</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <Award className="w-6 h-6 mx-auto text-indigo-500" />
              <p className="text-xs text-slate-600 mt-2">Peer Benchmarks</p>
            </div>
          </div>
          <Badge className="bg-amber-100 text-amber-800 mb-4">Premium Feature</Badge>
          <br />
          <Button 
            onClick={onUpgrade}
            className="bg-indigo-600 hover:bg-indigo-700 mt-4"
            data-testid="upgrade-to-premium-btn"
          >
            ⚡ Upgrade to Premium
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="border-indigo-200">
        <CardContent className="py-12 text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-500" />
          <p className="text-slate-500 mt-2">Analyzing similar creators...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="w-8 h-8 mx-auto text-red-500 mb-2" />
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchInsights} variant="outline" className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="cross-creator-insights">
      {/* Header */}
      <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-0">
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Creators Like You</h2>
                <p className="text-indigo-100 text-sm">
                  Insights from {metadata?.similarCreators || 0} similar creators
                </p>
              </div>
            </div>
            <Button 
              onClick={fetchInsights}
              variant="secondary"
              size="sm"
              className="bg-white/20 hover:bg-white/30 text-white border-0"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* No insights message */}
      {insights.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <Sparkles className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-700">Building Your Insights</h3>
            <p className="text-slate-500 max-w-md mx-auto">
              As more similar creators join and submit proposals, we&apos;ll generate 
              personalized insights for you. Keep submitting proposals!
            </p>
          </CardContent>
        </Card>
      )}

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, idx) => (
          <Card 
            key={idx}
            className={`${INSIGHT_COLORS[insight.type] || "border-slate-200 bg-slate-50"} transition-all hover:shadow-md`}
            data-testid={`insight-${insight.type}`}
          >
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  {INSIGHT_ICONS[insight.type] || <Sparkles className="w-5 h-5 text-slate-500" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-semibold text-slate-800">{insight.title}</h3>
                    {insight.confidence && (
                      <Badge variant="outline" className="text-xs">
                        {Math.round(insight.confidence * 100)}% conf
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{insight.description}</p>
                  
                  {/* Recommendation */}
                  {insight.recommendation && (
                    <div className="mt-2 p-2 bg-white/60 rounded-lg">
                      <p className="text-sm font-medium text-slate-700 flex items-center gap-1">
                        <ChevronRight className="w-4 h-4" />
                        {insight.recommendation}
                      </p>
                    </div>
                  )}

                  {/* Data points */}
                  {insight.data && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {insight.data.your_approval_rate !== undefined && (
                        <Badge variant="secondary" className="text-xs">
                          Your rate: {insight.data.your_approval_rate}%
                        </Badge>
                      )}
                      {insight.data.peer_avg_rate !== undefined && (
                        <Badge variant="secondary" className="text-xs">
                          Peer avg: {insight.data.peer_avg_rate}%
                        </Badge>
                      )}
                      {insight.data.percentile !== undefined && (
                        <Badge variant="secondary" className="text-xs">
                          Top {100 - insight.data.percentile}%
                        </Badge>
                      )}
                      {insight.data.platform && (
                        <Badge variant="secondary" className="text-xs">
                          {insight.data.platform}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Footer note */}
      <p className="text-xs text-slate-400 text-center">
        Insights are generated from anonymized data. No individual creator information is shared.
      </p>
    </div>
  );
}

export default CrossCreatorInsights;
