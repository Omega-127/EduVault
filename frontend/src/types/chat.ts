// ──────────────────────────────────────────────
// Chat Types
// ──────────────────────────────────────────────

export interface Citation {
  document_name: string;
  doc_id?: string | null;
  page: number | null;
  section: string | null;
  chunk_id?: string | null;
  snippet?: string | null;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

/** WebSocket frame types sent from the server */
export type WSFrameType = "token" | "citation" | "done" | "error";

export interface WSFrame {
  type: WSFrameType;
  data: string | Citation[] | null;
}

/** State for a streaming message in progress */
export interface StreamingMessage {
  content: string;
  citations: Citation[];
  isStreaming: boolean;
}
