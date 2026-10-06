"use client";

import { useRef, useState } from "react";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn, formatFileSize } from "@/lib/utils";

interface DocumentUploaderProps {
  onUpload: (file: File) => Promise<unknown>;
  isUploading: boolean;
  uploadProgress: number;
  className?: string;
}

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "text/csv",
];

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.csv";

/**
 * Document upload component with drag-and-drop support.
 * Accepts PDF, DOCX, TXT, and CSV files.
 */
export function DocumentUploader({
  onUpload,
  isUploading,
  uploadProgress,
  className,
}: DocumentUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");

  const handleFileSelect = (file: File) => {
    if (!ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(pdf|docx|txt|csv)$/i)) {
      setUploadStatus("error");
      return;
    }
    setSelectedFile(file);
    setUploadStatus("idle");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      const result = await onUpload(selectedFile);
      if (!result) {
        setUploadStatus("error");
        return;
      }
      setUploadStatus("success");
      setSelectedFile(null);
    } catch {
      setUploadStatus("error");
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setUploadStatus("idle");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "flex flex-col items-center justify-center gap-3 p-8 rounded-xl",
          "border-2 border-dashed cursor-pointer transition-all duration-200",
          isDragging
            ? "border-accent bg-accent-subtle/50"
            : "border-border hover:border-text-muted hover:bg-surface-tertiary/30"
        )}
      >
        <div
          className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center transition-colors",
            isDragging ? "bg-accent text-text-inverse" : "bg-surface-tertiary text-text-muted"
          )}
        >
          <Upload className="w-6 h-6" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-text-primary">
            {isDragging ? "Drop your file here" : "Click to upload or drag and drop"}
          </p>
          <p className="text-xs text-text-muted mt-1">
            PDF, DOCX, TXT, or CSV · Max 50 MB
          </p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {/* Selected file preview */}
      {selectedFile && (
        <div className="flex items-center justify-between p-3 rounded-lg bg-surface-secondary border border-border animate-slide-up">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <FileText className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary truncate max-w-[200px]">
                {selectedFile.name}
              </p>
              <p className="text-xs text-text-muted">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={handleUpload}
              isLoading={isUploading}
            >
              Upload
            </Button>
            <button
              onClick={clearSelection}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-tertiary transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Upload progress */}
      {isUploading && (
        <div className="space-y-2 animate-fade-in">
          <div className="flex justify-between text-xs text-text-muted">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-surface-tertiary overflow-hidden">
            <div
              className="h-full rounded-full bg-accent transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Status feedback */}
      {uploadStatus === "success" && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-accent-subtle text-accent text-sm animate-slide-up">
          <CheckCircle className="w-4 h-4" />
          <span>Document uploaded successfully. Ingestion has started.</span>
        </div>
      )}

      {uploadStatus === "error" && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-danger-subtle text-danger text-sm animate-slide-up">
          <AlertCircle className="w-4 h-4" />
          <span>Upload failed. Please check the file format and try again.</span>
        </div>
      )}
    </div>
  );
}
