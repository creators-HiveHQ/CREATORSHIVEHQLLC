/**
 * ARRIS Activity Feed Component for Creators Hive HQ
 * Real-time activity tracking and queue position updates for Premium users
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useNotifications } from "@/components/NotificationSystem";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Activity type icons
const ACTIVITY_ICONS = {
  request_queued: "📋",
  processing_started: "🔄",
  processing_completed: "✅",
  processing_failed: "❌",
};

// Priority badges
const PriorityBadge = ({ priority }) => {
  if (priority === "fast") {
    return (
      <Badge className="bg-amber-500 text-white text-xs">
        ⚡ Fast
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-xs">
      Standard
    </Badge>
  );
};

// Queue position indicator
const QueuePositionIndicator = ({ position, estimatedWait, status }) => {
  if (status === "processing") {
    return (
      <div className="flex items-center gap-2">
        <div className="animate-spin h-4 w-4 border-2 border-purple-500 border-t-transparent rounded-full" />
        <span className="text-sm text-purple-600 font-medium">Processing now...</span>
      </div>
    );
  }
  
  if (position === 0 || position === undefined) return null;
  
  return (
    <div className="flex items-center gap-3">
      <div className="text-center">
        <div className="text-2xl font-bold text-purple-600">#{position}</div>
        <div className="text-xs text-slate-500">in queue</div>
      </div>
      {estimatedWait > 0 && (
        <div className="text-center">
          <div className="text-lg font-semibold text-slate-700">~{estimatedWait}s</div>
          <div className="text-xs text-slate-500">est. wait</div>
        </div>
      )}
    </div>
  );
};

// Single activity item
const ActivityItem = ({ activity, isOwn }) => {
  const icon = ACTIVITY_ICONS[activity.activity_type] || "📋";
  const isRecent = new Date() - new Date(activity.created_at) < 60000; // Less than 1 min
  
  return (
    <div 
      className={`p-3 rounded-lg border transition-all ${
        isOwn ? "bg-purple-50 border-purple-200" : "bg-white border-slate-200"
      } ${isRecent ? "animate-pulse-once" : ""}`}
      data-testid={`activity-item-${activity.id}`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-slate-800 truncate">
              {activity.proposal_title || "Analysis Request"}
            </span>
            <PriorityBadge priority={activity.priority} />
            {isOwn && (
              <Badge className="bg-purple-600 text-white text-xs">You</Badge>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
            <span>{activity.creator_name}</span>
            <span>•</span>
            <span>
              {activity.status === "processing" ? "Processing..." :
               activity.status === "completed" ? `Completed in ${activity.processing_time?.toFixed(1)}s` :
               activity.status === "queued" ? "Queued" :
               activity.status}
            </span>
            <span>•</span>
            <span>{new Date(activity.created_at).toLocaleTimeString()}</span>
          </div>
        </div>
        {activity.status === "processing" && (
          <div className="animate-spin h-4 w-4 border-2 border-purple-500 border-t-transparent rounded-full" />
        )}
      </div>
    </div>
  );
};

// Queue stats display
const QueueStats = ({ stats }) => {
  if (!stats) return null;
  
  const totalQueued = stats.fast_queue_length + stats.standard_queue_length;
  
  return (
    <div className="grid grid-cols-4 gap-3">
      <div className="bg-purple-50 p-3 rounded-lg text-center">
        <div className="text-2xl font-bold text-purple-600">{stats.currently_processing}</div>
        <div className="text-xs text-purple-600">Processing</div>
      </div>
      <div className="bg-amber-50 p-3 rounded-lg text-center">
        <div className="text-2xl font-bold text-amber-600">{stats.fast_queue_length}</div>
        <div className="text-xs text-amber-600">Fast Queue</div>
      </div>
      <div className="bg-slate-50 p-3 rounded-lg text-center">
        <div className="text-2xl font-bold text-slate-600">{stats.standard_queue_length}</div>
        <div className="text-xs text-slate-600">Standard</div>
      </div>
      <div className="bg-green-50 p-3 rounded-lg text-center">
        <div className="text-2xl font-bold text-green-600">{stats.total_processed}</div>
        <div className="text-xs text-green-600">Completed</div>
      </div>
    </div>
  );
};

// My queue items panel
const MyQueueItems = ({ items, onRefresh }) => {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-6 text-slate-500">
        <span className="text-3xl block mb-2">🚀</span>
        <p className="text-sm">No items in queue</p>
        <p className="text-xs mt-1">Submit a proposal to see your queue position</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div 
          key={item.request_id} 
          className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200"
          data-testid={`my-queue-item-${item.proposal_id}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-purple-900 truncate">{item.proposal_title}</p>
              <div className="flex items-center gap-2 mt-1">
                <PriorityBadge priority={item.priority} />
                <Badge variant="outline" className="text-xs">
                  {item.tier}
                </Badge>
              </div>
            </div>
            <QueuePositionIndicator 
              position={item.queue_position} 
              estimatedWait={item.queue_position * 5} 
              status={item.status}
            />
          </div>
          <div className="mt-3">
            <Progress 
              value={item.status === "processing" ? 50 : item.status === "completed" ? 100 : 0} 
              className="h-2"
            />
            <p className="text-xs text-purple-600 mt-1">
              {item.status === "processing" ? "ARRIS is analyzing your proposal..." :
               item.status === "queued" ? `Position ${item.queue_position} in ${item.priority} queue` :
               "Completed"}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Main ARRIS Activity Feed Component
export const ArrisActivityFeed = ({ creatorId, hasPremiumAccess = false }) => {
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { notifications } = useNotifications();

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return { Authorization: `Bearer ${token}` };
  };

  // Fetch activity feed data
  const fetchActivityFeed = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/arris/activity-feed?limit=20`, { headers });
      setActivityData(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching activity feed:", err);
      setError(err.response?.data?.detail?.message || "Failed to load activity feed");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchActivityFeed();
  }, [fetchActivityFeed]);

  // Auto-refresh every 10 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchActivityFeed();
    }, 10000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, fetchActivityFeed]);

  // Refresh on relevant notifications
  useEffect(() => {
    const relevantTypes = [
      "arris_queue_update", 
      "arris_processing_started", 
      "arris_processing_complete",
      "arris_activity_update"
    ];
    
    const hasRelevantNotification = notifications.some(
      n => relevantTypes.includes(n.type) && !n.read
    );
    
    if (hasRelevantNotification) {
      fetchActivityFeed();
    }
  }, [notifications, fetchActivityFeed]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
      </div>
    );
  }

  // Show upgrade prompt for non-Premium users
  if (!hasPremiumAccess) {
    return (
      <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
        <CardContent className="py-8 text-center">
          <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-3xl">🚀</span>
          </div>
          <h3 className="text-xl font-bold text-amber-800 mb-2">Real-Time Activity Feed</h3>
          <p className="text-amber-600 max-w-md mx-auto mb-4">
            Premium users get real-time queue position updates, processing notifications, 
            and live activity tracking for their ARRIS requests.
          </p>
          <div className="grid grid-cols-3 gap-3 max-w-sm mx-auto mb-6">
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <span className="text-2xl">⏳</span>
              <p className="text-xs text-slate-600 mt-1">Queue Position</p>
            </div>
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <span className="text-2xl">🔔</span>
              <p className="text-xs text-slate-600 mt-1">Live Updates</p>
            </div>
            <div className="bg-white p-3 rounded-lg shadow-sm">
              <span className="text-2xl">📊</span>
              <p className="text-xs text-slate-600 mt-1">Activity Feed</p>
            </div>
          </div>
          <Button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600">
            ⚡ Upgrade to Premium
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="arris-activity-feed">
      {/* Header with refresh controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <span>🧠</span> ARRIS Activity Feed
            <Badge className="bg-green-500 text-white text-xs ml-2">LIVE</Badge>
          </h2>
          <p className="text-sm text-slate-500">Real-time queue positions and processing status</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-300"
            />
            Auto-refresh
          </label>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchActivityFeed}
            data-testid="refresh-activity-btn"
          >
            🔄 Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Queue Stats */}
      {activityData?.live_status?.queue_stats && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>📊</span> Queue Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <QueueStats stats={activityData.live_status.queue_stats} />
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                <span className="text-slate-600">Avg Fast Time</span>
                <span className="font-medium">{activityData.live_status.queue_stats.avg_fast_time?.toFixed(1) || 0}s</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-slate-50 rounded">
                <span className="text-slate-600">Avg Standard Time</span>
                <span className="font-medium">{activityData.live_status.queue_stats.avg_standard_time?.toFixed(1) || 0}s</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* My Queue Items */}
      {activityData?.my_queue_items && (
        <Card className="border-purple-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🎯</span> Your Queue Position
            </CardTitle>
            <CardDescription>Track your ARRIS processing requests in real-time</CardDescription>
          </CardHeader>
          <CardContent>
            <MyQueueItems 
              items={activityData.my_queue_items} 
              onRefresh={fetchActivityFeed}
            />
          </CardContent>
        </Card>
      )}

      {/* Live Activity Feed */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <span>📋</span> Recent Activity
          </CardTitle>
          <CardDescription>Live updates from ARRIS processing queue</CardDescription>
        </CardHeader>
        <CardContent>
          {activityData?.live_status?.recent_activity?.length > 0 ? (
            <div className="space-y-2">
              {activityData.live_status.recent_activity.map((activity, idx) => (
                <ActivityItem 
                  key={activity.id || idx} 
                  activity={activity}
                  isOwn={activity.creator_id === creatorId}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <span className="text-3xl block mb-2">🧠</span>
              <p>No recent activity</p>
              <p className="text-xs mt-1">Activity will appear here as proposals are processed</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Currently Processing */}
      {activityData?.live_status?.currently_processing?.length > 0 && (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2 text-green-800">
              <span>🔄</span> Currently Processing
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activityData.live_status.currently_processing.map((item, idx) => (
                <div 
                  key={item.request_id || idx}
                  className="p-3 bg-white rounded-lg border border-green-200 flex items-center gap-3"
                >
                  <div className="animate-spin h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full" />
                  <div className="flex-1">
                    <p className="font-medium text-green-800">{item.proposal_title}</p>
                    <p className="text-xs text-green-600">Processing by ARRIS...</p>
                  </div>
                  <PriorityBadge priority={item.priority} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timestamp */}
      <div className="text-center text-xs text-slate-400">
        Last updated: {activityData?.live_status?.timestamp ? 
          new Date(activityData.live_status.timestamp).toLocaleString() : 
          "N/A"}
      </div>
    </div>
  );
};

export default ArrisActivityFeed;
