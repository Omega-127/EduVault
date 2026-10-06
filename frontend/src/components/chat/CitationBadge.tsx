"use client";

import { cn } from "@/lib/utils";
import type { Citation } from "@/types/chat";
import { FileText } from "lucide-react";

interface CitationBadgeProps {
  citation: Citation;
  onClick?: () => void;
  className?: string;
}

/**
 * Tappable chip displaying [Doc Name · p.N].
 * On click, will open CitationDrawer (future) or scroll to source summary.
 */
export function CitationBadge({ citation, onClick, className }: CitationBadgeProps) {
  const label = [
    citation.document_name,
    citation.page != null ? `p.${citation.page}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg",
        "bg-accent-subtle text-accent text-xs font-medium",
        "border border-accent/20",
        "hover:bg-accent-muted hover:border-accent/40",
        "transition-all duration-200 cursor-pointer",
        "max-w-[240px]",
        className
      )}
      title={
        citation.section
          ? `${citation.document_name} — ${citation.section}`
          : citation.document_name
      }
    >
      <FileText className="w-3 h-3 flex-shrink-0" />
      <span className="truncate">{label}</span>
    </button>
  );
}
