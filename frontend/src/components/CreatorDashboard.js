/**
 * Creator Dashboard - Creator-Facing Proposal Management
 * View proposals, track status, read ARRIS insights
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

// ============== CREATOR DASHBOARD ==============

export const CreatorDashboard = () => {
  const { creator, logout } = useCreatorAuth();
  const [dashboard, setDashboard] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [selectedProposal, setSelectedProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const navigate = useNavigate();

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return { Authorization: `Bearer ${token}` };
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const headers = getAuthHeaders();
      
      const [dashboardRes, proposalsRes] = await Promise.all([
        axios.get(`${API}/creators/me/dashboard`, { headers }),
        axios.get(`${API}/creators/me/proposals`, { headers })
      ]);
      
      setDashboard(dashboardRes.data);
      setProposals(proposalsRes.data);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50" data-testid="creator-dashboard">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-purple-600">Creators Hive HQ</h1>
            <p className="text-xs text-slate-500">Creator Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-medium text-slate-900">{creator?.name}</p>
              <p className="text-xs text-slate-500">{creator?.email}</p>
            </div>
            <Badge className="bg-purple-100 text-purple-700">{dashboard?.creator?.tier || "Free"}</Badge>
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
                <h3 className="font-semibold text-slate-700 mb-4">All Proposals</h3>
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
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-2xl">🧠</span>
                            <h4 className="font-semibold text-purple-800">ARRIS AI Insights</h4>
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
                          {selectedProposal.arris_insights.strengths?.length > 0 && (
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
                          )}

                          {/* Risks */}
                          {selectedProposal.arris_insights.risks?.length > 0 && (
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
                          )}

                          {/* Recommendations */}
                          {selectedProposal.arris_insights.recommendations?.length > 0 && (
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
                          )}

                          {/* Milestones */}
                          {selectedProposal.arris_insights.suggested_milestones?.length > 0 && (
                            <div>
                              <p className="text-xs text-indigo-700 font-medium mb-1">🎯 Suggested Milestones</p>
                              <ol className="text-sm text-slate-700 space-y-1 list-decimal list-inside">
                                {selectedProposal.arris_insights.suggested_milestones.map((m, i) => (
                                  <li key={i}>{m}</li>
                                ))}
                              </ol>
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
