/**
 * Creators Hive HQ - Engine Status Panel
 * =======================================
 * UI component for displaying engine status on the dashboard.
 * Part of Phase 3: Engine Restoration.
 * 
 * Displays:
 * - Engine status (active/pending/blocked/inactive)
 * - Progress indicators
 * - Input/output counts
 * - Blockers
 * - Health indicators
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Briefcase, Users, Target, DollarSign,
  CheckCircle2, AlertCircle, Clock, XCircle,
  ChevronRight, Activity, Zap, RefreshCw
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Engine icons mapping
const ENGINE_ICONS = {
  business_engine: Briefcase,
  engagement_engine: Users,
  role_engine: Target,
  income_engine: DollarSign
};

// Engine colors mapping
const ENGINE_COLORS = {
  business_engine: { bg: "bg-blue-500", text: "text-blue-500", light: "bg-blue-50" },
  engagement_engine: { bg: "bg-purple-500", text: "text-purple-500", light: "bg-purple-50" },
  role_engine: { bg: "bg-amber-500", text: "text-amber-500", light: "bg-amber-50" },
  income_engine: { bg: "bg-emerald-500", text: "text-emerald-500", light: "bg-emerald-50" }
};

// Status badge variants
const STATUS_CONFIG = {
  active: { icon: CheckCircle2, color: "bg-emerald-100 text-emerald-700", label: "Active" },
  pending: { icon: Clock, color: "bg-amber-100 text-amber-700", label: "Pending" },
  blocked: { icon: XCircle, color: "bg-red-100 text-red-700", label: "Blocked" },
  inactive: { icon: AlertCircle, color: "bg-slate-100 text-slate-500", label: "Inactive" }
};

// Single Engine Card
const EngineCard = ({ engine, onViewDetails }) => {
  const Icon = ENGINE_ICONS[engine.engine_id] || Activity;
  const colors = ENGINE_COLORS[engine.engine_id] || { bg: "bg-slate-500", text: "text-slate-500", light: "bg-slate-50" };
  const statusConfig = STATUS_CONFIG[engine.status] || STATUS_CONFIG.inactive;
  const StatusIcon = statusConfig.icon;

  return (
    <Card className="border border-slate-200 hover:border-slate-300 transition-all">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2 rounded-lg ${colors.light}`}>
            <Icon className={`w-5 h-5 ${colors.text}`} />
          </div>
          <Badge className={`${statusConfig.color} text-xs`}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {statusConfig.label}
          </Badge>
        </div>

        <h4 className="font-semibold text-slate-900 mb-1">{engine.display_name}</h4>
        <p className="text-xs text-slate-500 mb-3 line-clamp-2">{engine.description}</p>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Progress</span>
            <span>{Math.round(engine.progress)}%</span>
          </div>
          <Progress value={engine.progress} className="h-2" />
        </div>

        {/* Stats */}
        <div className="flex gap-4 text-xs text-slate-600 mb-3">
          <div className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            <span>{engine.inputs_received} inputs</span>
          </div>
          <div className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            <span>{engine.outputs_generated} outputs</span>
          </div>
        </div>

        {/* Blockers */}
        {engine.blockers && engine.blockers.length > 0 && (
          <div className="bg-red-50 rounded p-2 mb-3">
            <p className="text-xs text-red-700 font-medium">Blockers:</p>
            <ul className="text-xs text-red-600 mt-1">
              {engine.blockers.map((blocker, idx) => (
                <li key={idx}>• {blocker}</li>
              ))}
            </ul>
          </div>
        )}

        {/* View Details Button */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-between text-slate-600 hover:text-slate-900"
          onClick={() => onViewDetails(engine.engine_id)}
          data-testid={`view-engine-${engine.engine_id}`}
        >
          View Details
          <ChevronRight className="w-4 h-4" />
        </Button>
      </CardContent>
    </Card>
  );
};

// Engine Details Modal/Panel
const EngineDetailsPanel = ({ engineId, token, onClose }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/engines/${engineId}/details`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to fetch engine details");
        const data = await res.json();
        setDetails(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    if (engineId && token) fetchDetails();
  }, [engineId, token]);

  if (loading) {
    return (
      <div className="p-6 text-center">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto text-slate-400" />
        <p className="text-sm text-slate-500 mt-2">Loading engine details...</p>
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="p-6 text-center">
        <AlertCircle className="w-6 h-6 mx-auto text-red-400" />
        <p className="text-sm text-red-500 mt-2">{error || "Failed to load details"}</p>
      </div>
    );
  }

  const Icon = ENGINE_ICONS[engineId] || Activity;
  const colors = ENGINE_COLORS[engineId] || { bg: "bg-slate-500", text: "text-slate-500", light: "bg-slate-50" };

  return (
    <div className="p-6 max-h-[70vh] overflow-y-auto">
      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <div className={`p-3 rounded-lg ${colors.light}`}>
          <Icon className={`w-6 h-6 ${colors.text}`} />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-bold text-slate-900">{details.display_name}</h3>
          <p className="text-sm text-slate-500">{details.description}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>×</Button>
      </div>

      {/* Health Status */}
      <div className={`p-4 rounded-lg mb-4 ${
        details.health.status === "good" ? "bg-emerald-50" :
        details.health.status === "needs_attention" ? "bg-amber-50" :
        details.health.status === "blocked" ? "bg-red-50" : "bg-slate-50"
      }`}>
        <div className="flex items-center gap-2 mb-2">
          {details.health.status === "good" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          ) : details.health.status === "blocked" ? (
            <XCircle className="w-5 h-5 text-red-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-amber-600" />
          )}
          <span className="font-medium capitalize">{details.health.status.replace("_", " ")}</span>
        </div>
        {details.health.notes.length > 0 && (
          <ul className="text-sm text-slate-600 space-y-1">
            {details.health.notes.map((note, idx) => (
              <li key={idx}>• {note}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="font-medium text-slate-700">Progress</span>
          <span className="text-slate-500">{Math.round(details.state.progress)}%</span>
        </div>
        <Progress value={details.state.progress} className="h-3" />
      </div>

      {/* Inputs */}
      <div className="mb-4">
        <h4 className="font-medium text-slate-700 mb-2">Inputs ({details.state.inputs_received} received)</h4>
        <div className="space-y-1">
          {details.inputs.completion.map((input, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              {input.received ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
              )}
              <span className={input.received ? "text-slate-700" : "text-slate-400"}>
                {input.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Outputs */}
      <div className="mb-4">
        <h4 className="font-medium text-slate-700 mb-2">Outputs ({details.state.outputs_generated} generated)</h4>
        <div className="space-y-1">
          {details.outputs.availability.map((output, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              {output.generated ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-slate-300" />
              )}
              <span className={output.generated ? "text-slate-700" : "text-slate-400"}>
                {output.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Rules */}
      <div className="mb-4">
        <h4 className="font-medium text-slate-700 mb-2">Rules</h4>
        <div className="space-y-2">
          {details.rules.status.map((rule, idx) => (
            <div key={idx} className={`p-2 rounded text-sm ${
              rule.status === "met" ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-600"
            }`}>
              {rule.rule}
            </div>
          ))}
        </div>
      </div>

      {/* Dependencies */}
      {details.dependencies.required.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-slate-700 mb-2">Dependencies</h4>
          <div className="flex flex-wrap gap-2">
            {details.dependencies.display_names.map((dep, idx) => (
              <Badge
                key={idx}
                className={details.dependencies.met ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}
              >
                {dep}
              </Badge>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {details.dependencies.met ? "All dependencies met" : "Waiting for dependencies"}
          </p>
        </div>
      )}

      {/* Connected Modules */}
      <div>
        <h4 className="font-medium text-slate-700 mb-2">Connected Modules ({details.modules.count})</h4>
        <div className="flex flex-wrap gap-2">
          {details.modules.required.map((module, idx) => (
            <Badge key={idx} variant="outline" className="text-xs">
              {module.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main Engine Status Panel Component
export default function EngineStatusPanel({ token }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEngine, setSelectedEngine] = useState(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/engines/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to fetch engine status");
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

  if (loading) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-slate-400" />
          <p className="text-sm text-slate-500 mt-2">Loading engine status...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <AlertCircle className="w-6 h-6 mx-auto text-red-400" />
          <p className="text-sm text-red-500 mt-2">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={fetchStatus}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!status?.initialized) {
    return (
      <Card className="border-0 shadow-sm">
        <CardContent className="p-6 text-center">
          <Zap className="w-8 h-8 mx-auto text-slate-300 mb-3" />
          <p className="text-slate-600">Engines not initialized</p>
          <p className="text-sm text-slate-400 mt-1">Complete the intake form to activate engines</p>
          <Button
            className="mt-4"
            onClick={() => window.location.href = "/intake"}
            data-testid="go-to-intake-btn"
          >
            Go to Intake Form
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
            <Activity className="w-5 h-5" />
            Engine Status
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge className={`${
              status.overall_health === "good" ? "bg-emerald-100 text-emerald-700" :
              status.overall_health === "has_blockers" ? "bg-red-100 text-red-700" :
              "bg-amber-100 text-amber-700"
            }`}>
              {status.overall_health.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
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
          <div className="flex items-center gap-1 text-amber-600">
            <Clock className="w-4 h-4" />
            <span>{status.summary.pending} Pending</span>
          </div>
          {status.summary.blocked > 0 && (
            <div className="flex items-center gap-1 text-red-600">
              <XCircle className="w-4 h-4" />
              <span>{status.summary.blocked} Blocked</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-slate-500">
            <span>{status.summary.average_progress}% avg progress</span>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Engine Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {status.engines.map((engine) => (
            <EngineCard
              key={engine.engine_id}
              engine={engine}
              onViewDetails={setSelectedEngine}
            />
          ))}
        </div>

        {/* Engine Details Modal */}
        {selectedEngine && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl bg-white">
              <EngineDetailsPanel
                engineId={selectedEngine}
                token={token}
                onClose={() => setSelectedEngine(null)}
              />
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Export individual components for flexibility
export { EngineCard, EngineDetailsPanel };
