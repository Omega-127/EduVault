"use client";

import { cn } from "@/lib/utils";
import type { Citation } from "@/types/chat";
import { FileText, Highlighter, ExternalLink } from "lucide-react";

interface CitationBadgeProps {
  citation: Citation;
  onClick?: (citation: Citation) => void;
  className?: string;
}

/**
 * Interactive citation badge displaying [Doc Name · p.N].
 * On click, opens the interactive PDF Citation Drawer and visual highlighter.
 */
export function CitationBadge({
  citation,
  onClick,
  className,
}: CitationBadgeProps) {
  const label = [
    citation.document_name,
    citation.page != null ? `p.${citation.page}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <button
      type="button"
      onClick={() => onClick?.(citation)}
      className={cn(
        "group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg",
        "bg-accent-subtle text-accent text-xs font-medium",
        "border border-accent/25 hover:border-accent/60",
        "hover:bg-accent-muted/40 hover:shadow-xs",
        "active:scale-95 transition-all duration-200 cursor-pointer",
        "max-w-[280px]",
        className
      )}
      title={`Click to open PDF at page ${citation.page || 1} & highlight passage`}
      aria-label={`View citation in ${citation.document_name}`}
    >
      <FileText className="w-3 h-3 flex-shrink-0 text-accent group-hover:text-yellow-400 transition-colors" />
      <span className="truncate">{label}</span>
      <Highlighter className="w-2.5 h-2.5 flex-shrink-0 opacity-0 group-hover:opacity-100 text-yellow-400 transition-opacity" />
    </button>
  );
}
