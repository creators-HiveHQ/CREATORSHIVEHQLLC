/**
 * Admin Memory Palace Dashboard - Phase 4 Module C
 * Memory consolidation management and health monitoring
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Database, RefreshCw, Archive, Zap, CheckCircle, 
  AlertTriangle, Clock, TrendingDown, Play, History
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function AdminMemoryDashboard({ token }) {
  const [loading, setLoading] = useState(true);
  const [consolidating, setConsolidating] = useState(false);
  const [health, setHealth] = useState(null);
  const [history, setHistory] = useState([]);
  const [consolidationResult, setConsolidationResult] = useState(null);
  const [error, setError] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [healthRes, historyRes] = await Promise.all([
        fetch(`${API}/admin/memory/health`, { headers }),
        fetch(`${API}/admin/memory/consolidation-history?limit=10`, { headers })
      ]);
      
      if (healthRes.ok) {
        setHealth(await healthRes.json());
      }
      if (historyRes.ok) {
        setHistory(await historyRes.json());
      }
    } catch (err) {
      setError("Failed to load memory data");
      console.error("Memory dashboard error:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token, fetchData]);

  const runConsolidation = async () => {
    setConsolidating(true);
    setConsolidationResult(null);
    
    try {
      const res = await fetch(`${API}/admin/memory/consolidate`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        const result = await res.json();
        setConsolidationResult(result);
        // Refresh data after consolidation
        await fetchData();
      }
    } catch (err) {
      console.error("Consolidation failed:", err);
    } finally {
      setConsolidating(false);
    }
  };

  const getHealthColor = (score) => {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 60) return "text-amber-600 bg-amber-100";
    return "text-red-600 bg-red-100";
  };

  const getStatusBadge = (status) => {
    const colors = {
      excellent: "bg-green-100 text-green-700",
      good: "bg-blue-100 text-blue-700",
      needs_attention: "bg-red-100 text-red-700"
    };
    return colors[status] || "bg-slate-100 text-slate-700";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-2 text-slate-600">Loading memory data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-memory-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
            <Database className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Memory Palace</h1>
            <p className="text-sm text-slate-500">Memory consolidation & health management</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={runConsolidation}
            disabled={consolidating}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="run-consolidation-btn"
          >
            {consolidating ? (
              <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Consolidating...</>
            ) : (
              <><Play className="w-4 h-4 mr-2" /> Run Consolidation</>
            )}
          </Button>
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Consolidation Result */}
      {consolidationResult && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div>
                <p className="font-semibold text-green-800">Consolidation Complete</p>
                <p className="text-sm text-green-600">
                  Processed {consolidationResult.creators_processed} creators • 
                  Consolidated {consolidationResult.memories_consolidated} memories • 
                  Archived {consolidationResult.memories_archived} memories
                </p>
                <p className="text-xs text-green-500 mt-1">
                  Estimated storage saved: ~{(consolidationResult.storage_saved_estimate / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card data-testid="health-score-card">
          <CardContent className="py-4 text-center">
            <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center text-2xl font-bold ${getHealthColor(health?.health_score || 0)}`}>
              {health?.health_score || 0}
            </div>
            <p className="text-sm text-slate-500 mt-2">Health Score</p>
            <Badge className={`mt-1 ${getStatusBadge(health?.status)}`}>
              {health?.status?.toUpperCase()}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-4 text-center">
            <Database className="w-8 h-8 mx-auto text-blue-500" />
            <p className="text-2xl font-bold mt-2">{health?.total_memories || 0}</p>
            <p className="text-sm text-slate-500">Active Memories</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-4 text-center">
            <Archive className="w-8 h-8 mx-auto text-slate-500" />
            <p className="text-2xl font-bold mt-2">{health?.archived_memories || 0}</p>
            <p className="text-sm text-slate-500">Archived</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-4 text-center">
            <TrendingDown className="w-8 h-8 mx-auto text-amber-500" />
            <p className="text-2xl font-bold mt-2">{health?.consolidation_candidates || 0}</p>
            <p className="text-sm text-slate-500">Consolidation Candidates</p>
          </CardContent>
        </Card>
      </div>

      {/* Issues & Recommendations */}
      {(health?.issues?.length > 0 || health?.recommendations?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {health?.issues?.length > 0 && (
            <Card className="border-amber-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  Issues Detected
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {health.issues.map((issue, idx) => (
                    <li key={idx} className="text-sm text-amber-700 flex items-start gap-2">
                      <span className="mt-1">•</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {health?.recommendations?.length > 0 && (
            <Card className="border-blue-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-500" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {health.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-blue-700 flex items-start gap-2">
                      <span className="mt-1">→</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Memory by Type */}
      {health?.by_type && Object.keys(health.by_type).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Memory Distribution by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(health.by_type).map(([type, data]) => (
                <div key={type} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{type?.replace("_", " ") || "Unknown"}</p>
                    <p className="text-xs text-slate-500">
                      Avg importance: {data.avg_importance?.toFixed(2) || "N/A"} • 
                      Recalls: {data.total_recalls || 0}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-slate-800">{data.count}</p>
                    <p className="text-xs text-slate-400">memories</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Consolidation History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="w-5 h-5" />
            Consolidation History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-slate-500 text-center py-4">No consolidation runs yet</p>
          ) : (
            <div className="space-y-3">
              {history.map((run) => (
                <div key={run.id} className="p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-800">
                        {new Date(run.run_at).toLocaleDateString()} {new Date(run.run_at).toLocaleTimeString()}
                      </p>
                      <p className="text-sm text-slate-500">
                        {run.results?.creators_processed || 0} creators • 
                        {run.results?.memories_consolidated || 0} consolidated • 
                        {run.results?.memories_archived || 0} archived
                      </p>
                    </div>
                    <Badge variant="outline">
                      {run.duration_seconds?.toFixed(1)}s
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default AdminMemoryDashboard;
