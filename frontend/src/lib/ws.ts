import { API_BASE_URL } from "./api";
import type { WSFrame } from "@/types/chat";

/**
 * Creates a WebSocket connection for chat streaming.
 *
 * The server expects JWT as a query param on handshake:
 *   ws://host/api/v1/chat/sessions/{id}/stream?token=<jwt>
 *
 * Server sends JSON frames:
 *   { type: "token",    data: "partial text" }
 *   { type: "citation", data: [{doc, page, section}] }
 *   { type: "done" }
 *   { type: "error",    data: "error message" }
 */

export function createChatSocket(
  sessionId: string,
  token: string,
  callbacks: {
    onToken: (text: string) => void;
    onCitation: (data: WSFrame["data"]) => void;
    onDone: () => void;
    onError: (error: string) => void;
    onClose?: () => void;
  }
): WebSocket {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  const url = `${wsBase}/api/v1/chat/sessions/${sessionId}/stream?token=${token}`;

  const ws = new WebSocket(url);

  ws.onopen = () => {
    // Connection established — ready to send questions
  };

  ws.onmessage = (event) => {
    try {
      const frame: WSFrame = JSON.parse(event.data);

      switch (frame.type) {
        case "token":
          callbacks.onToken(frame.data as string);
          break;
        case "citation":
          callbacks.onCitation(frame.data);
          break;
        case "done":
          callbacks.onDone();
          break;
        case "error":
          callbacks.onError(frame.data as string);
          break;
      }
    } catch {
      callbacks.onError("Failed to parse server message");
    }
  };

  ws.onerror = () => {
    callbacks.onError("WebSocket connection failed. Please ensure the backend server is running on port 8000.");
  };

  ws.onclose = (event) => {
    if (!event.wasClean && event.code !== 1000) {
      callbacks.onError("WebSocket disconnected from backend server.");
    }
    callbacks.onClose?.();
  };

  return ws;
}

/**
 * Sends a question through an existing WebSocket connection.
 */
export function sendQuestion(ws: WebSocket, question: string): void {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ question }));
  }
}
