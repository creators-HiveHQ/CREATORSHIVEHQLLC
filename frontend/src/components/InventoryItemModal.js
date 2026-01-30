/**
 * Inventory Item Modal - Expression Phase
 * ========================================
 * Modal for creating and editing inventory items
 * with consistent styling and micro-interactions.
 */

import { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Package, ShoppingBag, FileText, Workflow, CheckSquare,
  Save, X, Loader2, Tag, Plus, Trash2
} from "lucide-react";

// Category configuration
const CATEGORIES = {
  assets: { 
    label: "Asset", 
    icon: Package, 
    color: "text-blue-500",
    bgColor: "bg-blue-50",
    placeholder: "e.g., Brand Guidelines, Logo Pack, Content Templates"
  },
  offers: { 
    label: "Offer", 
    icon: ShoppingBag, 
    color: "text-emerald-500",
    bgColor: "bg-emerald-50",
    placeholder: "e.g., Consulting Package, Online Course, Coaching Program"
  },
  content: { 
    label: "Content", 
    icon: FileText, 
    color: "text-purple-500",
    bgColor: "bg-purple-50",
    placeholder: "e.g., Blog Post, Video Script, Email Sequence"
  },
  workflows: { 
    label: "Workflow", 
    icon: Workflow, 
    color: "text-amber-500",
    bgColor: "bg-amber-50",
    placeholder: "e.g., Client Onboarding, Content Publishing, Lead Nurture"
  },
  tasks: { 
    label: "Task", 
    icon: CheckSquare, 
    color: "text-rose-500",
    bgColor: "bg-rose-50",
    placeholder: "e.g., Update Website, Create Freebie, Record Video"
  }
};

// Status options
const STATUS_OPTIONS = [
  { value: "draft", label: "Draft", color: "bg-slate-100 text-slate-700" },
  { value: "active", label: "Active", color: "bg-emerald-100 text-emerald-700" },
  { value: "in_progress", label: "In Progress", color: "bg-blue-100 text-blue-700" },
  { value: "pending", label: "Pending", color: "bg-purple-100 text-purple-700" },
  { value: "completed", label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  { value: "published", label: "Published", color: "bg-blue-100 text-blue-700" },
  { value: "inactive", label: "Inactive", color: "bg-slate-100 text-slate-500" },
  { value: "archived", label: "Archived", color: "bg-slate-100 text-slate-400" }
];

export default function InventoryItemModal({
  isOpen,
  onClose,
  onSave,
  category,
  editItem = null,
  loading = false
}) {
  // Form state
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    status: "draft",
    type: "",
    tags: []
  });
  const [tagInput, setTagInput] = useState("");
  const [errors, setErrors] = useState({});
  
  // Track if modal just opened to reset form
  const modalOpenRef = useRef(false);
  const editItemRef = useRef(editItem);

  // Reset form when modal opens or editItem changes
  if (isOpen && !modalOpenRef.current) {
    // Modal just opened
    modalOpenRef.current = true;
    const newData = {
      name: editItem?.name || "",
      description: editItem?.description || "",
      status: editItem?.status || "draft",
      type: editItem?.type || "",
      tags: editItem?.tags || []
    };
    // Use a microtask to avoid setState during render
    Promise.resolve().then(() => {
      setFormData(newData);
      setErrors({});
      setTagInput("");
    });
  } else if (!isOpen && modalOpenRef.current) {
    // Modal closed
    modalOpenRef.current = false;
  }
  
  // Update editItemRef
  if (editItemRef.current !== editItem) {
    editItemRef.current = editItem;
    if (isOpen && editItem) {
      Promise.resolve().then(() => {
        setFormData({
          name: editItem.name || "",
          description: editItem.description || "",
          status: editItem.status || "draft",
          type: editItem.type || "",
          tags: editItem.tags || []
        });
        setErrors({});
      });
    }
  }

  const isEditMode = !!editItem;
  const categoryConfig = CATEGORIES[category] || CATEGORIES.assets;
  const CategoryIcon = categoryConfig.icon;

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleAddTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
    }
    setTagInput("");
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tagToRemove)
    }));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    } else if (formData.name.length > 200) {
      newErrors.name = "Name must be less than 200 characters";
    }
    if (formData.description && formData.description.length > 1000) {
      newErrors.description = "Description must be less than 1000 characters";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    
    onSave({
      ...formData,
      category
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${categoryConfig.bgColor}`}>
              <CategoryIcon className={`w-5 h-5 ${categoryConfig.color}`} />
            </div>
            <div>
              <DialogTitle>
                {isEditMode ? `Edit ${categoryConfig.label}` : `New ${categoryConfig.label}`}
              </DialogTitle>
              <DialogDescription>
                {isEditMode 
                  ? `Update the details for this ${categoryConfig.label.toLowerCase()}.`
                  : `Add a new ${categoryConfig.label.toLowerCase()} to your inventory.`
                }
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-sm font-medium">
              Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder={categoryConfig.placeholder}
              className={errors.name ? "border-red-500" : ""}
              data-testid="inventory-item-name"
            />
            {errors.name && (
              <p className="text-xs text-red-500">{errors.name}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium">
              Description
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange("description", e.target.value)}
              placeholder="Add a brief description..."
              rows={3}
              className={errors.description ? "border-red-500" : ""}
              data-testid="inventory-item-description"
            />
            {errors.description && (
              <p className="text-xs text-red-500">{errors.description}</p>
            )}
            <p className="text-xs text-slate-400 text-right">
              {formData.description.length}/1000
            </p>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Status</Label>
            <Select
              value={formData.status}
              onValueChange={(value) => handleChange("status", value)}
            >
              <SelectTrigger data-testid="inventory-item-status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${option.color.split(" ")[0]}`} />
                      {option.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Type */}
          <div className="space-y-2">
            <Label htmlFor="type" className="text-sm font-medium">
              Type <span className="text-slate-400">(optional)</span>
            </Label>
            <Input
              id="type"
              value={formData.type}
              onChange={(e) => handleChange("type", e.target.value)}
              placeholder="e.g., Document, Video, Template"
              data-testid="inventory-item-type"
            />
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              Tags <span className="text-slate-400">(optional)</span>
            </Label>
            <div className="flex gap-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add a tag..."
                className="flex-1"
                data-testid="inventory-item-tag-input"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handleAddTag}
                disabled={!tagInput.trim()}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="flex items-center gap-1 pl-2 pr-1"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 p-0.5 rounded hover:bg-slate-300 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="bg-slate-900 hover:bg-slate-800"
            data-testid="inventory-item-save"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {isEditMode ? "Update" : "Create"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Delete confirmation modal
export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  itemName,
  loading = false
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="w-5 h-5" />
            Delete Item
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>&quot;{itemName}&quot;</strong>? 
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="gap-2 mt-4">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={loading}
            data-testid="confirm-delete"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
