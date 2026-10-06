"use client";

import { CheckCircle, Clock, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Document } from "@/types/document";

interface JobStatusPanelProps {
  documents: Document[];
  className?: string;
}

const statusConfig = {
  pending: {
    icon: Clock,
    color: "text-info",
    bgColor: "bg-info-subtle",
    label: "Pending",
  },
  processing: {
    icon: Loader2,
    color: "text-warning",
    bgColor: "bg-warning-subtle",
    label: "Processing",
    animate: true,
  },
  indexed: {
    icon: CheckCircle,
    color: "text-accent",
    bgColor: "bg-accent-subtle",
    label: "Indexed",
  },
  failed: {
    icon: XCircle,
    color: "text-danger",
    bgColor: "bg-danger-subtle",
    label: "Failed",
  },
};

/**
 * Panel showing the ingestion status of recently uploaded documents.
 * Highlights documents that are currently processing.
 */
export function JobStatusPanel({ documents, className }: JobStatusPanelProps) {
  // Show only non-indexed documents or recently indexed ones
  const activeJobs = documents.filter(
    (doc) => doc.status !== "indexed" || isRecentlyIndexed(doc)
  );

  if (activeJobs.length === 0) {
    return (
      <div
        className={cn(
          "p-4 rounded-xl bg-surface-secondary border border-border text-center",
          className
        )}
      >
        <p className="text-sm text-text-muted">
          No active ingestion jobs
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <h3 className="text-sm font-semibold text-text-primary px-1">
        Ingestion Jobs
      </h3>
      {activeJobs.map((doc) => {
        const config = statusConfig[doc.status];
        const Icon = config.icon;

        return (
          <div
            key={doc.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-surface-secondary border border-border animate-fade-in"
          >
            <div
              className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center",
                config.bgColor
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4",
                  config.color,
                  "animate" in config && config.animate && "animate-spin"
                )}
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {doc.file_name}
              </p>
              <p className={cn("text-xs", config.color)}>
                {config.label}
                {doc.status === "indexed" && doc.chunk_count != null && (
                  <span className="text-text-muted">
                    {" "}
                    · {doc.chunk_count} chunks
                  </span>
                )}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Check if a document was indexed in the last 5 minutes */
function isRecentlyIndexed(doc: Document): boolean {
  const uploadedAt = new Date(doc.uploaded_at).getTime();
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
  return uploadedAt > fiveMinutesAgo;
}
