/**
 * Creators Hive HQ - Module Status Panel
 * ======================================
 * UI component for displaying module status on the dashboard.
 * Part of Phase 5: Dashboard Restoration.
 * 
 * Displays:
 * - Active/Unlocked/Blocked/Locked modules
 * - Module health indicators
 * - Priority alignment
 * - Blockers and next steps
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle2, AlertCircle, Lock, XCircle,
  ChevronRight, Grid3X3, RefreshCw, Zap,
  Star, AlertTriangle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Status configuration
const STATUS_CONFIG = {
  active: { icon: CheckCircle2, color: "bg-emerald-100 text-emerald-700", label: "Active" },
  unlocked: { icon: Zap, color: "bg-blue-100 text-blue-700", label: "Ready" },
  blocked: { icon: XCircle, color: "bg-red-100 text-red-700", label: "Blocked" },
  locked: { icon: Lock, color: "bg-slate-100 text-slate-500", label: "Locked" }
};

// Color mapping for modules
const COLOR_MAP = {
  slate: "bg-slate-500",
  blue: "bg-blue-500",
  purple: "bg-purple-500",
  amber: "bg-amber-500",
  emerald: "bg-emerald-500"
};

// Module Card Component
const ModuleCard = ({ module, onActivate, onDeactivate, compact = false }) => {
  const statusConfig = STATUS_CONFIG[module.status] || STATUS_CONFIG.locked;
  const StatusIcon = statusConfig.icon;
  const bgColor = COLOR_MAP[module.color] || "bg-slate-500";

  if (compact) {
    return (
      <div className={`flex items-center gap-3 p-3 rounded-lg border ${
        module.status === "active" ? "border-emerald-200 bg-emerald-50" :
        module.status === "blocked" ? "border-red-200 bg-red-50" :
        "border-slate-200"
      }`}>
        <div className={`w-2 h-2 rounded-full ${bgColor}`} />
        <span className="flex-1 text-sm font-medium text-slate-700 truncate">{module.name}</span>
        <Badge className={`${statusConfig.color} text-xs`}>
          {statusConfig.label}
        </Badge>
        {module.priority_alignment && (
          <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
        )}
      </div>
    );
  }

  return (
    <Card className={`border ${
      module.status === "active" ? "border-emerald-200" :
      module.status === "blocked" ? "border-red-200" :
      "border-slate-200"
    } hover:shadow-sm transition-all`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className={`p-2 rounded-lg ${bgColor} bg-opacity-10`}>
            <Grid3X3 className={`w-4 h-4 ${bgColor.replace('bg-', 'text-')}`} />
          </div>
          <div className="flex items-center gap-1">
            {module.priority_alignment && (
              <Star className="w-4 h-4 text-amber-500 fill-amber-500" title="Aligns with your priority" />
            )}
            <Badge className={`${statusConfig.color} text-xs`}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {statusConfig.label}
            </Badge>
          </div>
        </div>

        <h4 className="font-semibold text-slate-900 text-sm mb-1">{module.name}</h4>
        <p className="text-xs text-slate-500 mb-3 line-clamp-2">{module.purpose || module.description}</p>

        {/* Blockers */}
        {module.blockers && module.blockers.length > 0 && (
          <div className="bg-red-50 rounded p-2 mb-3">
            <p className="text-xs text-red-700">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              {module.blockers[0]}
            </p>
          </div>
        )}

        {/* Required engines */}
        {module.required_engines && module.required_engines.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {module.required_engines.map((engine, idx) => (
              <span key={idx} className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                {engine}
              </span>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          {module.status === "unlocked" && (
            <Button
              size="sm"
              variant="default"
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              onClick={() => onActivate(module.module_id)}
            >
              Activate
            </Button>
          )}
          {module.status === "active" && (
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={() => onDeactivate(module.module_id)}
            >
              Deactivate
            </Button>
          )}
          {(module.status === "locked" || module.status === "blocked") && (
            <Button size="sm" variant="ghost" className="flex-1" disabled>
              {module.status === "blocked" ? "Resolve Blockers" : "Unlock Required"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Main Module Status Panel
export default function ModuleStatusPanel({ token }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("active");
  const [updating, setUpdating] = useState(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/modules/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch module status");
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchStatus();
  }, [token]);

  const handleActivate = async (moduleId) => {
    setUpdating(moduleId);
    try {
      const res = await fetch(`${BACKEND_URL}/api/modules/update/${moduleId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ action: "activate" })
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (err) {
      console.error("Failed to activate module:", err);
    } finally {
      setUpdating(null);
    }
  };

  const handleDeactivate = async (moduleId) => {
    setUpdating(moduleId);
    try {
      const res = await fetch(`${BACKEND_URL}/api/modules/update/${moduleId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ action: "deactivate" })
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (err) {
      console.error("Failed to deactivate module:", err);
    } finally {
      setUpdating(null);
    }
  };

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-slate-400" />
          <p className="text-sm text-slate-500 mt-2">Loading modules...</p>
        </CardContent>
      </Card>
    );
  }

  if (error || !status?.initialized) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <AlertCircle className="w-6 h-6 mx-auto text-slate-300" />
          <p className="text-slate-500 mt-2">{error || "Modules not initialized"}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={fetchStatus}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Grid3X3 className="w-5 h-5" />
            Module Status
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge className={`${
              status.overall_health === "good" ? "bg-emerald-100 text-emerald-700" :
              status.overall_health === "has_blockers" ? "bg-red-100 text-red-700" :
              "bg-amber-100 text-amber-700"
            }`}>
              {status.overall_health?.replace(/_/g, " ")}
            </Badge>
            <Button variant="ghost" size="sm" onClick={fetchStatus}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex gap-4 mt-3 text-sm">
          <div className="flex items-center gap-1 text-emerald-600">
            <CheckCircle2 className="w-4 h-4" />
            <span>{status.summary.active} Active</span>
          </div>
          <div className="flex items-center gap-1 text-blue-600">
            <Zap className="w-4 h-4" />
            <span>{status.summary.unlocked} Ready</span>
          </div>
          {status.summary.blocked > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <XCircle className="w-4 h-4" />
              <span>{status.summary.blocked} Blocked</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-slate-400">
            <Lock className="w-4 h-4" />
            <span>{status.summary.locked} Locked</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-4 mb-4">
            <TabsTrigger value="active" className="text-xs">
              Active ({status.summary.active})
            </TabsTrigger>
            <TabsTrigger value="ready" className="text-xs">
              Ready ({status.summary.unlocked})
            </TabsTrigger>
            <TabsTrigger value="blocked" className="text-xs">
              Blocked ({status.summary.blocked})
            </TabsTrigger>
            <TabsTrigger value="all" className="text-xs">
              All ({status.summary.total})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="active" className="space-y-3">
            {status.active_modules.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No active modules. Activate some to get started!</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {status.active_modules.map((module) => (
                  <ModuleCard
                    key={module.module_id}
                    module={module}
                    onActivate={handleActivate}
                    onDeactivate={handleDeactivate}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="ready" className="space-y-3">
            {status.unlocked_modules.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">All available modules are active!</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {status.unlocked_modules.map((module) => (
                  <ModuleCard
                    key={module.module_id}
                    module={module}
                    onActivate={handleActivate}
                    onDeactivate={handleDeactivate}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="blocked" className="space-y-3">
            {status.blocked_modules.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No blocked modules. Great progress!</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {status.blocked_modules.map((module) => (
                  <ModuleCard
                    key={module.module_id}
                    module={module}
                    onActivate={handleActivate}
                    onDeactivate={handleDeactivate}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="all" className="space-y-2">
            {status.all_modules.map((module) => (
              <ModuleCard
                key={module.module_id}
                module={module}
                onActivate={handleActivate}
                onDeactivate={handleDeactivate}
                compact
              />
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

export { ModuleCard };
