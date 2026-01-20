/**
 * ARRIS Learning History Component for Creators Hive HQ
 * Historical comparison visualization showing how ARRIS has learned about the creator over time
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Learning stage colors and icons
const LEARNING_STAGES = {
  initializing: { color: "bg-slate-500", icon: "🌱", label: "Initializing" },
  learning: { color: "bg-blue-500", icon: "📚", label: "Learning" },
  developing: { color: "bg-purple-500", icon: "🔬", label: "Developing" },
  calibrating: { color: "bg-amber-500", icon: "⚙️", label: "Calibrating" },
  proficient: { color: "bg-green-500", icon: "🎯", label: "Proficient" },
  expert: { color: "bg-emerald-500", icon: "🏆", label: "Expert" }
};

// Milestone icons
const MILESTONE_ICONS = {
  first_memory: "🧠",
  first_pattern: "🔮",
  memories_10: "📚",
  memories_25: "📖",
  memories_50: "🎓",
  memories_100: "🏆",
  high_accuracy: "🎯"
};

// Health Score Indicator
const HealthScoreIndicator = ({ healthScore }) => {
  if (!healthScore) return null;
  
  const getColorClass = (score) => {
    if (score >= 80) return "from-green-500 to-emerald-500";
    if (score >= 60) return "from-blue-500 to-indigo-500";
    if (score >= 40) return "from-amber-500 to-orange-500";
    if (score >= 20) return "from-orange-500 to-red-500";
    return "from-slate-400 to-slate-500";
  };
  
  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl border" data-testid="health-score">
      <div className="text-center mb-4">
        <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br ${getColorClass(healthScore.score)} text-white shadow-lg`}>
          <span className="text-3xl font-bold">{healthScore.score}</span>
        </div>
        <h3 className="text-lg font-semibold text-slate-800 mt-3">{healthScore.status?.toUpperCase()}</h3>
        <p className="text-sm text-slate-500">{healthScore.message}</p>
      </div>
      
      <div className="space-y-3 mt-6">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-600">Memory Score</span>
            <span className="font-medium">{healthScore.breakdown?.memory_score || 0}/40</span>
          </div>
          <Progress value={(healthScore.breakdown?.memory_score || 0) / 40 * 100} className="h-2" />
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-600">Pattern Score</span>
            <span className="font-medium">{healthScore.breakdown?.pattern_score || 0}/30</span>
          </div>
          <Progress value={(healthScore.breakdown?.pattern_score || 0) / 30 * 100} className="h-2" />
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-600">Accuracy Score</span>
            <span className="font-medium">{healthScore.breakdown?.accuracy_score || 0}/30</span>
          </div>
          <Progress value={(healthScore.breakdown?.accuracy_score || 0) / 30 * 100} className="h-2" />
        </div>
      </div>
      
      <div className="mt-4 p-3 bg-white rounded-lg border border-slate-200">
        <p className="text-xs text-slate-600">💡 <strong>Tip:</strong> {healthScore.recommendation}</p>
      </div>
    </div>
  );
};

// Learning Stage Display
const LearningStageDisplay = ({ metrics }) => {
  if (!metrics) return null;
  
  const stage = LEARNING_STAGES[metrics.learning_stage] || LEARNING_STAGES.initializing;
  
  return (
    <div className="p-4 bg-white rounded-lg border" data-testid="learning-stage">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-12 h-12 rounded-full ${stage.color} flex items-center justify-center text-2xl`}>
          {stage.icon}
        </div>
        <div>
          <h4 className="font-semibold text-slate-800">{stage.label}</h4>
          <p className="text-xs text-slate-500">{metrics.stage_description}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-3 mt-4">
        <div className="text-center p-2 bg-slate-50 rounded">
          <p className="text-lg font-bold text-slate-700">{metrics.total_predictions}</p>
          <p className="text-xs text-slate-500">Predictions</p>
        </div>
        <div className="text-center p-2 bg-green-50 rounded">
          <p className="text-lg font-bold text-green-600">{metrics.accurate_predictions}</p>
          <p className="text-xs text-green-600">Accurate</p>
        </div>
        <div className="text-center p-2 bg-purple-50 rounded">
          <p className="text-lg font-bold text-purple-600">{metrics.accuracy_rate}%</p>
          <p className="text-xs text-purple-600">Rate</p>
        </div>
      </div>
    </div>
  );
};

// Milestones Timeline
const MilestonesTimeline = ({ milestones }) => {
  if (!milestones || milestones.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <span className="text-3xl block mb-2">🌱</span>
        <p>No milestones yet</p>
        <p className="text-xs mt-1">Submit proposals to start your learning journey</p>
      </div>
    );
  }
  
  return (
    <div className="relative" data-testid="milestones-timeline">
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 to-blue-500" />
      
      <div className="space-y-4 pl-10">
        {milestones.map((milestone, idx) => (
          <div key={idx} className="relative">
            <div className="absolute -left-10 w-8 h-8 rounded-full bg-white border-2 border-purple-500 flex items-center justify-center text-lg shadow-sm">
              {milestone.icon || MILESTONE_ICONS[milestone.type] || "⭐"}
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200 hover:border-purple-300 transition-colors">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-slate-800">{milestone.title}</h4>
                <span className="text-xs text-slate-400">{milestone.date}</span>
              </div>
              <p className="text-sm text-slate-500 mt-1">{milestone.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Pattern Card
const PatternCard = ({ pattern }) => {
  const categoryColors = {
    success: "bg-green-100 text-green-700 border-green-200",
    risk: "bg-red-100 text-red-700 border-red-200",
    timing: "bg-blue-100 text-blue-700 border-blue-200",
    complexity: "bg-purple-100 text-purple-700 border-purple-200",
    platform: "bg-amber-100 text-amber-700 border-amber-200"
  };
  
  return (
    <div className={`p-4 rounded-lg border ${categoryColors[pattern.category] || "bg-slate-100 text-slate-700 border-slate-200"}`}>
      <div className="flex items-start justify-between">
        <div>
          <Badge variant="outline" className="mb-2 text-xs">
            {pattern.category?.toUpperCase()}
          </Badge>
          <h4 className="font-medium">{pattern.title}</h4>
          <p className="text-sm opacity-80 mt-1">{pattern.description}</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold">{Math.round((pattern.confidence || 0) * 100)}%</span>
          <p className="text-xs">confidence</p>
        </div>
      </div>
      {pattern.recommendation && (
        <div className="mt-3 p-2 bg-white/50 rounded text-sm">
          💡 {pattern.recommendation}
        </div>
      )}
    </div>
  );
};

// Comparison Card
const ComparisonCard = ({ comparison, currentStats, previousStats }) => {
  if (!comparison) return null;
  
  const metrics = [
    { key: "memories_change", label: "Memories", current: currentStats?.memories_created, previous: previousStats?.memories_created },
    { key: "patterns_change", label: "Patterns", current: currentStats?.patterns_discovered, previous: previousStats?.patterns_discovered },
    { key: "accuracy_change", label: "Accuracy", current: `${currentStats?.prediction_accuracy}%`, previous: `${previousStats?.prediction_accuracy}%` },
    { key: "interactions_change", label: "Interactions", current: currentStats?.interactions, previous: previousStats?.interactions }
  ];
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="comparison-card">
      {metrics.map((m) => {
        const change = comparison[m.key];
        const isPositive = change > 0;
        const isNeutral = change === 0;
        
        return (
          <Card key={m.key} className={`${isPositive ? "border-green-200 bg-green-50/50" : isNeutral ? "border-slate-200" : "border-red-200 bg-red-50/50"}`}>
            <CardContent className="p-4 text-center">
              <p className="text-xs text-slate-500 mb-1">{m.label}</p>
              <p className="text-xl font-bold text-slate-700">{m.current}</p>
              <div className={`text-sm font-medium ${isPositive ? "text-green-600" : isNeutral ? "text-slate-400" : "text-red-600"}`}>
                {isPositive ? "↑" : isNeutral ? "→" : "↓"} {Math.abs(change)}%
              </div>
              <p className="text-xs text-slate-400 mt-1">vs {m.previous}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// Growth Chart
const GrowthChart = ({ data, metric }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <span className="text-3xl block mb-2">📈</span>
        <p>No data available for this period</p>
      </div>
    );
  }
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: "#fff", 
            border: "1px solid #e2e8f0",
            borderRadius: "8px"
          }} 
        />
        <Area 
          type="monotone" 
          dataKey="cumulative" 
          stroke="#8b5cf6" 
          fillOpacity={1} 
          fill="url(#colorCumulative)" 
          name={`Total ${metric}`}
        />
        <Line 
          type="monotone" 
          dataKey="daily" 
          stroke="#22c55e" 
          name="Daily" 
          strokeWidth={2}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// Main Component
export const ArrisLearningHistory = ({ creatorId, hasPremiumAccess = false }) => {
  const [activeTab, setActiveTab] = useState("snapshot");
  const [snapshot, setSnapshot] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [milestones, setMilestones] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Chart options
  const [chartMetric, setChartMetric] = useState("memories");
  const [chartGranularity, setChartGranularity] = useState("daily");
  const [comparisonPeriod, setComparisonPeriod] = useState("30d");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return { Authorization: `Bearer ${token}` };
  };

  // Fetch snapshot data
  const fetchSnapshot = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/arris/learning-snapshot`, { headers });
      setSnapshot(response.data);
    } catch (err) {
      console.error("Error fetching snapshot:", err);
      if (err.response?.status !== 403) {
        setError("Failed to load learning snapshot");
      }
    }
  }, []);

  // Fetch comparison data
  const fetchComparison = useCallback(async () => {
    if (!hasPremiumAccess) return;
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(
        `${API}/arris/learning-comparison?period1=${comparisonPeriod}&period2=prev_${comparisonPeriod}`,
        { headers }
      );
      setComparison(response.data);
    } catch (err) {
      console.error("Error fetching comparison:", err);
    }
  }, [hasPremiumAccess, comparisonPeriod]);

  // Fetch chart data
  const fetchChartData = useCallback(async () => {
    if (!hasPremiumAccess) return;
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(
        `${API}/arris/growth-chart?metric=${chartMetric}&granularity=${chartGranularity}`,
        { headers }
      );
      setChartData(response.data);
    } catch (err) {
      console.error("Error fetching chart data:", err);
    }
  }, [hasPremiumAccess, chartMetric, chartGranularity]);

  // Fetch milestones
  const fetchMilestones = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/arris/milestones`, { headers });
      setMilestones(response.data.milestones);
    } catch (err) {
      console.error("Error fetching milestones:", err);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      await Promise.all([
        fetchSnapshot(),
        fetchMilestones()
      ]);
      if (hasPremiumAccess) {
        await Promise.all([
          fetchComparison(),
          fetchChartData()
        ]);
      }
      setLoading(false);
    };
    fetchAll();
  }, [fetchSnapshot, fetchComparison, fetchChartData, fetchMilestones, hasPremiumAccess]);

  // Refetch chart when options change
  useEffect(() => {
    if (hasPremiumAccess && activeTab === "growth") {
      fetchChartData();
    }
  }, [chartMetric, chartGranularity, activeTab, fetchChartData, hasPremiumAccess]);

  // Refetch comparison when period changes
  useEffect(() => {
    if (hasPremiumAccess && activeTab === "comparison") {
      fetchComparison();
    }
  }, [comparisonPeriod, activeTab, fetchComparison, hasPremiumAccess]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="arris-learning-history">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <span>🧠</span> ARRIS Learning History
            {hasPremiumAccess && <Badge className="bg-purple-500 text-white text-xs ml-2">Premium</Badge>}
          </h2>
          <p className="text-sm text-slate-500">See how ARRIS has learned about your patterns over time</p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="snapshot" data-testid="tab-snapshot">Snapshot</TabsTrigger>
          <TabsTrigger value="milestones" data-testid="tab-milestones">Milestones</TabsTrigger>
          <TabsTrigger value="growth" disabled={!hasPremiumAccess} data-testid="tab-growth">
            Growth {!hasPremiumAccess && "🔒"}
          </TabsTrigger>
          <TabsTrigger value="comparison" disabled={!hasPremiumAccess} data-testid="tab-comparison">
            Compare {!hasPremiumAccess && "🔒"}
          </TabsTrigger>
        </TabsList>

        {/* Snapshot Tab */}
        <TabsContent value="snapshot" className="space-y-6">
          {snapshot && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Health Score */}
                <HealthScoreIndicator healthScore={snapshot.health_score} />
                
                {/* Learning Stage */}
                <div className="space-y-4">
                  <LearningStageDisplay metrics={snapshot.learning_metrics} />
                  
                  {/* Memory Summary */}
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Memory Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-2xl font-bold text-purple-600">
                          {snapshot.memory_summary?.total_memories || 0}
                        </span>
                        <span className="text-sm text-slate-500">Total Memories</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(snapshot.memory_summary?.by_type || {}).slice(0, 4).map(([type, data]) => (
                          <div key={type} className="p-2 bg-slate-50 rounded flex justify-between">
                            <span className="capitalize">{type}</span>
                            <span className="font-medium">{data.count}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              {/* Active Patterns */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span>🔮</span> Active Patterns
                  </CardTitle>
                  <CardDescription>
                    Patterns ARRIS has identified about your work
                    {!hasPremiumAccess && " (showing top 3)"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {snapshot.active_patterns?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {snapshot.active_patterns.map((pattern, idx) => (
                        <PatternCard key={idx} pattern={pattern} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <span className="text-3xl block mb-2">🔍</span>
                      <p>No patterns identified yet</p>
                      <p className="text-xs mt-1">Submit more proposals to help ARRIS learn</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Upgrade Prompt for non-Premium */}
              {snapshot.upgrade_prompt && (
                <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
                  <CardContent className="py-6 text-center">
                    <p className="text-lg font-medium text-purple-800 mb-2">
                      {snapshot.upgrade_prompt.message}
                    </p>
                    <div className="flex justify-center gap-4 flex-wrap mb-4">
                      {snapshot.upgrade_prompt.features.map((f, i) => (
                        <Badge key={i} variant="outline" className="border-purple-300">
                          ✓ {f}
                        </Badge>
                      ))}
                    </div>
                    <Button className="bg-purple-600 hover:bg-purple-700">
                      ⚡ Upgrade to Premium
                    </Button>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* Milestones Tab */}
        <TabsContent value="milestones">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <span>🏆</span> Your Learning Journey
              </CardTitle>
              <CardDescription>Key milestones in your ARRIS learning history</CardDescription>
            </CardHeader>
            <CardContent>
              <MilestonesTimeline milestones={milestones} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Growth Tab (Premium) */}
        <TabsContent value="growth">
          {hasPremiumAccess && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <span>📈</span> Learning Growth
                    </CardTitle>
                    <CardDescription>Track how ARRIS knowledge grows over time</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Select value={chartMetric} onValueChange={setChartMetric}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="memories">Memories</SelectItem>
                        <SelectItem value="patterns">Patterns</SelectItem>
                        <SelectItem value="accuracy">Accuracy</SelectItem>
                        <SelectItem value="interactions">Interactions</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={chartGranularity} onValueChange={setChartGranularity}>
                      <SelectTrigger className="w-28">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <GrowthChart 
                  data={chartData?.data_points} 
                  metric={chartMetric} 
                />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Comparison Tab (Premium) */}
        <TabsContent value="comparison">
          {hasPremiumAccess && comparison && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <span>📊</span> Period Comparison
                      </CardTitle>
                      <CardDescription>
                        Compare learning between time periods
                      </CardDescription>
                    </div>
                    <Select value={comparisonPeriod} onValueChange={setComparisonPeriod}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="7d">7 Days</SelectItem>
                        <SelectItem value="30d">30 Days</SelectItem>
                        <SelectItem value="90d">90 Days</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardHeader>
                <CardContent>
                  <ComparisonCard 
                    comparison={comparison.comparisons}
                    currentStats={comparison.current_period?.stats}
                    previousStats={comparison.previous_period?.stats}
                  />
                  
                  {/* Trend Indicator */}
                  <div className="mt-6 text-center">
                    <Badge className={`text-lg px-4 py-2 ${
                      comparison.comparisons?.overall_trend === "improving" 
                        ? "bg-green-500" 
                        : comparison.comparisons?.overall_trend === "stable"
                          ? "bg-blue-500"
                          : "bg-amber-500"
                    }`}>
                      {comparison.comparisons?.overall_trend === "improving" && "📈 Learning is Improving!"}
                      {comparison.comparisons?.overall_trend === "stable" && "➡️ Learning is Stable"}
                      {comparison.comparisons?.overall_trend === "needs_attention" && "⚠️ Needs More Engagement"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ArrisLearningHistory;
