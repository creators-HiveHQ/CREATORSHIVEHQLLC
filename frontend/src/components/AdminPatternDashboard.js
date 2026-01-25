/**
 * Admin Pattern Dashboard - Phase 4 Module A
 * Platform-wide pattern detection and analytics visualization
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { 
  TrendingUp, TrendingDown, Users, FileText, DollarSign, 
  AlertTriangle, CheckCircle, Activity, Brain, RefreshCw,
  ArrowUpRight, ArrowDownRight, Minus, BarChart3, PieChart
} from "lucide-react";
import {
  LineChart, Line, BarChart, Bar, PieChart as RechartsPie, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color palette for charts
const COLORS = {
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  purple: "#8b5cf6",
  teal: "#14b8a6",
  pink: "#ec4899"
};

const TIER_COLORS = {
  Free: "#94a3b8",
  Starter: "#3b82f6",
  Pro: "#8b5cf6",
  Premium: "#f59e0b",
  Elite: "#ec4899"
};

export function AdminPatternDashboard({ token }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Data states
  const [overview, setOverview] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [cohorts, setCohorts] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [insights, setInsights] = useState([]);
  const [churnRisk, setChurnRisk] = useState(null);
  
  // Filters
  const [rankingSort, setRankingSort] = useState("approval_rate");
  const [rankingTier, setRankingTier] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    const headers = { Authorization: `Bearer ${token}` };
    
    try {
      // Fetch all data in parallel
      const [
        overviewRes, patternsRes, cohortsRes, rankingsRes, 
        revenueRes, insightsRes, churnRes
      ] = await Promise.all([
        fetch(`${API}/admin/patterns/overview`, { headers }),
        fetch(`${API}/admin/patterns/detect`, { headers }),
        fetch(`${API}/admin/patterns/cohorts`, { headers }),
        fetch(`${API}/admin/patterns/rankings?sort_by=${rankingSort}${rankingTier !== "all" ? `&tier=${rankingTier}` : ""}`, { headers }),
        fetch(`${API}/admin/patterns/revenue`, { headers }),
        fetch(`${API}/admin/patterns/insights`, { headers }),
        fetch(`${API}/admin/patterns/churn-risk`, { headers })
      ]);

      if (!overviewRes.ok) throw new Error("Failed to fetch overview");
      
      setOverview(await overviewRes.json());
      setPatterns(await patternsRes.json());
      setCohorts(await cohortsRes.json());
      setRankings(await rankingsRes.json());
      setRevenue(await revenueRes.json());
      setInsights(await insightsRes.json());
      setChurnRisk(await churnRes.json());
      
    } catch (err) {
      setError(err.message);
      console.error("Pattern dashboard error:", err);
    } finally {
      setLoading(false);
    }
  }, [token, rankingSort, rankingTier]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token, fetchData]);

  // Refresh rankings when filters change
  const refreshRankings = async () => {
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await fetch(
        `${API}/admin/patterns/rankings?sort_by=${rankingSort}${rankingTier !== "all" ? `&tier=${rankingTier}` : ""}`, 
        { headers }
      );
      if (res.ok) {
        setRankings(await res.json());
      }
    } catch (err) {
      console.error("Failed to refresh rankings:", err);
    }
  };

  useEffect(() => {
    if (token && !loading) {
      refreshRankings();
    }
  }, [rankingSort, rankingTier]);

  const TrendIndicator = ({ value, suffix = "%" }) => {
    if (value > 0) {
      return (
        <span className="flex items-center text-green-600 text-sm">
          <ArrowUpRight className="w-4 h-4" />
          {value.toFixed(1)}{suffix}
        </span>
      );
    } else if (value < 0) {
      return (
        <span className="flex items-center text-red-600 text-sm">
          <ArrowDownRight className="w-4 h-4" />
          {Math.abs(value).toFixed(1)}{suffix}
        </span>
      );
    }
    return (
      <span className="flex items-center text-slate-500 text-sm">
        <Minus className="w-4 h-4" />
        {value.toFixed(1)}{suffix}
      </span>
    );
  };

  const HealthIndicator = ({ score, label }) => {
    const color = score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : score >= 40 ? "bg-orange-500" : "bg-red-500";
    return (
      <div className="flex flex-col items-center">
        <div className={`w-16 h-16 rounded-full ${color} flex items-center justify-center text-white font-bold text-xl`}>
          {score}
        </div>
        <span className="text-xs text-slate-500 mt-1">{label}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-2 text-slate-600">Analyzing patterns...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-red-700">Failed to Load Patterns</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={fetchData} variant="outline">Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-pattern-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">ARRIS Pattern Engine</h1>
            <p className="text-sm text-slate-500">Platform-wide pattern detection & analytics</p>
          </div>
        </div>
        <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-patterns">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Actionable Insights */}
      {insights.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {insights.slice(0, 4).map((insight) => (
            <Card 
              key={insight.id}
              className={`border-l-4 ${
                insight.type === "warning" ? "border-l-amber-500 bg-amber-50" :
                insight.type === "success" ? "border-l-green-500 bg-green-50" :
                "border-l-blue-500 bg-blue-50"
              }`}
              data-testid={`insight-${insight.id}`}
            >
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div>
                    <Badge 
                      className={`mb-2 ${
                        insight.priority === "high" ? "bg-red-100 text-red-700" :
                        insight.priority === "medium" ? "bg-yellow-100 text-yellow-700" :
                        "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {insight.priority.toUpperCase()}
                    </Badge>
                    <h3 className="font-semibold text-slate-800 text-sm">{insight.title}</h3>
                    <p className="text-xs text-slate-600 mt-1">{insight.description}</p>
                  </div>
                  {insight.type === "warning" && <AlertTriangle className="w-5 h-5 text-amber-500" />}
                  {insight.type === "success" && <CheckCircle className="w-5 h-5 text-green-500" />}
                  {insight.type === "opportunity" && <TrendingUp className="w-5 h-5 text-blue-500" />}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="patterns" data-testid="tab-patterns">Patterns</TabsTrigger>
          <TabsTrigger value="cohorts" data-testid="tab-cohorts">Cohorts</TabsTrigger>
          <TabsTrigger value="rankings" data-testid="tab-rankings">Rankings</TabsTrigger>
          <TabsTrigger value="churn" data-testid="tab-churn">Churn Risk</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Platform Health */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-600" />
                Platform Health
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-around">
                <HealthIndicator 
                  score={overview?.health_indicators?.overall || 0} 
                  label="Overall" 
                />
                <HealthIndicator 
                  score={overview?.health_indicators?.engagement || 0} 
                  label="Engagement" 
                />
                <HealthIndicator 
                  score={overview?.health_indicators?.success || 0} 
                  label="Success" 
                />
                <HealthIndicator 
                  score={overview?.health_indicators?.revenue || 0} 
                  label="Revenue" 
                />
              </div>
              <div className="mt-4 text-center">
                <Badge className={`
                  ${overview?.health_indicators?.status === "excellent" ? "bg-green-100 text-green-700" :
                    overview?.health_indicators?.status === "good" ? "bg-blue-100 text-blue-700" :
                    overview?.health_indicators?.status === "fair" ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  }
                `}>
                  Status: {overview?.health_indicators?.status?.toUpperCase()}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card data-testid="metric-creators">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <Users className="w-8 h-8 text-blue-500" />
                  <TrendIndicator value={overview?.activity_30d?.registration_growth_pct || 0} />
                </div>
                <p className="text-2xl font-bold mt-2">{overview?.snapshot?.total_creators || 0}</p>
                <p className="text-xs text-slate-500">Active Creators</p>
              </CardContent>
            </Card>
            
            <Card data-testid="metric-proposals">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <FileText className="w-8 h-8 text-purple-500" />
                  <TrendIndicator value={overview?.activity_30d?.proposal_growth_pct || 0} />
                </div>
                <p className="text-2xl font-bold mt-2">{overview?.snapshot?.total_proposals || 0}</p>
                <p className="text-xs text-slate-500">Total Proposals</p>
              </CardContent>
            </Card>

            <Card data-testid="metric-subscriptions">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <DollarSign className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-2xl font-bold mt-2">{overview?.snapshot?.active_subscriptions || 0}</p>
                <p className="text-xs text-slate-500">Active Subscriptions</p>
              </CardContent>
            </Card>

            <Card data-testid="metric-mrr">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <BarChart3 className="w-8 h-8 text-amber-500" />
                </div>
                <p className="text-2xl font-bold mt-2">${revenue?.summary?.mrr?.toLocaleString() || 0}</p>
                <p className="text-xs text-slate-500">Monthly Revenue</p>
              </CardContent>
            </Card>
          </div>

          {/* 30-Day Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">30-Day Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <p className="text-sm text-slate-500 mb-1">New Proposals</p>
                  <p className="text-3xl font-bold text-purple-600">{overview?.activity_30d?.new_proposals || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">New Registrations</p>
                  <p className="text-3xl font-bold text-blue-600">{overview?.activity_30d?.new_registrations || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Patterns Tab */}
        <TabsContent value="patterns" className="space-y-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              {patterns?.total_patterns || 0} patterns detected
            </p>
          </div>

          {/* Success Patterns */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                Success Patterns
              </CardTitle>
              <CardDescription>What&apos;s working well across the platform</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {patterns?.success_patterns?.map((pattern, idx) => (
                  <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-100">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-green-800">{pattern.title}</h4>
                        <p className="text-sm text-green-600">{pattern.description}</p>
                        {pattern.recommendation && (
                          <p className="text-xs text-green-700 mt-1 italic">💡 {pattern.recommendation}</p>
                        )}
                      </div>
                      <Badge className="bg-green-100 text-green-700">
                        {(pattern.confidence * 100).toFixed(0)}% conf
                      </Badge>
                    </div>
                  </div>
                ))}
                {(!patterns?.success_patterns || patterns.success_patterns.length === 0) && (
                  <p className="text-slate-500 text-sm">No success patterns detected yet</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Risk Patterns */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Risk Patterns
              </CardTitle>
              <CardDescription>Areas needing attention</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {patterns?.risk_patterns?.map((pattern, idx) => (
                  <div key={idx} className="p-3 bg-amber-50 rounded-lg border border-amber-100">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-amber-800">{pattern.title}</h4>
                        <p className="text-sm text-amber-600">{pattern.description}</p>
                        {pattern.recommendation && (
                          <p className="text-xs text-amber-700 mt-1 italic">⚠️ {pattern.recommendation}</p>
                        )}
                      </div>
                      <Badge className="bg-amber-100 text-amber-700">
                        {(pattern.confidence * 100).toFixed(0)}% conf
                      </Badge>
                    </div>
                  </div>
                ))}
                {(!patterns?.risk_patterns || patterns.risk_patterns.length === 0) && (
                  <p className="text-slate-500 text-sm">No risk patterns detected</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Engagement & Revenue Patterns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Engagement Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {patterns?.engagement_patterns?.map((pattern, idx) => (
                    <div key={idx} className="p-3 bg-blue-50 rounded-lg">
                      <h4 className="font-medium text-blue-800">{pattern.title}</h4>
                      <p className="text-sm text-blue-600">{pattern.description}</p>
                    </div>
                  ))}
                  {(!patterns?.engagement_patterns || patterns.engagement_patterns.length === 0) && (
                    <p className="text-slate-500 text-sm">No engagement patterns detected</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Revenue Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {patterns?.revenue_patterns?.map((pattern, idx) => (
                    <div key={idx} className="p-3 bg-purple-50 rounded-lg">
                      <h4 className="font-medium text-purple-800">{pattern.title}</h4>
                      <p className="text-sm text-purple-600">{pattern.description}</p>
                    </div>
                  ))}
                  {(!patterns?.revenue_patterns || patterns.revenue_patterns.length === 0) && (
                    <p className="text-slate-500 text-sm">No revenue patterns detected</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Cohorts Tab */}
        <TabsContent value="cohorts" className="space-y-6">
          {/* Tier Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <PieChart className="w-5 h-5 text-purple-600" />
                Creator Distribution by Tier
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPie>
                      <Pie
                        data={Object.entries(cohorts?.by_tier || {}).map(([tier, data]) => ({
                          name: tier || "Free",
                          value: data.count
                        }))}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {Object.keys(cohorts?.by_tier || {}).map((tier, index) => (
                          <Cell key={tier} fill={TIER_COLORS[tier] || COLORS.info} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPie>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-3">
                  {Object.entries(cohorts?.by_tier || {}).map(([tier, data]) => (
                    <div key={tier} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: TIER_COLORS[tier] || COLORS.info }}
                        />
                        <span className="font-medium">{tier || "Free"}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{data.count} creators</p>
                        <p className="text-xs text-slate-500">
                          {data.approval_rate}% approval • {data.avg_proposals_per_creator} avg proposals
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Engagement Cohorts */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Engagement Levels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(cohorts?.by_engagement || {}).map(([level, data]) => (
                  <div key={level} className="text-center p-4 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-slate-800">{data.count}</p>
                    <p className="text-sm font-medium text-slate-600 capitalize">{level.replace("_", " ")}</p>
                    <p className="text-xs text-slate-400">{data.criteria}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Monthly Retention */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Monthly Cohort Retention</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={cohorts?.by_registration_month?.slice(0, 6) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="retained" fill={COLORS.success} name="Retained" />
                    <Bar dataKey="churned" fill={COLORS.danger} name="Churned" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rankings Tab */}
        <TabsContent value="rankings" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Top Creators</CardTitle>
                <div className="flex items-center gap-2">
                  <Select value={rankingSort} onValueChange={setRankingSort}>
                    <SelectTrigger className="w-40" data-testid="ranking-sort">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="approval_rate">Approval Rate</SelectItem>
                      <SelectItem value="total_proposals">Total Proposals</SelectItem>
                      <SelectItem value="approved_proposals">Approved</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={rankingTier} onValueChange={setRankingTier}>
                    <SelectTrigger className="w-32" data-testid="ranking-tier">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Tiers</SelectItem>
                      <SelectItem value="Free">Free</SelectItem>
                      <SelectItem value="Starter">Starter</SelectItem>
                      <SelectItem value="Pro">Pro</SelectItem>
                      <SelectItem value="Premium">Premium</SelectItem>
                      <SelectItem value="Elite">Elite</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {rankings.map((creator, idx) => (
                  <div 
                    key={creator.creator_id} 
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center font-bold text-white
                        ${idx === 0 ? "bg-amber-500" : idx === 1 ? "bg-slate-400" : idx === 2 ? "bg-amber-700" : "bg-slate-300"}
                      `}>
                        {idx + 1}
                      </div>
                      <div>
                        <p className="font-medium">{creator.name}</p>
                        <p className="text-xs text-slate-500">{creator.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge style={{ backgroundColor: TIER_COLORS[creator.tier] || "#94a3b8" }} className="text-white">
                        {creator.tier}
                      </Badge>
                      <div className="text-right">
                        <p className="font-bold text-green-600">{creator.approval_rate}%</p>
                        <p className="text-xs text-slate-500">
                          {creator.approved_proposals}/{creator.total_proposals} approved
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {rankings.length === 0 && (
                  <p className="text-center text-slate-500 py-8">No creators found</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Churn Risk Tab */}
        <TabsContent value="churn" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-red-200 bg-red-50">
              <CardContent className="py-4 text-center">
                <AlertTriangle className="w-8 h-8 mx-auto text-red-500 mb-2" />
                <p className="text-3xl font-bold text-red-600">{churnRisk?.high_risk_count || 0}</p>
                <p className="text-sm text-red-700">High Risk</p>
              </CardContent>
            </Card>
            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="py-4 text-center">
                <Activity className="w-8 h-8 mx-auto text-amber-500 mb-2" />
                <p className="text-3xl font-bold text-amber-600">{churnRisk?.medium_risk_count || 0}</p>
                <p className="text-sm text-amber-700">Medium Risk</p>
              </CardContent>
            </Card>
            <Card className="border-slate-200 bg-slate-50">
              <CardContent className="py-4 text-center">
                <Users className="w-8 h-8 mx-auto text-slate-500 mb-2" />
                <p className="text-3xl font-bold text-slate-600">{churnRisk?.total_at_risk || 0}</p>
                <p className="text-sm text-slate-700">Total At Risk</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">At-Risk Creators</CardTitle>
              <CardDescription>Creators showing signs of disengagement</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {churnRisk?.at_risk_creators?.slice(0, 20).map((creator) => (
                  <div 
                    key={creator.creator_id}
                    className={`p-4 rounded-lg border ${
                      creator.risk_level === "high" ? "bg-red-50 border-red-200" : "bg-amber-50 border-amber-200"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{creator.creator_name}</h4>
                          <Badge className={creator.risk_level === "high" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}>
                            {creator.risk_level.toUpperCase()} RISK
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-500">{creator.creator_email}</p>
                        <div className="mt-2">
                          <p className="text-xs font-medium text-slate-600">Risk Factors:</p>
                          <ul className="text-xs text-slate-500 list-disc list-inside">
                            {creator.risk_factors?.map((factor, idx) => (
                              <li key={idx}>{factor}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-slate-700">{creator.risk_score}</div>
                        <p className="text-xs text-slate-500">Risk Score</p>
                      </div>
                    </div>
                    {creator.recommendation && (
                      <p className="mt-2 text-xs italic text-slate-600">💡 {creator.recommendation}</p>
                    )}
                  </div>
                ))}
                {(!churnRisk?.at_risk_creators || churnRisk.at_risk_creators.length === 0) && (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 mx-auto text-green-500 mb-2" />
                    <p className="text-slate-500">No creators at significant churn risk</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AdminPatternDashboard;
