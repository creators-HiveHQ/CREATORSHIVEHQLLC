/**
 * Proposal Recommendations Component - Phase 4 Module B
 * Displays AI-generated improvement suggestions for rejected proposals
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Lightbulb, AlertCircle, CheckCircle, Target, 
  Sparkles, RefreshCw, ChevronDown, ChevronUp
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function ProposalRecommendations({ proposalId, token, onResubmit }) {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (proposalId && token) {
      fetchRecommendations();
    }
  }, [proposalId, token]);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API}/proposals/${proposalId}/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations);
      } else {
        setRecommendations(null);
      }
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async () => {
    setGenerating(true);
    setError(null);
    
    try {
      const res = await fetch(`${API}/proposals/${proposalId}/generate-recommendations`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations);
      } else {
        setError("Failed to generate recommendations");
      }
    } catch (err) {
      setError("Failed to generate recommendations");
    } finally {
      setGenerating(false);
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "title": return "📝";
      case "description": return "📄";
      case "goals": return "🎯";
      case "timeline": return "📅";
      case "platforms": return "📱";
      case "priority": return "⚡";
      default: return "💡";
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "significant": return "text-red-600 bg-red-50 border-red-200";
      case "moderate": return "text-amber-600 bg-amber-50 border-amber-200";
      case "minor": return "text-blue-600 bg-blue-50 border-blue-200";
      default: return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  if (loading) {
    return (
      <Card className="border-purple-200">
        <CardContent className="py-6 text-center">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-purple-500" />
          <p className="text-sm text-slate-500 mt-2">Loading recommendations...</p>
        </CardContent>
      </Card>
    );
  }

  if (!recommendations) {
    return (
      <Card className="border-purple-200 bg-purple-50" data-testid="no-recommendations">
        <CardContent className="py-6 text-center">
          <Lightbulb className="w-10 h-10 mx-auto text-purple-400 mb-3" />
          <h3 className="font-semibold text-purple-800">No Recommendations Yet</h3>
          <p className="text-sm text-purple-600 mb-4">
            ARRIS can analyze your proposal and suggest improvements
          </p>
          <Button 
            onClick={generateRecommendations}
            disabled={generating}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="generate-recommendations-btn"
          >
            {generating ? (
              <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
            ) : (
              <><Sparkles className="w-4 h-4 mr-2" /> Generate Recommendations</>
            )}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="proposal-recommendations">
      {/* Header Card */}
      <Card className="border-purple-200">
        <CardHeader 
          className="cursor-pointer py-4"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
                <Lightbulb className="w-5 h-5 text-white" />
              </div>
              <div>
                <CardTitle className="text-lg">ARRIS Improvement Suggestions</CardTitle>
                <CardDescription>
                  AI-generated recommendations to strengthen your proposal
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {recommendations.analysis?.improvement_potential && (
                <Badge className={
                  recommendations.analysis.improvement_potential === "high" 
                    ? "bg-green-100 text-green-700"
                    : recommendations.analysis.improvement_potential === "medium"
                    ? "bg-amber-100 text-amber-700"
                    : "bg-slate-100 text-slate-700"
                }>
                  {recommendations.analysis.improvement_potential.toUpperCase()} potential
                </Badge>
              )}
              {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </div>
          </div>
        </CardHeader>
        
        {expanded && (
          <CardContent className="pt-0">
            {/* Analysis Summary */}
            {recommendations.analysis && (
              <div className={`p-4 rounded-lg border mb-4 ${getSeverityColor(recommendations.analysis.severity)}`}>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Analysis Summary
                </h4>
                <ul className="space-y-1">
                  {recommendations.analysis.likely_issues?.map((issue, idx) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <span className="mt-1">•</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quick Wins */}
            {recommendations.quick_wins?.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium text-slate-800 mb-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Quick Wins
                </h4>
                <div className="flex flex-wrap gap-2">
                  {recommendations.quick_wins.map((win, idx) => (
                    <Badge key={idx} className="bg-green-50 text-green-700 border border-green-200">
                      ✓ {win}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Detailed Recommendations */}
            {recommendations.recommendations?.length > 0 && (
              <div className="space-y-3 mb-4">
                <h4 className="font-medium text-slate-800 flex items-center gap-2">
                  <Target className="w-4 h-4 text-purple-500" />
                  Detailed Recommendations
                </h4>
                {recommendations.recommendations.map((rec, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-start gap-2">
                      <span className="text-lg">{getCategoryIcon(rec.category)}</span>
                      <div className="flex-1">
                        <Badge variant="outline" className="mb-1 capitalize">
                          {rec.category}
                        </Badge>
                        <p className="text-sm font-medium text-red-600">{rec.issue}</p>
                        <p className="text-sm text-slate-700 mt-1">{rec.suggestion}</p>
                        {rec.example && (
                          <p className="text-xs text-slate-500 mt-1 italic">
                            Example: {rec.example}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Revised Approach */}
            {recommendations.revised_approach && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 mb-4">
                <h4 className="font-medium text-blue-800 mb-2">📋 Revised Approach</h4>
                <p className="text-sm text-blue-700">{recommendations.revised_approach}</p>
              </div>
            )}

            {/* Success Tips */}
            {recommendations.success_tips?.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium text-slate-800 mb-2">💡 Success Tips</h4>
                <ul className="space-y-1">
                  {recommendations.success_tips.map((tip, idx) => (
                    <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                      <span className="text-green-500">✓</span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Encouragement */}
            {recommendations.encouragement && (
              <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                <p className="text-sm text-purple-700 italic flex items-start gap-2">
                  <Sparkles className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  {recommendations.encouragement}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6">
              {onResubmit && (
                <Button 
                  onClick={onResubmit}
                  className="bg-purple-600 hover:bg-purple-700"
                  data-testid="resubmit-proposal-btn"
                >
                  Resubmit Improved Proposal
                </Button>
              )}
              <Button 
                onClick={generateRecommendations}
                variant="outline"
                disabled={generating}
              >
                {generating ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Regenerating...</>
                ) : (
                  <><RefreshCw className="w-4 h-4 mr-2" /> Refresh Recommendations</>
                )}
              </Button>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

export default ProposalRecommendations;
