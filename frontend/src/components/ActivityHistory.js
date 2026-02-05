/**
 * Activity History Page
 * =====================
 * Full activity history view for creators.
 * Accessible via "View All" from the Home Screen.
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft, Clock, Zap, Target, Layers, Activity,
  Sparkles, RefreshCw, AlertCircle
} from "lucide-react";
import ActivityNotificationBell from "./ActivityNotificationBell";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== ACTIVITY ICONS ==============
const activityIcons = {
  engine: <Zap className="w-4 h-4 text-amber-500" />,
  module: <Target className="w-4 h-4 text-blue-500" />,
  inventory: <Layers className="w-4 h-4 text-purple-500" />,
  workflow: <Activity className="w-4 h-4 text-emerald-500" />,
  arris: <Sparkles className="w-4 h-4 text-purple-500" />,
  system: <Activity className="w-4 h-4 text-slate-500" />
};

// ============== FILTER CATEGORIES ==============
const filterCategories = [
  { key: "all", label: "All", types: null },
  { key: "inventory", label: "Inventory", types: ["inventory"] },
  { key: "workflows", label: "Workflows", types: ["workflow"] },
  { key: "engines", label: "Engines", types: ["engine", "module"] },
  { key: "arris", label: "ARRIS", types: ["arris"] }
];

// ============== HELPER: Format relative time ==============
const formatRelativeTime = (dateString) => {
  if (!dateString) return "Recently";
  const now = new Date();
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

// ============== HELPER: Generate activities from data ==============
const generateActivitiesFromData = (homeData, inventoryData) => {
  const activities = [];

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

    // Add ALL inventory items (no limit for history page)
    allItems.forEach(item => {
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
      executions.forEach(exec => {
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
    homeData.arris_outputs.forEach(output => {
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
      timestamp: new Date()
    });
  }

  // Sort all activities by timestamp (most recent first)
  activities.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

  // Return activities without timestamp field
  return activities.map(({ timestamp, ...rest }) => rest);
};

// ============== MAIN ACTIVITY HISTORY ==============
export default function ActivityHistory({ token }) {
  const [activities, setActivities] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchActivityData = useCallback(async () => {
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
        }).catch(() => null)
      ]);

      if (!commandCenterRes.ok) {
        if (commandCenterRes.status === 403) {
          navigate("/intake");
          return;
        }
        throw new Error("Failed to load activity data");
      }

      const homeData = await commandCenterRes.json();
      
      if (homeData.intake_required) {
        navigate("/intake");
        return;
      }

      let inventoryData = null;
      if (inventoryRes?.ok) {
        inventoryData = await inventoryRes.json();
      }

      // Generate activities from data
      const generatedActivities = generateActivitiesFromData(homeData, inventoryData);
      setActivities(generatedActivities);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, navigate]);

  useEffect(() => {
    fetchActivityData();
  }, [fetchActivityData]);

  // Apply filter
  const filteredActivities = activeFilter === "all"
    ? activities
    : activities.filter(activity => {
        const category = filterCategories.find(f => f.key === activeFilter);
        return category?.types?.includes(activity.type);
      });

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-slate-400" />
          <p className="text-slate-500 mt-3">Loading activity history...</p>
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
            <Button onClick={fetchActivityData}>Try Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="activity-history-page">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate("/home")}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-700 transition-colors mb-4"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Home</span>
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-900 rounded-lg">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Activity History</h1>
                <p className="text-sm text-slate-500">Your recent actions and system events</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ActivityNotificationBell activities={activities} />
              <Badge variant="outline" className="text-sm">
                {filteredActivities.length} total
              </Badge>
            </div>
          </div>
        </div>

        {/* Filters */}
        <Card className="border-0 shadow-sm mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              {filterCategories.map((filter) => (
                <button
                  key={filter.key}
                  onClick={() => setActiveFilter(filter.key)}
                  className={`px-4 py-2 text-sm font-medium rounded-full transition-all ${
                    activeFilter === filter.key
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                  data-testid={`history-filter-${filter.key}`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Activity List */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="w-5 h-5 text-slate-500" />
              {activeFilter === "all" ? "All Activity" : `${filterCategories.find(f => f.key === activeFilter)?.label} Activity`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredActivities.length > 0 ? (
                filteredActivities.map((activity, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    data-testid={`history-item-${idx}`}
                  >
                    <div className="p-2 bg-white rounded-lg shadow-sm">
                      {activityIcons[activity.type] || activityIcons.system}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700">{activity.message}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{activity.time}</p>
                    </div>
                    <Badge variant="outline" className="text-xs capitalize hidden sm:block">
                      {activity.type}
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No {activeFilter === "all" ? "" : activeFilter} activity yet</p>
                  <p className="text-xs mt-1">Your activity will appear here as you use the system</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
