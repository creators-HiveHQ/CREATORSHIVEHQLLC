/**
 * Asset Upload - Expression Phase
 * ================================
 * File/image upload functionality with preview,
 * validation, and backend storage.
 */

import { useState, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  ArrowLeft, Upload, Image, File, X, Check,
  FileText, FileImage, FileVideo, FileAudio,
  Loader2, AlertCircle, Cloud, CheckCircle2
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

// File type icons
const FILE_ICONS = {
  "image": FileImage,
  "video": FileVideo,
  "audio": FileAudio,
  "application/pdf": FileText,
  "default": File
};

// Get icon for file type
const getFileIcon = (mimeType) => {
  if (mimeType?.startsWith("image/")) return FILE_ICONS.image;
  if (mimeType?.startsWith("video/")) return FILE_ICONS.video;
  if (mimeType?.startsWith("audio/")) return FILE_ICONS.audio;
  if (mimeType === "application/pdf") return FILE_ICONS["application/pdf"];
  return FILE_ICONS.default;
};

// Format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// Allowed file types
const ALLOWED_TYPES = [
  "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
  "application/pdf",
  "video/mp4", "video/webm",
  "audio/mpeg", "audio/wav",
  "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// Get file icon component
const FileIconComponent = ({ mimeType, className }) => {
  if (mimeType?.startsWith("image/")) return <FileImage className={className} />;
  if (mimeType?.startsWith("video/")) return <FileVideo className={className} />;
  if (mimeType?.startsWith("audio/")) return <FileAudio className={className} />;
  if (mimeType === "application/pdf") return <FileText className={className} />;
  return <File className={className} />;
};

// ============== FILE PREVIEW CARD ==============
const FilePreviewCard = ({ file, preview, onRemove, uploadProgress, uploadStatus }) => {
  const isImage = file.type?.startsWith("image/");
  
  return (
    <div className="relative p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
      <div className="flex items-start gap-4">
        {/* Preview */}
        <div className="w-20 h-20 rounded-lg overflow-hidden bg-slate-100 flex items-center justify-center flex-shrink-0">
          {isImage && preview ? (
            <img src={preview} alt={file.name} className="w-full h-full object-cover" />
          ) : (
            <FileIconComponent mimeType={file.type} className="w-8 h-8 text-slate-400" />
          )}
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-slate-900 truncate">{file.name}</p>
          <p className="text-sm text-slate-500">{formatFileSize(file.size)}</p>
          <p className="text-xs text-slate-400 mt-1">{file.type || "Unknown type"}</p>
          
          {/* Upload Progress */}
          {uploadStatus === "uploading" && (
            <div className="mt-2">
              <Progress value={uploadProgress} className="h-1" />
              <p className="text-xs text-slate-500 mt-1">{uploadProgress}% uploaded</p>
            </div>
          )}
          
          {uploadStatus === "success" && (
            <div className="flex items-center gap-1 mt-2 text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
              <span className="text-sm">Uploaded</span>
            </div>
          )}
          
          {uploadStatus === "error" && (
            <div className="flex items-center gap-1 mt-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">Upload failed</span>
            </div>
          )}
        </div>
        
        {/* Remove Button */}
        {uploadStatus !== "uploading" && (
          <button
            onClick={onRemove}
            className="p-1 hover:bg-slate-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        )}
      </div>
    </div>
  );
};

// ============== DROP ZONE ==============
const DropZone = ({ onFilesSelected, isDragging, setIsDragging }) => {
  const inputRef = useRef(null);
  
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  }, [onFilesSelected, setIsDragging]);
  
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, [setIsDragging]);
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, [setIsDragging]);
  
  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    onFilesSelected(files);
  }, [onFilesSelected]);
  
  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => inputRef.current?.click()}
      className={`
        relative p-8 border-2 border-dashed rounded-xl cursor-pointer
        transition-all duration-200
        ${isDragging 
          ? "border-blue-500 bg-blue-50" 
          : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ALLOWED_TYPES.join(",")}
        onChange={handleFileInput}
        className="hidden"
      />
      
      <div className="text-center">
        <div className={`
          w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center
          ${isDragging ? "bg-blue-100" : "bg-slate-100"}
        `}>
          <Cloud className={`w-8 h-8 ${isDragging ? "text-blue-500" : "text-slate-400"}`} />
        </div>
        
        <p className="text-lg font-medium text-slate-700 mb-1">
          {isDragging ? "Drop files here" : "Drag & drop files here"}
        </p>
        <p className="text-sm text-slate-500 mb-4">
          or click to browse
        </p>
        
        <div className="flex flex-wrap justify-center gap-2">
          <span className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-500">Images</span>
          <span className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-500">PDFs</span>
          <span className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-500">Videos</span>
          <span className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-500">Documents</span>
        </div>
        
        <p className="text-xs text-slate-400 mt-4">
          Max file size: 10MB
        </p>
      </div>
    </div>
  );
};

// ============== MAIN COMPONENT ==============
export default function AssetUpload({ token }) {
  const { category, itemId } = useParams();
  const navigate = useNavigate();
  
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState({});
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadStatus, setUploadStatus] = useState({});
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  
  // Handle file selection
  const handleFilesSelected = useCallback((selectedFiles) => {
    const validFiles = selectedFiles.filter(file => {
      // Check type
      if (!ALLOWED_TYPES.includes(file.type)) {
        toast.error(`${file.name}: File type not allowed`);
        return false;
      }
      // Check size
      if (file.size > MAX_FILE_SIZE) {
        toast.error(`${file.name}: File too large (max 10MB)`);
        return false;
      }
      // Check if already added
      if (files.some(f => f.name === file.name && f.size === file.size)) {
        toast.error(`${file.name}: Already added`);
        return false;
      }
      return true;
    });
    
    // Generate previews for images
    validFiles.forEach(file => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setPreviews(prev => ({
            ...prev,
            [file.name]: e.target.result
          }));
        };
        reader.readAsDataURL(file);
      }
    });
    
    setFiles(prev => [...prev, ...validFiles]);
  }, [files]);
  
  // Remove file
  const handleRemoveFile = useCallback((fileName) => {
    setFiles(prev => prev.filter(f => f.name !== fileName));
    setPreviews(prev => {
      const updated = { ...prev };
      delete updated[fileName];
      return updated;
    });
    setUploadProgress(prev => {
      const updated = { ...prev };
      delete updated[fileName];
      return updated;
    });
    setUploadStatus(prev => {
      const updated = { ...prev };
      delete updated[fileName];
      return updated;
    });
  }, []);
  
  // Upload files
  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    const results = [];
    
    for (const file of files) {
      setUploadStatus(prev => ({ ...prev, [file.name]: "uploading" }));
      setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
      
      try {
        // Create form data
        const formData = new FormData();
        formData.append("file", file);
        formData.append("category", category);
        formData.append("item_id", itemId);
        
        // Upload with progress tracking using XMLHttpRequest
        const result = await new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          
          xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
              const progress = Math.round((e.loaded / e.total) * 100);
              setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
            }
          });
          
          xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(JSON.parse(xhr.responseText));
            } else {
              reject(new Error(xhr.statusText || "Upload failed"));
            }
          });
          
          xhr.addEventListener("error", () => reject(new Error("Network error")));
          
          xhr.open("POST", `${BACKEND_URL}/api/inventory/upload`);
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
          xhr.send(formData);
        });
        
        setUploadStatus(prev => ({ ...prev, [file.name]: "success" }));
        results.push({ file: file.name, success: true, data: result });
        
      } catch (error) {
        console.error(`Upload failed for ${file.name}:`, error);
        setUploadStatus(prev => ({ ...prev, [file.name]: "error" }));
        results.push({ file: file.name, success: false, error: error.message });
      }
    }
    
    setIsUploading(false);
    
    // Show summary
    const successCount = results.filter(r => r.success).length;
    if (successCount === results.length) {
      toast.success(`All ${successCount} files uploaded successfully`);
      // Navigate back after short delay
      setTimeout(() => {
        navigate(`/inventory/${category}/${itemId}`);
      }, 1500);
    } else {
      toast.error(`${successCount}/${results.length} files uploaded`);
    }
  };
  
  return (
    <div className="min-h-screen bg-slate-50" data-testid="asset-upload-page">
      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Button 
            variant="ghost" 
            onClick={() => navigate(`/inventory/${category}/${itemId}`)}
            className="text-slate-600"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Item
          </Button>
        </div>
        
        {/* Title */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl">
            <Upload className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Upload Files</h1>
            <p className="text-sm text-slate-500">Add attachments to your inventory item</p>
          </div>
        </div>
        
        {/* Drop Zone */}
        <Card className="border-0 shadow-sm mb-6">
          <CardContent className="p-6">
            <DropZone
              onFilesSelected={handleFilesSelected}
              isDragging={isDragging}
              setIsDragging={setIsDragging}
            />
          </CardContent>
        </Card>
        
        {/* Selected Files */}
        {files.length > 0 && (
          <Card className="border-0 shadow-sm mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Selected Files ({files.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {files.map((file) => (
                  <FilePreviewCard
                    key={file.name}
                    file={file}
                    preview={previews[file.name]}
                    onRemove={() => handleRemoveFile(file.name)}
                    uploadProgress={uploadProgress[file.name] || 0}
                    uploadStatus={uploadStatus[file.name]}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Upload Button */}
        {files.length > 0 && (
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setFiles([])}
              disabled={isUploading}
            >
              Clear All
            </Button>
            <Button
              onClick={handleUpload}
              disabled={isUploading || files.every(f => uploadStatus[f.name] === "success")}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload {files.length} {files.length === 1 ? "File" : "Files"}
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
