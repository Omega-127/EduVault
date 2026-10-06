// ──────────────────────────────────────────────
// Document Types
// ──────────────────────────────────────────────

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface Document {
  id: string;
  file_name: string;
  storage_path: string;
  mime_type: string;
  status: DocumentStatus;
  uploaded_by: string;
  uploaded_at: string;
  chunk_count: number | null;
}

export interface DocumentUploadResponse {
  id: string;
  file_name: string;
  status: DocumentStatus;
}
