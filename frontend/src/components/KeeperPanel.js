/**
 * Keeper Panel - Expression Phase (Enhanced)
 * ==========================================
 * The Keeper is the user's guide and system overseer.
 * Enhanced with refined styling and micro-interactions.
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import {
  Eye, Shield, Compass, Sparkles, Activity,
  CheckCircle2, AlertCircle, ArrowRight, RefreshCw,
  Lightbulb, Target, Zap, Heart, Star, TrendingUp,
  ChevronDown, ChevronUp
} from "lucide-react";

// ============== CUSTOM CSS STYLES ==============
const pulseKeyframes = `
  @keyframes keeper-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.05); opacity: 0.8; }
  }
  @keyframes keeper-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(251, 191, 36, 0.3); }
    50% { box-shadow: 0 0 30px rgba(251, 191, 36, 0.5); }
  }
  @keyframes insight-slide {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
  }
`;

// ============== KEEPER AVATAR ==============
const KeeperAvatar = ({ size = "md", isActive = true }) => {
  const sizeClasses = {
    sm: "w-10 h-10",
    md: "w-16 h-16",
    lg: "w-24 h-24"
  };

  const iconSizes = {
    sm: "w-5 h-5",
    md: "w-8 h-8",
    lg: "w-12 h-12"
  };

  return (
    <div className={`${sizeClasses[size]} relative group`}>
      <style>{pulseKeyframes}</style>
      
      {/* Outer animated ring */}
      <div 
        className="absolute inset-0 rounded-full bg-gradient-to-br from-amber-400 via-orange-400 to-amber-500"
        style={{ 
          animation: isActive ? "keeper-glow 3s ease-in-out infinite" : "none",
          opacity: 0.3
        }}
      />
      
      {/* Inner gradient ring */}
      <div className="absolute inset-0.5 rounded-full bg-gradient-to-br from-amber-400/40 via-purple-400/30 to-emerald-400/40 animate-pulse" />
      
      {/* Main avatar container */}
      <div className="absolute inset-1.5 rounded-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center border border-amber-500/50 overflow-hidden">
        {/* Inner glow effect */}
        <div className="absolute inset-0 bg-gradient-to-t from-amber-500/20 to-transparent" />
        <Eye className={`${iconSizes[size]} text-amber-400 relative z-10 group-hover:scale-110 transition-transform duration-300`} />
      </div>
      
      {/* Status indicator with pulse */}
      <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4">
        <div className="absolute inset-0 bg-emerald-400 rounded-full animate-ping opacity-75" />
        <div className="absolute inset-0 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center">
          <Sparkles className="w-2.5 h-2.5 text-white" />
        </div>
      </div>
    </div>
  );
};

// ============== ANIMATED PROGRESS RING ==============
const ProgressRing = ({ progress, size = 60, strokeWidth = 6 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-slate-700"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#progress-gradient)"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: offset,
            transition: "stroke-dashoffset 1s ease-out"
          }}
        />
        <defs>
          <linearGradient id="progress-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="50%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold text-white">{progress}%</span>
      </div>
    </div>
  );
};

// ============== KEEPER INSIGHT CARD ==============
const KeeperInsightCard = ({ insight, type = "observation", index = 0 }) => {
  const typeConfig = {
    observation: {
      icon: Eye,
      bgColor: "bg-slate-50",
      borderColor: "border-slate-200",
      iconColor: "text-slate-500",
      iconBg: "bg-slate-100"
    },
    guidance: {
      icon: Compass,
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      iconColor: "text-blue-500",
      iconBg: "bg-blue-100"
    },
    warning: {
      icon: AlertCircle,
      bgColor: "bg-amber-50",
      borderColor: "border-amber-200",
      iconColor: "text-amber-500",
      iconBg: "bg-amber-100"
    },
    celebration: {
      icon: Star,
      bgColor: "bg-purple-50",
      borderColor: "border-purple-200",
      iconColor: "text-purple-500",
      iconBg: "bg-purple-100"
    },
    action: {
      icon: Zap,
      bgColor: "bg-emerald-50",
      borderColor: "border-emerald-200",
      iconColor: "text-emerald-500",
      iconBg: "bg-emerald-100"
    }
  };

  const config = typeConfig[type] || typeConfig.observation;
  const Icon = config.icon;

  return (
    <div 
      className={`p-3 rounded-xl ${config.bgColor} border ${config.borderColor} hover:shadow-sm transition-all`}
      style={{ 
        animation: `insight-slide 0.3s ease-out ${index * 0.1}s both`
      }}
    >
      <style>{pulseKeyframes}</style>
      <div className="flex items-start gap-3">
        <div className={`p-1.5 rounded-lg ${config.iconBg}`}>
          <Icon className={`w-4 h-4 ${config.iconColor}`} />
        </div>
        <p className="text-sm text-slate-700 leading-relaxed">{insight}</p>
      </div>
    </div>
  );
};

// ============== HEALTH METRIC BAR ==============
const HealthMetricBar = ({ label, value, color = "emerald" }) => {
  const colorClasses = {
    emerald: "bg-emerald-500",
    blue: "bg-blue-500",
    amber: "bg-amber-500",
    purple: "bg-purple-500"
  };

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-medium">{value}%</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color]} rounded-full transition-all duration-1000`}
          style={{ width: `${value}%` }}
        />
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
    if (!systemState) return { overall: 0, engines: 0, modules: 0, progress: 0 };
    
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
      text: `You&apos;re walking the ${trackName} path. I&apos;m here to guide you through each step.`,
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
        text: `I see ${blockers.length} ${blockers.length === 1 ? "obstacle" : "obstacles"} in your path. Let&apos;s address these before moving forward.`,
        type: "warning"
      });
    }

    // Next steps insight
    if (nextSteps.length > 0) {
      insights.push({
        text: `Your next move: ${typeof nextSteps[0] === "string" ? nextSteps[0] : nextSteps[0]?.step || "Continue your current focus"}`,
        type: "action"
      });
    }

    // Progress celebration
    const progress = systemState.overall_progress || 0;
    if (progress >= 50 && progress < 75) {
      insights.push({
        text: "You&apos;ve crossed the halfway mark. The foundation is solid—now we build upward.",
        type: "celebration"
      });
    } else if (progress >= 75) {
      insights.push({
        text: "Remarkable progress. You&apos;re approaching mastery of this system.",
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
    <Card className="border-0 shadow-xl overflow-hidden" data-testid="keeper-panel">
      {/* Keeper Header */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-5">
        <div className="flex items-start gap-4">
          <KeeperAvatar size="md" isActive={true} />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-white">The Keeper</h3>
              <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 hover:bg-amber-500/30 transition-colors">
                <Shield className="w-3 h-3 mr-1" />
                Watching
              </Badge>
            </div>
            <p className="text-sm text-slate-400">
              Your guide through the Hive. I see what you&apos;ve built and what comes next.
            </p>
          </div>
          
          {/* Progress Ring */}
          <ProgressRing progress={health.overall} size={64} strokeWidth={5} />
        </div>

        {/* Health Metrics */}
        <div className="mt-5 p-4 bg-slate-800/60 rounded-xl border border-slate-700/50">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">System Pulse</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="space-y-3">
            <HealthMetricBar label="Engines" value={health.engines} color="amber" />
            <HealthMetricBar label="Modules" value={health.modules} color="blue" />
            <HealthMetricBar label="Progress" value={health.progress} color="emerald" />
          </div>
        </div>
      </div>

      {/* Keeper Insights */}
      <CardContent className="p-5 bg-white">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <div className="p-1 bg-amber-100 rounded-lg">
              <Lightbulb className="w-4 h-4 text-amber-600" />
            </div>
            Keeper&apos;s Observations
          </h4>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="text-xs hover:bg-slate-100"
          >
            {expanded ? (
              <>
                <ChevronUp className="w-4 h-4 mr-1" />
                Less
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-1" />
                More
              </>
            )}
          </Button>
        </div>

        <ScrollArea className={expanded ? "h-[320px]" : "h-[200px]"}>
          <div className="space-y-3 pr-2">
            {insights.map((insight, idx) => (
              <KeeperInsightCard 
                key={idx} 
                insight={insight.text.replace(/&apos;/g, "'")} 
                type={insight.type}
                index={idx}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Action Button */}
        {nextSteps.length > 0 && (
          <div className="mt-5 pt-4 border-t border-slate-100">
            <Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-md hover:shadow-lg transition-all" size="default">
              <Zap className="w-4 h-4 mr-2" />
              Take Next Step
              <ArrowRight className="w-4 h-4 ml-2" />
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
      className="flex items-center gap-3 p-3 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl hover:from-slate-800 hover:to-slate-700 transition-all group shadow-md hover:shadow-lg w-full"
      data-testid="keeper-widget"
    >
      <KeeperAvatar size="sm" isActive={true} />
      <div className="text-left flex-1">
        <p className="text-sm font-medium text-white group-hover:text-amber-300 transition-colors">
          The Keeper
        </p>
        <p className="text-xs text-slate-400">
          {enginesActive} engines • {progress}% complete
        </p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition-all" />
    </button>
  );
}
