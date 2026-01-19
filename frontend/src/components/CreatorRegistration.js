import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Public Creator Registration Form
export const CreatorRegistrationForm = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    platforms: [],
    niche: "",
    goals: "",
    arris_intake_question: ""
  });
  const [formOptions, setFormOptions] = useState({
    platforms: [],
    niches: [],
    arris_question: ""
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [submissionResult, setSubmissionResult] = useState(null);

  // Fetch form options
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await axios.get(`${API}/creators/form-options`);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/creators/register`, formData);
      setSubmissionResult(response.data);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted && submissionResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg" data-testid="registration-success">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-3xl">✅</span>
            </div>
            <CardTitle className="text-2xl text-green-600">Registration Successful!</CardTitle>
            <CardDescription className="text-base mt-2">
              {submissionResult.message}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <div className="bg-slate-50 rounded-lg p-4 mb-4">
              <p className="text-sm text-slate-500">Your Registration ID</p>
              <p className="text-lg font-mono font-bold text-slate-900">{submissionResult.id}</p>
            </div>
            <p className="text-sm text-slate-600">
              Keep this ID for your records. We'll send updates to <strong>{submissionResult.email}</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 px-4" data-testid="creator-registration-page">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Join Creators Hive HQ</h1>
          <p className="text-purple-200">Start your journey with ARRIS, your AI-powered creator assistant</p>
        </div>

        {/* Registration Form */}
        <Card>
          <CardHeader>
            <CardTitle>Creator Registration</CardTitle>
            <CardDescription>
              Tell us about yourself and your creator journey. ARRIS will use this to personalize your experience.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Name & Email */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Your name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    data-testid="input-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    data-testid="input-email"
                  />
                </div>
              </div>

              {/* Platforms */}
              <div className="space-y-3">
                <Label>Platforms (select all that apply) *</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {formOptions.platforms.map((platform) => (
                    <div
                      key={platform.value}
                      onClick={() => handlePlatformToggle(platform.value)}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all ${
                        formData.platforms.includes(platform.value)
                          ? "bg-purple-50 border-purple-500 text-purple-700"
                          : "bg-white border-slate-200 hover:border-slate-300"
                      }`}
                      data-testid={`platform-${platform.value}`}
                    >
                      <span className="text-lg">{platform.icon}</span>
                      <span className="text-sm font-medium">{platform.label}</span>
                      {formData.platforms.includes(platform.value) && (
                        <span className="ml-auto text-purple-500">✓</span>
                      )}
                    </div>
                  ))}
                </div>
                {formData.platforms.length > 0 && (
                  <p className="text-sm text-slate-500">
                    Selected: {formData.platforms.length} platform(s)
                  </p>
                )}
              </div>

              {/* Niche */}
              <div className="space-y-2">
                <Label htmlFor="niche">Your Niche / Industry *</Label>
                <Select
                  value={formData.niche}
                  onValueChange={(value) => setFormData({ ...formData, niche: value })}
                >
                  <SelectTrigger data-testid="select-niche">
                    <SelectValue placeholder="Select your niche" />
                  </SelectTrigger>
                  <SelectContent>
                    {formOptions.niches.map((niche) => (
                      <SelectItem key={niche} value={niche}>
                        {niche}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Goals */}
              <div className="space-y-2">
                <Label htmlFor="goals">Your Goals</Label>
                <Textarea
                  id="goals"
                  placeholder="What are you hoping to achieve? (e.g., grow audience, monetize content, launch a course...)"
                  value={formData.goals}
                  onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
                  rows={3}
                  data-testid="input-goals"
                />
              </div>

              {/* ARRIS Intake Question */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">🧠</span>
                  <Label htmlFor="arris_question" className="text-purple-700 font-medium">
                    ARRIS wants to know...
                  </Label>
                </div>
                <p className="text-sm text-slate-600 italic mb-2">
                  "{formOptions.arris_question || "What's the biggest challenge you're facing in your creator journey right now?"}"
                </p>
                <Textarea
                  id="arris_question"
                  placeholder="Share your thoughts here... ARRIS will use this to personalize your experience"
                  value={formData.arris_intake_question}
                  onChange={(e) => setFormData({ ...formData, arris_intake_question: e.target.value })}
                  rows={4}
                  className="border-purple-200 focus:border-purple-500"
                  data-testid="input-arris-question"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="error-message">
                  {error}
                </div>
              )}

              {/* Submit */}
              <Button 
                type="submit" 
                className="w-full bg-purple-600 hover:bg-purple-700" 
                disabled={loading || !formData.name || !formData.email || formData.platforms.length === 0 || !formData.niche}
                data-testid="submit-btn"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin">⏳</span> Submitting...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    🚀 Join Creators Hive HQ
                  </span>
                )}
              </Button>

              <p className="text-xs text-center text-slate-500">
                By registering, you agree to our Terms of Service and Privacy Policy
              </p>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-purple-200 text-sm">
          <p>Powered by ARRIS Pattern Engine</p>
          <p className="text-purple-300/60 mt-1">Zero-Human Operational Model</p>
        </div>
      </div>
    </div>
  );
};

// Admin Creators List Component
export const AdminCreatorsPage = ({ onNavigate }) => {
  const [creators, setCreators] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [selectedCreator, setSelectedCreator] = useState(null);

  const fetchCreators = useCallback(async () => {
    try {
      setLoading(true);
      const params = filter ? `?status=${filter}` : "";
      const [creatorsRes, statsRes] = await Promise.all([
        axios.get(`${API}/creators${params}`),
        axios.get(`${API}/creators/stats/summary`)
      ]);
      setCreators(creatorsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching creators:", error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchCreators();
  }, [fetchCreators]);

  const handleStatusUpdate = async (creatorId, newStatus, tier = null) => {
    try {
      const updateData = { status: newStatus };
      if (tier) updateData.assigned_tier = tier;
      
      await axios.patch(`${API}/creators/${creatorId}`, updateData);
      fetchCreators();
      setSelectedCreator(null);
    } catch (error) {
      console.error("Error updating creator:", error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-yellow-100 text-yellow-800",
      approved: "bg-green-100 text-green-800",
      rejected: "bg-red-100 text-red-800",
      active: "bg-blue-100 text-blue-800"
    };
    return styles[status] || "bg-slate-100 text-slate-800";
  };

  return (
    <div className="space-y-6" data-testid="admin-creators-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Creator Registrations</h1>
          <p className="text-slate-500">Review and manage creator applications</p>
        </div>
        <div className="flex gap-2">
          <Select value={filter || "all"} onValueChange={(v) => setFilter(v === "all" ? "" : v)}>
            <SelectTrigger className="w-36" data-testid="filter-status">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchCreators} variant="outline" data-testid="refresh-btn">
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total_registrations}</div>
              <p className="text-sm text-slate-500">Total Registrations</p>
            </CardContent>
          </Card>
          <Card className="bg-yellow-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-yellow-700">{stats.by_status?.pending || 0}</div>
              <p className="text-sm text-yellow-600">Pending Review</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-700">{stats.by_status?.approved || 0}</div>
              <p className="text-sm text-green-600">Approved</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-700">{stats.by_status?.active || 0}</div>
              <p className="text-sm text-blue-600">Active Users</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Creators Table */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left p-4 font-medium">Creator</th>
                <th className="text-left p-4 font-medium">Platforms</th>
                <th className="text-left p-4 font-medium">Niche</th>
                <th className="text-left p-4 font-medium">Status</th>
                <th className="text-left p-4 font-medium">Submitted</th>
                <th className="text-left p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8">Loading...</td>
                </tr>
              ) : creators.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-500">No registrations found</td>
                </tr>
              ) : (
                creators.map((creator) => (
                  <tr key={creator.id} className="border-t hover:bg-slate-50" data-testid={`creator-row-${creator.id}`}>
                    <td className="p-4">
                      <div>
                        <p className="font-medium">{creator.name}</p>
                        <p className="text-sm text-slate-500">{creator.email}</p>
                        <p className="text-xs text-slate-400 font-mono">{creator.id}</p>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-1">
                        {creator.platforms?.map((p) => (
                          <Badge key={p} variant="outline" className="text-xs">{p}</Badge>
                        ))}
                      </div>
                    </td>
                    <td className="p-4 text-sm">{creator.niche}</td>
                    <td className="p-4">
                      <Badge className={getStatusBadge(creator.status)}>
                        {creator.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-sm text-slate-500">
                      {new Date(creator.submitted_at).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setSelectedCreator(creator)}
                          data-testid={`view-btn-${creator.id}`}
                        >
                          View
                        </Button>
                        {creator.status === "pending" && (
                          <>
                            <Button 
                              size="sm" 
                              className="bg-green-500 hover:bg-green-600"
                              onClick={() => handleStatusUpdate(creator.id, "approved", "Free")}
                              data-testid={`approve-btn-${creator.id}`}
                            >
                              Approve
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleStatusUpdate(creator.id, "rejected")}
                              data-testid={`reject-btn-${creator.id}`}
                            >
                              Reject
                            </Button>
                          </>
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

      {/* Creator Detail Modal */}
      {selectedCreator && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedCreator(null)}>
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()} data-testid="creator-detail-modal">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{selectedCreator.name}</CardTitle>
                  <CardDescription>{selectedCreator.email}</CardDescription>
                </div>
                <Badge className={getStatusBadge(selectedCreator.status)}>
                  {selectedCreator.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-slate-500">Registration ID</Label>
                <p className="font-mono">{selectedCreator.id}</p>
              </div>
              <div>
                <Label className="text-slate-500">Platforms</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {selectedCreator.platforms?.map((p) => (
                    <Badge key={p} variant="secondary">{p}</Badge>
                  ))}
                </div>
              </div>
              <div>
                <Label className="text-slate-500">Niche</Label>
                <p>{selectedCreator.niche}</p>
              </div>
              <div>
                <Label className="text-slate-500">Goals</Label>
                <p className="text-slate-700">{selectedCreator.goals || "Not provided"}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <Label className="text-purple-700 flex items-center gap-2">
                  <span>🧠</span> ARRIS Intake Response
                </Label>
                <p className="text-slate-700 mt-2 italic">
                  "{selectedCreator.arris_intake_question || "No response provided"}"
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-slate-500">Submitted</Label>
                  <p>{new Date(selectedCreator.submitted_at).toLocaleString()}</p>
                </div>
                {selectedCreator.reviewed_at && (
                  <div>
                    <Label className="text-slate-500">Reviewed</Label>
                    <p>{new Date(selectedCreator.reviewed_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
              {selectedCreator.assigned_user_id && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <Label className="text-green-700">Assigned User ID</Label>
                  <p className="font-mono">{selectedCreator.assigned_user_id}</p>
                </div>
              )}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setSelectedCreator(null)}>
                  Close
                </Button>
                {selectedCreator.status === "pending" && (
                  <>
                    <Button 
                      className="bg-green-500 hover:bg-green-600"
                      onClick={() => handleStatusUpdate(selectedCreator.id, "approved", "Free")}
                    >
                      Approve & Create User
                    </Button>
                    <Button 
                      variant="destructive"
                      onClick={() => handleStatusUpdate(selectedCreator.id, "rejected")}
                    >
                      Reject
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CreatorRegistrationForm;
