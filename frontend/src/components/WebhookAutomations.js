import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Admin Webhooks Page
export const AdminWebhooksPage = () => {
  const [events, setEvents] = useState([]);
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ event_type: "", status: "" });
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [activeTab, setActiveTab] = useState("events");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter.event_type) params.append("event_type", filter.event_type);
      if (filter.status) params.append("status", filter.status);
      
      const [eventsRes, rulesRes, statsRes] = await Promise.all([
        axios.get(`${API}/webhooks/events?${params.toString()}`),
        axios.get(`${API}/webhooks/rules`),
        axios.get(`${API}/webhooks/stats`)
      ]);
      setEvents(eventsRes.data);
      setRules(rulesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching webhook data:", error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleToggleRule = async (ruleId, isActive) => {
    try {
      await axios.patch(`${API}/webhooks/rules/${ruleId}?is_active=${!isActive}`);
      fetchData();
    } catch (error) {
      console.error("Error toggling rule:", error);
    }
  };

  const handleTestWebhook = async (eventType) => {
    try {
      await axios.post(`${API}/webhooks/test?event_type=${eventType}`);
      fetchData();
    } catch (error) {
      console.error("Error testing webhook:", error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-yellow-100 text-yellow-700",
      processing: "bg-blue-100 text-blue-700",
      completed: "bg-green-100 text-green-700",
      failed: "bg-red-100 text-red-700"
    };
    return styles[status] || "bg-slate-100 text-slate-700";
  };

  const getEventTypeBadge = (eventType) => {
    if (eventType?.includes("creator")) return "bg-purple-100 text-purple-700";
    if (eventType?.includes("proposal")) return "bg-blue-100 text-blue-700";
    if (eventType?.includes("project")) return "bg-green-100 text-green-700";
    if (eventType?.includes("arris")) return "bg-amber-100 text-amber-700";
    return "bg-slate-100 text-slate-700";
  };

  const formatEventType = (type) => {
    return type?.replace(/\./g, " → ").replace(/_/g, " ");
  };

  // Get unique event types for filter
  const eventTypes = [...new Set(events.map(e => e.event_type))];

  return (
    <div className="space-y-6" data-testid="admin-webhooks-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Webhook Automations</h1>
          <p className="text-slate-500">Zero-Human Operational Model - Event Processing</p>
        </div>
        <Button onClick={fetchData} variant="outline" data-testid="refresh-btn">
          🔄 Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total_events}</div>
              <p className="text-sm text-slate-500">Total Events</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-700">{stats.events_last_24h}</div>
              <p className="text-sm text-blue-600">Last 24 Hours</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-700">{stats.by_status?.completed || 0}</div>
              <p className="text-sm text-green-600">Completed</p>
            </CardContent>
          </Card>
          <Card className="bg-red-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-700">{stats.by_status?.failed || 0}</div>
              <p className="text-sm text-red-600">Failed</p>
            </CardContent>
          </Card>
          <Card className="bg-purple-50">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-purple-700">
                {stats.automation_rules?.active}/{stats.automation_rules?.total}
              </div>
              <p className="text-sm text-purple-600">Active Rules</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="events" data-testid="tab-events">Event Log</TabsTrigger>
          <TabsTrigger value="rules" data-testid="tab-rules">Automation Rules</TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <div className="flex gap-2">
            <Select
              value={filter.event_type || "all"}
              onValueChange={(v) => setFilter({ ...filter, event_type: v === "all" ? "" : v })}
            >
              <SelectTrigger className="w-48" data-testid="filter-type">
                <SelectValue placeholder="All Event Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Event Types</SelectItem>
                {eventTypes.map((type) => (
                  <SelectItem key={type} value={type}>{formatEventType(type)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={filter.status || "all"}
              onValueChange={(v) => setFilter({ ...filter, status: v === "all" ? "" : v })}
            >
              <SelectTrigger className="w-36" data-testid="filter-status">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left p-4 font-medium">Event ID</th>
                    <th className="text-left p-4 font-medium">Type</th>
                    <th className="text-left p-4 font-medium">Source</th>
                    <th className="text-left p-4 font-medium">Status</th>
                    <th className="text-left p-4 font-medium">Actions</th>
                    <th className="text-left p-4 font-medium">Timestamp</th>
                    <th className="text-left p-4 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8">Loading...</td>
                    </tr>
                  ) : events.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-slate-500">No events found</td>
                    </tr>
                  ) : (
                    events.map((event) => (
                      <tr key={event.id} className="border-t hover:bg-slate-50" data-testid={`event-row-${event.id}`}>
                        <td className="p-4 font-mono text-sm">{event.id}</td>
                        <td className="p-4">
                          <Badge className={getEventTypeBadge(event.event_type)}>
                            {formatEventType(event.event_type)}
                          </Badge>
                        </td>
                        <td className="p-4 text-sm">
                          <span className="text-slate-500">{event.source_entity}</span>
                          <span className="text-slate-400 mx-1">:</span>
                          <span className="font-mono">{event.source_id}</span>
                        </td>
                        <td className="p-4">
                          <Badge className={getStatusBadge(event.status)}>
                            {event.status}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <span className="text-sm text-slate-600">
                            {event.actions_triggered?.length || 0} actions
                          </span>
                        </td>
                        <td className="p-4 text-sm text-slate-500">
                          {new Date(event.timestamp).toLocaleString()}
                        </td>
                        <td className="p-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedEvent(event)}
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <div className="grid gap-4">
            {rules.map((rule) => (
              <Card key={rule.id} data-testid={`rule-card-${rule.id}`}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{rule.name}</CardTitle>
                      <CardDescription>{rule.description}</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Label htmlFor={`switch-${rule.id}`} className="text-sm text-slate-500">
                        {rule.is_active ? "Active" : "Inactive"}
                      </Label>
                      <Switch
                        id={`switch-${rule.id}`}
                        checked={rule.is_active}
                        onCheckedChange={() => handleToggleRule(rule.id, rule.is_active)}
                        data-testid={`toggle-${rule.id}`}
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Trigger Event</p>
                      <Badge className={getEventTypeBadge(rule.event_type)}>
                        {formatEventType(rule.event_type)}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-slate-500">Actions</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rule.actions?.map((action, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {action.replace(/_/g, " ")}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-500">Times Triggered</p>
                      <p className="font-medium">{rule.times_triggered || 0}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Last Triggered</p>
                      <p className="font-medium">
                        {rule.last_triggered 
                          ? new Date(rule.last_triggered).toLocaleDateString()
                          : "Never"}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t flex justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleTestWebhook(rule.event_type)}
                      data-testid={`test-${rule.id}`}
                    >
                      🧪 Test Webhook
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          {stats && (
            <>
              {/* Events by Type Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Events by Type</CardTitle>
                  <CardDescription>Distribution of webhook events</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(stats.by_type || {}).map(([type, count]) => {
                      const percentage = stats.total_events > 0 
                        ? Math.round((count / stats.total_events) * 100) 
                        : 0;
                      return (
                        <div key={type} className="space-y-1">
                          <div className="flex justify-between text-sm">
                            <span className="truncate">{formatEventType(type)}</span>
                            <span className="font-medium">{count} ({percentage}%)</span>
                          </div>
                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${getEventTypeBadge(type).replace('text', 'bg').replace('-100', '-500').replace('-700', '-500')}`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Processing Status */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Processing Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <div className="text-3xl font-bold text-green-600">
                          {stats.by_status?.completed || 0}
                        </div>
                        <p className="text-sm text-green-700">Completed</p>
                      </div>
                      <div className="text-center p-4 bg-red-50 rounded-lg">
                        <div className="text-3xl font-bold text-red-600">
                          {stats.by_status?.failed || 0}
                        </div>
                        <p className="text-sm text-red-700">Failed</p>
                      </div>
                      <div className="text-center p-4 bg-yellow-50 rounded-lg">
                        <div className="text-3xl font-bold text-yellow-600">
                          {stats.by_status?.pending || 0}
                        </div>
                        <p className="text-sm text-yellow-700">Pending</p>
                      </div>
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <div className="text-3xl font-bold text-blue-600">
                          {stats.by_status?.processing || 0}
                        </div>
                        <p className="text-sm text-blue-700">Processing</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>System Health</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">Success Rate</span>
                        <span className="font-bold text-green-600">
                          {stats.total_events > 0 
                            ? Math.round(((stats.by_status?.completed || 0) / stats.total_events) * 100)
                            : 100}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">Active Rules</span>
                        <span className="font-bold">{stats.automation_rules?.active}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">Events/24h</span>
                        <span className="font-bold">{stats.events_last_24h}</span>
                      </div>
                      <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                          <span className="font-medium text-green-800">Zero-Human Ops Active</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedEvent(null)}>
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()} data-testid="event-detail-modal">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Event Details</CardTitle>
                  <CardDescription className="font-mono">{selectedEvent.id}</CardDescription>
                </div>
                <Badge className={getStatusBadge(selectedEvent.status)}>
                  {selectedEvent.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-500">Event Type</Label>
                  <Badge className={`mt-1 ${getEventTypeBadge(selectedEvent.event_type)}`}>
                    {formatEventType(selectedEvent.event_type)}
                  </Badge>
                </div>
                <div>
                  <Label className="text-slate-500">Timestamp</Label>
                  <p>{new Date(selectedEvent.timestamp).toLocaleString()}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Source</Label>
                  <p>{selectedEvent.source_entity}: {selectedEvent.source_id}</p>
                </div>
                <div>
                  <Label className="text-slate-500">User ID</Label>
                  <p className="font-mono">{selectedEvent.user_id || "N/A"}</p>
                </div>
              </div>

              <div>
                <Label className="text-slate-500">Payload</Label>
                <pre className="mt-1 p-3 bg-slate-50 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(selectedEvent.payload, null, 2)}
                </pre>
              </div>

              {selectedEvent.actions_triggered?.length > 0 && (
                <div>
                  <Label className="text-slate-500">Actions Triggered</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {selectedEvent.actions_triggered.map((action, i) => (
                      <Badge key={i} variant="secondary">{action.replace(/_/g, " ")}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedEvent.action_results && Object.keys(selectedEvent.action_results).length > 0 && (
                <div>
                  <Label className="text-slate-500">Action Results</Label>
                  <pre className="mt-1 p-3 bg-slate-50 rounded-lg text-sm overflow-x-auto">
                    {JSON.stringify(selectedEvent.action_results, null, 2)}
                  </pre>
                </div>
              )}

              {selectedEvent.error_message && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <Label className="text-red-700">Error</Label>
                  <p className="text-red-600">{selectedEvent.error_message}</p>
                </div>
              )}

              <div className="flex justify-end pt-4 border-t">
                <Button variant="outline" onClick={() => setSelectedEvent(null)}>
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AdminWebhooksPage;
