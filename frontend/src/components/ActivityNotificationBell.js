/**
 * Activity Notification Bell
 * ==========================
 * Shows recent activity notifications in a dropdown.
 * Client-side unread tracking using localStorage.
 */

import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import {
  Bell, Zap, Target, Layers, Activity,
  Sparkles, Clock, ChevronRight, Check
} from "lucide-react";

// Activity icons (same as Home Screen)
const activityIcons = {
  engine: <Zap className="w-4 h-4 text-amber-500" />,
  module: <Target className="w-4 h-4 text-blue-500" />,
  inventory: <Layers className="w-4 h-4 text-purple-500" />,
  workflow: <Activity className="w-4 h-4 text-emerald-500" />,
  arris: <Sparkles className="w-4 h-4 text-purple-500" />,
  system: <Activity className="w-4 h-4 text-slate-500" />
};

// LocalStorage key for tracking last seen activity
const LAST_SEEN_KEY = "activity_last_seen_timestamp";

export default function ActivityNotificationBell({ activities = [] }) {
  const [isOpen, setIsOpen] = useState(false);
  const [lastSeenTime, setLastSeenTime] = useState(() => {
    const lastSeenStr = localStorage.getItem(LAST_SEEN_KEY);
    return lastSeenStr ? new Date(lastSeenStr) : new Date(0);
  });
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Calculate unread count based on last seen timestamp using useMemo
  const unreadCount = useMemo(() => {
    // Count activities that appear recent (within today)
    return activities.filter(activity => {
      if (activity.time === "Just now" || activity.time === "Current") return true;
      if (activity.time?.includes("m ago") || activity.time?.includes("h ago")) return true;
      return false;
    }).length;
  }, [activities]);

  // Track if user has seen notifications this session
  const [hasSeenThisSession, setHasSeenThisSession] = useState(false);
  
  // Display count (0 if user has opened dropdown this session)
  const displayUnreadCount = hasSeenThisSession ? 0 : unreadCount;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Mark all as read when dropdown opens
  const handleToggle = () => {
    if (!isOpen) {
      // Mark as read when opening
      localStorage.setItem(LAST_SEEN_KEY, new Date().toISOString());
      setHasSeenThisSession(true);
    }
    setIsOpen(!isOpen);
  };

  const handleViewAll = () => {
    setIsOpen(false);
    navigate("/activity-history");
  };

  const recentActivities = activities.slice(0, 5);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-full hover:bg-slate-100 transition-colors"
        data-testid="activity-notification-bell"
        aria-label="Activity notifications"
      >
        <Bell className="w-5 h-5 text-slate-600" />
        {displayUnreadCount > 0 && (
          <span 
            className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs font-bold rounded-full h-4 w-4 flex items-center justify-center"
            data-testid="activity-unread-badge"
          >
            {displayUnreadCount > 9 ? "9+" : displayUnreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div 
          className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-50"
          data-testid="activity-dropdown"
        >
          {/* Header */}
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-500" />
              <h3 className="font-semibold text-slate-900 text-sm">Recent Activity</h3>
            </div>
            {unreadCount === 0 && activities.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-emerald-600">
                <Check className="w-3 h-3" />
                <span>All caught up</span>
              </div>
            )}
          </div>

          {/* Activity List */}
          <div className="max-h-80 overflow-y-auto">
            {recentActivities.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {recentActivities.map((activity, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
                    data-testid={`notification-item-${idx}`}
                  >
                    <div className="p-1.5 bg-slate-100 rounded-lg">
                      {activityIcons[activity.type] || activityIcons.system}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 truncate">{activity.message}</p>
                      <p className="text-xs text-slate-400">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-slate-400">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No recent activity</p>
              </div>
            )}
          </div>

          {/* Footer */}
          {activities.length > 0 && (
            <div className="px-4 py-3 bg-slate-50 border-t border-slate-200">
              <button
                onClick={handleViewAll}
                className="w-full flex items-center justify-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                data-testid="notification-view-all"
              >
                View All Activity
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
