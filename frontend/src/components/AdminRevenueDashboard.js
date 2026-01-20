/**
 * Admin Revenue Dashboard
 * Comprehensive financial analytics using Calculator service data
 * Part of the Self-Funding Loop visualization
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color palette for charts
const COLORS = {
  primary: "#8b5cf6",
  secondary: "#6366f1",
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  muted: "#64748b",
};

const PIE_COLORS = ["#8b5cf6", "#6366f1", "#3b82f6", "#22c55e", "#f59e0b", "#ef4444"];

// Format currency
const formatCurrency = (value) => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value?.toFixed(2) || 0}`;
};

// Metric Card Component
const MetricCard = ({ title, value, change, changeType, subtitle, icon, loading }) => {
  const isPositive = changeType === "positive" || (change > 0 && changeType !== "negative");
  const isNegative = changeType === "negative" || (change < 0 && changeType !== "positive");
  
  return (
    <Card className="relative overflow-hidden" data-testid={`metric-${title.toLowerCase().replace(/\s/g, "-")}`}>
      <CardContent className="pt-6">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            {loading ? (
              <div className="h-8 w-24 bg-slate-200 animate-pulse rounded mt-1" />
            ) : (
              <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
            )}
            {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
          </div>
          {icon && <span className="text-3xl opacity-80">{icon}</span>}
        </div>
        {change !== undefined && change !== null && (
          <div className={`mt-3 flex items-center text-sm ${
            isPositive ? "text-green-600" : isNegative ? "text-red-600" : "text-slate-500"
          }`}>
            <span>{isPositive ? "↑" : isNegative ? "↓" : "→"}</span>
            <span className="ml-1">{Math.abs(change).toFixed(1)}%</span>
            <span className="ml-1 text-slate-400">vs last month</span>
          </div>
        )}
      </CardContent>
      <div className={`absolute bottom-0 left-0 right-0 h-1 ${
        isPositive ? "bg-green-500" : isNegative ? "bg-red-500" : "bg-slate-300"
      }`} />
    </Card>
  );
};

// Health Indicator Badge
const HealthBadge = ({ status }) => {
  const colors = {
    excellent: "bg-green-500",
    healthy: "bg-green-400",
    good: "bg-blue-500",
    optimal: "bg-green-500",
    diversified: "bg-blue-500",
    moderate: "bg-yellow-500",
    fair: "bg-yellow-400",
    concerning: "bg-orange-500",
    low: "bg-orange-400",
    critical: "bg-red-500",
    loss: "bg-red-600",
    needs_improvement: "bg-red-400",
  };
  
  return (
    <Badge className={`${colors[status] || "bg-slate-400"} text-white`}>
      {status?.replace(/_/g, " ").toUpperCase()}
    </Badge>
  );
};

// Main Revenue Dashboard Component
export const AdminRevenueDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [revenueBreakdown, setRevenueBreakdown] = useState(null);
  const [revenueTrends, setRevenueTrends] = useState(null);
  const [profitAnalysis, setProfitAnalysis] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [selfFundingLoop, setSelfFundingLoop] = useState(null);
  const [eliteInquiries, setEliteInquiries] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState("6");
  const [activeTab, setActiveTab] = useState("overview");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    const headers = getAuthHeaders();
    
    try {
      const [
        metricsRes,
        breakdownRes,
        trendsRes,
        profitRes,
        forecastRes,
        loopRes,
        inquiriesRes,
      ] = await Promise.all([
        axios.get(`${API}/calculator/metrics/all`, { headers }),
        axios.get(`${API}/calculator/revenue/breakdown?months_back=${selectedPeriod}`, { headers }),
        axios.get(`${API}/calculator/revenue/trends?months_back=12`, { headers }),
        axios.get(`${API}/calculator/profit/analysis?months_back=${selectedPeriod}`, { headers }),
        axios.get(`${API}/calculator/forecast?months_ahead=3`, { headers }),
        axios.get(`${API}/calculator/self-funding-loop`, { headers }),
        axios.get(`${API}/elite/inquiries?limit=10`, { headers }),
      ]);

      setMetrics(metricsRes.data);
      setRevenueBreakdown(breakdownRes.data);
      setRevenueTrends(trendsRes.data);
      setProfitAnalysis(profitRes.data);
      setForecast(forecastRes.data);
      setSelfFundingLoop(loopRes.data);
      setEliteInquiries(inquiriesRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Prepare chart data
  const trendChartData = revenueTrends?.monthly_data?.map(item => ({
    month: item.month,
    revenue: item.revenue,
    transactions: item.transactions,
  })) || [];

  const profitChartData = profitAnalysis?.monthly_breakdown?.map(item => ({
    month: item.month,
    revenue: item.revenue,
    expenses: item.expenses,
    profit: item.profit,
  })) || [];

  const revenueSourceData = revenueBreakdown?.by_source 
    ? Object.entries(revenueBreakdown.by_source).map(([name, value]) => ({
        name: name.replace("Subscription: ", "").replace(" Monthly", ""),
        value,
      }))
    : [];

  const forecastChartData = forecast?.forecasts?.map(item => ({
    month: item.month,
    predicted: item.predicted_revenue,
    confidence: item.confidence,
  })) || [];

  return (
    <div className="p-6 space-y-6" data-testid="admin-revenue-dashboard">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Revenue Dashboard</h1>
          <p className="text-slate-500">Self-Funding Loop Analytics &amp; Financial Intelligence</p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-40" data-testid="period-selector">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">Last 3 months</SelectItem>
              <SelectItem value="6">Last 6 months</SelectItem>
              <SelectItem value="12">Last 12 months</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchDashboardData} variant="outline" data-testid="refresh-btn">
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="MRR"
          value={formatCurrency(metrics?.mrr?.mrr || 0)}
          change={metrics?.mrr?.mrr_growth_percent}
          subtitle={`${metrics?.mrr?.active_subscriptions || 0} active subscriptions`}
          icon="💰"
          loading={loading}
        />
        <MetricCard
          title="ARR"
          value={formatCurrency(metrics?.arr?.arr || 0)}
          change={metrics?.arr?.arr_growth_percent}
          subtitle={`Projected: ${formatCurrency(metrics?.arr?.projected_year_end || 0)}`}
          icon="📈"
          loading={loading}
        />
        <MetricCard
          title="Churn Rate"
          value={`${metrics?.churn?.churn_rate_percent?.toFixed(1) || 0}%`}
          change={-metrics?.churn?.churn_rate_percent}
          changeType={metrics?.churn?.churn_rate_percent < 5 ? "positive" : "negative"}
          subtitle={`Retention: ${metrics?.churn?.retention_rate_percent?.toFixed(1) || 100}%`}
          icon="🔄"
          loading={loading}
        />
        <MetricCard
          title="Customer LTV"
          value={formatCurrency(metrics?.ltv?.ltv || 0)}
          subtitle={`Avg lifetime: ${metrics?.ltv?.avg_lifetime_months?.toFixed(0) || 0} months`}
          icon="⭐"
          loading={loading}
        />
      </div>

      {/* Health Indicators */}
      <Card>
        <CardContent className="py-4">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Churn Health:</span>
              <HealthBadge status={metrics?.churn?.health_indicator} />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">LTV Health:</span>
              <HealthBadge status={metrics?.ltv?.health_indicator} />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Profit Health:</span>
              <HealthBadge status={profitAnalysis?.health_indicator} />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Self-Funding Loop:</span>
              <HealthBadge status={selfFundingLoop?.loop_health} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for detailed views */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-slate-100">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="revenue" data-testid="tab-revenue">Revenue</TabsTrigger>
          <TabsTrigger value="profit" data-testid="tab-profit">Profit Analysis</TabsTrigger>
          <TabsTrigger value="forecast" data-testid="tab-forecast">Forecast</TabsTrigger>
          <TabsTrigger value="loop" data-testid="tab-loop">Self-Funding Loop</TabsTrigger>
          <TabsTrigger value="elite" data-testid="tab-elite">Elite Inquiries</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Revenue Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue Trend</CardTitle>
                <CardDescription>Monthly revenue over time</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="h-64 bg-slate-100 animate-pulse rounded" />
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={trendChartData}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 12 }} />
                      <Tooltip formatter={(v) => formatCurrency(v)} />
                      <Area
                        type="monotone"
                        dataKey="revenue"
                        stroke={COLORS.primary}
                        fillOpacity={1}
                        fill="url(#colorRevenue)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
                {revenueTrends && (
                  <div className="mt-4 flex items-center gap-4 text-sm">
                    <Badge className={revenueTrends.trend === "growing" ? "bg-green-500" : revenueTrends.trend === "declining" ? "bg-red-500" : "bg-blue-500"}>
                      {revenueTrends.trend?.toUpperCase()}
                    </Badge>
                    <span className="text-slate-500">
                      Avg growth: {revenueTrends.avg_monthly_growth_percent?.toFixed(1)}%/month
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue by Source Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Revenue by Source</CardTitle>
                <CardDescription>Distribution of revenue streams</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="h-64 bg-slate-100 animate-pulse rounded" />
                ) : revenueSourceData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={revenueSourceData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {revenueSourceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => formatCurrency(v)} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-64 flex items-center justify-center text-slate-400">
                    No revenue data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Profit Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Profit Overview</CardTitle>
              <CardDescription>Revenue vs Expenses over time</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-64 bg-slate-100 animate-pulse rounded" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={profitChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(v) => formatCurrency(v)} />
                    <Legend />
                    <Bar dataKey="revenue" name="Revenue" fill={COLORS.success} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expenses" name="Expenses" fill={COLORS.danger} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="profit" name="Profit" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Revenue Tab */}
        <TabsContent value="revenue" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              title="Total Revenue"
              value={formatCurrency(revenueBreakdown?.total_revenue || 0)}
              subtitle={revenueBreakdown?.period_analyzed}
              icon="💵"
              loading={loading}
            />
            <MetricCard
              title="Avg Monthly"
              value={formatCurrency(revenueBreakdown?.avg_monthly_revenue || 0)}
              subtitle="Monthly average"
              icon="📊"
              loading={loading}
            />
            <MetricCard
              title="Top Source"
              value={revenueBreakdown?.top_revenue_source?.replace("Subscription: ", "") || "N/A"}
              subtitle="Highest revenue contributor"
              icon="🏆"
              loading={loading}
            />
          </div>

          {/* Revenue Trends Line Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Trends</CardTitle>
              <CardDescription>12-month revenue history with transaction counts</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="left" tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v, name) => name === "revenue" ? formatCurrency(v) : v} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="revenue" name="Revenue" stroke={COLORS.primary} strokeWidth={2} dot={{ r: 4 }} />
                  <Line yAxisId="right" type="monotone" dataKey="transactions" name="Transactions" stroke={COLORS.info} strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Revenue Source Percentages */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Source Breakdown</CardTitle>
              <CardDescription>Percentage contribution by source</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {revenueBreakdown?.source_percentages && Object.entries(revenueBreakdown.source_percentages).map(([source, percent]) => (
                  <div key={source} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{source.replace("Subscription: ", "")}</span>
                      <span className="text-slate-500">{percent}%</span>
                    </div>
                    <Progress value={percent} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profit Analysis Tab */}
        <TabsContent value="profit" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Net Profit"
              value={formatCurrency(profitAnalysis?.net_profit || 0)}
              changeType={profitAnalysis?.net_profit >= 0 ? "positive" : "negative"}
              icon="💎"
              loading={loading}
            />
            <MetricCard
              title="Profit Margin"
              value={`${profitAnalysis?.profit_margin_percent?.toFixed(1) || 0}%`}
              changeType={profitAnalysis?.profit_margin_percent >= 25 ? "positive" : profitAnalysis?.profit_margin_percent >= 10 ? undefined : "negative"}
              icon="📈"
              loading={loading}
            />
            <MetricCard
              title="Total Expenses"
              value={formatCurrency(profitAnalysis?.total_expenses || 0)}
              changeType="negative"
              icon="💸"
              loading={loading}
            />
            <MetricCard
              title="Expense Ratio"
              value={`${((profitAnalysis?.expense_to_revenue_ratio || 0) * 100).toFixed(1)}%`}
              changeType={profitAnalysis?.expense_to_revenue_ratio < 0.5 ? "positive" : "negative"}
              icon="⚖️"
              loading={loading}
            />
          </div>

          {/* Monthly Profit Breakdown Table */}
          <Card>
            <CardHeader>
              <CardTitle>Monthly Profit Breakdown</CardTitle>
              <CardDescription>Detailed monthly financial performance</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Month</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">Expenses</TableHead>
                    <TableHead className="text-right">Profit</TableHead>
                    <TableHead className="text-right">Margin</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profitAnalysis?.monthly_breakdown?.map((row) => (
                    <TableRow key={row.month}>
                      <TableCell className="font-medium">{row.month}</TableCell>
                      <TableCell className="text-right text-green-600">{formatCurrency(row.revenue)}</TableCell>
                      <TableCell className="text-right text-red-500">{formatCurrency(row.expenses)}</TableCell>
                      <TableCell className={`text-right font-medium ${row.profit >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {formatCurrency(row.profit)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge className={row.margin_percent >= 25 ? "bg-green-500" : row.margin_percent >= 10 ? "bg-yellow-500" : "bg-red-500"}>
                          {row.margin_percent?.toFixed(1)}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Forecast Tab */}
        <TabsContent value="forecast" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Forecast</CardTitle>
              <CardDescription>Predicted revenue for the next 3 months based on historical patterns</CardDescription>
            </CardHeader>
            <CardContent>
              {forecast?.error ? (
                <div className="text-center py-8 text-slate-500">
                  <p>⚠️ {forecast.error}</p>
                </div>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={forecastChartData}>
                      <defs>
                        <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.warning} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={COLORS.warning} stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 12 }} />
                      <Tooltip formatter={(v) => formatCurrency(v)} />
                      <Area
                        type="monotone"
                        dataKey="predicted"
                        name="Predicted Revenue"
                        stroke={COLORS.warning}
                        fillOpacity={1}
                        fill="url(#colorForecast)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {forecast?.forecasts?.map((f) => (
                      <Card key={f.month} className="bg-slate-50">
                        <CardContent className="pt-4">
                          <p className="text-sm text-slate-500">{f.month}</p>
                          <p className="text-xl font-bold text-slate-900">{formatCurrency(f.predicted_revenue)}</p>
                          <Badge className={f.confidence === "high" ? "bg-green-500" : f.confidence === "medium" ? "bg-yellow-500" : "bg-orange-500"}>
                            {f.confidence} confidence
                          </Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <div className="mt-4 text-sm text-slate-500">
                    <p>📊 Base amount: {formatCurrency(forecast?.base_amount || 0)}</p>
                    <p>📈 Growth rate used: {forecast?.growth_rate_used?.toFixed(1)}%</p>
                    <p>ℹ️ {forecast?.note}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Self-Funding Loop Tab */}
        <TabsContent value="loop" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Self-Funding Loop Status</CardTitle>
                  <CardDescription>17_Subscriptions → 06_Calculator Revenue Flow</CardDescription>
                </div>
                <HealthBadge status={selfFundingLoop?.loop_health} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Subscription Revenue */}
                <div className="p-6 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl">
                  <h3 className="text-lg font-semibold text-purple-900 mb-4">Subscription Revenue</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-purple-700">Total Revenue</span>
                      <span className="font-bold text-purple-900">{formatCurrency(selfFundingLoop?.subscription_revenue?.total || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-purple-700">Transactions</span>
                      <span className="font-medium">{selfFundingLoop?.subscription_revenue?.transactions || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-purple-700">Avg per Transaction</span>
                      <span className="font-medium">{formatCurrency(selfFundingLoop?.subscription_revenue?.avg_per_transaction || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-purple-700">% of Total</span>
                      <span className="font-bold text-purple-900">{selfFundingLoop?.subscription_revenue?.percentage_of_total?.toFixed(1) || 0}%</span>
                    </div>
                  </div>
                </div>

                {/* Other Revenue */}
                <div className="p-6 bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Other Revenue</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Total Revenue</span>
                      <span className="font-bold">{formatCurrency(selfFundingLoop?.other_revenue?.total || 0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Transactions</span>
                      <span className="font-medium">{selfFundingLoop?.other_revenue?.transactions || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Total Platform Revenue */}
              <div className="mt-6 p-6 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-amber-100">Total Platform Revenue</p>
                    <p className="text-3xl font-bold">{formatCurrency(selfFundingLoop?.total_platform_revenue || 0)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-amber-100">Active Subscriptions</p>
                    <p className="text-3xl font-bold">{selfFundingLoop?.active_subscriptions || 0}</p>
                  </div>
                </div>
              </div>

              <p className="mt-4 text-sm text-slate-500 italic">
                {selfFundingLoop?.description}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Elite Inquiries Tab */}
        <TabsContent value="elite" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total Inquiries"
              value={eliteInquiries?.stats?.total || 0}
              icon="📬"
              loading={loading}
            />
            <MetricCard
              title="Pending"
              value={eliteInquiries?.stats?.pending || 0}
              icon="⏳"
              loading={loading}
            />
            <MetricCard
              title="Contacted"
              value={eliteInquiries?.stats?.contacted || 0}
              icon="📞"
              loading={loading}
            />
            <MetricCard
              title="Converted"
              value={eliteInquiries?.stats?.converted || 0}
              icon="🎉"
              loading={loading}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recent Elite Inquiries</CardTitle>
              <CardDescription>Latest Elite plan inquiries from creators</CardDescription>
            </CardHeader>
            <CardContent>
              {eliteInquiries?.inquiries?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Creator</TableHead>
                      <TableHead>Company</TableHead>
                      <TableHead>Team Size</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {eliteInquiries.inquiries.map((inquiry) => (
                      <TableRow key={inquiry.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{inquiry.creator_name}</p>
                            <p className="text-sm text-slate-500">{inquiry.creator_email}</p>
                          </div>
                        </TableCell>
                        <TableCell>{inquiry.company_name || "-"}</TableCell>
                        <TableCell>{inquiry.team_size || "-"}</TableCell>
                        <TableCell>
                          <Badge className={
                            inquiry.status === "converted" ? "bg-green-500" :
                            inquiry.status === "contacted" ? "bg-blue-500" :
                            inquiry.status === "declined" ? "bg-red-500" :
                            "bg-yellow-500"
                          }>
                            {inquiry.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-500">
                          {new Date(inquiry.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  No Elite inquiries yet
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminRevenueDashboard;
