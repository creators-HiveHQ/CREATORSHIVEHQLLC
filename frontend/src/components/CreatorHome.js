/**
 * Creator Home Screen
 * ====================
 * The user-facing front door of the Hive.
 * First screen a creator sees after login or impersonation.
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Home, Eye, Layers, Zap, FileText, Calendar,
  ArrowRight, ChevronRight, Sparkles, Activity,
  Clock, Bell, TrendingUp, Target, Settings,
  MessageSquare, BarChart3, RefreshCw, AlertCircle,
  LogOut, Shield
} from "lucide-react";

import { KeeperWidget } from "./KeeperPanel";
import { InventoryWidget } from "./UniversalInventory";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== EXIT IMPERSONATION BANNER ==============
const ImpersonationBanner = ({ creatorName, onExit }) => {
  return (
    <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-3 mb-6 rounded-xl shadow-md" data-testid="impersonation-banner">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <p className="font-medium">Admin Impersonation Mode</p>
            <p className="text-sm text-white/80">
              You are viewing as {creatorName || "this creator"}
            </p>
          </div>
        </div>
        <button
          onClick={onExit}
          className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors font-medium"
          data-testid="exit-impersonation-btn"
        >
          <LogOut className="w-4 h-4" />
          Exit Impersonation
        </button>
      </div>
    </div>
  );
};

// ============== WELCOME HEADER ==============
const WelcomeHeader = ({ creator, systemState }) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const firstName = creator?.name?.split(" ")[0] || "Creator";

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900">
            {getGreeting()}, {firstName}
          </h1>
          <p className="text-slate-500 mt-1">
            Welcome back to your creative hub
          </p>
        </div>
        <div className="hidden md:flex items-center gap-4">
          {systemState && (
            <>
              <div className="text-center px-4 py-2 bg-emerald-50 rounded-lg">
                <p className="text-lg font-bold text-emerald-600">{systemState.engines_active || 0}</p>
                <p className="text-xs text-slate-500">Active Engines</p>
              </div>
              <div className="text-center px-4 py-2 bg-purple-50 rounded-lg">
                <p className="text-lg font-bold text-purple-600">{Math.round(systemState.overall_progress || 0)}%</p>
                <p className="text-xs text-slate-500">Progress</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// ============== QUICK ACCESS CARDS ==============
const QuickAccessSection = ({ onKeeperClick, onInventoryClick, systemState, inventoryData }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      {/* Keeper Card */}
      <Card className="border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer group" onClick={onKeeperClick}>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg">
              <Eye className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-slate-900 group-hover:text-amber-600 transition-colors">
                The Keeper
              </h3>
              <p className="text-sm text-slate-500">Your guide & system overseer</p>
              {systemState && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                    {systemState.engines_active || 0} engines active
                  </Badge>
                </div>
              )}
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-amber-500 group-hover:translate-x-1 transition-all" />
          </div>
        </CardContent>
      </Card>

      {/* Inventory Card */}
      <Card className="border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer group" onClick={onInventoryClick}>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl shadow-lg">
              <Layers className="w-8 h-8 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                Universal Inventory
              </h3>
              <p className="text-sm text-slate-500">Assets, offers & workflows</p>
              {inventoryData && (
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                    {Object.values(inventoryData).reduce((sum, items) => sum + (items?.length || 0), 0)} items
                  </Badge>
                </div>
              )}
            </div>
            <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ============== RECENT ACTIVITY SECTION ==============
const RecentActivitySection = ({ activities, onViewAll }) => {
  const [activeFilter, setActiveFilter] = useState("all");

  const activityIcons = {
    engine: <Zap className="w-4 h-4 text-amber-500" />,
    module: <Target className="w-4 h-4 text-blue-500" />,
    inventory: <Layers className="w-4 h-4 text-purple-500" />,
    workflow: <Activity className="w-4 h-4 text-emerald-500" />,
    arris: <Sparkles className="w-4 h-4 text-purple-500" />,
    system: <Activity className="w-4 h-4 text-slate-500" />
  };

  // Filter categories with their matching activity types
  const filterCategories = [
    { key: "all", label: "All", types: null },
    { key: "inventory", label: "Inventory", types: ["inventory"] },
    { key: "workflows", label: "Workflows", types: ["workflow"] },
    { key: "engines", label: "Engines", types: ["engine", "module"] },
    { key: "arris", label: "ARRIS", types: ["arris"] }
  ];

  // Show real activities or fallback
  const allActivities = activities?.length > 0 ? activities : [
    { type: "system", message: "Your system is ready for action", time: "Just now" }
  ];

  // Apply filter
  const filteredActivities = activeFilter === "all"
    ? allActivities
    : allActivities.filter(activity => {
        const category = filterCategories.find(f => f.key === activeFilter);
        return category?.types?.includes(activity.type);
      });

  return (
    <Card className="border-0 shadow-sm mb-8" data-testid="whats-new-section">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-500" />
            <CardTitle className="text-lg">What&apos;s New</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-xs">
              {filteredActivities.length} updates
            </Badge>
            <button
              onClick={onViewAll}
              className="text-xs text-slate-500 hover:text-slate-700 font-medium transition-colors flex items-center gap-1"
              data-testid="view-all-activity"
            >
              View All
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
        {/* Filter Buttons */}
        <div className="flex flex-wrap gap-2 mt-3">
          {filterCategories.map((filter) => (
            <button
              key={filter.key}
              onClick={() => setActiveFilter(filter.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                activeFilter === filter.key
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
              data-testid={`filter-${filter.key}`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {filteredActivities.length > 0 ? (
            filteredActivities.slice(0, 5).map((activity, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                data-testid={`activity-item-${idx}`}
              >
                <div className="p-2 bg-white rounded-lg shadow-sm">
                  {activityIcons[activity.type] || activityIcons.system}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{activity.message}</p>
                  <p className="text-xs text-slate-400">{activity.time}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-slate-400">
              <p className="text-sm">No {activeFilter} activity yet</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// ============== HELPER: Generate activities from data ==============
const generateActivitiesFromData = (homeData, inventoryData) => {
  const activities = [];
  const now = new Date();

  // Helper to format relative time
  const formatRelativeTime = (dateString) => {
    if (!dateString) return "Recently";
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Add inventory item activities
  if (inventoryData) {
    const allItems = [];
    Object.entries(inventoryData).forEach(([category, items]) => {
      if (Array.isArray(items)) {
        items.forEach(item => {
          allItems.push({ ...item, category });
        });
      }
    });

    // Sort by updated_at or created_at
    allItems.sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at || 0);
      const dateB = new Date(b.updated_at || b.created_at || 0);
      return dateB - dateA;
    });

    // Add recent inventory items
    allItems.slice(0, 3).forEach(item => {
      const isUpdated = item.updated_at && item.created_at && item.updated_at !== item.created_at;
      activities.push({
        type: "inventory",
        message: isUpdated 
          ? `Updated ${item.category.slice(0, -1)}: ${item.name}`
          : `Added ${item.category.slice(0, -1)}: ${item.name}`,
        time: formatRelativeTime(item.updated_at || item.created_at),
        timestamp: new Date(item.updated_at || item.created_at)
      });
    });

    // Check for workflow executions
    const workflows = inventoryData.workflows || [];
    workflows.forEach(workflow => {
      const executions = workflow.metadata?.executions || [];
      executions.slice(0, 2).forEach(exec => {
        activities.push({
          type: "workflow",
          message: `Workflow "${workflow.name}" ${exec.status}`,
          time: formatRelativeTime(exec.started_at),
          timestamp: new Date(exec.started_at)
        });
      });
    });
  }

  // Add engine activities from homeData
  if (homeData?.engine_status) {
    Object.entries(homeData.engine_status).forEach(([engineKey, engine]) => {
      if (engine.status === "active") {
        activities.push({
          type: "engine",
          message: `${engineKey.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())} is active`,
          time: formatRelativeTime(engine.last_activity),
          timestamp: new Date(engine.last_activity)
        });
      }
    });
  }

  // Add ARRIS outputs as activities
  if (homeData?.arris_outputs?.length > 0) {
    homeData.arris_outputs.slice(0, 2).forEach(output => {
      activities.push({
        type: "arris",
        message: `ARRIS ${output.output_type}: New guidance available`,
        time: formatRelativeTime(output.created_at),
        timestamp: new Date(output.created_at)
      });
    });
  }

  // Add module activities
  if (homeData?.active_modules?.length > 0) {
    activities.push({
      type: "module",
      message: `${homeData.active_modules.length} modules are active`,
      time: "Current",
      timestamp: now
    });
  }

  // Sort all activities by timestamp (most recent first)
  activities.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

  // Return top activities without timestamp field
  return activities.slice(0, 8).map(({ timestamp, ...rest }) => rest);
};

// ============== NAVIGATION GRID ==============
const NavigationGrid = ({ navigate }) => {
  const navItems = [
    {
      icon: BarChart3,
      label: "Dashboard",
      description: "View your analytics",
      path: "/creator/dashboard",
      color: "from-emerald-500 to-teal-500"
    },
    {
      icon: FileText,
      label: "Proposals",
      description: "Manage your proposals",
      path: "/creator/proposals",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: MessageSquare,
      label: "ARRIS Chat",
      description: "AI-powered guidance",
      path: "/creator/arris",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: Settings,
      label: "Settings",
      description: "Account preferences",
      path: "/creator/settings",
      color: "from-slate-500 to-slate-600"
    }
  ];

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          <CardTitle className="text-lg">Creator Tools</CardTitle>
        </div>
        <CardDescription>Quick access to all your tools</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {navItems.map((item, idx) => (
            <button
              key={idx}
              onClick={() => navigate(item.path)}
              className="p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-all group text-left"
              data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                <item.icon className="w-5 h-5 text-white" />
              </div>
              <p className="text-sm font-medium text-slate-900">{item.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// ============== MAIN CREATOR HOME ==============
export default function CreatorHome({ token, creator }) {
  const [homeData, setHomeData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isImpersonation, setIsImpersonation] = useState(false);
  const [impersonatedCreator, setImpersonatedCreator] = useState(null);
  const navigate = useNavigate();

  // Check for impersonation mode on mount
  useEffect(() => {
    const impersonationFlag = localStorage.getItem("is_impersonation");
    const creatorData = localStorage.getItem("creator_data");
    
    if (impersonationFlag === "true") {
      setIsImpersonation(true);
      if (creatorData) {
        try {
          setImpersonatedCreator(JSON.parse(creatorData));
        } catch (e) {
          console.error("Failed to parse creator data:", e);
        }
      }
    }
  }, []);

  const handleExitImpersonation = () => {
    // Restore admin token
    const adminToken = localStorage.getItem("admin_token_backup");
    
    // Clear impersonation data
    localStorage.removeItem("creator_token");
    localStorage.removeItem("creator_data");
    localStorage.removeItem("is_impersonation");
    localStorage.removeItem("admin_token_backup");
    
    // Redirect to admin dashboard with full page reload
    // If admin token was saved, they'll be logged in; otherwise they'll need to re-login
    window.location.href = "/admin";
  };

  const fetchHomeData = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // Fetch command center data and inventory data in parallel
      const [commandCenterRes, inventoryRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/command-center`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/inventory`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => null) // Don't fail if inventory fails
      ]);

      if (!commandCenterRes.ok) {
        // If intake required, redirect
        if (commandCenterRes.status === 403) {
          navigate("/intake");
          return;
        }
        throw new Error("Failed to load home data");
      }

      const data = await commandCenterRes.json();
      
      // Check if intake is required
      if (data.intake_required) {
        navigate("/intake");
        return;
      }

      setHomeData(data);

      // Parse inventory data if available
      if (inventoryRes?.ok) {
        const invData = await inventoryRes.json();
        setInventoryData(invData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, navigate]);

  useEffect(() => {
    fetchHomeData();
  }, [fetchHomeData]);

  const handleKeeperClick = () => {
    navigate("/command-center?tab=keeper");
  };

  const handleInventoryClick = () => {
    navigate("/inventory");
  };

  const handleViewAllActivity = () => {
    navigate("/activity-history");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-slate-400" />
          <p className="text-slate-500 mt-3">Loading your home...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-6 text-center">
            <AlertCircle className="w-8 h-8 mx-auto text-red-400 mb-3" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchHomeData}>Try Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const systemState = homeData?.system_state || homeData || {};
  
  // Generate real activities from homeData and inventoryData
  const activities = generateActivitiesFromData(homeData, inventoryData);

  // Use impersonated creator name or fall back to passed creator
  const displayCreator = isImpersonation && impersonatedCreator ? impersonatedCreator : creator;

  return (
    <div className="min-h-screen bg-slate-50" data-testid="creator-home">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Impersonation Banner - Only shown when admin is exploring as user */}
        {isImpersonation && (
          <ImpersonationBanner 
            creatorName={impersonatedCreator?.name}
            onExit={handleExitImpersonation}
          />
        )}

        {/* Welcome Header */}
        <WelcomeHeader creator={displayCreator} systemState={systemState} />

        {/* Quick Access Cards */}
        <QuickAccessSection
          onKeeperClick={handleKeeperClick}
          onInventoryClick={handleInventoryClick}
          systemState={systemState}
          inventoryData={inventoryData}
        />

        {/* Two Column Layout for Activity and Navigation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <RecentActivitySection activities={activities} />

          {/* Navigation Grid */}
          <NavigationGrid navigate={navigate} />
        </div>
      </div>
    </div>
  );
}

// Export a minimal home widget for other uses
export function CreatorHomeWidget({ creator, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all group w-full"
      data-testid="home-widget"
    >
      <div className="p-2 bg-gradient-to-br from-amber-100 to-orange-100 rounded-lg">
        <Home className="w-5 h-5 text-amber-600" />
      </div>
      <div className="text-left flex-1">
        <p className="text-sm font-medium text-slate-900">Home</p>
        <p className="text-xs text-slate-500">
          Welcome, {creator?.name?.split(" ")[0] || "Creator"}
        </p>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
    </button>
  );
}
