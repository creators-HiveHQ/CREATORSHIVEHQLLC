import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Project Proposal Form Component
export const ProjectProposalForm = ({ userId, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    user_id: userId || "",
    title: "",
    description: "",
    goals: "",
    platforms: [],
    timeline: "",
    estimated_hours: 0,
    arris_intake_question: "",
    priority: "medium"
  });
  const [formOptions, setFormOptions] = useState({
    platforms: [],
    timelines: [],
    priorities: [],
    arris_question: ""
  });
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [createdProposal, setCreatedProposal] = useState(null);

  // Fetch form options
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await axios.get(`${API}/proposals/form-options`);
        setFormOptions(response.data);
      } catch (err) {
        console.error("Error fetching form options:", err);
      }
    };
    fetchOptions();
  }, []);

  const handlePlatformToggle = (platform) => {
    setFormData(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }));
  };

  const handleSaveDraft = async () => {
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/proposals`, formData);
      setCreatedProposal(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save draft");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForReview = async () => {
    if (!createdProposal) {
      // First save as draft
      setError("");
      setLoading(true);
      try {
        const response = await axios.post(`${API}/proposals`, formData);
        setCreatedProposal(response.data);
        // Then submit
        setSubmitting(true);
        const submitResponse = await axios.post(`${API}/proposals/${response.data.id}/submit`);
        if (onSuccess) onSuccess(submitResponse.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to submit proposal");
      } finally {
        setLoading(false);
        setSubmitting(false);
      }
    } else {
      // Already saved, just submit
      setSubmitting(true);
      try {
        const response = await axios.post(`${API}/proposals/${createdProposal.id}/submit`);
        if (onSuccess) onSuccess(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to submit proposal");
      } finally {
        setSubmitting(false);
      }
    }
  };

  return (
    <Card className="w-full max-w-3xl" data-testid="proposal-form">
      <CardHeader>
        <CardTitle>📋 New Project Proposal</CardTitle>
        <CardDescription>
          Describe your project and ARRIS will provide strategic insights
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Project Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Q1 YouTube Series Launch"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              data-testid="input-title"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Project Description *</Label>
            <Textarea
              id="description"
              placeholder="Describe what you want to accomplish with this project..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              required
              data-testid="input-description"
            />
          </div>

          {/* Goals */}
          <div className="space-y-2">
            <Label htmlFor="goals">Project Goals</Label>
            <Textarea
              id="goals"
              placeholder="What specific outcomes do you want to achieve?"
              value={formData.goals}
              onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
              rows={3}
              data-testid="input-goals"
            />
          </div>

          {/* Platforms */}
          <div className="space-y-3">
            <Label>Platforms Involved</Label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {formOptions.platforms?.map((platform) => (
                <div
                  key={platform.value}
                  onClick={() => handlePlatformToggle(platform.value)}
                  className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer text-sm transition-all ${
                    formData.platforms.includes(platform.value)
                      ? "bg-blue-50 border-blue-500 text-blue-700"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                  data-testid={`platform-${platform.value}`}
                >
                  <span>{platform.icon}</span>
                  <span>{platform.label}</span>
                  {formData.platforms.includes(platform.value) && (
                    <span className="ml-auto text-blue-500">✓</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Timeline & Priority Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Timeline</Label>
              <Select
                value={formData.timeline}
                onValueChange={(value) => setFormData({ ...formData, timeline: value })}
              >
                <SelectTrigger data-testid="select-timeline">
                  <SelectValue placeholder="Select timeline" />
                </SelectTrigger>
                <SelectContent>
                  {formOptions.timelines?.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(value) => setFormData({ ...formData, priority: value })}
              >
                <SelectTrigger data-testid="select-priority">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {formOptions.priorities?.map((p) => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="hours">Estimated Hours</Label>
              <Input
                id="hours"
                type="number"
                min="0"
                placeholder="0"
                value={formData.estimated_hours || ""}
                onChange={(e) => setFormData({ ...formData, estimated_hours: parseFloat(e.target.value) || 0 })}
                data-testid="input-hours"
              />
            </div>
          </div>

          {/* ARRIS Intake Question */}
          <div className="space-y-2 bg-purple-50 p-4 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2">
              <span className="text-xl">🧠</span>
              <Label className="text-purple-700 font-medium">ARRIS wants to know...</Label>
            </div>
            <p className="text-sm text-purple-600 italic mb-2">
              &ldquo;{formOptions.arris_question || "What's the main outcome you want from this project?"}&rdquo;
            </p>
            <Textarea
              placeholder="Share your thoughts... This helps ARRIS provide better insights"
              value={formData.arris_intake_question}
              onChange={(e) => setFormData({ ...formData, arris_intake_question: e.target.value })}
              rows={3}
              className="border-purple-200"
              data-testid="input-arris-question"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="error-message">
              {error}
            </div>
          )}

          {/* Draft saved indicator */}
          {createdProposal && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              ✓ Draft saved - ID: {createdProposal.id}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={handleSaveDraft}
              disabled={loading || !formData.title || !formData.description}
              data-testid="save-draft-btn"
            >
              {loading ? "Saving..." : "💾 Save Draft"}
            </Button>
            <Button
              type="button"
              onClick={handleSubmitForReview}
              disabled={loading || submitting || !formData.title || !formData.description}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="submit-btn"
            >
              {submitting ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span> Generating Insights...
                </span>
              ) : (
                "🚀 Submit & Get ARRIS Insights"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

// ARRIS Insights Display Component
export const ArrisInsightsCard = ({ insights, onRegenerate }) => {
  if (!insights) return null;

  const getComplexityColor = (complexity) => {
    switch (complexity?.toLowerCase()) {
      case "low": return "bg-green-100 text-green-800";
      case "medium": return "bg-yellow-100 text-yellow-800";
      case "high": return "bg-red-100 text-red-800";
      default: return "bg-slate-100 text-slate-800";
    }
  };

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white" data-testid="arris-insights">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            <CardTitle className="text-purple-800">ARRIS Insights</CardTitle>
          </div>
          {onRegenerate && (
            <Button size="sm" variant="outline" onClick={onRegenerate} data-testid="regenerate-btn">
              🔄 Regenerate
            </Button>
          )}
        </div>
        {insights.generated_at && (
          <CardDescription>
            Generated {new Date(insights.generated_at).toLocaleString()}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        {insights.summary && (
          <div>
            <h4 className="font-medium text-slate-700 mb-2">📝 Summary</h4>
            <p className="text-slate-600">{insights.summary}</p>
          </div>
        )}

        {/* Complexity & Success */}
        <div className="flex gap-4">
          {insights.estimated_complexity && (
            <div>
              <span className="text-sm text-slate-500">Complexity</span>
              <Badge className={`ml-2 ${getComplexityColor(insights.estimated_complexity)}`}>
                {insights.estimated_complexity}
              </Badge>
            </div>
          )}
          {insights.success_probability && (
            <div className="flex-1">
              <span className="text-sm text-slate-500">Success Assessment</span>
              <p className="text-sm text-slate-700 mt-1">{insights.success_probability}</p>
            </div>
          )}
        </div>

        {/* Strengths */}
        {insights.strengths?.length > 0 && (
          <div>
            <h4 className="font-medium text-green-700 mb-2">💪 Strengths</h4>
            <ul className="space-y-1">
              {insights.strengths.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-green-500 mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risks */}
        {insights.risks?.length > 0 && (
          <div>
            <h4 className="font-medium text-orange-700 mb-2">⚠️ Risks & Challenges</h4>
            <ul className="space-y-1">
              {insights.risks.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-orange-500 mt-0.5">!</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendations */}
        {insights.recommendations?.length > 0 && (
          <div>
            <h4 className="font-medium text-blue-700 mb-2">💡 Recommendations</h4>
            <ul className="space-y-1">
              {insights.recommendations.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-blue-500 mt-0.5">→</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Milestones */}
        {insights.suggested_milestones?.length > 0 && (
          <div>
            <h4 className="font-medium text-purple-700 mb-2">🎯 Suggested Milestones</h4>
            <div className="space-y-2">
              {insights.suggested_milestones.map((milestone, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-xs font-medium">
                    {i + 1}
                  </div>
                  <span className="text-sm text-slate-600">{milestone}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Resources */}
        {insights.resource_suggestions && (
          <div className="bg-slate-50 p-3 rounded-lg">
            <h4 className="font-medium text-slate-700 mb-1">🛠️ Resource Suggestions</h4>
            <p className="text-sm text-slate-600">{insights.resource_suggestions}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Admin Proposals Page
export const AdminProposalsPage = () => {
  const [proposals, setProposals] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: "", priority: "" });
  const [selectedProposal, setSelectedProposal] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);

  const fetchProposals = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.status) params.append("status", filter.status);
      if (filter.priority) params.append("priority", filter.priority);
      
      const [proposalsRes, statsRes] = await Promise.all([
        axios.get(`${API}/proposals?${params.toString()}`),
        axios.get(`${API}/proposals/stats/summary`)
      ]);
      setProposals(proposalsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching proposals:", error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  const handleStatusUpdate = async (proposalId, newStatus, notes = "") => {
    try {
      await axios.patch(`${API}/proposals/${proposalId}`, { 
        status: newStatus,
        review_notes: notes 
      });
      fetchProposals();
      setSelectedProposal(null);
    } catch (error) {
      console.error("Error updating proposal:", error);
    }
  };

  const handleRegenerateInsights = async (proposalId) => {
    try {
      const response = await axios.post(`${API}/proposals/${proposalId}/regenerate-insights`);
      // Refresh the selected proposal
      const updatedProposal = await axios.get(`${API}/proposals/${proposalId}`);
      setSelectedProposal(updatedProposal.data);
    } catch (error) {
      console.error("Error regenerating insights:", error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: "bg-slate-100 text-slate-700",
      submitted: "bg-blue-100 text-blue-700",
      under_review: "bg-purple-100 text-purple-700",
      approved: "bg-green-100 text-green-700",
      in_progress: "bg-amber-100 text-amber-700",
      completed: "bg-emerald-100 text-emerald-700",
      rejected: "bg-red-100 text-red-700"
    };
    return styles[status] || "bg-slate-100 text-slate-700";
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      low: "bg-slate-100 text-slate-600",
      medium: "bg-blue-100 text-blue-600",
      high: "bg-orange-100 text-orange-600",
      critical: "bg-red-100 text-red-600"
    };
    return styles[priority] || "bg-slate-100 text-slate-600";
  };

  if (showNewForm) {
    return (
      <div className="space-y-6" data-testid="new-proposal-view">
        <Button variant="outline" onClick={() => setShowNewForm(false)}>
          ← Back to Proposals
        </Button>
        <ProjectProposalForm
          userId="admin"
          onSuccess={(data) => {
            setShowNewForm(false);
            fetchProposals();
          }}
          onCancel={() => setShowNewForm(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-proposals-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Project Proposals</h1>
          <p className="text-slate-500">Review proposals with ARRIS AI insights</p>
        </div>
        <div className="flex gap-2">
          <Select 
            value={filter.status || "all"} 
            onValueChange={(v) => setFilter({ ...filter, status: v === "all" ? "" : v })}
          >
            <SelectTrigger className="w-36" data-testid="filter-status">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="submitted">Submitted</SelectItem>
              <SelectItem value="under_review">Under Review</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
          <Select 
            value={filter.priority || "all"} 
            onValueChange={(v) => setFilter({ ...filter, priority: v === "all" ? "" : v })}
          >
            <SelectTrigger className="w-32" data-testid="filter-priority">
              <SelectValue placeholder="All Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priority</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={() => setShowNewForm(true)} data-testid="new-proposal-btn">
            + New Proposal
          </Button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total_proposals}</div>
              <p className="text-sm text-slate-500">Total</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-700">{stats.by_status?.submitted || 0}</div>
              <p className="text-sm text-blue-600">Submitted</p>
            </CardContent>
          </Card>
          <Card className="bg-purple-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-purple-700">{stats.by_status?.under_review || 0}</div>
              <p className="text-sm text-purple-600">Under Review</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-700">{(stats.by_status?.approved || 0) + (stats.by_status?.in_progress || 0)}</div>
              <p className="text-sm text-green-600">Approved</p>
            </CardContent>
          </Card>
          <Card className="bg-amber-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-amber-700">{stats.by_priority?.high || 0}</div>
              <p className="text-sm text-amber-600">High Priority</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Proposals Table */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left p-4 font-medium">Proposal</th>
                <th className="text-left p-4 font-medium">Creator</th>
                <th className="text-left p-4 font-medium">Priority</th>
                <th className="text-left p-4 font-medium">Status</th>
                <th className="text-left p-4 font-medium">ARRIS</th>
                <th className="text-left p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8">Loading...</td>
                </tr>
              ) : proposals.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-500">No proposals found</td>
                </tr>
              ) : (
                proposals.map((proposal) => (
                  <tr key={proposal.id} className="border-t hover:bg-slate-50" data-testid={`proposal-row-${proposal.id}`}>
                    <td className="p-4">
                      <div>
                        <p className="font-medium">{proposal.title}</p>
                        <p className="text-sm text-slate-500 truncate max-w-xs">{proposal.description}</p>
                        <p className="text-xs text-slate-400 font-mono mt-1">{proposal.id}</p>
                      </div>
                    </td>
                    <td className="p-4">
                      <p className="text-sm">{proposal.creator_name || proposal.user_id}</p>
                      <p className="text-xs text-slate-400">{proposal.creator_email}</p>
                    </td>
                    <td className="p-4">
                      <Badge className={getPriorityBadge(proposal.priority)}>
                        {proposal.priority}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <Badge className={getStatusBadge(proposal.status)}>
                        {proposal.status?.replace(/_/g, " ")}
                      </Badge>
                    </td>
                    <td className="p-4">
                      {proposal.arris_insights ? (
                        <span className="text-green-600 text-sm flex items-center gap-1">
                          🧠 Generated
                        </span>
                      ) : (
                        <span className="text-slate-400 text-sm">Pending</span>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedProposal(proposal)}
                          data-testid={`view-btn-${proposal.id}`}
                        >
                          View
                        </Button>
                        {proposal.status === "submitted" && (
                          <Button
                            size="sm"
                            onClick={() => handleStatusUpdate(proposal.id, "under_review")}
                            data-testid={`review-btn-${proposal.id}`}
                          >
                            Review
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Proposal Detail Modal */}
      {selectedProposal && (
        <div className="fixed inset-0 bg-black/50 flex items-start justify-center p-4 z-50 overflow-y-auto" onClick={() => setSelectedProposal(null)}>
          <div className="my-8 w-full max-w-4xl" onClick={(e) => e.stopPropagation()}>
            <Card data-testid="proposal-detail-modal">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{selectedProposal.title}</CardTitle>
                    <CardDescription>
                      {selectedProposal.creator_name} • {selectedProposal.id}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Badge className={getPriorityBadge(selectedProposal.priority)}>
                      {selectedProposal.priority}
                    </Badge>
                    <Badge className={getStatusBadge(selectedProposal.status)}>
                      {selectedProposal.status?.replace(/_/g, " ")}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <Tabs defaultValue="details">
                  <TabsList>
                    <TabsTrigger value="details">Details</TabsTrigger>
                    <TabsTrigger value="insights">ARRIS Insights</TabsTrigger>
                  </TabsList>

                  <TabsContent value="details" className="space-y-4 mt-4">
                    <div>
                      <Label className="text-slate-500">Description</Label>
                      <p className="mt-1">{selectedProposal.description}</p>
                    </div>
                    
                    {selectedProposal.goals && (
                      <div>
                        <Label className="text-slate-500">Goals</Label>
                        <p className="mt-1">{selectedProposal.goals}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <Label className="text-slate-500">Platforms</Label>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedProposal.platforms?.map((p) => (
                            <Badge key={p} variant="outline">{p}</Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <Label className="text-slate-500">Timeline</Label>
                        <p className="mt-1">{selectedProposal.timeline || "Not specified"}</p>
                      </div>
                      <div>
                        <Label className="text-slate-500">Est. Hours</Label>
                        <p className="mt-1">{selectedProposal.estimated_hours || 0}</p>
                      </div>
                      <div>
                        <Label className="text-slate-500">Submitted</Label>
                        <p className="mt-1">
                          {selectedProposal.submitted_at 
                            ? new Date(selectedProposal.submitted_at).toLocaleDateString()
                            : "Not submitted"}
                        </p>
                      </div>
                    </div>

                    {selectedProposal.arris_intake_question && (
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <Label className="text-purple-700">ARRIS Intake Response</Label>
                        <p className="mt-1 text-slate-700 italic">
                          &ldquo;{selectedProposal.arris_intake_question}&rdquo;
                        </p>
                      </div>
                    )}

                    {selectedProposal.assigned_project_id && (
                      <div className="p-3 bg-green-50 rounded-lg">
                        <Label className="text-green-700">Assigned Project</Label>
                        <p className="font-mono">{selectedProposal.assigned_project_id}</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="insights" className="mt-4">
                    {selectedProposal.arris_insights ? (
                      <ArrisInsightsCard
                        insights={selectedProposal.arris_insights}
                        onRegenerate={() => handleRegenerateInsights(selectedProposal.id)}
                      />
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        <p>No ARRIS insights generated yet.</p>
                        <p className="text-sm mt-1">Submit the proposal to generate insights.</p>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button variant="outline" onClick={() => setSelectedProposal(null)}>
                    Close
                  </Button>
                  {selectedProposal.status === "under_review" && (
                    <>
                      <Button
                        className="bg-green-500 hover:bg-green-600"
                        onClick={() => handleStatusUpdate(selectedProposal.id, "approved")}
                        data-testid="approve-btn"
                      >
                        ✓ Approve & Create Project
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={() => handleStatusUpdate(selectedProposal.id, "rejected")}
                        data-testid="reject-btn"
                      >
                        ✗ Reject
                      </Button>
                    </>
                  )}
                  {selectedProposal.status === "submitted" && (
                    <Button
                      onClick={() => handleStatusUpdate(selectedProposal.id, "under_review")}
                    >
                      Start Review
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectProposalForm;
