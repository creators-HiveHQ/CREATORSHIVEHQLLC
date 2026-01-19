import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { CreatorRegistrationForm, AdminCreatorsPage } from "@/components/CreatorRegistration";
import { AdminProposalsPage } from "@/components/ProjectProposal";
import WebhooksAdmin from "@/components/WebhooksAdmin";
import { CreatorAuthProvider, CreatorLoginPage, CreatorProtectedRoute, CreatorDashboard } from "@/components/CreatorDashboard";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icons as simple components
const Icons = {
  Users: () => <span className="text-xl">👥</span>,
  Projects: () => <span className="text-xl">📁</span>,
  Calculator: () => <span className="text-xl">💰</span>,
  Brain: () => <span className="text-xl">🧠</span>,
  Chart: () => <span className="text-xl">📊</span>,
  Database: () => <span className="text-xl">🗄️</span>,
  Refresh: () => <span className="text-lg">🔄</span>,
  Check: () => <span className="text-green-500">✓</span>,
  Warning: () => <span className="text-yellow-500">⚠️</span>,
  Activity: () => <span className="text-xl">📈</span>,
  Settings: () => <span className="text-xl">⚙️</span>,
  Menu: () => <span className="text-xl">☰</span>,
  Logout: () => <span className="text-xl">🚪</span>,
};

// Login Page
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register, isAuthenticated } = useAuth();

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register(name, email, password);
      }

      if (!result.success) {
        setError(result.error);
      }
      // If success, the isAuthenticated check above will redirect
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4" data-testid="login-page">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-amber-500">Creators Hive HQ</h1>
            <p className="text-sm text-slate-500">Zero-Human Operational Model</p>
          </div>
          <CardTitle>{isLogin ? "Admin Login" : "Register Admin"}</CardTitle>
          <CardDescription>
            {isLogin ? "Sign in to access the admin dashboard" : "Create a new admin account"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={!isLogin}
                  data-testid="input-name"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@hivehq.com"
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
            <Button type="submit" className="w-full" disabled={loading} data-testid="submit-btn">
              {loading ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => { setIsLogin(!isLogin); setError(""); }}
              className="text-sm text-amber-600 hover:underline"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "Need an account? Register" : "Already have an account? Sign In"}
            </button>
          </div>
          {isLogin && (
            <div className="mt-4 p-3 bg-slate-50 rounded-lg text-sm text-slate-600">
              <p className="font-medium">Default Admin Credentials:</p>
              <p>Email: admin@hivehq.com</p>
              <p>Password: admin123</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Navigation Sidebar
const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navItems = [
    { path: "/", label: "Dashboard", icon: "📊" },
    { path: "/creators", label: "Creators", icon: "✨" },
    { path: "/proposals", label: "Proposals", icon: "📋" },
    { path: "/webhooks", label: "Webhooks", icon: "⚡" },
    { path: "/users", label: "Users", icon: "👥" },
    { path: "/projects", label: "Projects", icon: "📁" },
    { path: "/calculator", label: "Calculator", icon: "💰" },
    { path: "/subscriptions", label: "Subscriptions", icon: "💳" },
    { path: "/arris", label: "ARRIS Engine", icon: "🧠" },
    { path: "/patterns", label: "Patterns", icon: "🔮" },
    { path: "/schema", label: "Schema Index", icon: "🗄️" },
  ];

  return (
    <div className="w-64 bg-slate-900 text-white min-h-screen p-4 fixed left-0 top-0">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-amber-400">Creators Hive HQ</h1>
        <p className="text-xs text-slate-400 mt-1">Zero-Human Ops Model</p>
      </div>
      <nav className="space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, "-")}`}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              location.pathname === item.path
                ? "bg-amber-500/20 text-amber-400"
                : "hover:bg-slate-800 text-slate-300"
            }`}
          >
            <span>{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="absolute bottom-4 left-4 right-4 space-y-3">
        {/* User Info */}
        {user && (
          <div className="bg-slate-800 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center text-sm font-bold text-slate-900">
                {user.name?.charAt(0)?.toUpperCase() || "A"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.name}</p>
                <p className="text-xs text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="w-full mt-2 text-slate-400 hover:text-white hover:bg-slate-700"
              onClick={logout}
              data-testid="logout-btn"
            >
              <Icons.Logout /> <span className="ml-2">Sign Out</span>
            </Button>
          </div>
        )}
        {/* System Status */}
        <div className="bg-slate-800 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-xs text-slate-400">System Active</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">ARRIS Pattern Engine Running</p>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard
const Dashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboard(response.data);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Master Dashboard</h1>
          <p className="text-slate-500">Zero-Human Operational Model</p>
        </div>
        <Button onClick={fetchDashboard} variant="outline" className="gap-2" data-testid="refresh-btn">
          <Icons.Refresh /> Refresh
        </Button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card data-testid="card-users">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.stats?.users || 0}</div>
            <p className="text-xs text-slate-500">Active creators & coaches</p>
          </CardContent>
        </Card>

        <Card data-testid="card-revenue">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${dashboard?.financials?.total_revenue?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-slate-500">Self-Funding Loop Active</p>
          </CardContent>
        </Card>

        <Card data-testid="card-projects">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Active Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.stats?.projects || 0}</div>
            <p className="text-xs text-slate-500">Across all users</p>
          </CardContent>
        </Card>

        <Card data-testid="card-arris">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">ARRIS Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{dashboard?.arris?.total_queries || 0}</div>
            <p className="text-xs text-slate-500">Avg: {dashboard?.arris?.avg_response_time?.toFixed(2) || 0}s</p>
          </CardContent>
        </Card>
      </div>

      {/* Financial Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card data-testid="card-financials">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icons.Calculator /> Financial Summary
            </CardTitle>
            <CardDescription>Self-Funding Loop via Calculator (Sheet 06)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Revenue</span>
                <span className="text-xl font-bold text-green-600">
                  ${dashboard?.financials?.total_revenue?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Expenses</span>
                <span className="text-xl font-bold text-red-500">
                  ${dashboard?.financials?.total_expenses?.toLocaleString() || 0}
                </span>
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-slate-900 font-medium">Net Profit</span>
                <span className={`text-xl font-bold ${dashboard?.financials?.net_profit >= 0 ? "text-green-600" : "text-red-500"}`}>
                  ${dashboard?.financials?.net_profit?.toLocaleString() || 0}
                </span>
              </div>
              <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                <p className="text-sm text-amber-800 flex items-center gap-2">
                  <Icons.Check /> Self-Funding Loop: Subscriptions → Calculator
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="card-system-stats">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icons.Database /> Collection Stats
            </CardTitle>
            <CardDescription>Database collections based on Sheet 15 Index</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {dashboard?.stats && Object.entries(dashboard.stats).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                  <span className="text-sm text-slate-600 capitalize">{key.replace(/_/g, " ")}</span>
                  <Badge variant="secondary">{value}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      <Card data-testid="card-system-status">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icons.Activity /> System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                <span className="font-medium text-green-800">Pattern Engine</span>
              </div>
              <p className="text-sm text-green-700">ARRIS Active</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                <span className="font-medium text-blue-800">Self-Funding Loop</span>
              </div>
              <p className="text-sm text-blue-700">Revenue Routing Active</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 bg-purple-500 rounded-full"></span>
                <span className="font-medium text-purple-800">Zero-Human Model</span>
              </div>
              <p className="text-sm text-purple-700">Fully Operational</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Users Page
const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ role: "", tier: "" });

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.role) params.append("role", filter.role);
      if (filter.tier) params.append("tier", filter.tier);
      const response = await axios.get(`${API}/users?${params.toString()}`);
      setUsers(response.data);
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return (
    <div className="space-y-6" data-testid="users-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Users (01_Users)</h1>
          <p className="text-slate-500">User Management - Sheet 01</p>
        </div>
        <div className="flex gap-2">
          <Select value={filter.role} onValueChange={(v) => setFilter({ ...filter, role: v === "all" ? "" : v })}>
            <SelectTrigger className="w-32" data-testid="filter-role">
              <SelectValue placeholder="All Roles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Roles</SelectItem>
              <SelectItem value="Creator">Creator</SelectItem>
              <SelectItem value="Coach">Coach</SelectItem>
              <SelectItem value="Staff">Staff</SelectItem>
              <SelectItem value="Admin">Admin</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filter.tier} onValueChange={(v) => setFilter({ ...filter, tier: v === "all" ? "" : v })}>
            <SelectTrigger className="w-32" data-testid="filter-tier">
              <SelectValue placeholder="All Tiers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tiers</SelectItem>
              <SelectItem value="Platinum">Platinum</SelectItem>
              <SelectItem value="Gold">Gold</SelectItem>
              <SelectItem value="Silver">Silver</SelectItem>
              <SelectItem value="Free">Free</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Business Type</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">Loading...</TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">No users found</TableCell>
                </TableRow>
              ) : (
                users.map((user) => (
                  <TableRow key={user.id} data-testid={`user-row-${user.id}`}>
                    <TableCell className="font-mono text-sm">{user.id}</TableCell>
                    <TableCell className="font-medium">{user.name}</TableCell>
                    <TableCell className="text-slate-500">{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{user.role}</Badge>
                    </TableCell>
                    <TableCell>{user.business_type}</TableCell>
                    <TableCell>
                      <Badge className={
                        user.tier === "Platinum" ? "bg-purple-500" :
                        user.tier === "Gold" ? "bg-amber-500" :
                        user.tier === "Silver" ? "bg-slate-400" : "bg-slate-200 text-slate-700"
                      }>
                        {user.tier}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className={`flex items-center gap-1 ${user.account_status === "Active" ? "text-green-600" : "text-slate-400"}`}>
                        <span className={`w-2 h-2 rounded-full ${user.account_status === "Active" ? "bg-green-500" : "bg-slate-300"}`}></span>
                        {user.account_status}
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// Projects Page
const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await axios.get(`${API}/projects`);
        setProjects(response.data);
      } catch (error) {
        console.error("Error fetching projects:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "Completed": return "bg-green-500";
      case "In_Progress": return "bg-blue-500";
      case "Planning": return "bg-amber-500";
      default: return "bg-slate-400";
    }
  };

  return (
    <div className="space-y-6" data-testid="projects-page">
      <div>
        <h1 className="text-2xl font-bold">Projects (04_Projects)</h1>
        <p className="text-slate-500">Operations & Planning - Sheet 04</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 text-center py-8">Loading...</div>
        ) : projects.map((project) => (
          <Card key={project.id} data-testid={`project-card-${project.id}`} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg">{project.title?.replace(/_/g, " ")}</CardTitle>
                <Badge className={getStatusColor(project.status)}>{project.status?.replace(/_/g, " ")}</Badge>
              </div>
              <CardDescription>{project.platform}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Project ID</span>
                  <span className="font-mono">{project.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">User</span>
                  <span>{project.user_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Priority</span>
                  <Badge variant="outline" className={
                    project.priority_level === "Critical" ? "border-red-500 text-red-500" :
                    project.priority_level === "High" ? "border-orange-500 text-orange-500" :
                    "border-slate-300"
                  }>
                    {project.priority_level}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

// Calculator Page (Revenue Hub)
const CalculatorPage = () => {
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [entriesRes, summaryRes] = await Promise.all([
          axios.get(`${API}/calculator`),
          axios.get(`${API}/calculator/summary`)
        ]);
        setEntries(entriesRes.data);
        setSummary(summaryRes.data);
      } catch (error) {
        console.error("Error fetching calculator data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6" data-testid="calculator-page">
      <div>
        <h1 className="text-2xl font-bold">Calculator (06_Calculator)</h1>
        <p className="text-slate-500">Revenue Hub - All money flows through here</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-green-50 border-green-200">
            <CardContent className="pt-6">
              <p className="text-sm text-green-700">Total Revenue</p>
              <p className="text-2xl font-bold text-green-800">${summary.total_revenue?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-red-50 border-red-200">
            <CardContent className="pt-6">
              <p className="text-sm text-red-700">Total Expenses</p>
              <p className="text-2xl font-bold text-red-800">${summary.total_expenses?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className={`${summary.net_profit >= 0 ? "bg-blue-50 border-blue-200" : "bg-orange-50 border-orange-200"}`}>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-600">Net Profit</p>
              <p className={`text-2xl font-bold ${summary.net_profit >= 0 ? "text-blue-800" : "text-orange-800"}`}>
                ${summary.net_profit?.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-amber-50 border-amber-200">
            <CardContent className="pt-6">
              <p className="text-sm text-amber-700">Self-Funding Loop</p>
              <p className="text-lg font-bold text-amber-800">{summary.self_funding_loop}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue & Expense Entries</CardTitle>
          <CardDescription>Financial transactions routed through Calculator</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Calc ID</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Month/Year</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="text-right">Revenue</TableHead>
                <TableHead className="text-right">Expenses</TableHead>
                <TableHead className="text-right">Net Margin</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">Loading...</TableCell>
                </TableRow>
              ) : entries.map((entry) => (
                <TableRow key={entry.id} data-testid={`calc-row-${entry.id}`}>
                  <TableCell className="font-mono text-sm">{entry.id}</TableCell>
                  <TableCell>{entry.user_id}</TableCell>
                  <TableCell>{entry.month_year}</TableCell>
                  <TableCell>
                    <Badge className={entry.category === "Income" ? "bg-green-500" : "bg-red-500"}>
                      {entry.category}
                    </Badge>
                  </TableCell>
                  <TableCell>{entry.source}</TableCell>
                  <TableCell className="text-right text-green-600">${entry.revenue?.toLocaleString()}</TableCell>
                  <TableCell className="text-right text-red-500">${entry.expenses?.toLocaleString()}</TableCell>
                  <TableCell className={`text-right font-medium ${entry.net_margin >= 0 ? "text-green-600" : "text-red-500"}`}>
                    ${entry.net_margin?.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// Subscriptions Page
const SubscriptionsPage = () => {
  const [subscriptions, setSubscriptions] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [subsRes, revenueRes] = await Promise.all([
          axios.get(`${API}/subscriptions`),
          axios.get(`${API}/subscriptions/revenue`)
        ]);
        setSubscriptions(subsRes.data);
        setRevenue(revenueRes.data);
      } catch (error) {
        console.error("Error fetching subscriptions:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6" data-testid="subscriptions-page">
      <div>
        <h1 className="text-2xl font-bold">Subscriptions (17_Subscriptions)</h1>
        <p className="text-slate-500">Self-Funding Loop - Links to Calculator</p>
      </div>

      {/* Revenue Summary */}
      {revenue && (
        <Card className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-700">Total Subscription Revenue</p>
                <p className="text-3xl font-bold text-amber-900">${revenue.total_subscription_revenue?.toLocaleString()}</p>
                <p className="text-sm text-amber-600 mt-1">{revenue.active_subscriptions} active subscriptions</p>
              </div>
              <div className="text-right">
                <Badge className="bg-amber-500 text-white px-4 py-2">
                  {revenue.self_funding_loop?.split("-")[0]}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Subscriptions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sub ID</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead className="text-right">Monthly Cost</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Linked Calc</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">Loading...</TableCell>
                </TableRow>
              ) : subscriptions.map((sub) => (
                <TableRow key={sub.id} data-testid={`sub-row-${sub.id}`}>
                  <TableCell className="font-mono text-sm">{sub.id}</TableCell>
                  <TableCell>{sub.user_id}</TableCell>
                  <TableCell>{sub.plan_name?.replace(/_/g, " ")}</TableCell>
                  <TableCell>
                    <Badge className={
                      sub.tier === "Platinum" ? "bg-purple-500" :
                      sub.tier === "Gold" ? "bg-amber-500" :
                      sub.tier === "Silver" ? "bg-slate-400" : "bg-slate-200 text-slate-700"
                    }>
                      {sub.tier}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">${sub.monthly_cost}</TableCell>
                  <TableCell>
                    <span className={`flex items-center gap-1 ${sub.payment_status === "Active" ? "text-green-600" : "text-slate-400"}`}>
                      <span className={`w-2 h-2 rounded-full ${sub.payment_status === "Active" ? "bg-green-500" : "bg-slate-300"}`}></span>
                      {sub.payment_status}
                    </span>
                  </TableCell>
                  <TableCell>
                    {sub.linked_calc_id ? (
                      <Badge variant="outline" className="text-amber-600 border-amber-300">
                        → {sub.linked_calc_id}
                      </Badge>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// ARRIS Engine Page
const ArrisPage = () => {
  const [usage, setUsage] = useState([]);
  const [performance, setPerformance] = useState([]);
  const [training, setTraining] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("usage");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usageRes, perfRes, trainRes] = await Promise.all([
          axios.get(`${API}/arris/usage`),
          axios.get(`${API}/arris/performance`),
          axios.get(`${API}/arris/training`)
        ]);
        setUsage(usageRes.data);
        setPerformance(perfRes.data);
        setTraining(trainRes.data);
      } catch (error) {
        console.error("Error fetching ARRIS data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6" data-testid="arris-page">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Icons.Brain /> ARRIS Pattern Engine
        </h1>
        <p className="text-slate-500">AI Agent - Usage Log, Performance, Training Data (Sheets 19-21)</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="usage" data-testid="tab-usage">Usage Log (19)</TabsTrigger>
          <TabsTrigger value="performance" data-testid="tab-performance">Performance (20)</TabsTrigger>
          <TabsTrigger value="training" data-testid="tab-training">Training Data (21)</TabsTrigger>
        </TabsList>

        <TabsContent value="usage">
          <Card>
            <CardHeader>
              <CardTitle>ARRIS Usage Log</CardTitle>
              <CardDescription>All AI interactions logged for pattern analysis</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Log ID</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Query</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Response</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Project</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={7} className="text-center py-8">Loading...</TableCell></TableRow>
                  ) : usage.map((log) => (
                    <TableRow key={log.id} data-testid={`arris-log-${log.id}`}>
                      <TableCell className="font-mono text-sm">{log.id}</TableCell>
                      <TableCell>{log.user_id}</TableCell>
                      <TableCell className="max-w-xs truncate">{log.user_query_snippet}</TableCell>
                      <TableCell><Badge variant="outline">{log.response_type}</Badge></TableCell>
                      <TableCell className="font-mono text-sm">{log.response_id}</TableCell>
                      <TableCell>{log.time_taken_s}s</TableCell>
                      <TableCell>{log.linked_project || "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>ARRIS Performance Reviews</CardTitle>
              <CardDescription>Quality assessments of AI responses</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Review ID</TableHead>
                    <TableHead>Log ID</TableHead>
                    <TableHead>Quality Score</TableHead>
                    <TableHead>Errors</TableHead>
                    <TableHead>Reviewer</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Verdict</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={7} className="text-center py-8">Loading...</TableCell></TableRow>
                  ) : performance.map((review) => (
                    <TableRow key={review.id} data-testid={`arris-perf-${review.id}`}>
                      <TableCell className="font-mono text-sm">{review.id}</TableCell>
                      <TableCell className="font-mono text-sm">{review.log_id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={review.quality_score * 10} className="w-16 h-2" />
                          <span>{review.quality_score}/10</span>
                        </div>
                      </TableCell>
                      <TableCell>{review.error_count}</TableCell>
                      <TableCell>{review.human_reviewer_id}</TableCell>
                      <TableCell><Badge variant="secondary">{review.feedback_tags}</Badge></TableCell>
                      <TableCell>
                        <Badge className={
                          review.final_verdict === "Approved" ? "bg-green-500" :
                          review.final_verdict === "Needs_Correction" ? "bg-amber-500" : "bg-red-500"
                        }>
                          {review.final_verdict}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="training">
          <Card>
            <CardHeader>
              <CardTitle>ARRIS Training Data Sources</CardTitle>
              <CardDescription>Data sources used to train ARRIS</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data Source ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Summary</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Reviewer</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={6} className="text-center py-8">Loading...</TableCell></TableRow>
                  ) : training.map((data) => (
                    <TableRow key={data.id} data-testid={`arris-train-${data.id}`}>
                      <TableCell className="font-mono text-sm">{data.id}</TableCell>
                      <TableCell><Badge variant="outline">{data.source_type}</Badge></TableCell>
                      <TableCell>{data.content_summary}</TableCell>
                      <TableCell>v{data.version}</TableCell>
                      <TableCell>
                        <Badge className={
                          data.compliance_status === "Approved" ? "bg-green-500" : "bg-amber-500"
                        }>
                          {data.compliance_status}
                        </Badge>
                      </TableCell>
                      <TableCell>{data.reviewer_id}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Patterns Page
const PatternsPage = () => {
  const [patterns, setPatterns] = useState(null);
  const [memoryPalace, setMemoryPalace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patternType, setPatternType] = useState("usage");

  useEffect(() => {
    const fetchPatterns = async () => {
      try {
        setLoading(true);
        const [patternsRes, memoryRes] = await Promise.all([
          axios.get(`${API}/patterns/analyze?pattern_type=${patternType}&days=30`),
          axios.get(`${API}/patterns/memory-palace`)
        ]);
        setPatterns(patternsRes.data);
        setMemoryPalace(memoryRes.data);
      } catch (error) {
        console.error("Error fetching patterns:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPatterns();
  }, [patternType]);

  return (
    <div className="space-y-6" data-testid="patterns-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            🔮 Pattern Analysis
          </h1>
          <p className="text-slate-500">ARRIS reads patterns over time, not single events</p>
        </div>
        <Select value={patternType} onValueChange={setPatternType}>
          <SelectTrigger className="w-40" data-testid="pattern-type-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="usage">Usage Patterns</SelectItem>
            <SelectItem value="revenue">Revenue Patterns</SelectItem>
            <SelectItem value="engagement">Engagement</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading patterns...</div>
      ) : (
        <>
          {/* Pattern Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Pattern Analysis: {patternType}</CardTitle>
              <CardDescription>
                Time Range: {patterns?.time_range?.start?.split("T")[0]} to {patterns?.time_range?.end?.split("T")[0]}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Data Points</h4>
                  <div className="space-y-2">
                    {patterns?.data?.map((item, i) => (
                      <div key={i} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                        <span>{item._id || "Unknown"}</span>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">{item.count || item.total_revenue?.toLocaleString() || item.total_views?.toLocaleString()}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Insights</h4>
                  <ul className="space-y-2">
                    {patterns?.insights?.map((insight, i) => (
                      <li key={i} className="flex items-start gap-2 p-2 bg-blue-50 rounded text-blue-800">
                        <Icons.Check />
                        {insight}
                      </li>
                    ))}
                  </ul>
                  {patterns?.recommendations?.length > 0 && (
                    <>
                      <h4 className="font-medium mb-3 mt-4">Recommendations</h4>
                      <ul className="space-y-2">
                        {patterns?.recommendations?.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2 p-2 bg-amber-50 rounded text-amber-800">
                            <Icons.Warning />
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Memory Palace */}
          {memoryPalace && (
            <Card>
              <CardHeader>
                <CardTitle>Memory Palace Overview</CardTitle>
                <CardDescription>Comprehensive view across all data sources</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-medium text-slate-700 mb-2">Activity Summary</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Projects</span>
                        <span className="font-medium">{memoryPalace.sections?.activity?.projects}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tasks Completed</span>
                        <span className="font-medium">{memoryPalace.sections?.activity?.tasks_completed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>ARRIS Queries</span>
                        <span className="font-medium">{memoryPalace.sections?.activity?.arris_queries}</span>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-700 mb-2">Financials</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Revenue</span>
                        <span className="font-medium text-green-600">${memoryPalace.sections?.financials?.total_revenue?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Expenses</span>
                        <span className="font-medium text-red-500">${memoryPalace.sections?.financials?.total_expenses?.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Net Profit</span>
                        <span className="font-medium">${memoryPalace.sections?.financials?.net_profit?.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-700 mb-2">System Status</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        <span>Self-Funding Loop Active</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        <span>Pattern Engine Running</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

// Schema Index Page
const SchemaPage = () => {
  const [schema, setSchema] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSchema = async () => {
      try {
        const response = await axios.get(`${API}/schema`);
        setSchema(response.data.schema_index || []);
      } catch (error) {
        console.error("Error fetching schema:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchSchema();
  }, []);

  // Group by category
  const groupedSchema = schema.reduce((acc, item) => {
    const cat = item.category || "Other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="schema-page">
      <div>
        <h1 className="text-2xl font-bold">Schema Index (15_Index)</h1>
        <p className="text-slate-500">Source of Truth - No-Assumption Protocol</p>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading schema...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(groupedSchema).map(([category, items]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="text-lg">{category.replace(/_/g, " ")}</CardTitle>
                <CardDescription>{items.length} sheets</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {items.map((item) => (
                    <div key={item.sheet_no} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                      <div>
                        <span className="font-mono text-sm text-slate-500 mr-2">{String(item.sheet_no).padStart(2, "0")}</span>
                        <span className="font-medium">{item.sheet_name}</span>
                      </div>
                      <Badge variant="outline" className="font-mono text-xs">
                        {item.primary_key_field}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Layout wrapper
const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-100">
      <Sidebar />
      <main className="ml-64 p-8">
        {children}
      </main>
    </div>
  );
};

// Main App
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public route - Login */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout><Dashboard /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/users" element={
            <ProtectedRoute>
              <Layout><UsersPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/projects" element={
            <ProtectedRoute>
              <Layout><ProjectsPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/calculator" element={
            <ProtectedRoute>
              <Layout><CalculatorPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/subscriptions" element={
            <ProtectedRoute>
              <Layout><SubscriptionsPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/arris" element={
            <ProtectedRoute>
              <Layout><ArrisPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/patterns" element={
            <ProtectedRoute>
              <Layout><PatternsPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/schema" element={
            <ProtectedRoute>
              <Layout><SchemaPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/creators" element={
            <ProtectedRoute>
              <Layout><AdminCreatorsPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/proposals" element={
            <ProtectedRoute>
              <Layout><AdminProposalsPage /></Layout>
            </ProtectedRoute>
          } />
          <Route path="/webhooks" element={
            <ProtectedRoute>
              <Layout><WebhooksAdmin /></Layout>
            </ProtectedRoute>
          } />
          
          {/* Public Creator Registration Form */}
          <Route path="/register" element={<CreatorRegistrationForm />} />
          
          {/* Catch-all redirect to login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
