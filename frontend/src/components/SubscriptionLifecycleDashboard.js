/**
 * Subscription Lifecycle Dashboard (Module B3)
 * Admin dashboard for monitoring subscription health and managing at-risk subscriptions.
 * Features: health metrics, at-risk list, retention actions, lifecycle tracking.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Risk level styles
const RISK_STYLES = {
  critical: { bg: "bg-red-100", border: "border-red-300", text: "text-red-700", badge: "bg-red-500" },
  high: { bg: "bg-orange-100", border: "border-orange-300", text: "text-orange-700", badge: "bg-orange-500" },
  medium: { bg: "bg-amber-100", border: "border-amber-300", text: "text-amber-700", badge: "bg-amber-500" },
  low: { bg: "bg-green-100", border: "border-green-300", text: "text-green-700", badge: "bg-green-500" },
};

// Lifecycle stage styles
const STAGE_STYLES = {
  onboarding: { color: "bg-blue-500", label: "Onboarding" },
  activation: { color: "bg-cyan-500", label: "Activation" },
  engaged: { color: "bg-green-500", label: "Engaged" },
  at_risk: { color: "bg-amber-500", label: "At Risk" },
  churning: { color: "bg-red-500", label: "Churning" },
  churned: { color: "bg-slate-500", label: "Churned" },
  reactivated: { color: "bg-purple-500", label: "Reactivated" },
};

// Retention actions
const RETENTION_ACTIONS = [
  { value: "welcome_email", label: "Send Welcome Email" },
  { value: "onboarding_reminder", label: "Onboarding Reminder" },
  { value: "feature_highlight", label: "Feature Highlight" },
  { value: "engagement_nudge", label: "Engagement Nudge" },
  { value: "success_celebration", label: "Success Celebration" },
  { value: "at_risk_outreach", label: "At-Risk Outreach" },
  { value: "discount_offer", label: "Discount Offer" },
  { value: "personal_call", label: "Schedule Personal Call" },
  { value: "win_back_campaign", label: "Win-Back Campaign" },
];

/**
 * Health Score Ring Component
 */
const HealthScoreRing = ({ score, size = "lg" }) => {
  const radius = size === "lg" ? 60 : 40;
  const stroke = size === "lg" ? 8 : 6;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  
  const getColor = (score) => {
    if (score >= 70) return "#22c55e";
    if (score >= 40) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={radius * 2 + stroke * 2} height={radius * 2 + stroke * 2}>
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
        />
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          transform={`rotate(-90 ${radius + stroke} ${radius + stroke})`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold ${size === "lg" ? "text-3xl" : "text-xl"}`}>{score}</span>
        <span className="text-xs text-slate-500">Health</span>
      </div>
    </div>
  );
};

/**
 * At-Risk Subscription Card
 */
const AtRiskCard = ({ subscription, onAction }) => {
  const riskStyle = RISK_STYLES[subscription.risk_level] || RISK_STYLES.medium;
  const stageStyle = STAGE_STYLES[subscription.lifecycle_stage] || STAGE_STYLES.engaged;

  return (
    <Card className={`${riskStyle.bg} ${riskStyle.border} border`} data-testid={`at-risk-${subscription.creator_id}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="font-semibold">{subscription.email}</span>
              <Badge className={`${riskStyle.badge} text-white`}>{subscription.risk_level}</Badge>
              <Badge variant="outline" className={stageStyle.color.replace("bg-", "text-")}>
                {stageStyle.label}
              </Badge>
              <Badge variant="outline">{subscription.tier?.toUpperCase()}</Badge>
            </div>
            
            {/* Risk factors */}
            {subscription.top_risk_factors?.length > 0 && (
              <div className="flex gap-2 mb-2">
                {subscription.top_risk_factors.map((factor, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {factor.replace(/_/g, " ")}
                  </Badge>
                ))}
              </div>
            )}
            
            <p className="text-sm text-slate-600">
              {subscription.days_remaining !== null 
                ? `${subscription.days_remaining} days remaining`
                : "Subscription details unavailable"}
            </p>
          </div>
          
          {/* Health score */}
          <div className="text-center ml-4">
            <HealthScoreRing score={subscription.health_score} size="sm" />
          </div>
        </div>
        
        {/* Quick actions */}
        <div className="flex gap-2 mt-3">
          <Button size="sm" variant="outline" onClick={() => onAction(subscription, "engagement_nudge")}>
            📧 Nudge
          </Button>
          <Button size="sm" variant="outline" onClick={() => onAction(subscription, "at_risk_outreach")}>
            📞 Outreach
          </Button>
          <Button size="sm" onClick={() => onAction(subscription, null)}>
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Retention Action Modal
 */
const RetentionActionModal = ({ subscription, isOpen, onClose, onSubmit, token }) => {
  const [selectedAction, setSelectedAction] = useState("");
  const [customMessage, setCustomMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!selectedAction) return;
    
    setSubmitting(true);
    try {
      await onSubmit(subscription.creator_id, selectedAction, customMessage);
      onClose();
    } catch (err) {
      console.error("Error triggering action:", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (!subscription) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Subscription Details</DialogTitle>
          <DialogDescription>{subscription.email}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Health score */}
          <div className="flex items-center justify-center">
            <HealthScoreRing score={subscription.health_score} size="lg" />
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{subscription.tier?.toUpperCase()}</p>
              <p className="text-xs text-slate-500">Tier</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{subscription.days_remaining ?? "N/A"}</p>
              <p className="text-xs text-slate-500">Days Remaining</p>
            </div>
          </div>
          
          {/* Recommendations */}
          {subscription.recommendations?.length > 0 && (
            <div>
              <Label className="text-sm font-medium">Recommendations</Label>
              <div className="space-y-2 mt-2">
                {subscription.recommendations.map((rec, i) => (
                  <div key={i} className="p-2 bg-slate-50 rounded text-sm">
                    <p className="font-medium">{rec.title}</p>
                    <p className="text-slate-600 text-xs">{rec.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Action selection */}
          <div>
            <Label>Trigger Retention Action</Label>
            <Select value={selectedAction} onValueChange={setSelectedAction}>
              <SelectTrigger className="mt-2">
                <SelectValue placeholder="Select an action..." />
              </SelectTrigger>
              <SelectContent>
                {RETENTION_ACTIONS.map((action) => (
                  <SelectItem key={action.value} value={action.value}>
                    {action.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Custom message */}
          {selectedAction && (
            <div>
              <Label>Custom Message (optional)</Label>
              <Textarea
                className="mt-2"
                placeholder="Add a personalized message..."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!selectedAction || submitting}>
            {submitting ? "Sending..." : "Trigger Action"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Main Subscription Lifecycle Dashboard Component
 */
export const SubscriptionLifecycleDashboard = ({ token }) => {
  const [metrics, setMetrics] = useState(null);
  const [atRiskList, setAtRiskList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [riskThreshold, setRiskThreshold] = useState("medium");
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [showActionModal, setShowActionModal] = useState(false);
  const [retentionHistory, setRetentionHistory] = useState([]);

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = getAuthHeaders();

      const [metricsRes, atRiskRes, historyRes] = await Promise.all([
        axios.get(`${API}/admin/subscription-lifecycle/metrics`, { headers }),
        axios.get(`${API}/admin/subscription-lifecycle/at-risk?threshold=${riskThreshold}`, { headers }),
        axios.get(`${API}/admin/subscription-lifecycle/retention-history?limit=20`, { headers }).catch(() => ({ data: { actions: [] } }))
      ]);

      setMetrics(metricsRes.data);
      setAtRiskList(atRiskRes.data.at_risk_subscriptions || []);
      setRetentionHistory(historyRes.data.actions || []);
    } catch (err) {
      console.error("Error fetching lifecycle data:", err);
      setError("Failed to load subscription lifecycle data");
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, riskThreshold]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token, fetchData]);

  const handleAction = (subscription, quickAction = null) => {
    setSelectedSubscription(subscription);
    if (quickAction) {
      // Direct quick action
      triggerRetentionAction(subscription.creator_id, quickAction);
    } else {
      setShowActionModal(true);
    }
  };

  const triggerRetentionAction = async (creatorId, action, customMessage = "") => {
    try {
      const headers = getAuthHeaders();
      await axios.post(
        `${API}/admin/subscription-lifecycle/retention-action`,
        { creator_id: creatorId, action, custom_message: customMessage },
        { headers }
      );
      // Refresh data
      fetchData();
    } catch (err) {
      console.error("Error triggering retention action:", err);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card data-testid="lifecycle-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Analyzing subscription health...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200" data-testid="lifecycle-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchData} className="mt-4">Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="subscription-lifecycle-dashboard">
      {/* Retention Action Modal */}
      <RetentionActionModal
        subscription={selectedSubscription}
        isOpen={showActionModal}
        onClose={() => { setShowActionModal(false); setSelectedSubscription(null); }}
        onSubmit={triggerRetentionAction}
        token={token}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            📊 Subscription Lifecycle
          </h2>
          <p className="text-sm text-slate-600">Monitor health and manage at-risk subscriptions</p>
        </div>
        <Button variant="outline" onClick={fetchData} data-testid="refresh-lifecycle">
          🔄 Refresh
        </Button>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-700">{metrics.active_subscriptions}</p>
              <p className="text-sm text-blue-600">Active</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-700">{metrics.health_distribution?.healthy || 0}</p>
              <p className="text-sm text-green-600">Healthy</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-amber-700">{metrics.health_distribution?.at_risk || 0}</p>
              <p className="text-sm text-amber-600">At Risk</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-700">{metrics.health_distribution?.critical || 0}</p>
              <p className="text-sm text-red-600">Critical</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-slate-700">{metrics.churn_metrics?.churn_rate_30d?.toFixed(1)}%</p>
              <p className="text-sm text-slate-600">30d Churn</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-overview">📈 Overview</TabsTrigger>
          <TabsTrigger value="at-risk" data-testid="tab-at-risk">
            ⚠️ At Risk ({atRiskList.length})
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">📜 Action History</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Lifecycle Stages */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Lifecycle Stages</CardTitle>
              </CardHeader>
              <CardContent>
                {metrics?.lifecycle_stages && (
                  <div className="space-y-3">
                    {Object.entries(STAGE_STYLES).map(([stage, style]) => {
                      const count = metrics.lifecycle_stages[stage] || 0;
                      const total = Object.values(metrics.lifecycle_stages).reduce((a, b) => a + b, 0) || 1;
                      const percentage = (count / total) * 100;
                      
                      return (
                        <div key={stage} className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${style.color}`}></div>
                          <span className="flex-1 text-sm">{style.label}</span>
                          <span className="text-sm font-medium">{count}</span>
                          <Progress value={percentage} className="w-24 h-2" />
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tier Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tier Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {metrics?.tier_distribution && (
                  <div className="space-y-3">
                    {Object.entries(metrics.tier_distribution).map(([tier, count]) => {
                      const total = Object.values(metrics.tier_distribution).reduce((a, b) => a + b, 0) || 1;
                      const percentage = (count / total) * 100;
                      
                      return (
                        <div key={tier} className="flex items-center gap-3">
                          <Badge variant="outline">{tier.toUpperCase()}</Badge>
                          <span className="flex-1 text-sm">{count} subscribers</span>
                          <Progress value={percentage} className="w-24 h-2" />
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* At Risk Tab */}
        <TabsContent value="at-risk" className="mt-4">
          {/* Filter */}
          <div className="flex items-center gap-4 mb-4">
            <Label>Risk Threshold:</Label>
            <Select value={riskThreshold} onValueChange={setRiskThreshold}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="critical">Critical Only</SelectItem>
                <SelectItem value="high">High & Critical</SelectItem>
                <SelectItem value="medium">Medium & Above</SelectItem>
                <SelectItem value="low">All</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* At Risk List */}
          {atRiskList.length > 0 ? (
            <div className="space-y-4">
              {atRiskList.map((sub) => (
                <AtRiskCard key={sub.creator_id} subscription={sub} onAction={handleAction} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">✨</span>
                <p className="text-slate-600 mt-2">
                  No subscriptions at this risk level. Great news!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-4">
          {retentionHistory.length > 0 ? (
            <div className="space-y-2">
              {retentionHistory.map((action) => (
                <Card key={action.id} className="bg-slate-50">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium">{action.action?.replace(/_/g, " ")}</p>
                      <p className="text-sm text-slate-600">
                        Creator: {action.creator_id} • Triggered by: {action.triggered_by}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={action.status === "completed" ? "default" : "secondary"}>
                        {action.status}
                      </Badge>
                      <p className="text-xs text-slate-400 mt-1">
                        {new Date(action.created_at).toLocaleString()}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">📜</span>
                <p className="text-slate-600 mt-2">No retention actions recorded yet.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SubscriptionLifecycleDashboard;
