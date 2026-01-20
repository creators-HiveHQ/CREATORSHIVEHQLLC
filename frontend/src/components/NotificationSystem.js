/**
 * WebSocket Notification System for Creators Hive HQ
 * Real-time notifications with toast display
 */

import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Convert HTTP URL to WebSocket URL
const getWebSocketUrl = () => {
  const url = new URL(BACKEND_URL);
  const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${wsProtocol}//${url.host}`;
};

// Notification Context
const NotificationContext = createContext(null);

// Notification types and their display settings
const NOTIFICATION_CONFIG = {
  // Proposal notifications
  proposal_submitted: {
    icon: "📋",
    title: "Proposal Submitted",
    type: "success",
  },
  proposal_approved: {
    icon: "🎉",
    title: "Proposal Approved!",
    type: "success",
  },
  proposal_rejected: {
    icon: "📝",
    title: "Proposal Update",
    type: "info",
  },
  proposal_under_review: {
    icon: "👀",
    title: "Under Review",
    type: "info",
  },
  
  // ARRIS notifications
  arris_insights_ready: {
    icon: "🧠",
    title: "ARRIS Insights Ready",
    type: "success",
  },
  arris_memory_updated: {
    icon: "💾",
    title: "ARRIS Memory Updated",
    type: "info",
  },
  arris_pattern_detected: {
    icon: "🔮",
    title: "Pattern Detected",
    type: "info",
  },
  
  // Subscription notifications
  subscription_created: {
    icon: "✨",
    title: "Subscription Active",
    type: "success",
  },
  subscription_upgraded: {
    icon: "🚀",
    title: "Subscription Upgraded",
    type: "success",
  },
  subscription_cancelled: {
    icon: "👋",
    title: "Subscription Update",
    type: "info",
  },
  
  // Elite notifications
  elite_inquiry_received: {
    icon: "🌟",
    title: "New Elite Inquiry",
    type: "info",
  },
  elite_inquiry_updated: {
    icon: "📞",
    title: "Elite Inquiry Updated",
    type: "info",
  },
  
  // System notifications
  system_alert: {
    icon: "⚠️",
    title: "System Alert",
    type: "warning",
  },
  welcome: {
    icon: "👋",
    title: "Connected",
    type: "success",
  },
  
  // Revenue notifications
  revenue_milestone: {
    icon: "💰",
    title: "Revenue Milestone",
    type: "success",
  },
};

// Custom hook for WebSocket connection
export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within NotificationProvider");
  }
  return context;
};

// Notification Provider Component
export const NotificationProvider = ({ children, userType, userId, userName }) => {
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const pingIntervalRef = useRef(null);

  // Handle incoming notification
  const handleNotification = useCallback((notification) => {
    const { type, data, timestamp } = notification;
    const config = NOTIFICATION_CONFIG[type] || {
      icon: "📢",
      title: "Notification",
      type: "info",
    };

    const newNotification = {
      id: `${type}-${timestamp}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      ...config,
      message: data.message || "",
      data,
      timestamp,
      read: false,
    };

    // Add to notifications list
    setNotifications((prev) => [newNotification, ...prev].slice(0, 50));
    setUnreadCount((prev) => prev + 1);

    // Show toast notification
    const toastMessage = `${config.icon} ${data.message || config.title}`;
    
    switch (config.type) {
      case "success":
        toast.success(toastMessage, {
          description: type === "proposal_approved" ? `Project ID: ${data.project_id}` : undefined,
          duration: 5000,
        });
        break;
      case "warning":
        toast.warning(toastMessage, { duration: 7000 });
        break;
      case "error":
        toast.error(toastMessage, { duration: 10000 });
        break;
      default:
        toast.info(toastMessage, { duration: 4000 });
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!userId || !userType) {
      console.log("Missing userId or userType for WebSocket connection");
      return;
    }

    const wsUrl = `${getWebSocketUrl()}/ws/notifications/${userType}/${userId}`;
    console.log("Connecting to WebSocket:", wsUrl);

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
        setConnected(true);
        reconnectAttempts.current = 0;
        
        // Start ping interval for keep-alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send("ping");
          }
        }, 30000);
      };

      wsRef.current.onmessage = (event) => {
        try {
          // Handle pong response
          if (event.data === "pong") {
            return;
          }

          const notification = JSON.parse(event.data);
          handleNotification(notification);
        } catch (error) {
          console.error("Failed to parse notification:", error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        setConnected(false);
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        
        // Attempt reconnect (non-recursive, uses setTimeout)
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Reconnecting in ${delay}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            // Reconnect by re-calling connect (safe since this is in a timeout)
            if (wsRef.current?.readyState !== WebSocket.OPEN) {
              wsRef.current = new WebSocket(wsUrl);
            }
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
    }
  }, [userId, userType, handleNotification]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((notificationId) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === notificationId ? { ...n, read: true } : n
      )
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // Send acknowledgment
  const sendAck = useCallback((notificationId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(`ack:${notificationId}`);
    }
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (userId && userType) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [userId, userType, connect, disconnect]);

  const value = {
    connected,
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotifications,
    sendAck,
    connect,
    disconnect,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

// Notification Bell Component
export const NotificationBell = ({ onClick }) => {
  const { unreadCount, connected } = useNotifications();

  return (
    <button
      onClick={onClick}
      className="relative p-2 rounded-full hover:bg-slate-100 transition-colors"
      data-testid="notification-bell"
    >
      <span className="text-xl">🔔</span>
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center" data-testid="notification-badge">
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
      <span
        className={`absolute bottom-0 right-0 h-2 w-2 rounded-full ${
          connected ? "bg-green-500" : "bg-red-500"
        }`}
        title={connected ? "Connected" : "Disconnected"}
      />
    </button>
  );
};

// Notification Panel Component
export const NotificationPanel = ({ isOpen, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearNotifications } = useNotifications();

  if (!isOpen) return null;

  return (
    <div
      className="absolute right-0 top-full mt-2 w-96 max-h-[500px] bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-50"
      data-testid="notification-panel"
    >
      {/* Header */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-slate-900">Notifications</h3>
          {unreadCount > 0 && (
            <span className="text-xs text-slate-500">{unreadCount} unread</span>
          )}
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-xs text-indigo-600 hover:text-indigo-800"
              data-testid="mark-all-read"
            >
              Mark all read
            </button>
          )}
          {notifications.length > 0 && (
            <button
              onClick={clearNotifications}
              className="text-xs text-slate-500 hover:text-slate-700"
              data-testid="clear-notifications"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Notification List */}
      <div className="overflow-y-auto max-h-[400px]">
        {notifications.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <span className="text-4xl block mb-2">🔔</span>
            <p>No notifications yet</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`px-4 py-3 hover:bg-slate-50 cursor-pointer transition-colors ${
                  !notification.read ? "bg-indigo-50/50" : ""
                }`}
                onClick={() => markAsRead(notification.id)}
                data-testid={`notification-item-${notification.type}`}
              >
                <div className="flex gap-3">
                  <span className="text-xl">{notification.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 text-sm">
                      {notification.title}
                    </p>
                    <p className="text-sm text-slate-600 truncate">
                      {notification.message}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      {new Date(notification.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  {!notification.read && (
                    <span className="h-2 w-2 bg-indigo-500 rounded-full mt-2" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Connection Status Indicator
export const ConnectionStatus = () => {
  const { connected } = useNotifications();

  return (
    <div className={`flex items-center gap-2 text-xs ${connected ? "text-green-600" : "text-red-600"}`}>
      <span className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
      {connected ? "Live" : "Offline"}
    </div>
  );
};

export default NotificationProvider;
