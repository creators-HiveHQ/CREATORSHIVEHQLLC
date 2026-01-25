import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Calendar, Clock, Mail, FileText, RefreshCw, Send, Trash2, 
  ChevronRight, CheckCircle, AlertCircle, Sparkles, TrendingUp,
  BarChart3, Target, Lightbulb, DollarSign, Users
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const topicIcons = {
  activity_summary: FileText,
  metrics_overview: BarChart3,
  arris_usage: Sparkles,
  pattern_insights: TrendingUp,
  recommendations: Lightbulb,
  upcoming_tasks: Target,
  financial_summary: DollarSign,
  engagement_trends: Users,
};

const topicDescriptions = {
  activity_summary: 'Proposals, tasks, and memories created',
  metrics_overview: 'Revenue, expenses, and key performance metrics',
  arris_usage: 'Your AI assistant interaction statistics',
  pattern_insights: 'Detected patterns and trends in your activity',
  recommendations: 'AI-powered suggestions for improvement',
  upcoming_tasks: 'Tasks and deadlines coming up',
  financial_summary: 'Detailed financial breakdown by category',
  engagement_trends: 'Daily activity and engagement analysis',
};

export default function ScheduledReportsManager({ token }) {
  const [settings, setSettings] = useState(null);
  const [topics, setTopics] = useState(null);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!token) return;
    
    let cancelled = false;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [settingsRes, topicsRes, historyRes] = await Promise.all([
          fetch(`${API_URL}/api/elite/reports/settings`, { headers }),
          fetch(`${API_URL}/api/elite/reports/topics`, { headers }),
          fetch(`${API_URL}/api/elite/reports/history`, { headers }),
        ]);

        if (cancelled) return;

        if (settingsRes.ok) {
          const data = await settingsRes.json();
          setSettings(data);
        }
        if (topicsRes.ok) {
          const data = await topicsRes.json();
          setTopics(data);
        }
        if (historyRes.ok) {
          const data = await historyRes.json();
          setReports(data.reports || []);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load report data:', error);
          toast.error('Failed to load report settings');
        }
      }
      if (!cancelled) {
        setLoading(false);
      }
    };
    
    fetchData();
    
    return () => { cancelled = true; };
  }, [token, refreshTrigger]);

  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const saveSettings = async (newSettings) => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/elite/reports/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSettings),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        toast.success('Report settings saved');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      toast.error('Failed to save settings');
    }
    setSaving(false);
  };

  const generateReport = async (reportType) => {
    setGenerating(true);
    try {
      const response = await fetch(
        `${API_URL}/api/elite/reports/generate?report_type=${reportType}&send_email=false`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        toast.success(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report generated!`);
        
        // Fetch the full report
        const reportRes = await fetch(
          `${API_URL}/api/elite/reports/${result.report_id}`,
          { headers: { 'Authorization': `Bearer ${token}` }}
        );
        if (reportRes.ok) {
          const reportData = await reportRes.json();
          setSelectedReport(reportData);
        }
        
        refreshData();
      } else {
        toast.error('Failed to generate report');
      }
    } catch (error) {
      toast.error('Failed to generate report');
    }
    setGenerating(false);
  };

  const viewReport = async (reportId) => {
    try {
      const response = await fetch(
        `${API_URL}/api/elite/reports/${reportId}`,
        { headers: { 'Authorization': `Bearer ${token}` }}
      );
      
      if (response.ok) {
        const data = await response.json();
        setSelectedReport(data);
      }
    } catch (error) {
      toast.error('Failed to load report');
    }
  };

  const deleteReport = async (reportId) => {
    if (!window.confirm('Delete this report?')) return;
    
    try {
      const response = await fetch(
        `${API_URL}/api/elite/reports/${reportId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );
      
      if (response.ok) {
        toast.success('Report deleted');
        refreshData();
      }
    } catch (error) {
      toast.error('Failed to delete report');
    }
  };

  const toggleTopic = (topic) => {
    const currentTopics = settings?.topics || [];
    const newTopics = currentTopics.includes(topic)
      ? currentTopics.filter(t => t !== topic)
      : [...currentTopics, topic];
    
    saveSettings({ ...settings, topics: newTopics });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="scheduled-reports-manager">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Mail className="h-6 w-6 text-purple-400" />
            Scheduled Reports
          </h2>
          <p className="text-gray-400 mt-1">
            Receive AI-generated summaries directly in your inbox
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => generateReport('daily')}
            disabled={generating}
            variant="outline"
            data-testid="generate-daily-btn"
          >
            {generating ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
            Generate Daily
          </Button>
          <Button
            onClick={() => generateReport('weekly')}
            disabled={generating}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="generate-weekly-btn"
          >
            {generating ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
            Generate Weekly
          </Button>
        </div>
      </div>

      {/* Settings Card */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white">Report Settings</CardTitle>
              <CardDescription>Configure when and what to include in your reports</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="reports-enabled" className="text-gray-400">
                {settings?.enabled ? 'Enabled' : 'Disabled'}
              </Label>
              <Switch
                id="reports-enabled"
                checked={settings?.enabled || false}
                onCheckedChange={(checked) => saveSettings({ ...settings, enabled: checked })}
                data-testid="reports-enabled-switch"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Frequency */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Label className="text-white">Frequency</Label>
              <Select
                value={settings?.frequency || 'weekly'}
                onValueChange={(value) => saveSettings({ ...settings, frequency: value })}
              >
                <SelectTrigger className="bg-gray-800 border-gray-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily Reports</SelectItem>
                  <SelectItem value="weekly">Weekly Reports</SelectItem>
                  <SelectItem value="both">Both Daily & Weekly</SelectItem>
                  <SelectItem value="none">No Scheduled Reports</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {(settings?.frequency === 'daily' || settings?.frequency === 'both') && (
              <div className="space-y-4">
                <Label className="text-white">Daily Report Time (UTC)</Label>
                <Select
                  value={settings?.daily_time || '08:00'}
                  onValueChange={(value) => saveSettings({ ...settings, daily_time: value })}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {topics?.times?.map((time) => (
                      <SelectItem key={time} value={time}>{time}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {(settings?.frequency === 'weekly' || settings?.frequency === 'both') && (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Label className="text-white">Weekly Report Day</Label>
                <Select
                  value={settings?.weekly_day || 'monday'}
                  onValueChange={(value) => saveSettings({ ...settings, weekly_day: value })}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {topics?.days?.map((day) => (
                      <SelectItem key={day} value={day} className="capitalize">{day}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-4">
                <Label className="text-white">Weekly Report Time (UTC)</Label>
                <Select
                  value={settings?.weekly_time || '09:00'}
                  onValueChange={(value) => saveSettings({ ...settings, weekly_time: value })}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {topics?.times?.map((time) => (
                      <SelectItem key={time} value={time}>{time}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Topics */}
          <div className="space-y-4">
            <Label className="text-white">Report Topics</Label>
            <p className="text-sm text-gray-500">Select what to include in your reports</p>
            <div className="grid md:grid-cols-2 gap-3">
              {topics?.topics?.map((topic) => {
                const isSelected = settings?.topics?.includes(topic.id);
                const IconComponent = topicIcons[topic.id] || FileText;
                
                return (
                  <div
                    key={topic.id}
                    onClick={() => toggleTopic(topic.id)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-purple-600/20 border-purple-500'
                        : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
                    }`}
                    data-testid={`topic-${topic.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-purple-600' : 'bg-gray-700'}`}>
                        <IconComponent className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-white">{topic.label}</span>
                          {isSelected && <CheckCircle className="h-4 w-4 text-purple-400" />}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {topicDescriptions[topic.id] || 'Report section'}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report History */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Report History</CardTitle>
          <CardDescription>View and manage your past reports</CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No reports generated yet.</p>
              <p className="text-sm mt-2">Generate your first report to see it here.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800/70 transition-colors"
                  data-testid={`report-${report.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      report.report_type === 'daily' ? 'bg-blue-600/20' : 'bg-purple-600/20'
                    }`}>
                      {report.report_type === 'daily' ? (
                        <Calendar className="h-5 w-5 text-blue-400" />
                      ) : (
                        <Clock className="h-5 w-5 text-purple-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white capitalize">
                          {report.report_type} Report
                        </span>
                        <Badge className={
                          report.status === 'sent' ? 'bg-green-600/20 text-green-400' :
                          report.status === 'ready' ? 'bg-blue-600/20 text-blue-400' :
                          report.status === 'failed' ? 'bg-red-600/20 text-red-400' :
                          'bg-gray-600/20 text-gray-400'
                        }>
                          {report.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">
                        {report.period_label} • {new Date(report.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => viewReport(report.id)}
                      data-testid={`view-report-${report.id}`}
                    >
                      View <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteReport(report.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Report View Dialog */}
      <Dialog open={!!selectedReport} onOpenChange={() => setSelectedReport(null)}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white capitalize">
              {selectedReport?.report_type} Report - {selectedReport?.period_label}
            </DialogTitle>
            <DialogDescription>
              Generated on {selectedReport && new Date(selectedReport.created_at).toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          
          {selectedReport && (
            <div className="space-y-6 py-4">
              {/* AI Summary */}
              {selectedReport.ai_summary && (
                <div className="bg-purple-900/30 border border-purple-700/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="h-5 w-5 text-purple-400" />
                    <span className="font-medium text-purple-300">AI Summary</span>
                  </div>
                  <p className="text-gray-300">{selectedReport.ai_summary}</p>
                </div>
              )}
              
              {/* Report Sections */}
              {Object.entries(selectedReport.sections || {}).map(([key, section]) => {
                const IconComponent = topicIcons[key] || FileText;
                
                return (
                  <div key={key} className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <IconComponent className="h-5 w-5 text-purple-400" />
                      <span className="font-medium text-white">{section.title || key}</span>
                    </div>
                    
                    <p className="text-gray-400 mb-3">{section.highlight}</p>
                    
                    {/* Render specific section data */}
                    {key === 'recommendations' && section.items && (
                      <div className="space-y-2">
                        {section.items.map((item, i) => (
                          <div key={i} className="flex items-start gap-2 p-2 bg-gray-900/50 rounded">
                            <Badge className={
                              item.priority === 'high' ? 'bg-red-600/20 text-red-400' :
                              item.priority === 'medium' ? 'bg-yellow-600/20 text-yellow-400' :
                              'bg-green-600/20 text-green-400'
                            }>
                              {item.priority}
                            </Badge>
                            <div>
                              <p className="text-white text-sm font-medium">{item.title}</p>
                              <p className="text-gray-500 text-xs">{item.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {key === 'arris_usage' && section.top_categories && (
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        {section.top_categories.map((cat, i) => (
                          <div key={i} className="flex justify-between p-2 bg-gray-900/50 rounded">
                            <span className="text-gray-400 text-sm">{cat.category}</span>
                            <span className="text-white text-sm font-medium">{cat.count}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedReport(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
