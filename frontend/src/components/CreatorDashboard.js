/**
 * Creator Dashboard - Creator-Facing Proposal Management
 * View proposals, track status, read ARRIS insights, create new proposals
 */

import { useState, useEffect, useCallback, createContext, useContext } from "react";
import { useNavigate, Navigate, Link } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============== CREATOR AUTH CONTEXT ==============

const CreatorAuthContext = createContext(null);

export const useCreatorAuth = () => {
  const context = useContext(CreatorAuthContext);
  if (!context) {
    throw new Error("useCreatorAuth must be used within CreatorAuthProvider");
  }
  return context;
};

export const CreatorAuthProvider = ({ children }) => {
  const [creator, setCreator] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("creator_token"));
  const [loading, setLoading] = useState(true);

  const verifyToken = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/creators/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCreator(response.data);
    } catch (error) {
      console.error("Creator token verification failed:", error);
      logout();
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    verifyToken();
  }, [verifyToken]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/creators/login`, { email, password });
      const { access_token, creator: creatorData } = response.data;
      
      localStorage.setItem("creator_token", access_token);
      setToken(access_token);
      setCreator(creatorData);
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || "Login failed";
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem("creator_token");
    setToken(null);
    setCreator(null);
  };

  return (
    <CreatorAuthContext.Provider value={{
      creator,
      token,
      loading,
      isAuthenticated: !!creator,
      login,
      logout
    }}>
      {children}
    </CreatorAuthContext.Provider>
  );
};

// ============== CREATOR LOGIN PAGE ==============

export const CreatorLoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useCreatorAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/creator/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await login(email, password);
    
    if (result.success) {
      navigate("/creator/dashboard");
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4" data-testid="creator-login-page">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-purple-600">Creators Hive HQ</h1>
            <p className="text-sm text-slate-500">Creator Portal</p>
          </div>
          <CardTitle>Creator Login</CardTitle>
          <CardDescription>
            Sign in to view your proposals and ARRIS insights
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="input-email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                data-testid="input-password"
              />
            </div>
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="error-message">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700" disabled={loading} data-testid="submit-btn">
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-slate-500">
              Don't have an account?{" "}
              <Link to="/register" className="text-purple-600 hover:underline">
                Register as a Creator
              </Link>
            </p>
            <p className="text-xs text-slate-400">
              Admin? <Link to="/login" className="text-amber-600 hover:underline">Admin Login</Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ============== PROTECTED ROUTE ==============

export const CreatorProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useCreatorAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/creator/login" replace />;
  }

  return children;
};

// ============== NEW PROPOSAL FORM ==============

const NewProposalModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
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
  const [step, setStep] = useState(1); // 1: Form, 2: Review, 3: Submitting, 4: Complete
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdProposal, setCreatedProposal] = useState(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return { Authorization: `Bearer ${token}` };
  };

  // Fetch form options
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const response = await axios.get(`${API}/proposals/form-options`);
        setFormOptions(response.data);
        // Set ARRIS question as placeholder
        if (response.data.arris_question) {
          setFormData(prev => ({ ...prev, arris_intake_question: "" }));
        }
      } catch (err) {
        console.error("Error fetching form options:", err);
      }
    };
    if (isOpen) {
      fetchOptions();
    }
  }, [isOpen]);

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
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/proposals`, formData, { headers });
      setCreatedProposal(response.data);
      setStep(2);
    } catch (err) {
      // Handle error - detail can be string or object (for proposal limit errors)
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail !== null) {
        setError(detail.message || "Failed to save draft");
      } else {
        setError(detail || "Failed to save draft");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForReview = async () => {
    setError("");
    setLoading(true);
    setStep(3);

    try {
      const headers = getAuthHeaders();
      
      let proposalId = createdProposal?.id;
      
      // If no draft exists, create one first
      if (!proposalId) {
        const createResponse = await axios.post(`${API}/proposals`, formData, { headers });
        proposalId = createResponse.data.id;
        setCreatedProposal(createResponse.data);
      }
      
      // Submit for ARRIS review
      const submitResponse = await axios.post(`${API}/proposals/${proposalId}/submit`, {}, { headers });
      setCreatedProposal(submitResponse.data);
      setStep(4);
      
    } catch (err) {
      // Handle error - detail can be string or object (for proposal limit errors)
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail !== null) {
        setError(detail.message || "Failed to submit proposal");
      } else {
        setError(detail || "Failed to submit proposal");
      }
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (step === 4 && onSuccess) {
      onSuccess(createdProposal);
    }
    // Reset form
    setFormData({
      title: "",
      description: "",
      goals: "",
      platforms: [],
      timeline: "",
      estimated_hours: 0,
      arris_intake_question: "",
      priority: "medium"
    });
    setStep(1);
    setCreatedProposal(null);
    setError("");
    onClose();
  };

  const isFormValid = formData.title.length >= 3 && formData.description.length >= 10;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="new-proposal-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {step === 1 && "📋 New Project Proposal"}
            {step === 2 && "📝 Review Your Proposal"}
            {step === 3 && "🧠 ARRIS is Analyzing..."}
            {step === 4 && "✅ Proposal Submitted!"}
          </DialogTitle>
          <DialogDescription>
            {step === 1 && "Describe your project and ARRIS will provide strategic insights"}
            {step === 2 && "Review your proposal before submitting for ARRIS analysis"}
            {step === 3 && "Please wait while ARRIS generates insights for your proposal"}
            {step === 4 && "Your proposal has been submitted and analyzed by ARRIS"}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="error-message">
            {error}
          </div>
        )}

        {/* Step 1: Form */}
        {step === 1 && (
          <div className="space-y-5 py-4">
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
                rows={3}
                required
                data-testid="input-description"
              />
              <p className="text-xs text-slate-500">Min 10 characters</p>
            </div>

            {/* Goals */}
            <div className="space-y-2">
              <Label htmlFor="goals">Project Goals</Label>
              <Textarea
                id="goals"
                placeholder="What specific outcomes do you want to achieve?"
                value={formData.goals}
                onChange={(e) => setFormData({ ...formData, goals: e.target.value })}
                rows={2}
                data-testid="input-goals"
              />
            </div>

            {/* Platforms */}
            <div className="space-y-2">
              <Label>Platforms Involved</Label>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                {formOptions.platforms?.map((platform) => (
                  <div
                    key={platform.value}
                    onClick={() => handlePlatformToggle(platform.value)}
                    className={`flex items-center gap-1.5 p-2 rounded-lg border cursor-pointer text-sm transition-all ${
                      formData.platforms.includes(platform.value)
                        ? "bg-purple-50 border-purple-500 text-purple-700"
                        : "bg-white border-slate-200 hover:border-slate-300"
                    }`}
                    data-testid={`platform-${platform.value}`}
                  >
                    <span>{platform.icon}</span>
                    <span className="truncate">{platform.label}</span>
                    {formData.platforms.includes(platform.value) && (
                      <span className="ml-auto text-purple-500">✓</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Timeline & Priority */}
            <div className="grid grid-cols-2 gap-4">
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
                      <SelectItem key={p.value} value={p.value}>{p.icon} {p.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* ARRIS Intake Question */}
            {formOptions.arris_question && (
              <div className="space-y-2 bg-gradient-to-r from-purple-50 to-indigo-50 p-4 rounded-lg border border-purple-200">
                <div className="flex items-center gap-2">
                  <span className="text-xl">🧠</span>
                  <Label className="text-purple-700 font-medium">ARRIS Wants to Know</Label>
                </div>
                <p className="text-sm text-purple-600 italic">{formOptions.arris_question}</p>
                <Textarea
                  placeholder="Share your thoughts..."
                  value={formData.arris_intake_question}
                  onChange={(e) => setFormData({ ...formData, arris_intake_question: e.target.value })}
                  rows={2}
                  className="bg-white"
                  data-testid="input-arris-question"
                />
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="outline" onClick={handleClose} data-testid="cancel-btn">
                Cancel
              </Button>
              <Button
                onClick={handleSaveDraft}
                disabled={!isFormValid || loading}
                className="bg-purple-600 hover:bg-purple-700"
                data-testid="continue-btn"
              >
                {loading ? "Saving..." : "Continue →"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Review */}
        {step === 2 && createdProposal && (
          <div className="space-y-5 py-4">
            <div className="bg-slate-50 p-4 rounded-lg space-y-3">
              <div>
                <p className="text-xs text-slate-500">Project Title</p>
                <p className="font-medium">{formData.title}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Description</p>
                <p className="text-sm text-slate-700">{formData.description}</p>
              </div>
              {formData.goals && (
                <div>
                  <p className="text-xs text-slate-500">Goals</p>
                  <p className="text-sm text-slate-700">{formData.goals}</p>
                </div>
              )}
              {formData.platforms.length > 0 && (
                <div>
                  <p className="text-xs text-slate-500">Platforms</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {formData.platforms.map((p) => (
                      <Badge key={p} variant="outline">{p}</Badge>
                    ))}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500">Timeline</p>
                  <p className="text-sm">{formData.timeline || "Not specified"}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Priority</p>
                  <Badge className={
                    formData.priority === "high" ? "bg-red-100 text-red-700" :
                    formData.priority === "critical" ? "bg-red-500 text-white" :
                    formData.priority === "low" ? "bg-slate-100 text-slate-700" :
                    "bg-blue-100 text-blue-700"
                  }>{formData.priority}</Badge>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <p className="text-sm text-purple-700">
                <strong>🧠 ARRIS Analysis:</strong> When you submit, ARRIS will analyze your proposal and provide strategic insights including strengths, risks, recommendations, and suggested milestones.
              </p>
            </div>

            <div className="flex justify-between gap-3 pt-4 border-t">
              <Button variant="outline" onClick={() => setStep(1)} data-testid="back-btn">
                ← Edit
              </Button>
              <Button
                onClick={handleSubmitForReview}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
                data-testid="submit-btn"
              >
                {loading ? "Submitting..." : "Submit for ARRIS Review 🚀"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Submitting */}
        {step === 3 && (
          <div className="py-12 text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center animate-pulse">
              <span className="text-3xl">🧠</span>
            </div>
            <p className="text-lg font-medium text-purple-700">ARRIS is analyzing your proposal...</p>
            <p className="text-sm text-slate-500">This usually takes a few seconds</p>
            <Progress value={66} className="w-48 mx-auto" />
          </div>
        )}

        {/* Step 4: Complete */}
        {step === 4 && createdProposal && (
          <div className="py-8 text-center space-y-4">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-3xl">✅</span>
            </div>
            <p className="text-lg font-medium text-green-700">Proposal Submitted!</p>
            <p className="text-sm text-slate-500">
              ARRIS has analyzed your proposal and generated strategic insights.
            </p>
            <div className="bg-slate-50 p-3 rounded-lg">
              <p className="text-xs text-slate-500">Proposal ID</p>
              <p className="font-mono text-sm">{createdProposal.id}</p>
            </div>
            {createdProposal.arris_insights?.summary && (
              <div className="bg-purple-50 p-4 rounded-lg text-left border border-purple-200">
                <p className="text-xs text-purple-600 font-medium mb-1">🧠 ARRIS Summary</p>
                <p className="text-sm text-purple-700 italic">"{createdProposal.arris_insights.summary}"</p>
              </div>
            )}
            <Button
              onClick={handleClose}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="done-btn"
            >
              View in My Proposals
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

// ============== CREATOR DASHBOARD ==============

export const CreatorDashboard = () => {
  const { creator, logout } = useCreatorAuth();
  const [dashboard, setDashboard] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [selectedProposal, setSelectedProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [showNewProposal, setShowNewProposal] = useState(false);
  const [advancedData, setAdvancedData] = useState(null);
  const [advancedLoading, setAdvancedLoading] = useState(false);
  const [premiumData, setPremiumData] = useState(null);
  const [premiumLoading, setPremiumLoading] = useState(false);
  const [premiumDateRange, setPremiumDateRange] = useState("30d");
  const [featureAccess, setFeatureAccess] = useState(null);
  const navigate = useNavigate();

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return { Authorization: `Bearer ${token}` };
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const headers = getAuthHeaders();
      
      const [dashboardRes, proposalsRes, featuresRes] = await Promise.all([
        axios.get(`${API}/creators/me/dashboard`, { headers }),
        axios.get(`${API}/creators/me/proposals`, { headers }),
        axios.get(`${API}/subscriptions/feature-access`, { headers }).catch(() => ({ data: null }))
      ]);
      
      setDashboard(dashboardRes.data);
      setProposals(proposalsRes.data);
      setFeatureAccess(featuresRes.data);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAdvancedDashboard = useCallback(async () => {
    if (advancedData) return; // Already loaded
    
    try {
      setAdvancedLoading(true);
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/creators/me/advanced-dashboard`, { headers });
      setAdvancedData(response.data);
    } catch (error) {
      console.error("Error fetching advanced dashboard:", error);
      // Feature might be gated - that's okay
    } finally {
      setAdvancedLoading(false);
    }
  }, [advancedData]);

  const fetchPremiumAnalytics = useCallback(async (dateRange = "30d") => {
    try {
      setPremiumLoading(true);
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/creators/me/premium-analytics?date_range=${dateRange}`, { headers });
      setPremiumData(response.data);
    } catch (error) {
      console.error("Error fetching premium analytics:", error);
      // Feature might be gated
    } finally {
      setPremiumLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    // Fetch advanced data when switching to analytics tab
    if (activeTab === "analytics" && !advancedData && !advancedLoading) {
      fetchAdvancedDashboard();
    }
    // Fetch premium data when switching to premium-analytics tab
    if (activeTab === "premium-analytics" && !premiumData && !premiumLoading) {
      fetchPremiumAnalytics(premiumDateRange);
    }
  }, [activeTab, advancedData, advancedLoading, fetchAdvancedDashboard, premiumData, premiumLoading, fetchPremiumAnalytics, premiumDateRange]);

  const handleNewProposalSuccess = (proposal) => {
    // Refresh data and switch to proposals tab
    fetchData();
    setActiveTab("proposals");
    // Select the new proposal
    if (proposal?.id) {
      setSelectedProposal(proposal);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: "bg-slate-100 text-slate-700",
      submitted: "bg-blue-100 text-blue-700",
      under_review: "bg-amber-100 text-amber-700",
      approved: "bg-green-100 text-green-700",
      in_progress: "bg-purple-100 text-purple-700",
      rejected: "bg-red-100 text-red-700",
      completed: "bg-emerald-100 text-emerald-700"
    };
    return styles[status] || "bg-slate-100 text-slate-700";
  };

  const getStatusIcon = (status) => {
    const icons = {
      draft: "📝",
      submitted: "📤",
      under_review: "🔍",
      approved: "✅",
      in_progress: "🚀",
      rejected: "❌",
      completed: "🎉"
    };
    return icons[status] || "📋";
  };

  const handleLogout = () => {
    logout();
    navigate("/creator/login");
  };

  // Check if user has advanced dashboard access (Pro+)
  const hasAdvancedDashboard = featureAccess?.features?.dashboard_level === "advanced" || 
                               featureAccess?.features?.dashboard_level === "custom";
  
  const hasPriorityReview = featureAccess?.features?.priority_review || false;
  
  // Check if user has Premium analytics access
  const hasPremiumAnalytics = featureAccess?.features?.advanced_analytics || false;

  // Handle date range change for premium analytics
  const handleDateRangeChange = (range) => {
    setPremiumDateRange(range);
    setPremiumData(null); // Clear old data
    fetchPremiumAnalytics(range);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50" data-testid="creator-dashboard">
      {/* New Proposal Modal */}
      <NewProposalModal
        isOpen={showNewProposal}
        onClose={() => setShowNewProposal(false)}
        onSuccess={handleNewProposalSuccess}
      />

      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-purple-600">Creators Hive HQ</h1>
            <p className="text-xs text-slate-500">Creator Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <Button 
              onClick={() => setShowNewProposal(true)} 
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="new-proposal-btn"
            >
              + New Proposal
            </Button>
            <Button 
              variant="outline"
              onClick={() => navigate("/creator/subscription")} 
              className="border-amber-500 text-amber-600 hover:bg-amber-50"
              data-testid="upgrade-btn"
            >
              {(featureAccess?.tier || dashboard?.creator?.tier) === "free" ? "⚡ Upgrade" : "💳 Manage Plan"}
            </Button>
            <div className="text-right">
              <p className="font-medium text-slate-900">{creator?.name}</p>
              <p className="text-xs text-slate-500">{creator?.email}</p>
            </div>
            <Badge className={`${
              featureAccess?.tier === "pro" ? "bg-purple-500 text-white" :
              featureAccess?.tier === "premium" ? "bg-amber-500 text-white" :
              featureAccess?.tier === "elite" ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white" :
              featureAccess?.tier === "starter" ? "bg-blue-500 text-white" :
              "bg-purple-100 text-purple-700"
            }`}>
              {(featureAccess?.tier || dashboard?.creator?.tier || "Free").toUpperCase()}
            </Badge>
            <Button variant="outline" size="sm" onClick={handleLogout} data-testid="logout-btn">
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview" data-testid="tab-overview">📊 Overview</TabsTrigger>
            <TabsTrigger value="proposals" data-testid="tab-proposals">📋 My Proposals ({proposals.length})</TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              data-testid="tab-analytics"
              className={!hasAdvancedDashboard ? "relative" : ""}
            >
              📈 Analytics
              {!hasAdvancedDashboard && (
                <Badge className="ml-2 bg-amber-500 text-white text-xs px-1.5 py-0">PRO</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger 
              value="premium-analytics" 
              data-testid="tab-premium-analytics"
              className={!hasPremiumAnalytics ? "relative" : ""}
            >
              🚀 Premium Insights
              {!hasPremiumAnalytics && (
                <Badge className="ml-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs px-1.5 py-0">PREMIUM</Badge>
              )}
            </TabsTrigger>
          </TabsList>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="space-y-6">
              {/* Welcome Card */}
              <Card className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white">
                <CardContent className="pt-6">
                  <h2 className="text-2xl font-bold mb-2">Welcome back, {creator?.name}! 👋</h2>
                  <p className="text-purple-100">
                    Track your proposals, view ARRIS insights, and monitor your project progress.
                  </p>
                </CardContent>
              </Card>

              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-purple-600">{dashboard?.proposals?.total || 0}</div>
                    <p className="text-sm text-slate-500">Total Proposals</p>
                  </CardContent>
                </Card>
                <Card className="bg-blue-50">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-blue-600">{dashboard?.proposals?.by_status?.submitted || 0}</div>
                    <p className="text-sm text-blue-600">Pending Review</p>
                  </CardContent>
                </Card>
                <Card className="bg-green-50">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-green-600">{dashboard?.proposals?.by_status?.approved || 0}</div>
                    <p className="text-sm text-green-600">Approved</p>
                  </CardContent>
                </Card>
                <Card className="bg-purple-50">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-purple-600">{dashboard?.projects?.total || 0}</div>
                    <p className="text-sm text-purple-600">Active Projects</p>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Proposals */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Proposals</CardTitle>
                  <CardDescription>Your latest project proposals and their status</CardDescription>
                </CardHeader>
                <CardContent>
                  {dashboard?.proposals?.recent?.length > 0 ? (
                    <div className="space-y-3">
                      {dashboard.proposals.recent.map((proposal) => (
                        <div
                          key={proposal.id}
                          className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 cursor-pointer transition-colors"
                          onClick={() => {
                            setSelectedProposal(proposal);
                            setActiveTab("proposals");
                          }}
                          data-testid={`recent-proposal-${proposal.id}`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{getStatusIcon(proposal.status)}</span>
                            <div>
                              <p className="font-medium">{proposal.title}</p>
                              <p className="text-xs text-slate-500">
                                {new Date(proposal.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <Badge className={getStatusBadge(proposal.status)}>
                            {proposal.status?.replace(/_/g, " ")}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <p className="text-4xl mb-2">📋</p>
                      <p>No proposals yet. Submit your first project idea!</p>
                      <Button 
                        onClick={() => setShowNewProposal(true)} 
                        className="mt-4 bg-purple-600 hover:bg-purple-700"
                        data-testid="new-proposal-empty-btn"
                      >
                        + Create Your First Proposal
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Tasks Progress (if any) */}
              {dashboard?.tasks?.total > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Task Progress</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <Progress 
                        value={(dashboard.tasks.completed / dashboard.tasks.total) * 100} 
                        className="flex-1"
                      />
                      <span className="text-sm text-slate-600">
                        {dashboard.tasks.completed} / {dashboard.tasks.total} completed
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Proposals Tab */}
          <TabsContent value="proposals">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Proposals List */}
              <div className="lg:col-span-1 space-y-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-slate-700">All Proposals</h3>
                  <Button 
                    onClick={() => setShowNewProposal(true)} 
                    size="sm"
                    className="bg-purple-600 hover:bg-purple-700"
                    data-testid="new-proposal-list-btn"
                  >
                    + New
                  </Button>
                </div>
                {proposals.length > 0 ? (
                  proposals.map((proposal) => (
                    <Card
                      key={proposal.id}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedProposal?.id === proposal.id ? "ring-2 ring-purple-500" : ""
                      }`}
                      onClick={() => setSelectedProposal(proposal)}
                      data-testid={`proposal-card-${proposal.id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{proposal.title}</p>
                            <p className="text-xs text-slate-500 mt-1">
                              {new Date(proposal.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge className={getStatusBadge(proposal.status)}>
                            {getStatusIcon(proposal.status)}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Card>
                    <CardContent className="p-6 text-center text-slate-500">
                      <p className="text-4xl mb-2">📋</p>
                      <p>No proposals yet</p>
                      <Button 
                        onClick={() => setShowNewProposal(true)} 
                        size="sm"
                        className="mt-3 bg-purple-600 hover:bg-purple-700"
                        data-testid="new-proposal-empty-list-btn"
                      >
                        + Create Proposal
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Proposal Detail */}
              <div className="lg:col-span-2">
                {selectedProposal ? (
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle>{selectedProposal.title}</CardTitle>
                          <CardDescription>
                            Submitted on {new Date(selectedProposal.created_at).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <Badge className={getStatusBadge(selectedProposal.status)}>
                          {getStatusIcon(selectedProposal.status)} {selectedProposal.status?.replace(/_/g, " ")}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {/* Status Timeline */}
                      <div className="flex items-center gap-2 text-sm">
                        <span className={`w-3 h-3 rounded-full ${
                          ["submitted", "under_review", "approved", "in_progress", "completed"].includes(selectedProposal.status)
                            ? "bg-green-500" : "bg-slate-300"
                        }`}></span>
                        <span className="text-slate-600">Submitted</span>
                        <span className="flex-1 h-0.5 bg-slate-200"></span>
                        <span className={`w-3 h-3 rounded-full ${
                          ["under_review", "approved", "in_progress", "completed"].includes(selectedProposal.status)
                            ? "bg-green-500" : "bg-slate-300"
                        }`}></span>
                        <span className="text-slate-600">Review</span>
                        <span className="flex-1 h-0.5 bg-slate-200"></span>
                        <span className={`w-3 h-3 rounded-full ${
                          ["approved", "in_progress", "completed"].includes(selectedProposal.status)
                            ? "bg-green-500" : "bg-slate-300"
                        }`}></span>
                        <span className="text-slate-600">Approved</span>
                        <span className="flex-1 h-0.5 bg-slate-200"></span>
                        <span className={`w-3 h-3 rounded-full ${
                          selectedProposal.status === "completed" ? "bg-green-500" : "bg-slate-300"
                        }`}></span>
                        <span className="text-slate-600">Complete</span>
                      </div>

                      {/* Description */}
                      <div>
                        <h4 className="font-medium text-slate-700 mb-2">Description</h4>
                        <p className="text-slate-600 bg-slate-50 p-3 rounded-lg">
                          {selectedProposal.description || "No description provided"}
                        </p>
                      </div>

                      {/* Details Grid */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-slate-500">Priority</p>
                          <p className="font-medium">{selectedProposal.priority || "Medium"}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Timeline</p>
                          <p className="font-medium">{selectedProposal.timeline || "Not specified"}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Platforms</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {selectedProposal.platforms?.map((p) => (
                              <Badge key={p} variant="outline" className="text-xs">{p}</Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-slate-500">Proposal ID</p>
                          <p className="font-mono text-xs">{selectedProposal.id}</p>
                        </div>
                      </div>

                      {/* ARRIS Insights */}
                      {selectedProposal.arris_insights && (
                        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-4 rounded-lg border border-purple-200">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className="text-2xl">🧠</span>
                              <h4 className="font-semibold text-purple-800">ARRIS AI Insights</h4>
                            </div>
                            <div className="flex items-center gap-2">
                              {/* Processing Speed Badge */}
                              {selectedProposal.arris_insights.priority_processed && (
                                <Badge className="bg-amber-100 text-amber-700 text-xs">
                                  ⚡ Fast Processing
                                </Badge>
                              )}
                              {selectedProposal.arris_insights.processing_time_seconds && (
                                <Badge className="bg-slate-100 text-slate-600 text-xs">
                                  {selectedProposal.arris_insights.processing_time_seconds}s
                                </Badge>
                              )}
                              {selectedProposal.arris_insights.insight_level && (
                                <Badge className="bg-purple-200 text-purple-700 text-xs">
                                  {selectedProposal.arris_insights.insight_level === "full" ? "Full Access" :
                                   selectedProposal.arris_insights.insight_level === "summary_strengths" ? "Starter" :
                                   "Free Tier"}
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          {/* Summary */}
                          {selectedProposal.arris_insights.summary && (
                            <div className="mb-4">
                              <p className="text-sm text-purple-700 italic">
                                "{selectedProposal.arris_insights.summary}"
                              </p>
                            </div>
                          )}

                          {/* Complexity */}
                          {selectedProposal.arris_insights.estimated_complexity && (
                            <div className="mb-3">
                              <span className="text-xs text-purple-600 font-medium">Complexity: </span>
                              <Badge className="bg-purple-200 text-purple-800">
                                {selectedProposal.arris_insights.estimated_complexity}
                              </Badge>
                            </div>
                          )}

                          {/* Strengths */}
                          {selectedProposal.arris_insights.strengths?.length > 0 ? (
                            <div className="mb-3">
                              <p className="text-xs text-green-700 font-medium mb-1">✅ Strengths</p>
                              <ul className="text-sm text-slate-700 space-y-1">
                                {selectedProposal.arris_insights.strengths.map((s, i) => (
                                  <li key={i} className="flex items-start gap-2">
                                    <span className="text-green-500">•</span> {s}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : selectedProposal.arris_insights._gated?.strengths && (
                            <div className="mb-3 p-2 bg-amber-50 rounded border border-amber-200">
                              <p className="text-xs text-amber-700">🔒 {selectedProposal.arris_insights._gated.strengths}</p>
                            </div>
                          )}

                          {/* Risks */}
                          {selectedProposal.arris_insights.risks?.length > 0 ? (
                            <div className="mb-3">
                              <p className="text-xs text-amber-700 font-medium mb-1">⚠️ Potential Risks</p>
                              <ul className="text-sm text-slate-700 space-y-1">
                                {selectedProposal.arris_insights.risks.map((r, i) => (
                                  <li key={i} className="flex items-start gap-2">
                                    <span className="text-amber-500">•</span> {r}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : selectedProposal.arris_insights._gated?.risks && (
                            <div className="mb-3 p-2 bg-amber-50 rounded border border-amber-200">
                              <p className="text-xs text-amber-700">🔒 {selectedProposal.arris_insights._gated.risks}</p>
                            </div>
                          )}

                          {/* Recommendations */}
                          {selectedProposal.arris_insights.recommendations?.length > 0 ? (
                            <div className="mb-3">
                              <p className="text-xs text-blue-700 font-medium mb-1">💡 Recommendations</p>
                              <ul className="text-sm text-slate-700 space-y-1">
                                {selectedProposal.arris_insights.recommendations.map((r, i) => (
                                  <li key={i} className="flex items-start gap-2">
                                    <span className="text-blue-500">•</span> {r}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : selectedProposal.arris_insights._gated?.recommendations && (
                            <div className="mb-3 p-2 bg-amber-50 rounded border border-amber-200">
                              <p className="text-xs text-amber-700">🔒 {selectedProposal.arris_insights._gated.recommendations}</p>
                            </div>
                          )}

                          {/* Milestones */}
                          {selectedProposal.arris_insights.suggested_milestones?.length > 0 ? (
                            <div>
                              <p className="text-xs text-indigo-700 font-medium mb-1">🎯 Suggested Milestones</p>
                              <ol className="text-sm text-slate-700 space-y-1 list-decimal list-inside">
                                {selectedProposal.arris_insights.suggested_milestones.map((m, i) => (
                                  <li key={i}>{m}</li>
                                ))}
                              </ol>
                            </div>
                          ) : selectedProposal.arris_insights._gated?.milestones && (
                            <div className="p-2 bg-amber-50 rounded border border-amber-200">
                              <p className="text-xs text-amber-700">🔒 {selectedProposal.arris_insights._gated.milestones}</p>
                            </div>
                          )}
                          
                          {/* Upgrade CTA for gated features */}
                          {selectedProposal.arris_insights._gated && Object.keys(selectedProposal.arris_insights._gated).length > 0 && (
                            <div className="mt-4 p-3 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-lg border border-purple-300">
                              <p className="text-sm text-purple-800 font-medium mb-2">Unlock Full ARRIS Insights</p>
                              <p className="text-xs text-purple-600 mb-3">Upgrade to Pro for complete analysis including risks, recommendations, and milestones.</p>
                              <Button 
                                size="sm" 
                                className="bg-purple-600 hover:bg-purple-700 text-white"
                                onClick={() => navigate("/creator/subscription")}
                              >
                                ⚡ Upgrade Now
                              </Button>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Review Notes (if any) */}
                      {selectedProposal.review_notes && (
                        <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
                          <h4 className="font-medium text-amber-800 mb-2">📝 Review Notes</h4>
                          <p className="text-sm text-amber-700">{selectedProposal.review_notes}</p>
                        </div>
                      )}

                      {/* Project Link (if approved) */}
                      {selectedProposal.assigned_project_id && (
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                          <h4 className="font-medium text-green-800 mb-2">🚀 Project Created!</h4>
                          <p className="text-sm text-green-700">
                            Project ID: <span className="font-mono">{selectedProposal.assigned_project_id}</span>
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="p-12 text-center text-slate-500">
                      <p className="text-5xl mb-4">👈</p>
                      <p className="text-lg">Select a proposal to view details</p>
                      <p className="text-sm mt-2">Click on any proposal from the list to see ARRIS insights and status updates</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Analytics Tab (Pro+) */}
          <TabsContent value="analytics" data-testid="analytics-tab-content">
            {!hasAdvancedDashboard ? (
              /* Upgrade Prompt for Free/Starter users */
              <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
                <CardContent className="py-12 text-center">
                  <div className="mx-auto w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6">
                    <span className="text-4xl">📈</span>
                  </div>
                  <h2 className="text-2xl font-bold text-purple-800 mb-3">Advanced Analytics</h2>
                  <p className="text-purple-600 max-w-md mx-auto mb-6">
                    Unlock powerful insights with Pro tier: performance metrics, approval rates, 
                    submission trends, ARRIS activity timeline, and priority review status.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <span className="text-2xl">📊</span>
                      <p className="text-xs text-slate-600 mt-2">Approval Rate</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <span className="text-2xl">⏱️</span>
                      <p className="text-xs text-slate-600 mt-2">Review Time</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <span className="text-2xl">📈</span>
                      <p className="text-xs text-slate-600 mt-2">Trends</p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <span className="text-2xl">🧠</span>
                      <p className="text-xs text-slate-600 mt-2">ARRIS Activity</p>
                    </div>
                  </div>
                  <Button 
                    onClick={() => navigate("/creator/subscription")}
                    className="bg-purple-600 hover:bg-purple-700"
                    data-testid="upgrade-to-pro-btn"
                  >
                    ⚡ Upgrade to Pro
                  </Button>
                </CardContent>
              </Card>
            ) : advancedLoading ? (
              /* Loading State */
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
              </div>
            ) : advancedData ? (
              /* Advanced Dashboard Content */
              <div className="space-y-6">
                {/* Priority Review Banner (if applicable) */}
                {advancedData.has_priority_review && (
                  <Card className="bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                    <CardContent className="py-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">⚡</span>
                        <div>
                          <p className="font-bold">Priority Review Active</p>
                          <p className="text-amber-100 text-sm">Your proposals are reviewed faster</p>
                        </div>
                      </div>
                      {advancedData.performance.priority_queue_position && (
                        <div className="text-right">
                          <p className="text-xs text-amber-100">Queue Position</p>
                          <p className="text-2xl font-bold">#{advancedData.performance.priority_queue_position}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Performance Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
                    <CardContent className="pt-6 text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {advancedData.performance.approval_rate}%
                      </div>
                      <p className="text-sm text-green-700 mt-1">Approval Rate</p>
                      <Progress 
                        value={advancedData.performance.approval_rate} 
                        className="mt-3 h-2"
                      />
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                    <CardContent className="pt-6 text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {advancedData.performance.avg_review_time_hours 
                          ? `${advancedData.performance.avg_review_time_hours}h`
                          : "—"}
                      </div>
                      <p className="text-sm text-blue-700 mt-1">Avg Review Time</p>
                      <p className="text-xs text-blue-500 mt-2">
                        {advancedData.has_priority_review ? "⚡ Priority" : "Standard"}
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200">
                    <CardContent className="pt-6 text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {advancedData.performance.completed}
                      </div>
                      <p className="text-sm text-purple-700 mt-1">Completed</p>
                      <p className="text-xs text-purple-500 mt-2">
                        {advancedData.performance.in_progress} in progress
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
                    <CardContent className="pt-6 text-center">
                      <div className="text-3xl font-bold text-amber-600">
                        {advancedData.arris.total_interactions}
                      </div>
                      <p className="text-sm text-amber-700 mt-1">ARRIS Interactions</p>
                      <p className="text-xs text-amber-500 mt-2">
                        {advancedData.arris.successful} successful
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Monthly Trends */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span>📈</span> Submission Trends
                      </CardTitle>
                      <CardDescription>Your proposal activity over time</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {advancedData.trends.monthly_submissions?.length > 0 ? (
                        <div className="space-y-3">
                          {advancedData.trends.monthly_submissions.map((month) => (
                            <div key={month.month} className="flex items-center gap-3">
                              <span className="text-xs text-slate-500 w-16">{month.month}</span>
                              <div className="flex-1 bg-slate-100 rounded-full h-6 overflow-hidden">
                                <div 
                                  className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full flex items-center justify-end pr-2"
                                  style={{ 
                                    width: `${Math.min(100, (month.count / Math.max(...advancedData.trends.monthly_submissions.map(m => m.count))) * 100)}%`,
                                    minWidth: '30px'
                                  }}
                                >
                                  <span className="text-xs text-white font-medium">{month.count}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-center py-4">No submission data yet</p>
                      )}
                      {advancedData.insights.top_performing_month && (
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-xs text-slate-500">
                            🏆 Most active: <span className="font-medium text-purple-600">{advancedData.insights.top_performing_month}</span>
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Status Breakdown */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span>📊</span> Status Breakdown
                      </CardTitle>
                      <CardDescription>Current proposal statuses</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {advancedData.status_breakdown?.length > 0 ? (
                        <div className="space-y-3">
                          {advancedData.status_breakdown.map((status) => (
                            <div key={status.status} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                              <div className="flex items-center gap-2">
                                <span>{getStatusIcon(status.status)}</span>
                                <span className="text-sm font-medium capitalize">
                                  {status.status?.replace(/_/g, " ")}
                                </span>
                              </div>
                              <Badge className={getStatusBadge(status.status)}>
                                {status.count}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-center py-4">No proposals yet</p>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Complexity Distribution & ARRIS Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Complexity Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span>🎯</span> Project Complexity
                      </CardTitle>
                      <CardDescription>ARRIS-analyzed complexity levels</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {advancedData.complexity_distribution?.length > 0 ? (
                        <div className="space-y-3">
                          {advancedData.complexity_distribution.map((item) => {
                            const colors = {
                              "Low": "bg-green-500",
                              "Medium": "bg-amber-500",
                              "High": "bg-orange-500",
                              "Very High": "bg-red-500"
                            };
                            return (
                              <div key={item.complexity} className="flex items-center gap-3">
                                <span className={`w-3 h-3 rounded-full ${colors[item.complexity] || "bg-slate-400"}`}></span>
                                <span className="text-sm flex-1">{item.complexity}</span>
                                <span className="text-sm font-medium text-slate-600">{item.count}</span>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-center py-4">Submit proposals to see complexity analysis</p>
                      )}
                      {advancedData.insights.most_common_complexity && (
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-xs text-slate-500">
                            Most common: <span className="font-medium text-purple-600">{advancedData.insights.most_common_complexity}</span>
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* ARRIS Activity Timeline */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <span>🧠</span> ARRIS Activity
                      </CardTitle>
                      <CardDescription>Recent AI analysis interactions</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {advancedData.arris.recent_activity?.length > 0 ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {advancedData.arris.recent_activity.map((activity, idx) => (
                            <div 
                              key={idx} 
                              className="flex items-center gap-3 p-2 bg-purple-50 rounded-lg text-sm"
                            >
                              <span className={`w-2 h-2 rounded-full ${activity.success ? "bg-green-500" : "bg-red-500"}`}></span>
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-purple-700 truncate">
                                  {activity.response_type || activity.query_category || "Analysis"}
                                </p>
                                <p className="text-xs text-purple-500">
                                  {new Date(activity.timestamp).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 text-center py-4">No ARRIS activity yet</p>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Dashboard Level Badge */}
                <div className="text-center pt-4 border-t">
                  <Badge className="bg-purple-100 text-purple-700">
                    {advancedData.dashboard_level === "custom" ? "🏆 Custom Dashboard (Elite)" : "⚡ Advanced Dashboard (Pro)"}
                  </Badge>
                  {advancedData.has_advanced_analytics && (
                    <Badge className="ml-2 bg-amber-100 text-amber-700">
                      📊 Advanced Analytics Enabled
                    </Badge>
                  )}
                </div>
              </div>
            ) : (
              /* Error/No Data State */
              <Card>
                <CardContent className="py-12 text-center text-slate-500">
                  <p className="text-4xl mb-4">📊</p>
                  <p>Unable to load analytics data</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => {
                      setAdvancedData(null);
                      fetchAdvancedDashboard();
                    }}
                  >
                    Retry
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-slate-400 text-sm">
        <p>Powered by ARRIS Pattern Engine • Creators Hive HQ</p>
      </footer>
    </div>
  );
};

export default CreatorDashboard;
