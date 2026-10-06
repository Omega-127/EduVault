"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { createChatSocket, sendQuestion } from "@/lib/ws";
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
  const connect = useCallback(() => {
    if (!sessionId || !accessToken) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = createChatSocket(sessionId, accessToken, {
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
          // Move the completed streaming message into the messages array
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
      },
    });

    ws.onopen = () => setIsConnected(true);
    wsRef.current = ws;
  }, [sessionId, accessToken]);

  /** Send a question */
  const ask = useCallback(
    (question: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        // Attempt to reconnect
        connect();
        // Queue the message to send after connection
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            const userMessage: Message = {
              id: `msg-${Date.now()}`,
              session_id: sessionId!,
              role: "user",
              content: question,
              citations: [],
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, userMessage]);
            sendQuestion(wsRef.current!, question);
            setStreaming({ content: "", citations: [], isStreaming: true });
          }
        }, 500);
        return;
      }

      // Add user message immediately
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        session_id: sessionId!,
        role: "user",
        content: question,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      sendQuestion(wsRef.current, question);
      setStreaming({ content: "", citations: [], isStreaming: true });
      setError(null);
    },
    [sessionId, connect]
  );

  /** Load history and connect on mount */
  useEffect(() => {
    if (sessionId) {
      loadHistory();
      connect();
    }

    return () => {
      wsRef.current?.close();
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
