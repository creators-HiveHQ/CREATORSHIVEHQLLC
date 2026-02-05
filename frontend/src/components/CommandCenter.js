/**
 * Creators Hive HQ - Command Center Dashboard
 * ============================================
 * Phase 5: Dashboard Restoration
 * 
 * Central control hub displaying:
 * - Engine Status (EngineStatusPanel)
 * - Module Status (ModuleStatusPanel)
 * - Next Steps
 * - Blockers
 * - ARRIS Structural Guidance
 * - Millicent Tone Guidance
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  LayoutDashboard, Activity, Grid3X3, ArrowRight,
  AlertTriangle, CheckCircle2, Lightbulb, MessageSquare,
  RefreshCw, Zap, Target, TrendingUp, User,
  ChevronRight, Sparkles, Brain, Eye, Layers
} from "lucide-react";

import EngineStatusPanel from "./EngineStatusPanel";
import ModuleStatusPanel from "./ModuleStatusPanel";
import KeeperPanel, { KeeperWidget } from "./KeeperPanel";
import { InventoryWidget } from "./UniversalInventory";
import ActivityNotificationBell from "./ActivityNotificationBell";
import useActivityData from "@/hooks/useActivityData";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== NEXT STEPS PANEL ==============
const NextStepsPanel = ({ nextSteps, loading }) => {
  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <ArrowRight className="w-5 h-5 text-emerald-500" />
          Next Steps
        </CardTitle>
        <CardDescription>Recommended actions based on your progress</CardDescription>
      </CardHeader>
      <CardContent>
        {nextSteps.length === 0 ? (
          <p className="text-sm text-slate-500">No pending steps. Great progress!</p>
        ) : (
          <div className="space-y-2">
            {nextSteps.map((step, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-emerald-50 rounded-lg border border-emerald-100"
              >
                <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {idx + 1}
                </div>
                <p className="text-sm text-slate-700 flex-1">
                  {typeof step === "string" ? step : step.step || step.message}
                </p>
                <ChevronRight className="w-4 h-4 text-emerald-500 flex-shrink-0" />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// ============== BLOCKERS PANEL ==============
const BlockersPanel = ({ blockers, loading }) => {
  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  if (blockers.length === 0) {
    return (
      <Card className="border-0 shadow-sm bg-emerald-50">
        <CardContent className="p-6 text-center">
          <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
          <p className="text-sm text-emerald-700 font-medium">No Blockers</p>
          <p className="text-xs text-emerald-600">All systems running smoothly</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm border-l-4 border-l-red-500">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          Blockers ({blockers.length})
        </CardTitle>
        <CardDescription>Issues preventing progress</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {blockers.map((blocker, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 bg-red-50 rounded-lg"
            >
              <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-red-700">
                  {typeof blocker === "string" ? blocker : blocker.blocker || blocker.message}
                </p>
                {blocker.engine && (
                  <span className="text-xs text-red-500">Engine: {blocker.engine}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// ============== ARRIS GUIDANCE PANEL ==============
const ArrisGuidancePanel = ({ outputs, loading }) => {
  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="w-5 h-5 text-blue-500" />
              ARRIS Guidance
            </CardTitle>
            <CardDescription>Structure • Clarity • Logic</CardDescription>
          </div>
          <Badge className="bg-blue-100 text-blue-700">AI Assistant</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {outputs.length === 0 ? (
          <p className="text-sm text-slate-500">No guidance available yet. Complete more modules to receive recommendations.</p>
        ) : (
          <ScrollArea className="h-[200px]">
            <div className="space-y-3">
              {outputs.map((output, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-blue-50 rounded-lg border border-blue-100"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs capitalize">
                      {output.output_type || "guidance"}
                    </Badge>
                    {output.priority && (
                      <Badge className={`text-xs ${
                        output.priority === "high" ? "bg-amber-100 text-amber-700" :
                        output.priority === "critical" ? "bg-red-100 text-red-700" :
                        "bg-slate-100 text-slate-600"
                      }`}>
                        {output.priority}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-slate-700">
                    {output.recommendation || output.content || output.message}
                  </p>
                  {output.related_module && (
                    <p className="text-xs text-blue-600 mt-1">
                      Related: {output.related_module}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

// ============== MILLICENT GUIDANCE PANEL ==============
const MillicentGuidancePanel = ({ outputs, loading }) => {
  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-500" />
              Millicent Guidance
            </CardTitle>
            <CardDescription>Tone • Resonance • Communication</CardDescription>
          </div>
          <Badge className="bg-purple-100 text-purple-700">Rule-Based</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {outputs.length === 0 ? (
          <p className="text-sm text-slate-500">No tone guidance available yet.</p>
        ) : (
          <ScrollArea className="h-[200px]">
            <div className="space-y-3">
              {outputs.map((output, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-purple-50 rounded-lg border border-purple-100"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs capitalize">
                      {output.output_type || output.tone_style || "tone"}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-700">
                    {output.guidance || output.content || output.message}
                  </p>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

// ============== TRACK INFO HEADER ==============
const TrackInfoHeader = ({ systemState, loading }) => {
  if (loading || !systemState) {
    return null;
  }

  const trackLabels = {
    creator_track: { label: "Creator Track", icon: Sparkles, color: "bg-purple-500" },
    business_track: { label: "Business Track", icon: TrendingUp, color: "bg-blue-500" },
    hybrid_track: { label: "Hybrid Track", icon: Target, color: "bg-emerald-500" }
  };

  const trackInfo = trackLabels[systemState.track] || trackLabels.hybrid_track;
  const TrackIcon = trackInfo.icon;

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${trackInfo.color}`}>
          <TrackIcon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-900">{trackInfo.label}</h2>
          <p className="text-sm text-slate-500">
            Priority: <span className="font-medium capitalize">{systemState.first_priority?.replace(/_/g, " ") || "Not set"}</span>
          </p>
        </div>
      </div>
      <div className="flex gap-3">
        <div className="text-center">
          <p className="text-2xl font-bold text-emerald-600">{systemState.engines_active || 0}</p>
          <p className="text-xs text-slate-500">Engines Active</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{systemState.modules_unlocked || 0}</p>
          <p className="text-xs text-slate-500">Modules Unlocked</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-purple-600">{Math.round(systemState.overall_progress || 0)}%</p>
          <p className="text-xs text-slate-500">Progress</p>
        </div>
      </div>
    </div>
  );
};

// ============== MAIN COMMAND CENTER ==============
export default function CommandCenter({ token, onNavigateToIntake }) {
  const [commandCenterData, setCommandCenterData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const navigate = useNavigate();

  const fetchCommandCenterData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/command-center`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        throw new Error("Failed to fetch command center data");
      }
      
      const data = await res.json();
      
      // Check if intake is required
      if (data.intake_required) {
        if (onNavigateToIntake) {
          onNavigateToIntake();
        }
        return;
      }
      
      setCommandCenterData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, onNavigateToIntake]);

  useEffect(() => {
    if (token) {
      fetchCommandCenterData();
    }
  }, [token, fetchCommandCenterData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-slate-400" />
          <p className="text-slate-500 mt-3">Loading Command Center...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <AlertTriangle className="w-8 h-8 mx-auto text-red-400 mb-3" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchCommandCenterData}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!commandCenterData) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <LayoutDashboard className="w-8 h-8 mx-auto text-slate-300 mb-3" />
            <p className="text-slate-600 mb-4">Please complete the intake form to access the Command Center</p>
            <Button onClick={onNavigateToIntake}>Go to Intake Form</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const nextSteps = commandCenterData.next_steps || [];
  const blockers = commandCenterData.blockers || [];
  const arrisOutputs = commandCenterData.arris_outputs || [];
  const millicentOutputs = commandCenterData.millicent_outputs || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-900 rounded-lg">
              <LayoutDashboard className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Command Center</h1>
              <p className="text-sm text-slate-500">Your system control hub</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchCommandCenterData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Track Info */}
        <TrackInfoHeader
          systemState={commandCenterData}
          loading={loading}
        />

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <LayoutDashboard className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="keeper" className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Keeper
            </TabsTrigger>
            <TabsTrigger value="engines" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Engines
            </TabsTrigger>
            <TabsTrigger value="modules" className="flex items-center gap-2">
              <Grid3X3 className="w-4 h-4" />
              Modules
            </TabsTrigger>
            <TabsTrigger value="guidance" className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              AI Guidance
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Status */}
              <div className="lg:col-span-2 space-y-6">
                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="border-0 shadow-sm">
                    <CardContent className="p-4 text-center">
                      <Activity className="w-6 h-6 mx-auto text-emerald-500 mb-2" />
                      <p className="text-2xl font-bold text-slate-900">{commandCenterData.engines_active || 0}</p>
                      <p className="text-xs text-slate-500">Engines Active</p>
                    </CardContent>
                  </Card>
                  <Card className="border-0 shadow-sm">
                    <CardContent className="p-4 text-center">
                      <Grid3X3 className="w-6 h-6 mx-auto text-blue-500 mb-2" />
                      <p className="text-2xl font-bold text-slate-900">{commandCenterData.modules_unlocked || 0}</p>
                      <p className="text-xs text-slate-500">Modules Unlocked</p>
                    </CardContent>
                  </Card>
                  <Card className="border-0 shadow-sm">
                    <CardContent className="p-4 text-center">
                      <ArrowRight className="w-6 h-6 mx-auto text-purple-500 mb-2" />
                      <p className="text-2xl font-bold text-slate-900">{nextSteps.length}</p>
                      <p className="text-xs text-slate-500">Next Steps</p>
                    </CardContent>
                  </Card>
                  <Card className="border-0 shadow-sm">
                    <CardContent className="p-4 text-center">
                      <AlertTriangle className={`w-6 h-6 mx-auto mb-2 ${blockers.length > 0 ? "text-red-500" : "text-emerald-500"}`} />
                      <p className="text-2xl font-bold text-slate-900">{blockers.length}</p>
                      <p className="text-xs text-slate-500">Blockers</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Next Steps */}
                <NextStepsPanel nextSteps={nextSteps} loading={false} />

                {/* Active Modules Quick View */}
                <Card className="border-0 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Grid3X3 className="w-5 h-5" />
                      Active Modules
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-2">
                      {(commandCenterData.active_modules || []).slice(0, 4).map((module, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg"
                        >
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          <span className="text-sm text-slate-700 truncate">
                            {module.name || module.id || module}
                          </span>
                        </div>
                      ))}
                    </div>
                    {(commandCenterData.active_modules || []).length > 4 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full mt-2"
                        onClick={() => setActiveTab("modules")}
                      >
                        View All Modules
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Keeper, Inventory & Blockers */}
              <div className="space-y-6">
                {/* Keeper Widget */}
                <KeeperWidget 
                  systemState={commandCenterData}
                  onClick={() => setActiveTab("keeper")}
                />

                {/* Inventory Widget */}
                <InventoryWidget 
                  inventoryData={{}}
                  onClick={() => navigate("/inventory")}
                />

                <BlockersPanel blockers={blockers} loading={false} />
                
                {/* Quick ARRIS Tip */}
                {arrisOutputs.length > 0 && (
                  <Card className="border-0 shadow-sm bg-blue-50">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <Brain className="w-5 h-5 text-blue-500 mt-0.5" />
                        <div>
                          <p className="text-xs text-blue-600 font-medium mb-1">ARRIS says:</p>
                          <p className="text-sm text-slate-700">
                            {arrisOutputs[0].recommendation || arrisOutputs[0].content}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Quick Millicent Tip */}
                {millicentOutputs.length > 0 && (
                  <Card className="border-0 shadow-sm bg-purple-50">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <MessageSquare className="w-5 h-5 text-purple-500 mt-0.5" />
                        <div>
                          <p className="text-xs text-purple-600 font-medium mb-1">Millicent says:</p>
                          <p className="text-sm text-slate-700">
                            {millicentOutputs[0].guidance || millicentOutputs[0].content}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Keeper Tab */}
          <TabsContent value="keeper">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <KeeperPanel
                  systemState={commandCenterData}
                  engines={commandCenterData.engines || []}
                  modules={commandCenterData.active_modules || []}
                  nextSteps={nextSteps}
                  blockers={blockers}
                  loading={false}
                />
              </div>
              <div className="space-y-4">
                {/* Quick Actions from Keeper */}
                <Card className="border-0 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => navigate("/inventory")}
                    >
                      <Layers className="w-4 h-4 mr-2" />
                      Open Inventory
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab("engines")}
                    >
                      <Activity className="w-4 h-4 mr-2" />
                      View Engines
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab("modules")}
                    >
                      <Grid3X3 className="w-4 h-4 mr-2" />
                      View Modules
                    </Button>
                  </CardContent>
                </Card>

                {/* System Status Summary */}
                <Card className="border-0 shadow-sm bg-gradient-to-br from-slate-50 to-slate-100">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">System Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Engines Active</span>
                        <Badge className="bg-emerald-100 text-emerald-700">
                          {commandCenterData.engines_active || 0} / 4
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Modules Unlocked</span>
                        <Badge className="bg-blue-100 text-blue-700">
                          {commandCenterData.modules_unlocked || 0} / 18
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Blockers</span>
                        <Badge className={blockers.length > 0 ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}>
                          {blockers.length}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Engines Tab */}
          <TabsContent value="engines">
            <EngineStatusPanel token={token} />
          </TabsContent>

          {/* Modules Tab */}
          <TabsContent value="modules">
            <ModuleStatusPanel token={token} />
          </TabsContent>

          {/* AI Guidance Tab */}
          <TabsContent value="guidance">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ArrisGuidancePanel outputs={arrisOutputs} loading={false} />
              <MillicentGuidancePanel outputs={millicentOutputs} loading={false} />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
