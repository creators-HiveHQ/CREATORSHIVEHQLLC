/**
 * Pattern Export Component (Module A5)
 * Allows Premium+ creators to export pattern analysis data in JSON or CSV format.
 * Features filtering options, preview, and export history.
 */

import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Category styles for visual display
const CATEGORY_STYLES = {
  success: { bg: "bg-green-100", text: "text-green-700", icon: "✅" },
  risk: { bg: "bg-red-100", text: "text-red-700", icon: "⚠️" },
  timing: { bg: "bg-blue-100", text: "text-blue-700", icon: "⏰" },
  growth: { bg: "bg-purple-100", text: "text-purple-700", icon: "📈" },
  engagement: { bg: "bg-amber-100", text: "text-amber-700", icon: "🎯" },
  platform: { bg: "bg-indigo-100", text: "text-indigo-700", icon: "📱" },
  content: { bg: "bg-pink-100", text: "text-pink-700", icon: "📝" },
};

/**
 * Export Preview Card
 */
const ExportPreviewCard = ({ preview }) => {
  if (!preview) return null;

  return (
    <Card className="bg-slate-50 border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Export Preview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Counts */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white p-3 rounded-lg border">
            <p className="text-2xl font-bold text-purple-600">{preview.total_patterns}</p>
            <p className="text-xs text-slate-500">Patterns</p>
          </div>
          <div className="bg-white p-3 rounded-lg border">
            <p className="text-2xl font-bold text-amber-600">{preview.total_recommendations}</p>
            <p className="text-xs text-slate-500">Recommendations</p>
          </div>
        </div>

        {/* Category Breakdown */}
        {preview.category_breakdown && Object.keys(preview.category_breakdown).length > 0 && (
          <div>
            <p className="text-xs text-slate-500 mb-2">By Category</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(preview.category_breakdown).map(([cat, count]) => {
                const style = CATEGORY_STYLES[cat] || { bg: "bg-slate-100", text: "text-slate-700", icon: "📊" };
                return (
                  <Badge key={cat} className={`${style.bg} ${style.text}`}>
                    {style.icon} {cat}: {count}
                  </Badge>
                );
              })}
            </div>
          </div>
        )}

        {/* Confidence Breakdown */}
        {preview.confidence_breakdown && (
          <div>
            <p className="text-xs text-slate-500 mb-2">By Confidence</p>
            <div className="flex gap-2">
              <Badge className="bg-green-100 text-green-700">High: {preview.confidence_breakdown.high}</Badge>
              <Badge className="bg-amber-100 text-amber-700">Medium: {preview.confidence_breakdown.medium}</Badge>
              <Badge className="bg-slate-100 text-slate-600">Low: {preview.confidence_breakdown.low}</Badge>
            </div>
          </div>
        )}

        {/* File Size Estimate */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-500">Estimated File Size</span>
          <span className="font-medium">{preview.estimated_file_size}</span>
        </div>

        {/* Actionable Indicator */}
        {preview.has_actionable && (
          <p className="text-xs text-purple-600">
            💡 Includes actionable patterns with recommendations
          </p>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Export History Item
 */
const ExportHistoryItem = ({ exportItem, onReExport }) => {
  const date = new Date(exportItem.exported_at);
  
  return (
    <div className="flex items-center justify-between p-3 bg-white border rounded-lg hover:bg-slate-50" data-testid={`export-history-${exportItem.export_id}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          exportItem.format === "json" ? "bg-purple-100 text-purple-600" : "bg-green-100 text-green-600"
        }`}>
          {exportItem.format === "json" ? "{ }" : "📊"}
        </div>
        <div>
          <p className="font-medium text-sm">{exportItem.export_id}</p>
          <p className="text-xs text-slate-500">
            {date.toLocaleDateString()} at {date.toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right text-xs text-slate-500">
          <p>{exportItem.record_counts?.patterns || 0} patterns</p>
          <p>{exportItem.record_counts?.recommendations || 0} recommendations</p>
        </div>
        <Badge variant="outline">{exportItem.format.toUpperCase()}</Badge>
      </div>
    </div>
  );
};

/**
 * Main Pattern Export Component
 */
export const PatternExport = ({ token, onUpgrade }) => {
  const [options, setOptions] = useState(null);
  const [preview, setPreview] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [activeTab, setActiveTab] = useState("export");
  
  // Export settings
  const [exportFormat, setExportFormat] = useState("json");
  const [selectedCategories, setSelectedCategories] = useState(["all"]);
  const [confidenceLevel, setConfidenceLevel] = useState("all");
  const [dateRange, setDateRange] = useState("all");
  const [includeRecommendations, setIncludeRecommendations] = useState(true);
  const [includeTrends, setIncludeTrends] = useState(true);
  const [includeFeedback, setIncludeFeedback] = useState(false);
  
  // Success dialog
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [exportResult, setExportResult] = useState(null);

  const getAuthHeaders = useCallback(() => {
    return { Authorization: `Bearer ${token}` };
  }, [token]);

  const fetchOptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = getAuthHeaders();
      
      const response = await axios.get(`${API}/creators/me/pattern-export/options`, { headers });
      
      if (response.data.access_denied) {
        setAccessDenied(true);
        return;
      }
      
      setOptions(response.data);
      setAccessDenied(false);
    } catch (err) {
      console.error("Error fetching export options:", err);
      if (err.response?.status === 403) {
        setAccessDenied(true);
      } else {
        setError("Failed to load export options");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchPreview = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const params = new URLSearchParams();
      
      if (selectedCategories.length > 0 && !selectedCategories.includes("all")) {
        params.set("categories", selectedCategories.join(","));
      }
      params.set("confidence_level", confidenceLevel);
      params.set("date_range", dateRange);
      
      const response = await axios.get(`${API}/creators/me/pattern-export/preview?${params}`, { headers });
      
      if (!response.data.access_denied) {
        setPreview(response.data.preview);
      }
    } catch (err) {
      console.error("Error fetching preview:", err);
    }
  }, [getAuthHeaders, selectedCategories, confidenceLevel, dateRange]);

  const fetchHistory = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/creators/me/pattern-export/history`, { headers });
      
      if (!response.data.access_denied) {
        setHistory(response.data.exports || []);
      }
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    if (token) {
      fetchOptions();
    }
  }, [token, fetchOptions]);

  useEffect(() => {
    if (token && !accessDenied) {
      fetchPreview();
    }
  }, [token, accessDenied, fetchPreview]);

  useEffect(() => {
    if (token && !accessDenied && activeTab === "history") {
      fetchHistory();
    }
  }, [token, accessDenied, activeTab, fetchHistory]);

  const handleCategoryChange = (category) => {
    if (category === "all") {
      setSelectedCategories(["all"]);
    } else {
      const newCategories = selectedCategories.filter(c => c !== "all");
      if (newCategories.includes(category)) {
        const filtered = newCategories.filter(c => c !== category);
        setSelectedCategories(filtered.length > 0 ? filtered : ["all"]);
      } else {
        setSelectedCategories([...newCategories, category]);
      }
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      setError(null);
      
      const headers = getAuthHeaders();
      const params = new URLSearchParams();
      
      params.set("export_format", exportFormat);
      if (selectedCategories.length > 0 && !selectedCategories.includes("all")) {
        params.set("categories", selectedCategories.join(","));
      }
      params.set("confidence_level", confidenceLevel);
      params.set("date_range", dateRange);
      params.set("include_recommendations", includeRecommendations);
      params.set("include_trends", includeTrends);
      params.set("include_feedback", includeFeedback);
      
      const response = await axios.post(`${API}/creators/me/pattern-export?${params}`, {}, { headers });
      
      if (response.data.success) {
        setExportResult(response.data);
        setShowSuccessDialog(true);
        
        // Trigger download
        const blob = new Blob([response.data.content], { type: response.data.content_type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = response.data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Refresh history
        fetchHistory();
      } else {
        setError(response.data.error || "Export failed");
      }
    } catch (err) {
      console.error("Export error:", err);
      if (err.response?.status === 403) {
        setAccessDenied(true);
      } else {
        setError(err.response?.data?.detail || "Export failed");
      }
    } finally {
      setExporting(false);
    }
  };

  // Access denied - show upgrade prompt
  if (accessDenied) {
    return (
      <Card className="bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200" data-testid="pattern-export-upgrade">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mb-6">
            <span className="text-4xl">📤</span>
          </div>
          <h2 className="text-2xl font-bold text-amber-800 mb-3">Pattern Export</h2>
          <p className="text-amber-600 max-w-md mx-auto mb-6">
            Export your pattern analysis data with Premium tier. Download patterns, recommendations, 
            and trends in JSON or CSV format for external analysis and reporting.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">📊</span>
              <p className="text-xs text-slate-600 mt-2">JSON Export</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">📋</span>
              <p className="text-xs text-slate-600 mt-2">CSV Export</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🎯</span>
              <p className="text-xs text-slate-600 mt-2">Custom Filters</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">📜</span>
              <p className="text-xs text-slate-600 mt-2">Export History</p>
            </div>
          </div>
          <Button
            onClick={onUpgrade}
            className="bg-amber-600 hover:bg-amber-700"
            data-testid="upgrade-to-premium-export"
          >
            ⚡ Upgrade to Premium
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Loading state
  if (loading) {
    return (
      <Card data-testid="pattern-export-loading">
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading export options...</p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-red-200" data-testid="pattern-export-error">
        <CardContent className="py-8 text-center">
          <span className="text-4xl">❌</span>
          <p className="text-red-600 mt-2">{error}</p>
          <Button variant="outline" onClick={fetchOptions} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="pattern-export">
      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="text-green-500">✅</span>
              Export Successful
            </DialogTitle>
            <DialogDescription>
              Your pattern data has been exported successfully.
            </DialogDescription>
          </DialogHeader>
          {exportResult && (
            <div className="space-y-4 py-4">
              <div className="bg-slate-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-slate-600">Export ID</span>
                  <span className="font-mono text-sm">{exportResult.export_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-600">Format</span>
                  <Badge>{exportResult.format.toUpperCase()}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-600">Patterns</span>
                  <span className="font-medium">{exportResult.record_counts?.patterns || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-600">Recommendations</span>
                  <span className="font-medium">{exportResult.record_counts?.recommendations || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-600">Checksum</span>
                  <span className="font-mono text-xs">{exportResult.checksum}</span>
                </div>
              </div>
              <p className="text-sm text-green-600 text-center">
                The file has been downloaded automatically.
              </p>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowSuccessDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            📤 Pattern Export
            <Badge className="bg-amber-100 text-amber-700">{options?.tier?.toUpperCase()}</Badge>
          </h2>
          <p className="text-sm text-slate-600">Export your pattern analysis data</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="export" data-testid="tab-export">
            📤 Export Data
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            📜 History ({history.length})
          </TabsTrigger>
        </TabsList>

        {/* Export Tab */}
        <TabsContent value="export" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Export Settings */}
            <div className="lg:col-span-2 space-y-6">
              {/* Format Selection */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Export Format</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        exportFormat === "json"
                          ? "border-purple-500 bg-purple-50"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                      onClick={() => setExportFormat("json")}
                      data-testid="format-json"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 font-mono">
                          {"{ }"}
                        </div>
                        <div>
                          <p className="font-medium">JSON</p>
                          <p className="text-xs text-slate-500">Structured data</p>
                        </div>
                      </div>
                    </div>
                    <div
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        exportFormat === "csv"
                          ? "border-green-500 bg-green-50"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                      onClick={() => setExportFormat("csv")}
                      data-testid="format-csv"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                          📊
                        </div>
                        <div>
                          <p className="font-medium">CSV</p>
                          <p className="text-xs text-slate-500">Spreadsheet format</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Filters */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Filters</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Category Selection */}
                  <div>
                    <Label className="text-sm text-slate-600 mb-2 block">Categories</Label>
                    <div className="flex flex-wrap gap-2">
                      {["all", "success", "risk", "timing", "growth", "engagement", "platform", "content"].map((cat) => {
                        const isSelected = selectedCategories.includes(cat);
                        const style = CATEGORY_STYLES[cat] || { bg: "bg-slate-100", text: "text-slate-700", icon: "📊" };
                        return (
                          <Badge
                            key={cat}
                            className={`cursor-pointer transition-all ${
                              isSelected
                                ? `${style.bg} ${style.text} ring-2 ring-offset-1 ring-slate-300`
                                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                            }`}
                            onClick={() => handleCategoryChange(cat)}
                            data-testid={`category-${cat}`}
                          >
                            {cat === "all" ? "📊" : style.icon} {cat.charAt(0).toUpperCase() + cat.slice(1)}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>

                  {/* Confidence Level */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm text-slate-600 mb-2 block">Confidence Level</Label>
                      <Select value={confidenceLevel} onValueChange={setConfidenceLevel}>
                        <SelectTrigger data-testid="confidence-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Levels</SelectItem>
                          <SelectItem value="high">High Only</SelectItem>
                          <SelectItem value="medium">Medium Only</SelectItem>
                          <SelectItem value="low">Low Only</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Date Range */}
                    <div>
                      <Label className="text-sm text-slate-600 mb-2 block">Date Range</Label>
                      <Select value={dateRange} onValueChange={setDateRange}>
                        <SelectTrigger data-testid="date-range-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Time</SelectItem>
                          <SelectItem value="7d">Last 7 Days</SelectItem>
                          <SelectItem value="30d">Last 30 Days</SelectItem>
                          <SelectItem value="90d">Last 90 Days</SelectItem>
                          <SelectItem value="1y">Last Year</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Include Options */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Include in Export</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-recs"
                      checked={includeRecommendations}
                      onCheckedChange={setIncludeRecommendations}
                      data-testid="include-recommendations"
                    />
                    <Label htmlFor="include-recs" className="text-sm">
                      Recommendations (actionable insights)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-trends"
                      checked={includeTrends}
                      onCheckedChange={setIncludeTrends}
                      data-testid="include-trends"
                    />
                    <Label htmlFor="include-trends" className="text-sm">
                      Trends (historical pattern data)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="include-feedback"
                      checked={includeFeedback}
                      onCheckedChange={setIncludeFeedback}
                      data-testid="include-feedback"
                    />
                    <Label htmlFor="include-feedback" className="text-sm">
                      Feedback history (your pattern ratings)
                    </Label>
                  </div>
                </CardContent>
              </Card>

              {/* Export Button */}
              <Button
                className="w-full bg-amber-600 hover:bg-amber-700 h-12 text-lg"
                onClick={handleExport}
                disabled={exporting}
                data-testid="export-button"
              >
                {exporting ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Exporting...
                  </>
                ) : (
                  <>
                    📤 Export {exportFormat.toUpperCase()}
                  </>
                )}
              </Button>
            </div>

            {/* Preview Panel */}
            <div>
              <ExportPreviewCard preview={preview} />
            </div>
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-4">
          {history.length > 0 ? (
            <div className="space-y-3">
              {history.map((exportItem) => (
                <ExportHistoryItem key={exportItem.export_id} exportItem={exportItem} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <span className="text-4xl">📜</span>
                <p className="text-slate-600 mt-2">
                  No export history yet. Export your first patterns above!
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PatternExport;
