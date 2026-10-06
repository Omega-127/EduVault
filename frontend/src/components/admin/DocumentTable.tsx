"use client";

import { Trash2, FileText, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, getStatusColor } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { Document } from "@/types/document";

interface DocumentTableProps {
  documents: Document[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  className?: string;
}

const statusVariantMap: Record<string, "accent" | "warning" | "info" | "danger" | "default"> = {
  indexed: "accent",
  processing: "warning",
  pending: "info",
  failed: "danger",
};

/**
 * Table displaying all uploaded documents with status, metadata, and actions.
 */
export function DocumentTable({
  documents,
  isLoading,
  onDelete,
  className,
}: DocumentTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-14 h-14 rounded-xl bg-surface-tertiary flex items-center justify-center mb-4">
          <FileText className="w-7 h-7 text-text-muted" />
        </div>
        <p className="text-sm font-medium text-text-secondary mb-1">
          No documents uploaded yet
        </p>
        <p className="text-xs text-text-muted">
          Upload your first document to start building the knowledge base.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full">
        <thead>
          <tr>
            <th className="table-header">Document</th>
            <th className="table-header">Type</th>
            <th className="table-header">Status</th>
            <th className="table-header">Chunks</th>
            <th className="table-header">Uploaded</th>
            <th className="table-header text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id} className="table-row">
              <td className="table-cell">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-accent-subtle flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4 text-accent" />
                  </div>
                  <span className="text-sm font-medium text-text-primary truncate max-w-[200px]">
                    {doc.file_name}
                  </span>
                </div>
              </td>
              <td className="table-cell">
                <span className="text-xs font-mono text-text-muted uppercase">
                  {doc.mime_type.split("/").pop()}
                </span>
              </td>
              <td className="table-cell">
                <Badge
                  variant={statusVariantMap[doc.status] || "default"}
                  dot
                >
                  {doc.status}
                </Badge>
              </td>
              <td className="table-cell">
                <span className="text-sm text-text-secondary">
                  {doc.chunk_count ?? "—"}
                </span>
              </td>
              <td className="table-cell">
                <span className="text-sm text-text-muted">
                  {formatDate(doc.uploaded_at)}
                </span>
              </td>
              <td className="table-cell text-right">
                <div className="flex items-center justify-end gap-1">
                  <Button size="icon" variant="ghost" className="w-8 h-8">
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="w-8 h-8 text-danger hover:text-danger hover:bg-danger-subtle"
                    onClick={() => onDelete(doc.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
