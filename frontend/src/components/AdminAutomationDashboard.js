/**
 * Admin Smart Automation Dashboard - Phase 4 Module B
 * Manage condition-based automation rules and view execution logs
 */

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { 
  Zap, Settings, History, Play, Pause, AlertTriangle, 
  CheckCircle, RefreshCw, Mail, Bell, FileText, ChevronRight
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function AdminAutomationDashboard({ token }) {
  const [activeTab, setActiveTab] = useState("rules");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [rules, setRules] = useState([]);
  const [logs, setLogs] = useState([]);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResults, setEvaluationResults] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [rulesRes, logsRes] = await Promise.all([
        fetch(`${API}/admin/automation/rules`, { headers }),
        fetch(`${API}/admin/automation/log?limit=50`, { headers })
      ]);
      
      if (!rulesRes.ok) throw new Error("Failed to fetch automation rules");
      
      setRules(await rulesRes.json());
      setLogs(await logsRes.json());
      
    } catch (err) {
      setError(err.message);
      console.error("Automation dashboard error:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token, fetchData]);

  const toggleRule = async (ruleId, isActive) => {
    try {
      const res = await fetch(
        `${API}/admin/automation/rules/${ruleId}/toggle?is_active=${!isActive}`,
        { method: "POST", headers }
      );
      
      if (res.ok) {
        setRules(rules.map(r => 
          r.id === ruleId ? { ...r, is_active: !isActive } : r
        ));
      }
    } catch (err) {
      console.error("Failed to toggle rule:", err);
    }
  };

  const evaluateAllCreators = async () => {
    setEvaluating(true);
    setEvaluationResults(null);
    
    try {
      const res = await fetch(`${API}/admin/automation/evaluate-all`, {
        method: "POST",
        headers
      });
      
      if (res.ok) {
        const results = await res.json();
        setEvaluationResults(results);
        // Refresh logs after evaluation
        const logsRes = await fetch(`${API}/admin/automation/log?limit=50`, { headers });
        if (logsRes.ok) {
          setLogs(await logsRes.json());
        }
      }
    } catch (err) {
      console.error("Evaluation failed:", err);
    } finally {
      setEvaluating(false);
    }
  };

  const getActionIcon = (actionType) => {
    switch (actionType) {
      case "send_email": return <Mail className="w-4 h-4" />;
      case "create_task": return <FileText className="w-4 h-4" />;
      case "notify_admin": return <Bell className="w-4 h-4" />;
      case "generate_recommendation": return <Zap className="w-4 h-4" />;
      default: return <Settings className="w-4 h-4" />;
    }
  };

  const formatCondition = (conditions) => {
    if (!conditions) return "Event-based trigger";
    
    if (conditions.type === "composite") {
      const rules = conditions.rules || [];
      return rules.map(r => `${r.field} ${r.operator} ${r.value}`).join(` ${conditions.operator} `);
    }
    
    return `${conditions.field} ${conditions.operator} ${conditions.value}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-2 text-slate-600">Loading automation rules...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h3 className="text-lg font-semibold text-red-700">Failed to Load</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={fetchData} variant="outline">Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-automation-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Smart Automation Engine</h1>
            <p className="text-sm text-slate-500">Condition-based triggers & automated actions</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={evaluateAllCreators}
            disabled={evaluating}
            className="bg-amber-600 hover:bg-amber-700"
            data-testid="evaluate-all-btn"
          >
            {evaluating ? (
              <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Evaluating...</>
            ) : (
              <><Play className="w-4 h-4 mr-2" /> Run All Rules</>
            )}
          </Button>
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Evaluation Results */}
      {evaluationResults && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div>
                <p className="font-semibold text-green-800">Evaluation Complete</p>
                <p className="text-sm text-green-600">
                  Evaluated {evaluationResults.creators_evaluated} creators • 
                  {evaluationResults.total_rules_triggered} rules triggered
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-slate-800">{rules.length}</p>
            <p className="text-sm text-slate-500">Total Rules</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-green-600">
              {rules.filter(r => r.is_active).length}
            </p>
            <p className="text-sm text-slate-500">Active Rules</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-amber-600">{logs.length}</p>
            <p className="text-sm text-slate-500">Recent Executions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <p className="text-3xl font-bold text-purple-600">
              {logs.filter(l => l.actions_executed?.every(a => a.success)).length}
            </p>
            <p className="text-sm text-slate-500">Successful</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="rules" data-testid="tab-rules">
            <Settings className="w-4 h-4 mr-2" /> Rules
          </TabsTrigger>
          <TabsTrigger value="logs" data-testid="tab-logs">
            <History className="w-4 h-4 mr-2" /> Execution Log
          </TabsTrigger>
        </TabsList>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          {rules.map((rule) => (
            <Card key={rule.id} className={!rule.is_active ? "opacity-60" : ""} data-testid={`rule-${rule.id}`}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-slate-800">{rule.name}</h3>
                      <Badge className={rule.is_active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"}>
                        {rule.is_active ? "Active" : "Inactive"}
                      </Badge>
                      <Badge className="bg-purple-100 text-purple-700">
                        {rule.trigger_type}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-500 mt-1">{rule.description}</p>
                    
                    {/* Conditions */}
                    <div className="mt-3 p-2 bg-slate-50 rounded text-xs">
                      <span className="font-medium text-slate-600">Conditions: </span>
                      <span className="text-slate-700">{formatCondition(rule.conditions)}</span>
                    </div>
                    
                    {/* Actions */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {rule.actions?.map((action, idx) => (
                        <Badge key={idx} variant="outline" className="flex items-center gap-1">
                          {getActionIcon(action.type)}
                          {action.type.replace("_", " ")}
                        </Badge>
                      ))}
                    </div>
                    
                    {/* Cooldown */}
                    {rule.cooldown_hours > 0 && (
                      <p className="text-xs text-slate-400 mt-2">
                        Cooldown: {rule.cooldown_hours} hours
                      </p>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <Switch
                      checked={rule.is_active}
                      onCheckedChange={() => toggleRule(rule.id, rule.is_active)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          {logs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-slate-500">
                No automation executions yet
              </CardContent>
            </Card>
          ) : (
            logs.map((log) => (
              <Card key={log.id} data-testid={`log-${log.id}`}>
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-slate-800">{log.rule_name}</h4>
                        <Badge className={
                          log.actions_executed?.every(a => a.success) 
                            ? "bg-green-100 text-green-700" 
                            : "bg-red-100 text-red-700"
                        }>
                          {log.actions_executed?.every(a => a.success) ? "Success" : "Partial"}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-500">
                        Creator: {log.creator_id}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {new Date(log.triggered_at).toLocaleString()}
                      </p>
                      
                      {/* Actions executed */}
                      <div className="mt-2 flex flex-wrap gap-2">
                        {log.actions_executed?.map((action, idx) => (
                          <Badge 
                            key={idx} 
                            className={action.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}
                          >
                            {action.action.replace("_", " ")} {action.success ? "✓" : "✗"}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div className="text-right text-sm">
                      <p className="text-slate-600">
                        Approval Rate: {log.metrics_snapshot?.approval_rate}%
                      </p>
                      <p className="text-slate-400">
                        Proposals: {log.metrics_snapshot?.total_proposals}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AdminAutomationDashboard;
