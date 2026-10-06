"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Download,
  AlertCircle,
  FileText,
  Highlighter,
  ExternalLink,
  Layers,
} from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import { useAuthStore } from "@/store/authStore";
import { API_BASE_URL } from "@/lib/api";

interface PdfViewerProps {
  docId?: string | null;
  fileName: string;
  targetPage?: number | null;
  snippet?: string | null;
  className?: string;
}

interface TextMatch {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export function PdfViewer({
  docId,
  fileName,
  targetPage = 1,
  snippet,
  className = "",
}: PdfViewerProps) {
  const { accessToken } = useAuthStore();
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(targetPage || 1);
  const [scale, setScale] = useState<number>(1.2);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfDoc, setPdfDoc] = useState<any | null>(null);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [renderedPages, setRenderedPages] = useState<number[]>([]);
  const [highlightMatches, setHighlightMatches] = useState<Record<number, TextMatch[]>>({});
  const [viewMode, setViewMode] = useState<"canvas" | "embed">("canvas");

  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const canvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());
  const renderTasksRef = useRef<Map<number, any>>(new Map());

  // Determine effective target page
  const activeTargetPage = targetPage && targetPage > 0 ? targetPage : 1;

  // 1. Fetch PDF document bytes and initialize PDF.js
  useEffect(() => {
    let isCancelled = false;

    async function loadPdf() {
      setLoading(true);
      setError(null);

      try {
        const token =
          accessToken ||
          (typeof window !== "undefined"
            ? localStorage.getItem("access_token")
            : null);

        let pdfData: Uint8Array | ArrayBuffer;

        if (docId) {
          const fetchUrl = `${API_BASE_URL}/api/v1/documents/${docId}/file${
            token ? `?token=${encodeURIComponent(token)}` : ""
          }`;

          const res = await fetch(fetchUrl, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });

          if (!res.ok) {
            throw new Error(`Failed to load document: HTTP ${res.status}`);
          }

          const blob = await res.blob();
          const blobUrl = URL.createObjectURL(blob);
          if (!isCancelled) setPdfBlobUrl(blobUrl);

          const arrayBuffer = await blob.arrayBuffer();
          pdfData = new Uint8Array(arrayBuffer);
        } else {
          // Fallback demo/mock PDF rendering if docId is not provided
          setError(
            "Document ID not specified. Check supporting passage summary above."
          );
          setLoading(false);
          return;
        }

        // Dynamically load PDF.js in the browser
        const pdfjsLib = await import("pdfjs-dist");
        // Configure standard worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`;

        const loadingTask = pdfjsLib.getDocument({
          data: pdfData,
          cMapUrl: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/",
          cMapPacked: true,
        });

        const loadedPdf = await loadingTask.promise;
        if (isCancelled) return;

        setPdfDoc(loadedPdf);
        setNumPages(loadedPdf.numPages);
        setRenderedPages(Array.from({ length: loadedPdf.numPages }, (_, i) => i + 1));
        setLoading(false);
      } catch (err: any) {
        if (isCancelled) return;
        console.warn("PDF Canvas loader error, falling back to embedded viewer:", err);
        setError(
          err?.message ||
            "Unable to render PDF canvas. You can switch to Embedded Viewer mode."
        );
        setViewMode("embed");
        setLoading(false);
      }
    }

    loadPdf();

    return () => {
      isCancelled = true;
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
    };
  }, [docId, accessToken]);

  // 2. Render PDF Pages on HTML5 Canvas
  const renderPage = useCallback(
    async (pageNum: number) => {
      if (!pdfDoc) return;
      const canvas = canvasRefs.current.get(pageNum);
      if (!canvas) return;

      try {
        // Cancel ongoing render for this page if any
        if (renderTasksRef.current.has(pageNum)) {
          renderTasksRef.current.get(pageNum).cancel();
        }

        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale });
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Support High DPI / Retina displays
        const outputScale = window.devicePixelRatio || 1;
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;

        const transform =
          outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : undefined;

        const renderContext = {
          canvasContext: ctx,
          transform: transform,
          viewport: viewport,
        };

        const renderTask = page.render(renderContext);
        renderTasksRef.current.set(pageNum, renderTask);
        await renderTask.promise;

        // Extract text content for visual highlighting if on target page and snippet exists
        if (pageNum === activeTargetPage && snippet) {
          try {
            const textContent = await page.getTextContent();
            const cleanSnippetWords = snippet
              .toLowerCase()
              .replace(/[^\w\s]/g, " ")
              .split(/\s+/)
              .filter((w) => w.length > 3);

            const matches: TextMatch[] = [];
            for (const item of textContent.items as any[]) {
              if (!item.str) continue;
              const itemStr = item.str.toLowerCase();
              const hasMatch = cleanSnippetWords.some((word) => itemStr.includes(word));

              if (hasMatch && item.transform) {
                // PDF coordinates: [scaleX, skewY, skewX, scaleY, transX, transY]
                const tx = item.transform;
                const x = tx[4] * scale;
                // PDF y is bottom-up, viewport converts to top-down
                const y = (viewport.height - tx[5] * scale) - (item.height * scale || 12 * scale);
                matches.push({
                  text: item.str,
                  x: Math.max(0, x),
                  y: Math.max(0, y),
                  width: (item.width || item.str.length * 6) * scale,
                  height: (item.height || 14) * scale,
                });
              }
            }
            if (matches.length > 0) {
              setHighlightMatches((prev) => ({ ...prev, [pageNum]: matches }));
            }
          } catch (textErr) {
            console.warn("Could not extract text layer for highlighting:", textErr);
          }
        }
      } catch (err: any) {
        if (err?.name !== "RenderingCancelledException") {
          console.error(`Page ${pageNum} render error:`, err);
        }
      }
    },
    [pdfDoc, scale, activeTargetPage, snippet]
  );

  // Trigger render when scale or pdfDoc changes
  useEffect(() => {
    if (!pdfDoc || viewMode !== "canvas") return;
    renderedPages.forEach((pageNum) => {
      renderPage(pageNum);
    });
  }, [pdfDoc, scale, renderedPages, renderPage, viewMode]);

  // 3. Automatically scroll to target page
  const scrollToTargetPage = useCallback(() => {
    if (viewMode === "canvas") {
      const targetEl = pageRefs.current.get(activeTargetPage);
      if (targetEl && containerRef.current) {
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
        setCurrentPage(activeTargetPage);
      }
    }
  }, [activeTargetPage, viewMode]);

  useEffect(() => {
    if (!loading && pdfDoc) {
      // Delay slightly for initial canvas layout pass
      const timer = setTimeout(() => {
        scrollToTargetPage();
      }, 350);
      return () => clearTimeout(timer);
    }
  }, [loading, pdfDoc, activeTargetPage, scrollToTargetPage]);

  // Zoom handlers
  const handleZoomIn = () => setScale((s) => Math.min(2.5, +(s + 0.15).toFixed(2)));
  const handleZoomOut = () => setScale((s) => Math.max(0.6, +(s - 0.15).toFixed(2)));
  const handleResetZoom = () => setScale(1.2);
  const handleFitWidth = () => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth - 48;
      // standard PDF width is ~612pt
      const newScale = Math.max(0.6, +(containerWidth / 612).toFixed(2));
      setScale(Math.min(2.0, newScale));
    }
  };

  const handleNextPage = () => {
    if (currentPage < numPages) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      pageRefs.current.get(nextPage)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const prevPage = currentPage - 1;
      setCurrentPage(prevPage);
      pageRefs.current.get(prevPage)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className={`flex flex-col h-full bg-surface-primary text-text-primary rounded-xl border border-border overflow-hidden ${className}`}>
      {/* ── PDF Controls Toolbar ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-surface-secondary border-b border-border text-xs">
        {/* Page navigation */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1 || loading}
            aria-label="Previous Page"
            className="p-1 rounded-md hover:bg-surface-tertiary disabled:opacity-40 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-mono text-text-secondary">
            Page <strong className="text-text-primary">{currentPage}</strong> of{" "}
            <strong>{numPages || "—"}</strong>
          </span>
          <button
            onClick={handleNextPage}
            disabled={currentPage >= numPages || loading}
            aria-label="Next Page"
            className="p-1 rounded-md hover:bg-surface-tertiary disabled:opacity-40 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          {/* Jump to cited page button */}
          {activeTargetPage > 0 && activeTargetPage !== currentPage && (
            <button
              onClick={scrollToTargetPage}
              className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-yellow-500/20 text-yellow-300 border border-yellow-400/40 text-2xs hover:bg-yellow-500/30 transition-all"
            >
              <Highlighter className="w-3 h-3 text-yellow-400" />
              Jump to p.{activeTargetPage}
            </button>
          )}
        </div>

        {/* Zoom & View Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleZoomOut}
            disabled={scale <= 0.6 || loading}
            aria-label="Zoom Out"
            className="p-1.5 rounded-md hover:bg-surface-tertiary disabled:opacity-40 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-text-secondary px-1 text-2xs">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            disabled={scale >= 2.5 || loading}
            aria-label="Zoom In"
            className="p-1.5 rounded-md hover:bg-surface-tertiary disabled:opacity-40 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded-md hover:bg-surface-tertiary transition-colors"
            title="Reset Zoom (120%)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFitWidth}
            className="p-1.5 rounded-md hover:bg-surface-tertiary transition-colors"
            title="Fit to Width"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-[1px] bg-border mx-1" />

          {/* View Mode Toggle */}
          <button
            onClick={() => setViewMode(viewMode === "canvas" ? "embed" : "canvas")}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md hover:bg-surface-tertiary text-text-secondary hover:text-text-primary transition-colors text-2xs"
            title={viewMode === "canvas" ? "Switch to Browser Embed" : "Switch to Canvas Highlighter"}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{viewMode === "canvas" ? "Interactive" : "Native"}</span>
          </button>

          {/* Download link */}
          {pdfBlobUrl && (
            <a
              href={pdfBlobUrl}
              download={fileName || "document.pdf"}
              className="p-1.5 rounded-md hover:bg-surface-tertiary text-text-secondary hover:text-text-primary transition-colors"
              title="Download PDF"
            >
              <Download className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* ── Document View Area ── */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto overflow-x-auto p-4 flex flex-col items-center bg-surface-primary/70 relative"
      >
        {/* Loading Spinner */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Spinner size="lg" />
            <p className="text-xs text-text-muted">Loading & rendering institutional PDF...</p>
          </div>
        )}

        {/* Error message */}
        {error && !pdfBlobUrl && (
          <div className="flex flex-col items-center justify-center py-12 px-6 max-w-md text-center">
            <div className="w-12 h-12 rounded-xl bg-danger-subtle text-danger flex items-center justify-center mb-3">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-text-primary mb-1">Document Preview Notice</h4>
            <p className="text-xs text-text-muted mb-4">{error}</p>
            {pdfBlobUrl && (
              <button
                onClick={() => setViewMode("embed")}
                className="px-3 py-1.5 rounded-lg bg-surface-secondary border border-border text-xs hover:bg-surface-tertiary transition-colors"
              >
                Use Native PDF Embed
              </button>
            )}
          </div>
        )}

        {/* Canvas Multi-page rendering mode with Yellow Visual Highlighter */}
        {!loading && viewMode === "canvas" && (
          <div className="flex flex-col gap-6 items-center w-full">
            {renderedPages.map((pageNum) => {
              const isTargetPage = pageNum === activeTargetPage;
              const matches = highlightMatches[pageNum] || [];

              return (
                <div
                  key={pageNum}
                  ref={(el) => {
                    if (el) pageRefs.current.set(pageNum, el);
                    else pageRefs.current.delete(pageNum);
                  }}
                  id={`pdf-page-${pageNum}`}
                  className={`relative flex flex-col items-center rounded-lg shadow-elevated transition-all duration-300 ${
                    isTargetPage
                      ? "ring-2 ring-yellow-400/90 ring-offset-4 ring-offset-surface-primary"
                      : "border border-border/80"
                  }`}
                >
                  {/* Target Page Visual Highlight Banner indicator */}
                  {isTargetPage && (
                    <div className="w-full flex items-center justify-between px-3 py-1.5 bg-yellow-400/15 border-b border-yellow-400/40 text-yellow-300 text-2xs font-semibold rounded-t-lg backdrop-blur-xs">
                      <div className="flex items-center gap-1.5">
                        <Highlighter className="w-3.5 h-3.5 text-yellow-400 animate-pulse" />
                        <span>CITED PASSAGE LOCATION · PAGE {pageNum}</span>
                      </div>
                      <span className="text-3xs text-yellow-400/80 uppercase tracking-wider font-mono">
                        Active Citation
                      </span>
                    </div>
                  )}

                  {/* Canvas Container & Highlight Layer */}
                  <div className="relative bg-white overflow-hidden rounded-b-lg">
                    <canvas
                      ref={(el) => {
                        if (el) canvasRefs.current.set(pageNum, el);
                        else canvasRefs.current.delete(pageNum);
                      }}
                      className="block shadow-sm"
                    />

                    {/* Visual Highlighter: Yellow highlight overlay on target page */}
                    {isTargetPage && (
                      <div
                        className="absolute inset-0 pointer-events-none"
                        style={{ width: "100%", height: "100%" }}
                      >
                        {/* Word-level matches highlight */}
                        {matches.length > 0 ? (
                          matches.map((m, idx) => (
                            <div
                              key={idx}
                              style={{
                                left: `${m.x}px`,
                                top: `${m.y}px`,
                                width: `${m.width}px`,
                                height: `${m.height}px`,
                              }}
                              className="absolute bg-yellow-300/60 ring-2 ring-yellow-400 rounded-xs shadow-[0_0_10px_rgba(250,204,21,0.6)] mix-blend-multiply"
                              title="Supporting citation passage match"
                            />
                          ))
                        ) : (
                          /* Prominent passage focus highlight box on target page */
                          <div className="absolute top-[20%] left-[8%] right-[8%] min-h-[120px] rounded-lg border-2 border-yellow-400 bg-yellow-300/20 backdrop-blur-[0.5px] shadow-[0_0_25px_rgba(250,204,21,0.45)] pointer-events-none flex flex-col justify-between p-3 animate-fade-in">
                            <div className="flex items-center gap-1 text-2xs font-bold text-amber-900 bg-yellow-300/90 w-fit px-2 py-0.5 rounded shadow-xs">
                              <Highlighter className="w-3 h-3 text-amber-950" />
                              Supporting Passage Highlight
                            </div>
                            {snippet && (
                              <p className="text-xs text-amber-950 font-medium line-clamp-3 bg-yellow-100/90 p-1.5 rounded border border-yellow-300/60">
                                &ldquo;{snippet}&rdquo;
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Page number badge underneath */}
                  <div className="absolute -bottom-5 right-2 text-3xs font-mono text-text-muted">
                    p. {pageNum}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Embedded PDF iframe / native view fallback */}
        {!loading && viewMode === "embed" && pdfBlobUrl && (
          <div className="w-full h-full min-h-[600px] flex flex-col relative rounded-lg overflow-hidden border border-border">
            <iframe
              src={`${pdfBlobUrl}#page=${activeTargetPage}&view=FitH`}
              className="w-full h-full min-h-[600px] border-0 rounded-lg bg-surface-secondary"
              title={fileName}
            />
          </div>
        )}
      </div>
    </div>
  );
}
