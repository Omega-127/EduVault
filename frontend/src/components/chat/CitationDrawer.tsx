"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  X,
  FileText,
  Highlighter,
  Copy,
  Check,
  ExternalLink,
  BookOpen,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import type { Citation } from "@/types/chat";
import { Spinner } from "@/components/ui/Spinner";

// Dynamically import PdfViewer client-side only to prevent SSR canvas issues
const PdfViewer = dynamic(
  () => import("./PdfViewer").then((mod) => mod.PdfViewer),
  {
    ssr: false,
    loading: () => (
      <div className="flex flex-col items-center justify-center h-full py-24 text-text-muted">
        <Spinner size="lg" />
        <span className="text-xs mt-3">Loading interactive PDF viewer...</span>
      </div>
    ),
  }
);

interface CitationDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export function CitationDrawer({
  citation,
  isOpen,
  onClose,
}: CitationDrawerProps) {
  const [copied, setCopied] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent background scrolling when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen || !citation) {
    return null;
  }

  const handleCopyCitation = () => {
    const text = [
      citation.document_name,
      citation.page != null ? `p. ${citation.page}` : null,
      citation.section ? `§ ${citation.section}` : null,
      citation.snippet ? `\n"${citation.snippet}"` : null,
    ]
      .filter(Boolean)
      .join(" · ");

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-fade-in">
      {/* ── Backdrop Overlay ── */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity cursor-pointer"
        aria-hidden="true"
      />

      {/* ── Slide-out Drawer Container ── */}
      <div
        className="relative z-10 w-full max-w-3xl lg:max-w-4xl xl:max-w-5xl h-full bg-surface-primary border-l border-border shadow-elevated flex flex-col transform transition-transform duration-300 ease-out"
        role="dialog"
        aria-modal="true"
        aria-label="PDF Citation Drawer"
      >
        {/* ── Top Header ── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-secondary/80 backdrop-blur-md">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent-subtle text-accent flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-text-primary truncate max-w-md">
                  {citation.document_name}
                </h3>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent-subtle text-accent text-3xs font-medium border border-accent/20">
                  <ShieldCheck className="w-3 h-3" />
                  Verified Source
                </span>
              </div>
              <div className="flex items-center gap-2 text-2xs text-text-muted mt-0.5">
                {citation.page != null && (
                  <span className="font-mono bg-surface-tertiary px-1.5 py-0.5 rounded text-text-secondary">
                    Page {citation.page}
                  </span>
                )}
                {citation.section && (
                  <span className="truncate max-w-[200px] text-text-secondary">
                    Section: {citation.section}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Copy Citation button */}
            <button
              onClick={handleCopyCitation}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-border text-xs text-text-secondary hover:text-text-primary transition-colors"
              title="Copy citation reference and passage"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-accent" />
                  <span className="text-accent font-medium">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Citation</span>
                </>
              )}
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-surface-tertiary text-text-secondary hover:text-text-primary transition-colors"
              aria-label="Close Drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ── Supporting Passage Banner (Yellow Visual Highlighter) ── */}
        <div className="px-6 py-3.5 bg-yellow-500/10 border-b border-yellow-500/30">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5 flex-1 min-w-0">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-yellow-300">
                <Highlighter className="w-4 h-4 text-yellow-400" />
                <span>Supporting Passage · Highlighted in Document</span>
              </div>

              {citation.snippet ? (
                <div className="p-2.5 rounded-lg bg-yellow-400/15 border-l-4 border-yellow-400 text-xs text-text-primary leading-relaxed font-sans shadow-2xs">
                  <mark className="bg-yellow-300/80 text-neutral-950 font-medium px-1 py-0.5 rounded shadow-2xs">
                    &ldquo;{citation.snippet}&rdquo;
                  </mark>
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">
                  Referenced from {citation.document_name}
                  {citation.page ? ` on page ${citation.page}` : ""}.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ── Embedded PDF Viewer with Canvas & Visual Highlighter ── */}
        <div className="flex-1 p-4 overflow-hidden bg-surface-primary">
          <PdfViewer
            docId={citation.doc_id}
            fileName={citation.document_name}
            targetPage={citation.page}
            snippet={citation.snippet}
            className="h-full w-full shadow-inner"
          />
        </div>
      </div>
    </div>
  );
}
