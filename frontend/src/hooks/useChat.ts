"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { createChatSocket, sendQuestion, waitForOpen } from "@/lib/ws";
import { useAuthStore } from "@/store/authStore";
import api from "@/lib/api";
import type { Message, Citation, StreamingMessage, ChatSession } from "@/types/chat";

/**
 * Chat hook — manages WebSocket streaming, message state, and session history.
 */
export function useChat(sessionId: string | null) {
  const { accessToken } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState<StreamingMessage>({
    content: "",
    citations: [],
    isStreaming: false,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(() => {
    return (
      accessToken ||
      (typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null)
    );
  }, [accessToken]);

  /** Load message history for the session */
  const loadHistory = useCallback(async () => {
    if (!sessionId) return;

    setIsLoadingHistory(true);
    try {
      const { data } = await api.get<Message[]>(
        `/chat/sessions/${sessionId}/messages`
      );
      setMessages(data);
    } catch {
      setError("Failed to load chat history");
    } finally {
      setIsLoadingHistory(false);
    }
  }, [sessionId]);

  /** Connect WebSocket for streaming */
  const connect = useCallback((): WebSocket | null => {
    const token = getToken();

    if (!sessionId) return null;
    if (!token) {
      setError("Please log in to chat with EduVault.");
      return null;
    }

    // Reuse an open or connecting socket instead of tearing it down
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return wsRef.current;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = createChatSocket(sessionId, token, {
      onOpen: () => {
        setIsConnected(true);
        setError(null);
      },
      onToken: (text) => {
        setStreaming((prev) => ({
          ...prev,
          content: prev.content + text,
          isStreaming: true,
        }));
      },
      onCitation: (data) => {
        setStreaming((prev) => ({
          ...prev,
          citations: data as Citation[],
        }));
      },
      onDone: () => {
        setStreaming((prev) => {
          const completedMessage: Message = {
            id: `msg-${Date.now()}`,
            session_id: sessionId!,
            role: "assistant",
            content: prev.content,
            citations: prev.citations,
            created_at: new Date().toISOString(),
          };

          setMessages((msgs) => [...msgs, completedMessage]);

          return {
            content: "",
            citations: [],
            isStreaming: false,
          };
        });
      },
      onError: (errorMsg) => {
        setError(errorMsg);
        setStreaming({ content: "", citations: [], isStreaming: false });
      },
      onClose: () => {
        setIsConnected(false);
        setStreaming((prev) =>
          prev.isStreaming
            ? { content: "", citations: [], isStreaming: false }
            : prev
        );
      },
    });

    wsRef.current = ws;
    return ws;
  }, [sessionId, getToken]);

  /** Send a question */
  const ask = useCallback(
    async (question: string) => {
      const token = getToken();

      if (!token) {
        setError(
          "You must be logged in to send messages. Please log in at /login."
        );
        return;
      }

      if (!sessionId) {
        setError("No active chat session. Please start a new chat.");
        return;
      }

      try {
        let ws = wsRef.current;
        if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
          ws = connect();
        }
        if (!ws) {
          setError("Unable to connect to the backend server.");
          return;
        }

        await waitForOpen(ws, 10000);

        const userMessage: Message = {
          id: `msg-${Date.now()}`,
          session_id: sessionId,
          role: "user",
          content: question,
          citations: [],
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);
        sendQuestion(ws, question);
        setStreaming({ content: "", citations: [], isStreaming: true });
        setError(null);
      } catch {
        setError(
          "Unable to connect to the backend server. Please verify the API is running and try again."
        );
        setStreaming({ content: "", citations: [], isStreaming: false });
      }
    },
    [sessionId, getToken, connect]
  );

  /** Load history and connect on mount */
  useEffect(() => {
    if (sessionId) {
      loadHistory();
      connect();
    }

    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [sessionId, loadHistory, connect]);

  return {
    messages,
    streaming,
    isConnected,
    isLoadingHistory,
    error,
    ask,
    clearError: () => setError(null),
  };
}

/**
 * Hook to manage chat sessions (list, create, delete).
 */
export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<ChatSession[]>("/chat/sessions");
      setSessions(data);
    } catch {
      // Silently fail — sessions will show empty
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createSession = useCallback(async (title?: string) => {
    const { data } = await api.post<ChatSession>("/chat/sessions", {
      title: title || "New Chat",
    });
    setSessions((prev) => [data, ...prev]);
    return data;
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return { sessions, isLoading, createSession, refreshSessions: loadSessions };
}
