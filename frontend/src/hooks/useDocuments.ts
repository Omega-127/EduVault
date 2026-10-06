"use client";

import { useState, useCallback, useEffect } from "react";
import api from "@/lib/api";
import type { Document, DocumentUploadResponse } from "@/types/document";

/**
 * Hook for document management (admin).
 * Lists documents, handles uploads, and polls ingestion status.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  /** Fetch all documents */
  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<{ total: number; documents: Document[] }>(
        "/documents/"
      );
      setDocuments(data.documents ?? []);
    } catch {
      setError("Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  /** Upload a new document */
  const uploadDocument = useCallback(async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const { data } = await api.post<DocumentUploadResponse>(
        "/documents/upload",
        formData,
        {
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadProgress(progress);
            }
          },
        }
      );

      // Add the new document to the list
      setDocuments((prev) => [
        {
          id: data.id,
          file_name: data.file_name,
          storage_path: "",
          mime_type: file.type,
          status: data.status,
          uploaded_by: "",
          uploaded_at: new Date().toISOString(),
          chunk_count: null,
        },
        ...prev,
      ]);

      // Start polling for status updates
      pollDocumentStatus(data.id);

      return data;
    } catch {
      setError("Failed to upload document");
      return null;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, []);

  /** Poll document ingestion status every 3 seconds */
  const pollDocumentStatus = useCallback(
    (documentId: string) => {
      const interval = setInterval(async () => {
        try {
          const { data } = await api.get<Document>(
            `/documents/${documentId}`
          );

          setDocuments((prev) =>
            prev.map((doc) => (doc.id === documentId ? data : doc))
          );

          // Stop polling when the document reaches a terminal state
          if (data.status === "indexed" || data.status === "failed") {
            clearInterval(interval);
          }
        } catch {
          clearInterval(interval);
        }
      }, 3000);

      // Clean up after 5 minutes max
      setTimeout(() => clearInterval(interval), 300000);
    },
    []
  );

  /** Delete a document */
  const deleteDocument = useCallback(async (documentId: string) => {
    try {
      await api.delete(`/documents/${documentId}`);
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
    } catch {
      setError("Failed to delete document");
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  return {
    documents,
    isLoading,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    deleteDocument,
    refreshDocuments: loadDocuments,
    clearError: () => setError(null),
  };
}
