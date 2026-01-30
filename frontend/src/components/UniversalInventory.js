/**
 * Universal Inventory - Expression Phase
 * =======================================
 * Displays the creator's assets, offers, content, workflows, and tasks.
 * Full CRUD operations with backend persistence.
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  Package, ShoppingBag, FileText, Workflow, CheckSquare,
  ArrowLeft, Plus, Search, Grid3X3, List,
  RefreshCw, AlertCircle, Eye, Clock, CheckCircle2, 
  XCircle, Pause, MoreHorizontal, ChevronRight, Layers,
  Edit, Trash2, TrendingUp
} from "lucide-react";
import InventoryItemModal, { DeleteConfirmModal } from "./InventoryItemModal";

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
const InventoryItemCard = ({ item, category, onEdit, onDelete, onView }) => {
  const categoryConfig = INVENTORY_CATEGORIES[category];
  const Icon = categoryConfig?.icon || Package;
  const isSystemGenerated = item.id?.startsWith("workflow-") || item.id?.startsWith("task-") || item.id?.startsWith("asset-");

  return (
    <Card 
      className={`border ${categoryConfig?.borderColor || "border-slate-200"} hover:shadow-md transition-all group cursor-pointer`}
      data-testid={`inventory-item-${item.id}`}
      onClick={() => onView && onView(item)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className={`p-2 rounded-lg ${categoryConfig?.bgColor || "bg-slate-50"}`}>
            <Icon className={`w-5 h-5 ${categoryConfig?.color || "text-slate-500"}`} />
          </div>
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <StatusBadge status={item.status || "draft"} />
            {!isSystemGenerated && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEdit(item)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={() => onDelete(item)}
                    className="text-red-600 focus:text-red-600"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
        
        <h4 className="font-medium text-slate-900 mt-3">
          {item.name || item.title || "Untitled"}
        </h4>
        
        {item.description && (
          <p className="text-sm text-slate-500 mt-1 line-clamp-2">
            {item.description}
          </p>
        )}

        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {item.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {item.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{item.tags.length - 3}
              </Badge>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            {item.created_at && (
              <span>Created {new Date(item.created_at).toLocaleDateString()}</span>
            )}
          </div>
          {isSystemGenerated && (
            <Badge variant="outline" className="text-xs text-slate-400">
              System
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// ============== INVENTORY LIST ITEM ==============
const InventoryListItem = ({ item, category, onEdit, onDelete, onView }) => {
  const categoryConfig = INVENTORY_CATEGORIES[category];
  const Icon = categoryConfig?.icon || Package;
  const isSystemGenerated = item.id?.startsWith("workflow-") || item.id?.startsWith("task-") || item.id?.startsWith("asset-");

  return (
    <div 
      className="flex items-center gap-4 p-3 bg-white rounded-lg border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all group cursor-pointer"
      data-testid={`inventory-list-item-${item.id}`}
      onClick={() => onView && onView(item)}
    >
      <div className={`p-2 rounded-lg ${categoryConfig?.bgColor || "bg-slate-50"}`}>
        <Icon className={`w-4 h-4 ${categoryConfig?.color || "text-slate-500"}`} />
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-slate-900 truncate">
          {item.name || item.title || "Untitled"}
        </h4>
        {item.description && (
          <p className="text-xs text-slate-500 truncate">{item.description}</p>
        )}
      </div>

      <StatusBadge status={item.status || "draft"} />
      
      {!isSystemGenerated && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(item); }}>
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={(e) => { e.stopPropagation(); onDelete(item); }}
              className="text-red-600 focus:text-red-600"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
      
      <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
    </div>
  );
};

// ============== EMPTY STATE ==============
const EmptyState = ({ category, onAdd }) => {
  const config = INVENTORY_CATEGORIES[category];
  const Icon = config?.icon || Package;

  return (
    <div className="text-center py-12">
      <div className={`w-16 h-16 rounded-full ${config?.bgColor || "bg-slate-50"} flex items-center justify-center mx-auto mb-4`}>
        <Icon className={`w-8 h-8 ${config?.color || "text-slate-400"}`} />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-2">No {config?.label || "Items"} Yet</h3>
      <p className="text-sm text-slate-500 mb-4 max-w-sm mx-auto">
        {config?.description || "Start building your inventory by adding your first item."}
      </p>
      <Button onClick={onAdd} className="bg-slate-900 hover:bg-slate-800">
        <Plus className="w-4 h-4 mr-2" />
        Add {config?.label?.slice(0, -1) || "Item"}
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
      active: categoryItems.filter(i => i.status === "active" || i.status === "published" || i.status === "in_progress").length
    };
  });

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.id} className="border-0 shadow-sm hover:shadow-md transition-shadow">
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
  const [systemGeneratedData, setSystemGeneratedData] = useState({
    assets: [],
    offers: [],
    content: [],
    workflows: [],
    tasks: []
  });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState("assets");
  const [viewMode, setViewMode] = useState("grid");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  
  const navigate = useNavigate();

  // Fetch inventory data
  const fetchInventory = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch persisted inventory from API
      const inventoryRes = await fetch(`${BACKEND_URL}/api/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (inventoryRes.ok) {
        const data = await inventoryRes.json();
        setInventoryData({
          assets: data.assets || [],
          offers: data.offers || [],
          content: data.content || [],
          workflows: data.workflows || [],
          tasks: data.tasks || []
        });
      }

      // Also fetch system profile for system-generated items
      const profileRes = await fetch(`${BACKEND_URL}/api/system/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (profileRes.ok) {
        const profile = await profileRes.json();
        const systemData = transformProfileToSystemItems(profile);
        setSystemGeneratedData(systemData);
      }
      
    } catch (err) {
      setError(err.message);
      toast.error("Failed to load inventory");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchInventory();
    }
  }, [token, fetchInventory]);

  // Transform system profile to system-generated items
  const transformProfileToSystemItems = (profile) => {
    const workflows = [];
    const tasks = [];

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
          description: `Automated workflow for ${engine.replace(/_/g, " ")}`,
          status: "active",
          type: "engine_workflow",
          created_at: profile.intake_completed_at || new Date().toISOString()
        });
      });
    }

    // Map unlocked modules to Tasks
    if (profile.unlocked_modules) {
      profile.unlocked_modules.slice(0, 5).forEach((module, idx) => {
        tasks.push({
          id: `task-${idx}`,
          name: `Complete ${module.replace(/_/g, " ")}`,
          description: `Work through the ${module.replace(/_/g, " ")} module`,
          status: idx === 0 ? "in_progress" : "pending",
          type: "module_task",
          module_id: module,
          created_at: profile.intake_completed_at || new Date().toISOString()
        });
      });
    }

    return { assets: [], offers: [], content: [], workflows, tasks };
  };

  // Merge user items with system-generated items
  const getMergedItems = (category) => {
    const userItems = inventoryData[category] || [];
    const systemItems = systemGeneratedData[category] || [];
    return [...userItems, ...systemItems];
  };

  // Filter items by search query
  const getFilteredItems = (category) => {
    const items = getMergedItems(category);
    if (!searchQuery) return items;
    
    return items.filter(item => 
      (item.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.description || "").toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  // CRUD Operations
  const handleCreate = async (itemData) => {
    setActionLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(itemData)
      });

      if (!res.ok) {
        throw new Error("Failed to create item");
      }

      const newItem = await res.json();
      
      // Update local state
      setInventoryData(prev => ({
        ...prev,
        [itemData.category]: [...(prev[itemData.category] || []), newItem]
      }));

      toast.success(`${INVENTORY_CATEGORIES[itemData.category]?.label?.slice(0, -1) || "Item"} created successfully`);
      setIsModalOpen(false);
      setEditingItem(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdate = async (itemData) => {
    if (!editingItem) return;
    
    setActionLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${activeCategory}/${editingItem.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(itemData)
      });

      if (!res.ok) {
        throw new Error("Failed to update item");
      }

      const updatedItem = await res.json();
      
      // Update local state
      setInventoryData(prev => ({
        ...prev,
        [activeCategory]: prev[activeCategory].map(item => 
          item.id === editingItem.id ? updatedItem : item
        )
      }));

      toast.success("Item updated successfully");
      setIsModalOpen(false);
      setEditingItem(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteItem) return;
    
    setActionLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${activeCategory}/${deleteItem.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error("Failed to delete item");
      }
      
      // Update local state
      setInventoryData(prev => ({
        ...prev,
        [activeCategory]: prev[activeCategory].filter(item => item.id !== deleteItem.id)
      }));

      toast.success("Item deleted successfully");
      setDeleteItem(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingItem(null);
    setIsModalOpen(true);
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const viewItem = (item) => {
    // Navigate to item detail page
    navigate(`/inventory/${activeCategory}/${item.id}`);
  };

  const handleSave = (itemData) => {
    if (editingItem) {
      handleUpdate(itemData);
    } else {
      handleCreate(itemData);
    }
  };

  const currentItems = getFilteredItems(activeCategory);
  const currentCategory = INVENTORY_CATEGORIES[activeCategory];
  const totalCounts = Object.entries(INVENTORY_CATEGORIES).reduce((acc, [key]) => {
    acc[key] = getMergedItems(key).length;
    return acc;
  }, {});

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
            <p className="text-sm text-slate-500">Everything you&apos;ve built, organized and accessible</p>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="mb-6">
          <CategoryStats items={{
            ...inventoryData,
            workflows: getMergedItems("workflows"),
            tasks: getMergedItems("tasks")
          }} />
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
          <Button onClick={openCreateModal} className="bg-slate-900 hover:bg-slate-800">
            <Plus className="w-4 h-4 mr-2" />
            Add Item
          </Button>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="mb-6 bg-white border border-slate-200">
            {Object.entries(INVENTORY_CATEGORIES).map(([key, config]) => {
              const Icon = config.icon;
              const count = totalCounts[key];
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
                      {error}
                    </p>
                  </CardContent>
                </Card>
              )}

              {currentItems.length === 0 ? (
                <EmptyState 
                  category={category} 
                  onAdd={openCreateModal} 
                />
              ) : viewMode === "grid" ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {currentItems.map((item) => (
                    <InventoryItemCard
                      key={item.id}
                      item={item}
                      category={category}
                      onEdit={openEditModal}
                      onDelete={setDeleteItem}
                      onView={viewItem}
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
                      onEdit={openEditModal}
                      onDelete={setDeleteItem}
                      onView={viewItem}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Create/Edit Modal */}
      <InventoryItemModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingItem(null);
        }}
        onSave={handleSave}
        category={activeCategory}
        editItem={editingItem}
        loading={actionLoading}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!deleteItem}
        onClose={() => setDeleteItem(null)}
        onConfirm={handleDelete}
        itemName={deleteItem?.name || ""}
        loading={actionLoading}
      />
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
