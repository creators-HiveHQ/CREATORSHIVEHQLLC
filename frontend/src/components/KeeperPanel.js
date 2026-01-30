/**
 * Keeper Panel - Expression Phase
 * ================================
 * The Keeper is the user's guide and system overseer.
 * Displays insights, system state, and guidance from the Keeper's perspective.
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Eye, Shield, Compass, Sparkles, Activity,
  CheckCircle2, AlertCircle, ArrowRight, RefreshCw,
  Lightbulb, Target, Zap, Heart, Star
} from "lucide-react";

// ============== KEEPER AVATAR ==============
const KeeperAvatar = ({ size = "md" }) => {
  const sizeClasses = {
    sm: "w-10 h-10",
    md: "w-16 h-16",
    lg: "w-24 h-24"
  };

  return (
    <div className={`${sizeClasses[size]} relative`}>
      {/* Outer glow ring */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-amber-400/30 via-purple-400/30 to-emerald-400/30 animate-pulse" />
      
      {/* Main avatar container */}
      <div className="absolute inset-1 rounded-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center border-2 border-amber-500/50">
        <Eye className="w-1/2 h-1/2 text-amber-400" />
      </div>
      
      {/* Status indicator */}
      <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center">
        <Sparkles className="w-2.5 h-2.5 text-white" />
      </div>
    </div>
  );
};

// ============== SYSTEM PULSE INDICATOR ==============
const SystemPulse = ({ health, label }) => {
  const getHealthColor = (h) => {
    if (h >= 80) return "bg-emerald-500";
    if (h >= 60) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-2">
      <div className="relative w-3 h-3">
        <div className={`absolute inset-0 rounded-full ${getHealthColor(health)} animate-ping opacity-75`} />
        <div className={`absolute inset-0 rounded-full ${getHealthColor(health)}`} />
      </div>
      <span className="text-sm text-slate-600">{label}</span>
      <span className="text-sm font-medium text-slate-900">{health}%</span>
    </div>
  );
};

// ============== KEEPER INSIGHT CARD ==============
const KeeperInsightCard = ({ insight, type = "observation" }) => {
  const typeConfig = {
    observation: {
      icon: Eye,
      bgColor: "bg-slate-50",
      borderColor: "border-slate-200",
      iconColor: "text-slate-500"
    },
    guidance: {
      icon: Compass,
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      iconColor: "text-blue-500"
    },
    warning: {
      icon: AlertCircle,
      bgColor: "bg-amber-50",
      borderColor: "border-amber-200",
      iconColor: "text-amber-500"
    },
    celebration: {
      icon: Star,
      bgColor: "bg-purple-50",
      borderColor: "border-purple-200",
      iconColor: "text-purple-500"
    },
    action: {
      icon: Zap,
      bgColor: "bg-emerald-50",
      borderColor: "border-emerald-200",
      iconColor: "text-emerald-500"
    }
  };

  const config = typeConfig[type] || typeConfig.observation;
  const Icon = config.icon;

  return (
    <div className={`p-3 rounded-lg ${config.bgColor} border ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
        <p className="text-sm text-slate-700">{insight}</p>
      </div>
    </div>
  );
};

// ============== MAIN KEEPER PANEL ==============
export default function KeeperPanel({ 
  systemState, 
  engines = [], 
  modules = [], 
  nextSteps = [],
  blockers = [],
  loading = false 
}) {
  const [expanded, setExpanded] = useState(false);

  // Calculate system health from engines and modules
  const calculateSystemHealth = () => {
    if (!systemState) return { overall: 0, engines: 0, modules: 0 };
    
    const enginesActive = systemState.engines_active || 0;
    const totalEngines = 4;
    const engineHealth = Math.round((enginesActive / totalEngines) * 100);
    
    const modulesUnlocked = systemState.modules_unlocked || 0;
    const totalModules = 18;
    const moduleHealth = Math.round((modulesUnlocked / totalModules) * 100);
    
    const progress = systemState.overall_progress || 0;
    
    return {
      overall: Math.round((engineHealth + moduleHealth + progress) / 3),
      engines: engineHealth,
      modules: moduleHealth,
      progress
    };
  };

  const health = calculateSystemHealth();

  // Generate Keeper insights based on system state
  const generateKeeperInsights = () => {
    const insights = [];
    
    if (!systemState) {
      return [{ text: "Awaiting system initialization...", type: "observation" }];
    }

    // Track-based insight
    const trackNames = {
      creator_track: "Creator",
      business_track: "Business",
      hybrid_track: "Hybrid"
    };
    const trackName = trackNames[systemState.track] || "your chosen";
    insights.push({
      text: `You're walking the ${trackName} path. I'm here to guide you through each step.`,
      type: "observation"
    });

    // Engine insights
    const enginesActive = systemState.engines_active || 0;
    if (enginesActive === 0) {
      insights.push({
        text: "No engines are active yet. Complete the intake form to ignite your first engine.",
        type: "guidance"
      });
    } else if (enginesActive === 1) {
      insights.push({
        text: "Your first engine is online. Focus here before expanding to others.",
        type: "guidance"
      });
    } else if (enginesActive >= 3) {
      insights.push({
        text: `${enginesActive} engines running in harmony. Your system is gaining strength.`,
        type: "celebration"
      });
    }

    // Blocker insights
    if (blockers.length > 0) {
      insights.push({
        text: `I see ${blockers.length} ${blockers.length === 1 ? 'obstacle' : 'obstacles'} in your path. Let's address these before moving forward.`,
        type: "warning"
      });
    }

    // Next steps insight
    if (nextSteps.length > 0) {
      insights.push({
        text: `Your next move: ${typeof nextSteps[0] === 'string' ? nextSteps[0] : nextSteps[0]?.step || 'Continue your current focus'}`,
        type: "action"
      });
    }

    // Progress celebration
    const progress = systemState.overall_progress || 0;
    if (progress >= 50 && progress < 75) {
      insights.push({
        text: "You've crossed the halfway mark. The foundation is solid—now we build upward.",
        type: "celebration"
      });
    } else if (progress >= 75) {
      insights.push({
        text: "Remarkable progress. You're approaching mastery of this system.",
        type: "celebration"
      });
    }

    return insights;
  };

  const insights = generateKeeperInsights();

  if (loading) {
    return (
      <Card className="border-0 shadow-lg bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <CardContent className="p-6 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-amber-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-lg overflow-hidden" data-testid="keeper-panel">
      {/* Keeper Header */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
        <div className="flex items-start gap-4">
          <KeeperAvatar size="md" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">The Keeper</h3>
              <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30">
                <Shield className="w-3 h-3 mr-1" />
                Watching
              </Badge>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Your guide through the Hive. I see what you&apos;ve built and what comes next.
            </p>
          </div>
        </div>

        {/* System Pulse */}
        <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 uppercase tracking-wider">System Pulse</span>
            <span className="text-lg font-bold text-white">{health.overall}%</span>
          </div>
          <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-amber-500 via-emerald-500 to-purple-500 transition-all duration-1000"
              style={{ width: `${health.overall}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-500">
            <span>Engines: {health.engines}%</span>
            <span>Modules: {health.modules}%</span>
            <span>Progress: {health.progress}%</span>
          </div>
        </div>
      </div>

      {/* Keeper Insights */}
      <CardContent className="p-4 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            Keeper's Observations
          </h4>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="text-xs"
          >
            {expanded ? "Show Less" : "Show More"}
          </Button>
        </div>

        <ScrollArea className={expanded ? "h-[300px]" : "h-[180px]"}>
          <div className="space-y-2">
            {insights.map((insight, idx) => (
              <KeeperInsightCard 
                key={idx} 
                insight={insight.text} 
                type={insight.type}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Quick Actions */}
        {nextSteps.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <Button className="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white" size="sm">
              <ArrowRight className="w-4 h-4 mr-2" />
              Take Next Step
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============== COMPACT KEEPER WIDGET ==============
export function KeeperWidget({ systemState, onClick }) {
  const enginesActive = systemState?.engines_active || 0;
  const progress = systemState?.overall_progress || 0;

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-3 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl hover:from-slate-800 hover:to-slate-700 transition-all group"
      data-testid="keeper-widget"
    >
      <KeeperAvatar size="sm" />
      <div className="text-left">
        <p className="text-sm font-medium text-white group-hover:text-amber-300 transition-colors">
          The Keeper
        </p>
        <p className="text-xs text-slate-400">
          {enginesActive} engines • {progress}% complete
        </p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 transition-colors" />
    </button>
  );
}
