/**
 * Inventory Item Detail - Expression Phase
 * =========================================
 * Full detail view for inventory items with metadata,
 * tags, notes, connections, and file attachments.
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  ArrowLeft, Edit, Trash2, Save, X, Plus,
  Package, ShoppingBag, FileText, Workflow, CheckSquare,
  Tag, Clock, Calendar, Link2, MessageSquare, Paperclip,
  Image, File, Download, Eye, ChevronRight, Zap,
  RefreshCw, MoreHorizontal, ExternalLink, Activity
} from "lucide-react";
import { DeleteConfirmModal } from "./InventoryItemModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// Category config
const CATEGORIES = {
  assets: { label: "Asset", icon: Package, color: "text-blue-500", bgColor: "bg-blue-50" },
  offers: { label: "Offer", icon: ShoppingBag, color: "text-emerald-500", bgColor: "bg-emerald-50" },
  content: { label: "Content", icon: FileText, color: "text-purple-500", bgColor: "bg-purple-50" },
  workflows: { label: "Workflow", icon: Workflow, color: "text-amber-500", bgColor: "bg-amber-50" },
  tasks: { label: "Task", icon: CheckSquare, color: "text-rose-500", bgColor: "bg-rose-50" }
};

// Status config
const STATUS_CONFIG = {
  active: { label: "Active", color: "bg-emerald-100 text-emerald-700" },
  inactive: { label: "Inactive", color: "bg-slate-100 text-slate-600" },
  draft: { label: "Draft", color: "bg-amber-100 text-amber-700" },
  published: { label: "Published", color: "bg-blue-100 text-blue-700" },
  archived: { label: "Archived", color: "bg-slate-100 text-slate-500" },
  pending: { label: "Pending", color: "bg-purple-100 text-purple-700" },
  completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  in_progress: { label: "In Progress", color: "bg-blue-100 text-blue-700" }
};

// ============== NOTE COMPONENT ==============
const NoteItem = ({ note, onDelete }) => (
  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 group">
    <div className="flex items-start justify-between gap-2">
      <p className="text-sm text-slate-700">{note.content}</p>
      <button
        onClick={() => onDelete(note.id)}
        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded transition-all"
      >
        <X className="w-3 h-3 text-slate-400" />
      </button>
    </div>
    <p className="text-xs text-slate-400 mt-2">
      {new Date(note.created_at).toLocaleString()}
    </p>
  </div>
);

// ============== CONNECTION CARD ==============
const ConnectionCard = ({ connection, onClick }) => {
  const config = CATEGORIES[connection.category] || CATEGORIES.assets;
  const Icon = config.icon;
  
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all w-full text-left"
    >
      <div className={`p-2 rounded-lg ${config.bgColor}`}>
        <Icon className={`w-4 h-4 ${config.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 truncate">{connection.name}</p>
        <p className="text-xs text-slate-500">{config.label}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-400" />
    </button>
  );
};

// ============== ATTACHMENT PREVIEW ==============
const AttachmentPreview = ({ attachment, onRemove }) => {
  const isImage = attachment.type?.startsWith("image/");
  
  return (
    <div className="relative group">
      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
        {isImage && attachment.url ? (
          <img 
            src={attachment.url} 
            alt={attachment.name}
            className="w-full h-32 object-cover rounded-lg mb-2"
          />
        ) : (
          <div className="w-full h-32 bg-slate-100 rounded-lg flex items-center justify-center mb-2">
            <File className="w-10 h-10 text-slate-400" />
          </div>
        )}
        <p className="text-sm font-medium text-slate-700 truncate">{attachment.name}</p>
        <p className="text-xs text-slate-400">{attachment.size}</p>
      </div>
      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {attachment.url && (
          <a
            href={attachment.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 bg-white rounded shadow hover:bg-slate-50"
          >
            <Download className="w-4 h-4 text-slate-600" />
          </a>
        )}
        <button
          onClick={() => onRemove(attachment.id)}
          className="p-1 bg-white rounded shadow hover:bg-red-50"
        >
          <X className="w-4 h-4 text-red-500" />
        </button>
      </div>
    </div>
  );
};

// ============== MAIN COMPONENT ==============
export default function InventoryItemDetail({ token }) {
  const { category, itemId } = useParams();
  const navigate = useNavigate();
  
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    status: "draft",
    type: "",
    tags: []
  });
  
  // Notes state
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState("");
  
  // Connections state
  const [connections, setConnections] = useState([]);
  
  // Attachments state
  const [attachments, setAttachments] = useState([]);
  
  const categoryConfig = CATEGORIES[category] || CATEGORIES.assets;
  const CategoryIcon = categoryConfig.icon;
  const statusConfig = STATUS_CONFIG[item?.status] || STATUS_CONFIG.draft;

  // Fetch item details
  const fetchItem = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) {
        if (res.status === 404) {
          toast.error("Item not found");
          navigate("/inventory");
          return;
        }
        throw new Error("Failed to fetch item");
      }
      
      const data = await res.json();
      setItem(data);
      setEditForm({
        name: data.name || "",
        description: data.description || "",
        status: data.status || "draft",
        type: data.type || "",
        tags: data.tags || []
      });
      setNotes(data.metadata?.notes || []);
      setConnections(data.metadata?.connections || []);
      setAttachments(data.metadata?.attachments || []);
      
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, category, itemId, navigate]);

  useEffect(() => {
    if (token && category && itemId) {
      fetchItem();
    }
  }, [token, category, itemId, fetchItem]);

  // Save item changes
  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...editForm,
          metadata: {
            ...item?.metadata,
            notes,
            connections,
            attachments
          }
        })
      });
      
      if (!res.ok) throw new Error("Failed to save changes");
      
      const updated = await res.json();
      setItem(updated);
      setIsEditing(false);
      toast.success("Changes saved");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Delete item
  const handleDelete = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error("Failed to delete item");
      
      toast.success("Item deleted");
      navigate("/inventory");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
      setShowDeleteModal(false);
    }
  };

  // Add note
  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    
    const note = {
      id: `note-${Date.now()}`,
      content: newNote.trim(),
      created_at: new Date().toISOString()
    };
    
    const updatedNotes = [...notes, note];
    setNotes(updatedNotes);
    setNewNote("");
    
    // Save to backend
    try {
      await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          metadata: { ...item?.metadata, notes: updatedNotes }
        })
      });
      toast.success("Note added");
    } catch (err) {
      toast.error("Failed to save note");
    }
  };

  // Delete note
  const handleDeleteNote = async (noteId) => {
    const updatedNotes = notes.filter(n => n.id !== noteId);
    setNotes(updatedNotes);
    
    try {
      await fetch(`${BACKEND_URL}/api/inventory/${category}/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          metadata: { ...item?.metadata, notes: updatedNotes }
        })
      });
    } catch (err) {
      toast.error("Failed to delete note");
    }
  };

  // Add tag
  const handleAddTag = (tag) => {
    if (tag && !editForm.tags.includes(tag)) {
      setEditForm(prev => ({
        ...prev,
        tags: [...prev.tags, tag.toLowerCase()]
      }));
    }
  };

  // Remove tag
  const handleRemoveTag = (tagToRemove) => {
    setEditForm(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tagToRemove)
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-500">Item not found</p>
      </div>
    );
  }

  const isSystemGenerated = item.id?.startsWith("workflow-") || item.id?.startsWith("task-") || item.id?.startsWith("asset-");

  return (
    <div className="min-h-screen bg-slate-50" data-testid="inventory-item-detail">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate("/inventory")}
            className="text-slate-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Inventory
          </Button>
          
          {!isSystemGenerated && (
            <div className="flex items-center gap-2">
              {isEditing ? (
                <>
                  <Button variant="outline" onClick={() => setIsEditing(false)} disabled={saving}>
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                  <Button onClick={handleSave} disabled={saving} className="bg-slate-900 hover:bg-slate-800">
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? "Saving..." : "Save Changes"}
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="outline" onClick={() => setIsEditing(true)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                  <Button variant="destructive" onClick={() => setShowDeleteModal(true)}>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </Button>
                </>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Item Header Card */}
            <Card className="border-0 shadow-lg overflow-hidden">
              <div className={`h-2 ${categoryConfig.bgColor.replace("bg-", "bg-gradient-to-r from-").replace("-50", "-400")} to-${categoryConfig.bgColor.replace("bg-", "").replace("-50", "-600")}`} />
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${categoryConfig.bgColor}`}>
                    <CategoryIcon className={`w-6 h-6 ${categoryConfig.color}`} />
                  </div>
                  <div className="flex-1">
                    {isEditing ? (
                      <Input
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        className="text-xl font-bold mb-2"
                        placeholder="Item name"
                      />
                    ) : (
                      <h1 className="text-xl font-bold text-slate-900 mb-2">{item.name}</h1>
                    )}
                    <div className="flex items-center gap-3">
                      <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                      <span className="text-sm text-slate-500">{categoryConfig.label}</span>
                      {isSystemGenerated && (
                        <Badge variant="outline" className="text-xs">System Generated</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Description</CardTitle>
              </CardHeader>
              <CardContent>
                {isEditing ? (
                  <Textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                    placeholder="Add a description..."
                  />
                ) : (
                  <p className="text-slate-600">
                    {item.description || "No description provided."}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Tags */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {(isEditing ? editForm.tags : item.tags || []).map((tag) => (
                    <Badge 
                      key={tag} 
                      variant="secondary"
                      className="flex items-center gap-1"
                    >
                      {tag}
                      {isEditing && (
                        <button onClick={() => handleRemoveTag(tag)} className="ml-1">
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </Badge>
                  ))}
                  {isEditing && (
                    <Input
                      placeholder="Add tag..."
                      className="w-32 h-6 text-sm"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleAddTag(e.target.value);
                          e.target.value = "";
                        }
                      }}
                    />
                  )}
                  {(!isEditing && (!item.tags || item.tags.length === 0)) && (
                    <span className="text-sm text-slate-400">No tags</span>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Attachments */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Paperclip className="w-4 h-4" />
                    Attachments
                  </CardTitle>
                  {!isSystemGenerated && (
                    <Button variant="outline" size="sm" onClick={() => navigate(`/inventory/${category}/${itemId}/upload`)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add File
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {attachments.length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {attachments.map((att) => (
                      <AttachmentPreview 
                        key={att.id} 
                        attachment={att}
                        onRemove={(id) => setAttachments(prev => prev.filter(a => a.id !== id))}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No attachments</p>
                )}
              </CardContent>
            </Card>

            {/* Notes */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Notes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 mb-4">
                  {notes.length > 0 ? (
                    notes.map((note) => (
                      <NoteItem key={note.id} note={note} onDelete={handleDeleteNote} />
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No notes yet</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Add a note..."
                    onKeyDown={(e) => e.key === "Enter" && handleAddNote()}
                  />
                  <Button onClick={handleAddNote} disabled={!newNote.trim()}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Metadata */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Status</span>
                  {isEditing ? (
                    <select
                      value={editForm.status}
                      onChange={(e) => setEditForm(prev => ({ ...prev, status: e.target.value }))}
                      className="text-sm border rounded px-2 py-1"
                    >
                      {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                        <option key={key} value={key}>{config.label}</option>
                      ))}
                    </select>
                  ) : (
                    <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                  )}
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">Type</span>
                  {isEditing ? (
                    <Input
                      value={editForm.type}
                      onChange={(e) => setEditForm(prev => ({ ...prev, type: e.target.value }))}
                      className="w-32 h-8 text-sm"
                      placeholder="Type"
                    />
                  ) : (
                    <span className="text-sm text-slate-900">{item.type || "—"}</span>
                  )}
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Created
                  </span>
                  <span className="text-sm text-slate-900">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Updated
                  </span>
                  <span className="text-sm text-slate-900">
                    {new Date(item.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-500">ID</span>
                  <code className="text-xs bg-slate-100 px-2 py-1 rounded">{item.id}</code>
                </div>
              </CardContent>
            </Card>

            {/* Connections */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Link2 className="w-4 h-4" />
                    Connections
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {connections.length > 0 ? (
                  <div className="space-y-2">
                    {connections.map((conn) => (
                      <ConnectionCard 
                        key={conn.id} 
                        connection={conn}
                        onClick={() => navigate(`/inventory/${conn.category}/${conn.id}`)}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No connections</p>
                )}
              </CardContent>
            </Card>

            {/* Workflow Triggers (for workflows only) */}
            {category === "workflows" && (
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    Automation Triggers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {item.metadata?.triggers?.length > 0 ? (
                      item.metadata.triggers.map((trigger, idx) => (
                        <div key={idx} className="p-2 bg-amber-50 rounded-lg border border-amber-200">
                          <p className="text-sm font-medium text-amber-700">{trigger.type}</p>
                          <p className="text-xs text-amber-600">{trigger.description}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-slate-400">No triggers configured</p>
                    )}
                    <Button variant="outline" size="sm" className="w-full mt-2" onClick={() => navigate(`/inventory/${category}/${itemId}/triggers`)}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Trigger
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Task Progress (for tasks only) */}
            {category === "tasks" && (
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Activity className="w-4 h-4 text-rose-500" />
                    Progress
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">Completion</span>
                      <span className="text-sm font-medium text-slate-900">
                        {item.metadata?.progress || 0}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-rose-500 rounded-full transition-all"
                        style={{ width: `${item.metadata?.progress || 0}%` }}
                      />
                    </div>
                    {item.status !== "completed" && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="w-full"
                        onClick={() => {
                          setEditForm(prev => ({ ...prev, status: "completed" }));
                          handleSave();
                        }}
                      >
                        Mark Complete
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        itemName={item.name}
        loading={saving}
      />
    </div>
  );
}
