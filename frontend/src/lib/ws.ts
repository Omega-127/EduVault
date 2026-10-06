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
    onOpen?: () => void;
  }
): WebSocket {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  const url = `${wsBase}/api/v1/chat/sessions/${sessionId}/stream?token=${encodeURIComponent(token)}`;

  const ws = new WebSocket(url);

  ws.onopen = () => {
    callbacks.onOpen?.();
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
    callbacks.onError(
      "WebSocket connection failed. Please ensure the backend server is running."
    );
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
 * Waits until a WebSocket is OPEN, or rejects on timeout / close / error.
 */
export function waitForOpen(
  ws: WebSocket,
  timeoutMs = 10000
): Promise<WebSocket> {
  if (ws.readyState === WebSocket.OPEN) {
    return Promise.resolve(ws);
  }
  if (
    ws.readyState === WebSocket.CLOSING ||
    ws.readyState === WebSocket.CLOSED
  ) {
    return Promise.reject(new Error("WebSocket is closed"));
  }

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("WebSocket connection timed out"));
    }, timeoutMs);

    const onOpen = () => {
      cleanup();
      resolve(ws);
    };
    const onError = () => {
      cleanup();
      reject(new Error("WebSocket connection failed"));
    };
    const onClose = () => {
      cleanup();
      reject(new Error("WebSocket closed before opening"));
    };

    const cleanup = () => {
      clearTimeout(timer);
      ws.removeEventListener("open", onOpen);
      ws.removeEventListener("error", onError);
      ws.removeEventListener("close", onClose);
    };

    ws.addEventListener("open", onOpen);
    ws.addEventListener("error", onError);
    ws.addEventListener("close", onClose);
  });
}

/**
 * Sends a question through an existing WebSocket connection.
 */
export function sendQuestion(ws: WebSocket, question: string): void {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ question }));
  }
}
