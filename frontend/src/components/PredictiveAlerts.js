/**
 * Predictive Alerts Component (Module A4)
 * Displays real-time predictive alerts and notifications for Pro+ creators.
 * Shows timing opportunities, performance insights, and risk warnings.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Priority styles
const PRIORITY_STYLES = {
  urgent: { bg: "bg-red-50", border: "border-red-300", text: "text-red-700", badge: "bg-red-500 text-white" },
  high: { bg: "bg-amber-50", border: "border-amber-300", text: "text-amber-700", badge: "bg-amber-500 text-white" },
  medium: { bg: "bg-blue-50", border: "border-blue-300", text: "text-blue-700", badge: "bg-blue-500 text-white" },
  low: { bg: "bg-slate-50", border: "border-slate-300", text: "text-slate-600", badge: "bg-slate-400 text-white" },
};

// Category styles
const CATEGORY_STYLES = {
  timing: { icon: "⏰", label: "Timing" },
  performance: { icon: "📊", label: "Performance" },
  risk: { icon: "⚠️", label: "Risk" },
  platform: { icon: "📱", label: "Platform" },
  arris: { icon: "🧠", label: "ARRIS" },
};

/**
 * Single Alert Card Component
 */
const AlertCard = ({ alert, onRead, onDismiss, onAction }) => {
  const priorityStyle = PRIORITY_STYLES[alert.priority] || PRIORITY_STYLES.medium;
  const categoryStyle = CATEGORY_STYLES[alert.category] || { icon: "🔔", label: "Alert" };

  return (
    <Card
      className={`${priorityStyle.bg} ${priorityStyle.border} border transition-all hover:shadow-md ${
        !alert.read ? "ring-2 ring-offset-2 ring-blue-400" : ""
      }`}
      data-testid={`alert-${alert.alert_id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="text-2xl shrink-0">{alert.icon}</div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className={`font-semibold ${priorityStyle.text}`}>{alert.title}</h4>
              <Badge className={priorityStyle.badge} variant="secondary">
                {alert.priority}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {categoryStyle.icon} {categoryStyle.label}
              </Badge>
              {!alert.read && (
                <Badge className="bg-blue-500 text-white text-xs">NEW</Badge>
              )}
            </div>
            
            <p className="text-sm text-slate-600 mt-1">{alert.message}</p>
            
            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              {alert.actionable && alert.cta_text && (
                <Button
                  size="sm"
                  className="bg-purple-600 hover:bg-purple-700"
                  onClick={() => onAction(alert)}
                  data-testid={`alert-action-${alert.alert_id}`}
                >
                  {alert.cta_text}
                </Button>
              )}
              {!alert.read && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRead(alert.alert_id)}
                  data-testid={`alert-read-${alert.alert_id}`}
                >
                  Mark Read
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDismiss(alert.alert_id)}
                data-testid={`alert-dismiss-${alert.alert_id}`}
              >
                Dismiss
              </Button>
            </div>
          </div>
          
          {/* Timestamp */}
          <div className="text-xs text-slate-400 shrink-0">
            {new Date(alert.created_at).toLocaleDateString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Alert Preferences Modal
 */
const PreferencesModal = ({ isOpen, onClose, preferences, onSave }) => {
  const [localPrefs, setLocalPrefs] = useState(preferences);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLocalPrefs(preferences);
  }, [preferences]);

  const handleSave = async () => {
    setSaving(true);
    await onSave(localPrefs);
    setSaving(false);
    onClose();
  };

  const toggleCategory = (category) => {
    setLocalPrefs({
      ...localPrefs,
      categories: {
        ...localPrefs.categories,
        [category]: !localPrefs.categories?.[category]
      }
    });
  };

  const togglePriority = (priority) => {
    setLocalPrefs({
      ...localPrefs,
      priorities: {
        ...localPrefs.priorities,
        [priority]: !localPrefs.priorities?.[priority]
      }
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Alert Preferences</DialogTitle>
          <DialogDescription>
            Customize which alerts you receive
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Master toggle */}
          <div className="flex items-center justify-between">
            <Label>Enable Alerts</Label>
            <Switch
              checked={localPrefs.enabled}
              onCheckedChange={(checked) => setLocalPrefs({ ...localPrefs, enabled: checked })}
            />
          </div>

          {/* Categories */}
          <div>
            <Label className="text-sm font-medium">Alert Categories</Label>
            <div className="grid grid-cols-2 gap-3 mt-2">
              {Object.entries(CATEGORY_STYLES).map(([key, style]) => (
                <div key={key} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                  <span className="text-sm">{style.icon} {style.label}</span>
                  <Switch
                    checked={localPrefs.categories?.[key] !== false}
                    onCheckedChange={() => toggleCategory(key)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Priorities */}
          <div>
            <Label className="text-sm font-medium">Priority Levels</Label>
            <div className="grid grid-cols-2 gap-3 mt-2">
              {Object.entries(PRIORITY_STYLES).map(([key, style]) => (
                <div key={key} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                  <Badge className={style.badge}>{key}</Badge>
                  <Switch
                    checked={localPrefs.priorities?.[key] !== false}
                    onCheckedChange={() => togglePriority(key)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Quiet hours */}
          <div className="flex items-center justify-between">
            <div>
              <Label>Quiet Hours</Label>
              <p className="text-xs text-slate-500">No alerts 10PM - 8AM</p>
            </div>
            <Switch
              checked={localPrefs.quiet_hours?.enabled}
              onCheckedChange={(checked) => setLocalPrefs({
                ...localPrefs,
                quiet_hours: { ...localPrefs.quiet_hours, enabled: checked }
              })}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Preferences"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Main Predictive Alerts Component
 */
export const PredictiveAlerts = ({ token, onUpgrade }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [tier, setTier] = useState(null);
  const [preferences, setPreferences] = useState({});
  const [showPreferences, setShowPreferences] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [priorityCounts, setPriorityCounts] = useState({});
  const [unreadCount, setUnreadCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = getAuthHeaders();

      const [alertsRes, prefsRes] = await Promise.all([
        axios.get(`${API}/creators/me/predictive-alerts`, { headers }),
        axios.get(`${API}/creators/me/alert-preferences`, { headers }).catch(() => ({ data: {} }))
      ]);

      if (alertsRes.data.access_denied) {
        setAccessDenied(true);
        setTier(alertsRes.data.tier);
        return;
      }

      setAlerts(alertsRes.data.alerts || []);
      setPriorityCounts(alertsRes.data.priority_counts || {});
      setUnreadCount(alertsRes.data.unread || 0);
      setTier(alertsRes.data.tier);
      setPreferences(prefsRes.data || {});
      setAccessDenied(false);
    } catch (err) {
      console.error("Error fetching alerts:", err);
      if (err.response?.status === 403) {
        setAccessDenied(true);
      } else {
        setError("Failed to load alerts");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (token) {
      fetchAlerts();
    }
  }, [token, fetchAlerts]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const headers = getAuthHeaders();
      await axios.post(`${API}/creators/me/trigger-alerts`, {}, { headers });
      await fetchAlerts();
    } catch (err) {
      console.error("Error refreshing alerts:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleMarkRead = async (alertId) => {
    try {
      const headers = getAuthHeaders();
      await axios.post(`${API}/creators/me/alerts/${alertId}/read`, {}, { headers });
      setAlerts(alerts.map(a => a.alert_id === alertId ? { ...a, read: true } : a));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Error marking alert read:", err);
    }
  };

  const handleDismiss = async (alertId) => {
    try {
      const headers = getAuthHeaders();
      await axios.post(`${API}/creators/me/alerts/${alertId}/dismiss`, {}, { headers });
      setAlerts(alerts.filter(a => a.alert_id !== alertId));
    } catch (err) {
      console.error("Error dismissing alert:", err);
    }
  };

  const handleAction = (alert) => {
    // Handle CTA click - navigate to the URL
    if (alert.cta_url) {
      window.location.href = alert.cta_url;
    }
  };

  const handleSavePreferences = async (newPrefs) => {
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/creators/me/alert-preferences`, newPrefs, { headers });
      setPreferences(newPrefs);
    } catch (err) {
      console.error("Error saving preferences:", err);
    }
  };

  // Filter alerts by tab
  const filteredAlerts = alerts.filter(alert => {
    if (activeTab === "all") return true;
    if (activeTab === "unread") return !alert.read;
    return alert.priority === activeTab;
  });

  // Access denied - show upgrade prompt
  if (accessDenied) {
    return (
      <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200" data-testid="alerts-upgrade">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mb-6">
            <span className="text-4xl">🔔</span>
          </div>
          <h2 className="text-2xl font-bold text-amber-800 mb-3">Predictive Alerts</h2>
          <p className="text-amber-600 max-w-md mx-auto mb-6">
            Upgrade to Pro to receive real-time predictive alerts. Get notified about optimal timing,
            performance changes, and actionable opportunities.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">⏰</span>
              <p className="text-xs text-slate-600 mt-2">Timing Alerts</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🔥</span>
              <p className="text-xs text-slate-600 mt-2">Streak Updates</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">⚠️</span>
              <p className="text-xs text-slate-600 mt-2">Risk Warnings</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">💡</span>
              <p className="text-xs text-slate-600 mt-2">Smart Insights</p>
            </div>
          </div>
          <Button
            onClick={onUpgrade}
            className="bg-amber-600 hover:bg-amber-700"
            data-testid="upgrade-to-pro-alerts"
          >
            ⚡ Upgrade to Pro
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Loading state
  if (loading) {
    return (
      <Card data-testid="alerts-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading alerts...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200" data-testid="alerts-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchAlerts} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="predictive-alerts">
      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={showPreferences}
        onClose={() => setShowPreferences(false)}
        preferences={preferences}
        onSave={handleSavePreferences}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            🔔 Predictive Alerts
            <Badge className="bg-purple-100 text-purple-700">{tier?.toUpperCase()}</Badge>
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">{unreadCount} new</Badge>
            )}
          </h2>
          <p className="text-sm text-slate-600">Real-time insights and actionable opportunities</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            data-testid="refresh-alerts"
          >
            {refreshing ? "🔄 Checking..." : "🔄 Refresh"}
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowPreferences(true)}
            data-testid="alert-preferences"
          >
            ⚙️ Preferences
          </Button>
        </div>
      </div>

      {/* Priority Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-700">{priorityCounts.urgent || 0}</p>
            <p className="text-sm text-red-600">Urgent</p>
          </CardContent>
        </Card>
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-amber-700">{priorityCounts.high || 0}</p>
            <p className="text-sm text-amber-600">High</p>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-700">{priorityCounts.medium || 0}</p>
            <p className="text-sm text-blue-600">Medium</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-slate-700">{priorityCounts.low || 0}</p>
            <p className="text-sm text-slate-600">Low</p>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-purple-700">{alerts.length}</p>
            <p className="text-sm text-purple-600">Total</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all" data-testid="tab-all-alerts">
            All ({alerts.length})
          </TabsTrigger>
          <TabsTrigger value="unread" data-testid="tab-unread-alerts">
            Unread ({unreadCount})
          </TabsTrigger>
          <TabsTrigger value="urgent" data-testid="tab-urgent-alerts">
            🔴 Urgent
          </TabsTrigger>
          <TabsTrigger value="high" data-testid="tab-high-alerts">
            🟠 High
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {filteredAlerts.length > 0 ? (
            <div className="space-y-4">
              {filteredAlerts.map((alert) => (
                <AlertCard
                  key={alert.alert_id}
                  alert={alert}
                  onRead={handleMarkRead}
                  onDismiss={handleDismiss}
                  onAction={handleAction}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">✨</span>
                <p className="text-slate-600 mt-2">
                  {activeTab === "all"
                    ? "No alerts right now. You're all caught up!"
                    : activeTab === "unread"
                    ? "No unread alerts"
                    : `No ${activeTab} priority alerts`}
                </p>
                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  className="mt-4"
                  disabled={refreshing}
                >
                  Check for New Alerts
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveAlerts;
