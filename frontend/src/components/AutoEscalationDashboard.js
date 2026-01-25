/**
 * Auto-Escalation Dashboard (Module B5)
 * Admin dashboard for managing proposal escalations.
 * Shows stalled proposals, escalation history, and analytics.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Escalation level styles
const LEVEL_STYLES = {
  critical: { bg: "bg-red-100", text: "text-red-700", border: "border-red-300", icon: "🔴" },
  urgent: { bg: "bg-orange-100", text: "text-orange-700", border: "border-orange-300", icon: "🟠" },
  elevated: { bg: "bg-yellow-100", text: "text-yellow-700", border: "border-yellow-300", icon: "🟡" },
  standard: { bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-300", icon: "⚪" },
};

// Health status styles
const HEALTH_STYLES = {
  healthy: { bg: "bg-green-100", text: "text-green-700", label: "All Clear" },
  fair: { bg: "bg-blue-100", text: "text-blue-700", label: "Fair" },
  needs_attention: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Needs Attention" },
  poor: { bg: "bg-orange-100", text: "text-orange-700", label: "Poor" },
  critical: { bg: "bg-red-100", text: "text-red-700", label: "Critical" },
};

/**
 * Escalation Summary Card
 */
const EscalationSummaryCard = ({ summary }) => {
  if (!summary) return null;
  
  const healthStyle = HEALTH_STYLES[summary.health_status] || HEALTH_STYLES.fair;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <Card className="border-l-4 border-l-slate-400">
        <CardContent className="pt-4">
          <p className="text-3xl font-bold text-slate-800">{summary.total_active}</p>
          <p className="text-sm text-slate-500">Active Escalations</p>
        </CardContent>
      </Card>
      <Card className={`border-l-4 ${summary.by_level?.critical > 0 ? "border-l-red-500" : "border-l-red-200"}`}>
        <CardContent className="pt-4">
          <p className="text-3xl font-bold text-red-600">{summary.by_level?.critical || 0}</p>
          <p className="text-sm text-slate-500">Critical</p>
        </CardContent>
      </Card>
      <Card className={`border-l-4 ${summary.by_level?.urgent > 0 ? "border-l-orange-500" : "border-l-orange-200"}`}>
        <CardContent className="pt-4">
          <p className="text-3xl font-bold text-orange-600">{summary.by_level?.urgent || 0}</p>
          <p className="text-sm text-slate-500">Urgent</p>
        </CardContent>
      </Card>
      <Card className={`border-l-4 ${summary.by_level?.elevated > 0 ? "border-l-yellow-500" : "border-l-yellow-200"}`}>
        <CardContent className="pt-4">
          <p className="text-3xl font-bold text-yellow-600">{summary.by_level?.elevated || 0}</p>
          <p className="text-sm text-slate-500">Elevated</p>
        </CardContent>
      </Card>
      <Card className={`border-l-4 border-l-green-400`}>
        <CardContent className="pt-4">
          <div className="flex items-center gap-2">
            <Badge className={`${healthStyle.bg} ${healthStyle.text}`}>{healthStyle.label}</Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">Resolved: {summary.resolved_24h} (24h)</p>
          <p className="text-xs text-slate-400">Avg resolution: {summary.avg_resolution_hours}h</p>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Escalation Item Row
 */
const EscalationItem = ({ escalation, onResolve, onViewProposal }) => {
  const levelStyle = LEVEL_STYLES[escalation.level] || LEVEL_STYLES.standard;
  const createdDate = new Date(escalation.created_at);
  // Calculate hours ago using the created_at timestamp
  const hoursAgo = Math.round((new Date().getTime() - createdDate.getTime()) / 3600000);
  
  return (
    <div
      className={`p-4 border rounded-lg ${levelStyle.border} ${escalation.resolved ? "bg-slate-50 opacity-70" : "bg-white"}`}
      data-testid={`escalation-${escalation.escalation_id}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{levelStyle.icon}</span>
            <Badge className={`${levelStyle.bg} ${levelStyle.text}`}>
              {escalation.level?.toUpperCase()}
            </Badge>
            {escalation.resolved && (
              <Badge className="bg-green-100 text-green-700">RESOLVED</Badge>
            )}
            <span className="text-xs text-slate-400">{escalation.escalation_id}</span>
          </div>
          
          <h4 className="font-medium text-slate-800 mb-1">
            {escalation.proposal_title || "Untitled Proposal"}
          </h4>
          
          <div className="flex flex-wrap gap-4 text-sm text-slate-500">
            <span>Status: <span className="font-medium">{escalation.status}</span></span>
            <span>Hours stalled: <span className="font-medium text-orange-600">{escalation.hours_in_status}h</span></span>
            <span>Reason: <span className="font-medium">{escalation.reason?.replace(/_/g, " ")}</span></span>
          </div>
          
          <p className="text-xs text-slate-400 mt-2">
            Escalated {hoursAgo}h ago • Creator: {escalation.creator_id?.slice(0, 20)}...
          </p>
          
          {escalation.notes && (
            <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-2 rounded">
              📝 {escalation.notes}
            </p>
          )}
          
          {escalation.resolution_notes && (
            <p className="text-sm text-green-700 mt-2 bg-green-50 p-2 rounded">
              ✅ Resolution: {escalation.resolution_notes}
            </p>
          )}
        </div>
        
        <div className="flex flex-col gap-2">
          {!escalation.resolved && (
            <Button
              size="sm"
              onClick={() => onResolve(escalation)}
              data-testid={`resolve-${escalation.escalation_id}`}
            >
              ✓ Resolve
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewProposal(escalation.proposal_id)}
          >
            View Proposal
          </Button>
        </div>
      </div>
    </div>
  );
};

/**
 * Stalled Proposal Item
 */
const StalledProposalItem = ({ proposal, onEscalate }) => {
  const hoursStalled = Math.round(proposal.hours_stalled || 0);
  const isUrgent = hoursStalled >= 96;
  const isCritical = hoursStalled >= 168;
  
  return (
    <div
      className={`p-4 border rounded-lg ${isCritical ? "border-red-300 bg-red-50" : isUrgent ? "border-orange-300 bg-orange-50" : "border-slate-200"}`}
      data-testid={`stalled-${proposal.proposal_id}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium text-slate-800">{proposal.title || "Untitled"}</h4>
          <div className="flex gap-4 text-sm text-slate-500 mt-1">
            <span>Status: <Badge variant="outline">{proposal.status}</Badge></span>
            <span className={`font-medium ${isCritical ? "text-red-600" : isUrgent ? "text-orange-600" : "text-yellow-600"}`}>
              Stalled: {hoursStalled}h
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {!proposal.already_escalated ? (
            <Button
              size="sm"
              variant={isCritical ? "destructive" : isUrgent ? "default" : "outline"}
              onClick={() => onEscalate(proposal)}
              data-testid={`escalate-${proposal.proposal_id}`}
            >
              Escalate
            </Button>
          ) : (
            <Badge className="bg-slate-100 text-slate-600">Already Escalated</Badge>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Main Auto-Escalation Dashboard Component
 */
export const AutoEscalationDashboard = ({ token }) => {
  const [dashboard, setDashboard] = useState(null);
  const [stalledProposals, setStalledProposals] = useState([]);
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Filter states
  const [thresholdHours, setThresholdHours] = useState(48);
  const [historyFilter, setHistoryFilter] = useState("all");
  const [includeResolved, setIncludeResolved] = useState(true);
  
  // Dialog states
  const [resolveDialog, setResolveDialog] = useState({ open: false, escalation: null });
  const [escalateDialog, setEscalateDialog] = useState({ open: false, proposal: null });
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [escalationLevel, setEscalationLevel] = useState("elevated");
  const [escalationReason, setEscalationReason] = useState("");
  const [escalationNotes, setEscalationNotes] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchDashboard = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/escalation/dashboard`, { headers });
      setDashboard(response.data);
    } catch (err) {
      console.error("Error fetching escalation dashboard:", err);
      setError("Failed to load escalation dashboard");
    }
  }, [getAuthHeaders]);

  const fetchStalled = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/escalation/stalled?threshold_hours=${thresholdHours}`, { headers });
      setStalledProposals(response.data.stalled_proposals || []);
    } catch (err) {
      console.error("Error fetching stalled proposals:", err);
    }
  }, [getAuthHeaders, thresholdHours]);

  const fetchHistory = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const params = new URLSearchParams();
      params.set("include_resolved", includeResolved);
      if (historyFilter !== "all") {
        params.set("level", historyFilter);
      }
      
      const response = await axios.get(`${API}/admin/escalation/history?${params}`, { headers });
      setHistory(response.data.escalations || []);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  }, [getAuthHeaders, includeResolved, historyFilter]);

  const fetchAnalytics = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/escalation/analytics`, { headers });
      setAnalytics(response.data);
    } catch (err) {
      console.error("Error fetching analytics:", err);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchDashboard();
      setLoading(false);
    };
    if (token) loadData();
  }, [token, fetchDashboard]);

  useEffect(() => {
    if (token && activeTab === "stalled") fetchStalled();
  }, [token, activeTab, fetchStalled]);

  useEffect(() => {
    if (token && activeTab === "history") fetchHistory();
  }, [token, activeTab, fetchHistory]);

  useEffect(() => {
    if (token && activeTab === "analytics") fetchAnalytics();
  }, [token, activeTab, fetchAnalytics]);

  const handleResolve = async () => {
    if (!resolveDialog.escalation) return;
    
    try {
      const headers = getAuthHeaders();
      const params = new URLSearchParams();
      if (resolutionNotes) params.set("resolution_notes", resolutionNotes);
      
      await axios.post(
        `${API}/admin/escalation/resolve/${resolveDialog.escalation.escalation_id}?${params}`,
        {},
        { headers }
      );
      
      setResolveDialog({ open: false, escalation: null });
      setResolutionNotes("");
      fetchDashboard();
      if (activeTab === "history") fetchHistory();
    } catch (err) {
      console.error("Error resolving escalation:", err);
    }
  };

  const handleEscalate = async () => {
    if (!escalateDialog.proposal) return;
    
    try {
      const headers = getAuthHeaders();
      const params = new URLSearchParams();
      params.set("level", escalationLevel);
      if (escalationReason) params.set("reason", escalationReason);
      if (escalationNotes) params.set("notes", escalationNotes);
      
      await axios.post(
        `${API}/admin/escalation/escalate/${escalateDialog.proposal.proposal_id}?${params}`,
        {},
        { headers }
      );
      
      setEscalateDialog({ open: false, proposal: null });
      setEscalationLevel("elevated");
      setEscalationReason("");
      setEscalationNotes("");
      fetchDashboard();
      fetchStalled();
    } catch (err) {
      console.error("Error escalating proposal:", err);
    }
  };

  const handleScan = async () => {
    try {
      setScanning(true);
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/admin/escalation/scan`, {}, { headers });
      setScanResult(response.data);
      fetchDashboard();
      if (activeTab === "stalled") fetchStalled();
    } catch (err) {
      console.error("Error running scan:", err);
    } finally {
      setScanning(false);
    }
  };

  const handleViewProposal = (proposalId) => {
    // Navigate to proposal - adjust based on your routing
    window.open(`/admin/proposals/${proposalId}`, "_blank");
  };

  if (loading) {
    return (
      <Card data-testid="escalation-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading escalation dashboard...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200" data-testid="escalation-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchDashboard} className="mt-4">Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="auto-escalation-dashboard">
      {/* Resolve Escalation Dialog */}
      <Dialog open={resolveDialog.open} onOpenChange={(open) => setResolveDialog({ ...resolveDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Escalation</DialogTitle>
            <DialogDescription>
              Mark this escalation as resolved. You can add notes about how it was handled.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Proposal</Label>
              <p className="text-sm font-medium">{resolveDialog.escalation?.proposal_title}</p>
            </div>
            <div>
              <Label htmlFor="resolution-notes">Resolution Notes</Label>
              <Textarea
                id="resolution-notes"
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Describe how this was resolved..."
                data-testid="resolution-notes-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResolveDialog({ open: false, escalation: null })}>
              Cancel
            </Button>
            <Button onClick={handleResolve} data-testid="confirm-resolve">
              ✓ Resolve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manual Escalation Dialog */}
      <Dialog open={escalateDialog.open} onOpenChange={(open) => setEscalateDialog({ ...escalateDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Escalate Proposal</DialogTitle>
            <DialogDescription>
              Manually escalate this proposal for priority attention.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Proposal</Label>
              <p className="text-sm font-medium">{escalateDialog.proposal?.title}</p>
            </div>
            <div>
              <Label>Escalation Level</Label>
              <Select value={escalationLevel} onValueChange={setEscalationLevel}>
                <SelectTrigger data-testid="escalation-level-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="elevated">🟡 Elevated</SelectItem>
                  <SelectItem value="urgent">🟠 Urgent</SelectItem>
                  <SelectItem value="critical">🔴 Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="escalation-reason">Reason</Label>
              <Input
                id="escalation-reason"
                value={escalationReason}
                onChange={(e) => setEscalationReason(e.target.value)}
                placeholder="e.g., admin_attention, high_value"
                data-testid="escalation-reason-input"
              />
            </div>
            <div>
              <Label htmlFor="escalation-notes">Notes</Label>
              <Textarea
                id="escalation-notes"
                value={escalationNotes}
                onChange={(e) => setEscalationNotes(e.target.value)}
                placeholder="Additional context..."
                data-testid="escalation-notes-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEscalateDialog({ open: false, proposal: null })}>
              Cancel
            </Button>
            <Button onClick={handleEscalate} className="bg-orange-600 hover:bg-orange-700" data-testid="confirm-escalate">
              ⚡ Escalate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            ⚡ Auto-Escalation Dashboard
          </h2>
          <p className="text-sm text-slate-600">Monitor and manage stalled proposals</p>
        </div>
        <Button
          onClick={handleScan}
          disabled={scanning}
          className="bg-orange-600 hover:bg-orange-700"
          data-testid="run-scan-button"
        >
          {scanning ? "Scanning..." : "🔍 Run Scan"}
        </Button>
      </div>

      {/* Scan Result */}
      {scanResult && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-800">
                  Scan Complete: {scanResult.scanned} proposals scanned, {scanResult.escalated} escalated
                </p>
                {scanResult.errors?.length > 0 && (
                  <p className="text-xs text-orange-600">{scanResult.errors.length} errors</p>
                )}
              </div>
              <Button size="sm" variant="ghost" onClick={() => setScanResult(null)}>✕</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      {dashboard?.summary && <EscalationSummaryCard summary={dashboard.summary} />}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-overview">
            📊 Active ({dashboard?.summary?.total_active || 0})
          </TabsTrigger>
          <TabsTrigger value="stalled" data-testid="tab-stalled">
            ⏳ Stalled ({stalledProposals.length})
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            📜 History
          </TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">
            📈 Analytics
          </TabsTrigger>
        </TabsList>

        {/* Active Escalations Tab */}
        <TabsContent value="overview" className="mt-4">
          {dashboard?.active_escalations?.length > 0 ? (
            <div className="space-y-3">
              {dashboard.active_escalations.map((escalation) => (
                <EscalationItem
                  key={escalation.escalation_id}
                  escalation={escalation}
                  onResolve={(esc) => setResolveDialog({ open: true, escalation: esc })}
                  onViewProposal={handleViewProposal}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-5xl">✅</span>
                <p className="text-slate-600 mt-4">No active escalations!</p>
                <p className="text-sm text-slate-400">All proposals are progressing normally.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Stalled Proposals Tab */}
        <TabsContent value="stalled" className="mt-4">
          <div className="mb-4 flex items-center gap-4">
            <Label>Threshold:</Label>
            <Select value={thresholdHours.toString()} onValueChange={(v) => setThresholdHours(parseInt(v))}>
              <SelectTrigger className="w-40" data-testid="threshold-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24">24+ hours</SelectItem>
                <SelectItem value="48">48+ hours</SelectItem>
                <SelectItem value="72">72+ hours</SelectItem>
                <SelectItem value="96">96+ hours</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchStalled}>
              Refresh
            </Button>
          </div>

          {stalledProposals.length > 0 ? (
            <div className="space-y-3">
              {stalledProposals.map((proposal) => (
                <StalledProposalItem
                  key={proposal.proposal_id}
                  proposal={proposal}
                  onEscalate={(p) => setEscalateDialog({ open: true, proposal: p })}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-5xl">🎉</span>
                <p className="text-slate-600 mt-4">No stalled proposals!</p>
                <p className="text-sm text-slate-400">All proposals are being processed in a timely manner.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-4">
          <div className="mb-4 flex items-center gap-4">
            <Label>Level:</Label>
            <Select value={historyFilter} onValueChange={setHistoryFilter}>
              <SelectTrigger className="w-36" data-testid="history-level-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="elevated">Elevated</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={includeResolved}
                onChange={(e) => setIncludeResolved(e.target.checked)}
                data-testid="include-resolved-checkbox"
              />
              Include Resolved
            </label>
          </div>

          {history.length > 0 ? (
            <div className="space-y-3">
              {history.map((escalation) => (
                <EscalationItem
                  key={escalation.escalation_id}
                  escalation={escalation}
                  onResolve={(esc) => setResolveDialog({ open: true, escalation: esc })}
                  onViewProposal={handleViewProposal}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-5xl">📜</span>
                <p className="text-slate-600 mt-4">No escalation history</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="mt-4">
          {analytics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Overview ({analytics.period_days} days)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Total Escalations</span>
                    <span className="font-bold">{analytics.total_escalations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolution Rate</span>
                    <span className="font-bold text-green-600">{analytics.resolution_rate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolved</span>
                    <span className="font-bold">{analytics.resolved_count}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">By Level</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(analytics.by_level || {}).map(([level, count]) => {
                    const style = LEVEL_STYLES[level] || LEVEL_STYLES.standard;
                    return (
                      <div key={level} className="flex items-center justify-between">
                        <Badge className={`${style.bg} ${style.text}`}>
                          {style.icon} {level}
                        </Badge>
                        <span className="font-bold">{count}</span>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">By Reason</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.by_reason || {}).map(([reason, count]) => (
                    <div key={reason} className="flex justify-between text-sm">
                      <span className="text-slate-600">{reason?.replace(/_/g, " ")}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                  {Object.keys(analytics.by_reason || {}).length === 0 && (
                    <p className="text-slate-400 text-sm">No data</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Avg Time to Escalation</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(analytics.avg_time_to_escalation_by_status || {}).map(([status, hours]) => (
                    <div key={status} className="flex justify-between text-sm">
                      <span className="text-slate-600">{status}</span>
                      <span className="font-medium">{hours}h</span>
                    </div>
                  ))}
                  {Object.keys(analytics.avg_time_to_escalation_by_status || {}).length === 0 && (
                    <p className="text-slate-400 text-sm">No data</p>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
                <p className="text-slate-500 mt-4">Loading analytics...</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AutoEscalationDashboard;
