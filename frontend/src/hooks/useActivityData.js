/**
 * useActivityData Hook
 * ====================
 * Shared hook for fetching activity data across creator pages.
 */

import { useState, useEffect, useCallback } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Helper: Format relative time
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

// Helper: Generate activities from data
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

    // Add recent inventory items
    allItems.slice(0, 5).forEach(item => {
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
      timestamp: new Date()
    });
  }

  // Sort all activities by timestamp (most recent first)
  activities.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

  // Return top activities without timestamp field
  return activities.slice(0, 10).map(({ timestamp, ...rest }) => rest);
};

export default function useActivityData(token) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchActivities = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }

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

      let homeData = null;
      let inventoryData = null;

      if (commandCenterRes.ok) {
        homeData = await commandCenterRes.json();
      }

      if (inventoryRes?.ok) {
        inventoryData = await inventoryRes.json();
      }

      // Generate activities from data
      const generatedActivities = generateActivitiesFromData(homeData, inventoryData);
      setActivities(generatedActivities);
    } catch (err) {
      console.error("Failed to fetch activities:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  return { activities, loading, refetch: fetchActivities };
}
