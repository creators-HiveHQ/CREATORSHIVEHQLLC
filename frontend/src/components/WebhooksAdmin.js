/**
 * Webhooks Admin Page
 * Zero-Human Operational Model - Event & Automation Monitoring
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icons
const Icons = {
  Refresh: () => <span className="text-lg">🔄</span>,
  Webhook: () => <span className="text-xl">⚡</span>,
  Rule: () => <span className="text-xl">📋</span>,
  Check: () => <span className="text-green-500">✓</span>,
  Clock: () => <span className="text-amber-500">⏱</span>,
  Error: () => <span className="text-red-500">✗</span>,
};

const WebhooksAdmin = () => {
  const [events, setEvents] = useState([]);
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("events");
  const [eventFilter, setEventFilter] = useState({ type: "", status: "" });

  // Get auth token
  const getAuthHeaders = () => {
    const token = localStorage.getItem("hivehq_token");
    return { Authorization: `Bearer ${token}` };
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const headers = getAuthHeaders();

      // Build events query
      const eventParams = new URLSearchParams();
      if (eventFilter.type) eventParams.append("event_type", eventFilter.type);
      if (eventFilter.status) eventParams.append("status", eventFilter.status);
      eventParams.append("limit", "50");

      const [eventsRes, rulesRes, statsRes] = await Promise.all([
        axios.get(`${API}/webhooks/events?${eventParams.toString()}`, { headers }),
        axios.get(`${API}/webhooks/rules`, { headers }),
        axios.get(`${API}/webhooks/stats`, { headers }),
      ]);

      setEvents(eventsRes.data);
      setRules(rulesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching webhook data:", error);
    } finally {
      setLoading(false);
    }
  }, [eventFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleToggleRule = async (ruleId, currentStatus) => {
    try {
      const headers = getAuthHeaders();
      await axios.patch(
        `${API}/webhooks/rules/${ruleId}?is_active=${!currentStatus}`,
        {},
        { headers }
      );
      // Refresh rules
      const rulesRes = await axios.get(`${API}/webhooks/rules`, { headers });
      setRules(rulesRes.data);
    } catch (error) {
      console.error("Error toggling rule:", error);
    }
  };

  const handleTestWebhook = async (eventType) => {
    try {
      const headers = getAuthHeaders();
      await axios.post(`${API}/webhooks/test?event_type=${eventType}`, {}, { headers });
      // Refresh events after test
      setTimeout(fetchData, 1000);
    } catch (error) {
      console.error("Error testing webhook:", error);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "completed":
        return <Badge className="bg-green-500"><Icons.Check /> Completed</Badge>;
      case "processing":
        return <Badge className="bg-blue-500"><Icons.Clock /> Processing</Badge>;
      case "pending":
        return <Badge className="bg-amber-500"><Icons.Clock /> Pending</Badge>;
      case "failed":
        return <Badge className="bg-red-500"><Icons.Error /> Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getEventTypeBadge = (type) => {
    const colors = {
      "creator.": "bg-purple-500",
      "proposal.": "bg-blue-500",
      "project.": "bg-green-500",
      "task.": "bg-amber-500",
      "subscription.": "bg-pink-500",
      "arris.": "bg-cyan-500",
      "system.": "bg-slate-500",
    };

    let color = "bg-slate-400";
    for (const [prefix, c] of Object.entries(colors)) {
      if (type.startsWith(prefix)) {
        color = c;
        break;
      }
    }

    return <Badge className={color}>{type}</Badge>;
  };

  const formatTimestamp = (ts) => {
    if (!ts) return "-";
    const date = new Date(ts);
    return date.toLocaleString();
  };

  // Get unique event types for filter
  const eventTypes = [...new Set(events.map((e) => e.event_type))];

  return (
    <div className="space-y-6" data-testid="webhooks-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Icons.Webhook /> Webhook Automations
          </h1>
          <p className="text-slate-500">Zero-Human Ops - Event-Driven Automation System</p>
        </div>
        <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
          <Icons.Refresh /> Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card data-testid="stat-total-events">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Total Events</p>
              <p className="text-2xl font-bold">{stats.total_events}</p>
              <p className="text-xs text-slate-400">All time</p>
            </CardContent>
          </Card>
          <Card data-testid="stat-recent-events">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Events (24h)</p>
              <p className="text-2xl font-bold text-blue-600">{stats.events_last_24h}</p>
              <p className="text-xs text-slate-400">Last 24 hours</p>
            </CardContent>
          </Card>
          <Card data-testid="stat-active-rules">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-500">Active Rules</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.automation_rules?.active || 0}/{stats.automation_rules?.total || 0}
              </p>
              <p className="text-xs text-slate-400">Automation rules</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200" data-testid="stat-zero-human">
            <CardContent className="pt-6">
              <p className="text-sm text-amber-700">Zero-Human Ops</p>
              <p className="text-xl font-bold text-amber-900">Active</p>
              <p className="text-xs text-amber-600">Fully automated</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="events" data-testid="tab-events">
            <Icons.Webhook /> <span className="ml-2">Event Log ({events.length})</span>
          </TabsTrigger>
          <TabsTrigger value="rules" data-testid="tab-rules">
            <Icons.Rule /> <span className="ml-2">Automation Rules ({rules.length})</span>
          </TabsTrigger>
        </TabsList>

        {/* Events Tab */}
        <TabsContent value="events">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Webhook Event Log</CardTitle>
                  <CardDescription>All automated events triggered by the system</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Select
                    value={eventFilter.type || "all"}
                    onValueChange={(v) => setEventFilter({ ...eventFilter, type: v === "all" ? "" : v })}
                  >
                    <SelectTrigger className="w-48" data-testid="filter-event-type">
                      <SelectValue placeholder="All Event Types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Event Types</SelectItem>
                      {eventTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={eventFilter.status || "all"}
                    onValueChange={(v) => setEventFilter({ ...eventFilter, status: v === "all" ? "" : v })}
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
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event ID</TableHead>
                    <TableHead>Event Type</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions Triggered</TableHead>
                    <TableHead>Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : events.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                        No webhook events found. Events will appear here as actions occur in the system.
                      </TableCell>
                    </TableRow>
                  ) : (
                    events.map((event) => (
                      <TableRow key={event.id} data-testid={`event-row-${event.id}`}>
                        <TableCell className="font-mono text-sm">{event.id}</TableCell>
                        <TableCell>{getEventTypeBadge(event.event_type)}</TableCell>
                        <TableCell>
                          <span className="text-slate-500">{event.source_entity}</span>
                          <span className="text-xs font-mono ml-1 text-slate-400">
                            {event.source_id?.slice(0, 12)}
                          </span>
                        </TableCell>
                        <TableCell>{getStatusBadge(event.status)}</TableCell>
                        <TableCell>
                          {event.actions_triggered?.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {event.actions_triggered.slice(0, 3).map((action) => (
                                <Badge key={action} variant="outline" className="text-xs">
                                  {action.replace(/_/g, " ")}
                                </Badge>
                              ))}
                              {event.actions_triggered.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{event.actions_triggered.length - 3}
                                </Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-slate-500">
                          {formatTimestamp(event.timestamp)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Automation Rules</CardTitle>
              <CardDescription>
                Configure which events trigger automated actions. Disabling a rule will stop its automations.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rule ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Event Trigger</TableHead>
                    <TableHead>Actions</TableHead>
                    <TableHead>Times Triggered</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Test</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : rules.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                        No automation rules configured.
                      </TableCell>
                    </TableRow>
                  ) : (
                    rules.map((rule) => (
                      <TableRow key={rule.id} data-testid={`rule-row-${rule.id}`}>
                        <TableCell className="font-mono text-sm">{rule.id}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{rule.name}</p>
                            <p className="text-xs text-slate-500">{rule.description}</p>
                          </div>
                        </TableCell>
                        <TableCell>{getEventTypeBadge(rule.event_type)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {rule.actions?.map((action) => (
                              <Badge key={action} variant="outline" className="text-xs">
                                {action.replace(/_/g, " ")}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-medium">{rule.times_triggered || 0}</span>
                          {rule.last_triggered && (
                            <p className="text-xs text-slate-400">
                              Last: {formatTimestamp(rule.last_triggered)}
                            </p>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={rule.is_active}
                              onCheckedChange={() => handleToggleRule(rule.id, rule.is_active)}
                              data-testid={`toggle-rule-${rule.id}`}
                            />
                            <span className={rule.is_active ? "text-green-600" : "text-slate-400"}>
                              {rule.is_active ? "Active" : "Disabled"}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleTestWebhook(rule.event_type)}
                            disabled={!rule.is_active}
                            data-testid={`test-rule-${rule.id}`}
                          >
                            Test
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Event Type Breakdown */}
      {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Events by Type</CardTitle>
            <CardDescription>Distribution of webhook events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {Object.entries(stats.by_type).map(([type, count]) => (
                <div key={type} className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500 truncate" title={type}>
                    {type}
                  </p>
                  <p className="text-lg font-bold">{count}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WebhooksAdmin;
