/**
 * Universal Inventory - Expression Phase
 * =======================================
 * Displays the creator's assets, offers, content, workflows, and tasks.
 * Pulls data from user_system_profiles and presents it in an organized view.
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import {
  Package, ShoppingBag, FileText, Workflow, CheckSquare,
  ArrowLeft, Plus, Search, Filter, Grid3X3, List,
  RefreshCw, AlertCircle, Sparkles, TrendingUp, Target,
  Eye, Clock, CheckCircle2, XCircle, Pause, MoreHorizontal,
  ChevronRight, Layers, Box, Zap
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// ============== INVENTORY CATEGORY CONFIG ==============
const INVENTORY_CATEGORIES = {
  assets: {
    id: "assets",
    label: "Assets",
    icon: Package,
    color: "text-blue-500",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    description: "Your foundational resources and tools"
  },
  offers: {
    id: "offers",
    label: "Offers",
    icon: ShoppingBag,
    color: "text-emerald-500",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    description: "Products and services you provide"
  },
  content: {
    id: "content",
    label: "Content",
    icon: FileText,
    color: "text-purple-500",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    description: "Your creative output and media"
  },
  workflows: {
    id: "workflows",
    label: "Workflows",
    icon: Workflow,
    color: "text-amber-500",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    description: "Automated processes and systems"
  },
  tasks: {
    id: "tasks",
    label: "Tasks",
    icon: CheckSquare,
    color: "text-rose-500",
    bgColor: "bg-rose-50",
    borderColor: "border-rose-200",
    description: "Action items and to-dos"
  }
};

// ============== STATUS BADGE ==============
const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { label: "Active", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
    inactive: { label: "Inactive", color: "bg-slate-100 text-slate-600", icon: Pause },
    draft: { label: "Draft", color: "bg-amber-100 text-amber-700", icon: Clock },
    published: { label: "Published", color: "bg-blue-100 text-blue-700", icon: Eye },
    archived: { label: "Archived", color: "bg-slate-100 text-slate-500", icon: XCircle },
    pending: { label: "Pending", color: "bg-purple-100 text-purple-700", icon: Clock },
    completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
    in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700", icon: TrendingUp }
  };

  const config = statusConfig[status] || statusConfig.draft;
  const Icon = config.icon;

  return (
    <Badge className={`${config.color} flex items-center gap-1`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  );
};

// ============== INVENTORY ITEM CARD ==============
const InventoryItemCard = ({ item, category, onClick }) => {
  const categoryConfig = INVENTORY_CATEGORIES[category];
  const Icon = categoryConfig?.icon || Package;

  return (
    <Card 
      className={`border ${categoryConfig?.borderColor || 'border-slate-200'} hover:shadow-md transition-all cursor-pointer group`}
      onClick={onClick}
      data-testid={`inventory-item-${item.id}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className={`p-2 rounded-lg ${categoryConfig?.bgColor || 'bg-slate-50'}`}>
            <Icon className={`w-5 h-5 ${categoryConfig?.color || 'text-slate-500'}`} />
          </div>
          <StatusBadge status={item.status || 'draft'} />
        </div>
        
        <h4 className="font-medium text-slate-900 mt-3 group-hover:text-blue-600 transition-colors">
          {item.name || item.title || 'Untitled'}
        </h4>
        
        {item.description && (
          <p className="text-sm text-slate-500 mt-1 line-clamp-2">
            {item.description}
          </p>
        )}

        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {item.created_at && (
              <span>Created {new Date(item.created_at).toLocaleDateString()}</span>
            )}
          </div>
          <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
        </div>
      </CardContent>
    </Card>
  );
};

// ============== INVENTORY LIST ITEM ==============
const InventoryListItem = ({ item, category, onClick }) => {
  const categoryConfig = INVENTORY_CATEGORIES[category];
  const Icon = categoryConfig?.icon || Package;

  return (
    <div 
      className="flex items-center gap-4 p-3 bg-white rounded-lg border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all cursor-pointer group"
      onClick={onClick}
      data-testid={`inventory-list-item-${item.id}`}
    >
      <div className={`p-2 rounded-lg ${categoryConfig?.bgColor || 'bg-slate-50'}`}>
        <Icon className={`w-4 h-4 ${categoryConfig?.color || 'text-slate-500'}`} />
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-slate-900 truncate group-hover:text-blue-600 transition-colors">
          {item.name || item.title || 'Untitled'}
        </h4>
        {item.description && (
          <p className="text-xs text-slate-500 truncate">{item.description}</p>
        )}
      </div>

      <StatusBadge status={item.status || 'draft'} />
      
      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors flex-shrink-0" />
    </div>
  );
};

// ============== EMPTY STATE ==============
const EmptyState = ({ category, onAdd }) => {
  const config = INVENTORY_CATEGORIES[category];
  const Icon = config?.icon || Package;

  return (
    <div className="text-center py-12">
      <div className={`w-16 h-16 rounded-full ${config?.bgColor || 'bg-slate-50'} flex items-center justify-center mx-auto mb-4`}>
        <Icon className={`w-8 h-8 ${config?.color || 'text-slate-400'}`} />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-2">No {config?.label || 'Items'} Yet</h3>
      <p className="text-sm text-slate-500 mb-4 max-w-sm mx-auto">
        {config?.description || 'Start building your inventory by adding your first item.'}
      </p>
      <Button onClick={onAdd} className="bg-slate-900 hover:bg-slate-800">
        <Plus className="w-4 h-4 mr-2" />
        Add {config?.label?.slice(0, -1) || 'Item'}
      </Button>
    </div>
  );
};

// ============== CATEGORY STATS ==============
const CategoryStats = ({ items }) => {
  const stats = Object.entries(INVENTORY_CATEGORIES).map(([key, config]) => {
    const categoryItems = items[key] || [];
    return {
      ...config,
      count: categoryItems.length,
      active: categoryItems.filter(i => i.status === 'active' || i.status === 'published').length
    };
  });

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.id} className="border-0 shadow-sm">
            <CardContent className="p-4 text-center">
              <Icon className={`w-5 h-5 mx-auto mb-2 ${stat.color}`} />
              <p className="text-2xl font-bold text-slate-900">{stat.count}</p>
              <p className="text-xs text-slate-500">{stat.label}</p>
              {stat.active > 0 && (
                <p className="text-xs text-emerald-600 mt-1">{stat.active} active</p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

// ============== MAIN INVENTORY COMPONENT ==============
export default function UniversalInventory({ token }) {
  const [inventoryData, setInventoryData] = useState({
    assets: [],
    offers: [],
    content: [],
    workflows: [],
    tasks: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState("assets");
  const [viewMode, setViewMode] = useState("grid"); // grid or list
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();

  // Fetch inventory data from user_system_profiles
  const fetchInventory = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch system profile which contains user data
      const res = await fetch(`${BACKEND_URL}/api/system/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error("Failed to fetch inventory data");
      }

      const profile = await res.json();
      
      // Transform profile data into inventory categories
      // This maps existing system data to inventory structure
      const transformedInventory = transformProfileToInventory(profile);
      setInventoryData(transformedInventory);
      
    } catch (err) {
      setError(err.message);
      // Use placeholder data if fetch fails
      setInventoryData(generatePlaceholderInventory());
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchInventory();
    }
  }, [token, fetchInventory]);

  // Transform system profile to inventory structure
  const transformProfileToInventory = (profile) => {
    const assets = [];
    const offers = [];
    const content = [];
    const workflows = [];
    const tasks = [];

    // Map assets_already_have to Assets
    const assetMap = {
      social_media_accounts: { name: "Social Media Accounts", description: "Your connected social platforms" },
      existing_audience: { name: "Existing Audience", description: "Your current follower base" },
      offers_products: { name: "Products/Services", description: "Your existing offerings" },
      brand_identity: { name: "Brand Identity", description: "Your visual and verbal brand" },
      content_system: { name: "Content System", description: "Your content creation setup" }
    };

    if (profile.intake_data?.starting_point?.assets_already_have) {
      profile.intake_data.starting_point.assets_already_have.forEach((asset, idx) => {
        const assetInfo = assetMap[asset] || { name: asset, description: "" };
        assets.push({
          id: `asset-${idx}`,
          name: assetInfo.name,
          description: assetInfo.description,
          status: "active",
          type: asset,
          created_at: profile.created_at || new Date().toISOString()
        });
      });
    }

    // Map active engines to Workflows
    if (profile.active_engines) {
      const engineNames = {
        business_engine: "Business Engine Workflow",
        engagement_engine: "Engagement Engine Workflow",
        role_engine: "Role Engine Workflow",
        income_engine: "Income Engine Workflow"
      };

      profile.active_engines.forEach((engine, idx) => {
        workflows.push({
          id: `workflow-${idx}`,
          name: engineNames[engine] || engine,
          description: `Automated workflow for ${engine.replace(/_/g, ' ')}`,
          status: "active",
          type: "engine_workflow",
          created_at: profile.created_at || new Date().toISOString()
        });
      });
    }

    // Map unlocked modules to Tasks (suggested actions)
    if (profile.unlocked_modules) {
      profile.unlocked_modules.slice(0, 5).forEach((module, idx) => {
        tasks.push({
          id: `task-${idx}`,
          name: `Complete ${module.replace(/_/g, ' ')}`,
          description: `Work through the ${module.replace(/_/g, ' ')} module`,
          status: idx === 0 ? "in_progress" : "pending",
          type: "module_task",
          module_id: module,
          created_at: profile.created_at || new Date().toISOString()
        });
      });
    }

    // Generate placeholder offers and content based on track
    if (profile.track === "creator_track" || profile.track === "hybrid_track") {
      content.push({
        id: "content-placeholder-1",
        name: "Content Strategy Document",
        description: "Your personalized content plan based on intake responses",
        status: "draft",
        type: "strategy",
        created_at: new Date().toISOString()
      });
    }

    if (profile.track === "business_track" || profile.track === "hybrid_track") {
      offers.push({
        id: "offer-placeholder-1",
        name: "Core Offer Framework",
        description: "Your primary offer structure awaiting definition",
        status: "draft",
        type: "framework",
        created_at: new Date().toISOString()
      });
    }

    return { assets, offers, content, workflows, tasks };
  };

  // Generate placeholder inventory for demo/empty states
  const generatePlaceholderInventory = () => ({
    assets: [
      { id: "asset-1", name: "Brand Guidelines", description: "Your visual identity system", status: "active", created_at: new Date().toISOString() },
      { id: "asset-2", name: "Content Library", description: "Repository of reusable content", status: "draft", created_at: new Date().toISOString() }
    ],
    offers: [
      { id: "offer-1", name: "Core Service Package", description: "Your primary offering", status: "draft", created_at: new Date().toISOString() }
    ],
    content: [
      { id: "content-1", name: "Welcome Sequence", description: "Onboarding email series", status: "draft", created_at: new Date().toISOString() }
    ],
    workflows: [
      { id: "workflow-1", name: "Client Onboarding", description: "Automated client welcome process", status: "active", created_at: new Date().toISOString() }
    ],
    tasks: [
      { id: "task-1", name: "Define Brand Voice", description: "Document your unique communication style", status: "pending", created_at: new Date().toISOString() },
      { id: "task-2", name: "Set Up Content Calendar", description: "Plan your content schedule", status: "pending", created_at: new Date().toISOString() }
    ]
  });

  // Filter items by search query
  const getFilteredItems = (category) => {
    const items = inventoryData[category] || [];
    if (!searchQuery) return items;
    
    return items.filter(item => 
      (item.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description || '').toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const currentItems = getFilteredItems(activeCategory);
  const currentCategory = INVENTORY_CATEGORIES[activeCategory];
  const CategoryIcon = currentCategory?.icon || Package;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-slate-400" />
          <p className="text-slate-500 mt-3">Loading Inventory...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="inventory-page">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate("/command-center")}
              className="text-slate-600"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Command Center
            </Button>
          </div>
          <Button variant="outline" size="sm" onClick={fetchInventory}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Title Section */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl">
            <Layers className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Universal Inventory</h1>
            <p className="text-sm text-slate-500">Everything you've built, organized and accessible</p>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="mb-6">
          <CategoryStats items={inventoryData} />
        </div>

        {/* Search and View Controls */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search inventory..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="inventory-search"
            />
          </div>
          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("grid")}
              className={viewMode === "grid" ? "bg-white shadow-sm" : ""}
            >
              <Grid3X3 className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
              className={viewMode === "list" ? "bg-white shadow-sm" : ""}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="mb-6 bg-white border border-slate-200">
            {Object.entries(INVENTORY_CATEGORIES).map(([key, config]) => {
              const Icon = config.icon;
              const count = (inventoryData[key] || []).length;
              return (
                <TabsTrigger 
                  key={key} 
                  value={key}
                  className="flex items-center gap-2 data-[state=active]:bg-slate-100"
                  data-testid={`tab-${key}`}
                >
                  <Icon className={`w-4 h-4 ${config.color}`} />
                  {config.label}
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {count}
                  </Badge>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* Tab Content */}
          {Object.keys(INVENTORY_CATEGORIES).map((category) => (
            <TabsContent key={category} value={category}>
              {error && (
                <Card className="border-amber-200 bg-amber-50 mb-4">
                  <CardContent className="p-4 flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-amber-500" />
                    <p className="text-sm text-amber-700">
                      Showing placeholder data. {error}
                    </p>
                  </CardContent>
                </Card>
              )}

              {currentItems.length === 0 ? (
                <EmptyState 
                  category={category} 
                  onAdd={() => console.log(`Add ${category}`)} 
                />
              ) : viewMode === "grid" ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {currentItems.map((item) => (
                    <InventoryItemCard
                      key={item.id}
                      item={item}
                      category={category}
                      onClick={() => console.log("View item:", item.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {currentItems.map((item) => (
                    <InventoryListItem
                      key={item.id}
                      item={item}
                      category={category}
                      onClick={() => console.log("View item:", item.id)}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}

// ============== INVENTORY QUICK ACCESS WIDGET ==============
export function InventoryWidget({ inventoryData, onClick }) {
  const totalItems = Object.values(inventoryData || {}).reduce(
    (sum, items) => sum + (items?.length || 0), 
    0
  );

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-3 bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all group w-full"
      data-testid="inventory-widget"
    >
      <div className="p-2 bg-slate-100 rounded-lg group-hover:bg-slate-200 transition-colors">
        <Layers className="w-5 h-5 text-slate-600" />
      </div>
      <div className="text-left flex-1">
        <p className="text-sm font-medium text-slate-900">Universal Inventory</p>
        <p className="text-xs text-slate-500">{totalItems} items across all categories</p>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
    </button>
  );
}
