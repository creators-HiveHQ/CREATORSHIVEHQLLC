/**
 * Workflow Triggers - Expression Phase
 * =====================================
 * Configure automation triggers for workflows.
 * Connect tasks and engines to workflow execution.
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import {
  ArrowLeft, Zap, Plus, Trash2, Save, Clock,
  CheckSquare, Activity, Play, Pause, Settings,
  RefreshCw, AlertCircle, ChevronRight, Calendar,
  Target, Bell, Mail, Webhook
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Trigger types
const TRIGGER_TYPES = {
  manual: {
    id: "manual",
    label: "Manual",
    description: "Trigger workflow manually with a button",
    icon: Play,
    color: "text-blue-500",
    bgColor: "bg-blue-50"
  },
  scheduled: {
    id: "scheduled",
    label: "Scheduled",
    description: "Run on a schedule (daily, weekly, etc.)",
    icon: Calendar,
    color: "text-purple-500",
    bgColor: "bg-purple-50"
  },
  task_completed: {
    id: "task_completed",
    label: "Task Completed",
    description: "Trigger when a specific task is completed",
    icon: CheckSquare,
    color: "text-emerald-500",
    bgColor: "bg-emerald-50"
  },
  engine_activated: {
    id: "engine_activated",
    label: "Engine Activated",
    description: "Trigger when an engine is activated",
    icon: Activity,
    color: "text-amber-500",
    bgColor: "bg-amber-50"
  },
  webhook: {
    id: "webhook",
    label: "Webhook",
    description: "Trigger via external webhook call",
    icon: Webhook,
    color: "text-rose-500",
    bgColor: "bg-rose-50"
  },
  condition: {
    id: "condition",
    label: "Condition Met",
    description: "Trigger when a condition is satisfied",
    icon: Target,
    color: "text-slate-500",
    bgColor: "bg-slate-50"
  }
};

// Schedule options
const SCHEDULE_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "custom", label: "Custom Cron" }
];

// Engine options
const ENGINE_OPTIONS = [
  { value: "business_engine", label: "Business Engine" },
  { value: "engagement_engine", label: "Engagement Engine" },
  { value: "role_engine", label: "Role Engine" },
  { value: "income_engine", label: "Income Engine" }
];

// ============== TRIGGER CARD ==============
const TriggerCard = ({ trigger, onEdit, onDelete, onToggle }) => {
  const typeConfig = TRIGGER_TYPES[trigger.type] || TRIGGER_TYPES.manual;
  const Icon = typeConfig.icon;
  
  return (
    <Card className={`border ${trigger.enabled ? "border-emerald-200" : "border-slate-200"} transition-all`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className={`p-2 rounded-lg ${typeConfig.bgColor}`}>
              <Icon className={`w-5 h-5 ${typeConfig.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-medium text-slate-900">{trigger.name || typeConfig.label}</h4>
                <Badge className={trigger.enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}>
                  {trigger.enabled ? "Active" : "Inactive"}
                </Badge>
              </div>
              <p className="text-sm text-slate-500 mt-1">{typeConfig.description}</p>
              
              {/* Trigger-specific details */}
              {trigger.type === "scheduled" && trigger.schedule && (
                <p className="text-xs text-purple-600 mt-2 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Runs {trigger.schedule}
                </p>
              )}
              {trigger.type === "task_completed" && trigger.task_id && (
                <p className="text-xs text-emerald-600 mt-2 flex items-center gap-1">
                  <CheckSquare className="w-3 h-3" />
                  When task &quot;{trigger.task_name || trigger.task_id}&quot; completes
                </p>
              )}
              {trigger.type === "engine_activated" && trigger.engine && (
                <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  When {trigger.engine.replace(/_/g, " ")} activates
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Switch
              checked={trigger.enabled}
              onCheckedChange={() => onToggle(trigger.id)}
            />
            <Button variant="ghost" size="icon" onClick={() => onEdit(trigger)}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => onDelete(trigger.id)} className="text-red-500 hover:text-red-600">
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// ============== ADD TRIGGER FORM ==============
const AddTriggerForm = ({ onSave, onCancel, existingTrigger = null, tasks = [] }) => {
  const [triggerType, setTriggerType] = useState(existingTrigger?.type || "manual");
  const [name, setName] = useState(existingTrigger?.name || "");
  const [schedule, setSchedule] = useState(existingTrigger?.schedule || "daily");
  const [customCron, setCustomCron] = useState(existingTrigger?.cron || "");
  const [taskId, setTaskId] = useState(existingTrigger?.task_id || "");
  const [engine, setEngine] = useState(existingTrigger?.engine || "");
  const [webhookUrl, setWebhookUrl] = useState(existingTrigger?.webhook_url || "");
  const [enabled, setEnabled] = useState(existingTrigger?.enabled ?? true);
  
  const handleSave = () => {
    const trigger = {
      id: existingTrigger?.id || `trigger-${Date.now()}`,
      type: triggerType,
      name: name || TRIGGER_TYPES[triggerType]?.label,
      enabled,
      created_at: existingTrigger?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // Add type-specific fields
    if (triggerType === "scheduled") {
      trigger.schedule = schedule;
      if (schedule === "custom") {
        trigger.cron = customCron;
      }
    } else if (triggerType === "task_completed") {
      trigger.task_id = taskId;
      trigger.task_name = tasks.find(t => t.id === taskId)?.name;
    } else if (triggerType === "engine_activated") {
      trigger.engine = engine;
    } else if (triggerType === "webhook") {
      trigger.webhook_url = webhookUrl || `${BACKEND_URL}/api/workflows/trigger/${existingTrigger?.id || "new"}`;
    }
    
    onSave(trigger);
  };
  
  const typeConfig = TRIGGER_TYPES[triggerType];
  const Icon = typeConfig?.icon || Zap;
  
  return (
    <Card className="border-2 border-blue-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">
          {existingTrigger ? "Edit Trigger" : "New Trigger"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Trigger Type */}
        <div className="space-y-2">
          <Label>Trigger Type</Label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(TRIGGER_TYPES).map(([key, config]) => {
              const TypeIcon = config.icon;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setTriggerType(key)}
                  className={`
                    flex items-center gap-2 p-3 rounded-lg border-2 transition-all
                    ${triggerType === key 
                      ? "border-blue-500 bg-blue-50" 
                      : "border-slate-200 hover:border-slate-300"
                    }
                  `}
                >
                  <TypeIcon className={`w-4 h-4 ${config.color}`} />
                  <span className="text-sm font-medium">{config.label}</span>
                </button>
              );
            })}
          </div>
        </div>
        
        {/* Name */}
        <div className="space-y-2">
          <Label>Name (optional)</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={typeConfig?.label}
          />
        </div>
        
        {/* Type-specific fields */}
        {triggerType === "scheduled" && (
          <div className="space-y-2">
            <Label>Schedule</Label>
            <Select value={schedule} onValueChange={setSchedule}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SCHEDULE_OPTIONS.map(opt => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {schedule === "custom" && (
              <Input
                value={customCron}
                onChange={(e) => setCustomCron(e.target.value)}
                placeholder="Cron expression (e.g., 0 9 * * *)"
                className="mt-2"
              />
            )}
          </div>
        )}
        
        {triggerType === "task_completed" && (
          <div className="space-y-2">
            <Label>Task</Label>
            <Select value={taskId} onValueChange={setTaskId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a task" />
              </SelectTrigger>
              <SelectContent>
                {tasks.map(task => (
                  <SelectItem key={task.id} value={task.id}>{task.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        
        {triggerType === "engine_activated" && (
          <div className="space-y-2">
            <Label>Engine</Label>
            <Select value={engine} onValueChange={setEngine}>
              <SelectTrigger>
                <SelectValue placeholder="Select an engine" />
              </SelectTrigger>
              <SelectContent>
                {ENGINE_OPTIONS.map(eng => (
                  <SelectItem key={eng.value} value={eng.value}>{eng.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        
        {triggerType === "webhook" && (
          <div className="space-y-2">
            <Label>Webhook URL</Label>
            <div className="flex gap-2">
              <Input
                value={webhookUrl || `${BACKEND_URL}/api/workflows/trigger/...`}
                readOnly
                className="bg-slate-50"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => {
                  navigator.clipboard.writeText(webhookUrl || `${BACKEND_URL}/api/workflows/trigger/...`);
                  toast.success("Copied to clipboard");
                }}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-slate-500">Use this URL to trigger the workflow externally</p>
          </div>
        )}
        
        {/* Enabled Toggle */}
        <div className="flex items-center justify-between">
          <Label>Enable Trigger</Label>
          <Switch checked={enabled} onCheckedChange={setEnabled} />
        </div>
        
        <Separator />
        
        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
            <Save className="w-4 h-4 mr-2" />
            {existingTrigger ? "Update" : "Add"} Trigger
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// ============== MAIN COMPONENT ==============
export default function WorkflowTriggers({ token }) {
  const { category, itemId } = useParams();
  const navigate = useNavigate();
  
  const [workflow, setWorkflow] = useState(null);
  const [triggers, setTriggers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTrigger, setEditingTrigger] = useState(null);
  
  // Fetch workflow and tasks
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch workflow
      const workflowRes = await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!workflowRes.ok) {
        toast.error("Workflow not found");
        navigate("/inventory");
        return;
      }
      
      const workflowData = await workflowRes.json();
      setWorkflow(workflowData);
      setTriggers(workflowData.metadata?.triggers || []);
      
      // Fetch tasks
      const tasksRes = await fetch(`${BACKEND_URL}/api/inventory/tasks`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        setTasks(tasksData.items || []);
      }
      
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [token, category, itemId, navigate]);

  useEffect(() => {
    if (token && itemId) {
      fetchData();
    }
  }, [token, itemId, fetchData]);

  // Save triggers to workflow
  const saveTriggers = async (updatedTriggers) => {
    setSaving(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          metadata: {
            ...workflow?.metadata,
            triggers: updatedTriggers
          }
        })
      });
      
      if (!res.ok) throw new Error("Failed to save triggers");
      
      setTriggers(updatedTriggers);
      toast.success("Triggers saved");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Add/update trigger
  const handleSaveTrigger = (trigger) => {
    let updatedTriggers;
    if (editingTrigger) {
      updatedTriggers = triggers.map(t => t.id === trigger.id ? trigger : t);
    } else {
      updatedTriggers = [...triggers, trigger];
    }
    
    saveTriggers(updatedTriggers);
    setShowAddForm(false);
    setEditingTrigger(null);
  };

  // Delete trigger
  const handleDeleteTrigger = (triggerId) => {
    const updatedTriggers = triggers.filter(t => t.id !== triggerId);
    saveTriggers(updatedTriggers);
  };

  // Toggle trigger enabled
  const handleToggleTrigger = (triggerId) => {
    const updatedTriggers = triggers.map(t => 
      t.id === triggerId ? { ...t, enabled: !t.enabled } : t
    );
    saveTriggers(updatedTriggers);
  };

  // Edit trigger
  const handleEditTrigger = (trigger) => {
    setEditingTrigger(trigger);
    setShowAddForm(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="workflow-triggers-page">
      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate(`/inventory/${category}/${itemId}`)}
            className="text-slate-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Workflow
          </Button>
        </div>
        
        {/* Title */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Automation Triggers</h1>
            <p className="text-sm text-slate-500">
              Configure when &quot;{workflow?.name}&quot; should run
            </p>
          </div>
        </div>
        
        {/* Info Card */}
        <Card className="border-amber-200 bg-amber-50 mb-6">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-700">How Triggers Work</p>
                <p className="text-sm text-amber-600 mt-1">
                  Triggers define when your workflow automatically executes. You can set multiple triggers,
                  and any active trigger can start the workflow.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Triggers List */}
        <div className="space-y-4 mb-6">
          {triggers.length > 0 ? (
            triggers.map((trigger) => (
              <TriggerCard
                key={trigger.id}
                trigger={trigger}
                onEdit={handleEditTrigger}
                onDelete={handleDeleteTrigger}
                onToggle={handleToggleTrigger}
              />
            ))
          ) : (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center">
                <Zap className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No triggers configured yet</p>
                <p className="text-sm text-slate-400 mb-4">Add a trigger to automate this workflow</p>
              </CardContent>
            </Card>
          )}
        </div>
        
        {/* Add Trigger Form or Button */}
        {showAddForm ? (
          <AddTriggerForm
            onSave={handleSaveTrigger}
            onCancel={() => {
              setShowAddForm(false);
              setEditingTrigger(null);
            }}
            existingTrigger={editingTrigger}
            tasks={tasks}
          />
        ) : (
          <Button
            onClick={() => setShowAddForm(true)}
            className="w-full bg-slate-900 hover:bg-slate-800"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Trigger
          </Button>
        )}
      </div>
    </div>
  );
}
